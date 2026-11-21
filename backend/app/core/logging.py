"""JSON logs on stdout, one object per line, each with a request id. Never log complaint text, complainant
details, tokens or passwords: log identifiers, counts and reasons.

The request id is the edge's X-Request-ID (nginx $request_id) when it is a plain hex or uuid string, else a new
one; in the worker it is the task id. Records from libraries (uvicorn, celery, httpx) go through the same
formatter. Database errors never carry statement parameters (the engine sets hide_parameters).
"""
import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

request_id: ContextVar[str] = ContextVar("request_id", default="-")
SAFE_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def accept_request_id(value: str | None, fallback: str) -> str:
    """The id from the edge if it is safe to log as is, else the fallback."""
    return value if value and SAFE_ID.match(value) else fallback


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rid = request_id.get()
        task = getattr(record, "data", None)  # celery's "task received" line: the id before the task starts
        if rid == "-" and isinstance(task, dict) and isinstance(task.get("id"), str):
            rid = task["id"]
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": rid,  # "-" only on lines outside any request or task (start-up, the scheduler)
        }
        # Structured fields passed with extra={...}: identifiers and counts only, by convention. Anything that is
        # not a plain value (a library's dict of task arguments, say) is left out rather than printed.
        for key, value in record.__dict__.items():
            plain = isinstance(value, str | int | float | bool | None)
            if plain and key not in _STANDARD and not key.startswith("_") and key not in entry:
                entry[key] = value
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


_STANDARD = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime", "color_message"}


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "celery", "celery.task", "celery.worker"):
        lg = logging.getLogger(name)
        lg.handlers[:] = []
        lg.propagate = True
    logging.getLogger("uvicorn.access").disabled = True  # the app logs each request itself, with its id
    logging.getLogger("httpx").setLevel(logging.WARNING)
