# Graph Report - jolly-feynman-1a9f96  (2026-11-22)

## Corpus Check
- 213 files · ~127,487 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 25 file(s) not represented in the graph (top: (none) 8, .csv 7, .lock 3)

## Summary
- 2553 nodes · 5831 edges · 162 communities (132 shown, 30 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 200 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `071e404d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- environment
- test_overlaps.py
- complaints/repo.py
- with
- institutions/repo.py
- test_findings.py
- test_alerts.py
- backend
- intake/api.py
- Principal
- institutions/schemas.py
- package.json
- options
- App
- institutions/types.ts
- intake/repo.py
- sqlalchemy
- graph/repo.py
- intake/schemas.py
- postgres
- env.py
- overlaps/repo.py
- web
- bureaus/service.py
- demo-users
- 3. Database
- k6.js
- x-backend-env
- compilerOptions
- environment
- crypto.py
- test_findings.py
- redis
- keycloak
- environment
- get_settings
- x-prod-backend-env
- 01. Scope Lock
- test_cases.py
- AuditLog.tsx
- complaints/service.py
- decide
- test_search.py
- record
- api.ts
- healthcheck
- complaints/api.py
- services
- Architecture Decision Records
- Architecture Snapshot
- test_seed.py
- migrate
- create
- session.py
- 03. Demo Story: "Institution A"
- 04. Mock Data Spec
- test_intake.py
- test_security.py
- api
- 05. Next Claude Code Prompts
- decide
- backup
- postgres
- import.sh
- SETHU
- .claude/CLAUDE.md
- 01-roles.sh
- reports/service.py
- reports/service.py
- test_scheduler.py
- sethu-backend
- test_auth_and_api.py
- environment
- dashboard/repo.py
- react
- graph/schemas.py
- detect
- get_principal
- worker
- secrets
- sqlalchemy
- test_config.py
- Findings.tsx
- logging.py
- scheduler
- OPERATIONS.md
- session_for
- Architecture
- task
- json
- environment
- backup.sh
- users/repo.py
- Data Model
- list_findings
- test_filters.py
- conftest.py
- Operations guide
- decide
- web
- Findings
- dashboard/schemas.py
- verify
- flow
- build
- alerts/repo.py
- config.py
- spool
- page
- search/schemas.py
- resources
- SETHU
- services
- decide
- export
- client
- redis
- migrate
- User guide
- audit_view/schemas.py
- _send_one
- Alerts.tsx
- as_
- complainant_key.py
- Security
- list_links
- Intake API: send one complaint
- Load test, failure drills and the offline run
- SingleScheduler
- Runbook
- 7. Production
- offline.sh
- alerts/schemas.py
- test_reports.py
- test_audit_view.py
- deliver
- safe_reason
- client
- pair
- spike_findings
- Report
- queue_findings
- deadline_findings
- workload
- complainant_visible
- test_missed_deadlines_make_one_digest_per_bureau_per_run_and_only_for_new_ones

## God Nodes (most connected - your core abstractions)
1. `session_for()` - 178 edges
2. `Principal` - 168 edges
3. `get_settings()` - 72 edges
4. `useLoad()` - 49 edges
5. `record()` - 45 edges
6. `api()` - 31 edges
7. `verify()` - 28 edges
8. `get_principal()` - 28 edges
9. `detect()` - 27 edges
10. `x-backend-env` - 23 edges

## Surprising Connections (you probably didn't know these)
- `Layout` --references--> `record()`  [INFERRED]
  CLAUDE.md → backend/app/audit/service.py
- `6. Audit ledger` --references--> `verify()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/audit/service.py
- `Tamper demonstration` --references--> `verify()`  [INFERRED]
  docs/RUNBOOK.md → backend/app/audit/service.py
- `Method` --references--> `require_roles()`  [INFERRED]
  docs/SECURITY-REVIEW.md → backend/app/core/auth.py
- `3. Trust boundaries and how each is defended` --references--> `session_for()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/db/session.py

## Import Cycles
- None detected.

## Communities (162 total, 30 thin omitted)

### Community 0 - "environment"
Cohesion: 0.27
Nodes (20): environment, SETHU_ALERT_FROM, SETHU_AUDIT_ANCHOR_DIR, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_INTAKE_SPOOL_DIR, SETHU_KEYCLOAK_EVENTS_SECRET (+12 more)

### Community 1 - "test_overlaps.py"
Cohesion: 0.16
Nodes (16): OverlapError, detected(), scalar(), suggested_pairs(), test_a_second_overlap_run_is_skipped_while_one_is_running(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs() (+8 more)

### Community 2 - "complaints/repo.py"
Cohesion: 0.14
Nodes (22): _all(), assigned_to(), bureaus(), case_counts(), deadline_days(), deadlines(), exists(), find() (+14 more)

### Community 3 - "with"
Cohesion: 0.05
Nodes (55): runs-on, services, steps, needs, runs-on, steps, timeout-minutes, concurrency (+47 more)

### Community 4 - "institutions/repo.py"
Cohesion: 0.07
Nodes (31): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+23 more)

### Community 5 - "test_findings.py"
Cohesion: 0.15
Nodes (19): cell(), detected(), findings_as(), hop(), test_a_second_run_adds_nothing(), test_a_spike_that_comes_back_is_reopened_with_its_new_counts(), test_an_acknowledgement_or_any_action_breaks_the_loop(), test_dismiss_reopen_and_resolve_are_audited_and_limited() (+11 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.12
Nodes (21): alert_row(), audit_count(), closed_port(), deliver(), FakeSMTP, held(), make_due(), relay() (+13 more)

### Community 7 - "backend"
Cohesion: 0.13
Nodes (17): build, cap_drop, depends_on, networks, read_only, restart, secrets, security_opt (+9 more)

### Community 8 - "intake/api.py"
Cohesion: 0.24
Nodes (14): create_source(), issue_key(), items(), manual(), retry(), reviewed(), _run(), sources() (+6 more)

### Community 9 - "Principal"
Cohesion: 0.16
Nodes (21): Principal, world(), person(), test_each_role_sees_only_its_share_of_links_and_transfers_and_never_text(), _count(), _refs(), test_a_bureau_can_only_hand_a_case_over_as_itself(), test_a_bureau_cannot_read_links_or_alerts_it_is_not_party_to() (+13 more)

### Community 10 - "institutions/schemas.py"
Cohesion: 0.17
Nodes (17): Alias, BureauCount, Candidate, CaseSummary, CategoryShare, Disposal, Dna, Institution (+9 more)

### Community 11 - "package.json"
Cohesion: 0.07
Nodes (31): @axe-core/playwright, @playwright/test, @types/cytoscape, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react (+23 more)

### Community 12 - "options"
Cohesion: 0.11
Nodes (24): logging, logging, driver, options, cap_drop, image, logging, networks (+16 more)

### Community 13 - "App"
Cohesion: 0.13
Nodes (29): App(), ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters, History() (+21 more)

### Community 14 - "institutions/types.ts"
Cohesion: 0.11
Nodes (29): useLoad(), InstitutionTimeline(), DnaPanel(), pct(), TREND, InstitutionList(), InstitutionProfile(), ResolutionQueue() (+21 more)

### Community 15 - "intake/repo.py"
Cohesion: 0.15
Nodes (19): _all(), claim_next(), failed(), finish(), forget_nonces(), health(), insert_item(), insert_source() (+11 more)

### Community 16 - "sqlalchemy"
Cohesion: 0.13
Nodes (8): anchor_check(), list_entries(), verify(), actions(), entries(), entry(), entries(), verify()

### Community 17 - "graph/repo.py"
Cohesion: 0.06
Nodes (19): live(), me(), metrics(), ready(), _label(), observe_request(), _process_lines(), record_run() (+11 more)

### Community 18 - "intake/schemas.py"
Cohesion: 0.18
Nodes (10): Accepted, Complainant, IssuedKey, Item, RowError, Source, SourceIn, SourcePatch (+2 more)

### Community 19 - "postgres"
Cohesion: 0.11
Nodes (18): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+10 more)

### Community 20 - "env.py"
Cohesion: 0.29
Nodes (4): run_migrations_online(), _url(), read_secret(), with_password()

### Community 21 - "overlaps/repo.py"
Cohesion: 0.18
Nodes (13): _all(), candidates(), decide(), insert_alert(), linked_case_ids(), links(), links_page(), _one() (+5 more)

### Community 22 - "web"
Cohesion: 0.15
Nodes (13): condition, backend, web, build, cap_drop, depends_on, networks, ports (+5 more)

### Community 23 - "bureaus/service.py"
Cohesion: 0.10
Nodes (17): create_bureau(), list_bureaus(), _run(), update_bureau(), _all(), by_code(), get(), insert() (+9 more)

### Community 24 - "demo-users"
Cohesion: 0.14
Nodes (14): cap_drop, depends_on, entrypoint, image, networks, profiles, read_only, restart (+6 more)

### Community 25 - "3. Database"
Cohesion: 0.11
Nodes (19): 3. Database, Alert mail (dev and demo), Audit-chain anchors, Browser tests, Case workflow, Complainant details: keys, Complaint intake, Continuous integration (+11 more)

### Community 26 - "k6.js"
Cohesion: 0.16
Nodes (18): b64url(), CATEGORIES, detector(), get(), intake(), internal(), officer(), options (+10 more)

### Community 27 - "x-backend-env"
Cohesion: 0.09
Nodes (23): x-backend-env, SETHU_AUDIT_ANCHOR_DIR, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_COMPLAINANT_KEYS_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT (+15 more)

### Community 28 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 29 - "environment"
Cohesion: 0.15
Nodes (13): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_BOOTSTRAP_ADMIN_USERNAME, KC_DB, KC_DB_PASSWORD, KC_DB_URL, KC_DB_USERNAME, KC_HEALTH_ENABLED, KC_HOSTNAME (+5 more)

### Community 30 - "crypto.py"
Cohesion: 0.18
Nodes (11): key_id_of(), Keyring, KeyringError, load_keyring(), parse_keyring(), _split(), ring(), test_a_broken_keyring_is_refused_without_showing_a_key() (+3 more)

### Community 31 - "test_findings.py"
Cohesion: 0.23
Nodes (10): scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_officer_picks_from_the_queue(), test_profile_dna_measures(), test_profile_shows_every_bureau_without_complaint_text() (+2 more)

### Community 32 - "redis"
Cohesion: 0.17
Nodes (12): REDIS_PASSWORD, cap_add, cap_drop, command, environment, image, networks, read_only (+4 more)

### Community 33 - "keycloak"
Cohesion: 0.15
Nodes (13): postgres, cap_drop, command, depends_on, deploy, image, networks, restart (+5 more)

### Community 34 - "environment"
Cohesion: 0.15
Nodes (13): KEYCLOAK_DB_PASSWORD, KEYCLOAK_DB_PASSWORD_FILE, POSTGRES_PASSWORD, POSTGRES_PASSWORD_FILE, SETHU_APP_PASSWORD, SETHU_APP_PASSWORD_FILE, SETHU_AUDITOR_PASSWORD, SETHU_AUDITOR_PASSWORD_FILE (+5 more)

### Community 35 - "get_settings"
Cohesion: 0.17
Nodes (11): get_settings(), main(), detect(), embed_pending(), _embedder(), semantic_on(), detect_overlaps(), detect() (+3 more)

### Community 36 - "x-prod-backend-env"
Cohesion: 0.05
Nodes (43): file, file, file, file, file, file, file, secrets (+35 more)

### Community 37 - "01. Scope Lock"
Cohesion: 0.17
Nodes (11): 01. Scope Lock, Constraints, Definition of done (per feature), Freeze rules, Goal in one sentence, Out of scope (do not discuss again), Parking lot, Sign-off (+3 more)

### Community 38 - "test_cases.py"
Cohesion: 0.17
Nodes (13): CaseError, audit_rows(), scalar(), test_api_hides_text_and_enforces_roles(), test_every_action_is_audited_and_the_chain_verifies(), test_list_filters_search_and_institution_timeline(), test_loop_case_c090_shows_both_unacknowledged_transfers(), test_officer_cannot_read_or_change_another_bureaus_complaint() (+5 more)

### Community 39 - "AuditLog.tsx"
Cohesion: 0.18
Nodes (12): AnchorReport, Anchors(), AuditLog(), ChainReport, EMPTY, Entry, EntryPage, moment() (+4 more)

### Community 40 - "complaints/service.py"
Cohesion: 0.13
Nodes (18): act(), actor_id(), assignees(), can_act(), deadline_days(), deadlines(), due_at(), get() (+10 more)

### Community 41 - "decide"
Cohesion: 0.18
Nodes (10): _can_decide(), _cases(), decide(), linked_case_ids(), links(), links_page(), _shape(), tier1() (+2 more)

### Community 42 - "test_search.py"
Cohesion: 0.18
Nodes (10): search(), test_a_bureau_code_matches_exactly_in_search(), test_api_decisions_detection_and_the_overlapping_filter(), find(), hits(), test_bureau_a_never_sees_bureau_b_text_through_search(), test_cases_by_reference_and_metadata_across_bureaus(), test_institutions_by_name_alias_initials_and_city() (+2 more)

### Community 43 - "record"
Cohesion: 0.13
Nodes (23): record(), sources(), ComplaintIn, body_hash(), _by_name(), create_source(), _enqueue(), fingerprint() (+15 more)

### Community 44 - "api.ts"
Cohesion: 0.09
Nodes (32): react, react-dom, dependencies, cytoscape@3.30.4, react@^18.3.1, react-dom@^18.3.1, answer(), download() (+24 more)

### Community 45 - "healthcheck"
Cohesion: 0.47
Nodes (11): interval, retries, start_period, test, timeout, healthcheck, healthcheck, healthcheck (+3 more)

### Community 46 - "complaints/api.py"
Cohesion: 0.05
Nodes (42): blank_to_none(), PageMeta, act(), assignees(), case(), deadlines(), institution_timeline(), list_cases() (+34 more)

### Community 47 - "services"
Cohesion: 0.13
Nodes (14): internal, file, internal, name, networks, app, data, edge (+6 more)

### Community 48 - "Architecture Decision Records"
Cohesion: 0.22
Nodes (8): 0001. Modular monolith, not microservices, 0002. Enforce access in the database with Row-Level Security, 0003. Hash-chained audit log inside PostgreSQL, not a blockchain, 0004. Transactional outbox for alerts, 0005. Local models only, each with a deterministic fallback, 0006. Object storage deferred, 0007. Keycloak for identity, Architecture Decision Records

### Community 49 - "Architecture Snapshot"
Cohesion: 0.22
Nodes (8): Architecture Pattern, Architecture Snapshot, Critical Modules, Dependency Rules, Entry Points, Extraction Quality, Repository Map, Routes

### Community 50 - "test_seed.py"
Cohesion: 0.07
Nodes (21): cross_bureau_pairs(), deadlocks(), duplicate_pairs(), not_closed(), silent(), spikes(), tagged(), test_expected_detections() (+13 more)

### Community 51 - "migrate"
Cohesion: 0.18
Nodes (11): MIGRATION_DATABASE_URL, build, cap_drop, command, environment, logging, networks, read_only (+3 more)

### Community 52 - "create"
Cohesion: 0.15
Nodes (8): insert_action(), insert_complaint(), search(), create(), keyring(), lock_text(), rotate_complainant_keys(), _create()

### Community 53 - "session.py"
Cohesion: 0.16
Nodes (6): require_roles(), page_params(), get_session(), Bureau, BureauRow, Person

### Community 54 - "03. Demo Story: "Institution A""
Cohesion: 0.25
Nodes (7): 03. Demo Story: "Institution A", Characters (fictional), Cut list if the demo runs long, Rehearsal checklist, Script, Seeded facts, The story in one line

### Community 55 - "04. Mock Data Spec"
Cohesion: 0.25
Nodes (7): 04. Mock Data Spec, Deliberate patterns to seed, Expected detections (used by tests), Files to generate, Fixed demo records (do not randomise), Negative cases (must NOT be flagged), Volume

### Community 56 - "test_intake.py"
Cohesion: 0.18
Nodes (4): make_due(), test_a_failing_attempt_is_retried_then_dead_lettered_and_an_admin_can_retry_it(), test_the_intake_api_has_a_per_source_quota(), test_while_the_primary_is_down_its_items_wait_and_the_fallback_spool_takes_over()

### Community 57 - "test_security.py"
Cohesion: 0.20
Nodes (8): parse_rows(), test_a01_001_a_link_in_the_spool_folder_is_refused_unread(), test_a01_001_an_unknown_header_is_not_echoed(), test_a06_001_a_spreadsheet_that_expands_too_far_is_refused_before_parsing(), test_a06_001_the_row_limit_is_enforced_while_reading(), _xlsx(), OWASP-A01-001 Spool folder: a symbolic link is followed and the target's first line echoed back (CWE-59, Improper Link Resolution Before File Access), OWASP-A06-001 XLSX expansion and row count not bounded before parsing (CWE-409, Improper Handling of Highly Compressed Data)

### Community 58 - "api"
Cohesion: 0.10
Nodes (30): api(), AdminPage(), changed(), create(), BureauLine(), save(), BureauRow, Deadline (+22 more)

### Community 59 - "05. Next Claude Code Prompts"
Cohesion: 0.33
Nodes (5): 05. Next Claude Code Prompts, After that, in this order, Prompt 1: bring the stack up, Prompt 2: mock data, Prompt 3: first feature (institutions and resolution)

### Community 60 - "decide"
Cohesion: 0.23
Nodes (5): AlertError, decide(), listing(), retry(), _shape()

### Community 61 - "backup"
Cohesion: 0.09
Nodes (22): cap_drop, command, depends_on, deploy, entrypoint, environment, image, networks (+14 more)

### Community 62 - "postgres"
Cohesion: 0.40
Nodes (4): networks, ports, services, postgres

### Community 67 - "import.sh"
Cohesion: 1.00
Nodes (3): kcadm(), login(), import.sh script

### Community 68 - "SETHU"
Cohesion: 0.50
Nodes (3): Quick start (Windows, PowerShell), SETHU, What is here

### Community 72 - "reports/service.py"
Cohesion: 0.27
Nodes (6): _all(), bureaus(), _in_range(), institutions(), overlaps(), test_no_complaint_text_or_complainant_details_in_logs_audit_or_errors()

### Community 73 - "reports/service.py"
Cohesion: 0.24
Nodes (4): _cell(), export(), run(), test_never_in_search_lists_reports_exports_audit_or_logs()

### Community 74 - "test_scheduler.py"
Cohesion: 0.24
Nodes (5): scheduler(), start(), test_a_scheduler_that_lost_its_lock_stops(), test_a_second_scheduler_refuses_to_start(), test_the_lock_passes_on_when_the_scheduler_stops_or_dies()

### Community 78 - "test_auth_and_api.py"
Cohesion: 0.07
Nodes (23): AuthError, decode_token(), principal_from_claims(), _call(), fetch(), _realm_url(), shape(), Unavailable (+15 more)

### Community 79 - "environment"
Cohesion: 0.17
Nodes (29): environment, environment, DEMO_USER_PASSWORD, KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_ADMIN_USER, SETHU_AUDIT_ANCHOR_DIR, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE (+21 more)

### Community 80 - "dashboard/repo.py"
Cohesion: 0.18
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 81 - "react"
Cohesion: 0.21
Nodes (16): cytoscape, ComplaintDetail(), EDGE_WORDS, GraphPage(), GraphTable(), KINDS, NodePanel(), COLOURS (+8 more)

### Community 82 - "graph/schemas.py"
Cohesion: 0.43
Nodes (4): Edge, Filters, Graph, Node

### Community 83 - "detect"
Cohesion: 0.16
Nodes (15): _all(), bureau_codes(), bureau_queues(), category_cells(), existing(), insert(), insert_alert(), institution_queues() (+7 more)

### Community 84 - "get_principal"
Cohesion: 0.08
Nodes (17): get_principal(), _jwks_client(), board(), counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data() (+9 more)

### Community 86 - "worker"
Cohesion: 0.18
Nodes (11): worker, build, cap_drop, command, networks, read_only, restart, secrets (+3 more)

### Community 87 - "secrets"
Cohesion: 0.25
Nodes (6): ensure_added_keys(), ensure_keyring(), main(), main(), rotate(), _write()

### Community 89 - "test_config.py"
Cohesion: 0.20
Nodes (11): refused(), settings(), _shell(), test_a_complete_production_configuration_starts(), test_all_problems_are_reported_at_once(), test_an_unreadable_secret_file_is_named_not_shown(), test_dev_and_test_keep_working_with_dev_values(), test_each_unsafe_value_is_refused_by_name() (+3 more)

### Community 90 - "Findings.tsx"
Cohesion: 0.12
Nodes (24): cases(), Count, CountTable(), Dashboard(), day(), OverdueCase, Overview, Trend() (+16 more)

### Community 91 - "logging.py"
Cohesion: 0.07
Nodes (17): accept_request_id(), configure_logging(), JsonFormatter, get_engine(), create_app(), request_context(), signins(), search() (+9 more)

### Community 92 - "scheduler"
Cohesion: 0.20
Nodes (10): build, cap_drop, command, networks, read_only, restart, secrets, security_opt (+2 more)

### Community 93 - "OPERATIONS.md"
Cohesion: 0.22
Nodes (5): API, Who calls what, Gaps, Phases (proposed), Production readiness

### Community 94 - "session_for"
Cohesion: 0.08
Nodes (16): apply_context(), session_for(), kinds(), test_a_bureau_sees_only_alerts_it_is_party_to(), test_a_deactivated_bureau_takes_no_transfers(), test_the_database_lets_a_person_write_only_their_own_row_with_their_token_role(), test_the_database_refuses_bureau_writes_from_anyone_but_admin(), net() (+8 more)

### Community 95 - "Architecture"
Cohesion: 0.17
Nodes (11): 10. Scaling path (after the hackathon), 11. What has been verified, 1. Shape, 2. Components, 3. Trust boundaries and how each is defended, 4. Request flow (example: approve an overlap link), 5. Processing pipeline (worker), 6. Audit ledger (+3 more)

### Community 96 - "task"
Cohesion: 0.17
Nodes (6): detect_findings(), process_intake(), resolve_pending(), rotate_complainant_keys(), take_spool(), verify_chain()

### Community 98 - "json"
Cohesion: 0.16
Nodes (10): compare(), export(), _file(), main(), export_anchor(), anchored(), check(), test_a_rewritten_entry_or_a_replaced_database_is_reported() (+2 more)

### Community 99 - "environment"
Cohesion: 0.18
Nodes (11): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_DB_PASSWORD, KC_HOSTNAME, KC_HOSTNAME_ADMIN, SETHU_PUBLIC_BASE_URL, command, entrypoint, environment (+3 more)

### Community 100 - "backup.sh"
Cohesion: 0.36
Nodes (10): backup_once(), counts(), GNUPGHOME, log(), PGHOST, PGUSER, prune(), record_run() (+2 more)

### Community 101 - "users/repo.py"
Cohesion: 0.17
Nodes (8): list_people(), _all(), find(), heads(), insert(), listing(), update(), listing()

### Community 103 - "Data Model"
Cohesion: 0.29
Nodes (6): Adding a table, Data Model, Database roles, Planned additions, Request context and policies, Tables

### Community 104 - "list_findings"
Cohesion: 0.18
Nodes (6): decide(), detect(), list_findings(), trend(), page(), trend()

### Community 105 - "test_filters.py"
Cohesion: 0.18
Nodes (12): get(), test_alert_status_filter(), test_audit_filters_narrow_combine_and_ignore_blanks(), test_each_case_filter_narrows_and_blank_is_no_filter(), total(), test_institution_list_filters(), test_institution_search_by_city_state_initials_typo_and_permanent_id(), test_institutions_screen_and_top_bar_search_agree() (+4 more)

### Community 107 - "conftest.py"
Cohesion: 0.15
Nodes (7): app_engine(), clean_db(), owner_engine(), write(), check_pem(), main(), nginx()

### Community 108 - "Operations guide"
Cohesion: 0.17
Nodes (12): 10. Incident response, 11. Known limits, 1. What runs, 2. Install, 3. Configuration reference, 4. First-time setup (after the first start), 5. Upgrade, 6. Backup and restore, and the drill (+4 more)

### Community 109 - "decide"
Cohesion: 0.14
Nodes (8): set_status(), _alert(), decide(), _digest(), FindingError, open_count(), _set(), recipients()

### Community 111 - "web"
Cohesion: 0.25
Nodes (8): condition, backend, keycloak, condition, web, depends_on, ports, volumes

### Community 112 - "Findings"
Cohesion: 0.14
Nodes (12): test_a02_001_the_api_description_is_not_under_the_proxied_path(), Areas checked with no finding, Findings, Method, OWASP-A02-001 The API description was served through the edge in dev (CWE-200, Exposure of Sensitive Information to an Unauthorized Actor), OWASP-A02-002 `/health/ready` reachable from outside (CWE-200), OWASP-A02-003 CSP allows inline styles (CWE-1021 family; style injection only), OWASP-A02-004 Dev realm is looser than production (+4 more)

### Community 113 - "dashboard/schemas.py"
Cohesion: 0.36
Nodes (6): Attention, Count, OverdueCase, Overview, Totals, Week

### Community 114 - "verify"
Cohesion: 0.18
Nodes (13): ChainStatus, verify(), _append(), test_actor_comes_from_the_session_not_the_caller(), test_chain_is_valid_and_sequential(), test_client_cannot_choose_seq_or_hash(), test_deleted_row_is_detected(), test_runtime_role_cannot_rewrite_history() (+5 more)

### Community 115 - "flow"
Cohesion: 0.50
Nodes (4): flow(), act(), as_(), sql()

### Community 116 - "build"
Cohesion: 0.26
Nodes (9): build(), add(), act(), assign(), close(), transfer(), details(), fresh() (+1 more)

### Community 117 - "alerts/repo.py"
Cohesion: 0.22
Nodes (8): _all(), claim_next(), decide(), delivered_to(), known_addresses(), listing(), mark(), retry()

### Community 118 - "config.py"
Cohesion: 0.12
Nodes (7): production_problems(), Settings, _weak(), _client(), queue(), status(), test_tls_modes_verify_the_relay_certificate()

### Community 119 - "spool"
Cohesion: 0.24
Nodes (4): spool(), test_files_are_what_the_generator_produces(), render(), variant()

### Community 120 - "page"
Cohesion: 0.29
Nodes (5): capped_count(), page(), listing(), page(), _where()

### Community 121 - "search/schemas.py"
Cohesion: 0.43
Nodes (4): ComplaintHit, ComplaintHits, InstitutionHit, Results

### Community 122 - "resources"
Cohesion: 0.20
Nodes (10): deploy, deploy, resources, memory, deploy, deploy, limits, deploy (+2 more)

### Community 123 - "SETHU"
Cohesion: 0.22
Nodes (8): Commands, graphify, Layout, Non-negotiable rules, Read first, SETHU, Stack, Working agreements

### Community 124 - "services"
Cohesion: 0.14
Nodes (14): secrets, environment, profiles, SETHU_ENVIRONMENT, ports, profiles, secrets, services (+6 more)

### Community 125 - "decide"
Cohesion: 0.25
Nodes (3): decide(), list_alerts(), retry()

### Community 126 - "export"
Cohesion: 0.33
Nodes (3): _check(), export(), report()

### Community 127 - "client"
Cohesion: 0.28
Nodes (7): audit_rows(), client(), row(), test_a_token_without_email_keeps_the_stored_address(), test_admin_creates_and_deactivates_a_bureau_and_both_are_audited(), test_first_sign_in_creates_the_record_with_email_and_a_bureau_change_reaches_it(), test_people_without_email_are_flagged_for_the_admin()

### Community 128 - "redis"
Cohesion: 0.20
Nodes (10): healthcheck, REDIS_PASSWORD, interval, start_period, test, command, environment, healthcheck (+2 more)

### Community 129 - "migrate"
Cohesion: 0.33
Nodes (6): MIGRATION_DATABASE_PASSWORD_FILE, MIGRATION_DATABASE_URL, environment, restart, secrets, migrate

### Community 130 - "User guide"
Cohesion: 0.22
Nodes (8): Admin, Auditor, Bureau head, If something looks wrong, Officer, Oversight, Signing in and moving around, User guide

### Community 131 - "audit_view/schemas.py"
Cohesion: 0.31
Nodes (6): AnchorLatest, AnchorReport, ChainReport, Entry, EntryPage, SignIn

### Community 132 - "_send_one"
Cohesion: 0.25
Nodes (3): backoff(), _connect(), _send_one()

### Community 133 - "Alerts.tsx"
Cohesion: 0.32
Nodes (7): Alert, AlertCard(), decide(), AlertPage, AlertsPage(), moment(), STATUS

### Community 134 - "as_"
Cohesion: 0.19
Nodes (12): listing(), test_cross_bureau_numbers_are_the_same_for_everyone(), as_(), test_case_pages_cover_every_case_once_and_end_exactly(), test_dashboard_counts_are_bounded(), test_filters_combine_with_pages(), test_finding_and_overlap_pages(), test_page_size_is_bounded() (+4 more)

### Community 135 - "complainant_key.py"
Cohesion: 0.43
Nodes (3): main(), _new_key(), _write()

### Community 136 - "Security"
Cohesion: 0.33
Nodes (5): Assets, Before any real deployment, Compliance notes (to confirm with the AICTE mentor), Rules for contributors, Security

### Community 137 - "list_links"
Cohesion: 0.21
Nodes (4): decide(), detect_status(), list_links(), tier1()

### Community 139 - "Intake API: send one complaint"
Cohesion: 0.25
Nodes (8): Answer, Body, Errors, Example, Headers, Intake API: send one complaint, Other channels, Signing and transport

### Community 140 - "Load test, failure drills and the offline run"
Cohesion: 0.25
Nodes (7): Drills, How to run it, Load test, failure drills and the offline run, Measured before the host gave out (not capacity figures), Paged lists (2026-11-22), Status (2026-11-21): incomplete, To run on a larger machine (at least 16 GB of RAM, nothing else running)

### Community 142 - "Runbook"
Cohesion: 0.20
Nodes (10): 1. First start, 2. Daily use, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, Restore, Restore drill (2026-11-20, throwaway production-mode stack), Runbook (+2 more)

### Community 143 - "7. Production"
Cohesion: 0.25
Nodes (8): 7. Production, Configuration reference, Keycloak administration (SSH tunnel), Published ports, Secrets, Start, The production realm, TLS certificate

### Community 144 - "offline.sh"
Cohesion: 0.40
Nodes (3): MSYS_NO_PATHCONV, offline.sh script, vm()

### Community 145 - "alerts/schemas.py"
Cohesion: 0.47
Nodes (3): Alert, AlertPage, DecisionIn

### Community 146 - "test_reports.py"
Cohesion: 0.23
Nodes (9): client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_export_is_csv_without_text_and_is_audited(), test_institution_report_counts_only_the_callers_cases(), test_overlap_outcomes(), test_viewing_is_not_audited_and_bad_names_are_refused() (+1 more)

### Community 147 - "test_audit_view.py"
Cohesion: 0.36
Nodes (4): client(), test_newest_first_with_filters(), test_only_auditor_oversight_and_admin_read_the_ledger(), test_verify_names_a_corrupted_row_and_restoring_it_heals_the_chain()

### Community 148 - "deliver"
Cohesion: 0.33
Nodes (3): deliver(), deliver_alerts(), Observability

### Community 151 - "safe_reason"
Cohesion: 0.33
Nodes (3): Held, safe_reason(), Threats and controls

## Knowledge Gaps
- **5 isolated node(s):** `sethu-backend`, `PGHOST`, `PGUSER`, `GNUPGHOME`, `MSYS_NO_PATHCONV`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1042 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `test_overlaps.py`, `institutions/repo.py`, `test_alerts.py`, `intake/api.py`, `list_links`, `sqlalchemy`, `graph/repo.py`, `test_audit_view.py`, `bureaus/service.py`, `test_findings.py`, `complainant_visible`, `get_settings`, `complaints/service.py`, `decide`, `test_search.py`, `record`, `complaints/api.py`, `create`, `session.py`, `test_intake.py`, `decide`, `reports/service.py`, `test_auth_and_api.py`, `detect`, `get_principal`, `sqlalchemy`, `logging.py`, `session_for`, `users/repo.py`, `list_findings`, `conftest.py`, `decide`, `verify`, `flow`, `decide`, `export`, `client`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sethu-backend`, `PGHOST`, `PGUSER` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `complaints/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13968253968253969 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `test_overlaps.py`, `test_findings.py`, `test_alerts.py`, `as_`, `intake/api.py`, `Principal`, `intake/repo.py`, `graph/repo.py`, `test_reports.py`, `deliver`, `client`, `pair`, `crypto.py`, `test_findings.py`, `test_missed_deadlines_make_one_digest_per_bureau_per_run_and_only_for_new_ones`, `get_settings`, `test_cases.py`, `decide`, `test_search.py`, `record`, `test_seed.py`, `session.py`, `test_intake.py`, `test_security.py`, `reports/service.py`, `test_auth_and_api.py`, `get_principal`, `sqlalchemy`, `logging.py`, `Architecture`, `task`, `json`, `test_filters.py`, `conftest.py`, `verify`, `flow`, `spool`, `client`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Are the 104 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 104 INFERRED edges - model-reasoned connections that need verification._
- **Should `with` be split into smaller, more focused modules?**
  _Cohesion score 0.05194805194805195 - nodes in this community are weakly interconnected._