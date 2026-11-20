"""Directory: people kept in step with their tokens, admin-managed bureaus, alerts that name the
bureaus they cannot reach, and exact bureau codes in search."""
import json
from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.alerts import service as alerts
from app.modules.complaints import service as complaints
from app.modules.overlaps import service as overlaps
from app.modules.search import service as search
from tests.conftest import requires_db

pytestmark = requires_db
ADMIN = Principal("u-admin-dir", "dir-admin", "admin", None, email="dir-admin@sethu.test", full_name="Dir Admin")


@pytest.fixture
def client(world):
    def as_(who):
        app.dependency_overrides[get_principal] = lambda: who if isinstance(who, Principal) else world[who]
        return TestClient(app)
    yield as_
    app.dependency_overrides.clear()


def row(world, subject):
    with session_for(SYSTEM, world["engine"]) as s:
        return s.execute(text("SELECT display_name, email, role, bureau_id FROM sethu.app_users WHERE subject = :s"),
                         {"s": subject}).mappings().first()


def audit_rows(world, action, entity_id):
    with session_for(SYSTEM, world["engine"]) as s:
        return s.execute(text("SELECT payload FROM sethu.audit_log WHERE action = :a AND entity_id = :e ORDER BY seq"),
                         {"a": action, "e": str(entity_id)}).scalars().all()


# --- People ---------------------------------------------------------------------------------------

def test_first_sign_in_creates_the_record_with_email_and_a_bureau_change_reaches_it(client, world):
    pgrc, rb = world["bureau"]["PGRC"], world["bureau"]["RB"]
    newcomer = Principal(str(uuid4()), "nkumar", "officer", pgrc, email="N.Kumar@sethu.test", full_name="Neha Kumar")
    assert client(newcomer).get("/api/v1/me").status_code == 200
    first = row(world, newcomer.subject)
    assert dict(first) == {"display_name": "Neha Kumar", "email": "n.kumar@sethu.test", "role": "officer",
                           "bureau_id": pgrc}
    with session_for(SYSTEM, world["engine"]) as s:
        user_id = s.execute(text("SELECT id FROM sethu.app_users WHERE subject = :s"), {"s": newcomer.subject}).scalar()
    registered = audit_rows(world, "user.registered", user_id)
    assert registered == [{"role": "officer", "bureau_id": str(pgrc), "has_email": True}]

    client(newcomer).get("/api/v1/me")  # nothing changed: nothing written
    assert audit_rows(world, "user.updated", user_id) == []

    moved = replace(newcomer, role="bureau_head", bureau_id=rb)  # changed in Keycloak, then signed in again
    client(moved).get("/api/v1/me")
    assert (row(world, newcomer.subject)["role"], row(world, newcomer.subject)["bureau_id"]) == ("bureau_head", rb)
    updated = audit_rows(world, "user.updated", user_id)
    assert updated == [{"changed": ["bureau_id", "role"], "role": "bureau_head", "bureau_id": str(rb),
                        "has_email": True}]
    assert "n.kumar" not in json.dumps(registered + updated)  # the audit names fields, never the address


def test_a_token_without_email_keeps_the_stored_address(client, world):
    client("iyer").get("/api/v1/me")  # the test tokens carry no e-mail claim
    assert row(world, world["iyer"].subject)["email"] == "iyer@sethu.test"


def test_the_database_lets_a_person_write_only_their_own_row_with_their_token_role(world):
    rao = world["rao"]
    with session_for(rao, world["engine"]) as s, pytest.raises(DBAPIError):
        s.execute(text("UPDATE sethu.app_users SET role = 'admin' WHERE subject = :s"), {"s": rao.subject})
    with session_for(rao, world["engine"]) as s:  # someone else's row: not visible to update at all
        hit = s.execute(text("UPDATE sethu.app_users SET display_name = 'x' WHERE subject = :s"),
                        {"s": world["iyer"].subject}).rowcount
        assert hit == 0
    with session_for(rao, world["engine"]) as s, pytest.raises(DBAPIError):
        s.execute(text("INSERT INTO sethu.app_users (subject, display_name, role) VALUES ('forged', 'x', 'admin')"))


