"""SQL for enrichment, attachments and review items. Row-Level Security decides what each caller sees."""
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

ENRICHMENT = """complaint_id, status, language, language_confidence, language_candidates, translated_text,
    translation_path, tags, glossary_version, glossary_coverage, ocr_text, ocr_path, attempts, updated_at"""
ATTACHMENT = "id, complaint_id, filename, content_type, size_bytes, sha256, ocr_status, created_at"


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(r) for r in session.execute(text(sql), params).mappings()]


def insert_pending(session: Session, complaint_id: UUID) -> None:
    session.execute(text("INSERT INTO sethu.complaint_enrichment (complaint_id) VALUES (:c) ON CONFLICT DO NOTHING"),
                    {"c": complaint_id})


def claim(session: Session, limit: int) -> list[dict]:
    """Complaints whose enrichment is pending, or that have an attachment waiting to be read; oldest first. Each
    attempt is counted (a complaint that keeps failing goes to a person instead of looping)."""
    return _all(session, """
        UPDATE sethu.complaint_enrichment e SET attempts = attempts + 1, status = 'pending', updated_at = now()
         WHERE e.complaint_id IN (
               SELECT complaint_id FROM sethu.complaint_enrichment WHERE status = 'pending'
               UNION SELECT complaint_id FROM sethu.complaint_attachments WHERE ocr_status = 'pending'
               ORDER BY 1 LIMIT :limit)
        RETURNING e.complaint_id, e.attempts, e.language, e.ocr_text""", limit=limit)


def can_read_case(session: Session, complaint_id: UUID) -> bool:
    """The complaint row is visible only where its text is (Row-Level Security on sethu.complaints)."""
    found = session.execute(text("SELECT 1 FROM sethu.complaints WHERE id = :c"), {"c": complaint_id})
    return found.first() is not None


def body(session: Session, complaint_id: UUID) -> str:
    return session.execute(text("SELECT body FROM sethu.complaints WHERE id = :c"), {"c": complaint_id}).scalar_one()


def pending_attachments(session: Session, complaint_id: UUID) -> list[dict]:
    return _all(session, """SELECT id, content_type, data_enc FROM sethu.complaint_attachments
                             WHERE complaint_id = :c AND ocr_status = 'pending' ORDER BY created_at""", c=complaint_id)


def save(session: Session, complaint_id: UUID, **fields: Any) -> None:
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    session.execute(text(f"UPDATE sethu.complaint_enrichment SET {sets}, updated_at = now() "  # noqa: S608 - names
                         "WHERE complaint_id = :complaint_id"), fields | {"complaint_id": complaint_id})


def set_attachment_status(session: Session, attachment_id: UUID, status: str) -> None:
    session.execute(text("UPDATE sethu.complaint_attachments SET ocr_status = :s WHERE id = :i"),
                    {"s": status, "i": attachment_id})


def add_review(session: Session, kind: str, complaint_id: UUID, reason: str, ai_run_id: str | None = None,
               attachment_id: UUID | None = None) -> UUID:
    return session.execute(text("""
        INSERT INTO sethu.review_items (kind, complaint_id, attachment_id, ai_run_id, reason)
        VALUES (:k, :c, :a, :r, :reason) RETURNING id"""),
        {"k": kind, "c": complaint_id, "a": attachment_id, "r": ai_run_id, "reason": reason[:500]}).scalar_one()


def enrichment(session: Session, complaint_id: UUID) -> dict | None:
    rows = _all(session, f"SELECT {ENRICHMENT} FROM sethu.complaint_enrichment WHERE complaint_id = :c",  # noqa: S608
                c=complaint_id)
    return rows[0] if rows else None


def insert_attachment(session: Session, **values: Any) -> None:
    session.execute(text(f"""INSERT INTO sethu.complaint_attachments ({', '.join(values)})
                             VALUES ({', '.join(':' + k for k in values)})"""), values)  # noqa: S608 - names


def attachments(session: Session, complaint_id: UUID) -> list[dict]:
    return _all(session, f"SELECT {ATTACHMENT} FROM sethu.complaint_attachments WHERE complaint_id = :c "  # noqa: S608
                         "ORDER BY created_at", c=complaint_id)


def attachment(session: Session, attachment_id: UUID) -> dict | None:
    rows = _all(session, f"SELECT {ATTACHMENT}, data_enc FROM sethu.complaint_attachments WHERE id = :i",  # noqa: S608
                i=attachment_id)
    return rows[0] if rows else None


def not_on_key(session: Session, active: str, limit: int) -> list[dict]:
    """Attachments sealed with a key other than the active one (the key id is stored in the value)."""
    return _all(session, """
        SELECT id, data_enc FROM sethu.complaint_attachments
         WHERE convert_from(substring(data_enc FROM 4 FOR get_byte(data_enc, 2)), 'UTF8') <> :active
         ORDER BY id LIMIT :limit""", active=active, limit=limit)


def set_data(session: Session, attachment_id: UUID, value: bytes) -> None:
    session.execute(text("UPDATE sethu.complaint_attachments SET data_enc = :v WHERE id = :i"),
                    {"v": value, "i": attachment_id})


def same_file(session: Session, complaint_id: UUID, sha256: str) -> bool:
    return session.execute(text("SELECT 1 FROM sethu.complaint_attachments WHERE complaint_id = :c AND sha256 = :h"),
                           {"c": complaint_id, "h": sha256}).first() is not None


def review_items(session: Session, status: str | None, limit: int) -> list[dict]:
    return _all(session, """
        SELECT r.id, r.kind, r.complaint_id, s.ref, b.code AS bureau, r.attachment_id, r.reason, r.status,
               r.created_at, r.resolved_at
          FROM sethu.review_items r
          JOIN sethu.complaint_summaries s ON s.id = r.complaint_id
          JOIN sethu.bureaus b ON b.id = s.bureau_id
         WHERE (CAST(:status AS text) IS NULL OR r.status = :status)
         ORDER BY r.status = 'open' DESC, r.created_at DESC LIMIT :limit""", status=status, limit=limit)


def resolve(session: Session, item_id: UUID, status: str, actor_id: UUID | None) -> dict | None:
    rows = _all(session, """
        UPDATE sethu.review_items SET status = :s, resolved_by = :a, resolved_at = now()
         WHERE id = :i AND status = 'open' RETURNING id, kind, complaint_id""", s=status, a=actor_id, i=item_id)
    return rows[0] if rows else None
