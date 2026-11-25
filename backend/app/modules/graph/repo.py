"""SQL for the network graph. Complaints come from sethu.complaint_summaries (metadata, every bureau, no text).
Overlap links, transfers and findings are read under Row-Level Security, so each role sees its own share."""
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

# Filter name -> SQL on the summary view `s`, its bureau `b` and institution `i`.
FILTERS = {
    "state": "i.state = :state",
    "category": "s.category = :category",
    "bureau": "b.code = upper(:bureau)",
    "filed_from": "s.filed_at >= :filed_from",
    "filed_to": "s.filed_at < CAST(:filed_to AS date) + 1",
    "institution_id": "s.institution_id = :institution_id",
}
CASES = """
      FROM sethu.complaint_summaries s
      JOIN sethu.bureaus b ON b.id = s.bureau_id
      JOIN sethu.institutions i ON i.id = s.institution_id
     WHERE {where}"""


def _all(session: Session, sql: str, **params: Any) -> list[dict]:
    return [dict(r) for r in session.execute(text(sql), params).mappings()]


def _where(filters: dict) -> str:
    return " AND ".join(FILTERS[k] for k in filters) or "true"


def holdings(session: Session, filters: dict) -> list[dict]:
    """Cases per institution and holding bureau: the aggregated graph."""
    return _all(session, f"""
        SELECT s.institution_id, i.name AS institution, i.state, b.id AS bureau_id, b.code AS bureau,
               count(*) AS cases, count(*) FILTER (WHERE s.status <> 'closed') AS open,
               count(*) FILTER (WHERE s.status <> 'closed' AND s.due_at < now()) AS overdue
        {CASES.format(where=_where(filters))}
         GROUP BY s.institution_id, i.name, i.state, b.id, b.code""", **filters)  # noqa: S608 - fixed clauses


def complaints(session: Session, filters: dict, institution_ids: list[UUID]) -> list[dict]:
    """The complaints of the expanded institutions, as summaries."""
    return _all(session, f"""
        SELECT s.id, s.ref, s.status, s.category, s.filed_at, s.institution_id, b.code AS bureau,
               s.status <> 'closed' AND s.due_at < now() AS overdue
        {CASES.format(where=_where(filters) + " AND s.institution_id = ANY(:ids)")}
         ORDER BY s.filed_at""", **filters, ids=institution_ids)  # noqa: S608 - fixed clauses


def overlaps(session: Session) -> list[dict]:
    """Suggested and approved links the caller may see (Row-Level Security on overlap_links)."""
    return _all(session, """
        SELECT l.complaint_a, l.complaint_b, l.status, sa.institution_id,
               CAST(l.signals->>'confidence' AS float) AS confidence, l.signals->>'method' AS method,
               l.signals->>'model_version' AS model_version
          FROM sethu.overlap_links l
          JOIN sethu.complaint_summaries sa ON sa.id = l.complaint_a
         WHERE l.status IN ('proposed', 'approved')""")


def transfers(session: Session, filters: dict) -> list[dict]:
    """Transfers between bureaus of the filtered cases, counted, from the history the caller may read."""
    return _all(session, f"""
        SELECT fb.code AS source, tb.code AS target, count(*) AS n
          FROM sethu.case_actions a
          JOIN sethu.bureaus fb ON fb.id = a.from_bureau_id
          JOIN sethu.bureaus tb ON tb.id = a.to_bureau_id
          JOIN sethu.complaint_summaries s ON s.id = a.complaint_id
          JOIN sethu.bureaus b ON b.id = s.bureau_id
          JOIN sethu.institutions i ON i.id = s.institution_id
         WHERE a.action = 'transferred' AND {_where(filters)}
         GROUP BY fb.code, tb.code""", **filters)  # noqa: S608 - fixed clauses


def open_findings(session: Session) -> list[dict]:
    """Open findings the caller may see (Row-Level Security on findings), with the institution of a case finding."""
    return _all(session, """
        SELECT f.kind, f.complaint_id, coalesce(f.institution_id, s.institution_id) AS institution_id,
               ARRAY(SELECT b.code FROM sethu.bureaus b WHERE b.id = ANY(f.bureau_ids)) AS bureaus,
               f.evidence->>'scope' AS scope
          FROM sethu.findings f
          LEFT JOIN sethu.complaint_summaries s ON s.id = f.complaint_id
         WHERE f.status = 'open'""")


def bureaus(session: Session) -> list[dict]:
    return _all(session, "SELECT id, code, name FROM sethu.bureaus ORDER BY code")


# --- A4: the edge table (sethu.graph_edges), kept in step with its sources, set by set -----------------------

