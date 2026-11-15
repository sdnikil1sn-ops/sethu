"""Append-only audit ledger.

Call `record` in the SAME transaction as the change it describes: either both
commit or neither does. The database assigns seq, ts and the hash chain.
"""
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import Principal


@dataclass(frozen=True)
class ChainStatus:
    ok: bool
    checked: int
    broken_seq: int | None
    reason: str | None


def record(
    session: Session,
    principal: Principal,
    action: str,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> int:
    """Append one entry and return its sequence number.

    Put identifiers and decisions in the payload, never complaint text or
    complainant details.
    """
    seq = session.execute(
        text(
            "INSERT INTO sethu.audit_log (actor, actor_role, action, entity_type, entity_id, payload)"
            " VALUES (:actor, :role, :action, :etype, :eid, CAST(:payload AS jsonb))"
            " RETURNING seq"
        ),
        {
            "actor": principal.subject,
            "role": principal.role,
            "action": action,
            "etype": entity_type,
            "eid": entity_id,
            "payload": json.dumps(payload or {}, sort_keys=True, default=str),
        },
    ).scalar_one()
    return int(seq)


def verify(session: Session) -> ChainStatus:
    row = session.execute(text("SELECT ok, checked, broken_seq, reason FROM sethu.audit_verify()")).one()
    return ChainStatus(ok=row.ok, checked=row.checked, broken_seq=row.broken_seq, reason=row.reason)
