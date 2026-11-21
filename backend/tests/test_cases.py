"""Cases: who can read and change what, the action history and its audit trail, on the seeded data."""
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.audit.service import verify
from app.core.auth import get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.complaints import service
from app.modules.complaints.service import CaseError
from tests.conftest import requires_db

pytestmark = requires_db

C101_PHRASE = "classes are being combined"  # only in the text of C-101 (PGRC)


def scalar(session, sql, **params):
    return session.execute(text(sql), params).scalar_one()


def audit_rows(session):
    return session.execute(text("SELECT action, actor, payload FROM sethu.audit_log ORDER BY seq")).all()


def test_officer_cannot_read_or_change_another_bureaus_complaint(world):
    c101 = world["case"]["C-101"]  # held by PGRC
    with session_for(SYSTEM, world["engine"]) as s:
        audit_before = len(audit_rows(s))

    with session_for(world["iyer"], world["engine"]) as s:
        seen = service.get(s, world["iyer"], c101)
        # The summary fields are there, the text and the history are not.
        assert (seen["ref"], seen["bureau"], seen["category"], seen["status"]) == (
            "C-101", "PGRC", "Faculty shortage", "in_progress")
        assert seen["readable"] is False and seen["can_act"] is False
        assert seen["body"] is None and seen["institution_name_raw"] is None and seen["history"] == []
        # Free text finds it by reference, never by words in a text this officer may not read.
        assert [c["ref"] for c in service.search(s, {"q": "C-101"}, 50, 0)["items"]] == ["C-101"]
        assert service.search(s, {"q": C101_PHRASE}, 50, 0)["total"] == 0
        # The database says the same without the service in the way.
        assert scalar(s, "SELECT count(*) FROM sethu.complaints WHERE id = :i", i=c101) == 0
        assert scalar(s, "SELECT count(*) FROM sethu.case_actions WHERE complaint_id = :i", i=c101) == 0
        assert s.execute(text("UPDATE sethu.complaints SET body = 'x', status = 'closed' WHERE id = :i"),
                         {"i": c101}).rowcount == 0
        for action in ("note", "close", "transfer", "assign"):
            with pytest.raises(CaseError) as refused:
                service.act(s, world["iyer"], c101, action, note="x", to_bureau="RB")
            assert refused.value.status == 403

    for outsider in (world["iyer"], world["das"], world["menon"]):  # history is closed to non-holders
        with pytest.raises(DBAPIError), session_for(outsider, world["engine"]) as s:
            s.execute(text("INSERT INTO sethu.case_actions (complaint_id, action, note) VALUES (:i, 'note', 'x')"),
                      {"i": c101})

    with session_for(world["rao"], world["engine"]) as s:  # the holder reads and searches the text
        mine = service.get(s, world["rao"], c101)
        assert C101_PHRASE in mine["body"] and mine["can_act"] and len(mine["history"]) == 2
        assert [c["ref"] for c in service.search(s, {"q": C101_PHRASE}, 50, 0)["items"]] == ["C-101"]
    with session_for(SYSTEM, world["engine"]) as s:
        assert len(audit_rows(s)) == audit_before  # nothing above was written


def test_transfer_and_acknowledgement_appear_in_the_history(world):
    c101, engine = world["case"]["C-101"], world["engine"]
    with session_for(world["rao"], engine) as s:
        after = service.act(s, world["rao"], c101, "transfer", to_bureau="RB", note="Concerns a regional matter")
        assert (after["bureau"], after["status"], after["awaiting_acknowledgement"]) == ("RB", "transferred", True)
        # The sender can still read it while nobody has acknowledged, but no longer acts on it.
        assert after["readable"] and not after["can_act"]
        with pytest.raises(CaseError):
            service.act(s, world["rao"], c101, "close")

    with session_for(world["iyer"], engine) as s:
        with pytest.raises(CaseError) as early:  # RB must acknowledge before working the case
            service.act(s, world["iyer"], c101, "close")
        assert early.value.status == 409
        after = service.act(s, world["iyer"], c101, "acknowledge")
        assert (after["status"], after["awaiting_acknowledgement"], after["can_act"]) == ("in_progress", False, True)
        assert [(a["action"], a["from_bureau"], a["to_bureau"], a["actor"]) for a in after["history"][-2:]] == [
            ("transferred", "PGRC", "RB", "Anita Rao"), ("acknowledged", "PGRC", "RB", "Suresh Iyer")]
        assert after["history"][-1]["acknowledged_at"] is not None
        assert [a["created_at"] for a in after["history"]] == sorted(a["created_at"] for a in after["history"])

    with session_for(world["rao"], engine) as s:  # acknowledged: PGRC has let go
        assert service.get(s, world["rao"], c101)["readable"] is False
    with session_for(SYSTEM, engine) as s:
        assert [(r.action, r.actor, r.payload["from"], r.payload["to"]) for r in audit_rows(s)[-2:]] == [
            ("case.transferred", world["rao"].subject, "PGRC", "RB"),
            ("case.acknowledged", world["iyer"].subject, "PGRC", "RB")]
        assert verify(s).ok


