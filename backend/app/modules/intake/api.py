from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.session import get_session, session_for
from app.modules.intake import schemas, service

router = APIRouter(prefix="/api/v1/intake", tags=["intake"])

ENTER = require_roles("officer", "bureau_head")                       # their own bureau's sources only
HEALTH = require_roles("admin", "oversight", "auditor", "bureau_head")  # a bureau head sees their bureau's
ITEMS = require_roles("admin", "oversight", "auditor", "bureau_head", "officer")
ADMIN = require_roles("admin")


def _run(work):
    try:
        return work()
    except service.IntakeError as e:
        raise HTTPException(e.status, str(e)) from e


@router.post("/submissions", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.Accepted)
def submit(
    complaint: dict = Body(...),  # validated after the key: an unknown caller learns nothing about the fields
    x_sethu_key: str = Header(""),
    x_sethu_timestamp: str = Header(""),
    x_sethu_nonce: str = Header(""),
) -> dict:
    """For portal systems: no user token; the source's API key, a Unix timestamp and a one-time nonce."""
    with session_for(service.GATEWAY) as session:
        return _run(lambda: service.submit_api(session, x_sethu_key, x_sethu_timestamp, x_sethu_nonce, complaint))


@router.post("/manual", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.Accepted)
def manual(complaint: schemas.ComplaintIn, principal: Principal = Depends(ENTER),
           session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.manual(session, principal, complaint))


@router.post("/upload", response_model=schemas.UploadResult)
def upload(data: bytes = Body(..., media_type="application/octet-stream"),
           filename: str = Query("upload.csv", max_length=200),
           principal: Principal = Depends(ENTER), session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.upload(session, principal, data, filename))


@router.get("/sources", response_model=list[schemas.Source])
def sources(_: Principal = Depends(HEALTH), session: Session = Depends(get_session)) -> list[dict]:
    return service.list_sources(session)


@router.post("/sources", response_model=schemas.Source, status_code=status.HTTP_201_CREATED)
def create_source(body: schemas.SourceIn, principal: Principal = Depends(ADMIN),
                  session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.create_source(session, principal, body.name, body.channel, body.bureau,
                                              body.priority, body.fallback))


@router.patch("/sources/{source_id}", response_model=schemas.Source)
def update_source(source_id: UUID, body: schemas.SourcePatch, principal: Principal = Depends(ADMIN),
                  session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.update_source(session, principal, source_id, body.model_dump()))


@router.post("/sources/{source_id}/key", response_model=schemas.IssuedKey)
def issue_key(source_id: UUID, principal: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.issue_key(session, principal, source_id))


@router.get("/items", response_model=list[schemas.Item])
def items(status_: Literal["pending", "done", "duplicate", "dead"] | None = Query(None, alias="status"),
          review: bool = False, principal: Principal = Depends(ITEMS),
          session: Session = Depends(get_session)) -> list[dict]:
    return service.list_items(session, principal, status_, review)


@router.post("/items/{item_id}/retry", response_model=schemas.Item)
def retry(item_id: UUID, principal: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.retry(session, principal, item_id))


@router.post("/items/{item_id}/reviewed", response_model=schemas.Item)
def reviewed(item_id: UUID, principal: Principal = Depends(ENTER), session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.mark_reviewed(session, principal, item_id))
