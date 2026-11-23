from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.session import get_session
from app.modules.ai_health import schemas, service

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

READ = require_roles("admin", "oversight")


@router.get("/health", response_model=schemas.AiHealth)
def health(_: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    return service.health(session)
