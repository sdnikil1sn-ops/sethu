"""The scheduler (Celery beat) cannot run twice: it holds a Redis lock. Needs a throwaway Redis:
    docker run -d --rm --name sethu-test-redis -p 127.0.0.1:6390:6379 redis:7-alpine
    SETHU_TEST_REDIS_URL=redis://127.0.0.1:6390/0
"""
import os
from types import SimpleNamespace

import pytest
import redis

from app import worker

URL = os.environ.get("SETHU_TEST_REDIS_URL")
pytestmark = pytest.mark.skipif(not URL, reason="needs SETHU_TEST_REDIS_URL (a throwaway Redis)")


@pytest.fixture
def scheduler(monkeypatch, tmp_path):
    monkeypatch.setattr(worker, "settings", SimpleNamespace(redis_url=URL))
    client = redis.Redis.from_url(URL)
    client.delete(worker.BEAT_LOCK)
    made = []

    def start(name="a"):
        s = worker.SingleScheduler(app=worker.celery, schedule_filename=str(tmp_path / name))
        made.append(s)
        return s

    yield start, client
    for s in made:
        s.close()
    client.delete(worker.BEAT_LOCK)


def test_a_second_scheduler_refuses_to_start(scheduler):
    start, client = scheduler
    first = start("a")
    with pytest.raises(SystemExit, match="another scheduler holds"):
        start("b")
    assert 0 < client.ttl(worker.BEAT_LOCK) <= worker.BEAT_LOCK_SECONDS
    assert first.tick() <= worker.BEAT_LOCK_SECONDS / 3  # wakes often enough to renew the lock


def test_the_lock_passes_on_when_the_scheduler_stops_or_dies(scheduler):
    start, client = scheduler
    start("a").close()          # a clean stop releases it
    start("b")
    client.delete(worker.BEAT_LOCK)  # as if b died and its lock expired
    start("c")


def test_a_scheduler_that_lost_its_lock_stops(scheduler):
    start, client = scheduler
    first = start("a")
    client.set(worker.BEAT_LOCK, "someone else")
    with pytest.raises(SystemExit, match="lost"):
        first.tick()
