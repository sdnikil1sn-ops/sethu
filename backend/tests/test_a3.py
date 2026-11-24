"""AI Phase A3: multilingual matching, semantic institution resolution, classification, officer feedback.

A stand-in E5 (StubE5) keeps the tests fast and deterministic: a text's vector is the sum of one fixed random vector
per word, with a few words mapped across languages to one concept, so a Hindi and an English sentence made of the
same concepts get cosine 1. The real model is measured in tests/test_ai_models_a3.py and scripts/measure_a3.py."""
import hashlib
import json
import logging
import math
import pickle
import random
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.ai import catalog, classify, memory, router
from app.ai.e5 import MODEL
from app.ai.providers import NotApplicable, Provider, Result
from app.ai.semantic import E5Institution, E5Match, FuzzyInstitution, TextMatch
from app.core.auth import Principal, get_principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.complaints import service as complaints
from app.modules.enrichment import service as enrichment
from app.modules.institutions import service as institutions
from app.modules.overlaps import service as overlaps
from app.modules.semantic import service as semantic
from tests.conftest import requires_db

STOP = {"the", "of", "a", "has", "not", "my", "is", "and", "ने", "मेरी", "की", "नहीं", "है"}
CONCEPTS = {"college": ["college", "कॉलेज"], "deposit": ["deposit", "जमा"], "returned": ["returned", "वापस"],
            "rupees": ["rupees", "रुपये"], "greenfield": ["greenfield", "ग्रीनफील्ड"],
            "institute": ["institute", "इंस्टीट्यूट"]}
WORD = {w: c for c, words in CONCEPTS.items() for w in words}
EN = "The college has not returned my deposit of 10000 rupees."
HI = "कॉलेज ने मेरी 10000 रुपये की जमा वापस नहीं की।"


def vec(text_: str) -> list[float]:
    v = [0.0] * 384
    for token in text_.lower().split():
        token = token.strip(".,;:!?()\"'।")
        if token and token not in STOP:
            rng = random.Random(hashlib.sha256(WORD.get(token, token).encode()).digest())  # noqa: S311 - test data
            v = [a + rng.gauss(0, 1) for a in v]
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class StubE5(Provider):
    name, model = "e5", MODEL

    def __init__(self, version="test-v1", fail=False):
        self.version, self.fail = version, fail

    def run(self, payload):
        if self.fail:
            raise RuntimeError("stub failure")
        return Result({"vectors": [vec(t) for t in payload["texts"]], "model": MODEL,
                       "model_version": self.version}, 1.0)

    def validate(self, output):
        return True


@pytest.fixture(autouse=True)
def fresh(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "ai_models_dir", str(tmp_path))     # no real models
    memory.manager.cache_clear()
    router.reset_circuits()
    semantic.bootstrap.cache_clear()
    yield
    router.reset_circuits()
    memory.manager.cache_clear()


@pytest.fixture
def e5(monkeypatch):
    """The stand-in E5, "installed" as version test-v1."""
    monkeypatch.setitem(catalog.PROVIDERS, "e5", lambda: StubE5())
    monkeypatch.setattr(semantic, "installed_version", lambda: "test-v1")
    return monkeypatch


def q(world, sql, **params):
    with session_for(SYSTEM, world["engine"]) as s:
        return [dict(r) for r in s.execute(text(sql), params).mappings()]


def add_pair(world, category="Fee refund"):
    """Two complaints at one institution in two bureaus: the same matter in English (RB) and Hindi (PGRC)."""
    with session_for(SYSTEM, world["engine"]) as s:
        inst = s.execute(text("SELECT id FROM sethu.institutions WHERE name = 'Sunmere Institute of Management "
                              "Studies'")).scalar_one()
        for ref, code, body, lang in (("X-EN", "RB", EN, "en"), ("X-HI", "PGRC", HI, "hi")):
            s.execute(text("""
                INSERT INTO sethu.complaints (ref, source, bureau_id, institution_id, institution_name_raw, category,
                                              body, body_sha256, filed_at, due_at, language, resolution_state)
                VALUES (:r, 'test', :b, :i, 'Sunmere', :cat, :body, md5(:body), now(), now() + interval '9 days',
                        :lang, 'auto')"""),
                {"r": ref, "b": world["bureau"][code], "i": inst, "cat": category, "body": body, "lang": lang})
        assert s.execute(text("SELECT similarity(:a, :b)"), {"a": EN, "b": HI}).scalar() < 0.30  # trigram cannot


