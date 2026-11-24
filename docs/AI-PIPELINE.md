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

One command installs every small model SETHU uses (about 202 MB): fastText lid-176, RapidOCR PP-OCRv5 for English,
Devanagari (Hindi, Marathi), Tamil and Telugu, Tesseract eng, hin, mar, tam, tel, kan, ben, and (A3)
multilingual-e5-small's int8 ONNX build with its tokenizer (135.4 MB of the total). Each file's SHA-256
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
- Matching and classification came in A3 (below); graph work belongs to a later phase.

## Phase A3: multilingual matching, institution resolution, classification

### The model: multilingual-e5-small

- **Licence**: MIT (the publisher's model card and repository metadata, `intfloat/multilingual-e5-small`), recorded
  in the manifest entry.
- **Route**: the publisher's own ONNX export, run on ONNX Runtime 1.19.2 with the `tokenizers` library. Both were
  already in the image (they came with fastembed), so A3 adds **no dependency**. No PyTorch, no
  sentence-transformers, no scikit-learn.
- **Build**: the int8 file `onnx/model_qint8_avx512_vnni.onnx` (118.3 MB) plus `tokenizer.json` (17.1 MB), pinned to
  revision `614241f`; registry version `614241f-int8`. Installed by `python scripts/fetch_models.py small`.
- **Why int8, not fp32**: same quality on every measure below (cross-lingual precision/recall within one pair of
  each other at every threshold), half the memory, twice the speed.

| Measured 2026-11-24, ai-worker image, `--network none`, i5-1155G7 | int8 (installed) | fp32 (470.3 MB) |
|---|---|---|
| Install size (model + tokenizer) | 135.4 MB | 487.4 MB |
| Load time (first use after the checksum check) | 3.8 s | 11.1 s |
| Process memory: before load / after load / peak while embedding | 58 / 475 / 544 MB | 59 / 807 / 891 MB |
| Latency per complaint (passage, batch of 16) | 7.1 ms | 14.4 ms |
| Latency per institution name (query) | 5.6 ms | 7.7 ms |

- **Idle ai-worker**, no model loaded: 94.7 MiB (`docker stats`). With E5 loaded it sits near 95 + 420 MB. The
  memory manager unloads it after `ai_idle_unload_seconds` (300 s) unused.
- **One model at a time**: E5 loads through the same memory manager as OCR and IndicTrans2, so it is never resident
  with either. The pipeline runs it last, after the translation stage.
- **Prefixes**: `passage: ` for complaint text, `query: ` for institution names (E5's advice for short symmetric
  texts). Vectors are mean-pooled and L2-normalised; 384 dimensions; text past 512 tokens is cut.
- **What is embedded**: the **original** complaint text (`sethu.complaints.body`), never the translation, so a
  translation error cannot affect matching. The text is never changed.
- **Unverified**: the int8 build targets AVX512-VNNI. This CPU has VNNI. On a CPU without it, run
  `scripts/measure_a3.py` before go-live. If precision drops, install the fp32 file as its own version (registry
  name `multilingual-e5-small`, version `614241f-fp32`, the same tokenizer). It needs 891 MB at peak.

### Vectors: labelled, never mixed

- **Labels**: `sethu.complaint_embeddings` carries `embedding_model` and `embedding_version`, and its key includes
  both.
- **Comparison**: matching joins on both, so vectors of different models or versions are never compared. A test
  proves it with identical bge vectors and different E5 ones.
- **Active version**: the setting `ai.embedding.active` names the version the ai-worker makes now. The ai-worker
  writes it, with an audit entry, when it first stores a vector of a new version.
- **Old bge-small vectors**: they keep their label (`BAAI/bge-small-en-v1.5`, version `fastembed-0.9.1`).
  Nothing reads them any more, and the backend worker no longer makes them.
- **Re-embed job** (`sethu.ai.maintain`, every 30 s on the ai queue; also *Re-embed now* on AI health):
  - It gives every complaint a vector of the installed version, newest first, in batches of
    `ai.embed.reembed_batch` (64).
  - Each batch is committed on its own. An interruption loses at most one batch, and the next run carries on (tested).
  - The same job keeps the registry's name vectors current: names, "name, district" and aliases in any script. They
    are computed once per version; labels removed from the registry lose theirs.
  - It also trains the first classifier when there is none.

### Complaint matching (task `match.complaints`)

**The chain**, inside the unchanged Tier 1 / Tier 2 rules (same institution and category, different bureaus, both
open, filed within 30 days):

1. **`e5-match`**: the cosine of the two complaints' vectors, computed by pgvector, in any languages. It is off with
   `SETHU_SEMANTIC_OVERLAP=false`, and does not apply when either complaint has no vector of the active version.
2. **`text-match`**: the pg_trgm similarity used before A3. It applies only when both texts are in the same
   language, because trigram cannot compare scripts.
3. **An officer**: when neither provider is confident, the pair is suggested, marked "an officer decides", only if
   a signal crossed its threshold.

**Confidence and settings**:

- **Confidence**: 0.5 at the threshold, rising to 1 at `confidence_span` (0.06) away from it.
- **Agreement**: when both signals exist and the texts share a language, agreement adds `agreement_bonus` (0.15) and
  disagreement takes off `disagreement_penalty` (0.25).
- **Router minimum**: `ai.match.complaints.min_confidence` (0.5).

**One judgement per change**: each pair is judged once per `match_key` (vector version, both thresholds, category,
institution). A detection run judges only new or changed pairs, and every judgement writes an `ai_runs` row.

**Evidence**: every suggestion stores it in `overlap_links.signals`:

- method, similarity, confidence and agreement;
- both scores and both thresholds;
- whether the two texts share a language;
- model and version;
- the shared institution and category;
- both complaint ids;
- the `ai_runs` row.

`reasons` is the sentence form. The overlaps screen shows both as an explanation with the matching confidence.

**Threshold**: `ai.match.complaints.e5_threshold = 0.88`. This was calibrated fresh for E5; the old 0.75 was for
bge-small and is gone.

| Labelled set | Pairs (same matter) | What it measures |
|---|---|---|
| Hand-written cross-lingual set (`backend/tests/data/a3/eval.json`): 12 complaints × English, Hindi, Tamil; two different matters per category | 90 same-category pairs (36) | cross-lingual recall; hard same-category negatives |
| Seed pairs inside the overlap rules | 7 (7) | the planted Tier 2 pairs |

Measured with `scripts/measure_a3.py` (int8). E5 alone:

| E5 threshold | 0.85 | 0.86 | 0.87 | **0.88** | 0.89 | 0.90 |
|---|---|---|---|---|---|---|
| Precision (cross-lingual set) | 0.750 | 0.783 | 0.854 | **0.917** | 0.938 | 1.000 |
| Recall (cross-lingual set) | 1.000 | 1.000 | 0.972 | **0.917** | 0.833 | 0.639 |

The full chain (E5, then trigram for same-language pairs, then the officer) at 0.88 measured precision 0.825 and
recall 0.917. All 3 misses were English–Tamil pairs. Of the 7 false suggestions, 6 were same-language pairs:

- Hindi–Hindi: 3;
- Tamil–Tamil: 3.

The chain makes 4 more false suggestions than E5 alone. Two Hindi or two Tamil complaints in one category share
enough function words to reach trigram 0.30. Where E5 was close to its threshold, trigram either confirmed a
borderline E5 match or overrode a borderline E5 "no".

A per-language trigram threshold would help; it is not built (parking lot).

**Trigram alone at 0.30**, for comparison:

- **Cross-lingual set**: precision 0, recall 0 (it cannot match across scripts).
- **Seed**: all 7 seed pairs are within the rules, and E5 scores them 0.916–0.959, all above 0.88. The seed has no
  negative pair inside the rules, so it can show recall (7/7) but not precision.

**Weaker languages**: English↔Tamil is the weakest pair:

- **True pairs**: they score lowest (minimum 0.857, mean 0.889). Hindi↔Tamil has a minimum of 0.897 and a mean of
  0.949, and English↔Hindi a minimum of 0.890 and a mean of 0.908.
- **Misses**: at 0.88, 3 of the 12 English–Tamil pairs are missed.
- **Negatives**: different matters in the same category score up to 0.874 in English, 0.897 in Hindi and 0.890 in
  Tamil. Same-language false matches are therefore the main precision risk in Hindi and Tamil.
- **Not measured**: Telugu, Kannada, Marathi, Bengali and the other scheduled languages. Do not present cross-lingual
  matching as equally good across all 22 languages.

### Institution resolution (task `institution.resolve`)

**The cascade**:

1. Permanent id; then the exact name, alias or abbreviation (deterministic, as before).
2. **`institution-e5`**: the typed name against every registry name and alias by cosine. Regional-script aliases
   count the same as any other.
3. **`institution-fuzzy`**: the alias dictionary and spelling ratio, as before.
4. The officer queue.

**Rules**:

- An acronym ("GIT Pune") is never linked automatically.
- A link needs the top score at or above `ai.institution.resolve.e5_threshold` (0.93) and ahead of the next
  institution by `e5_margin` (0.03). For the fuzzy step these are `fuzzy_threshold` 95 and `fuzzy_margin` 5.
- Anything else goes to the queue with the top 3 candidates and their scores (E5 first), plus a review item.
- The backend worker's deterministic run (every 5 min) is unchanged. The ai-worker adds the E5 step for what is
  left.

Measured on the seed registry (43 institutions, 89 names and aliases) with 53 typed names from `eval.json`:

| Typed name | n | E5 top-1 | E5 top-3 | Spelling top-1 | Linked automatically at 0.93 / 0.03 |
|---|---|---|---|---|---|
| Misspelt ("Rivertn College of Engg Chennai") | 15 | 15 | 15 | 14 | 14 (0 wrong) |
| Reworded ("Ashmere Engineering College Jaipur") | 11 | 11 | 11 | 11 | 11 (1 by the exact step) |
| Regional script (Devanagari, Tamil; transliterated or translated) | 19 | 19 | 19 | 2 | 2 |
| Acronym ("NIT Coimbatore") | 4 | 1 | 4 | 4 | 0 (rule) |
| Not in the registry ("Sunrise Institute of Technology, Pune") | 4 | – | – | – | 0 |

- **Overall**: 27 of 53 were linked automatically, all correctly. 26 went to the queue: 22 with the right
  institution in the top 3, and the 4 unknown names (correctly not linked).
- **Regional-script names**: E5 ranked the right institution first for all 19, but only 2 cleared 0.93 (scores
  0.852–0.932). They go to an officer with the answer at the top of the list. Lowering the threshold to 0.88 would
  have linked 12 of them with no error on this set.
- **Why the margin matters**: an unknown name scored 0.928. At a 0.01–0.02 margin it was linked wrongly.

**What this cannot prove**:

- The seed names are invented and few: 43 institutions, about 6 share a pattern like "X Institute of Technology".
- AICTE's register has about 9,000 institutions, many with near-identical names in one city.
- The regional-script names were written by us, not by complainants, and no native speaker checked them.
- The thresholds rest on 4 unknown names. Watch the queue, and the auto-link audit entries, in the first weeks.

### Classification (task `classify.category`)

**The chain**:

1. **`category-e5`**: the complaint's E5 vector and logistic regression.
2. **`category-rules`**: English keywords and the A2 glossary's English tags, per category. Its confidence is
   top / (top + second + 1), so two clear hits are needed.
3. **An officer**: the suggestion is "an officer picks", with a review item.

**Settings and data**:

- **Minimum confidence**: `ai.classify.category.min_confidence` (0.6).
- **Implementation**: numpy logistic regression, no scikit-learn (about 100 MB of image for one small model).
- **Calibration**: probabilities are calibrated with one temperature fitted on the held-out set.
- **Bootstrap set**: `backend/app/ai/data/category_bootstrap.jsonl`, written by
  `scripts/make_category_bootstrap.py`. It holds 330 examples: 305 seed complaints and 25 glossary category terms in
  their own languages.
- **Held-out set**: a fixed fifth, chosen by text hash. It is never trained on and is the same for every version.

**Artifact**:

- **Format**: a JSON document of fixed shape, `sethu-logreg-json-1`, about 39 KB. It is stored in
  `sethu.classifier_versions` with its SHA-256.
- **Load checks**: anything else is refused, including bytes (a pickle), another format, a wrong checksum, extra
  fields, wrong shapes or a non-finite number.
- **Immutable**: the application role cannot update the artifact column.

| Measured (int8) | Result |
|---|---|
| Held-out seed set (71 examples) | 97.2% accuracy |
| Hand-written set, model alone | English 10/12, Hindi 10/12, Tamil 9/12 (29/36 = 81%); mean confidence 0.83 / 0.78 / 0.73 |
| Hand-written set, rules alone | English 12/12, Hindi 6/12 (5 no answer), Tamil 2/12 (10 no answer) |
| Hand-written set, the whole chain at 0.6 | 31 of 36 answered, 28 correct (90%); 5 to an officer (Hindi 2, Tamil 3) |
| Training time | 0.3 s |

- **The seed figure is not real-world accuracy.** The seed complaints come from two English templates per category
  and one Hindi template, so held-out examples are near-copies of training ones.
- **The hand-written figure** is closer to real text, but there are only 36 sentences, written by us.
- **Errors seen**:
  - Fee refund ↔ Scholarship delay: a scholarship that should have paid the fees.
  - Infrastructure → Ragging: a hostel complaint, in all three languages.

### Officer feedback and retraining

**Feedback**: every Accept, Change, keep-current (reject) or overlap decision writes one row to `sethu.ai_feedback`
(who, when, suggested, path, old value, new value) and an `ai.feedback` audit entry, in the same transaction.

- **Append-only**: the application role has no UPDATE or DELETE grant (tested).
- **Visibility**: rows are visible where the complaint is.

**Retraining**: an admin presses *Retrain classifier* on AI health (`POST /api/v1/ai/classifier/retrain`).

1. The ai-worker trains a new version from the bootstrap set plus officers' latest accepted or changed category for
   each complaint.
2. It evaluates the new version on the same held-out set.
3. It activates the new version only if its accuracy is not lower than the active one's. Otherwise the version is
   stored as `rejected`.

Earlier versions stay. An admin can roll back to any inactive one (*Use vN*); a rejected one cannot be used. Every
step is audited: `classifier.trained`, `classifier.activated` and `classifier.retrain_requested`.

**AI health** shows the active version, its held-out accuracy (with the warning above), the version list, and how
many complaints have a vector of the active E5 version.

### Screens

- **Overlaps**: each suggestion shows the explanation (method, matching confidence, both similarities against their
  thresholds, agreement, model version).
- **Case page**: an "AI suggestions" panel shows the suggested category (with other possibilities) and institution
  (top 3 with scores). Each shows the path that produced it: the AI model, the fallback rules, or an officer.
  Accept and Change appear for the holding bureau.
- **Review**: new kinds, Category and Institution, linking to the case page and the resolution queue.

### Settings added (`sethu.app_settings`, migration 0016)

`ai.match.complaints.` `min_confidence` 0.5, `e5_threshold` 0.88, `trigram_threshold` 0.30, `confidence_span`
0.06, `agreement_bonus` 0.15, `disagreement_penalty` 0.25. `ai.institution.resolve.` `min_confidence` 0.5,
`e5_threshold` 0.93, `e5_margin` 0.03, `fuzzy_threshold` 95, `fuzzy_margin` 5. `ai.classify.category.min_confidence`
0.6. `ai.embed.text.timeout_seconds` 120. `ai.embed.reembed_batch` 64. `ai.embedding.active` is written by the
ai-worker.

### Reproducing the numbers

```powershell
docker run --rm --network none -m 3g -e PYTHONPATH=/w/backend -e SETHU_ENVIRONMENT=test -e SETHU_OIDC_ISSUER=http://x/r -e SETHU_OIDC_JWKS_URL=http://x/c -e SETHU_DATABASE_URL=postgresql+psycopg://u:p@x/y -v "${PWD}:/w:ro" -v "${PWD}\models\multilingual-e5-small\614241f-int8:/e5:ro" sethu-ai-worker python /w/scripts/measure_a3.py /e5
```

The optional test `backend/tests/test_ai_models_a3.py` (marker `real_models`) asserts floors with the installed
model. It passed in the ai-worker image:

- **Matching** at 0.88: P 0.917, R 0.917.
- **Resolution top-1**: misspelt 15/15, regional 19/19.
- **Classification**: held-out 97.2%; hand-written 29/36.
- **Peak memory**: 544 MB.

### Not verified in A3

- **The full stack on 8 GB**: the A3 pipeline was not run inside a freshly started stack with all its services.
  The components were measured in the ai-worker image, and the stack stayed the one already running. The memory
  budget above comes from those measurements.
- **The int8 build on a CPU without AVX512-VNNI** (see above).
- **Real complaints and the real institution register**: every figure here is on synthetic data, and no native
  speaker reviewed the Hindi or Tamil sentences.
- **Languages other than English, Hindi and Tamil**: cross-lingual matching was not measured for them.
- **Larger data**: re-embedding and resolution at the size of AICTE's data. Each batch is small, and pgvector
  scans without an index at this size.
