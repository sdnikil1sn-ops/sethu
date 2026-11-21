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


def queue(name: str) -> str:
    return _client().send_task(name).id


def status(task_id: str) -> dict:
    result = _client().AsyncResult(task_id)
    done = result.state == "SUCCESS" and isinstance(result.result, dict)
    return {"state": result.state, "suggested": result.result.get("suggested") if done else None}
