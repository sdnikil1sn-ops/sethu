"""Observability: JSON logs with a request id on every line and nothing sensitive in them over a full request
cycle; /metrics for the internal network only; job runs; Keycloak sign-in events, read-only and role-scoped."""
import io
import json
import logging
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.auth import Principal, get_principal
from app.core.config import get_settings
from app.core.logging import JsonFormatter
from app.db.session import SYSTEM, get_engine, session_for
from app.main import app
from app.modules.audit_view import signins
from app.modules.intake import service as intake
from app.worker import _task_finished, _task_started
from tests.test_seed import load

PERSON = {"name": "Ishaan Logcheck", "email": "ishaan.logcheck@sethu.test", "phone": "+91 98000 22222"}
BODY = ("The library has been closed for three weeks and students were told to pay a fine for books they "
        "could not return because the doors were locked.")


@pytest.fixture
def lines(world):
    """Everything logged, formatted exactly as in production, one JSON object per line."""
    out = io.StringIO()
    handler = logging.StreamHandler(out)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    old = root.level
    root.setLevel(logging.DEBUG)
    yield world | {"out": out}
    root.removeHandler(handler)
    root.setLevel(old)
    app.dependency_overrides.clear()


def as_(world, who):
    people = world | {"admin": Principal(str(load.user_id("admin")), "admin", "admin", None)}
    app.dependency_overrides[get_principal] = lambda: people[who]
    return TestClient(app)


def test_a_full_request_cycle_logs_json_with_ids_and_nothing_sensitive(lines):
    admin = Principal(str(load.user_id("admin")), "admin", "admin", None)
    with session_for(SYSTEM, lines["engine"]) as s:
        portal = s.execute(text("SELECT id FROM sethu.intake_sources WHERE name = 'pgrc-portal'")).scalar_one()
    with session_for(admin, lines["engine"]) as s:
        key = intake.issue_key(s, admin, portal)["api_key"]
    edge_id = uuid.uuid4().hex
    complaint = {"institution_name": "Greenfield Institute of Technology", "category": "Library",
                 "body": BODY, "complainant": PERSON}
    sent = TestClient(app).post("/api/v1/intake/submissions", json=complaint, headers={
        "X-Sethu-Key": key, "X-Sethu-Timestamp": str(int(time.time())), "X-Sethu-Nonce": uuid.uuid4().hex,
        "X-Request-ID": edge_id})
    assert sent.status_code == 202 and sent.headers["X-Request-ID"] == edge_id   # the edge's id is kept
    bad = TestClient(app).get("/health/live", headers={"X-Request-ID": "x\nforged line"})
    assert bad.headers["X-Request-ID"] != "x\nforged line"                     # an unsafe id is replaced
    intake.process_due(lines["engine"])
    rao = as_(lines, "rao")
    case = rao.get("/api/v1/cases", params={"q": "Library"}).json()["items"][0]["id"]
    rao.get(f"/api/v1/cases/{case}")
    rao.get("/api/v1/search", params={"q": PERSON["name"]})
    rao.post(f"/api/v1/cases/{case}/actions", json={"action": "note", "note": "Spoke to the librarian."})
    rao.post("/api/v1/intake/upload", content=b"institution_name,category,body\nX,Y,too short\n",
             headers={"Content-Type": "application/octet-stream"})
    as_(lines, "menon").get("/api/v1/audit")

    raw = lines["out"].getvalue().strip().splitlines()
    records = [json.loads(line) for line in raw]          # every line is one JSON object
    assert len(records) > 8 and all({"ts", "level", "logger", "msg", "request_id"} <= set(r) for r in records)
    http = [r for r in records if r["logger"] == "sethu.http"]
    assert len(http) >= 7 and all(r["request_id"] != "-" for r in http)
    assert any(r["request_id"] == edge_id for r in http)
    assert all("{" in r["msg"] or "/api" in r["msg"] or "/health" in r["msg"] for r in http)
    assert not any(case in r["msg"] for r in http)        # route templates, not ids
    everything = "\n".join(raw)
    db_password = get_engine().url.password or "unset-password"
    with open(get_settings().complainant_keys_file, encoding="utf-8") as f:
        keyring = f.read()[30:60]                          # a slice of the key material
    secret = [key, BODY[:30], PERSON["name"], PERSON["email"], PERSON["phone"], "Spoke to the librarian",
              db_password, keyring]
    assert not [s for s in secret if s and s in everything]
    assert get_engine().hide_parameters                  # database errors never print statement values


