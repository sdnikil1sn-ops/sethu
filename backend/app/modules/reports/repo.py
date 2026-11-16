"""SQL for reports. Case figures come from sethu.complaint_summaries (no complaint text).
SCOPE keeps bureau staff to their own bureau's cases, read from the request context;
overlap links and alerts are already limited to the caller's bureau by Row-Level Security."""
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

SCOPE = "(sethu.ctx_sees_all() OR s.bureau_id = sethu.ctx_bureau())"
OVERDUE = "(s.status <> 'closed' AND s.due_at < now())"


def _in_range(column: str) -> str:
    return (f"((CAST(:date_from AS date) IS NULL OR {column} >= CAST(:date_from AS date))"
            f" AND (CAST(:date_to AS date) IS NULL OR {column} < CAST(:date_to AS date) + 1))")


def _all(session: Session, sql: str, date_from: date | None, date_to: date | None) -> list[dict[str, Any]]:
    rows = session.execute(text(sql), {"date_from": date_from, "date_to": date_to}).mappings()
    return [dict(r) for r in rows]


def institutions(session: Session, date_from: date | None, date_to: date | None) -> list[dict]:
    """Per institution: the caller's cases filed in the range, and how many bureaus (any) hold cases there."""
    return _all(session, f"""
        SELECT i.id AS institution_id, i.permanent_id, i.name AS institution, i.state, i.district,
               count(*) FILTER (WHERE {SCOPE}) AS cases,
               count(*) FILTER (WHERE {SCOPE} AND s.status <> 'closed') AS open,
               count(*) FILTER (WHERE {SCOPE} AND {OVERDUE}) AS overdue,
               count(DISTINCT s.bureau_id) AS bureaus
          FROM sethu.complaint_summaries s JOIN sethu.institutions i ON i.id = s.institution_id
         WHERE {_in_range("s.filed_at")}
         GROUP BY i.id HAVING count(*) FILTER (WHERE {SCOPE}) > 0
         ORDER BY cases DESC, i.name""", date_from, date_to)  # noqa: S608 - constants only


def bureaus(session: Session, date_from: date | None, date_to: date | None) -> list[dict]:
    """Per bureau: filed and closed in the range, median days to close for those closed,
    and how many of those filed in the range are overdue now."""
    closed = f"s.status = 'closed' AND {_in_range('s.closed_at')}"
    return _all(session, f"""
        SELECT b.code AS bureau, b.name AS bureau_name,
               count(s.id) FILTER (WHERE {_in_range("s.filed_at")}) AS filed,
               count(s.id) FILTER (WHERE {closed}) AS closed,
               round(CAST(percentile_cont(0.5) WITHIN GROUP (
                   ORDER BY extract(epoch FROM s.closed_at - s.filed_at) / 86400) FILTER (WHERE {closed})
                   AS numeric), 1) AS median_days_to_close,
               count(s.id) FILTER (WHERE {_in_range("s.filed_at")} AND {OVERDUE}) AS overdue
          FROM sethu.bureaus b LEFT JOIN sethu.complaint_summaries s ON s.bureau_id = b.id
         WHERE sethu.ctx_sees_all() OR b.id = sethu.ctx_bureau()
         GROUP BY b.code, b.name ORDER BY b.code""", date_from, date_to)  # noqa: S608


def overlaps(session: Session, date_from: date | None, date_to: date | None) -> list[dict]:
    """Per pair of bureaus: links suggested in the range and what became of them."""
    return _all(session, f"""
        SELECT least(ba.code, bb.code) || ' + ' || greatest(ba.code, bb.code) AS bureaus,
               count(DISTINCT l.id) AS suggested,
               count(DISTINCT l.id) FILTER (WHERE l.status = 'approved') AS approved,
               count(DISTINCT l.id) FILTER (WHERE l.status = 'rejected') AS rejected,
               count(DISTINCT l.id) FILTER (WHERE l.status = 'proposed') AS pending,
               count(DISTINCT al.id) FILTER (WHERE al.status = 'sent') AS alerts_sent
          FROM sethu.overlap_links l
          JOIN sethu.complaint_summaries a ON a.id = l.complaint_a
          JOIN sethu.complaint_summaries b ON b.id = l.complaint_b
          JOIN sethu.bureaus ba ON ba.id = a.bureau_id
          JOIN sethu.bureaus bb ON bb.id = b.bureau_id
          LEFT JOIN sethu.alerts al ON al.overlap_link_id = l.id
         WHERE {_in_range("l.created_at")}
         GROUP BY 1 ORDER BY 1""", date_from, date_to)  # noqa: S608
