# Production readiness

What stands between SETHU as built and a system AICTE can run with real complaints. One row per gap. "Done" means checked in this repository (the "How verified" note says how); nothing is marked done on trust.

Risk: **high** = could expose complaint data, let the wrong person in, or lose data; **medium** = weakens a control or makes an outage likely; **low** = hygiene.

## Phases (proposed)

| Phase | Theme |
|---|---|
| 1 | Production configuration and identity: refuse unsafe config, separate prod from dev, Keycloak hardening, no demo paths in production, bureaus as data |
| 2 | Data protection and operations: secrets store, TLS certificates, scheduled and tested backups (both databases), audit-chain anchor, encryption of complainant details, SMTP over TLS, offline run |
| 3 | Observability and reliability: central logs and alerting, Keycloak events, scheduler separated from workers, CPU limits, health endpoints not public |
| 4 | Supply chain and testing: pinned dependencies and image digests, CI running the full suite, browser tests, dependency scanning |
| 5 | Go-live: penetration test, load test, disaster-recovery drill, remaining problem-statement features, sign-off |

## Gaps

| # | Area | What is wrong or missing today | Risk | Phase | Status |
|---|---|---|---|---|---|
| 1 | Secrets | All secrets live in a plain `.env` file read by Compose. No Docker secrets, Vault or rotation procedure. | high | 2 | Open |
| 2 | Environment validation | The backend starts in `prod` with a missing, empty, placeholder (`CHANGE_ME`) or dev password in its database or Redis URL, an `http://` Keycloak issuer, Mailpit as the mail host, or a `@sethu.test` sender. | high | 1 | Done (tests: `test_config.py`; a production-mode stack refused a short password and Mailpit by name) |
| 3 | Environment validation | No `debug` switch is checked; nothing stops a debug build reaching production. | medium | 1 | Done (`SETHU_DEBUG` added; refused in prod; test) |
| 4 | Environment validation | Interactive API docs (`/api/docs`) are off in `prod`. | low | 1 | Done (code: `app/main.py`, `interactive_docs`) |
| 5 | Demo in production path | The production override imports the dev realm (`infra/keycloak`), whose only redirect URI is `http://localhost:8080/*`, and runs Keycloak with the dev realm's settings. | high | 1 | Done (production override imports `infra/keycloak-prod`, runs `start`; checked on a production-mode stack) |
| 6 | Demo in production path | The `demo-users` service creates six logins with one shared password on any stack started with `--profile dev`, production included. | high | 1 | Done (import refuses `prod`, test; the production override disables the service even under `--profile dev`, checked with `docker compose config`) |
| 7 | Demo in production path | `seed/load.py` loads mock complaints into any empty database, production included; it only refuses a database that already has complaints. | high | 1 | Done (loader refuses `prod` before connecting; test) |
| 8 | Demo in production path | Mailpit and `demo-users` are in the `dev` profile only, so a plain `docker compose up` does not start them. | low | 1 | Done (compose `profiles: ["dev"]`) |
| 9 | Keycloak | Redirect URIs are hard-coded to `http://localhost:8080/*`; production needs the real host. | high | 1 | Done (production realm: exact URIs from `PUBLIC_BASE_URL`; checked after import) |
| 10 | Keycloak | Post-logout redirect URIs: `+` (same as redirect URIs) in the dev realm; no exact value for production. | medium | 1 | Done (dev realm `+`, sign-out checked in a browser; production realm exact URI; checked after import) |
| 11 | Keycloak | `bureau_id` is an unmanaged attribute; only the demo script sets "administrators may edit" (otherwise Keycloak drops it and officers cannot sign in). Production relies on a manual console step. | high | 1 | Done (production realm sets `unmanagedAttributePolicy: ADMIN_EDIT` and the mapper; checked after import) |
| 12 | Keycloak | The admin console and the `master` realm sign-in are proxied on the public edge at `/auth/admin/` and `/auth/realms/master/`. | high | 1 | Done (404 on the public port, 200 on the loopback admin port; production-mode stack) |
| 13 | Keycloak | The admin console hangs on "Loading the Administration Console": nginx adds the app's strict CSP and `X-Frame-Options: DENY` to `/auth/` responses, which blocks Keycloak's inline scripts and frames. | medium | 1 | Done (dev stack in a browser: the console loads and lists users. Two causes: the CSP and `DENY` on `/auth`, and the sign-in rate limit refusing the console's burst of requests) |
| 14 | Keycloak | Token lifetimes: access token 5 minutes and SSO idle 30 minutes are set; no SSO maximum lifespan, refresh tokens are reusable. | medium | 1 | Done (production realm: SSO maximum 10 hours, single-use refresh tokens, 60-second codes; checked after import) |
| 15 | Keycloak | Brute-force detection is on (5 failures) with default wait times; password policy has length, case and digit but no special character, e-mail or history rule. | low | 1 | Done (production realm: waits up to 15 minutes, special character, not e-mail, history of 5; checked after import) |
| 16 | Keycloak | `sslRequired` is `external`; production should require TLS for every request. | medium | 1 | Done (production realm `sslRequired: all`; checked after import) |
| 17 | Keycloak | The realm file is imported only when the realm does not exist; later changes need the console or a full re-import (which drops all Keycloak users). No config-as-code tool. | medium | 2 | Open |
| 18 | Keycloak | No second factor required, not even for `admin` and `oversight`. | medium | 2 | Open |
| 19 | Keycloak | Login and admin events are not recorded. | medium | 3 | Open |
| 20 | Keycloak | The Keycloak bootstrap admin is a permanent account named by default `sethu-admin`. | medium | 2 | Open |
| 21 | TLS and headers | The production nginx config (TLS 1.3, HSTS) exists but has never been run; certificate issuance and renewal are undocumented. | high | 2 | Open |
| 22 | TLS and headers | No port 80 listener redirecting to HTTPS. | low | 2 | Open |
| 23 | TLS and headers | CSP allows `'unsafe-inline'` styles (React inline styles). | low | 4 | Open |
| 24 | TLS and headers | App responses carry CSP, `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`; HSTS in production. | low | 1 | Done (nginx configs; browser saw them on 8081) |
| 25 | CORS | No CORS middleware: the API is same-origin only behind nginx. | low | 1 | Done (code: no `CORSMiddleware` in `backend/app`) |
| 26 | Database | Least-privilege roles; the runtime role is `NOBYPASSRLS`; Row-Level Security on complaint tables. | low | 1 | Done (tests: `test_rls.py`) |
| 27 | Database | `sethu_app` can read every `audit_log` row (SECURITY.md row 18). | medium | 3 | Open |
| 28 | Database | Connections inside the `data` network are not TLS. | low | 2 | Open |
| 29 | Backups | Manual `pg_dump` of the `sethu` database only: no schedule, no off-host copy, no restore drill, and the `keycloak` database is not in the procedure. | high | 2 | Open |
| 30 | Backups | The audit-chain head hash is not exported to write-once storage (ARCHITECTURE section 6, planned). | medium | 2 | Open |
| 31 | Data | `complaints.complainant_enc` is described as encrypted by the application, but no code encrypts or writes it. Harmless with mock data; must exist before real intake. | high | 2 | Open |
| 32 | Logging | JSON logs to Docker's file driver with rotation; no central collection, retention policy or alerting. | medium | 3 | Open |
| 33 | Logging | Request bodies are never logged; identifiers only. | low | 1 | Done (code: `app/main.py` logs method, path, status) |
| 34 | Health checks | `keycloak`, `web` and `worker` have no health check (the worker's is disabled). | medium | 1 | Done (Keycloak, web and worker checks added; all services turned healthy on the dev and production-mode stacks) |
| 35 | Health checks | `/health/ready` is reachable from outside through nginx. | low | 3 | Open |
| 36 | Resource limits | Memory limits on long-running services; none on `migrate` or `mailpit`; no CPU limits. | low | 1 | Partly: `migrate` limited; Mailpit is dev only; CPU limits left for phase 3 |
| 37 | Reliability | Celery beat runs inside the worker: a second worker would run every scheduled job twice. | medium | 3 | Open |
| 38 | Bureaus | Bureau codes and names are written in `seed/load.py`; application logic does not branch on a code (only comments name PGRC and RB). The seed has two bureaus, so cross-bureau behaviour is only ever PGRC and RB. | low | 1 | Done (bureaus come from `seed/bureaus.csv`; NRB and AB added; the old records are byte-identical) |
| 39 | Mail | SMTP is plain (no STARTTLS, no authentication); the sender defaults to `sethu-alerts@sethu.test`. | medium | 2 | Open |
| 40 | Dependencies | Python dependencies are ranges with no lock file; images are pinned by tag, not digest (`keycloak:26.0`, `pg16`, `redis:7-alpine`, `python:3.12-slim`, `node:22-alpine`, `nginx-unprivileged:1.27-alpine`). | medium | 4 | Open |
| 41 | Testing | No CI runs the tests; no browser tests (screens are checked by hand, RUNBOOK). | medium | 4 | Open |
| 42 | Containers | `postgres` and `keycloak` are not read-only (their images write to their own paths). | low | 3 | Open |
| 43 | Checklist | Unticked: updates within 5 seconds when a case changes; runs with Wi-Fi off (not tested); graph line asks for complaints as nodes (bureaus are drawn instead). | medium | 5 | Open |
| 44 | Configuration | The findings thresholds (`SETHU_STALLED_TRANSFER_DAYS`, `SETHU_BOTTLENECK_*`, `SETHU_SPIKE_*`) were documented as settable in `.env` but Compose never passed them to the backend or worker (found during this audit). | medium | 1 | Done (passed through with the same defaults; `docker compose config` shows them) |
| 45 | Logging | A settings error printed a shortened copy of all settings, which can include a password (found during this audit). | high | 1 | Done (`hide_input_in_errors`; test) |
| 46 | Bureaus | Production has no way to create a bureau: the seed loader refuses `prod` and there is no API or screen, so the first bureaus need SQL (not audited by the application). | high | 2 | Open (found while signing in to the production-mode stack) |
| 47 | Identity | A person is registered in `app_users` from the token on first use, without an e-mail address, and later role or bureau changes in Keycloak never reach that row. A bureau head registered this way receives no alerts. | high | 2 | Open (found while signing in to the production-mode stack) |
