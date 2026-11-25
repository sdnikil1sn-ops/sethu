"""AI Phase A4: relationship graph (NetworkX, Louvain, CTE fallback, node cap), workflow bottlenecks, national early
warning (DBSCAN, Z-score, ratio; stable ids, lifecycle, feedback), the map data, and bureau isolation throughout."""
import shutil
import subprocess
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.ai import catalog, graph, router, warning
from app.ai.providers import NotApplicable, Provider
from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.findings import service as findings
from app.modules.graph import repo as graph_repo
from app.modules.graph import service as graphs
from app.modules.overlaps import service as overlaps
from app.modules.signals import service as signals
from tests.conftest import requires_db

SETTINGS = {"recent_days": 30, "baseline_days": 90, "km_per_unit": 500.0, "days_per_unit": 10.0, "eps": 1.0,
            "min_samples": 6, "min_members": 8, "max_points": 30000, "max_baseline_share": 0.5, "z_threshold": 3.0,
            "z_min_count": 5, "z_sd_floor": 1.0, "ratio_min_count": 5, "ratio_threshold": 3.0}
WEB = Path(__file__).resolve().parents[2] / "web"


@pytest.fixture(autouse=True)
def circuits():
    router.reset_circuits()
    yield
    router.reset_circuits()


def q(world, sql, **params):
    with session_for(SYSTEM, world["engine"]) as s:
        return [dict(r) for r in s.execute(text(sql), params).mappings()]


def setting(world, key, value):
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.app_settings SET value = CAST(:v AS jsonb) WHERE key = :k"),
                  {"k": key, "v": value})


# --- pure: the algorithms ----------------------------------------------------------------------------------

def test_dbscan_finds_hand_made_clusters_and_leaves_noise():
    a = [(0.0 + i * 0.1, 0.0) for i in range(6)]
    b = [(10.0, 10.0 + i * 0.1) for i in range(5)]
    noise = [(5.0, 5.0), (-7.0, 3.0), (20.0, -4.0)]
    labels = warning.dbscan(a + b + noise, eps=0.5, min_samples=4)
    assert len(set(labels[:6])) == 1 and len(set(labels[6:11])) == 1 and labels[0] != labels[6]
    assert labels[11:] == [-1, -1, -1]
    assert warning.dbscan(a, eps=0.5, min_samples=7) == [-1] * 6          # too sparse: all noise
    assert warning.dbscan([], 1.0, 3) == []


def rows(n, state, category="Fee refund", start=1, step=1, bureau="b1"):
    return [{"id": f"{state}-{category}-{start + i * step}", "category": category, "group": category,
             "state": state, "bureau_id": bureau, "days_ago": start + i * step} for i in range(n)]


def test_zscore_floors_a_quiet_baseline():
    # Eight in Kerala this month, nothing in the 90 days before: the weekly SD is 0, so the floor (1.0) is used.
    payload = {"complaints": rows(8, "Kerala") + rows(1, "Goa", start=40), "settings": SETTINGS}
    out = warning.ZScoreWarning().run(payload).output["signals"]
    assert len(out) == 1 and out[0]["explanation"]["floored"] and out[0]["explanation"]["sd_used"] == 1.0
    weeks = SETTINGS["recent_days"] / 7
    assert out[0]["score"] == pytest.approx(8 / (weeks ** 0.5 * 1.0), abs=0.01)   # finite, not 8 / 0
    small = {"complaints": rows(8, "Kerala") + rows(1, "Goa", start=40), "settings": SETTINGS | {"z_sd_floor": 3.0}}
    assert warning.ZScoreWarning().run(small).output["signals"] == []               # a bigger floor: no signal


class Broken(Provider):
    def __init__(self, name):
        self.name = name

    def run(self, payload):
        raise RuntimeError("down")


