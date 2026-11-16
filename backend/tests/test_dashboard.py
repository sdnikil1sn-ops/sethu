"""Dashboard counts against the seeded data, and what each role may see."""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.auth import get_principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.dashboard import service
from app.modules.overlaps import service as overlaps
from tests.conftest import requires_db
from tests.test_seed import COMPLAINTS

pytestmark = requires_db


def overdue(c: dict) -> bool:
    return c["status"] != "closed" and float(c["filed_days_ago"]) >= get_settings().sla_days


def counts(rows: list[dict]) -> dict:
    return {r["key"]: (r["total"], r["open"], r["overdue"]) for r in rows}


def expected(column: str) -> dict:
    out = {}
    for key in {c[column] for c in COMPLAINTS}:
        mine = [c for c in COMPLAINTS if c[column] == key]
        out[key] = (len(mine), sum(c["status"] != "closed" for c in mine), sum(map(overdue, mine)))
    return out


@pytest.fixture
def board(world):
    with session_for(SYSTEM, world["engine"]) as s:
        overlaps.detect(s, SYSTEM)
    return world


def test_counts_match_the_seeded_data(board):
    with session_for(board["rao"], board["engine"]) as s:
        view = service.overview(s)
    assert counts(view["by_bureau"]) == expected("bureau")
    assert counts(view["by_status"]) == expected("status")
    assert counts(view["by_category"]) == expected("category")
    assert view["totals"] == {"total": len(COMPLAINTS), "open": sum(c["status"] != "closed" for c in COMPLAINTS),
                              "overdue": sum(map(overdue, COMPLAINTS))}
    assert len(view["weekly"]) == service.WEEKS
    # Every seeded case was filed within the 26 weeks shown, so the weeks add up to all of them.
    assert max(float(c["filed_days_ago"]) for c in COMPLAINTS) < 7 * (service.WEEKS - 1)
    assert sum(w["filed"] for w in view["weekly"]) == len(COMPLAINTS)


def test_cross_bureau_numbers_are_the_same_for_everyone(board):
    views = {}
    for who in ("rao", "iyer", "menon", "das"):
        with session_for(board[who], board["engine"]) as s:
            views[who] = service.overview(s)
    shared = ("totals", "by_bureau", "by_status", "by_category", "weekly")
    assert len({json.dumps([views[w][k] for k in shared], default=str) for w in views}) == 1


def test_a_bureau_sees_no_text_it_cannot_read_and_only_its_own_work(board):
    pgrc = board["bureau"]["PGRC"]
    with session_for(board["rao"], board["engine"]) as s:
        view = service.overview(s)
    with session_for(SYSTEM, board["engine"]) as s:
        proposed_for_pgrc = s.execute(text("""
            SELECT count(*) FROM sethu.overlap_links l
              JOIN sethu.complaints a ON a.id = l.complaint_a JOIN sethu.complaints b ON b.id = l.complaint_b
             WHERE l.status = 'proposed' AND :pgrc IN (a.bureau_id, b.bureau_id)"""), {"pgrc": pgrc}).scalar()
    dumped = json.dumps(view, default=str)
    assert not any(c["body"] in dumped for c in COMPLAINTS)  # no complaint text, not even its own bureau's
    attention = view["attention"]
    assert {c["bureau"] for c in attention["overdue"]} == {"PGRC"}
    assert attention["overdue_total"] == sum(overdue(c) for c in COMPLAINTS if c["bureau"] == "PGRC")
    assert attention["overlaps_to_review"] == proposed_for_pgrc > 0


def test_every_role_gets_the_dashboard(board):
    client = TestClient(app)
    try:
        for who in ("rao", "fernandes", "iyer", "menon", "das"):
            app.dependency_overrides[get_principal] = lambda who=who: board[who]
            response = client.get("/api/v1/dashboard")
            assert response.status_code == 200, who
            assert response.json()["totals"]["total"] == len(COMPLAINTS)
        everyone_overdue = sum(map(overdue, COMPLAINTS))
        assert len(response.json()["attention"]["overdue"]) == min(service.OVERDUE_SHOWN, everyone_overdue)
        assert response.json()["attention"]["overdue_total"] == everyone_overdue
    finally:
        app.dependency_overrides.clear()
