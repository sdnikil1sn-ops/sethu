"""SQL for institutions and name resolution. Every query runs in the caller's
session, so Row-Level Security decides which complaints are visible."""
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

# Every spelling known for an institution: its canonical name and its aliases.
NAMES = """(SELECT id AS institution_id, name AS label FROM sethu.institutions
            UNION ALL SELECT institution_id, alias FROM sethu.institution_aliases)"""
COLUMNS = "i.id, i.permanent_id, i.name, i.state, i.district"


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(row) for row in session.execute(text(sql), params).mappings()]


def _one(session: Session, sql: str, **params: Any) -> dict | None:
    rows = _all(session, sql, **params)
    return rows[0] if rows else None


def list_institutions(session: Session, state: str | None, limit: int, offset: int) -> list[dict]:
    return _all(session, f"""
        SELECT {COLUMNS}, count(s.id) AS complaints,
               count(s.id) FILTER (WHERE s.status <> 'closed') AS open
          FROM sethu.institutions i
          LEFT JOIN sethu.complaint_summaries s ON s.institution_id = i.id
         WHERE CAST(:state AS text) IS NULL OR i.state = :state
         GROUP BY i.id ORDER BY i.name LIMIT :limit OFFSET :offset""",  # noqa: S608 - constants only
                state=state, limit=limit, offset=offset)


def get(session: Session, institution_id: UUID) -> dict | None:
    return _one(session, f"SELECT {COLUMNS} FROM sethu.institutions i WHERE i.id = :id",  # noqa: S608
                id=institution_id)


def by_permanent_id(session: Session, permanent_id: str) -> dict | None:
    return _one(session, f"SELECT {COLUMNS} FROM sethu.institutions i WHERE i.permanent_id = :pid",  # noqa: S608
                pid=permanent_id)


def aliases(session: Session, institution_id: UUID) -> list[dict]:
    return _all(session, "SELECT alias, source FROM sethu.institution_aliases"
                         " WHERE institution_id = :id ORDER BY alias", id=institution_id)


def summaries(session: Session, institution_id: UUID) -> list[dict]:
    """Cases from every bureau, without complaint text (the cross-bureau view)."""
    return _all(session, """
        SELECT s.id, s.ref, b.code AS bureau, s.category, s.status, s.filed_at, s.due_at, s.closed_at
          FROM sethu.complaint_summaries s JOIN sethu.bureaus b ON b.id = s.bureau_id
         WHERE s.institution_id = :id ORDER BY s.filed_at DESC""", id=institution_id)


def candidates(session: Session, q: str, limit: int) -> list[dict]:
    """Spellings close to q by pg_trgm (whole spelling, or q close to a word in it: "Greenfeild"
    scores 0.55 against Greenfield, under pg_trgm's default word threshold of 0.6), or containing it.
    One row per spelling. shortcut: scans every spelling (a few hundred); use the `<%` index at scale."""
    return _all(session, f"""
        SELECT {COLUMNS}, n.label, similarity(n.label, :q) AS similarity, word_similarity(:q, n.label) AS word
          FROM {NAMES} n JOIN sethu.institutions i ON i.id = n.institution_id
         WHERE n.label % :q OR word_similarity(:q, n.label) >= 0.5 OR strpos(lower(n.label), lower(:q)) > 0
         ORDER BY similarity DESC, i.name LIMIT :limit""", q=q, limit=limit)  # noqa: S608


def in_place(session: Session, q: str, limit: int) -> list[dict]:
    """Institutions whose district (the city) or state is q, ignoring case."""
    return _all(session, f"""
        SELECT {COLUMNS}, lower(i.district) = lower(:q) AS in_district FROM sethu.institutions i
         WHERE lower(i.district) = lower(:q) OR lower(i.state) = lower(:q)
         ORDER BY i.name LIMIT :limit""", q=q, limit=limit)  # noqa: S608


def counts(session: Session, ids: list[UUID]) -> dict[UUID, dict]:
    """Case counts (all bureaus, from the summaries view) for the given institutions."""
    rows = _all(session, """
        SELECT s.institution_id AS id, count(*) AS complaints, count(*) FILTER (WHERE s.status <> 'closed') AS open
          FROM sethu.complaint_summaries s WHERE s.institution_id = ANY(:ids) GROUP BY s.institution_id""",
                ids=list(ids))
    return {r["id"]: r for r in rows}


def by_acronym(session: Session, acronym: str) -> list[dict]:
    """Institutions whose initials spell the acronym: 'GIT' finds Greenfield Institute of Technology."""
    return _all(session, f"""
        SELECT {COLUMNS} FROM sethu.institutions i
         WHERE upper(:acronym) = (
               SELECT upper(string_agg(left(w, 1), '' ORDER BY n))
                 FROM string_to_table(i.name, ' ') WITH ORDINALITY AS t(w, n)
                WHERE lower(w) NOT IN ('of', 'and', 'the', 'for', ''))
         ORDER BY i.name LIMIT 20""", acronym=acronym)  # noqa: S608


def unresolved(session: Session, limit: int) -> list[dict]:
    return _all(session, """
        SELECT c.id, c.ref, b.code AS bureau, c.institution_name_raw, c.filed_at
          FROM sethu.complaints c JOIN sethu.bureaus b ON b.id = c.bureau_id
         WHERE c.resolution_state = 'unresolved' ORDER BY c.filed_at, c.ref LIMIT :limit""", limit=limit)


def set_resolution(session: Session, complaint_id: UUID, institution_id: UUID, state: str) -> dict | None:
    """Link an unresolved complaint. Returns None if it is not unresolved or not writable by the caller."""
    return _one(session, """
        UPDATE sethu.complaints SET institution_id = :iid, resolution_state = :state, updated_at = now()
         WHERE id = :cid AND resolution_state = 'unresolved'
     RETURNING ref, institution_name_raw""", cid=complaint_id, iid=institution_id, state=state)


def add_alias(session: Session, institution_id: UUID, alias: str, source: str) -> bool:
    return session.execute(text(
        "INSERT INTO sethu.institution_aliases (institution_id, alias, source) VALUES (:id, :alias, :source)"
        " ON CONFLICT (institution_id, alias) DO NOTHING"),
        {"id": institution_id, "alias": alias, "source": source}).rowcount == 1
