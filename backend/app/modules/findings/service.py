"""Deadlock, bottleneck and early-warning detection, and the trend indicator. Fully deterministic: rules on
case actions and summary counts, no AI model and no complaint text.

Deadlock (one case):
  transfer_loop     the case's latest actions are two or more transfers in a row, none acknowledged
                    and nothing else done in between, and the case came back to a bureau it had left
                    (C-090: PGRC to RB to PGRC).
  stalled_transfer  the latest action is a transfer nobody has acknowledged for `stalled_transfer_days`.
Bottleneck (a bureau's or an institution's open cases), with at least `bottleneck_min_open` open:
  overdue_share     more than `bottleneck_share` of them are past their 21-day deadline.
  older_than_median (bureaus only) more than `bottleneck_share` of them are older than the bureau's median
                    days to close. Not for institutions: a handful of cases makes it fire too easily.
Deadline (one case):
  deadline_escalation  an open case past its deadline (the category's days, set by an admin); for the head of
                    the bureau holding it. Resolved when the case is closed.
Early warning (one state and category):
  category_spike    complaints in the last 30 days reach `spike_min_count` and are at least `spike_ratio`
                    times the baseline: the same cell's previous 90 days, scaled to 30. A comparison with
                    past counts, not a forecast. No alert: the finding is shown on screen only.

A finding's key names it, so a second run adds nothing. A finding that no longer holds is marked
resolved; if it comes back it is reopened with the numbers and bureaus of that day. Deadlock
findings also put an alert in the outbox in pending_approval: nothing is sent until a bureau head
or oversight approves it.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.core.config import get_settings
from app.modules.complaints import service as complaints
from app.modules.findings import repo
from app.modules.users import service as users

TREND_DAYS = 30
SPIKE_RECENT_DAYS, SPIKE_BASELINE_DAYS = 30, 90


class FindingError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def transfer_finding(history: list[dict], now: datetime, stall_days: int) -> dict | None:
    """Look at one case's actions, oldest first. Returns a loop or stall, or None."""
    run: list[dict] = []
    for a in history:
        # An acknowledgement, or any other action, means someone picked the case up.
        run = run + [a] if a["action"] == "transferred" and a["acknowledged_at"] is None else []
    if not run:
        return None
    visited = [run[0]["from_bureau_id"]] + [a["to_bureau_id"] for a in run]
    if len(run) >= 2 and len(set(visited)) < len(visited):
        kind = "transfer_loop"
    elif now - run[-1]["created_at"] >= timedelta(days=stall_days):
        kind = "stalled_transfer"
    else:
        return None
    last = run[-1]
    return {
        "kind": kind, "key": f"{kind}:{last['complaint_id']}:{last['id']}", "complaint_id": last["complaint_id"],
        "institution_id": last["institution_id"], "ref": last["ref"],
        "bureau_ids": list(dict.fromkeys(b for b in visited if b)), "path": [b for b in visited if b],
        "evidence": {"action_ids": [str(a["id"]) for a in run], "transfers": len(run),
                     "days_unacknowledged": (now - last["created_at"]).days},
    }


def queue_findings(scope: str, rows: list[dict], min_open: int, share: float) -> list[dict]:
    """Bottlenecks in bureau or institution queues, with the numbers used."""
    found = []
    for r in rows:
        measures = [("overdue_share", r["overdue"])]
        if scope == "bureau":
            measures.insert(0, ("older_than_median", r["older_than_median"]))
        for measure, count in measures:
            if r["open"] >= min_open and count / r["open"] > share:
                found.append({
                    "kind": "bottleneck", "key": f"bottleneck:{scope}:{r['id']}:{measure}",
                    "institution_id": r["id"] if scope == "institution" else None, "bureau_ids": r["bureau_ids"],
                    "evidence": {"scope": scope, "measure": measure, "open": r["open"], "overdue": r["overdue"],
                                 "older_than_median": r["older_than_median"],
                                 "median_days_to_close": float(r["median_days"]) if r["median_days"] else None,
                                 "share": round(count / r["open"], 2), "threshold": share, "min_open": min_open},
                })
    return found


