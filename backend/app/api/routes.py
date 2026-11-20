"""Platform endpoints. Feature routers live in app/modules/<feature>/api.py
(the audit screen and "Verify chain" are in app/modules/audit_view)."""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, get_session, session_for
from app.modules.users import service as users

health = APIRouter(prefix="/health", tags=["health"])
api = APIRouter(prefix="/api/v1", tags=["platform"])


@health.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@health.get("/ready")
def ready(response: Response) -> dict[str, str]:
    try:
        with session_for(SYSTEM) as session:
            session.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "down"}
    return {"status": "ok", "database": "up"}


@api.get("/me")
def me(principal: Principal = Depends(get_principal), session: Session = Depends(get_session)) -> dict[str, str | None]:
    """Called by the web app on every sign-in: brings the person's record in step with the token."""
    users.sync(session, principal)
    return {
        "subject": principal.subject,
        "name": principal.name,
        "role": principal.role,
        "bureau_id": str(principal.bureau_id) if principal.bureau_id else None,
    }

