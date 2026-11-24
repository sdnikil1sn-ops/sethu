"""SQL for cases. Listing reads sethu.complaint_summaries (every bureau, no text)
joined to sethu.complaints, which Row-Level Security empties for rows the caller
may not read. So `c.` columns are NULL exactly when the text is off limits."""
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import paging

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
    "bureau": "b.code = upper(:bureau)",
    "category": "s.category = :category",
    "status": "s.status = :status",
    "institution_id": "s.institution_id = :institution_id",
    "state": "i.state = :state",
    "filed_from": "s.filed_at >= :filed_from",
    "filed_to": "s.filed_at < CAST(:filed_to AS date) + 1",
    "overdue": "(s.status <> 'closed' AND s.due_at < now()) = :overdue",
    "ids": "s.id = ANY(:ids)",
    "q": "(s.ref ILIKE :q OR i.name ILIKE :q OR c.institution_name_raw ILIKE :q OR c.body ILIKE :q)",
}

# Why a case matched the top-bar search. Metadata reasons work across bureaus; the last two
# read `c`, which Row-Level Security leaves NULL where the caller may not read the text.
REASONS = """array_remove(ARRAY[
    CASE WHEN s.ref ILIKE :q THEN 'reference' END,
    CASE WHEN s.category ILIKE :q THEN 'category' END,
    CASE WHEN replace(s.status, '_', ' ') ILIKE :q THEN 'status' END,
    CASE WHEN upper(b.code) = upper(:code) OR b.name ILIKE :q THEN 'bureau' END,
    CASE WHEN i.name ILIKE :q THEN 'institution' END,
    CASE WHEN c.institution_name_raw ILIKE :q THEN 'institution name as typed' END,
    CASE WHEN c.body ILIKE :q THEN 'complaint text' END], NULL)"""

HISTORY = """
    SELECT a.id, c.ref, a.action, fb.code AS from_bureau, tb.code AS to_bureau, u.display_name AS actor,
           au.display_name AS assignee, a.note, a.reason, a.created_at, a.acknowledged_at
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


def lookup(session: Session, q: str, code: str, limit: int) -> list[dict]:
    """Cases matching q, each with the reasons it matched; reference matches first."""
    return _all(session, f"""
        SELECT * , count(*) OVER () AS total FROM (
            {SUMMARY.format(extra=f", {REASONS} AS why")}) m
         WHERE cardinality(m.why) > 0
         ORDER BY 'reference' = ANY(m.why) DESC, m.filed_at DESC, m.ref LIMIT :limit""",  # noqa: S608
                q=q, code=code, limit=limit)


def search(session: Session, filters: dict[str, Any], limit: int, offset: int) -> dict:
    """One page of cases, newest first, with a total counted only up to app.db.paging.COUNT_CAP (a broad filter
    over every case answers "1,000+" instead of counting them all)."""
    where = " AND ".join(FILTERS[name] for name in filters) or "true"
    return paging.page(session, SUMMARY.format(extra="") + f" WHERE {where}",  # noqa: S608 - constants only
                       "s.filed_at DESC, s.ref", filters, limit, offset)


def find(session: Session, complaint_id: UUID) -> dict | None:
    return _one(session, SUMMARY.format(  # noqa: S608 - fixed text
        extra=", c.body, c.institution_name_raw, c.language, c.source, c.resolution_state, c.complainant_enc,"
              " c.assignee_id, (SELECT display_name FROM sethu.app_users u WHERE u.id = c.assignee_id) AS assignee,"
              " (SELECT a.reason FROM sethu.case_actions a WHERE a.complaint_id = s.id AND a.action = 'closed'"
              "   ORDER BY a.created_at DESC LIMIT 1) AS close_reason")
        + " WHERE s.id = :id",
        id=complaint_id)


def not_on_key(session: Session, active: str, limit: int) -> list[dict]:
    """Encrypted complainant details whose key id is not the active one (the id is stored in the value:
    byte 3 holds its length, the id follows)."""
    return _all(session, """
        SELECT id, complainant_enc FROM sethu.complaints
         WHERE complainant_enc IS NOT NULL
           AND convert_from(substring(complainant_enc FROM 4 FOR get_byte(complainant_enc, 2)), 'UTF8') <> :active
         ORDER BY id LIMIT :limit""", active=active, limit=limit)


def set_complainant(session: Session, complaint_id: UUID, value: bytes) -> None:
    session.execute(text("UPDATE sethu.complaints SET complainant_enc = :v WHERE id = :id"),
                    {"id": complaint_id, "v": value})


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


def set_category(session: Session, complaint_id: UUID, category: str) -> None:
    session.execute(text("UPDATE sethu.complaints SET category = :c, updated_at = now() WHERE id = :id"),
                    {"c": category, "id": complaint_id})


def lock(session: Session, complaint_id: UUID) -> dict | None:
    """The case as the caller may read it, locked until the transaction ends."""
    return _one(session, """
        SELECT c.id, c.ref, c.status, c.category, c.bureau_id, c.transferred_from_bureau_id, c.assignee_id,
               b.code AS bureau
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