def spike_findings(rows: list[dict], min_count: int, ratio: float, as_of: str) -> list[dict]:
    """Regional category spikes, with the counts, baseline and thresholds used."""
    found = []
    for r in rows:
        baseline = r["previous"] * SPIKE_RECENT_DAYS / SPIKE_BASELINE_DAYS
        if r["recent"] < min_count or (baseline and r["recent"] < ratio * baseline):
            continue  # too few to mean anything, or not far enough above its own past
        found.append({
            "kind": "category_spike", "key": f"category_spike:{r['state']}:{r['category']}",
            "institution_id": None, "bureau_ids": r["bureau_ids"],
            "evidence": {"state": r["state"], "category": r["category"], "recent": r["recent"],
                         "previous": r["previous"], "baseline": round(baseline, 2),
                         "ratio": round(r["recent"] / baseline, 2) if baseline else None,  # None: nothing before
                         "recent_days": SPIKE_RECENT_DAYS, "baseline_days": SPIKE_BASELINE_DAYS,
                         "min_count": min_count, "ratio_threshold": ratio, "as_of": as_of},
        })
    return found


def deadline_findings(rows: list[dict], now: datetime) -> list[dict]:
    """One escalation per open case past its deadline. The key names the deadline, so a reopened case with a
    new deadline that passes again is a new finding; closing the case resolves it."""
    return [{
        "kind": "deadline_escalation", "key": f"deadline_escalation:{r['id']}:{r['due_at']:%Y-%m-%d}",
        "complaint_id": r["id"], "institution_id": r["institution_id"], "ref": r["ref"], "bureau_ids": [r["bureau_id"]],
        "evidence": {"ref": r["ref"], "category": r["category"], "due_at": r["due_at"].isoformat(),
                     "days_overdue_when_found": (now - r["due_at"]).days},
    } for r in rows]


def _alert(session: Session, f: dict, codes: dict[UUID, str]) -> UUID:
    if f["kind"] == "deadline_escalation":
        subject = f"Deadline passed on case {f['ref']}"
        body = (f"{subject}\n\nCase {f['ref']} ({codes[f['bureau_ids'][0]]}) was due on {f['evidence']['due_at'][:10]} "
                f"and is still open ({f['evidence']['days_overdue_when_found']} day(s) late when found).\n\n"
                "Open SETHU to see who holds it and decide what happens next.")
        recipients, missing = users.recipients(session, f["bureau_ids"])  # the holding bureau's heads
        return repo.insert_alert(session, f["complaint_id"], recipients, missing, subject, body, kind="sla")
    bureaus = " to ".join(codes[b] for b in f["path"])  # the route taken: PGRC to RB to PGRC
    what = "transfer loop" if f["kind"] == "transfer_loop" else "transfer not acknowledged"
    subject = f"Bottleneck detected: {what} on case {f['ref']}"
    # References and counts only. Complaint text never goes into an alert.
    body = (f"{subject}\n\nCase {f['ref']} has moved {bureaus} with no acknowledgement for "
            f"{f['evidence']['days_unacknowledged']} days ({f['evidence']['transfers']} transfer(s) in a row).\n\n"
            "Open SETHU to see the case history and agree which bureau will act on it.")
    recipients, missing = users.recipients(session, f["bureau_ids"])
    return repo.insert_alert(session, f["complaint_id"], recipients, missing, subject, body)


