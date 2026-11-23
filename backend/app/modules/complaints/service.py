"""Cases: list, detail, history and the actions that move a case along.

Who sees what is decided by the database (Row-Level Security), not here: the
text and history of a case come back only for the bureau holding it, the bureau
that transferred it and is waiting for an acknowledgement, and the oversight,
admin and auditor roles. Everyone else gets the summary fields.

Every action writes one case_actions row, updates the case and appends one audit
entry in the caller's transaction, so they are saved together or not at all.
"""
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.core.config import get_settings
from app.core.crypto import Keyring, KeyringError, key_id_of, load_keyring
from app.modules.complaints import repo
from app.modules.enrichment import service as enrichment
from app.modules.users import service as users

# action -> (case_actions.action, statuses it is allowed from, status afterwards; None keeps it)
ACTIONS: dict[str, tuple[str, set[str], str | None]] = {
    "assign": ("assigned", {"open", "in_progress", "replied"}, "in_progress"),
    "note": ("note", {"open", "in_progress", "replied", "transferred"}, None),
    "reply": ("replied", {"open", "in_progress"}, "replied"),
    "transfer": ("transferred", {"open", "in_progress", "replied", "transferred"}, "transferred"),
    "acknowledge": ("acknowledged", {"transferred"}, "in_progress"),
    "close": ("closed", {"open", "in_progress", "replied"}, "closed"),
    "reopen": ("reopened", {"closed"}, "open"),
}
# Why a case was closed (migration 0010 enforces the same list).
CLOSE_REASONS = ("resolved", "no_action_needed", "duplicate", "withdrawn", "outside_jurisdiction")


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
    found = repo.search(session, filters, limit, offset)
    return found | {"items": [r | _sla(r) for r in found["items"]]}


def lookup(session: Session, q: str, limit: int) -> dict:
    """For the top-bar search. Summary fields only: matching on complaint text is done
    in the database, where Row-Level Security limits it to text the caller may read."""
    rows = repo.lookup(session, _like(q.strip()), q.strip(), limit)  # a bureau code must match exactly
    keep = ("id", "ref", "bureau", "institution_id", "institution", "category", "status", "filed_at", "readable", "why")
    return {"total": rows[0]["total"] if rows else 0, "items": [{k: r[k] for k in keep} for r in rows]}


def can_act(principal: Principal, case: dict) -> bool:
    """Only the bureau holding the case works it. (The sender of an unacknowledged
    transfer can still read it, but no longer holds it.)"""
    if principal.role in ("admin", "system"):
        return True
    return principal.role in ("officer", "bureau_head") and case["holder_id"] == principal.bureau_id


def keyring() -> Keyring:
    path = get_settings().complainant_keys_file
    if not path:
        raise KeyringError("SETHU_COMPLAINANT_KEYS_FILE is not set (docs/RUNBOOK.md, complainant details)")
    return load_keyring(path)


def complainant_visible(principal: Principal, case: dict) -> bool:
    """Only the officers and heads of the bureau holding the case see who complained. The sender of an
    unacknowledged transfer, oversight, admin and auditor see that details exist, not what they are."""
    return principal.role in ("officer", "bureau_head") and principal.bureau_id is not None \
        and principal.bureau_id == case["holder_id"]


def get(session: Session, principal: Principal, complaint_id: UUID) -> dict:
    case = repo.find(session, complaint_id)
    if case is None:
        raise CaseError(404, "case not found")
    readable = case["readable"]
    sealed = case.pop("complainant_enc", None)
    shown = sealed is not None and complainant_visible(principal, case)
    return case | _sla(case) | {
        "complainant": keyring().decrypt(sealed, str(case["id"])) if shown else None,
        "complainant_withheld": sealed is not None and not shown,
        "history": repo.history(session, complaint_id) if readable else [],
        "deadline_days": deadline_days(session, case["category"]),
        "can_act": readable and can_act(principal, case),
        "awaiting_acknowledgement": case["status"] == "transferred",
    } | (enrichment.for_case(session, complaint_id) if readable else {"enrichment": None, "attachments": []})


def rotate_complainant_keys(session: Session, principal: Principal, batch: int = 500) -> dict:
    """Re-encrypt one batch of complainant details onto the active key. Run until it returns 0 left
    (complaints.worker task sethu.complainant.rotate_keys does). Audited with counts and key ids only."""
    ring = keyring()
    rows = repo.not_on_key(session, ring.active, batch)
    old = sorted({key_id_of(r["complainant_enc"]) for r in rows})
    for r in rows:
        aad = str(r["id"])
        repo.set_complainant(session, r["id"], ring.encrypt(ring.decrypt(r["complainant_enc"], aad), aad))
    if rows:
        audit.record(session, principal, "complainant.rekeyed", entity_type="complaints",
                     payload={"rows": len(rows), "to_key": ring.active, "from_keys": old})
    return {"rekeyed": len(rows), "left": len(repo.not_on_key(session, ring.active, 1))}


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
    """The app_users id of a signed-in person, kept in step with the token (users.sync)."""
    return users.sync(session, principal)


