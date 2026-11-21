# Seed data

Synthetic data for the demo and the tests, built to `docs/04-MOCK-DATA-SPEC.md`. Every institution, person and complaint is invented. Emails end in `@sethu.test`.

```powershell
python seed/generate.py     # rewrite the CSV files (same output every time, random seed 26264)
python seed/load.py         # load them into an EMPTY database (see docs/RUNBOOK.md section 3)
```

`backend/tests/test_seed.py` fails if the committed CSV files differ from what the generator produces, or if any count below is off.

## Files

| File | Rows | Notes |
|---|---|---|
| `bureaus.csv` | 4 | PGRC, RB, NRB, AB: code and name. Bureaus are data; the application never names a code |
| `institutions.csv` | 43 | 6 states. `aliases` is `\|`-separated; only Greenfield has any |
| `users.csv` | 24 | 16 officers, 5 bureau heads (one or more per bureau), 1 oversight, 1 admin, 1 auditor. `rao`, `iyer`, `fernandes`, `menon`, `admin` and `das` are also Keycloak demo logins (docs/RUNBOOK.md). `desk` is the RB desk (`RB-D1` to `RB-D3`) |
| `complaints.csv` | 310 | `institution_pid` and `seed_tags` are the answer key and are not loaded |
| `actions.csv` | 1013 | filed, assigned, transferred, acknowledged, replied, closed, note |

Dates are stored as days before the load (`filed_days_ago`, `days_ago`), so "C-101 was filed 12 days ago" is true whenever you load. Silent and overdue counts drift as a loaded database ages: **reset and reseed before a rehearsal or the demo.**

## What the loader does

- One transaction through `session_for(SYSTEM)`. Every inserted row gets an audit entry in that transaction (`complaint.created`, `case.transferred`, ... and a final `seed.loaded`). Payloads hold references and codes, never complaint text.
- Refuses to run when `SETHU_ENVIRONMENT=prod`: mock data never goes into production.
- Refuses to run if any complaint exists. The audit log and case history are append-only, so a load cannot be undone short of a reset.
- Each assignment names the officer (`assignee`); a case in an unacknowledged transfer names the sending bureau (`transferred_from`, only C-090).
- Bureau ids are derived from the bureau code (UUIDv5), so the `bureau_id` attribute on Keycloak users stays valid after a reseed.
- Links a complaint to its institution only when the typed name is exactly the canonical name or a stored alias. The other 38 name variants are loaded `unresolved` for the resolution cascade; `institution_pid` says what the right answer is.
- `due_at` is `filed_at` plus the 21-day SLA. `complainant_enc` is left empty: there is no complainant data in the seed.

## Seeded patterns and the expected detection

`seed_tags` marks each pattern. A pair shares a tag such as `tier2:3`.

| Pattern | Tag | Count | Expected detection |
|---|---|---|---|
| Demo records C-101, C-102, C-103 at Greenfield | `demo` | 3 | One profile for three spellings; C-101 and C-102 overlap |
| Same institution, two bureaus, same category, similar wording | `tier2:N` | 7 pairs | 7 Tier 2 suggestions from `sethu.overlaps.detect` (`tier2:1` is C-101 and C-102; `tier2:7` is RB and NRB, C-301 and C-302); text similarity 0.34 to 0.62 against a threshold of 0.30 |
| Same institution, two or three bureaus, different category | `tier1:N` | 12 pairs | Tier 1 only, no Tier 2 (`tier1:10` is C-102 and C-103; `tier1:1` spans PGRC, RB and NRB, so it is three pairs) |
| Identical text filed twice at one bureau | `dup:N` | 5 pairs | 5 duplicates, by `body_sha256` |
| Typed name differs from the canonical name | `variant` | 40 | Resolved by the cascade: abbreviation, acronym with city, typo, abbreviation without city |
| C-090: PGRC to RB to PGRC, no acknowledgement | `deadlock` | 1 | 1 transfer-loop bottleneck |
| Not closed, no action for 30+ days | `silent` | 8 | 8 silent cases |
| Not closed, filed more than 21 days ago | `overdue` | 25 | 25 overdue: the 8 silent, C-090, and 16 with recent activity |
| Fee refund in Uttar Pradesh: 9 in the last 3 weeks against 15 in the 159 days before | `spike` | 1 cell | 1 early warning, about 4.5 times the baseline. No other state and category reaches 5 recent cases |
| Hindi text | `hindi` | 15 | `language = hi` |

Institutions with a cross-bureau pair hold nothing else, and every other institution's complaints all sit with one bureau. That is why the pair counts are exact.

The NRB and AB records (C-301 to C-310, and the institutions Rosemere, Sandalvale and Tealcrest) are appended after everything else, so every older record is unchanged. They are placed so that no state and category reaches 5 complaints in 30 days (no new spike), nothing is overdue, and neither new bureau holds 3 open cases (no new bottleneck). On a fresh load the detector finds the same findings as before: the C-090 loop, 4 bottlenecks (the PGRC and RB queues, Banyanmere and Jadehollow) and the Uttar Pradesh fee-refund spike. Since Phase 3 it also escalates every open case already past its deadline (about two dozen on a fresh load, each with an alert held for approval); that number grows as a loaded database ages.

## Negative cases: no alert expected

| Case | Tag | Why it must stay quiet |
|---|---|---|
| Nearly identical text, different institutions in different states | `neg-similar-text` | Different institution, and the text is not byte-identical |
| Same institution, same category, same bureau | `neg-same-bureau` | Not cross-bureau |
| Same category, two bureaus, different institutions | `neg-same-category` | Different institution |
| Transfers that were acknowledged, including two round trips and one NRB to AB handover | `transfer-ack` (8) | Not a deadlock |

`sources.csv` adds the intake sources (no API keys: an admin issues them on the Intake screen): an api source with a spool fallback for PGRC and RB, and an upload and a manual source for every bureau.