def test_people_without_email_are_flagged_for_the_admin(client, world):
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.app_users SET email = NULL WHERE subject = :s"),
                  {"s": str(__import__("seed.load", fromlist=["user_id"]).user_id("rbhat"))})
    people = client(ADMIN).get("/api/v1/admin/users").json()
    flagged = [p for p in people if p["no_email"]]
    assert [p["display_name"] for p in flagged] == ["Ravi Bhat"] and people[0]["no_email"]  # listed first
    assert client("rao").get("/api/v1/admin/users").status_code == 403


def test_an_alert_names_the_bureau_it_cannot_reach(world):
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.app_users SET email = NULL WHERE role = 'bureau_head' AND bureau_id = :b"),
                  {"b": world["bureau"]["NRB"]})
        overlaps.detect(s, SYSTEM)
        link = next(link["id"] for link in overlaps.links(s, SYSTEM)
                    if {c["ref"] for c in link["cases"]} == {"C-301", "C-302"})  # RB and NRB
    with session_for(world["iyer"], world["engine"]) as s:
        overlaps.decide(s, world["iyer"], link, approve=True)
        shown = next(a for a in alerts.listing(s, world["iyer"]) if a["cases"] == ["C-301", "C-302"]
                     or set(a["cases"]) == {"C-301", "C-302"})
    assert shown["missing_recipients"] == ["NRB"]
    assert shown["recipients"] and all(r in ("iyer@sethu.test", "mkulkarni@sethu.test") for r in shown["recipients"])


# --- Bureaus ---------------------------------------------------------------------------------------

def test_admin_creates_and_deactivates_a_bureau_and_both_are_audited(client, world):
    admin = client(ADMIN)
    made = admin.post("/api/v1/admin/bureaus", json={"code": "srb", "name": "Regional Bureau (Southern Region)"})
    assert made.status_code == 201 and made.json()["code"] == "SRB" and made.json()["active"]
    assert admin.post("/api/v1/admin/bureaus", json={"code": "SRB", "name": "Again"}).status_code == 409
    srb = made.json()["id"]
    off = admin.patch(f"/api/v1/admin/bureaus/{srb}", json={"active": False})
    assert off.status_code == 200 and off.json()["active"] is False
    assert audit_rows(world, "bureau.created", srb) == [
        {"code": "SRB", "name": "Regional Bureau (Southern Region)"}]
    assert audit_rows(world, "bureau.updated", srb) == [{"code": "SRB", "changed": ["active"], "active": False}]
    listed = {b["code"]: b for b in admin.get("/api/v1/admin/bureaus").json()}
    assert set(listed) == {"PGRC", "RB", "NRB", "AB", "SRB"} and listed["RB"]["heads_with_email"] == 2

    for who in ("rao", "fernandes", "menon", "das"):
        assert client(who).post("/api/v1/admin/bureaus", json={"code": "XX", "name": "Nope"}).status_code == 403
        assert client(who).get("/api/v1/admin/bureaus").status_code == 403


def test_the_database_refuses_bureau_writes_from_anyone_but_admin(world):
    with session_for(world["menon"], world["engine"]) as s, pytest.raises(DBAPIError):
        s.execute(text("INSERT INTO sethu.bureaus (code, name) VALUES ('ZZ', 'oversight cannot')"))
    with session_for(world["menon"], world["engine"]) as s:
        assert s.execute(text("UPDATE sethu.bureaus SET name = 'x'")).rowcount == 0


def test_a_deactivated_bureau_takes_no_transfers(client, world):
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.bureaus SET active = false WHERE code = 'AB'"))
        c103 = world["case"]["C-103"]  # open, held by PGRC
    with session_for(world["rao"], world["engine"]) as s, pytest.raises(complaints.CaseError) as refused:
        complaints.act(s, world["rao"], c103, "transfer", to_bureau="AB")
    assert refused.value.status == 422


# --- Search ----------------------------------------------------------------------------------------

def test_a_bureau_code_matches_exactly_in_search(world):
    with session_for(world["menon"], world["engine"]) as s:
        found = search.search(s, "RB", 500)["complaints"]["items"]
    by_bureau = {c["bureau"] for c in found if "bureau" in c["why"]}
    assert by_bureau == {"RB"}  # NRB contains "RB" but is another bureau
