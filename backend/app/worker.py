"""Background jobs (Celery). Workers act as the `system` principal."""
import logging

import redis
from celery import Celery
from celery.beat import PersistentScheduler
from celery.schedules import crontab
from celery.signals import setup_logging, task_postrun, task_prerun
from sqlalchemy import text

from app.audit import anchor
from app.audit import service as audit
from app.core import metrics
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id
from app.db.session import SYSTEM, session_for
from app.modules.alerts import service as alerts
from app.modules.complaints import service as complaints
from app.modules.enrichment import service as enrichment
from app.modules.findings import service as findings
from app.modules.institutions import service as institutions
from app.modules.intake import service as intake
from app.modules.overlaps import service as overlaps

log = logging.getLogger("sethu.worker")
settings = get_settings()


@setup_logging.connect
def _json_logs(**_kwargs) -> None:
    """Celery's own log setup is replaced: the same JSON lines as the API, each with the task id."""
    configure_logging()


_task_ids: dict[str, object] = {}


@task_prerun.connect
def _task_started(task_id: str | None = None, **_kwargs) -> None:
    if task_id:
        _task_ids[task_id] = request_id.set(task_id)


@task_postrun.connect
def _task_finished(task_id: str | None = None, task=None, state: str | None = None, **_kwargs) -> None:
    """Record the run (sethu.job_runs) for /metrics: when each job last ran and last succeeded."""
    try:
        with session_for(SYSTEM) as session:
            metrics.record_run(session, task.name.removeprefix("sethu."), state == "SUCCESS")
    except Exception:  # noqa: BLE001 - a metrics write never fails the job
        log.warning("could not record the job run", extra={"job": getattr(task, "name", "?")})
    finally:
        token = _task_ids.pop(task_id or "", None)
        if token is not None:
            request_id.reset(token)

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
        "audit-anchor-hourly": {"task": "sethu.audit.export_anchor", "schedule": crontab(minute=7)},
        "resolve-institutions": {"task": "sethu.institutions.resolve_pending", "schedule": 300.0},
        "detect-overlaps": {"task": "sethu.overlaps.detect", "schedule": 300.0},
        "detect-findings": {"task": "sethu.findings.detect", "schedule": 300.0},
        # The AI pipeline: run by the ai-worker (its own queue), never by this worker.
        "ai-enrich": {"task": "sethu.ai.enrich_pending", "schedule": 10.0, "options": {"queue": "ai"}},
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
    """Embed new complaints (if the semantic signal is on), then suggest new Tier 2 overlap links. A person
    approves or rejects each one."""
    with session_for(SYSTEM) as session:
        if not _only_run(session, "sethu.overlaps.detect"):
            return {"suggested": 0, "embedded": 0, "skipped": 1}
        embedded = overlaps.embed_pending(session)
    total = 0
    while True:  # batch by batch, each its own transaction (the audit chain's lock is held until commit)
        with session_for(SYSTEM) as session:
            if not _only_run(session, "sethu.overlaps.detect"):
                break
            done = overlaps.detect(session, SYSTEM)["suggested"]
        total += done
        if done < settings.detect_batch:
            break
    return {"suggested": total, "embedded": embedded}


def _only_run(session, job: str) -> bool:
    """Held to the end of the transaction: a second run of the same job (the schedule and the admin's button)
    skips instead of repeating the work and deadlocking on the same rows."""
    return session.execute(text("SELECT pg_try_advisory_xact_lock(hashtext(:j))"), {"j": job}).scalar_one()


@celery.task(name="sethu.findings.detect")
def detect_findings() -> dict:
    """Transfer loops, stalled transfers and queue bottlenecks. Repeatable: known findings are left alone."""
    total: dict[str, int] = {}
    while True:  # batch by batch, each its own transaction, so other writers wait seconds, not minutes
        with session_for(SYSTEM) as session:
            done = findings.detect(session, SYSTEM)
        total = {k: total.get(k, 0) + v for k, v in done.items()}
        if done["created"] < settings.detect_batch:
            return total


@celery.task(name="sethu.complainant.rotate_keys")
def rotate_complainant_keys() -> dict:
    """After a new key is made active: re-encrypt every complainant detail onto it, batch by batch."""
    total = 0
    while True:
        with session_for(SYSTEM) as session:
            done = complaints.rotate_complainant_keys(session, SYSTEM)
        total += done["rekeyed"]
        if not done["left"]:
            break
    files = 0
    while True:   # attachments are sealed with the same keyring
        with session_for(SYSTEM) as session:
            done = enrichment.rekey_attachments(session, SYSTEM)
        files += done["rekeyed"]
        if not done["left"]:
            return {"rekeyed": total, "attachments_rekeyed": files}


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


@celery.task(name="sethu.audit.export_anchor")
def export_anchor() -> dict:
    """Append the chain head to the write-once anchor file (proof outside the database)."""
    with session_for(SYSTEM) as session:
        result = anchor.export(session)
    if not result["exported"] and get_settings().audit_anchor_dir:
        raise RuntimeError(result["reason"])  # recorded as a failed run in job_runs (and /metrics)
    return {k: v for k, v in result.items() if k != "hash"}
