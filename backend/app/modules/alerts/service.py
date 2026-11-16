"""Alert outbox: human approval of held alerts, and delivery by the worker (ADR 0004).

Delivery takes one approved alert at a time with FOR UPDATE SKIP LOCKED, so two
workers never hold the same alert. It sends one email per recipient through the
configured SMTP relay and records each one in the audit log, in the same
transaction that finally marks the alert sent. If a send fails, the alert stays
`approved` with the error and attempt count, and the next run sends only to the
recipients not reached yet. A crash mid-run can repeat at most the emails of the
alert in hand (at-least-once, as ADR 0004 accepts).

The worker sends the alert's subject and body as written. Those are composed by
the module that raised the alert from references, institution and category only.
"""
import smtplib
from email.message import EmailMessage
from uuid import UUID

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.modules.alerts import repo
from app.modules.complaints import service as complaints


class AlertError(Exception):
    """A request that cannot be carried out. `status` is the HTTP status to answer with."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def _shape(principal: Principal, alert: dict) -> dict:
    return alert | {
        "cases": sorted(alert["cases"]),
        "can_decide": alert["status"] == "pending_approval" and principal.role in ("bureau_head", "oversight"),
    }


def listing(session: Session, principal: Principal, status: str | None = None) -> list[dict]:
    return [_shape(principal, a) for a in repo.listing(session, status=status)]


def decide(session: Session, principal: Principal, alert_id: UUID, approve: bool) -> dict:
    """Release (approve) or drop (reject) an alert held in pending_approval. Audited in the same transaction."""
    found = repo.listing(session, alert_id=alert_id)
    if not found:  # Row-Level Security hides alerts that do not concern the caller's bureau
        raise AlertError(404, "alert not found")
    if found[0]["status"] != "pending_approval":
        raise AlertError(409, f"this alert is already {found[0]['status'].replace('_', ' ')}")
    status = "approved" if approve else "rejected"
    if not repo.decide(session, alert_id, status, complaints.actor_id(session, principal)):
        raise AlertError(403, "only a head of a bureau this alert concerns, or oversight, can decide it")
    audit.record(session, principal, f"alert.{'approve' if approve else 'reject'}", entity_type="alerts",
                 entity_id=str(alert_id), payload={"kind": found[0]["kind"], "cases": sorted(found[0]["cases"])})
    return _shape(principal, repo.listing(session, alert_id=alert_id)[0])


def _send_one(session: Session, alert: dict, host: str, port: int, sender: str) -> str:
    """Deliver one claimed alert inside the caller's transaction. Returns its new status."""
    alert_id, recipients = alert["id"], alert["recipients"]
    entity = {"entity_type": "alerts", "entity_id": str(alert_id)}

    # Only people who are SETHU users may receive alert mail: nothing goes to an address someone typed in.
    unknown = sorted(set(recipients) - repo.known_addresses(session, recipients))
    if unknown or not recipients:
        reason = f"not a SETHU user: {', '.join(unknown)}" if unknown else "no recipients"
        repo.mark(session, alert_id, "failed", reason)
        audit.record(session, SYSTEM, "alert.refused", **entity, payload={"unknown_recipients": len(unknown)})
        return "failed"

    reached = repo.delivered_to(session, alert_id)
    try:
        if pending := [r for r in recipients if r not in reached]:
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                for recipient in pending:
                    message = EmailMessage()
                    message["From"], message["To"], message["Subject"] = sender, recipient, alert["subject"]
                    message.set_content(alert["body"])
                    smtp.send_message(message)
                    audit.record(session, SYSTEM, "alert.delivered", **entity, payload={"recipient": recipient})
                    reached.add(recipient)
    except (OSError, smtplib.SMTPException) as e:
        # Stays approved: the next run retries the recipients not reached yet.
        # shortcut: retried on every run with no backoff; add a next-attempt time if a relay is down for long.
        repo.mark(session, alert_id, "approved", f"{type(e).__name__}: {e}"[:500])
        audit.record(session, SYSTEM, "alert.send_failed", **entity,
                     payload={"error": type(e).__name__, "reached": len(reached), "recipients": len(recipients)})
        return "approved"
    repo.mark(session, alert_id, "sent", None)
    audit.record(session, SYSTEM, "alert.sent", **entity, payload={"recipients": len(recipients)})
    return "sent"


def deliver(engine: Engine | None = None, host: str | None = None, port: int | None = None,
            limit: int = 50) -> dict[str, int]:
    """Send approved alerts, one transaction per alert. Safe to run from several workers at once."""
    settings = get_settings()
    host, port = host or settings.smtp_host, port or settings.smtp_port
    tried: list[UUID] = []
    result = {"sent": 0, "retry": 0, "failed": 0}
    while len(tried) < limit:
        with session_for(SYSTEM, engine) as session:
            alert = repo.claim_next(session, tried)
            if alert is None:
                break
            tried.append(alert["id"])
            outcome = _send_one(session, alert, host, port, settings.alert_from)
        result[{"sent": "sent", "approved": "retry", "failed": "failed"}[outcome]] += 1
    return result
