"""The AI layer's health, for admin and oversight: what the ai-worker last published (models, loaded model,
memory, circuits, provider health), the length of its queue, and the last day's runs by path."""
import json

import redis
from sqlalchemy.orm import Session

from app.ai import QUEUE, STATE_KEY
from app.core.config import get_settings
from app.modules.ai_health import repo


def health(session: Session) -> dict:
    settings = get_settings()
    state, depth = None, None
    try:
        client = redis.Redis.from_url(settings.redis_url, socket_timeout=2)
        raw, depth = client.get(STATE_KEY), client.llen(QUEUE)
        state = json.loads(raw) if raw else None
    except redis.RedisError:
        pass
    counts: dict[str, dict[str, int]] = {}
    for row in repo.counts_last_day(session):
        counts.setdefault(row["task"], {})[row["path"]] = row["runs"]
    tasks = []
    for task, names in settings.ai_routes.items():
        reported = {p["name"]: p for p in (state or {}).get("tasks", {}).get(task, [])}
        providers = [reported.get(name) or {"name": name, "path": ("primary", "fallback", "last_resort")[min(i, 2)]}
                     for i, name in enumerate(names)]
        tasks.append({"task": task, "providers": providers, "last_24h": counts.get(task, {})})
    return {"reporting": state is not None, "reported_at": state and state["at"], "queue_depth": depth,
            "memory": state and state["memory"], "models": (state or {}).get("models", {}), "tasks": tasks}
