"""Providers: the plug-ins the router tries in order. Each one answers health(), run(payload) and validate(output).

A1 ships only the stub pair below, so the whole routing mechanism (fallback, timeouts, validation, confidence,
circuits, provenance) can be exercised without a real model. Real providers (OCR, translation, matching) come in
later phases and must keep to the same rule: no network call outside the deployment; a model server, if any, lives
in the `ai` zone and is named in SETHU_AI_ENDPOINTS (production refuses any other address).
"""
import time
from dataclasses import dataclass
from pathlib import Path

from app.ai.memory import manager


@dataclass
class Result:
    output: dict
    confidence: float


class Provider:
    name = "provider"
    model: str | None = None        # the registry name of the model it loads, if any

    def health(self) -> bool:
        return True

    def run(self, payload: dict) -> Result:
        raise NotImplementedError

    def validate(self, output: dict) -> bool:
        return isinstance(output, dict)


class StubProvider(Provider):
    """Echoes `payload["text"]` with a fixed confidence. `behaviour` makes it misbehave on purpose, for tests and
    drills: "ok", "unhealthy", "error", "slow" (sleeps `delay` seconds), "invalid" (output fails validation)."""

    def __init__(self, name: str, confidence: float = 0.9, model: str | None = None, behaviour: str = "ok",
                 delay: float = 0.0):
        self.name, self.confidence, self.model, self.behaviour, self.delay = name, confidence, model, behaviour, delay

    def health(self) -> bool:
        return self.behaviour != "unhealthy"

    def run(self, payload: dict) -> Result:
        if self.model:   # exercises the registry and memory manager: the stub model is a small checked file
            manager().acquire(self.model, lambda path: Path(path).read_bytes())
        if self.behaviour == "error":
            raise RuntimeError("stub failure")
        if self.behaviour == "slow":
            time.sleep(self.delay)
        if self.behaviour == "invalid":
            return Result({"unexpected": True}, self.confidence)
        return Result({"text": str(payload.get("text", ""))}, self.confidence)

    def validate(self, output: dict) -> bool:
        return isinstance(output, dict) and isinstance(output.get("text"), str)


# The providers that SETHU_AI_ROUTES may name, each made fresh per call (they hold no state; circuits are kept by
# the router, by name).
PROVIDERS = {
    "stub-model": lambda: StubProvider("stub-model", confidence=0.9, model="stub-echo"),
    "stub-rules": lambda: StubProvider("stub-rules", confidence=0.7),
}
