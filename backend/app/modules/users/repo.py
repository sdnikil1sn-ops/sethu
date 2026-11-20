"""SQL for people (sethu.app_users). Row-Level Security lets a person write only their own row,
with the role and bureau of their token; admin and system may write any row."""
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(row) for row in session.execute(text(sql), params).mappings()]


def find(session: Session, subject: str) -> dict | None:
    rows = _all(session, "SELECT id, display_name, email, role, bureau_id FROM sethu.app_users WHERE subject = :s",
                s=subject)
    return rows[0] if rows else None


def insert(session: Session, subject: str, display_name: str, email: str | None, role: str,
           bureau_id: UUID | None) -> UUID:
    return session.execute(text("""
        INSERT INTO sethu.app_users (subject, display_name, email, role, bureau_id)
        VALUES (:s, :n, :e, :r, :b) RETURNING id"""),
        {"s": subject, "n": display_name, "e": email, "r": role, "b": bureau_id}).scalar_one()


def update(session: Session, user_id: UUID, display_name: str, email: str | None, role: str,
           bureau_id: UUID | None) -> None:
    session.execute(text("""
        UPDATE sethu.app_users SET display_name = :n, email = :e, role = :r, bureau_id = :b, updated_at = now()
         WHERE id = :id"""), {"id": user_id, "n": display_name, "e": email, "r": role, "b": bureau_id})


def heads(session: Session, bureau_ids: list[UUID]) -> list[dict]:
    """Active bureau heads of these bureaus, with or without an e-mail address."""
    return _all(session, """
        SELECT b.code, u.email FROM sethu.bureaus b
          LEFT JOIN sethu.app_users u ON u.bureau_id = b.id AND u.role = 'bureau_head' AND u.active
         WHERE b.id = ANY(:b) ORDER BY b.code, u.email""", b=list(bureau_ids))


def listing(session: Session) -> list[dict]:
    """Everyone, with their bureau's code. For the admin screen."""
    return _all(session, """
        SELECT u.id, u.display_name, u.email, u.role, b.code AS bureau, u.active, u.updated_at
          FROM sethu.app_users u LEFT JOIN sethu.bureaus b ON b.id = u.bureau_id
         ORDER BY u.email IS NOT NULL, b.code NULLS FIRST, u.role, u.display_name""")
