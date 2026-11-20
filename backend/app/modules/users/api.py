from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.db.session import get_session
from app.modules.users import schemas, service

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin"])

ADMIN = require_roles("admin")


@router.get("", response_model=list[schemas.Person])
def list_people(_: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> list[dict]:
    """Everyone SETHU knows, people without an e-mail address first."""
    return service.listing(session)
