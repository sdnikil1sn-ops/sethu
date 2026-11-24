# Runbook

Commands are PowerShell, run from the project root (`E:\App\Project\SETHU`). Requires Docker Desktop and Python 3.12+.

## 1. First start

```powershell
python scripts/init_env.py
docker compose --profile dev up --build -d
docker compose ps
```

Expected: `postgres`, `redis`, `backend` healthy; `migrate` exited with code 0; `keycloak`, `worker`, `web`, `mailpit` running.

Check:

```powershell
curl.exe http://localhost:8080/health/ready      # {"status":"ok","database":"up"}
```

Open http://localhost:8080 (app), http://localhost:8080/auth (Keycloak), http://localhost:8025 (mail).

This full start has **not** been run yet. Likely first-run issues and where to look:

| Symptom | Look at |
|---|---|
| `postgres` unhealthy, log shows `\r: command not found` | `infra/postgres/init/01-roles.sh` was saved with Windows line endings; convert to LF, then reset (section 5) |
| `migrate` exits non-zero | `docker compose logs migrate` |
| `keycloak` restarts | `docker compose logs keycloak`; the realm file or the `KC_HOSTNAME` value |
| `web` exits with "host not found in upstream" | `keycloak` or `backend` was not up; `docker compose up -d web` again |
| `redis` restarts | `docker compose logs redis`; try removing `read_only` for that service |

## 2. Daily use

```powershell
docker compose --profile dev up -d
docker compose logs -f backend worker
docker compose down
```

### Scheduler

Scheduled jobs (alert delivery every 15 s, detectors every 5 min, the nightly chain check) are put on the queue by the `scheduler` service (Celery beat) and run by `worker`. Run exactly one scheduler; workers can be scaled (`up -d --scale worker=2`). A second scheduler cannot run: the first holds the Redis lock `sethu:beat:lock` (renewed every 20 s, expires 60 s after a scheduler dies), and another refuses to start while it is held (`another scheduler holds sethu:beat:lock`), keeps restarting as a standby, and takes over within a minute if the first one dies. Tests: `tests/test_scheduler.py` (needs a throwaway Redis, see the file).

## 3. Database

```powershell
# open a shell as the read-only auditor
docker compose exec postgres psql -U sethu_auditor -d sethu

# verify the audit chain
docker compose exec postgres psql -U sethu_auditor -d sethu -c "SELECT * FROM sethu.audit_verify();"

# new migration after changing the schema (creates a file in backend/alembic/versions)
cd backend; alembic revision -m "describe change"; cd ..
docker compose up --build migrate
```

### Demo logins (dev and demo only)

`docker compose --profile dev up` runs a one-shot `demo-users` service that creates six Keycloak users. They are the same people as in `seed/users.csv`, with the same ids, so what they do in the app is tied to their seeded history.

| Username | Person | Role | Bureau |
|---|---|---|---|
| `rao` | Ms. Anita Rao | officer | PGRC |
| `iyer` | Mr. Suresh Iyer | bureau_head | RB |
| `fernandes` | Ms. Maria Fernandes | bureau_head | PGRC |
| `menon` | Dr. Kavita Menon | oversight | none |
| `admin` | Ms. Asha Chopra | admin | none |
| `das` | Mr. Arun Das | auditor | none |

All six share the password in `DEMO_USER_PASSWORD` in `.env`. The repository holds only a placeholder (`infra/demo-users/users.json`). A `.env` created before this variable existed needs the line added by hand: 12 or more characters with upper case, lower case and a digit.

The production start (section 7) does not use the `dev` profile, so these users are never created there. Do not add users to `infra/keycloak/sethu-realm.json`: that file is shared with production.

### Re-importing the realm on an existing stack

Keycloak imports `infra/keycloak/sethu-realm.json` only when the `sethu` realm does not exist yet, so editing the file changes nothing on a stack that has already started.

Demo users only (new password in `.env`, or a user was changed or deleted). It also sets the web client's sign-out return address (`post.logout.redirect.uris` = `+`, the same addresses as sign-in), which an existing realm may lack. Safe to repeat; other users and all SETHU data are untouched:

```powershell
docker compose --profile dev run --rm demo-users
```

The whole realm (roles, client, token settings changed in the realm file). This empties Keycloak's own database and keeps the SETHU data. Every Keycloak user and session is lost; the demo users come back with the same ids:

```powershell
docker compose stop keycloak
docker compose exec postgres psql -U postgres -c "DROP DATABASE keycloak" -c "CREATE DATABASE keycloak OWNER keycloak"
docker compose --profile dev up -d keycloak demo-users
docker compose logs -f demo-users          # ends with "demo users imported"
```

### Alert mail (dev and demo)

A send that fails is tried again after 1, 2, 4, 8, 16, 32 minutes and then hourly (never more than an hour apart); after ten attempts (about 4 hours, so a relay that is down for an hour heals itself) the alert is `failed` and shows why on the Alerts screen (filter "Failed"). An admin, or a head of a bureau the alert concerns, presses Retry to put it back in the queue with a fresh set of attempts; the retry is in the audit log. Settings: `SETHU_ALERT_MAX_ATTEMPTS`, `SETHU_ALERT_RETRY_BASE_SECONDS`, `SETHU_ALERT_RETRY_MAX_SECONDS`.

In production mail must be encrypted: `SMTP_SECURITY=starttls` (usually port 587) or `tls` (usually 465). The relay's certificate and host name are always verified; for a relay with a private CA, mount the CA certificate into the backend and worker and set `SMTP_CA_FILE` to its path inside the container. The backend refuses to start with `SMTP_SECURITY=none`, with a username but no password, or with an `SMTP_CA_FILE` that does not exist.

Approved alerts are emailed within 15 seconds, one email per recipient, to Mailpit at http://localhost:8025 (the Alerts page links to it). An alert that could not be sent stays "Approved, queued to send" on the Alerts page with the error and is retried; check `docker compose logs worker` and that `mailpit` is running.

### Complainant details: keys

