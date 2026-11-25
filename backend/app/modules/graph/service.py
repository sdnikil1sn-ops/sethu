"""The network-wide intelligence graph: bureaus, institutions and complaints as nodes; holding, transfer and
overlap as edges.

Aggregated by default, so it stays small however many complaints there are: one node per bureau and per
institution, a `holds` edge per bureau and institution carrying the case counts, and `transfer` edges between
bureaus with their counts. Complaint nodes appear only for the institutions asked for (`expand`), with `holds`
edges to their bureau and `overlap` edges (suggested or approved) between them; while aggregated, an
institution carries its overlap counts instead.

Metadata only: references, codes, statuses, categories, dates and counts from the summary view. Overlap links,
transfers and findings come through Row-Level Security, so a bureau sees the links and transfers of the cases
it may read. Complaint text is never part of the graph; the screen fetches a case (and its text, only where the
caller may read it) when a complaint node is opened.
"""
import time
from collections import defaultdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import router
from app.audit import service as audit
from app.core.auth import Principal
from app.modules.graph import repo

MAX_EXPANDED = 25  # institutions expanded at once; each adds its complaint nodes
RESTRICTED = "restricted record: held by another bureau; its details are not visible to you"


class GraphError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def settings(session: Session) -> dict:
    def get(key: str, default):
        return type(default)(router.setting(session, f"ai.graph.{key}", default))
    return {"node_cap": get("node_cap", 60000), "seed": get("louvain_seed", 26264),
            "resolution": get("louvain_resolution", 1.0), "max_hops": get("max_hops", 3),
            "min_edge_confidence": get("min_edge_confidence", 0.0)}


# --- A4: the scheduled build (worker, system principal) ------------------------------------------------------

def build_task(session: Session, principal: Principal, force: bool = False) -> dict:
    """Bring the edge table in step with its sources, then, if anything changed, run task graph.build through the
    router: Louvain communities (NetworkX) over the whole graph when it has at most `node_cap` nodes, else over the
    institution-bureau graph; the CTE or direct-links fallback otherwise. Safe to repeat."""
    started = time.perf_counter()
    changed = repo.refresh_edges(session)
    signature = repo.edge_signature(session)
    last = repo.latest_run(session)
    if not force and last and last["params"].get("signature") == signature:
        return {"changed": changed, "rebuilt": False, "version": last["version"]}
    s = settings(session)
    nodes = repo.node_count(session)
    capped = nodes > s["node_cap"]
    edges = repo.aggregate_edges(session) if capped else repo.full_edges(session)
    r = router.run(session, principal, "graph.build", {"edges": edges, "capped": capped, "seed": s["seed"],
                                                       "resolution": s["resolution"]},
                   subject_type="graph", subject_id=signature[:100])
    out = r["output"] if r["status"] == "ok" else {"method": "direct", "communities": None, "capped": capped,
                                                     "edges": len(edges)}
    params = {"signature": signature, "node_cap": s["node_cap"], "seed": s["seed"], "resolution": s["resolution"],
              "graph_nodes_estimate": nodes, "ms": round((time.perf_counter() - started) * 1000),
              "seconds_in_networkx": out.get("seconds")}
    version = repo.store_run(session, out, r["path"], params, r["run_id"])
    if out.get("communities"):
        repo.store_communities(session, version, out["communities"])
    audit.record(session, principal, "graph.built", entity_type="graph_runs", entity_id=str(version),
                 payload={"method": out["method"], "path": r["path"], "nodes": out.get("nodes"),
                          "edges": out.get("edges"), "communities": out.get("count"), "capped": capped,
                          "changed_edges": changed})
    return {"changed": changed, "rebuilt": True, "version": version, "method": out["method"],
            "communities": out.get("count"), "capped": capped, "nodes": out.get("nodes"), "edges": out.get("edges"),
            "ms": params["ms"], "rss_mb": out.get("rss_mb")}


