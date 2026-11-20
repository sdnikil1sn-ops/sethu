"""Deadlock and bottleneck findings, the early-warning trend, and who sees and changes what."""
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.auth import get_principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.alerts import service as alerts
from app.modules.complaints import service as complaints
from app.modules.findings import service
from tests.conftest import requires_db
from tests.test_seed import COMPLAINTS, INSTITUTIONS

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
    old = [{"id": "z", "bureau_ids": [A], "open": 4, "overdue": 0, "older_than_median": 4, "median_days": 10}]
    by_bureau = service.queue_findings("bureau", old, 3, 0.6)
    assert [f["key"] for f in by_bureau] == ["bottleneck:bureau:z:older_than_median"]
    assert service.queue_findings("institution", old, 3, 0.6) == []  # institutions: overdue measure only


@requires_db
def test_seed_gives_few_bottlenecks_listed_after_transfer_findings(detected):
    found = findings_as(detected, "menon")
    bottlenecks = [f for f in found if f["kind"] == "bottleneck"]
    assert 1 <= len(bottlenecks) <= 5
    by_institution = [f for f in bottlenecks if f["evidence"]["scope"] == "institution"]
    assert by_institution and all(f["evidence"]["measure"] == "overdue_share" for f in by_institution)
    assert all(f["evidence"]["share"] > 0.6 for f in bottlenecks)
    order = ["transfer_loop", "stalled_transfer", "bottleneck", "category_spike"]
    assert [order.index(f["kind"]) for f in found] == sorted(order.index(f["kind"]) for f in found)
    shares = [(f["evidence"]["share"], f["evidence"]["open"]) for f in bottlenecks]
    assert shares == sorted(shares, reverse=True)  # worst first


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
    assert "Case C-090 has moved PGRC to RB to PGRC with no acknowledgement" in alert["body"]
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


# --- Early warning: regional category spike ------------------------------------------------------

DAY = "2026-11-01"


def cell(recent, previous, state="Kerala", category="Fee refund"):
    return {"state": state, "category": category, "recent": recent, "previous": previous, "bureau_ids": [A]}


def test_spike_rule_minimum_ratio_and_its_numbers():
    found = service.spike_findings([cell(10, 8)], 5, 3.0, DAY)  # baseline 8 * 30/90 = 2.67; 10 is 3.75 times it
    assert [f["key"] for f in found] == ["category_spike:Kerala:Fee refund"]
    assert found[0]["evidence"] == {"state": "Kerala", "category": "Fee refund", "recent": 10, "previous": 8,
                                    "baseline": 2.67, "ratio": 3.75, "recent_days": 30, "baseline_days": 90,
                                    "min_count": 5, "ratio_threshold": 3.0, "as_of": DAY}
    assert service.spike_findings([cell(4, 1)], 5, 3.0, DAY) == []   # 12 times its past, but only 4: below the minimum
    assert service.spike_findings([cell(8, 9)], 5, 3.0, DAY) == []   # 8 against a baseline of 3: 2.67 times, not 3
    new = service.spike_findings([cell(5, 0)], 5, 3.0, DAY)          # nothing before: the minimum alone decides
    assert new[0]["evidence"]["ratio"] is None and new[0]["evidence"]["baseline"] == 0


@requires_db
def test_seeded_spike_is_found_once_with_its_counts_and_no_alert(detected):
    spikes = findings_as(detected, "menon", kind="category_spike")
    assert [(f["evidence"]["state"], f["evidence"]["category"]) for f in spikes] == [("Uttar Pradesh", "Fee refund")]
    e = spikes[0]["evidence"]
    assert (e["recent"], e["previous"], e["baseline"], e["ratio"]) == (10, 8, 2.67, 3.75)
    assert spikes[0]["alert_id"] is None and spikes[0]["complaint_id"] is None and spikes[0]["institution_id"] is None
    # Maharashtra / Infrastructure: 4 in 30 days against 1 before, 12 times its past, but under the minimum of 5.
    assert all(f["evidence"]["state"] != "Maharashtra" for f in spikes)

    with session_for(SYSTEM, detected["engine"]) as s:
        assert service.detect(s, SYSTEM)["created"] == 0
        rows = s.execute(text("SELECT count(*) FROM sethu.findings WHERE kind = 'category_spike'")).scalar_one()
        created = s.execute(text("SELECT payload FROM sethu.audit_log WHERE action = 'finding.created'"
                                 " AND payload->>'kind' = 'category_spike'")).scalars().all()
        alerts = s.execute(text(
            "SELECT c.ref FROM sethu.alerts a JOIN sethu.complaints c ON c.id = a.complaint_id"
            " UNION ALL SELECT 'no case' FROM sethu.alerts WHERE complaint_id IS NULL")).scalars().all()
    assert rows == 1 and len(created) == 1 and created[0]["evidence"] == e
    assert alerts == ["C-090"]  # the loop's alert; the spike made none
    spike_bodies = [c["body"] for c in COMPLAINTS if "spike" in c["seed_tags"].split(";")]
    assert not any(b[:30] in json.dumps([spikes[0], created[0]], default=str) for b in spike_bodies)


