from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.session import get_session
from app.modules.search import schemas, service

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("", response_model=schemas.Results,
            dependencies=[Depends(require_roles("officer", "bureau_head", "oversight", "admin", "auditor"))])
def search(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> dict:
    return service.search(session, q.strip(), limit)
