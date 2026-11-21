"""Complaint intake: the API (key, timestamp, nonce), file and manual channels, the queue with retry and
dead letters, fallback while a primary source is down, duplicate handling, and what never leaks."""
import io
import logging
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.auth import Principal, get_principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.institutions import service as institutions
from app.modules.intake import service
from tests.test_seed import load

BODY = ("Students of the third year were charged Rs 18500 as a development fee that is not in the "
        "notified fee structure, and receipts were refused when parents asked for them.")
NEAR = BODY.replace("third year", "final year").replace("18500", "18600")
PERSON = {"name": "Vihaan Testcase", "email": "vihaan.testcase@sethu.test", "phone": "+91 98000 11111"}
COMPLAINT = {"institution_name": "Greenfield Institute of Technology", "category": "Fee refund",
             "body": BODY, "complainant": PERSON}


@pytest.fixture
def intake(world):
    admin = Principal(str(load.user_id("admin")), "admin", "admin", None)
    with session_for(SYSTEM, world["engine"]) as s:
        portal = s.execute(text("SELECT id FROM sethu.intake_sources WHERE name = 'pgrc-portal'")).scalar_one()
    with session_for(admin, world["engine"]) as s:
        key = service.issue_key(s, admin, portal)["api_key"]

    people = world | {"admin": admin}

    def as_(who):
        app.dependency_overrides[get_principal] = lambda: who if isinstance(who, Principal) else people[who]
        return TestClient(app)

    def post(body=None, key=key, nonce=None, ts=None):
        headers = {"X-Sethu-Key": key, "X-Sethu-Timestamp": str(ts if ts is not None else int(time.time())),
                   "X-Sethu-Nonce": nonce or uuid.uuid4().hex}
        return TestClient(app).post("/api/v1/intake/submissions", json=body or COMPLAINT, headers=headers)

    def run():
        return service.process_due(world["engine"])

    def scalar(sql, **p):
        with session_for(SYSTEM, world["engine"]) as s:
            return s.execute(text(sql), p).scalar()

    yield world | {"admin": admin, "portal": portal, "key": key, "as_": as_, "post": post, "run": run,
                   "scalar": scalar}
    app.dependency_overrides.clear()


def make_due(world):
    """Move the test clock: every waiting item is due now."""
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.intake_items SET next_attempt_at = now() WHERE status = 'pending'"))


def test_api_intake_creates_a_resolved_complaint_with_its_source_and_path(intake):
    r = intake["post"]()
    assert r.status_code == 202 and r.json()["path"] == "primary"
    assert intake["run"]() == {"done": 1}
    row = intake["scalar"]("""SELECT row_to_json(x) FROM (
        SELECT c.ref, c.source, c.resolution_state, c.complainant_enc IS NOT NULL AS sealed,
               (SELECT count(*) FROM sethu.case_actions a WHERE a.complaint_id = c.id AND a.action = 'filed') AS filed
          FROM sethu.complaints c WHERE c.ref LIKE 'IN-%') x""")
    assert row["ref"].startswith("IN-") and row["source"] == "pgrc-portal"
    assert row["resolution_state"] == "auto" and row["sealed"] and row["filed"] == 1
    entry = intake["scalar"]("SELECT payload FROM sethu.audit_log WHERE action = 'complaint.created'"
                             " AND payload ? 'intake_item'")
    assert entry["channel"] == "api" and entry["path"] == "primary" and entry["intake_item"]


def test_a_bad_key_a_stale_timestamp_and_a_replayed_nonce_are_refused(intake):
    assert intake["post"](key="sethu_wrong").status_code == 401
    assert intake["post"](key="").status_code == 401
    assert intake["post"](ts=int(time.time()) - 3600).status_code == 401
    assert intake["post"](nonce="short").status_code == 401
    assert intake["post"]({"body": "x"}, key="sethu_wrong").status_code == 401  # the key is checked first
    invalid = intake["post"]({**COMPLAINT, "body": "too short"})
    assert invalid.status_code == 422 and "body" in invalid.json()["detail"] and "too short" not in invalid.text
    nonce = uuid.uuid4().hex
    assert intake["post"](nonce=nonce).status_code == 202
    replay = intake["post"](nonce=nonce)
    assert replay.status_code == 409 and "replayed" in replay.json()["detail"]
    assert intake["scalar"]("SELECT count(*) FROM sethu.intake_items") == 1  # nothing else was queued


