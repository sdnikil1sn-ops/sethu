# AI pipeline

AI Phase A1: the foundation every later AI feature (OCR, translation, matching) will run on. It adds no AI feature
yet; it adds the zone the models run in, the registry that decides which model files may load, the memory rules, the
router that falls back from model to rules to a person, and the record of every decision.

Two rules hold throughout:

- **Complaint data never leaves AICTE.** The AI code makes no network call outside the deployment, the `ai` zone has
  no route out, and models are never downloaded at run time.
- **AI proposes, a person decides.** When no provider gives an answer that is valid and confident enough, the item
  goes to human review. Nothing the router returns is acted on without the existing officer approvals.

## Zones

| Zone | Internal | Who is on it |
|---|---|---|
| edge | no (published ports need it) | web, keycloak, mailpit (dev) |
| app | yes | backend, worker, web, keycloak, mailpit |
| data | yes | postgres, redis, backend, worker, scheduler, migrate, **ai-worker** |
| **ai** | yes | **ai-worker** (later: local model servers) |

The `ai-worker` (Compose service, same image as the backend) runs `celery -A app.ai.tasks:celery worker -Q ai --pool
solo`. It has its own queue and a single process. It is read-only, runs as uid 10001 with every capability dropped,
and has a memory limit of `SETHU_AI_WORKER_MEMORY` (default `3g`). It sets `HF_HUB_OFFLINE=1` and
`TRANSFORMERS_OFFLINE=1`. It is on `ai` and `data` only, because it needs Redis (its queue) and PostgreSQL
(provenance), and nothing else. It imports only the AI layer, the database session and the audit ledger, which keeps
it small while idle.

## Registry

`models/manifest.json` lists every model the AI layer may load:

```json
{"models": [{"name": "stub-echo", "version": "1", "task": "stub.echo", "license": "...",
             "sha256": "<file or folder digest>", "path": "stub-echo/stub.txt", "approx_memory_mb": 1}]}
```

The `models/` folder is mounted read-only into the ai-worker at `/models` (`SETHU_MODELS_DIR` on the host,
`SETHU_AI_MODELS_DIR` inside). `backend/app/ai/registry.py`:

- `verify()` recomputes the checksum before every load. A file is hashed as is; a folder is hashed over its files'
  relative paths and SHA-256s, sorted.
- A mismatch, a missing file, or a path that leaves the folder raises `ModelIntegrityError`, so that model is never
  loaded.
- At start the worker checks every model and logs each result (`model check`). The health screen shows them too.

`models/` is marked binary in `.gitattributes`, so a Windows checkout cannot change a checksum by converting line
endings. `stub-echo` is a few bytes used by the stub providers; it is not a model.

### Adding a model

Only on a machine with internet access, never inside a container. The script refuses to run in a container or with
`SETHU_ENVIRONMENT=prod`.

```powershell
python scripts/fetch_models.py add <name> <version> <task> "<license>" <memory_mb> <https-url> [<url> ...] --sha256 <publisher's sha256> [...]
python scripts/fetch_models.py check
```

`add` downloads each file (https only) into `models/<name>/<version>/`. It checks each file against the publisher's
SHA-256 when given (a mismatch deletes the file and records nothing), then writes the folder's digest to the
manifest. Copy `models/` to the AICTE host and restart `ai-worker`. Review the model's license before use.

## Memory

`backend/app/ai/memory.py` keeps **one model in memory at a time**:

- a model is loaded when a provider first asks for it;
- asking for a different model unloads the current one first;
- a model unused for `SETHU_AI_IDLE_UNLOAD_SECONDS` (default 300) is unloaded. The worker checks every 30 seconds.

The worker reports the loaded model, its version, its approximate size from the manifest, and the process's resident
memory.

## Routing

`router.run(session, principal, task, payload, subject_type=..., subject_id=...)` tries the task's providers in the
order of `SETHU_AI_ROUTES`, for example `{"stub.echo": ["stub-model", "stub-rules"]}`. The first provider is the
primary, the second the fallback, any later one the last resort. A provider falls through to the next when:

