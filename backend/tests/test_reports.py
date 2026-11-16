"""Reports: role scoping, date ranges, CSV export and its audit entry."""
import csv
import io
from datetime import date, timedelta
from statistics import median

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.auth import get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.overlaps import service as overlaps
from app.modules.reports import service
from tests.conftest import requires_db
from tests.test_seed import COMPLAINTS

pytestmark = requires_db


def report(world, who, name, date_from=None, date_to=None):
    with session_for(world[who], world["engine"]) as s:
        return service.run(s, world[who], name, date_from, date_to)


@pytest.fixture
def client(world):
    def as_(who):
        app.dependency_overrides[get_principal] = lambda: world[who]
        return TestClient(app)
    yield as_
    app.dependency_overrides.clear()


def test_bureau_performance_is_scoped_by_role(world):
    pgrc = [c for c in COMPLAINTS if c["bureau"] == "PGRC"]
    mine = report(world, "rao", "bureaus")["rows"]
    assert [r["bureau"] for r in mine] == ["PGRC"]
    assert mine[0]["filed"] == len(pgrc) and mine[0]["closed"] == sum(c["status"] == "closed" for c in pgrc)
    every = {r["bureau"]: r for r in report(world, "menon", "bureaus")["rows"]}
    assert set(every) == set(world["bureau"])
    assert every["PGRC"] == mine[0]
    assert [r["bureau"] for r in report(world, "iyer", "bureaus")["rows"]] == ["RB"]
    took = [float(c["filed_days_ago"]) - float(c["closed_days_ago"]) for c in pgrc if c["status"] == "closed"]
    assert float(mine[0]["median_days_to_close"]) == pytest.approx(median(took), abs=0.1)


def test_institution_report_counts_only_the_callers_cases(world):
    with session_for(SYSTEM, world["engine"]) as s:
        expected = {r.name: (r.mine, r.bureaus) for r in s.execute(text("""
            SELECT i.name, count(*) FILTER (WHERE b.code = 'PGRC') AS mine, count(DISTINCT s.bureau_id) AS bureaus
              FROM sethu.complaint_summaries s JOIN sethu.institutions i ON i.id = s.institution_id
              JOIN sethu.bureaus b ON b.id = s.bureau_id GROUP BY i.name"""))}
    rows = report(world, "rao", "institutions")["rows"]
    assert rows and {r["institution"]: (r["cases"], r["bureaus"]) for r in rows} == {
        name: v for name, v in expected.items() if v[0] > 0}
    greenfield = next(r for r in rows if r["institution"] == "Greenfield Institute of Technology")
    assert greenfield["bureaus"] >= 2  # RB holds C-102 there: counted, not shown
    assert sum(r["cases"] for r in report(world, "menon", "institutions")["rows"]) > sum(r["cases"] for r in rows)


def test_date_range(world):
    tomorrow = date.today() + timedelta(days=2)
    assert report(world, "menon", "institutions", tomorrow)["rows"] == []
    assert all(r["filed"] == 0 for r in report(world, "menon", "bureaus", tomorrow)["rows"])
    last_week = report(world, "rao", "bureaus", date.today() - timedelta(days=7))["rows"][0]["filed"]
    assert last_week == sum(c["bureau"] == "PGRC" and float(c["filed_days_ago"]) <= 7 for c in COMPLAINTS)


def test_overlap_outcomes(world):
    with session_for(SYSTEM, world["engine"]) as s:
        overlaps.detect(s, SYSTEM)
        link = next(link["id"] for link in overlaps.links(s, SYSTEM)
                    if {c["ref"] for c in link["cases"]} == {"C-101", "C-102"})
    with session_for(world["rao"], world["engine"]) as s:
        overlaps.decide(s, world["rao"], link, approve=True)
    every = report(world, "menon", "overlaps")["rows"]
    assert sum(r["suggested"] for r in every) == 6 and sum(r["approved"] for r in every) == 1
    assert sum(r["pending"] for r in every) == 5 and sum(r["alerts_sent"] for r in every) == 0
    assert all("PGRC" in r["bureaus"] for r in report(world, "rao", "overlaps")["rows"])


def test_export_is_csv_without_text_and_is_audited(client, world):
    response = client("iyer").get("/api/v1/reports/institutions/export", params={"date_from": "2020-01-01"})
    assert response.status_code == 200 and response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0][:2] == ["Institution", "Permanent id"] and len(rows) > 2
    for c in COMPLAINTS:
        assert c["body"] not in response.text
    with session_for(SYSTEM, world["engine"]) as s:
        entry = s.execute(text("SELECT actor, actor_role, entity_id, payload FROM sethu.audit_log"
                               " WHERE action = 'report.export'")).one()
    assert entry.actor == world["iyer"].subject and entry.actor_role == "bureau_head"
    assert entry.entity_id == "institutions"
    assert entry.payload == {"report": "institutions", "rows": len(rows) - 1, "scope": "your bureau only",
                             "filters": {"date_from": "2020-01-01", "date_to": None}}


def test_viewing_is_not_audited_and_bad_names_are_refused(client, world):
    das = client("das")
    assert das.get("/api/v1/reports/bureaus").json()["scope"] == "all bureaus"
    assert das.get("/api/v1/reports/complaints").status_code == 422
    assert das.get("/api/v1/reports/bureaus/export", params={"date_from": "soon"}).status_code == 422
    with session_for(SYSTEM, world["engine"]) as s:
        assert s.execute(text("SELECT count(*) FROM sethu.audit_log WHERE action = 'report.export'")).scalar() == 0


def test_spreadsheet_formulas_are_made_inert():
    assert service._cell("=HYPERLINK(1)") == "'=HYPERLINK(1)"
    assert service._cell("@SUM") == "'@SUM" and service._cell("Pune") == "Pune" and service._cell(None) == ""
