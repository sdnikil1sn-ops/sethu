"""National early warning (docs/AI-PIPELINE.md, "A4"): "Emerging signal: requires verification".

`detect` (worker, every 5 minutes) runs AI task warning.detect through the router: DBSCAN over place and time,
else a weekly Z-score, else the baseline ratio (app/ai/warning.py). A detection that matches a signal already
known (same category group, a state in common, overlapping windows) updates it: the id stays the same across runs
and nothing is duplicated; a dismissed signal stays dismissed. A new signal puts one alert per bureau involved in
the outbox, held for a person's approval (kind early_warning), with counts and states only.

People: oversight and the heads of the bureaus involved acknowledge, dismiss (with a reason) or mark a signal
actioned; each decision is audited and written to the append-only feedback table. Officers see the signals of
their bureau. Member cases are listed by reference and summary; a case the viewer may not read carries the
restricted marker instead of a link.
"""
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import router
from app.ai import suggestions as feedback
from app.ai.warning import LABEL, state_key
from app.audit import service as audit
from app.core.auth import Principal
from app.modules.findings import service as findings
from app.modules.graph.service import RESTRICTED
from app.modules.signals import repo
from app.modules.users import service as users

DECISIONS = {"acknowledged": "acknowledged", "dismissed": "dismissed", "actioned": "actioned"}


class SignalError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def warning_settings(session: Session) -> dict:
    def get(key: str, default):
        return type(default)(router.setting(session, f"ai.warning.{key}", default))
    return {"recent_days": get("recent_days", 30), "baseline_days": get("baseline_days", 90),
            "km_per_unit": get("km_per_unit", 500.0), "days_per_unit": get("days_per_unit", 10.0),
            "eps": get("eps", 1.0), "min_samples": get("min_samples", 6), "min_members": get("min_members", 8),
            "max_points": get("max_points", 30000), "max_baseline_share": get("max_baseline_share", 0.5),
            "z_threshold": get("z_threshold", 3.0), "z_min_count": get("z_min_count", 5),
            "z_sd_floor": get("z_sd_floor", 1.0), "ratio_min_count": get("ratio_min_count", 5),
            "ratio_threshold": get("ratio_threshold", 3.0)}


def payload(session: Session) -> dict:
    """The task's input: complaints of the recent and baseline windows, each with its category group."""
    s = warning_settings(session)
    groups = router.setting(session, "ai.warning.category_groups", {}) or {}
    group_of = {c: g for g, cats in groups.items() for c in cats}
    rows = repo.complaints(session, s["recent_days"] + s["baseline_days"])
    for r in rows:
        r["group"] = group_of.get(r["category"], r["category"])
    return {"complaints": rows, "settings": s}


def detect(session: Session, principal: Principal) -> dict:
    r = router.run(session, principal, "warning.detect", payload(session), subject_type="signals",
                   subject_id=date.today().isoformat())
    if r["status"] != "ok":
        return {"created": 0, "updated": 0, "method": None}
    today = date.today()
    s = warning_settings(session)
    known = repo.recent_signals(session, s["recent_days"] + s["baseline_days"])
    counts = {"created": 0, "updated": 0, "method": r["output"]["method"]}
    for sig in r["output"]["signals"]:
        oldest, newest = sig["window_days_ago"]
        sig |= {"window_start": today - timedelta(days=oldest), "window_end": today - timedelta(days=newest),
                "path": r["path"], "run_id": r["run_id"]}
        same = next((k for k in known if k["category_group"] == sig["category_group"]
                     and set(k["states"]) & set(sig["states"])
                     and k["window_start"] <= sig["window_end"]
                     and k["window_end"] >= sig["window_start"] - timedelta(days=s["recent_days"])), None)
        if same:
            repo.update(session, same["id"], sig)
            counts["updated"] += 1
            continue
        signal_id = repo.insert(session, sig)
        alert_ids = [_alert(session, signal_id, sig, UUID(b)) for b in sig["bureau_ids"]]
        repo.set_alerts(session, signal_id, alert_ids)
        known.append({"id": signal_id, "category_group": sig["category_group"], "states": sig["states"],
                      "window_start": sig["window_start"], "window_end": sig["window_end"]})
        audit.record(session, principal, "signal.created", entity_type="warning_signals", entity_id=str(signal_id),
                     payload={"method": sig["method"], "path": r["path"], "group": sig["category_group"],
                              "states": sig["states"], "members": sig["members"], "score": sig["score"],
                              "alerts": [str(a) for a in alert_ids]})
        counts["created"] += 1
    return counts


