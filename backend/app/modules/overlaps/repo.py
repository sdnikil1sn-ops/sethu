"""SQL for overlap detection. Text similarity is computed inside PostgreSQL
(pg_trgm); nothing leaves the database. Row-Level Security decides which links
and alerts a caller sees."""
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

OPEN = "status <> 'closed'"


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(row) for row in session.execute(text(sql), params).mappings()]


def _one(session: Session, sql: str, **params: Any) -> dict | None:
    rows = _all(session, sql, **params)
    return rows[0] if rows else None


def suggest_tier2(session: Session, threshold: float, window_days: int) -> list[dict]:
    """Store every new Tier 2 pair as a proposed link and return the rows created.

    Reads complaint text of both bureaus, so it only finds everything when run as
    `system` (the worker) or `admin`. A pair that already has a link, decided or
    not, is left alone: a rejected pair is never suggested again.
    """
    return _all(session, f"""
        INSERT INTO sethu.overlap_links (complaint_a, complaint_b, tier, score, reasons)
        SELECT a.id, b.id, 2, x.score,
               jsonb_build_array('same institution', 'same category: ' || a.category,
                                 'filed ' || x.days_apart || ' days apart',
                                 'text similarity ' || to_char(x.score, 'FM0.00'))
          FROM sethu.complaints a
          JOIN sethu.complaints b
            ON b.institution_id = a.institution_id AND b.bureau_id <> a.bureau_id AND a.id < b.id
           AND b.category = a.category
          CROSS JOIN LATERAL (SELECT similarity(a.body, b.body)::numeric(5,4) AS score,
                                     abs(a.filed_at::date - b.filed_at::date) AS days_apart) x
         WHERE a.{OPEN} AND b.{OPEN} AND x.days_apart <= :window AND x.score >= :threshold
            ON CONFLICT (complaint_a, complaint_b, tier) DO NOTHING
     RETURNING id, complaint_a, complaint_b, score""", threshold=threshold, window=window_days)  # noqa: S608


def refs(session: Session, ids: list[UUID]) -> dict[UUID, str]:
    return {r["id"]: r["ref"] for r in _all(
        session, "SELECT id, ref FROM sethu.complaint_summaries WHERE id = ANY(:ids)", ids=ids)}


def tier1_pairs(session: Session, institution_id: UUID | None) -> list[dict]:
    """Tier 1: every pair of open cases at one institution held by different bureaus.
    Metadata only, so any role may run it. `tier2` says whether the pair also has a link."""
    return _all(session, f"""
        SELECT i.id AS institution_id, i.name AS institution, i.state,
               a.id AS a_id, a.ref AS a_ref, ba.code AS a_bureau, a.category AS a_category,
               b.id AS b_id, b.ref AS b_ref, bb.code AS b_bureau, b.category AS b_category,
               EXISTS (SELECT 1 FROM sethu.overlap_links l
                        WHERE l.complaint_a = a.id AND l.complaint_b = b.id AND l.tier = 2) AS tier2
          FROM sethu.complaint_summaries a
          JOIN sethu.complaint_summaries b
            ON b.institution_id = a.institution_id AND b.bureau_id <> a.bureau_id AND a.id < b.id
          JOIN sethu.institutions i ON i.id = a.institution_id
          JOIN sethu.bureaus ba ON ba.id = a.bureau_id
          JOIN sethu.bureaus bb ON bb.id = b.bureau_id
         WHERE a.{OPEN} AND b.{OPEN} AND (CAST(:inst AS uuid) IS NULL OR i.id = :inst)
         ORDER BY i.name, a.ref, b.ref""", inst=institution_id)  # noqa: S608


def links(session: Session, *, link_id: UUID | None = None, status: str | None = None,
          institution_id: UUID | None = None) -> list[dict]:
    """Links the caller is allowed to see, with both cases' summary fields (never their text)."""
    return _all(session, """
        SELECT l.id, l.tier, l.score, l.reasons, l.status, l.created_at, l.decided_at,
               u.display_name AS decided_by, i.id AS institution_id, i.name AS institution, a.category,
               a.id AS a_id, a.ref AS a_ref, ba.code AS a_bureau, a.bureau_id AS a_bureau_id,
               a.status AS a_status, a.filed_at AS a_filed_at,
               b.id AS b_id, b.ref AS b_ref, bb.code AS b_bureau, b.bureau_id AS b_bureau_id,
               b.status AS b_status, b.filed_at AS b_filed_at,
               al.status AS alert_status, al.recipients AS alert_recipients
          FROM sethu.overlap_links l
          JOIN sethu.complaint_summaries a ON a.id = l.complaint_a
          JOIN sethu.complaint_summaries b ON b.id = l.complaint_b
          JOIN sethu.bureaus ba ON ba.id = a.bureau_id
          JOIN sethu.bureaus bb ON bb.id = b.bureau_id
          LEFT JOIN sethu.institutions i ON i.id = a.institution_id
          LEFT JOIN sethu.app_users u ON u.id = l.decided_by
          LEFT JOIN sethu.alerts al ON al.overlap_link_id = l.id
         WHERE (CAST(:id AS uuid) IS NULL OR l.id = :id)
           AND (CAST(:status AS text) IS NULL OR l.status = :status)
           AND (CAST(:inst AS uuid) IS NULL OR a.institution_id = :inst)
         ORDER BY (l.status = 'proposed') DESC, l.created_at DESC, a.ref""",
                id=link_id, status=status, inst=institution_id)


def linked_case_ids(session: Session) -> list[UUID]:
    """Cases in a link that is suggested or approved, as far as the caller may see links."""
    return [r["id"] for r in _all(session, """
        SELECT complaint_a AS id FROM sethu.overlap_links WHERE status <> 'rejected'
        UNION SELECT complaint_b FROM sethu.overlap_links WHERE status <> 'rejected'""")]


def decide(session: Session, link_id: UUID, status: str, actor_id: UUID) -> bool:
    """Record a decision on a link that is still open. False if it was decided meanwhile,
    or the database does not let this caller decide it."""
    return session.execute(text("""
        UPDATE sethu.overlap_links SET status = :status, decided_by = :actor, decided_at = now()
         WHERE id = :id AND status = 'proposed'"""), {"id": link_id, "status": status, "actor": actor_id}).rowcount == 1


def head_emails(session: Session, bureau_ids: list[UUID]) -> list[str]:
    return [r["email"] for r in _all(session, """
        SELECT email FROM sethu.app_users
         WHERE role = 'bureau_head' AND active AND email IS NOT NULL AND bureau_id = ANY(:b)
         ORDER BY email""", b=bureau_ids)]


def insert_alert(session: Session, link_id: UUID, recipients: list[str], subject: str, body: str,
                 approved_by: UUID) -> UUID:
    return session.execute(text("""
        INSERT INTO sethu.alerts (kind, overlap_link_id, status, recipients, subject, body, approved_by, approved_at)
        VALUES ('overlap', :link, 'approved', CAST(:recipients AS jsonb), :subject, :body, :by, now())
        RETURNING id"""), {"link": link_id, "recipients": json.dumps(recipients), "subject": subject,
                           "body": body, "by": approved_by}).scalar_one()
