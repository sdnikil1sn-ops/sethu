# User guide

SETHU shows every complaint about an AICTE-approved institution across all bureaus on one screen. It warns when two
bureaus are working the same matter, and keeps a hash-chained audit log of who did what and when.
Screens are shown in [screens/](screens/) at desktop (1366 px) and phone (375 px) width.

## Signing in and moving around

- Open the address your administrator gave you and sign in with your SETHU account (Keycloak). After 30 minutes without
  use you are asked to sign in again.
- The menu at the top shows only the screens your role may use. The search box at the top finds institutions (by any
  spelling, initials, city or permanent id) and cases (by reference such as C-101, or by words).
- Keyboard: Tab first reaches **Skip to main content**. Every control is reachable with Tab and shows a blue focus ring.
- Long lists (Cases, Findings, Overlaps) come a page at a time: **Previous page**, **Next page**, **Per page**. Very large
  totals show as "1,000+".
- On a phone, the case and findings lists turn each row into a card with labelled fields.
- The Cases screen keeps its filters, page and page size in the address, so you can bookmark or share a view.

What you can see is enforced by the database, not only by the screens. Complaint text and the complainant's details are
shown only to the bureau that holds the case; others see the summary (reference, bureau, institution, category, status,
dates).

## Officer

Works the cases of their own bureau.

- **My cases**: your open cases, soonest deadline first.
- **Cases**: every case in summary; your bureau's in full. Filter by bureau, category, status, institution, state,
  dates, overdue or overlapping. Open a case to see its history and act on it:
  - reply;
  - transfer to another bureau (with a reason);
  - acknowledge a case transferred to you;
  - close with a reason (resolved, no action needed, duplicate, withdrawn, outside jurisdiction);
  - reopen with a reason;
  - add a note (seen only by the bureau holding the case).

  Every action is in the history and the audit log.
- **Overlaps**: two open cases in different bureaus about the same institution and matter, in any language. Each
  suggestion explains how it was found:
  - meaning similarity by the AI model, or text similarity as the fallback;
  - the scores against their thresholds;
  - whether the two signals agree;
  - a matching confidence.

  If your bureau holds one of the two cases, decide: **Approve link** (it queues an alert to both bureau heads, which a
  head then releases) or **Not the same matter**. Both choices are recorded.
- **AI suggestions** (on a case your bureau holds): the suggested category and institution, and what produced them:
  the AI model, the fallback rules, or nobody (then you pick).
  - **Category**: **Accept** the suggested category, or **Change to** another one. To keep the category the case has,
    choose that one.
  - **Institution**: **Accept**, or **Choose this one** among the top three. If none is right, use **Unmatched names**.

  Nothing changes until you decide. Your decision is recorded, and it helps train the next classifier.
- **Intake**: enter a complaint by hand or upload a CSV or XLSX file for your bureau's sources. An upload reports each bad
  row by row number and field, and queues the good ones.
- **Unmatched names**: complaints whose institution name could not be matched automatically; pick the right institution.
- **Institutions**, **Graph**, **Findings**, **Alerts**, **Reports**: read (see below).

## Bureau head

Everything an officer can do in their bureau, and:

- **Assign** a case to an officer of the bureau (and reassign; the history keeps every assignment).
- **Workload**: open, overdue and unassigned cases per person.
- **Alerts**: alerts are held until a person releases them. For alerts that concern your bureau, choose **Approve and
  send** or **Reject**. If a send failed (the reason is shown), **Retry** it.
- **Findings**: **Dismiss** a finding that is not a real problem, or **Reopen** it. Findings include:
  - transfer loops ("Bottleneck detected");
  - stalled transfers;
  - queues where too many cases are old or overdue;
  - missed deadlines;
  - early warnings (a category in one state well above its own recent past).
- **Intake > Sources**: the health of your bureau's sources.

## Oversight

Sees every bureau's summaries and every bureau's work.

