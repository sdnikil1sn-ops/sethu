# 04. Mock Data Spec

Rule: every record is synthetic. Do not paste real complaints, names, emails or phone numbers anywhere in the repo.

## Volume
- 40 institutions across 6 states (fictional names, plausible cities)
- 300 complaints over the last 180 days
- 2 bureaus (PGRC, RB), with 3 desks inside RB
- 12 officers, 3 bureau heads, 1 oversight, 1 admin, 1 auditor

## Fixed demo records (do not randomise)
Greenfield Institute of Technology, Pune, Maharashtra. Aliases: "Greenfield Inst. of Tech., Pune", "GIT Pune", "Greenfield Institute of Tech".
Cases C-101, C-102, C-103 exactly as in `03-DEMO-STORY.md`.

## Deliberate patterns to seed
| Pattern | Count | Purpose |
|---|---|---|
| Same institution, two bureaus, same category (Tier 2 overlap) | 6 pairs (one is the demo pair) | Overlap detection |
| Same institution, two bureaus, different category (Tier 1 only) | 10 pairs | Shows Tier 1 without a false Tier 2 |
| Exact duplicate text | 5 pairs | Duplicate detection |
| Institution name variants (abbreviations, typos, missing city) | 40 | Resolution cascade |
| Transfer loop (PGRC to RB to PGRC, no acknowledgement) | 1 (C-090) | Deadlock |
| Silent case (no action for 30+ days) | 8 | Bottleneck |
| Regional spike: "fee refund" complaints in one state, 4x the baseline in the last 3 weeks | 1 | Early warning |
| Hindi complaints | 15 | Translation (Tier C) |
| Overdue cases (past 21 days) | 25 | Dashboard, SLA |

## Negative cases (must NOT be flagged)
- Two cases in different states with similar text and different institutions
- Same institution, same bureau (not cross-bureau)
- Same category at different institutions

## Files to generate
- `seed/institutions.csv`
- `seed/complaints.csv`
- `seed/actions.csv` (assignments, transfers, replies)
- `seed/users.csv` (fake names, `@sethu.test` emails only)
- `seed/README.md` describing each seeded pattern and the expected detection result

## Expected detections (used by tests)
- Overlap alerts: 6 Tier 2 pairs
- Duplicates: 5
- Deadlock: 1 (C-090)
- Silent cases: 8
- Early warning: 1 region and category
- Zero alerts on the negative cases

Generation must be deterministic (fixed random seed) so tests and the demo are repeatable.