REFRESH = [
    # complaint -> institution: how it was linked (auto or officer) and, for an AI link, its confidence and version
    """INSERT INTO sethu.graph_edges (edge_key, edge_type, source_type, source_id, target_type, target_id,
                                      complaint_id, confidence, method, model_version, evidence)
       SELECT 'about:' || c.id, 'about', 'complaint', c.id, 'institution', c.institution_id, c.id,
              CASE WHEN g.status = 'auto_linked' THEN g.confidence ELSE 1 END,
              CASE WHEN g.status = 'auto_linked' THEN 'resolve-' || coalesce(g.provider, 'ai')
                   ELSE 'resolve-' || c.resolution_state END,
              CASE WHEN g.status = 'auto_linked' THEN g.model_version END, jsonb_build_object('ref', c.ref)
         FROM sethu.complaints c
         LEFT JOIN sethu.ai_suggestions g ON g.complaint_id = c.id AND g.kind = 'institution'
        WHERE c.institution_id IS NOT NULL
       ON CONFLICT (edge_key) DO UPDATE SET target_id = EXCLUDED.target_id, confidence = EXCLUDED.confidence,
              method = EXCLUDED.method, model_version = EXCLUDED.model_version, updated_at = now()
        WHERE (sethu.graph_edges.target_id, sethu.graph_edges.method) IS DISTINCT FROM
              (EXCLUDED.target_id, EXCLUDED.method)""",
    # complaint -> the bureau holding it
    """INSERT INTO sethu.graph_edges (edge_key, edge_type, source_type, source_id, target_type, target_id,
                                      complaint_id, confidence, method, evidence)
       SELECT 'held:' || c.id, 'held_by', 'complaint', c.id, 'bureau', c.bureau_id, c.id, 1, 'register',
              jsonb_build_object('ref', c.ref)
         FROM sethu.complaints c
       ON CONFLICT (edge_key) DO UPDATE SET target_id = EXCLUDED.target_id, updated_at = now()
        WHERE sethu.graph_edges.target_id IS DISTINCT FROM EXCLUDED.target_id""",
    # institution -> bureau, one per complaint (the screen and Louvain add them up)
    """INSERT INTO sethu.graph_edges (edge_key, edge_type, source_type, source_id, target_type, target_id,
                                      complaint_id, confidence, method, evidence)
       SELECT 'handled:' || c.id, 'handled_by', 'institution', c.institution_id, 'bureau', c.bureau_id, c.id, 1,
              'register', jsonb_build_object('ref', c.ref)
         FROM sethu.complaints c WHERE c.institution_id IS NOT NULL
       ON CONFLICT (edge_key) DO UPDATE SET source_id = EXCLUDED.source_id, target_id = EXCLUDED.target_id,
              updated_at = now()
        WHERE (sethu.graph_edges.source_id, sethu.graph_edges.target_id) IS DISTINCT FROM
              (EXCLUDED.source_id, EXCLUDED.target_id)""",
    # bureau -> bureau: one per transfer action
    """INSERT INTO sethu.graph_edges (edge_key, edge_type, source_type, source_id, target_type, target_id,
                                      complaint_id, case_action_id, confidence, method, evidence)
       SELECT 'transfer:' || a.id, 'transfer', 'bureau', a.from_bureau_id, 'bureau', a.to_bureau_id,
              a.complaint_id, a.id, 1, 'case-history',
              jsonb_build_object('acknowledged', a.acknowledged_at IS NOT NULL, 'at', a.created_at)
         FROM sethu.case_actions a
        WHERE a.action = 'transferred' AND a.from_bureau_id IS NOT NULL AND a.to_bureau_id IS NOT NULL
       ON CONFLICT (edge_key) DO UPDATE SET evidence = EXCLUDED.evidence, updated_at = now()
        WHERE sethu.graph_edges.evidence IS DISTINCT FROM EXCLUDED.evidence""",
    # complaint -> complaint: suggested or approved overlaps, with A3's method, confidence and model version
    """INSERT INTO sethu.graph_edges (edge_key, edge_type, source_type, source_id, target_type, target_id,
                                      complaint_id, overlap_link_id, confidence, method, model, model_version,
                                      evidence)
       SELECT 'overlap:' || l.id, 'overlap', 'complaint', l.complaint_a, 'complaint', l.complaint_b, l.complaint_a,
              l.id, CAST(l.signals->>'confidence' AS numeric), coalesce(l.signals->>'method', 'text'),
              l.signals->>'model', l.signals->>'model_version',
              jsonb_build_object('status', l.status, 'similarity', l.signals->'similarity', 'reasons', l.reasons,
                                 'run_id', l.signals->'run_id', 'agreement', l.signals->'agreement')
         FROM sethu.overlap_links l WHERE l.status IN ('proposed', 'approved')
       ON CONFLICT (edge_key) DO UPDATE SET evidence = EXCLUDED.evidence, confidence = EXCLUDED.confidence,
              updated_at = now()
        WHERE sethu.graph_edges.evidence IS DISTINCT FROM EXCLUDED.evidence""",
    # what no longer holds: a rejected overlap, a complaint no longer linked to an institution
    """DELETE FROM sethu.graph_edges e WHERE e.edge_type = 'overlap'
          AND NOT EXISTS (SELECT 1 FROM sethu.overlap_links l
                           WHERE l.id = e.overlap_link_id AND l.status IN ('proposed', 'approved'))""",
    """DELETE FROM sethu.graph_edges e WHERE e.edge_type IN ('about', 'handled_by')
          AND NOT EXISTS (SELECT 1 FROM sethu.complaints c WHERE c.id = e.complaint_id
                             AND c.institution_id IS NOT NULL)""",
]


