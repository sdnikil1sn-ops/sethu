"""SQL for bureaus. Row-Level Security: every signed-in role reads; only admin and system write."""
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

COLUMNS = "id, code, name, active, created_at, updated_at"


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(row) for row in session.execute(text(sql), params).mappings()]


def listing(session: Session) -> list[dict]:
    """Every bureau, with how many cases it holds and how many people belong to it."""
    return _all(session, f"""
        SELECT {COLUMNS},
               (SELECT count(*) FROM sethu.complaint_summaries s WHERE s.bureau_id = b.id) AS cases,
               (SELECT count(*) FROM sethu.app_users u WHERE u.bureau_id = b.id) AS people,
               (SELECT count(*) FROM sethu.app_users u WHERE u.bureau_id = b.id AND u.role = 'bureau_head'
                   AND u.active AND u.email IS NOT NULL) AS heads_with_email
          FROM sethu.bureaus b ORDER BY b.code""")  # noqa: S608 - constants only


def get(session: Session, bureau_id: UUID) -> dict | None:
    rows = _all(session, f"SELECT {COLUMNS} FROM sethu.bureaus WHERE id = :id", id=bureau_id)  # noqa: S608
    return rows[0] if rows else None


def by_code(session: Session, code: str) -> dict | None:
    rows = _all(session, f"SELECT {COLUMNS} FROM sethu.bureaus WHERE code = :c", c=code)  # noqa: S608
    return rows[0] if rows else None


def insert(session: Session, code: str, name: str) -> UUID:
    return session.execute(text("INSERT INTO sethu.bureaus (code, name) VALUES (:c, :n) RETURNING id"),
                           {"c": code, "n": name}).scalar_one()


def update(session: Session, bureau_id: UUID, name: str, active: bool) -> bool:
    """False when Row-Level Security (or the row's absence) stops the update."""
    return session.execute(text("""
        UPDATE sethu.bureaus SET name = :n, active = :a, updated_at = now() WHERE id = :id"""),
        {"id": bureau_id, "n": name, "a": active}).rowcount == 1
