"""SQL for findings. Detection reads summaries and case actions (no complaint text);
Row-Level Security decides which findings a caller sees."""
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import paging


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(row) for row in session.execute(text(sql), params).mappings()]


def transfer_histories(session: Session) -> list[dict]:
    """Every action of every case that is not closed and has been transferred, oldest first per case."""
    return _all(session, """
        SELECT a.id, a.complaint_id, s.ref, s.institution_id, a.action, a.from_bureau_id, a.to_bureau_id,
               a.acknowledged_at, a.created_at
          FROM sethu.case_actions a
          JOIN sethu.complaint_summaries s ON s.id = a.complaint_id
         WHERE s.status <> 'closed'
           AND a.complaint_id IN (SELECT complaint_id FROM sethu.case_actions WHERE action = 'transferred')
         ORDER BY a.complaint_id, a.created_at, a.id""")


def workflow_actions(session: Session) -> list[dict]:
    """Every case's actions, oldest first per case: the workflow graph's input (no notes, no text)."""
    return _all(session, """
        SELECT a.complaint_id, a.action, a.from_bureau_id, a.to_bureau_id, a.acknowledged_at, a.created_at
          FROM sethu.case_actions a
         ORDER BY a.complaint_id, a.created_at, a.id""")


def workflow_cases(session: Session) -> list[dict]:
    return _all(session, "SELECT id, bureau_id, due_at, status FROM sethu.complaint_summaries")


# Open cases with their bureau's median days to close (over its closed cases) and whether each is overdue.
QUEUE = """
    WITH median AS (
        SELECT bureau_id, percentile_cont(0.5) WITHIN GROUP (
                   ORDER BY extract(epoch FROM closed_at - filed_at) / 86400) AS days
          FROM sethu.complaint_summaries WHERE closed_at IS NOT NULL GROUP BY bureau_id),
    queue AS (
        SELECT s.id, s.bureau_id, s.institution_id, s.due_at < now() AS overdue,
               extract(epoch FROM now() - s.filed_at) / 86400 > m.days AS old, m.days AS median_days
          FROM sethu.complaint_summaries s LEFT JOIN median m ON m.bureau_id = s.bureau_id
         WHERE s.status <> 'closed')"""


def bureau_queues(session: Session) -> list[dict]:
    return _all(session, QUEUE + """
        SELECT bureau_id AS id, ARRAY[bureau_id] AS bureau_ids, count(*) AS open,
               count(*) FILTER (WHERE overdue) AS overdue, count(*) FILTER (WHERE old) AS older_than_median,
               round(max(median_days)::numeric, 1) AS median_days
          FROM queue GROUP BY bureau_id""")  # noqa: S608 - constants only


def institution_queues(session: Session) -> list[dict]:
    """Per institution; each case is compared with its own bureau's median."""
    return _all(session, QUEUE + """
        SELECT institution_id AS id, array_agg(DISTINCT bureau_id) AS bureau_ids, count(*) AS open,
               count(*) FILTER (WHERE overdue) AS overdue, count(*) FILTER (WHERE old) AS older_than_median,
               NULL::numeric AS median_days
          FROM queue WHERE institution_id IS NOT NULL GROUP BY institution_id""")  # noqa: S608


def category_cells(session: Session, recent_days: int, baseline_days: int) -> list[dict]:
    """Complaints per state and category: the last `recent_days`, and the `baseline_days` before.
    Summary fields only. Cases whose institution is not matched yet have no state and are left out."""
    return _all(session, """
        SELECT i.state, s.category,
               count(*) FILTER (WHERE s.filed_at >= now() - make_interval(days => :r)) AS recent,
               count(*) FILTER (WHERE s.filed_at < now() - make_interval(days => :r)) AS previous,
               coalesce(array_agg(DISTINCT s.bureau_id)
                        FILTER (WHERE s.filed_at >= now() - make_interval(days => :r)), '{}') AS bureau_ids
          FROM sethu.complaint_summaries s JOIN sethu.institutions i ON i.id = s.institution_id
         WHERE s.filed_at >= now() - make_interval(days => :r + :b)
           AND i.state IS NOT NULL AND s.category IS NOT NULL
         GROUP BY i.state, s.category""", r=recent_days, b=baseline_days)


def bureau_codes(session: Session) -> dict[UUID, str]:
    return {r["id"]: r["code"] for r in _all(session, "SELECT id, code FROM sethu.bureaus")}


def existing(session: Session) -> list[dict]:
    return _all(session, "SELECT id, key, status FROM sethu.findings")


def insert(session: Session, f: dict, alert_id: UUID | None) -> UUID:
    return session.execute(text("""
        INSERT INTO sethu.findings (kind, key, complaint_id, institution_id, bureau_ids, evidence, alert_id)
        VALUES (:kind, :key, :complaint_id, :institution_id, :bureau_ids, CAST(:evidence AS jsonb), :alert_id)
        RETURNING id"""), {**{k: f.get(k) for k in ("kind", "key", "complaint_id", "institution_id", "bureau_ids")},
                           "evidence": json.dumps(f["evidence"]), "alert_id": alert_id}).scalar_one()


def set_status(session: Session, finding_id: UUID, status: str, actor_id: UUID | None) -> bool:
    """False when Row-Level Security (or the row's absence) stops the update."""
    return session.execute(text("""
        UPDATE sethu.findings SET status = :status, decided_by = :actor, decided_at = now()
         WHERE id = :id"""), {"id": finding_id, "status": status, "actor": actor_id}).rowcount == 1


