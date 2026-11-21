"""Case workflow: assignment and reassignment, deadlines by category, escalation of a missed deadline, private
notes, closing with a reason and reopening, and the My cases and workload views."""
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.findings import service as findings
from tests.test_seed import load


@pytest.fixture
def flow(world):
    people = world | {
        "admin": Principal(str(load.user_id("admin")), "admin", "admin", None),
        "mdutta": Principal(str(load.user_id("mdutta")), "mdutta", "officer", world["bureau"]["PGRC"]),
    }

    def as_(who):
        app.dependency_overrides[get_principal] = lambda: people[who]
        return TestClient(app)

    def sql(query, **p):
        with session_for(SYSTEM, world["engine"]) as s:
            return s.execute(text(query), p).mappings().all()

    # An open PGRC case, not yet late: the one the tests work on.
    ref = sql("""SELECT c.ref FROM sethu.complaints c JOIN sethu.bureaus b ON b.id = c.bureau_id
                  WHERE b.code = 'PGRC' AND c.status IN ('open', 'in_progress') AND c.due_at > now()
                  ORDER BY c.ref LIMIT 1""")[0]["ref"]
    case = world["case"][ref]

    def act(who, **body):
        return as_(who).post(f"/api/v1/cases/{case}/actions", json=body)

    yield people | {"as_": as_, "sql": sql, "ref": ref, "case_id": case, "act": act,
                    "uid": lambda name: str(sql("SELECT id FROM sethu.app_users WHERE subject = :s",
                                                s=str(load.user_id(name)))[0]["id"])}
    app.dependency_overrides.clear()


def test_assignment_stays_inside_the_holding_bureau_and_reassignment_keeps_history(flow):
    assert flow["act"]("fernandes", action="assign", assignee_id=flow["uid"]("snair")).status_code == 422  # RB officer
    assert flow["act"]("iyer", action="assign", assignee_id=flow["uid"]("snair")).status_code == 403   # RB head
    assert flow["act"]("menon", action="assign", assignee_id=flow["uid"]("rao")).status_code == 403   # oversight
    first = flow["act"]("fernandes", action="assign", assignee_id=flow["uid"]("rao"))
    assert first.status_code == 200 and first.json()["assignee"] == "Anita Rao"
    assert flow["act"]("fernandes", action="assign", assignee_id=flow["uid"]("rao")).status_code == 409
    again = flow["act"]("rao", action="assign", assignee_id=flow["uid"]("mdutta")).json()
    assert again["assignee"] == "Meera Dutta"
    assert [a["assignee"] for a in again["history"] if a["action"] == "assigned"][-2:] == ["Anita Rao", "Meera Dutta"]
    payload = flow["sql"]("SELECT payload FROM sethu.audit_log WHERE action = 'case.assigned' ORDER BY seq DESC"
                          " LIMIT 1")[0]["payload"]
    assert payload["previous_assignee_id"] == flow["uid"]("rao") and payload["assignee_id"] == flow["uid"]("mdutta")
    assert [c["ref"] for c in flow["as_"]("mdutta").get("/api/v1/cases/mine").json()].count(flow["ref"]) == 1
    assert flow["ref"] not in [c["ref"] for c in flow["as_"]("rao").get("/api/v1/cases/mine").json()]
    moved = flow["act"]("fernandes", action="transfer", to_bureau="RB").json()
    assert moved["assignee"] is None  # the receiving bureau assigns its own people


def test_deadlines_by_category_are_set_by_admin_and_used_for_new_and_reopened_cases(flow):
    category = flow["sql"]("SELECT category FROM sethu.complaints WHERE id = :i", i=flow["case_id"])[0]["category"]
    assert flow["as_"]("fernandes").put(f"/api/v1/admin/deadlines/{category}", json={"days": 5}).status_code == 403
    rows = flow["as_"]("admin").put(f"/api/v1/admin/deadlines/{category}", json={"days": 5}).json()
    assert next(r for r in rows if r["category"] == category)["effective_days"] == 5
    assert flow["as_"]("rao").get(f"/api/v1/cases/{flow['case_id']}").json()["deadline_days"] == 5
    assert flow["act"]("rao", action="close").status_code == 422                     # a reason is required
    closed = flow["act"]("rao", action="close", reason="resolved").json()
    assert closed["status"] == "closed" and closed["close_reason"] == "resolved" and closed["can_act"]
    assert flow["act"]("rao", action="reopen").status_code == 422                     # and so is a reopening reason
    reopened = flow["act"]("rao", action="reopen", note="The refund was never received.").json()
    assert reopened["status"] == "open" and reopened["closed_at"] is None
    due = datetime.fromisoformat(reopened["due_at"])
    assert abs(due - (datetime.now(UTC) + timedelta(days=5))) < timedelta(minutes=5)
    actions = [r["action"] for r in flow["sql"]("SELECT action FROM sethu.audit_log ORDER BY seq DESC LIMIT 3")]
    assert actions == ["case.reopened", "case.closed", "deadline.set"]


