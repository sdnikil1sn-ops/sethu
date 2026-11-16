"""SQL for the alert outbox. Row-Level Security decides which alerts a caller sees."""
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(row) for row in session.execute(text(sql), params).mappings()]


def listing(session: Session, *, status: str | None = None, alert_id: UUID | None = None) -> list[dict]:
    """Alerts the caller may see, newest first, with the references of the cases they concern."""
    return _all(session, """
        SELECT al.id, al.kind, al.status, al.subject, al.body, al.recipients, al.created_at,
               al.approved_at, u.display_name AS approved_by, al.sent_at, al.attempts, al.last_error,
               array_remove(ARRAY[ca.ref, cb.ref, cc.ref], NULL) AS cases
          FROM sethu.alerts al
          LEFT JOIN sethu.app_users u ON u.id = al.approved_by
          LEFT JOIN sethu.overlap_links l ON l.id = al.overlap_link_id
          LEFT JOIN sethu.complaint_summaries ca ON ca.id = l.complaint_a
          LEFT JOIN sethu.complaint_summaries cb ON cb.id = l.complaint_b
          LEFT JOIN sethu.complaint_summaries cc ON cc.id = al.complaint_id
         WHERE (CAST(:status AS text) IS NULL OR al.status = :status)
           AND (CAST(:id AS uuid) IS NULL OR al.id = :id)
         ORDER BY al.created_at DESC""", status=status, id=alert_id)


def decide(session: Session, alert_id: UUID, status: str, actor_id: UUID) -> bool:
    """False when the alert is no longer held, or the database does not let this caller decide it."""
    return session.execute(text("""
        UPDATE sethu.alerts SET status = :status, approved_by = :actor, approved_at = now()
         WHERE id = :id AND status = 'pending_approval'"""),
        {"id": alert_id, "status": status, "actor": actor_id}).rowcount == 1


def claim_next(session: Session, skip: list[UUID]) -> dict | None:
    """The oldest approved alert no other worker is holding, locked until this transaction ends."""
    rows = _all(session, """
        SELECT id, recipients, subject, body FROM sethu.alerts
         WHERE status = 'approved' AND NOT (id = ANY(:skip))
         ORDER BY approved_at NULLS FIRST, created_at
         LIMIT 1 FOR UPDATE SKIP LOCKED""", skip=skip)
    return rows[0] if rows else None


def delivered_to(session: Session, alert_id: UUID) -> set[str]:
    """Recipients an earlier, partly failed run already reached (from the audit log)."""
    return {r["recipient"] for r in _all(session, """
        SELECT payload->>'recipient' AS recipient FROM sethu.audit_log
         WHERE action = 'alert.delivered' AND entity_id = :id""", id=str(alert_id))}


def known_addresses(session: Session, addresses: list[str]) -> set[str]:
    return {r["email"] for r in _all(
        session, "SELECT email FROM sethu.app_users WHERE active AND email = ANY(:a)", a=addresses)}


def mark(session: Session, alert_id: UUID, status: str, error: str | None) -> None:
    session.execute(text("""
        UPDATE sethu.alerts
           SET status = :status, attempts = attempts + 1, last_error = :error,
               sent_at = CASE WHEN :status = 'sent' THEN now() END
         WHERE id = :id"""), {"id": alert_id, "status": status, "error": error})
