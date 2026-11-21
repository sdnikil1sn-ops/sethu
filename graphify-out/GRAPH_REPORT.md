# Graph Report - jolly-feynman-1a9f96  (2026-11-21)

## Corpus Check
- 206 files · ~118,254 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 25 file(s) not represented in the graph (top: (none) 8, .csv 7, .lock 3)

## Summary
- 2473 nodes · 5571 edges · 162 communities (121 shown, 41 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 158 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e766d423`
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
- metrics
- x-prod-backend-env
- 01. Scope Lock
- 02. PS Coverage Checklist (SIH26264)
- AuditLog.tsx
- complaints/service.py
- x-prod-backend-env
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
- Dashboard.tsx
- session.py
- 03. Demo Story: "Institution A"
- 04. Mock Data Spec
- test_intake.py
- intake/service.py
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
- findings/service.py
- worker
- secrets
- get_settings
- test_config.py
- Findings.tsx
- logging.py
- scheduler
- Production readiness
- session_for
- time
- task
- json
- environment
- backup.sh
- users/repo.py
- Data Model
- list_findings
- test_filters.py
- install_cert.py
- signins.py
- decide
- web
- Findings
- dashboard/schemas.py
- verify
- flow
- build
- alerts/repo.py
- jobs.py
- test_dashboard.py
- overlaps/schemas.py
- search/schemas.py
- SETHU
- services
- redis
- migrate
- audit_view/schemas.py
- App.tsx
- json
- complainant_key.py
- Security
- list_links
- list_people
- Load test, failure drills and the offline run
- SingleScheduler
- Runbook
- 7. Production
- offline.sh
- Seed data
- test_reports.py
- conftest.py
- volume.py
- test_tls_modes_verify_the_relay_certificate
- linked
- pair
- test_missed_deadlines_make_one_digest_per_bureau_per_run_and_only_for_new_ones
- open_count
- queue_findings

## God Nodes (most connected - your core abstractions)
1. `session_for()` - 173 edges
2. `Principal` - 167 edges
3. `get_settings()` - 72 edges
4. `useLoad()` - 49 edges
5. `record()` - 45 edges
6. `api()` - 31 edges
7. `verify()` - 28 edges
8. `get_principal()` - 27 edges
9. `detect()` - 26 edges
10. `x-backend-env` - 23 edges

## Surprising Connections (you probably didn't know these)
- `Threats and controls` --references--> `safe_reason()`  [INFERRED]
  docs/SECURITY.md → backend/app/modules/intake/service.py
- `Non-negotiable rules` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py
- `Layout` --references--> `record()`  [INFERRED]
  CLAUDE.md → backend/app/audit/service.py
- `Working agreements` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py
- `3. Trust boundaries and how each is defended` --references--> `session_for()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/db/session.py

## Import Cycles
- None detected.

## Communities (162 total, 41 thin omitted)

### Community 0 - "environment"
Cohesion: 0.24
Nodes (22): environment, environment, SETHU_ALERT_FROM, SETHU_AUDIT_ANCHOR_DIR, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT (+14 more)

### Community 1 - "load"
Cohesion: 0.12
Nodes (6): test_keycloak_demo_logins_match_the_seed(), insert(), load(), ProductionRefused, rows(), user_id()

### Community 2 - "complaints/repo.py"
Cohesion: 0.12
Nodes (26): _all(), assigned_to(), bureaus(), case_counts(), deadline_days(), deadlines(), exists(), find() (+18 more)

### Community 3 - "with"
Cohesion: 0.05
Nodes (55): runs-on, services, steps, needs, runs-on, steps, timeout-minutes, concurrency (+47 more)

### Community 4 - "institutions/repo.py"
Cohesion: 0.07
Nodes (31): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+23 more)