def test_an_exact_duplicate_is_refused_and_a_near_duplicate_is_flagged_for_review(intake):
    intake["post"]()
    intake["run"]()
    spaced = {**COMPLAINT, "body": "  " + BODY.replace(" ", "   ") + " "}  # spacing is normalised
    again = intake["post"](spaced)  # the gateway sees what its own source sent, not the complaints
    assert again.status_code == 409 and again.json()["detail"] == "already received from this source"
    typed = intake["as_"]("rao").post("/api/v1/intake/manual", json=spaced)  # an officer's check sees the case
    assert typed.status_code == 409 and typed.json()["detail"].startswith("duplicate of IN-")
    assert intake["post"]({**COMPLAINT, "body": NEAR}).status_code == 202
    assert intake["run"]() == {"done": 1}
    flagged = intake["as_"]("rao").get("/api/v1/intake/items", params={"review": True}).json()
    assert len(flagged) == 1 and flagged[0]["near_duplicate_of"].startswith("IN-")
    assert intake["as_"]("iyer").post(f"/api/v1/intake/items/{flagged[0]['id']}/reviewed").status_code == 409
    done = intake["as_"]("rao").post(f"/api/v1/intake/items/{flagged[0]['id']}/reviewed")
    assert done.status_code == 200 and done.json()["review_state"] == "reviewed"


def test_a_failing_attempt_is_retried_then_dead_lettered_and_an_admin_can_retry_it(intake, monkeypatch):
    monkeypatch.setattr(get_settings(), "intake_max_attempts", 2)

    def broken(*_a, **_k):
        raise RuntimeError("cascade unavailable")

    monkeypatch.setattr(institutions, "rank", broken)
    intake["post"]()
    assert intake["run"]() == {"retry": 1}
    assert intake["run"]() == {}  # not due yet: it waits (backoff)
    make_due(intake)
    assert intake["run"]() == {"dead": 1}
    dead = intake["as_"]("admin").get("/api/v1/intake/items", params={"status": "dead"}).json()
    assert len(dead) == 1 and dead[0]["last_error"] == "RuntimeError" and dead[0]["can_retry"]
    assert intake["scalar"]("SELECT count(*) FROM sethu.complaints WHERE ref LIKE 'IN-%'") == 0
    assert intake["as_"]("fernandes").post(f"/api/v1/intake/items/{dead[0]['id']}/retry").status_code == 403
    monkeypatch.undo()
    assert intake["as_"]("admin").post(f"/api/v1/intake/items/{dead[0]['id']}/retry").status_code == 200
    assert intake["run"]() == {"done": 1}
    actions = intake["scalar"](
        "SELECT array_agg(action ORDER BY seq) FROM sethu.audit_log WHERE action LIKE 'intake.%'")
    assert actions[-3:] == ["intake.attempt_failed", "intake.dead_lettered", "intake.retry"]


def test_while_the_primary_is_down_its_items_wait_and_the_fallback_spool_takes_over(intake, tmp_path):
    admin = intake["as_"]("admin")
    assert admin.patch(f"/api/v1/intake/sources/{intake['portal']}", json={"marked_down": True}).status_code == 200
    assert intake["post"]().status_code == 202  # still accepted and kept: nothing is dropped
    assert intake["run"]() == {"retry": 1}
    held = intake["as_"]("admin").get("/api/v1/intake/items", params={"status": "pending"}).json()[0]
    assert held["last_error"] == "source pgrc-portal is marked down"

    (tmp_path / "pgrc-spool").mkdir()
    (tmp_path / "pgrc-spool" / "batch.csv").write_text(
        "institution_name,category,body,complainant_name\n"
        f'Greenfield Institute of Technology,Fee refund,"{BODY}",{PERSON["name"]}\n', encoding="utf-8")
    assert service.spool(intake["engine"], str(tmp_path)) == {"files": 1, "accepted": 1, "rejected": 0}
    assert list((tmp_path / "pgrc-spool" / "processed").glob("*batch.csv"))
    assert intake["run"]() == {"done": 1}
    path = intake["scalar"]("SELECT payload->>'path' FROM sethu.audit_log WHERE action = 'complaint.created'"
                            " AND payload->>'source' = 'pgrc-spool'")
    assert path == "fallback"

    admin.patch(f"/api/v1/intake/sources/{intake['portal']}", json={"marked_down": False})
    make_due(intake)
    assert intake["run"]() == {"duplicate": 1}  # the held copy is recognised, not filed twice
    assert intake["scalar"]("SELECT count(*) FROM sethu.complaints WHERE ref LIKE 'IN-%'") == 1
    health = {s["name"]: s for s in admin.get("/api/v1/intake/sources").json()}
    assert health["pgrc-portal"]["last_success_at"] and health["pgrc-portal"]["pending"] == 0


