"""Enrichment (AI Phase A2): the pipeline with no models installed (the real fallbacks), each task's fall-through
with stub providers, the stage order (one model at a time), attachments (type and size checks, encryption, Row-Level
Security, audit), human review, and the original text never changing."""
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.ai import catalog, memory, router
from app.ai.providers import Provider, Result
from app.core.auth import get_principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.complaints import service as complaints
from app.modules.enrichment import service as enrichment
from app.modules.glossary import service as glossary
from tests.conftest import requires_db

pytestmark = requires_db
DATA = Path(__file__).parent / "data/multilingual"
SAMPLES = {s["id"]: s for s in json.loads((DATA / "samples.json").read_text(encoding="utf-8"))["samples"]}
SEED = Path(__file__).resolve().parents[2] / "seed/glossary.csv"
CALLS: list[tuple[str, str]] = []


class Fake(Provider):
    """A stub for any task: answers `output` with `confidence`, or fails as told. Records each call."""

    def __init__(self, name, task, output=None, confidence=0.9, fail=False):
        self.name, self.task, self.output, self.confidence, self.fail = name, task, output, confidence, fail

    def run(self, payload):
        CALLS.append((self.task, self.name))
        if self.fail:
            raise RuntimeError("stub failure")
        return Result(self.output if self.output is not None else {"text": payload.get("text")}, self.confidence)

    def validate(self, output):
        return bool(output)


def stub(monkeypatch, name, *args, **kw):
    monkeypatch.setitem(catalog.PROVIDERS, name, lambda: Fake(name, *args, **kw))


@pytest.fixture(autouse=True)
def fresh(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "ai_models_dir", str(tmp_path))     # no models: real engines unhealthy
    memory.manager.cache_clear()
    router.reset_circuits()
    CALLS.clear()
    yield
    router.reset_circuits()
    memory.manager.cache_clear()


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def file_case(world, sample="hi-1", bureau="PGRC"):
    with session_for(SYSTEM, world["engine"]) as s:
        if not glossary.listing(s)["terms"]:
            glossary.upload(s, SYSTEM, SEED.read_bytes(), "glossary.csv")
        made = complaints.create(s, SYSTEM, bureau_id=world["bureau"][bureau], source="test",
                                 institution_name_raw="Greenfield Institute of Technology", category="Fee refund",
                                 body=SAMPLES[sample]["text"], language="hi", filed_at=datetime.now(UTC),
                                 complainant=None, institution_id=None, audit_extra={})
    return made["id"]


def enriched(world, cid):
    with session_for(SYSTEM, world["engine"]) as s:
        return dict(s.execute(text("SELECT * FROM sethu.complaint_enrichment WHERE complaint_id = :c"),
                              {"c": cid}).mappings().one())


def runs(world, task):
    with session_for(SYSTEM, world["engine"]) as s:
        return [dict(r) for r in s.execute(text("SELECT path, status, provider FROM sethu.ai_runs WHERE task = :t "
                                                "ORDER BY created_at"), {"t": task}).mappings()]


def reviews(world, cid):
    with session_for(SYSTEM, world["engine"]) as s:
        return [dict(r) for r in s.execute(text("SELECT kind, attachment_id, reason, ai_run_id FROM sethu.review_items "
                                                "WHERE complaint_id = :c ORDER BY created_at"), {"c": cid}).mappings()]


def body_of(world, cid):
    with session_for(SYSTEM, world["engine"]) as s:
        return s.execute(text("SELECT body, body_sha256 FROM sethu.complaints WHERE id = :c"), {"c": cid}).one()


def test_with_no_models_every_step_falls_back_and_the_text_is_untouched(world):
    cid = file_case(world)
    assert enriched(world, cid)["status"] == "pending"                        # written with the complaint
    before = body_of(world, cid)
    assert enrichment.enrich_pending(engine=world["engine"]) == {"complaints": 1, "review": 1}
    e = enriched(world, cid)
    assert (e["language"], e["language_candidates"][0]) == ("hi", "hi")       # Unicode script, the fallback
    assert e["translation_path"] == "untranslated" and e["translated_text"] is None   # glossary covers too little
    assert set(SAMPLES["hi-1"]["tags"]) <= set(e["tags"]) and e["glossary_version"] == 1
    assert e["status"] == "review" and [r["kind"] for r in reviews(world, cid)] == ["translation"]
    assert runs(world, "language.detect")[0] == {"path": "fallback", "status": "ok", "provider": "script-lid"}
    assert runs(world, "translate.to_en")[0]["status"] == "human_review"
    after = body_of(world, cid)
    assert after == before and hashlib.sha256(after[0].encode()).hexdigest() == after[1]   # original kept