@requires_db
def test_warning_falls_through_dbscan_then_zscore_then_ratio(world):
    # Five complaints in one state, no baseline: too few for DBSCAN (min_samples 6), no baseline for the Z-score,
    # so the ratio rule (min 5, nothing before) answers.
    payload = {"complaints": rows(5, "Kerala"), "settings": SETTINGS}
    chain = [warning.DBSCANWarning(), warning.ZScoreWarning(), warning.RatioWarning()]
    with session_for(SYSTEM, world["engine"]) as s:
        r = router.run(s, SYSTEM, "warning.detect", payload, chain=chain)
    assert (r["status"], r["path"], r["output"]["method"]) == ("ok", "last_resort", "ratio")
    assert len(r["output"]["signals"]) == 1
    with session_for(SYSTEM, world["engine"]) as s:          # a failing primary: the Z-score answers
        r = router.run(s, SYSTEM, "warning.detect", {"complaints": rows(6, "Kerala") + rows(1, "Goa", start=40),
                                                     "settings": SETTINGS},
                       chain=[Broken("warning-dbscan"), warning.ZScoreWarning(), warning.RatioWarning()])
    assert (r["path"], r["output"]["method"]) == ("fallback", "zscore")


def test_louvain_is_reproducible_with_the_fixed_seed():
    edges = [(f"i:{a}", f"b:{a % 3}", 1.0) for a in range(30)] + [("b:0", "b:1", 1.0), ("i:1", "i:2", 3.0)]
    first = graph.communities(graph.build(edges), seed=26264, resolution=1.0)
    again = graph.communities(graph.build(list(reversed(edges))), seed=26264, resolution=1.0)
    assert first == again and len(first) >= 2


# --- the graph on the seed ---------------------------------------------------------------------------------

@requires_db
def test_graph_build_stores_communities_and_rebuilds_only_on_change(world):
    with session_for(SYSTEM, world["engine"]) as s:
        built = graphs.build_task(s, SYSTEM)
    assert built["rebuilt"] and built["method"] == "louvain" and built["communities"] >= 2 and not built["capped"]
    kinds = {r["edge_type"]: r["n"] for r in q(world, "SELECT edge_type, count(*) AS n FROM sethu.graph_edges "
                                                      "GROUP BY 1")}
    assert kinds["held_by"] == 318 and kinds["about"] == kinds["handled_by"] and kinds["transfer"] >= 8
    stored = q(world, "SELECT node_type, count(*) AS n FROM sethu.graph_communities GROUP BY 1")
    assert {r["node_type"] for r in stored} == {"institution", "bureau"}               # never complaints
    with session_for(SYSTEM, world["engine"]) as s:
        assert graphs.build_task(s, SYSTEM) == {"changed": 0, "rebuilt": False, "version": built["version"]}
        assert overlaps.detect(s, SYSTEM)["suggested"] == 7
    with session_for(SYSTEM, world["engine"]) as s:     # new overlap suggestions: edges change, it rebuilds
        again = graphs.build_task(s, SYSTEM)
    assert again["rebuilt"] and again["changed"] == 7
    edge = q(world, "SELECT method, confidence, evidence FROM sethu.graph_edges WHERE edge_type = 'overlap' LIMIT 1")[0]
    assert edge["method"] == "text" and 0 <= float(edge["confidence"]) <= 1 and edge["evidence"]["reasons"]
    # Louvain with a fixed seed: the same graph gives the same communities.
    with session_for(SYSTEM, world["engine"]) as s:
        third = graphs.build_task(s, SYSTEM, force=True)

    def members(v):
        return sorted((r["node_type"], str(r["node_id"]), r["community"])
                      for r in q(world, "SELECT * FROM sethu.graph_communities WHERE version = :v", v=v))
    assert members(again["version"]) == members(third["version"])


@requires_db
def test_cte_fallback_agrees_with_networkx_on_direct_links(world):
    with session_for(SYSTEM, world["engine"]) as s:
        graphs.build_task(s, SYSTEM)
        g = graph.build(graph_repo.full_edges(s))
        inst = s.execute(text("SELECT id FROM sethu.institutions WHERE name = 'Greenfield Institute of Technology'"))\
            .scalar_one()
        cte = graph_repo.ego(s, inst, 1, 0.0, 10_000)
    direct = {n for n in g.neighbors(f"i:{inst}") if n.startswith("c:")}
    assert direct and direct == {f"c:{r['node_id']}" for r in cte if r["node_type"] == "complaint"}