def refresh_edges(session: Session) -> int:
    """Bring the edge table in step with its sources (worker only). Returns the rows changed."""
    return sum(session.execute(text(sql)).rowcount for sql in REFRESH)


def edge_signature(session: Session) -> str:
    row = session.execute(text("SELECT count(*), max(updated_at) FROM sethu.graph_edges")).one()
    return f"{row[0]}:{row[1].isoformat() if row[1] else '-'}"


def node_count(session: Session) -> int:
    return session.execute(text("""
        SELECT (SELECT count(*) FROM sethu.complaints) + (SELECT count(*) FROM sethu.institutions)
               + (SELECT count(*) FROM sethu.bureaus)""")).scalar_one()


PREFIX = {"complaint": "c:", "institution": "i:", "bureau": "b:"}


def full_edges(session: Session) -> list[tuple[str, str, float]]:
    rows = session.execute(text("SELECT source_type, source_id, target_type, target_id, weight "
                                "FROM sethu.graph_edges"))
    return [(PREFIX[st] + str(s), PREFIX[tt] + str(t), float(w)) for st, s, tt, t, w in rows]


def aggregate_edges(session: Session) -> list[tuple[str, str, float]]:
    """Institution-bureau (complaints counted) and bureau-bureau (transfers counted): the graph without
    complaint nodes, for data above the node cap."""
    rows = session.execute(text("""
        SELECT 'i:' || source_id, 'b:' || target_id, count(*) FROM sethu.graph_edges
         WHERE edge_type = 'handled_by' GROUP BY source_id, target_id
        UNION ALL
        SELECT 'b:' || source_id, 'b:' || target_id, count(*) FROM sethu.graph_edges
         WHERE edge_type = 'transfer' GROUP BY source_id, target_id"""))
    return [(u, v, float(n)) for u, v, n in rows]


def store_run(session: Session, out: dict, path: str | None, params: dict, run_id: str) -> int:
    return session.execute(text("""
        INSERT INTO sethu.graph_runs (method, path, nodes, edges, communities, modularity, capped, params,
                                      duration_ms, peak_mb, ai_run_id)
        VALUES (:method, :path, :nodes, :edges, :count, :modularity, :capped, CAST(:params AS jsonb), :ms, :mb, :run)
        RETURNING version"""),
        {"method": out["method"], "path": path, "nodes": out.get("nodes") or 0, "edges": out.get("edges") or 0,
         "count": out.get("count"), "modularity": out.get("modularity"), "capped": out.get("capped", False),
         "params": json.dumps(params), "ms": params.get("ms"), "mb": out.get("rss_mb"), "run": run_id}).scalar_one()


def store_communities(session: Session, version: int, member: dict[str, int]) -> None:
    rows = [{"v": version, "t": "institution" if node.startswith("i:") else "bureau", "n": node[2:], "c": c}
            for node, c in member.items()]
    if rows:
        session.execute(text("INSERT INTO sethu.graph_communities (version, node_type, node_id, community) "
                             "VALUES (:v, :t, :n, :c)"), rows)


def latest_run(session: Session) -> dict | None:
    rows = _all(session, """SELECT version, method, path, nodes, edges, communities, modularity, capped, params,
                                   duration_ms, peak_mb, created_at
                              FROM sethu.graph_runs ORDER BY version DESC LIMIT 1""")
    return rows[0] if rows else None


