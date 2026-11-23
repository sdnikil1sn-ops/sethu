# SETHU

AI-assisted AICTE institutional complaint monitoring across bureaus. Smart India Hackathon 2026, problem statement SIH26264, team PIVOTT.

One screen where an AICTE officer sees every complaint about an institution across all bureaus, is warned when bureaus are working the same matter, and can prove who did what and when.

## Read first

| Need | File |
|---|---|
| What is in and out of scope | `docs/01-SCOPE-LOCK.md` |
| The 8 PS features and their acceptance tests | `docs/02-PS-COVERAGE-CHECKLIST.md` |
| The demo the build must serve | `docs/03-DEMO-STORY.md` |
| Synthetic data to generate | `docs/04-MOCK-DATA-SPEC.md` |
| System design, zones, module rules | `docs/ARCHITECTURE.md` |
| Tables, roles, Row-Level Security | `docs/DATA-MODEL.md` |
| Threat model and control status | `docs/SECURITY.md` |
| Why each major choice was made | `docs/adr/` |
| Start, stop, back up, verify | `docs/RUNBOOK.md` |
| Install, configure, upgrade, rotate, monitor, respond | `docs/OPERATIONS.md` |
| What each role does on each screen | `docs/USER-GUIDE.md` |
| The intake API for portals | `docs/API.md` |
| What stands before go-live (Done, Accepted risk, Open) | `docs/PRODUCTION-READINESS.md` |
| Security review, load test and drills | `docs/SECURITY-REVIEW.md`, `docs/LOAD-AND-DRILLS.md` |

Do not add features outside the scope docs. New ideas go to the parking lot in `docs/01-SCOPE-LOCK.md`.

## Non-negotiable rules

1. **Data stays inside.** No external APIs, hosted services, telemetry or CDN assets at run time. The `app` and `data` Docker networks are `internal`; do not change that. Ask before adding any dependency that makes network calls.
2. **Mock data only.** Never put real complaints or personal data in the repo, prompts, logs, tests or screenshots. Test emails use `@sethu.test`.
3. **Every state change is audited in the same transaction.** Call `app.audit.service.record(...)` inside the same `session_for(...)` block as the change. Payloads carry identifiers and decisions, never complaint text or complainant details.
4. **The database enforces access, not just the API.** All queries run through `session_for(principal)` / `get_session`, which sets the request context that Row-Level Security reads. Never connect as `sethu_owner` or a superuser from application code. Never add `BYPASSRLS` or `SECURITY DEFINER` shortcuts.
5. **The audit ledger is append-only.** No migration may update, delete from, truncate or drop `sethu.audit_log`, or weaken its triggers.
6. **AI proposes, a person decides.** Overlap links and alerts are created as `proposed` / `pending_approval`. Nothing is sent and no link is confirmed without an officer's action, and that action is audited.
7. **Every AI step has a deterministic fallback** (rules, TF-IDF, fuzzy match) and the system must work with the AI models switched off.
8. Say "hash-chained audit log", never "blockchain".

## Stack

- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (sync, psycopg 3), Alembic, Celery with Redis.
- Database: PostgreSQL 16 with `pg_trgm`, `pgcrypto`, `pgvector`. Schema `sethu`.
- Identity: Keycloak (OIDC, PKCE). Roles: `officer`, `bureau_head`, `oversight`, `admin`, `auditor`.
- Web: React 18, TypeScript, Vite. Served by unprivileged Nginx, which is also the edge proxy.
- Runtime: Docker Compose. One command brings up everything.

## Layout

```
backend/app/core/      config, logging, auth (JWT to Principal)
backend/app/db/        session_for(principal): the only way to reach the database
backend/app/audit/     append-only ledger: record(), verify()
backend/app/api/       platform routes (health, me); the audit screen and Verify chain are in modules/audit_view
backend/app/modules/   one package per feature (create as features are built)
backend/app/worker.py  Celery app and scheduled jobs
backend/alembic/       migrations (run as sethu_owner)
backend/tests/         run against real PostgreSQL
web/src/               React app; features under src/features/<feature>/
infra/                 postgres init, nginx, keycloak realm
seed/                  deterministic mock data: generate.py, load.py, CSV files (see seed/README.md)
```

Feature module shape: `backend/app/modules/<feature>/{api.py, service.py, repo.py, schemas.py}`.
`api` handles HTTP and roles; `service` holds rules and calls `audit.record`; `repo` holds SQL. A module never imports another module's `repo`; it calls that module's `service`.

## Commands

```powershell
python scripts/init_env.py                      # once: create .env with random secrets
docker compose --profile dev up --build -d      # start everything (+ Mailpit)
docker compose ps                               # check health
docker compose logs -f backend
docker compose down                             # stop (keeps data)
```

App: http://localhost:8080 . API docs: internal network only, `http://backend:8000/docs` (docs/API.md). Mail: http://localhost:8025 .

Backend tests run against a real PostgreSQL and **empty every table**; use a throwaway stack. Full steps: `docs/RUNBOOK.md` section 3. Short form:

```powershell
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d postgres migrate
cd backend; pip install -e ".[dev]"
# set MIGRATION_DATABASE_URL, SETHU_DATABASE_URL, SETHU_TEST_DB_WIPE_OK=1 (see runbook)
pytest -q; ruff check .
```

Web: `cd web; npm install; npm run build` (type-checks, then builds).

## Working agreements

- Build order: PS must-haves (profile, tracking, overlap, dashboard, history, search, alerts, reports), then flagship features (graph, deadlock, profile DNA, early warning), then optional AI features.
- Definition of done for a feature: works on the seeded demo data, has a test, writes to the audit log where it changes data, and its line in `docs/02-PS-COVERAGE-CHECKLIST.md` is ticked.
- Schema changes are new Alembic revisions. Never edit an applied migration. New tables that hold complaint content get Row-Level Security in the same revision, with a test in `tests/test_rls.py`.
- New endpoints declare their roles with `require_roles(...)` and take their session from `get_session`.
- Do not log request bodies. Log identifiers.
- Keep `docs/` true: if a design decision changes, update the relevant doc or add an ADR in the same change.
- Windows is the development machine: give PowerShell commands, and keep `.sh`, `.conf`, `.yml` files LF (see `.gitattributes`).

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
- Never run git commit, git push, git merge or git worktree commands. Leave changes uncommitted in the working tree; the user reviews and commits them.