### Community 5 - "test_findings.py"
Cohesion: 0.17
Nodes (17): cell(), findings_as(), hop(), test_a_second_run_adds_nothing(), test_a_spike_that_comes_back_is_reopened_with_its_new_counts(), test_an_acknowledgement_or_any_action_breaks_the_loop(), test_dismiss_reopen_and_resolve_are_audited_and_limited(), test_findings_are_scoped_to_the_bureaus_involved() (+9 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.14
Nodes (17): alert_row(), audit_count(), closed_port(), deliver(), kinds(), make_due(), SMTPSession, test_a_bureau_sees_only_alerts_it_is_party_to() (+9 more)

### Community 7 - "backend"
Cohesion: 0.11
Nodes (19): build, cap_drop, deploy, networks, read_only, restart, secrets, security_opt (+11 more)

### Community 8 - "intake/api.py"
Cohesion: 0.20
Nodes (14): create_source(), issue_key(), items(), manual(), retry(), reviewed(), _run(), sources() (+6 more)

### Community 9 - "Principal"
Cohesion: 0.15
Nodes (24): Principal, test_a_deactivated_bureau_takes_no_transfers(), test_the_database_lets_a_person_write_only_their_own_row_with_their_token_role(), test_the_database_refuses_bureau_writes_from_anyone_but_admin(), test_each_role_sees_only_its_share_of_links_and_transfers_and_never_text(), as_(), test_a_full_request_cycle_logs_json_with_ids_and_nothing_sensitive(), _count() (+16 more)

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
Cohesion: 0.16
Nodes (24): ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters, History(), InstitutionTimeline() (+16 more)

### Community 14 - "institutions/types.ts"
Cohesion: 0.11
Nodes (26): DnaPanel(), pct(), TREND, InstitutionList(), InstitutionProfile(), ResolutionQueue(), Candidate, CaseSummary (+18 more)

### Community 15 - "intake/repo.py"
Cohesion: 0.15
Nodes (19): _all(), claim_next(), failed(), finish(), forget_nonces(), health(), insert_item(), insert_source() (+11 more)

### Community 16 - "sqlalchemy"
Cohesion: 0.13
Nodes (8): anchor_check(), list_entries(), verify(), actions(), entries(), entry(), entries(), verify()

### Community 17 - "graph/repo.py"
Cohesion: 0.10
Nodes (10): graph(), _all(), bureaus(), complaints(), holdings(), open_findings(), overlaps(), transfers() (+2 more)

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
Cohesion: 0.06
Nodes (32): main(), _all(), candidates(), decide(), insert_alert(), linked_case_ids(), links(), _one() (+24 more)

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
Cohesion: 0.16
Nodes (14): key_id_of(), Keyring, KeyringError, load_keyring(), parse_keyring(), _split(), set_complainant(), keyring() (+6 more)

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

### Community 35 - "metrics"
Cohesion: 0.22
Nodes (4): live(), me(), metrics(), ready()

### Community 36 - "x-prod-backend-env"
Cohesion: 0.09
Nodes (23): file, file, file, file, file, file, file, secrets (+15 more)

### Community 37 - "01. Scope Lock"
Cohesion: 0.17
Nodes (11): 01. Scope Lock, Constraints, Definition of done (per feature), Freeze rules, Goal in one sentence, Out of scope (do not discuss again), Parking lot, Sign-off (+3 more)

### Community 38 - "02. PS Coverage Checklist (SIH26264)"
Cohesion: 0.17
Nodes (11): 02. PS Coverage Checklist (SIH26264), 1. Institution profile, 2. Case tracking, 3. Overlap detection, 4. Real-time dashboard, 5. Action history, 6. Search and filters, 7. Alerts (+3 more)

### Community 39 - "AuditLog.tsx"
Cohesion: 0.19
Nodes (13): useLoad(), AnchorReport, Anchors(), AuditLog(), ChainReport, EMPTY, Entry, EntryPage (+5 more)

### Community 40 - "complaints/service.py"
Cohesion: 0.09
Nodes (23): act(), actor_id(), assignees(), can_act(), CaseError, complainant_visible(), create(), deadline_days() (+15 more)

### Community 41 - "x-prod-backend-env"
Cohesion: 0.11
Nodes (19): x-prod-backend-env, SETHU_ALERT_FROM, SETHU_AUDIT_ANCHOR_DIR, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_INTAKE_SPOOL_DIR (+11 more)

### Community 42 - "test_search.py"
Cohesion: 0.07
Nodes (18): _check(), export(), report(), _cell(), export(), run(), search(), search() (+10 more)

### Community 43 - "record"
Cohesion: 0.20
Nodes (16): record(), sources(), _by_name(), create_source(), _enqueue(), IntakeError, issue_key(), list_sources() (+8 more)

### Community 44 - "api.ts"
Cohesion: 0.15
Nodes (19): react-dom, answer(), download(), upload(), accessToken(), base64url(), login(), logout() (+11 more)

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
Cohesion: 0.11
Nodes (22): scalar(), suggested_pairs(), test_a_second_overlap_run_is_skipped_while_one_is_running(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs(), test_negative_cases_are_never_flagged(), test_suggestions_are_written_in_bounded_batches() (+14 more)

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

### Community 56 - "test_intake.py"
Cohesion: 0.16
Nodes (4): make_due(), test_a_failing_attempt_is_retried_then_dead_lettered_and_an_admin_can_retry_it(), test_the_intake_api_has_a_per_source_quota(), test_while_the_primary_is_down_its_items_wait_and_the_fallback_spool_takes_over()

### Community 57 - "intake/service.py"
Cohesion: 0.09
Nodes (16): ComplaintIn, body_hash(), _create(), fingerprint(), Held, key_hash(), list_items(), parse_rows() (+8 more)

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
Cohesion: 0.19
Nodes (6): _all(), bureaus(), _in_range(), institutions(), overlaps(), test_no_complaint_text_or_complainant_details_in_logs_audit_or_errors()

### Community 74 - "test_scheduler.py"
Cohesion: 0.24
Nodes (5): scheduler(), start(), test_a_scheduler_that_lost_its_lock_stops(), test_a_second_scheduler_refuses_to_start(), test_the_lock_passes_on_when_the_scheduler_stops_or_dies()

### Community 78 - "get_principal"
Cohesion: 0.18
Nodes (10): AuthError, decode_token(), _jwks_client(), principal_from_claims(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins(), test_me_and_role_gate() (+2 more)

### Community 79 - "environment"
Cohesion: 0.22
Nodes (25): environment, SETHU_AUDIT_ANCHOR_DIR, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_COMPLAINANT_KEYS_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT (+17 more)

### Community 80 - "dashboard/repo.py"
Cohesion: 0.20
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 81 - "react"
Cohesion: 0.18
Nodes (19): cytoscape, react, dependencies, cytoscape@3.30.4, react@^18.3.1, react-dom@^18.3.1, ComplaintDetail(), GraphPage() (+11 more)

### Community 82 - "datetime"
Cohesion: 0.10
Nodes (14): Alert, AlertPage, DecisionIn, Bureau, BureauRow, Edge, Filters, Graph (+6 more)

### Community 83 - "detect"
Cohesion: 0.16
Nodes (15): _all(), bureau_codes(), bureau_queues(), category_cells(), existing(), insert(), insert_alert(), institution_queues() (+7 more)

### Community 84 - "findings/service.py"
Cohesion: 0.12
Nodes (8): deadline_findings(), transfer_finding(), kinds(), test_aggregated_by_default_with_counts_and_multi_bureau_clusters(), test_expanding_an_institution_adds_its_complaints_and_overlap_edges(), test_filters_narrow_the_graph(), test_five_thousand_more_complaints_stay_aggregated_and_fast(), test_notes_are_read_only_by_the_bureau_holding_the_case()

### Community 86 - "worker"
Cohesion: 0.18
Nodes (11): worker, build, cap_drop, command, networks, read_only, restart, secrets (+3 more)

### Community 87 - "secrets"
Cohesion: 0.25
Nodes (6): ensure_added_keys(), ensure_keyring(), main(), main(), rotate(), _write()

### Community 88 - "get_settings"
Cohesion: 0.06
Nodes (14): get_principal(), get_settings(), production_problems(), _weak(), signins(), _embedder(), semantic_on(), export_anchor() (+6 more)

### Community 89 - "test_config.py"
Cohesion: 0.16
Nodes (12): Settings, refused(), settings(), _shell(), test_a_complete_production_configuration_starts(), test_all_problems_are_reported_at_once(), test_an_unreadable_secret_file_is_named_not_shown(), test_dev_and_test_keep_working_with_dev_values() (+4 more)

### Community 90 - "Findings.tsx"
Cohesion: 0.31
Nodes (9): day(), Finding, FindingsPage(), KIND, numbers(), pct(), spikeWindow(), Target() (+1 more)

### Community 91 - "logging.py"
Cohesion: 0.08
Nodes (15): accept_request_id(), configure_logging(), JsonFormatter, _label(), observe_request(), _process_lines(), record_run(), render() (+7 more)

### Community 92 - "scheduler"
Cohesion: 0.13
Nodes (17): depends_on, migrate, redis, condition, condition, build, cap_drop, command (+9 more)

### Community 93 - "Production readiness"
Cohesion: 0.50
Nodes (3): Gaps, Phases (proposed), Production readiness

### Community 94 - "session_for"
Cohesion: 0.08
Nodes (22): apply_context(), get_engine(), session_for(), test_loop_case_c090_shows_both_unacknowledged_transfers(), audit_rows(), client(), row(), test_a_token_without_email_keeps_the_stored_address() (+14 more)

### Community 95 - "time"
Cohesion: 0.43
Nodes (3): fetch(), main(), sha256()

### Community 96 - "task"
Cohesion: 0.11
Nodes (9): deliver_alerts(), detect_findings(), detect_overlaps(), _only_run(), process_intake(), resolve_pending(), rotate_complainant_keys(), take_spool() (+1 more)

### Community 98 - "json"
Cohesion: 0.21
Nodes (9): compare(), export(), _file(), main(), anchored(), check(), test_a_rewritten_entry_or_a_replaced_database_is_reported(), test_export_appends_and_the_live_chain_matches() (+1 more)

### Community 99 - "environment"
Cohesion: 0.18
Nodes (11): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_DB_PASSWORD, KC_HOSTNAME, KC_HOSTNAME_ADMIN, SETHU_PUBLIC_BASE_URL, command, entrypoint, environment (+3 more)

### Community 100 - "backup.sh"
Cohesion: 0.36
Nodes (10): backup_once(), counts(), GNUPGHOME, log(), PGHOST, PGUSER, prune(), record_run() (+2 more)

### Community 101 - "users/repo.py"
Cohesion: 0.29
Nodes (6): _all(), find(), heads(), insert(), listing(), update()

### Community 103 - "Data Model"
Cohesion: 0.29
Nodes (6): Adding a table, Data Model, Database roles, Planned additions, Request context and policies, Tables

### Community 104 - "list_findings"
Cohesion: 0.14
Nodes (7): decide(), detect(), list_findings(), trend(), listing(), listing(), trend()

### Community 105 - "test_filters.py"
Cohesion: 0.08
Nodes (22): detect(), links(), approved(), FakeSMTP, held(), relay(), board(), test_an_alert_names_the_bureau_it_cannot_reach() (+14 more)

### Community 107 - "install_cert.py"
Cohesion: 0.31
Nodes (3): check_pem(), main(), nginx()

### Community 108 - "signins.py"
Cohesion: 0.29
Nodes (5): _call(), fetch(), _realm_url(), shape(), Unavailable

### Community 109 - "decide"
Cohesion: 0.20
Nodes (6): _alert(), decide(), _digest(), FindingError, _set(), recipients()

### Community 111 - "web"
Cohesion: 0.25
Nodes (8): condition, backend, keycloak, condition, web, depends_on, ports, volumes

### Community 112 - "Findings"
Cohesion: 0.15
Nodes (11): test_a02_001_the_api_description_is_not_under_the_proxied_path(), Areas checked with no finding, Findings, Method, OWASP-A02-001 The API description was served through the edge in dev (CWE-200, Exposure of Sensitive Information to an Unauthorized Actor), OWASP-A02-002 `/health/ready` reachable from outside (CWE-200), OWASP-A02-003 CSP allows inline styles (CWE-1021 family; style injection only), OWASP-A02-004 Dev realm is looser than production (+3 more)

### Community 113 - "dashboard/schemas.py"
Cohesion: 0.36
Nodes (6): Attention, Count, OverdueCase, Overview, Totals, Week

### Community 114 - "verify"
Cohesion: 0.16
Nodes (15): ChainStatus, verify(), _append(), test_actor_comes_from_the_session_not_the_caller(), test_chain_is_valid_and_sequential(), test_client_cannot_choose_seq_or_hash(), test_deleted_row_is_detected(), test_runtime_role_cannot_rewrite_history() (+7 more)

### Community 115 - "flow"
Cohesion: 0.50
Nodes (4): flow(), act(), as_(), sql()

### Community 116 - "build"
Cohesion: 0.15
Nodes (11): test_files_are_what_the_generator_produces(), build(), add(), act(), assign(), close(), transfer(), details() (+3 more)

### Community 117 - "alerts/repo.py"
Cohesion: 0.06
Nodes (21): decide(), list_alerts(), retry(), _all(), claim_next(), decide(), delivered_to(), known_addresses() (+13 more)

### Community 118 - "jobs.py"
Cohesion: 0.43
Nodes (3): _client(), queue(), status()

### Community 119 - "test_dashboard.py"
Cohesion: 0.39
Nodes (6): counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data(), test_every_role_gets_the_dashboard()

### Community 120 - "overlaps/schemas.py"
Cohesion: 0.31
Nodes (8): DecisionIn, DetectOut, DetectQueued, DetectStatus, Link, LinkedCase, Tier1Case, Tier1Institution

### Community 121 - "search/schemas.py"
Cohesion: 0.43
Nodes (4): ComplaintHit, ComplaintHits, InstitutionHit, Results

### Community 123 - "SETHU"
Cohesion: 0.22
Nodes (8): Commands, graphify, Layout, Non-negotiable rules, Read first, SETHU, Stack, Working agreements

### Community 124 - "services"
Cohesion: 0.14
Nodes (13): secrets, profiles, ports, profiles, secrets, services, backend, demo-users (+5 more)

### Community 128 - "redis"
Cohesion: 0.20
Nodes (10): healthcheck, REDIS_PASSWORD, interval, start_period, test, command, environment, healthcheck (+2 more)

### Community 129 - "migrate"
Cohesion: 0.33
Nodes (6): MIGRATION_DATABASE_PASSWORD_FILE, MIGRATION_DATABASE_URL, environment, restart, secrets, migrate

### Community 131 - "audit_view/schemas.py"
Cohesion: 0.31
Nodes (6): AnchorLatest, AnchorReport, ChainReport, Entry, EntryPage, SignIn

### Community 133 - "App.tsx"
Cohesion: 0.11
Nodes (22): App(), CAN_AUDIT, CAN_DECIDE, CAN_INTAKE, CAN_RESOLVE, HAS_CASES, Me, SEES_WORKLOAD (+14 more)

### Community 134 - "json"
Cohesion: 0.15
Nodes (9): test_list_filters_search_and_institution_timeline(), test_cross_bureau_numbers_are_the_same_for_everyone(), main(), submit(), main(), hashes(), main(), pins() (+1 more)

### Community 135 - "complainant_key.py"
Cohesion: 0.43
Nodes (3): main(), _new_key(), _write()

### Community 136 - "Security"
Cohesion: 0.29
Nodes (6): Assets, Before any real deployment, Compliance notes (to confirm with the AICTE mentor), Rules for contributors, Security, Threats and controls

### Community 140 - "Load test, failure drills and the offline run"
Cohesion: 0.33
Nodes (5): Drills, How to run it, Load test, failure drills and the offline run, Measured before the host gave out (not capacity figures), Status (2026-11-21): incomplete

### Community 142 - "Runbook"
Cohesion: 0.18
Nodes (10): 1. First start, 2. Daily use, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, Restore, Restore drill (2026-11-20, throwaway production-mode stack), Runbook (+2 more)

### Community 143 - "7. Production"
Cohesion: 0.25
Nodes (8): 7. Production, Configuration reference, Keycloak administration (SSH tunnel), Published ports, Secrets, Start, The production realm, TLS certificate

### Community 144 - "offline.sh"
Cohesion: 0.40
Nodes (3): MSYS_NO_PATHCONV, offline.sh script, vm()

### Community 145 - "Seed data"
Cohesion: 0.33
Nodes (5): Files, Negative cases: no alert expected, Seed data, Seeded patterns and the expected detection, What the loader does

### Community 146 - "test_reports.py"
Cohesion: 0.18
Nodes (9): client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_export_is_csv_without_text_and_is_audited(), test_institution_report_counts_only_the_callers_cases(), test_overlap_outcomes(), test_viewing_is_not_audited_and_bad_names_are_refused() (+1 more)

### Community 147 - "conftest.py"
Cohesion: 0.12
Nodes (12): app_engine(), clean_db(), owner_engine(), world(), person(), client(), test_newest_first_with_filters(), test_only_auditor_oversight_and_admin_read_the_ledger() (+4 more)

## Knowledge Gaps
- **5 isolated node(s):** `MSYS_NO_PATHCONV`, `GNUPGHOME`, `PGHOST`, `PGUSER`, `sethu-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1022 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **41 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `institutions/repo.py`, `test_alerts.py`, `json`, `intake/api.py`, `list_links`, `list_people`, `sqlalchemy`, `graph/repo.py`, `conftest.py`, `overlaps/repo.py`, `bureaus/service.py`, `crypto.py`, `test_findings.py`, `metrics`, `complaints/service.py`, `test_search.py`, `record`, `complaints/api.py`, `test_seed.py`, `session.py`, `test_intake.py`, `intake/service.py`, `reports/service.py`, `get_principal`, `datetime`, `detect`, `findings/service.py`, `get_settings`, `session_for`, `list_findings`, `test_filters.py`, `decide`, `verify`, `flow`, `alerts/repo.py`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MSYS_NO_PATHCONV`, `GNUPGHOME`, `PGHOST` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `load` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `load`, `test_findings.py`, `test_alerts.py`, `json`, `intake/api.py`, `Principal`, `intake/repo.py`, `test_reports.py`, `conftest.py`, `volume.py`, `overlaps/repo.py`, `linked`, `pair`, `test_missed_deadlines_make_one_digest_per_bureau_per_run_and_only_for_new_ones`, `crypto.py`, `test_findings.py`, `metrics`, `test_search.py`, `test_seed.py`, `session.py`, `test_intake.py`, `intake/service.py`, `findings/service.py`, `get_settings`, `logging.py`, `task`, `json`, `test_filters.py`, `verify`, `flow`, `alerts/repo.py`, `test_dashboard.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 78 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 78 INFERRED edges - model-reasoned connections that need verification._
- **Should `complaints/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11627906976744186 - nodes in this community are weakly interconnected._