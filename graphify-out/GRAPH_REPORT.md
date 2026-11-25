# Graph Report - jolly-feynman-1a9f96  (2026-11-25)

## Corpus Check
- 299 files · ~194,696 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 29 file(s) not represented in the graph (top: (none) 9, .csv 8, .lock 4)

## Summary
- 3663 nodes · 9035 edges · 206 communities (172 shown, 34 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 354 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cc8b9002`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- environment
- test_overlaps.py
- complaints/repo.py
- run
- institutions/repo.py
- test_findings.py
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
- test_a4.py
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
- classify.py
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
- complaints/schemas.py
- services
- Architecture Decision Records
- Architecture Snapshot
- test_seed.py
- migrate
- test_a3.py
- session.py
- 03. Demo Story: "Institution A"
- 04. Mock Data Spec
- enrichment/repo.py
- test_glossary.py
- api
- 05. Next Claude Code Prompts
- Principal
- backup
- postgres
- import.sh
- SETHU
- .claude/CLAUDE.md
- 01-roles.sh
- reports/service.py
- semantic/repo.py
- test_scheduler.py
- sethu-backend
- test_auth_and_api.py
- environment
- dashboard/repo.py
- GraphPage.tsx
- bureaus/api.py
- detect
- test_directory.py
- worker
- secrets
- get_settings
- test_config.py
- Findings.tsx
- worker.py
- scheduler
- signals/repo.py
- test_anchor.py
- AI pipeline
- x-prod-backend-env
- translate.py
- environment
- backup.sh
- users/repo.py
- Data Model
- list_findings
- fetch_models.py
- test_ai_models.py
- Operations guide
- Session
- web
- parse_rows
- signins.py
- Findings
- test_glossary.py
- build
- alerts/service.py
- tasks.py
- ocr.py
- page
- Session
- resources
- SETHU
- services
- decide
- OPERATIONS.md
- graph
- redis
- migrate
- User guide
- audit_view/schemas.py
- main
- App.tsx
- test_paging.py
- Intake API: send one complaint
- _create
- post
- signals
- Load test, failure drills and the offline run
- MapPage.tsx
- Runbook
- load.py
- offline.sh
- NotApplicable
- test_reports.py
- flow
- graph/schemas.py
- 7. Production
- test_ai_router.py
- datetime
- pathlib
- generate.py
- refresh_registry
- resolve
- SingleScheduler
- ai-worker
- Seed data
- suggestions.py
- glossary/repo.py
- glossary/service.py
- ci.yml
- jobs
- fetch_model.py
- egress_canary.py
- metrics.py
- with
- FindingError
- retrain
- Phase A2: enrichment (language, OCR, translation, glossary)
- ai_health/schemas.py
- demo-users
- SemanticError
- backend-tests
- deadline_findings
- semantic/schemas.py
- signals/schemas.py
- Vendored: IndicTrans2 inference helpers
- browser-tests
- egress-canary
- env
- test_graph.py
- manifest.json
- models/README.md
- check-offline.mjs
- listing
- test_dashboard.py
- AiHealth.tsx
- make_india_map.py
- test_fetch_models.py
- sqlalchemy
- run
- json
- Result

## God Nodes (most connected - your core abstractions)
1. `session_for()` - 240 edges
2. `Principal` - 226 edges
3. `get_settings()` - 98 edges
4. `Result` - 63 edges
5. `record()` - 63 edges
6. `useLoad()` - 62 edges
7. `Provider` - 46 edges
8. `api()` - 43 edges
9. `detect()` - 34 edges
10. `get_principal()` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Settings added (`sethu.app_settings`, migration 0016)` --references--> `min_confidence()`  [INFERRED]
  docs/AI-PIPELINE.md → backend/app/ai/router.py
- `6. Audit ledger` --references--> `verify()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/audit/service.py
- `Tamper demonstration` --references--> `verify()`  [INFERRED]
  docs/RUNBOOK.md → backend/app/audit/service.py
- `Informational` --references--> `test_a10_001_concurrent_writers_keep_the_audit_chain_whole()`  [INFERRED]
  docs/SECURITY-REVIEW.md → backend/tests/test_security.py
- `Compliance notes (to confirm with the AICTE mentor)` --references--> `due_at()`  [INFERRED]
  docs/SECURITY.md → backend/app/modules/complaints/service.py

## Import Cycles
- None detected.

## Communities (206 total, 34 thin omitted)

### Community 0 - "environment"
Cohesion: 0.22
Nodes (26): environment, environment, HF_HUB_OFFLINE, SETHU_AI_MODELS_DIR, SETHU_ALERT_FROM, SETHU_AUDIT_ANCHOR_DIR, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL (+18 more)

### Community 1 - "test_overlaps.py"
Cohesion: 0.18
Nodes (15): detect_overlaps(), detected(), scalar(), suggested_pairs(), test_a_second_overlap_run_is_skipped_while_one_is_running(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs() (+7 more)

### Community 2 - "complaints/repo.py"
Cohesion: 0.11
Nodes (28): _all(), assigned_to(), bureaus(), case_counts(), deadline_days(), deadlines(), exists(), find() (+20 more)

### Community 3 - "run"
Cohesion: 0.37
Nodes (13): steps, steps, steps, steps, steps, steps, steps, if (+5 more)

### Community 4 - "institutions/repo.py"
Cohesion: 0.09
Nodes (26): add_alias(), aliases(), _all(), by_acronym(), by_permanent_id(), candidates(), counts(), get() (+18 more)

### Community 5 - "test_findings.py"
Cohesion: 0.14
Nodes (20): cell(), detected(), findings_as(), hop(), test_a_second_run_adds_nothing(), test_a_spike_that_comes_back_is_reopened_with_its_new_counts(), test_an_acknowledgement_or_any_action_breaks_the_loop(), test_dismiss_reopen_and_resolve_are_audited_and_limited() (+12 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.10
Nodes (24): alert_row(), approved(), audit_count(), closed_port(), deliver(), FakeSMTP, held(), kinds() (+16 more)

### Community 7 - "backend"
Cohesion: 0.13
Nodes (18): depends_on, build, cap_drop, depends_on, networks, read_only, restart, secrets (+10 more)

### Community 8 - "intake/api.py"
Cohesion: 0.12
Nodes (20): create_source(), issue_key(), items(), manual(), retry(), reviewed(), _run(), sources() (+12 more)

### Community 9 - "session_for"
Cohesion: 0.11
Nodes (26): session_for(), test_a_deactivated_bureau_takes_no_transfers(), test_the_database_lets_a_person_write_only_their_own_row_with_their_token_role(), test_the_database_refuses_bureau_writes_from_anyone_but_admin(), test_who_sees_and_does_what_on_the_intake_screens(), _count(), linked(), _refs() (+18 more)

### Community 10 - "institutions/schemas.py"
Cohesion: 0.17
Nodes (17): Alias, BureauCount, Candidate, CaseSummary, CategoryShare, Disposal, Dna, Institution (+9 more)

### Community 11 - "package.json"
Cohesion: 0.06
Nodes (38): @axe-core/playwright, echarts, @playwright/test, react-dom, @types/cytoscape, @types/react, @types/react-dom, typescript (+30 more)

### Community 12 - "options"
Cohesion: 0.10
Nodes (26): logging, logging, logging, driver, options, cap_drop, image, logging (+18 more)

### Community 13 - "App"
Cohesion: 0.09
Nodes (40): ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters, Attachments(), EnrichmentPanel() (+32 more)

### Community 14 - "institutions/types.ts"
Cohesion: 0.16
Nodes (21): useLoad(), InstitutionTimeline(), DnaPanel(), pct(), TREND, InstitutionList(), InstitutionProfile(), ResolutionQueue() (+13 more)

### Community 15 - "intake/repo.py"
Cohesion: 0.15
Nodes (19): _all(), claim_next(), failed(), finish(), forget_nonces(), health(), insert_item(), insert_source() (+11 more)

### Community 16 - "sqlalchemy"
Cohesion: 0.11
Nodes (9): anchor_check(), list_entries(), signins(), verify(), actions(), entries(), entry(), entries() (+1 more)

### Community 17 - "test_a4.py"
Cohesion: 0.05
Nodes (57): build(), reset_circuits(), aggregate_edges(), _all(), bureaus(), case_refs(), communities_of(), complaints() (+49 more)

### Community 18 - "intake/schemas.py"
Cohesion: 0.18
Nodes (10): Accepted, Complainant, IssuedKey, Item, RowError, Source, SourceIn, SourcePatch (+2 more)

### Community 19 - "postgres"
Cohesion: 0.11
Nodes (18): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+10 more)

### Community 20 - "config.py"
Cohesion: 0.09
Nodes (10): run_migrations_online(), _url(), production_problems(), read_secret(), remote_url(), Settings, _weak(), with_password() (+2 more)

### Community 21 - "overlaps/repo.py"
Cohesion: 0.06
Nodes (38): _all(), candidates(), decide(), insert_alert(), insert_link(), linked_case_ids(), links(), links_page() (+30 more)

### Community 22 - "web"
Cohesion: 0.15
Nodes (13): condition, backend, web, build, cap_drop, depends_on, networks, ports (+5 more)

### Community 23 - "bureaus/service.py"
Cohesion: 0.18
Nodes (10): _all(), by_code(), get(), insert(), listing(), update(), BureauError, by_code() (+2 more)

### Community 24 - "registry.py"
Cohesion: 0.10
Nodes (15): ModelManager, check_all(), digest(), _file_sha256(), load_manifest(), ModelEntry, ModelIntegrityError, verify() (+7 more)

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
Cohesion: 0.12
Nodes (15): key_id_of(), Keyring, KeyringError, load_keyring(), parse_keyring(), _split(), keyring(), rotate_complainant_keys() (+7 more)

### Community 31 - "test_findings.py"
Cohesion: 0.18
Nodes (12): normalize(), scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_normalize_expands_abbreviations(), test_officer_picks_from_the_queue() (+4 more)

### Community 32 - "redis"
Cohesion: 0.17
Nodes (12): REDIS_PASSWORD, cap_add, cap_drop, command, environment, image, networks, read_only (+4 more)

### Community 33 - "keycloak"
Cohesion: 0.15
Nodes (13): postgres, cap_drop, command, depends_on, deploy, image, networks, restart (+5 more)

### Community 34 - "environment"
Cohesion: 0.15
Nodes (13): KEYCLOAK_DB_PASSWORD, KEYCLOAK_DB_PASSWORD_FILE, POSTGRES_PASSWORD, POSTGRES_PASSWORD_FILE, SETHU_APP_PASSWORD, SETHU_APP_PASSWORD_FILE, SETHU_AUDITOR_PASSWORD, SETHU_AUDITOR_PASSWORD_FILE (+5 more)

### Community 35 - "classify.py"
Cohesion: 0.08
Nodes (19): ArtifactError, CategoryModel, checksum(), evaluate(), load(), predict(), train(), nll() (+11 more)

### Community 36 - "x-prod-backend-env"
Cohesion: 0.09
Nodes (23): file, file, file, file, file, file, file, secrets (+15 more)

### Community 37 - "01. Scope Lock"
Cohesion: 0.17
Nodes (11): 01. Scope Lock, Constraints, Definition of done (per feature), Freeze rules, Goal in one sentence, Out of scope (do not discuss again), Parking lot, Sign-off (+3 more)

### Community 38 - "test_cases.py"
Cohesion: 0.22
Nodes (12): audit_rows(), scalar(), test_api_hides_text_and_enforces_roles(), test_every_action_is_audited_and_the_chain_verifies(), test_list_filters_search_and_institution_timeline(), test_loop_case_c090_shows_both_unacknowledged_transfers(), test_officer_cannot_read_or_change_another_bureaus_complaint(), test_transfer_and_acknowledgement_appear_in_the_history() (+4 more)

### Community 39 - "AuditLog.tsx"
Cohesion: 0.18
Nodes (12): AnchorReport, Anchors(), AuditLog(), ChainReport, EMPTY, Entry, EntryPage, moment() (+4 more)

### Community 40 - "complaints/service.py"
Cohesion: 0.09
Nodes (23): act(), actor_id(), assignees(), can_act(), CaseError, complainant_visible(), create(), deadline_days() (+15 more)

### Community 41 - "test_enrichment.py"
Cohesion: 0.07
Nodes (8): E5Embed, installed(), manager(), RapidOCR, TesseractOCR, StubProvider, client(), fresh()

### Community 42 - "test_search.py"
Cohesion: 0.16
Nodes (10): search(), test_a_bureau_code_matches_exactly_in_search(), test_api_decisions_detection_and_the_overlapping_filter(), find(), hits(), test_bureau_a_never_sees_bureau_b_text_through_search(), test_cases_by_reference_and_metadata_across_bureaus(), test_institutions_by_name_alias_initials_and_city() (+2 more)

### Community 43 - "record"
Cohesion: 0.15
Nodes (23): record(), sources(), ComplaintIn, body_hash(), _by_name(), create_source(), _enqueue(), fingerprint() (+15 more)

### Community 44 - "api.ts"
Cohesion: 0.14
Nodes (22): answer(), download(), upload(), accessToken(), base64url(), login(), logout(), redirectUri() (+14 more)

### Community 45 - "healthcheck"
Cohesion: 0.47
Nodes (12): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+4 more)

### Community 46 - "complaints/schemas.py"
Cohesion: 0.06
Nodes (36): blank_to_none(), PageMeta, Action, ActionIn, Assignee, Bureau, Case, CasePage (+28 more)

### Community 47 - "services"
Cohesion: 0.12
Nodes (16): internal, internal, file, internal, name, networks, ai, app (+8 more)

### Community 48 - "Architecture Decision Records"
Cohesion: 0.22
Nodes (8): 0001. Modular monolith, not microservices, 0002. Enforce access in the database with Row-Level Security, 0003. Hash-chained audit log inside PostgreSQL, not a blockchain, 0004. Transactional outbox for alerts, 0005. Local models only, each with a deterministic fallback, 0006. Object storage deferred, 0007. Keycloak for identity, Architecture Decision Records

### Community 49 - "Architecture Snapshot"
Cohesion: 0.22
Nodes (8): Architecture Pattern, Architecture Snapshot, Critical Modules, Dependency Rules, Entry Points, Extraction Quality, Repository Map, Routes

### Community 50 - "test_seed.py"
Cohesion: 0.16
Nodes (12): cross_bureau_pairs(), deadlocks(), duplicate_pairs(), not_closed(), silent(), spikes(), tagged(), test_expected_detections() (+4 more)

### Community 51 - "migrate"
Cohesion: 0.18
Nodes (11): MIGRATION_DATABASE_URL, build, cap_drop, command, deploy, environment, networks, read_only (+3 more)

### Community 52 - "test_a3.py"
Cohesion: 0.14
Nodes (21): add_pair(), detect(), e5(), file_case(), fresh(), pair_link(), q(), StubE5 (+13 more)

### Community 53 - "session.py"
Cohesion: 0.12
Nodes (4): require_roles(), page_params(), get_session(), dna()

### Community 54 - "03. Demo Story: "Institution A""
Cohesion: 0.25
Nodes (7): 03. Demo Story: "Institution A", Characters (fictional), Cut list if the demo runs long, Rehearsal checklist, Script, Seeded facts, The story in one line

### Community 55 - "04. Mock Data Spec"
Cohesion: 0.25
Nodes (7): 04. Mock Data Spec, Deliberate patterns to seed, Expected detections (used by tests), Files to generate, Fixed demo records (do not randomise), Negative cases (must NOT be flagged), Volume

### Community 56 - "enrichment/repo.py"
Cohesion: 0.07
Nodes (55): add_review(), _all(), attachment(), attachments(), body(), can_read_case(), claim(), enrichment() (+47 more)

### Community 57 - "test_glossary.py"
Cohesion: 0.25
Nodes (8): Glossary, _latin(), Match, normalise(), test_indic_terms_may_take_a_suffix_but_must_start_a_word(), test_longest_match_first_and_word_boundaries(), test_the_starter_glossary_on_the_samples(), test_unicode_normalisation_and_coverage()

### Community 58 - "api"
Cohesion: 0.08
Nodes (35): api(), AdminPage(), changed(), create(), BureauLine(), save(), BureauRow, Deadline (+27 more)

### Community 59 - "05. Next Claude Code Prompts"
Cohesion: 0.33
Nodes (5): 05. Next Claude Code Prompts, After that, in this order, Prompt 1: bring the stack up, Prompt 2: mock data, Prompt 3: first feature (institutions and resolution)

### Community 60 - "Principal"
Cohesion: 0.14
Nodes (18): Principal, apply_context(), act(), assignees(), case(), deadlines(), institution_timeline(), list_cases() (+10 more)

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
Cohesion: 0.09
Nodes (15): _check(), export(), report(), _all(), bureaus(), _in_range(), institutions(), overlaps() (+7 more)

### Community 73 - "semantic/repo.py"
Cohesion: 0.16
Nodes (19): activate_classifier(), active_classifier(), _all(), classifier(), classifier_versions(), classify_inputs(), complaint_count(), corrections() (+11 more)

### Community 74 - "test_scheduler.py"
Cohesion: 0.24
Nodes (5): scheduler(), start(), test_a_scheduler_that_lost_its_lock_stops(), test_a_second_scheduler_refuses_to_start(), test_the_lock_passes_on_when_the_scheduler_stops_or_dies()

### Community 78 - "test_auth_and_api.py"
Cohesion: 0.11
Nodes (12): AuthError, decode_token(), get_principal(), _jwks_client(), principal_from_claims(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins() (+4 more)

### Community 79 - "environment"
Cohesion: 0.18
Nodes (33): environment, environment, environment, DEMO_USER_PASSWORD, HF_HUB_OFFLINE, KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_ADMIN_USER, SETHU_AI_MODELS_DIR (+25 more)

### Community 80 - "dashboard/repo.py"
Cohesion: 0.18
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 81 - "GraphPage.tsx"
Cohesion: 0.16
Nodes (21): cytoscape, ComplaintDetail(), EDGE_WORDS, EdgePanel(), EvidenceCase, Explanation, GraphPage(), GraphTable() (+13 more)

### Community 82 - "bureaus/api.py"
Cohesion: 0.27
Nodes (5): create_bureau(), list_bureaus(), _run(), update_bureau(), listing()

### Community 83 - "detect"
Cohesion: 0.16
Nodes (15): _all(), bureau_codes(), bureau_queues(), category_cells(), existing(), insert(), institution_queues(), overdue_cases() (+7 more)

### Community 84 - "test_directory.py"
Cohesion: 0.23
Nodes (7): audit_rows(), client(), row(), test_a_token_without_email_keeps_the_stored_address(), test_admin_creates_and_deactivates_a_bureau_and_both_are_audited(), test_first_sign_in_creates_the_record_with_email_and_a_bureau_change_reaches_it(), test_people_without_email_are_flagged_for_the_admin()

### Community 86 - "worker"
Cohesion: 0.18
Nodes (11): worker, build, cap_drop, command, networks, read_only, restart, secrets (+3 more)

### Community 87 - "secrets"
Cohesion: 0.25
Nodes (6): ensure_added_keys(), ensure_keyring(), main(), main(), rotate(), _write()

### Community 88 - "get_settings"
Cohesion: 0.13
Nodes (14): chain_for(), _Circuit, circuit_state(), _failed(), _record(), _succeeded(), _try(), get_settings() (+6 more)

### Community 89 - "test_config.py"
Cohesion: 0.18
Nodes (12): refused(), settings(), _shell(), test_a_complete_production_configuration_starts(), test_ai_endpoints_inside_the_deployment_are_allowed(), test_all_problems_are_reported_at_once(), test_an_unreadable_secret_file_is_named_not_shown(), test_dev_and_test_keep_working_with_dev_values() (+4 more)

### Community 90 - "Findings.tsx"
Cohesion: 0.08
Nodes (35): Options, cases(), Count, CountTable(), Dashboard(), day(), OverdueCase, Overview (+27 more)

### Community 91 - "worker.py"
Cohesion: 0.05
Nodes (21): accept_request_id(), configure_logging(), JsonFormatter, observe_request(), get_engine(), create_app(), request_context(), health() (+13 more)

### Community 92 - "scheduler"
Cohesion: 0.18
Nodes (11): build, cap_drop, command, deploy, networks, read_only, restart, secrets (+3 more)

### Community 93 - "signals/repo.py"
Cohesion: 0.12
Nodes (23): _all(), case_refs(), complaints(), decide(), insert(), institutions_in(), listing(), _params() (+15 more)

### Community 94 - "test_anchor.py"
Cohesion: 0.16
Nodes (10): compare(), export(), _file(), main(), export_anchor(), anchored(), check(), test_a_rewritten_entry_or_a_replaced_database_is_reported() (+2 more)

### Community 95 - "AI pipeline"
Cohesion: 0.05
Nodes (40): Adding a model, AI pipeline, Classification (task `classify.category`), Complaint matching (task `match.complaints`), Dependencies, Health, Institution resolution (task `institution.resolve`), Measured time and memory (+32 more)

### Community 96 - "x-prod-backend-env"
Cohesion: 0.10
Nodes (20): x-prod-backend-env, SETHU_ALERT_FROM, SETHU_AUDIT_ANCHOR_DIR, SETHU_DATABASE_PASSWORD_FILE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_INTAKE_SPOOL_DIR (+12 more)

### Community 98 - "translate.py"
Cohesion: 0.15
Nodes (9): detokenize(), preprocess(), to_devanagari(), tokenize(), punc_norm(), normalize(), normalize_indic_numerals(), wrap_with_placeholders() (+1 more)

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
Cohesion: 0.20
Nodes (5): decide(), detect(), list_findings(), trend(), trend()

### Community 105 - "fetch_models.py"
Cohesion: 0.25
Nodes (7): add(), download(), installed(), main(), record(), refuse_if_deployed(), small()

### Community 107 - "test_ai_models.py"
Cohesion: 0.16
Nodes (11): rss_mb(), IndicTrans2, cer(), edit_distance(), peak_mb(), real_models(), test_language_detection_with_fasttext(), test_ocr_on_the_rendered_samples() (+3 more)

### Community 108 - "Operations guide"
Cohesion: 0.13
Nodes (15): 10. Incident response, 11. Known limits, 1. What runs, 2. Install, 3. Configuration reference, 4. First-time setup (after the first start), 5. Upgrade, 6. Backup and restore, and the drill (+7 more)

### Community 109 - "Session"
Cohesion: 0.13
Nodes (12): insert_alert(), _alert(), bottleneck_settings(), decide(), detect(), _digest(), hold_alert(), queue_findings() (+4 more)

### Community 111 - "web"
Cohesion: 0.25
Nodes (8): condition, backend, keycloak, condition, web, depends_on, ports, volumes

### Community 112 - "parse_rows"
Cohesion: 0.15
Nodes (10): parse_rows(), read_plain_file(), spool(), test_a01_001_a_link_in_the_spool_folder_is_refused_unread(), test_a01_001_an_unknown_header_is_not_echoed(), test_a06_001_a_spreadsheet_that_expands_too_far_is_refused_before_parsing(), test_a06_001_the_row_limit_is_enforced_while_reading(), _xlsx() (+2 more)

### Community 113 - "signins.py"
Cohesion: 0.29
Nodes (5): _call(), fetch(), _realm_url(), shape(), Unavailable

### Community 114 - "Findings"
Cohesion: 0.13
Nodes (13): test_a02_001_the_api_description_is_not_under_the_proxied_path(), Areas checked with no finding, Findings, Informational, Method, OWASP-A02-001 The API description was served through the edge in dev (CWE-200, Exposure of Sensitive Information to an Unauthorized Actor), OWASP-A02-002 `/health/ready` reachable from outside (CWE-200), OWASP-A02-003 CSP allows inline styles (CWE-1021 family; style injection only) (+5 more)

### Community 115 - "test_glossary.py"
Cohesion: 0.31
Nodes (4): client(), csv_bytes(), test_upload_is_all_or_nothing_versioned_and_audited(), test_xlsx_upload_and_who_may()

### Community 116 - "build"
Cohesion: 0.26
Nodes (9): build(), add(), act(), assign(), close(), transfer(), details(), fresh() (+1 more)

### Community 117 - "alerts/service.py"
Cohesion: 0.05
Nodes (27): _all(), claim_next(), decide(), delivered_to(), known_addresses(), listing(), mark(), retry() (+19 more)

### Community 118 - "tasks.py"
Cohesion: 0.17
Nodes (9): enrich_pending(), _json_logs(), maintain(), publish(), retrain_classifier(), run_task(), _started(), state() (+1 more)

### Community 119 - "ocr.py"
Cohesion: 0.33
Nodes (4): PageLimit, Pages, pages(), _png()

### Community 120 - "page"
Cohesion: 0.32
Nodes (4): capped_count(), page(), open_count(), open_count()

### Community 121 - "Session"
Cohesion: 0.19
Nodes (4): counts_last_day(), last_runs(), health(), classifiers()

### Community 122 - "resources"
Cohesion: 0.22
Nodes (9): deploy, deploy, deploy, resources, memory, deploy, limits, deploy (+1 more)

### Community 123 - "SETHU"
Cohesion: 0.22
Nodes (8): Commands, graphify, Layout, Non-negotiable rules, Read first, SETHU, Stack, Working agreements

### Community 124 - "services"
Cohesion: 0.14
Nodes (14): secrets, secrets, environment, profiles, SETHU_ENVIRONMENT, ports, profiles, services (+6 more)

### Community 125 - "decide"
Cohesion: 0.25
Nodes (3): decide(), list_alerts(), retry()

### Community 126 - "OPERATIONS.md"
Cohesion: 0.22
Nodes (5): API, Who calls what, Gaps, Phases (proposed), Production readiness

### Community 127 - "graph"
Cohesion: 0.14
Nodes (4): build(), ego(), explain(), graph()

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

### Community 132 - "main"
Cohesion: 0.09
Nodes (9): Encoder, E5Match, TextMatch, test_match_providers_fall_through_and_agreement_moves_confidence(), main(), chain(), pr(), rss() (+1 more)

### Community 133 - "App.tsx"
Cohesion: 0.10
Nodes (26): react, App(), CAN_AUDIT, CAN_DECIDE, CAN_INTAKE, CAN_RESOLVE, DECIDES_REVIEW, HAS_CASES (+18 more)

### Community 134 - "test_paging.py"
Cohesion: 0.21
Nodes (12): listing(), as_(), client(), detected(), test_case_pages_cover_every_case_once_and_end_exactly(), test_dashboard_counts_are_bounded(), test_filters_combine_with_pages(), test_finding_and_overlap_pages() (+4 more)

### Community 135 - "Intake API: send one complaint"
Cohesion: 0.25
Nodes (8): Answer, Body, Errors, Example, Headers, Intake API: send one complaint, Other channels, Signing and transport

### Community 136 - "_create"
Cohesion: 0.14
Nodes (9): _create(), Held, safe_reason(), Assets, Before any real deployment, Compliance notes (to confirm with the AICTE mentor), Rules for contributors, Security (+1 more)

### Community 137 - "post"
Cohesion: 0.13
Nodes (8): _client(), queue(), status(), decide(), detect(), detect_status(), list_links(), tier1()

### Community 139 - "signals"
Cohesion: 0.14
Nodes (5): decide(), detect(), map_state(), map_states(), signals()

### Community 140 - "Load test, failure drills and the offline run"
Cohesion: 0.25
Nodes (7): Drills, How to run it, Load test, failure drills and the offline run, Measured before the host gave out (not capacity figures), Paged lists (2026-11-22), Status (2026-11-21): incomplete, To run on a larger machine (at least 16 GB of RAM, nothing else running)

### Community 141 - "MapPage.tsx"
Cohesion: 0.18
Nodes (13): GeoJSON, IndiaMap(), MapPage(), MapStates, Member, METHOD, Signal, SignalCard() (+5 more)

### Community 142 - "Runbook"
Cohesion: 0.20
Nodes (10): 1. First start, 2. Daily use, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, Restore, Restore drill (2026-11-20, throwaway production-mode stack), Runbook (+2 more)

### Community 143 - "load.py"
Cohesion: 0.17
Nodes (5): insert(), load(), ProductionRefused, rows(), user_id()

### Community 144 - "offline.sh"
Cohesion: 0.40
Nodes (3): MSYS_NO_PATHCONV, offline.sh script, vm()

### Community 145 - "NotApplicable"
Cohesion: 0.08
Nodes (20): NotApplicable, _adjust(), _clamp(), _distance_confidence(), E5Institution, FuzzyInstitution, _institution_decision(), centroids() (+12 more)

### Community 146 - "test_reports.py"
Cohesion: 0.19
Nodes (9): client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_export_is_csv_without_text_and_is_audited(), test_institution_report_counts_only_the_callers_cases(), test_overlap_outcomes(), test_viewing_is_not_audited_and_bad_names_are_refused() (+1 more)

### Community 147 - "flow"
Cohesion: 0.50
Nodes (4): flow(), act(), as_(), sql()

### Community 148 - "graph/schemas.py"
Cohesion: 0.24
Nodes (10): Edge, Ego, EgoEdge, EgoNode, EvidenceCase, Explanation, Filters, Graph (+2 more)

### Community 151 - "7. Production"
Cohesion: 0.25
Nodes (8): 7. Production, Configuration reference, Keycloak administration (SSH tunnel), Published ports, Secrets, Start, The production realm, TLS certificate

### Community 153 - "test_ai_router.py"
Cohesion: 0.34
Nodes (13): ai_run(), call(), ok(), test_a_primary_timeout_falls_back(), test_ai_runs_are_append_only_and_scoped(), test_an_open_circuit_is_skipped_until_its_cooldown_ends(), test_an_unhealthy_provider_is_passed_over(), test_low_confidence_falls_through_by_the_setting_in_app_settings() (+5 more)

### Community 154 - "datetime"
Cohesion: 0.07
Nodes (24): Alert, AlertPage, DecisionIn, Bureau, BureauChange, BureauIn, BureauRow, Attention (+16 more)

### Community 155 - "pathlib"
Cohesion: 0.13
Nodes (10): candidates(), detect_script(), FastTextLID, model_file(), script_of(), ScriptLID, test_every_scheduled_language_has_a_script_and_a_translation_code(), test_fasttext_is_unhealthy_until_installed() (+2 more)

### Community 156 - "generate.py"
Cohesion: 0.33
Nodes (3): test_files_are_what_the_generator_produces(), render(), variant()

### Community 157 - "refresh_registry"
Cohesion: 0.33
Nodes (3): registry_drop_stale(), maintain(), refresh_registry()

### Community 158 - "resolve"
Cohesion: 0.24
Nodes (6): attach(), decide(), Decision, download(), review_items(), _run()

### Community 160 - "ai-worker"
Cohesion: 0.15
Nodes (13): build, cap_drop, command, networks, read_only, restart, secrets, security_opt (+5 more)

### Community 161 - "Seed data"
Cohesion: 0.33
Nodes (5): Files, Negative cases: no alert expected, Seed data, Seeded patterns and the expected detection, What the loader does

### Community 162 - "suggestions.py"
Cohesion: 0.29
Nodes (5): attempt_keys(), decide(), get(), record(), store()

### Community 163 - "glossary/repo.py"
Cohesion: 0.31
Nodes (6): current_version(), insert_version(), terms(), versions(), current(), listing()

### Community 164 - "glossary/service.py"
Cohesion: 0.17
Nodes (6): glossary(), upload(), check(), GlossaryError, _table(), upload()

### Community 165 - "ci.yml"
Cohesion: 0.18
Nodes (10): concurrency, cancel-in-progress, group, name, on, pull_request, push, permissions (+2 more)

### Community 166 - "jobs"
Cohesion: 0.18
Nodes (11): runs-on, runs-on, jobs, dependency-audit, images, lint, secret-scan, web (+3 more)

### Community 167 - "fetch_model.py"
Cohesion: 0.17
Nodes (6): fetch(), main(), sha256(), check_pem(), main(), nginx()

### Community 168 - "egress_canary.py"
Cohesion: 0.22
Nodes (11): box(), test_a_sealed_stack_passes_and_edge_routes_are_only_noted(), test_ai_worker_must_run_be_sealed_and_be_probed(), test_an_internal_container_that_reaches_out_fails(), test_strict_fails_the_edge_too(), containers(), host_rules(), main() (+3 more)

### Community 169 - "metrics.py"
Cohesion: 0.14
Nodes (8): live(), me(), metrics(), ready(), _label(), _process_lines(), record_run(), render()

### Community 170 - "with"
Cohesion: 0.22
Nodes (9): with, cache, cache-dependency-path, fetch-depth, name, node-version, path, python-version (+1 more)

### Community 172 - "retrain"
Cohesion: 0.14
Nodes (16): active(), bootstrap(), classify_complaints(), coverage(), decide_category(), _embed(), embed_complaints(), for_case() (+8 more)

### Community 173 - "Phase A2: enrichment (language, OCR, translation, glossary)"
Cohesion: 0.20
Nodes (9): garbled(), Getting the models (connected machine only), Glossary normalisation, Language tiers (what is really supported), Not done in A2, OCR engine: PaddlePaddle or ONNX Runtime (measured 2026-11-23), Phase A2: enrichment (language, OCR, translation, glossary), Settings (`sethu.app_settings`) (+1 more)

### Community 174 - "ai_health/schemas.py"
Cohesion: 0.53
Nodes (4): AiHealth, Memory, ProviderHealth, TaskHealth

### Community 175 - "demo-users"
Cohesion: 0.14
Nodes (14): cap_drop, depends_on, entrypoint, image, networks, profiles, read_only, restart (+6 more)

### Community 177 - "backend-tests"
Cohesion: 0.33
Nodes (6): runs-on, services, backend-tests, image, ports, redis

### Community 179 - "semantic/schemas.py"
Cohesion: 0.31
Nodes (8): Activated, CaseSuggestions, CategoryIn, ClassifierVersion, Decided, InstitutionIn, Queued, Suggestion

### Community 180 - "signals/schemas.py"
Cohesion: 0.31
Nodes (8): DecisionIn, MapState, MapStates, MemberCase, Queued, Signal, StateInstitution, StateRow

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

### Community 189 - "test_graph.py"
Cohesion: 0.21
Nodes (8): kinds(), net(), sql(), test_aggregated_by_default_with_counts_and_multi_bureau_clusters(), test_each_role_sees_only_its_share_of_links_and_transfers_and_never_text(), test_expanding_an_institution_adds_its_complaints_and_overlap_edges(), test_filters_narrow_the_graph(), test_five_thousand_more_complaints_stay_aggregated_and_fast()

### Community 195 - "check-offline.mjs"
Cohesion: 0.25
Nodes (5): DIST, failures, files(), LOADS, mentioned

### Community 196 - "listing"
Cohesion: 0.38
Nodes (4): listing(), page(), _where(), page()

### Community 198 - "test_dashboard.py"
Cohesion: 0.27
Nodes (9): board(), counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data(), test_cross_bureau_numbers_are_the_same_for_everyone(), test_every_role_gets_the_dashboard() (+1 more)

### Community 199 - "AiHealth.tsx"
Cohesion: 0.21
Nodes (11): AiHealthPage(), Classifier(), act(), Health, Metrics, PATHS, pct(), Provider (+3 more)

### Community 200 - "make_india_map.py"
Cohesion: 0.38
Nodes (3): area_centroid(), main(), ring()

### Community 202 - "sqlalchemy"
Cohesion: 0.09
Nodes (22): ChainStatus, verify(), verify_chain(), app_engine(), clean_db(), owner_engine(), world(), person() (+14 more)

### Community 203 - "run"
Cohesion: 0.53
Nodes (3): min_confidence(), run(), setting()

### Community 206 - "json"
Cohesion: 0.11
Nodes (17): test_a4_at_volume(), main(), submit(), main(), main(), _new_key(), _write(), hashes() (+9 more)

### Community 208 - "Result"
Cohesion: 0.06
Nodes (17): CategoryRules, rule_scores(), communities(), GraphCTE, GraphDirect, GraphNetworkX, Provider, Result (+9 more)

## Knowledge Gaps
- **5 isolated node(s):** `GNUPGHOME`, `PGHOST`, `PGUSER`, `MSYS_NO_PATHCONV`, `sethu-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1444 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `test_overlaps.py`, `institutions/repo.py`, `test_alerts.py`, `intake/api.py`, `session_for`, `post`, `signals`, `sqlalchemy`, `test_a4.py`, `flow`, `overlaps/repo.py`, `bureaus/service.py`, `resolve`, `crypto.py`, `test_findings.py`, `suggestions.py`, `glossary/service.py`, `complaints/service.py`, `metrics.py`, `test_search.py`, `record`, `retrain`, `test_a3.py`, `session.py`, `enrichment/repo.py`, `test_graph.py`, `reports/service.py`, `semantic/repo.py`, `sqlalchemy`, `run`, `test_auth_and_api.py`, `json`, `bureaus/api.py`, `test_directory.py`, `get_settings`, `worker.py`, `signals/repo.py`, `users/repo.py`, `list_findings`, `Session`, `test_glossary.py`, `alerts/service.py`, `decide`, `graph`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `GNUPGHOME`, `PGHOST`, `PGUSER` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `complaints/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1072463768115942 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `test_overlaps.py`, `test_findings.py`, `test_alerts.py`, `test_paging.py`, `intake/api.py`, `intake/repo.py`, `load.py`, `test_a4.py`, `test_reports.py`, `flow`, `NotApplicable`, `overlaps/repo.py`, `config.py`, `test_ai_router.py`, `refresh_registry`, `crypto.py`, `test_findings.py`, `test_cases.py`, `metrics.py`, `test_search.py`, `record`, `retrain`, `test_enrichment.py`, `test_seed.py`, `test_a3.py`, `session.py`, `enrichment/repo.py`, `Principal`, `test_graph.py`, `test_dashboard.py`, `reports/service.py`, `sqlalchemy`, `json`, `test_auth_and_api.py`, `test_directory.py`, `get_settings`, `worker.py`, `test_anchor.py`, `AI pipeline`, `Session`, `parse_rows`, `test_glossary.py`, `alerts/service.py`, `tasks.py`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Are the 143 inferred relationships involving `Principal` (e.g. with `run()` and `decide()`) actually correct?**
  _`Principal` has 143 INFERRED edges - model-reasoned connections that need verification._
- **Should `institutions/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09397163120567376 - nodes in this community are weakly interconnected._