def detect(session: Session, principal: Principal) -> dict[str, int]:
    """Run every detector. Safe to repeat: known findings are left alone. Needs a principal who
    sees every bureau (the worker's system principal, or an admin)."""
    settings = get_settings()
    now = datetime.now(UTC)
    by_case: dict[UUID, list[dict]] = {}
    for a in repo.transfer_histories(session):
        by_case.setdefault(a["complaint_id"], []).append(a)
    current = [f for h in by_case.values() if (f := transfer_finding(h, now, settings.stalled_transfer_days))]
    for scope, rows in (("bureau", repo.bureau_queues(session)), ("institution", repo.institution_queues(session))):
        current += queue_findings(scope, rows, settings.bottleneck_min_open, settings.bottleneck_share)
    current += spike_findings(repo.category_cells(session, SPIKE_RECENT_DAYS, SPIKE_BASELINE_DAYS),
                              settings.spike_min_count, settings.spike_ratio, now.date().isoformat())
    current += deadline_findings(repo.overdue_cases(session), now)

    known = {r["key"]: r for r in repo.existing(session)}
    codes = repo.bureau_codes(session)
    counts = {"created": 0, "reopened": 0, "resolved": 0}
    for f in current:
        if f["key"] not in known:
            # A stuck or late case gets an alert (held for approval); bottlenecks and spikes are on screen only.
            alerted = ("transfer_loop", "stalled_transfer", "deadline_escalation")
            alert_id = _alert(session, f, codes) if f["kind"] in alerted else None
            finding_id = repo.insert(session, f, alert_id)
            audit.record(session, principal, "finding.created", entity_type="findings", entity_id=str(finding_id),
                         payload={"kind": f["kind"], "complaint_id": f.get("complaint_id") and str(f["complaint_id"]),
                                  "institution_id": f["institution_id"] and str(f["institution_id"]),
                                  "bureaus": sorted(codes[b] for b in f["bureau_ids"]), "evidence": f["evidence"],
                                  "alert_id": alert_id and str(alert_id)})
            counts["created"] += 1
        elif known[f["key"]]["status"] == "resolved":
            # It holds again, maybe with other numbers (a spike months later): show those, not the old ones.
            finding_id = known[f["key"]]["id"]
            repo.reopen(session, finding_id, f["evidence"], f["bureau_ids"])
            audit.record(session, principal, "finding.reopened", entity_type="findings", entity_id=str(finding_id),
                         payload={"status": "open", "bureaus": sorted(codes[b] for b in f["bureau_ids"]),
                                  "evidence": f["evidence"]})
            counts["reopened"] += 1
    still = {f["key"] for f in current}
    for key, row in known.items():
        if row["status"] == "open" and key not in still:
            _set(session, principal, row["id"], "resolved", "finding.resolved", None)
            counts["resolved"] += 1
    return counts


def _set(session: Session, principal: Principal, finding_id: UUID, status: str, action: str,
         actor_id: UUID | None) -> bool:
    if not repo.set_status(session, finding_id, status, actor_id):
        return False
    audit.record(session, principal, action, entity_type="findings", entity_id=str(finding_id),
                 payload={"status": status})
    return True


def listing(session: Session, filters: dict) -> list[dict]:
    return repo.listing(session, {k: v for k, v in filters.items() if v is not None})


def decide(session: Session, principal: Principal, finding_id: UUID, status: str) -> dict:
    """A person dismisses a finding (not a real problem, or handled outside SETHU) or reopens it."""
    found = repo.listing(session, {"id": finding_id})
    if not found:  # Row-Level Security hides findings that do not involve the caller's bureau
        raise FindingError(404, "finding not found")
    if found[0]["status"] == status:
        raise FindingError(409, f"this finding is already {status}")
    action = "finding.dismissed" if status == "dismissed" else "finding.reopened"
    if not _set(session, principal, finding_id, status, action, complaints.actor_id(session, principal)):
        raise FindingError(403, "only a head of a bureau this finding involves, or oversight, can change it")
    return repo.listing(session, {"id": finding_id})[0]


def open_count(session: Session) -> int:
    """Open findings the caller may see. For the dashboard."""
    return repo.open_count(session)


def trend(session: Session) -> dict:
    """Trend indicator (not the early warning): counts only, no prediction."""
    return {"days": TREND_DAYS, "items": repo.trend(session, TREND_DAYS)}
