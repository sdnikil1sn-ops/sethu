from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.core.params import Day
from app.db.session import get_session
from app.modules.reports import schemas, service

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# Bureau staff see their own bureau only: the queries read the scope from the database session.
READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
Name = Literal["institutions", "bureaus", "overlaps"]


def _check(date_from: date | None, date_to: date | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "the start date is after the end date")


@router.get("/{name}", response_model=schemas.Report)
def report(name: Name, date_from: Day = None, date_to: Day = None,
           principal: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    _check(date_from, date_to)
    return service.run(session, principal, name, date_from, date_to)


@router.get("/{name}/export", response_class=Response)
def export(name: Name, date_from: Day = None, date_to: Day = None,
           principal: Principal = Depends(READ), session: Session = Depends(get_session)) -> Response:
    _check(date_from, date_to)
    body = service.export(session, principal, name, date_from, date_to)
    span = f"{date_from or 'start'}_to_{date_to or 'today'}"
    return Response(body, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="sethu-{name}-{span}.csv"'})
