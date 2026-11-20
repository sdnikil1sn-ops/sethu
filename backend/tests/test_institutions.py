"""Institutions: profile, alias search and the resolution cascade, on the seeded data."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.audit.service import verify
from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.institutions import service
from app.modules.institutions.service import normalize
from tests.conftest import requires_db
from tests.test_seed import COMPLAINTS, INSTITUTIONS, load

GREENFIELD = "Greenfield Institute of Technology"
ANSWER = {c["ref"]: c["institution_pid"] for c in COMPLAINTS}  # the seed's answer key
PID_OF_NAME = {i["name"]: i["permanent_id"] for i in INSTITUTIONS}


def test_profile_dna_measures():
    now = datetime(2026, 11, 1, tzinfo=UTC)

    def case(category, bureau, filed_days_ago, closed_after=None):
        filed = now - timedelta(days=filed_days_ago)
        return {"category": category, "bureau": bureau, "filed_at": filed,
                "closed_at": filed + timedelta(days=closed_after) if closed_after is not None else None}

    cases = [case("Fee refund", "PGRC", 300, 10), case("Fee refund", "RB", 200, 20),  # 100 days apart: a repeat
             case("Fee refund", "PGRC", 10), case("Ragging", "RB", 150, 30),         # 190 days later: not one
             case(None, "PGRC", 400, 4)]
    dna = service.dna(cases, now)
    assert dna["category_mix"][0] == {"category": "Fee refund", "cases": 3, "share": 0.6}
    assert dna["volume"] == {"total": 5, "last_12_months": 4, "per_month": 0.3}
    assert dna["recurrence"] == {"repeat_cases": 1, "share": 0.2, "categories": ["Fee refund"], "window_days": 180}
    assert dna["disposal"] == {"closed": 4, "median_days": 15.0}  # 4, 10, 20, 30 days
    assert dna["bureaus"] == [{"bureau": "PGRC", "cases": 3}, {"bureau": "RB", "cases": 2}]
    assert dna["trend"] == {"recent": 1, "previous": 1, "window_days": 90, "direction": "flat"}
    assert service.dna([], now)["disposal"]["median_days"] is None


def test_normalize_expands_abbreviations():
    assert normalize("Greenfield Inst. of Tech., Pune") == "greenfield institute of technology pune"
    assert normalize("  Stonemere Poly. Coll.  ") == "stonemere polytechnic college"
    assert normalize("...") == ""


@pytest.fixture
def seeded(app_engine):
    load.load(app_engine)
    return app_engine


def scalar(session, sql, **params):
    return session.execute(text(sql), params).scalar_one()


SPELLINGS = [
    ("Greenfield Institute of Technology", "alias"),   # C-101: the canonical name
    ("Greenfield Inst. of Tech., Pune", "alias"),      # C-102
    ("GIT Pune", "alias"),                             # C-103
    ("greenfield institute of tech", "alias"),         # case and abbreviation
    ("Greenfeild Institute of Technology", "fuzzy"),   # typo
    ("Complaint against 1-90000001", "permanent_id"),
]


@requires_db
def test_greenfield_spellings_resolve_to_one_institution(seeded):
    with session_for(SYSTEM, seeded) as s:
        for typed, step in SPELLINGS:
            decision, candidates = service.rank(s, typed)
            assert decision and decision["step"] == step, typed
            assert candidates[0]["name"] == GREENFIELD and candidates[0]["id"] == decision["institution_id"], typed


@requires_db
def test_unknown_or_ambiguous_names_are_not_guessed(seeded):
    with session_for(SYSTEM, seeded) as s:
        assert service.rank(s, "Some College Nobody Has Heard Of")[0] is None
        assert service.rank(s, "  ") == (None, [])
        # An acronym is a suggestion, never a decision: two seeded colleges are "GIT".
        decision, candidates = service.rank(s, "GIT")
        assert decision is None and {c["reason"] for c in candidates} == {"acronym"}
        assert {GREENFIELD, "Goldmere Institute of Technology"} <= {c["name"] for c in candidates}
        # The same spelling on two institutions: exact, but not unique.
        other = scalar(s, "SELECT id FROM sethu.institutions WHERE name <> :n LIMIT 1", n=GREENFIELD)
        s.execute(text("INSERT INTO sethu.institution_aliases (institution_id, alias) VALUES (:i, 'GIT Pune')"),
                  {"i": other})
        assert service.rank(s, "GIT Pune")[0] is None


@requires_db
def test_cascade_resolves_most_variants_and_queues_the_rest(seeded):
    with session_for(SYSTEM, seeded) as s:
        assert len(service.queue(s, 200)) == 38
        result = service.resolve_pending(s, SYSTEM)
    assert result["resolved"] + result["queued"] == 38
    assert result["resolved"] >= 25  # 27 today: 19 by known spelling, 8 by fuzzy match

    with session_for(SYSTEM, seeded) as s:
        linked = s.execute(text(
            "SELECT c.ref, i.permanent_id FROM sethu.complaints c JOIN sethu.institutions i ON i.id = c.institution_id"
        )).all()
        assert len(linked) == 300 - result["queued"]
        assert all(pid == ANSWER[ref] for ref, pid in linked), "a complaint was linked to the wrong institution"
        assert scalar(s, "SELECT count(*) FROM sethu.audit_log WHERE action = 'institution.resolve'"
                         " AND payload->>'step' IN ('alias', 'fuzzy')") == result["resolved"]

        # Whatever is left is in the queue, with the right institution among the five offered.
        queue = service.queue(s, 200)
        assert len(queue) == result["queued"] > 0
        assert scalar(s, "SELECT count(*) FROM sethu.complaints WHERE institution_id IS NULL") == len(queue)
        for item in queue:
            assert 0 < len(item["candidates"]) <= 5
            assert ANSWER[item["ref"]] in {PID_OF_NAME[c["name"]] for c in item["candidates"]}, item

        assert service.resolve_pending(s, SYSTEM) == {"resolved": 0, "queued": len(queue)}  # repeatable
        assert verify(s).ok


@requires_db
def test_officer_picks_from_the_queue(seeded):
    with session_for(SYSTEM, seeded) as s:
        service.resolve_pending(s, SYSTEM)
        item = service.queue(s)[0]
        bureau = {r.code: r.id for r in s.execute(text("SELECT code, id FROM sethu.bureaus"))}
    choice = next(c for c in item["candidates"] if PID_OF_NAME[c["name"]] == ANSWER[item["ref"]])
    own = Principal("u-own", "own", "officer", bureau[item["bureau"]])
    other = Principal("u-other", "other", "officer", next(v for k, v in bureau.items() if k != item["bureau"]))

    with session_for(other, seeded) as s:  # another bureau's officer neither sees nor resolves it
        assert item["ref"] not in {q["ref"] for q in service.queue(s, 200)}
        assert service.resolve_by_officer(s, other, item["id"], choice["id"]) is None
    with session_for(own, seeded) as s:
        assert service.resolve_by_officer(s, own, item["id"], uuid4()) is None  # no such institution
        assert service.resolve_by_officer(s, own, item["id"], choice["id"]) == {
            "ref": item["ref"], "institution_id": choice["id"], "alias_added": True}
        assert service.resolve_by_officer(s, own, item["id"], choice["id"]) is None  # already resolved

    with session_for(SYSTEM, seeded) as s:
        assert scalar(s, "SELECT resolution_state FROM sethu.complaints WHERE id = :i", i=item["id"]) == "officer"
        assert scalar(s, "SELECT actor FROM sethu.audit_log WHERE action = 'institution.resolve'"
                         " AND payload->>'step' = 'officer' AND entity_id = :i", i=str(item["id"])) == "u-own"
        # The spelling was learned: next time it resolves without a person.
        decision, _ = service.rank(s, item["institution_name_raw"])
        assert decision == {"institution_id": choice["id"], "step": "alias", "score": 100.0}


@requires_db
def test_profile_shows_every_bureau_without_complaint_text(seeded):
    with session_for(SYSTEM, seeded) as s:
        pgrc = scalar(s, "SELECT id FROM sethu.bureaus WHERE code = 'PGRC'")
    officer = Principal("u-rao", "rao", "officer", pgrc)
    with session_for(officer, seeded) as s:
        hit = service.list_institutions(s, "GIT Pune", None, 10, 0)[0]
        assert hit["name"] == GREENFIELD and hit["why"] == 'also known as "GIT Pune": same spelling'
        assert (hit["complaints"], hit["open"]) == (3, 3)
        profile = service.profile(s, hit["id"])
        assert [c["ref"] for c in profile["complaints"]] == ["C-103", "C-102", "C-101"]  # RB's C-102 included
        assert profile["bureaus"] == ["PGRC", "RB"]
        assert (profile["open"], profile["closed"], profile["oldest_open"]["ref"]) == (3, 0, "C-101")
        assert len(profile["aliases"]) == 3
        assert "body" not in profile["complaints"][0]
        assert service.profile(s, uuid4()) is None

        everything = service.list_institutions(s, None, None, 200, 0)
        assert len(everything) == 40 and sum(i["complaints"] for i in everything) == 262
        assert {i["state"] for i in service.list_institutions(s, None, "Gujarat", 200, 0)} == {"Gujarat"}


@requires_db
def test_api_search_and_role_gates(seeded):
    client = TestClient(app)
    try:
        app.dependency_overrides[get_principal] = lambda: Principal("u-aud", "aud", "auditor", None)
        for q in ("Greenfield Inst. of Tech", "GIT Pune"):  # checklist section 1, line 2
            rows = client.get("/api/v1/institutions", params={"q": q}).json()
            assert rows[0]["name"] == GREENFIELD
        profile = client.get(f"/api/v1/institutions/{rows[0]['id']}")
        assert profile.status_code == 200 and len(profile.json()["complaints"]) == 3
        dna = profile.json()["dna"]  # Greenfield: C-101 and C-102 faculty shortage, C-103 fee refund, all open
        mix = [(c["category"], c["cases"]) for c in dna["category_mix"]]
        assert mix == [("Faculty shortage", 2), ("Fee refund", 1)]
        assert dna["recurrence"]["repeat_cases"] == 1 and dna["recurrence"]["categories"] == ["Faculty shortage"]
        assert dna["disposal"] == {"closed": 0, "median_days": None}
        assert dna["bureaus"] == [{"bureau": "PGRC", "cases": 2}, {"bureau": "RB", "cases": 1}]
        assert (dna["volume"]["total"], dna["trend"]["recent"], dna["trend"]["direction"]) == (3, 3, "up")
        assert client.get(f"/api/v1/institutions/{uuid4()}").status_code == 404
        assert len(client.get("/api/v1/institutions/resolution/queue", params={"limit": 200}).json()) == 38
        # An auditor reads but never resolves.
        assert client.post("/api/v1/institutions/resolution/run").status_code == 403
        assert client.post(f"/api/v1/institutions/resolution/{uuid4()}",
                           json={"institution_id": str(uuid4())}).status_code == 403

        app.dependency_overrides[get_principal] = lambda: Principal("u-adm", "adm", "admin", None)
        run = client.post("/api/v1/institutions/resolution/run").json()
        assert run["resolved"] >= 25 and run["resolved"] + run["queued"] == 38
        assert client.post(f"/api/v1/institutions/resolution/{uuid4()}",
                           json={"institution_id": str(uuid4())}).status_code == 404
    finally:
        app.dependency_overrides.clear()