@requires_db
def test_node_cap_builds_the_institution_bureau_graph(world):
    setting(world, "ai.graph.node_cap", "50")
    try:
        with session_for(SYSTEM, world["engine"]) as s:
            built = graphs.build_task(s, SYSTEM)
    finally:
        setting(world, "ai.graph.node_cap", "60000")
    assert built["capped"] and built["nodes"] <= 43 + 4 and built["communities"] >= 1


@requires_db
def test_graph_falls_back_to_cte_when_networkx_is_unavailable(world, monkeypatch):
    monkeypatch.setattr(graph.GraphNetworkX, "health", lambda self: False)
    with session_for(SYSTEM, world["engine"]) as s:
        built = graphs.build_task(s, SYSTEM)
    assert built["method"] == "cte" and built["communities"] is None
    run = q(world, "SELECT path, communities FROM sethu.graph_runs ORDER BY version DESC LIMIT 1")[0]
    assert run == {"path": "fallback", "communities": None}


# --- bureau isolation through the graph ---------------------------------------------------------------------

@requires_db
def test_graph_explanations_mark_restricted_records_and_hide_others_links(world):
    with session_for(SYSTEM, world["engine"]) as s:
        overlaps.detect(s, SYSTEM)
        graphs.build_task(s, SYSTEM)
    demo = q(world, """SELECT l.complaint_a, l.complaint_b FROM sethu.overlap_links l
                         JOIN sethu.complaints a ON a.id = l.complaint_a JOIN sethu.complaints b ON b.id = l.complaint_b
                        WHERE ARRAY[a.ref, b.ref] <@ ARRAY['C-101', 'C-102']""")[0]
    client = TestClient(app)
    try:
        app.dependency_overrides[get_principal] = lambda: world["rao"]               # PGRC holds C-101
        got = client.get("/api/v1/graph/explain", params={"source": f"c:{demo['complaint_a']}",
                                                          "target": f"c:{demo['complaint_b']}",
                                                          "kind": "overlap_proposed"}).json()
        assert got["method"] == "text" and len(got["evidence"]) == 2
        mine = {c["ref"]: c for c in got["evidence"]}
        assert mine["C-101"]["readable"] and mine["C-101"]["source"]
        assert not mine["C-102"]["readable"] and mine["C-102"]["restricted"] and mine["C-102"]["source"] is None
        # A bureau that is not a party sees no such link, and no overlap or transfer edge of others.
        app.dependency_overrides[get_principal] = lambda: Principal("x", "x", "officer", world["bureau"]["AB"])
        assert client.get("/api/v1/graph/explain", params={"source": f"c:{demo['complaint_a']}",
                                                           "target": f"c:{demo['complaint_b']}",
                                                           "kind": "overlap_proposed"}).status_code == 404
    finally:
        app.dependency_overrides.clear()
    ab = Principal("x", "x", "officer", world["bureau"]["AB"])
    with session_for(ab, world["engine"]) as s:
        seen = dict(s.execute(text("SELECT edge_type, count(*) FROM sethu.graph_edges GROUP BY 1")).all())
    assert "overlap" not in seen and seen["held_by"] == 318                    # summaries yes, others' links no
    with session_for(world["rao"], world["engine"]) as s:
        ego = graphs.ego(s, UUID(str(q(world, "SELECT institution_id FROM sethu.complaints WHERE ref = 'C-101'")[0]
                                     ["institution_id"])), 2, None)
    assert any(n.get("label") == "C-102" and n["readable"] is False for n in ego["nodes"])


# --- bottlenecks --------------------------------------------------------------------------------------------

@requires_db
def test_bottlenecks_come_from_the_workflow_graph_with_explanations(world):
    with session_for(SYSTEM, world["engine"]) as s:
        findings.detect(s, SYSTEM)
    found = q(world, "SELECT kind, key, evidence FROM sethu.findings WHERE kind IN ('bottleneck', 'transfer_loop')")
    assert all(f["evidence"]["path"] == "primary" and f["evidence"]["explanation"] for f in found)
    loop = [f for f in found if f["evidence"].get("scope") == "handoff_cycle"]
    assert loop and loop[0]["evidence"]["route"] in ("PGRC -> RB -> PGRC", "RB -> PGRC -> RB")
    assert any(f["kind"] == "transfer_loop" for f in found)                     # C-090 still found
    run = q(world, "SELECT path, provider FROM sethu.ai_runs WHERE task = 'bottleneck.detect'")[0]
    assert run == {"path": "primary", "provider": "workflow-graph"}