def reopen(session: Session, finding_id: UUID, evidence: dict, bureau_ids: list[UUID]) -> bool:
    """The detector reopens a finding that holds again, with today's numbers and bureaus."""
    return session.execute(text("""
        UPDATE sethu.findings SET status = 'open', evidence = CAST(:e AS jsonb), bureau_ids = :b,
               decided_by = NULL, decided_at = now()
         WHERE id = :id"""), {"id": finding_id, "e": json.dumps(evidence), "b": bureau_ids}).rowcount == 1


def insert_alert(session: Session, complaint_id: UUID | None, recipients: list[str], missing: list[str], subject: str,
                 body: str, kind: str = "bottleneck", bureau_id: UUID | None = None) -> UUID:
    """Into the existing outbox, held for a person's approval. Nothing is sent before that."""
    return session.execute(text("""
        INSERT INTO sethu.alerts (kind, complaint_id, bureau_id, status, recipients, missing_recipients, subject, body)
        VALUES (:kind, :c, :b, 'pending_approval', CAST(:r AS jsonb), :missing, :subject, :body)
        RETURNING id"""), {"c": complaint_id, "b": bureau_id, "r": json.dumps(recipients), "missing": missing,
                           "subject": subject, "body": body, "kind": kind}).scalar_one()


def overdue_count(session: Session, bureau_id: UUID) -> int:
    return session.execute(text("""
        SELECT count(*) FROM sethu.complaints
         WHERE bureau_id = :b AND status NOT IN ('closed', 'transferred') AND due_at < now()"""),
        {"b": bureau_id}).scalar_one()


def overdue_cases(session: Session) -> list[dict]:
    """Open cases past their deadline (a case awaiting acknowledgement of a transfer is the stalled-transfer
    detector's business, not this one's)."""
    return _all(session, """
        SELECT c.id, c.ref, c.bureau_id, c.institution_id, c.category, c.due_at
          FROM sethu.complaints c
         WHERE c.status NOT IN ('closed', 'transferred') AND c.due_at < now()
         ORDER BY c.due_at""")


FINDING = """
    SELECT f.id, f.kind, f.status, f.first_seen, f.decided_at, u.display_name AS decided_by, f.evidence,
           f.complaint_id, s.ref, f.institution_id, i.name AS institution,
           ARRAY(SELECT b.code FROM sethu.bureaus b WHERE b.id = ANY(f.bureau_ids) ORDER BY b.code) AS bureaus,
           f.alert_id, al.status AS alert_status
      FROM sethu.findings f
      LEFT JOIN sethu.complaint_summaries s ON s.id = f.complaint_id
      LEFT JOIN sethu.institutions i ON i.id = f.institution_id
      LEFT JOIN sethu.app_users u ON u.id = f.decided_by
      LEFT JOIN sethu.alerts al ON al.id = f.alert_id"""

FILTERS = {
    "kind": "f.kind = :kind",
    "status": "f.status = :status",
    "bureau": "EXISTS (SELECT 1 FROM sethu.bureaus b WHERE b.id = ANY(f.bureau_ids) AND b.code = upper(:bureau))",
    "institution_id": "(f.institution_id = :institution_id OR s.institution_id = :institution_id)",
    "id": "f.id = :id",
}


# Open first; then transfer loops, stalled transfers and bottlenecks, the worst bottleneck (largest share, then
# most open cases) first.
ORDER = """(f.status = 'open') DESC,
           array_position(ARRAY['transfer_loop', 'stalled_transfer', 'deadline_escalation', 'bottleneck',
                                 'category_spike'], f.kind),
           (f.evidence->>'share')::numeric DESC NULLS LAST, (f.evidence->>'open')::int DESC NULLS LAST,
           f.first_seen DESC, f.id"""


def _where(filters: dict[str, Any]) -> str:
    return f"{FINDING} WHERE {' AND '.join(FILTERS[k] for k in filters) or 'true'}"  # noqa: S608 - constants only


def listing(session: Session, filters: dict[str, Any]) -> list[dict]:
    """Findings the caller may see (Row-Level Security), unbounded: for one finding by id, and tests."""
    return _all(session, f"{_where(filters)} ORDER BY {ORDER}", **filters)


def page(session: Session, filters: dict[str, Any], limit: int, offset: int) -> dict:
    """One page of the findings the caller may see, with a capped total (app.db.paging)."""
    return paging.page(session, _where(filters), ORDER, filters, limit, offset)


def open_count(session: Session) -> int:
    """Counted up to COUNT_CAP + 1 (the dashboard shows more than COUNT_CAP as "1,000+")."""
    return paging.capped_count(session, "SELECT 1 FROM sethu.findings WHERE status = 'open'", {},
                               paging.COUNT_CAP + 1)[0]


def trend(session: Session, days: int) -> list[dict]:
    """New complaints per institution in the last `days` days against the `days` before, where the
    recent ones come from two or more bureaus and the count went up. Summary fields only."""
    return _all(session, """
        SELECT * FROM (
            SELECT i.id AS institution_id, i.name AS institution, i.state, i.district,
                   count(*) FILTER (WHERE s.filed_at >= now() - make_interval(days => :d)) AS recent,
                   count(*) FILTER (WHERE s.filed_at < now() - make_interval(days => :d)) AS previous,
                   coalesce(array_agg(DISTINCT b.code)
                            FILTER (WHERE s.filed_at >= now() - make_interval(days => :d)), '{}') AS bureaus
              FROM sethu.complaint_summaries s
              JOIN sethu.institutions i ON i.id = s.institution_id
              JOIN sethu.bureaus b ON b.id = s.bureau_id
             WHERE s.filed_at >= now() - make_interval(days => 2 * :d)
             GROUP BY i.id) t
         WHERE cardinality(bureaus) >= 2 AND recent > previous
         ORDER BY recent - previous DESC, recent DESC, institution""", d=days)