| Reason | Counts against its circuit |
|---|---|
| its circuit is open | (skipped) |
| `health()` is false or raises | yes |
| `run()` raises, or takes longer than `SETHU_AI_TIMEOUT_SECONDS` (30) | yes |
| `validate(output)` rejects the output | yes |
| confidence below `ai.<task>.min_confidence` in `sethu.app_settings` (default `SETHU_AI_DEFAULT_MIN_CONFIDENCE`, 0.5) | no |

**Circuit breaker.** After `SETHU_AI_CIRCUIT_FAILURES` (3) failures in a row, a provider's circuit opens for
`SETHU_AI_CIRCUIT_COOLDOWN_SECONDS` (60). After the cooldown, one trial call is let through ("half open"). A success
closes the circuit; a failure opens it again for a full cooldown.

When every provider falls through, the answer is `status: "human_review"` with no output.

**Providers** are plug-ins (`backend/app/ai/providers.py`) answering `health()`, `run(payload) -> Result(output,
confidence)` and `validate(output)`. A1 ships one stub class used as a pair:

- `stub-model` loads the `stub-echo` model through the registry and memory manager, with confidence 0.9;
- `stub-rules` is deterministic, with confidence 0.7.

Its `behaviour` argument makes it unhealthy, raise, run slowly or return invalid output, for tests and drills. A
provider that needs a model server names it in `SETHU_AI_ENDPOINTS` (provider: URL). Production refuses any URL that
is not a one-word service name, `localhost`, or a loopback or private address.

## Provenance

Every router call writes one row in `sethu.ai_runs` (migration 0014) and one `ai.run` entry in the hash-chained audit
log, in the caller's transaction:

