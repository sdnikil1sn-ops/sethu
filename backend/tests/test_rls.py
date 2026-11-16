from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.auth import Principal
from app.db.session import SYSTEM, session_for
from tests.conftest import requires_db

pytestmark = requires_db


@pytest.fixture
def world(app_engine):
    """Two bureaus, one institution, one complaint in each bureau."""
    with session_for(SYSTEM, app_engine) as s:
        pgrc, rb = (UUID(str(s.execute(text(
            "INSERT INTO sethu.bureaus (code, name) VALUES (:c, :c) RETURNING id"), {"c": c}
        ).scalar_one())) for c in ("PGRC", "RB"))
        inst = s.execute(text(
            "INSERT INTO sethu.institutions (name, state) VALUES ('Greenfield Institute of Technology', 'MH')"
            " RETURNING id")).scalar_one()
        for ref, bureau in (("C-101", pgrc), ("C-102", rb)):
            s.execute(text(
                "INSERT INTO sethu.complaints (ref, source, bureau_id, institution_id, institution_name_raw,"
                " category, body, body_sha256, filed_at)"
                " VALUES (:ref, 'mock', :b, :i, 'GIT Pune', 'faculty_shortage', 'secret text', 'x', now())"),
                {"ref": ref, "b": bureau, "i": inst})
    return {"pgrc": pgrc, "rb": rb}


def _refs(session, relation="complaints"):
    return sorted(r[0] for r in session.execute(text(f"SELECT ref FROM sethu.{relation}")))  # noqa: S608


def test_officer_sees_only_own_bureau_text(app_engine, world):
    officer = Principal("u1", "rao", "officer", world["pgrc"])
    with session_for(officer, app_engine) as s:
        assert _refs(s) == ["C-101"]


def test_officer_sees_cross_bureau_summaries_without_text(app_engine, world):
    officer = Principal("u1", "rao", "officer", world["pgrc"])
    with session_for(officer, app_engine) as s:
        assert _refs(s, "complaint_summaries") == ["C-101", "C-102"]
        columns = s.execute(text("SELECT * FROM sethu.complaint_summaries LIMIT 1")).keys()
        assert "body" not in columns and "complainant_enc" not in columns


@pytest.mark.parametrize("role", ["oversight", "admin", "auditor"])
def test_oversight_roles_see_everything(app_engine, world, role):
    with session_for(Principal("u2", "x", role, None), app_engine) as s:
        assert _refs(s) == ["C-101", "C-102"]


def test_no_request_context_sees_nothing(app_engine, world):
    with Session(app_engine) as s:
        assert _refs(s) == []
        assert _refs(s, "complaint_summaries") == []


def test_officer_cannot_write_into_another_bureau(app_engine, world):
    officer = Principal("u1", "rao", "officer", world["pgrc"])
    with pytest.raises(DBAPIError), session_for(officer, app_engine) as s:
        s.execute(text(
            "INSERT INTO sethu.complaints (ref, source, bureau_id, institution_name_raw, body, body_sha256, filed_at)"
            " VALUES ('C-X', 'mock', :b, 'n', 'b', 'h', now())"), {"b": world["rb"]})
    with session_for(officer, app_engine) as s:
        changed = s.execute(text("UPDATE sethu.complaints SET status = 'closed' WHERE ref = 'C-102'")).rowcount
        assert changed == 0


def test_auditor_cannot_modify_complaints(app_engine, world):
    with session_for(Principal("u3", "aud", "auditor", None), app_engine) as s:
        changed = s.execute(text("UPDATE sethu.complaints SET status = 'closed'")).rowcount
        assert changed == 0


def test_case_action_history_cannot_be_edited(app_engine, world):
    with session_for(SYSTEM, app_engine) as s:
        cid = s.execute(text("SELECT id FROM sethu.complaints WHERE ref = 'C-101'")).scalar_one()
        s.execute(text("INSERT INTO sethu.case_actions (complaint_id, action) VALUES (:c, 'filed')"), {"c": cid})
    with pytest.raises(DBAPIError), session_for(SYSTEM, app_engine) as s:
        s.execute(text("UPDATE sethu.case_actions SET note = 'edited'"))


def test_unknown_bureau_sees_nothing(app_engine, world):
    with session_for(Principal("u9", "x", "officer", uuid4()), app_engine) as s:
        assert _refs(s) == []


@pytest.mark.parametrize("role", ["auditor", "oversight"])
def test_read_only_roles_cannot_add_case_history(app_engine, world, role):
    with pytest.raises(DBAPIError), session_for(Principal("u4", "x", role, None), app_engine) as s:
        s.execute(text("INSERT INTO sethu.case_actions (complaint_id, action)"
                       " SELECT id, 'note' FROM sethu.complaints WHERE ref = 'C-101'"))


def test_a_bureau_can_only_hand_a_case_over_as_itself(app_engine, world):
    officer = Principal("u1", "rao", "officer", world["pgrc"])
    give_away = "UPDATE sethu.complaints SET bureau_id = :to, transferred_from_bureau_id = :sender WHERE ref = 'C-101'"
    with pytest.raises(DBAPIError), session_for(officer, app_engine) as s:  # no sender named
        s.execute(text(give_away), {"to": world["rb"], "sender": None})
    with session_for(officer, app_engine) as s:
        assert s.execute(text(give_away), {"to": world["rb"], "sender": world["pgrc"]}).rowcount == 1
        assert _refs(s) == ["C-101"]  # still readable while unacknowledged
        assert s.execute(text("UPDATE sethu.complaints SET status = 'closed' WHERE ref = 'C-101'")).rowcount == 0
    with session_for(Principal("u5", "iyer", "bureau_head", world["rb"]), app_engine) as s:
        assert s.execute(text("UPDATE sethu.complaints SET transferred_from_bureau_id = NULL"
                              " WHERE ref = 'C-101'")).rowcount == 1
    with session_for(officer, app_engine) as s:
        assert _refs(s) == []
