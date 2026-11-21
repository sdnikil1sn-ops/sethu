"""Background jobs (Celery). Workers act as the `system` principal."""
import logging

import redis
from celery import Celery
from celery.beat import PersistentScheduler
from celery.schedules import crontab

from app.audit import service as audit
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.modules.alerts import service as alerts
from app.modules.complaints import service as complaints
from app.modules.findings import service as findings
from app.modules.institutions import service as institutions
from app.modules.intake import service as intake
from app.modules.overlaps import service as overlaps

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
        "detect-overlaps": {"task": "sethu.overlaps.detect", "schedule": 300.0},
        "detect-findings": {"task": "sethu.findings.detect", "schedule": 300.0},
        "deliver-alerts": {"task": "sethu.alerts.deliver", "schedule": 15.0},
        "intake-process": {"task": "sethu.intake.process", "schedule": 10.0},
        "intake-spool": {"task": "sethu.intake.spool", "schedule": 30.0},
    },
)

BEAT_LOCK = "sethu:beat:lock"
BEAT_LOCK_SECONDS = 60


class SingleScheduler(PersistentScheduler):
    """Celery beat that runs only while it holds a Redis lock, so a second scheduler (a scaled
    service, a stray `celery beat`) cannot fire every job twice. It refuses to start while another
    holds the lock, renews the lock on every tick, and stops if it ever loses it. A scheduler that
    dies without releasing it is replaced after BEAT_LOCK_SECONDS."""

    def setup_schedule(self):
        self.lock = redis.Redis.from_url(settings.redis_url).lock(
            BEAT_LOCK, timeout=BEAT_LOCK_SECONDS, thread_local=False)
        if not self.lock.acquire(blocking=False):
            raise SystemExit(f"another scheduler holds {BEAT_LOCK}: not starting a second one")
        log.info("scheduler lock %s acquired", BEAT_LOCK)
        super().setup_schedule()

    def tick(self, *args, **kwargs):
        try:
            self.lock.reacquire()  # atomic: renews only if the lock is still ours
        except redis.exceptions.LockError:
            raise SystemExit(f"scheduler lost {BEAT_LOCK}: stopping") from None
        return min(super().tick(*args, **kwargs), BEAT_LOCK_SECONDS / 3)

    def close(self):
        super().close()
        try:
            self.lock.release()
        except redis.exceptions.LockError:  # expired or taken over: nothing to release
            pass


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


@celery.task(name="sethu.overlaps.detect")
def detect_overlaps() -> dict:
    """Suggest new Tier 2 overlap links. A person approves or rejects each one."""
    with session_for(SYSTEM) as session:
        return overlaps.detect(session, SYSTEM)


@celery.task(name="sethu.findings.detect")
def detect_findings() -> dict:
    """Transfer loops, stalled transfers and queue bottlenecks. Repeatable: known findings are left alone."""
    with session_for(SYSTEM) as session:
        return findings.detect(session, SYSTEM)


@celery.task(name="sethu.complainant.rotate_keys")
def rotate_complainant_keys() -> dict:
    """After a new key is made active: re-encrypt every complainant detail onto it, batch by batch."""
    total = 0
    while True:
        with session_for(SYSTEM) as session:
            done = complaints.rotate_complainant_keys(session, SYSTEM)
        total += done["rekeyed"]
        if not done["left"]:
            return {"rekeyed": total}


@celery.task(name="sethu.alerts.deliver")
def deliver_alerts() -> dict:
    """Email approved alerts through the SMTP relay; failures stay approved and are retried."""
    return alerts.deliver()


@celery.task(name="sethu.intake.process")
def process_intake() -> dict:
    """Turn queued intake items into complaints; failures wait and are retried, then dead-lettered."""
    return intake.process_due()


@celery.task(name="sethu.intake.spool")
def take_spool() -> dict:
    """The fallback channel: queue the rows of files dropped into the spool folder."""
    return intake.spool()
