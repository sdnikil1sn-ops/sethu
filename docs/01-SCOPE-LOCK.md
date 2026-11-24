# 01. Scope Lock

Status: DRAFT until all team members tick the sign-off box at the bottom.

## Goal in one sentence
One screen where an AICTE officer sees every complaint about an institution across all bureaus, is warned when bureaus are working the same matter, and can prove who did what and when.

## Tier A: MUST ship (the PS itself)
1. Institution profile (single view per institution)
2. Case tracking (status, owner bureau, dates, SLA clock)
3. Overlap detection (Tier 1: same institution across bureaus; Tier 2: same matter)
4. Real-time dashboard (counts by bureau, status, category, overdue)
5. Action history (every action on a case, in order)
6. Search and filters (institution, bureau, category, status, date, free text)
7. Alerts (email via outbox, to the right bureau heads)
8. Reports (summary and overlap report, PDF or CSV export)

Plus the cross-cutting must-haves: login with roles, human approval step for overlap links, hash-chained audit log.

## Tier B: SHOULD ship (the flagship features, thin but real)
| Feature | Minimum viable version for the demo |
|---|---|
| Cross-bureau intelligence graph | Cytoscape graph of one institution's complaints and bureaus; overlaps highlighted |
| Deadlock and bottleneck detection | Detect one seeded ping-pong or cycle in transfers; show as an alert |
| Institutional Complaint Profile DNA | Panel of 6 measures on the institution page (category mix, volume, recurrence, disposal time, bureaus involved, trend) |
| Early-warning | One regional category spike flagged against a trailing baseline (simple z-score is acceptable) |

## Tier C: COULD ship (only if Tier A and B are done)
- Translation of Hindi complaints (IndicTrans2 with a fallback)
- Complaint classification model
- Embedding-based Tier 2 matching (fall back to TF-IDF)
- Ollama-drafted alert text (human-approved)

## Out of scope (do not discuss again)
- Real AICTE or PGRC integrations (we use adapters that read mock files)
- Real complainant data of any kind
- Mobile app
- Blockchain (we say "hash-chained audit log")
- External AI APIs, hosted databases, or any cloud service
- Multi-tenant SaaS features, billing, public-facing pages

## Definition of done (per feature)
A feature is done only when:
1. It works on the seeded demo data end to end.
2. It has one automated test.
3. Its action is written to the audit log (where it changes data).
4. It appears in the demo script or is deliberately cut from it.

## Freeze rules
- New ideas go in a `parking-lot` list in this file, not into the build.
- Tier C starts only after the full demo script runs clean once.
- Final 12 hours before submission: bug fixes and demo rehearsal only.

## Constraints
- All data stays inside the deployment. No outbound network calls from the app at run time.
- Docker Compose must bring the whole system up with one command.
- Demo must run offline (we will switch Wi-Fi off during the demo).

## Parking lot
- A per-language trigram threshold for the overlap fallback: Hindi and Tamil complaints in one category reach 0.30
  through shared function words (docs/AI-PIPELINE.md, A3).
- Remove the unused bge-small model and fastembed from the backend image (needs the lock files regenerated).

## Sign-off
- [ ] Member 1
- [ ] Member 2
- [ ] Member 3
- [ ] Member 4
- [ ] Member 5
- [ ] Member 6
