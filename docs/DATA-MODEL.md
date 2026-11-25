# Data Model

All tables live in schema `sethu`, created by `backend/alembic/versions/0001_core_schema.py` and changed by the later revisions in the same folder (0002 to 0013; 0009 adds intake, 0010 the case workflow, 0011 digests and the intake quota, 0012 embeddings and overlap signals, 0013 job runs).

## Tables

| Table | Holds | Notes |
|---|---|---|
| `bureaus` | PGRC, RB, NRB, AB and any an admin adds | `code` unique and fixed once created; `active` (deactivated, never deleted: a deactivated bureau takes no transfers); managed on Admin > Bureaus, every change a `bureau.created` / `bureau.updated` audit entry; **Row-Level Security** |
| `app_users` | Local profile of a Keycloak user | `subject` = OIDC `sub`; name, e-mail, role and bureau brought in step with the token on every sign-in and action (`user.registered` / `user.updated` audit entries name the fields that changed, never values); alert mail goes to the stored e-mail; **Row-Level Security** |
| `institutions` | Canonical institution | `permanent_id` unique; trigram index on `name` |
| `institution_aliases` | Spellings seen for an institution | trigram index; feeds the resolution cascade |
| `complaints` | One complaint (`assignee_id`: who works it now; `due_at` from the category deadline) | `bureau_id` owner; `institution_name_raw` as typed; `resolution_state`; `body_sha256` for duplicates; `complainant_enc`: name, e-mail and phone, AES-256-GCM with the complaint id as associated data, the key id stored in the value (`app/core/crypto.py`); decrypted only for the officers and head of the holding bureau; never selected by search, lists or reports; **Row-Level Security** |
| `case_actions` | Timeline of a complaint (`reopened` action; `reason` on a closing, from a fixed list) | insert-only for the app role; transfers carry `from`/`to` bureau; an acknowledgement is its own row (`acknowledged`, with `acknowledged_at`); `assignee_id` on assignments; **Row-Level Security** |
| `overlap_links` | A suggested or decided link between two complaints | `tier` (only 2 is stored today), `score`, `reasons`, `signals` (trigram and meaning similarity, which fired, the model), `status` (`proposed` is the suggestion, then `approved` or `rejected`), who decided; **Row-Level Security** |
| `alerts` | Outbox of emails (`bureau_id`: a digest addressed to a bureau, for deadline escalations) | `pending_approval -> approved -> sent` (or `rejected`, `failed`); `missing_recipients` names the bureaus that had no head with an e-mail address; `next_attempt_at` holds the backoff after a failed send, and after the last attempt the status is `failed` (Retry: admin, or a head of a concerned bureau); an overlap alert is written already `approved`, by the approval of its link; each email sent is an `alert.delivered` audit entry; a deadlock finding writes a `bottleneck` alert in `pending_approval`; **Row-Level Security** |
| `findings` | What the deadlock, bottleneck and early-warning detectors found | `kind` (`transfer_loop`, `stalled_transfer`, `bottleneck`, `category_spike`: a state and category above its own baseline, no case or institution, evidence holds state, category, counts, baseline, ratio and thresholds), unique `key` (no duplicates), the case or institution, `bureau_ids` involved, `evidence` (action ids and the numbers used, never text), `alert_id`, `status` (`open`, `resolved` by the detector, `dismissed` by a person); **Row-Level Security** |
| `category_deadlines` | Days to close a case, per category | set by admin (`deadline.set` audited); a category without a row uses `SETHU_SLA_DAYS`; used when a case is filed or reopened |
| `intake_sources` | Where complaints come from | `channel` (`api`, `upload`, `manual`, `spool`), `bureau_id` it feeds, `priority`, `fallback_source_id`, `active`, `marked_down`, `rate_per_minute` (intake API quota; empty: the default); `key_sha256` (an api source's key, hash only); health: `last_success_at`, `last_failure_at`, `failures` in a row |
| `intake_items` | The intake queue | one row per incoming complaint, any channel; `payload_enc` (the complaint and complainant, AES-256-GCM with the complainant keyring, item id as associated data); `fingerprint`, `external_ref`, `path` (`primary`/`fallback`), `status` (`pending`, `done`, `duplicate`, `dead`), `attempts`, `next_attempt_at`, `last_error` (a reason without values), `complaint_id`, `duplicate_of`, `near_duplicate_of` and `review_state` |
| `intake_nonces` | Nonces used by intake API requests | (source, nonce) primary key: a replay is refused; older than 10 minutes forgotten |
| `complaint_embeddings` | One vector (384 dimensions) per complaint, `embedding_model` and `embedding_version` (A3: all three are the key; vectors of different models or versions are never compared) | computed by the ai-worker from the original text; readable exactly where the complaint is (Row-Level Security reads `complaints`); written by `system`/`admin` only; never returned by an API |
| `institution_embeddings` (A3) | One vector per registry name, "name, district" and alias (any script), per model and version | `system`/`admin` only (read, insert, delete) |
| `match_evaluations` (A3) | The last verdict on each rule-allowed pair (matched, method, score, confidence, `ai_runs` row) and the key it was made under | read by the bureaus party to the pair and the roles that see everything; written by `system`/`admin` |
| `ai_suggestions` (A3) | The AI's category and institution for a complaint: suggestion, top candidates, path (model, fallback, officer), confidence, status | read where the complaint's text is; written by `system`/`admin`; decided by the holding bureau's officers and heads |
| `ai_feedback` (A3) | Every officer decision on a category, institution or overlap suggestion: who, when, suggested, old, new | append-only (no UPDATE or DELETE grant); inserted by the case's bureau or `system`/`admin`; each row audited |
| `graph_edges` (A4) | One row per relationship, each from one complaint: about, held_by, handled_by, transfer, overlap; method, confidence, model version, evidence ids | visible as its source: summary edges to every signed-in role, transfers as `case_actions`, overlaps as `overlap_links`; written by `system`/`admin` |
| `graph_runs`, `graph_communities` (A4) | Each graph build (method, sizes, time, memory) and the Louvain community of each institution and bureau (never complaints) | read by every signed-in role; written by `system`/`admin` |
| `warning_signals` (A4) | "Emerging signal: requires verification": group, states, window, method, score, member ids, explanation, parameters, lifecycle, held alert ids | read by the roles that see everything and the bureaus whose cases are in it; decided by oversight and those bureaus' heads (status columns only, by trigger); written by `system`/`admin` |
| `classifier_versions` (A3) | Trained category classifiers: a fixed-shape JSON artifact with its SHA-256, metrics, status (one active) | read by `admin`, `system`, `oversight`, `auditor`; written by `system`/`admin`; the artifact cannot be changed by the application role |
| `job_runs` | When each scheduled job (and the backup) last ran and succeeded | for `/metrics`; written by the worker and the backup service; counts and times only |
| `audit_log` | Hash-chained ledger | append-only; no Row-Level Security (the chain trigger reads the last row as whoever inserts); the API shows it to `auditor`, `oversight` and `admin` only; each report export is a `report.export` entry and each finding change a `finding.*` entry; see ARCHITECTURE section 6 |
| `complaint_summaries` (view) | Complaint metadata without text | visible across bureaus; the dashboard's needs-attention list and the reports narrow it to the caller's bureau with `sethu.ctx_bureau()` in the query (a filter, not a policy) |

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
| `case_actions` | if the parent complaint is readable; a `note` only by `officer`/`bureau_head` of the bureau holding the case now, and `system` (migration 0010) | insert: `officer` and `bureau_head` of the bureau holding the case, `admin`, `system` (not `oversight` or `auditor`); never updated |
| `overlap_links` | a party (a bureau holding one of the two cases), or role in `oversight`, `admin`, `auditor`, `system` | insert: `admin`, `system` (the detector). Update (the decision): `officer` and `bureau_head` of a party only |
| `findings` | a bureau in `bureau_ids`, or role in `oversight`, `admin`, `auditor`, `system` | insert: `admin`, `system` (the detector). Update: `admin`, `system`; a `bureau_head` of an involved bureau, or `oversight`, may set `open` or `dismissed`, and a trigger lets them change only `status`, `decided_by`, `decided_at` |
| `category_deadlines` | any signed-in role | insert and update: `admin`, `system` |
| `intake_sources` | `oversight`, `admin`, `auditor`, `system`, the `intake` gateway, and `officer`/`bureau_head` of its bureau | insert: `admin` (and `system` for the dev seed); update: `admin`, `system` (health) |
| `intake_items` | `oversight`, `admin`, `auditor`, `system`; `officer`/`bureau_head` of its bureau; the `intake` gateway, `api` items only (to refuse a resubmission) | insert: `admin`, `system`; bureau staff for `upload`/`manual` into their bureau; the gateway for `api` into an active api source's bureau. Update: `admin`, `system`; bureau staff may only mark a near duplicate reviewed (guard trigger) |
| `intake_nonces` | the `intake` gateway, `system` | the same |
| `bureaus` | any signed-in role | insert and update: `admin`, `system` (no delete) |
| `app_users` | any signed-in role | a person inserts or updates only their own row (`subject` = `sethu.ctx_subject()`), and only with the role and bureau of their token; `admin`, `system`: any row |
| `alerts` | whoever can read the alert's link or its case, or staff of the bureau a digest is addressed to (`bureau_id`, migration 0011) | insert: `admin`, `system`, or `officer` and `bureau_head` for a link or case they can read. Update: `admin` and `system` (delivery); a `bureau_head` of a bureau the alert concerns, or `oversight`, may move a `pending_approval` alert to `approved` or `rejected`. Outside `admin` and `system` a trigger lets an update change only `status`, `approved_by` and `approved_at` |

The audit trigger reads the same context: `actor` and `actor_role` of a new `audit_log` row come from `app.user_id` and `app.role` when they are set.

`system` is the worker identity. It cannot be obtained from a token: only the five human roles are accepted from Keycloak. `intake` is the intake API gateway (`app/modules/intake/service.py`): used only by `POST /api/v1/intake/submissions` after nothing but an API key has been presented, so it reads no complaints and writes only api queue items and nonces. `IN-` references come from the sequence `complaint_ref_seq`.

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