@requires_db
def test_bottleneck_fallback_and_findings_kept_when_nothing_can_judge(world, monkeypatch):
    monkeypatch.setattr(catalog.PROVIDERS["workflow-graph"], "health", lambda self: False)
    with session_for(SYSTEM, world["engine"]) as s:
        findings.detect(s, SYSTEM)
    keys = {r["key"]: r["evidence"] for r in q(world, "SELECT key, evidence FROM sethu.findings "
                                                     "WHERE kind IN ('bottleneck', 'transfer_loop')")}
    assert keys and all(e["path"] == "fallback" and e["method"] == "rules" for e in keys.values())
    monkeypatch.setitem(catalog.PROVIDERS, "bottleneck-rules", lambda: Broken("bottleneck-rules"))
    router.reset_circuits()
    with session_for(SYSTEM, world["engine"]) as s:
        assert findings.detect(s, SYSTEM)["resolved"] == 0                   # not resolved blindly
    open_now = {r["key"] for r in q(world, "SELECT key FROM sethu.findings WHERE status = 'open'")}
    assert set(keys) <= open_now


# --- early warning on the seed -----------------------------------------------------------------------------

@requires_db
def test_each_method_finds_the_seeded_spike_and_only_dbscan_the_cross_state_cluster(world):
    with session_for(SYSTEM, world["engine"]) as s:
        payload = signals.payload(s)
    found = {}
    for p in (warning.DBSCANWarning(), warning.ZScoreWarning(), warning.RatioWarning()):
        found[p.name] = {(x["category_group"], tuple(x["states"])) for x in p.run(payload).output["signals"]}
    spike = ("Fee refund", ("Uttar Pradesh",))
    cluster = ("Scholarship delay", ("Karnataka", "Tamil Nadu"))
    assert spike in found["warning-dbscan"] and spike in found["warning-zscore"] and spike in found["warning-ratio"]
    assert cluster in found["warning-dbscan"]
    assert cluster not in found["warning-zscore"] and cluster not in found["warning-ratio"]
    assert found["warning-dbscan"] == {spike, cluster}                          # nothing else on the seed


@requires_db
def test_signals_keep_their_ids_flow_to_the_outbox_and_are_decided_with_feedback(world):
    with session_for(SYSTEM, world["engine"]) as s:
        first = signals.detect(s, SYSTEM)
    with session_for(SYSTEM, world["engine"]) as s:
        second = signals.detect(s, SYSTEM)
    assert first["created"] == 2 and first["method"] == "dbscan" and second == {"created": 0, "updated": 2,
                                                                                "method": "dbscan"}
    rows = q(world, "SELECT id, states, alert_ids, explanation FROM sethu.warning_signals ORDER BY states")
    assert len(rows) == 2 and all(r["explanation"]["label"] == "Emerging signal: requires verification" for r in rows)
    alerts = q(world, "SELECT kind, status FROM sethu.alerts WHERE id = ANY(:ids)",
               ids=[a for r in rows for a in r["alert_ids"]])
    assert alerts and all(a == {"kind": "early_warning", "status": "pending_approval"} for a in alerts)
    up = next(r for r in rows if r["states"] == ["Uttar Pradesh"])
    client = TestClient(app)
    try:
        app.dependency_overrides[get_principal] = lambda: world["rao"]                  # an officer
        assert client.post(f"/api/v1/signals/{up['id']}/decision", json={"status": "acknowledged"}).status_code == 403
        app.dependency_overrides[get_principal] = lambda: world["menon"]                # oversight
        assert client.post(f"/api/v1/signals/{up['id']}/decision", json={"status": "dismissed"}).status_code == 422
        r = client.post(f"/api/v1/signals/{up['id']}/decision", json={"status": "acknowledged"})
        assert r.status_code == 200 and r.json()["status"] == "acknowledged"
        r = client.post(f"/api/v1/signals/{up['id']}/decision",
                        json={"status": "dismissed", "reason": "Seasonal: refunds after admissions close"})
        assert r.status_code == 200 and r.json()["status_reason"].startswith("Seasonal")
    finally:
        app.dependency_overrides.clear()
    fb = q(world, "SELECT decision, reason, signal_id FROM sethu.ai_feedback WHERE kind = 'signal' ORDER BY id")
    assert [f["decision"] for f in fb] == ["acknowledged", "dismissed"] and fb[1]["reason"].startswith("Seasonal")
    for sql in ("UPDATE sethu.ai_feedback SET reason = 'x'", "DELETE FROM sethu.ai_feedback"):
        with pytest.raises(DBAPIError, match="permission denied"), session_for(SYSTEM, world["engine"]) as s:
            s.execute(text(sql))
    with session_for(SYSTEM, world["engine"]) as s:          # a dismissed signal stays dismissed, same id
        signals.detect(s, SYSTEM)
    assert q(world, "SELECT status FROM sethu.warning_signals WHERE id = :i", i=up["id"])[0]["status"] == "dismissed"
    assert len(q(world, "SELECT 1 FROM sethu.warning_signals")) == 2
    with pytest.raises(DBAPIError, match="only the status"), session_for(world["menon"], world["engine"]) as s:
        s.execute(text("UPDATE sethu.warning_signals SET members = 1"))


