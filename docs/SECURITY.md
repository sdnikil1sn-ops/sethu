# Security

Status key: **Built** (tested in this repo), **Scaffolded** (configured, not yet run end to end), **Planned**.

## Assets

1. Complaint text and complainant identity (most sensitive: a leak can expose a whistle-blower).
2. Integrity of the action history (who decided what, and when).
3. Availability of the dashboard to bureaus.

## Threats and controls

| # | Threat | Control | Status |
|---|---|---|---|
| 1 | Complaint data sent to an outside service | App and data networks are `internal`; no external APIs; local models only | Scaffolded |
| 2 | Officer of one bureau reads another bureau's complaint text | Row-Level Security on `complaints` and `case_actions`; cross-bureau view exposes metadata only; free-text search and case detail go through the same policies; overlap links and alerts are readable only by the bureaus involved and carry references, not text | Built |
| 3 | API bug forgets an access filter | RLS applies in the database regardless; no request context returns nothing | Built |
| 4 | Forged or replayed token | RS256/ES256 only, issuer, audience and expiry checked, 5-minute lifetime; HS256 tokens rejected | Built |
| 5 | Privilege escalation through token claims | Only five known roles accepted; bureau-scoped roles require a `bureau_id`; `system` cannot come from a token | Built |
| 6 | Someone edits or deletes history | Append-only triggers; app role has no UPDATE/DELETE; hash chain detects tampering by privileged users; the Verify chain button names the first broken row | Built |
| 7 | Whole audit chain rebuilt by a database superuser | Nightly head-hash exported to write-once storage and emailed to the auditor | Planned |
| 8 | SQL injection | Bound parameters everywhere; ruff `S` rules in lint | Built (convention + lint) |
| 9 | Stolen database dump reveals complainants | `complainant_enc` encrypted by the application (AES-256-GCM, bound to the complaint id) with a key held outside the database, in a keyring file mounted as a secret; rotatable; shown only to the holding bureau's officers and head; absent from search, lists, reports, exports, logs and audit (tested) | Built |
| 10 | Brute-force login | Keycloak brute-force detection (production realm: 5 failures, waits up to 15 minutes), password policy (12+ with upper, lower, digit, special; not username, e-mail or last 5); strict edge rate limit on sign-in and token requests; TOTP available, not yet required | Built (production realm imported and checked; MFA planned) |
| 11 | XSS, clickjacking | CSP `default-src 'self'`, `frame-ancestors 'none'`, no inline scripts, React escaping | Scaffolded |
| 12 | Malicious upload | ClamAV scan before storage; type and size limits | Planned (no uploads yet) |
| 13 | Container breakout or lateral movement | Non-root users, `cap_drop: ALL`, `no-new-privileges`, read-only filesystems, memory limits | Scaffolded |
| 14 | Secrets in the repository, an image or an environment variable | `.env` and `secrets/` git-ignored; production passwords and keys are files mounted read-only under `/run/secrets` into only the containers that need them; the backend refuses inline passwords; rotation per secret in the RUNBOOK (tested for the app database password) | Built |
| 15 | Alert sent without authorisation | Only an approved row is delivered: overlap alerts are approved by a person's decision on the link, other alerts start `pending_approval` for a bureau head or oversight; every decision and every email is audited; mail goes only to active SETHU users | Built |
| 16 | Insider with admin rights changes configuration silently | Maker-checker for admin changes; every change audited | Planned |
| 17 | Sensitive data in logs | Logs carry identifiers only; request bodies are never logged | Built (convention) |
| 18 | Bureau staff read the whole audit ledger | The audit screen and `/api/v1/audit` admit only `auditor`, `oversight` and `admin`; entries hold identifiers and decisions, never complaint text. Not enforced by the database: `sethu_app` can SELECT every `audit_log` row, because the chain trigger reads the last row as whoever inserts, and the no-`SECURITY DEFINER` rule rules out the usual fix | Built (API only) |
| 19 | A report export leaks complaint text or another bureau's figures | Reports have no text or complainant columns; bureau staff get their own bureau only (query scope from the session context, policies for links and alerts); every export is audited with report, filters and row count; CSV cells that start with = + - @ are made inert for spreadsheets | Built |
| 21 | A finding or its alert leaks complaint text, or another bureau's queue | Findings hold identifiers and counts only (a category spike holds state, category and counts); Row-Level Security shows a finding to the bureaus involved (and oversight, admin, auditor); only the detector writes them, and people may change only the status (trigger); loop alerts carry the reference and bureaus and wait in `pending_approval` | Built |
| 22 | Production runs with a placeholder, dev or missing secret, debug on, an http issuer or the dev mail catcher | Backend and worker refuse to start in `prod` and name each variable (never its value, never the other settings); Compose refuses to start without the production variables | Built (tests; production-mode stack) |
| 23 | Keycloak administration reachable from the internet | Admin console and `master` realm return 404 on the public edge; administration on a TLS port bound to the host's loopback, via SSH tunnel; `KC_HOSTNAME_ADMIN` set | Built (production-mode stack) |
| 24 | Demo logins or mock data reach production | The seed loader and the demo-user import refuse `SETHU_ENVIRONMENT=prod`; the production override disables Mailpit and demo-users even under `--profile dev`; the production realm has no users | Built (tests) |
| 26 | Someone raises their own role, or writes another person's or a bureau's record | `app_users` and `bureaus` have Row-Level Security: a person writes only their own row and only with their token's role and bureau; only `admin` writes bureaus; every change audited | Built (tests) |
| 25 | Open redirect after sign-in or sign-out | Production realm: exact redirect and post-logout URIs from `PUBLIC_BASE_URL`, exact web origin; dev realm: `+` (the same as its redirect URIs) | Built |
| 20 | Search reveals another bureau's complaint text | Text matching goes through `sethu.complaints`, which Row-Level Security empties for other bureaus; results carry summary fields and match reasons only | Built |
| 27 | Loss of the database, or a stolen backup | `backup` service: both databases every 24 h, encrypted with gpg AES-256 under a key kept apart from the backups; restore only into an empty database, ends with Verify chain; drill passed (RUNBOOK section 4). Off-host copy is an operator step | Built |
| 28 | Expired or wrong edge certificate | `scripts/install_cert.py`: refuses non-PEM or expired files, `nginx -t` before reload, puts the old pair back on failure; no rebuild needed. Renewal is manual | Built |
| 29 | A stolen or guessed intake API key files complaints | Keys are 256-bit random, stored as SHA-256 only, shown once, replaceable by an admin (audited); a key works only for its own api source and bureau (Row-Level Security on the queue); an admin can mark the source down or deactivate it | Built |
| 30 | A captured intake request is replayed | `X-Sethu-Timestamp` within 5 minutes and a one-time `X-Sethu-Nonce` per source (`intake_nonces`); a reuse is refused (409) and logged; TLS on the edge | Built |
| 31 | Flooding the intake API or the queue | nginx per-IP rate limit on `/api/`; a per-source quota (`SETHU_INTAKE_RATE_PER_MINUTE`, or the source's own) answering 429; 10 MB body limit at the edge, 2 MB and 5,000 rows per file in the app; resubmissions from a source refused | Built |
| 32 | A malicious upload or spool file (formula injection, zip bomb, malformed XLSX) | Files are parsed, never executed or stored; CSV read as text; XLSX read with openpyxl (values only, no formulas evaluated); size and row limits before parsing; an unreadable file is refused (upload) or moved to `rejected/` (spool). The error report repeats row, field and rule, never a cell value | Built |
| 33 | Complaint text or complainant details leak through intake logs, errors or audit | The queue holds the complaint encrypted; audit entries and logs carry identifiers, counts and reasons; failure reasons keep only field or constraint names (`safe_reason`); a test searches audit, logs, errors and the stored queue for the submitted text and details | Built |
| 34 | A complaint is lost when a source or the pipeline fails | Written to the queue before processing; retried with backoff; dead letters kept with the reason for an admin Retry; a held primary and its fallback copy are recognised as duplicates; spool files are moved, never deleted | Built |
| 35 | The spool folder is written by someone who should not | It is a host folder mounted into the worker only; on a Linux host owned by the portal's transfer account and the worker's uid (10001), mode 0770. What is dropped there is filed for the folder's source's bureau only | Operator step |
| 36 | Internal case notes read outside the bureau working the case | Row-Level Security on `case_actions`: a `note` row is read only by the officers and heads of the bureau holding the case (and the worker); tested for oversight, auditor, the sender of a transfer and the receiving bureau | Built |
| 37 | The network graph shows another bureau's complaint text or links | The graph API returns summary metadata only (references, codes, statuses, categories, dates, counts); overlap links, transfers and findings are read under Row-Level Security; the side panel fetches a case through the case API, which returns text only to the holding bureau; tested for an uninvolved bureau | Built |
| 38 | Embeddings leak complaint content (vectors can be partly inverted) | Stored in `complaint_embeddings` under the same Row-Level Security as the text; computed in the worker only; never selected by an API; never logged (tested against API responses and logs); the model runs locally from the image (`HF_HUB_OFFLINE=1`, internal networks) | Built |
| 39 | Operational data or secrets leak through metrics or logs | `/metrics` is served only on the internal network (nginx 404; the backend refuses proxied requests) and carries counts and times only; logs are JSON with identifiers and route templates, no query strings at the edge, no statement values on database errors; a test scans every log line of a full request cycle for complaint text, complainant details, the API key, the database password and key material | Built |
| 40 | Password guessing goes unnoticed | Keycloak login events on (90 days) with brute-force lockout; failed sign-ins shown read-only on the Audit log screen through a client that can only view events; alert threshold documented (RUNBOOK, Observability) | Built |
| 41 | A dependency or base image changes under us, or carries a known vulnerability | Python packages installed only with `--require-hashes` from lock files; npm from `package-lock.json`; base images by digest; the model by hash; CI runs pip-audit, npm audit (high), Trivy on both images (fixable high or critical) and gitleaks on the history, all failing the build | Built (workflow not yet run on GitHub) |
| 42 | The audit log is replaced or rewritten together with its database (an insider with database access) | Hourly anchors (entry number and hash) appended to a file outside the database that the operator makes write-once; any later comparison names rewritten or missing entries | Built (the write-once property is an operator step) |
| 43 | A file dropped in the spool folder reads another file (a link), or a spreadsheet expands to exhaust memory | Links and non-regular files refused unread (`O_NOFOLLOW`); an unknown header is not echoed; an XLSX's expanded size is checked before parsing and rows are streamed to the limit (docs/SECURITY-REVIEW.md) | Built |
| 44 | An AI component sends complaint text out (a model hub, a hosted API, telemetry) | The ai-worker sits on the internal `ai` and `data` networks only; models come from a read-only folder checked against `models/manifest.json`, never downloaded; `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, required in production; production refuses any `SETHU_AI_ENDPOINTS` URL outside the deployment; the egress canary (CI) fails on any outbound attempt or route from an internal container | Built and tested (tests/test_config.py, scripts/egress_canary.py: 0 attempts in 60 idle seconds and no route from ai-worker on a dev stack, 2026-11-23) |
| 45 | A tampered or swapped model file is loaded | SHA-256 of every model file (or folder) checked before each load; a mismatch, a missing file or a path leaving the models folder refuses the model | Built and tested (tests/test_ai_registry.py) |
| 46 | An AI answer is acted on without a person, or its origin cannot be shown | The router only returns answers; low confidence, invalid output, timeouts and failures fall through to rules and then human review; every call is in `sethu.ai_runs` (append-only, Row-Level Security) and the hash-chained audit log, without the text | Built and tested (tests/test_ai_router.py) |

## Rules for contributors

- Never commit real data or secrets. Mock data only.
- Never widen a grant, policy or network to make a feature easier. Ask first and record the decision as an ADR.
- A new endpoint without `require_roles(...)` is a defect.
- A state change without `audit.record(...)` in the same transaction is a defect.

## Compliance notes (to confirm with the AICTE mentor)

- CERT-In 2022 directions: logs kept 180 days in India, clocks synchronised to NIC or NPL NTP, incidents reported within 6 hours. Our reading is from secondary sources.
- DPDP Act and Rules: purpose limitation and breach notification apply to complainant data. Dates and thresholds need confirming against the official text.
- GIGW 3.0 accessibility for the web interface.
- DARPG timelines (21 days, 3 days urgent) drive `due_at`; category-specific timelines need the mentor's input.

## Before any real deployment

Run an OWASP Top 10 review, a dependency audit (`pip-audit`, `npm audit`), and an image scan. Pin container images by digest. None of this has been done yet. (A restore test from backup was done: RUNBOOK section 4.)