def test_english_needs_no_translation(world):
    cid = file_case(world, "en-1")
    enrichment.enrich_pending(engine=world["engine"])
    e = enriched(world, cid)
    assert (e["language"], e["translation_path"], e["status"]) == ("en", "not_needed", "done")
    assert runs(world, "translate.to_en") == [] and "scholarship" in e["tags"]


def test_each_task_takes_its_primary_when_it_answers(world, monkeypatch):
    stub(monkeypatch, "fasttext-lid", "language", {"language": "hi", "candidates": ["hi", "mr"]}, 0.97)
    stub(monkeypatch, "indictrans2", "translate", {"text": "The scholarship has not come."}, 0.8)
    cid = file_case(world)
    enrichment.enrich_pending(engine=world["engine"])
    e = enriched(world, cid)
    assert (e["language"], float(e["language_confidence"]), e["language_candidates"]) == ("hi", 0.97, ["hi", "mr"])
    assert (e["translation_path"], e["translated_text"], e["status"]) == ("model", "The scholarship has not come.",
                                                                          "done")
    assert runs(world, "language.detect")[0]["path"] == runs(world, "translate.to_en")[0]["path"] == "primary"


def test_translation_falls_back_to_the_glossary_when_it_covers_enough(world, monkeypatch):
    stub(monkeypatch, "indictrans2", "translate", fail=True)
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.app_settings SET value = '0.3' WHERE key = 'ai.translate.to_en.min_confidence'"))
    try:
        cid = file_case(world)
        enrichment.enrich_pending(engine=world["engine"])
        e = enriched(world, cid)
        assert (e["translation_path"], e["translated_text"]) == ("glossary", None)   # terms only, no translation
        assert runs(world, "translate.to_en")[0] == {"path": "fallback", "status": "ok", "provider": "glossary"}
    finally:
        with session_for(SYSTEM, world["engine"]) as s:
            s.execute(text("UPDATE sethu.app_settings SET value = '0.5' "
                           "WHERE key = 'ai.translate.to_en.min_confidence'"))


def test_an_unsure_language_goes_to_a_person(world, monkeypatch):
    stub(monkeypatch, "fasttext-lid", "language", {"language": "hi"}, 0.2)
    stub(monkeypatch, "script-lid", "language", {"language": "hi"}, 0.3)
    cid = file_case(world)
    enrichment.enrich_pending(engine=world["engine"])
    e = enriched(world, cid)
    assert e["language"] == "unknown" and e["translation_path"] == "untranslated" and e["status"] == "review"
    assert [r["kind"] for r in reviews(world, cid)] == ["language", "translation"]
    assert all(r["ai_run_id"] for r in reviews(world, cid))


def attach(client, world, cid, data, who="rao", name="scan.png"):
    app.dependency_overrides[get_principal] = lambda: world[who]
    return client.post(f"/api/v1/cases/{cid}/attachments", content=data, params={"filename": name},
                       headers={"Content-Type": "application/octet-stream"})


def test_ocr_falls_back_and_when_all_fail_needs_manual_entry(world, client, monkeypatch):
    stub(monkeypatch, "rapidocr", "ocr", fail=True)
    stub(monkeypatch, "tesseract", "ocr", {"text": "छात्रवृत्ति नहीं मिली"}, 0.8)
    cid = file_case(world)
    assert attach(client, world, cid, (DATA / "hi-1.png").read_bytes()).status_code == 201
    enrichment.enrich_pending(engine=world["engine"])
    e = enriched(world, cid)
    assert (e["ocr_path"], e["ocr_text"]) == ("fallback", "छात्रवृत्ति नहीं मिली")
    stub(monkeypatch, "tesseract", "ocr", fail=True)
    assert attach(client, world, cid, (DATA / "ta-1.png").read_bytes(), name="second.png").status_code == 201
    enrichment.enrich_pending(engine=world["engine"])
    e = enriched(world, cid)
    assert e["ocr_path"] == "manual" and e["ocr_text"] == "छात्रवृत्ति नहीं मिली"     # the earlier text is kept
    ocr_reviews = [r for r in reviews(world, cid) if r["kind"] == "ocr"]
    assert len(ocr_reviews) == 1 and ocr_reviews[0]["attachment_id"] and "manual entry" in ocr_reviews[0]["reason"]


