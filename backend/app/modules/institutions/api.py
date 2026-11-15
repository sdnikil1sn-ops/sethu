from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.session import get_session
from app.modules.institutions import schemas, service

router = APIRouter(prefix="/api/v1/institutions", tags=["institutions"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
WRITE = require_roles("officer", "bureau_head", "admin")


@router.get("", response_model=list[schemas.InstitutionRow])
def list_institutions(
    q: str | None = Query(None, max_length=200, description="Name, alias or acronym"),
    state: str | None = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> list[dict]:
    return service.list_institutions(session, q, state, limit, offset)


@router.get("/resolution/queue", response_model=list[schemas.QueueItem])
def resolution_queue(
    limit: int = Query(50, ge=1, le=200),
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> list[dict]:
    return service.queue(session, limit)


@router.post("/resolution/run", response_model=schemas.RunOut)
def run_resolution(
    principal: Principal = Depends(WRITE),
    session: Session = Depends(get_session),
) -> dict:
    return service.resolve_pending(session, principal)


@router.post("/resolution/{complaint_id}", response_model=schemas.ResolveOut)
def resolve(
    complaint_id: UUID,
    body: schemas.ResolveIn,
    principal: Principal = Depends(WRITE),
    session: Session = Depends(get_session),
) -> dict:
    result = service.resolve_by_officer(session, principal, complaint_id, body.institution_id)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such unresolved complaint or institution")
    return result


@router.get("/{institution_id}", response_model=schemas.Profile)
def institution_profile(
    institution_id: UUID,
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> dict:
    result = service.profile(session, institution_id)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "institution not found")
    return result
