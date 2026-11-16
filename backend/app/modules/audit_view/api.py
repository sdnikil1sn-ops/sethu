from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.session import get_session
from app.modules.audit_view import schemas, service

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

# shortcut: enforced here only. sethu.audit_log has no Row-Level Security because the
# chain trigger must read the last row whoever inserts; see docs/SECURITY.md.
READ = require_roles("auditor", "oversight", "admin")


@router.get("", response_model=schemas.EntryPage, dependencies=[Depends(READ)])
def list_entries(
    action: str | None = Query(None, max_length=100),
    actor: str | None = Query(None, max_length=100),
    entity_type: str | None = Query(None, max_length=100),
    entity_id: str | None = Query(None, max_length=100),
    date_from: date | None = None,
    date_to: date | None = None,
    before_seq: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict:
    given = {"action": action, "actor": actor, "entity_type": entity_type, "entity_id": entity_id,
             "date_from": date_from, "date_to": date_to, "before_seq": before_seq}
    return service.entries(session, {k: v for k, v in given.items() if v not in (None, "")}, limit)


@router.get("/verify", response_model=schemas.ChainReport)
def verify(principal: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    return service.verify(session, principal)
