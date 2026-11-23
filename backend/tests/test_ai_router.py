"""The AI router (AI Phase A1): ordered providers with fallback, timeouts, validation, confidence, circuit breaker,
human review when every provider fails, and provenance (sethu.ai_runs plus an audit entry) for every call."""
import json
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.ai import memory, router
from app.ai.providers import StubProvider
from app.audit.service import verify
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from tests.conftest import requires_db

pytestmark = requires_db
MODELS = Path(__file__).resolve().parents[2] / "models"
COMPLAINT_TEXT = "The hostel warden demanded a bribe for the refund"   # must never reach provenance or audit


@pytest.fixture(autouse=True)
def quick(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "ai_models_dir", str(MODELS))
    monkeypatch.setattr(s, "ai_timeout_seconds", 0.3)
    monkeypatch.setattr(s, "ai_circuit_failures", 3)
    monkeypatch.setattr(s, "ai_circuit_cooldown_seconds", 60)
    memory.manager.cache_clear()
    router.reset_circuits()
    yield
    router.reset_circuits()
    memory.manager.cache_clear()


def call(world, chain=None, task="stub.echo", **kw):
    with session_for(SYSTEM, world["engine"]) as s:
        return router.run(s, SYSTEM, task, {"text": COMPLAINT_TEXT}, chain=chain, subject_type="complaint",
                          subject_id=str(world["case"]["C-101"]), **kw)


def ai_run(world, run_id):
    with session_for(SYSTEM, world["engine"]) as s:
        row = s.execute(text("SELECT * FROM sethu.ai_runs WHERE id = :i"), {"i": run_id}).mappings().one()
        entry = s.execute(text("SELECT payload FROM sethu.audit_log WHERE action = 'ai.run' AND entity_id = :i"),
                          {"i": run_id}).scalar_one()
    return dict(row), entry


def ok(name, **kw):
    return StubProvider(name, **kw)


def test_primary_success_is_recorded_with_its_model_and_without_the_text(world):
    result = call(world)                                        # the configured chain: stub-model, then stub-rules
    assert result["status"] == "ok" and result["path"] == "primary" and result["provider"] == "stub-model"
    assert result["output"] == {"text": COMPLAINT_TEXT} and memory.manager().report()["loaded"] == "stub-echo"
    row, entry = ai_run(world, result["run_id"])
    assert (row["task"], row["path"], row["status"], row["model_name"], row["model_version"]) == \
        ("stub.echo", "primary", "ok", "stub-echo", "1")
    assert row["subject_type"] == "complaint" and float(row["confidence"]) == 0.9 and row["error"] is None
    assert entry["path"] == "primary" and entry["provider"] == "stub-model"
    assert COMPLAINT_TEXT not in json.dumps([row, entry], default=str)       # identifiers and decisions only
    with session_for(SYSTEM, world["engine"]) as s:
        assert verify(s).ok


def test_a_primary_timeout_falls_back(world):
    result = call(world, [ok("slow", behaviour="slow", delay=2), ok("rules", confidence=0.7)])
    assert result["path"] == "fallback" and result["provider"] == "rules"
    assert "primary slow: timed out after 0.3 s" in ai_run(world, result["run_id"])[0]["error"]


def test_output_that_fails_validation_falls_back(world):
    result = call(world, [ok("odd", behaviour="invalid"), ok("rules")])
    assert result["path"] == "fallback"
    assert "primary odd: output failed validation" in ai_run(world, result["run_id"])[0]["error"]


def test_low_confidence_falls_through_by_the_setting_in_app_settings(world):
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("UPDATE sethu.app_settings SET value = '0.8' WHERE key = 'ai.stub.echo.min_confidence'"))
    try:
        result = call(world, [ok("unsure", confidence=0.6), ok("sure", confidence=0.85)])
        assert result["path"] == "fallback" and result["confidence"] == 0.85
        assert "confidence 0.60 below 0.80" in ai_run(world, result["run_id"])[0]["error"]
        assert router.circuit_state("unsure") == "closed"               # low confidence is not a failure
    finally:
        with session_for(SYSTEM, world["engine"]) as s:
            s.execute(text("UPDATE sethu.app_settings SET value = '0.5' WHERE key = 'ai.stub.echo.min_confidence'"))


