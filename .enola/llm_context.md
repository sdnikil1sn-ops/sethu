# Architecture Snapshot

## Repository Map

78 modules, 1426 symbols, grouped by area. Every module is in `facts.jsonl`, or query_facts(kind="module").

| Area | Modules | Symbols | Languages |
|------|---------|---------|-----------|
| `.claude` | 39 | 713 | python, typescript |
| `backend` | 22 | 496 | python |
| `web` | 14 | 161 | typescript |
| `loadtest` | 1 | 30 | python |
| `scripts` | 1 | 16 | python |
| `seed` | 1 | 10 | python |

Largest modules:
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints` — 78 symbols (python)
- `backend/app/modules/complaints` — 78 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/intake` — 72 symbols (python)
- `backend/app/modules/intake` — 72 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions` — 46 symbols (python)
- `backend/app/modules/institutions` — 46 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/findings` — 39 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps` — 39 symbols (python)
- `backend/app/modules/findings` — 39 symbols (python)
- `backend/app/modules/overlaps` — 39 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/core` — 36 symbols (python)
- `backend/app/core` — 36 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/loadtest` — 30 symbols (python)
- `loadtest` — 30 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/web/src` — 27 symbols (typescript)
- `web/src` — 27 symbols (typescript)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic/versions` — 26 symbols (python)
- `backend/alembic/versions` — 26 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/cases` — 25 symbols (typescript)
- `web/src/features/cases` — 25 symbols (typescript)

## Extraction Quality

- Files parsed: **296** / 1406 seen (57 file(s) + 8 directory tree(s) skipped by ignore globs)
- Parse errors: 0

## Architecture Pattern

_No specific architecture pattern detected._

## Entry Points

- **handler**: `.claude/worktrees/jolly-feynman-1a9f96/backend/app/core/metrics.observe_request` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/core/metrics.py)
- **handler**: `.claude/worktrees/jolly-feynman-1a9f96/loadtest.handleSummary` (.claude/worktrees/jolly-feynman-1a9f96/loadtest/k6.js)
- **handler**: `backend/app/core/metrics.observe_request` (backend/app/core/metrics.py)
- **handler**: `loadtest.handleSummary` (loadtest/k6.js)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/backend/app/audit/anchor.main` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/audit/anchor.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps/measure.main` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps/measure.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/backend/fetch_model.main` (.claude/worktrees/jolly-feynman-1a9f96/backend/fetch_model.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/loadtest/drill_intake.main` (.claude/worktrees/jolly-feynman-1a9f96/loadtest/drill_intake.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/loadtest/drill_smtp.main` (.claude/worktrees/jolly-feynman-1a9f96/loadtest/drill_smtp.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/complainant_key.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/complainant_key.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/init_env.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/init_env.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/init_secrets.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/init_secrets.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/install_cert.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/install_cert.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/lock_python.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/lock_python.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/seed/volume.main` (.claude/worktrees/jolly-feynman-1a9f96/seed/volume.py)
- **main**: `backend/app/audit/anchor.main` (backend/app/audit/anchor.py)
- **main**: `backend/app/modules/overlaps/measure.main` (backend/app/modules/overlaps/measure.py)
- **main**: `backend/fetch_model.main` (backend/fetch_model.py)
- **main**: `loadtest/drill_intake.main` (loadtest/drill_intake.py)
- **main**: `loadtest/drill_smtp.main` (loadtest/drill_smtp.py)
- **main**: `scripts/complainant_key.main` (scripts/complainant_key.py)
- **main**: `scripts/init_env.main` (scripts/init_env.py)
- **main**: `scripts/init_secrets.main` (scripts/init_secrets.py)
- **main**: `scripts/install_cert.main` (scripts/install_cert.py)
- **main**: `scripts/lock_python.main` (scripts/lock_python.py)
- **main**: `seed/volume.main` (seed/volume.py)
130 routes, 15 shown:
- **route** GET `/api/v1/admin/bureaus` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/bureaus/api.py)
- **route** GET `/api/v1/admin/bureaus` (backend/app/modules/bureaus/api.py)
- **route** GET `/api/v1/admin/deadlines` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py)
- **route** GET `/api/v1/admin/deadlines` (backend/app/modules/complaints/api.py)
- **route** GET `/api/v1/admin/users` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/users/api.py)
- **route** GET `/api/v1/admin/users` (backend/app/modules/users/api.py)
- **route** GET `/api/v1/alerts` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts/api.py)
- **route** GET `/api/v1/alerts` (backend/app/modules/alerts/api.py)
- **route** GET `/api/v1/audit/anchor` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/audit/anchor` (backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/audit/signins` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/audit/signins` (backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/audit/verify` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/audit/verify` (backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/audit` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view/api.py)
- … and 115 more (query_facts(kind="route") for all)