def detect(world):
    with session_for(SYSTEM, world["engine"]) as s:
        return overlaps.detect(s, SYSTEM)


def pair_link(world):
    rows = q(world, """SELECT l.* FROM sethu.overlap_links l JOIN sethu.complaints a ON a.id = l.complaint_a
                        JOIN sethu.complaints b ON b.id = l.complaint_b WHERE a.ref LIKE 'X-%' AND b.ref LIKE 'X-%'""")
    return rows[0] if rows else None


# --- matching -----------------------------------------------------------------------------------------------

SETTINGS = {"e5_threshold": 0.88, "trigram_threshold": 0.30, "confidence_span": 0.06, "agreement_bonus": 0.15,
            "disagreement_penalty": 0.25}


def test_match_providers_fall_through_and_agreement_moves_confidence():
    pair = {"semantic": None, "trigram": 0.5, "same_language": False}
    with pytest.raises(NotApplicable):
        E5Match().run({"pair": pair, "settings": SETTINGS})          # no vectors
    with pytest.raises(NotApplicable):
        TextMatch().run({"pair": pair, "settings": SETTINGS})        # different languages: trigram cannot judge
    alone = E5Match().run({"pair": {"semantic": 0.91, "trigram": 0.0, "same_language": False}, "settings": SETTINGS})
    agree = E5Match().run({"pair": {"semantic": 0.91, "trigram": 0.45, "same_language": True}, "settings": SETTINGS})
    clash = E5Match().run({"pair": {"semantic": 0.91, "trigram": 0.05, "same_language": True}, "settings": SETTINGS})
    assert alone.output["matched"] and alone.output["agreement"] == "not compared"
    assert agree.confidence > alone.confidence > clash.confidence and clash.output["agreement"] == "disagree"
    near = E5Match().run({"pair": {"semantic": 0.885, "trigram": 0.0, "same_language": False}, "settings": SETTINGS})
    assert near.confidence < alone.confidence                         # close to the threshold: less sure


@requires_db
def test_without_e5_matching_is_the_trigram_rule_and_says_so(world):
    assert detect(world) == {"suggested": 7}
    links = q(world, "SELECT signals, reasons FROM sethu.overlap_links")
    assert len(links) == 7 and all(x["signals"]["method"] == "text" and x["signals"]["semantic"] is None
                                   and x["signals"]["model_version"] is None for x in links)
    assert all(any(r.startswith("decided by: text similarity") for r in x["reasons"]) for x in links)
    runs = q(world, "SELECT path, status, provider, error FROM sethu.ai_runs WHERE task = 'match.complaints'")
    assert runs and all(r["provider"] == "text-match" and r["path"] == "fallback" for r in runs if r["status"] == "ok")
    assert all("not applicable" in r["error"] for r in runs)           # e5-match had no vectors to judge
    assert detect(world) == {"suggested": 0}                            # each pair is judged once per key
    assert len(q(world, "SELECT 1 FROM sethu.ai_runs WHERE task = 'match.complaints'")) == len(runs)


