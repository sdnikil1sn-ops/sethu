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

`docker compose --profile dev up` runs a one-shot `demo-users` service that creates five Keycloak users. They are the same people as in `seed/users.csv`, with the same ids, so what they do in the app is tied to their seeded history.

| Username | Person | Role | Bureau |
|---|---|---|---|
| `rao` | Ms. Anita Rao | officer | PGRC |
| `iyer` | Mr. Suresh Iyer | bureau_head | RB |
| `fernandes` | Ms. Maria Fernandes | bureau_head | PGRC |
| `menon` | Dr. Kavita Menon | oversight | none |
| `das` | Mr. Arun Das | auditor | none |

All five share the password in `DEMO_USER_PASSWORD` in `.env`. The repository holds only a placeholder (`infra/demo-users/users.json`). A `.env` created before this variable existed needs the line added by hand: 12 or more characters with upper case, lower case and a digit.

The production start (section 7) does not use the `dev` profile, so these users are never created there. Do not add users to `infra/keycloak/sethu-realm.json`: that file is shared with production.

### Re-importing the realm on an existing stack

Keycloak imports `infra/keycloak/sethu-realm.json` only when the `sethu` realm does not exist yet, so editing the file changes nothing on a stack that has already started.

Demo users only (new password in `.env`, or a user was changed or deleted). Safe to repeat; other users and all SETHU data are untouched:

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

### Seeding the demo data

Load into an empty database only (after a first start or a reset, section 5). The files and the patterns they contain are described in `seed/README.md`.

```powershell
docker compose run --rm --no-deps -v "${PWD}/seed:/seed:ro" backend python /seed/load.py
```

The worker links misspelt institution names and suggests overlaps every 5 minutes. To have both at once after seeding:

```powershell
docker compose exec worker celery -A app.worker:celery call sethu.institutions.resolve_pending
docker compose exec worker celery -A app.worker:celery call sethu.overlaps.detect
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

## 7. Production differences

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Before giving a production user a `bureau_id`, set Realm settings > General > Unmanaged attributes to "Only administrators can write" in the Keycloak console; otherwise Keycloak discards the attribute and the user cannot log in. (The demo import does this for dev.)

Needs certificates in `infra/certs/`, `PUBLIC_BASE_URL=https://...`, a real SMTP relay, secrets from Docker secrets or Vault, images pinned by digest, and backups scheduled. The production override has not been exercised.
