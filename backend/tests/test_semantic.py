"""The semantic overlap signal: shown beside trigram, off means trigram only, embeddings never leave the
database or reach a log, and Row-Level Security applies to them like the text. A stand-in embedder keeps the
tests fast and deterministic; the real model is checked in the worker image (docs/RUNBOOK.md)."""
import hashlib
import logging
import math

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.auth import Principal, get_principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.overlaps import service

REAL_LOADER = service._embedder  # saved before the fixture swaps in the stand-in

# Two complaints that say the same thing in different words (trigram similarity well under 0.30).
SAID_ONE_WAY = ("The college has kept back the caution deposit of ten thousand rupees for four months after "
                "I withdrew and nobody in accounts answers.")
SAID_ANOTHER = ("Four months since leaving, my Rs 10,000 security money is still not returned; the finance "
                "office ignores every mail I send.")


class StandIn:
    """Same vector for texts sharing a topic word, otherwise near-orthogonal ones."""

    def embed(self, texts):
        for t in texts:
            topic = "deposit" if ("deposit" in t or "security money" in t) else t
            seed = hashlib.sha256(topic.encode()).digest()
            v = [((seed[i % 32] + i * 31) % 97) / 97 - 0.5 for i in range(384)]
            norm = math.sqrt(sum(x * x for x in v))
            yield [x / norm for x in v]


@pytest.fixture
def pair(world, monkeypatch):
    service._embedder.cache_clear()
    monkeypatch.setattr(service, "_embedder", lambda: StandIn())
    with session_for(SYSTEM, world["engine"]) as s:
        ids = s.execute(text("""
            SELECT (SELECT id FROM sethu.bureaus WHERE code = 'PGRC'), (SELECT id FROM sethu.bureaus WHERE code = 'RB'),
                   (SELECT id FROM sethu.institutions WHERE name = 'Sunmere Institute of Management Studies')""")).one()
        for ref, bureau, body in (("SEM-1", ids[0], SAID_ONE_WAY), ("SEM-2", ids[1], SAID_ANOTHER)):
            s.execute(text("""
                INSERT INTO sethu.complaints (ref, source, bureau_id, institution_id, institution_name_raw, category,
                                              body, body_sha256, filed_at, due_at, language)
                VALUES (:r, 'test', :b, :i, 'Sunmere', 'Caution deposit', :body, md5(:body), now(),
                        now() + interval '9 days', 'en')"""), {"r": ref, "b": bureau, "i": ids[2], "body": body})
        trigram = s.execute(text("SELECT similarity(:a, :b)"), {"a": SAID_ONE_WAY, "b": SAID_ANOTHER}).scalar()
    assert trigram < service.SIMILARITY_THRESHOLD  # trigram alone would miss this pair
    yield world


def detect(world):
    with session_for(SYSTEM, world["engine"]) as s:
        service.embed_pending(s)
    with session_for(SYSTEM, world["engine"]) as s:
        service.detect(s, SYSTEM)
    with session_for(SYSTEM, world["engine"]) as s:
        return s.execute(text("""SELECT l.reasons, l.signals FROM sethu.overlap_links l
                                    JOIN sethu.complaints a ON a.id = l.complaint_a
                                   WHERE a.ref IN ('SEM-1', 'SEM-2')""")).mappings().all()


def test_a_paraphrase_is_suggested_with_both_signals_shown(pair):
    links = detect(pair)
    assert len(links) == 1
    signals, reasons = links[0]["signals"], links[0]["reasons"]
    assert signals["fired"] == ["semantic"] and signals["semantic"] >= get_settings().semantic_threshold
    assert signals["trigram"] < service.SIMILARITY_THRESHOLD and signals["model"] == get_settings().embedding_model
    assert any(r.startswith("meaning similarity") and r.endswith("(fired)") for r in reasons)
    assert any(r.startswith("text similarity") and not r.endswith("(fired)") for r in reasons)
    # The seeded trigram suggestions still show their signals, trigram fired.
    with session_for(SYSTEM, pair["engine"]) as s:
        fired = s.execute(text("SELECT signals->'fired' FROM sethu.overlap_links")).scalars().all()
    assert sum("trigram" in f for f in fired) >= 6


def test_switched_off_it_is_trigram_only_and_the_paraphrase_is_missed(pair, monkeypatch):
    monkeypatch.setattr(get_settings(), "semantic_overlap", False)
    REAL_LOADER.cache_clear()
    monkeypatch.setattr(service, "_embedder", REAL_LOADER)  # the real loader, with the setting off
    assert not service.semantic_on()
    assert detect(pair) == []
    with session_for(SYSTEM, pair["engine"]) as s:
        assert s.execute(text("SELECT count(*) FROM sethu.complaint_embeddings")).scalar() == 0
        signals = s.execute(text("SELECT signals FROM sethu.overlap_links")).scalars().all()
    assert signals and all(set(x) == {"trigram", "fired"} and x["fired"] == ["trigram"] for x in signals)


def test_no_embedding_leaves_the_database_or_reaches_a_log(pair, caplog):
    caplog.set_level(logging.DEBUG)
    detect(pair)
    with session_for(SYSTEM, pair["engine"]) as s:
        sample = s.execute(text("SELECT embedding::text FROM sethu.complaint_embeddings LIMIT 1")).scalar()
        assert s.execute(text("SELECT count(*) FROM sethu.complaint_embeddings")).scalar() >= 300
    numbers = sample.strip("[]").split(",")[:3]
    app.dependency_overrides[get_principal] = lambda: pair["menon"]
    client = TestClient(app)
    try:
        sem1 = client.get("/api/v1/cases", params={"q": "SEM-1"}).json()["items"][0]["id"]
        bodies = [client.get(path).text for path in (
            "/api/v1/overlaps", f"/api/v1/cases/{sem1}", "/api/v1/graph", "/api/v1/search?q=deposit",
            "/api/v1/audit?limit=200")]
    finally:
        app.dependency_overrides.clear()
    for body in bodies + [caplog.text]:
        assert '"embedding"' not in body and not any(n in body for n in numbers)
    assert SAID_ONE_WAY[:40] not in caplog.text and SAID_ANOTHER[:40] not in caplog.text


def test_embeddings_are_scoped_like_the_text(pair):
    detect(pair)
    rb = Principal("u", "x", "officer", pair["bureau"]["RB"])
    with session_for(rb, pair["engine"]) as s:
        vectors = set(s.execute(text("SELECT complaint_id FROM sethu.complaint_embeddings")).scalars())
        readable = set(s.execute(text("SELECT id FROM sethu.complaints")).scalars())   # text RB may read
        total = s.execute(text("SELECT count(*) FROM sethu.complaint_summaries")).scalar()
    assert vectors == readable and 0 < len(vectors) < total   # exactly the cases whose text RB may read
    with pytest.raises(DBAPIError, match="row-level security"), session_for(rb, pair["engine"]) as s:
        s.execute(text("""INSERT INTO sethu.complaint_embeddings (complaint_id, model, embedding)
                          SELECT id, 'x', array_fill(0, ARRAY[384])::vector FROM sethu.complaints LIMIT 1"""))
