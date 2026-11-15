"""Background jobs (Celery). Workers act as the `system` principal."""
import logging

from celery import Celery
from celery.schedules import crontab

from app.audit import service as audit
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.modules.institutions import service as institutions

log = logging.getLogger("sethu.worker")
settings = get_settings()

celery = Celery("sethu", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    beat_schedule={
        "audit-chain-nightly": {"task": "sethu.audit.verify_chain", "schedule": crontab(hour=2, minute=0)},
        "resolve-institutions": {"task": "sethu.institutions.resolve_pending", "schedule": 300.0},
    },
)


@celery.task(name="sethu.audit.verify_chain")
def verify_chain() -> dict:
    with session_for(SYSTEM) as session:
        result = audit.verify(session)
        audit.record(session, SYSTEM, "audit.verify", payload={"ok": result.ok, "checked": result.checked})
    if not result.ok:
        log.error("AUDIT CHAIN BROKEN at seq %s: %s", result.broken_seq, result.reason)
    return {"ok": result.ok, "checked": result.checked, "broken_seq": result.broken_seq}


@celery.task(name="sethu.institutions.resolve_pending")
def resolve_pending() -> dict:
    """Link newly arrived complaints to institutions; what cannot be linked waits in the officer queue."""
    with session_for(SYSTEM) as session:
        return institutions.resolve_pending(session, SYSTEM)