def test_a_missed_deadline_is_escalated_once_to_the_holding_bureau_head_and_resolved_on_closing(flow):
    with session_for(flow["admin"], flow["engine"]) as s:  # move the clock: the deadline passed yesterday
        s.execute(text("UPDATE sethu.complaints SET due_at = now() - interval '1 day' WHERE id = :i"),
                  {"i": flow["case_id"]})
    with session_for(SYSTEM, flow["engine"]) as s:
        findings.detect(s, SYSTEM)
    with session_for(SYSTEM, flow["engine"]) as s:
        assert findings.detect(s, SYSTEM)["created"] == 0          # a second run adds nothing
    mine = flow["sql"]("""SELECT f.status, f.bureau_ids, a.kind, a.status AS alert, a.recipients
                            FROM sethu.findings f JOIN sethu.alerts a ON a.id = f.alert_id
                           WHERE f.kind = 'deadline_escalation' AND f.complaint_id = :i""", i=flow["case_id"])
    assert len(mine) == 1 and mine[0]["kind"] == "sla" and mine[0]["alert"] == "pending_approval"
    assert mine[0]["recipients"] == ["fernandes@sethu.test"] and mine[0]["bureau_ids"] == [flow["bureau"]["PGRC"]]
    assert flow["ref"] not in str(flow["as_"]("iyer").get("/api/v1/findings").json())  # RB does not see it
    flow["act"]("rao", action="close", reason="resolved")
    with session_for(SYSTEM, flow["engine"]) as s:
        findings.detect(s, SYSTEM)
    assert flow["sql"]("SELECT status FROM sethu.findings WHERE kind = 'deadline_escalation' AND complaint_id = :i",
                       i=flow["case_id"])[0]["status"] == "resolved"


def test_notes_are_read_only_by_the_bureau_holding_the_case(flow):
    flow["act"]("rao", action="note", note="Called the registrar; they promised a reply by Friday.")

    def notes(who):
        history = flow["as_"](who).get(f"/api/v1/cases/{flow['case_id']}").json()["history"]
        return [a["note"] for a in history if a["action"] == "note"]

    assert notes("rao") == notes("fernandes") == ["Called the registrar; they promised a reply by Friday."]
    assert notes("menon") == [] and notes("das") == []
    flow["act"]("fernandes", action="transfer", to_bureau="RB")
    assert notes("rao") == []                                     # the sender no longer holds it
    flow["as_"]("iyer").post(f"/api/v1/cases/{flow['case_id']}/actions", json={"action": "acknowledge"})
    assert len(notes("iyer")) == 1                                # the bureau now holding it does


def test_workload_shows_open_overdue_and_unassigned_per_person_to_heads_only(flow):
    flow["act"]("fernandes", action="assign", assignee_id=flow["uid"]("rao"))
    rows = flow["as_"]("fernandes").get("/api/v1/cases/workload").json()
    assert {r["bureau"] for r in rows} == {"PGRC"}
    assert any(r["assignee"] == "Anita Rao" and r["open"] >= 1 for r in rows)
    assert all(r["overdue"] <= r["open"] for r in rows)
    assert flow["as_"]("rao").get("/api/v1/cases/workload").status_code == 403
    assert {r["bureau"] for r in flow["as_"]("menon").get("/api/v1/cases/workload").json()} >= {"PGRC", "RB"}
    assert flow["as_"]("menon").get("/api/v1/cases/mine").status_code == 403
