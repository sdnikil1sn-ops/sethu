"""The ai-worker: a Celery worker on its own queue (`ai`), one process (`--pool solo`), in the `ai` network zone.

    celery -A app.ai.tasks:celery worker -Q ai --pool solo -n ai@%h

It imports only the AI layer, the database session and the audit ledger, so it stays small while idle. At start it
checks every model in the manifest against its checksum (and logs the result); every 30 seconds it unloads a model
idle for too long and publishes its state (models, loaded model, memory, circuits, provider health) to Redis for
GET /api/v1/ai/health.
"""
import json
import logging
import threading
import time

import redis
from celery import Celery
from celery.signals import setup_logging, worker_ready

from app.ai import QUEUE, STATE_KEY, registry, router
from app.ai.memory import manager
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SYSTEM, session_for

STATE_TTL = 120          # the health screen says "not reporting" when the state is older than this
TICK = 30

log = logging.getLogger("sethu.ai")
settings = get_settings()
celery = Celery("sethu-ai", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(task_default_queue=QUEUE, task_serializer="json", accept_content=["json"],
                   result_serializer="json", result_expires=3600, worker_hijack_root_logger=False,
                   broker_connection_retry_on_startup=True)


@setup_logging.connect
def _json_logs(**_kwargs) -> None:
    configure_logging()


@celery.task(name="sethu.ai.run")
def run_task(task: str, payload: dict, subject_type: str | None = None, subject_id: str | None = None) -> dict:
    """Route one item. The answer is returned to the caller; provenance and audit are committed here."""
    with session_for(SYSTEM) as session:
        result = router.run(session, SYSTEM, task, payload, subject_type=subject_type, subject_id=subject_id)
    publish()
    return result


def state() -> dict:
    """What the health screen shows about this worker (no payloads, no model contents)."""
    tasks = {}
    for task in settings.ai_routes:
        providers = []
        for i, provider in enumerate(router.chain_for(task)):
            try:
                healthy = bool(provider.health())
            except Exception:  # noqa: BLE001 - reported, not raised
                healthy = False
            providers.append({"name": provider.name, "path": router.PATHS[min(i, 2)], "model": provider.model,
                              "healthy": healthy, "circuit": router.circuit_state(provider.name)})
        tasks[task] = providers
    return {"at": time.time(), "models": registry.check_all(settings.ai_models_dir), "memory": manager().report(),
            "tasks": tasks}


def publish() -> None:
    try:
        redis.Redis.from_url(settings.redis_url).set(STATE_KEY, json.dumps(state()), ex=STATE_TTL)
    except redis.RedisError:
        log.warning("could not publish the AI state")


def _tick() -> None:
    while True:
        time.sleep(TICK)
        if manager().unload_if_idle():
            log.info("model unloaded after being idle")
        publish()


@worker_ready.connect
def _started(**_kwargs) -> None:
    for name, verdict in registry.check_all(settings.ai_models_dir).items():
        (log.info if verdict == "ok" else log.error)("model check", extra={"model": name, "result": verdict})
    publish()
    threading.Thread(target=_tick, name="ai-idle", daemon=True).start()
