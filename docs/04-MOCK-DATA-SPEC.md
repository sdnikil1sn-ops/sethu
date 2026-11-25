# 04. Mock Data Spec

Rule: every record is synthetic. Do not paste real complaints, names, emails or phone numbers anywhere in the repo.

## Volume
- 43 institutions across 6 states (fictional names, plausible cities)
- 310 complaints over the last 180 days
- 4 bureaus (PGRC, RB, NRB, AB), with 3 desks inside RB; bureaus are data (`seed/bureaus.csv`)
- 16 officers, 5 bureau heads, 1 oversight, 1 admin, 1 auditor

## Fixed demo records (do not randomise)
Greenfield Institute of Technology, Pune, Maharashtra. Aliases: "Greenfield Inst. of Tech., Pune", "GIT Pune", "Greenfield Institute of Tech".
Cases C-101, C-102, C-103 exactly as in `03-DEMO-STORY.md`.

## Deliberate patterns to seed
| Pattern | Count | Purpose |
|---|---|---|
| Same institution, two bureaus, same category (Tier 2 overlap) | 7 pairs (one is the demo pair, one is RB and NRB) | Overlap detection |
| Same institution, two or three bureaus, different category (Tier 1 only) | 12 pairs (one institution has three bureaus) | Shows Tier 1 without a false Tier 2 |
| Exact duplicate text | 5 pairs | Duplicate detection |
| Institution name variants (abbreviations, typos, missing city) | 40 | Resolution cascade |
| Transfer loop (PGRC to RB to PGRC, no acknowledgement) | 1 (C-090) | Deadlock |
| Silent case (no action for 30+ days) | 8 | Bottleneck |
| Regional spike: "fee refund" complaints in one state, 4x the baseline in the last 3 weeks | 1 | Early warning (found by DBSCAN, Z-score and ratio) |
| Cross-state cluster (A4): 4 + 4 "Scholarship delay" complaints in Karnataka and Tamil Nadu within six days, tag `cluster:2` (C-311 to C-318); each state under the per-state minimum of 5 | 1 | Early warning: DBSCAN only |
| Repeated handoff loop PGRC to RB to PGRC (C-090 and the two acknowledged round trips) | 3 cases | Workflow-graph bottleneck (A4) |
| Hindi complaints | 15 | Translation (Tier C) |
| Overdue cases (past 21 days) | 25 | Dashboard, SLA |

## Negative cases (must NOT be flagged)
- Two cases in different states with similar text and different institutions
- Same institution, same bureau (not cross-bureau)
- Same category at different institutions

## Files to generate
- `seed/bureaus.csv`
- `seed/institutions.csv`
- `seed/complaints.csv`
- `seed/actions.csv` (assignments, transfers, replies)
- `seed/users.csv` (fake names, `@sethu.test` emails only)
- `seed/README.md` describing each seeded pattern and the expected detection result

## Expected detections (used by tests)
- Overlap alerts: 7 Tier 2 pairs
- Duplicates: 5
- Deadlock: 1 (C-090)
- Silent cases: 8
- Early warning: 1 region and category (findings); 2 signals (A4): Uttar Pradesh / Fee refund (DBSCAN, Z-score and
  ratio) and Karnataka + Tamil Nadu / Scholarship delay (DBSCAN only)
- Handoff loop: PGRC to RB to PGRC, 3 cases (A4 workflow graph)
- Zero alerts on the negative cases
- 318 complaints in all (310 before A4)

Generation must be deterministic (fixed random seed) so tests and the demo are repeatable.
