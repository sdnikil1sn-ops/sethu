# Graph Report - jolly-feynman-1a9f96  (2026-11-21)

## Corpus Check
- 173 files · ~94,621 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 21 file(s) not represented in the graph (top: (none) 8, .csv 7, .conf 2)

## Summary
- 2093 nodes · 4654 edges · 158 communities (105 shown, 53 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 80 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `138d1244`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- environment
- load.py
- complaints/repo.py
- audit/service.py
- institutions/repo.py
- test_findings.py
- test_alerts.py
- backend
- intake/api.py
- verify
- BaseModel
- package.json
- options
- App.tsx
- useLoad
- intake/repo.py
- sqlalchemy
- Principal
- test_overlaps.py
- postgres
- test_config.py
- overlaps/repo.py
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
- intake/service.py
- overlaps/service.py
- test_intake.py
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
- update_bureau
- worker
- secrets
- worker.py
- x-prod-backend-env
- Findings.tsx
- test_search.py
- scheduler
- Production readiness
- pytest
- environment
- backup.sh
- users/repo.py
- complaints/service.py
- test_filters.py
- Overlaps.tsx
- pathlib
- web
- alerts/service.py
- overlaps/schemas.py
- SETHU
- services
- redis
- migrate
- list_links
- datetime
- findings/schemas.py
- Alerts.tsx
- test_cases.py
- audit_view/schemas.py
- search/schemas.py
- complainant_key.py
- SingleScheduler
- Seed data
- test_tls_modes_verify_the_relay_certificate
- build
- flow
- findings/service.py
- conftest.py
- OverlapError
- FakeSMTP
- SMTPSession

## God Nodes (most connected - your core abstractions)
1. `Principal` - 154 edges
2. `session_for()` - 138 edges
3. `useLoad()` - 44 edges
4. `get_settings()` - 38 edges
5. `record()` - 38 edges
6. `api()` - 31 edges
7. `verify()` - 26 edges
8. `detect()` - 24 edges
9. `get_principal()` - 23 edges
10. `App()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Tables` --references--> `due_at()`  [INFERRED]
  docs/DATA-MODEL.md → backend/app/modules/complaints/service.py
- `Compliance notes (to confirm with the AICTE mentor)` --references--> `due_at()`  [INFERRED]
  docs/SECURITY.md → backend/app/modules/complaints/service.py
- `What the loader does` --references--> `due_at()`  [INFERRED]
  seed/README.md → backend/app/modules/complaints/service.py
- `3. Trust boundaries and how each is defended` --references--> `session_for()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/db/session.py
- `6. Audit ledger` --references--> `verify()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/audit/service.py

## Import Cycles
- None detected.

## Communities (158 total, 53 thin omitted)

### Community 0 - "environment"
Cohesion: 0.29
Nodes (18): environment, SETHU_ALERT_FROM, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_INTAKE_SPOOL_DIR, SETHU_OIDC_ISSUER (+10 more)

### Community 1 - "load.py"
Cohesion: 0.10
Nodes (9): parse_rows(), test_export_is_csv_without_text_and_is_audited(), test_keycloak_demo_logins_match_the_seed(), render(), insert(), load(), ProductionRefused, rows() (+1 more)

### Community 2 - "complaints/repo.py"
Cohesion: 0.12
Nodes (26): _all(), assigned_to(), bureaus(), case_counts(), deadline_days(), deadlines(), exists(), find() (+18 more)

### Community 3 - "audit/service.py"
Cohesion: 0.13
Nodes (3): live(), me(), ready()

### Community 4 - "institutions/repo.py"
Cohesion: 0.07
Nodes (31): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+23 more)

