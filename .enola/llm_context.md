# Architecture Snapshot

## Repository Map

| Module | Language | Symbols | Exported |
|--------|----------|---------|----------|
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic` | python | 2 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic/versions` | python | 12 | 12 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app` | python | 6 | 6 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/api` | python | 3 | 3 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/audit` | python | 3 | 3 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/core` | python | 16 | 13 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/db` | python | 4 | 4 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | python | 0 | 0 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts` | python | 19 | 15 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view` | python | 10 | 10 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints` | python | 48 | 41 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/dashboard` | python | 14 | 13 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/findings` | python | 36 | 32 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions` | python | 46 | 43 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps` | python | 30 | 24 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/reports` | python | 13 | 9 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/search` | python | 6 | 6 |
| `.claude/worktrees/jolly-feynman-1a9f96/scripts` | python | 1 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/seed` | python | 9 | 9 |
| `.claude/worktrees/jolly-feynman-1a9f96/web` | typescript | 1 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src` | typescript | 22 | 7 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/alerts` | typescript | 6 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/audit` | typescript | 9 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/cases` | typescript | 21 | 15 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/dashboard` | typescript | 9 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/findings` | typescript | 9 | 2 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/institutions` | typescript | 26 | 15 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/overlaps` | typescript | 10 | 4 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/reports` | typescript | 5 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/search` | typescript | 5 | 2 |
| `backend/alembic` | python | 2 | 1 |
| `backend/alembic/versions` | python | 10 | 10 |
| `backend/app` | python | 6 | 6 |
| `backend/app/api` | python | 3 | 3 |
| `backend/app/audit` | python | 3 | 3 |
| `backend/app/core` | python | 13 | 12 |
| `backend/app/db` | python | 4 | 4 |
| `backend/app/modules` | python | 0 | 0 |
| `backend/app/modules/alerts` | python | 19 | 15 |
| `backend/app/modules/audit_view` | python | 10 | 10 |
| `backend/app/modules/complaints` | python | 48 | 41 |
| `backend/app/modules/dashboard` | python | 14 | 13 |
| `backend/app/modules/findings` | python | 33 | 29 |
| `backend/app/modules/institutions` | python | 46 | 43 |
| `backend/app/modules/overlaps` | python | 30 | 24 |
| `backend/app/modules/reports` | python | 13 | 9 |
| `backend/app/modules/search` | python | 6 | 6 |
| `scripts` | python | 1 | 1 |
| `seed` | python | 8 | 8 |
| `web` | typescript | 1 | 1 |
| `web/src` | typescript | 22 | 7 |
| `web/src/features/alerts` | typescript | 6 | 1 |
| `web/src/features/audit` | typescript | 9 | 1 |
| `web/src/features/cases` | typescript | 21 | 15 |
| `web/src/features/dashboard` | typescript | 9 | 1 |
| `web/src/features/findings` | typescript | 8 | 2 |
| `web/src/features/institutions` | typescript | 26 | 15 |
| `web/src/features/overlaps` | typescript | 10 | 4 |
| `web/src/features/reports` | typescript | 5 | 1 |
| `web/src/features/search` | typescript | 5 | 2 |

## Extraction Quality

- Files parsed: **202** / 710 seen (34 file(s) + 5 directory tree(s) skipped by ignore globs)
- Parse errors: 0

## Architecture Pattern

_No specific architecture pattern detected._

## Entry Points

- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/init_env.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/init_env.py)
- **main**: `scripts/init_env.main` (scripts/init_env.py)
66 routes, 15 shown:
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
- **route** GET `/api/v1/cases/{complaint_id}/assignees` (backend/app/modules/complaints/api.py)
- **route** GET `/api/v1/cases/{complaint_id}` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py)
- **route** GET `/api/v1/cases/{complaint_id}` (backend/app/modules/complaints/api.py)
- **route** GET `/api/v1/cases` (.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py)
- … and 51 more (query_facts(kind="route") for all)

## Routes

66 routes, grouped by path prefix. query_facts(kind="route") for all of them.

| Prefix | Routes | Methods | Example |
|--------|--------|---------|----------|
| `/api` | 60 | GET, POST | `/api/v1` |
| `/health` | 4 | GET | `/health/live` |
| `/auth` | 2 | POST | `/auth/realms/sethu/protocol/openid-connect/token` |

## Dependency Rules

82 internal module dependencies. The modules that reach furthest; traverse() or query_facts(kind="dependency") for the edges themselves.

| Module | Depends on |
|--------|------------|
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app` | 7 modules |
| `backend/app` | 7 modules |
| `.` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/findings` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/search` | 3 modules |
| `backend/app/modules/alerts` | 3 modules |
| `backend/app/modules/complaints` | 3 modules |
| `backend/app/modules/findings` | 3 modules |
| `backend/app/modules/overlaps` | 3 modules |
| `backend/app/modules/search` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/dashboard` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/reports` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features` | 2 modules |
| `backend` | 2 modules |
| `backend/app/modules` | 2 modules |
| `backend/app/modules/audit_view` | 2 modules |
| `backend/app/modules/dashboard` | 2 modules |
| `backend/app/modules/institutions` | 2 modules |
| `backend/app/modules/reports` | 2 modules |
| `web/src/features` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic/versions` | 1 modules |
| `backend/alembic` | 1 modules |
| `backend/alembic/versions` | 1 modules |

## Critical Modules

| Module | Fan-In | Fan-Out | Criticality |
|--------|--------|---------|-------------|
| `backend/app/db` | 24 | 0 | high |
| `backend/app/audit` | 18 | 0 | high |
| `backend/app/core` | 15 | 0 | high |
| `backend/app/modules/complaints` | 10 | 4 | high |
| `backend/alembic` | 12 | 1 | high |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | 0 | 12 | high |
| `backend/app/modules` | 0 | 12 | high |
| `backend/app/modules/findings` | 6 | 4 | high |
| `backend/app/modules/overlaps` | 6 | 4 | high |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app` | 0 | 9 | medium |

## Risk Zones

- **Cyclic dependency detected (2 modules)** (confidence: 100%): The following modules form a dependency cycle: backend/app/modules/complaints -> backend/app/modules/overlaps -> backend/app/modules/complaints. This can cause initialization issues, make refactoring harder, and indicates tight coupling.

---

*Generated at 2026-11-20T12:49:49Z in 2.783411s. 2375 facts, 162 insights.*
