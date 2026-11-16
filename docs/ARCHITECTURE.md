# Architecture

Status key: **Built** (in this repo and tested), **Scaffolded** (in this repo, not yet run end to end), **Planned** (designed, not written).

## 1. Shape

A modular monolith with a worker pool, deployed as containers on one AICTE-controlled host (or VM pair). One codebase, one database, clear module boundaries. A six-person team in a hackathon cannot operate microservices, and nothing in the problem statement needs them (ADR 0001).

```
                 officers' browsers
                        |
        ============ edge network ============            (only published port)
                        |
                   [ web / nginx ]   static app, TLS, rate limits, security headers
                        |
        ============ app network (internal, no internet) ============
            |                 |                |              |
       [ backend ]       [ keycloak ]     [ worker ]     [ mailpit* ]
        FastAPI           OIDC, roles      Celery          *dev only
            |                 |                |
        ============ data network (internal, no internet) ============
            |                                  |
       [ postgres 16 ]                     [ redis ]
        schema sethu, RLS,                  job queue
        hash-chained audit log
```

`app` and `data` are Docker `internal` networks: containers on them have no route out. That is how "data never leaves AICTE" is enforced by the platform instead of by promise. Only `web` touches the edge, and it holds no data.

## 2. Components

| Component | Responsibility | Status |
|---|---|---|
| web (Nginx + React) | Serve the app, terminate TLS, proxy `/api` and `/auth`, rate-limit, set CSP | Built: Keycloak sign-in (PKCE), institutions, unmatched-names queue, case list, case detail and actions. Run end to end in dev; the production TLS config is not yet run |
| backend (FastAPI) | HTTP API, role checks, business rules, audit writes | Built: config, auth, session context, audit, health, `institutions` (profile, alias search, resolution cascade), `complaints` (case list, detail, history, actions). Other features: Planned |
| worker (Celery) | Ingestion, matching, graph jobs, alert delivery, nightly audit verification | Built: nightly audit verify, institution resolution every 5 minutes. The rest: Planned |
| postgres | System of record, Row-Level Security, audit ledger | Built and tested (migrations 0001, 0002) |
| keycloak | Login, MFA, roles, `bureau_id` claim | Built for dev: realm imports, demo users are created by the `demo-users` service. Production realm settings: not yet run |
| redis | Celery broker | Scaffolded |
| mailpit | Catches alert email in dev and demo | Scaffolded |
| object storage | Complaint attachments | Planned (ADR 0006) |

## 3. Trust boundaries and how each is defended

1. **Browser to edge.** TLS 1.3 in production, CSP `default-src 'self'`, no third-party assets, per-IP rate limits.
2. **Edge to API.** Every `/api` call needs a Keycloak-signed JWT. The API checks signature, issuer, audience and expiry, and maps claims to a `Principal(role, bureau_id)`. Tokens with no SETHU role, or an officer token with no bureau, are rejected.
3. **API to database.** The API connects as `sethu_app`, which cannot create objects, cannot bypass Row-Level Security and cannot change the audit log. Each request runs in one transaction that carries the caller's role and bureau (`session_for`). Policies read that context, so a query that forgets a `WHERE bureau_id = ...` still returns only permitted rows. With no context set, policies return nothing (fail closed).
4. **Anyone to the audit log.** Only INSERT and SELECT are granted. The database, not the application, assigns sequence, time and hash. See section 6.
5. **Deployment to the internet.** There is no path. Application and data networks are internal.

## 4. Request flow (example: approve an overlap link)

1. Officer clicks Approve. Browser sends `POST /api/v1/overlaps/{id}/approve` with a bearer token.
2. `require_roles("officer","bureau_head")` admits the caller; `get_session` opens a transaction and sets the context.
3. `overlaps.service.approve` loads the link (RLS decides visibility), sets `status='approved'`, inserts an `alerts` row in `pending_approval` or `approved` state, and calls `audit.record("overlap.approve", ...)`.
4. The transaction commits. Link, outbox row and audit entry are saved together or not at all.
5. The worker picks up approved outbox rows, sends mail through the relay, marks them `sent`, and audits the send. A crash between steps re-sends at most once more; nothing is lost (ADR 0004).

## 5. Processing pipeline (worker)

```
source adapters -> intake -> language/translate* -> institution resolution -> classify*
                -> overlap detection (Tier 1 rule, Tier 2 similarity, Tier 3 duplicate)
                -> proposed links -> officer approval -> alert outbox -> email
                -> graph, bottleneck, profile DNA, early-warning jobs (scheduled)
```

`*` optional AI steps. Each has a deterministic fallback and a confidence threshold; below the threshold the item goes to an officer queue instead of being auto-accepted. The pipeline must pass its tests with every AI model switched off.

