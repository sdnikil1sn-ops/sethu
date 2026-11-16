# Graph Report - jolly-feynman-1a9f96  (2026-11-16)

## Corpus Check
- 124 files · ~51,583 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 8, .csv 4, .conf 2)

## Summary
- 1219 nodes · 2567 edges · 87 communities (66 shown, 21 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 68 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0b3016cf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- overlaps/service.py
- test_seed.py
- complaints/service.py
- institutions/schemas.py
- institutions/repo.py
- alerts/repo.py
- test_alerts.py
- backend
- record
- session_for
- complaints/api.py
- package.json
- options
- CaseDetail.tsx
- useLoad
- test_auth_and_api.py
- dashboard/repo.py
- Principal
- test_overlaps.py
- postgres
- export
- auth.py
- web
- test_reports.py
- demo-users
- Runbook
- load.py
- Architecture
- compilerOptions
- session.py
- test_search.py
- test_institutions.py
- networks
- keycloak
- environment
- redis
- services
- 01. Scope Lock
- 02. PS Coverage Checklist (SIH26264)
- AuditLog.tsx
- Overlaps.tsx
- conftest.py
- resources
- migrate
- api.ts
- test_audit_view.py
- reports/service.py
- x-backend-env
- Architecture Decision Records
- Architecture Snapshot
- App.tsx
- build
- Dashboard.tsx
- test_dashboard.py
- 03. Demo Story: "Institution A"
- 04. Mock Data Spec
- Data Model
- Security
- worker
- 05. Next Claude Code Prompts
- env.py
- linked
- postgres
- import.sh
- SETHU
- .claude/CLAUDE.md
- 01-roles.sh
- sethu-backend
- environment
- generate.py
- mailpit
- logging.py
- pathlib
- Seed data
- client

## God Nodes (most connected - your core abstractions)
1. `Principal` - 94 edges
2. `session_for()` - 90 edges
3. `useLoad()` - 31 edges
4. `verify()` - 26 edges
5. `record()` - 22 edges
6. `decide()` - 19 edges
7. `get_principal()` - 17 edges
8. `act()` - 16 edges
9. `App()` - 16 edges
10. `get_settings()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `3. Trust boundaries and how each is defended` --references--> `session_for()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/db/session.py
- `6. Audit ledger` --references--> `verify()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/audit/service.py
- `Tamper demonstration` --references--> `verify()`  [INFERRED]
  docs/RUNBOOK.md → backend/app/audit/service.py
- `Non-negotiable rules` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py
- `Working agreements` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py

## Import Cycles
- None detected.

## Communities (87 total, 21 thin omitted)

### Community 0 - "overlaps/service.py"
Cohesion: 0.08
Nodes (26): decide(), detect(), list_links(), tier1(), _all(), decide(), head_emails(), insert_alert() (+18 more)

### Community 1 - "test_seed.py"
Cohesion: 0.17
Nodes (12): cross_bureau_pairs(), deadlocks(), duplicate_pairs(), not_closed(), silent(), spikes(), tagged(), tagged_pairs() (+4 more)

### Community 2 - "complaints/service.py"
Cohesion: 0.10
Nodes (29): _all(), bureaus(), case_counts(), ensure_user(), exists(), find(), history(), insert_action() (+21 more)

### Community 3 - "institutions/schemas.py"
Cohesion: 0.05
Nodes (34): Alert, AlertPage, DecisionIn, ChainReport, Entry, EntryPage, Attention, Count (+26 more)

### Community 4 - "institutions/repo.py"
Cohesion: 0.09
Nodes (27): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+19 more)

### Community 5 - "alerts/repo.py"
Cohesion: 0.07
Nodes (18): decide(), list_alerts(), _all(), claim_next(), decide(), delivered_to(), known_addresses(), listing() (+10 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.12
Nodes (14): alert_row(), audit_count(), closed_port(), deliver(), FakeSMTP, kinds(), relay(), SMTPSession (+6 more)

### Community 7 - "backend"
Cohesion: 0.15
Nodes (14): build, cap_drop, depends_on, networks, read_only, restart, security_opt, tmpfs (+6 more)

### Community 8 - "record"
Cohesion: 0.07
Nodes (17): record(), list_entries(), verify(), actions(), entries(), entry(), entries(), verify() (+9 more)

### Community 9 - "session_for"
Cohesion: 0.13
Nodes (21): ChainStatus, verify(), apply_context(), get_engine(), session_for(), verify_chain(), test_heads_of_a_concerned_bureau_and_oversight_approve_held_alerts(), _append() (+13 more)

### Community 10 - "complaints/api.py"
Cohesion: 0.15
Nodes (17): act(), assignees(), case(), institution_timeline(), list_cases(), options(), _run(), Action (+9 more)

### Community 11 - "package.json"
Cohesion: 0.10
Nodes (23): react-dom, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, dependencies, react@^18.3.1 (+15 more)

### Community 12 - "options"
Cohesion: 0.19
Nodes (15): logging, logging, driver, options, logging, max-file, max-size, logging (+7 more)

### Community 13 - "CaseDetail.tsx"
Cohesion: 0.18
Nodes (21): App(), ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters, History() (+13 more)

### Community 14 - "useLoad"
Cohesion: 0.22
Nodes (16): useLoad(), InstitutionTimeline(), InstitutionList(), InstitutionProfile(), ResolutionQueue(), Candidate, CaseSummary, day() (+8 more)

### Community 15 - "test_auth_and_api.py"
Cohesion: 0.15
Nodes (11): AuthError, decode_token(), _jwks_client(), principal_from_claims(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins(), test_me_and_role_gate() (+3 more)

### Community 16 - "dashboard/repo.py"
Cohesion: 0.20
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 17 - "Principal"
Cohesion: 0.26
Nodes (16): Principal, _count(), _refs(), test_a_bureau_can_only_hand_a_case_over_as_itself(), test_a_bureau_cannot_read_links_or_alerts_it_is_not_party_to(), test_auditor_cannot_modify_complaints(), test_case_action_history_cannot_be_edited(), test_no_request_context_sees_nothing() (+8 more)

### Community 18 - "test_overlaps.py"
Cohesion: 0.16
Nodes (13): OverlapError, detected(), scalar(), suggested_pairs(), tagged_pairs(), test_api_decisions_detection_and_the_overlapping_filter(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2() (+5 more)

### Community 19 - "postgres"
Cohesion: 0.10
Nodes (23): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+15 more)

### Community 20 - "export"
Cohesion: 0.16
Nodes (8): live(), me(), ready(), export(), report(), _cell(), export(), run()

### Community 21 - "auth.py"
Cohesion: 0.25
Nodes (4): require_roles(), configure_logging(), get_session(), create_app()

### Community 22 - "web"
Cohesion: 0.12
Nodes (16): condition, depends_on, backend, keycloak, condition, web, build, cap_drop (+8 more)

### Community 23 - "test_reports.py"
Cohesion: 0.17
Nodes (5): get_principal(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_institution_report_counts_only_the_callers_cases()

### Community 24 - "demo-users"
Cohesion: 0.13
Nodes (15): cap_drop, entrypoint, environment, image, networks, profiles, read_only, restart (+7 more)

### Community 25 - "Runbook"
Cohesion: 0.12
Nodes (15): 1. First start, 2. Daily use, 3. Database, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, 7. Production differences, Alert mail (dev and demo) (+7 more)

### Community 26 - "load.py"
Cohesion: 0.17
Nodes (4): test_keycloak_demo_logins_match_the_seed(), load(), rows(), user_id()

### Community 27 - "Architecture"
Cohesion: 0.15
Nodes (12): 10. Scaling path (after the hackathon), 11. What has been verified, 1. Shape, 2. Components, 3. Trust boundaries and how each is defended, 4. Request flow (example: approve an overlap link), 5. Processing pipeline (worker), 6. Audit ledger (+4 more)

### Community 28 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 30 - "test_search.py"
Cohesion: 0.14
Nodes (8): search(), search(), find(), hits(), test_bureau_a_never_sees_bureau_b_text_through_search(), test_cases_by_reference_and_metadata_across_bureaus(), test_institutions_by_name_alias_initials_and_city(), test_own_bureau_text_is_searched()

### Community 31 - "test_institutions.py"
Cohesion: 0.21
Nodes (10): normalize(), scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_normalize_expands_abbreviations(), test_officer_picks_from_the_queue() (+2 more)

### Community 32 - "networks"
Cohesion: 0.33
Nodes (6): internal, internal, networks, app, data, edge

### Community 33 - "keycloak"
Cohesion: 0.15
Nodes (13): postgres, cap_drop, command, depends_on, deploy, image, networks, restart (+5 more)

### Community 34 - "environment"
Cohesion: 0.17
Nodes (12): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_BOOTSTRAP_ADMIN_USERNAME, KC_DB, KC_DB_PASSWORD, KC_DB_URL, KC_DB_USERNAME, KC_HEALTH_ENABLED, KC_HOSTNAME (+4 more)

### Community 35 - "redis"
Cohesion: 0.17
Nodes (12): REDIS_PASSWORD, cap_add, cap_drop, command, environment, image, networks, read_only (+4 more)

### Community 36 - "services"
Cohesion: 0.18
Nodes (11): environment, SETHU_ENVIRONMENT, command, services, backend, keycloak, web, worker (+3 more)

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
Cohesion: 0.14
Nodes (17): api(), Alert, AlertCard(), decide(), AlertPage, AlertsPage(), moment(), STATUS (+9 more)

### Community 41 - "conftest.py"
Cohesion: 0.29
Nodes (5): app_engine(), clean_db(), owner_engine(), world(), person()

### Community 42 - "resources"
Cohesion: 0.22
Nodes (9): deploy, deploy, resources, memory, deploy, deploy, limits, deploy (+1 more)

### Community 43 - "migrate"
Cohesion: 0.20
Nodes (10): MIGRATION_DATABASE_URL, build, cap_drop, command, environment, networks, read_only, restart (+2 more)

### Community 44 - "api.ts"
Cohesion: 0.17
Nodes (17): react, download(), accessToken(), base64url(), login(), logout(), redirectUri(), requestTokens() (+9 more)

### Community 45 - "test_audit_view.py"
Cohesion: 0.36
Nodes (4): client(), test_newest_first_with_filters(), test_only_auditor_oversight_and_admin_read_the_ledger(), test_verify_names_a_corrupted_row_and_restoring_it_heals_the_chain()

### Community 46 - "reports/service.py"
Cohesion: 0.23
Nodes (5): _all(), bureaus(), _in_range(), institutions(), overlaps()

### Community 47 - "x-backend-env"
Cohesion: 0.13
Nodes (14): name, services, volumes, pgdata, redisdata, x-backend-env, SETHU_DATABASE_URL, SETHU_ENVIRONMENT (+6 more)

### Community 48 - "Architecture Decision Records"
Cohesion: 0.22
Nodes (8): 0001. Modular monolith, not microservices, 0002. Enforce access in the database with Row-Level Security, 0003. Hash-chained audit log inside PostgreSQL, not a blockchain, 0004. Transactional outbox for alerts, 0005. Local models only, each with a deterministic fallback, 0006. Object storage deferred, 0007. Keycloak for identity, Architecture Decision Records

### Community 49 - "Architecture Snapshot"
Cohesion: 0.22
Nodes (8): Architecture Pattern, Architecture Snapshot, Critical Modules, Dependency Rules, Entry Points, Extraction Quality, Repository Map, Routes

### Community 50 - "App.tsx"
Cohesion: 0.22
Nodes (8): CAN_AUDIT, CAN_RESOLVE, Me, useHashRoute(), ComplaintHit, InstitutionHit, Results, SearchBox()

### Community 51 - "build"
Cohesion: 0.26
Nodes (10): test_files_are_what_the_generator_produces(), build(), add(), act(), assign(), close(), transfer(), details() (+2 more)

### Community 52 - "Dashboard.tsx"
Cohesion: 0.39
Nodes (8): cases(), Count, CountTable(), Dashboard(), day(), OverdueCase, Overview, Trend()

### Community 53 - "test_dashboard.py"
Cohesion: 0.38
Nodes (7): counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data(), test_cross_bureau_numbers_are_the_same_for_everyone(), test_every_role_gets_the_dashboard()

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
Cohesion: 0.18
Nodes (11): disable, worker, build, cap_drop, command, healthcheck, networks, read_only (+3 more)

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

### Community 79 - "environment"
Cohesion: 0.36
Nodes (10): environment, SETHU_DATABASE_URL, SETHU_ENVIRONMENT, SETHU_OIDC_AUDIENCE, SETHU_OIDC_ISSUER, SETHU_OIDC_JWKS_URL, SETHU_REDIS_URL, SETHU_SMTP_HOST (+2 more)

### Community 80 - "generate.py"
Cohesion: 0.33
Nodes (3): test_export_is_csv_without_text_and_is_audited(), render(), variant()

### Community 81 - "mailpit"
Cohesion: 0.22
Nodes (9): cap_drop, image, logging, networks, ports, profiles, restart, security_opt (+1 more)

### Community 84 - "Seed data"
Cohesion: 0.40
Nodes (4): Files, Negative cases: no alert expected, Seed data, What the loader does

## Knowledge Gaps
- **1 isolated node(s):** `sethu-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 507 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `overlaps/service.py`, `complaints/service.py`, `institutions/repo.py`, `alerts/repo.py`, `test_alerts.py`, `record`, `session_for`, `complaints/api.py`, `test_auth_and_api.py`, `test_overlaps.py`, `export`, `auth.py`, `test_reports.py`, `session.py`, `test_institutions.py`, `conftest.py`, `test_audit_view.py`, `reports/service.py`, `audit/service.py`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 41 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sethu-backend` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `overlaps/service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07896575821104122 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `overlaps/service.py`, `test_seed.py`, `alerts/repo.py`, `test_alerts.py`, `test_auth_and_api.py`, `Principal`, `test_overlaps.py`, `export`, `auth.py`, `test_reports.py`, `load.py`, `Architecture`, `session.py`, `test_search.py`, `test_institutions.py`, `conftest.py`, `test_dashboard.py`, `linked`, `generate.py`, `client`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `complaints/service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09796806966618288 - nodes in this community are weakly interconnected._