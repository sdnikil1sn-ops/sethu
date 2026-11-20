"""Every filter on every list screen, through the HTTP API the web app calls: each one narrows,
two together narrow further, a blank or all-space value is no filter, and leaving it out restores
the full list. Also: the Institutions screen and the top-bar search find the same institutions."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.auth import get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.overlaps import service as overlaps
from tests.conftest import requires_db

pytestmark = requires_db
GREENFIELD = "Greenfield Institute of Technology"


@pytest.fixture
def get(world):
    """get(who, path, **params) -> JSON; a non-200 answer fails the test."""
    client = TestClient(app)

    def call(who, path, **params):
        app.dependency_overrides[get_principal] = lambda: world[who]
        response = client.get(f"/api/v1{path}", params=params)
        assert response.status_code == 200, (path, params, response.text)
        return response.json()
    yield call
    app.dependency_overrides.clear()


# --- Institutions: the screen and the top-bar search are one search ---------------------------------

@pytest.mark.parametrize("q", ["madurai", "GIT", "Greenfeild", "Tamil Nadu", "GIT Pune"])
def test_institutions_screen_and_top_bar_search_agree(get, q):
    screen = get("rao", "/institutions", q=q)
    top_bar = get("rao", "/search", q=q, limit=50)["institutions"]
    assert screen, q
    assert [i["id"] for i in screen] == [i["id"] for i in top_bar]
    assert [i["why"] for i in screen] == [i["why"] for i in top_bar]
    assert all(isinstance(i["complaints"], int) and isinstance(i["open"], int) for i in screen)


def test_institution_search_by_city_state_initials_typo_and_permanent_id(get, world):
    madurai = get("rao", "/institutions", q="madurai")
    assert len(madurai) >= 1 and all(i["district"] == "Madurai" and i["why"] == "city: Madurai" for i in madurai)
    assert all(i["state"] == "Tamil Nadu" for i in get("rao", "/institutions", q="tamil nadu"))
    assert GREENFIELD in {i["name"] for i in get("rao", "/institutions", q="GIT")}
    assert get("rao", "/institutions", q="Greenfeild")[0]["name"] == GREENFIELD
    with session_for(SYSTEM, world["engine"]) as s:
        pid = s.execute(text("SELECT permanent_id FROM sethu.institutions WHERE name = :n"), {"n": GREENFIELD}).scalar()
    hit = get("rao", "/institutions", q=pid)[0]
    assert hit["name"] == GREENFIELD and hit["why"] == "permanent id"


def test_institution_list_filters(get):
    everything = get("rao", "/institutions", limit=200)
    assert len(everything) == 43
    gujarat = get("rao", "/institutions", state="Gujarat", limit=200)
    assert 0 < len(gujarat) < 40 and {i["state"] for i in gujarat} == {"Gujarat"}
    # search and state together: Tamil Nadu institutions only, then none of them in Gujarat
    assert get("rao", "/institutions", q="Tamil Nadu", state="Gujarat") == []
    for blank in ("", "   "):  # a blank search or state is no filter
        assert len(get("rao", "/institutions", q=blank, state=blank, limit=200)) == 43


# --- Cases ----------------------------------------------------------------------------------------

def test_each_case_filter_narrows_and_blank_is_no_filter(get, world):
    def total(**params):
        return get("menon", "/cases", limit=1, **params)["total"]

    everything = total()
    greenfield = get("menon", "/institutions", q="GIT Pune")[0]["id"]
    newest = get("menon", "/cases", limit=1)["items"][0]["filed_at"][:10]
    narrowing = {
        "bureau": "RB", "status": "transferred", "category": "Fee refund", "institution_id": greenfield,
        "state": "Gujarat", "filed_from": newest, "filed_to": "2000-01-01", "overdue": "true",
        "overlapping": "true", "q": "Greenfield",
    }
    with session_for(SYSTEM, world["engine"]) as s:  # so "overlapping only" has links to find
        overlaps.detect(s, SYSTEM)
    for name, value in narrowing.items():
        assert total(**{name: value}) < everything, name
    for name in narrowing:
        assert total(**{name: ""}) == everything, name
        assert total(**{name: "  "}) == everything, name
    assert total(bureau="rb") == total(bureau="RB")  # the bureau code is not case-sensitive
    assert total(q="  Greenfield  ") == total(q="Greenfield")


def test_two_case_filters_together(get):
    def total(**params):
        return get("menon", "/cases", limit=1, **params)["total"]

    rb, overdue = total(bureau="RB"), total(overdue="true")
    both = total(bureau="RB", overdue="true")
    assert both <= min(rb, overdue) and both == total(bureau="RB", overdue="true", q="")
    assert sum(total(bureau=b) for b in ("PGRC", "RB", "NRB", "AB")) == total()
    assert total(state="Uttar Pradesh", category="Fee refund") < total(state="Uttar Pradesh")
    ranged = total(filed_from="2000-01-01", filed_to="2999-12-31")
    assert ranged == total() and total(filed_from="2999-01-01", filed_to="2999-12-31") == 0


# --- Overlaps and alerts -------------------------------------------------------------------------

def test_overlap_filters(get, world):
    with session_for(SYSTEM, world["engine"]) as s:
        overlaps.detect(s, SYSTEM)
    everything = get("menon", "/overlaps")
    assert len(everything) == 7
    assert get("menon", "/overlaps", status="approved") == []
    assert len(get("menon", "/overlaps", status="proposed")) == 7
    assert len(get("menon", "/overlaps", tier=2)) == 7 and get("menon", "/overlaps", tier=1) == []
    # Six links are PGRC and RB, one is RB and NRB: the bureau filter narrows both ways.
    assert len(get("menon", "/overlaps", bureau="pgrc")) == 6 and get("menon", "/overlaps", bureau="NOPE") == []
    nrb = get("menon", "/overlaps", bureau="NRB")
    assert len(nrb) == 1 and {c["bureau"] for c in nrb[0]["cases"]} == {"RB", "NRB"}
    assert get("menon", "/overlaps", bureau="AB") == []
    assert get("menon", "/overlaps", bureau="RB", status="rejected") == []
    assert len(get("menon", "/overlaps", bureau="RB", status="proposed", tier=2)) == 7
    for blank in ("", " "):
        assert len(get("menon", "/overlaps", status=blank, bureau=blank, tier=blank)) == 7


def test_alert_status_filter(get, world):
    with session_for(SYSTEM, world["engine"]) as s:
        overlaps.detect(s, SYSTEM)
        demo = next(link["id"] for link in overlaps.links(s, SYSTEM)
                    if [c["ref"] for c in link["cases"]] == ["C-101", "C-102"])
    with session_for(world["rao"], world["engine"]) as s:
        overlaps.decide(s, world["rao"], demo, approve=True)
    assert len(get("menon", "/alerts")["items"]) == 1
    assert len(get("menon", "/alerts", status="approved")["items"]) == 1  # an officer's approval
    assert get("menon", "/alerts", status="sent")["items"] == []
    assert len(get("menon", "/alerts", status=" ")["items"]) == 1


# --- Audit log -----------------------------------------------------------------------------------

def test_audit_filters_narrow_combine_and_ignore_blanks(get, world):
    get("das", "/audit/verify")  # one entry by Mr. Das
    newest = get("das", "/audit", limit=200)["items"]
    c101 = str(world["case"]["C-101"])
    # filter -> (value, what every entry found must satisfy)
    narrowing = {
        "action": ("institution.", lambda e: e["action"].startswith("institution.")),
        "actor": ("das", lambda e: "das" in (e["actor_name"] + e["actor"]).lower()),
        "entity_type": ("complaints", lambda e: e["entity_type"] == "complaints"),
        "entity_id": (c101, lambda e: e["entity_id"] == c101),
        "date_from": ("2999-01-01", lambda e: False),
        "date_to": ("2000-01-01", lambda e: False),
    }
    for name, (value, holds) in narrowing.items():
        found = get("das", "/audit", limit=200, **{name: value})["items"]
        assert all(holds(e) for e in found), name
        assert found != newest, name  # it narrowed
        assert get("das", "/audit", limit=200, **{name: " "})["items"] == newest, name  # blank: no filter
    both = get("das", "/audit", limit=200, action="audit.", actor="das")["items"]
    assert [e["action"] for e in both] == ["audit.verify"]
    assert get("das", "/audit", action="institution.", actor="das")["items"] == []
    assert get("das", "/audit", actor="d_s")["items"] == []  # _ is a literal, not a wildcard


# --- Reports ------------------------------------------------------------------------------------

def test_report_dates_blank_and_reversed(get, world):
    full = get("menon", "/reports/bureaus")
    assert get("menon", "/reports/bureaus", date_from="", date_to=" ") == full
    narrow = get("menon", "/reports/bureaus", date_from="2999-01-01")
    assert sum(r["filed"] for r in narrow["rows"]) == 0 < sum(r["filed"] for r in full["rows"])
    client = TestClient(app)
    app.dependency_overrides[get_principal] = lambda: world["menon"]
    for path in ("/api/v1/reports/bureaus", "/api/v1/reports/bureaus/export"):
        refused = client.get(path, params={"date_from": "2026-02-01", "date_to": "2026-01-01"})
        assert refused.status_code == 422 and "start date" in refused.text
