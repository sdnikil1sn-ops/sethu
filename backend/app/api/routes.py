"""Platform endpoints. Feature routers live in app/modules/<feature>/api.py
(the audit screen and "Verify chain" are in app/modules/audit_view)."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import metrics as prometheus
from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, get_session, session_for
from app.modules.users import service as users

health = APIRouter(prefix="/health", tags=["health"])
internal = APIRouter(tags=["internal"])
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


@internal.get("/metrics", include_in_schema=False)
def metrics(request: Request) -> Response:
    """Prometheus, for a scraper on the internal network. Never through the edge: nginx does not proxy it, and a
    request that came through a proxy (X-Forwarded-For) is answered as if the path did not exist."""
    if request.headers.get("x-forwarded-for") or request.headers.get("x-real-ip"):
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    with session_for(SYSTEM) as session:
        body = prometheus.render(session)
    return Response(body, media_type="text/plain; version=0.0.4; charset=utf-8")


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

