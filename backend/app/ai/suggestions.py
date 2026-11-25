"""AI suggestions and officer feedback, shared by the modules that show a suggestion and take the decision on it
(complaints' category, institutions, overlaps).

sethu.ai_suggestions holds the current suggestion per complaint and kind; sethu.ai_feedback is the append-only
record of every decision (who, when, what was suggested, old value, new value), written with an audit entry in the
caller's transaction. Values are categories, institution ids and link decisions: never complaint text.
"""
import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal


def get(session: Session, complaint_id: UUID, kind: str) -> dict | None:
    """The suggestion, if the caller may read the complaint's text (Row-Level Security)."""
    row = session.execute(text("""
        SELECT complaint_id, kind, suggested, candidates, path, provider, confidence, model_version, status,
               created_at, decided_at
          FROM sethu.ai_suggestions WHERE complaint_id = :c AND kind = :k"""),
        {"c": complaint_id, "k": kind}).mappings().first()
    return dict(row) if row else None


def store(session: Session, complaint_id: UUID, kind: str, *, suggested: str | None, candidates: list[dict],
          path: str, provider: str | None, confidence: float | None, model_version: str | None, attempt_key: str,
          run_id: str | None, status: str = "suggested") -> None:
    """Write (or replace, on a new attempt) the suggestion. Worker only (the database checks)."""
    session.execute(text("""
        INSERT INTO sethu.ai_suggestions (complaint_id, kind, suggested, candidates, path, provider, confidence,
                                          model_version, attempt_key, ai_run_id, status)
        VALUES (:c, :k, :s, CAST(:cand AS jsonb), :path, :provider, :conf, :mv, :key, :run, :status)
        ON CONFLICT (complaint_id, kind) DO UPDATE SET
            suggested = EXCLUDED.suggested, candidates = EXCLUDED.candidates, path = EXCLUDED.path,
            provider = EXCLUDED.provider, confidence = EXCLUDED.confidence, model_version = EXCLUDED.model_version,
            attempt_key = EXCLUDED.attempt_key, ai_run_id = EXCLUDED.ai_run_id, status = EXCLUDED.status,
            created_at = now(), decided_by = NULL, decided_at = NULL"""),
        {"c": complaint_id, "k": kind, "s": suggested, "cand": json.dumps(candidates, default=str), "path": path,
         "provider": provider, "conf": confidence, "mv": model_version, "key": attempt_key, "run": run_id,
         "status": status})


def attempt_keys(session: Session, kind: str, complaint_ids: list[UUID]) -> dict[UUID, str]:
    return {r[0]: r[1] for r in session.execute(text(
        "SELECT complaint_id, attempt_key FROM sethu.ai_suggestions WHERE kind = :k AND complaint_id = ANY(:ids)"),
        {"k": kind, "ids": complaint_ids})}


def record(session: Session, principal: Principal, kind: str, complaint_id: UUID | None, decision: str, *,
           actor_id: UUID | None, suggested: str | None = None, suggested_path: str | None = None,
           old: str | None = None, new: str | None = None, overlap_link_id: UUID | None = None,
           signal_id: UUID | None = None, reason: str | None = None) -> int:
    """One append-only feedback row and its audit entry."""
    row_id = session.execute(text("""
        INSERT INTO sethu.ai_feedback (kind, complaint_id, overlap_link_id, signal_id, decision, suggested,
                                       suggested_path, old_value, new_value, reason, decided_by)
        VALUES (:kind, :c, :link, :signal, :decision, :suggested, :path, :old, :new, :reason, :by) RETURNING id"""),
        {"kind": kind, "c": complaint_id, "link": overlap_link_id, "signal": signal_id, "decision": decision,
         "suggested": suggested, "path": suggested_path, "old": old, "new": new, "reason": reason,
         "by": actor_id}).scalar_one()
    audit.record(session, principal, "ai.feedback", entity_type="ai_feedback", entity_id=str(row_id),
                 payload={"kind": kind, "decision": decision, "complaint_id": complaint_id and str(complaint_id),
                          "overlap_link_id": overlap_link_id and str(overlap_link_id),
                          "signal_id": signal_id and str(signal_id), "suggested": suggested,
                          "suggested_path": suggested_path, "old": old, "new": new, "reason": reason})
    return row_id


def decide(session: Session, principal: Principal, complaint_id: UUID, kind: str, new: str, old: str | None,
           actor_id: UUID | None) -> dict | None:
    """An officer settled a category or institution: mark the open suggestion (if any) accepted (took it), rejected
    (kept the value it had) or changed (chose a third), and record the feedback. Returns the decision, or None when
    there was no open suggestion to answer."""
    found = get(session, complaint_id, kind)
    if found is None or found["status"] != "suggested":
        return None
    decision = "accepted" if found["suggested"] == new else "rejected" if new == old else "changed"
    session.execute(text("""
        UPDATE sethu.ai_suggestions SET status = :s, decided_by = :by, decided_at = now()
         WHERE complaint_id = :c AND kind = :k AND status = 'suggested'"""),
        {"s": decision, "by": actor_id, "c": complaint_id, "k": kind})
    record(session, principal, kind, complaint_id, decision, actor_id=actor_id, suggested=found["suggested"],
           suggested_path=found["path"], old=old, new=new)
    return {"decision": decision, "suggested": found["suggested"], "path": found["path"]}