@requires_db
def test_a_cross_lingual_pair_is_matched_by_e5_with_its_evidence(world, e5):
    add_pair(world)
    assert semantic.reembed(engine=world["engine"])["left"] == 0
    assert q(world, "SELECT value FROM sethu.app_settings WHERE key = 'ai.embedding.active'")[0]["value"] == {
        "model": MODEL, "version": "test-v1"}
    detect(world)
    link = pair_link(world)
    assert link is not None and link["status"] == "proposed"
    sig = link["signals"]
    assert (sig["method"], sig["model"], sig["model_version"], sig["same_language"]) == ("e5", MODEL, "test-v1",
                                                                                        False)
    assert sig["similarity"] >= 0.99 and sig["trigram"] < 0.30 and 0.5 <= sig["confidence"] <= 1
    assert sig["shared"]["category"] == "Fee refund" and len(sig["complaints"]) == 2 and sig["run_id"]
    assert any(r.startswith("decided by: E5 meaning similarity") for r in link["reasons"])
    # Shown on the overlaps screen: the API carries the evidence (numbers and ids, never text or vectors).
    app.dependency_overrides[get_principal] = lambda: world["menon"]
    try:
        body = TestClient(app).get("/api/v1/overlaps").json()
    finally:
        app.dependency_overrides.clear()
    shown = next(i for i in body["items"] if {c["ref"] for c in i["cases"]} == {"X-EN", "X-HI"})
    assert shown["signals"]["method"] == "e5" and shown["signals"]["confidence"] == sig["confidence"]
    assert EN[:20] not in json.dumps(body) and '"embedding"' not in json.dumps(body)


@requires_db
def test_vectors_of_different_models_or_versions_are_never_compared(world, e5):
    add_pair(world)
    ids = {r["ref"]: r["id"] for r in q(world, "SELECT id, ref FROM sethu.complaints WHERE ref LIKE 'X-%'")}
    same = "[" + ",".join(["0.05103104"] * 384) + "]"          # identical unit vectors: cosine 1 if compared
    with session_for(SYSTEM, world["engine"]) as s:
        for cid, (model, version, vector) in ((ids["X-EN"], ("BAAI/bge-small-en-v1.5", "fastembed-0.9.1", same)),
                                              (ids["X-HI"], ("BAAI/bge-small-en-v1.5", "fastembed-0.9.1", same)),
                                              (ids["X-EN"], (MODEL, "v-old", same))):
            s.execute(text("""INSERT INTO sethu.complaint_embeddings (complaint_id, embedding_model,
                              embedding_version, embedding) VALUES (:c, :m, :v, CAST(:e AS vector))"""),
                      {"c": cid, "m": model, "v": version, "e": vector})
        for version in ("fastembed-0.9.1", "v-old", "test-v1"):
            found = [p for p in overlaps.repo.candidates(s, 30, MODEL, version)
                     if {p["complaint_a"], p["complaint_b"]} == set(ids.values())]
            assert found and found[0]["semantic"] is None        # one side has no vector of exactly this version
        bge = [p for p in overlaps.repo.candidates(s, 30, "BAAI/bge-small-en-v1.5", "fastembed-0.9.1")
               if {p["complaint_a"], p["complaint_b"]} == set(ids.values())]
        assert float(bge[0]["semantic"]) > 0.99                  # only with the same model AND version
    semantic.reembed(engine=world["engine"])
    detect(world)
    assert pair_link(world)["signals"]["model_version"] == "test-v1"   # matching used the active version only
    left = q(world, "SELECT embedding_model, embedding_version FROM sethu.complaint_embeddings "
                    "WHERE embedding_version <> 'test-v1'")
    assert len(left) == 3                                                # old vectors kept, still labelled


@requires_db
def test_reembed_resumes_after_an_interruption(world, e5):
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.app_settings SET value = '40' WHERE key = 'ai.embed.reembed_batch'"))
    try:
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            return StubE5(fail=calls["n"] == 2)             # the second batch dies
        e5.setitem(catalog.PROVIDERS, "e5", flaky)
        first = semantic.reembed(engine=world["engine"])
        total = q(world, "SELECT count(*) AS n FROM sethu.complaints")[0]["n"]
        assert first == {"embedded": 40, "left": total - 40}  # the committed batch stays
        router.reset_circuits()
        e5.setitem(catalog.PROVIDERS, "e5", lambda: StubE5())
        assert semantic.reembed(engine=world["engine"]) == {"embedded": total - 40, "left": 0}
        assert semantic.reembed(engine=world["engine"]) == {"embedded": 0, "left": 0}
        rows = q(world, "SELECT count(*) AS n, count(DISTINCT complaint_id) AS d FROM sethu.complaint_embeddings")
        assert rows[0]["n"] == rows[0]["d"] == total
    finally:
        with session_for(SYSTEM, world["engine"]) as s:
            s.execute(text("UPDATE sethu.app_settings SET value = '64' WHERE key = 'ai.embed.reembed_batch'"))


