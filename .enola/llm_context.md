# Architecture Snapshot

## Repository Map

| Module | Language | Symbols | Exported |
|--------|----------|---------|----------|
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic` | python | 2 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic/versions` | python | 8 | 8 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app` | python | 5 | 5 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/api` | python | 3 | 3 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/audit` | python | 3 | 3 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/core` | python | 12 | 11 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/db` | python | 4 | 4 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | python | 0 | 0 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts` | python | 19 | 15 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view` | python | 10 | 10 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints` | python | 47 | 41 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/dashboard` | python | 14 | 13 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions` | python | 37 | 34 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps` | python | 30 | 24 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/reports` | python | 12 | 9 |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/search` | python | 6 | 6 |
| `.claude/worktrees/jolly-feynman-1a9f96/scripts` | python | 1 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/seed` | python | 8 | 8 |
| `.claude/worktrees/jolly-feynman-1a9f96/web` | typescript | 1 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src` | typescript | 21 | 7 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/alerts` | typescript | 6 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/audit` | typescript | 9 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/cases` | typescript | 21 | 15 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/dashboard` | typescript | 9 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/institutions` | typescript | 12 | 12 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/overlaps` | typescript | 10 | 4 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/reports` | typescript | 5 | 1 |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features/search` | typescript | 5 | 2 |
| `backend/alembic` | python | 2 | 1 |
| `backend/alembic/versions` | python | 8 | 8 |
| `backend/app` | python | 5 | 5 |
| `backend/app/api` | python | 3 | 3 |
| `backend/app/audit` | python | 3 | 3 |
| `backend/app/core` | python | 12 | 11 |
| `backend/app/db` | python | 4 | 4 |
| `backend/app/modules` | python | 0 | 0 |
| `backend/app/modules/alerts` | python | 19 | 15 |
| `backend/app/modules/audit_view` | python | 10 | 10 |
| `backend/app/modules/complaints` | python | 45 | 39 |
| `backend/app/modules/dashboard` | python | 14 | 13 |
| `backend/app/modules/institutions` | python | 35 | 32 |
| `backend/app/modules/overlaps` | python | 30 | 24 |
| `scripts` | python | 1 | 1 |
| `seed` | python | 8 | 8 |
| `web` | typescript | 1 | 1 |
| `web/src` | typescript | 20 | 6 |
| `web/src/features/alerts` | typescript | 6 | 1 |
| `web/src/features/audit` | typescript | 9 | 1 |
| `web/src/features/cases` | typescript | 21 | 15 |
| `web/src/features/dashboard` | typescript | 9 | 1 |
| `web/src/features/institutions` | typescript | 12 | 12 |
| `web/src/features/overlaps` | typescript | 10 | 4 |

## Extraction Quality

- Files parsed: **173** / 493 seen (27 file(s) + 5 directory tree(s) skipped by ignore globs)
- Parse errors: 0

## Architecture Pattern

_No specific architecture pattern detected._

## Entry Points

- **main**: `.claude/worktrees/jolly-feynman-1a9f96/scripts/init_env.main` (.claude/worktrees/jolly-feynman-1a9f96/scripts/init_env.py)
- **main**: `scripts/init_env.main` (scripts/init_env.py)
54 routes, 15 shown:
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
- … and 39 more (query_facts(kind="route") for all)

## Routes

| Method | Path | File | Type |
|--------|------|------|------|
| GET | `/api/v1` | `.claude/worktrees/jolly-feynman-1a9f96/web/src/api.ts` |  |
| GET | `/api/v1` | `.claude/worktrees/jolly-feynman-1a9f96/web/src/api.ts` |  |
| GET | `/api/v1` | `web/src/api.ts` |  |
| GET | `/api/v1/alerts` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts/api.py` |  |
| GET | `/api/v1/alerts` | `backend/app/modules/alerts/api.py` |  |
| POST | `/api/v1/alerts/{alert_id}/decision` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts/api.py` |  |
| POST | `/api/v1/alerts/{alert_id}/decision` | `backend/app/modules/alerts/api.py` |  |
| GET | `/api/v1/audit` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view/api.py` |  |
| GET | `/api/v1/audit` | `backend/app/modules/audit_view/api.py` |  |
| GET | `/api/v1/audit/verify` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view/api.py` |  |
| GET | `/api/v1/audit/verify` | `backend/app/modules/audit_view/api.py` |  |
| GET | `/api/v1/cases` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/cases` | `backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/cases/options` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/cases/options` | `backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/cases/timeline` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/cases/timeline` | `backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/cases/{complaint_id}` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/cases/{complaint_id}` | `backend/app/modules/complaints/api.py` |  |
| POST | `/api/v1/cases/{complaint_id}/actions` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py` |  |
| POST | `/api/v1/cases/{complaint_id}/actions` | `backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/cases/{complaint_id}/assignees` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/cases/{complaint_id}/assignees` | `backend/app/modules/complaints/api.py` |  |
| GET | `/api/v1/dashboard` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/dashboard/api.py` |  |
| GET | `/api/v1/dashboard` | `backend/app/modules/dashboard/api.py` |  |
| GET | `/api/v1/institutions` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions/api.py` |  |
| GET | `/api/v1/institutions` | `backend/app/modules/institutions/api.py` |  |
| GET | `/api/v1/institutions/resolution/queue` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions/api.py` |  |
| GET | `/api/v1/institutions/resolution/queue` | `backend/app/modules/institutions/api.py` |  |
| POST | `/api/v1/institutions/resolution/run` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions/api.py` |  |
| POST | `/api/v1/institutions/resolution/run` | `backend/app/modules/institutions/api.py` |  |
| POST | `/api/v1/institutions/resolution/{complaint_id}` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions/api.py` |  |
| POST | `/api/v1/institutions/resolution/{complaint_id}` | `backend/app/modules/institutions/api.py` |  |
| GET | `/api/v1/institutions/{institution_id}` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions/api.py` |  |
| GET | `/api/v1/institutions/{institution_id}` | `backend/app/modules/institutions/api.py` |  |
| GET | `/api/v1/me` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/api/routes.py` |  |
| GET | `/api/v1/me` | `backend/app/api/routes.py` |  |
| GET | `/api/v1/overlaps` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps/api.py` |  |
| GET | `/api/v1/overlaps` | `backend/app/modules/overlaps/api.py` |  |
| POST | `/api/v1/overlaps/detect` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps/api.py` |  |
| POST | `/api/v1/overlaps/detect` | `backend/app/modules/overlaps/api.py` |  |
| GET | `/api/v1/overlaps/tier1` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps/api.py` |  |
| GET | `/api/v1/overlaps/tier1` | `backend/app/modules/overlaps/api.py` |  |
| POST | `/api/v1/overlaps/{link_id}/decision` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps/api.py` |  |
| POST | `/api/v1/overlaps/{link_id}/decision` | `backend/app/modules/overlaps/api.py` |  |
| GET | `/api/v1/reports/{name}` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/reports/api.py` |  |
| GET | `/api/v1/reports/{name}/export` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/reports/api.py` |  |
| GET | `/api/v1/search` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/search/api.py` |  |
| POST | `/auth/realms/sethu/protocol/openid-connect/token` | `.claude/worktrees/jolly-feynman-1a9f96/web/src/auth.ts` |  |
| POST | `/auth/realms/sethu/protocol/openid-connect/token` | `web/src/auth.ts` |  |
| GET | `/health/live` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/api/routes.py` |  |
| GET | `/health/live` | `backend/app/api/routes.py` |  |
| GET | `/health/ready` | `.claude/worktrees/jolly-feynman-1a9f96/backend/app/api/routes.py` |  |
| GET | `/health/ready` | `backend/app/api/routes.py` |  |

