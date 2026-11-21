# Security review (Phase 5)

Date: 2026-11-21. Scope: this repository (backend FastAPI and PostgreSQL Row-Level Security, web React, nginx, Keycloak realm files, Docker Compose, CI workflow). Standard: OWASP Top 10:2025.

## Method

1. **Static review**, following attacker-controlled data from each entry point to its sink: every HTTP route and its role dependency (48 routes; all but the intake API carry `require_roles`, which authenticates by API key instead), the Row-Level Security policies in the Alembic revisions, every SQL string built with an f-string, the intake channels (API, upload, manual form, spool folder), the web client's token handling, nginx, the realm files and the images.
2. **Tests**: a regression test for each fixed finding (`backend/tests/test_security.py`), plus the existing suites (Row-Level Security, intake, observability log scan, anchors).
3. **Live checks on a dev stack** (2026-11-21), noted with each item: the spool attack inside the worker container, CORS, rate limits, the edge's exposure of `/health` and the API description.
4. **Earlier scans, same day** (Phase 4): `pip-audit` (no known vulnerabilities), `npm audit --audit-level=high` (0), Trivy on both images (0 fixable HIGH or CRITICAL), gitleaks (no leaks).

Not done: a penetration test of the deployed system, a review of Keycloak's own code and forms (its CSRF and login flows), TLS cipher scanning of a real deployment, and cloud or host configuration (there is none in the repository).

## Summary

| Severity | Found | Fixed | Accepted or open |
|---|---|---|---|
| Critical | 0 | - | - |
| High | 1 | 1 | 0 |
| Medium | 1 | 1 | 0 |
| Low | 4 | 2 | 2 |
| Informational | 5 | - | 5 (notes) |

Confidence is given per finding. Everything marked "fixed" has a regression test or a recorded live check; nothing here is claimed without one.

## Findings

### OWASP-A01-001 Spool folder: a symbolic link is followed and the target's first line echoed back (CWE-59, Improper Link Resolution Before File Access)

