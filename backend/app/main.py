"""Application factory."""
import logging
import uuid

from fastapi import FastAPI, Request

from app.api.routes import api, health
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id
from app.modules.alerts.api import router as alerts
from app.modules.complaints.api import router as cases
from app.modules.institutions.api import router as institutions
from app.modules.overlaps.api import router as overlaps

log = logging.getLogger("sethu.http")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    interactive_docs = settings.environment != "prod"
    app = FastAPI(
        title="SETHU API",
        version="0.1.0",
        docs_url="/api/docs" if interactive_docs else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if interactive_docs else None,
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = uuid.uuid4().hex
        token = request_id.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id.reset(token)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        log.info("%s %s -> %s", request.method, request.url.path, response.status_code)
        return response

    app.include_router(health)
    app.include_router(api)
    app.include_router(institutions)
    app.include_router(cases)
    app.include_router(overlaps)
    app.include_router(alerts)
    return app


app = create_app()
