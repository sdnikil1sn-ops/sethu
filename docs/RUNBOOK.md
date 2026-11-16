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

### Seeding the demo data

Load into an empty database only (after a first start or a reset, section 5). The files and the patterns they contain are described in `seed/README.md`.

```powershell
docker compose run --rm --no-deps -v "${PWD}/seed:/seed:ro" backend python /seed/load.py
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

1. Start the stack and seed data while online, the day before.
2. Switch Wi-Fi off. `docker compose --profile dev up -d` must still work: every image is local and nothing calls out.
3. Run the script in `docs/03-DEMO-STORY.md` twice.

## 7. Production differences

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Before giving a production user a `bureau_id`, set Realm settings > General > Unmanaged attributes to "Only administrators can write" in the Keycloak console; otherwise Keycloak discards the attribute and the user cannot log in. (The demo import does this for dev.)

Needs certificates in `infra/certs/`, `PUBLIC_BASE_URL=https://...`, a real SMTP relay, secrets from Docker secrets or Vault, images pinned by digest, and backups scheduled. The production override has not been exercised.
