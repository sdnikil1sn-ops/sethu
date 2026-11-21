
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.audit import anchor
from app.core.auth import Principal, require_roles
from app.core.params import Day, Text100
from app.db.session import get_session
from app.modules.audit_view import schemas, service
from app.modules.audit_view import signins as signin_events

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

# shortcut: enforced here only. sethu.audit_log has no Row-Level Security because the
# chain trigger must read the last row whoever inserts; see docs/SECURITY.md.
READ = require_roles("auditor", "oversight", "admin")


@router.get("", response_model=schemas.EntryPage, dependencies=[Depends(READ)])
def list_entries(
    action: Text100 = None,
    actor: Text100 = None,
    entity_type: Text100 = None,
    entity_id: Text100 = None,
    date_from: Day = None,
    date_to: Day = None,
    before_seq: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict:
    given = {"action": action, "actor": actor, "entity_type": entity_type, "entity_id": entity_id,
             "date_from": date_from, "date_to": date_to, "before_seq": before_seq}
    return service.entries(session, {k: v for k, v in given.items() if v is not None}, limit)


@router.get("/verify", response_model=schemas.ChainReport)
def verify(principal: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    return service.verify(session, principal)


@router.get("/anchor", response_model=schemas.AnchorReport, dependencies=[Depends(READ)])
def anchor_check(session: Session = Depends(get_session)) -> dict:
    """The exported chain anchors compared with the live chain."""
    return anchor.compare(session)


@router.get("/signins", response_model=list[schemas.SignIn], dependencies=[Depends(READ)])
def signins(failed: bool = True, limit: int = Query(100, ge=1, le=500)) -> list[dict]:
    """Keycloak's sign-in events (read-only): failed ones by default."""
    try:
        return signin_events.fetch(failed, limit)
    except signin_events.Unavailable as e:
        raise HTTPException(503, str(e)) from e
