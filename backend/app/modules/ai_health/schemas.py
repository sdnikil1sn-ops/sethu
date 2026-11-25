from pydantic import BaseModel


class ProviderHealth(BaseModel):
    name: str
    path: str                    # primary, fallback or last_resort
    model: str | None = None
    healthy: bool | None = None  # None: the ai-worker is not reporting
    circuit: str | None = None   # closed, open or half_open


class TaskHealth(BaseModel):
    task: str
    providers: list[ProviderHealth]
    last_24h: dict[str, int]     # runs by path, and "human_review"
    last_run: dict | None = None  # A4: the latest run: when, path, provider (the method in use)


class Memory(BaseModel):
    loaded: str | None = None
    version: str | None = None
    approx_memory_mb: int = 0
    process_rss_mb: float | None = None


class AiHealth(BaseModel):
    reporting: bool              # the ai-worker published its state in the last two minutes
    reported_at: float | None = None
    queue_depth: int | None = None
    memory: Memory | None = None
    models: dict[str, str]       # model name: "ok" or why it is refused
    tasks: list[TaskHealth]
    classifier: dict | None = None        # the active category classifier and its held-out accuracy (A3)
    classifier_versions: int = 0
    embeddings: dict | None = None        # vectors per model and version, and the active one (A3)
    graph: dict | None = None             # the latest relationship-graph build (A4)
