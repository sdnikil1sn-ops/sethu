"""Queue a worker job from the API and read its state, without importing the worker (or its model).

The API only sends the task name to the broker; the worker runs it. Results are kept by the Celery result
backend (Redis) for a day. Only counts come back, never content.
"""
from functools import lru_cache

from celery import Celery

from app.core.config import get_settings


@lru_cache
def _client() -> Celery:
    url = get_settings().redis_url
    return Celery("sethu", broker=url, backend=url)


def queue(name: str, kwargs: dict | None = None, on: str | None = None) -> str:
    """`on`: the Celery queue (the ai-worker's is "ai"); identifiers only in `kwargs`, never content."""
    return _client().send_task(name, kwargs=kwargs or {}, queue=on).id


def status(task_id: str) -> dict:
    result = _client().AsyncResult(task_id)
    done = result.state == "SUCCESS" and isinstance(result.result, dict)
    answer = result.result if done else {}
    return {"state": result.state, "suggested": answer.get("suggested"), "skipped": bool(answer.get("skipped"))}
