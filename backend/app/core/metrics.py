"""Prometheus metrics, text format, no extra dependency.

Request counts and latency are kept in this process (one backend process per container; add a scrape per
container if there are more). Queue depths, failures and job times are read from the database at scrape time
as the system principal: counts and timestamps only, never content. Served on /metrics at the backend's own
port, which only the internal network reaches; nginx never proxies it, and a request that came through a
proxy (it carries X-Forwarded-For) is refused.
"""
import threading
from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.orm import Session

BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
_lock = threading.Lock()
_requests: dict[tuple[str, str, str], int] = defaultdict(int)
_latency: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0.0] * (len(BUCKETS) + 2))  # buckets, sum, n


def observe_request(method: str, route: str, status: int, seconds: float) -> None:
    with _lock:
        _requests[(method, route, f"{status // 100}xx")] += 1
        row = _latency[(method, route)]
        for i, edge in enumerate(BUCKETS):
            if seconds <= edge:
                row[i] += 1
        row[-2] += seconds
        row[-1] += 1


def _label(**labels: str) -> str:
    return "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + "}"


def _process_lines() -> list[str]:
    out = ["# HELP sethu_http_requests_total HTTP requests handled, by route template and status class.",
           "# TYPE sethu_http_requests_total counter"]
    with _lock:
        out += [f"sethu_http_requests_total{_label(method=m, route=r, status=s)} {n}"
                for (m, r, s), n in sorted(_requests.items())]
        out += ["# HELP sethu_http_request_duration_seconds Request latency.",
                "# TYPE sethu_http_request_duration_seconds histogram"]
        for (m, r), row in sorted(_latency.items()):
            name = "sethu_http_request_duration_seconds_bucket"
            for i, edge in enumerate(BUCKETS):
                out.append(f"{name}{_label(method=m, route=r, le=str(edge))} {int(row[i])}")
            out.append(f"{name}{_label(method=m, route=r, le='+Inf')} {int(row[-1])}")
            out.append(f"sethu_http_request_duration_seconds_sum{_label(method=m, route=r)} {row[-2]:.6f}")
            out.append(f"sethu_http_request_duration_seconds_count{_label(method=m, route=r)} {int(row[-1])}")
    return out


GAUGES = """
SELECT (SELECT count(*) FROM sethu.intake_items WHERE status = 'pending') AS intake_pending,
       (SELECT count(*) FROM sethu.intake_items WHERE status = 'dead') AS intake_dead,
       (SELECT coalesce(sum(failures), 0) FROM sethu.intake_sources) AS intake_failures_in_a_row,
       (SELECT count(*) FROM sethu.intake_sources WHERE marked_down AND active) AS intake_sources_down,
       (SELECT count(*) FROM sethu.alerts WHERE status = 'pending_approval') AS alerts_pending_approval,
       (SELECT count(*) FROM sethu.alerts WHERE status = 'approved') AS alerts_queued,
       (SELECT count(*) FROM sethu.alerts WHERE status = 'failed') AS alerts_failed,
       (SELECT count(*) FROM sethu.findings WHERE status = 'open') AS findings_open"""

HELP = {
    "intake_pending": "Intake items waiting to be processed (held or retrying included).",
    "intake_dead": "Intake items dead-lettered, waiting for an admin Retry.",
    "intake_failures_in_a_row": "Sum over sources of consecutive failed intake attempts.",
    "intake_sources_down": "Active intake sources marked down.",
    "alerts_pending_approval": "Alerts waiting for a person's approval.",
    "alerts_queued": "Approved alerts not yet sent.",
    "alerts_failed": "Alerts that gave up after the maximum attempts.",
    "findings_open": "Open findings.",
}


def render(session: Session) -> str:
    out = _process_lines()
    values = session.execute(text(GAUGES)).mappings().one()
    for name, value in values.items():
        out += [f"# HELP sethu_{name} {HELP[name]}", f"# TYPE sethu_{name} gauge", f"sethu_{name} {value}"]
    out += ["# HELP sethu_job_last_run_timestamp_seconds When each scheduled job last ran (Unix time).",
            "# TYPE sethu_job_last_run_timestamp_seconds gauge",
            "# HELP sethu_job_last_success_timestamp_seconds When each scheduled job last succeeded (Unix time).",
            "# TYPE sethu_job_last_success_timestamp_seconds gauge",
            "# HELP sethu_job_failures_total Failed runs of each scheduled job.",
            "# TYPE sethu_job_failures_total counter"]
    for r in session.execute(text("""SELECT name, extract(epoch FROM last_run_at) AS run,
                                            extract(epoch FROM last_ok_at) AS ok, failures
                                       FROM sethu.job_runs ORDER BY name""")).mappings():
        out.append(f"sethu_job_last_run_timestamp_seconds{_label(job=r['name'])} {float(r['run']):.0f}")
        if r["ok"] is not None:
            out.append(f"sethu_job_last_success_timestamp_seconds{_label(job=r['name'])} {float(r['ok']):.0f}")
        out.append(f"sethu_job_failures_total{_label(job=r['name'])} {r['failures']}")
    return "\n".join(out) + "\n"


def record_run(session: Session, name: str, ok: bool) -> None:
    """A scheduled job finished (ok or not). Called by the worker in its own transaction."""
    session.execute(text("""
        INSERT INTO sethu.job_runs (name, last_run_at, last_ok_at, last_ok, failures)
        VALUES (:n, now(), CASE WHEN :ok THEN now() END, :ok, CASE WHEN :ok THEN 0 ELSE 1 END)
        ON CONFLICT (name) DO UPDATE SET last_run_at = now(), last_ok = :ok, runs = sethu.job_runs.runs + 1,
            last_ok_at = CASE WHEN :ok THEN now() ELSE sethu.job_runs.last_ok_at END,
            failures = sethu.job_runs.failures + CASE WHEN :ok THEN 0 ELSE 1 END"""), {"n": name, "ok": ok})
