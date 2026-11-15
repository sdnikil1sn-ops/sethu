# Data Model

All tables live in schema `sethu`, created by `backend/alembic/versions/0001_core_schema.py`.

## Tables

| Table | Holds | Notes |
|---|---|---|
| `bureaus` | PGRC, RB and others | `code` unique |
| `app_users` | Local profile of a Keycloak user | `subject` = OIDC `sub`; role and bureau mirror token claims |
| `institutions` | Canonical institution | `permanent_id` unique; trigram index on `name` |
| `institution_aliases` | Spellings seen for an institution | trigram index; feeds the resolution cascade |
| `complaints` | One complaint | `bureau_id` owner; `institution_name_raw` as typed; `resolution_state`; `body_sha256` for duplicates; `complainant_enc` encrypted by the application; **Row-Level Security** |
| `case_actions` | Timeline of a complaint | insert-only for the app role; transfers carry `from`/`to` bureau and `acknowledged_at`; **Row-Level Security** |
| `overlap_links` | A proposed or decided link between two complaints | `tier` 1 to 3, `score`, `reasons`, `status`, who decided |
| `alerts` | Outbox of emails | `pending_approval -> approved -> sent` (or `rejected`, `failed`) |
| `audit_log` | Hash-chained ledger | append-only; see ARCHITECTURE section 6 |
| `complaint_summaries` (view) | Complaint metadata without text | visible across bureaus |

`overlap_links` stores each pair once (`complaint_a < complaint_b`).

## Database roles

| Role | Used by | Can |
|---|---|---|
| `postgres` | Bootstrap only | Everything. Not used after first start. |
| `sethu_owner` | Alembic migrations | Own and alter the schema |
| `sethu_app` | API and workers | Read and write rows through RLS; INSERT and SELECT on `audit_log` and `case_actions`; no DDL; `NOBYPASSRLS` |
| `sethu_auditor` | Direct read access for auditors | SELECT on `audit_log`, summaries and reference data; run `audit_verify()` |
| `keycloak` | Keycloak | Its own `keycloak` database only |

## Request context and policies

The API sets three transaction-local settings: `app.user_id`, `app.role`, `app.bureau_id`.

| Table | Read | Write |
|---|---|---|
| `complaints` | own bureau, or role in `oversight`, `admin`, `auditor`, `system` | insert and update: own bureau for `officer` and `bureau_head`; any for `admin`, `system` |
| `case_actions` | if the parent complaint is readable | insert if the parent complaint is readable; never updated |

`system` is the worker identity. It cannot be obtained from a token: only the five human roles are accepted from Keycloak.

No context means every policy evaluates to false.

## Adding a table

1. New Alembic revision; never edit 0001.
2. If the table holds complaint content or personal data: `ENABLE ROW LEVEL SECURITY`, write policies using `sethu.ctx_role()`, `sethu.ctx_bureau()`, `sethu.ctx_sees_all()`.
3. Grant the minimum to `sethu_app`. History tables get no UPDATE or DELETE.
4. Add a test in `backend/tests/test_rls.py` that proves another bureau cannot read it.

## Planned additions

- `0002`: `complaint_embeddings` (`pgvector`) for Tier 2 matching.
- `attachments` metadata once object storage is chosen (ADR 0006).
- `audit_checkpoints` for the nightly head-hash anchor.
- Partition `audit_log` and `case_actions` by month when volumes justify it.
