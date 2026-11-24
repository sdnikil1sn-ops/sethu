# Graph Report - jolly-feynman-1a9f96  (2026-11-24)

## Corpus Check
- 265 files · ~154,088 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 28 file(s) not represented in the graph (top: (none) 9, .csv 8, .lock 4)

## Summary
- 3116 nodes · 7380 edges · 198 communities (157 shown, 41 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 236 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dff74b54`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- environment
- test_overlaps.py
- complaints/repo.py
- run
- institutions/repo.py
- findings_as
- test_alerts.py
- backend
- intake/api.py
- session_for
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
- config.py
- overlaps/repo.py
- web
- bureaus/service.py
- registry.py
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
- translate.py
- x-prod-backend-env
- 01. Scope Lock
- test_cases.py
- AuditLog.tsx
- complaints/service.py
- test_enrichment.py
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
- _create
- session.py
- 03. Demo Story: "Institution A"
- 04. Mock Data Spec
- enrichment/repo.py
- test_glossary.py
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
- overlaps/schemas.py
- test_scheduler.py
- sethu-backend
- test_auth_and_api.py
- environment
- dashboard/repo.py
- react
- datetime
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
- intake
- Architecture
- task
- json
- environment
- backup.sh
- users/repo.py
- Data Model
- list_findings
- metrics.py
- test_ai_models.py
- Operations guide
- decide
- web
- parse_rows
- dashboard/schemas.py
- verify
- flow
- build
- alerts/repo.py
- get_settings
- ocr.py
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
- App.tsx
- as_
- json
- Security
- list_links
- Intake API: send one complaint
- Load test, failure drills and the offline run
- SingleScheduler
- 7. Production
- load.py
- offline.sh
- Result
- test_reports.py
- conftest.py
- deliver
- safe_reason
- test_ai_router.py
- pair
- lid.py
- Report
- signins.py
- resolve
- open_attachment
- ai-worker
- catalog.py
- run
- glossary/repo.py
- glossary/service.py
- ci.yml
- jobs
- Findings.tsx
- Provider
- metrics
- with
- networks
- migrate
- Phase A2: enrichment (language, OCR, translation, glossary)
- ai_health/schemas.py
- search
- glossary/schemas.py
- backend-tests
- run_task
- glossary
- test_tls_modes_verify_the_relay_certificate
- Seed data
- Vendored: IndicTrans2 inference helpers
- browser-tests
- egress-canary
- env
- client
- manifest.json
- models/README.md

## God Nodes (most connected - your core abstractions)
1. `session_for()` - 207 edges
2. `Principal` - 188 edges
3. `get_settings()` - 99 edges
4. `useLoad()` - 55 edges
5. `record()` - 49 edges
6. `api()` - 34 edges
7. `get_principal()` - 31 edges
8. `verify()` - 30 edges
9. `detect()` - 27 edges
10. `environment` - 26 edges

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

## Communities (198 total, 41 thin omitted)

### Community 0 - "environment"
Cohesion: 0.26
Nodes (24): environment, environment, HF_HUB_OFFLINE, SETHU_AI_MODELS_DIR, SETHU_ALERT_FROM, SETHU_AUDIT_ANCHOR_DIR, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL (+16 more)

### Community 1 - "test_overlaps.py"
Cohesion: 0.20
Nodes (15): detected(), scalar(), suggested_pairs(), test_a_second_overlap_run_is_skipped_while_one_is_running(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs(), test_negative_cases_are_never_flagged() (+7 more)

### Community 2 - "complaints/repo.py"
Cohesion: 0.12
Nodes (25): _all(), assigned_to(), bureaus(), case_counts(), deadline_days(), deadlines(), exists(), find() (+17 more)

### Community 3 - "run"
Cohesion: 0.37
Nodes (13): steps, steps, steps, steps, steps, steps, steps, if (+5 more)

### Community 4 - "institutions/repo.py"
Cohesion: 0.07
Nodes (31): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+23 more)

### Community 5 - "findings_as"
Cohesion: 0.21
Nodes (13): cell(), findings_as(), test_a_second_run_adds_nothing(), test_dismiss_reopen_and_resolve_are_audited_and_limited(), test_findings_are_scoped_to_the_bureaus_involved(), test_loop_detection_finds_c090_and_queues_an_alert_for_approval(), test_seed_gives_few_bottlenecks_listed_after_transfer_findings(), test_seeded_spike_is_found_once_with_its_counts_and_no_alert() (+5 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.10
Nodes (23): alert_row(), audit_count(), closed_port(), deliver(), FakeSMTP, held(), kinds(), make_due() (+15 more)

### Community 7 - "backend"
Cohesion: 0.18
Nodes (11): build, cap_drop, deploy, networks, read_only, restart, secrets, security_opt (+3 more)

### Community 8 - "intake/api.py"
Cohesion: 0.24
Nodes (13): create_source(), issue_key(), items(), manual(), retry(), reviewed(), _run(), sources() (+5 more)

### Community 9 - "session_for"
Cohesion: 0.09
Nodes (34): Principal, apply_context(), session_for(), test_a_deactivated_bureau_takes_no_transfers(), test_the_database_lets_a_person_write_only_their_own_row_with_their_token_role(), test_the_database_refuses_bureau_writes_from_anyone_but_admin(), detected(), net() (+26 more)

### Community 10 - "institutions/schemas.py"
Cohesion: 0.17
Nodes (17): Alias, BureauCount, Candidate, CaseSummary, CategoryShare, Disposal, Dna, Institution (+9 more)

### Community 11 - "package.json"
Cohesion: 0.07
Nodes (31): @axe-core/playwright, @playwright/test, @types/cytoscape, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react (+23 more)

### Community 12 - "options"
Cohesion: 0.18
Nodes (17): logging, logging, logging, driver, options, logging, max-file, max-size (+9 more)

### Community 13 - "App"
Cohesion: 0.12
Nodes (32): ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters, Attachments(), EnrichmentPanel() (+24 more)

### Community 14 - "institutions/types.ts"
Cohesion: 0.17
Nodes (18): DnaPanel(), pct(), TREND, RelationshipGraph(), InstitutionList(), InstitutionProfile(), ResolutionQueue(), Candidate (+10 more)

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
Cohesion: 0.16
Nodes (12): Accepted, Complainant, ComplaintIn, IssuedKey, Item, RowError, Source, SourceIn (+4 more)

### Community 19 - "postgres"
Cohesion: 0.11
Nodes (18): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+10 more)

### Community 20 - "config.py"
Cohesion: 0.14
Nodes (8): run_migrations_online(), _url(), production_problems(), read_secret(), remote_url(), Settings, _weak(), with_password()

### Community 21 - "overlaps/repo.py"
Cohesion: 0.05
Nodes (42): main(), _all(), candidates(), decide(), insert_alert(), linked_case_ids(), links(), links_page() (+34 more)

### Community 22 - "web"
Cohesion: 0.20
Nodes (10): web, build, cap_drop, networks, ports, read_only, restart, security_opt (+2 more)

### Community 23 - "bureaus/service.py"
Cohesion: 0.09
Nodes (19): create_bureau(), list_bureaus(), _run(), update_bureau(), _all(), by_code(), get(), insert() (+11 more)

### Community 24 - "registry.py"
Cohesion: 0.05
Nodes (24): ModelManager, TesseractOCR, check_all(), digest(), _file_sha256(), load_manifest(), ModelEntry, ModelIntegrityError (+16 more)

### Community 25 - "3. Database"
Cohesion: 0.10
Nodes (20): 3. Database, Alert mail (dev and demo), Audit-chain anchors, Browser tests, Case workflow, Complainant details: keys, Complaint intake, Continuous integration (+12 more)

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
Nodes (10): key_id_of(), Keyring, KeyringError, _split(), rotate_complainant_keys(), ring(), test_a_broken_keyring_is_refused_without_showing_a_key(), test_re_encryption_moves_every_value_to_the_new_key() (+2 more)

### Community 31 - "test_findings.py"
Cohesion: 0.28
Nodes (9): scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_officer_picks_from_the_queue(), test_profile_shows_every_bureau_without_complaint_text(), test_unknown_or_ambiguous_names_are_not_guessed() (+1 more)

### Community 32 - "redis"
Cohesion: 0.17
Nodes (12): REDIS_PASSWORD, cap_add, cap_drop, command, environment, image, networks, read_only (+4 more)

### Community 33 - "keycloak"
Cohesion: 0.15
Nodes (13): postgres, cap_drop, command, depends_on, deploy, image, networks, restart (+5 more)

### Community 34 - "environment"
Cohesion: 0.15
Nodes (13): KEYCLOAK_DB_PASSWORD, KEYCLOAK_DB_PASSWORD_FILE, POSTGRES_PASSWORD, POSTGRES_PASSWORD_FILE, SETHU_APP_PASSWORD, SETHU_APP_PASSWORD_FILE, SETHU_AUDITOR_PASSWORD, SETHU_AUDITOR_PASSWORD_FILE (+5 more)

### Community 35 - "translate.py"
Cohesion: 0.14
Nodes (9): detokenize(), preprocess(), to_devanagari(), tokenize(), punc_norm(), normalize(), normalize_indic_numerals(), wrap_with_placeholders() (+1 more)

### Community 36 - "x-prod-backend-env"
Cohesion: 0.05
Nodes (43): file, file, file, file, file, file, file, secrets (+35 more)

### Community 37 - "01. Scope Lock"
Cohesion: 0.17
Nodes (11): 01. Scope Lock, Constraints, Definition of done (per feature), Freeze rules, Goal in one sentence, Out of scope (do not discuss again), Parking lot, Sign-off (+3 more)

### Community 38 - "test_cases.py"
Cohesion: 0.20
Nodes (13): audit_rows(), scalar(), test_api_hides_text_and_enforces_roles(), test_every_action_is_audited_and_the_chain_verifies(), test_list_filters_search_and_institution_timeline(), test_loop_case_c090_shows_both_unacknowledged_transfers(), test_officer_cannot_read_or_change_another_bureaus_complaint(), test_transfer_and_acknowledgement_appear_in_the_history() (+5 more)

### Community 39 - "AuditLog.tsx"
Cohesion: 0.19
Nodes (13): useLoad(), AnchorReport, Anchors(), AuditLog(), ChainReport, EMPTY, Entry, EntryPage (+5 more)

### Community 40 - "complaints/service.py"
Cohesion: 0.12
Nodes (19): act(), actor_id(), assignees(), can_act(), CaseError, complainant_visible(), create(), deadline_days() (+11 more)

### Community 41 - "test_enrichment.py"
Cohesion: 0.23
Nodes (23): enrich_pending(), attach(), body_of(), enriched(), file_case(), _pdf_with_text(), reviews(), runs() (+15 more)

### Community 42 - "test_search.py"
Cohesion: 0.18
Nodes (10): search(), test_a_bureau_code_matches_exactly_in_search(), test_api_decisions_detection_and_the_overlapping_filter(), find(), hits(), test_bureau_a_never_sees_bureau_b_text_through_search(), test_cases_by_reference_and_metadata_across_bureaus(), test_institutions_by_name_alias_initials_and_city() (+2 more)

### Community 43 - "record"
Cohesion: 0.17
Nodes (21): record(), sources(), body_hash(), _by_name(), create_source(), _enqueue(), fingerprint(), IntakeError (+13 more)

### Community 44 - "api.ts"
Cohesion: 0.11
Nodes (25): react-dom, react-dom@^18.3.1, answer(), download(), upload(), accessToken(), base64url(), login() (+17 more)

### Community 45 - "healthcheck"
Cohesion: 0.47
Nodes (12): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+4 more)

### Community 46 - "complaints/api.py"
Cohesion: 0.06
Nodes (31): blank_to_none(), act(), assignees(), case(), deadlines(), institution_timeline(), list_cases(), my_cases() (+23 more)

### Community 47 - "services"
Cohesion: 0.11
Nodes (17): file, cap_drop, image, logging, networks, ports, profiles, restart (+9 more)

### Community 48 - "Architecture Decision Records"
Cohesion: 0.22
Nodes (8): 0001. Modular monolith, not microservices, 0002. Enforce access in the database with Row-Level Security, 0003. Hash-chained audit log inside PostgreSQL, not a blockchain, 0004. Transactional outbox for alerts, 0005. Local models only, each with a deterministic fallback, 0006. Object storage deferred, 0007. Keycloak for identity, Architecture Decision Records

### Community 49 - "Architecture Snapshot"
Cohesion: 0.22
Nodes (8): Architecture Pattern, Architecture Snapshot, Critical Modules, Dependency Rules, Entry Points, Extraction Quality, Repository Map, Routes

### Community 50 - "test_seed.py"
Cohesion: 0.14
Nodes (13): cross_bureau_pairs(), deadlocks(), duplicate_pairs(), not_closed(), silent(), spikes(), tagged(), test_expected_detections() (+5 more)

### Community 51 - "migrate"
Cohesion: 0.18
Nodes (11): MIGRATION_DATABASE_URL, build, cap_drop, command, deploy, environment, networks, read_only (+3 more)

### Community 52 - "_create"
Cohesion: 0.25
Nodes (5): similar_text(), keyring(), lock_text(), similar_text(), _create()

### Community 53 - "session.py"
Cohesion: 0.13
Nodes (3): require_roles(), page_params(), get_session()

### Community 54 - "03. Demo Story: "Institution A""
Cohesion: 0.25
Nodes (7): 03. Demo Story: "Institution A", Characters (fictional), Cut list if the demo runs long, Rehearsal checklist, Script, Seeded facts, The story in one line

### Community 55 - "04. Mock Data Spec"
Cohesion: 0.25
Nodes (7): 04. Mock Data Spec, Deliberate patterns to seed, Expected detections (used by tests), Files to generate, Fixed demo records (do not randomise), Negative cases (must NOT be flagged), Volume

### Community 56 - "enrichment/repo.py"
Cohesion: 0.19
Nodes (17): _all(), attachment(), attachments(), body(), can_read_case(), claim(), enrichment(), insert_attachment() (+9 more)

### Community 57 - "test_glossary.py"
Cohesion: 0.16
Nodes (12): Glossary, _latin(), Match, normalise(), client(), csv_bytes(), test_indic_terms_may_take_a_suffix_but_must_start_a_word(), test_longest_match_first_and_word_boundaries() (+4 more)

### Community 58 - "api"
Cohesion: 0.08
Nodes (35): api(), AdminPage(), changed(), create(), BureauLine(), save(), BureauRow, Deadline (+27 more)

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
Cohesion: 0.19
Nodes (8): _all(), bureaus(), _in_range(), institutions(), overlaps(), make_due(), test_a_failing_attempt_is_retried_then_dead_lettered_and_an_admin_can_retry_it(), test_while_the_primary_is_down_its_items_wait_and_the_fallback_spool_takes_over()

### Community 73 - "overlaps/schemas.py"
Cohesion: 0.13
Nodes (16): PageMeta, DecisionIn, DetectOut, Finding, FindingPage, Trend, TrendRow, DecisionIn (+8 more)

### Community 74 - "test_scheduler.py"
Cohesion: 0.21
Nodes (7): scheduler(), start(), test_a_scheduler_that_lost_its_lock_stops(), test_a_second_scheduler_refuses_to_start(), test_the_lock_passes_on_when_the_scheduler_stops_or_dies(), 2. Daily use, Scheduler

### Community 78 - "test_auth_and_api.py"
Cohesion: 0.18
Nodes (10): AuthError, decode_token(), _jwks_client(), principal_from_claims(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins(), test_me_and_role_gate() (+2 more)

### Community 79 - "environment"
Cohesion: 0.09
Nodes (50): environment, condition, environment, cap_drop, depends_on, entrypoint, environment, image (+42 more)

### Community 80 - "dashboard/repo.py"
Cohesion: 0.18
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 81 - "react"
Cohesion: 0.17
Nodes (19): cytoscape, react, dependencies, cytoscape@3.30.4, react@^18.3.1, ComplaintDetail(), EDGE_WORDS, GraphPage() (+11 more)

### Community 82 - "datetime"
Cohesion: 0.16
Nodes (8): Alert, AlertPage, DecisionIn, Edge, Filters, Graph, Node, Person

### Community 83 - "detect"
Cohesion: 0.14
Nodes (16): _all(), bureau_codes(), bureau_queues(), category_cells(), existing(), insert(), insert_alert(), institution_queues() (+8 more)

### Community 84 - "get_principal"
Cohesion: 0.06
Nodes (19): get_principal(), _embedder(), semantic_on(), counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data() (+11 more)

### Community 86 - "worker"
Cohesion: 0.18
Nodes (11): worker, build, cap_drop, command, networks, read_only, restart, secrets (+3 more)

### Community 87 - "secrets"
Cohesion: 0.25
Nodes (6): ensure_added_keys(), ensure_keyring(), main(), main(), rotate(), _write()

### Community 88 - "sqlalchemy"
Cohesion: 0.11
Nodes (6): hop(), test_a_spike_that_comes_back_is_reopened_with_its_new_counts(), test_an_acknowledgement_or_any_action_breaks_the_loop(), test_findings_are_written_in_bounded_batches(), test_loop_needs_two_unacknowledged_transfers_back_to_a_bureau(), test_stall_threshold()

### Community 89 - "test_config.py"
Cohesion: 0.07
Nodes (29): fetch(), main(), sha256(), refused(), settings(), _shell(), test_a_complete_production_configuration_starts(), test_ai_endpoints_inside_the_deployment_are_allowed() (+21 more)

### Community 90 - "Findings.tsx"
Cohesion: 0.11
Nodes (24): cases(), Count, CountTable(), Dashboard(), day(), OverdueCase, Overview, Trend() (+16 more)

### Community 91 - "logging.py"
Cohesion: 0.10
Nodes (10): JsonFormatter, get_engine(), _json_logs(), _task_finished(), _task_started(), as_(), lines(), test_a_full_request_cycle_logs_json_with_ids_and_nothing_sensitive() (+2 more)

### Community 92 - "scheduler"
Cohesion: 0.20
Nodes (10): build, cap_drop, command, networks, read_only, restart, secrets, security_opt (+2 more)

### Community 93 - "OPERATIONS.md"
Cohesion: 0.22
Nodes (5): API, Who calls what, Gaps, Phases (proposed), Production readiness

### Community 95 - "Architecture"
Cohesion: 0.09
Nodes (21): Adding a model, AI pipeline, Health, Memory, Not in A1 (some added in A2, below), Offline guarantees and how they are checked, Provenance, Registry (+13 more)

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
Cohesion: 0.14
Nodes (10): list_people(), _all(), find(), heads(), insert(), listing(), update(), listing() (+2 more)

### Community 103 - "Data Model"
Cohesion: 0.29
Nodes (6): Adding a table, Data Model, Database roles, Planned additions, Request context and policies, Tables

### Community 104 - "list_findings"
Cohesion: 0.22
Nodes (5): decide(), detect(), list_findings(), trend(), page()

### Community 105 - "metrics.py"
Cohesion: 0.11
Nodes (12): accept_request_id(), _label(), observe_request(), _process_lines(), record_run(), render(), create_app(), request_context() (+4 more)

### Community 107 - "test_ai_models.py"
Cohesion: 0.16
Nodes (12): FastTextLID, manager(), rss_mb(), test_fasttext_is_unhealthy_until_installed(), cer(), edit_distance(), peak_mb(), real_models() (+4 more)

### Community 108 - "Operations guide"
Cohesion: 0.15
Nodes (13): 10. Incident response, 11. Known limits, 1. What runs, 2. Install, 3. Configuration reference, 4. First-time setup (after the first start), 5. Upgrade, 6. Backup and restore, and the drill (+5 more)

### Community 109 - "decide"
Cohesion: 0.11
Nodes (12): set_status(), _alert(), deadline_findings(), decide(), _digest(), FindingError, open_count(), queue_findings() (+4 more)

### Community 111 - "web"
Cohesion: 0.25
Nodes (8): condition, backend, keycloak, condition, web, depends_on, ports, volumes

### Community 112 - "parse_rows"
Cohesion: 0.08
Nodes (20): parse_rows(), read_plain_file(), spool(), test_a01_001_a_link_in_the_spool_folder_is_refused_unread(), test_a01_001_an_unknown_header_is_not_echoed(), test_a02_001_the_api_description_is_not_under_the_proxied_path(), test_a06_001_a_spreadsheet_that_expands_too_far_is_refused_before_parsing(), Areas checked with no finding (+12 more)

### Community 113 - "dashboard/schemas.py"
Cohesion: 0.36
Nodes (6): Attention, Count, OverdueCase, Overview, Totals, Week

### Community 114 - "verify"
Cohesion: 0.21
Nodes (13): ChainStatus, verify(), _append(), test_actor_comes_from_the_session_not_the_caller(), test_chain_is_valid_and_sequential(), test_client_cannot_choose_seq_or_hash(), test_deleted_row_is_detected(), test_runtime_role_cannot_rewrite_history() (+5 more)

### Community 115 - "flow"
Cohesion: 0.50
Nodes (4): flow(), act(), as_(), sql()

### Community 116 - "build"
Cohesion: 0.16
Nodes (12): test_files_are_what_the_generator_produces(), build(), add(), act(), assign(), close(), transfer(), details() (+4 more)

### Community 117 - "alerts/repo.py"
Cohesion: 0.22
Nodes (8): _all(), claim_next(), decide(), delivered_to(), known_addresses(), listing(), mark(), retry()

### Community 118 - "get_settings"
Cohesion: 0.06
Nodes (25): chain_for(), _Circuit, _failed(), _record(), reset_circuits(), _json_logs(), publish(), _started() (+17 more)

### Community 119 - "ocr.py"
Cohesion: 0.26
Nodes (6): garbled(), PageLimit, Pages, pages(), _png(), OCR engine: PaddlePaddle or ONNX Runtime (measured 2026-11-23)

### Community 120 - "page"
Cohesion: 0.29
Nodes (5): capped_count(), page(), listing(), page(), _where()

### Community 121 - "search/schemas.py"
Cohesion: 0.43
Nodes (4): ComplaintHit, ComplaintHits, InstitutionHit, Results

### Community 122 - "resources"
Cohesion: 0.22
Nodes (9): deploy, deploy, resources, memory, deploy, limits, deploy, deploy (+1 more)

### Community 123 - "SETHU"
Cohesion: 0.25
Nodes (7): Commands, graphify, Non-negotiable rules, Read first, SETHU, Stack, Working agreements

### Community 124 - "services"
Cohesion: 0.12
Nodes (16): secrets, secrets, environment, profiles, SETHU_ENVIRONMENT, ports, profiles, secrets (+8 more)

### Community 126 - "export"
Cohesion: 0.13
Nodes (9): _check(), export(), report(), _cell(), export(), run(), client(), test_never_in_search_lists_reports_exports_audit_or_logs() (+1 more)

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

### Community 133 - "App.tsx"
Cohesion: 0.08
Nodes (31): App(), CAN_AUDIT, CAN_DECIDE, CAN_INTAKE, CAN_RESOLVE, DECIDES_REVIEW, HAS_CASES, Me (+23 more)

### Community 134 - "as_"
Cohesion: 0.21
Nodes (12): listing(), as_(), client(), detected(), test_case_pages_cover_every_case_once_and_end_exactly(), test_dashboard_counts_are_bounded(), test_filters_combine_with_pages(), test_finding_and_overlap_pages() (+4 more)

### Community 135 - "json"
Cohesion: 0.08
Nodes (14): load_keyring(), parse_keyring(), main(), submit(), main(), main(), _new_key(), _write() (+6 more)

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

### Community 142 - "7. Production"
Cohesion: 0.12
Nodes (16): 1. First start, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, 7. Production, Configuration reference, Keycloak administration (SSH tunnel), Published ports (+8 more)

### Community 143 - "load.py"
Cohesion: 0.13
Nodes (5): insert(), load(), ProductionRefused, rows(), user_id()

### Community 144 - "offline.sh"
Cohesion: 0.40
Nodes (3): MSYS_NO_PATHCONV, offline.sh script, vm()

### Community 145 - "Result"
Cohesion: 0.12
Nodes (5): RapidOCR, Result, GlossaryTranslate, Fake, test_the_job_status_says_when_a_run_was_skipped()

### Community 146 - "test_reports.py"
Cohesion: 0.23
Nodes (9): client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_export_is_csv_without_text_and_is_audited(), test_institution_report_counts_only_the_callers_cases(), test_overlap_outcomes(), test_viewing_is_not_audited_and_bad_names_are_refused() (+1 more)

### Community 147 - "conftest.py"
Cohesion: 0.16
Nodes (9): app_engine(), clean_db(), owner_engine(), world(), person(), client(), test_newest_first_with_filters(), test_only_auditor_oversight_and_admin_read_the_ledger() (+1 more)

### Community 151 - "safe_reason"
Cohesion: 0.33
Nodes (3): Held, safe_reason(), Threats and controls

### Community 153 - "test_ai_router.py"
Cohesion: 0.26
Nodes (15): circuit_state(), ai_run(), call(), ok(), test_a_primary_timeout_falls_back(), test_ai_runs_are_append_only_and_scoped(), test_an_open_circuit_is_skipped_until_its_cooldown_ends(), test_an_unhealthy_provider_is_passed_over() (+7 more)

### Community 155 - "lid.py"
Cohesion: 0.17
Nodes (8): candidates(), detect_script(), model_file(), script_of(), ScriptLID, test_every_scheduled_language_has_a_script_and_a_translation_code(), test_no_letters_is_unknown_and_never_passes(), test_the_script_of_each_sample_and_its_candidates()

### Community 157 - "signins.py"
Cohesion: 0.21
Nodes (6): signins(), _call(), fetch(), _realm_url(), shape(), Unavailable

### Community 158 - "resolve"
Cohesion: 0.20
Nodes (7): attach(), decide(), Decision, download(), review_items(), _run(), resolve()

### Community 159 - "open_attachment"
Cohesion: 0.16
Nodes (7): EnrichmentError, for_case(), _keyring(), mark_pending(), open_attachment(), rekey_attachments(), review_items()

### Community 160 - "ai-worker"
Cohesion: 0.15
Nodes (13): build, cap_drop, command, networks, read_only, restart, secrets, security_opt (+5 more)

### Community 162 - "run"
Cohesion: 0.32
Nodes (8): min_confidence(), run(), setting(), add_review(), save(), _attachments(), _language(), _translate_and_tag()

### Community 163 - "glossary/repo.py"
Cohesion: 0.31
Nodes (6): current_version(), insert_version(), terms(), versions(), current(), listing()

### Community 164 - "glossary/service.py"
Cohesion: 0.31
Nodes (4): check(), GlossaryError, _table(), upload()

### Community 165 - "ci.yml"
Cohesion: 0.18
Nodes (10): concurrency, cancel-in-progress, group, name, on, pull_request, push, permissions (+2 more)

### Community 166 - "jobs"
Cohesion: 0.18
Nodes (11): runs-on, runs-on, jobs, dependency-audit, images, lint, secret-scan, web (+3 more)

### Community 167 - "Findings.tsx"
Cohesion: 0.31
Nodes (9): day(), Finding, FindingsPage(), KIND, numbers(), pct(), spikeWindow(), Target() (+1 more)

### Community 168 - "Provider"
Cohesion: 0.24
Nodes (4): Provider, _succeeded(), _try(), IndicTrans2

### Community 169 - "metrics"
Cohesion: 0.22
Nodes (4): live(), me(), metrics(), ready()

### Community 170 - "with"
Cohesion: 0.22
Nodes (9): with, cache, cache-dependency-path, fetch-depth, name, node-version, path, python-version (+1 more)

### Community 171 - "networks"
Cohesion: 0.25
Nodes (8): internal, internal, internal, networks, ai, app, data, edge

### Community 172 - "migrate"
Cohesion: 0.36
Nodes (8): depends_on, depends_on, migrate, redis, condition, condition, depends_on, depends_on

### Community 173 - "Phase A2: enrichment (language, OCR, translation, glossary)"
Cohesion: 0.25
Nodes (8): Getting the models (connected machine only), Glossary normalisation, Language tiers (what is really supported), Not done in A2, Phase A2: enrichment (language, OCR, translation, glossary), Settings (`sethu.app_settings`), Translation: IndicTrans2 (not installed here), What happens to a complaint

### Community 174 - "ai_health/schemas.py"
Cohesion: 0.53
Nodes (4): AiHealth, Memory, ProviderHealth, TaskHealth

### Community 175 - "search"
Cohesion: 0.33
Nodes (3): _like(), lookup(), search()

### Community 176 - "glossary/schemas.py"
Cohesion: 0.53
Nodes (4): GlossaryOut, Term, UploadOut, Version

### Community 177 - "backend-tests"
Cohesion: 0.33
Nodes (6): runs-on, services, backend-tests, image, ports, redis

### Community 181 - "Seed data"
Cohesion: 0.40
Nodes (4): Files, Negative cases: no alert expected, Seed data, What the loader does

### Community 184 - "Vendored: IndicTrans2 inference helpers"
Cohesion: 0.50
Nodes (3): Review (2026-11-23), Simplified, not vendored (in `app/ai/translate.py`), Vendored: IndicTrans2 inference helpers

### Community 185 - "browser-tests"
Cohesion: 0.50
Nodes (4): needs, runs-on, timeout-minutes, browser-tests

### Community 186 - "egress-canary"
Cohesion: 0.50
Nodes (4): needs, runs-on, timeout-minutes, egress-canary

### Community 187 - "env"
Cohesion: 0.67
Nodes (3): SETHU_TEST_DB_WIPE_OK, SETHU_TEST_REDIS_URL, env

## Knowledge Gaps
- **5 isolated node(s):** `sethu-backend`, `GNUPGHOME`, `PGHOST`, `PGUSER`, `MSYS_NO_PATHCONV`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1252 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **41 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `session_for` to `test_overlaps.py`, `institutions/repo.py`, `test_alerts.py`, `json`, `intake/api.py`, `list_links`, `sqlalchemy`, `graph/repo.py`, `conftest.py`, `overlaps/repo.py`, `bureaus/service.py`, `resolve`, `crypto.py`, `open_attachment`, `test_findings.py`, `run`, `glossary/service.py`, `complaints/service.py`, `metrics`, `test_search.py`, `record`, `complaints/api.py`, `glossary`, `session.py`, `enrichment/repo.py`, `test_glossary.py`, `decide`, `test_auth_and_api.py`, `detect`, `get_principal`, `sqlalchemy`, `logging.py`, `intake`, `users/repo.py`, `list_findings`, `metrics.py`, `decide`, `verify`, `flow`, `get_settings`, `decide`, `export`, `client`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sethu-backend`, `GNUPGHOME`, `PGHOST` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `complaints/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1173054587688734 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `test_overlaps.py`, `findings_as`, `test_alerts.py`, `json`, `intake/api.py`, `as_`, `intake/repo.py`, `load.py`, `test_reports.py`, `conftest.py`, `deliver`, `overlaps/repo.py`, `test_ai_router.py`, `pair`, `crypto.py`, `test_findings.py`, `run`, `test_cases.py`, `metrics`, `test_enrichment.py`, `record`, `test_search.py`, `run_task`, `test_seed.py`, `session.py`, `test_glossary.py`, `reports/service.py`, `detect`, `get_principal`, `sqlalchemy`, `logging.py`, `intake`, `Architecture`, `task`, `json`, `parse_rows`, `verify`, `flow`, `get_settings`, `export`, `client`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 94 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 94 INFERRED edges - model-reasoned connections that need verification._
- **Should `institutions/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07457627118644068 - nodes in this community are weakly interconnected._