def act(session: Session, principal: Principal, complaint_id: UUID, action: str, *, note: str | None = None,
        to_bureau: str | None = None, assignee_id: UUID | None = None, reason: str | None = None) -> dict:
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
    holder, sender, assignee, new_due = case["bureau_id"], case["transferred_from_bureau_id"], case["assignee_id"], None
    row: dict[str, Any] = {"complaint_id": complaint_id, "action": db_action, "note": note}
    payload: dict[str, Any] = {"ref": case["ref"], "status": new_status or case["status"]}
    known = repo.bureaus(session)
    by_code = {b["code"]: b["id"] for b in known}
    code_of = {v: k for k, v in by_code.items()}
    receiving = {b["code"]: b["id"] for b in known if b["active"]}  # a deactivated bureau takes no new cases

    if action == "note" and not note:
        raise CaseError(422, "a note needs some text")
    if action == "close":
        if reason not in CLOSE_REASONS:
            raise CaseError(422, f"choose why the case is closed: {', '.join(CLOSE_REASONS)}")
        row["reason"] = payload["reason"] = reason
    if action == "reopen":
        if not note:
            raise CaseError(422, "say why the case is reopened")
        new_due = due_at(session, case["category"], datetime.now(UTC))  # a fresh deadline from today
        payload["due_at"] = new_due.isoformat()
    if action == "assign":
        if assignee_id not in {s["id"] for s in repo.staff(session, holder)}:
            raise CaseError(422, "the assignee must be an active officer or head of the bureau holding the case")
        if assignee_id == assignee:
            raise CaseError(409, "the case is already assigned to this person")
        row["assignee_id"] = assignee_id
        payload |= {"assignee_id": str(assignee_id), "previous_assignee_id": assignee and str(assignee)}
        assignee = assignee_id
    if action == "transfer":
        target = receiving.get(to_bureau or "")
        if target is None or target == holder:
            raise CaseError(422, "choose another bureau to transfer to")
        row |= {"from_bureau_id": holder, "to_bureau_id": target}
        payload |= {"from": case["bureau"], "to": to_bureau}
        holder, sender, assignee = target, holder, None  # the receiving bureau assigns its own people
    if action == "acknowledge":
        transfer = repo.last_transfer(session, complaint_id) or {"from_bureau_id": sender, "to_bureau_id": holder}
        row |= transfer | {"acknowledged_at": datetime.now(UTC)}
        payload |= {"from": code_of.get(transfer["from_bureau_id"]), "to": code_of.get(transfer["to_bureau_id"])}
        sender = None

    if principal.role != "system":
        row["actor_id"] = actor_id(session, principal)
    # History first: the insert policy checks the case is still held by the caller's bureau.
    repo.insert_action(session, **row)
    repo.update_case(session, complaint_id, new_status or case["status"], holder, sender, assignee, new_due)
    audit.record(session, principal, f"case.{db_action}", entity_type="complaints", entity_id=str(complaint_id),
                 payload=payload)
    session.execute(text("SELECT 1"))  # surface any policy error here, inside the caller's transaction
    return get(session, principal, complaint_id)


def deadline_days(session: Session, category: str | None) -> int:
    """Days to close a case of this category: the admin's setting, else the default (SETHU_SLA_DAYS)."""
    return repo.deadline_days(session, category) or get_settings().sla_days


def due_at(session: Session, category: str | None, start: datetime) -> datetime:
    return start + timedelta(days=deadline_days(session, category))


def deadlines(session: Session) -> list[dict]:
    default = get_settings().sla_days
    return [r | {"effective_days": r["days"] or default, "default_days": default} for r in repo.deadlines(session)]


def set_deadline(session: Session, principal: Principal, category: str, days: int) -> list[dict]:
    """For new cases and reopened ones; a case already open keeps the deadline it was given."""
    repo.set_deadline(session, category, days, actor_id(session, principal))
    audit.record(session, principal, "deadline.set", entity_type="category_deadlines", entity_id=category,
                 payload={"category": category, "days": days})
    return deadlines(session)


def my_cases(session: Session, principal: Principal) -> list[dict]:
    return [r | _sla(r) for r in repo.assigned_to(session, actor_id(session, principal))]


def workload(session: Session) -> list[dict]:
    return repo.workload(session)


def create(session: Session, principal: Principal, *, bureau_id: UUID, source: str, institution_name_raw: str,
           category: str, body: str, language: str, filed_at: datetime, complainant: dict | None,
           institution_id: UUID | None, audit_extra: dict) -> dict:
    """A new complaint, its 'filed' history row and its audit entry, in the caller's transaction.
    `body` is expected normalised (single spaces); its hash is what duplicate checks compare."""
    cid = uuid4()  # chosen here: the encryption binds the complainant details to this complaint's id
    ref = repo.insert_complaint(
        session, id=cid, source=source, bureau_id=bureau_id, institution_id=institution_id,
        institution_name_raw=institution_name_raw, resolution_state="auto" if institution_id else "unresolved",
        category=category, status="open", language=language, body=body,
        body_sha256=hashlib.sha256(body.encode()).hexdigest(), filed_at=filed_at,
        due_at=due_at(session, category, filed_at),
        complainant_enc=keyring().encrypt(complainant, str(cid)) if complainant else None)
    repo.insert_action(session, complaint_id=cid, action="filed", to_bureau_id=bureau_id,
                       note=f"Received via {source}")
    enrichment.mark_pending(session, cid)   # the AI pipeline enriches it later; the case is usable now
    audit.record(session, principal, "complaint.created", entity_type="complaints", entity_id=str(cid),
                 payload={"ref": ref, "source": source, "resolved": institution_id is not None} | audit_extra)
    return {"id": cid, "ref": ref}


def same_text(session: Session, bureau_id: UUID, name: str, body: str) -> dict | None:
    """An existing complaint in this bureau with exactly this (normalised) text about the same typed name."""
    return repo.same_text(session, bureau_id, hashlib.sha256(body.encode()).hexdigest(), name)


def similar_text(session: Session, bureau_id: UUID, institution_id: UUID | None, name: str, body: str,
                 threshold: float, days: int) -> dict | None:
    return repo.similar_text(session, bureau_id, institution_id, name, body, threshold, days)


def lock_text(session: Session, fingerprint: str) -> None:
    """Serialise work on one fingerprint until the transaction ends (two workers, same complaint)."""
    session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:f))"), {"f": fingerprint})