@requires_db
def test_spike_is_scoped_to_the_bureaus_that_received_it(detected):
    spike = findings_as(detected, "menon", kind="category_spike")[0]
    state = {i["permanent_id"]: i["state"] for i in INSTITUTIONS}
    received = {c["bureau"] for c in COMPLAINTS if float(c["filed_days_ago"]) <= 30 and c["category"] == "Fee refund"
                and state[c["institution_pid"]] == "Uttar Pradesh"}  # every complaint in the cell's last 30 days
    assert set(spike["bureaus"]) == received
    for who, bureau in (("rao", "PGRC"), ("fernandes", "PGRC"), ("iyer", "RB")):
        seen = [f["id"] for f in findings_as(detected, who, kind="category_spike")]
        assert seen == ([spike["id"]] if bureau in received else []), who
    assert [f["id"] for f in findings_as(detected, "das", kind="category_spike")] == [spike["id"]]
    # The seed's spike reached both bureaus, so prove the other half with a spike only RB received.
    goa_rb = cell(6, 0, state="Goa") | {"bureau_ids": [detected["bureau"]["RB"]]}
    rb_only = service.spike_findings([goa_rb], 5, 3.0, DAY)[0]
    with session_for(SYSTEM, detected["engine"]) as s:
        service.repo.insert(s, rb_only, None)
    goa = {who: [f["evidence"]["state"] for f in findings_as(detected, who, kind="category_spike")]
           for who in ("rao", "fernandes", "iyer", "menon")}
    assert "Goa" not in goa["rao"] and "Goa" not in goa["fernandes"]
    assert "Goa" in goa["iyer"] and "Goa" in goa["menon"]


@requires_db
def test_a_spike_that_comes_back_is_reopened_with_its_new_counts(detected, monkeypatch):
    engine, settings = detected["engine"], get_settings()
    first = findings_as(detected, "menon", kind="category_spike")[0]
    assert first["evidence"]["recent"] == 10

    monkeypatch.setattr(settings, "spike_min_count", 50)  # it no longer holds: the detector resolves it
    with session_for(SYSTEM, engine) as s:
        assert service.detect(s, SYSTEM)["resolved"] >= 1
    assert findings_as(detected, "menon", kind="category_spike")[0]["status"] == "resolved"

    with session_for(SYSTEM, engine) as s:  # three more fee-refund complaints in Uttar Pradesh today
        where = s.execute(text(
            "SELECT s.institution_id, s.bureau_id FROM sethu.complaint_summaries s"
            " JOIN sethu.institutions i ON i.id = s.institution_id"
            " WHERE i.state = 'Uttar Pradesh' AND s.category = 'Fee refund' LIMIT 1")).one()
        for n in range(3):
            s.execute(text(
                "INSERT INTO sethu.complaints (ref, source, bureau_id, institution_id, institution_name_raw,"
                " category, body, body_sha256, filed_at)"
                " VALUES (:ref, 'mock', :b, :i, 'test', 'Fee refund', 'synthetic test text', :h, now())"),
                {"ref": f"T-90{n}", "b": where.bureau_id, "i": where.institution_id, "h": f"t{n}"})
    monkeypatch.setattr(settings, "spike_min_count", 5)
    with session_for(SYSTEM, engine) as s:
        assert service.detect(s, SYSTEM)["reopened"] == 1
        reopened = s.execute(text("SELECT payload FROM sethu.audit_log WHERE action = 'finding.reopened'"
                                  " AND entity_id = :i"), {"i": str(first["id"])}).scalar_one()

    again = findings_as(detected, "menon", kind="category_spike")
    assert [f["id"] for f in again] == [first["id"]] and again[0]["status"] == "open"  # the same finding, reopened
    e = again[0]["evidence"]
    assert (e["recent"], e["previous"], e["baseline"], e["ratio"]) == (13, 8, 2.67, 4.88)
    assert e["as_of"] == datetime.now(UTC).date().isoformat()
    assert reopened["evidence"] == e and reopened["status"] == "open"