def test_loop_case_c090_shows_both_unacknowledged_transfers(world):
    c090 = world["case"]["C-090"]
    with session_for(world["rao"], world["engine"]) as s:  # PGRC holds it again
        case = service.get(s, world["rao"], c090)
        hops = [(a["from_bureau"], a["to_bureau"], a["acknowledged_at"]) for a in case["history"]
                if a["action"] == "transferred"]
        assert hops == [("PGRC", "RB", None), ("RB", "PGRC", None)]
        assert not [a for a in case["history"] if a["action"] == "acknowledged"]
        assert (case["bureau"], case["status"], case["awaiting_acknowledgement"], case["overdue"]) == (
            "PGRC", "transferred", True, True)
        assert case["days_remaining"] < 0 and case["can_act"]
    with session_for(world["iyer"], world["engine"]) as s:  # RB sent it back and is still waiting
        waiting = service.get(s, world["iyer"], c090)
        assert waiting["readable"] and not waiting["can_act"]


def test_every_action_is_audited_and_the_chain_verifies(world):
    c103, engine, rao = world["case"]["C-103"], world["engine"], world["rao"]  # open, PGRC
    with session_for(SYSTEM, engine) as s:
        before = len(audit_rows(s))
        fernandes_id = scalar(s, "SELECT id FROM sethu.app_users WHERE subject = :s", s=world["fernandes"].subject)

    steps = [("assign", {"assignee_id": fernandes_id}, "in_progress"), ("note", {"note": "Called the registrar"},
             "in_progress"), ("reply", {}, "replied"),
             ("close", {"note": "Refund paid", "reason": "resolved"}, "closed")]
    for action, extra, status in steps:
        with session_for(rao, engine) as s:  # one transaction per action, as one request would be
            assert service.act(s, rao, c103, action, **extra)["status"] == status

    with session_for(rao, engine) as s:
        case = service.get(s, rao, c103)
        assert [a["action"] for a in case["history"]] == ["filed", "assigned", "note", "replied", "closed"]
        # Changed in Phase 3: a closed case still offers one action, reopening (tests/test_workflow.py).
        assert case["history"][1]["assignee"] == "Maria Fernandes" and case["closed_at"] and case["can_act"]
        for action, extra in (("note", {"note": "late"}), ("close", {}), ("transfer", {"to_bureau": "RB"})):
            with pytest.raises(CaseError) as closed:
                service.act(s, rao, c103, action, **extra)
            assert closed.value.status == 409
    # Bad input is refused before anything is written.
    with session_for(world["fernandes"], engine) as s:
        for action, extra in (("note", {"note": "  "}), ("transfer", {"to_bureau": "PGRC"}),
                              ("transfer", {"to_bureau": "NOPE"}), ("assign", {"assignee_id": world["bureau"]["RB"]})):
            with pytest.raises(CaseError) as bad:
                service.act(s, world["fernandes"], world["case"]["C-101"], action, **extra)
            assert bad.value.status == 422

    # A failure after the action rolls back the history row and its audit entry together.
    with pytest.raises(RuntimeError), session_for(world["fernandes"], engine) as s:
        service.act(s, world["fernandes"], world["case"]["C-101"], "note", note="never saved")
        raise RuntimeError("request failed after the action")

    with session_for(SYSTEM, engine) as s:
        written = audit_rows(s)[before:]
        assert [(r.action, r.actor) for r in written] == [
            (f"case.{a}", rao.subject) for a in ("assigned", "note", "replied", "closed")]
        assert all("Called" not in str(r.payload) and "Refund" not in str(r.payload) for r in written)
        assert scalar(s, "SELECT count(*) FROM sethu.case_actions WHERE note = 'never saved'") == 0
        chain = verify(s)
        assert chain.ok and chain.checked == before + 4