@requires_db
def test_no_vector_reaches_an_api_or_a_log_and_vectors_are_scoped_like_the_text(world, e5, caplog):
    caplog.set_level(logging.DEBUG)
    add_pair(world)
    semantic.reembed(engine=world["engine"])
    detect(world)
    sample = q(world, "SELECT embedding::text AS e FROM sethu.complaint_embeddings LIMIT 1")[0]["e"]
    numbers = sample.strip("[]").split(",")[:3]
    app.dependency_overrides[get_principal] = lambda: world["menon"]
    try:
        client = TestClient(app)
        case = client.get("/api/v1/cases", params={"q": "X-EN"}).json()["items"][0]["id"]
        bodies = [client.get(p).text for p in ("/api/v1/overlaps", f"/api/v1/cases/{case}",
                                               f"/api/v1/cases/{case}/suggestions", "/api/v1/ai/health",
                                               "/api/v1/audit?limit=200")]
    finally:
        app.dependency_overrides.clear()
    for body in [*bodies, caplog.text]:
        assert not any(n in body for n in numbers)
    assert EN[:30] not in caplog.text and HI[:15] not in caplog.text
    rb = Principal("u", "x", "officer", world["bureau"]["RB"])
    with session_for(rb, world["engine"]) as s:
        vectors = set(s.execute(text("SELECT complaint_id FROM sethu.complaint_embeddings")).scalars())
        readable = set(s.execute(text("SELECT id FROM sethu.complaints")).scalars())
    assert vectors == readable


# --- institution resolution ---------------------------------------------------------------------------------

def test_institution_rules_threshold_margin_and_acronym():
    s = {"e5_threshold": 0.93, "e5_margin": 0.03, "fuzzy_threshold": 95, "fuzzy_margin": 5}

    def e5(scores, acronym=False):
        cands = [{"institution_id": f"i{n}", "label": f"L{n}", "score": x} for n, x in enumerate(scores)]
        return E5Institution().run({"e5": cands, "acronym": acronym, "settings": s}).output

    assert e5([0.97, 0.90])["auto"] and e5([0.97, 0.90])["institution_id"] == "i0"
    assert not e5([0.97, 0.95])["auto"] and "too close" in e5([0.97, 0.95])["why"]     # margin
    assert not e5([0.92, 0.10])["auto"] and "below" in e5([0.92, 0.10])["why"]         # threshold
    assert not e5([0.99, 0.10], acronym=True)["auto"]                                  # acronyms: never
    assert len(e5([0.9, 0.8, 0.7, 0.6])["top"]) == 3
    fuzzy = FuzzyInstitution().run({"fuzzy": [{"institution_id": "a", "score": 97}, {"institution_id": "b",
                                                                                     "score": 80}],
                                    "acronym": False, "settings": s}).output
    assert fuzzy["auto"] and fuzzy["institution_id"] == "a"
    with pytest.raises(NotApplicable):
        E5Institution().run({"e5": [], "acronym": False, "settings": s})
    assert institutions.is_acronym("GIT Pune") and not institutions.is_acronym("Greenfield Institute")


def file_case(world, raw, body="Complaint text for the test.", bureau="PGRC", category="Fee refund"):
    with session_for(SYSTEM, world["engine"]) as s:
        return complaints.create(s, SYSTEM, bureau_id=world["bureau"][bureau], source="test",
                                 institution_name_raw=raw, category=category, body=body, language="en",
                                 filed_at=datetime.now(UTC), complainant=None, institution_id=None,
                                 audit_extra={})["id"]


