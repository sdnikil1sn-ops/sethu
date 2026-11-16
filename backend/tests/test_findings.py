"""Deadlock and bottleneck findings, the early-warning trend, and who sees and changes what."""
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.auth import get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.alerts import service as alerts
from app.modules.complaints import service as complaints
from app.modules.findings import service
from tests.conftest import requires_db
from tests.test_seed import COMPLAINTS

NOW = datetime(2026, 11, 1, tzinfo=UTC)
A, B, C = uuid4(), uuid4(), uuid4()


def hop(action, days_ago, frm=None, to=None, acknowledged=False):
    return {"id": uuid4(), "complaint_id": "case", "ref": "C-1", "institution_id": None, "action": action,
            "from_bureau_id": frm, "to_bureau_id": to, "created_at": NOW - timedelta(days=days_ago),
            "acknowledged_at": NOW if acknowledged else None}


# --- The rules, without a database ---------------------------------------------------------------

def test_loop_needs_two_unacknowledged_transfers_back_to_a_bureau():
    loop = [hop("filed", 40), hop("assigned", 39), hop("transferred", 30, A, B), hop("transferred", 18, B, A)]
    found = service.transfer_finding(loop, NOW, 7)
    assert found["kind"] == "transfer_loop" and found["bureau_ids"] == [A, B]
    assert found["evidence"]["transfers"] == 2 and found["evidence"]["days_unacknowledged"] == 18
    assert service.transfer_finding(loop[:3] + [hop("transferred", 18, B, C)], NOW, 7)["kind"] == "stalled_transfer"


@pytest.mark.parametrize("breaker", [hop("acknowledged", 25), hop("note", 25), hop("assigned", 25)])
def test_an_acknowledgement_or_any_action_breaks_the_loop(breaker):
    history = [hop("transferred", 30, A, B), breaker, hop("transferred", 1, B, A)]
    assert service.transfer_finding(history, NOW, 7) is None  # one recent transfer: not stalled yet
    acknowledged = [hop("transferred", 30, A, B, acknowledged=True), hop("transferred", 20, B, A, acknowledged=True)]
    assert service.transfer_finding(acknowledged, NOW, 7) is None


def test_stall_threshold():
    one = [hop("transferred", 7, A, B)]
    assert service.transfer_finding(one, NOW, 7)["kind"] == "stalled_transfer"
    assert service.transfer_finding(one, NOW, 8) is None


def test_bottleneck_rule_and_its_numbers():
    rows = [{"id": "x", "bureau_ids": [A], "open": 4, "overdue": 3, "older_than_median": 2, "median_days": 10},
            {"id": "y", "bureau_ids": [B], "open": 2, "overdue": 2, "older_than_median": 2, "median_days": 10}]
    found = service.queue_findings("bureau", rows, 3, 0.5)
    assert [f["key"] for f in found] == ["bottleneck:bureau:x:overdue_share"]  # 2 of 4 is not more than half
    assert found[0]["evidence"]["share"] == 0.75 and found[0]["evidence"]["overdue"] == 3


# --- On the seeded data --------------------------------------------------------------------------

@pytest.fixture
def detected(world):
    with session_for(SYSTEM, world["engine"]) as s:
        world["first"] = service.detect(s, SYSTEM)
    return world


def findings_as(world, who, **filters):
    with session_for(world[who], world["engine"]) as s:
        return service.listing(s, filters)


@requires_db
def test_loop_detection_finds_c090_and_queues_an_alert_for_approval(detected):
    loops = findings_as(detected, "menon", kind="transfer_loop")
    assert [f["ref"] for f in loops] == ["C-090"]
    loop = loops[0]
    assert loop["bureaus"] == ["PGRC", "RB"] and loop["status"] == "open" and loop["alert_status"] == "pending_approval"
    assert findings_as(detected, "menon", kind="stalled_transfer") == []  # the loop is not counted twice
    with session_for(SYSTEM, detected["engine"]) as s:
        alert = s.execute(text("SELECT * FROM sethu.alerts WHERE id = :i"), {"i": loop["alert_id"]}).mappings().one()
        created = s.execute(text("SELECT payload FROM sethu.audit_log WHERE action = 'finding.created'"
                                 " AND entity_id = :i"), {"i": str(loop["id"])}).scalar_one()
    assert alert["status"] == "pending_approval" and alert["kind"] == "bottleneck" and alert["sent_at"] is None
    assert alert["complaint_id"] == detected["case"]["C-090"] and alert["approved_by"] is None
    assert len(alert["recipients"]) >= 2 and all(r.endswith("@sethu.test") for r in alert["recipients"])
    assert alert["subject"] == "Bottleneck detected: transfer loop on case C-090"
    assert created["alert_id"] == str(alert["id"]) and created["kind"] == "transfer_loop"
    c090 = next(c for c in COMPLAINTS if c["ref"] == "C-090")
    stored = json.dumps([dict(alert), loop, created], default=str)
    assert c090["body"] not in stored and c090["body"][:30] not in stored  # no complaint text anywhere

    # A bureau head of a bureau involved releases it; only then can the worker send it.
    with session_for(detected["iyer"], detected["engine"]) as s:
        assert alerts.decide(s, detected["iyer"], loop["alert_id"], approve=True)["status"] == "approved"