def test_an_open_circuit_is_skipped_until_its_cooldown_ends(world, monkeypatch):
    failing = ok("flaky", behaviour="error")
    for _ in range(3):                                                  # three failures in a row open it
        assert call(world, [failing, ok("rules")])["path"] == "fallback"
    assert router.circuit_state("flaky") == "open"
    result = call(world, [ok("flaky"), ok("rules")])                    # healthy again, but still cooling down
    assert result["provider"] == "rules"
    assert "primary flaky: circuit open" in ai_run(world, result["run_id"])[0]["error"]
    monkeypatch.setattr(get_settings(), "ai_circuit_cooldown_seconds", 0)
    assert router.circuit_state("flaky") == "half_open"
    assert call(world, [ok("flaky"), ok("rules")])["provider"] == "flaky"   # the trial call succeeds: closed
    assert router.circuit_state("flaky") == "closed"


def test_an_unhealthy_provider_is_passed_over(world):
    result = call(world, [ok("down", behaviour="unhealthy"), ok("rules")])
    assert result["path"] == "fallback" and "primary down: unhealthy" in ai_run(world, result["run_id"])[0]["error"]


def test_when_every_provider_fails_the_item_goes_to_a_person(world):
    result = call(world, [ok("a", behaviour="error"), ok("b", behaviour="invalid"), ok("c", confidence=0.1)])
    assert result == {"run_id": result["run_id"], "status": "human_review", "path": None, "provider": None,
                      "confidence": None, "output": None}
    row, entry = ai_run(world, result["run_id"])
    assert row["status"] == "human_review" and row["path"] is None and row["provider"] is None
    assert row["error"] == ("primary a: error (RuntimeError); fallback b: output failed validation; "
                            "last_resort c: confidence 0.10 below 0.50")
    assert entry["status"] == "human_review" and entry["fell_through"] == 3


def test_an_unknown_task_is_refused():
    with pytest.raises(ValueError, match="no providers"):
        router.chain_for("nope.task")


def test_ai_runs_are_append_only_and_scoped(world):
    run_id = call(world)["run_id"]
    with session_for(world["menon"], world["engine"]) as s:             # oversight sees every run
        assert s.execute(text("SELECT count(*) FROM sethu.ai_runs WHERE id = :i"), {"i": run_id}).scalar() == 1
    with session_for(world["iyer"], world["engine"]) as s:              # RB cannot read PGRC's C-101: hidden
        assert s.execute(text("SELECT count(*) FROM sethu.ai_runs WHERE id = :i"), {"i": run_id}).scalar() == 0
    with session_for(world["rao"], world["engine"]) as s:               # PGRC holds C-101: visible
        assert s.execute(text("SELECT count(*) FROM sethu.ai_runs WHERE id = :i"), {"i": run_id}).scalar() == 1
    with pytest.raises(DBAPIError), session_for(world["rao"], world["engine"]) as s:   # only the worker writes
        s.execute(text("INSERT INTO sethu.ai_runs (task, latency_ms, status) VALUES ('x.y', 1, 'human_review')"))
    for change in ("UPDATE sethu.ai_runs SET status = 'ok'", "DELETE FROM sethu.ai_runs"):
        with pytest.raises(DBAPIError), session_for(SYSTEM, world["engine"]) as s:     # nobody rewrites history
            s.execute(text(change))


def test_settings_are_read_by_all_and_written_by_admin_only(world):
    with session_for(world["rao"], world["engine"]) as s:
        assert s.execute(text("SELECT count(*) FROM sethu.app_settings")).scalar() >= 1
    with pytest.raises(DBAPIError), session_for(world["rao"], world["engine"]) as s:
        s.execute(text("INSERT INTO sethu.app_settings (key, value) VALUES ('ai.x.min_confidence', '0.1')"))
    with session_for(world["rao"], world["engine"]) as s:     # an officer's UPDATE matches no row it may change
        s.execute(text("UPDATE sethu.app_settings SET value = '0.01'"))
        assert s.execute(text("SELECT value FROM sethu.app_settings WHERE key = 'ai.stub.echo.min_confidence'"
                              )).scalar() == 0.5
