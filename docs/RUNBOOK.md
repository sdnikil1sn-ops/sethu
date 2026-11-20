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

Approved alerts are emailed within 15 seconds, one email per recipient, to Mailpit at http://localhost:8025 (the Alerts page links to it). An alert that could not be sent stays "Approved, queued to send" on the Alerts page with the error and is retried; check `docker compose logs worker` and that `mailpit` is running.

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

## 4. Backup and restore

```powershell
docker compose exec postgres pg_dump -U postgres -Fc sethu -f /tmp/sethu.dump
docker compose cp postgres:/tmp/sethu.dump .\sethu.dump
```

Restore into a fresh stack: start `postgres` only, `pg_restore -U postgres -d sethu --clean /tmp/sethu.dump`, then run `audit_verify()`; it must return `ok = true`. Dumps contain complaint data: keep them inside AICTE storage, never in the repo (`*.dump` is git-ignored).

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

1. Certificates from the AICTE/NIC CA in `infra/certs/server.crt` and `infra/certs/server.key` (git-ignored).
2. `python scripts/init_env.py`, then in `.env`: `SETHU_ENVIRONMENT=prod`, `PUBLIC_BASE_URL=https://<host>`, `SMTP_HOST`, `SMTP_PORT`, `ALERT_FROM`, and delete `DEMO_USER_PASSWORD`.
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

To add a person: in the admin console, realm `sethu` > Users > Add user (username, e-mail, first and last name), set a temporary password under Credentials, assign one realm role (`officer`, `bureau_head`, `oversight`, `admin` or `auditor`), and for `officer` and `bureau_head` add the attribute `bureau_id` = the bureau's id (`SELECT id, code FROM sethu.bureaus`). SETHU registers the person in `sethu.app_users` on their first action (audited as `user.registered`), without an e-mail address: until PRODUCTION-READINESS row 47 is fixed, set `email` on a bureau head's row by hand, or that bureau's alerts have no recipient. Bureaus themselves can only be created with SQL today (row 46).

Like the dev realm, the file is read only when the realm does not exist yet; a change to it reaches a running system only through the console or a full re-import (section 3).

### Configuration reference

| Variable | Used by | Dev | Production |
|---|---|---|---|
| `SETHU_ENVIRONMENT` | backend, worker, demo-user import, seed loader | `dev` | `prod` |
| `PUBLIC_BASE_URL` | Keycloak hostname and realm URIs, the backend's token issuer | `http://localhost:8080` | `https://<host>`, required |
| `POSTGRES_SUPERUSER_PASSWORD` | PostgreSQL bootstrap | random | random |
| `SETHU_OWNER_PASSWORD` | migrations (`sethu_owner`) | random | random |
| `SETHU_APP_PASSWORD` | backend and worker (`sethu_app`) | random | random, 16+, checked |
| `SETHU_AUDITOR_PASSWORD` | direct read access for auditors | random | random |
| `KEYCLOAK_DB_PASSWORD` | Keycloak's database | random | random |
| `REDIS_PASSWORD` | Redis, backend and worker | random | random, 16+, checked |
| `KEYCLOAK_ADMIN_USER`, `KEYCLOAK_ADMIN_PASSWORD` | Keycloak bootstrap administrator | `sethu-admin`, random | change the name; disable after creating named admins |
| `DEMO_USER_PASSWORD` | demo-user import | set | not set (the import refuses production) |
| `SMTP_HOST`, `SMTP_PORT` | alert delivery | `mailpit`, `1025` | the relay, required; Mailpit refused |
| `ALERT_FROM` | sender of alert mail | not used (default `sethu-alerts@sethu.test`) | required; not a `.test` address |
| `SETHU_DEBUG` | FastAPI debug pages | `false` | must be `false` |
| `SETHU_STALLED_TRANSFER_DAYS`, `SETHU_BOTTLENECK_MIN_OPEN`, `SETHU_BOTTLENECK_SHARE`, `SETHU_SPIKE_MIN_COUNT`, `SETHU_SPIKE_RATIO` | findings detector | 7, 3, 0.6, 5, 3.0 | same unless tuned |
