"""Glossary normalisation (AI Phase A2): Unicode normalisation, longest match first, word boundaries, coverage; the
starter list on the multilingual samples; the admin upload (all-or-nothing, versioned, audited)."""
import csv
import io
import json
from pathlib import Path

import openpyxl
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.ai.glossary import Glossary, normalise
from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.glossary import service
from tests.conftest import requires_db

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = json.loads((ROOT / "backend/tests/data/multilingual/samples.json").read_text(encoding="utf-8"))["samples"]
SEED = list(csv.DictReader(open(ROOT / "seed/glossary.csv", encoding="utf-8")))
ADMIN = Principal("u-admin-glossary", "admin", "admin", None)


def test_longest_match_first_and_word_boundaries():
    g = Glossary([("fee", "fee"), ("fee refund", "fee refund"), ("refund", "refund")])
    assert g.tag("The FEE REFUND is late")["tags"] == ["fee refund"]          # the longer term wins, case-blind
    assert g.tag("feedback on the refund")["tags"] == ["refund"]              # "fee" never inside "feedback"
    found = g.tag("fee, fee refund; fee")
    assert found["tags"] == ["fee", "fee refund"] and len(found["matches"]) == 3


def test_indic_terms_may_take_a_suffix_but_must_start_a_word():
    g = Glossary([("விண்ணப்ப", "application"), ("कॉलेज", "college")])
    assert g.tag("விண்ணப்பத்தை ஏற்கவில்லை")["tags"] == ["application"]       # case ending attached
    assert g.tag("मेडिकलकॉलेज")["tags"] == []                                 # not at a word start


def test_unicode_normalisation_and_coverage():
    g = Glossary([("कॉलेज", "college")])
    decomposed = "कॉलेज"                                                   # the same word, other code points
    assert normalise("कॉ‍लेज") == normalise("कॉलेज") and g.tag(decomposed)["tags"] == ["college"]
    assert g.tag("कॉलेज कॉलेज")["coverage"] == 1.0 and g.tag("कॉलेज abcde")["coverage"] == 0.5
    assert g.tag("")["coverage"] == 0.0


def test_the_starter_glossary_on_the_samples():
    assert len(SEED) >= 100 and all(r["needs_review"] == "true" for r in SEED if r["language"] in
                                    ("ta", "te", "kn", "bn", "mr"))
    g = Glossary([(r["term"], r["english"]) for r in SEED], 1)
    for sample in SAMPLES:
        found = g.tag(sample["text"])
        assert set(sample["tags"]) <= set(found["tags"]), sample["id"]
        assert 0 < found["coverage"] < 1


def csv_bytes(rows: list[list[str]]) -> bytes:
    out = io.StringIO()
    csv.writer(out).writerows([["language", "term", "english", "type", "notes", "needs_review"], *rows])
    return out.getvalue().encode()


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


@requires_db
def test_upload_is_all_or_nothing_versioned_and_audited(world, client):
    app.dependency_overrides[get_principal] = lambda: ADMIN
    good = csv_bytes([["hi", "छात्रवृत्ति", "scholarship", "category", "", "false"],
                      ["ta", "உதவித்தொகை", "scholarship", "category", "", "true"]])
    first = client.post("/api/v1/admin/glossary", content=good, params={"filename": "g.csv"},
                        headers={"Content-Type": "application/octet-stream"})
    assert first.status_code == 201 and first.json()["terms"] == 2
    version = first.json()["version"]
    bad = csv_bytes([["hi", "फीस", "fee", "fee", "", "false"], ["xx1", "", "!! no", "colour", "", "false"],
                     ["hi", "फीस", "fee", "fee", "", "false"]])
    refused = client.post("/api/v1/admin/glossary", content=bad, headers={"Content-Type": "application/octet-stream"})
    assert refused.status_code == 422
    problems = {(e["row"], e["field"]) for e in refused.json()["detail"]["errors"]}
    assert problems == {(2, "language"), (2, "term"), (2, "english"), (2, "type"), (3, "term")}
    listing = client.get("/api/v1/glossary").json()
    assert listing["version"] == version and len(listing["terms"]) == 2          # nothing from the bad file
    with session_for(SYSTEM, world["engine"]) as s:
        entry = s.execute(text("SELECT payload FROM sethu.audit_log WHERE action = 'glossary.uploaded' "
                               "AND entity_id = :v"), {"v": str(version)}).scalar_one()
        assert entry["terms"] == 2 and entry["needs_review"] == 1 and "छात्रवृत्ति" not in json.dumps(entry)
        assert service.current(s).tag("छात्रवृत्ति नहीं मिली")["tags"] == ["scholarship"]


@requires_db
def test_xlsx_upload_and_who_may(world, client):
    book = openpyxl.Workbook()
    book.active.append(["language", "term", "english", "type"])
    book.active.append(["en", "noc", "noc", "document"])
    data = io.BytesIO()
    book.save(data)
    app.dependency_overrides[get_principal] = lambda: world["rao"]
    assert client.post("/api/v1/admin/glossary", content=data.getvalue()).status_code == 403
    assert client.get("/api/v1/glossary").status_code == 200                      # every role may read it
    app.dependency_overrides[get_principal] = lambda: ADMIN
    done = client.post("/api/v1/admin/glossary", content=data.getvalue(), params={"filename": "g.xlsx"},
                       headers={"Content-Type": "application/octet-stream"})
    assert done.status_code == 201 and done.json()["terms"] == 1
