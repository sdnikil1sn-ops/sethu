"""SQL for cases. Listing reads sethu.complaint_summaries (every bureau, no text)
joined to sethu.complaints, which Row-Level Security empties for rows the caller
may not read. So `c.` columns are NULL exactly when the text is off limits."""
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import Principal

SUMMARY = """
    SELECT s.id, s.ref, b.code AS bureau, b.name AS bureau_name, s.category, s.status,
           s.institution_id, i.name AS institution, i.state, s.filed_at, s.due_at, s.closed_at,
           c.id IS NOT NULL AS readable, c.bureau_id AS holder_id{extra}
      FROM sethu.complaint_summaries s
      JOIN sethu.bureaus b ON b.id = s.bureau_id
      LEFT JOIN sethu.institutions i ON i.id = s.institution_id
      LEFT JOIN sethu.complaints c ON c.id = s.id"""

# Filter name -> SQL. Free text matches the reference and institution name for everyone,
# and complaint text only through `c`, that is, only where the caller may read it.
FILTERS = {
    "bureau": "b.code = :bureau",
    "category": "s.category = :category",
    "status": "s.status = :status",
    "institution_id": "s.institution_id = :institution_id",
    "state": "i.state = :state",
    "filed_from": "s.filed_at >= :filed_from",
    "filed_to": "s.filed_at < CAST(:filed_to AS date) + 1",
    "overdue": "(s.status <> 'closed' AND s.due_at < now()) = :overdue",
    "q": "(s.ref ILIKE :q OR i.name ILIKE :q OR c.institution_name_raw ILIKE :q OR c.body ILIKE :q)",
}

HISTORY = """
    SELECT a.id, c.ref, a.action, fb.code AS from_bureau, tb.code AS to_bureau, u.display_name AS actor,
           au.display_name AS assignee, a.note, a.created_at, a.acknowledged_at
      FROM sethu.case_actions a
      JOIN sethu.complaints c ON c.id = a.complaint_id
      LEFT JOIN sethu.bureaus fb ON fb.id = a.from_bureau_id
      LEFT JOIN sethu.bureaus tb ON tb.id = a.to_bureau_id
      LEFT JOIN sethu.app_users u ON u.id = a.actor_id
      LEFT JOIN sethu.app_users au ON au.id = a.assignee_id
     WHERE {where} ORDER BY a.created_at, a.id"""


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(row) for row in session.execute(text(sql), params).mappings()]


def _one(session: Session, sql: str, **params: Any) -> dict | None:
    rows = _all(session, sql, **params)
    return rows[0] if rows else None


def search(session: Session, filters: dict[str, Any], limit: int, offset: int) -> list[dict]:
    where = " AND ".join(FILTERS[name] for name in filters) or "true"
    return _all(session, SUMMARY.format(extra=", count(*) OVER () AS total")
                + f" WHERE {where} ORDER BY s.filed_at DESC, s.ref LIMIT :limit OFFSET :offset",  # noqa: S608
                **filters, limit=limit, offset=offset)


def find(session: Session, complaint_id: UUID) -> dict | None:
    return _one(session, SUMMARY.format(
        extra=", c.body, c.institution_name_raw, c.language, c.source, c.resolution_state") + " WHERE s.id = :id",
        id=complaint_id)


def history(session: Session, complaint_id: UUID) -> list[dict]:
    return _all(session, HISTORY.format(where="a.complaint_id = :id"), id=complaint_id)


def institution_history(session: Session, institution_id: UUID) -> list[dict]:
    return _all(session, HISTORY.format(where="c.institution_id = :id"), id=institution_id)


def case_counts(session: Session, institution_id: UUID) -> dict:
    """How many of an institution's cases exist, and how many the caller may read."""
    return _one(session, """
        SELECT count(*) AS total, count(c.id) AS readable
          FROM sethu.complaint_summaries s LEFT JOIN sethu.complaints c ON c.id = s.id
         WHERE s.institution_id = :id""", id=institution_id)  # type: ignore[return-value]


def lock(session: Session, complaint_id: UUID) -> dict | None:
    """The case as the caller may read it, locked until the transaction ends."""
    return _one(session, """
        SELECT c.id, c.ref, c.status, c.bureau_id, c.transferred_from_bureau_id, b.code AS bureau
          FROM sethu.complaints c JOIN sethu.bureaus b ON b.id = c.bureau_id
         WHERE c.id = :id FOR UPDATE OF c""", id=complaint_id)


def exists(session: Session, complaint_id: UUID) -> bool:
    return _one(session, "SELECT 1 AS x FROM sethu.complaint_summaries WHERE id = :id", id=complaint_id) is not None


def last_transfer(session: Session, complaint_id: UUID) -> dict | None:
    return _one(session, """
        SELECT from_bureau_id, to_bureau_id FROM sethu.case_actions
         WHERE complaint_id = :id AND action = 'transferred' ORDER BY created_at DESC LIMIT 1""", id=complaint_id)


def insert_action(session: Session, **values: Any) -> None:
    session.execute(text(
        f"INSERT INTO sethu.case_actions ({', '.join(values)})"  # noqa: S608 - column names from service code
        f" VALUES ({', '.join(':' + k for k in values)})"), values)


def update_case(session: Session, complaint_id: UUID, status: str, bureau_id: UUID, sender_id: UUID | None) -> None:
    session.execute(text("""
        UPDATE sethu.complaints
           SET status = :status, bureau_id = :bureau, transferred_from_bureau_id = :sender,
               closed_at = CASE WHEN :status = 'closed' THEN now() ELSE closed_at END, updated_at = now()
         WHERE id = :id"""), {"id": complaint_id, "status": status, "bureau": bureau_id, "sender": sender_id})


def bureaus(session: Session) -> list[dict]:
    return _all(session, "SELECT id, code, name FROM sethu.bureaus ORDER BY code")


def staff(session: Session, bureau_id: UUID) -> list[dict]:
    """People a case held by this bureau can be assigned to."""
    return _all(session, """
        SELECT id, display_name, role FROM sethu.app_users
         WHERE bureau_id = :b AND active AND role IN ('officer', 'bureau_head') ORDER BY display_name""", b=bureau_id)


def options(session: Session) -> dict:
    row = _one(session, """
        SELECT (SELECT array_agg(DISTINCT category ORDER BY category) FROM sethu.complaint_summaries
                 WHERE category IS NOT NULL) AS categories,
               (SELECT array_agg(DISTINCT state ORDER BY state) FROM sethu.institutions
                 WHERE state IS NOT NULL) AS states""") or {}
    return {"categories": row.get("categories") or [], "states": row.get("states") or []}


def ensure_user(session: Session, principal: Principal) -> tuple[UUID, bool]:
    """The app_users row for a logged-in person, created from the token on first use."""
    found = _one(session, "SELECT id FROM sethu.app_users WHERE subject = :s", s=principal.subject)
    if found:
        return found["id"], False
    return session.execute(text(
        "INSERT INTO sethu.app_users (subject, display_name, role, bureau_id) VALUES (:s, :n, :r, :b) RETURNING id"),
        {"s": principal.subject, "n": principal.name, "r": principal.role, "b": principal.bureau_id}).scalar_one(), True
