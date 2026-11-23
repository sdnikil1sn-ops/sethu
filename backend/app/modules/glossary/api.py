from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.session import get_session
from app.modules.glossary import schemas, service

router = APIRouter(tags=["glossary"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
ADMIN = require_roles("admin")


@router.get("/api/v1/glossary", response_model=schemas.GlossaryOut)
def glossary(_: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    return service.listing(session)


@router.post("/api/v1/admin/glossary", response_model=schemas.UploadOut, status_code=201)
def upload(data: bytes = Body(..., media_type="application/octet-stream"),
           filename: str = Query("glossary.csv", max_length=200),
           principal: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> dict:
    """The whole glossary as CSV or XLSX: a new version if every row passes; otherwise 422 with the error report
    (row, field, problem) and nothing stored."""
    try:
        return service.upload(session, principal, data, filename)
    except service.GlossaryError as e:
        raise HTTPException(e.status, {"message": str(e), "errors": e.errors} if e.errors else str(e)) from e
