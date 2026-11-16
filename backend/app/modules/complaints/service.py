"""Cases: list, detail, history and the actions that move a case along.

Who sees what is decided by the database (Row-Level Security), not here: the
text and history of a case come back only for the bureau holding it, the bureau
that transferred it and is waiting for an acknowledgement, and the oversight,
admin and auditor roles. Everyone else gets the summary fields.

Every action writes one case_actions row, updates the case and appends one audit
entry in the caller's transaction, so they are saved together or not at all.
"""
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.modules.complaints import repo

# action -> (case_actions.action, statuses it is allowed from, status afterwards; None keeps it)
ACTIONS: dict[str, tuple[str, set[str], str | None]] = {
    "assign": ("assigned", {"open", "in_progress", "replied"}, "in_progress"),
    "note": ("note", {"open", "in_progress", "replied", "transferred"}, None),
    "reply": ("replied", {"open", "in_progress"}, "replied"),
    "transfer": ("transferred", {"open", "in_progress", "replied", "transferred"}, "transferred"),
    "acknowledge": ("acknowledged", {"transferred"}, "in_progress"),
    "close": ("closed", {"open", "in_progress", "replied"}, "closed"),
}


class CaseError(Exception):
    """A request that cannot be carried out. `status` is the HTTP status to answer with."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def _like(q: str) -> str:
    """A contains-pattern with the LIKE wildcards in q taken literally."""
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _sla(case: dict) -> dict:
    """The 21-day clock: whole days left before the due date, negative once it has passed."""
    if case["status"] == "closed" or case["due_at"] is None:
        return {"overdue": False, "days_remaining": None}
    days = (case["due_at"] - datetime.now(UTC)).days  # floors: 2 hours late is -1
    return {"overdue": days < 0, "days_remaining": days}


def search(session: Session, filters: dict[str, Any], limit: int, offset: int) -> dict:
    filters = {k: v for k, v in filters.items() if v not in (None, "")}
    if "q" in filters:
        filters["q"] = _like(filters["q"].strip())
    rows = repo.search(session, filters, limit, offset)
    return {"total": rows[0]["total"] if rows else 0, "items": [r | _sla(r) for r in rows]}


def can_act(principal: Principal, case: dict) -> bool:
    """Only the bureau holding the case works it. (The sender of an unacknowledged
    transfer can still read it, but no longer holds it.)"""
    if principal.role in ("admin", "system"):
        return True
    return principal.role in ("officer", "bureau_head") and case["holder_id"] == principal.bureau_id


def get(session: Session, principal: Principal, complaint_id: UUID) -> dict:
    case = repo.find(session, complaint_id)
    if case is None:
        raise CaseError(404, "case not found")
    readable = case["readable"]
    return case | _sla(case) | {
        "history": repo.history(session, complaint_id) if readable else [],
        "can_act": readable and can_act(principal, case) and case["status"] != "closed",
        "awaiting_acknowledgement": case["status"] == "transferred",
    }


def institution_timeline(session: Session, institution_id: UUID) -> dict:
    """Actions across an institution's cases, oldest first, limited to cases the caller may read."""
    counts = repo.case_counts(session, institution_id)
    return {"actions": repo.institution_history(session, institution_id),
            "hidden_cases": counts["total"] - counts["readable"]}


def options(session: Session) -> dict:
    return repo.options(session) | {"bureaus": repo.bureaus(session), "statuses": sorted(
        {"open", "in_progress", "transferred", "replied", "closed"})}


def assignees(session: Session, complaint_id: UUID) -> list[dict]:
    case = repo.find(session, complaint_id)
    return repo.staff(session, case["holder_id"]) if case and case["readable"] else []


def actor_id(session: Session, principal: Principal) -> UUID:
    """The app_users id of a signed-in person, registered (and audited) on first use."""
    user_id, created = repo.ensure_user(session, principal)
    if created:
        audit.record(session, principal, "user.registered", entity_type="app_users", entity_id=str(user_id),
                     payload={"role": principal.role})
    return user_id


def act(session: Session, principal: Principal, complaint_id: UUID, action: str, *, note: str | None = None,
        to_bureau: str | None = None, assignee_id: UUID | None = None) -> dict:
    db_action, allowed_from, new_status = ACTIONS[action]
    case = repo.lock(session, complaint_id)
    if case is None:  # Row-Level Security hid it: another bureau's case, or no such case
        raise CaseError(403, "this case belongs to another bureau") if repo.exists(session, complaint_id) \
            else CaseError(404, "case not found")
    if not can_act(principal, case | {"holder_id": case["bureau_id"]}):
        raise CaseError(403, "only the bureau holding this case can act on it")
    if case["status"] not in allowed_from:
        raise CaseError(409, f"a case that is {case['status'].replace('_', ' ')} cannot take the action '{action}'")

    note = (note or "").strip() or None
    holder, sender = case["bureau_id"], case["transferred_from_bureau_id"]
    row: dict[str, Any] = {"complaint_id": complaint_id, "action": db_action, "note": note}
    payload: dict[str, Any] = {"ref": case["ref"], "status": new_status or case["status"]}
    by_code = {b["code"]: b["id"] for b in repo.bureaus(session)}
    code_of = {v: k for k, v in by_code.items()}

    if action == "note" and not note:
        raise CaseError(422, "a note needs some text")
    if action == "assign":
        if assignee_id not in {s["id"] for s in repo.staff(session, holder)}:
            raise CaseError(422, "the assignee must be an officer or head of the bureau holding the case")
        row["assignee_id"] = assignee_id
        payload["assignee_id"] = str(assignee_id)
    if action == "transfer":
        target = by_code.get(to_bureau or "")
        if target is None or target == holder:
            raise CaseError(422, "choose another bureau to transfer to")
        row |= {"from_bureau_id": holder, "to_bureau_id": target}
        payload |= {"from": case["bureau"], "to": to_bureau}
        holder, sender = target, holder
    if action == "acknowledge":
        transfer = repo.last_transfer(session, complaint_id) or {"from_bureau_id": sender, "to_bureau_id": holder}
        row |= transfer | {"acknowledged_at": datetime.now(UTC)}
        payload |= {"from": code_of.get(transfer["from_bureau_id"]), "to": code_of.get(transfer["to_bureau_id"])}
        sender = None

    if principal.role != "system":
        row["actor_id"] = actor_id(session, principal)
    # History first: the insert policy checks the case is still held by the caller's bureau.
    repo.insert_action(session, **row)
    repo.update_case(session, complaint_id, new_status or case["status"], holder, sender)
    audit.record(session, principal, f"case.{db_action}", entity_type="complaints", entity_id=str(complaint_id),
                 payload=payload)
    session.execute(text("SELECT 1"))  # surface any policy error here, inside the caller's transaction
    return get(session, principal, complaint_id)
