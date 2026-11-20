"""Complainant details: encrypted at rest with a rotatable key, shown only to the bureau holding the
case, and absent from search, reports, exports, logs and audit entries."""
import base64
import json
import logging
import os

import pytest
from cryptography.exceptions import InvalidTag
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.auth import get_principal
from app.core.config import get_settings
from app.core.crypto import Keyring, KeyringError, key_id_of, load_keyring
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.complaints import service as complaints
from app.modules.reports import service as reports
from app.modules.search import service as search
from tests.conftest import requires_db
from tests.test_seed import COMPLAINTS

DETAILS = {"name": "Test Person", "email": "test.person@sethu.test", "phone": "+91 90000 12345"}
SECRETS = [v for c in COMPLAINTS for v in (c["complainant_name"], c["complainant_email"], c["complainant_phone"])]
C101 = next(c for c in COMPLAINTS if c["ref"] == "C-101")


def ring(*ids: str, active: str | None = None) -> Keyring:
    return Keyring(active or ids[-1], {i: os.urandom(32) for i in ids})


# --- The helper ----------------------------------------------------------------------------------

def test_round_trip_binding_and_tampering():
    keys = ring("k1")
    sealed = keys.encrypt(DETAILS, "complaint-a")
    assert keys.decrypt(sealed, "complaint-a") == DETAILS and key_id_of(sealed) == "k1"
    assert b"Test Person" not in sealed and b"sethu.test" not in sealed
    with pytest.raises(InvalidTag):
        keys.decrypt(sealed, "complaint-b")  # copied onto another complaint: refused
    tampered = sealed[:-1] + bytes([sealed[-1] ^ 1])
    with pytest.raises(InvalidTag):
        keys.decrypt(tampered, "complaint-a")
    assert keys.encrypt(DETAILS, "complaint-a") != sealed  # a fresh nonce each time


def test_rotation_keeps_old_values_readable_until_re_encrypted():
    old = ring("k1")
    sealed = old.encrypt(DETAILS, "x")
    both = Keyring("k2", old.keys | {"k2": os.urandom(32)})
    assert both.decrypt(sealed, "x") == DETAILS            # the old key still opens old values
    moved = both.encrypt(both.decrypt(sealed, "x"), "x")
    assert key_id_of(moved) == "k2"
    new_only = Keyring("k2", {"k2": both.keys["k2"]})       # after re-encryption the old key can go
    assert new_only.decrypt(moved, "x") == DETAILS
    with pytest.raises(KeyringError, match="no key 'k1'"):
        new_only.decrypt(sealed, "x")


def test_a_broken_keyring_is_refused_without_showing_a_key():
    with pytest.raises(KeyringError, match="active key id is not in the keyring"):
        Keyring("missing", {"k1": os.urandom(32)})
    with pytest.raises(KeyringError, match="32 bytes"):
        Keyring("k1", {"k1": b"short"})


# --- On the seeded data --------------------------------------------------------------------------

@pytest.fixture
def client(world):
    def as_(who):
        app.dependency_overrides[get_principal] = lambda: world[who]
        return TestClient(app)
    yield as_
    app.dependency_overrides.clear()


@requires_db
def test_stored_only_encrypted_and_shown_only_to_the_holding_bureau(client, world):
    c101 = world["case"]["C-101"]  # held by PGRC
    with session_for(SYSTEM, world["engine"]) as s:
        raw = s.execute(text("SELECT complainant_enc FROM sethu.complaints WHERE id = :i"), {"i": c101}).scalar()
        missing = s.execute(text("SELECT count(*) FROM sethu.complaints WHERE complainant_enc IS NULL")).scalar()
    assert missing == 0 and C101["complainant_name"].encode() not in bytes(raw)

    shown = client("rao").get(f"/api/v1/cases/{c101}").json()  # PGRC officer: the holding bureau
    assert shown["complainant"] == {"name": C101["complainant_name"], "email": C101["complainant_email"],
                                    "phone": C101["complainant_phone"]} and not shown["complainant_withheld"]
    for who in ("menon", "das"):  # oversight and auditor read the case, not the person
        seen = client(who).get(f"/api/v1/cases/{c101}").json()
        assert seen["complainant"] is None and seen["complainant_withheld"] and seen["body"]
    other = client("iyer").get(f"/api/v1/cases/{c101}").json()  # RB: summary only, not even that it exists
    assert other["complainant"] is None and not other["complainant_withheld"]
    c090 = client("iyer").get(f"/api/v1/cases/{world['case']['C-090']}").json()  # RB sent it, PGRC holds it
    assert c090["body"] and c090["complainant"] is None and c090["complainant_withheld"]


