from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.session import get_session
from app.modules.overlaps import schemas, service

router = APIRouter(prefix="/api/v1/overlaps", tags=["overlaps"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
DECIDE = require_roles("officer", "bureau_head")  # and the database checks the bureau is a party
DETECT = require_roles("admin")                   # needs to read every bureau's text; the worker also runs it


@router.get("", response_model=list[schemas.Link])
def list_links(
    status: Literal["proposed", "approved", "rejected"] | None = None,
    institution_id: UUID | None = None,
    principal: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> list[dict]:
    return service.links(session, principal, status, institution_id)


@router.get("/tier1", response_model=list[schemas.Tier1Institution])
def tier1(
    institution_id: UUID | None = None,
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> list[dict]:
    return service.tier1(session, institution_id)


@router.post("/detect", response_model=schemas.DetectOut)
def detect(principal: Principal = Depends(DETECT), session: Session = Depends(get_session)) -> dict:
    return service.detect(session, principal)


@router.post("/{link_id}/decision", response_model=schemas.Link)
def decide(
    link_id: UUID,
    body: schemas.DecisionIn,
    principal: Principal = Depends(DECIDE),
    session: Session = Depends(get_session),
) -> dict:
    try:
        return service.decide(session, principal, link_id, body.decision == "approve")
    except service.OverlapError as e:
        raise HTTPException(e.status, str(e)) from e
