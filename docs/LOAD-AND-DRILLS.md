# Load test, failure drills and the offline run

Phase 5, item 3. Every number here was measured on a dev stack on one Windows 11 laptop running Docker Desktop
(WSL2), with the mock data only. They show how the system behaves and where it bends, not production capacity.

## How to run it

```powershell
# 1. A throwaway stack, seeded (docs/RUNBOOK.md); never the stack you demo from.
# 2. Bring it to 100,000 complaints (adds 2,000 mock institutions; refuses SETHU_ENVIRONMENT=prod):
docker compose run --rm --no-deps -v "${PWD}/seed:/seed:ro" backend python /seed/volume.py 100000
# 3. Run k6 on the stack's internal network (DEMO_USER_PASSWORD from .env):
docker run --rm --network sethu_app -e DEMO_USER_PASSWORD -e SETHU_PUBLIC=http://localhost:8080 -v "${PWD}/loadtest:/scripts:ro" -v "${PWD}/loadtest/out:/out" grafana/k6:0.55.0@sha256:b24f418fc99a26dd57904c952c03bfaf79462be18508acc45aafa07ff68e7df2 run /scripts/k6.js
```

`loadtest/k6.js` signs each virtual user in through Keycloak's own form (authorization code with PKCE, as the
browser does), refreshes tokens like the web client, and runs three scenarios at once:

| Scenario | What it does |
|---|---|
| officers | 50 users (the six demo people in turn), each looping over the screens with 1 to 3 seconds of think time: dashboard 15%, case list with a filter and a case 25%, search 15%, overlaps 8%, alerts 7%, findings 6%, graph (one state) 8%, institutions 6%, my cases 5%, reports 5% |
| intake | Two bursts through the intake API (key, timestamp, one-time nonce), 20 a second for 30 seconds each, a minute apart |
| detector | Queues the overlap detector once a minute (the admin's button) on top of the worker's own five-minute schedule; the findings detector runs on its schedule |

k6 talks to the backend and Keycloak inside the Compose network. Through the edge, all 50 virtual users would share
one client address and the edge's per-address limits (20 API requests a second) would be what was measured; those
limits were checked on their own in the security review.

Slow statements were collected with `log_min_duration_statement = 200` (milliseconds) on the test database.

## Status (2026-11-21): incomplete

Item 3 is **not finished**. The machine (7.7 GB RAM, with the demo stack also running) could not hold a 100,000-
complaint stack under 50 users: free memory fell to 0.3 to 0.7 GB, the test Postgres crashed and recovered once,
and the Docker daemon stopped answering. No latency figure below is a capacity result. What was found and fixed
on the way is real and tested.

## Found and fixed

| # | Found under load | Fix | Proof |
|---|---|---|---|
| L1 | The findings detector created every new finding in one transaction. At volume (about 77,000 overdue cases in the first data shape) it held the audit chain's lock for minutes, and 21 intake requests queued behind it until they timed out (500 after 46 s). | At most `SETHU_DETECT_BATCH` (500) new findings per transaction; the worker repeats until done; a finding left for the next batch is never resolved by this one. | `test_findings_are_written_in_bounded_batches`; on the stack, the lock wait went to zero with the findings still being written. |
| L2 | The overlap detector did the same for new links, and two runs (the schedule and the admin's button) ran at once and deadlocked on the same embeddings (`DeadlockDetected` in the worker log). | Same batching (strongest pairs first); a second run skips while one holds `pg_try_advisory_xact_lock`. | `test_suggestions_are_written_in_bounded_batches`, `test_a_second_overlap_run_is_skipped_while_one_is_running` |
| L3 | A relay outage of an hour turned approved alerts into `failed`: six attempts span about 31 minutes. | `SETHU_ALERT_MAX_ATTEMPTS` default 10 (about 4 hours). | Existing alert tests (they set the limit themselves); the timed drill was not run. |
| L4 | With Keycloak down, the browser got nginx's bare "502 Bad Gateway". | `/auth/` answers 502/503/504 with a plain page saying sign-in is unavailable and nothing was lost (`web/public/sign-in-unavailable.html`). | Config only; not yet checked on a stack. |
| L5 | The volume loader put 100,000 complaints on 43 institutions, 80% of them open for two years. That made 566,000 candidate pairs (54 s of database time for every overlap run) and 45,000 deadline findings, an artifact rather than a real shape. | `seed/volume.py` adds 2,000 mock institutions (30% of complaints on the 43 hot spots), and only complaints of the last 60 days are in every state; older ones are closed except a stuck 3%. | Not yet re-run on a stack. |

## Measured before the host gave out (not capacity figures)

First data shape (43 institutions, 80% open), detectors catching up, 50 users signing in over two minutes:
302 requests in 8 minutes, 49% failed, median 48 s. The slowest statements (Postgres log, 200 ms threshold):

| Statement | Count | Median | Max |
|---|---|---|---|
| Findings list (`GET /findings`, every row, about 45,000) | 5 | 11 s | 482 s |
| Case list with its total (`GET /cases` with a filter) | 5 | 102 s | 258 s |
| Overlap candidate pairs (worker) | 2 | 515 s | 515 s |
| Tier 1 pairs (`GET /overlaps/tier1`) | 5 | 14 s | 401 s |
| Dashboard counts of overlap links | 5 | 7 s | 408 s |
| Overlap list (`GET /overlaps`, every row, about 12,500) | 8 | 31 s | 243 s |
| Audit insert (waiting for the chain's lock) | 26 | 0.4 s | 39 s |

Uncontended, the overlap candidate join alone took 5.0 s and produced 566,000 pairs; with similarity computed,
54 s (EXPLAIN ANALYZE, first data shape). No index was added: nothing was measured cleanly enough to justify one.

Two lists have no limit, Findings and Overlaps; with the realistic data shape they should hold hundreds of rows,
not tens of thousands, but that is not yet measured (readiness row 56).

## Drills

| Drill | Status |
|---|---|
| Postgres restart mid-intake | Not run as a drill (`loadtest/drill_intake.py` is ready). An unplanned crash happened under memory pressure: Postgres recovered by itself; Keycloak, which was creating its schema on first start at that moment, could not resume (`idx_rev_token_on_expire already exists`) and kept restarting until its database was recreated. A first start of Keycloak is not crash-safe; an established one was not tested. |
| Redis restart | Not run |
| Worker killed mid-job | Not run |
| SMTP down for an hour | Not run (`loadtest/drill_smtp.py` is ready; see L3) |
| Disk full on the backup volume | Not run |
| Keycloak down | Not run (see L4) |
| Offline run (egress blocked, Playwright journeys) | Not run (`loadtest/offline.sh` is ready: DOCKER-USER rules on the project's bridges) |
