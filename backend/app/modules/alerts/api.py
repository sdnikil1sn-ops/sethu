from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.core.config import get_settings
from app.db.session import get_session
from app.modules.alerts import schemas, service

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
DECIDE = require_roles("bureau_head", "oversight")  # and the database checks the bureau is concerned


@router.get("", response_model=schemas.AlertPage)
def list_alerts(
    status: Literal["pending_approval", "approved", "sent", "rejected", "failed"] | None = None,
    principal: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> dict:
    # Mailpit is published on this address by docker-compose.yml, in the dev profile only.
    inbox = "http://localhost:8025" if get_settings().environment == "dev" else None
    return {"items": service.listing(session, principal, status), "mail_inbox_url": inbox}


@router.post("/{alert_id}/decision", response_model=schemas.Alert)
def decide(
    alert_id: UUID,
    body: schemas.DecisionIn,
    principal: Principal = Depends(DECIDE),
    session: Session = Depends(get_session),
) -> dict:
    try:
        return service.decide(session, principal, alert_id, body.decision == "approve")
    except service.AlertError as e:
        raise HTTPException(e.status, str(e)) from e
