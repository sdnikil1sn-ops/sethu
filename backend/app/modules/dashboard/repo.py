"""SQL for the dashboard. Case numbers come only from sethu.complaint_summaries
(every bureau, no complaint text). Overlap and alert counts read their tables,
which Row-Level Security limits to what the caller's bureau is a party to."""
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import paging

OVERDUE = "s.status <> 'closed' AND s.due_at < now()"


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(row) for row in session.execute(text(sql), params).mappings()]


def by_bureau(session: Session) -> list[dict]:
    return _all(session, f"""
        SELECT b.code AS key, b.name AS label, count(s.id) AS total,
               count(s.id) FILTER (WHERE s.status <> 'closed') AS open,
               count(s.id) FILTER (WHERE {OVERDUE}) AS overdue
          FROM sethu.bureaus b LEFT JOIN sethu.complaint_summaries s ON s.bureau_id = b.id
         GROUP BY b.code, b.name ORDER BY b.code""")  # noqa: S608 - constant only


def by_column(session: Session, column: str) -> list[dict]:
    assert column in ("status", "category")  # noqa: S101 - a column name, never user input
    return _all(session, f"""
        SELECT s.{column} AS key, s.{column} AS label, count(*) AS total,
               count(*) FILTER (WHERE s.status <> 'closed') AS open,
               count(*) FILTER (WHERE {OVERDUE}) AS overdue
          FROM sethu.complaint_summaries s GROUP BY s.{column} ORDER BY total DESC, key""")  # noqa: S608


def weekly(session: Session, weeks: int) -> list[dict]:
    """Complaints filed per week (weeks start on Monday), oldest first, with empty weeks as 0."""
    return _all(session, """
        SELECT w.week::date AS week, count(s.id) AS filed
          FROM generate_series(date_trunc('week', now()) - make_interval(weeks => :weeks - 1),
                               date_trunc('week', now()), interval '1 week') AS w(week)
          LEFT JOIN sethu.complaint_summaries s ON date_trunc('week', s.filed_at) = w.week
           AND s.filed_at >= date_trunc('week', now()) - make_interval(weeks => :weeks - 1)  -- only the weeks shown
         GROUP BY w.week ORDER BY w.week""", weeks=weeks)


OVERDUE_MINE = f"""
        SELECT s.id, s.ref, b.code AS bureau, i.name AS institution, s.category, s.status, s.due_at
          FROM sethu.complaint_summaries s
          JOIN sethu.bureaus b ON b.id = s.bureau_id
          LEFT JOIN sethu.institutions i ON i.id = s.institution_id
         WHERE {OVERDUE} AND (sethu.ctx_sees_all() OR s.bureau_id = sethu.ctx_bureau())"""  # noqa: S608


def overdue_cases(session: Session, limit: int) -> dict:
    """The first overdue cases the caller's bureau holds (every bureau's for oversight, admin and auditor), with
    a total counted up to app.db.paging.COUNT_CAP."""
    return paging.page(session, OVERDUE_MINE, "s.due_at, s.ref", {}, limit, 0)


def pending(session: Session) -> dict:
    """Overlap suggestions and held alerts visible to the caller (Row-Level Security filters both), each
    counted up to COUNT_CAP + 1: the screen shows more than COUNT_CAP as "1,000+"."""
    return dict(session.execute(text("""
        SELECT (SELECT count(*) FROM (SELECT 1 FROM sethu.overlap_links WHERE status = 'proposed' LIMIT :n) x)
                   AS overlaps_to_review,
               (SELECT count(*) FROM (SELECT 1 FROM sethu.overlap_links WHERE status = 'approved' LIMIT :n) x)
                   AS overlaps_confirmed,
               (SELECT count(*) FROM (SELECT 1 FROM sethu.alerts WHERE status = 'pending_approval' LIMIT :n) x)
                   AS alerts_to_approve,
               (SELECT count(*) FROM (SELECT 1 FROM sethu.alerts WHERE status IN ('approved', 'failed') LIMIT :n) x)
                   AS alerts_unsent
    """), {"n": paging.COUNT_CAP + 1}).mappings().one())
