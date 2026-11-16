"""The audit screen: browse the hash-chained audit log and verify the chain."""
import re
from dataclasses import asdict
from typing import Any

from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.modules.audit_view import repo


def entries(session: Session, filters: dict[str, Any], limit: int) -> dict:
    if "actor" in filters:
        # The typed name is taken literally: % and _ are not wildcards.
        filters["actor"] = "%" + re.sub(r"([\\%_])", r"\\\1", filters["actor"]) + "%"
    return {"items": repo.entries(session, filters, limit), "actions": repo.actions(session)}


def verify(session: Session, principal: Principal) -> dict:
    """Walk the chain with sethu.audit_verify(). If it is broken, return the first bad row too."""
    result = audit.verify(session)
    audit.record(session, principal, "audit.verify",
                 payload={"ok": result.ok, "checked": result.checked, "broken_seq": result.broken_seq})
    row = repo.entry(session, result.broken_seq) if result.broken_seq is not None else None
    return asdict(result) | {"row": row}
