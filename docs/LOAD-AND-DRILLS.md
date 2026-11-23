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
| L5 | The volume loader put 100,000 complaints on 43 institutions, 80% of them open for two years. That made 566,000 candidate pairs (54 s of database time for every overlap run) and 45,000 deadline findings, an artifact rather than a real shape. | `seed/volume.py` adds 2,000 mock institutions (30% of complaints on the 43 hot spots), and only complaints of the last 60 days are in every state; older ones are closed except a stuck 3%. | At 20,000 on the test database: 1,974 open, 1,699 findings, 618 links, detectors finished in 4 s ("Paged lists"); 100,000 not re-run. |

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

Findings, Overlaps and the case list had no limit; they are paged now (see "Paged lists" below, readiness row 58).

## Paged lists (2026-11-22)

The load test's clearest application finding: Findings, Overlaps and the case list returned every row, and the case
list counted every match (`count(*) OVER ()`). All three now come a page at a time (`limit` 1 to 200, default 50;
`offset`), with `has_next` from fetching one row more, and a total counted only up to 1,000 (`total_capped`: the
screens show "1,000+"). The dashboard's counts of overlap links, alerts, open findings and overdue cases are capped
the same way; its weekly chart reads only the weeks it shows. Code: `backend/app/db/paging.py`; tests:
`backend/tests/test_paging.py` (page boundaries, totals and the cap, filters with pages, page-size bounds, role
scoping, dashboard caps).

**Measured** on the test database alone (Postgres 16 in Docker, no other stack running; the host could not hold a full
stack), 20,000 complaints in the realistic shape (443 institutions, 1,974 open, 1,699 findings, 618 overlap links after
the detectors ran), through real Row-Level Security sessions, median of 5 runs (`seed/volume.py 20000`):

| List | Oversight before | Oversight after | PGRC officer before | PGRC officer after |
|---|---|---|---|---|
| Cases, no filter | 42.8 ms | 31.1 ms | 44.8 ms | 38.3 ms |
| Cases, status open | 13.8 ms | 20.3 ms | 22.7 ms | 27.0 ms |
| Cases, text search "hostel" | 87.7 ms | 104.4 ms | 56.9 ms | 98.1 ms |
| Findings, open | 48.6 ms | 14.7 ms | 23.1 ms | 14.0 ms |
| Overlaps, proposed | 33.9 ms | 33.8 ms | 29.0 ms | 43.1 ms |
| Dashboard, pending counts | 2.0 ms | 2.2 ms | 4.4 ms | 3.7 ms |
| Dashboard, overdue list and total | 2.3 ms | 3.8 ms | 2.1 ms | 4.1 ms |
| Dashboard, weekly | 12.3 ms | 9.1 ms | 10.6 ms | 11.0 ms |
| Dashboard, whole (after only) | | 58.1 ms | | 59.4 ms |

What it shows: at this size every list answers in about 100 ms or less. Paging pays where the list is long (findings,
the unfiltered case list) and costs a few milliseconds where it is short (a second query for the count); what it
removes is the growth: a page and a count that stops at 1,001 rows do not grow with the table, an unbounded list does.

**No index added.** The slowest list is the case text search (about 100 ms). `EXPLAIN ANALYZE` under an oversight
session shows a sequential scan of all 20,000 rows because the search is one `OR` across the reference, the institution
name, the raw name and the complaint text in three tables, which the existing trigram indexes cannot serve; "hostel"
also matches 26% of rows, where no index would help. An index alone would not change the plan; the next step at larger
volumes is a query that unions the indexed matches (readiness row 58).

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

## To run on a larger machine (at least 16 GB of RAM, nothing else running)

The development laptop (7.7 GB, 3.9 GB for Docker) cannot give a clean capacity figure. No capacity number is
claimed anywhere in this repository. On a machine with at least 16 GB, give Docker at least 10 GB and run, from the
repository root, against a throwaway stack (`docker compose -p sethu-load ...`, never the demo stack):

1. **Stack and data.** `python scripts/init_env.py`; `docker compose -p sethu-load --profile dev up --build -d --wait`;
   `docker compose -p sethu-load run --rm --no-deps -v "${PWD}/seed:/seed:ro" backend python /seed/load.py`, then
   `... backend python /seed/volume.py 100000`. Wait until the worker's `sethu.findings.detect` and
   `sethu.overlaps.detect` runs finish (worker log) and embeddings stop growing.
2. **Slow statements.** `docker exec sethu-load-postgres-1 psql -U postgres -c "ALTER SYSTEM SET log_min_duration_statement = 200" -c "SELECT pg_reload_conf()"`.
3. **Load.** The k6 command under "How to run it" with `--network sethu-load_app`. Record p50, p95 and p99 per screen
   (`sethu_screen_ms` in `loadtest/out/summary.json`) and rank the Postgres log's statements by total time.
4. **Indexes.** Only for a statement in the top of that ranking whose plan (`EXPLAIN (ANALYZE, BUFFERS)`) shows a scan
   an index removes; a new Alembic revision; re-run step 3 and record both runs here.

Drills, each on the same stack, with the result written in the table above:

| Drill | Steps | Pass when |
|---|---|---|
| Postgres restart mid-intake | Start `docker compose -p sethu-load run --rm --no-deps -v "${PWD}/loadtest:/loadtest:ro" backend python /loadtest/drill_intake.py 120 5`; after 30 s, `docker restart sethu-load-postgres-1` | The report's `lost` is empty: every submission answered 202 is in `intake_items` and processed |
| Redis restart | The same, restarting `sethu-load-redis-1` | `lost` empty; the scheduler and worker resume without a restart of their own |
| Worker killed mid-job | Start the intake drill; `docker kill sethu-load-worker-1` during it; `docker start sethu-load-worker-1` | `lost` empty; items left `pending` are processed after the start; the audit chain verifies |
| SMTP down for an hour | `docker stop sethu-load-mailpit-1`; `... python /loadtest/drill_smtp.py 300`; start Mailpit after 60 minutes | Every approved alert ends `sent`, none `failed` (10 attempts span about 4 hours) |
| Backup disk full | The backup service is in `docker-compose.prod.yml` only: run the production-shaped stack (docs/RUNBOOK.md section 5), override `backup` with `tmpfs: ["/backups:size=10m,uid=999"]` in place of its volume, and let it run | The backup fails with a clear log line and a non-zero exit; the previous backup is untouched; the app keeps serving |
| Keycloak down | `docker stop sethu-load-keycloak-1`; open the app in a fresh browser | The "Sign-in is unavailable right now" page (status 502), not a blank page; signed-in users keep working until their token expires (5 minutes) |
| Offline run | `sh loadtest/offline.sh on sethu-load`; `sh loadtest/offline.sh probe sethu-load` must print "no route out" for web and keycloak; run the Playwright journeys (`cd web; $env:SETHU_URL="http://localhost:8080"; $env:DEMO_USER_PASSWORD="<from .env>"; npx playwright test`); `sh loadtest/offline.sh off sethu-load` | All journeys pass with egress blocked. Then, and only then, tick "Runs with Wi-Fi off" in docs/02-PS-COVERAGE-CHECKLIST.md with this evidence |
