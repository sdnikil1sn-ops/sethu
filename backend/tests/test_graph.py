"""The network graph: aggregated by default, complaints only for expanded institutions, filters, findings,
role scoping (overlaps and transfers through Row-Level Security) and no complaint text."""
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.findings import service as findings
from app.modules.overlaps import service as overlaps
from tests.test_seed import load


@pytest.fixture
def net(world):
    people = world | {"admin": Principal(str(load.user_id("admin")), "admin", "admin", None),
                      "rbhat": Principal(str(load.user_id("rbhat")), "rbhat", "bureau_head", world["bureau"]["NRB"])}
    with session_for(SYSTEM, world["engine"]) as s:
        overlaps.detect(s, SYSTEM)
        findings.detect(s, SYSTEM)

    def graph(who, **params):
        app.dependency_overrides[get_principal] = lambda: people[who]
        r = TestClient(app).get("/api/v1/graph", params=params)
        assert r.status_code == 200, r.text
        return r.json()

    def sql(q, **p):
        with session_for(SYSTEM, world["engine"]) as s:
            return s.execute(text(q), p).all()

    yield world | {"graph": graph, "sql": sql}
    app.dependency_overrides.clear()


def kinds(g, kind):
    return [n for n in g["nodes"] if n["kind"] == kind]


def test_aggregated_by_default_with_counts_and_multi_bureau_clusters(net):
    g = net["graph"]("menon")
    assert not kinds(g, "complaint")
    resolved = net["sql"]("SELECT count(*) FROM sethu.complaints WHERE institution_id IS NOT NULL")[0][0]
    assert sum(e["count"] for e in g["edges"] if e["kind"] == "holds") == resolved
    institutions = kinds(g, "institution")
    assert len(institutions) == net["sql"](
        "SELECT count(DISTINCT institution_id) FROM sethu.complaints WHERE institution_id IS NOT NULL")[0][0]
    greenfield = next(n for n in institutions if n["label"] == "Greenfield Institute of Technology")
    assert greenfield["multi_bureau"] and len(greenfield["bureaus"]) >= 2
    assert {n["label"] for n in kinds(g, "bureau")} == {"PGRC", "RB", "NRB", "AB"}
    assert any(e["kind"] == "transfer" for e in g["edges"])
    c090 = net["sql"]("SELECT institution_id FROM sethu.complaints WHERE ref = 'C-090'")[0][0]
    assert "transfer_loop" in next(n for n in institutions if n["institution_id"] == str(c090))["findings"]


def test_expanding_an_institution_adds_its_complaints_and_overlap_edges(net):
    gid = net["sql"]("SELECT id FROM sethu.institutions WHERE name = 'Greenfield Institute of Technology'")[0][0]
    g = net["graph"]("menon", expand=str(gid))
    cases = kinds(g, "complaint")
    assert len(cases) == net["sql"]("SELECT count(*) FROM sethu.complaints WHERE institution_id = :i", i=gid)[0][0]
    assert any(e["kind"].startswith("overlap_") for e in g["edges"])
    assert all("body" not in n for n in cases) and next(n for n in kinds(g, "institution")
                                                         if n["institution_id"] == str(gid))["expanded"]
    profile = net["graph"]("menon", institution_id=str(gid), expand=str(gid))  # the institution-profile view
    assert {n["kind"] for n in profile["nodes"]} == {"bureau", "institution", "complaint"}
    assert len(kinds(profile, "institution")) == 1


def test_filters_narrow_the_graph(net):
    assert {n["state"] for n in kinds(net["graph"]("menon", state="Uttar Pradesh"), "institution")} == {"Uttar Pradesh"}
    rb = net["graph"]("menon", bureau="RB")
    assert {n["label"] for n in kinds(rb, "bureau")} >= {"RB"} and all("RB" in n["bureaus"]
                                                                       for n in kinds(rb, "institution"))
    loops = net["graph"]("menon", finding_kind="transfer_loop")
    assert [n["label"] for n in kinds(loops, "institution")] == [
        net["sql"]("SELECT i.name FROM sethu.complaints c JOIN sethu.institutions i ON i.id = c.institution_id"
                   " WHERE c.ref = 'C-090'")[0][0]]
    assert kinds(net["graph"]("menon", filed_from="2100-01-01"), "institution") == []


def test_each_role_sees_only_its_share_of_links_and_transfers_and_never_text(net):
    gid = net["sql"]("SELECT id FROM sethu.institutions WHERE name = 'Greenfield Institute of Technology'")[0][0]

    def links(g):
        return {e["id"] for e in g["edges"] if e["kind"].startswith("overlap_")}

    every, rb = net["graph"]("menon", expand=str(gid)), net["graph"]("iyer", expand=str(gid))
    nrb = net["graph"]("rbhat", expand=str(gid))
    assert links(every) and links(nrb) < links(every)     # NRB is party to none of these links
    for g, code in ((rb, "RB"), (nrb, "NRB")):            # a bureau sees a link only if one of its cases is in it
        own = {r[0] for r in net["sql"]("SELECT c.id::text FROM sethu.complaints c JOIN sethu.bureaus b"
                                        " ON b.id = c.bureau_id WHERE b.code = :c", c=code)}
        for e in (e for e in g["edges"] if e["kind"].startswith("overlap_")):
            assert e["source"][2:] in own or e["target"][2:] in own
    transfers = {e["id"]: e["count"] for e in every["edges"] if e["kind"] == "transfer"}
    assert sum(e["count"] for e in rb["edges"] if e["kind"] == "transfer") <= sum(transfers.values())
    bodies = [r[0][:30] for r in net["sql"]("SELECT body FROM sethu.complaints WHERE institution_id = :i", i=gid)]
    assert not any(b in str(rb) or b in str(every) for b in bodies)
    app.dependency_overrides[get_principal] = lambda: Principal("x", "x", "nobody", None)
    assert TestClient(app).get("/api/v1/graph").status_code == 403


def test_five_thousand_more_complaints_stay_aggregated_and_fast(net):
    with session_for(SYSTEM, net["engine"]) as s:
        s.execute(text("""
            INSERT INTO sethu.complaints (ref, source, bureau_id, institution_id, institution_name_raw, category,
                                          body, body_sha256, filed_at, due_at)
            SELECT 'LOAD-' || n, 'load-test', b.id, i.id, i.name, 'Fee refund', 'load test row', md5(n::text),
                   now() - (n % 300) * interval '1 day', now() + interval '10 days'
              FROM generate_series(1, 5200) n
              JOIN LATERAL (SELECT id FROM sethu.bureaus ORDER BY code OFFSET n % 4 LIMIT 1) b ON true
              JOIN LATERAL (SELECT id, name FROM sethu.institutions ORDER BY name OFFSET n % 40 LIMIT 1) i ON true"""))
    start = time.monotonic()
    g = net["graph"]("menon")
    elapsed = time.monotonic() - start
    assert not kinds(g, "complaint") and len(g["nodes"]) < 60
    assert sum(e["count"] for e in g["edges"] if e["kind"] == "holds") > 5200
    assert elapsed < 5, elapsed
