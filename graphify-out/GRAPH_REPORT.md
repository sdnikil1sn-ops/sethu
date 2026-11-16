# Graph Report - jolly-feynman-1a9f96  (2026-11-16)

## Corpus Check
- 111 files · ~47,458 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 8, .csv 4, .conf 2)

## Summary
- 1119 nodes · 2294 edges · 78 communities (61 shown, 17 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 69 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `de050dd0`
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
- worker
- audit/service.py
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
- auth.py
- session.py
- web
- pytest
- demo-users
- Runbook
- load.py
- Architecture
- compilerOptions
- main.py
- test_institutions.py
- services
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
- SETHU
- x-backend-env
- Architecture Decision Records
- Architecture Snapshot
- App.tsx
- api
- Dashboard.tsx
- test_dashboard.py
- 03. Demo Story: "Institution A"
- 04. Mock Data Spec
- Data Model
- Security
- healthcheck
- 05. Next Claude Code Prompts
- env.py
- linked
- postgres
- import.sh
- SETHU
- .claude/CLAUDE.md
- 01-roles.sh
- sethu-backend

## God Nodes (most connected - your core abstractions)
1. `Principal` - 88 edges
2. `session_for()` - 81 edges
3. `useLoad()` - 27 edges
4. `verify()` - 26 edges
5. `record()` - 21 edges
6. `decide()` - 18 edges
7. `act()` - 16 edges
8. `get_principal()` - 15 edges
9. `get_settings()` - 15 edges
10. `demo-users` - 15 edges

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

## Communities (78 total, 17 thin omitted)

### Community 0 - "overlaps/service.py"
Cohesion: 0.06
Nodes (28): record(), decide(), detect(), list_links(), tier1(), _all(), decide(), head_emails() (+20 more)

### Community 1 - "test_seed.py"
Cohesion: 0.05
Nodes (31): JsonFormatter, cross_bureau_pairs(), deadlocks(), duplicate_pairs(), not_closed(), silent(), spikes(), tagged() (+23 more)

### Community 2 - "complaints/service.py"
Cohesion: 0.11
Nodes (27): _all(), bureaus(), case_counts(), ensure_user(), exists(), find(), history(), insert_action() (+19 more)

### Community 3 - "institutions/schemas.py"
Cohesion: 0.07
Nodes (28): Alert, AlertPage, DecisionIn, ChainReport, Entry, EntryPage, Attention, Count (+20 more)

### Community 4 - "institutions/repo.py"
Cohesion: 0.10
Nodes (25): institution_profile(), list_institutions(), resolution_queue(), resolve(), run_resolution(), add_alias(), aliases(), _all() (+17 more)

### Community 5 - "alerts/repo.py"
Cohesion: 0.09
Nodes (15): decide(), list_alerts(), _all(), claim_next(), decide(), delivered_to(), known_addresses(), listing() (+7 more)

### Community 6 - "test_alerts.py"
Cohesion: 0.09
Nodes (18): AlertError, normalize(), alert_row(), audit_count(), closed_port(), deliver(), FakeSMTP, kinds() (+10 more)

### Community 7 - "worker"
Cohesion: 0.07
Nodes (35): build, cap_drop, depends_on, environment, networks, read_only, restart, security_opt (+27 more)

### Community 8 - "audit/service.py"
Cohesion: 0.12
Nodes (7): list_entries(), verify(), actions(), entries(), entry(), entries(), verify()

### Community 9 - "session_for"
Cohesion: 0.14
Nodes (16): ChainStatus, verify(), apply_context(), get_engine(), session_for(), detect_overlaps(), resolve_pending(), verify_chain() (+8 more)

### Community 10 - "complaints/api.py"
Cohesion: 0.15
Nodes (17): act(), assignees(), case(), institution_timeline(), list_cases(), options(), _run(), Action (+9 more)

### Community 11 - "package.json"
Cohesion: 0.10
Nodes (23): react-dom, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, dependencies, react@^18.3.1 (+15 more)

### Community 12 - "options"
Cohesion: 0.11
Nodes (24): logging, logging, driver, options, cap_drop, image, logging, networks (+16 more)

### Community 13 - "CaseDetail.tsx"
Cohesion: 0.19
Nodes (19): ActionForm(), ACTIONS, CaseDetail(), CaseList(), EMPTY, Filters, History(), unacknowledged() (+11 more)

### Community 14 - "useLoad"
Cohesion: 0.23
Nodes (15): useLoad(), InstitutionTimeline(), InstitutionList(), InstitutionProfile(), ResolutionQueue(), Candidate, CaseSummary, day() (+7 more)

### Community 15 - "test_auth_and_api.py"
Cohesion: 0.20
Nodes (9): AuthError, decode_token(), principal_from_claims(), decode(), test_bad_tokens_are_rejected(), test_highest_role_wins(), test_me_and_role_gate(), test_valid_token_maps_to_principal() (+1 more)

### Community 16 - "dashboard/repo.py"
Cohesion: 0.20
Nodes (8): overview(), _all(), by_bureau(), by_column(), overdue_cases(), pending(), weekly(), overview()

### Community 17 - "Principal"
Cohesion: 0.27
Nodes (15): Principal, _count(), _refs(), test_a_bureau_can_only_hand_a_case_over_as_itself(), test_a_bureau_cannot_read_links_or_alerts_it_is_not_party_to(), test_auditor_cannot_modify_complaints(), test_no_request_context_sees_nothing(), test_officer_cannot_write_into_another_bureau() (+7 more)

### Community 18 - "test_overlaps.py"
Cohesion: 0.21
Nodes (12): detected(), scalar(), suggested_pairs(), tagged_pairs(), test_api_decisions_detection_and_the_overlapping_filter(), test_approval_writes_link_alert_and_audit_together(), test_closed_or_far_apart_cases_are_not_tier2(), test_detector_suggests_exactly_the_six_tier2_pairs() (+4 more)

### Community 19 - "postgres"
Cohesion: 0.12
Nodes (17): KEYCLOAK_DB_PASSWORD, POSTGRES_DB, POSTGRES_INITDB_ARGS, POSTGRES_PASSWORD, POSTGRES_USER, SETHU_APP_PASSWORD, SETHU_AUDITOR_PASSWORD, SETHU_OWNER_PASSWORD (+9 more)

### Community 20 - "auth.py"
Cohesion: 0.17
Nodes (6): live(), me(), ready(), get_principal(), _jwks_client(), Settings

### Community 22 - "web"
Cohesion: 0.12
Nodes (16): condition, depends_on, backend, keycloak, condition, web, build, cap_drop (+8 more)

### Community 23 - "pytest"
Cohesion: 0.21
Nodes (8): audit_rows(), scalar(), test_every_action_is_audited_and_the_chain_verifies(), test_list_filters_search_and_institution_timeline(), test_loop_case_c090_shows_both_unacknowledged_transfers(), test_officer_cannot_read_or_change_another_bureaus_complaint(), test_transfer_and_acknowledgement_appear_in_the_history(), test_case_action_history_cannot_be_edited()

### Community 24 - "demo-users"
Cohesion: 0.13
Nodes (15): cap_drop, entrypoint, environment, image, networks, profiles, read_only, restart (+7 more)

### Community 25 - "Runbook"
Cohesion: 0.13
Nodes (14): 1. First start, 2. Daily use, 3. Database, 4. Backup and restore, 5. Reset everything (destroys data), 6. Demo day, 7. Production differences, Alert mail (dev and demo) (+6 more)

### Community 26 - "load.py"
Cohesion: 0.22
Nodes (4): insert(), load(), rows(), user_id()

### Community 27 - "Architecture"
Cohesion: 0.15
Nodes (12): 10. Scaling path (after the hackathon), 11. What has been verified, 1. Shape, 2. Components, 3. Trust boundaries and how each is defended, 4. Request flow (example: approve an overlap link), 5. Processing pipeline (worker), 6. Audit ledger (+4 more)

### Community 28 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, jsx, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 30 - "main.py"
Cohesion: 0.29
Nodes (3): get_settings(), configure_logging(), create_app()

### Community 31 - "test_institutions.py"
Cohesion: 0.30
Nodes (8): scalar(), seeded(), test_api_search_and_role_gates(), test_cascade_resolves_most_variants_and_queues_the_rest(), test_greenfield_spellings_resolve_to_one_institution(), test_officer_picks_from_the_queue(), test_profile_shows_every_bureau_without_complaint_text(), test_unknown_or_ambiguous_names_are_not_guessed()

### Community 32 - "services"
Cohesion: 0.17
Nodes (11): internal, internal, name, networks, app, data, edge, services (+3 more)

### Community 33 - "keycloak"
Cohesion: 0.17
Nodes (12): postgres, cap_drop, command, depends_on, image, networks, restart, security_opt (+4 more)

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
Cohesion: 0.21
Nodes (10): BANNER, day(), Link, LinkCard(), decide(), LinkedCase, Links(), OverlapsPage() (+2 more)

### Community 41 - "conftest.py"
Cohesion: 0.29
Nodes (5): app_engine(), clean_db(), owner_engine(), world(), person()

### Community 42 - "resources"
Cohesion: 0.20
Nodes (10): deploy, deploy, resources, deploy, memory, deploy, deploy, limits (+2 more)

### Community 43 - "migrate"
Cohesion: 0.20
Nodes (10): MIGRATION_DATABASE_URL, build, cap_drop, command, environment, networks, read_only, restart (+2 more)

### Community 44 - "api.ts"
Cohesion: 0.40
Nodes (8): accessToken(), base64url(), login(), logout(), redirectUri(), requestTokens(), start(), Tokens

### Community 45 - "test_audit_view.py"
Cohesion: 0.31
Nodes (4): client(), test_newest_first_with_filters(), test_only_auditor_oversight_and_admin_read_the_ledger(), test_verify_names_a_corrupted_row_and_restoring_it_heals_the_chain()

### Community 46 - "SETHU"
Cohesion: 0.22
Nodes (8): Commands, graphify, Layout, Non-negotiable rules, Read first, SETHU, Stack, Working agreements

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
Cohesion: 0.31
Nodes (7): react, App(), CAN_AUDIT, CAN_RESOLVE, Me, useHashRoute(), root

### Community 51 - "api"
Cohesion: 0.33
Nodes (8): api(), Alert, AlertCard(), decide(), AlertPage, AlertsPage(), moment(), STATUS

### Community 52 - "Dashboard.tsx"
Cohesion: 0.39
Nodes (8): cases(), Count, CountTable(), Dashboard(), day(), OverdueCase, Overview, Trend()

### Community 53 - "test_dashboard.py"
Cohesion: 0.46
Nodes (6): counts(), expected(), overdue(), test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(), test_counts_match_the_seeded_data(), test_every_role_gets_the_dashboard()

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

### Community 58 - "healthcheck"
Cohesion: 0.53
Nodes (6): interval, retries, test, timeout, healthcheck, healthcheck

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

## Knowledge Gaps
- **1 isolated node(s):** `sethu-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 473 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Principal` connect `Principal` to `overlaps/service.py`, `complaints/service.py`, `institutions/repo.py`, `alerts/repo.py`, `test_alerts.py`, `audit/service.py`, `session_for`, `complaints/api.py`, `conftest.py`, `test_audit_view.py`, `test_auth_and_api.py`, `test_overlaps.py`, `auth.py`, `session.py`, `alerts/service.py`, `main.py`, `test_institutions.py`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `Principal` (e.g. with `me()` and `record()`) actually correct?**
  _`Principal` has 48 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sethu-backend` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `overlaps/service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06349206349206349 - nodes in this community are weakly interconnected._
- **Why does `session_for()` connect `session_for` to `overlaps/service.py`, `test_seed.py`, `alerts/repo.py`, `test_alerts.py`, `conftest.py`, `Principal`, `test_overlaps.py`, `linked`, `auth.py`, `session.py`, `test_dashboard.py`, `pytest`, `load.py`, `Architecture`, `alerts/service.py`, `test_institutions.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `session_for()` (e.g. with `Principal` and `3. Trust boundaries and how each is defended`) actually correct?**
  _`session_for()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_seed.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05136612021857923 - nodes in this community are weakly interconnected._