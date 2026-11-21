"""Audit-chain anchors: exported by appending, compared with the live chain, and a rewritten entry or a replaced
(shorter) database is reported. Shown to auditors, oversight and admin only."""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.audit import anchor
from app.audit.service import record
from app.core.auth import get_principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.main import app


@pytest.fixture
def anchored(world, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "audit_anchor_dir", str(tmp_path))
    yield world | {"file": tmp_path / anchor.FILE}
    app.dependency_overrides.clear()


def check(world, who="das"):
    app.dependency_overrides[get_principal] = lambda: world[who]
    return TestClient(app).get("/api/v1/audit/anchor")


def test_export_appends_and_the_live_chain_matches(anchored):
    assert check(anchored).json()["problems"] == ["no anchor exported yet"]
    with session_for(SYSTEM, anchored["engine"]) as s:
        first = anchor.export(s)
        record(s, SYSTEM, "test.event", payload={"n": 1})
    with session_for(SYSTEM, anchored["engine"]) as s:
        second = anchor.export(s)
    lines = [json.loads(x) for x in anchored["file"].read_text().splitlines()]
    assert [x["seq"] for x in lines] == [first["seq"], second["seq"]] and second["seq"] == first["seq"] + 1
    assert lines[0]["entries"] >= 1 and len(lines[0]["hash"]) == 64
    report = check(anchored).json()
    assert report["ok"] is True and report["anchors"] == 2 and report["latest"]["seq"] == second["seq"]
    for who in ("menon", "das"):
        assert check(anchored, who).status_code == 200
    for who in ("rao", "fernandes"):
        assert check(anchored, who).status_code == 403


def test_a_rewritten_entry_or_a_replaced_database_is_reported(anchored):
    with session_for(SYSTEM, anchored["engine"]) as s:
        good = anchor.export(s)
    with open(anchored["file"], "a", encoding="utf-8") as f:   # what a different database's chain would show
        f.write(json.dumps({"seq": good["seq"], "hash": "0" * 64, "exported_at": "x", "entries": 1}) + "\n")
        f.write(json.dumps({"seq": good["seq"] + 10_000, "hash": "f" * 64, "exported_at": "y", "entries": 1}) + "\n")
        f.write("not json\n")
    report = check(anchored).json()
    assert report["ok"] is False
    assert any("different hash now" in p for p in report["problems"])
    assert any("missing: the chain was truncated or replaced" in p for p in report["problems"])
    assert any("not a valid anchor" in p for p in report["problems"])
    assert anchor.main("compare") == 1                          # the command fails too


def test_not_configured_is_said_plainly(world, monkeypatch):
    monkeypatch.setattr(get_settings(), "audit_anchor_dir", None)
    report = check(world).json()
    assert report == {"configured": False, "ok": None, "anchors": 0, "problems": [], "live_entries": None,
                      "latest": None}
    with session_for(SYSTEM, world["engine"]) as s:
        assert anchor.export(s)["exported"] is False
        assert s.execute(text("SELECT count(*) FROM sethu.audit_log")).scalar() > 0
    app.dependency_overrides.clear()
