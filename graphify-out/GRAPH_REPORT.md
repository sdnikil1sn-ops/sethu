# Graph Report - jolly-feynman-1a9f96  (2026-11-20)

## Corpus Check
- 162 files · ~80,879 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 19 file(s) not represented in the graph (top: (none) 8, .csv 5, .conf 2)

## Summary
- 1848 nodes · 3921 edges · 146 communities (98 shown, 48 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 64 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f88bf694`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- environment
- load.py
- complaints/repo.py
- test_search.py
- institutions/repo.py
- test_findings.py
- test_alerts.py
- backend
- sqlalchemy
- session_for
- BaseModel
- package.json
- options
- App.tsx
- useLoad
- test_config.py
- dashboard/repo.py
- Principal
- test_overlaps.py
- postgres
- pathlib
- overlaps/service.py
- web
- bureaus/service.py
- demo-users
- 3. Database
- Architecture
- x-backend-env
- compilerOptions
- environment
- test_complainant.py
- test_findings.py
- redis
- keycloak
- environment
- findings/service.py
- x-prod-backend-env
- 01. Scope Lock
- 02. PS Coverage Checklist (SIH26264)
- AuditLog.tsx
- Overlaps.tsx
- install_cert.py
- reports/service.py
- complaints/schemas.py
- api.ts
- healthcheck
- complaints/api.py
- services
- Architecture Decision Records
- Architecture Snapshot
- test_seed.py
- migrate
- Dashboard.tsx
- session.py
- 03. Demo Story: "Institution A"
- 04. Mock Data Spec
- Data Model
- Security
- api
- 05. Next Claude Code Prompts
- test_reports.py
- backup
- postgres
- import.sh
- SETHU
- .claude/CLAUDE.md
- 01-roles.sh
- test_scheduler.py
- sethu-backend
- get_principal
- environment
- generate.py
- cases/types.ts
- main.py
- dashboard/schemas.py
- worker
- overlaps/schemas.py
- worker.py
- get_principal
- Findings.tsx
- Reports.tsx
- scheduler
- Production readiness
- pytest
- environment
- backup.sh
- users/repo.py
- complaints/service.py
- Runbook
- reports/schemas.py
- test_audit_view.py
- web
- alerts/service.py
- services
- redis
- migrate
- 7. Production
- datetime
- findings/schemas.py
- env.py
- search/schemas.py
- list_entries
- SingleScheduler
- Seed data
- test_tls_modes_verify_the_relay_certificate
- add
- deploy

## God Nodes (most connected - your core abstractions)
1. `session_for()` - 124 edges
2. `Principal` - 120 edges
3. `useLoad()` - 37 edges
4. `get_settings()` - 28 edges
5. `record()` - 28 edges
6. `verify()` - 26 edges
7. `get_principal()` - 21 edges
8. `decide()` - 21 edges
9. `detect()` - 21 edges
10. `x-backend-env` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Tamper demonstration` --references--> `verify()`  [INFERRED]
  docs/RUNBOOK.md → backend/app/audit/service.py
- `6. Audit ledger` --references--> `verify()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/audit/service.py
- `Seeded patterns and the expected detection` --references--> `silent()`  [INFERRED]
  seed/README.md → backend/tests/test_seed.py
- `Non-negotiable rules` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py
- `Working agreements` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py

## Import Cycles
- None detected.

## Communities (146 total, 48 thin omitted)

### Community 0 - "environment"
Cohesion: 0.28
Nodes (18): environment, environment, SETHU_ALERT_FROM, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_OIDC_ISSUER (+10 more)

### Community 1 - "load.py"
Cohesion: 0.13
Nodes (6): test_keycloak_demo_logins_match_the_seed(), insert(), load(), ProductionRefused, rows(), user_id()

### Community 2 - "complaints/repo.py"
Cohesion: 0.19
Nodes (18): _all(), bureaus(), case_counts(), exists(), find(), history(), insert_action(), institution_history() (+10 more)

### Community 3 - "test_search.py"
Cohesion: 0.10
Nodes (14): _check(), export(), report(), export(), run(), search(), test_never_in_search_lists_reports_exports_audit_or_logs(), test_a_bureau_code_matches_exactly_in_search() (+6 more)

### Community 4 - "institutions/repo.py"
Cohesion: 0.07
Nodes (31): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+23 more)

### Community 5 - "test_findings.py"
Cohesion: 0.17
Nodes (17): cell(), detected(), findings_as(), hop(), test_a_second_run_adds_nothing(), test_a_spike_that_comes_back_is_reopened_with_its_new_counts(), test_an_acknowledgement_or_any_action_breaks_the_loop(), test_dismiss_reopen_and_resolve_are_audited_and_limited() (+9 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.10
Nodes (20): alert_row(), audit_count(), closed_port(), deliver(), FakeSMTP, held(), kinds(), make_due() (+12 more)

### Community 7 - "backend"
Cohesion: 0.14
Nodes (16): build, cap_drop, depends_on, networks, read_only, restart, secrets, security_opt (+8 more)

### Community 8 - "sqlalchemy"
Cohesion: 0.11
Nodes (5): actions(), entries(), entry(), entries(), verify()

### Community 9 - "session_for"
Cohesion: 0.13
Nodes (19): ChainStatus, verify(), apply_context(), get_engine(), session_for(), _append(), test_actor_comes_from_the_session_not_the_caller(), test_chain_is_valid_and_sequential() (+11 more)

### Community 10 - "BaseModel"
Cohesion: 0.17
Nodes (17): Alias, BureauCount, Candidate, CaseSummary, CategoryShare, Disposal, Dna, Institution (+9 more)

### Community 11 - "package.json"
Cohesion: 0.10
Nodes (23): react-dom, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, dependencies, react@^18.3.1 (+15 more)

### Community 12 - "options"
Cohesion: 0.26
Nodes (13): logging, logging, driver, options, logging, logging, max-file, max-size (+5 more)

### Community 13 - "App.tsx"
Cohesion: 0.16
Nodes (23): useLoad(), App(), CAN_AUDIT, CAN_DECIDE, CAN_RESOLVE, Me, useHashRoute(), AlertsPage() (+15 more)

### Community 14 - "useLoad"
Cohesion: 0.17
Nodes (18): DnaPanel(), pct(), TREND, InstitutionList(), InstitutionProfile(), ResolutionQueue(), Candidate, CaseSummary (+10 more)

### Community 15 - "test_config.py"
Cohesion: 0.19
Nodes (12): Settings, refused(), settings(), _shell(), test_a_complete_production_configuration_starts(), test_all_problems_are_reported_at_once(), test_an_unreadable_secret_file_is_named_not_shown(), test_dev_and_test_keep_working_with_dev_values() (+4 more)

### Community 16 - "dashboard/repo.py"
Cohesion: 0.10
Nodes (16): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview() (+8 more)

### Community 17 - "Principal"
Cohesion: 0.18
Nodes (18): Principal, _count(), linked(), _refs(), test_a_bureau_can_only_hand_a_case_over_as_itself(), test_a_bureau_cannot_read_links_or_alerts_it_is_not_party_to(), test_auditor_cannot_modify_complaints(), test_findings_are_read_by_the_bureaus_involved_and_written_by_the_detector() (+10 more)

### Community 18 - "test_overlaps.py"
Cohesion: 0.23
Nodes (12): detected(), scalar(), suggested_pairs(), test_api_decisions_detection_and_the_overlapping_filter(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs(), test_negative_cases_are_never_flagged() (+4 more)

### Community 19 - "postgres"
Cohesion: 0.11
Nodes (18): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+10 more)

### Community 20 - "pathlib"
Cohesion: 0.17
Nodes (8): main(), _new_key(), _write(), ensure_keyring(), main(), main(), rotate(), _write()

### Community 21 - "overlaps/service.py"
Cohesion: 0.05
Nodes (36): decide(), detect(), list_links(), tier1(), _all(), decide(), insert_alert(), linked_case_ids() (+28 more)

### Community 22 - "web"
Cohesion: 0.12
Nodes (16): condition, depends_on, backend, keycloak, condition, web, build, cap_drop (+8 more)

### Community 23 - "bureaus/service.py"
Cohesion: 0.10
Nodes (18): create_bureau(), list_bureaus(), _run(), update_bureau(), _all(), by_code(), get(), insert() (+10 more)

### Community 24 - "demo-users"
Cohesion: 0.13
Nodes (15): cap_drop, entrypoint, environment, image, networks, profiles, read_only, restart (+7 more)

### Community 25 - "3. Database"
Cohesion: 0.20
Nodes (10): 3. Database, Alert mail (dev and demo), Complainant details: keys, Demo logins (dev and demo only), Findings (deadlocks and bottlenecks), Manual check of the screens (no browser tests), Re-importing the realm on an existing stack, Reports and exports (+2 more)

### Community 26 - "Architecture"
Cohesion: 0.17
Nodes (11): 10. Scaling path (after the hackathon), 11. What has been verified, 1. Shape, 2. Components, 3. Trust boundaries and how each is defended, 4. Request flow (example: approve an overlap link), 5. Processing pipeline (worker), 6. Audit ledger (+3 more)

### Community 27 - "x-backend-env"
Cohesion: 0.10
Nodes (20): x-backend-env, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_COMPLAINANT_KEYS_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_OIDC_AUDIENCE (+12 more)

### Community 28 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 29 - "environment"
Cohesion: 0.17
Nodes (12): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_BOOTSTRAP_ADMIN_USERNAME, KC_DB, KC_DB_PASSWORD, KC_DB_URL, KC_DB_USERNAME, KC_HEALTH_ENABLED, KC_HOSTNAME (+4 more)

### Community 30 - "test_complainant.py"
Cohesion: 0.13
Nodes (16): get_settings(), key_id_of(), Keyring, KeyringError, load_keyring(), parse_keyring(), _split(), keyring() (+8 more)

### Community 31 - "test_findings.py"
Cohesion: 0.24
Nodes (9): scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_officer_picks_from_the_queue(), test_profile_dna_measures(), test_profile_shows_every_bureau_without_complaint_text() (+1 more)

### Community 32 - "redis"
Cohesion: 0.17
Nodes (12): REDIS_PASSWORD, cap_add, cap_drop, command, environment, image, networks, read_only (+4 more)

### Community 33 - "keycloak"
Cohesion: 0.15
Nodes (13): postgres, cap_drop, command, depends_on, deploy, image, networks, restart (+5 more)

### Community 34 - "environment"
Cohesion: 0.15
Nodes (13): KEYCLOAK_DB_PASSWORD, KEYCLOAK_DB_PASSWORD_FILE, POSTGRES_PASSWORD, POSTGRES_PASSWORD_FILE, SETHU_APP_PASSWORD, SETHU_APP_PASSWORD_FILE, SETHU_AUDITOR_PASSWORD, SETHU_AUDITOR_PASSWORD_FILE (+5 more)

### Community 35 - "findings/service.py"
Cohesion: 0.06
Nodes (34): record(), _all(), bureau_codes(), bureau_queues(), category_cells(), existing(), insert(), insert_alert() (+26 more)

### Community 36 - "x-prod-backend-env"
Cohesion: 0.05
Nodes (37): file, file, file, file, file, file, secrets, backup_key (+29 more)

### Community 37 - "01. Scope Lock"
Cohesion: 0.17
Nodes (11): 01. Scope Lock, Constraints, Definition of done (per feature), Freeze rules, Goal in one sentence, Out of scope (do not discuss again), Parking lot, Sign-off (+3 more)

### Community 38 - "02. PS Coverage Checklist (SIH26264)"
Cohesion: 0.17
Nodes (11): 02. PS Coverage Checklist (SIH26264), 1. Institution profile, 2. Case tracking, 3. Overlap detection, 4. Real-time dashboard, 5. Action history, 6. Search and filters, 7. Alerts (+3 more)

### Community 39 - "AuditLog.tsx"
Cohesion: 0.24
Nodes (8): AuditLog(), ChainReport, EMPTY, Entry, EntryPage, moment(), target(), Verify()

### Community 40 - "Overlaps.tsx"
Cohesion: 0.22
Nodes (9): Options, BANNER, day(), Link, LinkCard(), decide(), LinkedCase, STATUS (+1 more)

### Community 41 - "install_cert.py"
Cohesion: 0.29
Nodes (3): check_pem(), main(), nginx()

### Community 42 - "reports/service.py"
Cohesion: 0.15
Nodes (8): create_app(), _all(), bureaus(), _in_range(), institutions(), overlaps(), _cell(), search()

### Community 43 - "complaints/schemas.py"
Cohesion: 0.11
Nodes (11): blank_to_none(), Action, Assignee, Bureau, Case, CasePage, CaseRow, Complainant (+3 more)

### Community 44 - "api.ts"
Cohesion: 0.35
Nodes (9): accessToken(), base64url(), login(), logout(), redirectUri(), requestTokens(), start(), Tokens (+1 more)

### Community 45 - "healthcheck"
Cohesion: 0.47
Nodes (11): interval, retries, start_period, test, timeout, healthcheck, healthcheck, healthcheck (+3 more)

### Community 46 - "complaints/api.py"
Cohesion: 0.25
Nodes (8): act(), assignees(), case(), institution_timeline(), list_cases(), options(), _run(), ActionIn

### Community 47 - "services"
Cohesion: 0.07
Nodes (26): internal, file, internal, cap_drop, image, networks, ports, profiles (+18 more)

### Community 48 - "Architecture Decision Records"
Cohesion: 0.22
Nodes (8): 0001. Modular monolith, not microservices, 0002. Enforce access in the database with Row-Level Security, 0003. Hash-chained audit log inside PostgreSQL, not a blockchain, 0004. Transactional outbox for alerts, 0005. Local models only, each with a deterministic fallback, 0006. Object storage deferred, 0007. Keycloak for identity, Architecture Decision Records

### Community 49 - "Architecture Snapshot"
Cohesion: 0.22
Nodes (8): Architecture Pattern, Architecture Snapshot, Critical Modules, Dependency Rules, Entry Points, Extraction Quality, Repository Map, Routes

### Community 50 - "test_seed.py"
Cohesion: 0.21
Nodes (10): cross_bureau_pairs(), deadlocks(), duplicate_pairs(), not_closed(), silent(), spikes(), tagged(), test_expected_detections() (+2 more)

### Community 51 - "migrate"
Cohesion: 0.18
Nodes (11): MIGRATION_DATABASE_URL, build, cap_drop, command, deploy, environment, networks, read_only (+3 more)

### Community 52 - "Dashboard.tsx"
Cohesion: 0.39
Nodes (8): cases(), Count, CountTable(), Dashboard(), day(), OverdueCase, Overview, Trend()

### Community 54 - "03. Demo Story: "Institution A""
Cohesion: 0.25
Nodes (7): 03. Demo Story: "Institution A", Characters (fictional), Cut list if the demo runs long, Rehearsal checklist, Script, Seeded facts, The story in one line

### Community 55 - "04. Mock Data Spec"
Cohesion: 0.25
Nodes (7): 04. Mock Data Spec, Deliberate patterns to seed, Expected detections (used by tests), Files to generate, Fixed demo records (do not randomise), Negative cases (must NOT be flagged), Volume

### Community 56 - "Data Model"
Cohesion: 0.29
Nodes (6): Adding a table, Data Model, Database roles, Planned additions, Request context and policies, Tables

### Community 57 - "Security"
Cohesion: 0.29
Nodes (6): Assets, Before any real deployment, Compliance notes (to confirm with the AICTE mentor), Rules for contributors, Security, Threats and controls

### Community 58 - "api"
Cohesion: 0.20
Nodes (14): api(), AdminPage(), changed(), create(), BureauLine(), save(), BureauRow, Person (+6 more)

### Community 59 - "05. Next Claude Code Prompts"
Cohesion: 0.33
Nodes (5): 05. Next Claude Code Prompts, After that, in this order, Prompt 1: bring the stack up, Prompt 2: mock data, Prompt 3: first feature (institutions and resolution)

### Community 60 - "test_reports.py"
Cohesion: 0.20
Nodes (8): client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_export_is_csv_without_text_and_is_audited(), test_institution_report_counts_only_the_callers_cases(), test_overlap_outcomes(), test_viewing_is_not_audited_and_bad_names_are_refused()

### Community 61 - "backup"
Cohesion: 0.11
Nodes (18): cap_drop, command, depends_on, entrypoint, environment, image, networks, restart (+10 more)

### Community 62 - "postgres"
Cohesion: 0.40
Nodes (4): networks, ports, services, postgres

### Community 67 - "import.sh"
Cohesion: 1.00
Nodes (3): kcadm(), login(), import.sh script

### Community 68 - "SETHU"
Cohesion: 0.50
Nodes (3): Quick start (Windows, PowerShell), SETHU, What is here

### Community 74 - "test_scheduler.py"
Cohesion: 0.21
Nodes (7): scheduler(), start(), test_a_scheduler_that_lost_its_lock_stops(), test_a_second_scheduler_refuses_to_start(), test_the_lock_passes_on_when_the_scheduler_stops_or_dies(), 2. Daily use, Scheduler

### Community 78 - "get_principal"
Cohesion: 0.14
Nodes (11): AuthError, decode_token(), _jwks_client(), principal_from_claims(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins(), test_me_and_role_gate() (+3 more)

### Community 79 - "environment"
Cohesion: 0.25
Nodes (22): environment, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_COMPLAINANT_KEYS_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_OIDC_AUDIENCE (+14 more)

### Community 80 - "generate.py"
Cohesion: 0.18
Nodes (7): test_files_are_what_the_generator_produces(), build(), details(), fresh(), two_wordings(), render(), variant()

### Community 81 - "cases/types.ts"
Cohesion: 0.29
Nodes (10): History(), InstitutionTimeline(), unacknowledged(), Action, Case, CasePage, CaseRow, describe() (+2 more)

### Community 83 - "dashboard/schemas.py"
Cohesion: 0.36
Nodes (6): Attention, Count, OverdueCase, Overview, Totals, Week

### Community 86 - "worker"
Cohesion: 0.20
Nodes (10): worker, build, cap_drop, command, networks, read_only, restart, secrets (+2 more)

### Community 87 - "overlaps/schemas.py"
Cohesion: 0.36
Nodes (6): DecisionIn, DetectOut, Link, LinkedCase, Tier1Case, Tier1Institution

### Community 88 - "worker.py"
Cohesion: 0.13
Nodes (6): deliver_alerts(), detect_findings(), detect_overlaps(), resolve_pending(), rotate_complainant_keys(), verify_chain()

### Community 89 - "get_principal"
Cohesion: 0.18
Nodes (4): live(), me(), ready(), get_principal()

### Community 90 - "Findings.tsx"
Cohesion: 0.18
Nodes (15): react, day(), Finding, FindingsPage(), KIND, numbers(), pct(), spikeWindow() (+7 more)

### Community 91 - "Reports.tsx"
Cohesion: 0.32
Nodes (7): download(), NOTES, NUMERIC, Report, REPORTS, ReportsPage(), exportCsv()

### Community 92 - "scheduler"
Cohesion: 0.11
Nodes (19): deploy, deploy, resources, memory, deploy, limits, build, cap_drop (+11 more)

### Community 93 - "Production readiness"
Cohesion: 0.50
Nodes (3): Gaps, Phases (proposed), Production readiness

### Community 95 - "pytest"
Cohesion: 0.13
Nodes (16): app_engine(), clean_db(), owner_engine(), world(), person(), audit_rows(), client(), row() (+8 more)

### Community 99 - "environment"
Cohesion: 0.18
Nodes (11): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_DB_PASSWORD, KC_HOSTNAME, KC_HOSTNAME_ADMIN, SETHU_PUBLIC_BASE_URL, command, entrypoint, environment (+3 more)

### Community 100 - "backup.sh"
Cohesion: 0.36
Nodes (9): backup_once(), counts(), GNUPGHOME, log(), PGHOST, PGUSER, prune(), restore() (+1 more)

### Community 101 - "users/repo.py"
Cohesion: 0.14
Nodes (10): list_people(), _all(), find(), heads(), insert(), listing(), update(), listing() (+2 more)

### Community 104 - "complaints/service.py"
Cohesion: 0.11
Nodes (14): act(), actor_id(), assignees(), can_act(), CaseError, complainant_visible(), get(), institution_timeline() (+6 more)

### Community 105 - "Runbook"
Cohesion: 0.22
Nodes (8): 1. First start, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, Restore, Restore drill (2026-11-20, throwaway production-mode stack), Runbook, Tamper demonstration

### Community 107 - "test_audit_view.py"
Cohesion: 0.36
Nodes (4): client(), test_newest_first_with_filters(), test_only_auditor_oversight_and_admin_read_the_ledger(), test_verify_names_a_corrupted_row_and_restoring_it_heals_the_chain()

### Community 111 - "web"
Cohesion: 0.25
Nodes (8): condition, backend, keycloak, condition, web, depends_on, ports, volumes

### Community 117 - "alerts/service.py"
Cohesion: 0.06
Nodes (24): decide(), list_alerts(), retry(), _all(), claim_next(), decide(), delivered_to(), known_addresses() (+16 more)

### Community 124 - "services"
Cohesion: 0.17
Nodes (12): secrets, profiles, ports, profiles, secrets, services, backend, demo-users (+4 more)

### Community 128 - "redis"
Cohesion: 0.20
Nodes (10): healthcheck, REDIS_PASSWORD, interval, start_period, test, command, environment, healthcheck (+2 more)

### Community 129 - "migrate"
Cohesion: 0.33
Nodes (6): MIGRATION_DATABASE_PASSWORD_FILE, MIGRATION_DATABASE_URL, environment, restart, secrets, migrate

### Community 130 - "7. Production"
Cohesion: 0.25
Nodes (8): 7. Production, Configuration reference, Keycloak administration (SSH tunnel), Published ports, Secrets, Start, The production realm, TLS certificate

### Community 131 - "datetime"
Cohesion: 0.16
Nodes (7): Alert, AlertPage, DecisionIn, ChainReport, Entry, EntryPage, Person

### Community 132 - "findings/schemas.py"
Cohesion: 0.29
Nodes (5): DecisionIn, DetectOut, Finding, Trend, TrendRow

### Community 135 - "env.py"
Cohesion: 0.15
Nodes (6): run_migrations_online(), _url(), production_problems(), read_secret(), _weak(), with_password()

### Community 139 - "search/schemas.py"
Cohesion: 0.43
Nodes (4): ComplaintHit, ComplaintHits, InstitutionHit, Results

### Community 142 - "Seed data"
Cohesion: 0.33
Nodes (5): Files, Negative cases: no alert expected, Seed data, Seeded patterns and the expected detection, What the loader does

### Community 144 - "add"
Cohesion: 0.70
Nodes (5): add(), act(), assign(), close(), transfer()

### Community 145 - "deploy"
Cohesion: 0.50
Nodes (4): deploy, resources, memory, limits

## Knowledge Gaps
- **4 isolated node(s):** `sethu-backend`, `GNUPGHOME`, `PGHOST`, `PGUSER`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 784 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **48 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `test_search.py`, `institutions/repo.py`, `test_alerts.py`, `sqlalchemy`, `session_for`, `list_entries`, `test_overlaps.py`, `overlaps/service.py`, `bureaus/service.py`, `test_complainant.py`, `test_findings.py`, `findings/service.py`, `reports/service.py`, `complaints/api.py`, `session.py`, `get_principal`, `get_principal`, `pytest`, `users/repo.py`, `complaints/service.py`, `test_audit_view.py`, `alerts/service.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sethu-backend`, `GNUPGHOME`, `PGHOST` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `load.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12857142857142856 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `load.py`, `test_search.py`, `test_findings.py`, `test_alerts.py`, `dashboard/repo.py`, `Principal`, `test_overlaps.py`, `overlaps/service.py`, `Architecture`, `test_complainant.py`, `test_findings.py`, `test_seed.py`, `session.py`, `test_reports.py`, `get_principal`, `worker.py`, `get_principal`, `pytest`, `alerts/service.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_search.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10344827586206896 - nodes in this community are weakly interconnected._