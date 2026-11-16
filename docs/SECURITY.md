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
| 9 | Stolen database dump reveals complainants | `complainant_enc` encrypted by the application with a key held outside the database | Planned (column exists) |
| 10 | Brute-force login | Keycloak brute-force protection, password policy, TOTP; edge rate limit on `/auth` | Scaffolded |
| 11 | XSS, clickjacking | CSP `default-src 'self'`, `frame-ancestors 'none'`, no inline scripts, React escaping | Scaffolded |
| 12 | Malicious upload | ClamAV scan before storage; type and size limits | Planned (no uploads yet) |
| 13 | Container breakout or lateral movement | Non-root users, `cap_drop: ALL`, `no-new-privileges`, read-only filesystems, memory limits | Scaffolded |
| 14 | Secrets in the repository | `.env` git-ignored, generated per machine; production uses Docker secrets or Vault | Built (dev) / Planned (prod) |
| 15 | Alert sent without authorisation | Only an approved row is delivered: overlap alerts are approved by a person's decision on the link, other alerts start `pending_approval` for a bureau head or oversight; every decision and every email is audited; mail goes only to active SETHU users | Built |
| 16 | Insider with admin rights changes configuration silently | Maker-checker for admin changes; every change audited | Planned |
| 17 | Sensitive data in logs | Logs carry identifiers only; request bodies are never logged | Built (convention) |
| 18 | Bureau staff read the whole audit ledger | The audit screen and `/api/v1/audit` admit only `auditor`, `oversight` and `admin`; entries hold identifiers and decisions, never complaint text. Not enforced by the database: `sethu_app` can SELECT every `audit_log` row, because the chain trigger reads the last row as whoever inserts, and the no-`SECURITY DEFINER` rule rules out the usual fix | Built (API only) |
| 19 | A report export leaks complaint text or another bureau's figures | Reports have no text or complainant columns; bureau staff get their own bureau only (query scope from the session context, policies for links and alerts); every export is audited with report, filters and row count; CSV cells that start with = + - @ are made inert for spreadsheets | Built |
| 21 | A finding or its alert leaks complaint text, or another bureau's queue | Findings hold identifiers and counts only; Row-Level Security shows a finding to the bureaus involved (and oversight, admin, auditor); only the detector writes them, and people may change only the status (trigger); loop alerts carry the reference and bureaus and wait in `pending_approval` | Built |
| 20 | Search reveals another bureau's complaint text | Text matching goes through `sethu.complaints`, which Row-Level Security empties for other bureaus; results carry summary fields and match reasons only | Built |

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

Run an OWASP Top 10 review, a dependency audit (`pip-audit`, `npm audit`), an image scan, and a restore test from backup. Pin container images by digest. None of this has been done yet.
