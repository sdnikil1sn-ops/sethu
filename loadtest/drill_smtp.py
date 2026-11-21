"""Failure drill: the mail relay is down while approved alerts wait to be sent. Mock data only; dev and test only.

    docker compose run --rm --no-deps -v "$PWD/loadtest:/loadtest:ro" backend python /loadtest/drill_smtp.py [minutes]

Approves up to three alerts held for approval, as the demo RB bureau head would on the Alerts screen (audited),
then reports every 30 seconds how many are approved (waiting or retrying), sent or failed, until all are sent or
failed or `minutes` pass. Stop the relay before and start it again during the run. docs/LOAD-AND-DRILLS.md.
"""
import json
import sys
import time
from collections import Counter
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import text

from app.core.auth import Principal
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.modules.alerts import service as alerts


def main(minutes: int = 30) -> None:
    if get_settings().environment == "prod":
        raise SystemExit("refusing: dev and test stacks only")
    subject = str(uuid5(NAMESPACE_URL, "sethu:user:iyer"))   # the demo RB head (seed/load.py user_id)
    with session_for(SYSTEM) as s:
        bureau = s.execute(text("SELECT bureau_id FROM sethu.app_users WHERE subject = :s"),
                           {"s": subject}).scalar_one()
    iyer = Principal(subject, "iyer", "bureau_head", bureau)
    with session_for(iyer) as s:
        waiting = [a["id"] for a in alerts.listing(s, iyer, status="pending_approval")][:3]
        for alert_id in waiting:
            alerts.decide(s, iyer, alert_id, approve=True)
    print(json.dumps({"approved": len(waiting)}), flush=True)
    end = time.monotonic() + minutes * 60
    while True:
        with session_for(SYSTEM) as s:
            rows = s.execute(text("SELECT status, attempts FROM sethu.alerts WHERE id = ANY(:ids)"),
                             {"ids": waiting}).all()
        states = Counter(r.status for r in rows)
        print(json.dumps({"at": time.strftime("%H:%M:%S"), "states": states,
                          "attempts": sorted(r.attempts for r in rows)}), flush=True)
        if not states.get("approved") or time.monotonic() > end:
            return
        time.sleep(30)


if __name__ == "__main__":
    main(*[int(a) for a in sys.argv[1:2]])
