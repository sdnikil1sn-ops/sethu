"""SQL for early-warning signals and the India map. Summary fields and counts only; Row-Level Security decides
which signals a caller sees (sethu.warning_signals: the bureaus whose cases are in it, and the roles that see
everything)."""
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(r) for r in session.execute(text(sql), params).mappings()]


def complaints(session: Session, days: int) -> list[dict]:
    """Complaints filed in the last `days` with a matched institution (it gives the state): id, category, state,
    bureau and days ago. Worker only (every bureau)."""
    return _all(session, """
        SELECT s.id, s.category, i.state, s.bureau_id,
               floor(extract(epoch FROM now() - s.filed_at) / 86400)::int AS days_ago
          FROM sethu.complaint_summaries s JOIN sethu.institutions i ON i.id = s.institution_id
         WHERE s.filed_at >= now() - make_interval(days => :d) AND s.category IS NOT NULL AND i.state IS NOT NULL""",
                d=days)


def recent_signals(session: Session, days: int) -> list[dict]:
    return _all(session, """
        SELECT id, category_group, states, window_start, window_end, status, alert_ids
          FROM sethu.warning_signals WHERE last_seen >= now() - make_interval(days => :d)""", d=days)


def insert(session: Session, s: dict) -> UUID:
    return session.execute(text("""
        INSERT INTO sethu.warning_signals (category_group, categories, states, window_start, window_end, method, path,
                                           score, members, complaint_ids, bureau_ids, explanation, parameters,
                                           ai_run_id)
        VALUES (:group, :categories, :states, :ws, :we, :method, :path, :score, :members, CAST(:ids AS uuid[]),
                CAST(:bureaus AS uuid[]), CAST(:explanation AS jsonb), CAST(:parameters AS jsonb), :run)
        RETURNING id"""), _params(s)).scalar_one()


def update(session: Session, signal_id: UUID, s: dict) -> None:
    """The same signal seen again: its latest numbers (a person's status is kept)."""
    session.execute(text("""
        UPDATE sethu.warning_signals SET categories = :categories,
               states = ARRAY(SELECT DISTINCT unnest(states || CAST(:states AS text[])) ORDER BY 1),
               window_start = least(window_start, :ws), window_end = greatest(window_end, :we), method = :method,
               path = :path, score = :score, members = :members, complaint_ids = CAST(:ids AS uuid[]),
               bureau_ids = ARRAY(SELECT DISTINCT unnest(bureau_ids || CAST(:bureaus AS uuid[]))),
               explanation = CAST(:explanation AS jsonb), parameters = CAST(:parameters AS jsonb), ai_run_id = :run,
               last_seen = now()
         WHERE id = :id"""), _params(s) | {"id": signal_id})


def _params(s: dict) -> dict:
    return {"group": s["category_group"], "categories": s["categories"], "states": s["states"],
            "ws": s["window_start"], "we": s["window_end"], "method": s["method"], "path": s["path"],
            "score": s["score"], "members": s["members"], "ids": s["complaint_ids"], "bureaus": s["bureau_ids"],
            "explanation": json.dumps(s["explanation"], default=str), "parameters": json.dumps(s["parameters"]),
            "run": s["run_id"]}


def set_alerts(session: Session, signal_id: UUID, alert_ids: list[UUID]) -> None:
    session.execute(text("UPDATE sethu.warning_signals SET alert_ids = :a WHERE id = :id"),
                    {"a": alert_ids, "id": signal_id})


LIST = """
    SELECT w.id, w.category_group, w.categories, w.states, w.window_start, w.window_end, w.method, w.path, w.score,
           w.members, w.complaint_ids, w.explanation, w.parameters, w.status, w.status_reason, w.decided_at,
           u.display_name AS decided_by, w.first_seen, w.last_seen,
           ARRAY(SELECT b.code FROM sethu.bureaus b WHERE b.id = ANY(w.bureau_ids) ORDER BY b.code) AS bureaus
      FROM sethu.warning_signals w LEFT JOIN sethu.app_users u ON u.id = w.decided_by"""


def listing(session: Session, status: str | None, state: str | None, signal_id: UUID | None = None) -> list[dict]:
    return _all(session, LIST + """
         WHERE (CAST(:status AS text) IS NULL OR w.status = :status)
           AND (CAST(:state AS text) IS NULL OR :state = ANY(w.states))
           AND (CAST(:id AS uuid) IS NULL OR w.id = :id)
         ORDER BY (w.status = 'new') DESC, w.last_seen DESC, w.id""",  # noqa: S608 - constants only
                status=status, state=state, id=signal_id)


def decide(session: Session, signal_id: UUID, status: str, reason: str | None, actor: UUID) -> bool:
    return session.execute(text("""
        UPDATE sethu.warning_signals SET status = :s, status_reason = :r, decided_by = :by, decided_at = now()
         WHERE id = :id AND status <> :s"""), {"s": status, "r": reason, "by": actor, "id": signal_id}).rowcount == 1


def case_refs(session: Session, ids: list[UUID]) -> list[dict]:
    """Summary of each member case, and whether the caller may read the case itself."""
    return _all(session, """
        SELECT s.id, s.ref, b.code AS bureau, i.state, s.category, s.filed_at, c.id IS NOT NULL AS readable
          FROM sethu.complaint_summaries s JOIN sethu.bureaus b ON b.id = s.bureau_id
          LEFT JOIN sethu.institutions i ON i.id = s.institution_id
          LEFT JOIN sethu.complaints c ON c.id = s.id
         WHERE s.id = ANY(:ids) ORDER BY s.filed_at DESC, s.ref""", ids=ids)


def state_counts(session: Session, days: int) -> list[dict]:
    """Complaint density per state (summary counts every signed-in role may see)."""
    return _all(session, """
        SELECT i.state, count(*) AS complaints, count(*) FILTER (WHERE s.status <> 'closed') AS open,
               count(*) FILTER (WHERE s.filed_at >= now() - make_interval(days => :d)) AS recent,
               count(DISTINCT s.institution_id) AS institutions
          FROM sethu.complaint_summaries s JOIN sethu.institutions i ON i.id = s.institution_id
         WHERE i.state IS NOT NULL GROUP BY i.state ORDER BY i.state""", d=days)


def institutions_in(session: Session, state: str) -> list[dict]:
    return _all(session, """
        SELECT i.id, i.name, i.district, count(s.id) AS complaints,
               count(s.id) FILTER (WHERE s.status <> 'closed') AS open
          FROM sethu.institutions i LEFT JOIN sethu.complaint_summaries s ON s.institution_id = i.id
         WHERE i.state = :state GROUP BY i.id ORDER BY count(s.id) DESC, i.name""", state=state)
