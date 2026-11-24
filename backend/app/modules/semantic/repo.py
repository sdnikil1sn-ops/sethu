"""SQL for A3: E5 vectors of complaints and of the institution registry, classifier versions, and the counts the
AI health screen shows. Vectors are written and read by the worker only; no query here returns one to an API."""
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(r) for r in session.execute(text(sql), params).mappings()]


def _vector(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


# --- complaint vectors -------------------------------------------------------------------------------------

def missing_vectors(session: Session, model: str, version: str, limit: int, ids: list[UUID] | None = None) -> list:
    """Complaints (the newest first) with no vector of exactly this model and version: id and ORIGINAL text."""
    return _all(session, """
        SELECT c.id, c.body FROM sethu.complaints c
         WHERE (CAST(:ids AS uuid[]) IS NULL OR c.id = ANY(:ids))
           AND NOT EXISTS (SELECT 1 FROM sethu.complaint_embeddings e WHERE e.complaint_id = c.id
                              AND e.embedding_model = :m AND e.embedding_version = :v)
         ORDER BY c.filed_at DESC, c.id LIMIT :limit""", m=model, v=version, limit=limit, ids=ids)


def store_vectors(session: Session, model: str, version: str, rows: list[tuple[UUID, list[float]]]) -> None:
    for complaint_id, vector in rows:
        session.execute(text("""
            INSERT INTO sethu.complaint_embeddings (complaint_id, embedding_model, embedding_version, embedding)
            VALUES (:c, :m, :v, CAST(:e AS vector)) ON CONFLICT DO NOTHING"""),
            {"c": complaint_id, "m": model, "v": version, "e": _vector(vector)})


def vector_of(session: Session, complaint_id: UUID, model: str, version: str) -> list[float] | None:
    found = session.execute(text("""
        SELECT embedding::text FROM sethu.complaint_embeddings
         WHERE complaint_id = :c AND embedding_model = :m AND embedding_version = :v"""),
        {"c": complaint_id, "m": model, "v": version}).scalar()
    return json.loads(found) if found else None


def vector_counts(session: Session) -> list[dict]:
    return _all(session, """
        SELECT embedding_model AS model, embedding_version AS version, count(*) AS complaints
          FROM sethu.complaint_embeddings GROUP BY 1, 2 ORDER BY 1, 2""")


def complaint_count(session: Session) -> int:
    return session.execute(text("SELECT count(*) FROM sethu.complaints")).scalar_one()


# --- registry vectors --------------------------------------------------------------------------------------

LABELS = """
    SELECT id AS institution_id, name AS label FROM sethu.institutions
    UNION SELECT id, name || ', ' || district FROM sethu.institutions WHERE district IS NOT NULL
    UNION SELECT institution_id, alias FROM sethu.institution_aliases"""


def registry_missing(session: Session, model: str, version: str, limit: int) -> list[dict]:
    return _all(session, f"""
        SELECT n.institution_id, n.label FROM ({LABELS}) n
         WHERE NOT EXISTS (SELECT 1 FROM sethu.institution_embeddings e
                            WHERE e.institution_id = n.institution_id AND e.label = n.label
                              AND e.embedding_model = :m AND e.embedding_version = :v)
         ORDER BY n.institution_id, n.label LIMIT :limit""", m=model, v=version, limit=limit)  # noqa: S608


def registry_drop_stale(session: Session, model: str, version: str) -> int:
    """Names and aliases removed from the registry lose their vectors."""
    return session.execute(text(f"""
        DELETE FROM sethu.institution_embeddings e
         WHERE e.embedding_model = :m AND e.embedding_version = :v
           AND NOT EXISTS (SELECT 1 FROM ({LABELS}) n
                            WHERE n.institution_id = e.institution_id AND n.label = e.label)"""),  # noqa: S608
        {"m": model, "v": version}).rowcount


def registry_store(session: Session, model: str, version: str, rows: list[tuple[UUID, str, list[float]]]) -> None:
    for institution_id, label, vector in rows:
        session.execute(text("""
            INSERT INTO sethu.institution_embeddings (institution_id, label, embedding_model, embedding_version,
                                                      embedding)
            VALUES (:i, :l, :m, :v, CAST(:e AS vector)) ON CONFLICT DO NOTHING"""),
            {"i": institution_id, "l": label, "m": model, "v": version, "e": _vector(vector)})


def nearest_institutions(session: Session, vector: list[float], model: str, version: str, k: int) -> list[dict]:
    """The k institutions whose closest name or alias is nearest (cosine), with that label and score."""
    return _all(session, """
        SELECT best.institution_id, i.name, best.label, best.score FROM (
            SELECT DISTINCT ON (institution_id) institution_id, label,
                   round((1 - (embedding <=> CAST(:e AS vector)))::numeric, 5)::float AS score
              FROM sethu.institution_embeddings WHERE embedding_model = :m AND embedding_version = :v
             ORDER BY institution_id, embedding <=> CAST(:e AS vector)) best
          JOIN sethu.institutions i ON i.id = best.institution_id
         ORDER BY best.score DESC, i.name LIMIT :k""", e=_vector(vector), m=model, v=version, k=k)


# --- classification inputs -------------------------------------------------------------------------------

def classify_inputs(session: Session, complaint_id: UUID) -> dict:
    """The complaint's category, text, translation and glossary tags (worker only)."""
    return _all(session, """
        SELECT c.category, c.body, e.translated_text, coalesce(e.tags, '[]'::jsonb) AS tags
          FROM sethu.complaints c LEFT JOIN sethu.complaint_enrichment e ON e.complaint_id = c.id
         WHERE c.id = :c""", c=complaint_id)[0]


def corrections(session: Session, model: str, version: str) -> list[dict]:
    """Officers' latest category decision per complaint that set a category (accepted or changed), with the
    complaint's vector of this model and version."""
    return _all(session, """
        SELECT DISTINCT ON (f.complaint_id) f.complaint_id, f.new_value AS category, e.embedding::text AS vector
          FROM sethu.ai_feedback f
          JOIN sethu.complaint_embeddings e ON e.complaint_id = f.complaint_id
           AND e.embedding_model = :m AND e.embedding_version = :v
         WHERE f.kind = 'category' AND f.decision IN ('accepted', 'changed') AND f.new_value IS NOT NULL
         ORDER BY f.complaint_id, f.decided_at DESC, f.id DESC""", m=model, v=version)


# --- classifier versions -----------------------------------------------------------------------------------

def classifier_versions(session: Session) -> list[dict]:
    return _all(session, """
        SELECT v.version, v.status, v.metrics, v.embedding_model, v.embedding_version, v.sha256, v.created_at,
               v.activated_at, u.display_name AS created_by
          FROM sethu.classifier_versions v LEFT JOIN sethu.app_users u ON u.id = v.created_by
         ORDER BY v.version DESC""")


def active_classifier(session: Session) -> dict | None:
    rows = _all(session, """
        SELECT version, artifact, sha256, embedding_model, embedding_version, metrics
          FROM sethu.classifier_versions WHERE status = 'active'""")
    return rows[0] if rows else None


def classifier(session: Session, version: int) -> dict | None:
    rows = _all(session, "SELECT version, status, artifact, sha256, embedding_version, metrics "
                         "FROM sethu.classifier_versions WHERE version = :v", v=version)
    return rows[0] if rows else None


def insert_classifier(session: Session, *, artifact: dict, sha256: str, model: str, version: str, metrics: dict,
                      status: str, created_by: UUID | None) -> int:
    return session.execute(text("""
        INSERT INTO sethu.classifier_versions (version, task, format, artifact, sha256, embedding_model,
                                               embedding_version, metrics, status, created_by, activated_at)
        SELECT coalesce(max(version), 0) + 1, 'classify.category', :format, CAST(:artifact AS jsonb), :sha, :m, :v,
               CAST(:metrics AS jsonb), :status, :by, CASE WHEN :status = 'active' THEN now() END
          FROM sethu.classifier_versions RETURNING version"""),
        {"format": artifact["format"], "artifact": json.dumps(artifact), "sha": sha256, "m": model, "v": version,
         "metrics": json.dumps(metrics), "status": status, "by": created_by}).scalar_one()


def deactivate_classifiers(session: Session) -> None:
    session.execute(text("UPDATE sethu.classifier_versions SET status = 'inactive' WHERE status = 'active'"))


def activate_classifier(session: Session, version: int) -> bool:
    return session.execute(text("""
        UPDATE sethu.classifier_versions SET status = 'active', activated_at = now()
         WHERE version = :v AND status <> 'active'"""), {"v": version}).rowcount == 1
