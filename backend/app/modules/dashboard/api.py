from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.session import get_session
from app.modules.dashboard import schemas, service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("", response_model=schemas.Overview,
            dependencies=[Depends(require_roles("officer", "bureau_head", "oversight", "admin", "auditor"))])
def overview(session: Session = Depends(get_session)) -> dict:
    return service.overview(session)
