# 02. PS Coverage Checklist (SIH26264)

Each line has an acceptance test. Tick it only when the test passes on the seeded data.

## 1. Institution profile
- [ ] Open "Greenfield Institute of Technology" and see all its complaints from every bureau on one page
- [ ] Alias search ("Greenfield Inst. of Tech", "GIT Pune") lands on the same profile
- [ ] Profile shows bureaus involved, open and closed counts, oldest open case

## 2. Case tracking
- [ ] Each case shows status, owner bureau, filed date, due date, days remaining
- [ ] Overdue cases are visibly marked
- [ ] Status change is possible for the owner bureau only (role check)

## 3. Overlap detection
- [ ] Tier 1: two cases on the same institution in different bureaus are linked as "same institution"
- [ ] Tier 2: two cases on the same matter (same category, similar text, near dates) are flagged "potential overlap"
- [ ] Banner text: "Potential Overlapping Cases – Coordination Required"
- [ ] Officer must approve or reject the link; both choices are logged

## 4. Real-time dashboard
- [ ] Counts by bureau, status, category, overdue
- [ ] Updates within 5 seconds when a case changes (poll or websocket)
- [ ] Overlap count and open alerts shown

## 5. Action history
- [ ] Timeline per case: filed, assigned, transferred, replied, closed, with actor and time
- [ ] Timeline per institution across all its cases
- [ ] Entries cannot be edited or deleted from the UI

## 6. Search and filters
- [ ] Free text over complaint text and institution names
- [ ] Filters: bureau, category, status, date range, overdue only, overlapping only
- [ ] Results under 1 second on the seeded data

## 7. Alerts
- [ ] Overlap alert is queued to an email outbox for both bureau heads
- [ ] Alert is held until an officer approves it (human approval)
- [ ] A local mail catcher shows the delivered email during the demo
- [ ] Sent alerts are listed with time and recipient

## 8. Reports
- [ ] Institution report (profile, cases, overlaps, timeline), exportable
- [ ] Bureau summary report, exportable
- [ ] Overlap report, exportable
- [ ] Export is logged in the audit log

## Cross-cutting
- [ ] Login with roles: Officer, Bureau Head, Admin, Auditor (read-only)
- [ ] Audit log with hash chain; a "Verify chain" button returns OK
- [ ] Tamper test: change one row directly in the database, "Verify chain" fails and names the row
- [ ] One command starts everything: `docker compose up`
- [ ] Runs with Wi-Fi off

## Flagship features (Tier B)
- [ ] Graph: institution view shows bureaus and complaints as nodes, overlaps as highlighted edges
- [ ] Deadlock: seeded transfer loop is detected and shown as "Bottleneck detected"
- [ ] Profile DNA: 6 measures visible on the institution page
- [ ] Early warning: one regional spike flagged, with the baseline shown
