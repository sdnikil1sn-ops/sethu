# Operations guide

For whoever installs and runs SETHU. Each section says what to do and points to the exact commands in
[RUNBOOK.md](RUNBOOK.md); what is not yet ready for real complaints is in [PRODUCTION-READINESS.md](PRODUCTION-READINESS.md)
(rows marked Open). Commands are PowerShell, run from the repository root.

## 1. What runs

One Docker host, one Compose project. Production is `docker-compose.yml` plus `docker-compose.prod.yml`.

| Service | Job | Network |
|---|---|---|
| `web` (nginx) | The only published service: the app, `/api`, the sign-in pages; TLS on 443; Keycloak administration on 127.0.0.1:9443 | edge, app |
| `backend` (FastAPI) | The API; every query through Row-Level Security | app, data |
| `worker`, `scheduler` (Celery) | Detectors, intake processing, alert mail, chain check, anchors; one scheduler at a time (it holds a lock) | app, data |
| `ai-worker` (Celery, queue `ai`, one process) | The AI layer: model registry, router, provenance (docs/AI-PIPELINE.md); models from the read-only `models/` folder | ai, data |
| `keycloak` | Sign-in (OIDC with PKCE), roles | edge, data |
| `postgres` (16, pgvector) | The `sethu` and `keycloak` databases | data |
| `redis` | Job queue | data |
| `migrate` | Applies schema migrations, then exits | data |
| `backup` (production only) | Encrypted dumps of both databases | data |

The `app`, `data` and `ai` networks are internal: nothing on them can reach the internet. No service calls an outside API,
model hub or CDN at run time.

## 2. Install

Needs a Linux host with Docker Engine and Compose v2; at least 8 GB of RAM (the containers' memory limits add up to
about 5.4 GB; the 100,000-complaint load test needs a 16 GB machine, docs/LOAD-AND-DRILLS.md); a host name and a
certificate from the AICTE/NIC CA; and an SMTP relay.

1. Copy the repository to the host (no `git` access is needed at run time).
2. `python scripts/init_env.py` creates `.env`; set the production values in it (section 3).
3. `python scripts/init_secrets.py` creates every secret file with a random value (RUNBOOK section 7, "Secrets").
4. `python scripts/install_cert.py <fullchain.pem> <key.pem>` (RUNBOOK, "TLS certificate").
5. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`, then `... ps`: every service healthy,
   `migrate` exited 0. If `backend` or `worker` restarts, its log names each unsafe setting (RUNBOOK, "Start").

## 3. Configuration reference

Settings are environment variables in `.env`; passwords and keys are files in `SETHU_SECRETS_DIR`, never variables.
The full table, with dev and production values, is RUNBOOK section 7, "Configuration reference". The settings an
operator is most likely to change:

| Setting | Default | Meaning |
|---|---|---|
| `PUBLIC_BASE_URL` | none (required) | `https://<host>`; also the token issuer |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY`, `SMTP_USERNAME`, `SMTP_CA_FILE`, `ALERT_FROM` | none (required) | The relay; TLS always verifies its certificate |
| `SETHU_ALERT_MAX_ATTEMPTS`, `SETHU_ALERT_RETRY_BASE_SECONDS`, `SETHU_ALERT_RETRY_MAX_SECONDS` | 10, 60, 3600 | Alert retries: 1, 2, 4 ... minutes, at most hourly, about 4 hours in all; then `failed` with the reason |
| `SETHU_SLA_DAYS` | 21 | Default days to respond (per-category deadlines are set on Admin > Deadlines) |
| `SETHU_INTAKE_RATE_PER_MINUTE`, `SETHU_INTAKE_CLOCK_SKEW_SECONDS` | 60, 300 | Intake API quota per source (a source can set its own) and allowed clock difference |
| `SETHU_INTAKE_MAX_UPLOAD_BYTES`, `SETHU_INTAKE_MAX_ROWS`, `SETHU_INTAKE_MAX_XLSX_EXPANDED_BYTES` | 2,000,000; 5,000; 20,000,000 | Limits on uploaded and spooled files |
| `SETHU_INTAKE_SPOOL_DIR` (host folder) | `./spool` | The fallback channel's folder (one subfolder per spool source), mounted into the worker |
| `SETHU_AUDIT_ANCHOR_DIR` (host folder) | `./anchor` | Where the hourly audit-chain anchors go; make it write-once (section 8) |
| `SETHU_SEMANTIC_OVERLAP` | true | Meaning-based overlap signal (A3: E5 vectors made by the ai-worker); off means trigram only. Its threshold is the setting `ai.match.complaints.e5_threshold` (0.88), no longer an environment variable |
| `SETHU_DETECT_BATCH` | 500 | New findings or overlap links written per transaction (keeps the audit lock short) |
| `SETHU_STALLED_TRANSFER_DAYS`, `SETHU_BOTTLENECK_MIN_OPEN`, `SETHU_BOTTLENECK_SHARE`, `SETHU_SPIKE_MIN_COUNT`, `SETHU_SPIKE_RATIO` | 7, 3, 0.6, 5, 3.0 | Detector rules |
| `BACKUP_INTERVAL_HOURS`, `BACKUP_KEEP_DAYS`, `SETHU_BACKUP_DIR` | 24, 14, `./backups` | Backups (section 6) |
| `SETHU_MODELS_DIR` (host folder), `SETHU_AI_WORKER_MEMORY` | `./models`, `3g` | The AI models (read-only, checked against `models/manifest.json`) and the ai-worker's memory limit |
| `SETHU_AI_IDLE_UNLOAD_SECONDS`, `SETHU_AI_TIMEOUT_SECONDS`, `SETHU_AI_CIRCUIT_FAILURES`, `SETHU_AI_CIRCUIT_COOLDOWN_SECONDS` | 300, 30, 3, 60 | Unload an unused model; a provider's time limit; failures that open its circuit, and for how long |
| `SETHU_AI_ROUTES`, `SETHU_AI_ENDPOINTS` | stub pair, none | Providers per task, in order; model-server URLs inside the `ai` zone (production refuses any other address) |
| `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE` | `1` (set in the image) | Production refuses to start unless both are `1` |
| `ai.<task>.min_confidence` (row in `sethu.app_settings`) | 0.5 | Below this an answer falls through to the next provider |

