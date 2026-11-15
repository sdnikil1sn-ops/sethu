# 03. Demo Story: "Institution A"

All names and cases are fictional. Total running time: about 5 minutes. One story, one thread.

## The story in one line
Two bureaus are quietly investigating the same college. Today neither knows. SETHU tells them, and proves it.

## Characters (fictional)
- Institution A: **Greenfield Institute of Technology**, Pune, Maharashtra
- Bureau 1: **PGRC** (Public Grievance Redressal Cell)
- Bureau 2: **RB** (Regional Bureau, Western region)
- Officer: **Ms. Rao** (PGRC officer)
- Bureau Head: **Mr. Iyer** (RB head)

## Seeded facts
| Case | Bureau | Filed | Institution name as typed | Category | Summary |
|---|---|---|---|---|---|
| C-101 | PGRC | 12 days ago | Greenfield Institute of Technology | Faculty shortage | Students say required faculty posts are vacant |
| C-102 | RB | 6 days ago | Greenfield Inst. of Tech., Pune | Faculty shortage | Parent says the college shows more faculty than it has |
| C-103 | PGRC | 3 days ago | GIT Pune | Fee refund | Refund pending for a withdrawn student |

C-103 shows the institution link across name variants. C-101 and C-102 are the overlap.

## Script

**0:00 Problem (30 s)**
"Today the PGRC and the Regional Bureau each hold complaints about the same college, in separate systems. Nobody sees the whole picture."

**0:30 Complaints arrive (30 s)**
- Show the intake screen with the three cases arriving from the two source adapters.
- Point out that all three typed the institution name differently.

**1:00 Institution resolved (30 s)**
- Search "GIT Pune". It opens the Greenfield profile.
- Say: "Three spellings, one institution, matched without a person doing it."

**1:30 Overlap detected (60 s)**
- Dashboard shows a new alert: "Potential Overlapping Cases – Coordination Required".
- Open it. Show C-101 and C-102 side by side with the reason: same institution, same category, 6 days apart, similar text.
- Ms. Rao clicks **Approve link**. (Human approval.)

**2:30 Alert goes out (30 s)**
- The email outbox shows the alert to Mr. Iyer and the PGRC head.
- Open the mail catcher and show the delivered email.

**3:00 Graph and DNA (45 s)**
- Open the institution graph: two bureaus, three cases, the approved overlap in red.
- Show the Profile DNA panel: category mix, recurrence, disposal time, bureaus involved.

**3:45 Bottleneck (30 s)**
- Open the transfer view. A separate seeded case (C-090) bounced PGRC to RB to PGRC with nobody acknowledging.
- SETHU flags "Bottleneck detected: transfer loop".

**4:15 Audit proof (30 s)**
- Open the audit log. Show the approval, the alert and the export as chained entries.
- Click **Verify chain**: OK.
- (If time allows) edit one row in the database, click again: it fails and names the row.

**4:45 Close (15 s)**
"Nothing left this machine. Wi-Fi is off. Every action is on the record."

## Cut list if the demo runs long
Cut in this order: tamper test, DNA panel, bottleneck. Never cut: resolution, overlap, approval, email, audit verify.

## Rehearsal checklist
- [ ] Runs clean from a fresh `docker compose up` and a reseed
- [ ] Full run under 5 minutes, twice in a row
- [ ] Wi-Fi off run
- [ ] A backup screen recording exists
- [ ] Two people can run the demo (not just one)
