# Graph Report - jolly-feynman-1a9f96  (2026-11-17)

## Corpus Check
- 135 files · ~59,251 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 8, .csv 4, .conf 2)

## Summary
- 1369 nodes · 2949 edges · 99 communities (79 shown, 20 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `42a299db`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Principal
- test_seed.py
- complaints/service.py
- uuid
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
- test_auth_and_api.py
- dashboard/repo.py
- Principal
- test_overlaps.py
- postgres
- routes.py
- auth.py
- web
- test_reports.py
- demo-users
- Runbook
- load.py
- Architecture
- compilerOptions
- worker.py
- alerts/service.py
- test_institutions.py
- networks
- keycloak
- environment
- findings/service.py
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
- generate.py
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
- overlaps/repo.py
- environment
- test_findings.py
- mailpit
- main.py
- datetime
- Seed data
- test_filters.py
- test_cases.py
- list_links
- institutions/schemas.py
- Findings.tsx
- dashboard/schemas.py
- overlaps/schemas.py
- SETHU
- decide
- findings/schemas.py
- add

## God Nodes (most connected - your core abstractions)
1. `session_for()` - 104 edges
2. `Principal` - 103 edges
3. `useLoad()` - 35 edges
4. `verify()` - 26 edges
5. `record()` - 24 edges
6. `decide()` - 20 edges
7. `get_principal()` - 19 edges
8. `detect()` - 18 edges
9. `get_settings()` - 17 edges
10. `App()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Tamper demonstration` --references--> `verify()`  [INFERRED]
  docs/RUNBOOK.md → backend/app/audit/service.py
- `Layout` --references--> `record()`  [INFERRED]
  CLAUDE.md → backend/app/audit/service.py
- `Non-negotiable rules` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py
- `Working agreements` --references--> `get_session()`  [INFERRED]
  CLAUDE.md → backend/app/db/session.py
- `7. Cross-bureau visibility without leaking content` --references--> `lookup()`  [INFERRED]
  docs/ARCHITECTURE.md → backend/app/modules/institutions/service.py

## Import Cycles
- None detected.

## Communities (99 total, 20 thin omitted)

### Community 0 - "Principal"
Cohesion: 0.11
Nodes (16): record(), Principal, verify(), actor_id(), _can_decide(), _cases(), decide(), detect() (+8 more)

### Community 1 - "test_seed.py"
Cohesion: 0.18
Nodes (12): cross_bureau_pairs(), deadlocks(), duplicate_pairs(), not_closed(), silent(), spikes(), tagged(), tagged_pairs() (+4 more)

### Community 2 - "complaints/service.py"
Cohesion: 0.11
Nodes (27): _all(), bureaus(), case_counts(), ensure_user(), exists(), find(), history(), insert_action() (+19 more)

### Community 3 - "uuid"
Cohesion: 0.20
Nodes (7): Alert, AlertPage, DecisionIn, ComplaintHit, ComplaintHits, InstitutionHit, Results

### Community 4 - "institutions/repo.py"
Cohesion: 0.07
Nodes (30): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+22 more)

### Community 5 - "alerts/repo.py"
Cohesion: 0.25
Nodes (7): _all(), claim_next(), decide(), delivered_to(), known_addresses(), listing(), mark()

### Community 6 - "test_alerts.py"
Cohesion: 0.10
Nodes (16): AlertError, alert_row(), audit_count(), closed_port(), deliver(), FakeSMTP, kinds(), relay() (+8 more)

### Community 7 - "backend"
Cohesion: 0.15
Nodes (14): build, cap_drop, depends_on, networks, read_only, restart, security_opt, tmpfs (+6 more)

### Community 8 - "audit_view/repo.py"
Cohesion: 0.15
Nodes (6): list_entries(), verify(), actions(), entries(), entry(), entries()

### Community 9 - "session_for"
Cohesion: 0.14
Nodes (15): ChainStatus, verify(), apply_context(), get_engine(), session_for(), _append(), test_actor_comes_from_the_session_not_the_caller(), test_chain_is_valid_and_sequential() (+7 more)

### Community 10 - "complaints/api.py"
Cohesion: 0.09
Nodes (18): blank_to_none(), act(), assignees(), case(), institution_timeline(), list_cases(), options(), _run() (+10 more)

