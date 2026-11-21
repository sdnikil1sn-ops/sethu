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


# The pairs the rules allow (same institution and category, different bureaus, both open, filed close together),
# with both signals. `semantic` is NULL unless both complaints are English and embedded with `model`.
CANDIDATES = """
        SELECT a.id AS complaint_a, b.id AS complaint_b, a.category, x.days_apart,
               similarity(a.body, b.body)::numeric(5,4) AS trigram,
               CASE WHEN a.language = 'en' AND b.language = 'en'
                    THEN (1 - (ea.embedding <=> eb.embedding))::numeric(5,4) END AS semantic
          FROM sethu.complaints a
          JOIN sethu.complaints b
            ON b.institution_id = a.institution_id AND b.bureau_id <> a.bureau_id AND a.id < b.id
           AND b.category = a.category
          LEFT JOIN sethu.complaint_embeddings ea ON ea.complaint_id = a.id AND ea.model = :model
          LEFT JOIN sethu.complaint_embeddings eb ON eb.complaint_id = b.id AND eb.model = :model
          CROSS JOIN LATERAL (SELECT abs(a.filed_at::date - b.filed_at::date) AS days_apart) x
         WHERE a.status <> 'closed' AND b.status <> 'closed' AND x.days_apart <= :window"""


def candidates(session: Session, window_days: int, model: str) -> list[dict]:
    """Every pair the rules allow, with its signal values (no text leaves the database)."""
    return _all(session, CANDIDATES, window=window_days, model=model)


def suggest_tier2(session: Session, threshold: float, window_days: int, semantic_threshold: float | None,
                  model: str) -> list[dict]:
    """Store every new Tier 2 pair as a proposed link and return the rows created.

    The rules gate; then a pair is suggested when its trigram similarity reaches `threshold` or, with the
    semantic signal on (`semantic_threshold` not None), its embedding similarity reaches that. The score is the
    higher of the two; `signals` records both values and which fired. Reads complaint text and embeddings of
    both bureaus, so it only finds everything when run as `system` (the worker) or `admin`. A pair that already
    has a link, decided or not, is left alone: a rejected pair is never suggested again.
    """
    return _all(session, f"""
        WITH c AS ({CANDIDATES}),
        s AS (SELECT c.*, c.trigram >= :threshold AS t_fired,
                     coalesce(CAST(:semantic_threshold AS numeric) IS NOT NULL
                              AND c.semantic >= CAST(:semantic_threshold AS numeric), false) AS s_fired
                FROM c)
        INSERT INTO sethu.overlap_links (complaint_a, complaint_b, tier, score, reasons, signals)
        SELECT complaint_a, complaint_b, 2, greatest(trigram, CASE WHEN s_fired THEN semantic END),
               jsonb_build_array('same institution', 'same category: ' || category,
                                 'filed ' || days_apart || ' days apart',
                                 'text similarity ' || to_char(trigram, 'FM0.00')
                                     || CASE WHEN t_fired THEN ' (fired)' ELSE '' END)
               || CASE WHEN semantic IS NULL OR CAST(:semantic_threshold AS numeric) IS NULL THEN '[]'::jsonb
                       ELSE jsonb_build_array('meaning similarity ' || to_char(semantic, 'FM0.00')
                                              || CASE WHEN s_fired THEN ' (fired)' ELSE '' END) END,
               jsonb_strip_nulls(jsonb_build_object(
                   'trigram', trigram,
                   'semantic', CASE WHEN CAST(:semantic_threshold AS numeric) IS NOT NULL THEN semantic END,
                   'fired', to_jsonb(array_remove(ARRAY[CASE WHEN t_fired THEN 'trigram' END,
                                                        CASE WHEN s_fired THEN 'semantic' END], NULL)),
                   'model', CASE WHEN s_fired THEN CAST(:model AS text) END))
          FROM s WHERE t_fired OR s_fired
            ON CONFLICT (complaint_a, complaint_b, tier) DO NOTHING
     RETURNING id, complaint_a, complaint_b, score, signals""",  # noqa: S608 - fixed text
                threshold=threshold, window=window_days, semantic_threshold=semantic_threshold, model=model)


def unembedded(session: Session, model: str, limit: int) -> list[dict]:
    """Complaints with no embedding for this model yet: their id and text, for the worker only."""
    return _all(session, """
        SELECT c.id, c.body FROM sethu.complaints c
         WHERE NOT EXISTS (SELECT 1 FROM sethu.complaint_embeddings e WHERE e.complaint_id = c.id AND e.model = :m)
         ORDER BY c.filed_at DESC LIMIT :limit""", m=model, limit=limit)


def store_embeddings(session: Session, model: str, rows: list[tuple[UUID, list[float]]]) -> None:
    for complaint_id, vector in rows:
        session.execute(text("""
            INSERT INTO sethu.complaint_embeddings (complaint_id, model, embedding)
            VALUES (:c, :m, CAST(:v AS vector)) ON CONFLICT (complaint_id, model) DO NOTHING"""),
            {"c": complaint_id, "m": model, "v": "[" + ",".join(f"{x:.6f}" for x in vector) + "]"})


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
          institution_id: UUID | None = None, bureau: str | None = None, tier: int | None = None) -> list[dict]:
    """Links the caller is allowed to see, with both cases' summary fields (never their text)."""
    return _all(session, """
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
           AND (CAST(:tier AS int) IS NULL OR l.tier = :tier)
         ORDER BY (l.status = 'proposed') DESC, l.created_at DESC, a.ref""",
                id=link_id, status=status, inst=institution_id, bureau=bureau, tier=tier)


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