def test_an_upload_reports_bad_rows_by_row_and_field_and_queues_the_good_ones(intake):
    csv_file = (
        "institution_name,category,body,complainant_name,complainant_email\n"
        f'Greenfield Institute of Technology,Fee refund,"{BODY}",{PERSON["name"]},{PERSON["email"]}\n'
        "Greenfield Institute of Technology,Fee refund,too short,Asha Rowtest,asha@sethu.test\n"
        f'Greenfield Institute of Technology,Fee refund,"{NEAR}",Ravi Rowtest,not-an-email\n')
    r = intake["as_"]("rao").post("/api/v1/intake/upload", params={"filename": "batch.csv"},
                                  content=csv_file.encode(), headers={"Content-Type": "application/octet-stream"})
    assert r.status_code == 200
    out = r.json()
    assert out["accepted"] == 1 and out["rejected"] == 2
    assert {(e["row"], e["field"]) for e in out["errors"]} == {(2, "body"), (3, "complainant.email")}
    assert "too short" not in str(out) and "not-an-email" not in str(out)  # positions and rules, never content
    import openpyxl

    book = openpyxl.Workbook()
    book.active.append(["institution_name", "category", "body"])
    book.active.append(["Greenfield Institute of Technology", "Fee refund", NEAR])
    xlsx = io.BytesIO()
    book.save(xlsx)
    r = intake["as_"]("rao").post("/api/v1/intake/upload", params={"filename": "batch.xlsx"}, content=xlsx.getvalue(),
                                  headers={"Content-Type": "application/octet-stream"})
    assert r.json() == {"accepted": 1, "rejected": 0, "errors": []}
    bad = intake["as_"]("rao").post("/api/v1/intake/upload", content=b"name,text\nx,y\n",
                                    headers={"Content-Type": "application/octet-stream"})
    assert bad.status_code == 422 and "header" in bad.json()["detail"]


def test_manual_entry_goes_through_the_same_pipeline(intake):
    r = intake["as_"]("rao").post("/api/v1/intake/manual", json={**COMPLAINT, "institution_name": "Unknownshire Poly"})
    assert r.status_code == 202
    assert intake["run"]() == {"done": 1}
    state = intake["scalar"]("SELECT resolution_state FROM sethu.complaints WHERE source = 'pgrc-manual'")
    assert state == "unresolved"
    assert intake["as_"]("menon").post("/api/v1/intake/manual", json=COMPLAINT).status_code == 403


def test_no_complaint_text_or_complainant_details_in_logs_audit_or_errors(intake, caplog, monkeypatch, tmp_path):
    caplog.set_level(logging.DEBUG)
    intake["post"]()
    intake["post"]({**COMPLAINT, "body": NEAR})
    intake["run"]()
    intake["post"]()  # duplicate, refused
    monkeypatch.setattr(institutions, "rank", lambda *a, **k: (_ for _ in ()).throw(ValueError(BODY)))
    intake["post"]({**COMPLAINT, "body": BODY + " Again."})
    intake["run"]()
    secrets = [BODY[:40], NEAR[:40], PERSON["name"], PERSON["email"], PERSON["phone"]]
    audit = intake["scalar"]("SELECT string_agg(payload::text, ' ') FROM sethu.audit_log")
    errors = intake["scalar"]("SELECT string_agg(coalesce(last_error, ''), ' ') FROM sethu.intake_items")
    stored = intake["scalar"]("SELECT string_agg(encode(payload_enc, 'escape'), ' ') FROM sethu.intake_items")
    for s in secrets:
        assert s not in audit and s not in errors and s not in caplog.text and s not in stored


def test_who_sees_and_does_what_on_the_intake_screens(intake):
    def get(who, path, **params):
        return intake["as_"](who).get(f"/api/v1/intake/{path}", params=params)

    assert get("rao", "sources").status_code == 403
    assert {s["bureau"] for s in get("iyer", "sources").json()} == {"RB"}
    assert {s["bureau"] for s in get("menon", "sources").json()} == {"PGRC", "RB", "NRB", "AB"}
    intake["post"]()
    assert len(get("rao", "items").json()) == 1 and get("iyer", "items").json() == []
    assert intake["as_"]("fernandes").post(
        "/api/v1/intake/sources", json={"name": "pgrc-new", "channel": "api", "bureau": "PGRC"}).status_code == 403
    made = intake["as_"]("admin").post(
        "/api/v1/intake/sources", json={"name": "pgrc-new", "channel": "api", "bureau": "PGRC"})
    assert made.status_code == 201 and not made.json()["has_key"]
    assert intake["as_"]("fernandes").post(f"/api/v1/intake/sources/{made.json()['id']}/key").status_code == 403
    with session_for(service.GATEWAY, intake["engine"]) as s:  # the API gateway reads no complaints
        assert s.execute(text("SELECT count(*) FROM sethu.complaints")).scalar() == 0
        assert s.execute(text("SELECT count(*) FROM sethu.intake_items WHERE channel <> 'api'")).scalar() == 0


def test_the_intake_api_has_a_per_source_quota(intake, monkeypatch):
    monkeypatch.setattr(get_settings(), "intake_rate_per_minute", 2)
    bodies = [{**COMPLAINT, "body": f"{BODY} Case number {n}."} for n in range(4)]
    assert [intake["post"](b).status_code for b in bodies[:2]] == [202, 202]
    refused = intake["post"](bodies[2])
    assert refused.status_code == 429 and refused.headers["Retry-After"] == "60"
    assert intake["scalar"]("SELECT count(*) FROM sethu.intake_items") == 2     # the refused one was not queued
    admin = intake["as_"]("admin")
    assert admin.patch(f"/api/v1/intake/sources/{intake['portal']}", json={"rate_per_minute": 5}).status_code == 200
    assert intake["post"](bodies[3]).status_code == 202                        # a source's own quota wins
