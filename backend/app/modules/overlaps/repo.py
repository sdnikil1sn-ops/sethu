"""SQL for overlap detection. Text similarity is computed inside PostgreSQL
(pg_trgm); nothing leaves the database. Row-Level Security decides which links
and alerts a caller sees."""
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import paging

OPEN = "status <> 'closed'"


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(row) for row in session.execute(text(sql), params).mappings()]


def _one(session: Session, sql: str, **params: Any) -> dict | None:
    rows = _all(session, sql, **params)
    return rows[0] if rows else None


# The pairs the rules allow (same institution and category, different bureaus, both open, filed close together)
# that have no link yet, with both signals and the last verdict's key. `semantic` is NULL unless both complaints
# have a vector of exactly this model AND version: vectors of different models are never compared. The language
# is the one detected by enrichment, else the one the complaint was filed with.
CANDIDATES = """
        SELECT a.id AS complaint_a, b.id AS complaint_b, a.category, a.institution_id, x.days_apart,
               similarity(a.body, b.body)::numeric(5,4) AS trigram,
               (1 - (ea.embedding <=> eb.embedding))::numeric(6,5) AS semantic,
               coalesce(nullif(na.language, 'unknown'), a.language)
                   = coalesce(nullif(nb.language, 'unknown'), b.language) AS same_language,
               me.match_key AS last_key
          FROM sethu.complaints a
          JOIN sethu.complaints b
            ON b.institution_id = a.institution_id AND b.bureau_id <> a.bureau_id AND a.id < b.id
           AND b.category = a.category
          LEFT JOIN sethu.complaint_embeddings ea ON ea.complaint_id = a.id
           AND ea.embedding_model = :model AND ea.embedding_version = :version
          LEFT JOIN sethu.complaint_embeddings eb ON eb.complaint_id = b.id
           AND eb.embedding_model = :model AND eb.embedding_version = :version
          LEFT JOIN sethu.complaint_enrichment na ON na.complaint_id = a.id
          LEFT JOIN sethu.complaint_enrichment nb ON nb.complaint_id = b.id
          LEFT JOIN sethu.match_evaluations me ON me.complaint_a = a.id AND me.complaint_b = b.id
          CROSS JOIN LATERAL (SELECT abs(a.filed_at::date - b.filed_at::date) AS days_apart) x
         WHERE a.status <> 'closed' AND b.status <> 'closed' AND x.days_apart <= :window
           AND NOT EXISTS (SELECT 1 FROM sethu.overlap_links l
                            WHERE l.complaint_a = a.id AND l.complaint_b = b.id AND l.tier = 2)"""


def candidates(session: Session, window_days: int, model: str | None, version: str | None) -> list[dict]:
    """Every unlinked pair the rules allow, with its signal values (no text leaves the database). Reads both
    bureaus' text and vectors, so it finds everything only as `system` (the worker) or `admin`."""
    return _all(session, f"{CANDIDATES} ORDER BY a.filed_at DESC, a.id, b.id",  # noqa: S608 - constants only
                window=window_days, model=model, version=version)


def save_evaluation(session: Session, a: UUID, b: UUID, key: str, matched: bool, method: str,
                    score: float | None, confidence: float | None, run_id: str | None) -> None:
    session.execute(text("""
        INSERT INTO sethu.match_evaluations (complaint_a, complaint_b, match_key, matched, method, score, confidence,
                                             ai_run_id)
        VALUES (:a, :b, :key, :matched, :method, :score, :conf, :run)
        ON CONFLICT (complaint_a, complaint_b) DO UPDATE SET
            match_key = EXCLUDED.match_key, matched = EXCLUDED.matched, method = EXCLUDED.method,
            score = EXCLUDED.score, confidence = EXCLUDED.confidence, ai_run_id = EXCLUDED.ai_run_id,
            evaluated_at = now()"""),
        {"a": a, "b": b, "key": key, "matched": matched, "method": method, "score": score, "conf": confidence,
         "run": run_id})


def insert_link(session: Session, a: UUID, b: UUID, score: float | None, reasons: list[str],
                signals: dict) -> UUID | None:
    """A proposed Tier 2 link; None if the pair got one meanwhile (a rejected pair is never suggested again)."""
    return session.execute(text("""
        INSERT INTO sethu.overlap_links (complaint_a, complaint_b, tier, score, reasons, signals)
        VALUES (:a, :b, 2, :score, CAST(:reasons AS jsonb), CAST(:signals AS jsonb))
        ON CONFLICT (complaint_a, complaint_b, tier) DO NOTHING RETURNING id"""),
        {"a": a, "b": b, "score": score, "reasons": json.dumps(reasons),
         "signals": json.dumps(signals, default=str)}).scalar()


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


LINKS = """
        SELECT l.id, l.tier, l.score, l.reasons, l.signals, l.status, l.created_at, l.decided_at,
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
           AND (CAST(:bureau AS text) IS NULL OR upper(:bureau) IN (ba.code, bb.code))
           AND (CAST(:tier AS int) IS NULL OR l.tier = :tier)"""
LINK_ORDER = "(l.status = 'proposed') DESC, l.created_at DESC, a.ref, l.id"


def links(session: Session, *, link_id: UUID | None = None, status: str | None = None,
          institution_id: UUID | None = None, bureau: str | None = None, tier: int | None = None) -> list[dict]:
    """Links the caller is allowed to see, with both cases' summary fields (never their text). Unbounded: for
    one link by id, and tests; the screen uses `links_page`."""
    return _all(session, f"{LINKS} ORDER BY {LINK_ORDER}",  # noqa: S608 - constants only
                id=link_id, status=status, inst=institution_id, bureau=bureau, tier=tier)


def links_page(session: Session, limit: int, offset: int, *, status: str | None = None,
               institution_id: UUID | None = None, bureau: str | None = None, tier: int | None = None) -> dict:
    return paging.page(session, LINKS, LINK_ORDER, {"id": None, "status": status, "inst": institution_id,
                                                    "bureau": bureau, "tier": tier}, limit, offset)


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


def insert_alert(session: Session, link_id: UUID, recipients: list[str], missing: list[str], subject: str,
                 body: str, approved_by: UUID) -> UUID:
    return session.execute(text("""
        INSERT INTO sethu.alerts (kind, overlap_link_id, status, recipients, missing_recipients, subject, body,
                                  approved_by, approved_at)
        VALUES ('overlap', :link, 'approved', CAST(:recipients AS jsonb), :missing, :subject, :body, :by, now())
        RETURNING id"""), {"link": link_id, "recipients": json.dumps(recipients), "missing": missing,
                           "subject": subject, "body": body, "by": approved_by}).scalar_one()