def test_list_filters_search_and_institution_timeline(world):
    engine, menon, rao = world["engine"], world["menon"], world["rao"]
    with session_for(menon, engine) as s:  # oversight reads every bureau
        def total(**filters):
            return service.search(s, filters, 200, 0)["total"]

        started = time.perf_counter()
        assert total() == 310 and total(overdue=True) == 25 and total(status="transferred") == 1
        assert sum(total(bureau=b) for b in ("PGRC", "RB", "NRB", "AB")) == 310
        assert total(state="Uttar Pradesh", category="Fee refund") == 24  # the seeded spike and its baseline
        assert total(q="GREENFIELD") == 3 and total(q="100%_") == 0  # case-blind; wildcards are literal
        assert total(q=C101_PHRASE) == 1
        assert time.perf_counter() - started < 1  # checklist: results under 1 second on the seeded data

        greenfield = service.search(s, {"q": "C-101"}, 5, 0)["items"][0]["institution_id"]
        assert total(institution_id=greenfield) == 3 and total(institution_id=greenfield, bureau="RB") == 1
        newest = service.search(s, {}, 1, 0)["items"][0]["filed_at"].date()
        assert 0 < total(filed_from=newest) < 310 and total(filed_to=newest) == 310
        assert total(filed_from=newest, filed_to=newest) == total(filed_from=newest)
        page = service.search(s, {"overdue": True}, 10, 20)
        assert len(page["items"]) == 5 and all(c["overdue"] and c["days_remaining"] < 0 for c in page["items"])

        timeline = service.institution_timeline(s, greenfield)
        assert {a["ref"] for a in timeline["actions"]} == {"C-101", "C-102", "C-103"} and timeline["hidden_cases"] == 0
        assert [a["created_at"] for a in timeline["actions"]] == sorted(a["created_at"] for a in timeline["actions"])
        assert {b["code"] for b in service.options(s)["bureaus"]} == {"PGRC", "RB", "NRB", "AB"}

    with session_for(rao, engine) as s:  # a PGRC officer gets PGRC's part and is told one case is hidden
        timeline = service.institution_timeline(s, greenfield)
        assert {a["ref"] for a in timeline["actions"]} == {"C-101", "C-103"} and timeline["hidden_cases"] == 1
        rows = service.search(s, {"institution_id": greenfield}, 10, 0)["items"]
        assert {c["ref"]: c["readable"] for c in rows} == {"C-101": True, "C-102": False, "C-103": True}


def test_api_hides_text_and_enforces_roles(world):
    client, c101 = TestClient(app), world["case"]["C-101"]
    try:
        app.dependency_overrides[get_principal] = lambda: world["iyer"]
        other = client.get(f"/api/v1/cases/{c101}").json()
        assert other["ref"] == "C-101" and other["body"] is None and other["history"] == [] and not other["can_act"]
        assert client.post(f"/api/v1/cases/{c101}/actions", json={"action": "close"}).status_code == 403
        assert client.get("/api/v1/cases", params={"q": C101_PHRASE}).json()["total"] == 0
        assert client.get("/api/v1/cases", params={"status": "nonsense"}).status_code == 422

        app.dependency_overrides[get_principal] = lambda: world["das"]  # auditor: reads all, changes nothing
        assert C101_PHRASE in client.get(f"/api/v1/cases/{c101}").json()["body"]
        assert client.post(f"/api/v1/cases/{c101}/actions", json={"action": "note", "note": "x"}).status_code == 403

        app.dependency_overrides[get_principal] = lambda: world["rao"]
        assert {a["display_name"] for a in client.get(f"/api/v1/cases/{c101}/assignees").json()} >= {"Anita Rao"}
        done = client.post(f"/api/v1/cases/{c101}/actions", json={"action": "note", "note": "Site visit planned"})
        assert done.status_code == 200 and done.json()["history"][-1]["note"] == "Site visit planned"
        assert client.post(f"/api/v1/cases/{c101}/actions", json={"action": "acknowledge"}).status_code == 409
        page = client.get("/api/v1/cases", params={"overdue": "true", "bureau": "PGRC", "limit": 5}).json()
        assert len(page["items"]) == 5 and page["total"] > 5
    finally:
        app.dependency_overrides.clear()
