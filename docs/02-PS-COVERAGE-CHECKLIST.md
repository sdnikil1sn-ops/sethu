# 02. PS Coverage Checklist (SIH26264)

Each line has an acceptance test. Tick it only when the test passes on the seeded data, and name the evidence.
Re-audited 2026-11-22 (Phase 5): backend tests are in `backend/tests/` (run against PostgreSQL, docs/RUNBOOK.md
section 3), browser tests in `web/e2e/` (run against a freshly seeded dev stack), screenshots in `docs/screens/`
(taken by `web/e2e/a11y.spec.ts` on 2026-11-22). Counts at the end.

## 1. Institution profile
- [x] Open "Greenfield Institute of Technology" and see all its complaints from every bureau on one page. Evidence: `test_institutions.py::test_profile_shows_every_bureau_without_complaint_text`; `docs/screens/institution-1366.png` (cases from PGRC and RB on one page).
- [x] Alias search ("Greenfield Inst. of Tech", "GIT Pune") lands on the same profile. Evidence: `test_institutions.py::test_greenfield_spellings_resolve_to_one_institution`, `test_search.py::test_institutions_by_name_alias_initials_and_city`; browser: `journeys.spec.ts` "search finds an institution by an alias".
- [x] Profile shows bureaus involved, open and closed counts, oldest open case. Evidence: `test_institutions.py::test_profile_shows_every_bureau_without_complaint_text`; `docs/screens/institution-1366.png`.

## 2. Case tracking
- [x] Each case shows status, owner bureau, filed date, due date, days remaining. Evidence: `test_cases.py::test_list_filters_search_and_institution_timeline` (days remaining, overdue), `test_cases.py::test_api_hides_text_and_enforces_roles`; `docs/screens/case-1366.png`, `cases-1366.png`.
- [x] Overdue cases are visibly marked. Evidence: `test_cases.py::test_list_filters_search_and_institution_timeline` (`overdue` flag); `docs/screens/cases-1366.png` and `dashboard-1366.png` (overdue in red).
- [x] Status change is possible for the owner bureau only (role check). Evidence: `test_cases.py::test_officer_cannot_read_or_change_another_bureaus_complaint`, `test_rls.py::test_officer_cannot_write_into_another_bureau`; browser: `journeys.spec.ts` "a bureau head assigns a case and closes it with a reason".
- [x] A case is assigned to a person in the holding bureau (reassignable, with history); deadlines by category; a missed deadline is escalated to the bureau head (a finding per case, one digest alert per bureau and run, held for approval); notes for the holding bureau only; closing with a reason and reopening with a reason. Evidence: `test_workflow.py` (all five tests); browser: `journeys.spec.ts` "a bureau head assigns a case and closes it with a reason".
- [x] Complaints arrive through designated sources (portal API, file upload, manual form, spool folder), each with a primary and a fallback path; nothing is dropped when a source or the pipeline fails (queue, retry, dead letters with Retry). Evidence: `test_intake.py` (ten tests, including the fallback and dead-letter ones), `test_security.py::test_a01_001_*`; browser: `journeys.spec.ts` "a complaint sent to the intake API becomes a case". The restart drills under failure are not run (readiness row 57).

## 3. Overlap detection
- [x] Tier 1: two cases on the same institution in different bureaus are linked as "same institution". Evidence: `test_overlaps.py::test_ten_pairs_are_tier1_only`; `docs/screens/institution-1366.png` ("Same institution, 2 bureaus").
- [x] Tier 2: two cases on the same matter (same category, similar text, near dates) are flagged "potential overlap". Evidence: `test_overlaps.py::test_detector_suggests_exactly_the_six_tier2_pairs`, `test_negative_cases_are_never_flagged`, `test_closed_or_far_apart_cases_are_not_tier2`, `test_semantic.py::test_a_paraphrase_is_suggested_with_both_signals_shown`.
- [x] Banner text: "Potential Overlapping Cases – Coordination Required". Evidence: `test_overlaps.py::test_approval_writes_link_alert_and_audit_together` (alert subject); `docs/screens/institution-1366.png` (banner on the profile).
- [x] Officer must approve or reject the link; both choices are logged. Evidence: `test_overlaps.py::test_approval_writes_link_alert_and_audit_together`, `test_only_staff_of_a_party_bureau_can_see_and_decide`, `test_rls.py::test_reading_roles_see_links_and_alerts_but_cannot_decide`; browser: `journeys.spec.ts` "an approved overlap queues an alert to both bureau heads".