Institution resolution cascade: exact permanent ID; exact alias within state or district; fuzzy match (`pg_trgm` picks candidates, Python's standard `difflib` ratio scores them; no extra dependency; auto-accept only at 95+ with a clear runner-up gap; complaints carry no state or PIN, so the district is used only when it was typed with the name); embedding match that must agree with the fuzzy step; otherwise an officer picks from the top five.

## 6. Audit ledger

Each row stores `prev_hash` and `hash = SHA-256(prev_hash, seq, ts, actor, role, action, entity, payload)`. A `BEFORE INSERT` trigger takes a lock, reads the last row and fills in `seq`, `ts`, `prev_hash` and `hash`, ignoring anything the client supplied. Triggers reject UPDATE, DELETE and TRUNCATE. `sethu.audit_verify()` walks the chain and returns the first broken sequence number. Since migration 0002 the trigger also takes `actor` and `actor_role` from the request context when one is set, so application code cannot record an entry under another person's name.

What this proves: any edit, deletion or reordering of past entries is detected, even if done by someone with owner rights who disables the triggers (tested). What it does not prove on its own: that the entire chain was not rebuilt from scratch by a database superuser. The mitigation is **Planned**: export the head hash nightly to write-once storage and email it to the auditor, so an outside copy anchors the chain.

## 7. Cross-bureau visibility without leaking content

Overlap detection needs to know that RB also holds a complaint about the same institution. It does not need RB's complaint text. So:

- `sethu.complaints` (text, encrypted complainant data): own bureau only, plus `oversight`, `admin`, `auditor`.
- `sethu.complaint_summaries` (reference, bureau, institution, category, status, dates): any authenticated role.

An officer sees *that* another bureau has a matching case and who to coordinate with, not what the complainant wrote. Tested in `tests/test_rls.py`.

The case screens follow the same rule. The case list joins the summaries to `sethu.complaints`, which Row-Level Security empties for rows the caller may not read, so free-text search can only match text the caller is allowed to see, and a case from another bureau opens with its summary fields only (no text, no history). Tested in `tests/test_cases.py`.

Transfers: the receiving bureau holds the case at once (`bureau_id`) with status `transferred`; the sender is kept in `transferred_from_bureau_id` and can still read the case until the receiver acknowledges, but only the holder can act on it. The database lets a bureau hand a case over only by naming itself as the sender. An acknowledgement is its own `case_actions` row (history is never updated), so an unacknowledged transfer is one with no acknowledgement after it. That is what deadlock detection will read.

## 8. Module rules

- One package per feature under `backend/app/modules/`: `api.py` (HTTP, roles), `service.py` (rules, audit), `repo.py` (SQL), `schemas.py` (Pydantic).
- Dependencies point inward: `api -> service -> repo`. A module calls another module through its `service`, never its `repo` or tables.
- `core`, `db` and `audit` are shared kernel; they import no feature module.
- Built modules: `institutions`, `complaints`. Planned modules: `intake`, `overlaps`, `alerts`, `dashboard`, `reports`, `graph`, `bottlenecks`, `profile_dna`, `early_warning`.

## 9. Failure behaviour

| Failure | Behaviour |
|---|---|
| Database down | `/health/ready` returns 503; API returns errors; nothing is half-written (single transaction per request) |
| Redis or worker down | API keeps working; jobs and alerts queue in PostgreSQL (outbox) and drain on recovery |
| Mail relay down | Outbox rows stay `approved`, attempts are counted, retried with backoff, surfaced on the dashboard |
| Keycloak down | Existing tokens work until expiry (5 minutes); new logins fail; no anonymous fallback |
| AI model missing or slow | Deterministic fallback runs; item is marked as fallback-processed |
| Audit chain broken | Nightly job logs an error and raises an admin alert; the ledger is never auto-repaired |

## 10. Scaling path (after the hackathon)

Stateless API and workers scale horizontally behind the edge. PostgreSQL gets a streaming replica for reports and PITR backups. Embedding and translation models move to a dedicated inference host on the app network. None of this changes module boundaries.

## 11. What has been verified

- Migrations 0001 and 0002 applied to PostgreSQL 16; 55 backend tests pass (hash chain, tamper detection, append-only, Row-Level Security, token validation, role gates, seed patterns, institution resolution, case visibility, case actions and their audit entries).
- Web app type-checks and builds.
- A full `docker compose --profile dev up` on a fresh, isolated copy of the stack: realm import, demo-user import, seeding, sign-in through Nginx and Keycloak, the case list, case detail and one recorded action in a browser.
- Both Compose files parse (`docker compose config`).
- **Not yet verified:** the production TLS override and production realm settings, anything using `pgvector`, mail delivery, and the Keycloak login page under the Nginx content security policy (it logs blocked inline scripts; sign-in still works).