## Dependency Rules

64 internal module dependencies. The modules that reach furthest; traverse() or query_facts(kind="dependency") for the edges themselves.

| Module | Depends on |
|--------|------------|
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app` | 6 modules |
| `backend/app` | 6 modules |
| `.` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/alerts` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/complaints` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/overlaps` | 3 modules |
| `backend/app/modules/alerts` | 3 modules |
| `backend/app/modules/complaints` | 3 modules |
| `backend/app/modules/overlaps` | 3 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/audit_view` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/institutions` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/search` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src/features` | 2 modules |
| `backend` | 2 modules |
| `backend/app/modules` | 2 modules |
| `backend/app/modules/audit_view` | 2 modules |
| `backend/app/modules/institutions` | 2 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/alembic/versions` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/dashboard` | 1 modules |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules/reports` | 1 modules |
| `backend/alembic` | 1 modules |
| `backend/alembic/versions` | 1 modules |
| `backend/app/modules/dashboard` | 1 modules |
| `web/src/features` | 1 modules |

## Critical Modules

| Module | Fan-In | Fan-Out | Criticality |
|--------|--------|---------|-------------|
| `backend/app/db` | 20 | 0 | high |
| `backend/app/audit` | 15 | 0 | high |
| `backend/app/core` | 11 | 0 | high |
| `backend/app/modules/complaints` | 7 | 4 | high |
| `backend/alembic` | 9 | 1 | high |
| `backend/app/modules/overlaps` | 6 | 4 | high |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app/modules` | 0 | 9 | medium |
| `.claude/worktrees/jolly-feynman-1a9f96/backend/app` | 0 | 8 | medium |
| `.claude/worktrees/jolly-feynman-1a9f96/web/src` | 8 | 0 | medium |
| `backend/app/modules/alerts` | 4 | 4 | medium |

## Risk Zones

- **Cyclic dependency detected (2 modules)** (confidence: 100%): The following modules form a dependency cycle: backend/app/modules/complaints -> backend/app/modules/overlaps -> backend/app/modules/complaints. This can cause initialization issues, make refactoring harder, and indicates tight coupling.
- **Cyclic dependency detected (7 modules)** (confidence: 100%): The following modules form a dependency cycle: web/src -> web/src/features/alerts -> web/src/features/audit -> web/src/features/cases -> web/src/features/dashboard -> web/src/features/institutions -> web/src/features/overlaps -> web/src. This can cause initialization issues, make refactoring harder, and indicates tight coupling.

---

*Generated at 2026-11-16T17:52:28Z in 2.6755204s. 1934 facts, 156 insights.*
