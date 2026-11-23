from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.core.params import Blank
from app.db.session import get_session
from app.modules.enrichment import schemas, service

router = APIRouter(tags=["enrichment"])

ATTACH = require_roles("officer", "bureau_head")                  # and the database checks the bureau holds the case
OPEN = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")   # and it can read the case's text
REVIEW = require_roles("officer", "bureau_head", "oversight", "admin")
RESOLVE = require_roles("officer", "bureau_head", "admin")


def _run(work):
    try:
        return work()
    except service.EnrichmentError as e:
        raise HTTPException(e.status, str(e)) from e


@router.post("/api/v1/cases/{complaint_id}/attachments", response_model=schemas.AttachmentOut, status_code=201)
def attach(complaint_id: UUID, data: bytes = Body(..., media_type="application/octet-stream"),
           filename: str = Query("attachment", max_length=200), principal: Principal = Depends(ATTACH),
           session: Session = Depends(get_session)) -> dict:
    """A PDF, PNG or JPEG (up to 10 MB) for the case; read by the AI pipeline in the background."""
    return _run(lambda: service.add_attachment(session, principal, complaint_id, data, filename))


@router.get("/api/v1/cases/{complaint_id}/attachments/{attachment_id}")
def download(complaint_id: UUID, attachment_id: UUID, principal: Principal = Depends(OPEN),
             session: Session = Depends(get_session)) -> Response:
    found = _run(lambda: service.open_attachment(session, principal, complaint_id, attachment_id))
    return Response(found["data"], media_type=found["content_type"], headers={
        "Content-Disposition": f'attachment; filename="{found["filename"]}"',   # safe characters only (service)
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/api/v1/review-items", response_model=list[schemas.ReviewItem])
def review_items(status: Annotated[Literal["open", "resolved", "dismissed"] | None, Blank] = "open",
                 _: Principal = Depends(REVIEW), session: Session = Depends(get_session)) -> list[dict]:
    return service.review_items(session, status)


class Decision(BaseModel):
    status: Literal["resolved", "dismissed"]


@router.post("/api/v1/review-items/{item_id}/decision", response_model=schemas.ReviewDone)
def decide(item_id: UUID, body: Decision, principal: Principal = Depends(RESOLVE),
           session: Session = Depends(get_session)) -> dict:
    return _run(lambda: service.resolve(session, principal, item_id, body.status))
