"""SQL for intake. Row-Level Security decides who reads and writes sources and items (migration 0009)."""
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

SOURCES = """
    SELECT s.id, s.name, s.channel, b.code AS bureau, s.bureau_id, s.priority, f.name AS fallback,
           s.fallback_source_id, s.active, s.marked_down, s.key_sha256 IS NOT NULL AS has_key,
           s.last_success_at, s.last_failure_at, s.failures,
           (SELECT count(*) FROM sethu.intake_items i WHERE i.source_id = s.id AND i.status = 'pending') AS pending,
           (SELECT count(*) FROM sethu.intake_items i WHERE i.source_id = s.id AND i.status = 'dead') AS dead,
           EXISTS (SELECT 1 FROM sethu.intake_sources p
                    WHERE p.fallback_source_id = s.id AND p.marked_down AND p.active) AS standing_in
      FROM sethu.intake_sources s
      JOIN sethu.bureaus b ON b.id = s.bureau_id
      LEFT JOIN sethu.intake_sources f ON f.id = s.fallback_source_id"""

ITEMS = """
    SELECT i.id, s.name AS source, b.code AS bureau, i.bureau_id, i.channel, i.path, i.status, i.attempts,
           CASE WHEN i.status = 'pending' THEN i.next_attempt_at END AS next_attempt_at, i.last_error,
           c.ref, d.ref AS duplicate_of, n.ref AS near_duplicate_of, i.review_state, i.created_at
      FROM sethu.intake_items i
      JOIN sethu.intake_sources s ON s.id = i.source_id
      JOIN sethu.bureaus b ON b.id = i.bureau_id
      LEFT JOIN sethu.complaint_summaries c ON c.id = i.complaint_id
      LEFT JOIN sethu.complaint_summaries d ON d.id = i.duplicate_of
      LEFT JOIN sethu.complaint_summaries n ON n.id = i.near_duplicate_of"""


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(r) for r in session.execute(text(sql), params).mappings()]


def _one(session: Session, sql: str, **params: Any) -> dict | None:
    rows = _all(session, sql, **params)
    return rows[0] if rows else None


def sources(session: Session, **where: Any) -> list[dict]:
    clauses = {"id": "s.id = :id", "name": "s.name = :name", "key": "s.key_sha256 = :key",
               "channel": "s.channel = :channel", "bureau_id": "s.bureau_id = :bureau_id"}
    sql = SOURCES + " WHERE " + (" AND ".join(clauses[k] for k in where) or "true")
    return _all(session, sql + " ORDER BY b.code, s.priority, s.name", **where)  # noqa: S608 - fixed clauses


def insert_source(session: Session, **values: Any) -> UUID:
    sql = f"INSERT INTO sethu.intake_sources ({', '.join(values)}) VALUES ({', '.join(':' + k for k in values)})"  # noqa: S608 - column names from service code
    return session.execute(text(sql + " RETURNING id"), values).scalar_one()


def update_source(session: Session, source_id: UUID, **values: Any) -> bool:
    sets = ", ".join(f"{k} = :{k}" for k in values)
    return session.execute(text(
        f"UPDATE sethu.intake_sources SET {sets}, updated_at = now() WHERE id = :id"),  # noqa: S608
        values | {"id": source_id}).rowcount == 1


def health(session: Session, source_id: UUID, ok: bool) -> None:
    """A processing attempt for this source succeeded or failed."""
    session.execute(text("""
        UPDATE sethu.intake_sources
           SET last_success_at = CASE WHEN :ok THEN now() ELSE last_success_at END,
               last_failure_at = CASE WHEN :ok THEN last_failure_at ELSE now() END,
               failures = CASE WHEN :ok THEN 0 ELSE failures + 1 END
         WHERE id = :id"""), {"id": source_id, "ok": ok})


def use_nonce(session: Session, source_id: UUID, nonce: str) -> bool:
    """False if this source already used the nonce (a replayed request)."""
    return session.execute(text("""
        INSERT INTO sethu.intake_nonces (source_id, nonce) VALUES (:s, :n)
        ON CONFLICT DO NOTHING RETURNING 1"""), {"s": source_id, "n": nonce}).first() is not None


