"""Top-bar search: institutions by name, alias, initials or city; cases by reference and metadata
for everyone; complaint text only where Row-Level Security lets the caller read it."""
import json

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_principal
from app.db.session import session_for
from app.main import app
from app.modules.search import service
from tests.conftest import requires_db
from tests.test_seed import COMPLAINTS

pytestmark = requires_db
GREENFIELD = "Greenfield Institute of Technology"


def find(world, who, q):
    with session_for(world[who], world["engine"]) as s:
        return service.search(s, q, 100)


def hits(result):
    return {c["ref"]: c for c in result["complaints"]["items"]}


@pytest.mark.parametrize(("q", "why"), [
    ("GIT Pune", "also known as"),       # an alias, typed exactly
    ("Greenfeild Institute", "similar"),  # a typo, found by pg_trgm
    ("Pune", "city: Pune"),
    ("GIT", "initials GIT"),
])
def test_institutions_by_name_alias_initials_and_city(world, q, why):
    found = find(world, "rao", q)["institutions"]
    greenfield = next(i for i in found if i["name"] == GREENFIELD)
    assert why in greenfield["why"]


def test_cases_by_reference_and_metadata_across_bureaus(world):
    by_ref = hits(find(world, "rao", "C-102"))
    assert by_ref["C-102"]["why"] == ["reference"] and by_ref["C-102"]["readable"] is False
    assert by_ref["C-102"]["bureau"] == "RB" and by_ref["C-102"]["institution"] == GREENFIELD

    by_category = hits(find(world, "rao", "Faculty shortage"))
    assert {"C-101", "C-102"} <= set(by_category) and "category" in by_category["C-102"]["why"]
    by_bureau = find(world, "rao", "RB")["complaints"]
    assert by_bureau["total"] >= sum(c["bureau"] == "RB" for c in COMPLAINTS)  # plus names containing "rb"
    assert all(c["bureau"] == "RB" for c in by_bureau["items"] if "bureau" in c["why"])


def test_bureau_a_never_sees_bureau_b_text_through_search(world):
    """Search every RB complaint's own words as a PGRC officer: never a text match, never the text."""
    others = [c for c in COMPLAINTS if c["bureau"] != "PGRC"]
    assert len(others) > 20
    with session_for(world["rao"], world["engine"]) as s:
        for c in others:
            for phrase in (c["body"][10:50].strip(), c["institution_name_raw"]):
                result = service.search(s, phrase, 100)
                dumped = json.dumps(result, default=str)
                assert c["body"] not in dumped
                for hit in result["complaints"]["items"]:
                    text_reasons = {"complaint text", "institution name as typed"} & set(hit["why"])
                    assert not text_reasons or hit["bureau"] == "PGRC", (c["ref"], hit)
    # The same words do find the case for its own bureau.
    c102 = next(c for c in COMPLAINTS if c["ref"] == "C-102")
    assert "complaint text" in hits(find(world, "iyer", c102["body"][10:50]))["C-102"]["why"]
    assert "C-102" not in hits(find(world, "rao", c102["body"][10:50]))


def test_own_bureau_text_is_searched(world):
    c103 = next(c for c in COMPLAINTS if c["ref"] == "C-103")
    assert "complaint text" in hits(find(world, "rao", c103["body"][4:40]))["C-103"]["why"]


def test_every_role_can_search_and_short_queries_are_refused(world):
    client = TestClient(app)
    try:
        for who in ("rao", "fernandes", "iyer", "menon", "das"):
            app.dependency_overrides[get_principal] = lambda who=who: world[who]
            page = client.get("/api/v1/search", params={"q": "Greenfield"}).json()
            assert page["institutions"][0]["name"] == GREENFIELD, who
        assert client.get("/api/v1/search", params={"q": "G"}).status_code == 422
    finally:
        app.dependency_overrides.clear()
