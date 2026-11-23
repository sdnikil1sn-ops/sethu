from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.paging import page_params
from app.db.session import get_session
from app.modules.complaints import schemas, service
from app.modules.overlaps import service as overlaps

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
WRITE = require_roles("officer", "bureau_head", "admin")  # the database also refuses the others
MINE = require_roles("officer", "bureau_head")
WORKLOAD = require_roles("bureau_head", "oversight", "admin")
ADMIN = require_roles("admin")

deadlines_router = APIRouter(prefix="/api/v1/admin/deadlines", tags=["admin"])


def _run(work):
    try:
        return work()
    except service.CaseError as e:
        raise HTTPException(e.status, str(e)) from e


@router.get("", response_model=schemas.CasePage)
def list_cases(
    filters: Annotated[schemas.Filters, Query()],
    paged: tuple[int, int] = Depends(page_params),
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> dict:
    wanted = filters.model_dump()
    if wanted.pop("overlapping"):
        wanted["ids"] = overlaps.linked_case_ids(session)
    return service.search(session, wanted, *paged)


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


@router.get("/mine", response_model=list[schemas.CaseRow])
def my_cases(principal: Principal = Depends(MINE), session: Session = Depends(get_session)) -> list[dict]:
    """Open cases assigned to the caller in their bureau, soonest deadline first."""
    return service.my_cases(session, principal)


@router.get("/workload", response_model=list[schemas.WorkloadRow])
def workload(_: Principal = Depends(WORKLOAD), session: Session = Depends(get_session)) -> list[dict]:
    """Open and overdue cases per person and unassigned; a bureau head sees their bureau (Row-Level Security)."""
    return service.workload(session)


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
                                    to_bureau=body.to_bureau, assignee_id=body.assignee_id, reason=body.reason))


@deadlines_router.get("", response_model=list[schemas.Deadline])
def deadlines(_: Principal = Depends(READ), session: Session = Depends(get_session)) -> list[dict]:
    return service.deadlines(session)


@deadlines_router.put("/{category}", response_model=list[schemas.Deadline])
def set_deadline(category: str, body: schemas.DeadlineIn, principal: Principal = Depends(ADMIN),
                 session: Session = Depends(get_session)) -> list[dict]:
    if not 1 <= len(category) <= 100:
        raise HTTPException(422, "category must be 1 to 100 characters")
    return service.set_deadline(session, principal, category, body.days)
