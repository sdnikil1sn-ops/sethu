"""SQL for the glossary: versions are append-only; the newest is in use."""
from sqlalchemy import text
from sqlalchemy.orm import Session


def current_version(session: Session) -> int:
    return session.execute(text("SELECT coalesce(max(version), 0) FROM sethu.glossary_terms")).scalar_one()


def terms(session: Session, version: int) -> list[dict]:
    return [dict(r) for r in session.execute(text("""
        SELECT language, term, english, type, notes, needs_review FROM sethu.glossary_terms
         WHERE version = :v ORDER BY language, term"""), {"v": version}).mappings()]


def versions(session: Session) -> list[dict]:
    return [dict(r) for r in session.execute(text("""
        SELECT version, count(*) AS terms, min(created_at) AS created_at FROM sethu.glossary_terms
         GROUP BY version ORDER BY version DESC""")).mappings()]


def insert_version(session: Session, version: int, rows: list[dict]) -> None:
    session.execute(text("""
        INSERT INTO sethu.glossary_terms (version, language, term, english, type, notes, needs_review)
        VALUES (:version, :language, :term, :english, :type, :notes, :needs_review)"""),
        [r | {"version": version} for r in rows])