def forget_nonces(session: Session, older_than_seconds: int) -> int:
    return session.execute(text(
        "DELETE FROM sethu.intake_nonces WHERE seen_at < now() - make_interval(secs => :s)"),
        {"s": older_than_seconds}).rowcount


def insert_item(session: Session, **values: Any) -> None:
    sql = f"INSERT INTO sethu.intake_items ({', '.join(values)}) VALUES ({', '.join(':' + k for k in values)})"  # noqa: S608 - column names from service code
    session.execute(text(sql), values)


def waiting_with(session: Session, source_id: UUID, fingerprint: str, external_ref: str | None) -> bool:
    """This source already delivered this complaint and it is waiting or done."""
    return _one(session, """
        SELECT 1 AS x FROM sethu.intake_items
         WHERE source_id = :s AND status IN ('pending','done')
           AND (fingerprint = :f OR (CAST(:r AS text) IS NOT NULL AND external_ref = :r)) LIMIT 1""",
                s=source_id, f=fingerprint, r=external_ref) is not None


def claim_next(session: Session) -> dict | None:
    """The next due pending item, locked; another worker skips it."""
    return _one(session, """
        SELECT i.id, i.source_id, i.bureau_id, i.channel, i.path, i.fingerprint, i.payload_enc, i.attempts,
               s.name AS source, s.marked_down AS source_down, s.active AS source_active
          FROM sethu.intake_items i JOIN sethu.intake_sources s ON s.id = i.source_id
         WHERE i.status = 'pending' AND i.next_attempt_at <= now()
         ORDER BY i.next_attempt_at, i.created_at
         FOR UPDATE OF i SKIP LOCKED LIMIT 1""")


def finish(session: Session, item_id: UUID, **values: Any) -> None:
    sets = ", ".join(f"{k} = :{k}" for k in values)
    session.execute(text(f"UPDATE sethu.intake_items SET {sets}, updated_at = now() WHERE id = :id"),  # noqa: S608
                    values | {"id": item_id})


def failed(session: Session, item_id: UUID, error: str, retry_in_seconds: int | None) -> None:
    """One more failed attempt: due again later, or dead (retry_in_seconds None)."""
    session.execute(text("""
        UPDATE sethu.intake_items
           SET attempts = attempts + 1, last_error = :e, updated_at = now(),
               status = CASE WHEN CAST(:later AS integer) IS NULL THEN 'dead' ELSE status END,
               next_attempt_at = CASE WHEN CAST(:later AS integer) IS NULL THEN next_attempt_at
                                      ELSE now() + make_interval(secs => CAST(:later AS integer)) END
         WHERE id = :id"""), {"id": item_id, "e": error, "later": retry_in_seconds})


def retry(session: Session, item_id: UUID) -> bool:
    return session.execute(text("""
        UPDATE sethu.intake_items SET status = 'pending', attempts = 0, next_attempt_at = now(), updated_at = now()
         WHERE id = :id AND status = 'dead'"""), {"id": item_id}).rowcount == 1


def reviewed(session: Session, item_id: UUID, user_id: UUID) -> bool:
    return session.execute(text("""
        UPDATE sethu.intake_items SET review_state = 'reviewed', reviewed_by = :u, reviewed_at = now()
         WHERE id = :id AND review_state = 'pending'"""), {"id": item_id, "u": user_id}).rowcount == 1


def items(session: Session, status: str | None, review: bool, limit: int) -> list[dict]:
    where = ["true"]
    if status:
        where.append("i.status = :status")
    if review:
        where.append("i.review_state = 'pending'")
    return _all(session, ITEMS + f" WHERE {' AND '.join(where)} ORDER BY i.created_at DESC LIMIT :limit",
                status=status, limit=limit)  # noqa: S608 - fixed clauses


def item(session: Session, item_id: UUID) -> dict | None:
    return _one(session, ITEMS + " WHERE i.id = :id", id=item_id)
