"""The audit screen: who may read the ledger, filters, and a tampered row reported by Verify chain."""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.auth import Principal, get_principal
from app.main import app
from tests.conftest import requires_db

pytestmark = requires_db

ADMIN = Principal("u-admin", "admin", "admin", None)

# The exact statements of docs/RUNBOOK.md, "Tamper demonstration", read from the runbook.
RUNBOOK = (Path(__file__).resolve().parents[2] / "docs" / "RUNBOOK.md").read_text(encoding="utf-8")
TAMPER, RESTORE = re.findall(r'psql -U sethu_owner -d sethu -c "([^"]+)"', RUNBOOK)


@pytest.fixture
def client(world):
    def as_(who):
        app.dependency_overrides[get_principal] = lambda: who if isinstance(who, Principal) else world[who]
        return TestClient(app)
    yield as_
    app.dependency_overrides.clear()


def test_only_auditor_oversight_and_admin_read_the_ledger(client):
    for who in ("rao", "fernandes", "iyer"):
        assert client(who).get("/api/v1/audit").status_code == 403
        assert client(who).get("/api/v1/audit/verify").status_code == 403
    for who in ("das", "menon", ADMIN):
        assert client(who).get("/api/v1/audit").status_code == 200
        assert client(who).get("/api/v1/audit/verify").json()["ok"] is True


def test_newest_first_with_filters(client):
    das = client("das")
    page = das.get("/api/v1/audit", params={"limit": 20}).json()
    seqs = [e["seq"] for e in page["items"]]
    assert seqs == sorted(seqs, reverse=True) and len(seqs) == 20
    assert all(len(e["hash"]) == 64 and len(e["prev_hash"]) == 64 for e in page["items"])
    assert page["actions"] == sorted(set(page["actions"])) and len(page["actions"]) > 1

    action = page["actions"][0]
    family = action.split(".")[0] + "."
    filtered = das.get("/api/v1/audit", params={"action": family, "limit": 200}).json()["items"]
    assert filtered and all(e["action"].startswith(family) for e in filtered)

    older = das.get("/api/v1/audit", params={"before_seq": seqs[-1], "limit": 5}).json()["items"]
    assert [e["seq"] for e in older] == list(range(seqs[-1] - 1, seqs[-1] - 6, -1))

    das.get("/api/v1/audit/verify")  # recorded under Mr. Das's id, shown with his name
    mine = das.get("/api/v1/audit", params={"actor": "das"}).json()["items"]
    assert [e["action"] for e in mine] == ["audit.verify"] and mine[0]["actor_name"] != mine[0]["actor"]
    assert {e["actor"] for e in das.get("/api/v1/audit", params={"actor": "system"}).json()["items"]} == {"system"}
    assert das.get("/api/v1/audit", params={"date_from": "2999-01-01"}).json()["items"] == []
    assert das.get("/api/v1/audit", params={"limit": 0}).status_code == 422


def test_verify_names_a_corrupted_row_and_restoring_it_heals_the_chain(client, owner_engine):
    das = client("das")
    with owner_engine.begin() as conn:
        conn.exec_driver_sql(TAMPER)
    report = das.get("/api/v1/audit/verify").json()
    assert report["ok"] is False and report["broken_seq"] == 5 and report["checked"] == 4
    assert report["reason"] == "row content does not match its hash"
    assert report["row"]["seq"] == 5 and report["row"]["payload"]["tampered"] is True

    with owner_engine.begin() as conn:
        conn.exec_driver_sql(RESTORE)
    healed = das.get("/api/v1/audit/verify").json()
    assert healed["ok"] is True and healed["row"] is None
    with owner_engine.connect() as conn:  # each check is itself on the record
        checks = conn.execute(text("SELECT payload FROM sethu.audit_log WHERE action = 'audit.verify' ORDER BY seq"))
        payloads = checks.scalars().all()
    assert [p["ok"] for p in payloads] == [False, True] and payloads[0]["broken_seq"] == 5
