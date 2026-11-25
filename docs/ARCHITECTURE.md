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
            |                                  |                |
       [ postgres 16 ]                     [ redis ]        [ ai-worker ]  registry, router, one model at a time
        schema sethu, RLS,                  job queue            |
        hash-chained audit log                          ======= ai network (internal, no internet) =======
                                                          (later: local model servers; nothing else)
```

`app`, `data` and `ai` are Docker `internal` networks: containers on them have no route out. That is how "data never leaves AICTE" is enforced by the platform instead of by promise. Only `web` touches the edge, and it holds no data.

## 2. Components

The AI layer (ai-worker, `backend/app/ai/`, `ai` zone, `sethu.ai_runs`) is described in [AI-PIPELINE.md](AI-PIPELINE.md).

| Component | Responsibility | Status |
|---|---|---|
| web (Nginx + React) | Serve the app, terminate TLS, proxy `/api` and `/auth`, rate-limit, set CSP | Built: Keycloak sign-in (PKCE), institutions, unmatched-names queue, dashboard, case list, case detail and actions, overlaps, alerts, audit log with Verify chain, top-bar search, reports with CSV export; the case list keeps its filters in the address. Run end to end in dev; the production TLS config is not yet run |
| backend (FastAPI) | HTTP API, role checks, business rules, audit writes | Built: config, auth, session context, audit, health, `institutions` (profile with Profile DNA, alias search, resolution cascade), `complaints` (case list, detail, history, actions), `overlaps` (Tier 1 view, Tier 2 suggestions, approval, alert outbox row), `alerts` (approval of held alerts, delivery), `dashboard` (counts, weekly trend, needs-attention list), `audit_view` (audit log browser, Verify chain), `search` (top-bar search over institutions and cases), `reports` (three reports, audited CSV export), `findings` (transfer loops, stalled transfers, queue bottlenecks, early-warning trend). Other features: Planned |
| worker (Celery) | Ingestion, matching, graph jobs, alert delivery, nightly audit verification | Built: nightly audit verify; institution resolution, Tier 2 overlap detection and deadlock/bottleneck detection every 5 minutes; alert delivery every 15 seconds. The rest: Planned |
| scheduler (Celery beat) | Puts the scheduled jobs on the queue; the worker runs them | Built: its own service, so workers scale without running jobs twice; holds a Redis lock, so a second scheduler refuses to start (`tests/test_scheduler.py`) |
| intake (module) | Complaints from portal APIs, uploads, the manual form and a spool folder | Built: one encrypted queue for every channel; worker validates, refuses exact duplicates, flags near duplicates, resolves the institution, files the case; retry with backoff, dead letters with Retry; primary and fallback sources with health on the Intake screen; no outbound call |
| graph (module) | Network-wide intelligence graph | Built: `GET /api/v1/graph`, aggregated to bureaus and institutions by default (5,200 extra complaints still give under 60 nodes, tested), complaints for expanded institutions; metadata only, overlap links, transfers and findings under Row-Level Security; Cytoscape.js bundled and loaded on demand |
| semantic overlap signal (overlaps, worker; vectors by the ai-worker) | Multilingual meaning similarity for Tier 2 suggestions (A3) | Built: AI task `match.complaints` through the router (E5, then trigram, then an officer); E5 vectors made by the ai-worker from the checksum-verified registry, labelled with model and version, never compared across versions; evidence and confidence on every suggestion; off switch gives trigram only; measured (docs/AI-PIPELINE.md, A3) |
| relationship graph (modules/graph, worker) | A4: edge table kept in step with its sources; task `graph.build` (NetworkX + Louvain, else CTE, else direct links) every 5 minutes when edges changed; communities, ego graphs, link explanations | Built: `sethu.graph_edges` with its sources' visibility; node cap (institution-bureau graph above it); measured (docs/AI-PIPELINE.md, A4) |
| workflow bottlenecks (modules/findings, worker) | A4: task `bottleneck.detect` (workflow graph of bureau and stage, else the rules); findings keep their structure and alert path, with explanation and path | Built |
| national early warning and map (modules/signals, worker) | A4: task `warning.detect` (DBSCAN over place and time, else weekly Z-score, else baseline ratio); signals with stable ids, lifecycle, held alerts; India map data | Built: numpy DBSCAN (no scikit-learn); state centroids and boundaries bundled from DataMeet (SECURITY row 53) |
| semantic (modules/semantic, ai-worker) | A3: embed, classify and resolve-by-meaning stages; re-embed job; classifier training, activation and roll-back; case-page suggestions and decisions | Built: providers in app/ai (e5, semantic, classify), shared suggestions and feedback in app/ai/suggestions.py |
| observability | Logs, metrics, sign-in events | Built: JSON logs with a request id on every line (edge to backend; task id in the worker), no text or secrets (tested over a request cycle); `/metrics` (Prometheus) on the internal network only; job runs in `job_runs`; Keycloak login and admin events on, failed sign-ins shown read-only on the Audit log screen. Not yet: central log store, a Prometheus server |
| enrichment, glossary, review (A2: `modules/enrichment`, `modules/glossary`) | Language, OCR, translation and glossary tags beside the original text; attachments; human review | Built: outbox row with each complaint, staged batches in the ai-worker, fallbacks to rules and people (docs/AI-PIPELINE.md, Phase A2) |
| AI layer (ai-worker, `app/ai`) | Model registry with checksums, one model in memory, router with fallback to a person, provenance | Built (A1, the foundation; stub providers only): docs/AI-PIPELINE.md |
| paged lists (`app/db/paging.py`) | Long lists stay fast as data grows | Built: cases, findings and overlaps a page at a time (default 50, at most 200) with a total counted up to 1,000 ("1,000+"); dashboard counts capped the same way; detectors write at most 500 new items per transaction |
| audit anchors (worker, audit) | Proof outside the database | Built: hourly append-only anchor export; comparison on the Audit log screen and by command |
| build and CI | Reproducible images and checks | Built: Python locked with hashes, npm by lock file, base images by digest, model by hash; GitHub Actions workflow (lint, tests, build, secret scan, dependency audit, image scan, Playwright); Playwright journeys pass locally. The workflow has not run on GitHub yet |
| case workflow (complaints, findings) | Assignment, deadlines, escalation, notes, closing and reopening | Built: current assignee on the case; category deadlines set by admin; `deadline_escalation` findings with an alert held for approval; notes readable by the holding bureau only; close reasons from a list; reopen with a reason and a fresh deadline; My cases and Workload screens |
| backup (production) | Encrypted backups of the `sethu` and `keycloak` databases | Built: `pg_dump` into gpg AES-256 with a key from the secret store, every 24 h, 14-day retention; restore drill passed (RUNBOOK section 4) |
| postgres | System of record, Row-Level Security, audit ledger | Built and tested (migrations 0001 to 0006) |
| keycloak | Login, roles, `bureau_id` claim | Built: dev realm (`infra/keycloak`) with demo users from the `demo-users` service; production realm (`infra/keycloak-prod`, no users, URIs from `PUBLIC_BASE_URL`) imported and checked on a production-mode test stack. MFA: planned |
| redis | Celery broker | Scaffolded |
| mailpit | Catches alert email in dev and demo | Built (dev profile): receives the alert emails, inbox at http://localhost:8025 |
| object storage | Complaint attachments | Planned (ADR 0006) |

## 3. Trust boundaries and how each is defended

1. **Browser to edge.** TLS 1.3 in production, CSP `default-src 'self'`, no third-party assets, per-IP rate limits.
2. **Edge to API.** Every `/api` call needs a Keycloak-signed JWT. The API checks signature, issuer, audience and expiry, and maps claims to a `Principal(role, bureau_id)`. Tokens with no SETHU role, or an officer token with no bureau, are rejected.
3. **API to database.** The API connects as `sethu_app`, which cannot create objects, cannot bypass Row-Level Security and cannot change the audit log. Each request runs in one transaction that carries the caller's role and bureau (`session_for`). Policies read that context, so a query that forgets a `WHERE bureau_id = ...` still returns only permitted rows. With no context set, policies return nothing (fail closed).
4. **Anyone to the audit log.** Only INSERT and SELECT are granted. The database, not the application, assigns sequence, time and hash. See section 6.
5. **Deployment to the internet.** There is no path. Application and data networks are internal.
6. **Administration.** In production the Keycloak admin console and the `master` realm are not on the public edge (404 there); nginx serves them on a second TLS port that Compose binds to the host's loopback, reached through an SSH tunnel (RUNBOOK section 7).
7. **Configuration.** In production the backend and worker refuse to start on a missing, placeholder or dev secret, an `http` issuer, the dev mail catcher, a `.test` sender or `SETHU_DEBUG` (`app/core/config.py`); the seed loader and the demo-user import refuse `SETHU_ENVIRONMENT=prod`. Errors name the variable, never its value.

## 4. Request flow (example: approve an overlap link)

1. Officer clicks Approve. Browser sends `POST /api/v1/overlaps/{id}/decision` (`approve` or `reject`) with a bearer token.
2. `require_roles("officer","bureau_head")` admits the caller; `get_session` opens a transaction and sets the context.
3. `overlaps.service.decide` loads the link (RLS shows it only to the two bureaus involved and the reading roles), sets `status='approved'`, inserts an `alerts` row in `approved` state addressed to the heads of both bureaus, and calls `audit.record("overlap.approve", ...)`. The alert holds case references, never complaint text. A rejection writes the decision and its audit entry, and no alert.
4. The transaction commits. Link, outbox row and audit entry are saved together or not at all.
5. Every 15 seconds the worker takes one `approved` alert at a time with `FOR UPDATE SKIP LOCKED` (so two workers never hold the same row), sends one email per recipient through the relay, records each email in the audit log, and marks the alert `sent`, all in one transaction. If a send fails, the alert stays `approved` with the attempt count and the error, the emails already sent stay recorded, and the next run sends only to the recipients not reached yet. A crash in the middle can repeat the emails of the alert in hand at most once (ADR 0004). Mail goes only to addresses that belong to active SETHU users; an alert with any other address is marked `failed` and nothing is sent.

## 5. Processing pipeline (worker)

```
source adapters -> intake -> language/translate* -> institution resolution -> classify*
                -> overlap detection (Tier 1 rule, Tier 2 similarity, Tier 3 duplicate)
                -> proposed links -> officer approval -> alert outbox -> email
                -> deadlock, bottleneck and category-spike detection (scheduled); graph, profile DNA, institution trend (on request)