CPU limits are not set by default because they depend on the host. On a shared host add, in an override file,
`deploy.resources.limits.cpus` for `ai-worker` (the AI models are the heaviest users) and `postgres`.

### AI models (A2)

The ai-worker reads models only from `SETHU_MODELS_DIR` (read-only, checked against `models/manifest.json`). Fetch
them on a machine with internet access and copy the folder to the host: the commands and sizes are in
docs/AI-PIPELINE.md, "Getting the models". Without them every AI step falls back (Unicode script for the language,
the glossary for translation, a person for OCR) and nothing breaks. The thresholds and limits are rows in
`sethu.app_settings` (docs/AI-PIPELINE.md, "Settings"); the image's AI packages are pinned in
`backend/requirements-ai.lock` (`python scripts/lock_python.py --ai <freeze>` to update).

### Matching, classification and resolution models (A3): re-embed, retrain, roll back

The jobs:

- **Install or upgrade E5**:
  1. `python scripts/fetch_models.py small` on a connected machine. It adds `multilingual-e5-small` 614241f-int8,
     135 MB.
  2. Copy `models/` to the host.
  3. `docker compose restart ai-worker`.
  4. Within a minute **AI health** lists the model as "Matches the manifest". Complaint vectors then start to fill
     in (the *Complaint vectors* line).
- **Re-embed**: automatic. The `sethu.ai.maintain` job (every 30 s, ai queue) embeds complaints that have no vector of
  the installed version, in batches of `ai.embed.reembed_batch` (64), newest first. It also embeds the registry's
  names and aliases.
  - **Interruptions**: each batch is committed on its own, so a restart or a crash loses at most one batch. The next
    tick carries on.
  - **Run it now**: *Re-embed now* on AI health.
  - **Measured speed**: about 7 ms per complaint, so 100,000 complaints take about 12 minutes of ai-worker time.
  - **During a model upgrade**: pairs not yet re-embedded are matched by text similarity. Vectors of different
    versions are never compared.
- **Retrain the classifier**: AI health > *Retrain classifier* (admin). The ai-worker trains on the bootstrap set
  plus officers' accepted or changed categories.
  - It activates the new version only if it does no worse on the fixed held-out set; otherwise the version is listed
    as "not used (did worse)".
  - A first version is trained automatically when E5 is installed and there is none.
  - Retrain after a batch of officer corrections, or after an E5 upgrade. A classifier trained on another E5 version
    is not used: classification falls back to the rules until a retrain.
- **Roll back**: AI health > *Use vN* on an earlier version that is not marked "did worse" (admin). It is checked
  against its SHA-256 before it is used, and audited (`classifier.activated`).