@requires_db
def test_institution_cascade_e5_auto_links_and_unsure_names_go_to_the_officer(world, e5):
    assert semantic.refresh_registry(world["engine"])["added"] > 40
    assert semantic.refresh_registry(world["engine"]) == {"added": 0, "removed": 0}        # computed once
    clear = file_case(world, "Greenfield Institute Technology Pune")
    unsure = file_case(world, "ग्रीनफील्ड इंस्टीट्यूट पुणे")
    acronym = file_case(world, "GFT Pune")
    semantic.resolve_institutions([clear, unsure, acronym], world["engine"])
    rows = {r["id"]: r for r in q(world, "SELECT c.id, c.resolution_state, i.name FROM sethu.complaints c "
                                         "LEFT JOIN sethu.institutions i ON i.id = c.institution_id "
                                         "WHERE c.id = ANY(:ids)", ids=[clear, unsure, acronym])}
    assert (rows[clear]["resolution_state"], rows[clear]["name"]) == ("auto", "Greenfield Institute of Technology")
    assert rows[unsure]["resolution_state"] == rows[acronym]["resolution_state"] == "unresolved"
    step = q(world, "SELECT payload->>'step' AS step FROM sethu.audit_log WHERE action = 'institution.resolve'")
    assert [r["step"] for r in step] == ["e5"]
    with session_for(SYSTEM, world["engine"]) as s:
        queued = {c["id"]: c for c in institutions.queue(s, 500)}
        sug = semantic.for_case(s, unsure)["institution"]
    assert sug["path"] == "model" and sug["status"] == "suggested" and len(sug["candidates"]) <= 3
    first = queued[unsure]["candidates"][0]
    assert first["name"] == "Greenfield Institute of Technology" and first["reason"] == "meaning match (E5)"
    assert len(queued[unsure]["candidates"]) == 3
    kinds = q(world, "SELECT kind FROM sethu.review_items WHERE complaint_id = ANY(:ids)", ids=[unsure, acronym])
    assert [k["kind"] for k in kinds] == ["institution", "institution"]
    # The officer picks; the decision is fed back and audited; the typed name becomes an alias.
    app.dependency_overrides[get_principal] = lambda: world["rao"]
    try:
        r = TestClient(app).post(f"/api/v1/cases/{unsure}/suggestions/institution",
                                 json={"institution_id": str(first["id"])})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200, r.text
    fb = q(world, "SELECT kind, decision, suggested, new_value, decided_by FROM sethu.ai_feedback")
    assert fb == [{"kind": "institution", "decision": "accepted", "suggested": str(first["id"]),
                   "new_value": str(first["id"]), "decided_by": fb[0]["decided_by"]}] and fb[0]["decided_by"]
    assert q(world, "SELECT count(*) AS n FROM sethu.audit_log WHERE action = 'ai.feedback'")[0]["n"] == 1


# --- classification -----------------------------------------------------------------------------------------

def test_classifier_artifact_refuses_anything_but_its_checked_json():
    import numpy as np
    rng = np.random.default_rng(1)
    centres = rng.normal(size=(3, 384))
    x = np.vstack([c + 0.1 * rng.normal(size=(20, 384)) for c in centres])
    y = [lab for lab in ("A", "B", "C") for _ in range(20)]
    artifact, metrics = classify.train(x, y, x[::4], y[::4], MODEL, "test-v1", steps=300)
    sha = classify.checksum(artifact)
    assert classify.load(artifact, sha) is artifact and metrics["holdout_accuracy"] == 1.0
    with pytest.raises(classify.ArtifactError, match="never bytes"):
        classify.load(pickle.dumps(artifact), sha)
    with pytest.raises(classify.ArtifactError, match="unknown classifier format"):
        bad = artifact | {"format": "pickle"}
        classify.load(bad, classify.checksum(bad))
    with pytest.raises(classify.ArtifactError, match="checksum"):
        classify.load(artifact | {"intercept": [9.0] * 3}, sha)
    with pytest.raises(classify.ArtifactError, match="non-finite"):
        bad = artifact | {"temperature": float("nan")}
        classify.load(bad, classify.checksum(bad))
    with pytest.raises(classify.ArtifactError, match="missing or extra"):
        bad = artifact | {"code": "import os"}
        classify.load(bad, classify.checksum(bad))