## Routes

130 routes, grouped by path prefix. query_facts(kind="route") for all of them.

| Prefix | Routes | Methods | Example |
|--------|--------|---------|----------|
| `/api` | 122 | GET, PATCH, POST, PUT | `/api/v1` |
| `/health` | 4 | GET | `/health/live` |
| `/auth` | 2 | POST | `/auth/realms/sethu/protocol/openid-connect/token` |
| `/metrics` | 2 | GET | `/metrics` |

## Dependency Rules

129 internal module dependencies. The modules that reach furthest; traverse() or query_facts(kind="dependency") for the edges themselves.

| Module | Depends on |
|--------|------------|
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app` | 9 modules |
| `backend/app` | 9 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/intake` | 7 modules |
| `backend/app/modules/intake` | 7 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps` | 5 modules |
| `backend/app/modules/overlaps` | 5 modules |
| `.claude/worktrees/jolly-feynman-1a9f96` | 4 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints` | 4 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/findings` | 4 modules |
| `backend/app/modules/complaints` | 4 modules |
| `backend/app/modules/findings` | 4 modules |
| `.` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/search` | 3 modules |
| `backend/app/modules/alerts` | 3 modules |
| `backend/app/modules/search` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/api` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/bureaus` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/dashboard` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/reports` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/users` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/loadtest` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features` | 2 modules |
| `backend` | 2 modules |
| `backend/app/api` | 2 modules |
| `backend/app/modules` | 2 modules |
| `backend/app/modules/audit_view` | 2 modules |
| `backend/app/modules/bureaus` | 2 modules |
| `backend/app/modules/dashboard` | 2 modules |
| `backend/app/modules/institutions` | 2 modules |
| `backend/app/modules/reports` | 2 modules |
| `backend/app/modules/users` | 2 modules |
| `loadtest` | 2 modules |
| `web/src/features` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic/versions` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/graph` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/seed` | 1 modules |
| `backend/alembic` | 1 modules |
| `backend/alembic/versions` | 1 modules |
| `backend/app/modules/graph` | 1 modules |
| `seed` | 1 modules |

## Critical Modules

| Module | Fan-In | Fan-Out | Criticality |
|--------|--------|---------|-------------|
| `backend/app/db` | 36 | 0 | high |
| `backend/app/audit` | 30 | 0 | high |
| `backend/app/core` | 29 | 0 | high |
| `backend/alembic` | 27 | 1 | high |
| `backend/app/modules/complaints` | 16 | 5 | high |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | 0 | 18 | high |
| `backend/app/modules` | 0 | 18 | high |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app` | 0 | 15 | high |
| `backend/app/modules/overlaps` | 7 | 8 | high |
| `backend/app/modules/users` | 12 | 3 | high |

## Risk Zones

- **Cyclic dependency detected (2 modules)** (confidence: 100%): The following modules form a dependency cycle: backend/app/modules/complaints -> backend/app/modules/overlaps -> backend/app/modules/complaints. This can cause initialization issues, make refactoring harder, and indicates tight coupling.

---

*Generated at 2026-11-22T07:42:25Z in 2.7112187s. 3898 facts, 185 insights.*