def test_metrics_are_served_inside_and_refused_through_the_edge(lines):
    with session_for(SYSTEM, lines["engine"]) as s:
        s.execute(text("UPDATE sethu.intake_sources SET marked_down = true WHERE name = 'pgrc-portal'"))
    _task_started(task_id="t-1")
    _task_finished(task_id="t-1", task=type("T", (), {"name": "sethu.findings.detect"})(), state="SUCCESS")
    _task_finished(task_id="t-2", task=type("T", (), {"name": "sethu.alerts.deliver"})(), state="FAILURE")
    client = TestClient(app)
    client.get("/health/live")
    body = client.get("/metrics")
    assert body.status_code == 200 and body.headers["content-type"].startswith("text/plain")
    m = body.text
    for name in ("sethu_http_requests_total", "sethu_http_request_duration_seconds_bucket", "sethu_intake_pending",
                 "sethu_intake_dead", "sethu_intake_failures_in_a_row", "sethu_alerts_failed",
                 "sethu_alerts_pending_approval", "sethu_findings_open"):
        assert f"\n{name}" in "\n" + m, name
    assert "sethu_intake_sources_down 1" in m
    assert 'sethu_job_last_success_timestamp_seconds{job="findings.detect"}' in m
    assert 'sethu_job_failures_total{job="alerts.deliver"} 1' in m
    assert 'route="/health/live"' in m
    assert client.get("/metrics", headers={"X-Forwarded-For": "203.0.113.9"}).status_code == 404
    assert client.get("/metrics", headers={"X-Real-IP": "203.0.113.9"}).status_code == 404
    with session_for(SYSTEM, lines["engine"]) as s:
        bodies = s.execute(text("SELECT left(body, 30) FROM sethu.complaints LIMIT 20")).scalars().all()
    assert not any(b in m for b in bodies)


def test_sign_in_events_are_read_only_role_scoped_and_carry_no_secrets(lines, monkeypatch):
    assert as_(lines, "das").get("/api/v1/audit/signins").status_code == 503   # not configured: says so
    monkeypatch.setattr(get_settings(), "keycloak_events_secret", "test-secret-value-0123456789")
    monkeypatch.setattr(get_settings(), "oidc_jwks_url",
                        "http://keycloak:8080/auth/realms/sethu/protocol/openid-connect/certs")
    calls = []

    def keycloak(request):
        calls.append(request.full_url)
        if request.full_url.endswith("/token"):
            return {"access_token": "eyJ.fake.token"}
        return [{"time": 1763700000000, "type": "LOGIN_ERROR", "clientId": "sethu-web", "ipAddress": "10.0.0.7",
                 "error": "invalid_user_credentials", "sessionId": "abc", "details": {"username": "rao"}}]

    monkeypatch.setattr(signins, "_call", keycloak)
    events = as_(lines, "das").get("/api/v1/audit/signins").json()
    assert events == [{"time": "2025-11-21T04:40:00Z", "type": "LOGIN_ERROR", "username": "rao", "client": "sethu-web",
                       "ip": "10.0.0.7", "error": "invalid_user_credentials"}]
    assert calls[0] == "http://keycloak:8080/auth/realms/sethu/protocol/openid-connect/token"
    assert calls[1].startswith("http://keycloak:8080/auth/admin/realms/sethu/events?max=100&type=LOGIN_ERROR")
    for who in ("menon", "admin"):
        assert as_(lines, who).get("/api/v1/audit/signins").status_code == 200
    for who in ("rao", "fernandes"):
        assert as_(lines, who).get("/api/v1/audit/signins").status_code == 403
    assert "test-secret-value" not in lines["out"].getvalue() and "eyJ.fake.token" not in lines["out"].getvalue()
