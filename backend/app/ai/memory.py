"""One heavy model in memory at a time, loaded when first needed and unloaded after `ai_idle_unload_seconds` unused.

The ai-worker has one process and one slot: asking for a different model unloads the current one first, so the
container's memory stays near the largest single model (its `approx_memory_mb`) plus the worker itself.
"""
import gc
import threading
import time
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.ai import registry
from app.core.config import get_settings


class ModelManager:
    def __init__(self, models_dir: str | Path, idle_seconds: float, clock: Callable[[], float] = time.monotonic):
        self.models_dir, self.idle_seconds, self.clock = models_dir, idle_seconds, clock
        self._lock = threading.RLock()
        self._name: str | None = None
        self._model: Any = None
        self._entry: registry.ModelEntry | None = None
        self._last_used = 0.0

    def acquire(self, name: str, loader: Callable[[Path], Any]) -> tuple[Any, registry.ModelEntry]:
        """The named model, loading it (after its checksum is verified) if it is not the one in memory."""
        with self._lock:
            if self._name != name:
                entry = registry.load_manifest(self.models_dir).get(name)
                if entry is None:
                    raise registry.ModelIntegrityError(f"model {name} is not in the manifest")
                path = registry.verify(entry, self.models_dir)   # refuses a changed or missing model
                self.unload()
                self._model, self._name, self._entry = loader(path), name, entry
            self._last_used = self.clock()
            return self._model, self._entry

    def unload(self) -> None:
        with self._lock:
            self._model = self._name = self._entry = None
            gc.collect()

    def unload_if_idle(self) -> bool:
        with self._lock:
            if self._name and self.clock() - self._last_used >= self.idle_seconds:
                self.unload()
                return True
            return False

    def report(self) -> dict:
        with self._lock:
            entry = self._entry
            return {"loaded": self._name, "version": entry.version if entry else None,
                    "approx_memory_mb": entry.approx_memory_mb if entry else 0, "process_rss_mb": rss_mb()}


def rss_mb() -> float | None:
    """This process's resident memory (Linux; None elsewhere)."""
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    return None


@lru_cache
def manager() -> ModelManager:
    s = get_settings()
    return ModelManager(s.ai_models_dir, s.ai_idle_unload_seconds)