- **Dashboard**: counts by bureau, status and category, overdue cases, overlaps awaiting review, alerts awaiting
  approval and open findings. It refreshes every 30 seconds, and **Refresh now** refreshes at once.
- **Graph**: bureaus, institutions and their links; filter by state, category, bureau, dates or finding; click an
  institution and **Show its complaints**. **The graph as tables** gives the same facts as tables.
  - **Colour: by community** shows groups of bureaus and institutions linked more to each other than to the rest.
  - **Overlaps shown** hides suggested overlaps below a confidence.
  - Click a link (or **Explain** in the table) to see why two things are linked: method, confidence, model version
    and the cases behind it. A case you may not open is marked **restricted record** instead of showing its details.
- **Map and signals** (everyone; oversight and bureau heads decide): a map of India shaded by complaints, outlined
  in red where there is an **Emerging signal: requires verification**. Choose a state (on the map or in the table)
  to see its institutions (to their profiles) and its signals (to their cases). Each signal says how it was found
  (clustering in place and time, or a comparison with the recent past), its window, score and parameters.
  **Acknowledge**, **Linked to action**, or **Dismiss** with a reason; each choice is recorded.
- **Alerts** and **Findings**: decide, like a bureau head, for any bureau.
- **Reports**: complaints by institution, bureau performance and overlap outcomes, for a date range. **Export CSV**
  (the export is recorded in the audit log; complaint text is never exported).
- **Audit log**: see Auditor.

## Admin

Runs the system; does not work cases.

- **Admin > Bureaus**: create, rename, deactivate. A deactivated bureau takes no new transfers. **Admin > People**
  lists the people synced from Keycloak and flags anyone without an e-mail (alerts could not reach them). **Admin >
  Deadlines by category** sets the days to respond.
- **Intake > Sources**:
  - create a source and choose its fallback;
  - mark a source down or up, or deactivate it;
  - set its per-minute API quota;
  - **Issue / Replace API key** (shown once: hand it to the portal over a secure channel).
- **Intake > Queue**: **Retry** an item that failed its attempts (the reason is shown).
- **Overlaps**: **Look for new overlaps now** (the worker searches; the answer appears when it finishes).
- **Findings**: **Check now**.
- **AI health** (also readable by oversight):
  - the active category classifier, its accuracy on the held-out set (synthetic data: not real-world accuracy) and
    its earlier versions;
  - how many complaints have a vector of the active E5 model.

  The admin buttons: **Retrain classifier** (a new version is used only if it does no worse), **Use vN** (roll back)
  and **Re-embed now**.
- **Audit log**: see Auditor.

People and roles themselves are managed in Keycloak by the identity administrator (docs/OPERATIONS.md, section 4).

## Auditor

Read-only, across everything; cannot change any case, alert or setting.

- **Audit log**: every change made through SETHU, newest first. Filter by action, actor, target, dates.
  - **Verify chain** re-checks every entry's hash. It says "Chain intact" or names the first entry that does not match.
  - **Exported anchors** compares the chain with the hourly anchors kept outside the database. It names any entry that
    was rewritten or is missing.
  - **Failed sign-ins** lists Keycloak's records of failed logins.
- **Reports** and every reading screen.

## If something looks wrong

| You see | Means | Do |
|---|---|---|
| "Sign-in is unavailable right now" | The sign-in service is down; nothing was lost | Try again in a few minutes; tell the administrator if it lasts |
| "summary only" on a case | Another bureau holds it | Ask that bureau; transfers and overlaps are how bureaus coordinate |
| An alert "Failed" with a reason | The mail relay refused or was down for hours | A bureau head or admin presses Retry once it is fixed |
| "No recipient for X" on an alert | That bureau's head has no e-mail in Keycloak | Tell the administrator |
| "Verify chain" names an entry, or an anchor does not match | The audit log was changed outside SETHU | Do not try to fix it; tell the security officer at once (OPERATIONS.md, incident response) |