### Community 5 - "test_findings.py"
Cohesion: 0.18
Nodes (17): cell(), detected(), findings_as(), hop(), test_a_second_run_adds_nothing(), test_a_spike_that_comes_back_is_reopened_with_its_new_counts(), test_an_acknowledgement_or_any_action_breaks_the_loop(), test_dismiss_reopen_and_resolve_are_audited_and_limited() (+9 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.15
Nodes (16): alert_row(), audit_count(), closed_port(), deliver(), kinds(), make_due(), test_a_bureau_sees_only_alerts_it_is_party_to(), test_a_failed_send_stays_approved_and_is_retried_without_duplicates() (+8 more)

### Community 7 - "backend"
Cohesion: 0.11
Nodes (18): build, cap_drop, deploy, networks, read_only, restart, secrets, security_opt (+10 more)

### Community 8 - "intake/api.py"
Cohesion: 0.26
Nodes (13): list_alerts(), create_source(), issue_key(), items(), manual(), retry(), reviewed(), _run() (+5 more)

### Community 9 - "verify"
Cohesion: 0.22
Nodes (10): ChainStatus, verify(), _append(), test_actor_comes_from_the_session_not_the_caller(), test_chain_is_valid_and_sequential(), test_client_cannot_choose_seq_or_hash(), test_deleted_row_is_detected(), test_runtime_role_cannot_rewrite_history() (+2 more)

### Community 10 - "BaseModel"
Cohesion: 0.08
Nodes (30): Alert, AlertPage, DecisionIn, Alias, BureauCount, Candidate, CaseSummary, CategoryShare (+22 more)

### Community 11 - "package.json"
Cohesion: 0.10
Nodes (23): react-dom, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, dependencies, react@^18.3.1 (+15 more)

### Community 12 - "options"
Cohesion: 0.11
Nodes (25): logging, logging, driver, options, cap_drop, image, logging, networks (+17 more)

### Community 13 - "App.tsx"
Cohesion: 0.17
Nodes (24): useLoad(), App(), CAN_AUDIT, CAN_DECIDE, CAN_INTAKE, CAN_RESOLVE, HAS_CASES, Me (+16 more)

### Community 14 - "useLoad"
Cohesion: 0.13
Nodes (23): Finding, DnaPanel(), pct(), TREND, CENTRE, curve(), Link, place() (+15 more)

### Community 15 - "intake/repo.py"
Cohesion: 0.18
Nodes (16): _all(), claim_next(), failed(), finish(), forget_nonces(), health(), insert_item(), insert_source() (+8 more)

### Community 16 - "sqlalchemy"
Cohesion: 0.06
Nodes (19): list_entries(), verify(), actions(), entries(), entry(), entries(), verify(), overview() (+11 more)

### Community 17 - "Principal"
Cohesion: 0.12
Nodes (25): Principal, apply_context(), get_engine(), session_for(), intake(), scalar(), _count(), linked() (+17 more)

### Community 18 - "test_overlaps.py"
Cohesion: 0.23
Nodes (12): detected(), scalar(), suggested_pairs(), test_api_decisions_detection_and_the_overlapping_filter(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs(), test_negative_cases_are_never_flagged() (+4 more)

### Community 19 - "postgres"
Cohesion: 0.11
Nodes (18): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+10 more)

### Community 20 - "test_config.py"
Cohesion: 0.10
Nodes (18): run_migrations_online(), _url(), production_problems(), read_secret(), Settings, _weak(), with_password(), refused() (+10 more)

### Community 21 - "overlaps/repo.py"
Cohesion: 0.23
Nodes (9): _all(), decide(), insert_alert(), linked_case_ids(), links(), _one(), refs(), suggest_tier2() (+1 more)

### Community 22 - "web"
Cohesion: 0.12
Nodes (16): condition, depends_on, backend, keycloak, condition, web, build, cap_drop (+8 more)

### Community 23 - "bureaus/service.py"
Cohesion: 0.16
Nodes (11): _all(), by_code(), get(), insert(), listing(), update(), BureauError, by_code() (+3 more)

### Community 24 - "demo-users"
Cohesion: 0.13
Nodes (15): cap_drop, entrypoint, environment, image, networks, profiles, read_only, restart (+7 more)

### Community 25 - "3. Database"
Cohesion: 0.06
Nodes (30): 1. First start, 2. Daily use, 3. Database, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, 7. Production, Alert mail (dev and demo) (+22 more)

### Community 26 - "Architecture"
Cohesion: 0.17
Nodes (11): 10. Scaling path (after the hackathon), 11. What has been verified, 1. Shape, 2. Components, 3. Trust boundaries and how each is defended, 4. Request flow (example: approve an overlap link), 5. Processing pipeline (worker), 6. Audit ledger (+3 more)

### Community 27 - "x-backend-env"
Cohesion: 0.10
Nodes (21): x-backend-env, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_COMPLAINANT_KEYS_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_INTAKE_SPOOL_DIR (+13 more)

### Community 28 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 29 - "environment"
Cohesion: 0.17
Nodes (12): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_BOOTSTRAP_ADMIN_USERNAME, KC_DB, KC_DB_PASSWORD, KC_DB_URL, KC_DB_USERNAME, KC_HEALTH_ENABLED, KC_HOSTNAME (+4 more)

### Community 30 - "test_complainant.py"
Cohesion: 0.13
Nodes (15): key_id_of(), Keyring, KeyringError, load_keyring(), parse_keyring(), _split(), keyring(), rotate_complainant_keys() (+7 more)

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
Nodes (36): decide(), detect(), list_findings(), trend(), _all(), bureau_codes(), bureau_queues(), category_cells() (+28 more)

### Community 36 - "x-prod-backend-env"
Cohesion: 0.10
Nodes (21): file, file, file, file, file, file, secrets, backup_key (+13 more)

### Community 37 - "01. Scope Lock"
Cohesion: 0.17
Nodes (11): 01. Scope Lock, Constraints, Definition of done (per feature), Freeze rules, Goal in one sentence, Out of scope (do not discuss again), Parking lot, Sign-off (+3 more)

### Community 38 - "02. PS Coverage Checklist (SIH26264)"
Cohesion: 0.17
Nodes (11): 02. PS Coverage Checklist (SIH26264), 1. Institution profile, 2. Case tracking, 3. Overlap detection, 4. Real-time dashboard, 5. Action history, 6. Search and filters, 7. Alerts (+3 more)

### Community 39 - "AuditLog.tsx"
Cohesion: 0.24
Nodes (8): AuditLog(), ChainReport, EMPTY, Entry, EntryPage, moment(), target(), Verify()

### Community 40 - "intake/service.py"
Cohesion: 0.13
Nodes (15): get_settings(), ComplaintIn, body_hash(), _create(), _enqueue(), fingerprint(), Held, key_hash() (+7 more)

### Community 41 - "overlaps/service.py"
Cohesion: 0.18
Nodes (10): _can_decide(), _cases(), decide(), linked_case_ids(), links(), _shape(), tier1(), approved() (+2 more)

### Community 42 - "test_intake.py"
Cohesion: 0.06
Nodes (19): create_app(), _check(), export(), report(), _all(), bureaus(), _in_range(), institutions() (+11 more)

### Community 43 - "record"
Cohesion: 0.22
Nodes (14): record(), sources(), _by_name(), create_source(), IntakeError, issue_key(), list_items(), list_sources() (+6 more)

### Community 44 - "api.ts"
Cohesion: 0.16
Nodes (18): answer(), download(), upload(), accessToken(), base64url(), login(), logout(), redirectUri() (+10 more)

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

### Community 56 - "Data Model"
Cohesion: 0.29
Nodes (6): Adding a table, Data Model, Database roles, Planned additions, Request context and policies, Tables

### Community 57 - "Security"
Cohesion: 0.29
Nodes (6): Assets, Before any real deployment, Compliance notes (to confirm with the AICTE mentor), Rules for contributors, Security, Threats and controls

### Community 58 - "api"
Cohesion: 0.10
Nodes (30): api(), AdminPage(), changed(), create(), BureauLine(), save(), BureauRow, Deadline (+22 more)

### Community 59 - "05. Next Claude Code Prompts"
Cohesion: 0.33
Nodes (5): 05. Next Claude Code Prompts, After that, in this order, Prompt 1: bring the stack up, Prompt 2: mock data, Prompt 3: first feature (institutions and resolution)

### Community 60 - "test_reports.py"
Cohesion: 0.22
Nodes (7): client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_institution_report_counts_only_the_callers_cases(), test_overlap_outcomes(), test_viewing_is_not_audited_and_bad_names_are_refused()

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

### Community 74 - "test_scheduler.py"
Cohesion: 0.19
Nodes (6): held(), scheduler(), start(), test_a_scheduler_that_lost_its_lock_stops(), test_a_second_scheduler_refuses_to_start(), test_the_lock_passes_on_when_the_scheduler_stops_or_dies()

### Community 78 - "get_principal"
Cohesion: 0.16
Nodes (10): AuthError, decode_token(), _jwks_client(), principal_from_claims(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins(), test_me_and_role_gate() (+2 more)

### Community 79 - "environment"
Cohesion: 0.24
Nodes (23): environment, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_COMPLAINANT_KEYS_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_INTAKE_SPOOL_DIR (+15 more)

### Community 81 - "cases/types.ts"
Cohesion: 0.18
Nodes (16): react, ACTIONS, EMPTY, Filters, History(), InstitutionTimeline(), unacknowledged(), Action (+8 more)

### Community 83 - "update_bureau"
Cohesion: 0.16
Nodes (6): decide(), retry(), create_bureau(), list_bureaus(), _run(), update_bureau()

### Community 86 - "worker"
Cohesion: 0.18
Nodes (11): worker, build, cap_drop, command, networks, read_only, restart, secrets (+3 more)

### Community 87 - "secrets"
Cohesion: 0.29
Nodes (5): ensure_keyring(), main(), main(), rotate(), _write()

### Community 88 - "worker.py"
Cohesion: 0.11
Nodes (8): deliver_alerts(), detect_findings(), detect_overlaps(), process_intake(), resolve_pending(), rotate_complainant_keys(), take_spool(), verify_chain()

### Community 89 - "x-prod-backend-env"
Cohesion: 0.11
Nodes (17): x-prod-backend-env, SETHU_ALERT_FROM, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_INTAKE_SPOOL_DIR, SETHU_OIDC_ISSUER (+9 more)

### Community 90 - "Findings.tsx"
Cohesion: 0.36
Nodes (8): day(), FindingsPage(), KIND, numbers(), pct(), spikeWindow(), Target(), Trend

### Community 91 - "test_search.py"
Cohesion: 0.17
Nodes (8): search(), test_a_bureau_code_matches_exactly_in_search(), find(), hits(), test_bureau_a_never_sees_bureau_b_text_through_search(), test_cases_by_reference_and_metadata_across_bureaus(), test_institutions_by_name_alias_initials_and_city(), test_own_bureau_text_is_searched()

### Community 92 - "scheduler"
Cohesion: 0.13
Nodes (17): depends_on, migrate, redis, condition, condition, build, cap_drop, command (+9 more)

### Community 93 - "Production readiness"
Cohesion: 0.50
Nodes (3): Gaps, Phases (proposed), Production readiness

### Community 95 - "pytest"
Cohesion: 0.26
Nodes (10): audit_rows(), client(), row(), test_a_deactivated_bureau_takes_no_transfers(), test_a_token_without_email_keeps_the_stored_address(), test_admin_creates_and_deactivates_a_bureau_and_both_are_audited(), test_first_sign_in_creates_the_record_with_email_and_a_bureau_change_reaches_it(), test_people_without_email_are_flagged_for_the_admin() (+2 more)

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
Cohesion: 0.10
Nodes (23): act(), actor_id(), assignees(), can_act(), complainant_visible(), create(), deadline_days(), deadlines() (+15 more)

### Community 105 - "test_filters.py"
Cohesion: 0.14
Nodes (13): detect(), board(), get(), test_audit_filters_narrow_combine_and_ignore_blanks(), test_each_case_filter_narrows_and_blank_is_no_filter(), total(), test_institution_list_filters(), test_institution_search_by_city_state_initials_typo_and_permanent_id() (+5 more)

### Community 106 - "Overlaps.tsx"
Cohesion: 0.21
Nodes (10): BANNER, day(), Link, LinkCard(), decide(), LinkedCase, Links(), OverlapsPage() (+2 more)

### Community 107 - "pathlib"
Cohesion: 0.24
Nodes (3): check_pem(), main(), nginx()

### Community 111 - "web"
Cohesion: 0.25
Nodes (8): condition, backend, keycloak, condition, web, depends_on, ports, volumes

### Community 117 - "alerts/service.py"
Cohesion: 0.09
Nodes (17): _all(), claim_next(), decide(), delivered_to(), known_addresses(), listing(), mark(), retry() (+9 more)

### Community 120 - "overlaps/schemas.py"
Cohesion: 0.36
Nodes (6): DecisionIn, DetectOut, Link, LinkedCase, Tier1Case, Tier1Institution

### Community 123 - "SETHU"
Cohesion: 0.22
Nodes (8): Commands, graphify, Layout, Non-negotiable rules, Read first, SETHU, Stack, Working agreements

### Community 124 - "services"
Cohesion: 0.15
Nodes (13): secrets, environment, profiles, ports, profiles, secrets, services, backend (+5 more)

### Community 128 - "redis"
Cohesion: 0.20
Nodes (10): healthcheck, REDIS_PASSWORD, interval, start_period, test, command, environment, healthcheck (+2 more)

### Community 129 - "migrate"
Cohesion: 0.33
Nodes (6): MIGRATION_DATABASE_PASSWORD_FILE, MIGRATION_DATABASE_URL, environment, restart, secrets, migrate

### Community 130 - "list_links"
Cohesion: 0.19
Nodes (4): decide(), detect(), list_links(), tier1()

### Community 131 - "datetime"
Cohesion: 0.12
Nodes (13): Bureau, BureauChange, BureauIn, BureauRow, Attention, Count, OverdueCase, Overview (+5 more)

### Community 132 - "findings/schemas.py"
Cohesion: 0.39
Nodes (5): DecisionIn, DetectOut, Finding, Trend, TrendRow

### Community 133 - "Alerts.tsx"
Cohesion: 0.32
Nodes (7): Alert, AlertCard(), decide(), AlertPage, AlertsPage(), moment(), STATUS

### Community 134 - "test_cases.py"
Cohesion: 0.18
Nodes (8): CaseError, audit_rows(), scalar(), test_every_action_is_audited_and_the_chain_verifies(), test_list_filters_search_and_institution_timeline(), test_loop_case_c090_shows_both_unacknowledged_transfers(), test_officer_cannot_read_or_change_another_bureaus_complaint(), test_transfer_and_acknowledgement_appear_in_the_history()

### Community 135 - "audit_view/schemas.py"
Cohesion: 0.47
Nodes (3): ChainReport, Entry, EntryPage

### Community 139 - "search/schemas.py"
Cohesion: 0.43
Nodes (4): ComplaintHit, ComplaintHits, InstitutionHit, Results

### Community 140 - "complainant_key.py"
Cohesion: 0.47
Nodes (3): main(), _new_key(), _write()

### Community 142 - "Seed data"
Cohesion: 0.33
Nodes (5): Files, Negative cases: no alert expected, Seed data, Seeded patterns and the expected detection, What the loader does

### Community 144 - "build"
Cohesion: 0.23
Nodes (10): test_files_are_what_the_generator_produces(), build(), add(), act(), assign(), close(), transfer(), details() (+2 more)

### Community 145 - "flow"
Cohesion: 0.50
Nodes (4): flow(), act(), as_(), sql()

### Community 146 - "findings/service.py"
Cohesion: 0.11
Nodes (5): get_principal(), deadline_findings(), transfer_finding(), test_a_missed_deadline_is_escalated_once_to_the_holding_bureau_head_and_resolved_on_closing(), test_notes_are_read_only_by_the_bureau_holding_the_case()

### Community 147 - "conftest.py"
Cohesion: 0.25
Nodes (5): app_engine(), clean_db(), owner_engine(), world(), person()

## Knowledge Gaps
- **4 isolated node(s):** `GNUPGHOME`, `PGHOST`, `PGUSER`, `sethu-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 862 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **53 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `list_links`, `audit/service.py`, `institutions/repo.py`, `test_alerts.py`, `intake/api.py`, `verify`, `sqlalchemy`, `flow`, `findings/service.py`, `conftest.py`, `test_overlaps.py`, `bureaus/service.py`, `test_complainant.py`, `test_findings.py`, `findings/service.py`, `intake/service.py`, `overlaps/service.py`, `test_intake.py`, `record`, `complaints/api.py`, `session.py`, `get_principal`, `update_bureau`, `pytest`, `users/repo.py`, `complaints/service.py`, `test_filters.py`, `alerts/service.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GNUPGHOME`, `PGHOST`, `PGUSER` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `load.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10461538461538461 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `Principal` to `load.py`, `audit/service.py`, `test_findings.py`, `test_alerts.py`, `test_cases.py`, `intake/api.py`, `verify`, `flow`, `test_overlaps.py`, `conftest.py`, `findings/service.py`, `Architecture`, `test_complainant.py`, `test_findings.py`, `findings/service.py`, `intake/service.py`, `overlaps/service.py`, `test_intake.py`, `test_seed.py`, `session.py`, `test_reports.py`, `test_scheduler.py`, `worker.py`, `test_search.py`, `pytest`, `test_filters.py`, `alerts/service.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `complaints/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11738648947951273 - nodes in this community are weakly interconnected._