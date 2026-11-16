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


@pytest.fixture
def linked(app_engine, world):
    """A suggested link between C-101 (PGRC) and C-102 (RB) with an alert, and a third bureau."""
    with session_for(SYSTEM, app_engine) as s:
        link = s.execute(text(
            "INSERT INTO sethu.overlap_links (complaint_a, complaint_b, tier)"
            " SELECT least(a.id, b.id), greatest(a.id, b.id), 2 FROM sethu.complaints a, sethu.complaints b"
            " WHERE a.ref = 'C-101' AND b.ref = 'C-102' RETURNING id")).scalar_one()
        s.execute(text("INSERT INTO sethu.alerts (kind, overlap_link_id, subject, body)"
                       " VALUES ('overlap', :l, 'subject', 'references only')"), {"l": link})
        third = s.execute(text("INSERT INTO sethu.bureaus (code, name) VALUES ('XB', 'XB') RETURNING id")).scalar_one()
    return world | {"link": link, "third": third}


def _count(session, table):
    return session.execute(text(f"SELECT count(*) FROM sethu.{table}")).scalar_one()  # noqa: S608


def test_a_bureau_cannot_read_links_or_alerts_it_is_not_party_to(app_engine, linked):
    with session_for(Principal("u7", "x", "bureau_head", linked["third"]), app_engine) as s:
        assert (_count(s, "overlap_links"), _count(s, "alerts")) == (0, 0)
        assert s.execute(text("UPDATE sethu.overlap_links SET status = 'approved'")).rowcount == 0
    for party in ("pgrc", "rb"):
        with session_for(Principal("u1", "x", "officer", linked[party]), app_engine) as s:
            assert (_count(s, "overlap_links"), _count(s, "alerts")) == (1, 1)
    with Session(app_engine) as s:  # no request context
        assert (_count(s, "overlap_links"), _count(s, "alerts")) == (0, 0)


@pytest.mark.parametrize("role", ["oversight", "admin", "auditor"])
def test_reading_roles_see_links_and_alerts_but_cannot_decide(app_engine, linked, role):
    with session_for(Principal("u2", "x", role, None), app_engine) as s:
        assert (_count(s, "overlap_links"), _count(s, "alerts")) == (1, 1)
        assert s.execute(text("UPDATE sethu.overlap_links SET status = 'approved'")).rowcount == 0


def test_only_the_detector_creates_links_and_only_the_worker_changes_alerts(app_engine, linked):
    officer = Principal("u1", "rao", "officer", linked["pgrc"])
    with pytest.raises(DBAPIError), session_for(officer, app_engine) as s:
        s.execute(text("INSERT INTO sethu.overlap_links (complaint_a, complaint_b, tier)"
                       " SELECT complaint_a, complaint_b, 3 FROM sethu.overlap_links"))
    with session_for(officer, app_engine) as s:
        assert s.execute(text("UPDATE sethu.overlap_links SET status = 'approved'")).rowcount == 1  # a party decides
        s.execute(text("INSERT INTO sethu.alerts (kind, overlap_link_id, subject, body)"
                       " VALUES ('overlap', :l, 's', 'b')"), {"l": linked["link"]})  # and may queue its alert
        assert s.execute(text("UPDATE sethu.alerts SET status = 'sent'")).rowcount == 0
    with pytest.raises(DBAPIError), session_for(Principal("u7", "x", "officer", linked["third"]), app_engine) as s:
        s.execute(text("INSERT INTO sethu.alerts (kind, overlap_link_id, subject, body)"
                       " VALUES ('overlap', :l, 's', 'b')"), {"l": linked["link"]})
    with session_for(SYSTEM, app_engine) as s:
        assert s.execute(text("UPDATE sethu.alerts SET status = 'sent'")).rowcount == 2


def test_findings_are_read_by_the_bureaus_involved_and_written_by_the_detector(app_engine, world):
    with session_for(SYSTEM, app_engine) as s:
        s.execute(text("INSERT INTO sethu.findings (kind, key, bureau_ids) VALUES ('bottleneck', 'rb-only', :b)"),
                  {"b": [world["rb"]]})
    officer = Principal("u1", "rao", "officer", world["pgrc"])
    with session_for(officer, app_engine) as s:
        assert s.execute(text("SELECT count(*) FROM sethu.findings")).scalar_one() == 0
        assert s.execute(text("UPDATE sethu.findings SET status = 'dismissed'")).rowcount == 0
    with pytest.raises(DBAPIError):
        with session_for(officer, app_engine) as s:
            s.execute(text("INSERT INTO sethu.findings (kind, key, bureau_ids) VALUES ('bottleneck', 'x', :b)"),
                      {"b": [world["pgrc"]]})
    with session_for(Principal("u2", "das", "auditor", None), app_engine) as s:
        assert s.execute(text("SELECT count(*) FROM sethu.findings")).scalar_one() == 1