Complainant name, e-mail and phone are stored only encrypted (`complaints.complainant_enc`), with a key from a keyring file mounted into the backend and worker as a secret (`/run/secrets/complainant_keys`). The file is in `secrets/complainant_keys.json` (git-ignored; `SETHU_SECRETS_DIR` moves it). Only the officers and head of the bureau holding a case see the details; everyone else sees "withheld".

Create (dev: `python scripts/init_env.py` does it; production: once, on the server):

```powershell
python scripts/complainant_key.py new secrets/complainant_keys.json
```

On Linux the containers run as uid 10001, so give them the file and nobody else: `sudo chown 10001:10001 secrets/complainant_keys.json` and `chmod 600`.

Rotate (for example yearly, or at once if the file may have leaked):

```powershell
python scripts/complainant_key.py add secrets/complainant_keys.json        # new key, now active
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend worker
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec worker celery -A app.worker:celery call sethu.complainant.rotate_keys
python scripts/complainant_key.py show secrets/complainant_keys.json       # key ids only
```

The task re-encrypts every value onto the active key and writes a `complainant.rekeyed` audit entry per batch (counts and key ids only). When it has finished (`docker compose ... logs worker` shows `rekeyed`), and only then, drop the old key with `python scripts/complainant_key.py remove secrets/complainant_keys.json <old id>` and restart backend and worker. Keep a copy of the keyring apart from the database backups: a backup without its keyring cannot show who complained, and a backup with it is the data.

### Semantic overlap

**Since A3** (docs/AI-PIPELINE.md, "Phase A3"), Tier 2 matching is the AI task `match.complaints`, run through the router. Its stages:

1. E5 meaning similarity of the original texts, in any languages, at threshold `ai.match.complaints.e5_threshold` (0.88).
2. Trigram similarity at 0.30, for same-language pairs.
3. An officer.

It runs inside the same rules: same institution, same category, different bureaus, both open, filed within 30 days.

- **The suggestion**: each one shows the explanation and a matching confidence on the overlaps screen.
- **The vectors**: the ai-worker makes them (`sethu.ai.maintain`, resumable). The backend worker no longer embeds.
- **Old vectors**: the bge-small-en-v1.5 vectors from before A3 stay, labelled `BAAI/bge-small-en-v1.5` / `fastembed-0.9.1`, and are never compared with E5 vectors.
- **Off switch**: `SETHU_SEMANTIC_OVERLAP=false`, or no E5 model, gives exactly the trigram rule.
- **Measure**: `scripts/measure_a3.py` (offline, in the ai-worker image) prints precision and recall at every threshold. It replaces `app.modules.overlaps.measure`.

**History (2026-11-21, bge-small).** The English-only bge-small model scored the 7 seed pairs 0.77 to 0.91, with a threshold of 0.75. It did not compare Hindi text. Its weights are still baked into the backend image by `backend/fetch_model.py` (`models.lock.json`) but are no longer used. Removing them needs the lock files regenerated (readiness row 66 plan, or a later clean-up).

### Graph

**Look for new overlaps now** (Overlaps, admin) queues the worker's job and the screen waits for its answer; the embedding model is never loaded by the API.

**Graph** (every role) draws the whole network with Cytoscape.js, bundled into the web app (its own file, loaded when a graph is shown; nothing comes from a CDN). By default it is aggregated: one node per bureau and per institution, an edge per bureau and institution weighted by the cases it holds, and transfer edges between bureaus; so it stays small with thousands of complaints. Clicking an institution and **Show its complaints** adds its complaints as nodes, with overlap edges (dashed: suggested, solid: approved). A ring marks an institution with cases in several bureaus; a red halo an open finding. Filters: state, category, filed dates, bureau, finding kind. The side panel shows metadata; for a complaint it shows the text only if your bureau holds the case. The institution profile shows the same component for one institution, already expanded. Data: `GET /api/v1/graph` (summary view plus overlap links, transfers and findings under Row-Level Security: each role sees its share).

### Case workflow