@requires_db
def test_classification_falls_back_to_rules_then_to_an_officer(world):
    rules = file_case(world, "Greenfield Institute of Technology", body="My scholarship and scholarship arrears are "
                      "pending.", category="Fee refund")
    nothing = file_case(world, "Greenfield Institute of Technology", body="Please look into this matter.")
    semantic.classify_complaints([rules, nothing], world["engine"])     # no E5, no classifier
    with session_for(SYSTEM, world["engine"]) as s:
        got = semantic.for_case(s, rules)["category"]
        none = semantic.for_case(s, nothing)["category"]
    assert (got["suggested"], got["path"], got["provider"]) == ("Scholarship delay", "fallback", "category-rules")
    assert (none["suggested"], none["path"]) == (None, "officer")
    assert [r["kind"] for r in q(world, "SELECT kind FROM sethu.review_items WHERE complaint_id = :c",
                                 c=nothing)] == ["category"]
    semantic.classify_complaints([rules], world["engine"])               # once per key: no second run
    assert len(q(world, "SELECT 1 FROM sethu.ai_runs WHERE task = 'classify.category' AND subject_id = :c",
                 c=str(rules))) == 1


@requires_db
def test_officer_decisions_are_fed_back_append_only_and_audited(world):
    cid = file_case(world, "Greenfield Institute of Technology", body="The scholarship and the scholarship "
                    "arrears have not come.", category="Fee refund")
    semantic.classify_complaints([cid], world["engine"])
    app.dependency_overrides[get_principal] = lambda: world["iyer"]          # RB: not the holding bureau
    client = TestClient(app)
    try:
        assert client.post(f"/api/v1/cases/{cid}/suggestions/category",
                           json={"category": "Scholarship delay"}).status_code == 404
        app.dependency_overrides[get_principal] = lambda: world["rao"]
        shown = client.get(f"/api/v1/cases/{cid}/suggestions").json()
        assert shown["category"]["suggested"] == "Scholarship delay" and "Ragging" in shown["categories"]
        r = client.post(f"/api/v1/cases/{cid}/suggestions/category", json={"category": "Scholarship delay"})
        assert r.status_code == 200 and r.json()["decision"] == "accepted"
        assert client.post(f"/api/v1/cases/{cid}/suggestions/category",
                           json={"category": "Ragging"}).status_code == 409          # decided already
    finally:
        app.dependency_overrides.clear()
    assert q(world, "SELECT category FROM sethu.complaints WHERE id = :c", c=cid)[0]["category"] == "Scholarship delay"
    fb = q(world, "SELECT decision, suggested, suggested_path, old_value, new_value FROM sethu.ai_feedback")
    assert fb == [{"decision": "accepted", "suggested": "Scholarship delay", "suggested_path": "fallback",
                   "old_value": "Fee refund", "new_value": "Scholarship delay"}]
    actions = [r["action"] for r in q(world, "SELECT action FROM sethu.audit_log ORDER BY seq DESC LIMIT 2")]
    assert set(actions) == {"ai.feedback", "case.category_changed"}
    for sql in ("UPDATE sethu.ai_feedback SET decision = 'rejected'", "DELETE FROM sethu.ai_feedback"):
        with pytest.raises(DBAPIError, match="permission denied"), session_for(world["rao"], world["engine"]) as s:
            s.execute(text(sql))
    # An overlap decision is fed back too.
    detect(world)
    link = q(world, "SELECT l.id FROM sethu.overlap_links l JOIN sethu.complaints a ON a.id = l.complaint_a "
                    "WHERE a.bureau_id = :b OR EXISTS (SELECT 1 FROM sethu.complaints b WHERE b.id = l.complaint_b "
                    "AND b.bureau_id = :b) LIMIT 1", b=world["bureau"]["PGRC"])[0]["id"]
    with session_for(world["rao"], world["engine"]) as s:
        overlaps.decide(s, world["rao"], link, approve=False)
    assert q(world, "SELECT kind, decision, suggested_path FROM sethu.ai_feedback WHERE kind = 'overlap'") == [
        {"kind": "overlap", "decision": "rejected", "suggested_path": "fallback"}]