- **Thresholds**: `ai.match.complaints.e5_threshold` (0.88), `ai.institution.resolve.e5_threshold` (0.93) and
  `e5_margin` (0.03), `ai.classify.category.min_confidence` (0.6), with their measured effect in
  docs/AI-PIPELINE.md, A3.
  - **Matching**: changing a matching threshold makes the next detection run judge every pair again. That writes one
    `ai_runs` row per pair.
  - **Institutions**: watch the resolution queue and the `institution.resolve` audit entries with step `e5` in the
    first weeks. The institution thresholds were measured on synthetic names only.
- **Without E5**: everything keeps working. Matching is trigram only, institutions use the spelling cascade, and
  categories use the keyword and glossary rules or an officer.

## 4. First-time setup (after the first start)

1. **Keycloak administrators**: through the SSH tunnel (RUNBOOK, "Keycloak administration"), create a named
   administrator account per person, then disable the bootstrap account (readiness row 20).
2. **Second factor** for `admin` and `oversight` in the production realm (readiness row 18, an AICTE decision).
3. **Bureaus**: Admin > Bureaus (the seed bureaus are not loaded in production). Each bureau's id: `GET /api/v1/admin/bureaus` or `SELECT id, code FROM sethu.bureaus`.
4. **People**: Keycloak realm `sethu` > Users: one role each; `bureau_id` for officers and bureau heads; an e-mail for
   every bureau head (alerts go there). Admin > People flags anyone without one.
5. **Deadlines** per category: Admin > Deadlines by category.
6. **Intake sources**: Intake > Sources: one per portal or channel, with its fallback; issue an API key for each API
   source and hand it to the portal over a secure channel (it is shown once). Docs: [API.md](API.md).
7. **Anchors**: once the first `audit-anchor.jsonl` line exists, make the file append-only (section 8).
8. **AI models**: copy the `models/` folder prepared on a connected machine (`scripts/fetch_models.py`, docs/AI-PIPELINE.md) to the host; the ai-worker logs `model check` per model at start and the **AI health** screen shows each verdict.
9. **Check**: sign in with each role; Audit log > Verify chain says intact; the backup service is healthy; AI health says the worker is reporting.

## 5. Upgrade

1. Read the release notes and `docs/PRODUCTION-READINESS.md` for anything new.
2. Take a backup now: `docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backup bash /backup.sh once`,
   and copy it off the host.
3. Copy the new repository version over the old one (keep `.env`, `secrets/`, `infra/certs/`, `backups/`, `anchor/`,
   `spool/`; they are git-ignored).
4. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`. `migrate` applies new migrations
   before the backend and worker start; nginx finds the recreated containers by itself (RUNBOOK, "Edge and recreated
   containers").
5. Check: every service healthy; Audit log > Verify chain intact; *Exported anchors* all match; sign in.
6. **Going back**: migrations are not written to be reversed. To go back, restore the backup from step 2 into an empty
   database with the old version (section 6). Do not run an older version against a newer schema.

## 6. Backup and restore, and the drill

Backups: both databases, encrypted, every 24 hours, kept 14 days (RUNBOOK section 4). Copy them off the host; keep
`backup_key` and `complainant_keys.json` apart from them (a backup is unreadable without the first and cannot show
complainant details without the second).

Restore only into empty databases (the audit ledger is append-only, so the script refuses a non-empty one). The steps
and the drill are RUNBOOK section 4, "Restore" and "Restore drill": the drill on 2026-11-20 restored both databases with
identical row counts and `verify chain: ok=true`. **Repeat the drill after every schema change and at least every
quarter**, on a separate host or project, never over the live data.

## 7. Secret and certificate rotation

| What | How (RUNBOOK section 7) | Downtime |
|---|---|---|
| Database role passwords | `python scripts/init_secrets.py rotate <name>`, run the printed `psql` command, restart the services named | The restarted services, seconds |
| Redis password | `rotate redis_password`, restart redis, backend, worker | Seconds; queued jobs stay in Redis |
| SMTP password | Write it into `secrets/smtp_password`, restart backend and worker | Seconds; unsent alerts retry |
| Backup passphrase | New value in `secrets/backup_key`, restart backup; keep the old value until the old backups age out | None |
| Complainant key | `python scripts/complainant_key.py add`, restart, let the worker re-encrypt, then remove the old key (RUNBOOK, "Complainant details: keys") | None |
| API key of a source | Intake > Sources > Replace API key (the old key stops working at once) | That portal, until it has the new key |
| TLS certificate | `python scripts/install_cert.py <chain> <key>`: checked, installed, nginx reloaded; a bad pair is refused and the old one kept | None |

Rotate after anyone with access leaves, after any suspected exposure, and on the AICTE schedule. Put the certificate's
expiry date in the operations calendar.

## 8. Audit-chain anchors

Every hour the worker appends the latest entry number and hash to `SETHU_AUDIT_ANCHOR_DIR/audit-anchor.jsonl`. Make it
write-once: a WORM share, or `sudo chattr +a` on Linux, and copy it off the host. Compare at any time on the Audit log
screen (*Exported anchors*) or with `docker compose exec backend python -m app.audit.anchor compare` (exit 1 on a
mismatch). A rewritten entry, a truncated chain and a replaced database are each named (drill: RUNBOOK, 2026-11-22).

## 9. Monitoring and thresholds

The **AI health** screen (`GET /api/v1/ai/health`) shows whether the ai-worker reports, model checksums, provider health and circuits, the queue depth and the last day's runs by path; alert when it stops reporting for 5 minutes, when a circuit stays open, or when human review grows. Logs are JSON on stdout, one request id per request across nginx, backend and worker, with no complaint text or
personal details (tested). Ship them to the AICTE log store (readiness row 32). Metrics: `GET /metrics` on the backend's
own port, internal network only. The alert thresholds to configure are in RUNBOOK, "Observability":

- a health check failing for 2 minutes;
- a job not succeeding in time (alert mail 5 minutes, detectors and intake 20 minutes, chain check and backup 26 hours);
- any dead letter;
- a stuck intake queue;
- a source down for an hour;
- any failed alert;
- 5xx above 2%;
- p95 latency above 2 s;
- failed sign-ins above 20 in 10 minutes for one user or address.

## 10. Incident response

| Sign | First look | Then |
|---|---|---|
| Users see "Sign-in is unavailable right now" | `docker compose ... ps keycloak`, `logs keycloak` | Restart Keycloak; signed-in users keep working until their 5-minute token expires. If its database migration failed on a first start, see readiness row 57 (a first start is not crash-safe) |
| The app answers 502 | `ps backend`, `logs backend` | A backend that refuses to start names each unsafe setting; fix `.env` or the secret file |
| Alerts not arriving | Alerts screen (Failed, with reason); `logs worker`; the relay | Fix the relay; press Retry on failed alerts (audited) |
| Intake dead letters | Intake > Queue (reason per item) | Fix the cause, then Retry (admin) |
| Verify chain fails, or an anchor does not match | Audit log screen; `python -m app.audit.anchor compare` | Treat as a security incident: stop writes (stop backend and worker), keep the database volume and the anchor file as they are, take a copy, inform the AICTE security officer; do not "repair" the chain. Restore from a backup whose chain verifies only with the security officer's agreement |
| Suspected leaked password or key | Keycloak events (Audit log > Failed sign-ins), nginx JSON log | Rotate it (section 7); for a person, reset their Keycloak credentials and sessions |
| AI health: a model "Refused" | The model's files differ from `models/manifest.json` | Do not edit the manifest to match: restore the files from the connected machine where they were fetched and checked, then restart `ai-worker` |
| AI health: not reporting | `ps ai-worker`, `logs ai-worker` | Items wait in the `ai` queue; restart it. Nothing else depends on it |
| Disk filling | `df -h`; Docker volumes; `backups/` | Copy old backups off and delete them; the backup service fails loudly rather than overwrite (drill pending, readiness row 57) |

After any incident: write down what happened, when, and what was changed; the hash-chained audit log already holds every
change made through SETHU.

## 11. Known limits

- **Capacity is not measured.** The development machine could not run the 100,000-complaint load test cleanly; no
  capacity figure is claimed (readiness row 56; the steps for a 16 GB machine are in docs/LOAD-AND-DRILLS.md). At 20,000
  complaints the list queries answered in about 100 ms or less on a database alone.
- **Failure drills are not run** (Postgres, Redis or worker restart under load, a one-hour mail outage, a full backup
  disk, Keycloak down), nor the offline run (readiness row 57). Scripts and pass conditions are ready.
- **The case text search reads every row** (about 100 ms at 20,000 complaints); it needs a rewrite before 100,000+.
- **Totals stop at 1,000**: lists and dashboard counts show "1,000+" beyond that, by design, to stay fast.
- **The dashboard refreshes every 30 seconds**, not within 5 seconds of a change (unticked checklist line).
- **The AI layer is a foundation only (A1)**: stub providers, no OCR, translation or matching yet; human-review items are counted, not yet listed on a screen. ai-worker idle memory measured 64 to 76 MiB on a dev stack.
- **One host.** No high availability; recovery is restart or restore. Connections inside the host are not TLS (row 28).
- **Rate limits are per client address** at the edge; a whole office behind one address shares them.
- **Keycloak realm changes after the first start** need the console or a full re-import (row 17).
- **CI has not yet run on GitHub** (row 41); its steps pass locally.