@requires_db
def test_a_second_run_adds_nothing(detected):
    assert detected["first"]["created"] > 0
    with session_for(SYSTEM, detected["engine"]) as s:
        counted = "SELECT (SELECT count(*) FROM sethu.findings), (SELECT count(*) FROM sethu.alerts)," \
                  " (SELECT count(*) FROM sethu.audit_log WHERE action LIKE 'finding.%')"
        before = s.execute(text(counted)).one()
        assert service.detect(s, SYSTEM) == {"created": 0, "reopened": 0, "resolved": 0}
        assert s.execute(text(counted)).one() == before


@requires_db
def test_findings_are_scoped_to_the_bureaus_involved(detected):
    everything = findings_as(detected, "menon")
    pgrc, rb = findings_as(detected, "rao"), findings_as(detected, "iyer")
    assert {f["id"] for f in findings_as(detected, "das")} == {f["id"] for f in everything}
    assert all("PGRC" in f["bureaus"] for f in pgrc) and all("RB" in f["bureaus"] for f in rb)
    assert {f["id"] for f in everything if "PGRC" in f["bureaus"]} == {f["id"] for f in pgrc}
    assert {f["id"] for f in everything if "RB" in f["bureaus"]} == {f["id"] for f in rb}
    assert "C-090" in {f["ref"] for f in pgrc} & {f["ref"] for f in rb}  # both bureaus see the loop
    assert {f["id"] for f in pgrc} != {f["id"] for f in rb}

    client = TestClient(app)
    try:
        app.dependency_overrides[get_principal] = lambda: detected["rao"]
        assert {f["id"] for f in client.get("/api/v1/findings").json()} == {str(f["id"]) for f in pgrc}
        assert client.get("/api/v1/findings", params={"bureau": "RB"}).json() == [
            f for f in client.get("/api/v1/findings").json() if "RB" in f["bureaus"]]
        assert client.post("/api/v1/findings/detect").status_code == 403
        assert client.get("/api/v1/findings", params={"kind": "nonsense"}).status_code == 422
    finally:
        app.dependency_overrides.clear()


@requires_db
def test_dismiss_reopen_and_resolve_are_audited_and_limited(detected):
    rb_only = next(f for f in findings_as(detected, "menon", kind="bottleneck") if f["bureaus"] == ["RB"])
    loop = findings_as(detected, "menon", kind="transfer_loop")[0]
    engine = detected["engine"]

    with session_for(detected["fernandes"], engine) as s:  # a PGRC head cannot see an RB-only finding
        with pytest.raises(service.FindingError) as hidden:
            service.decide(s, detected["fernandes"], rb_only["id"], "dismissed")
        assert hidden.value.status == 404
    with session_for(detected["iyer"], engine) as s:
        assert service.decide(s, detected["iyer"], rb_only["id"], "dismissed")["status"] == "dismissed"
    with session_for(detected["menon"], engine) as s:
        assert service.decide(s, detected["menon"], rb_only["id"], "open")["status"] == "open"
    with session_for(detected["iyer"], engine) as s:  # the database lets people change only the status
        with pytest.raises(DBAPIError, match="only the status"):
            s.execute(text("UPDATE sethu.findings SET evidence = '{}' WHERE id = :i"), {"i": rb_only["id"]})

    client = TestClient(app)
    try:
        app.dependency_overrides[get_principal] = lambda: detected["rao"]  # an officer may not decide
        assert client.post(f"/api/v1/findings/{loop['id']}/decision", json={"status": "dismissed"}).status_code == 403
    finally:
        app.dependency_overrides.clear()

    # PGRC picks C-090 up: the loop no longer holds, and the next run says so.
    with session_for(detected["rao"], engine) as s:
        complaints.act(s, detected["rao"], detected["case"]["C-090"], "acknowledge")
    with session_for(SYSTEM, engine) as s:
        assert service.detect(s, SYSTEM)["resolved"] >= 1
        actions = [r[0] for r in s.execute(text(
            "SELECT action FROM sethu.audit_log WHERE entity_type = 'findings' AND entity_id IN (:a, :b) ORDER BY seq"),
            {"a": str(rb_only["id"]), "b": str(loop["id"])})]
    assert actions.count("finding.created") == 2
    decided = [a for a in actions if a != "finding.created"]
    assert decided == ["finding.dismissed", "finding.reopened", "finding.resolved"]
    assert findings_as(detected, "menon", kind="transfer_loop")[0]["status"] == "resolved"


@requires_db
def test_trend_indicator_and_dashboard_count(detected):
    with session_for(detected["rao"], detected["engine"]) as s:
        trend = service.trend(s)
    top = trend["items"][0]
    assert trend["days"] == 30 and top["institution"] == "Greenfield Institute of Technology"
    assert (top["recent"], top["previous"], top["bureaus"]) == (3, 0, ["PGRC", "RB"])
    assert all(r["recent"] > r["previous"] and len(r["bureaus"]) >= 2 for r in trend["items"])

    client = TestClient(app)
    try:
        for who in ("rao", "menon"):
            app.dependency_overrides[get_principal] = lambda who=who: detected[who]
            shown = client.get("/api/v1/dashboard").json()["attention"]["findings_open"]
            assert shown == len(findings_as(detected, who, status="open")) > 0
    finally:
        app.dependency_overrides.clear()