def test_a_pdf_with_good_text_needs_no_ocr_and_garbled_text_is_read_again(world, client, monkeypatch):
    pytest.importorskip("pypdf")
    pytest.importorskip("pypdfium2")
    from app.ai import ocr
    english = ocr.pages(_pdf_with_text(SAMPLES["en-1"]["text"]), "application/pdf", 10, 25_000_000)
    assert english.images == [] and "scholarship" in english.embedded_text        # good text: no OCR
    # A Chrome-made Hindi PDF: pypdf gives vowel signs out of order and NUL bytes, so the page is OCRed instead.
    hindi = ocr.pages((DATA / "hi-1-text.pdf").read_bytes(), "application/pdf", 10, 25_000_000)
    assert hindi.embedded_text == "" and len(hindi.images) == 1
    stub(monkeypatch, "rapidocr", "ocr", {"text": SAMPLES["hi-1"]["text"]}, 0.95)
    cid = file_case(world)
    assert attach(client, world, cid, (DATA / "hi-1-text.pdf").read_bytes(), name="letter.pdf").status_code == 201
    enrichment.enrich_pending(engine=world["engine"])
    e = enriched(world, cid)
    assert e["ocr_path"] == "primary" and e["ocr_text"] == SAMPLES["hi-1"]["text"] and "\x00" not in e["ocr_text"]
    with pytest.raises(ocr.PageLimit):
        ocr.pages((DATA / "hi-1-text.pdf").read_bytes(), "application/pdf", 10, 1000)   # rendering over the limit


def _pdf_with_text(line: str) -> bytes:
    """A one-page PDF with real text in the standard Helvetica font (no shaping involved)."""
    content = f"BT /F1 11 Tf 40 700 Td ({line}) Tj ET".encode()
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
               b"/Resources << /Font << /F1 5 0 R >> >> >>",
               b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for n, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


def test_stages_run_in_order_so_only_one_model_is_needed_at_a_time(world, client, monkeypatch):
    stub(monkeypatch, "fasttext-lid", "language", {"language": "hi"}, 0.97)
    stub(monkeypatch, "rapidocr", "ocr", {"text": "पढ़ा गया पाठ"}, 0.9)
    stub(monkeypatch, "indictrans2", "translate", {"text": "translated"}, 0.9)
    first, second = file_case(world), file_case(world, "hi-2")
    for cid in (first, second):
        attach(client, world, cid, (DATA / "hi-1.png").read_bytes())
    enrichment.enrich_pending(engine=world["engine"])
    order = [task for task, _ in CALLS]
    assert order == ["language", "language", "ocr", "ocr", "translate", "translate"]


def test_attachments_are_checked_encrypted_scoped_and_audited(world, client, monkeypatch):
    cid = file_case(world)
    png = (DATA / "hi-1.png").read_bytes()
    made = attach(client, world, cid, png, name="../../etc/My Scan?.PNG")
    assert made.status_code == 201 and made.json()["filename"] == "My Scan_.png"
    assert made.json()["sha256"] == hashlib.sha256(png).hexdigest()
    assert attach(client, world, cid, png).status_code == 409                           # same file twice
    assert attach(client, world, cid, b"just text, named as a picture", name="x.png").status_code == 415
    assert attach(client, world, cid, (DATA / "te-1.png").read_bytes(), who="iyer").status_code == 404   # RB
    monkeypatch.setattr(enrichment, "MAX_ATTACHMENT_BYTES", 100)
    assert attach(client, world, cid, (DATA / "ta-1.png").read_bytes()).status_code == 413
    with session_for(SYSTEM, world["engine"]) as s:
        stored = s.execute(text("SELECT data_enc FROM sethu.complaint_attachments")).scalar_one()
    assert png[100:140] not in bytes(stored) and bytes(stored)[:2] == b"S1"               # encrypted at rest
    aid = made.json()["id"]
    url = f"/api/v1/cases/{cid}/attachments/{aid}"
    app.dependency_overrides[get_principal] = lambda: world["rao"]
    got = client.get(url)
    assert got.status_code == 200 and got.content == png and got.headers["cache-control"] == "no-store"
    app.dependency_overrides[get_principal] = lambda: world["iyer"]
    assert client.get(url).status_code == 404                                        # hidden from RB
    assert client.get(f"/api/v1/cases/{cid}").json()["attachments"] == []
    app.dependency_overrides[get_principal] = lambda: world["menon"]
    assert client.get(url).status_code == 200                                         # oversight may read it
    with session_for(SYSTEM, world["engine"]) as s:
        entries = [dict(r) for r in s.execute(text("SELECT action, actor, payload FROM sethu.audit_log "
                                                   "WHERE entity_type = 'complaint_attachments' ORDER BY seq")
                                              ).mappings()]
    rao, menon = world["rao"].subject, world["menon"].subject
    assert [(e["action"], e["actor"]) for e in entries] == [("attachment.added", rao), ("attachment.viewed", rao),
                                                           ("attachment.viewed", menon)]
    assert "My Scan" not in json.dumps(entries) and png[:40].hex() not in json.dumps(entries)
    with session_for(world["rao"], world["engine"]) as s:     # only the worker updates: an officer's changes nothing
        assert s.execute(text("UPDATE sethu.complaint_enrichment SET translated_text = 'x'")).rowcount == 0
        assert s.execute(text("UPDATE sethu.complaint_attachments SET ocr_status = 'done'")).rowcount == 0
        assert s.execute(text("UPDATE sethu.complaint_attachments SET data_enc = 'x'")).rowcount == 0
    with pytest.raises(DBAPIError), session_for(world["rao"], world["engine"]) as s:   # no column grant for this
        s.execute(text("UPDATE sethu.complaint_attachments SET filename = 'x.png'"))


