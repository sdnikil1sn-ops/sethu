"""GET /api/v1/ai/health (AI Phase A1): admin and oversight only; the ai-worker's published state, its queue depth,
and the last day's runs by path."""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai import memory, router
from app.ai.providers import StubProvider
from app.core.auth import Principal, get_principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.main import app
from tests.conftest import requires_db

pytestmark = requires_db
MODELS = Path(__file__).resolve().parents[2] / "models"
REDIS = os.environ.get("SETHU_TEST_REDIS_URL")
ADMIN = Principal("u-admin-ai", "admin", "admin", None)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(get_settings(), "ai_models_dir", str(MODELS))
    memory.manager.cache_clear()
    router.reset_circuits()
    yield TestClient(app)
    app.dependency_overrides.clear()
    router.reset_circuits()


def as_(who):
    app.dependency_overrides[get_principal] = lambda: who


def test_only_admin_and_oversight_see_it(world, client):
    for who, allowed in ((ADMIN, True), (world["menon"], True), (world["rao"], False), (world["iyer"], False),
                         (world["das"], False)):
        as_(who)
        assert (client.get("/api/v1/ai/health").status_code == 200) is allowed, who


def test_counts_by_path_and_a_silent_worker(world, client, monkeypatch):
    monkeypatch.setattr(get_settings(), "redis_url", "redis://127.0.0.1:1/0")   # nobody there: not reporting
    with session_for(SYSTEM, world["engine"]) as s:
        router.run(s, SYSTEM, "stub.echo", {"text": "x"})
        router.run(s, SYSTEM, "stub.echo", {"text": "x"}, chain=[StubProvider("a", behaviour="error"),
                                                                  StubProvider("b")])
        router.run(s, SYSTEM, "stub.echo", {"text": "x"}, chain=[StubProvider("a", behaviour="error")])
    as_(ADMIN)
    body = client.get("/api/v1/ai/health").json()
    assert body["reporting"] is False and body["queue_depth"] is None
    task = next(t for t in body["tasks"] if t["task"] == "stub.echo")
    assert task["last_24h"] == {"primary": 1, "fallback": 1, "human_review": 1}
    assert [(p["name"], p["path"], p["healthy"]) for p in task["providers"]] == \
        [("stub-model", "primary", None), ("stub-rules", "fallback", None)]


@pytest.mark.skipif(not REDIS, reason="needs SETHU_TEST_REDIS_URL")
def test_what_the_worker_publishes_is_shown(world, client, monkeypatch):
    monkeypatch.setattr(get_settings(), "redis_url", REDIS)
    from app.ai import tasks  # the ai-worker's module: imports the AI layer only, connects nowhere at import
    monkeypatch.setattr(tasks, "settings", get_settings())
    memory.manager().acquire("stub-echo", lambda path: b"")
    tasks.publish()
    as_(world["menon"])
    body = client.get("/api/v1/ai/health").json()
    assert body["reporting"] is True and body["queue_depth"] == 0
    assert body["models"] == {"stub-echo": "ok"} and body["memory"]["loaded"] == "stub-echo"
    providers = next(t for t in body["tasks"] if t["task"] == "stub.echo")["providers"]
    assert [(p["name"], p["healthy"], p["circuit"], p["model"]) for p in providers] == \
        [("stub-model", True, "closed", "stub-echo"), ("stub-rules", True, "closed", None)]