| Column | Holds |
|---|---|
| `task`, `subject_type`, `subject_id` | what was asked, about what (for example a complaint's id) |
| `provider`, `model_name`, `model_version` | who answered (none for human review) |
| `path` | `primary`, `fallback` or `last_resort` (none for human review) |
| `confidence`, `latency_ms`, `status` | `ok` or `human_review` |
| `error` | why each earlier provider fell through, for example "primary stub-model: timed out after 30 s" |

Neither the row nor the audit entry holds the payload or the output.

`ai_runs` is append-only: there is no UPDATE or DELETE policy and no such grant. Writes come only from the worker
(system) and admin. Reads come from oversight, admin and auditor, and from anyone who may read the complaint the run
is about (Row-Level Security). `sethu.app_settings` holds the per-task minimum confidence: every role reads it, and
only admin and system write it.

## Health

`GET /api/v1/ai/health` (admin and oversight; the **AI health** screen) shows:

- whether the ai-worker is reporting (it publishes its state to Redis every 30 seconds);
- each model's checksum verdict;
- each task's providers with health and circuit state;
- the loaded model and memory;
- the queue depth;
- the last 24 hours' runs by path, including human review.

The path follows the API's existing `/api/v1` prefix.

## Offline guarantees and how they are checked

- **Production refuses to start** (`backend/app/core/config.py`) unless `HF_HUB_OFFLINE=1` and
  `TRANSFORMERS_OFFLINE=1`, and if any `SETHU_AI_ENDPOINTS` URL points outside the deployment. Tested in
  `tests/test_config.py`.
- **Egress canary** (`scripts/egress_canary.py`, CI job `egress-canary`) starts the stack and runs two checks:
  - it counts, at the Docker host's firewall, any new connection from the project's networks to a public address
    during two idle minutes;
  - it probes every container for a TCP route and a DNS answer from outside.

  It fails if an internal-only container (above all `ai-worker`) reaches anything, or if `ai-worker` is on a network
  with a route out. The edge containers (web, keycloak, mailpit) have a route by design: Docker publishes ports only
  from a non-internal network. They fail only with `--strict`, together with `loadtest/offline.sh on`.
- **Tests**: `tests/test_ai_registry.py`, `test_ai_router.py`, `test_ai_health.py`, `test_egress_canary.py`, and the
  AI cases in `test_config.py`.

## Not in A1 (some added in A2, below)

No OCR, translation or matching provider, and no screen that triggers an AI run. There is also no human-review queue
screen yet: human-review runs are recorded and counted on the health screen. Later phases add these on top of the
router.

## Phase A2: enrichment (language, OCR, translation, glossary)

### What happens to a complaint

A complaint can be worked on the moment it is filed. All intake paths go through `complaints.create`, which writes a
pending row in `sethu.complaint_enrichment` in the same transaction (an outbox). Adding an attachment marks the
complaint pending again. Every 10 seconds the scheduler queues `sethu.ai.enrich_pending` on the `ai` queue. The
ai-worker then takes up to 10 pending complaints and runs four steps through the A1 router, so provenance, circuit
breakers and confidence thresholds all apply:

| Step | Task | Primary | Fallback | Last resort |
|---|---|---|---|---|
| Language | `language.detect` | fastText lid.176 (`lid-176`) | Unicode script (no model) | `unknown` and a review item |
| Attachments | `ocr.read` | RapidOCR, PaddleOCR PP-OCRv5 models on ONNX Runtime (`rapidocr-<script>`) | Tesseract 5 (`tessdata-<lang>`) | `manual` ("needs manual entry") and a review item |
| Translation | `translate.to_en` | IndicTrans2 distilled 200M, CTranslate2 int8 (`indictrans2-indic-en-dist-200m`) | Glossary terms only (no translation) | `untranslated` and a review item |
| Tags | `glossary.tag` | Glossary normaliser | (none) | (none) |

- **English needs no translation**: `translation_path` is `not_needed`.
- **PDFs**: text a PDF carries is used as is (pypdf, `ocr_path` `embedded`). Only pages without trustworthy text are
  rendered (pypdfium2, 144 dpi) and read by OCR.
- **Limits**: `ai.ocr.max_pages` (10) and `ai.ocr.max_image_pixels` (25 million) in `sethu.app_settings`. Pillow's
  decompression-bomb guard is set to the same pixel limit.
- **Original text is never changed**: everything lands in `complaint_enrichment`, beside `complaints.body`
  (`tests/test_enrichment.py` checks the text and its hash before and after).
- **Repeated failure**: a complaint that fails 3 times goes to a person instead of looping.

**One model at a time.** The steps run stage by stage over the whole batch: all languages, then all attachments,
then all translations. So each model is loaded once per batch, and the memory manager's single slot never holds two
(`test_stages_run_in_order_so_only_one_model_is_needed_at_a_time`). Tesseract runs as a separate short-lived process
of about 44 MB.

**Human review.** `sethu.review_items` records each case where a step was unsure or failed: language, OCR or
translation, with the reason and the AI run. The **Review** screen lists them. Officers and heads of the holding
bureau, or an admin, mark each one resolved or dismissed, and that decision is audited. Oversight can read them.

### Settings (`sethu.app_settings`)

| Key | Default |
|---|---|
| `ai.language.detect.min_confidence` | 0.5 |
| `ai.ocr.read.min_confidence` | 0.6 |
| `ai.translate.to_en.min_confidence` | 0.5 |
| `ai.ocr.read.timeout_seconds` | 300 |
| `ai.translate.to_en.timeout_seconds` | 180 |
| `ai.ocr.max_pages` | 10 |
| `ai.ocr.max_image_pixels` | 25,000,000 |

The order of providers is `SETHU_AI_ROUTES`. For example, to make Tesseract the primary OCR engine (see the
measurements below), set `SETHU_AI_ROUTES` to the default value with `"ocr.read": ["tesseract", "rapidocr"]`.

### Language tiers (what is really supported)

Measured on this project's mock samples (`backend/tests/data/multilingual/`: rendered text, not real scans), in the
ai-worker image with no network:

| Tier | Languages | Language detection | OCR | Translation |
|---|---|---|---|---|
| 1: measured end to end except translation | Hindi, Marathi, Tamil, Telugu, English | fastText: correct on all samples | RapidOCR and Tesseract both read them (numbers below) | IndicTrans2 covers them; **not measured** (model not installed) |
| 2: OCR by Tesseract only | Kannada (Tesseract good), Bengali (**Tesseract poor**: character error rate 0.82), Gujarati, Malayalam, Punjabi, Odia, Assamese, Urdu, Nepali, Sanskrit | fastText has them (Kannada and Bengali measured correct) | no RapidOCR/PaddleOCR model exists for them; Tesseract language files exist (only Kannada and Bengali measured) | IndicTrans2 covers them; not measured |
| 3: script detection only | Bodo, Dogri, Kashmiri, Maithili, Manipuri, Santali, Konkani, Sindhi | fastText lid.176 lacks Bodo, Dogri, Kashmiri, Maithili, Manipuri and Santali: the script fallback narrows to the script's languages (Devanagari alone covers nine) | no dedicated model; Devanagari languages fall back to Hindi or Marathi files | IndicTrans2 covers all 22 (codes in `app/ai/translate.py`); not measured |

Romanised Hindi ("college ne fees refund nahi kiya") is recognised only as Latin script (English first). The
glossary's `hi-latn` terms still tag it.

### OCR engine: PaddlePaddle or ONNX Runtime (measured 2026-11-23)

Both engines ran in throwaway `python:3.12-slim` containers. Each language ran in a fresh process; peak memory is
VmHWM.

| | PaddleOCR 3 on PaddlePaddle 3.0.0 | RapidOCR 3.10 (PaddleOCR PP-OCRv5 models) on ONNX Runtime |
|---|---|---|
| Install size (site-packages growth) | 1,314 MB (PaddlePaddle alone: 822 MB) | 401 MB on a bare image. 324 MB on SETHU's image, which already has numpy and ONNX Runtime; this includes CTranslate2, SentencePiece, pypdf and pypdfium2 |
| Peak memory, one page | 704 to 820 MB (Hindi, Marathi, Tamil, Telugu) | 743 to 778 MB |
| Languages that ran | Hindi, Marathi (Devanagari), Tamil, Telugu | English, Devanagari, Tamil, Telugu (PP-OCRv5); Kannada exists only in PP-OCRv4, whose download failed |
| No model | Kannada, Bengali, Gujarati, Malayalam, Punjabi, Odia, Assamese | Bengali, Gujarati, Malayalam, Punjabi, Odia, Assamese, Kannada (v5) |
| Other | English crashed inside PaddlePaddle ("Type of attribute: strides"); Urdu's model could not be downloaded | |

**Chosen: RapidOCR on ONNX Runtime.** It installs about 1 GB less, uses the same memory, covers the same languages,
and its English works.

Then, in the ai-worker image, offline, on the rendered samples (character error rate, lower is better):

| Sample | RapidOCR (PP-OCRv5 mobile) | Tesseract 5.5 (tessdata_fast 4.1.0) |
|---|---|---|
| Hindi 1, Hindi 2 | 0.168, 0.241 | 0.000, 0.000 |
| Marathi | 0.155 | 0.000 |
| Tamil | 0.010 | 0.052 |
| Telugu | 0.307 | 0.000 |
| Kannada | no model | 0.012 |
| Bengali | no model | 0.818 |
| English | 0.000 | 0.000 |
| Time per image | 4 to 9 s | 0.3 to 0.6 s |
| Peak memory | 778 MB | about 44 MB (its own process) |

**What this means.** On clean printed text, Tesseract was more accurate, about ten times faster and far lighter.
RapidOCR's confidence stayed between 0.93 and 0.98 even with 30% of characters wrong, so its confidence cannot be
used to catch its errors. These samples are not real scans: photos and poor scans, where deep-learning OCR usually
does better, were not tested. The configured order follows the brief (RapidOCR first). Making Tesseract primary is a
one-line settings change and a decision for AICTE (docs/PRODUCTION-READINESS.md, row 63).

**fastText lid.176** named all 8 non-romanised samples correctly (Hindi, Marathi, Tamil, Telugu, Bengali, Kannada,
English). Each took about 1 ms after a 0.14 s load, at 80 MB peak.

**Embedded PDF text can be wrong.** A Hindi PDF made by Chrome, read with pypdf, gave vowel signs in visual order
("िमली" for "मिली") and NUL bytes for shaped glyphs. `app/ai/ocr.py` (`garbled()`) treats such a page as a scan and
reads it with OCR instead.

### Translation: IndicTrans2 (not installed here)

The provider follows the reference CTranslate2 path of AI4Bharat/IndicTrans2 at a pinned commit. The helpers are
vendored and reviewed (`backend/app/ai/vendor/indictrans2/README.md`), and no remote code runs. The model archive is
gated on Hugging Face (`ai4bharat/BPCC`, `additional/indic-en-dist.tar.gz`, which needs an account that accepted
AI4Bharat's terms). This machine got 401, so the model was **not installed, run or measured**. Until it is, every
non-English complaint gets the glossary fallback or `untranslated` and a review item, which the tests check.

To install it on a connected machine:

1. Download and unpack the archive.
2. Copy its CTranslate2 directory (with `model.bin`) and its `vocab/` folder into
   `models/indictrans2-indic-en-dist-200m/1/`.
3. Run `python scripts/fetch_models.py record indictrans2-indic-en-dist-200m 1 translate.to_en "MIT" 900`.
4. Run `tests/test_ai_models.py` in the ai-worker image.

### Glossary normalisation

`sethu.glossary_terms` holds terms with English tags. It is versioned and append-only, and the newest version is
used.

- **Starter list**: `seed/glossary.csv` has 144 terms: 78 in Hindi (Devanagari), 18 Hindi in Latin script, 23
  English variants, and 5 each in Tamil, Telugu, Kannada, Bengali and Marathi. Those 25 are marked "needs native
  review".
- **Matching**: Unicode NFC, case folded, zero-width joiners removed, longest match first, terms start at a word
  start. In Latin script a term must also end at a word end; Indic terms may take a suffix.
- **Output**: English tags and a coverage ratio.
- **Upload**: Admin > Glossary, CSV or XLSX. All-or-nothing, with a row-by-row error report, versioned and audited.

This is term normalisation, not translation, and the screens say so.

### Getting the models (connected machine only)

One command installs every small model SETHU uses (about 66.5 MB): fastText lid-176, RapidOCR PP-OCRv5 for English,
Devanagari (Hindi, Marathi), Tamil and Telugu, and Tesseract eng, hin, mar, tam, tel, kan, ben. Each file's SHA-256
is pinned in the script; a model already installed and intact is skipped, and a failure does not stop the rest. It
prints installed, skipped and failed, then the restart command (`docker compose restart ai-worker`). Not included:
IndicTrans2 (gated, below) and a RapidOCR Kannada model (PP-OCRv5 has none; Tesseract `kan` reads Kannada).

```powershell
python scripts/fetch_models.py small
```

Other languages, one model at a time:

```powershell
python scripts/fetch_models.py add lid-176 1 language.detect "CC-BY-SA-3.0 (fastText)" 5 https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz
$ms = "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv5"
foreach ($g in "devanagari", "ta", "te", "en") { python scripts/fetch_models.py add "rapidocr-$g" PP-OCRv5 ocr.read "Apache-2.0 (PaddleOCR models)" 200 "$ms/det/ch_PP-OCRv5_det_mobile.onnx" "$ms/rec/${g}_PP-OCRv5_rec_mobile.onnx" }
foreach ($l in "hin", "mar", "nep", "san", "tam", "tel", "kan", "mal", "ben", "asm", "guj", "pan", "ori", "urd", "eng") { python scripts/fetch_models.py add "tessdata-$l" 4.1.0-fast ocr.read "Apache-2.0 (tessdata_fast)" 60 "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/$l.traineddata" }
python scripts/fetch_models.py check
```

- **Size**: on 2026-11-23 these files (without IndicTrans2) came to 66.5 MB, and every one passed its checksum.
- **Placement**: copy `models/` to the host (`SETHU_MODELS_DIR`). The model files are git-ignored; the manifest is
  committed.
- **Publisher checksums**: give `--sha256` where a publisher lists one.

### Not done in A2

- IndicTrans2 not installed or measured: gated download.
- The whole A2 pipeline was not run inside the Compose stack on this machine: the demo stack already used the
  memory. The components were measured in the ai-worker image instead.
- Scans and photos were not tested, and no native speaker has reviewed the glossary or the samples.
- Matching, classification and graph work belong to later phases.
