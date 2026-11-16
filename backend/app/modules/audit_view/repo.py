"""SQL for reading the audit ledger. Read only: the ledger is append-only."""
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

ENTRY = """
    SELECT a.seq, a.ts, a.actor, coalesce(u.display_name, a.actor) AS actor_name, a.actor_role,
           a.action, a.entity_type, a.entity_id, a.payload, a.prev_hash, a.hash
      FROM sethu.audit_log a
      LEFT JOIN sethu.app_users u ON u.subject = a.actor"""

FILTERS = {
    "action": "starts_with(a.action, :action)",
    "actor": "(u.display_name ILIKE :actor OR a.actor ILIKE :actor)",
    "entity_type": "a.entity_type = :entity_type",
    "entity_id": "a.entity_id = :entity_id",
    "date_from": "a.ts >= :date_from",
    "date_to": "a.ts < CAST(:date_to AS date) + 1",
    "before_seq": "a.seq < :before_seq",
}


def entries(session: Session, filters: dict[str, Any], limit: int) -> list[dict]:
    """Newest first. Page with before_seq = the last seq shown."""
    where = " AND ".join(FILTERS[name] for name in filters) or "true"
    sql = f"{ENTRY} WHERE {where} ORDER BY a.seq DESC LIMIT :limit"  # noqa: S608 - fixed fragments only
    return [dict(r) for r in session.execute(text(sql), filters | {"limit": limit}).mappings()]


def entry(session: Session, seq: int) -> dict | None:
    row = session.execute(text(f"{ENTRY} WHERE a.seq = :seq"), {"seq": seq}).mappings().first()  # noqa: S608
    return dict(row) if row else None


def actions(session: Session) -> list[str]:
    return list(session.execute(text("SELECT DISTINCT action FROM sethu.audit_log ORDER BY action")).scalars())
