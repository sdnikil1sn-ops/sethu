from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.session import get_session
from app.modules.complaints import schemas, service
from app.modules.overlaps import service as overlaps

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
WRITE = require_roles("officer", "bureau_head", "admin")  # the database also refuses the others


def _run(work):
    try:
        return work()
    except service.CaseError as e:
        raise HTTPException(e.status, str(e)) from e


@router.get("", response_model=schemas.CasePage)
def list_cases(
    filters: Annotated[schemas.Filters, Query()],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> dict:
    wanted = filters.model_dump()
    if wanted.pop("overlapping"):
        wanted["ids"] = overlaps.linked_case_ids(session)
    return service.search(session, wanted, limit, offset)


@router.get("/options", response_model=schemas.Options)
def options(_: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    return service.options(session)


@router.get("/timeline", response_model=schemas.Timeline)
def institution_timeline(
    institution_id: UUID,
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> dict:
    return service.institution_timeline(session, institution_id)


@router.get("/{complaint_id}", response_model=schemas.Case)
def case(
    complaint_id: UUID,
    principal: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> dict:
    return _run(lambda: service.get(session, principal, complaint_id))


@router.get("/{complaint_id}/assignees", response_model=list[schemas.Assignee])
def assignees(
    complaint_id: UUID,
    _: Principal = Depends(WRITE),
    session: Session = Depends(get_session),
) -> list[dict]:
    return service.assignees(session, complaint_id)


@router.post("/{complaint_id}/actions", response_model=schemas.Case)
def act(
    complaint_id: UUID,
    body: schemas.ActionIn,
    principal: Principal = Depends(WRITE),
    session: Session = Depends(get_session),
) -> dict:
    return _run(lambda: service.act(session, principal, complaint_id, body.action, note=body.note,
                                    to_bureau=body.to_bureau, assignee_id=body.assignee_id))