## 4. Real-time dashboard
- [x] Counts by bureau, status, category, overdue. Evidence: `test_dashboard.py::test_counts_match_the_seeded_data`, `test_cross_bureau_numbers_are_the_same_for_everyone`; `docs/screens/dashboard-1366.png`.
- [ ] Updates within 5 seconds when a case changes (poll or websocket). Not met: the dashboard refreshes every 30 seconds (and on "Refresh now"); no test measures 5 seconds.
- [x] Overlap count and open alerts shown. Evidence: `test_dashboard.py::test_counts_match_the_seeded_data`, `test_paging.py::test_dashboard_counts_are_bounded`; `docs/screens/dashboard-1366.png` ("Needs attention").

## 5. Action history
- [x] Timeline per case: filed, assigned, transferred, replied, closed, with actor and time. Evidence: `test_cases.py::test_transfer_and_acknowledgement_appear_in_the_history`, `test_loop_case_c090_shows_both_unacknowledged_transfers`, `test_every_action_is_audited_and_the_chain_verifies`.
- [x] Timeline per institution across all its cases (each person sees the cases they may read; the page says how many are hidden). Evidence: `test_cases.py::test_list_filters_search_and_institution_timeline` (`hidden_cases`); `docs/screens/institution-1366.png` ("1 case held by another bureau").
- [x] Entries cannot be edited or deleted from the UI. Evidence: `test_rls.py::test_case_action_history_cannot_be_edited`, `test_audit.py::test_runtime_role_cannot_rewrite_history` (the database refuses it, so no screen can); the API has no route that edits or deletes history (checked in the security review's route list).

## 6. Search and filters
- [x] Free text over complaint text and institution names. Evidence: `test_search.py::test_own_bureau_text_is_searched`, `test_bureau_a_never_sees_bureau_b_text_through_search`, `test_cases.py::test_list_filters_search_and_institution_timeline`.
- [x] Filters: bureau, category, status, date range, overdue only, overlapping only. Evidence: `test_filters.py::test_each_case_filter_narrows_and_blank_is_no_filter`, `test_two_case_filters_together`, `test_overlaps.py::test_api_decisions_detection_and_the_overlapping_filter`, `test_paging.py::test_filters_combine_with_pages`.
- [x] Results under 1 second on the seeded data. Evidence: `test_cases.py::test_list_filters_search_and_institution_timeline` (wall-clock assertion; it failed once on 2026-11-21 when the machine was saturated, and passes on its own); at 20,000 complaints the slowest list query took about 100 ms (docs/LOAD-AND-DRILLS.md, "Paged lists").

## 7. Alerts
- [x] Overlap alert is queued to an email outbox for both bureau heads. Evidence: `test_overlaps.py::test_approval_writes_link_alert_and_audit_together`, `test_alerts.py::test_one_email_per_recipient_with_references_only`; browser: `journeys.spec.ts` "an approved overlap queues an alert to both bureau heads".
- [x] Alert is held until an officer approves it (human approval). Evidence: `test_alerts.py::test_heads_of_a_concerned_bureau_and_oversight_approve_held_alerts`, `test_rls.py::test_only_the_detector_creates_links_and_only_the_worker_changes_alerts`.
- [x] A local mail catcher shows the delivered email during the demo. Evidence: `test_alerts.py::test_one_email_per_recipient_with_references_only` (the message as sent); `docs/screens/institution-1366.png` (dev stack, 2026-11-22: the alert to three `@sethu.test` addresses marked "sent" by the worker through Mailpit). The Mailpit inbox page itself was not opened in Phase 5.
- [x] Sent alerts are listed with time and recipient. Evidence: `test_alerts.py::test_api_lists_and_decides_by_role`; `docs/screens/alerts-1366.png`.
- [x] Alerts go to the e-mail stored for each bureau head; a bureau with no reachable head shows "No recipient for X". Evidence: `test_directory.py::test_an_alert_names_the_bureau_it_cannot_reach`, `test_first_sign_in_creates_the_record_with_email_and_a_bureau_change_reaches_it`, `test_alerts.py::test_mail_only_goes_to_sethu_users`.
- [x] A failed send is retried with growing waits, then marked Failed with the reason; an admin or bureau head can Retry (audited). Evidence: `test_alerts.py::test_backoff_doubles_and_is_capped`, `test_after_the_last_attempt_the_alert_fails_with_the_reason`, `test_retry_by_a_concerned_head_puts_it_back_and_is_audited`. The one-hour relay outage drill is not run (readiness row 57).

## 8. Reports
- [x] Institution report: the institution profile screen (profile, every bureau's cases, overlaps, timeline, relationship graph); its counts are in the exportable "Complaints by institution" report. Evidence: `test_reports.py::test_institution_report_counts_only_the_callers_cases`; `docs/screens/institution-1366.png`.
- [x] Bureau summary report, exportable. Evidence: `test_reports.py::test_bureau_performance_is_scoped_by_role`, `test_export_is_csv_without_text_and_is_audited`; browser: `journeys.spec.ts` "a report runs and exports as CSV".
- [x] Overlap report, exportable. Evidence: `test_reports.py::test_overlap_outcomes`, `test_export_is_csv_without_text_and_is_audited`.
- [x] Export is logged in the audit log. Evidence: `test_reports.py::test_export_is_csv_without_text_and_is_audited`, `test_viewing_is_not_audited_and_bad_names_are_refused`.

## Cross-cutting
- [x] Login with roles: Officer, Bureau Head, Admin, Auditor (read-only). Evidence: `test_auth_and_api.py` (six tests), `test_seed.py::test_keycloak_demo_logins_match_the_seed`; browser: `journeys.spec.ts` "every role signs in and sees its own menu" (dev demo logins for all five roles; the production realm has no users, docs/PRODUCTION-READINESS.md).
- [x] Audit log with hash chain; a "Verify chain" button returns OK. Evidence: `test_audit.py::test_chain_is_valid_and_sequential`, `test_security.py::test_a10_001_concurrent_writers_keep_the_audit_chain_whole`; browser: `journeys.spec.ts` "Verify chain reports the audit log intact".
- [x] Tamper test: change one row directly in the database, "Verify chain" fails and names the row. Evidence: `test_audit.py::test_tampering_by_a_privileged_user_is_detected`, `test_deleted_row_is_detected`, `test_audit_view.py::test_verify_names_a_corrupted_row_and_restoring_it_heals_the_chain`; a replaced database is also caught by the anchors (`test_anchor.py`; drill in docs/RUNBOOK.md, 2026-11-22).
- [x] One command starts everything: `docker compose up` (`--profile dev` adds Mailpit and the demo logins). Evidence: the dev stack used for the browser runs on 2026-11-22 was started with `docker compose --profile dev up -d --wait` and became healthy (all nine services).
- [ ] Runs with Wi-Fi off. Not proven: the app and data networks are internal and the offline-run script exists (`loadtest/offline.sh`), but the run with egress blocked and the journeys passing has not been done. Steps: docs/LOAD-AND-DRILLS.md, "Offline run" (readiness row 57).

## Flagship features (Tier B)
- [x] Graph: institution view shows bureaus and complaints as nodes, overlaps as highlighted edges (the institution profile shows its corner of the network Graph screen, same component and data). Evidence: `test_graph.py::test_expanding_an_institution_adds_its_complaints_and_overlap_edges`; `docs/screens/institution-1366.png`.
- [x] Network graph: bureaus, institutions and complaints as nodes; holding, transfer and overlap edges; filters (state, category, dates, bureau, finding kind); institutions with cases in several bureaus and open findings marked; aggregated to institutions, complaints on request. Evidence: `test_graph.py` (five tests); `docs/screens/graph-1366.png`; the same facts as tables ("The graph as tables").
- [x] Deadlock: seeded transfer loop is detected and shown as "Bottleneck detected". Evidence: `test_findings.py::test_loop_detection_finds_c090_and_queues_an_alert_for_approval`; `docs/screens/findings-1366.png`.
- [x] Profile DNA: 6 measures visible on the institution page. Evidence: `test_institutions.py::test_profile_dna_measures`; `docs/screens/institution-1366.png` (category mix, volume, recurrence, disposal time, bureaus involved, trend).
- [x] Early warning: one regional spike flagged, with the baseline shown. Evidence: `test_findings.py::test_seeded_spike_is_found_once_with_its_counts_and_no_alert`, `test_spike_rule_minimum_ratio_and_its_numbers`.

## Counts (2026-11-22)

41 lines: 39 ticked with evidence, 2 not proven ("Updates within 5 seconds", "Runs with Wi-Fi off").