def test_review_items_are_scoped_and_resolved_by_the_holding_bureau(world, client):
    file_case(world)
    enrichment.enrich_pending(engine=world["engine"])                     # untranslated: one item for PGRC
    app.dependency_overrides[get_principal] = lambda: world["iyer"]
    assert client.get("/api/v1/review-items").json() == []                # RB does not see PGRC's case
    app.dependency_overrides[get_principal] = lambda: world["menon"]
    items = client.get("/api/v1/review-items").json()
    assert [(i["kind"], i["ref"], i["bureau"]) for i in items] == [("translation", items[0]["ref"], "PGRC")]
    assert client.post(f"/api/v1/review-items/{items[0]['id']}/decision", json={"status": "resolved"}).status_code \
        == 403                                                            # oversight reads; the holder decides
    app.dependency_overrides[get_principal] = lambda: world["rao"]
    done = client.post(f"/api/v1/review-items/{items[0]['id']}/decision", json={"status": "resolved"})
    assert done.status_code == 200 and done.json()["status"] == "resolved"
    assert client.post(f"/api/v1/review-items/{items[0]['id']}/decision", json={"status": "dismissed"}).status_code \
        == 404                                                            # only open items
    assert client.get("/api/v1/review-items").json() == []
    with session_for(SYSTEM, world["engine"]) as s:
        assert s.execute(text("SELECT count(*) FROM sethu.audit_log WHERE action = 'review.resolved'")).scalar() == 1


def test_case_detail_shows_enrichment_only_where_the_text_is_readable(world, client):
    cid = file_case(world)
    enrichment.enrich_pending(engine=world["engine"])
    app.dependency_overrides[get_principal] = lambda: world["rao"]
    own = client.get(f"/api/v1/cases/{cid}").json()
    assert own["body"] == SAMPLES["hi-1"]["text"] and own["enrichment"]["language"] == "hi"
    assert own["enrichment"]["translation_path"] == "untranslated" and "scholarship" in own["enrichment"]["tags"]
    app.dependency_overrides[get_principal] = lambda: world["iyer"]
    other = client.get(f"/api/v1/cases/{cid}").json()
    assert other["body"] is None and other["enrichment"] is None


def test_a_complaint_that_keeps_failing_goes_to_a_person(world, monkeypatch):
    cid = file_case(world)
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.complaint_enrichment SET attempts = 3 WHERE complaint_id = :c"), {"c": cid})
    enrichment.enrich_pending(engine=world["engine"])
    assert enriched(world, cid)["status"] == "review" and "failed 3 times" in reviews(world, cid)[0]["reason"]


def test_key_rotation_reseals_attachments(world, client, tmp_path, monkeypatch):
    """Attachments use the complainant keyring: rotation moves them to the new key, so the old one can go."""
    import base64
    import os as os_

    from app.core.crypto import key_id_of, load_keyring
    cid = file_case(world)
    png = (DATA / "hi-1.png").read_bytes()
    aid = attach(client, world, cid, png).json()["id"]
    current = json.loads(open(get_settings().complainant_keys_file, encoding="utf-8").read())
    new_key = base64.b64encode(os_.urandom(32)).decode()
    both, only_new = tmp_path / "both.json", tmp_path / "new.json"
    both.write_text(json.dumps({"active": "rotated", "keys": current["keys"] | {"rotated": new_key}}))
    only_new.write_text(json.dumps({"active": "rotated", "keys": {"rotated": new_key}}))
    monkeypatch.setattr(get_settings(), "complainant_keys_file", str(both))
    load_keyring.cache_clear()
    try:
        with session_for(SYSTEM, world["engine"]) as s:
            assert enrichment.rekey_attachments(s, SYSTEM) == {"rekeyed": 1, "left": 0}
            assert key_id_of(s.execute(text("SELECT data_enc FROM sethu.complaint_attachments")).scalar_one()) \
                == "rotated"
        monkeypatch.setattr(get_settings(), "complainant_keys_file", str(only_new))   # the old key removed
        load_keyring.cache_clear()
        app.dependency_overrides[get_principal] = lambda: world["rao"]
        assert client.get(f"/api/v1/cases/{cid}/attachments/{aid}").content == png
    finally:
        load_keyring.cache_clear()