def _alert(session: Session, signal_id: UUID, sig: dict, bureau_id: UUID) -> UUID:
    subject = f"{LABEL}: {sig['category_group']} in {', '.join(sig['states'])}"
    body = (f"{subject}\n\n{sig['members']} complaints between {sig['window_start']:%d %b} and "
            f"{sig['window_end']:%d %b %Y} ({sig['method']}, score {sig['score']}). This is a pattern in the "
            "numbers, not a confirmed problem.\n\nOpen SETHU (Signals) to see the explanation and the cases you may "
            f"see, then acknowledge or dismiss it. Signal {signal_id}.")
    recipients, missing = users.recipients(session, [bureau_id])
    return findings.hold_alert(session, recipients, missing, subject, body, kind="early_warning", bureau_id=bureau_id)


def _shape(session: Session, row: dict) -> dict:
    members = []
    for c in repo.case_refs(session, row.pop("complaint_ids")):
        members.append({"id": c["id"], "ref": c["ref"], "bureau": c["bureau"], "state": c["state"],
                        "category": c["category"], "filed_at": c["filed_at"], "readable": c["readable"]}
                       | ({} if c["readable"] else {"restricted": RESTRICTED}))
    return row | {"label": LABEL, "cases": members}


def listing(session: Session, status: str | None = None, state: str | None = None) -> list[dict]:
    return [_shape(session, r) for r in repo.listing(session, status, state)]


def decide(session: Session, principal: Principal, signal_id: UUID, status: str, reason: str | None) -> dict:
    reason = " ".join((reason or "").split()) or None
    if status == "dismissed" and not reason:
        raise SignalError(422, "say why the signal is dismissed")
    found = repo.listing(session, None, None, signal_id)
    if not found:                                   # Row-Level Security: not a signal of the caller's bureau
        raise SignalError(404, "signal not found")
    old = found[0]["status"]
    actor = users.sync(session, principal)
    if not repo.decide(session, signal_id, status, reason, actor):
        raise SignalError(409 if old == status else 403,
                          f"this signal is already {status}" if old == status
                          else "only oversight or a head of a bureau in this signal can decide it")
    audit.record(session, principal, f"signal.{status}", entity_type="warning_signals", entity_id=str(signal_id),
                 payload={"from": old, "to": status, "reason": reason})
    feedback.record(session, principal, "signal", None, DECISIONS[status], actor_id=actor, signal_id=signal_id,
                    suggested=found[0]["method"], suggested_path=None, old=old, new=status, reason=reason)
    return _shape(session, repo.listing(session, None, None, signal_id)[0])


def map_states(session: Session) -> dict:
    """Per state: complaint density (summary counts) and the signals the caller may see."""
    s_days = warning_settings(session)["recent_days"]
    signals = repo.listing(session, None, None)
    by_state: dict[str, list] = {}
    for sig in signals:
        if sig["status"] == "dismissed":
            continue
        for st in sig["states"]:
            by_state.setdefault(st, []).append(sig["id"])
    states = []
    for row in repo.state_counts(session, s_days):
        states.append(row | {"map_name": state_key(row["state"]), "signals": len(by_state.get(row["state"], []))})
    known = {r["state"] for r in states}
    states += [{"state": st, "map_name": state_key(st), "complaints": 0, "open": 0, "recent": 0,
                "institutions": 0, "signals": len(ids)} for st, ids in by_state.items() if st not in known]
    return {"recent_days": s_days, "states": states, "label": LABEL}


def map_state(session: Session, state: str) -> dict:
    return {"state": state, "institutions": repo.institutions_in(session, state),
            "signals": listing(session, None, state)}
