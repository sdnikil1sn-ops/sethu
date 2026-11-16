# Data Model

All tables live in schema `sethu`, created by `backend/alembic/versions/0001_core_schema.py` and changed by `0002_case_tracking.py`, `0003_overlap_policies.py` and `0004_alert_approval.py`.

## Tables

| Table | Holds | Notes |
|---|---|---|
| `bureaus` | PGRC, RB and others | `code` unique |
| `app_users` | Local profile of a Keycloak user | `subject` = OIDC `sub`; role and bureau mirror token claims |
| `institutions` | Canonical institution | `permanent_id` unique; trigram index on `name` |
| `institution_aliases` | Spellings seen for an institution | trigram index; feeds the resolution cascade |
| `complaints` | One complaint | `bureau_id` owner; `institution_name_raw` as typed; `resolution_state`; `body_sha256` for duplicates; `complainant_enc` encrypted by the application; **Row-Level Security** |
| `case_actions` | Timeline of a complaint | insert-only for the app role; transfers carry `from`/`to` bureau; an acknowledgement is its own row (`acknowledged`, with `acknowledged_at`); `assignee_id` on assignments; **Row-Level Security** |
| `overlap_links` | A suggested or decided link between two complaints | `tier` (only 2 is stored today), `score`, `reasons`, `status` (`proposed` is the suggestion, then `approved` or `rejected`), who decided; **Row-Level Security** |
| `alerts` | Outbox of emails | `pending_approval -> approved -> sent` (or `rejected`, `failed`); an overlap alert is written already `approved`, by the approval of its link; each email sent is an `alert.delivered` audit entry; **Row-Level Security** |
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
| `complaints` | the bureau holding the case, the bureau named in `transferred_from_bureau_id` (sender of an unacknowledged transfer), or role in `oversight`, `admin`, `auditor`, `system` | insert: own bureau for `officer` and `bureau_head`. Update: only the holding bureau, and the new row must stay with it or name it as the sender (a transfer). Any for `admin`, `system` |
| `case_actions` | if the parent complaint is readable | insert: `officer` and `bureau_head` of the bureau holding the case, `admin`, `system` (not `oversight` or `auditor`); never updated |
| `overlap_links` | a party (a bureau holding one of the two cases), or role in `oversight`, `admin`, `auditor`, `system` | insert: `admin`, `system` (the detector). Update (the decision): `officer` and `bureau_head` of a party only |
| `alerts` | whoever can read the alert's link or its case | insert: `admin`, `system`, or `officer` and `bureau_head` for a link or case they can read. Update: `admin` and `system` (delivery); a `bureau_head` of a bureau the alert concerns, or `oversight`, may move a `pending_approval` alert to `approved` or `rejected`. Outside `admin` and `system` a trigger lets an update change only `status`, `approved_by` and `approved_at` |

The audit trigger reads the same context: `actor` and `actor_role` of a new `audit_log` row come from `app.user_id` and `app.role` when they are set.

`system` is the worker identity. It cannot be obtained from a token: only the five human roles are accepted from Keycloak.

No context means every policy evaluates to false. That includes a direct `sethu_auditor` login: it sees `overlap_links` and `alerts` only after setting `app.role` to `auditor` for its session.

## Adding a table

1. New Alembic revision; never edit 0001.
2. If the table holds complaint content or personal data: `ENABLE ROW LEVEL SECURITY`, write policies using `sethu.ctx_role()`, `sethu.ctx_bureau()`, `sethu.ctx_sees_all()`.
3. Grant the minimum to `sethu_app`. History tables get no UPDATE or DELETE.
4. Add a test in `backend/tests/test_rls.py` that proves another bureau cannot read it.

## Planned additions

- `complaint_embeddings` (`pgvector`) for Tier 2 matching.
- `attachments` metadata once object storage is chosen (ADR 0006).
- `audit_checkpoints` for the nightly head-hash anchor.
- Partition `audit_log` and `case_actions` by month when volumes justify it.