def ego(session: Session, institution_id: UUID, hops: int | None, min_confidence: float | None) -> dict:
    """The institution's neighbourhood: its cases, their overlaps and the institutions those lead to, up to
    `hops` (at most ai.graph.max_hops), as the caller may see it. Recursive CTE, whatever the graph's size."""
    s = settings(session)
    hops = max(1, min(hops or 2, s["max_hops"]))
    minc = s["min_edge_confidence"] if min_confidence is None else min_confidence
    found = repo.ego(session, institution_id, hops, minc, s["node_cap"])
    ids = [r["node_id"] for r in found]
    cases = {r["id"]: r for r in repo.case_refs(session, [r["node_id"] for r in found
                                                           if r["node_type"] == "complaint"])}
    nodes = []
    for r in found:
        if r["node_type"] == "complaint":
            c = cases.get(r["node_id"])
            if c is None:
                continue
            nodes.append({"id": f"c:{c['id']}", "kind": "complaint", "label": c["ref"], "depth": r["depth"],
                          "bureau": c["bureau"], "readable": c["readable"]})
        else:
            nodes.append({"id": f"i:{r['node_id']}", "kind": "institution", "depth": r["depth"]})
    shown = {n["id"] for n in nodes}
    edges = []
    for e in repo.edges_among(session, ids, minc):
        u = repo.PREFIX[e["source_type"]] + str(e["source_id"])
        v = repo.PREFIX[e["target_type"]] + str(e["target_id"])
        if u in shown and v in shown:
            edges.append({"source": u, "target": v, "kind": e["edge_type"], "method": e["method"],
                          "confidence": e["confidence"] and float(e["confidence"]),
                          "model_version": e["model_version"]})
    return {"institution_id": institution_id, "hops": hops, "min_confidence": minc, "nodes": nodes,
            "edges": edges, "capped": len(found) >= s["node_cap"], "method": "cte"}


def _cases(session: Session, ids: list[UUID]) -> list[dict]:
    """Evidence cases: reference and summary for every one the caller may see in the summary; source and a link
    only where the caller may read the case; otherwise the restricted marker."""
    out = []
    for c in repo.case_refs(session, ids):
        item = {"id": c["id"], "ref": c["ref"], "bureau": c["bureau"], "status": c["status"],
                "filed_at": c["filed_at"], "readable": c["readable"]}
        out.append(item | ({"source": c["source"]} if c["readable"] else {"restricted": RESTRICTED}))
    return out


def explain(session: Session, source: str, target: str, kind: str) -> dict:
    """Why two nodes of the graph are linked: method, confidence, model version and the evidence cases."""
    if kind.startswith("overlap"):
        a, b = UUID(source.removeprefix("c:")), UUID(target.removeprefix("c:"))
        link = repo.overlap_edge(session, a, b)
        if link is None:                       # Row-Level Security: not a link the caller may see
            raise GraphError(404, "no such link")
        sig = link["signals"] or {}
        return {"kind": "overlap", "status": link["status"], "method": sig.get("method") or link["method"] or "text",
                "confidence": link["confidence"] and float(link["confidence"]), "model": sig.get("model"),
                "model_version": sig.get("model_version"), "similarity": sig.get("similarity"),
                "reasons": link["reasons"], "evidence": _cases(session, [a, b])}
    if kind == "holds":
        bureau, inst = source.removeprefix("b:"), UUID(target.removeprefix("i:"))
        ids = repo.holding_cases(session, inst, bureau, 50)
        return {"kind": "holds", "method": "case register (summary)", "confidence": 1.0, "model": None,
                "model_version": None, "reasons": [f"{len(ids)} case(s) about this institution held by {bureau}"],
                "evidence": _cases(session, ids)}
    if kind == "transfer":
        rows = repo.transfer_cases(session, source.removeprefix("b:"), target.removeprefix("b:"), 50)
        return {"kind": "transfer", "method": "case history (transfers)", "confidence": 1.0, "model": None,
                "model_version": None,
                "reasons": [f"{len(rows)} transfer(s) you may see, "
                            f"{sum(r['acknowledged'] == 'true' for r in rows)} acknowledged"],
                "evidence": _cases(session, [r["complaint_id"] for r in rows])}
    if kind == "about":
        cid = UUID(target.removeprefix("c:"))
        return {"kind": "about", "method": "institution resolution", "confidence": None, "model": None,
                "model_version": None, "reasons": ["the case is about this institution"],
                "evidence": _cases(session, [cid])}
    raise GraphError(422, "unknown link kind")


def meta(session: Session) -> dict | None:
    """The latest build, for the screen: version, method, sizes, when."""
    run = repo.latest_run(session)
    return run and {k: run[k] for k in ("version", "method", "path", "nodes", "edges", "communities",
                                        "modularity", "capped", "created_at")}