```

`*` optional AI steps. Each has a deterministic fallback and a confidence threshold; below the threshold the item goes to an officer queue instead of being auto-accepted. The pipeline must pass its tests with every AI model switched off.

Overlap detection as built. Tier 1 is a view over case summaries (open cases at one institution held by two or more bureaus); nothing is stored and no link is suggested. Tier 2 is a worker job run as `system`, because it must compare the text of both bureaus: same institution, different bureaus, same category, both open, filed within 30 days, and `pg_trgm` similarity of the two texts of at least 0.30, computed inside PostgreSQL. Each new pair is stored as a `proposed` link (the suggestion shown to officers); a pair that was rejected is not suggested again. Tier 3 (duplicates) is not built.

Institution resolution cascade: exact permanent ID; exact alias within state or district; fuzzy match (`pg_trgm` picks candidates, Python's standard `difflib` ratio scores them; no extra dependency; auto-accept only at 95+ with a clear runner-up gap; complaints carry no state or PIN, so the district is used only when it was typed with the name); embedding match that must agree with the fuzzy step; otherwise an officer picks from the top five.

## 6. Audit ledger

Each row stores `prev_hash` and `hash = SHA-256(prev_hash, seq, ts, actor, role, action, entity, payload)`. A `BEFORE INSERT` trigger takes a lock, reads the last row and fills in `seq`, `ts`, `prev_hash` and `hash`, ignoring anything the client supplied. Triggers reject UPDATE, DELETE and TRUNCATE. `sethu.audit_verify()` walks the chain and returns the first broken sequence number. Since migration 0002 the trigger also takes `actor` and `actor_role` from the request context when one is set, so application code cannot record an entry under another person's name.

The audit screen (`audit_view`, for `auditor`, `oversight` and `admin`) lists entries newest first with filters, and its **Verify chain** button runs `sethu.audit_verify()`: it shows "chain intact, N entries" or the first broken sequence number with that row as it is stored now. Each verification is itself an `audit.verify` entry. Reading the ledger is limited to those roles by the API only: `audit_log` has no Row-Level Security, because the chain trigger must read the last row whoever inserts, and a policy hiding rows from officers would break their inserts. Entries hold identifiers and decisions, never complaint text (SECURITY.md row 18). The runbook has the tamper demonstration.

What this proves: any edit, deletion or reordering of past entries is detected, even if done by someone with owner rights who disables the triggers (tested). What it does not prove on its own: that the entire chain was not rebuilt from scratch by a database superuser. The mitigation is **Planned**: export the head hash nightly to write-once storage and email it to the auditor, so an outside copy anchors the chain.

## 7. Cross-bureau visibility without leaking content

Overlap detection needs to know that RB also holds a complaint about the same institution. It does not need RB's complaint text. So:

- `sethu.complaints` (text, encrypted complainant data): own bureau only, plus `oversight`, `admin`, `auditor`.
- `sethu.complaint_summaries` (reference, bureau, institution, category, status, dates): any authenticated role.

An officer sees *that* another bureau has a matching case and who to coordinate with, not what the complainant wrote. Tested in `tests/test_rls.py`.

The case screens follow the same rule. The case list joins the summaries to `sethu.complaints`, which Row-Level Security empties for rows the caller may not read, so free-text search can only match text the caller is allowed to see, and a case from another bureau opens with its summary fields only (no text, no history). Tested in `tests/test_cases.py`.

The top-bar search (`search`) works the same way. Institutions match by name or alias (pg_trgm), initials or city. Cases match by reference, category, status, bureau and institution for everyone, and by complaint text or the institution name as typed only through `c`, so only where Row-Level Security lets the caller read the case. Each hit says why it matched; a hit never carries complaint text. Tested in `tests/test_search.py`, including every other-bureau complaint's own words searched by a PGRC officer.

Complainant details are encrypted by the application (`app/core/crypto.py`, AES-256-GCM, key id in each value, the complaint id as associated data) with a keyring mounted as a secret. Case detail decrypts them only for the officers and head of the holding bureau (`complaints.service.complainant_visible`); the sender of an unacknowledged transfer, oversight, admin and auditor see "withheld", other bureaus not even that. No list, search, report, export, log line or audit entry carries them (`tests/test_complainant.py`). Keys rotate with `sethu.complainant.rotate_keys` (RUNBOOK).

Reports (`reports`) read only `complaint_summaries`, `overlap_links` and `alerts`, and have no column for text or complainant details. Bureau staff see their own bureau only: case figures are limited by `sethu.ctx_bureau()` in the query, because the summaries view is cross-bureau by design; overlap links and alerts are already limited by their policies. Each CSV export is an audit entry (`report.export`: report, date range, scope, row count) in the same transaction.

Transfers: the receiving bureau holds the case at once (`bureau_id`) with status `transferred`; the sender is kept in `transferred_from_bureau_id` and can still read the case until the receiver acknowledges, but only the holder can act on it. The database lets a bureau hand a case over only by naming itself as the sender. An acknowledgement is its own `case_actions` row (history is never updated), so an unacknowledged transfer is one with no acknowledgement after it. That is what deadlock detection reads.

Profile DNA is computed with each institution profile from the same case summaries the page already shows (every bureau, no text): category mix; volume (all cases, the last 12 months, the monthly average); recurrence (cases whose category was raised at the institution in the 180 days before); disposal time (median days from filing to closing); cases per bureau; and the last 90 days against the 90 before. They are counts, not a score or a judgement. Tested in `tests/test_institutions.py`.

Deadlock and bottleneck detection (`findings`) is a worker job run as `system` every 5 minutes, reading case actions and summaries only (no text). A transfer loop is a case whose latest actions are two or more transfers in a row, none acknowledged and nothing else done in between, that came back to a bureau it had left (seed case C-090). A stalled transfer is a latest transfer nobody has acknowledged for `SETHU_STALLED_TRANSFER_DAYS` (default 7). A bottleneck is a bureau's or an institution's set of open cases (at least `SETHU_BOTTLENECK_MIN_OPEN`, default 3) where more than `SETHU_BOTTLENECK_SHARE` (default 0.6) are overdue; for a bureau, also where more than that share are older than its median days to close (not used for institutions, where a few cases make it fire too easily). On freshly loaded seed data this gives 4 bottlenecks: both bureaus' queues (older than the median) and two institutions' (overdue). The Findings screen lists open findings first, then loops, stalled transfers and bottlenecks, the worst share first. Each finding is a row in `findings` with a `key` that names it, so a second run adds nothing; a finding that no longer holds is marked `resolved`, and reopened if it returns, with that day's numbers and bureaus (the `finding.reopened` audit entry carries them too). Loops and stalled transfers also put an alert in the outbox in `pending_approval`; a bureau head of an involved bureau or oversight releases it. Creation, resolution, reopening and a person's dismissal are each an audit entry. Early warning is a finding of kind `category_spike`, made by the same job: for each state and category, the complaints of the last 30 days against a baseline from the 90 days before, scaled to 30 days. It is flagged only when the count reaches `SETHU_SPIKE_MIN_COUNT` (default 5) and is at least `SETHU_SPIKE_RATIO` (default 3.0) times the baseline; with no complaints in the baseline the minimum alone decides. The finding stores the counts, the baseline, the ratio, both thresholds and the day they were taken (`as_of`); the screen says "in the 30 days to" that day, and its link opens exactly those 30 days; its bureaus are those that received the recent complaints, so the usual policy decides who sees it. It makes no alert. A complaint whose institution is not matched yet has no state and is not counted. On the seed exactly one cell is flagged: Uttar Pradesh / Fee refund, 10 complaints against a baseline of 2.67 (ratio 3.75); the next cells have 4. On screen it reads "Early warning: category spike" and says it is a comparison with past counts, not a forecast. Separately, an institution trend is computed on request: institutions whose new complaints in the last 30 days, coming to two or more bureaus, outnumber the 30 days before. It is shown as a trend indicator with its counts, not a prediction. The institution profile draws the institution, its bureaus, overlap links and open transfer loops in plain SVG from the same endpoints. Tested in `tests/test_findings.py`.

The Institutions screen and the top-bar search call one institution search (`institutions.service.lookup`): name or alias (pg_trgm, whole spelling or one word of it), permanent id, initials, city (district) or state. List filters share one rule (`app/core/params.py`): surrounding spaces are dropped and a blank value is no filter. Tested in `tests/test_filters.py`.

## 8. Module rules

- One package per feature under `backend/app/modules/`: `api.py` (HTTP, roles), `service.py` (rules, audit), `repo.py` (SQL), `schemas.py` (Pydantic).
- Dependencies point inward: `api -> service -> repo`. A module calls another module through its `service`, never its `repo` or tables.
- `core`, `db` and `audit` are shared kernel; they import no feature module.
- Bureaus are data (`sethu.bureaus`, seeded from `seed/bureaus.csv`): no application code branches on a bureau code. The seed has four (PGRC, RB, NRB, AB).
- Built modules: `users` (people kept in step with their tokens, admin list), `bureaus` (admin-managed), `institutions`, `complaints`, `overlaps`, `alerts`, `dashboard`, `audit_view`, `search`, `reports`. Planned modules: `intake`. (The graph is a web component over existing endpoints; Profile DNA is part of the `institutions` profile; bottlenecks and the early-warning trend live in `findings`.)

## 9. Failure behaviour

| Failure | Behaviour |
|---|---|
| Database down | `/health/ready` returns 503; API returns errors; nothing is half-written (single transaction per request) |
| Redis or worker down | API keeps working; jobs and alerts queue in PostgreSQL (outbox) and drain on recovery |
| Mail relay down | The alert stays `approved` with the error; the next attempt waits (1, 2, 4, 8... minutes, at most an hour); after `SETHU_ALERT_MAX_ATTEMPTS` (10, about 4 hours, so an hour-long outage heals itself) it becomes `failed` with the reason, and an admin or a head of a concerned bureau can Retry it (audited) |
| Keycloak down | Existing tokens work until expiry (5 minutes); new logins fail; no anonymous fallback |
| AI model missing or slow | Deterministic fallback runs; item is marked as fallback-processed |
| Unsafe production configuration | Backend and worker exit at start with the list of variables to fix; Compose restarts them until it is fixed; nothing is served half-configured |
| Audit chain broken | Nightly job logs an error and raises an admin alert; the ledger is never auto-repaired |

## 10. Scaling path (after the hackathon)

Stateless API and workers scale horizontally behind the edge. PostgreSQL gets a streaming replica for reports and PITR backups. Embedding and translation models move to a dedicated inference host on the app network. None of this changes module boundaries.

## 11. What has been verified

- Migrations 0001 to 0006 applied to PostgreSQL 16; the backend tests pass (hash chain, tamper detection, append-only, Row-Level Security, token validation, role gates, seed patterns, institution resolution, case visibility, case actions and their audit entries, overlap detection, approval and its alert, alert delivery to a fake SMTP relay with retry and no duplicates, dashboard counts against the seed and per-role visibility, audit screen roles and filters, Verify chain naming a tampered row and passing again after the runbook's restore, top-bar search including bureau isolation of complaint text, report scoping by role, date ranges, CSV export and its audit entry, every list filter through the API including blank values, the two institution searches agreeing, transfer-loop detection of C-090 with its held alert, no duplicates on a second run, findings scoped to the bureaus involved, dismiss and resolve audited).
- Web app type-checks and builds.
- A full `docker compose --profile dev up` on a fresh, isolated copy of the stack: realm import, demo-user import, seeding, sign-in through Nginx and Keycloak, the case list, case detail and one recorded action in a browser; the overlap worker task (6 suggestions on the seeded data of the time), one approval and its alert delivered to Mailpit (one email per bureau head), shown as sent on the Alerts page.
- A second full run on a fresh, isolated stack after the search, filter and findings work (one `up --build`, seed, then the three worker jobs: 27 names resolved, 6 overlap suggestions, 5 findings). In a browser as `rao` (officer), `fernandes` (bureau head), `menon` (oversight), `das` (auditor) and `admin` (runs the overlap and findings detectors, reads the audit log): the Institutions screen and the top-bar search agreeing; every case filter narrowing the list and writing itself into the address, the address reopening the same view in a new tab, and the Cases link and Clear filters restoring all 300 (the seed then had 300; it now has 310); Overlaps, Alerts, Reports (a reversed date range refused; scope "your bureau only" for `rao`, "all bureaus" for `menon`); Findings scoped by bureau and filtered; the C-090 loop drawn on the Meadowvale profile; a finding dismissed and reopened, and the C-090 alert approved and emailed to three heads; the audit log filters, those decisions under the person's name, and Verify chain intact. Every request the browser made went to the stack itself, and the backend and worker cannot resolve an outside address. Not covered: a CSV download in the browser, and a run with Wi-Fi actually switched off.
- Both Compose files parse (`docker compose config`).
- A production-mode stack (base file plus `docker-compose.prod.yml`, a self-signed certificate, random secrets, ports moved to 127.0.0.1:8443 and 9443): with a short password and Mailpit configured the backend exits naming both variables; with valid settings every service turns healthy, the token issuer is the https address, the app, `/api` health and the `sethu` sign-in answer on the public port, `/auth/admin/` and `/auth/realms/master/` return 404 there and 200 on the admin port, `/api/docs` is off, TLS 1.2 is refused, app pages carry the app's CSP and `X-Frame-Options: DENY` and `/auth` pages Keycloak's own. The production realm file imported into a throwaway Keycloak with the client URIs, `bureau_id` mapper, user-profile setting, brute-force, password and lifetime settings as written.
- On the dev stack in a browser: the Keycloak admin console loads and lists the realm's users (it used to hang on "Loading the Administration Console": the app's CSP and `DENY` applied to `/auth`, and the sign-in rate limit refused its burst of requests with 503).
- Signing in through the production realm on that stack, as a script doing what the browser does (the browser pane refuses the self-signed certificate): a test `oversight` user created with the admin tool; an unlisted redirect URI refused (400); the PKCE sign-in redirected back to the app; the access token carried the https issuer, the `sethu-api` audience, the role and a 300-second lifetime; `/api/v1/me` and `/api/v1/dashboard` answered 200 with it and 401 without; a refresh token used twice was refused the second time; sign-out returned to the app.
- **Not yet verified:** signing in through the production realm in a real browser, a real certificate, anything using `pgvector`, a real SMTP relay (only Mailpit and a fake relay in tests), a run with Wi-Fi switched off.
