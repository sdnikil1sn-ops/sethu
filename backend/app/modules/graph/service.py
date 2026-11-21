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
from collections import defaultdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.graph import repo

MAX_EXPANDED = 25  # institutions expanded at once; each adds its complaint nodes


def build(session: Session, filters: dict, expand: list[UUID], finding_kind: str | None) -> dict:
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

    links = [link for link in repo.overlaps(session) if link["institution_id"] in by_inst]
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
                          "findings": sorted(kinds_of_bureau[b["code"]])})
    for iid, rows in by_inst.items():
        nodes.append({"id": f"i:{iid}", "kind": "institution", "label": rows[0]["institution"],
                      "institution_id": str(iid), "state": rows[0]["state"],
                      "cases": sum(r["cases"] for r in rows), "open": sum(r["open"] for r in rows),
                      "overdue": sum(r["overdue"] for r in rows), "bureaus": sorted(r["bureau"] for r in rows),
                      "multi_bureau": len(rows) > 1, "expanded": iid in expand,
                      "overlaps": links_of_inst[iid], "findings": sorted(kinds_of_inst[iid])})
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
                   "target": f"c:{link['complaint_b']}", "kind": f"overlap_{link['status']}", "count": 1}
                  for link in links if link["complaint_a"] in shown_cases and link["complaint_b"] in shown_cases]

    edges += [{"id": f"t:{t['source']}:{t['target']}", "source": f"b:{t['source']}", "target": f"b:{t['target']}",
               "kind": "transfer", "count": t["n"]}
              for t in repo.transfers(session, filters) if t["source"] in shown_bureaus or t["target"] in shown_bureaus]
    ids = {n["id"] for n in nodes}
    edges = [e for e in edges if e["source"] in ids and e["target"] in ids]
    return {"nodes": nodes, "edges": edges, "expanded_limit": MAX_EXPANDED}
