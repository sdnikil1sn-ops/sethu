# Architecture Snapshot

## Repository Map

66 modules, 946 symbols, grouped by area. Every module is in `facts.jsonl`, or query_facts(kind="module").

| Area | Modules | Symbols | Languages |
|------|---------|---------|-----------|
| `.claude` | 33 | 473 | python, typescript |
| `backend` | 19 | 326 | python |
| `web` | 12 | 127 | typescript |
| `scripts` | 1 | 11 | python |
| `seed` | 1 | 9 | python |

Largest modules:
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints` — 53 symbols (python)
- `backend/app/modules/complaints` — 53 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions` — 46 symbols (python)
- `backend/app/modules/institutions` — 46 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/findings` — 35 symbols (python)
- `backend/app/modules/findings` — 35 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps` — 29 symbols (python)
- `backend/app/modules/overlaps` — 29 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/core` — 27 symbols (python)
- `backend/app/core` — 27 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/institutions` — 26 symbols (typescript)
- `web/src/features/institutions` — 26 symbols (typescript)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts` — 24 symbols (python)
- `backend/app/modules/alerts` — 24 symbols (python)
- `.claude/worktrees/jolly-feynman-1a9f96/web/src` — 22 symbols (typescript)
- `web/src` — 22 symbols (typescript)
- `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/cases` — 21 symbols (typescript)
- `web/src/features/cases` — 21 symbols (typescript)
- `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/bureaus` — 19 symbols (python)
- `backend/app/modules/bureaus` — 19 symbols (python)

## Extraction Quality

- Files parsed: **234** / 986 seen (41 file(s) + 8 directory tree(s) skipped by ignore globs)
- Parse errors: 0

## Architecture Pattern

_No specific architecture pattern detected._

## Entry Points

- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/complainant_key.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/complainant_key.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/init_env.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/init_env.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/init_secrets.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/init_secrets.py)
- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/install_cert.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/install_cert.py)
- **main**: `scripts/complainant_key.main` (scripts/complainant_key.py)
- **main**: `scripts/init_env.main` (scripts/init_env.py)
- **main**: `scripts/init_secrets.main` (scripts/init_secrets.py)
- **main**: `scripts/install_cert.main` (scripts/install_cert.py)
76 routes, 15 shown:
- **route** GET `/api/v1/admin/bureaus` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/bureaus/api.py)
- **route** GET `/api/v1/admin/bureaus` (backend/app/modules/bureaus/api.py)
- **route** GET `/api/v1/admin/users` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/users/api.py)
- **route** GET `/api/v1/admin/users` (backend/app/modules/users/api.py)
- **route** GET `/api/v1/alerts` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts/api.py)
- **route** GET `/api/v1/alerts` (backend/app/modules/alerts/api.py)
- **route** GET `/api/v1/audit/verify` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/audit/verify` (backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/audit` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/audit` (backend/app/modules/audit_view/api.py)
- **route** GET `/api/v1/cases/options` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py)
- **route** GET `/api/v1/cases/options` (backend/app/modules/complaints/api.py)
- **route** GET `/api/v1/cases/timeline` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py)
- **route** GET `/api/v1/cases/timeline` (backend/app/modules/complaints/api.py)
- **route** GET `/api/v1/cases/{complaint_id}/assignees` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py)
- … and 61 more (query_facts(kind="route") for all)

## Routes

76 routes, grouped by path prefix. query_facts(kind="route") for all of them.

| Prefix | Routes | Methods | Example |
|--------|--------|---------|----------|
| `/api` | 70 | GET, PATCH, POST | `/api/v1` |
| `/health` | 4 | GET | `/health/live` |
| `/auth` | 2 | POST | `/auth/realms/sethu/protocol/openid-connect/token` |

## Dependency Rules

103 internal module dependencies. The modules that reach furthest; traverse() or query_facts(kind="dependency") for the edges themselves.

| Module | Depends on |
|--------|------------|
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app` | 8 modules |
| `backend/app` | 8 modules |
| `.claude/worktrees/jolly-feynman-1a9f96` | 4 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints` | 4 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/findings` | 4 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps` | 4 modules |
| `backend/app/modules/complaints` | 4 modules |
| `backend/app/modules/findings` | 4 modules |
| `backend/app/modules/overlaps` | 4 modules |
| `.` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/search` | 3 modules |
| `backend/app/modules/alerts` | 3 modules |
| `backend/app/modules/search` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/bureaus` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/dashboard` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/reports` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/users` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features` | 2 modules |
| `backend` | 2 modules |
| `backend/app/modules` | 2 modules |
| `backend/app/modules/audit_view` | 2 modules |
| `backend/app/modules/bureaus` | 2 modules |
| `backend/app/modules/dashboard` | 2 modules |
| `backend/app/modules/institutions` | 2 modules |
| `backend/app/modules/reports` | 2 modules |
| `backend/app/modules/users` | 2 modules |
| `web/src/features` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic/versions` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/api` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/seed` | 1 modules |
| `backend/alembic` | 1 modules |
| `backend/alembic/versions` | 1 modules |
| `backend/app/api` | 1 modules |
| `seed` | 1 modules |

## Critical Modules

| Module | Fan-In | Fan-Out | Criticality |
|--------|--------|---------|-------------|
| `backend/app/db` | 28 | 0 | high |
| `backend/app/audit` | 22 | 0 | high |
| `backend/app/modules/complaints` | 14 | 5 | high |
| `backend/alembic` | 17 | 1 | high |
| `backend/app/core` | 17 | 0 | high |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | 0 | 14 | high |
| `backend/app/modules` | 0 | 14 | high |
| `backend/app/modules/users` | 10 | 3 | high |
| `backend/app/modules/findings` | 6 | 5 | high |
| `backend/app/modules/overlaps` | 6 | 5 | high |

## Risk Zones

- **Cyclic dependency detected (2 modules)** (confidence: 100%): The following modules form a dependency cycle: backend/app/modules/complaints -> backend/app/modules/overlaps -> backend/app/modules/complaints. This can cause initialization issues, make refactoring harder, and indicates tight coupling.

---

*Generated at 2026-11-20T19:37:13Z in 2.3414965s. 2799 facts, 165 insights.*