### Community 11 - "package.json"
Cohesion: 0.10
Nodes (23): react-dom, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, dependencies, react@^18.3.1 (+15 more)

### Community 12 - "options"
Cohesion: 0.18
Nodes (16): logging, logging, driver, options, logging, logging, max-file, max-size (+8 more)

### Community 13 - "CaseDetail.tsx"
Cohesion: 0.19
Nodes (18): ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters, History(), unacknowledged() (+10 more)

### Community 14 - "useLoad"
Cohesion: 0.16
Nodes (23): useLoad(), App(), InstitutionTimeline(), CENTRE, curve(), Link, place(), RelationshipGraph() (+15 more)

### Community 15 - "test_auth_and_api.py"
Cohesion: 0.09
Nodes (17): AuthError, decode_token(), _jwks_client(), principal_from_claims(), search(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins() (+9 more)

### Community 16 - "dashboard/repo.py"
Cohesion: 0.20
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 17 - "Principal"
Cohesion: 0.20
Nodes (16): _count(), _refs(), test_a_bureau_can_only_hand_a_case_over_as_itself(), test_a_bureau_cannot_read_links_or_alerts_it_is_not_party_to(), test_auditor_cannot_modify_complaints(), test_case_action_history_cannot_be_edited(), test_findings_are_read_by_the_bureaus_involved_and_written_by_the_detector(), test_no_request_context_sees_nothing() (+8 more)

### Community 18 - "test_overlaps.py"
Cohesion: 0.16
Nodes (13): OverlapError, detected(), scalar(), suggested_pairs(), tagged_pairs(), test_api_decisions_detection_and_the_overlapping_filter(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2() (+5 more)

### Community 19 - "postgres"
Cohesion: 0.06
Nodes (36): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, REDIS_PASSWORD, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD (+28 more)

### Community 20 - "routes.py"
Cohesion: 0.38
Nodes (3): live(), me(), ready()

### Community 22 - "web"
Cohesion: 0.12
Nodes (16): condition, depends_on, backend, keycloak, condition, web, build, cap_drop (+8 more)

### Community 23 - "test_reports.py"
Cohesion: 0.21
Nodes (7): client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_export_is_csv_without_text_and_is_audited(), test_institution_report_counts_only_the_callers_cases(), test_viewing_is_not_audited_and_bad_names_are_refused()

### Community 24 - "demo-users"
Cohesion: 0.13
Nodes (15): cap_drop, entrypoint, environment, image, networks, profiles, read_only, restart (+7 more)

### Community 25 - "Runbook"
Cohesion: 0.11
Nodes (17): 1. First start, 2. Daily use, 3. Database, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, 7. Production differences, Alert mail (dev and demo) (+9 more)

### Community 26 - "load.py"
Cohesion: 0.17
Nodes (5): test_keycloak_demo_logins_match_the_seed(), insert(), load(), rows(), user_id()

### Community 27 - "Architecture"
Cohesion: 0.17
Nodes (11): 10. Scaling path (after the hackathon), 11. What has been verified, 1. Shape, 2. Components, 3. Trust boundaries and how each is defended, 4. Request flow (example: approve an overlap link), 5. Processing pipeline (worker), 7. Cross-bureau visibility without leaking content (+3 more)

### Community 28 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 29 - "worker.py"
Cohesion: 0.16
Nodes (5): deliver_alerts(), detect_findings(), detect_overlaps(), resolve_pending(), verify_chain()

### Community 30 - "alerts/service.py"
Cohesion: 0.18
Nodes (5): decide(), deliver(), listing(), _send_one(), _shape()

### Community 31 - "test_institutions.py"
Cohesion: 0.30
Nodes (8): scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_officer_picks_from_the_queue(), test_profile_shows_every_bureau_without_complaint_text(), test_unknown_or_ambiguous_names_are_not_guessed()

### Community 32 - "networks"
Cohesion: 0.33
Nodes (6): internal, internal, networks, app, data, edge

### Community 33 - "keycloak"
Cohesion: 0.17
Nodes (12): postgres, cap_drop, command, depends_on, image, networks, restart, security_opt (+4 more)

### Community 34 - "environment"
Cohesion: 0.17
Nodes (12): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_BOOTSTRAP_ADMIN_USERNAME, KC_DB, KC_DB_PASSWORD, KC_DB_URL, KC_DB_USERNAME, KC_HEALTH_ENABLED, KC_HOSTNAME (+4 more)

### Community 35 - "findings/service.py"
Cohesion: 0.07
Nodes (27): decide(), detect(), list_findings(), trend(), _all(), bureau_codes(), bureau_queues(), existing() (+19 more)

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
Cohesion: 0.16
Nodes (16): api(), Alert, AlertCard(), decide(), AlertPage, AlertsPage(), moment(), STATUS (+8 more)

### Community 41 - "conftest.py"
Cohesion: 0.18
Nodes (6): app_engine(), clean_db(), owner_engine(), world(), person(), main()

### Community 42 - "resources"
Cohesion: 0.22
Nodes (9): deploy, deploy, resources, deploy, memory, deploy, limits, deploy (+1 more)

### Community 43 - "migrate"
Cohesion: 0.20
Nodes (10): MIGRATION_DATABASE_URL, build, cap_drop, command, environment, networks, read_only, restart (+2 more)

### Community 44 - "api.ts"
Cohesion: 0.35
Nodes (9): accessToken(), base64url(), login(), logout(), redirectUri(), requestTokens(), start(), Tokens (+1 more)

### Community 45 - "test_audit_view.py"
Cohesion: 0.36
Nodes (4): client(), test_newest_first_with_filters(), test_only_auditor_oversight_and_admin_read_the_ledger(), test_verify_names_a_corrupted_row_and_restoring_it_heals_the_chain()

### Community 46 - "reports/service.py"
Cohesion: 0.12
Nodes (11): _check(), export(), report(), _all(), bureaus(), _in_range(), institutions(), overlaps() (+3 more)

### Community 47 - "x-backend-env"
Cohesion: 0.22
Nodes (9): x-backend-env, SETHU_DATABASE_URL, SETHU_ENVIRONMENT, SETHU_OIDC_AUDIENCE, SETHU_OIDC_ISSUER, SETHU_OIDC_JWKS_URL, SETHU_REDIS_URL, SETHU_SMTP_HOST (+1 more)

### Community 48 - "Architecture Decision Records"
Cohesion: 0.22
Nodes (8): 0001. Modular monolith, not microservices, 0002. Enforce access in the database with Row-Level Security, 0003. Hash-chained audit log inside PostgreSQL, not a blockchain, 0004. Transactional outbox for alerts, 0005. Local models only, each with a deterministic fallback, 0006. Object storage deferred, 0007. Keycloak for identity, Architecture Decision Records

### Community 49 - "Architecture Snapshot"
Cohesion: 0.22
Nodes (8): Architecture Pattern, Architecture Snapshot, Critical Modules, Dependency Rules, Entry Points, Extraction Quality, Repository Map, Routes

### Community 50 - "App.tsx"
Cohesion: 0.14
Nodes (18): react, download(), CAN_AUDIT, CAN_DECIDE, CAN_RESOLVE, Me, useHashRoute(), NOTES (+10 more)

### Community 51 - "generate.py"
Cohesion: 0.20
Nodes (7): test_files_are_what_the_generator_produces(), build(), details(), fresh(), two_wordings(), render(), variant()

### Community 52 - "Dashboard.tsx"
Cohesion: 0.39
Nodes (8): cases(), Count, CountTable(), Dashboard(), day(), OverdueCase, Overview, Trend()

### Community 53 - "test_dashboard.py"
Cohesion: 0.19
Nodes (10): get_principal(), get_settings(), Settings, counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data() (+2 more)

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

### Community 78 - "overlaps/repo.py"
Cohesion: 0.23
Nodes (10): _all(), decide(), head_emails(), insert_alert(), linked_case_ids(), links(), _one(), refs() (+2 more)

### Community 79 - "environment"
Cohesion: 0.36
Nodes (10): environment, SETHU_DATABASE_URL, SETHU_ENVIRONMENT, SETHU_OIDC_AUDIENCE, SETHU_OIDC_ISSUER, SETHU_OIDC_JWKS_URL, SETHU_REDIS_URL, SETHU_SMTP_HOST (+2 more)

### Community 80 - "test_findings.py"
Cohesion: 0.18
Nodes (11): detected(), findings_as(), hop(), test_a_second_run_adds_nothing(), test_an_acknowledgement_or_any_action_breaks_the_loop(), test_dismiss_reopen_and_resolve_are_audited_and_limited(), test_findings_are_scoped_to_the_bureaus_involved(), test_loop_detection_finds_c090_and_queues_an_alert_for_approval() (+3 more)

### Community 81 - "mailpit"
Cohesion: 0.14
Nodes (13): cap_drop, image, networks, ports, profiles, restart, security_opt, name (+5 more)

### Community 82 - "main.py"
Cohesion: 0.20
Nodes (4): configure_logging(), JsonFormatter, create_app(), search()

### Community 83 - "datetime"
Cohesion: 0.15
Nodes (5): ChainReport, Entry, EntryPage, Column, Report

### Community 84 - "Seed data"
Cohesion: 0.40
Nodes (4): Files, Negative cases: no alert expected, Seed data, What the loader does

### Community 85 - "test_filters.py"
Cohesion: 0.18
Nodes (11): get(), test_audit_filters_narrow_combine_and_ignore_blanks(), test_each_case_filter_narrows_and_blank_is_no_filter(), total(), test_institution_list_filters(), test_institution_search_by_city_state_initials_typo_and_permanent_id(), test_institutions_screen_and_top_bar_search_agree(), test_overlap_filters() (+3 more)

### Community 87 - "test_cases.py"
Cohesion: 0.20
Nodes (8): CaseError, audit_rows(), scalar(), test_every_action_is_audited_and_the_chain_verifies(), test_list_filters_search_and_institution_timeline(), test_loop_case_c090_shows_both_unacknowledged_transfers(), test_officer_cannot_read_or_change_another_bureaus_complaint(), test_transfer_and_acknowledgement_appear_in_the_history()

### Community 88 - "list_links"
Cohesion: 0.19
Nodes (4): decide(), detect(), list_links(), tier1()

### Community 89 - "institutions/schemas.py"
Cohesion: 0.27
Nodes (10): Alias, Candidate, CaseSummary, Institution, InstitutionRow, Profile, QueueItem, ResolveIn (+2 more)

### Community 90 - "Findings.tsx"
Cohesion: 0.25
Nodes (9): Options, day(), Finding, FindingsPage(), KIND, numbers(), pct(), Target() (+1 more)

### Community 91 - "dashboard/schemas.py"
Cohesion: 0.36
Nodes (6): Attention, Count, OverdueCase, Overview, Totals, Week

### Community 92 - "overlaps/schemas.py"
Cohesion: 0.36
Nodes (6): DecisionIn, DetectOut, Link, LinkedCase, Tier1Case, Tier1Institution

### Community 93 - "SETHU"
Cohesion: 0.22
Nodes (8): Commands, graphify, Layout, Non-negotiable rules, Read first, SETHU, Stack, Working agreements

### Community 95 - "findings/schemas.py"
Cohesion: 0.39
Nodes (5): DecisionIn, DetectOut, Finding, Trend, TrendRow

### Community 96 - "add"
Cohesion: 0.70
Nodes (5): add(), act(), assign(), close(), transfer()

## Knowledge Gaps
- **1 isolated node(s):** `sethu-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 564 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `complaints/service.py`, `institutions/repo.py`, `test_alerts.py`, `audit_view/repo.py`, `session_for`, `complaints/api.py`, `test_auth_and_api.py`, `Principal`, `test_overlaps.py`, `routes.py`, `auth.py`, `alerts/service.py`, `test_institutions.py`, `findings/service.py`, `conftest.py`, `test_audit_view.py`, `reports/service.py`, `test_dashboard.py`, `list_links`, `decide`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sethu-backend` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Principal` be split into smaller, more focused modules?**
  _Cohesion score 0.11428571428571428 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `Principal`, `test_seed.py`, `test_alerts.py`, `test_auth_and_api.py`, `Principal`, `test_overlaps.py`, `routes.py`, `auth.py`, `test_reports.py`, `load.py`, `Architecture`, `worker.py`, `alerts/service.py`, `test_institutions.py`, `conftest.py`, `test_dashboard.py`, `linked`, `test_findings.py`, `test_filters.py`, `test_cases.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `complaints/service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11378353376503238 - nodes in this community are weakly interconnected._