@requires_db
def test_signals_and_map_respect_bureau_isolation(world):
    with session_for(SYSTEM, world["engine"]) as s:
        signals.detect(s, SYSTEM)
    client = TestClient(app)
    seen = {}
    try:
        for who in ("rao", "iyer", "menon"):
            app.dependency_overrides[get_principal] = lambda w=who: world[w]
            seen[who] = client.get("/api/v1/signals").json()
            seen[who + "-map"] = client.get("/api/v1/map/states").json()
        app.dependency_overrides[get_principal] = lambda: Principal("x", "x", "officer", world["bureau"]["AB"])
        seen["ab"] = client.get("/api/v1/signals").json()
        seen["ab-map"] = client.get("/api/v1/map/states").json()
        state = client.get("/api/v1/map/state", params={"state": "Uttar Pradesh"}).json()
    finally:
        app.dependency_overrides.clear()
    assert len(seen["menon"]) == 2 and seen["ab"] == [] and state["signals"] == [] and state["institutions"]
    # Density counts are summary counts, the same for everyone; signal counts follow what each may see.
    assert [s["complaints"] for s in seen["ab-map"]["states"]] == [s["complaints"] for s in seen["menon-map"]["states"]]
    assert sum(s["signals"] for s in seen["ab-map"]["states"]) == 0
    for who, bureau in (("rao", "PGRC"), ("iyer", "RB")):
        for sig in seen[who]:
            assert bureau in sig["bureaus"]
            for c in sig["cases"]:
                if c["bureau"] != bureau:          # another bureau's case: marked, never opened
                    assert not c["readable"]
                assert (c.get("restricted") is None) == c["readable"]


# --- the web bundle ------------------------------------------------------------------------------------------

@pytest.mark.skipif(not (WEB / "dist").is_dir() or not shutil.which("node"), reason="needs node and web/dist")
def test_the_built_web_bundle_loads_nothing_from_outside():
    done = subprocess.run(["node", str(WEB / "scripts/check-offline.mjs")], capture_output=True, text=True)  # noqa: S603, S607
    assert done.returncode == 0, done.stderr
    assert (WEB / "dist/maps/india-states.json").is_file()          # the boundaries are served by the app itself


def test_the_centroid_table_covers_the_states_used():
    for st in ("Uttar Pradesh", "Karnataka", "Tamil Nadu", "Maharashtra", "Gujarat", "Rajasthan", "Kerala",
               "Telangana", "West Bengal", "Madhya Pradesh", "Ladakh", "Jammu and Kashmir"):
        assert warning.state_key(st), st
    assert warning.state_key("Atlantis") is None
    with pytest.raises(NotApplicable):
        warning.DBSCANWarning().run({"complaints": rows(2, "Kerala"), "settings": SETTINGS})
