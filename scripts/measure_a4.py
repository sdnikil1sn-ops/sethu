"""Measure A4 at load-test volume: time and memory of the graph build (edges, NetworkX, Louvain), the ego query,
bottleneck detection (workflow graph) and early warning (DBSCAN, Z-score, ratio). Prints JSON; counts and
timings only.

    # a THROWAWAY database: it is emptied and loaded with the seed, then brought up to each size by seed/volume.py
    docker run --rm -e SETHU_ALLOW_WIPE=1 -e MIGRATION_DATABASE_URL=... -e SETHU_DATABASE_URL=... \
        -e PYTHONPATH=/w/backend:/w/seed -v <repo>:/w:ro sethu-backend \
        python /w/scripts/measure_a4.py 10000 50000 100000

Peak memory is the process's VmHWM (Linux), read after each phase; it only grows, so a phase's own peak is its
value when it is higher than the one before.
"""
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text


def peak_mb() -> float:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmHWM:"):
            return round(int(line.split()[1]) / 1024, 1)
    return -1.0


def rss_mb() -> float:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return round(int(line.split()[1]) / 1024, 1)
    return -1.0


def timed(name: str, out: dict, fn):
    started = time.perf_counter()
    result = fn()
    out[name] = {"seconds": round(time.perf_counter() - started, 2), "rss_mb": rss_mb(), "peak_mb": peak_mb()}
    return result


def wipe_and_seed() -> None:
    if os.environ.get("SETHU_ALLOW_WIPE") != "1":
        raise SystemExit("refusing: set SETHU_ALLOW_WIPE=1 (this empties the database)")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    from tests.conftest import TABLES
    owner = create_engine(os.environ["MIGRATION_DATABASE_URL"])
    with owner.begin() as c:
        c.execute(text("ALTER TABLE sethu.audit_log DISABLE TRIGGER audit_log_no_truncate"))
        c.execute(text(f"TRUNCATE {', '.join('sethu.' + t.strip() for t in TABLES.split(','))} CASCADE"))
        c.execute(text("ALTER TABLE sethu.audit_log ENABLE TRIGGER audit_log_no_truncate"))
        c.execute(text("DELETE FROM sethu.app_settings WHERE key = 'ai.embedding.active'"))
    import load
    load.load()


def measure(size: int) -> dict:
    import volume

    from app.ai.warning import DBSCANWarning, RatioWarning, ZScoreWarning
    from app.ai.workflow import WorkflowGraph
    from app.db.session import SYSTEM, session_for
    from app.modules.findings import repo as findings_repo
    from app.modules.findings import service as findings
    from app.modules.graph import service as graph
    from app.modules.signals import service as signals

    out: dict = {"complaints": size}
    timed("volume_load", out, lambda: volume.main(size, 2000))
    if os.environ.get("SETHU_ANALYZE") == "1":     # fresh statistics, as autovacuum gives a running system
        with create_engine(os.environ["MIGRATION_DATABASE_URL"]).begin() as c:
            timed("analyze", out, lambda: c.execute(text("ANALYZE")))
    with session_for(SYSTEM) as s:
        out["actual_complaints"] = s.execute(text("SELECT count(*) FROM sethu.complaints")).scalar_one()
        built = timed("graph_build", out, lambda: graph.build_task(s, SYSTEM, force=True))
    out["graph"] = {k: built.get(k) for k in ("method", "nodes", "edges", "communities", "capped", "changed")}
    with session_for(SYSTEM) as s:      # the whole graph, even above the cap: what the cap avoids
        s.execute(text("UPDATE sethu.app_settings SET value = '10000000' WHERE key = 'ai.graph.node_cap'"))
        full = timed("graph_build_uncapped", out, lambda: graph.build_task(s, SYSTEM, force=True))
        out["graph_uncapped"] = {k: full.get(k) for k in ("nodes", "edges", "communities")}
        s.execute(text("UPDATE sethu.app_settings SET value = '60000' WHERE key = 'ai.graph.node_cap'"))
    with session_for(SYSTEM) as s:
        hot = s.execute(text("""SELECT institution_id FROM sethu.complaints WHERE institution_id IS NOT NULL
                                 GROUP BY 1 ORDER BY count(*) DESC LIMIT 1""")).scalar_one()
        ego = timed("ego_2_hops_hottest_institution", out, lambda: graph.ego(s, hot, 2, None))
        out["ego_nodes"] = len(ego["nodes"])
        payload = timed("bottleneck_payload", out, lambda: {
            "actions": findings_repo.workflow_actions(s),
            "cases": {c["id"]: c for c in findings_repo.workflow_cases(s)}, "codes": findings_repo.bureau_codes(s),
            "rule_findings": [], "settings": findings.bottleneck_settings(s), "now": datetime.now(UTC)})
        out["actions"] = len(payload["actions"])
        res = timed("bottleneck_workflow_graph", out, lambda: WorkflowGraph().run(payload))
        out["bottleneck_findings"] = len(res.output["findings"])
        wp = timed("warning_payload", out, lambda: signals.payload(s))
        out["warning_complaints"] = len(wp["complaints"])
        for p in (DBSCANWarning(), ZScoreWarning(), RatioWarning()):
            try:
                got = timed(f"warning_{p.name}", out, lambda p=p: p.run(wp))
                out[f"{p.name}_signals"] = len(got.output["signals"])
            except Exception as e:  # noqa: BLE001 - recorded: a NotApplicable is a result here
                out[f"{p.name}_signals"] = f"{type(e).__name__}: {e}"
    return out


def main(sizes: list[int]) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seed"))
    wipe_and_seed()
    for size in sizes:
        print(json.dumps(measure(size), default=str), flush=True)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [10_000, 50_000, 100_000])
