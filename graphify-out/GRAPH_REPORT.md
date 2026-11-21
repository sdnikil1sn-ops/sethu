# Graph Report - jolly-feynman-1a9f96  (2026-11-21)

## Corpus Check
- 195 files · ~108,882 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 25 file(s) not represented in the graph (top: (none) 8, .csv 7, .lock 3)

## Summary
- 2331 nodes · 5247 edges · 141 communities (114 shown, 27 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 166 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4bccf1c1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- environment
- load
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
- test_audit_view.py
- graph/repo.py
- intake/schemas.py
- postgres
- config.py
- overlaps/repo.py
- web
- bureaus/service.py
- demo-users
- 3. Database
- Architecture
- x-backend-env
- compilerOptions
- environment
- crypto.py
- test_findings.py
- redis
- keycloak
- environment
- metrics.py
- x-prod-backend-env
- 01. Scope Lock
- 02. PS Coverage Checklist (SIH26264)
- AuditLog.tsx
- test_search.py
- overlaps/service.py
- export
- record
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
- create
- api
- 05. Next Claude Code Prompts
- findings/schemas.py
- backup
- postgres
- import.sh
- SETHU
- .claude/CLAUDE.md
- 01-roles.sh
- reports/service.py
- test_scheduler.py
- sethu-backend
- get_principal
- environment
- dashboard/repo.py
- react
- datetime
- detect
- test_graph.py
- worker
- secrets
- detect
- test_config.py
- Findings.tsx
- worker.py
- scheduler
- Production readiness
- session_for
- sys
- search
- Seed data
- environment
- backup.sh
- users/repo.py
- SETHU_ENVIRONMENT
- user_id
- test_filters.py
- pathlib
- flow
- test_overlaps.py
- web
- test_directory.py
- add
- verify
- test_intake.py
- build
- alerts/repo.py
- test_dashboard.py
- overlaps/schemas.py
- SETHU
- services
- redis
- migrate
- list_links
- audit_view/schemas.py
- Alerts.tsx
- test_cases.py
- test_tls_modes_verify_the_relay_certificate
- dashboard/schemas.py
- SingleScheduler
- Runbook
- 7. Production
- sqlalchemy
- conftest.py
- OverlapError

## God Nodes (most connected - your core abstractions)
1. `Principal` - 165 edges
2. `session_for()` - 156 edges
3. `get_settings()` - 54 edges
4. `useLoad()` - 48 edges
5. `record()` - 38 edges
6. `api()` - 31 edges
7. `verify()` - 26 edges
8. `get_principal()` - 26 edges
9. `detect()` - 26 edges
10. `x-backend-env` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Layout` --references--> `record()`  [INFERRED]
  CLAUDE.md → backend/app/audit/service.py
- `6. Audit ledger` --references--> `verify()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/audit/service.py
- `Tamper demonstration` --references--> `verify()`  [INFERRED]
  docs/RUNBOOK.md → backend/app/audit/service.py
- `3. Trust boundaries and how each is defended` --references--> `session_for()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/db/session.py
- `Non-negotiable rules` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py

## Import Cycles
- None detected.

## Communities (141 total, 27 thin omitted)

### Community 0 - "environment"
Cohesion: 0.28
Nodes (19): environment, SETHU_ALERT_FROM, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_INTAKE_SPOOL_DIR, SETHU_KEYCLOAK_EVENTS_SECRET, SETHU_KEYCLOAK_EVENTS_SECRET_FILE (+11 more)

### Community 1 - "load"
Cohesion: 0.15
Nodes (5): body_hash(), fingerprint(), insert(), load(), ProductionRefused

### Community 2 - "complaints/repo.py"
Cohesion: 0.05
Nodes (58): _all(), assigned_to(), bureaus(), case_counts(), deadline_days(), deadlines(), exists(), find() (+50 more)

### Community 3 - "with"
Cohesion: 0.05
Nodes (55): runs-on, services, steps, needs, runs-on, steps, timeout-minutes, concurrency (+47 more)

### Community 4 - "institutions/repo.py"
Cohesion: 0.08
Nodes (29): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+21 more)

### Community 5 - "test_findings.py"
Cohesion: 0.17
Nodes (17): cell(), detected(), findings_as(), hop(), test_a_second_run_adds_nothing(), test_a_spike_that_comes_back_is_reopened_with_its_new_counts(), test_an_acknowledgement_or_any_action_breaks_the_loop(), test_dismiss_reopen_and_resolve_are_audited_and_limited() (+9 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.09
Nodes (20): alert_row(), audit_count(), closed_port(), deliver(), FakeSMTP, held(), kinds(), make_due() (+12 more)

### Community 7 - "backend"
Cohesion: 0.14
Nodes (16): build, cap_drop, depends_on, networks, read_only, restart, secrets, security_opt (+8 more)

### Community 8 - "intake/api.py"
Cohesion: 0.26
Nodes (13): create_source(), issue_key(), items(), manual(), retry(), reviewed(), _run(), sources() (+5 more)

### Community 9 - "Principal"
Cohesion: 0.16
Nodes (19): Principal, _count(), linked(), _refs(), test_a_bureau_can_only_hand_a_case_over_as_itself(), test_a_bureau_cannot_read_links_or_alerts_it_is_not_party_to(), test_auditor_cannot_modify_complaints(), test_findings_are_read_by_the_bureaus_involved_and_written_by_the_detector() (+11 more)

### Community 10 - "institutions/schemas.py"
Cohesion: 0.17
Nodes (17): Alias, BureauCount, Candidate, CaseSummary, CategoryShare, Disposal, Dna, Institution (+9 more)

### Community 11 - "package.json"
Cohesion: 0.09
Nodes (24): @playwright/test, @types/cytoscape, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, ROLES (+16 more)

### Community 12 - "options"
Cohesion: 0.11
Nodes (25): logging, logging, driver, options, cap_drop, image, logging, networks (+17 more)

### Community 13 - "App"
Cohesion: 0.14
Nodes (32): useLoad(), App(), ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters (+24 more)

### Community 14 - "institutions/types.ts"
Cohesion: 0.10
Nodes (27): DnaPanel(), pct(), TREND, InstitutionList(), InstitutionProfile(), ResolutionQueue(), Candidate, CaseSummary (+19 more)

### Community 15 - "intake/repo.py"
Cohesion: 0.15
Nodes (19): _all(), claim_next(), failed(), finish(), forget_nonces(), health(), insert_item(), insert_source() (+11 more)

### Community 16 - "test_audit_view.py"
Cohesion: 0.09
Nodes (13): list_entries(), signins(), verify(), actions(), entries(), entry(), entries(), verify() (+5 more)

### Community 17 - "graph/repo.py"
Cohesion: 0.10
Nodes (10): graph(), _all(), bureaus(), complaints(), holdings(), open_findings(), overlaps(), transfers() (+2 more)

### Community 18 - "intake/schemas.py"
Cohesion: 0.16
Nodes (12): Accepted, Complainant, ComplaintIn, IssuedKey, Item, RowError, Source, SourceIn (+4 more)

### Community 19 - "postgres"
Cohesion: 0.11
Nodes (18): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+10 more)

### Community 20 - "config.py"
Cohesion: 0.14
Nodes (7): run_migrations_online(), _url(), production_problems(), read_secret(), Settings, _weak(), with_password()

### Community 21 - "overlaps/repo.py"
Cohesion: 0.17
Nodes (13): main(), _all(), candidates(), decide(), insert_alert(), linked_case_ids(), links(), _one() (+5 more)

### Community 22 - "web"
Cohesion: 0.12
Nodes (16): condition, depends_on, backend, keycloak, condition, web, build, cap_drop (+8 more)

### Community 23 - "bureaus/service.py"
Cohesion: 0.10
Nodes (17): create_bureau(), list_bureaus(), _run(), update_bureau(), _all(), by_code(), get(), insert() (+9 more)

### Community 24 - "demo-users"
Cohesion: 0.13
Nodes (15): cap_drop, entrypoint, environment, image, networks, profiles, read_only, restart (+7 more)

### Community 25 - "3. Database"
Cohesion: 0.12
Nodes (17): 3. Database, Alert mail (dev and demo), Browser tests, Case workflow, Complainant details: keys, Complaint intake, Continuous integration, Demo logins (dev and demo only) (+9 more)

### Community 26 - "Architecture"
Cohesion: 0.17
Nodes (11): 10. Scaling path (after the hackathon), 11. What has been verified, 1. Shape, 2. Components, 3. Trust boundaries and how each is defended, 4. Request flow (example: approve an overlap link), 5. Processing pipeline (worker), 6. Audit ledger (+3 more)

### Community 27 - "x-backend-env"
Cohesion: 0.09
Nodes (22): x-backend-env, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_COMPLAINANT_KEYS_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_INTAKE_SPOOL_DIR (+14 more)

### Community 28 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 29 - "environment"
Cohesion: 0.15
Nodes (13): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_BOOTSTRAP_ADMIN_USERNAME, KC_DB, KC_DB_PASSWORD, KC_DB_URL, KC_DB_USERNAME, KC_HEALTH_ENABLED, KC_HOSTNAME (+5 more)

### Community 30 - "crypto.py"
Cohesion: 0.14
Nodes (13): key_id_of(), Keyring, KeyringError, load_keyring(), parse_keyring(), _split(), client(), ring() (+5 more)

### Community 31 - "test_findings.py"
Cohesion: 0.19
Nodes (11): normalize(), scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_normalize_expands_abbreviations(), test_officer_picks_from_the_queue() (+3 more)

### Community 32 - "redis"
Cohesion: 0.17
Nodes (12): REDIS_PASSWORD, cap_add, cap_drop, command, environment, image, networks, read_only (+4 more)

### Community 33 - "keycloak"
Cohesion: 0.15
Nodes (13): postgres, cap_drop, command, depends_on, deploy, image, networks, restart (+5 more)

### Community 34 - "environment"
Cohesion: 0.15
Nodes (13): KEYCLOAK_DB_PASSWORD, KEYCLOAK_DB_PASSWORD_FILE, POSTGRES_PASSWORD, POSTGRES_PASSWORD_FILE, SETHU_APP_PASSWORD, SETHU_APP_PASSWORD_FILE, SETHU_AUDITOR_PASSWORD, SETHU_AUDITOR_PASSWORD_FILE (+5 more)

### Community 35 - "metrics.py"
Cohesion: 0.33
Nodes (5): _label(), observe_request(), _process_lines(), record_run(), render()

### Community 36 - "x-prod-backend-env"
Cohesion: 0.05
Nodes (42): file, file, file, file, file, file, file, secrets (+34 more)

### Community 37 - "01. Scope Lock"
Cohesion: 0.17
Nodes (11): 01. Scope Lock, Constraints, Definition of done (per feature), Freeze rules, Goal in one sentence, Out of scope (do not discuss again), Parking lot, Sign-off (+3 more)

### Community 38 - "02. PS Coverage Checklist (SIH26264)"
Cohesion: 0.17
Nodes (11): 02. PS Coverage Checklist (SIH26264), 1. Institution profile, 2. Case tracking, 3. Overlap detection, 4. Real-time dashboard, 5. Action history, 6. Search and filters, 7. Alerts (+3 more)

### Community 39 - "AuditLog.tsx"
Cohesion: 0.21
Nodes (10): AuditLog(), ChainReport, EMPTY, Entry, EntryPage, moment(), SignIn, SignIns() (+2 more)

### Community 40 - "test_search.py"
Cohesion: 0.27
Nodes (6): find(), hits(), test_bureau_a_never_sees_bureau_b_text_through_search(), test_cases_by_reference_and_metadata_across_bureaus(), test_institutions_by_name_alias_initials_and_city(), test_own_bureau_text_is_searched()

### Community 41 - "overlaps/service.py"
Cohesion: 0.18
Nodes (10): _can_decide(), _cases(), decide(), linked_case_ids(), links(), _shape(), tier1(), approved() (+2 more)

### Community 42 - "export"
Cohesion: 0.18
Nodes (7): _check(), export(), report(), _cell(), export(), run(), test_never_in_search_lists_reports_exports_audit_or_logs()

### Community 43 - "record"
Cohesion: 0.18
Nodes (17): record(), sources(), _by_name(), create_source(), _enqueue(), IntakeError, issue_key(), key_hash() (+9 more)

### Community 44 - "api.ts"
Cohesion: 0.11
Nodes (26): answer(), download(), upload(), CAN_AUDIT, CAN_DECIDE, CAN_INTAKE, CAN_RESOLVE, HAS_CASES (+18 more)

### Community 45 - "healthcheck"
Cohesion: 0.47
Nodes (11): interval, retries, start_period, test, timeout, healthcheck, healthcheck, healthcheck (+3 more)

### Community 46 - "complaints/api.py"
Cohesion: 0.08
Nodes (26): blank_to_none(), act(), assignees(), case(), deadlines(), institution_timeline(), list_cases(), my_cases() (+18 more)

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

### Community 57 - "create"
Cohesion: 0.17
Nodes (8): Held, safe_reason(), Assets, Before any real deployment, Compliance notes (to confirm with the AICTE mentor), Rules for contributors, Security, Threats and controls

### Community 58 - "api"
Cohesion: 0.10
Nodes (30): api(), AdminPage(), changed(), create(), BureauLine(), save(), BureauRow, Deadline (+22 more)

### Community 59 - "05. Next Claude Code Prompts"
Cohesion: 0.33
Nodes (5): 05. Next Claude Code Prompts, After that, in this order, Prompt 1: bring the stack up, Prompt 2: mock data, Prompt 3: first feature (institutions and resolution)

### Community 60 - "findings/schemas.py"
Cohesion: 0.39
Nodes (5): DecisionIn, DetectOut, Finding, Trend, TrendRow

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
Cohesion: 0.21
Nodes (6): _all(), bureaus(), _in_range(), institutions(), overlaps(), test_no_complaint_text_or_complainant_details_in_logs_audit_or_errors()

### Community 74 - "test_scheduler.py"
Cohesion: 0.24
Nodes (5): scheduler(), start(), test_a_scheduler_that_lost_its_lock_stops(), test_a_second_scheduler_refuses_to_start(), test_the_lock_passes_on_when_the_scheduler_stops_or_dies()

### Community 78 - "get_principal"
Cohesion: 0.18
Nodes (10): AuthError, decode_token(), _jwks_client(), principal_from_claims(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins(), test_me_and_role_gate() (+2 more)

### Community 79 - "environment"
Cohesion: 0.23
Nodes (24): environment, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_COMPLAINANT_KEYS_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_INTAKE_SPOOL_DIR (+16 more)

### Community 80 - "dashboard/repo.py"
Cohesion: 0.20
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 81 - "react"
Cohesion: 0.17
Nodes (19): cytoscape, react, react-dom, dependencies, cytoscape@3.30.4, react@^18.3.1, react-dom@^18.3.1, GraphPage() (+11 more)

### Community 82 - "datetime"
Cohesion: 0.09
Nodes (16): Alert, AlertPage, DecisionIn, Bureau, BureauRow, Edge, Filters, Graph (+8 more)

### Community 83 - "detect"
Cohesion: 0.06
Nodes (34): decide(), detect(), list_findings(), trend(), _all(), bureau_codes(), bureau_queues(), category_cells() (+26 more)

### Community 84 - "test_graph.py"
Cohesion: 0.31
Nodes (6): kinds(), test_aggregated_by_default_with_counts_and_multi_bureau_clusters(), test_each_role_sees_only_its_share_of_links_and_transfers_and_never_text(), test_expanding_an_institution_adds_its_complaints_and_overlap_edges(), test_filters_narrow_the_graph(), test_five_thousand_more_complaints_stay_aggregated_and_fast()

### Community 86 - "worker"
Cohesion: 0.10
Nodes (20): deploy, deploy, resources, memory, deploy, limits, deploy, worker (+12 more)

### Community 87 - "secrets"
Cohesion: 0.25
Nodes (6): ensure_added_keys(), ensure_keyring(), main(), main(), rotate(), _write()

### Community 88 - "detect"
Cohesion: 0.22
Nodes (6): detect(), embed_pending(), _embedder(), semantic_on(), detect_overlaps(), test_overlap_filters()

### Community 89 - "test_config.py"
Cohesion: 0.18
Nodes (11): refused(), settings(), _shell(), test_a_complete_production_configuration_starts(), test_all_problems_are_reported_at_once(), test_an_unreadable_secret_file_is_named_not_shown(), test_dev_and_test_keep_working_with_dev_values(), test_each_unsafe_value_is_refused_by_name() (+3 more)

### Community 90 - "Findings.tsx"
Cohesion: 0.31
Nodes (9): day(), Finding, FindingsPage(), KIND, numbers(), pct(), spikeWindow(), Target() (+1 more)

### Community 91 - "worker.py"
Cohesion: 0.09
Nodes (15): get_settings(), accept_request_id(), configure_logging(), JsonFormatter, get_engine(), create_app(), request_context(), _json_logs() (+7 more)

### Community 92 - "scheduler"
Cohesion: 0.20
Nodes (10): build, cap_drop, command, networks, read_only, restart, secrets, security_opt (+2 more)

### Community 93 - "Production readiness"
Cohesion: 0.50
Nodes (3): Gaps, Phases (proposed), Production readiness

### Community 94 - "session_for"
Cohesion: 0.10
Nodes (14): apply_context(), session_for(), net(), sql(), intake(), scalar(), test_who_sees_and_does_what_on_the_intake_screens(), detect() (+6 more)

### Community 95 - "sys"
Cohesion: 0.19
Nodes (7): main(), _new_key(), _write(), hashes(), main(), pins(), write()

### Community 96 - "search"
Cohesion: 0.33
Nodes (3): search(), search(), test_a_bureau_code_matches_exactly_in_search()

### Community 98 - "Seed data"
Cohesion: 0.33
Nodes (5): Files, Negative cases: no alert expected, Seed data, Seeded patterns and the expected detection, What the loader does

### Community 99 - "environment"
Cohesion: 0.18
Nodes (11): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_DB_PASSWORD, KC_HOSTNAME, KC_HOSTNAME_ADMIN, SETHU_PUBLIC_BASE_URL, command, entrypoint, environment (+3 more)

### Community 100 - "backup.sh"
Cohesion: 0.36
Nodes (10): backup_once(), counts(), GNUPGHOME, log(), PGHOST, PGUSER, prune(), record_run() (+2 more)

### Community 101 - "users/repo.py"
Cohesion: 0.09
Nodes (14): live(), me(), metrics(), ready(), list_people(), _all(), find(), heads() (+6 more)

### Community 103 - "SETHU_ENVIRONMENT"
Cohesion: 0.50
Nodes (4): environment, profiles, SETHU_ENVIRONMENT, demo-users

### Community 105 - "test_filters.py"
Cohesion: 0.19
Nodes (10): get(), test_audit_filters_narrow_combine_and_ignore_blanks(), test_each_case_filter_narrows_and_blank_is_no_filter(), total(), test_institution_list_filters(), test_institution_search_by_city_state_initials_typo_and_permanent_id(), test_institutions_screen_and_top_bar_search_agree(), test_report_dates_blank_and_reversed() (+2 more)

### Community 107 - "pathlib"
Cohesion: 0.13
Nodes (7): _connect(), fetch(), main(), sha256(), check_pem(), main(), nginx()

### Community 108 - "flow"
Cohesion: 0.50
Nodes (4): flow(), act(), as_(), sql()

### Community 109 - "test_overlaps.py"
Cohesion: 0.23
Nodes (12): detected(), scalar(), suggested_pairs(), test_api_decisions_detection_and_the_overlapping_filter(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs(), test_negative_cases_are_never_flagged() (+4 more)

### Community 111 - "web"
Cohesion: 0.25
Nodes (8): condition, backend, keycloak, condition, web, depends_on, ports, volumes

### Community 112 - "test_directory.py"
Cohesion: 0.22
Nodes (11): audit_rows(), client(), row(), test_a_deactivated_bureau_takes_no_transfers(), test_a_token_without_email_keeps_the_stored_address(), test_admin_creates_and_deactivates_a_bureau_and_both_are_audited(), test_first_sign_in_creates_the_record_with_email_and_a_bureau_change_reaches_it(), test_people_without_email_are_flagged_for_the_admin() (+3 more)

### Community 113 - "add"
Cohesion: 0.70
Nodes (5): add(), act(), assign(), close(), transfer()

### Community 114 - "verify"
Cohesion: 0.24
Nodes (10): ChainStatus, verify(), _append(), test_actor_comes_from_the_session_not_the_caller(), test_chain_is_valid_and_sequential(), test_client_cannot_choose_seq_or_hash(), test_deleted_row_is_detected(), test_runtime_role_cannot_rewrite_history() (+2 more)

### Community 115 - "test_intake.py"
Cohesion: 0.08
Nodes (10): get_principal(), client(), test_newest_first_with_filters(), test_only_auditor_oversight_and_admin_read_the_ledger(), test_verify_names_a_corrupted_row_and_restoring_it_heals_the_chain(), make_due(), test_a_failing_attempt_is_retried_then_dead_lettered_and_an_admin_can_retry_it(), test_the_intake_api_has_a_per_source_quota() (+2 more)

### Community 116 - "build"
Cohesion: 0.22
Nodes (6): test_files_are_what_the_generator_produces(), build(), details(), fresh(), two_wordings(), variant()

### Community 117 - "alerts/repo.py"
Cohesion: 0.05
Nodes (27): decide(), list_alerts(), retry(), _all(), claim_next(), decide(), delivered_to(), known_addresses() (+19 more)

### Community 119 - "test_dashboard.py"
Cohesion: 0.29
Nodes (8): board(), counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data(), test_cross_bureau_numbers_are_the_same_for_everyone(), test_every_role_gets_the_dashboard()

### Community 120 - "overlaps/schemas.py"
Cohesion: 0.36
Nodes (6): DecisionIn, DetectOut, Link, LinkedCase, Tier1Case, Tier1Institution

### Community 123 - "SETHU"
Cohesion: 0.22
Nodes (8): Commands, graphify, Layout, Non-negotiable rules, Read first, SETHU, Stack, Working agreements

### Community 124 - "services"
Cohesion: 0.20
Nodes (10): secrets, ports, profiles, secrets, services, backend, mailpit, scheduler (+2 more)

### Community 128 - "redis"
Cohesion: 0.20
Nodes (10): healthcheck, REDIS_PASSWORD, interval, start_period, test, command, environment, healthcheck (+2 more)

### Community 129 - "migrate"
Cohesion: 0.33
Nodes (6): MIGRATION_DATABASE_PASSWORD_FILE, MIGRATION_DATABASE_URL, environment, restart, secrets, migrate

### Community 130 - "list_links"
Cohesion: 0.19
Nodes (4): decide(), detect(), list_links(), tier1()

### Community 131 - "audit_view/schemas.py"
Cohesion: 0.36
Nodes (4): ChainReport, Entry, EntryPage, SignIn

### Community 133 - "Alerts.tsx"
Cohesion: 0.32
Nodes (7): Alert, AlertCard(), decide(), AlertPage, AlertsPage(), moment(), STATUS

### Community 134 - "test_cases.py"
Cohesion: 0.21
Nodes (8): CaseError, audit_rows(), scalar(), test_every_action_is_audited_and_the_chain_verifies(), test_list_filters_search_and_institution_timeline(), test_loop_case_c090_shows_both_unacknowledged_transfers(), test_officer_cannot_read_or_change_another_bureaus_complaint(), test_transfer_and_acknowledgement_appear_in_the_history()

### Community 139 - "dashboard/schemas.py"
Cohesion: 0.36
Nodes (6): Attention, Count, OverdueCase, Overview, Totals, Week

### Community 142 - "Runbook"
Cohesion: 0.18
Nodes (10): 1. First start, 2. Daily use, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, Restore, Restore drill (2026-11-20, throwaway production-mode stack), Runbook (+2 more)

### Community 143 - "7. Production"
Cohesion: 0.25
Nodes (8): 7. Production, Configuration reference, Keycloak administration (SSH tunnel), Published ports, Secrets, Start, The production realm, TLS certificate

### Community 146 - "sqlalchemy"
Cohesion: 0.12
Nodes (12): parse_rows(), spool(), client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_export_is_csv_without_text_and_is_audited(), test_institution_report_counts_only_the_callers_cases() (+4 more)

### Community 147 - "conftest.py"
Cohesion: 0.31
Nodes (5): app_engine(), clean_db(), owner_engine(), world(), person()

## Knowledge Gaps
- **4 isolated node(s):** `sethu-backend`, `PGHOST`, `PGUSER`, `GNUPGHOME`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 955 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `complaints/repo.py`, `list_links`, `institutions/repo.py`, `test_alerts.py`, `intake/api.py`, `test_audit_view.py`, `graph/repo.py`, `conftest.py`, `bureaus/service.py`, `test_findings.py`, `overlaps/service.py`, `export`, `record`, `complaints/api.py`, `session.py`, `intake/service.py`, `reports/service.py`, `get_principal`, `detect`, `test_graph.py`, `detect`, `worker.py`, `session_for`, `users/repo.py`, `flow`, `test_overlaps.py`, `test_directory.py`, `verify`, `test_intake.py`, `alerts/repo.py`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 101 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 101 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sethu-backend`, `PGHOST`, `PGUSER` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `complaints/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05241228070175439 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `load`, `test_findings.py`, `test_alerts.py`, `test_cases.py`, `intake/api.py`, `Principal`, `intake/repo.py`, `sqlalchemy`, `conftest.py`, `overlaps/repo.py`, `Architecture`, `crypto.py`, `test_findings.py`, `test_search.py`, `overlaps/service.py`, `export`, `test_seed.py`, `session.py`, `intake/service.py`, `detect`, `test_graph.py`, `detect`, `worker.py`, `search`, `users/repo.py`, `test_filters.py`, `flow`, `test_overlaps.py`, `test_directory.py`, `verify`, `test_intake.py`, `alerts/repo.py`, `overlaps/__init__.py`, `test_dashboard.py`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `with` be split into smaller, more focused modules?**
  _Cohesion score 0.05194805194805195 - nodes in this community are weakly interconnected._