@requires_db
def test_never_in_search_lists_reports_exports_audit_or_logs(client, world, caplog):
    caplog.set_level(logging.DEBUG)
    leaks = []

    def check(where: str, blob: str) -> None:
        leaks.extend((where, v) for v in SECRETS if v in blob)

    with session_for(world["menon"], world["engine"]) as s:  # oversight sees the most
        for c in COMPLAINTS[:40]:
            for value in (c["complainant_name"], c["complainant_email"], c["complainant_phone"]):
                found = search.search(s, value, 100)
                assert not any(set(h["why"]) & {"complaint text", "institution name as typed"}
                               for h in found["complaints"]["items"]), value
                results = {k: v for k, v in found.items() if k != "q"}  # "q" is the caller's own query, echoed
                check("search", json.dumps(results, default=str))
        for name in reports.REPORTS:
            check(f"report {name}", json.dumps(reports.run(s, world["menon"], name, None, None), default=str))
            check(f"export {name}", reports.export(s, world["menon"], name, None, None))
    check("case list", client("menon").get("/api/v1/cases", params={"limit": 200}).text)
    client("rao").get(f"/api/v1/cases/{world['case']['C-101']}")  # a request that does decrypt: its logs count
    with session_for(SYSTEM, world["engine"]) as s:
        check("audit log", " ".join(s.execute(text("SELECT payload::text FROM sethu.audit_log")).scalars()))
    check("logs", "\n".join(r.getMessage() for r in caplog.records))
    assert leaks == []


@requires_db
def test_re_encryption_moves_every_value_to_the_new_key(world, tmp_path, monkeypatch):
    current = json.loads(open(get_settings().complainant_keys_file, encoding="utf-8").read())
    rotated = tmp_path / "keys.json"
    rotated.write_text(json.dumps({"active": "test-2", "keys": current["keys"] | {
        "test-2": base64.b64encode(os.urandom(32)).decode()}}))
    monkeypatch.setattr(get_settings(), "complainant_keys_file", str(rotated))
    load_keyring.cache_clear()
    try:
        total = 0
        while True:
            with session_for(SYSTEM, world["engine"]) as s:
                done = complaints.rotate_complainant_keys(s, SYSTEM, batch=100)
            total += done["rekeyed"]
            if not done["left"]:
                break
        assert total == len(COMPLAINTS)
        with session_for(SYSTEM, world["engine"]) as s:
            assert {key_id_of(v) for v in s.execute(text("SELECT complainant_enc FROM sethu.complaints")).scalars()} \
                == {"test-2"}
            audits = s.execute(text("SELECT payload FROM sethu.audit_log WHERE action = 'complainant.rekeyed'"
                                    " ORDER BY seq")).scalars().all()
        assert sum(a["rows"] for a in audits) == len(COMPLAINTS) and audits[0]["from_keys"] == ["test-1"]

        # The old key can now go: the details still open with the new one alone.
        new_only = tmp_path / "new-only.json"
        new_only.write_text(json.dumps({"active": "test-2", "keys": {"test-2": json.loads(rotated.read_text())[
            "keys"]["test-2"]}}))
        monkeypatch.setattr(get_settings(), "complainant_keys_file", str(new_only))
        load_keyring.cache_clear()
        with session_for(world["rao"], world["engine"]) as s:
            assert complaints.get(s, world["rao"], world["case"]["C-101"])["complainant"]["name"] == \
                C101["complainant_name"]
    finally:
        load_keyring.cache_clear()
