from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.core.params import Blank, Text20
from app.db.session import get_session
from app.modules.findings import schemas, service

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
DECIDE = require_roles("bureau_head", "oversight")  # and the database checks the bureau is involved
DETECT = require_roles("admin")                    # reads every bureau's queue; the worker also runs it


@router.get("", response_model=list[schemas.Finding])
def list_findings(
    kind: Annotated[Literal["transfer_loop", "stalled_transfer", "bottleneck", "category_spike"] | None, Blank] = None,
    status: Annotated[Literal["open", "resolved", "dismissed"] | None, Blank] = None,
    bureau: Text20 = None,
    institution_id: Annotated[UUID | None, Blank] = None,
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> list[dict]:
    return service.listing(session, {"kind": kind, "status": status, "bureau": bureau,
                                     "institution_id": institution_id})


@router.get("/trend", response_model=schemas.Trend)
def trend(_: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    return service.trend(session)


@router.post("/detect", response_model=schemas.DetectOut)
def detect(principal: Principal = Depends(DETECT), session: Session = Depends(get_session)) -> dict:
    return service.detect(session, principal)


@router.post("/{finding_id}/decision", response_model=schemas.Finding)
def decide(
    finding_id: UUID,
    body: schemas.DecisionIn,
    principal: Principal = Depends(DECIDE),
    session: Session = Depends(get_session),
) -> dict:
    try:
        return service.decide(session, principal, finding_id, body.status)
    except service.FindingError as e:
        raise HTTPException(e.status, str(e)) from e
