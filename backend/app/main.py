"""Application factory."""
import logging
import time
import uuid

from fastapi import FastAPI, Request

from app.api.routes import api, health, internal
from app.core import metrics
from app.core.config import get_settings
from app.core.logging import accept_request_id, configure_logging, request_id
from app.modules.ai_health.api import router as ai_health
from app.modules.alerts.api import router as alerts
from app.modules.audit_view.api import router as audit_view
from app.modules.bureaus.api import router as bureaus
from app.modules.complaints.api import deadlines_router
from app.modules.complaints.api import router as cases
from app.modules.dashboard.api import router as dashboard
from app.modules.enrichment.api import router as enrichment
from app.modules.findings.api import router as findings
from app.modules.glossary.api import router as glossary
from app.modules.graph.api import router as graph
from app.modules.institutions.api import router as institutions
from app.modules.intake.api import router as intake
from app.modules.overlaps.api import router as overlaps
from app.modules.reports.api import router as reports
from app.modules.search.api import router as search
from app.modules.semantic.api import router as semantic
from app.modules.users.api import router as users

log = logging.getLogger("sethu.http")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    app = FastAPI(
        title="SETHU API",
        version="0.1.0",
        debug=settings.debug,  # dev only: Settings refuses SETHU_DEBUG in production
        # Internal network only: not under /api, so the edge never serves them (docs/API.md).
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = accept_request_id(request.headers.get("x-request-id"), uuid.uuid4().hex)
        token = request_id.set(rid)
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = rid
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Cache-Control"] = "no-store"
            return response
        finally:
            route = request.scope.get("route")
            path = getattr(route, "path", "unmatched")  # the route template: no ids or query values
            elapsed = time.perf_counter() - start
            metrics.observe_request(request.method, path, status, elapsed)
            log.info("%s %s -> %s", request.method, path, status,
                     extra={"status": status, "duration_ms": round(elapsed * 1000, 1)})
            request_id.reset(token)

    app.include_router(health)
    app.include_router(internal)
    app.include_router(api)
    app.include_router(institutions)
    app.include_router(cases)
    app.include_router(overlaps)
    app.include_router(alerts)
    app.include_router(dashboard)
    app.include_router(audit_view)
    app.include_router(search)
    app.include_router(reports)
    app.include_router(findings)
    app.include_router(bureaus)
    app.include_router(users)
    app.include_router(intake)
    app.include_router(deadlines_router)
    app.include_router(graph)
    app.include_router(ai_health)
    app.include_router(enrichment)
    app.include_router(glossary)
    app.include_router(semantic)
    return app


app = create_app()