def update_case(session: Session, complaint_id: UUID, status: str, bureau_id: UUID, sender_id: UUID | None,
                assignee_id: UUID | None, due_at: Any = None) -> None:
    """Status, holder, sender and assignee as given; closed_at set on closing and cleared on reopening;
    due_at replaced only when given (a reopened case gets a new deadline)."""
    session.execute(text("""
        UPDATE sethu.complaints
           SET status = :status, bureau_id = :bureau, transferred_from_bureau_id = :sender, assignee_id = :assignee,
               closed_at = CASE WHEN :status = 'closed' THEN now() WHEN status = 'closed' THEN NULL ELSE closed_at END,
               due_at = coalesce(CAST(:due AS timestamptz), due_at), updated_at = now()
         WHERE id = :id"""), {"id": complaint_id, "status": status, "bureau": bureau_id, "sender": sender_id,
                              "assignee": assignee_id, "due": due_at})


def bureaus(session: Session) -> list[dict]:
    return _all(session, "SELECT id, code, name, active FROM sethu.bureaus ORDER BY code")


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





def insert_complaint(session: Session, **values: Any) -> str:
    """A new complaint with the next IN- reference. Returns the reference."""
    return session.execute(text(f"""
        INSERT INTO sethu.complaints ({', '.join(values)}, ref)
        VALUES ({', '.join(':' + k for k in values)},
                'IN-' || lpad(nextval('sethu.complaint_ref_seq')::text, 6, '0'))
        RETURNING ref"""), values).scalar_one()  # noqa: S608 - column names from service code


def same_text(session: Session, bureau_id: UUID, body_sha256: str, name: str) -> dict | None:
    """A complaint in this bureau with exactly this text about the same typed institution."""
    return _one(session, """
        SELECT id, ref FROM sethu.complaints
         WHERE bureau_id = :b AND body_sha256 = :h
           AND lower(regexp_replace(institution_name_raw, '[[:space:]]+', ' ', 'g')) = :name
         LIMIT 1""", b=bureau_id, h=body_sha256, name=name)


def similar_text(session: Session, bureau_id: UUID, institution_id: UUID | None, name: str, body: str,
                 threshold: float, days: int) -> dict | None:
    """The closest recent complaint in this bureau about the same institution whose text is similar."""
    return _one(session, """
        SELECT id, ref, similarity(body, :body) AS score FROM sethu.complaints
         WHERE bureau_id = :b AND filed_at > now() - make_interval(days => :days)
           AND (institution_id = :iid OR lower(regexp_replace(institution_name_raw, '[[:space:]]+', ' ', 'g')) = :name)
           AND similarity(body, :body) >= :t
         ORDER BY score DESC LIMIT 1""", b=bureau_id, iid=institution_id, name=name, body=body, t=threshold, days=days)


def deadline_days(session: Session, category: str | None) -> int | None:
    row = _one(session, "SELECT days FROM sethu.category_deadlines WHERE category = :c", c=category)
    return row["days"] if row else None


def deadlines(session: Session) -> list[dict]:
    """Every category in use or configured, with its days if an admin set them."""
    return _all(session, """
        SELECT k.category, d.days, d.updated_at
          FROM (SELECT DISTINCT category FROM sethu.complaint_summaries WHERE category IS NOT NULL
                UNION SELECT category FROM sethu.category_deadlines) k
          LEFT JOIN sethu.category_deadlines d ON d.category = k.category ORDER BY k.category""")


def set_deadline(session: Session, category: str, days: int, user_id: UUID | None) -> None:
    session.execute(text("""
        INSERT INTO sethu.category_deadlines (category, days, updated_by) VALUES (:c, :d, :u)
        ON CONFLICT (category) DO UPDATE SET days = :d, updated_by = :u, updated_at = now()"""),
        {"c": category, "d": days, "u": user_id})


def assigned_to(session: Session, user_id: UUID) -> list[dict]:
    """Open cases assigned to this person in the bureau holding them, soonest deadline first."""
    return _all(session, SUMMARY.format(extra="") + """
         WHERE c.assignee_id = :u AND s.status <> 'closed' AND c.bureau_id = sethu.ctx_bureau()
         ORDER BY s.due_at NULLS LAST, s.ref""", u=user_id)


def workload(session: Session) -> list[dict]:
    """Open cases per bureau and assignee (NULL: unassigned), for the bureaus the caller can read."""
    return _all(session, """
        SELECT b.code AS bureau, u.id AS assignee_id, u.display_name AS assignee, u.role,
               count(c.id) AS open, count(c.id) FILTER (WHERE c.due_at < now()) AS overdue
          FROM sethu.complaints c
          JOIN sethu.bureaus b ON b.id = c.bureau_id
          LEFT JOIN sethu.app_users u ON u.id = c.assignee_id
         WHERE c.status NOT IN ('closed', 'transferred')
         GROUP BY b.code, u.id, u.display_name, u.role
         ORDER BY b.code, u.display_name NULLS FIRST""")

