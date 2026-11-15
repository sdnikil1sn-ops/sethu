# Architecture Snapshot

## Repository Map

| Module | Language | Symbols | Exported |
|--------|----------|---------|----------|
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/alembic` | python | 2 | 1 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/alembic/versions` | python | 2 | 2 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app` | python | 2 | 2 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api` | python | 4 | 4 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/audit` | python | 3 | 3 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/core` | python | 12 | 11 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/db` | python | 4 | 4 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/scripts` | python | 1 | 1 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/seed` | python | 7 | 7 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/web` | typescript | 1 | 1 |
| `.claude/worktrees/mock-data-generator-loader-5238d1/web/src` | typescript | 2 | 1 |
| `backend/alembic` | python | 2 | 1 |
| `backend/alembic/versions` | python | 2 | 2 |
| `backend/app` | python | 2 | 2 |
| `backend/app/api` | python | 4 | 4 |
| `backend/app/audit` | python | 3 | 3 |
| `backend/app/core` | python | 12 | 11 |
| `backend/app/db` | python | 4 | 4 |
| `scripts` | python | 1 | 1 |
| `web` | typescript | 1 | 1 |
| `web/src` | typescript | 2 | 1 |

## Extraction Quality

- Files parsed: **77** / 146 seen (12 file(s) + 3 directory tree(s) skipped by ignore globs)
- Parse errors: 0

## Architecture Pattern

_No specific architecture pattern detected._

## Entry Points

- **main**: `.claude/worktrees/mock-data-generator-loader-5238d1/scripts/init_env.main` (.claude/worktrees/mock-data-generator-loader-5238d1/scripts/init_env.py)
- **main**: `scripts/init_env.main` (scripts/init_env.py)
- **route** GET `/api/v1/audit/verify` (.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api/routes.py)
- **route** GET `/api/v1/audit/verify` (backend/app/api/routes.py)
- **route** GET `/api/v1/me` (.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api/routes.py)
- **route** GET `/api/v1/me` (backend/app/api/routes.py)
- **route** GET `/health/live` (.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api/routes.py)
- **route** GET `/health/live` (backend/app/api/routes.py)
- **route** GET `/health/ready` (.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api/routes.py)
- **route** GET `/health/ready` (.claude/worktrees/mock-data-generator-loader-5238d1/web/src/App.tsx)
- **route** GET `/health/ready` (backend/app/api/routes.py)
- **route** GET `/health/ready` (web/src/App.tsx)

## Routes

| Method | Path | File | Type |
|--------|------|------|------|
| GET | `/api/v1/audit/verify` | `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api/routes.py` |  |
| GET | `/api/v1/audit/verify` | `backend/app/api/routes.py` |  |
| GET | `/api/v1/me` | `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api/routes.py` |  |
| GET | `/api/v1/me` | `backend/app/api/routes.py` |  |
| GET | `/health/live` | `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api/routes.py` |  |
| GET | `/health/live` | `backend/app/api/routes.py` |  |
| GET | `/health/ready` | `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api/routes.py` |  |
| GET | `/health/ready` | `.claude/worktrees/mock-data-generator-loader-5238d1/web/src/App.tsx` |  |
| GET | `/health/ready` | `backend/app/api/routes.py` |  |
| GET | `/health/ready` | `web/src/App.tsx` |  |

## Dependency Rules

- `.claude/worktrees/mock-data-generator-loader-5238d1/backend/alembic/versions` -> `backend/alembic`
- `.claude/worktrees/mock-data-generator-loader-5238d1/backend/alembic` -> `backend/alembic`
- `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api` -> `backend/app/audit`
- `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app` -> `backend/app/audit`
- `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app` -> `backend/app/core`
- `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app` -> `backend/app/db`
- `.claude/worktrees/mock-data-generator-loader-5238d1/backend` -> `backend/app/core`
- `.claude/worktrees/mock-data-generator-loader-5238d1/backend` -> `backend/app/db`
- `.claude/worktrees/mock-data-generator-loader-5238d1` -> `backend/app/audit`
- `.claude/worktrees/mock-data-generator-loader-5238d1` -> `backend/app/core`
- `.claude/worktrees/mock-data-generator-loader-5238d1` -> `backend/app/db`
- `backend/alembic/versions` -> `backend/alembic`
- `backend/alembic` -> `.claude/worktrees/mock-data-generator-loader-5238d1/backend/alembic`
- `backend/app/api` -> `backend/app/audit`
- `backend/app` -> `backend/app/audit`
- `backend/app` -> `backend/app/core`
- `backend/app` -> `backend/app/db`
- `backend` -> `backend/app/core`
- `backend` -> `backend/app/db`

## Critical Modules

| Module | Fan-In | Fan-Out | Criticality |
|--------|--------|---------|-------------|
| `backend/app/core` | 8 | 0 | medium |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app` | 0 | 5 | medium |
| `backend/app/audit` | 5 | 0 | medium |
| `backend/app/db` | 5 | 0 | medium |
| `backend/alembic` | 3 | 1 | low |
| `backend/app` | 0 | 4 | low |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/alembic` | 1 | 1 | low |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/alembic/versions` | 0 | 1 | low |
| `.claude/worktrees/mock-data-generator-loader-5238d1/backend/app/api` | 0 | 1 | low |
| `backend/alembic/versions` | 0 | 1 | low |

---

*Generated at 2026-11-15T19:50:23Z in 759.8708ms. 650 facts, 31 insights.*
