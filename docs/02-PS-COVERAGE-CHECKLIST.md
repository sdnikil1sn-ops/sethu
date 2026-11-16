# 02. PS Coverage Checklist (SIH26264)

Each line has an acceptance test. Tick it only when the test passes on the seeded data.

## 1. Institution profile
- [x] Open "Greenfield Institute of Technology" and see all its complaints from every bureau on one page
- [x] Alias search ("Greenfield Inst. of Tech", "GIT Pune") lands on the same profile
- [x] Profile shows bureaus involved, open and closed counts, oldest open case

## 2. Case tracking
- [x] Each case shows status, owner bureau, filed date, due date, days remaining
- [x] Overdue cases are visibly marked
- [x] Status change is possible for the owner bureau only (role check)

## 3. Overlap detection
- [x] Tier 1: two cases on the same institution in different bureaus are linked as "same institution"
- [x] Tier 2: two cases on the same matter (same category, similar text, near dates) are flagged "potential overlap"
- [x] Banner text: "Potential Overlapping Cases – Coordination Required"
- [x] Officer must approve or reject the link; both choices are logged

## 4. Real-time dashboard
- [x] Counts by bureau, status, category, overdue
- [ ] Updates within 5 seconds when a case changes (poll or websocket)
- [x] Overlap count and open alerts shown

## 5. Action history
- [x] Timeline per case: filed, assigned, transferred, replied, closed, with actor and time
- [x] Timeline per institution across all its cases (each person sees the cases they may read; the page says how many are hidden)
- [x] Entries cannot be edited or deleted from the UI

## 6. Search and filters
- [x] Free text over complaint text and institution names
- [x] Filters: bureau, category, status, date range, overdue only, overlapping only
- [x] Results under 1 second on the seeded data

## 7. Alerts
- [x] Overlap alert is queued to an email outbox for both bureau heads
- [x] Alert is held until an officer approves it (human approval)
- [x] A local mail catcher shows the delivered email during the demo
- [x] Sent alerts are listed with time and recipient

## 8. Reports
- [x] Institution report: the institution profile screen (profile, every bureau's cases, overlaps, timeline, relationship graph); its counts are in the exportable "Complaints by institution" report
- [x] Bureau summary report, exportable
- [x] Overlap report, exportable
- [x] Export is logged in the audit log

## Cross-cutting
- [ ] Login with roles: Officer, Bureau Head, Admin, Auditor (read-only)
- [x] Audit log with hash chain; a "Verify chain" button returns OK
- [x] Tamper test: change one row directly in the database, "Verify chain" fails and names the row
- [ ] One command starts everything: `docker compose up`
- [ ] Runs with Wi-Fi off

## Flagship features (Tier B)
- [ ] Graph: institution view shows bureaus and complaints as nodes, overlaps as highlighted edges
- [x] Deadlock: seeded transfer loop is detected and shown as "Bottleneck detected"
- [ ] Profile DNA: 6 measures visible on the institution page
- [ ] Early warning: one regional spike flagged, with the baseline shown