- **Severity: High.** Whoever can write to the spool folder (a portal's file-transfer account, by design a semi-trusted party) could read files the worker can read, including the mounted complainant keyring. **Confidence: High** (traced and reproduced).
- **Where**: `backend/app/modules/intake/service.py`, `spool()` selected files with `Path.is_file()` (follows links) and read them with `read_bytes()`; `parse_rows()` put an unrecognised header line into the error message, which `spool()` wrote to `rejected/<file>.errors.txt` inside the same folder.
- **Path**: drop `steal.csv -> /run/secrets/complainant_keys` into `<spool>/<source>/`; the worker reads the keyring, its first line is the "header", the error file repeats it.
- **Fix**: `read_plain_file()` refuses a link (`is_symlink`, `O_NOFOLLOW`, `S_ISREG` after open) and checks the size before reading; the header error names an unknown column only if it looks like one (`^[a-z][a-z0-9_ ]{0,39}$`), otherwise counts them.
- **Verified**: `test_a01_001_a_link_in_the_spool_folder_is_refused_unread`, `test_a01_001_an_unknown_header_is_not_echoed`; live in the worker container (Linux): a link to `/run/secrets/complainant_keys` was moved to `rejected/` with "not a regular file (a link): refused without reading it" and no key material in any file.

### OWASP-A06-001 XLSX expansion and row count not bounded before parsing (CWE-409, Improper Handling of Highly Compressed Data)

- **Severity: Medium.** An officer upload or a spooled file of under 2 MB could expand to gigabytes, or hold millions of rows, and exhaust the backend's or worker's memory (container restart; queued work is kept). **Confidence: High.**
- **Where**: `parse_rows()` checked the compressed size only, then materialised every row before checking the row limit.
- **Fix**: the zip's total uncompressed size must be at most `SETHU_INTAKE_MAX_XLSX_EXPANDED_BYTES` (20 MB) before openpyxl opens it; rows are streamed and reading stops at the row limit.
- **Verified**: `test_a06_001_a_spreadsheet_that_expands_too_far_is_refused_before_parsing` (a 21 MB-expanding file under 2 MB is refused with 413), `test_a06_001_the_row_limit_is_enforced_while_reading`.

### OWASP-A02-001 The API description was served through the edge in dev (CWE-200, Exposure of Sensitive Information to an Unauthorized Actor)

- **Severity: Low** (dev and demo stacks only; production already switched it off). **Confidence: High.**
- **Fix**: OpenAPI and its page now live at the backend's own `/docs` and `/openapi.json`, outside `/api/`, which is all the edge proxies; available on the internal network in every environment (docs/API.md).
- **Verified**: `test_a02_001_the_api_description_is_not_under_the_proxied_path`; live: edge `/api/docs` 404, backend `/docs` 200 from inside the container.

### OWASP-A02-002 `/health/ready` reachable from outside (CWE-200)

- **Severity: Low** (it says whether the database is up). **Confidence: High.** Readiness row 35.
- **Fix**: the edge answers 404 for `/health/*`; container health checks call the backend directly. **Verified** live: edge `/health/ready` 404.

### OWASP-A02-003 CSP allows inline styles (CWE-1021 family; style injection only)

- **Severity: Low. Accepted risk** (readiness row 23): React and Cytoscape set inline styles; scripts remain `'self'` only, so no script injection follows from it.

### OWASP-A02-004 Dev realm is looser than production

- **Severity: Low. Accepted** (dev only): wildcard redirect URI `http://localhost:8080/*`, `sslRequired: external`, no maximum session length. The production realm has exact URIs, `sslRequired: all`, a 10-hour maximum and refresh-token rotation; the demo-user import and the seed refuse production.

### Informational

- **A01 transfer sender sees the receiver's staff list.** While a transfer is unacknowledged, the sending bureau can still read the case (by design) and so `GET /cases/{id}/assignees` returns the receiving bureau's officer names. Names and roles of staff only; no action is possible. Left as is.
- **A07 rate limits are per client address.** nginx limits `/api/` to 20 requests a second (burst 40) and `/auth/` to 5 (burst 20) per address; live burst: 20 of 120 API requests and 31 of 60 sign-in-path requests got 429. Behind a shared NAT one office shares the budget. Keycloak also locks an account after 5 failures. The intake API has a per-source quota.
- **A01 CSRF and CORS: not applicable / closed.** The API takes a bearer token from the `Authorization` header, never a cookie, so a cross-site form cannot act as the user. No CORS middleware: live, a request with `Origin: https://evil.example` got no `Access-Control-Allow-*` header and the preflight was refused (405). Keycloak's own forms carry its CSRF protection (not reviewed).
- **A10 audit chain under concurrency and truncation.** Every insert takes `pg_advisory_xact_lock` before reading the chain head, so writers are serialised: `test_a10_001_concurrent_writers_keep_the_audit_chain_whole` (8 writers, 80 entries, contiguous numbers, chain verifies). The runtime role has no `TRUNCATE`, `UPDATE` or `DELETE` on the ledger and triggers refuse them; the owner role could still disable a trigger, which the hourly anchors outside the database now expose (`tests/test_anchor.py`).
- **A09 alerting.** Security events are logged (401, 403, replays, failed sign-ins, quota refusals) and thresholds are documented, but no alerting system is deployed (readiness row 32).

## Areas checked with no finding

| Category | What was checked |
|---|---|
| A01 Broken access control | Every route's role dependency; Row-Level Security on complaints, history and notes, overlap links, alerts (including digests), findings, intake sources and items, embeddings, job runs; IDOR on case, note, graph, intake item, admin and report endpoints (the database refuses or hides rows; tested in `test_rls.py`, `test_workflow.py`, `test_graph.py`, `test_intake.py`, `test_semantic.py`); path traversal in upload names (only the extension is read) and spool source names (pattern-checked); no open redirect (exact URIs in production). |
| A02 Misconfiguration | Debug refused in production; security headers in both nginx configs; containers read-only with dropped capabilities; secrets as files; `/metrics` internal only; no secrets in the images (checked: only system CA certificates). |
| A03 Supply chain | Lock files with hashes, images by digest, actions by commit SHA; same-day pip-audit, npm audit and Trivy clean. |
| A04 Cryptography | AES-256-GCM for complainant details with the complaint id as associated data; API keys are 256-bit random values stored as SHA-256; TLS 1.3 at the production edge; JWT signature verified against the realm's keys. |
| A05 Injection | SQL strings built with f-strings interpolate only names from code (filter dictionaries, column lists), every value is a bound parameter; LIKE patterns escaped; no `dangerouslySetInnerHTML` or `innerHTML`; CSV export neutralises formulas; no shell call with user input. |
| A07 Authentication | Tokens verified for signature, issuer, audience, expiry, issued-at and subject, algorithms limited to RS256 and ES256; the web keeps tokens in memory only (PKCE verifier briefly in sessionStorage); 5-minute access tokens; brute-force protection. |
| A08 Integrity | Celery accepts JSON only; no pickle; request bodies are Pydantic models (`extra="forbid"` on intake). |
| A10 Exceptional conditions | Auth fails closed (a key-server error is a 401); database errors hide statement parameters; intake failure reasons keep only field and constraint names; unhandled errors return a plain 500 without a trace in production. |

## Residual risks

- The spool folder is trusted to the portal that writes it; the fix stops it reading other files, not from sending bad complaints (those pass the normal validation and duplicate checks).
- Rate limits are per address; a distributed attempt is limited only by Keycloak's per-account lockout and the per-source intake quota.
- The owner database role and the host's root can still change the database; the anchors make that detectable, not impossible.
- No penetration test or deployed-configuration scan has been done.