- **Assign and reassign**: on a case's page, an officer or head of the bureau holding it chooses an active officer or head of that bureau. The case shows who has it; every assignment is in the history and the audit log (with the previous assignee). A transfer clears the assignee: the receiving bureau assigns its own people.
- **My cases** (officers and heads): open cases assigned to you, soonest deadline first. **Workload** (heads see their bureau; oversight and admin see all): open and overdue cases per person, and the unassigned ones.
- **Deadlines** (Admin > Deadlines by category): days to close a case, per category; a category without a setting uses `SETHU_SLA_DAYS` (21). They apply to cases filed or reopened afterwards; an open case keeps the deadline it was given.
- **Escalation**: the findings detector (every 5 minutes) makes a `deadline_escalation` finding for each open case past its deadline. The alert is a **digest**: one per bureau per run, to that bureau's heads, listing the cases that became late since the last digest and how many of its open cases are late in all (references and counts, never text), held for approval (Alerts). A run with no newly late case sends nothing. Closing the case resolves its finding; a reopened case that misses its new deadline is a new finding. On the demo data the first run makes one digest for PGRC and one for RB.
- **Notes** are read only by the officers and heads of the bureau holding the case (Row-Level Security); oversight, admin, auditors and a bureau that transferred the case away do not see them. The other history entries are unchanged.
- **Close** requires a reason (resolved, no action needed, duplicate, withdrawn, outside AICTE's jurisdiction). **Reopen** requires a reason, gives the case a fresh deadline from today, and keeps its assignee.

### Complaint intake

Complaints enter through **sources** (Intake screen, admin): each has a channel, the bureau it feeds, a priority and optionally a fallback source. The dev seed adds `pgrc-portal` (api, falls back to `pgrc-spool`), `rb-register` (api, falls back to `rb-spool`), and an `upload` and a `manual` source per bureau.

| Channel | Who | How |
|---|---|---|
| `api` | a portal system | `POST /api/v1/intake/submissions` with the source's API key, a timestamp and a one-time nonce (below) |
| `upload` | officer, bureau head | Intake screen > Upload a file: CSV or XLSX, up to 2 MB and 5,000 rows; bad rows are listed by row and field and can be downloaded as a CSV report |
| `manual` | officer, bureau head | Intake screen > Enter a complaint |
| `spool` | a portal, when its API is down | drop CSV or XLSX files into `SETHU_INTAKE_SPOOL_DIR/<source name>/` (default `./spool`, mounted into the worker at `/spool`); taken every 30 s, then moved to `processed/` (with `<file>.errors.csv` for refused rows) or `rejected/` (with `<file>.errors.txt`). Nothing is deleted |

Every channel writes the complaint to the intake queue first, encrypted with the complainant keyring. The worker (every 10 s) validates, refuses an exact duplicate (same bureau, typed institution and text), matches the institution (unmatched names go to the Unmatched names queue), flags a near duplicate (similar text, same institution, last 180 days) for the bureau to review, encrypts the complainant details and files the case (`IN-000001`, ...), recording the source and whether it came by the `primary` or `fallback` path.

**Failures are never dropped.** While a source is *marked down* (Intake screen, admin) its items wait; any failed attempt is retried after 1, 2, 4, 8, 16 minutes (`SETHU_INTAKE_RETRY_*`), and after `SETHU_INTAKE_MAX_ATTEMPTS` (6) the item becomes a dead letter with the reason. An admin presses **Retry** on the Intake screen's queue (Show: Dead letters). Each source's last success, failures in a row, queued and dead-lettered counts are on the Intake screen.

A source that is the fallback of a primary marked down is the stand-in: what it delivers is recorded as path `fallback`. When the primary is back, anything it held that the fallback already filed is recognised as a duplicate, not filed twice.

Sample file: `docs/samples/intake-sample.csv` (mock data). Columns: `institution_name`, `category`, `body` (required); `language` (`en` or `hi`), `filed_at` (date), `external_ref` (the portal's own id; a repeat from the same source is refused), `complainant_name`, `complainant_email`, `complainant_phone`.

**Intake API.** An admin issues the key (Intake screen > Sources > Issue API key); it is shown once and stored only as a hash. Every request carries `X-Sethu-Key`, `X-Sethu-Timestamp` (Unix seconds, within 5 minutes of the server clock) and `X-Sethu-Nonce` (16 to 128 characters, never reused: a replay is refused with 409). Sample call (dev stack):

```powershell
$headers = @{ "X-Sethu-Key" = "<key from the Intake screen>"; "X-Sethu-Timestamp" = [string][DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); "X-Sethu-Nonce" = [guid]::NewGuid().ToString("N") }
$body = @{ institution_name = "Greenfield Institute of Technology"; category = "Fee refund"; body = "The caution deposit of Rs 10000 has not been refunded four months after withdrawal."; external_ref = "PORTAL-0042"; complainant = @{ name = "Kavya Samplename"; email = "kavya.samplename@sethu.test" } } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/v1/intake/submissions -Headers $headers -ContentType application/json -Body $body
# -> id, status "queued", path "primary"
```

Each api source may make `SETHU_INTAKE_RATE_PER_MINUTE` (60) requests a minute, or its own number set on the Intake screen; beyond that the API answers 429 with `Retry-After: 60` and queues nothing. 401: unknown key, or a timestamp too old or in the future. 409: nonce reused, or the same complaint (or `external_ref`) already received from this source. 422: a field failed validation (the reply names the field, never repeats the value). The request never leaves the deployment: no step of intake makes an outbound call.

### Reports and exports

The Reports screen exports CSV. Each export is a `report.export` entry in the audit log (who, which report, date range, scope, row count): on the Audit log screen choose the action `report.*`, or run

```powershell
docker compose exec postgres psql -U sethu_auditor -d sethu -c "SELECT seq, ts, actor, entity_id, payload FROM sethu.audit_log WHERE action = 'report.export' ORDER BY seq DESC LIMIT 20;"
```

Exports hold counts and reference data only. Officers and bureau heads get their own bureau's figures; oversight, admin and auditor get every bureau.

### Findings (deadlocks and bottlenecks)

The worker checks transfers and queues every 5 minutes; an admin can also press **Check now** on the Findings screen. On the seeded data there is also one "Early warning: category spike" (Uttar Pradesh, Fee refund: 10 complaints in 30 days against a baseline of 2.67), which makes no alert. C-090 shows as "Bottleneck detected: transfer loop", with an alert waiting on the Alerts screen for a bureau head or oversight. Thresholds are environment variables read by the backend and worker: `SETHU_STALLED_TRANSFER_DAYS` (7), `SETHU_BOTTLENECK_MIN_OPEN` (3), `SETHU_BOTTLENECK_SHARE` (0.6), `SETHU_SPIKE_MIN_COUNT` (5), `SETHU_SPIKE_RATIO` (3.0). On freshly loaded seed data there are 4 bottleneck findings; the count grows as the seeded cases age, so reseed before a rehearsal. Changing one does not rewrite existing findings; the next run resolves those that no longer hold and adds new ones.

### Manual check of the screens (no browser tests)

The backend tests cover what each filter sends and returns. Before a demo, sign in as `rao` (PGRC officer) and check by eye:

1. Institutions: search `madurai`, `GIT`, `Greenfeild`, `Tamil Nadu`; each finds the same institutions as the top-bar search, with Cases, Open and Matched on. Clear the box: all 43 return.
2. Cases: set each filter in turn (unit, category, status, institution, state, dates, overdue, overlaps, text); the count drops and the address changes. Copy the address into a new tab: the same view opens. Press **Clear filters**, or follow the Cases link: the full list (310) returns.
3. Overlaps: Show and Bureau change the list; the Same institution table follows the bureau.
4. Alerts: each status shows only that status; All restores.
5. Audit log (sign in as `das`): action, actor, target type, target id, from, to, then **Clear**.
6. Reports: change dates on each report; a From after To shows an error; scope reads "your bureau only" for `rao`, "all bureaus" for `menon`.
7. Findings: kind, status and bureau filters; C-090 listed; the Meadowvale profile draws the loop in red; the dashboard shows the open findings count.

### Seeding the demo data

Load into an empty database only (after a first start or a reset, section 5). The files and the patterns they contain are described in `seed/README.md`.

```powershell
docker compose run --rm --no-deps -v "${PWD}/seed:/seed:ro" backend python /seed/load.py
```

The worker links misspelt institution names and suggests overlaps every 5 minutes. To have both at once after seeding:

```powershell
docker compose exec worker celery -A app.worker:celery call sethu.institutions.resolve_pending
docker compose exec worker celery -A app.worker:celery call sethu.overlaps.detect
docker compose exec worker celery -A app.worker:celery call sethu.findings.detect
```

Dates are relative to the moment of loading, so reset and reseed before each rehearsal. To change the data, edit `seed/generate.py`, run `python seed/generate.py` and commit the CSV files.

### Running backend tests

The tests need a real PostgreSQL and they **empty every table**, so use a throwaway stack, never one holding demo data.

```powershell
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d postgres migrate
cd backend
pip install -e ".[dev]"
$pw = (Get-Content ..\.env | Select-String "^SETHU_OWNER_PASSWORD=").ToString().Split("=",2)[1]
$ap = (Get-Content ..\.env | Select-String "^SETHU_APP_PASSWORD=").ToString().Split("=",2)[1]
$env:MIGRATION_DATABASE_URL = "postgresql+psycopg://sethu_owner:$pw@127.0.0.1:5432/sethu"
$env:SETHU_DATABASE_URL     = "postgresql+psycopg://sethu_app:$ap@127.0.0.1:5432/sethu"
$env:SETHU_TEST_DB_WIPE_OK  = "1"
pytest -q
```

Without those variables the database tests are skipped and only the token and API tests run.

The scheduler-lock tests (`tests/test_scheduler.py`) also need a throwaway Redis; without it they are skipped:

```powershell
docker run -d --rm --name sethu-test-redis -p 127.0.0.1:6390:6379 redis:7-alpine
$env:SETHU_TEST_REDIS_URL = "redis://127.0.0.1:6390/0"
```

FastAPI must be 0.165 or newer (`pyproject.toml`); an older one already installed fails the case-list tests with 422 "filters field required". `pip install -e ".[dev]"` upgrades it.

### Observability

**Logs.** Every service logs to stdout; Docker keeps them (`docker compose logs -f backend worker web`). The backend and worker write one JSON object per line: `ts`, `level`, `logger`, `msg`, `request_id`, and for requests `status` and `duration_ms`; the message names the route template (`GET /api/v1/cases/{complaint_id}`), never an id, a query value, complaint text, complainant details, a token or a password. The edge (nginx) writes JSON too, with the path but not its query string. One id ties a request together: nginx makes `$request_id`, passes it as `X-Request-ID`, the backend logs it and returns it; in the worker the id is the task id. Database errors never print statement values (`hide_parameters`). Central collection and retention are not set up (PRODUCTION-READINESS row 32): ship the Docker log files to the AICTE log store.

**Metrics.** `GET /metrics` on the backend's own port (`http://backend:8000/metrics`, internal network only; nginx answers 404, and the backend refuses any request that came through a proxy). Prometheus text format:

| Metric | Means |
|---|---|
| `sethu_http_requests_total{method,route,status}`, `sethu_http_request_duration_seconds` | requests and latency per route template (this backend process) |
| `sethu_intake_pending`, `sethu_intake_dead`, `sethu_intake_failures_in_a_row`, `sethu_intake_sources_down` | the intake queue, dead letters, consecutive failures, sources marked down |
| `sethu_alerts_pending_approval`, `sethu_alerts_queued`, `sethu_alerts_failed` | the alert outbox |
| `sethu_findings_open` | open findings |
| `sethu_job_last_run_timestamp_seconds{job}`, `sethu_job_last_success_timestamp_seconds{job}`, `sethu_job_failures_total{job}` | each scheduled job (`findings.detect`, `overlaps.detect`, `intake.process`, `alerts.deliver`, `audit.verify_chain`, ...) and `backup` (written by the backup service) |

A Prometheus server must run on the `app` network to scrape it (not part of this repository). To look by hand: `docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/metrics').read().decode())"`.

**Alert thresholds to set** (in Prometheus or whatever watches the metrics):

| Condition | Threshold | Why |
|---|---|---|
| backend `/health/ready` not 200 | 2 minutes | database unreachable |
| `time() - sethu_job_last_success_timestamp_seconds{job="alerts.deliver"}` | > 5 minutes | the worker or scheduler is down: no mail goes out |
| same for `findings.detect`, `overlaps.detect`, `intake.process` | > 20 minutes | detectors and intake stopped |
| same for `audit.verify_chain` | > 26 hours | the nightly chain check did not run |
| same for `backup` | > 26 hours | no backup in a day (the backup service also turns unhealthy) |
| `sethu_intake_dead` | > 0 | a complaint needs an admin's Retry |
| `sethu_intake_pending` | > 50 for 30 minutes | intake is stuck or a source is down |
| `sethu_intake_sources_down` | > 0 for 1 hour | a primary source has been down for an hour |
| `sethu_alerts_failed` | > 0 | an alert gave up: check the SMTP relay |
| `sethu_alerts_pending_approval` | > 20 | approvals are not keeping up |
| 5xx share of `sethu_http_requests_total` | > 2% over 10 minutes | errors |
| p95 of `sethu_http_request_duration_seconds` | > 2 s over 10 minutes | slow |
| failed sign-ins (below) | > 20 for one username or address in 10 minutes | password guessing (Keycloak also locks the account) |

**Sign-in events.** Both realms record login events (successes and failures, logouts, password changes; 90 days) and admin events (who changed what in Keycloak; without representations). Read them:

- **Audit log screen** (auditor, oversight, admin): *Failed sign-ins (from Keycloak)*, read-only. The backend asks Keycloak with the confidential client `sethu-events`, whose service account holds only `view-events`; its secret is `KEYCLOAK_EVENTS_SECRET` (dev `.env`, made by `python scripts/init_env.py`) or the secret file `keycloak_events_secret` (production). These are Keycloak's records, not entries of the hash-chained audit log.
- **Keycloak admin console**: realm *sethu* > *Events* (user events and admin events); in production through the SSH tunnel (section 7).
- **Keycloak's log**: the `jboss-logging` listener writes each event to the Keycloak container's log (`docker compose logs keycloak`).

A realm that already exists is not re-imported, so a stack created before Phase 4 needs the realm re-imported (Re-importing the realm, above) to get the events settings and the `sethu-events` client.

### Pinned dependencies

Everything that goes into an image is pinned, so a rebuild gives the same bits:

| What | Pinned in | Checked by |
|---|---|---|
| Python packages | `backend/requirements.lock` (runtime), `requirements-dev.lock` (tests, lint), `requirements-build.lock` (setuptools): exact versions with the SHA-256 of every published file | `pip install --require-hashes` in the Dockerfile and in CI |
| npm packages | `web/package-lock.json` (exact versions and integrity hashes) | `npm ci` |
| Base images | digests in `backend/Dockerfile`, `web/Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml` (`image: name:tag@sha256:...`) | Docker refuses a different image |
| Embedding model | `backend/models.lock.json` (revision and file hashes) | `backend/fetch_model.py` at build time |

Each image also applies its OS's security updates at build time (`apt-get upgrade`, `apk upgrade`, retried), because fixes are often released before the next base image; so two builds on different days can differ in OS patches only.

`pyproject.toml` keeps the allowed ranges and a few deliberate pins with the reason beside them (fastembed; Pillow at least 13, because older versions have known vulnerabilities; onnxruntime 1.19.2, because later builds bundle a telemetry client).

**Updating.**

- *A Python package*: change `backend/pyproject.toml`; resolve in a clean container and read back the versions, then write the locks from PyPI's published hashes (only small requests, retried):
  ```powershell
  docker run --rm -v "${PWD}/backend:/src:ro" python:3.12-slim sh -c "cp -r /src /b && cd /b && pip install -q . && pip freeze" > freeze.txt
  python scripts/lock_python.py freeze.txt dev-versions.txt    # dev-versions.txt: pytest, httpx, ruff and their deps, name==version
  ```
  Review the diff of the lock files, rebuild, run the tests and `pip-audit -r backend/requirements.lock`.
- *An npm package*: `cd web; npm install <name>@<version>`, commit `package.json` and `package-lock.json`, run `npm audit --audit-level=high` and `npm run build`.
- *A base image*: `docker pull <name>:<tag>`, then `docker image inspect --format "{{index .RepoDigests 0}}" <name>:<tag>`, and replace the digest everywhere it appears (search for the old one). Rebuild and scan (CI's Trivy step).
- *The model*: see Semantic overlap (new revision, new hashes in `models.lock.json`, re-measure).

### Continuous integration

`.github/workflows/ci.yml` runs on every push to `main` and every pull request: `ruff`; the backend tests against a throwaway PostgreSQL 16 with pgvector (made with the repo's own init script, passwords generated in the job) and Redis; the web build; a secret scan of the whole history (gitleaks, `.gitleaks.toml`); `pip-audit` on the runtime lock and `npm audit --audit-level=high`; the two images built and scanned with Trivy (fails on fixable HIGH or CRITICAL); and the Playwright journeys against a full dev stack with the demo data. No step uses a repository secret. Actions are pinned to commit SHAs (the tag each was taken from is in the comment beside it), and the gitleaks and Trivy images by digest. To move an action: read the commit behind the tag (`https://api.github.com/repos/<owner>/<action>/git/ref/tags/<tag>`; for an annotated tag, follow `object.url` to the commit), replace the SHA and the comment, and let CI run.

Checked locally on 2026-11-21: ruff clean; backend suite green; web build; gitleaks "no leaks found"; pip-audit "No known vulnerabilities found" (after moving to fastembed 0.9.1 and Pillow 13); npm audit 0 vulnerabilities (after moving to Vite 8); Trivy 0 HIGH and 0 CRITICAL fixable findings in both images (after nginx-unprivileged 1.29 and the build-time OS updates; before: 1 in the backend, 68 in the web image). The workflow itself has not run on GitHub yet.

### Browser tests

Playwright tests of the main journeys (`web/e2e/journeys.spec.ts`): every role signs in and sees its own menu; search by alias; approving an overlap queues an alert; a complaint sent to the intake API becomes a case (the admin issues the key on the Intake screen); a bureau head assigns and closes a case; a report runs and exports as CSV; Verify chain reports the chain intact. They change data, so run them against a freshly seeded dev stack:

```powershell
cd web
npm ci
npx playwright install chromium
$env:DEMO_USER_PASSWORD = "<DEMO_USER_PASSWORD from .env>"; $env:SETHU_URL = "http://localhost:8080"
npx playwright test
```

Run on 2026-11-21 against a freshly seeded dev stack: 7 passed.

`web/e2e/a11y.spec.ts` checks accessibility and layout. It runs axe (WCAG 2.1 A and AA) on every screen at 1366 and 375 px wide and fails on any serious or critical result, and fails if a page is wider than the screen. It also checks that the keyboard reaches the content with a visible focus ("Skip to main content" first), and that the phone layout of the case list is still a table to assistive technology. `$env:SETHU_SCREENS = "1"` also saves each screen to `docs/screens/<screen>-<width>.png`. Run on 2026-11-22 against a freshly seeded dev stack: 3 passed, then the 7 journeys passed on the same stack; 32 screenshots saved.

After the upgrade to Playwright 1.56.1 (2026-11-22, freshly seeded dev stack, run on the machine's installed Chrome through a local `channel: "chrome"` config while Playwright's own browser download kept failing on the network): all 10 tests passed (3 accessibility, 7 journeys). The overlap journey now waits for the worker's search, which is skipped while the scheduled one is still running.

### Audit-chain anchors

Every hour (minute 7) the worker appends one line to `audit-anchor.jsonl` in `SETHU_AUDIT_ANCHOR_DIR` (default `./anchor`, mounted read-write into the worker and read-only into the backend): the time, the latest entry number, its hash and the number of entries. The worker only ever opens the file for appending. Make the place write-once yourself: a WORM share, or on a Linux host `sudo chattr +a anchor/audit-anchor.jsonl` once the first line exists (root can still remove the flag, so copy the file off the host as well).

To prove the chain against it: the **Audit log** screen, *Exported anchors* (auditor, oversight, admin), or `docker compose exec backend python -m app.audit.anchor compare` (exit 1 on a mismatch). Every exported entry must still exist with the same hash; a rewritten entry, a truncated chain or a database restored from elsewhere is named. To export now: `docker compose exec worker python -m app.audit.anchor export`.

Drill (2026-11-22, dev stack): the database was replaced (`down -v`, fresh seed) while the anchor folder was kept. `compare` answered `ok: false` with "entry 1410 ... has a different hash now: it was rewritten" and "entry 1476 ... is missing: the chain was truncated or replaced".

### Edge and recreated containers

nginx looks the backend and Keycloak up by name through Docker's DNS every 10 seconds (`resolver 127.0.0.11 valid=10s` and a variable upstream), so recreating them (an upgrade, `up -d --force-recreate`) needs no restart of `web`. Drill (2026-11-21, dev stack): the backend's address was occupied by a placeholder container so the recreated backend had to take a new one (172.25.0.6 to 172.25.0.5); the edge answered the next API request within 5 seconds with the web container never restarted.

## 4. Backup and restore

In production the `backup` service (`docker-compose.prod.yml`, script `infra/backup/backup.sh`) backs up **both** databases, `sethu` and `keycloak`, once at start and then every `BACKUP_INTERVAL_HOURS` (default 24). Each is a `pg_dump` custom-format dump piped straight into `gpg` (AES-256, with an integrity check) under the passphrase in the `backup_key` secret; nothing unencrypted touches the disk. Files land in `SETHU_BACKUP_DIR` (default `./backups`, git-ignored) as `<stamp>-sethu.dump.gpg` and `<stamp>-keycloak.dump.gpg`; files older than `BACKUP_KEEP_DAYS` (default 14) are deleted. The service turns unhealthy when the last good backup is older than one interval plus an hour.

- **Copy the backups off this host** (AICTE storage) on your own schedule: a backup on the same disk does not survive the disk. They are encrypted, so the copy may sit on ordinary storage.
- **Keep `backup_key` apart from the backups** (with the other secrets, section 7). Without it the backups cannot be read; with both, anyone can.
- Restoring also needs `complainant_keys.json`: the complainant details inside the dump are encrypted with it.

```powershell
$C = "docker compose -f docker-compose.yml -f docker-compose.prod.yml"
Invoke-Expression "$C exec backup bash /backup.sh once"    # a backup now
Invoke-Expression "$C exec backup bash /backup.sh list"
```

### Restore

The script restores only into **empty** databases: the audit ledger is append-only, so it never merges into or drops a live one (it refuses and names the database). So a restore is: wipe the data volume, start PostgreSQL alone (its init script recreates the roles and empty databases from the secret files), restore, then start everything else. `migrate` then finds the schema already at the restored revision.

```powershell
$C = "docker compose -f docker-compose.yml -f docker-compose.prod.yml"
Invoke-Expression "$C exec backup bash /backup.sh counts sethu" > counts-before.txt   # if the old stack still runs
Invoke-Expression "$C down"
docker volume rm sethu_pgdata                                                           # DESTROYS the database
Invoke-Expression "$C up -d --wait postgres"
Invoke-Expression "$C run --rm backup restore <stamp>"     # both databases; ends with 'verify chain: ok=true checked=N'
Invoke-Expression "$C up -d"
Invoke-Expression "$C run --rm --no-deps backup counts sethu" > counts-after.txt
```

The restore must end with `verify chain: ok=true`; if it says `ok=false`, stop and treat the backup as suspect (SECURITY.md).

### Restore drill (2026-11-20, throwaway production-mode stack)

On a stack started from the base file plus `docker-compose.prod.yml`, with every password and key from secret files: the seed loaded (310 complaints, 1,013 case actions, 24 people); backend, worker and Keycloak stopped so nothing wrote during the backup; `backup.sh once` wrote both encrypted files (no `PGDMP` marker or plain text in them); row counts taken; the stack brought down and its `pgdata` volume **deleted**; PostgreSQL started alone; `backup.sh restore` restored both databases and printed `verify chain: ok=true checked=1438`. Counts after the restore were identical, table by table, to the counts before: all 11 tables in `sethu` (audit_log 1,438, complaints 310, case_actions 1,013, app_users 24, ...) and all 87 in `keycloak` (2 realms, the users). A second `restore` over the restored data was refused ("database sethu already has 11 tables"). Migrate then found nothing to do and the backend came up healthy on the restored data. Repeat the drill after any schema change and at least every quarter.

## 5. Reset everything (destroys data)

```powershell
docker compose --profile dev down -v
```

## 6. Demo day

1. The day before, while online: start the stack once so every image is built and pulled.
2. On the day: reset (section 5), start, and seed (section 3). Seed dates count back from the moment of loading, so data seeded the day before shows C-101 as 13 days old and the wrong number of overdue cases. Seeding needs no network.
3. Switch Wi-Fi off. `docker compose --profile dev up -d` must still work: every image is local and nothing calls out.
4. Run the script in `docs/03-DEMO-STORY.md` twice.

### Tamper demonstration

Shows that an edit made directly in the database, even by the owner with the append-only trigger switched off, is caught. Use it on demo data only.

1. Sign in as Mr. Das (auditor) or Dr. Menon (oversight), open **Audit log**, click **Verify chain**: "Chain intact, N entries".
2. Alter entry 5, as the database owner:

```powershell
docker compose exec postgres psql -U sethu_owner -d sethu -c "ALTER TABLE sethu.audit_log DISABLE TRIGGER audit_log_no_change; UPDATE sethu.audit_log SET payload = payload || jsonb_build_object('tampered', true) WHERE seq = 5; ALTER TABLE sethu.audit_log ENABLE TRIGGER audit_log_no_change;"
```

3. Click **Verify chain** again. The screen reports "Chain broken at entry #5: row content does not match its hash. The 4 entries before it are intact." and shows entry 5 as stored now, with `"tampered": true` in its payload.
4. Restore the row, which makes the chain verify again:

```powershell
docker compose exec postgres psql -U sethu_owner -d sethu -c "ALTER TABLE sethu.audit_log DISABLE TRIGGER audit_log_no_change; UPDATE sethu.audit_log SET payload = payload - 'tampered' WHERE seq = 5; ALTER TABLE sethu.audit_log ENABLE TRIGGER audit_log_no_change;"
```

Each `psql -c` runs its three statements in one transaction, so the trigger is never left off. Removing the key restores the payload exactly, so entry 5 matches its hash again; the two `audit.verify` entries the demonstration added stay in the log. If you changed anything else, reseed instead (section 5, then section 3). `backend/tests/test_audit_view.py` runs these exact statements.

## 7. Production

Production is the base file plus `docker-compose.prod.yml`. Never add `--profile dev` (it would change nothing: Mailpit and the demo-user import are switched off there, and both refuse production anyway). What is still missing before real complaints is in `docs/PRODUCTION-READINESS.md`.

### Start

1. Certificates: see TLS below (`python scripts/install_cert.py`).
2. Secrets: `python scripts/init_secrets.py` (see Secrets below). Then `.env` holds settings only, no passwords: `SETHU_ENVIRONMENT=prod`, `PUBLIC_BASE_URL=https://<host>`, `SETHU_SECRETS_DIR` (if not `./secrets`), `KEYCLOAK_ADMIN_USER`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY`, `SMTP_USERNAME` (if the relay needs a login), `ALERT_FROM`; and the password names left empty (`POSTGRES_SUPERUSER_PASSWORD=` and the others) so Compose does not warn about them.
3. Start:

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps   # every service healthy; migrate exited 0
```

If `backend` or `worker` keeps restarting, read why: `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend`. In production they refuse to start, naming each variable (never its value), when:

- `SETHU_DEBUG` is on;
- the password in the database or Redis URL is missing, shorter than 16 characters, or contains a placeholder or dev word (`CHANGE_ME`, `seedtest`, `password`, `postgres`, `secret`, `admin`, `sethu`, `demo`);
- the Keycloak issuer (`PUBLIC_BASE_URL`) is not `https`;
- `SMTP_HOST` is Mailpit, localhost or empty;
- `ALERT_FROM` is a `.test` address.

Compose itself stops before starting anything if `PUBLIC_BASE_URL`, `SMTP_HOST`, `SMTP_PORT` or `ALERT_FROM` is unset. The seed loader (`seed/load.py`) and the demo-user import refuse to run when `SETHU_ENVIRONMENT=prod`.

### Secrets

In production every password and key is a file in `SETHU_SECRETS_DIR` (default `./secrets`, git-ignored), mounted read-only under `/run/secrets` into only the containers that need it. None is in `.env`, an image or an environment variable; the backend refuses to start if its database or Redis URL, or `SMTP_PASSWORD`, carries a password instead.

```powershell
python scripts/init_secrets.py            # creates every missing file with a random value; never overwrites
```

On a Linux host: `sudo chown root:root secrets && sudo chmod 700 secrets` (the files themselves are 0644 so each container's own user can read the ones mounted into it; nobody else on the host can open the folder). Back the folder up apart from the database backups.

| File | Used by | Rotate |
|---|---|---|
| `postgres_superuser_password` | PostgreSQL, first start only | `python scripts/init_secrets.py rotate postgres_superuser_password`, then the printed `psql` command |
| `sethu_owner_password` | migrations | `rotate sethu_owner_password`, the printed `psql` command; used at the next `migrate` |
| `sethu_app_password` | backend, worker | `rotate sethu_app_password`, the printed `psql` command, `restart backend worker` (done on a production-mode stack: healthy again, `/health/ready` 200) |
| `sethu_auditor_password` | direct auditor logins | `rotate sethu_auditor_password`, the printed `psql` command |
| `keycloak_db_password` | Keycloak | `rotate keycloak_db_password`, the printed `psql` command, `restart keycloak` |
| `redis_password`, `redis_conf` | Redis; backend and worker | `rotate redis_password` (rewrites both), `restart redis backend worker` |
| `keycloak_admin_password` | Keycloak's bootstrap admin, first start only | create a named admin per person in the console, then delete the bootstrap user; the file is not read again |
| `smtp_password` | backend, worker (only if `SMTP_USERNAME` is set) | write the relay's new password into the file, `restart backend worker` |
| `backup_key` | backup service | write a new value (`python -c "import secrets; print(secrets.token_urlsafe(32))"` into the file), `restart backup`. Old backups stay readable only with the old value: keep it until they have aged out |
| `complainant_keys.json` | backend, worker | `python scripts/complainant_key.py add`, then re-encrypt (Complainant details: keys) |

The printed `psql` command pipes `infra/postgres/rotate_role.sql` into the postgres container, which reads the new value from its own mounted copy: the password never appears on a command line. `rotate` rewrites the file in place, so the containers see the new value at once.

There is no Keycloak client secret: `sethu-web` is a public client using PKCE, by design (a browser cannot keep a secret).

### TLS certificate

The edge serves the certificate in `SETHU_CERTS_DIR` (default `infra/certs`, git-ignored): `server.crt` (the server certificate first, then the intermediates) and `server.key`. The folder is mounted read-only into the web container, so installing or renewing a certificate needs no rebuild and no restart:

```powershell
python scripts/install_cert.py C:\path\to\fullchain.pem C:\path\to\private-key.pem
```

The script refuses a file that is not a PEM certificate or key, or a certificate that has expired; prints the certificate's names and expiry; writes both files in place (keeping the previous pair as `*.prev`); runs `nginx -t`; and reloads nginx only if it passes. If nginx rejects the pair (a key that does not match, a broken chain file) the previous pair is put back and nothing is reloaded. Tried on a production-mode stack (2026-11-20): a renewed certificate was served right after the reload, with the web container never restarted; then a key that did not match was refused (`key values mismatch`), the previous pair was put back and the renewed certificate stayed live.

- Get the certificate from the AICTE/NIC CA for the public host name in `PUBLIC_BASE_URL`. Never commit a certificate or key: `infra/certs/` is git-ignored.
- On a Linux host: `sudo chmod 700 infra/certs` (the key is 0644 so nginx's own user can read it inside the container; nobody else on the host can open the folder).
- Renew before expiry; put the expiry date in the operations calendar. Automatic renewal (ACME) needs a CA that offers it and outbound access: not set up.

### Published ports

| Port | Bound to | What |
|---|---|---|
| 443 | all interfaces | the web app, `/api`, and the sign-in pages of the `sethu` realm |
| 9443 | 127.0.0.1 on the host | Keycloak administration (admin console and `master` realm) |

Nothing else is published: PostgreSQL, Redis, Keycloak, the backend and the worker are on internal networks. The public port refuses `/auth/admin/` and `/auth/realms/master/`.

### Keycloak administration (SSH tunnel)

From an administrator's machine:

```powershell
ssh -L 9443:127.0.0.1:9443 <admin-user>@<host>
```

then open https://localhost:9443/auth/admin/ and sign in with `KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD`. The browser warns that the certificate is for the public host name; that is expected on the tunnel. Create a named administrator account for each person and disable the bootstrap one (PRODUCTION-READINESS row 20).

### The production realm

Keycloak imports `infra/keycloak-prod/sethu-realm.json` (not the dev realm) the first time it starts. It has no users. It sets: exact redirect and post-logout URIs from `PUBLIC_BASE_URL`; the `bureau_id` attribute (administrators may edit it, users may not) and its token mapper; brute-force detection (5 failures, waits up to 15 minutes); a password policy (12+ characters with upper, lower, digit and special character, not the username or e-mail, not one of the last 5); TLS for every request; access tokens of 5 minutes, sessions idle out after 30 minutes and end after 10 hours, single-use refresh tokens.

To add a person: in the admin console, realm `sethu` > Users > Add user (username, e-mail, first and last name), set a temporary password under Credentials, assign one realm role (`officer`, `bureau_head`, `oversight`, `admin` or `auditor`), and for `officer` and `bureau_head` add the attribute `bureau_id` = the bureau's id (`SELECT id, code FROM sethu.bureaus`). SETHU brings the person's record (`sethu.app_users`) in step with their token each time they sign in: name, e-mail, role and bureau. Alert mail goes to that e-mail, so give every bureau head one in Keycloak; Admin > People flags anyone without one, and an alert names any bureau it could not reach. Bureaus are created, renamed and deactivated on Admin > Bureaus (`admin` only); the bureau's id for the `bureau_id` attribute is shown in the API (`GET /api/v1/admin/bureaus`) and in `SELECT id, code FROM sethu.bureaus`.

Like the dev realm, the file is read only when the realm does not exist yet; a change to it reaches a running system only through the console or a full re-import (section 3).

### Configuration reference

| Variable | Used by | Dev | Production |
|---|---|---|---|
| `SETHU_ENVIRONMENT` | backend, worker, demo-user import, seed loader | `dev` | `prod` |
| `PUBLIC_BASE_URL` | Keycloak hostname and realm URIs, the backend's token issuer | `http://localhost:8080` | `https://<host>`, required |
| `POSTGRES_SUPERUSER_PASSWORD` | PostgreSQL bootstrap | random | empty: the secret file `postgres_superuser_password` |
| `SETHU_OWNER_PASSWORD` | migrations (`sethu_owner`) | random | empty: the secret file `sethu_owner_password` |
| `SETHU_APP_PASSWORD` | backend and worker (`sethu_app`) | random | empty: the secret file `sethu_app_password` |
| `SETHU_AUDITOR_PASSWORD` | direct read access for auditors | random | empty: the secret file `sethu_auditor_password` |
| `KEYCLOAK_DB_PASSWORD` | Keycloak's database | random | empty: the secret file `keycloak_db_password` |
| `REDIS_PASSWORD` | Redis, backend and worker | random | empty: the secret file `redis_password` (`redis_conf` too for Redis) |
| `KEYCLOAK_ADMIN_USER`, `KEYCLOAK_ADMIN_PASSWORD` | Keycloak bootstrap administrator | `sethu-admin`, random | change the name; disable after creating named admins |
| `DEMO_USER_PASSWORD` | demo-user import | set | not set (the import refuses production) |
| `SMTP_HOST`, `SMTP_PORT` | alert delivery | `mailpit`, `1025` | the relay, required; Mailpit refused |
| `SMTP_SECURITY` | alert delivery | `none` (Mailpit) | `starttls` or `tls`, required |
| `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_CA_FILE` | alert delivery | empty | as the relay needs; checked at start |
| `ALERT_FROM` | sender of alert mail | not used (default `sethu-alerts@sethu.test`) | required; not a `.test` address |
| `SETHU_DEBUG` | FastAPI debug pages | `false` | must be `false` |
| `SETHU_SECRETS_DIR` | where the secret files are (`complainant_keys.json`, ...) | `./secrets` | a directory readable by uid 10001 only |
| `SETHU_STALLED_TRANSFER_DAYS`, `SETHU_BOTTLENECK_MIN_OPEN`, `SETHU_BOTTLENECK_SHARE`, `SETHU_SPIKE_MIN_COUNT`, `SETHU_SPIKE_RATIO` | findings detector | 7, 3, 0.6, 5, 3.0 | same unless tuned |
