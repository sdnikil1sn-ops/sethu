# Graph Report - jolly-feynman-1a9f96  (2026-11-20)

## Corpus Check
- 140 files · ~67,951 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 19 file(s) not represented in the graph (top: (none) 8, .csv 5, .conf 2)

## Summary
- 1493 nodes · 3145 edges · 118 communities (76 shown, 42 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d3e3e6be`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_dashboard.py
- test_seed.py
- complaints/service.py
- test_search.py
- institutions/repo.py
- alerts/repo.py
- test_alerts.py
- backend
- audit_view/repo.py
- session_for
- complaints/api.py
- package.json
- options
- CaseDetail.tsx
- useLoad
- test_config.py
- dashboard/repo.py
- Principal
- test_overlaps.py
- postgres
- export
- overlaps/service.py
- web
- test_findings.py
- demo-users
- Runbook
- Architecture
- x-backend-env
- compilerOptions
- environment
- config.py
- test_findings.py
- redis
- keycloak
- load.py
- findings/service.py
- services
- 01. Scope Lock
- 02. PS Coverage Checklist (SIH26264)
- AuditLog.tsx
- Overlaps.tsx
- conftest.py
- reports/service.py
- generate.py
- api.ts
- healthcheck
- reports/service.py
- services
- Architecture Decision Records
- Architecture Snapshot
- App.tsx
- migrate
- Dashboard.tsx
- auth.py
- 03. Demo Story: "Institution A"
- 04. Mock Data Spec
- Data Model
- Security
- worker
- 05. Next Claude Code Prompts
- findings/service.py
- postgres
- import.sh
- SETHU
- .claude/CLAUDE.md
- 01-roles.sh
- sethu-backend
- test_filters.py
- environment
- linked
- main.py
- dashboard/schemas.py
- test_audit_view.py
- audit_view/schemas.py
- overlaps/schemas.py
- test_reports.py
- institutions/schemas.py
- Findings.tsx
- env.py
- init_env.py
- Production readiness
- search
- build
- routes.py
- pydantic
- Seed data

## God Nodes (most connected - your core abstractions)
1. `session_for()` - 107 edges
2. `Principal` - 103 edges
3. `useLoad()` - 35 edges
4. `verify()` - 26 edges
5. `record()` - 24 edges
6. `detect()` - 21 edges
7. `decide()` - 20 edges
8. `get_settings()` - 19 edges
9. `get_principal()` - 19 edges
10. `App()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `3. Trust boundaries and how each is defended` --references--> `session_for()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/db/session.py
- `6. Audit ledger` --references--> `verify()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/audit/service.py
- `7. Cross-bureau visibility without leaking content` --references--> `lookup()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/modules/institutions/service.py
- `Tamper demonstration` --references--> `verify()`  [INFERRED]
  docs/RUNBOOK.md → backend/app/audit/service.py
- `Non-negotiable rules` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py

## Import Cycles
- None detected.

## Communities (118 total, 42 thin omitted)

### Community 0 - "test_dashboard.py"
Cohesion: 0.36
Nodes (8): get_settings(), counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data(), test_cross_bureau_numbers_are_the_same_for_everyone(), test_every_role_gets_the_dashboard()

### Community 1 - "test_seed.py"
Cohesion: 0.17
Nodes (11): cross_bureau_pairs(), deadlocks(), duplicate_pairs(), not_closed(), silent(), spikes(), tagged(), test_expected_detections() (+3 more)

### Community 2 - "complaints/service.py"
Cohesion: 0.09
Nodes (30): _all(), bureaus(), case_counts(), ensure_user(), exists(), find(), history(), insert_action() (+22 more)

### Community 3 - "test_search.py"
Cohesion: 0.21
Nodes (7): search(), find(), hits(), test_bureau_a_never_sees_bureau_b_text_through_search(), test_cases_by_reference_and_metadata_across_bureaus(), test_institutions_by_name_alias_initials_and_city(), test_own_bureau_text_is_searched()

### Community 4 - "institutions/repo.py"
Cohesion: 0.07
Nodes (33): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+25 more)

### Community 5 - "alerts/repo.py"
Cohesion: 0.06
Nodes (19): decide(), list_alerts(), _all(), claim_next(), decide(), delivered_to(), known_addresses(), listing() (+11 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.10
Nodes (17): alert_row(), approved(), audit_count(), closed_port(), deliver(), FakeSMTP, held(), kinds() (+9 more)

### Community 7 - "backend"
Cohesion: 0.11
Nodes (18): build, cap_drop, deploy, networks, read_only, restart, security_opt, tmpfs (+10 more)

### Community 8 - "audit_view/repo.py"
Cohesion: 0.15
Nodes (7): list_entries(), verify(), actions(), entries(), entry(), entries(), verify()

### Community 9 - "session_for"
Cohesion: 0.13
Nodes (20): ChainStatus, verify(), apply_context(), get_engine(), session_for(), verify_chain(), _append(), test_actor_comes_from_the_session_not_the_caller() (+12 more)

### Community 10 - "complaints/api.py"
Cohesion: 0.09
Nodes (18): blank_to_none(), act(), assignees(), case(), institution_timeline(), list_cases(), options(), _run() (+10 more)

### Community 11 - "package.json"
Cohesion: 0.10
Nodes (23): react-dom, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, dependencies, react@^18.3.1 (+15 more)

### Community 12 - "options"
Cohesion: 0.19
Nodes (15): logging, logging, driver, options, logging, max-file, max-size, logging (+7 more)

### Community 13 - "CaseDetail.tsx"
Cohesion: 0.19
Nodes (19): ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters, History(), unacknowledged() (+11 more)

### Community 14 - "useLoad"
Cohesion: 0.15
Nodes (23): useLoad(), App(), AlertsPage(), InstitutionTimeline(), DnaPanel(), pct(), TREND, InstitutionList() (+15 more)

### Community 15 - "test_config.py"
Cohesion: 0.20
Nodes (9): refused(), settings(), _shell(), test_a_complete_production_configuration_starts(), test_all_problems_are_reported_at_once(), test_dev_and_test_keep_working_with_dev_values(), test_each_unsafe_value_is_refused_by_name(), test_the_demo_user_import_refuses_production() (+1 more)

### Community 16 - "dashboard/repo.py"
Cohesion: 0.20
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 17 - "Principal"
Cohesion: 0.25
Nodes (17): Principal, _count(), _refs(), test_a_bureau_can_only_hand_a_case_over_as_itself(), test_a_bureau_cannot_read_links_or_alerts_it_is_not_party_to(), test_auditor_cannot_modify_complaints(), test_case_action_history_cannot_be_edited(), test_findings_are_read_by_the_bureaus_involved_and_written_by_the_detector() (+9 more)

### Community 18 - "test_overlaps.py"
Cohesion: 0.23
Nodes (12): detected(), scalar(), suggested_pairs(), test_api_decisions_detection_and_the_overlapping_filter(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs(), test_negative_cases_are_never_flagged() (+4 more)

### Community 19 - "postgres"
Cohesion: 0.11
Nodes (18): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+10 more)

### Community 20 - "export"
Cohesion: 0.39
Nodes (3): _check(), export(), report()

### Community 21 - "overlaps/service.py"
Cohesion: 0.05
Nodes (36): decide(), detect(), list_links(), tier1(), _all(), decide(), head_emails(), insert_alert() (+28 more)

### Community 22 - "web"
Cohesion: 0.15
Nodes (13): condition, backend, web, build, cap_drop, depends_on, networks, ports (+5 more)

### Community 23 - "test_findings.py"
Cohesion: 0.17
Nodes (17): cell(), detected(), findings_as(), hop(), test_a_second_run_adds_nothing(), test_a_spike_that_comes_back_is_reopened_with_its_new_counts(), test_an_acknowledgement_or_any_action_breaks_the_loop(), test_dismiss_reopen_and_resolve_are_audited_and_limited() (+9 more)

### Community 24 - "demo-users"
Cohesion: 0.14
Nodes (14): cap_drop, depends_on, entrypoint, image, networks, profiles, read_only, restart (+6 more)

### Community 25 - "Runbook"
Cohesion: 0.09
Nodes (22): 1. First start, 2. Daily use, 3. Database, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, 7. Production, Alert mail (dev and demo) (+14 more)

### Community 26 - "Architecture"
Cohesion: 0.15
Nodes (12): 10. Scaling path (after the hackathon), 11. What has been verified, 1. Shape, 2. Components, 3. Trust boundaries and how each is defended, 4. Request flow (example: approve an overlap link), 5. Processing pipeline (worker), 6. Audit ledger (+4 more)

### Community 27 - "x-backend-env"
Cohesion: 0.13
Nodes (15): x-backend-env, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_DATABASE_URL, SETHU_DEBUG, SETHU_ENVIRONMENT, SETHU_OIDC_AUDIENCE, SETHU_OIDC_ISSUER (+7 more)

### Community 28 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 29 - "environment"
Cohesion: 0.17
Nodes (12): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_BOOTSTRAP_ADMIN_USERNAME, KC_DB, KC_DB_PASSWORD, KC_DB_URL, KC_DB_USERNAME, KC_HEALTH_ENABLED, KC_HOSTNAME (+4 more)

### Community 30 - "config.py"
Cohesion: 0.21
Nodes (3): production_problems(), Settings, _weak()

### Community 31 - "test_findings.py"
Cohesion: 0.19
Nodes (11): normalize(), scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_normalize_expands_abbreviations(), test_officer_picks_from_the_queue() (+3 more)

### Community 32 - "redis"
Cohesion: 0.17
Nodes (12): REDIS_PASSWORD, cap_add, cap_drop, command, environment, image, networks, read_only (+4 more)

### Community 33 - "keycloak"
Cohesion: 0.17
Nodes (12): postgres, cap_drop, command, depends_on, image, networks, restart, security_opt (+4 more)

### Community 34 - "load.py"
Cohesion: 0.15
Nodes (6): test_keycloak_demo_logins_match_the_seed(), insert(), load(), ProductionRefused, rows(), user_id()

### Community 35 - "findings/service.py"
Cohesion: 0.05
Nodes (37): record(), decide(), detect(), list_findings(), trend(), _all(), bureau_codes(), bureau_queues() (+29 more)

### Community 36 - "services"
Cohesion: 0.06
Nodes (41): condition, environment, environment, profiles, backend, keycloak, KC_HOSTNAME, KC_HOSTNAME_ADMIN (+33 more)

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
Cohesion: 0.16
Nodes (15): api(), Alert, AlertCard(), decide(), AlertPage, moment(), STATUS, BANNER (+7 more)

### Community 41 - "conftest.py"
Cohesion: 0.29
Nodes (5): app_engine(), clean_db(), owner_engine(), world(), person()

### Community 42 - "reports/service.py"
Cohesion: 0.29
Nodes (3): _cell(), export(), run()

### Community 43 - "generate.py"
Cohesion: 0.29
Nodes (4): test_export_is_csv_without_text_and_is_audited(), test_files_are_what_the_generator_produces(), render(), variant()

### Community 44 - "api.ts"
Cohesion: 0.17
Nodes (17): react, download(), accessToken(), base64url(), login(), logout(), redirectUri(), requestTokens() (+9 more)

### Community 45 - "healthcheck"
Cohesion: 0.49
Nodes (10): interval, retries, start_period, test, timeout, healthcheck, healthcheck, healthcheck (+2 more)

### Community 46 - "reports/service.py"
Cohesion: 0.26
Nodes (6): create_app(), _all(), bureaus(), _in_range(), institutions(), overlaps()

### Community 47 - "services"
Cohesion: 0.10
Nodes (20): internal, internal, cap_drop, image, logging, networks, ports, profiles (+12 more)

### Community 48 - "Architecture Decision Records"
Cohesion: 0.22
Nodes (8): 0001. Modular monolith, not microservices, 0002. Enforce access in the database with Row-Level Security, 0003. Hash-chained audit log inside PostgreSQL, not a blockchain, 0004. Transactional outbox for alerts, 0005. Local models only, each with a deterministic fallback, 0006. Object storage deferred, 0007. Keycloak for identity, Architecture Decision Records

### Community 49 - "Architecture Snapshot"
Cohesion: 0.22
Nodes (8): Architecture Pattern, Architecture Snapshot, Critical Modules, Dependency Rules, Entry Points, Extraction Quality, Repository Map, Routes

### Community 50 - "App.tsx"
Cohesion: 0.20
Nodes (9): CAN_AUDIT, CAN_DECIDE, CAN_RESOLVE, Me, useHashRoute(), ComplaintHit, InstitutionHit, Results (+1 more)

### Community 51 - "migrate"
Cohesion: 0.20
Nodes (10): MIGRATION_DATABASE_URL, build, cap_drop, command, environment, networks, read_only, restart (+2 more)

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

### Community 58 - "worker"
Cohesion: 0.14
Nodes (15): depends_on, migrate, redis, condition, condition, worker, build, cap_drop (+7 more)

### Community 59 - "05. Next Claude Code Prompts"
Cohesion: 0.33
Nodes (5): 05. Next Claude Code Prompts, After that, in this order, Prompt 1: bring the stack up, Prompt 2: mock data, Prompt 3: first feature (institutions and resolution)

### Community 62 - "postgres"
Cohesion: 0.40
Nodes (4): networks, ports, services, postgres

### Community 67 - "import.sh"
Cohesion: 1.00
Nodes (3): kcadm(), login(), import.sh script

### Community 68 - "SETHU"
Cohesion: 0.50
Nodes (3): Quick start (Windows, PowerShell), SETHU, What is here

### Community 78 - "test_filters.py"
Cohesion: 0.15
Nodes (11): AuthError, decode_token(), _jwks_client(), principal_from_claims(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins(), test_me_and_role_gate() (+3 more)

### Community 79 - "environment"
Cohesion: 0.17
Nodes (20): environment, environment, DEMO_USER_PASSWORD, KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_ADMIN_USER, SETHU_BOTTLENECK_MIN_OPEN, SETHU_BOTTLENECK_SHARE, SETHU_DATABASE_URL (+12 more)

### Community 83 - "dashboard/schemas.py"
Cohesion: 0.36
Nodes (6): Attention, Count, OverdueCase, Overview, Totals, Week

### Community 84 - "test_audit_view.py"
Cohesion: 0.31
Nodes (4): client(), test_newest_first_with_filters(), test_only_auditor_oversight_and_admin_read_the_ledger(), test_verify_names_a_corrupted_row_and_restoring_it_heals_the_chain()

### Community 85 - "audit_view/schemas.py"
Cohesion: 0.47
Nodes (3): ChainReport, Entry, EntryPage

### Community 87 - "overlaps/schemas.py"
Cohesion: 0.36
Nodes (6): DecisionIn, DetectOut, Link, LinkedCase, Tier1Case, Tier1Institution

### Community 88 - "test_reports.py"
Cohesion: 0.22
Nodes (7): client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_institution_report_counts_only_the_callers_cases(), test_overlap_outcomes(), test_viewing_is_not_audited_and_bad_names_are_refused()

### Community 89 - "institutions/schemas.py"
Cohesion: 0.12
Nodes (22): DecisionIn, DetectOut, Finding, Trend, TrendRow, Alias, BureauCount, Candidate (+14 more)

### Community 90 - "Findings.tsx"
Cohesion: 0.18
Nodes (15): day(), Finding, FindingsPage(), KIND, numbers(), pct(), spikeWindow(), Target() (+7 more)

### Community 93 - "Production readiness"
Cohesion: 0.50
Nodes (3): Gaps, Phases (proposed), Production readiness

### Community 96 - "build"
Cohesion: 0.26
Nodes (9): build(), add(), act(), assign(), close(), transfer(), details(), fresh() (+1 more)

### Community 101 - "routes.py"
Cohesion: 0.28
Nodes (4): live(), me(), ready(), get_principal()

### Community 106 - "pydantic"
Cohesion: 0.21
Nodes (5): Alert, AlertPage, DecisionIn, Column, Report

### Community 111 - "Seed data"
Cohesion: 0.40
Nodes (4): Files, Negative cases: no alert expected, Seed data, What the loader does

## Knowledge Gaps
- **1 isolated node(s):** `sethu-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 624 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **42 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `complaints/service.py`, `institutions/repo.py`, `alerts/repo.py`, `test_alerts.py`, `audit_view/repo.py`, `session_for`, `complaints/api.py`, `test_overlaps.py`, `export`, `overlaps/service.py`, `test_findings.py`, `findings/service.py`, `conftest.py`, `reports/service.py`, `auth.py`, `findings/service.py`, `test_filters.py`, `test_audit_view.py`, `routes.py`, `complaints/service.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sethu-backend` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `complaints/service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08853410740203194 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `test_dashboard.py`, `test_seed.py`, `test_search.py`, `alerts/repo.py`, `test_alerts.py`, `Principal`, `test_overlaps.py`, `overlaps/service.py`, `test_findings.py`, `Architecture`, `test_findings.py`, `load.py`, `conftest.py`, `generate.py`, `auth.py`, `test_filters.py`, `linked`, `test_reports.py`, `routes.py`, `complaints/service.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `institutions/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06845238095238096 - nodes in this community are weakly interconnected._