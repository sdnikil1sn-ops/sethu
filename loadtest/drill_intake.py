"""Failure drill: keep submitting through the intake API while something is restarted, then prove that every
submission answered 202 was kept and processed. Mock data only; dev and test stacks only.

    docker compose run --rm --no-deps -v "$PWD/loadtest:/loadtest:ro" backend
        python /loadtest/drill_intake.py [seconds] [per_second]

Run it in a backend container on the stack (it issues a fresh key for the `pgrc-portal` source, audited, and calls
the running backend). Restart the service under test from another terminal while it runs. docs/LOAD-AND-DRILLS.md.
"""
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.modules.intake import service

URL = os.environ.get("SETHU_DRILL_API", "http://backend:8000") + "/api/v1/intake/submissions"
if not URL.startswith("http"):
    raise SystemExit("SETHU_DRILL_API must be an http(s) address")


def submit(key: str, ref: str) -> str:
    body = json.dumps({"institution_name": "Greenfield Institute of Technology", "category": "Fee refund",
                       "body": f"Drill submission {ref}: the hostel deposit was not refunded after repeated requests.",
                       "external_ref": ref}).encode()
    request = urllib.request.Request(URL, data=body, method="POST", headers={  # noqa: S310
        "Content-Type": "application/json", "X-Sethu-Key": key, "X-Sethu-Timestamp": str(int(time.time())),
        "X-Sethu-Nonce": secrets.token_urlsafe(18)})
    try:
        with urllib.request.urlopen(request, timeout=30) as r:  # noqa: S310 - http(s) only, checked above
            return str(r.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except OSError as e:
        return type(e).__name__


def main(seconds: int = 90, per_second: int = 5) -> dict:
    if get_settings().environment == "prod":
        raise SystemExit("refusing: dev and test stacks only")
    run = secrets.token_hex(3)
    with session_for(SYSTEM) as s:
        source = s.execute(text("SELECT id FROM sethu.intake_sources WHERE name = 'pgrc-portal'")).scalar_one()
        service.update_source(s, SYSTEM, source, {"rate_per_minute": 10000, "active": True, "marked_down": False})
        key = service.issue_key(s, SYSTEM, source)["api_key"]
    outcome: dict[str, str] = {}
    with ThreadPoolExecutor(8) as pool:
        start, n = time.monotonic(), 0
        while time.monotonic() - start < seconds:
            for _ in range(per_second):
                ref = f"drill-{run}-{n}"
                outcome[ref] = pool.submit(submit, key, ref)
                n += 1
            time.sleep(1)
    outcome = {ref: f.result() for ref, f in outcome.items()}
    accepted = {ref for ref, status in outcome.items() if status == "202"}
    deadline = time.monotonic() + 300                      # let the worker catch up
    while True:
        with session_for(SYSTEM) as s:
            rows = dict(s.execute(text("SELECT external_ref, status FROM sethu.intake_items"
                                       " WHERE external_ref LIKE :p"), {"p": f"drill-{run}-%"}).all())
        if all(rows.get(r) in ("done", "duplicate", "dead") for r in accepted) or time.monotonic() > deadline:
            break
        time.sleep(5)
    report = {"run": run, "sent": len(outcome), "answers": dict(Counter(outcome.values())),
              "accepted": len(accepted), "kept": len(accepted & rows.keys()),
              "lost": sorted(accepted - rows.keys())[:20], "item_states": dict(Counter(rows.values())),
              "kept_without_202": len(rows.keys() - accepted)}
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    main(*[int(a) for a in sys.argv[1:3]])
