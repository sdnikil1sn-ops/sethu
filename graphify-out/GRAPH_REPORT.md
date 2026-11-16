# Graph Report - jolly-feynman-1a9f96  (2026-11-17)

## Corpus Check
- 135 files · ~59,516 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 8, .csv 4, .conf 2)

## Summary
- 1372 nodes · 2952 edges · 101 communities (76 shown, 25 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f5e90929`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- overlaps/service.py
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
- alerts/service.py
- detect
- test_institutions.py
- redis
- keycloak
- environment
- findings/service.py
- services
- 01. Scope Lock
- 02. PS Coverage Checklist (SIH26264)
- AuditLog.tsx
- Overlaps.tsx
- sqlalchemy
- resources
- migrate
- api.ts
- healthcheck
- reports/service.py
- services
- Architecture Decision Records
- Architecture Snapshot
- App.tsx
- generate.py
- Dashboard.tsx
- pathlib
- 03. Demo Story: "Institution A"
- 04. Mock Data Spec
- Data Model
- Security
- worker
- 05. Next Claude Code Prompts
- OverlapError
- postgres
- import.sh
- SETHU
- .claude/CLAUDE.md
- 01-roles.sh
- sethu-backend
- overlaps/repo.py
- environment
- test_findings.py
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

## Communities (101 total, 25 thin omitted)

### Community 0 - "overlaps/service.py"
Cohesion: 0.22
Nodes (8): _can_decide(), _cases(), decide(), linked_case_ids(), links(), _shape(), tier1(), test_alert_status_filter()

### Community 1 - "test_seed.py"
Cohesion: 0.18
Nodes (12): cross_bureau_pairs(), deadlocks(), duplicate_pairs(), not_closed(), silent(), spikes(), tagged(), tagged_pairs() (+4 more)

### Community 2 - "complaints/service.py"
Cohesion: 0.11
Nodes (28): _all(), bureaus(), case_counts(), ensure_user(), exists(), find(), history(), insert_action() (+20 more)

### Community 3 - "uuid"
Cohesion: 0.20
Nodes (7): Alert, AlertPage, DecisionIn, ComplaintHit, ComplaintHits, InstitutionHit, Results

### Community 4 - "institutions/repo.py"
Cohesion: 0.08
Nodes (28): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+20 more)

### Community 5 - "alerts/repo.py"
Cohesion: 0.06
Nodes (20): decide(), list_alerts(), _all(), claim_next(), decide(), delivered_to(), known_addresses(), listing() (+12 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.15
Nodes (13): alert_row(), audit_count(), closed_port(), deliver(), kinds(), SMTPSession, test_a_bureau_sees_only_alerts_it_is_party_to(), test_a_failed_send_stays_approved_and_is_retried_without_duplicates() (+5 more)

### Community 7 - "backend"
Cohesion: 0.14
Nodes (15): build, cap_drop, depends_on, deploy, networks, read_only, restart, security_opt (+7 more)

### Community 8 - "audit_view/repo.py"
Cohesion: 0.14
Nodes (7): list_entries(), verify(), actions(), entries(), entry(), entries(), verify()

### Community 9 - "session_for"
Cohesion: 0.27
Nodes (9): verify(), _append(), test_actor_comes_from_the_session_not_the_caller(), test_chain_is_valid_and_sequential(), test_client_cannot_choose_seq_or_hash(), test_deleted_row_is_detected(), test_runtime_role_cannot_rewrite_history(), test_tampering_by_a_privileged_user_is_detected() (+1 more)

### Community 10 - "complaints/api.py"
Cohesion: 0.11
Nodes (18): blank_to_none(), act(), assignees(), case(), institution_timeline(), list_cases(), options(), _run() (+10 more)

### Community 11 - "package.json"
Cohesion: 0.10
Nodes (23): react-dom, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, dependencies, react@^18.3.1 (+15 more)

### Community 12 - "options"
Cohesion: 0.11
Nodes (24): logging, logging, driver, options, cap_drop, image, logging, networks (+16 more)

### Community 13 - "CaseDetail.tsx"
Cohesion: 0.19
Nodes (18): ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters, History(), unacknowledged() (+10 more)

### Community 14 - "useLoad"
Cohesion: 0.16
Nodes (23): useLoad(), App(), InstitutionTimeline(), CENTRE, curve(), Link, place(), RelationshipGraph() (+15 more)

### Community 15 - "test_auth_and_api.py"
Cohesion: 0.14
Nodes (12): AuthError, decode_token(), get_principal(), _jwks_client(), principal_from_claims(), Settings, decode(), test_bad_tokens_are_rejected() (+4 more)

### Community 16 - "dashboard/repo.py"
Cohesion: 0.20
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 17 - "Principal"
Cohesion: 0.15
Nodes (22): Principal, apply_context(), get_engine(), session_for(), _count(), linked(), _refs(), test_a_bureau_can_only_hand_a_case_over_as_itself() (+14 more)

### Community 18 - "test_overlaps.py"
Cohesion: 0.21
Nodes (12): detected(), scalar(), suggested_pairs(), tagged_pairs(), test_api_decisions_detection_and_the_overlapping_filter(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs() (+4 more)

### Community 19 - "postgres"
Cohesion: 0.12
Nodes (17): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+9 more)

### Community 20 - "routes.py"
Cohesion: 0.38
Nodes (3): live(), me(), ready()

### Community 22 - "web"
Cohesion: 0.12
Nodes (16): condition, depends_on, backend, keycloak, condition, web, build, cap_drop (+8 more)

### Community 23 - "test_reports.py"
Cohesion: 0.17
Nodes (9): detected(), client(), report(), test_bureau_performance_is_scoped_by_role(), test_date_range(), test_export_is_csv_without_text_and_is_audited(), test_institution_report_counts_only_the_callers_cases(), test_overlap_outcomes() (+1 more)

### Community 24 - "demo-users"
Cohesion: 0.13
Nodes (15): cap_drop, entrypoint, environment, image, networks, profiles, read_only, restart (+7 more)

### Community 25 - "Runbook"
Cohesion: 0.11
Nodes (17): 1. First start, 2. Daily use, 3. Database, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, 7. Production differences, Alert mail (dev and demo) (+9 more)

### Community 26 - "load.py"
Cohesion: 0.18
Nodes (5): test_keycloak_demo_logins_match_the_seed(), insert(), load(), rows(), user_id()

### Community 27 - "Architecture"
Cohesion: 0.15
Nodes (12): 10. Scaling path (after the hackathon), 11. What has been verified, 1. Shape, 2. Components, 3. Trust boundaries and how each is defended, 4. Request flow (example: approve an overlap link), 5. Processing pipeline (worker), 6. Audit ledger (+4 more)

### Community 28 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 30 - "detect"
Cohesion: 0.17
Nodes (6): detect(), approved(), FakeSMTP, held(), relay(), test_overlap_filters()

### Community 31 - "test_institutions.py"
Cohesion: 0.23
Nodes (10): normalize(), scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_normalize_expands_abbreviations(), test_officer_picks_from_the_queue() (+2 more)

### Community 32 - "redis"
Cohesion: 0.17
Nodes (12): REDIS_PASSWORD, cap_add, cap_drop, command, environment, image, networks, read_only (+4 more)

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

### Community 41 - "sqlalchemy"
Cohesion: 0.12
Nodes (11): run_migrations_online(), _url(), app_engine(), clean_db(), owner_engine(), world(), person(), client() (+3 more)

### Community 42 - "resources"
Cohesion: 0.22
Nodes (9): deploy, resources, deploy, memory, deploy, deploy, limits, deploy (+1 more)

### Community 43 - "migrate"
Cohesion: 0.20
Nodes (10): MIGRATION_DATABASE_URL, build, cap_drop, command, environment, networks, read_only, restart (+2 more)

### Community 44 - "api.ts"
Cohesion: 0.35
Nodes (9): accessToken(), base64url(), login(), logout(), redirectUri(), requestTokens(), start(), Tokens (+1 more)

### Community 45 - "healthcheck"
Cohesion: 0.53
Nodes (6): interval, retries, test, timeout, healthcheck, healthcheck

### Community 46 - "reports/service.py"
Cohesion: 0.12
Nodes (11): _check(), export(), report(), _all(), bureaus(), _in_range(), institutions(), overlaps() (+3 more)

### Community 47 - "services"
Cohesion: 0.10
Nodes (20): internal, internal, name, networks, app, data, edge, services (+12 more)

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
Cohesion: 0.08
Nodes (25): search(), board(), counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data(), test_cross_bureau_numbers_are_the_same_for_everyone() (+17 more)

### Community 82 - "main.py"
Cohesion: 0.15
Nodes (5): get_settings(), configure_logging(), JsonFormatter, create_app(), search()

### Community 83 - "datetime"
Cohesion: 0.16
Nodes (5): ChainReport, Entry, EntryPage, Column, Report

### Community 84 - "Seed data"
Cohesion: 0.40
Nodes (4): Files, Negative cases: no alert expected, Seed data, What the loader does

### Community 85 - "test_filters.py"
Cohesion: 0.19
Nodes (10): get(), test_audit_filters_narrow_combine_and_ignore_blanks(), test_each_case_filter_narrows_and_blank_is_no_filter(), total(), test_institution_list_filters(), test_institution_search_by_city_state_initials_typo_and_permanent_id(), test_institutions_screen_and_top_bar_search_agree(), test_report_dates_blank_and_reversed() (+2 more)

### Community 87 - "test_cases.py"
Cohesion: 0.21
Nodes (9): CaseError, audit_rows(), scalar(), test_every_action_is_audited_and_the_chain_verifies(), test_list_filters_search_and_institution_timeline(), test_loop_case_c090_shows_both_unacknowledged_transfers(), test_officer_cannot_read_or_change_another_bureaus_complaint(), test_transfer_and_acknowledgement_appear_in_the_history() (+1 more)

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
Cohesion: 0.15
Nodes (9): record(), Commands, graphify, Layout, Non-negotiable rules, Read first, SETHU, Stack (+1 more)

### Community 95 - "findings/schemas.py"
Cohesion: 0.39
Nodes (5): DecisionIn, DetectOut, Finding, Trend, TrendRow

### Community 96 - "add"
Cohesion: 0.70
Nodes (5): add(), act(), assign(), close(), transfer()

## Knowledge Gaps
- **1 isolated node(s):** `sethu-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 563 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `overlaps/service.py`, `complaints/service.py`, `institutions/repo.py`, `alerts/repo.py`, `test_alerts.py`, `audit_view/repo.py`, `session_for`, `complaints/api.py`, `test_auth_and_api.py`, `test_overlaps.py`, `routes.py`, `auth.py`, `alerts/service.py`, `detect`, `test_institutions.py`, `findings/service.py`, `sqlalchemy`, `reports/service.py`, `list_links`, `SETHU`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sethu-backend` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `complaints/service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1096938775510204 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `Principal` to `overlaps/service.py`, `test_seed.py`, `alerts/repo.py`, `test_alerts.py`, `sqlalchemy`, `session_for`, `test_findings.py`, `test_overlaps.py`, `routes.py`, `auth.py`, `test_filters.py`, `test_cases.py`, `test_reports.py`, `load.py`, `Architecture`, `alerts/service.py`, `detect`, `test_institutions.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `institutions/repo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07796610169491526 - nodes in this community are weakly interconnected._