"""Paged lists (Phase 5, after the load test): cases, findings and overlaps come a page at a time with a total that
is counted only up to a cap; filters still apply; who sees what is unchanged; the dashboard's counts are bounded."""
import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_principal
from app.db import paging
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.complaints import service as cases
from app.modules.findings import service as findings
from app.modules.overlaps import service as overlaps
from tests.conftest import requires_db

pytestmark = requires_db


@pytest.fixture
def detected(world):
    with session_for(SYSTEM, world["engine"]) as s:
        findings.detect(s, SYSTEM)
        overlaps.detect(s, SYSTEM)
    return world


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def as_(who):
    app.dependency_overrides[get_principal] = lambda: who


def walk(client, path, limit, **params) -> list[dict]:
    """Every page of a list, checking each page's own numbers on the way."""
    pages, offset = [], 0
    while True:
        page = client.get(path, params={**params, "limit": limit, "offset": offset}).json()
        assert page["limit"] == limit and page["offset"] == offset and len(page["items"]) <= limit
        pages.append(page)
        if not page["has_next"]:
            return pages
        assert len(page["items"]) == limit
        offset += limit


def test_case_pages_cover_every_case_once_and_end_exactly(world, client):
    as_(world["menon"])
    pages = walk(client, "/api/v1/cases", 7, overdue="true")
    refs = [c["ref"] for p in pages for c in p["items"]]
    assert [len(p["items"]) for p in pages] == [7, 7, 7, 4]                 # 25 overdue cases
    assert len(refs) == len(set(refs)) == 25 and all(p["total"] == 25 and not p["total_capped"] for p in pages)
    past = client.get("/api/v1/cases", params={"overdue": "true", "offset": 25}).json()
    assert past["items"] == [] and not past["has_next"] and past["total"] == 25


def test_filters_combine_with_pages(world, client):
    as_(world["menon"])
    with session_for(world["menon"], world["engine"]) as s:
        rb_total = cases.search(s, {"bureau": "RB", "status": "open"}, 200, 0)["total"]
    pages = walk(client, "/api/v1/cases", 5, bureau="RB", status="open")
    rows = [c for p in pages for c in p["items"]]
    assert len(rows) == rb_total > 5 and all(c["bureau"] == "RB" and c["status"] == "open" for c in rows)


def test_the_total_is_capped_on_a_broad_filter(world, client, monkeypatch):
    monkeypatch.setattr(paging, "COUNT_CAP", 100)
    as_(world["menon"])
    broad = client.get("/api/v1/cases").json()                               # 310 cases
    assert broad["total"] == 100 and broad["total_capped"] and broad["has_next"]
    narrow = client.get("/api/v1/cases", params={"overdue": "true"}).json()
    assert narrow["total"] == 25 and not narrow["total_capped"]


def test_page_size_is_bounded(world, client):
    as_(world["menon"])
    for path in ("/api/v1/cases", "/api/v1/findings", "/api/v1/overlaps"):
        assert client.get(path, params={"limit": 0}).status_code == 422
        assert client.get(path, params={"limit": 201}).status_code == 422
        assert client.get(path, params={"offset": -1}).status_code == 422
        assert client.get(path).json()["limit"] == 50                       # the default


def test_finding_and_overlap_pages(detected, client):
    as_(detected["menon"])
    found = walk(client, "/api/v1/findings", 2)
    with session_for(detected["menon"], detected["engine"]) as s:
        every = findings.listing(s, {})
    assert [f["id"] for p in found for f in p["items"]] == [str(f["id"]) for f in every]   # same order, no gaps
    links = walk(client, "/api/v1/overlaps", 3)
    assert [len(p["items"]) for p in links] == [3, 3, 1] and links[0]["total"] == 7
    rb = walk(client, "/api/v1/overlaps", 2, bureau="RB", status="proposed")
    with session_for(detected["menon"], detected["engine"]) as s:
        expected = {str(link["id"]) for link in overlaps.links(s, detected["menon"], "proposed", None, "RB")}
    assert {link["id"] for p in rb for link in p["items"]} == expected and rb[0]["total"] == len(expected) > 2


def test_role_scoping_is_unchanged_by_paging(detected, client):
    """A PGRC officer's pages hold exactly what they could see before: findings involving PGRC, links where PGRC
    holds a case, and the case list's summary rows (text only where readable)."""
    rao = detected["rao"]
    with session_for(rao, detected["engine"]) as s:
        own_findings = {str(f["id"]) for f in findings.listing(s, {})}
        own_links = {str(link["id"]) for link in overlaps.links(s, rao)}
    as_(rao)
    paged_findings = {f["id"] for p in walk(client, "/api/v1/findings", 3) for f in p["items"]}
    paged_links = {link["id"] for p in walk(client, "/api/v1/overlaps", 2) for link in p["items"]}
    assert paged_findings == own_findings and all("PGRC" in f["bureaus"] for p in walk(client, "/api/v1/findings", 50)
                                                  for f in p["items"])
    assert paged_links == own_links
    cases_seen = [(c["ref"], c["readable"]) for p in walk(client, "/api/v1/cases", 100) for c in p["items"]]
    with session_for(rao, detected["engine"]) as s:
        unpaged = [(c["ref"], c["readable"]) for c in cases.search(s, {}, 1000, 0)["items"]]
    assert cases_seen == unpaged and len(unpaged) == 310 and 0 < sum(r for _, r in unpaged) < 310


def test_dashboard_counts_are_bounded(detected, client, monkeypatch):
    monkeypatch.setattr(paging, "COUNT_CAP", 3)
    as_(detected["menon"])
    attention = client.get("/api/v1/dashboard").json()["attention"]
    assert attention["overlaps_to_review"] == 4        # COUNT_CAP + 1: shown as "3+" (7 proposed)
    assert attention["overdue_total"] == 4 and attention["findings_open"] == 4
    assert len(attention["overdue"]) == 15             # the list is its own page (OVERDUE_SHOWN)
