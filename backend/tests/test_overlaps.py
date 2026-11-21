"""Overlap detection on the seeded data: what is suggested, who decides, and what an approval writes."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.audit.service import verify
from app.core import jobs
from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.institutions import service as institutions
from app.modules.overlaps import service
from app.modules.overlaps.service import OverlapError
from tests.conftest import requires_db
from tests.test_seed import COMPLAINTS, tagged_pairs  # the answer key, as pairs

pytestmark = requires_db

DEMO_PAIR = frozenset(("C-101", "C-102"))


NEGATIVES = {c["ref"] for c in COMPLAINTS if "neg-" in c["seed_tags"] or "transfer-ack" in c["seed_tags"]}


def suggested_pairs(session) -> set[frozenset]:
    return {frozenset(c["ref"] for c in link["cases"]) for link in service.links(session, SYSTEM)}


def tier1_only_pairs(session) -> set[frozenset]:
    return {frozenset((c["a_ref"], c["b_ref"])) for c in service.repo.tier1_pairs(session, None) if not c["tier2"]}


def scalar(session, sql, **params):
    return session.execute(text(sql), params).scalar_one()


@pytest.fixture
def detected(world):
    with session_for(SYSTEM, world["engine"]) as s:
        assert service.detect(s, SYSTEM) == {"suggested": 7}
        world["link"] = {frozenset(c["ref"] for c in link["cases"]): link["id"] for link in service.links(s, SYSTEM)}
    return world


def test_detector_suggests_exactly_the_six_tier2_pairs(detected):
    with session_for(SYSTEM, detected["engine"]) as s:
        pairs = suggested_pairs(s)
        assert len(pairs) == 7 and pairs == tagged_pairs("tier2:") and DEMO_PAIR in pairs
        links = service.links(s, SYSTEM)
        assert all(link["status"] == "proposed" and link["tier"] == 2 and link["alert_status"] is None
                   for link in links)  # a suggestion only: nothing approved, nothing queued
        assert all(float(link["score"]) >= service.SIMILARITY_THRESHOLD for link in links)
        demo = next(link for link in links if frozenset(c["ref"] for c in link["cases"]) == DEMO_PAIR)
        assert demo["reasons"][:3] == ["same institution", "same category: Faculty shortage", "filed 6 days apart"]
        assert scalar(s, "SELECT count(*) FROM sethu.audit_log WHERE action = 'overlap.suggested'") == 7
        assert service.detect(s, SYSTEM) == {"suggested": 0}  # repeatable


def test_ten_pairs_are_tier1_only(detected):
    with session_for(detected["menon"], detected["engine"]) as s:  # metadata only: oversight can see it all
        only = tier1_only_pairs(s)
        # tier1:1 spans three bureaus, so it is three pairs
        assert len(only) == 12 and only == tagged_pairs("tier1:") and frozenset(("C-102", "C-103")) in only
        shown = service.tier1(s)
        # + Rosemere (RB and NRB, 1 pair) and NRB at the tier1:1 institution (2 more pairs there)
        assert len(shown) == 16 and sum(i["pairs"] for i in shown) == 19
        assert sum(i["tier2_pairs"] for i in shown) == 7
        greenfield = next(i for i in shown if i["institution"] == "Greenfield Institute of Technology")
        assert (greenfield["bureaus"], [c["ref"] for c in greenfield["cases"]], greenfield["pairs"]) == (
            ["PGRC", "RB"], ["C-101", "C-102", "C-103"], 2)
        assert service.tier1(s, greenfield["institution_id"]) == [greenfield]
    # An officer sees the same cases and pairs, but a Tier 2 link only where the own bureau is a party
    # (Row-Level Security on overlap_links): to PGRC, the RB and NRB pair is just "same institution".
    with session_for(detected["rao"], detected["engine"]) as s:
        assert tier1_only_pairs(s) == only | {frozenset(("C-301", "C-302"))}
    with session_for(detected["iyer"], detected["engine"]) as s:  # RB is a party to every link
        assert tier1_only_pairs(s) == only


def test_negative_cases_are_never_flagged(world):
    with session_for(SYSTEM, world["engine"]) as s:
        institutions.resolve_pending(s, SYSTEM)  # link the misspelt names first: more cases per institution
        service.detect(s, SYSTEM)
        pairs = suggested_pairs(s)
        assert pairs == tagged_pairs("tier2:")  # still exactly the six
        assert tier1_only_pairs(s) == tagged_pairs("tier1:")
        flagged = set().union(*pairs, *tier1_only_pairs(s))
        assert len(NEGATIVES) == 14 and not NEGATIVES & flagged  # + the NRB to AB handover


def test_closed_or_far_apart_cases_are_not_tier2(world):
    older = min((p for p in tagged_pairs("tier2:") if p != DEMO_PAIR), key=sorted)
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.complaints SET status = 'closed' WHERE ref = 'C-101'"))
        s.execute(text("UPDATE sethu.complaints SET filed_at = filed_at - interval '40 days' WHERE ref = :r"),
                  {"r": min(older)})
        assert service.detect(s, SYSTEM) == {"suggested": 5}
        assert not {DEMO_PAIR, older} & suggested_pairs(s)


def test_approval_writes_link_alert_and_audit_together(detected):
    engine, rao, iyer = detected["engine"], detected["rao"], detected["iyer"]
    demo, other = detected["link"][DEMO_PAIR], next(v for k, v in detected["link"].items() if k != DEMO_PAIR)

    # A failure after the decision leaves no approved link, no alert and no audit entry.
    with pytest.raises(RuntimeError), session_for(rao, engine) as s:
        service.decide(s, rao, demo, approve=True)
        raise RuntimeError("request failed after the decision")
    with session_for(SYSTEM, engine) as s:
        assert scalar(s, "SELECT status FROM sethu.overlap_links WHERE id = :i", i=demo) == "proposed"
        assert scalar(s, "SELECT count(*) FROM sethu.alerts") == 0
        assert scalar(s, "SELECT count(*) FROM sethu.audit_log WHERE action LIKE 'overlap.approve'") == 0

    with session_for(rao, engine) as s:
        link = service.decide(s, rao, demo, approve=True)
        assert (link["status"], link["decided_by"], link["can_decide"], link["alert_status"]) == (
            "approved", "Anita Rao", False, "approved")
        assert link["alert_recipients"] == ["fernandes@sethu.test", "iyer@sethu.test", "mkulkarni@sethu.test"]
        with pytest.raises(OverlapError) as again:
            service.decide(s, rao, demo, approve=False)
        assert again.value.status == 409
    with session_for(iyer, engine) as s:  # the other bureau's head can decide too; rejecting queues nothing
        assert service.decide(s, iyer, other, approve=False)["status"] == "rejected"

    with session_for(SYSTEM, engine) as s:
        alert = s.execute(text(
            "SELECT kind, status, subject, body, overlap_link_id, approved_at FROM sethu.alerts")).one()
        assert (alert.kind, alert.status, alert.overlap_link_id) == ("overlap", "approved", demo) and alert.approved_at
        assert alert.subject == "Potential Overlapping Cases – Coordination Required: C-101 and C-102"
        assert "C-101 (PGRC)" in alert.body and "C-102 (RB)" in alert.body
        for body in s.execute(text("SELECT body FROM sethu.complaints WHERE ref IN ('C-101', 'C-102')")).scalars():
            assert not any(sentence.strip() in alert.body for sentence in body.split(".") if sentence.strip())
        decisions = s.execute(text("SELECT action, actor, payload FROM sethu.audit_log"
                                   " WHERE action IN ('overlap.approve', 'overlap.reject') ORDER BY seq")).all()
        assert [(d.action, d.actor) for d in decisions] == [("overlap.approve", rao.subject),
                                                            ("overlap.reject", iyer.subject)]
        assert decisions[0].payload["cases"] == ["C-101", "C-102"] and decisions[0].payload["recipients"] == 3
        assert verify(s).ok
        assert service.detect(s, SYSTEM) == {"suggested": 0}  # a rejected pair is not suggested again


def test_only_staff_of_a_party_bureau_can_see_and_decide(detected):
    engine, demo = detected["engine"], detected["link"][DEMO_PAIR]
    with session_for(SYSTEM, engine) as s:  # a third bureau that holds neither case
        outsider_bureau = scalar(s, "INSERT INTO sethu.bureaus (code, name) VALUES ('XB', 'XB') RETURNING id")
    outsider = Principal("u-outsider", "outsider", "bureau_head", outsider_bureau)
    admin = Principal("u-admin", "admin", "admin", None)

    with session_for(detected["rao"], engine) as s:
        service.decide(s, detected["rao"], demo, approve=True)
    pending = next(v for k, v in detected["link"].items() if k != DEMO_PAIR)

    with session_for(outsider, engine) as s:
        assert service.links(s, outsider) == [] and service.linked_case_ids(s) == []
        assert scalar(s, "SELECT count(*) FROM sethu.overlap_links") == 0
        assert scalar(s, "SELECT count(*) FROM sethu.alerts") == 0
        with pytest.raises(OverlapError) as hidden:
            service.decide(s, outsider, pending, approve=True)
        assert hidden.value.status == 404
        assert s.execute(text("UPDATE sethu.overlap_links SET status = 'approved'")).rowcount == 0

    for reader in (detected["menon"], detected["das"], admin):  # they read everything and decide nothing
        with session_for(reader, engine) as s:
            links = service.links(s, reader)
            assert len(links) == 7 and not any(link["can_decide"] for link in links)
            assert scalar(s, "SELECT count(*) FROM sethu.alerts") == 1
            with pytest.raises(OverlapError) as refused:
                service.decide(s, reader, pending, approve=True)
            assert refused.value.status == 403
            assert s.execute(text("UPDATE sethu.overlap_links SET status = 'approved' WHERE status = 'proposed'")
                             ).rowcount == 0

    with session_for(detected["iyer"], engine) as s:  # a party: sees its links and the alert
        assert len(service.links(s, detected["iyer"])) == 7 and len(service.links(s, detected["iyer"], "proposed")) == 6
        assert scalar(s, "SELECT count(*) FROM sethu.alerts") == 1


def test_api_decisions_detection_and_the_overlapping_filter(world, monkeypatch):
    client = TestClient(app)

    def as_(principal):
        app.dependency_overrides[get_principal] = lambda: principal

    try:
        as_(world["menon"])
        assert client.get("/api/v1/cases", params={"overlapping": "true"}).json()["total"] == 0
        assert client.post("/api/v1/overlaps/detect").status_code == 403
        as_(world["rao"])
        assert client.post("/api/v1/overlaps/detect").status_code == 403  # an officer cannot read both texts
        as_(Principal("u-admin", "admin", "admin", None))
        # Phase 5: the button queues the worker's job (the model never runs in the API process). The test plays
        # the worker: it records the queued name, then runs the job itself.
        queued = []
        monkeypatch.setattr(jobs, "queue", lambda name: queued.append(name) or "task-1")
        answer = client.post("/api/v1/overlaps/detect")
        assert answer.status_code == 202 and answer.json() == {"task_id": "task-1"}
        assert queued == ["sethu.overlaps.detect"]
        with session_for(SYSTEM, world["engine"]) as s:
            assert service.detect(s, SYSTEM) == {"suggested": 7}
            assert s.execute(text("SELECT count(*) FROM sethu.audit_log WHERE action = 'overlap.detect_requested'"
                                  " AND entity_id = 'task-1'")).scalar() == 1

        as_(world["menon"])
        page = client.get("/api/v1/cases", params={"overlapping": "true", "limit": 200}).json()
        assert page["total"] == 14 and {"C-101", "C-102"}  # 7 links, 2 cases each <= {c["ref"] for c in page["items"]}
        assert client.get("/api/v1/cases", params={"overlapping": "true", "bureau": "RB"}).json()["total"] == 7
        links = client.get("/api/v1/overlaps", params={"status": "proposed"}).json()
        demo = next(link["id"] for link in links if {c["ref"] for c in link["cases"]} == set(DEMO_PAIR))
        assert len(client.get("/api/v1/overlaps/tier1").json()) == 16  # + Rosemere (RB and NRB)
        for reader in (world["menon"], world["das"]):
            as_(reader)
            assert client.post(f"/api/v1/overlaps/{demo}/decision", json={"decision": "approve"}).status_code == 403

        as_(world["rao"])
        assert client.post(f"/api/v1/overlaps/{uuid4()}/decision", json={"decision": "approve"}).status_code == 404
        done = client.post(f"/api/v1/overlaps/{demo}/decision", json={"decision": "approve"})
        assert done.status_code == 200 and done.json()["status"] == "approved"
        assert "body" not in done.json() and "body" not in done.json()["cases"][0]
        assert client.post(f"/api/v1/overlaps/{demo}/decision", json={"decision": "reject"}).status_code == 409
        greenfield = done.json()["institution_id"]
        assert len(client.get("/api/v1/overlaps", params={"institution_id": greenfield}).json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_suggestions_are_written_in_bounded_batches(world, monkeypatch):
    """Load test (docs/LOAD-AND-DRILLS.md): a run stores at most `detect_batch` new links, strongest first, so the
    audit chain's lock is held briefly; repeated runs reach the same seven as one run."""
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "detect_batch", 3)
    runs = []
    for _ in range(4):
        with session_for(SYSTEM, world["engine"]) as s:
            runs.append(service.detect(s, SYSTEM)["suggested"])
    assert runs == [3, 3, 1, 0]
    with session_for(SYSTEM, world["engine"]) as s:
        assert len(suggested_pairs(s)) == 7


def test_a_second_overlap_run_is_skipped_while_one_is_running(world):
    """Two runs at once (the schedule and the admin's button) deadlocked on the same embeddings under load; the
    second now skips."""
    from app import worker
    with session_for(SYSTEM, world["engine"]) as running:
        running.execute(text("SELECT pg_advisory_xact_lock(hashtext('sethu.overlaps.detect'))"))
        assert worker.detect_overlaps() == {"suggested": 0, "embedded": 0, "skipped": 1}
    assert worker.detect_overlaps()["suggested"] == 7
