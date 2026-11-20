from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.session import get_session
from app.modules.bureaus import schemas, service

router = APIRouter(prefix="/api/v1/admin/bureaus", tags=["admin"])

ADMIN = require_roles("admin")  # and the database allows only admin and system to write bureaus


def _run(work):
    try:
        return work()
    except service.BureauError as e:
        raise HTTPException(e.status, str(e)) from e


@router.get("", response_model=list[schemas.BureauRow])
def list_bureaus(_: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> list[dict]:
    return service.listing(session)


@router.post("", response_model=schemas.Bureau, status_code=status.HTTP_201_CREATED)
def create_bureau(body: schemas.BureauIn, principal: Principal = Depends(ADMIN),
                  session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.create(session, principal, body.code, body.name))


@router.patch("/{bureau_id}", response_model=schemas.Bureau)
def update_bureau(bureau_id: UUID, body: schemas.BureauChange, principal: Principal = Depends(ADMIN),
                  session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.update(session, principal, bureau_id, body.name, body.active))
