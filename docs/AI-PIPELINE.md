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

## Not in A1

No OCR, translation or matching provider, and no screen that triggers an AI run. There is also no human-review queue
screen yet: human-review runs are recorded and counted on the health screen. Later phases add these on top of the
router.
