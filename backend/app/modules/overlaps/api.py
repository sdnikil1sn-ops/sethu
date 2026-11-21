from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core import jobs
from app.core.auth import Principal, require_roles
from app.core.params import Blank, Text20
from app.db.session import get_session
from app.modules.overlaps import schemas, service

router = APIRouter(prefix="/api/v1/overlaps", tags=["overlaps"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
DECIDE = require_roles("officer", "bureau_head")  # and the database checks the bureau is a party
DETECT = require_roles("admin")                   # needs to read every bureau's text; the worker also runs it


@router.get("", response_model=list[schemas.Link])
def list_links(
    status: Annotated[Literal["proposed", "approved", "rejected"] | None, Blank] = None,
    institution_id: Annotated[UUID | None, Blank] = None,
    bureau: Text20 = None,
    tier: Annotated[Annotated[int, Field(ge=1, le=3)] | None, Blank] = None,
    principal: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> list[dict]:
    return service.links(session, principal, status, institution_id, bureau, tier)


@router.get("/tier1", response_model=list[schemas.Tier1Institution])
def tier1(
    institution_id: UUID | None = None,
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> list[dict]:
    return service.tier1(session, institution_id)


@router.post("/detect", response_model=schemas.DetectQueued, status_code=202)
def detect(principal: Principal = Depends(DETECT), session: Session = Depends(get_session)) -> dict:
    """Queue the worker's job (embed new complaints, then suggest): the model never runs in this process."""
    task_id = jobs.queue("sethu.overlaps.detect")
    audit.record(session, principal, "overlap.detect_requested", entity_type="jobs", entity_id=task_id,
                 payload={"job": "overlaps.detect"})
    return {"task_id": task_id}


@router.get("/detect/{task_id}", response_model=schemas.DetectStatus)
def detect_status(task_id: UUID, _: Principal = Depends(DETECT)) -> dict:
    return jobs.status(str(task_id))


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
