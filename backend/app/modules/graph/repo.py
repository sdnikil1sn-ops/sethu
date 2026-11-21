"""SQL for the network graph. Complaints come from sethu.complaint_summaries (metadata, every bureau, no text).
Overlap links, transfers and findings are read under Row-Level Security, so each role sees its own share."""
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

# Filter name -> SQL on the summary view `s`, its bureau `b` and institution `i`.
FILTERS = {
    "state": "i.state = :state",
    "category": "s.category = :category",
    "bureau": "b.code = upper(:bureau)",
    "filed_from": "s.filed_at >= :filed_from",
    "filed_to": "s.filed_at < CAST(:filed_to AS date) + 1",
    "institution_id": "s.institution_id = :institution_id",
}
CASES = """
      FROM sethu.complaint_summaries s
      JOIN sethu.bureaus b ON b.id = s.bureau_id
      JOIN sethu.institutions i ON i.id = s.institution_id
     WHERE {where}"""


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(r) for r in session.execute(text(sql), params).mappings()]


def _where(filters: dict) -> str:
    return " AND ".join(FILTERS[k] for k in filters) or "true"


def holdings(session: Session, filters: dict) -> list[dict]:
    """Cases per institution and holding bureau: the aggregated graph."""
    return _all(session, f"""
        SELECT s.institution_id, i.name AS institution, i.state, b.id AS bureau_id, b.code AS bureau,
               count(*) AS cases, count(*) FILTER (WHERE s.status <> 'closed') AS open,
               count(*) FILTER (WHERE s.status <> 'closed' AND s.due_at < now()) AS overdue
        {CASES.format(where=_where(filters))}
         GROUP BY s.institution_id, i.name, i.state, b.id, b.code""", **filters)  # noqa: S608 - fixed clauses


def complaints(session: Session, filters: dict, institution_ids: list[UUID]) -> list[dict]:
    """The complaints of the expanded institutions, as summaries."""
    return _all(session, f"""
        SELECT s.id, s.ref, s.status, s.category, s.filed_at, s.institution_id, b.code AS bureau,
               s.status <> 'closed' AND s.due_at < now() AS overdue
        {CASES.format(where=_where(filters) + " AND s.institution_id = ANY(:ids)")}
         ORDER BY s.filed_at""", **filters, ids=institution_ids)  # noqa: S608 - fixed clauses


def overlaps(session: Session) -> list[dict]:
    """Suggested and approved links the caller may see (Row-Level Security on overlap_links)."""
    return _all(session, """
        SELECT l.complaint_a, l.complaint_b, l.status, sa.institution_id
          FROM sethu.overlap_links l
          JOIN sethu.complaint_summaries sa ON sa.id = l.complaint_a
         WHERE l.status IN ('proposed', 'approved')""")


def transfers(session: Session, filters: dict) -> list[dict]:
    """Transfers between bureaus of the filtered cases, counted, from the history the caller may read."""
    return _all(session, f"""
        SELECT fb.code AS source, tb.code AS target, count(*) AS n
          FROM sethu.case_actions a
          JOIN sethu.bureaus fb ON fb.id = a.from_bureau_id
          JOIN sethu.bureaus tb ON tb.id = a.to_bureau_id
          JOIN sethu.complaint_summaries s ON s.id = a.complaint_id
          JOIN sethu.bureaus b ON b.id = s.bureau_id
          JOIN sethu.institutions i ON i.id = s.institution_id
         WHERE a.action = 'transferred' AND {_where(filters)}
         GROUP BY fb.code, tb.code""", **filters)  # noqa: S608 - fixed clauses


def open_findings(session: Session) -> list[dict]:
    """Open findings the caller may see (Row-Level Security on findings), with the institution of a case finding."""
    return _all(session, """
        SELECT f.kind, f.complaint_id, coalesce(f.institution_id, s.institution_id) AS institution_id,
               ARRAY(SELECT b.code FROM sethu.bureaus b WHERE b.id = ANY(f.bureau_ids)) AS bureaus,
               f.evidence->>'scope' AS scope
          FROM sethu.findings f
          LEFT JOIN sethu.complaint_summaries s ON s.id = f.complaint_id
         WHERE f.status = 'open'""")


def bureaus(session: Session) -> list[dict]:
    return _all(session, "SELECT id, code, name FROM sethu.bureaus ORDER BY code")