@requires_db
def test_retrain_activates_only_when_not_worse_and_versions_roll_back(world, e5, monkeypatch):
    first = semantic.retrain(None, world["engine"])
    assert first["status"] == "activated" and first["version"] == 1 and first["metrics"]["holdout_size"] > 0
    real_train = classify.train

    def train_scoring(accuracy):
        def fake(*args, **kw):
            artifact, metrics = real_train(*args, **kw)
            return artifact, metrics | {"holdout_accuracy": accuracy}
        return fake

    monkeypatch.setattr(classify, "train", train_scoring(0.0))
    worse = semantic.retrain(None, world["engine"])
    assert worse["status"] == "kept previous" and worse["version"] == 2
    monkeypatch.setattr(classify, "train", train_scoring(1.0))
    better = semantic.retrain(None, world["engine"])
    assert better["status"] == "activated" and better["version"] == 3
    status = {r["version"]: r["status"] for r in q(world, "SELECT version, status FROM sethu.classifier_versions")}
    assert status == {1: "inactive", 2: "rejected", 3: "active"}
    admin = Principal("admin-sub", "admin", "admin", None)
    with session_for(admin, world["engine"]) as s:
        assert semantic.activate(s, admin, 1) == {"version": 1, "previous": 3}
    with pytest.raises(semantic.SemanticError, match="did worse"), session_for(admin, world["engine"]) as s:
        semantic.activate(s, admin, 2)
    with pytest.raises(DBAPIError, match="permission denied"), session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.classifier_versions SET artifact = '{}' WHERE version = 3"))   # immutable
    with session_for(world["menon"], world["engine"]) as s:
        assert len(s.execute(text("SELECT version FROM sethu.classifier_versions")).all()) == 3   # oversight reads
    actions = [r["action"] for r in q(world, "SELECT action FROM sethu.audit_log WHERE action LIKE 'classifier.%'")]
    assert actions.count("classifier.trained") == 3 and actions.count("classifier.activated") == 1
    # The AI health screen shows the active version and its measured accuracy.
    app.dependency_overrides[get_principal] = lambda: admin
    try:
        health = TestClient(app).get("/api/v1/ai/health").json()
    finally:
        app.dependency_overrides.clear()
    assert health["classifier"]["version"] == 1 and "holdout_accuracy" in health["classifier"]


@requires_db
def test_the_pipeline_runs_every_a3_stage_with_no_models_and_nothing_breaks(world):
    cid = file_case(world, "Greenfeild Institue of Technology", body="Results of the examination are not declared "
                    "and the revaluation results are pending.")
    done = enrichment.enrich_pending(engine=world["engine"], then=semantic.stages)
    assert done["complaints"] >= 1
    tasks = [r["task"] for r in q(world, "SELECT task FROM sethu.ai_runs WHERE subject_id = :c OR subject_type = "
                                         "'complaints' ORDER BY created_at", c=str(cid))]
    assert tasks.index("glossary.tag") < tasks.index("embed.text") < tasks.index("classify.category")
    assert tasks[-1] == "institution.resolve"
    with session_for(SYSTEM, world["engine"]) as s:
        found = semantic.for_case(s, cid)
    assert found["category"]["suggested"] == "Examination" and found["category"]["path"] == "fallback"
    assert found["institution"]["path"] == "fallback" and found["institution"]["provider"] == "institution-fuzzy"
    assert q(world, "SELECT count(*) AS n FROM sethu.complaint_embeddings")[0]["n"] == 0     # no E5: no vectors