def communities_of(session: Session, version: int) -> dict[tuple[str, str], int]:
    """(node_type, node_id) -> community, institutions by id and bureaus by code."""
    return {(r["node_type"], r["key"]): r["community"] for r in _all(session, """
        SELECT g.node_type, coalesce(b.code, g.node_id::text) AS key, g.community
          FROM sethu.graph_communities g LEFT JOIN sethu.bureaus b ON g.node_type = 'bureau' AND b.id = g.node_id
         WHERE g.version = :v""", v=version)}


def ego(session: Session, institution_id: UUID, hops: int, min_confidence: float, cap: int) -> list[dict]:
    """Nodes within `hops` of an institution, walking only `about` and `overlap` edges (bureaus are hubs: going
    through them would reach a whole bureau). Recursive CTE under the caller's Row-Level Security: the fallback
    and the way large graphs are explored."""
    return _all(session, """
        WITH RECURSIVE walk(node_type, node_id, depth) AS (
            SELECT 'institution'::text, CAST(:start AS uuid), 0
            UNION
            SELECT CASE WHEN e.source_id = w.node_id THEN e.target_type ELSE e.source_type END,
                   CASE WHEN e.source_id = w.node_id THEN e.target_id ELSE e.source_id END, w.depth + 1
              FROM walk w JOIN sethu.graph_edges e
                ON e.edge_type IN ('about', 'overlap')
               AND ((e.source_type = w.node_type AND e.source_id = w.node_id)
                    OR (e.target_type = w.node_type AND e.target_id = w.node_id))
             WHERE w.depth < :hops AND coalesce(e.confidence, 1) >= :minc)
        SELECT node_type, node_id, min(depth) AS depth FROM walk GROUP BY node_type, node_id
         ORDER BY min(depth), node_type, node_id LIMIT :cap""",
                start=institution_id, hops=hops, minc=min_confidence, cap=cap)


def edges_among(session: Session, ids: list[UUID], min_confidence: float) -> list[dict]:
    return _all(session, """
        SELECT edge_type, source_type, source_id, target_type, target_id, confidence, method, model_version
          FROM sethu.graph_edges
         WHERE edge_type IN ('about', 'overlap') AND source_id = ANY(:ids) AND target_id = ANY(:ids)
           AND coalesce(confidence, 1) >= :minc""", ids=ids, minc=min_confidence)


def case_refs(session: Session, ids: list[UUID]) -> list[dict]:
    """Summary fields of these cases, whether the caller may read the case itself (its text and history), and its
    source channel only when the caller may."""
    return _all(session, """
        SELECT s.id, s.ref, b.code AS bureau, s.status, s.category, s.filed_at,
               c.id IS NOT NULL AS readable, c.source
          FROM sethu.complaint_summaries s JOIN sethu.bureaus b ON b.id = s.bureau_id
          LEFT JOIN sethu.complaints c ON c.id = s.id
         WHERE s.id = ANY(:ids) ORDER BY s.ref""", ids=ids)


def overlap_edge(session: Session, a: UUID, b: UUID) -> dict | None:
    rows = _all(session, """
        SELECT l.id, l.status, l.score, l.reasons, l.signals, e.confidence, e.method, e.model, e.model_version
          FROM sethu.overlap_links l
          LEFT JOIN sethu.graph_edges e ON e.overlap_link_id = l.id
         WHERE (l.complaint_a, l.complaint_b) IN ((:a, :b), (:b, :a))""", a=a, b=b)
    return rows[0] if rows else None


def holding_cases(session: Session, institution_id: UUID, bureau: str, limit: int) -> list[UUID]:
    return [r["id"] for r in _all(session, """
        SELECT s.id FROM sethu.complaint_summaries s JOIN sethu.bureaus b ON b.id = s.bureau_id
         WHERE s.institution_id = :i AND b.code = upper(:b) ORDER BY s.filed_at DESC LIMIT :n""",
        i=institution_id, b=bureau, n=limit)]


def transfer_cases(session: Session, source: str, target: str, limit: int) -> list[dict]:
    """Transfers between two bureaus the caller may see (Row-Level Security on case_actions via the edge)."""
    return _all(session, """
        SELECT e.complaint_id, e.evidence->>'acknowledged' AS acknowledged, e.evidence->>'at' AS at
          FROM sethu.graph_edges e
          JOIN sethu.bureaus fb ON fb.id = e.source_id JOIN sethu.bureaus tb ON tb.id = e.target_id
         WHERE e.edge_type = 'transfer' AND fb.code = upper(:s) AND tb.code = upper(:t)
         ORDER BY e.evidence->>'at' DESC LIMIT :n""", s=source, t=target, n=limit)
