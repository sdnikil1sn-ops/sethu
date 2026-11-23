"""run(task, payload): try the task's providers in order (primary, fallback, last resort) and keep the first answer
that is healthy, on time, valid and confident enough; if none is, the item goes to a person ("human_review").

A provider falls through when its circuit is open, health() is false, run() raises or exceeds
`ai.<task>.timeout_seconds` (default `ai_timeout_seconds`), validate() rejects the output, or its confidence is
below `ai.<task>.min_confidence` (default `ai_default_min_confidence`); both settings live in sethu.app_settings.
`ai_circuit_failures` failures in a row open its circuit for `ai_circuit_cooldown_seconds`; then one trial call is
let through (half open). Low confidence is not a failure.

Every call writes one sethu.ai_runs row (provenance: task, subject, provider, model and version, path, confidence,
latency, status, the reasons earlier providers fell through) and an audit-ledger entry, in the caller's transaction.
Neither holds the payload or the output: identifiers and decisions only.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai.memory import manager
from app.ai.providers import Provider
from app.audit import service as audit
from app.core.auth import Principal
from app.core.config import get_settings

PATHS = ("primary", "fallback", "last_resort")
# shortcut: a provider that times out keeps its thread until it returns; fine for one-process stubs and local
# models, revisit (a process per provider) if a real provider can hang for good.
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ai-provider")


@dataclass
class _Circuit:
    failures: int = 0
    opened_at: float | None = None


# shortcut: circuits live in this process; the ai-worker runs one process (solo pool), so this is all of them.
_circuits: dict[str, _Circuit] = {}
_lock = threading.Lock()


def circuit_state(name: str, now: float | None = None) -> str:
    """"closed", "open" (cooling down) or "half_open" (the next call is a trial)."""
    with _lock:
        c = _circuits.get(name)
        if c is None or c.opened_at is None:
            return "closed"
        cooldown = get_settings().ai_circuit_cooldown_seconds
        return "open" if (now or time.monotonic()) - c.opened_at < cooldown else "half_open"


def _failed(name: str) -> None:
    with _lock:
        c = _circuits.setdefault(name, _Circuit())
        c.failures += 1
        if c.failures >= get_settings().ai_circuit_failures or c.opened_at is not None:
            c.opened_at = time.monotonic()      # (re)open; a failed half-open trial waits a full cooldown again


def _succeeded(name: str) -> None:
    with _lock:
        _circuits.pop(name, None)


def reset_circuits() -> None:
    with _lock:
        _circuits.clear()


def chain_for(task: str) -> list[Provider]:
    from app.ai.catalog import PROVIDERS  # noqa: I001 - here, not at the top: it imports every engine module
    names = get_settings().ai_routes.get(task)
    if not names:
        raise ValueError(f"no providers are configured for AI task {task}")
    return [PROVIDERS[n]() for n in names]


def setting(session: Session, key: str, default):
    """A value from sethu.app_settings (JSON), or the default."""
    value = session.execute(text("SELECT value FROM sethu.app_settings WHERE key = :k"), {"k": key}).scalar()
    return default if value is None else value


def min_confidence(session: Session, task: str) -> float:
    return float(setting(session, f"ai.{task}.min_confidence", get_settings().ai_default_min_confidence))


def run(session: Session, principal: Principal, task: str, payload: dict, *, subject_type: str | None = None,
        subject_id: str | None = None, chain: list[Provider] | None = None) -> dict:
    """The accepted answer, or status "human_review" when no provider gave one. Provenance and audit are written
    in `session`, so they commit (or roll back) with the caller's work."""
    chain = chain if chain is not None else chain_for(task)
    threshold = min_confidence(session, task)
    timeout = float(setting(session, f"ai.{task}.timeout_seconds", get_settings().ai_timeout_seconds))
    started, why = time.monotonic(), []
    for i, provider in enumerate(chain):
        path = PATHS[min(i, len(PATHS) - 1)]
        reason = _try(provider, payload, threshold, timeout)
        if isinstance(reason, str):
            why.append(f"{path} {provider.name}: {reason}")
            continue
        result = reason
        model = manager().report() if provider.model else None
        row = _record(session, principal, task, subject_type, subject_id, provider.name,
                      provider.model, model and model["version"], path, result.confidence, started, "ok", why)
        return {"run_id": row, "status": "ok", "path": path, "provider": provider.name,
                "confidence": result.confidence, "output": result.output}
    row = _record(session, principal, task, subject_type, subject_id, None, None, None, None, None, started,
                  "human_review", why)
    return {"run_id": row, "status": "human_review", "path": None, "provider": None, "confidence": None,
            "output": None}


def _try(provider: Provider, payload: dict, threshold: float, timeout: float):
    """The provider's Result if it is acceptable, otherwise a short reason (never payload or output text)."""
    if circuit_state(provider.name) == "open":
        return "circuit open"
    try:
        healthy = provider.health()
    except Exception:  # noqa: BLE001 - a health check that fails is an unhealthy provider
        healthy = False
    if not healthy:
        _failed(provider.name)
        return "unhealthy"
    future = _pool.submit(provider.run, payload)
    try:
        result = future.result(timeout=timeout)
    except FutureTimeout:
        _failed(provider.name)
        return f"timed out after {timeout:g} s"
    except Exception as e:  # noqa: BLE001 - any provider error falls through to the next provider
        _failed(provider.name)
        return f"error ({type(e).__name__})"
    if not provider.validate(result.output):
        _failed(provider.name)
        return "output failed validation"
    _succeeded(provider.name)
    if result.confidence < threshold:
        return f"confidence {result.confidence:.2f} below {threshold:.2f}"
    return result


def _record(session, principal, task, subject_type, subject_id, provider, model_name, model_version, path,
            confidence, started, status, why) -> str:
    latency = round((time.monotonic() - started) * 1000)
    run_id = str(session.execute(text("""
        INSERT INTO sethu.ai_runs (task, subject_type, subject_id, provider, model_name, model_version, path,
                                   confidence, latency_ms, status, error)
        VALUES (:task, :st, :sid, :provider, :mn, :mv, :path, :conf, :lat, :status, :error) RETURNING id"""),
        {"task": task, "st": subject_type, "sid": subject_id, "provider": provider, "mn": model_name,
         "mv": model_version, "path": path, "conf": confidence, "lat": latency, "status": status,
         "error": "; ".join(why)[:1000] or None}).scalar_one())
    audit.record(session, principal, "ai.run", entity_type="ai_runs", entity_id=run_id,
                 payload={"task": task, "subject_type": subject_type, "subject_id": subject_id, "provider": provider,
                          "model": model_name, "model_version": model_version, "path": path, "status": status,
                          "confidence": confidence, "fell_through": len(why)})
    return run_id