def build(session: Session, filters: dict, expand: list[UUID], finding_kind: str | None,
          min_confidence: float | None = None) -> dict:
    filters = {k: v for k, v in filters.items() if v not in (None, "")}
    held = repo.holdings(session, filters)
    findings = repo.open_findings(session)
    if finding_kind:
        findings = [f for f in findings if f["kind"] == finding_kind]
        marked = {f["institution_id"] for f in findings if f["institution_id"]}
        marked_bureaus = {b for f in findings if not f["institution_id"] for b in f["bureaus"]}
        held = [h for h in held if h["institution_id"] in marked or h["bureau"] in marked_bureaus]

    by_inst: dict[UUID, list[dict]] = defaultdict(list)
    for h in held:
        by_inst[h["institution_id"]].append(h)
    kinds_of_inst: dict[UUID, set[str]] = defaultdict(set)
    kinds_of_case: dict[UUID, set[str]] = defaultdict(set)
    kinds_of_bureau: dict[str, set[str]] = defaultdict(set)
    for f in findings:
        if f["complaint_id"]:
            kinds_of_case[f["complaint_id"]].add(f["kind"])
        if f["institution_id"]:
            kinds_of_inst[f["institution_id"]].add(f["kind"])
        elif f["scope"] == "bureau" or f["kind"] == "category_spike":
            for b in f["bureaus"]:
                kinds_of_bureau[b].add(f["kind"])

    links = [link for link in repo.overlaps(session) if link["institution_id"] in by_inst
             and (min_confidence is None or link["confidence"] is None or link["confidence"] >= min_confidence)]
    run = repo.latest_run(session)
    community = repo.communities_of(session, run["version"]) if run and run["communities"] else {}
    links_of_inst: dict[UUID, dict[str, int]] = defaultdict(lambda: {"proposed": 0, "approved": 0})
    for link in links:
        links_of_inst[link["institution_id"]][link["status"]] += 1

    nodes, edges = [], []
    shown_bureaus = {h["bureau"] for h in held}
    for b in repo.bureaus(session):
        if b["code"] in shown_bureaus or not (filters or finding_kind):  # narrowed: only bureaus with cases
            nodes.append({"id": f"b:{b['code']}", "kind": "bureau", "label": b["code"], "name": b["name"],
                          "cases": sum(h["cases"] for h in held if h["bureau"] == b["code"]),
                          "open": sum(h["open"] for h in held if h["bureau"] == b["code"]),
                          "findings": sorted(kinds_of_bureau[b["code"]]),
                          "community": community.get(("bureau", b["code"]))})
    for iid, rows in by_inst.items():
        nodes.append({"id": f"i:{iid}", "kind": "institution", "label": rows[0]["institution"],
                      "institution_id": str(iid), "state": rows[0]["state"],
                      "cases": sum(r["cases"] for r in rows), "open": sum(r["open"] for r in rows),
                      "overdue": sum(r["overdue"] for r in rows), "bureaus": sorted(r["bureau"] for r in rows),
                      "multi_bureau": len(rows) > 1, "expanded": iid in expand,
                      "overlaps": links_of_inst[iid], "findings": sorted(kinds_of_inst[iid]),
                      "community": community.get(("institution", str(iid)))})
        if iid not in expand:
            edges += [{"id": f"h:{r['bureau']}:{iid}", "source": f"b:{r['bureau']}", "target": f"i:{iid}",
                       "kind": "holds", "count": r["cases"]} for r in rows]

    if expand:
        shown_cases = set()
        for c in repo.complaints(session, filters, expand[:MAX_EXPANDED]):
            shown_cases.add(c["id"])
            nodes.append({"id": f"c:{c['id']}", "kind": "complaint", "label": c["ref"], "complaint_id": str(c["id"]),
                          "status": c["status"], "category": c["category"], "bureau": c["bureau"],
                          "filed_at": c["filed_at"].isoformat(), "overdue": c["overdue"],
                          "findings": sorted(kinds_of_case[c["id"]])})
            edges.append({"id": f"in:{c['id']}", "source": f"i:{c['institution_id']}", "target": f"c:{c['id']}",
                          "kind": "about", "count": 1})
            edges.append({"id": f"h:{c['id']}", "source": f"b:{c['bureau']}", "target": f"c:{c['id']}",
                          "kind": "holds", "count": 1})
        edges += [{"id": f"o:{link['complaint_a']}:{link['complaint_b']}", "source": f"c:{link['complaint_a']}",
                   "target": f"c:{link['complaint_b']}", "kind": f"overlap_{link['status']}", "count": 1,
                   "confidence": link["confidence"], "method": link["method"],
                   "model_version": link["model_version"]}
                  for link in links if link["complaint_a"] in shown_cases and link["complaint_b"] in shown_cases]

    edges += [{"id": f"t:{t['source']}:{t['target']}", "source": f"b:{t['source']}", "target": f"b:{t['target']}",
               "kind": "transfer", "count": t["n"]}
              for t in repo.transfers(session, filters) if t["source"] in shown_bureaus or t["target"] in shown_bureaus]
    ids = {n["id"] for n in nodes}
    edges = [e for e in edges if e["source"] in ids and e["target"] in ids]
    return {"nodes": nodes, "edges": edges, "expanded_limit": MAX_EXPANDED,
            "build": run and {k: run[k] for k in ("version", "method", "communities", "created_at")}}
