"""Bottleneck detection (task "bottleneck.detect"): a workflow graph -> the rules used before A4 -> the overdue list.

workflow-graph  Every case's path through SETHU as a series of stints at a node: a bureau and a stage, "queue"
                (waiting for a person to be assigned) or "desk" (with an officer). Filing opens a stint in the
                bureau's queue; assignment moves it to the desk; a transfer to the other bureau's queue; closing
                ends it. Per node: stints, mean dwell days, SLA breach rate (stints during which the case passed
                its deadline), queue size (stints still open) and betweenness centrality (NetworkX, how much of the
                flow between other nodes passes through it). A node is a bottleneck with at least `min_cases`
                stints, mean dwell of `min_dwell_days` or more and a breach rate above `min_breach_rate`. A
                handoff cycle between bureaus (A -> B -> A, up to four bureaus) followed by `loop_min_cases` cases
                or more is a repeated loop. The rules' own findings (per-case loops and stalls, queue shares) are
                kept and get the graph's numbers as explanation.
bottleneck-rules  The rules' findings as they are (app/modules/findings).
A person        Nothing detected automatically: the overdue list (deadline findings) still stands.

Findings keep their structure (kind, key, bureaus, evidence) and alert path; evidence gains `explanation`,
`method` and `path`.
"""
from collections import defaultdict
from datetime import datetime

from app.ai.providers import Provider, Result

STAGE = {"queue": "waiting to be assigned", "desk": "with an officer"}


def stints(actions: list[dict], cases: dict, now: datetime) -> list[dict]:
    """One row per stay of a case at a (bureau, stage) node, in order. `actions` sorted by case, then time."""
    by_case: dict = defaultdict(list)
    for a in actions:
        by_case[a["complaint_id"]].append(a)
    out = []
    for cid, acts in by_case.items():
        case = cases.get(cid)
        if case is None or not acts:
            continue
        first_transfer = next((a for a in acts if a["action"] == "transferred"), None)
        bureau = first_transfer["from_bureau_id"] if first_transfer else case["bureau_id"]
        node, enter, step = (bureau, "queue"), acts[0]["created_at"], []
        for a in acts[1:]:
            move = None
            if a["action"] in ("assigned", "reopened"):
                move = (bureau, "desk")
            elif a["action"] == "transferred" and a["to_bureau_id"]:
                bureau = a["to_bureau_id"]
                move = (bureau, "queue")
            elif a["action"] == "closed":
                move = ("closed", "closed")
            if move and move != node:
                step.append({"node": node, "enter": enter, "exit": a["created_at"], "next": move, "case": cid})
                node, enter = move, a["created_at"]
        if node[0] != "closed":
            step.append({"node": node, "enter": enter, "exit": None, "next": None, "case": cid})
        for s in step:
            exit_at = s["exit"] or now
            s["dwell"] = max(0.0, (exit_at - s["enter"]).total_seconds() / 86400)
            s["breach"] = s["enter"] <= case["due_at"] < exit_at
        out += step
    return out


def transfer_paths(actions: list[dict]) -> dict:
    """Per case, the bureaus it was transferred through, in order (A, B, A, ...)."""
    paths: dict = defaultdict(list)
    for a in actions:
        if a["action"] == "transferred" and a["from_bureau_id"] and a["to_bureau_id"]:
            p = paths[a["complaint_id"]]
            if not p:
                p.append(a["from_bureau_id"])
            p.append(a["to_bureau_id"])
    return paths


def _explain(finding: dict, method: str, path: str, why: str | None = None) -> dict:
    ev = dict(finding["evidence"])
    ev |= {"method": method, "path": path}
    ev.setdefault("explanation", why or {
        "transfer_loop": "the case went back to a bureau it had left, with no transfer acknowledged",
        "stalled_transfer": "a transfer nobody has acknowledged",
        "bottleneck": "too large a share of this queue is overdue or older than the bureau's usual time to close",
    }.get(finding["kind"], "rule"))
    return finding | {"evidence": ev}


class BottleneckRules(Provider):
    """payload {"rule_findings"}: the rules' findings, explained."""
    name = "bottleneck-rules"

    def run(self, payload: dict) -> Result:
        return Result({"findings": [_explain(f, "rules", "fallback") for f in payload["rule_findings"]],
                       "method": "rules"}, 1.0)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("findings"), list)


class WorkflowGraph(Provider):
    """payload {"actions", "cases", "codes", "rule_findings", "settings", "now"}."""
    name = "workflow-graph"

    def health(self) -> bool:
        try:
            import networkx  # noqa: F401
        except ImportError:
            return False
        return True

    def run(self, payload: dict) -> Result:
        import networkx as nx
        s, codes, now = payload["settings"], payload["codes"], payload["now"]
        rows = stints(payload["actions"], payload["cases"], now)
        g = nx.DiGraph()
        metrics: dict = defaultdict(lambda: {"stints": 0, "dwell": 0.0, "breach": 0, "open": 0})
        for r in rows:
            m = metrics[r["node"]]
            m["stints"] += 1
            m["dwell"] += r["dwell"]
            m["breach"] += r["breach"]
            m["open"] += r["exit"] is None
            g.add_node(r["node"])
            if r["next"]:
                w = g.get_edge_data(r["node"], r["next"], {"weight": 0})["weight"]
                g.add_edge(r["node"], r["next"], weight=w + 1)
        between = nx.betweenness_centrality(g, normalized=True) if g.number_of_nodes() > 2 else {}
        findings = [_explain(f, "workflow-graph", "primary") for f in payload["rule_findings"]]
        graph_nodes = []
        for node, m in sorted(metrics.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
            if node[0] == "closed":
                continue
            dwell = m["dwell"] / m["stints"]
            rate = m["breach"] / m["stints"]
            name = f"{codes.get(node[0], '?')} {STAGE[node[1]]}"
            info = {"node": name, "stints": m["stints"], "mean_dwell_days": round(dwell, 1),
                    "breach_rate": round(rate, 2), "queue": m["open"],
                    "betweenness": round(between.get(node, 0.0), 3)}
            graph_nodes.append(info)
            if m["stints"] >= s["min_cases"] and dwell >= s["min_dwell_days"] and rate > s["min_breach_rate"]:
                findings.append({
                    "kind": "bottleneck", "key": f"bottleneck:workflow:{node[0]}:{node[1]}", "complaint_id": None,
                    "institution_id": None, "bureau_ids": [node[0]],
                    "evidence": info | {
                        "scope": "workflow", "share": round(rate, 2), "open": m["open"],
                        "thresholds": {k: s[k] for k in ("min_cases", "min_dwell_days", "min_breach_rate")},
                        "explanation": f"{name}: cases stay {dwell:.0f} days on average and {rate:.0%} of them pass "
                                       f"their deadline here; {m['open']} are waiting now; betweenness "
                                       f"{info['betweenness']:.2f}", "method": "workflow-graph", "path": "primary"}})
        # Repeated handoff loops between bureaus.
        paths = transfer_paths(payload["actions"])
        tg = nx.DiGraph()
        for p in paths.values():
            tg.add_edges_from(zip(p, p[1:], strict=False))
        for cycle in nx.simple_cycles(tg, length_bound=4):
            start = min(range(len(cycle)), key=lambda i: str(cycle[i]))
            cycle = cycle[start:] + cycle[:start]           # the key: the same cycle, however it was found
            seen: dict[tuple, int] = {}                     # a case may enter the loop at any of its bureaus
            cases = []
            for c, p in paths.items():
                for k in range(len(cycle)):
                    loop = cycle[k:] + cycle[:k] + [cycle[k]]
                    if any(p[i:i + len(loop)] == loop for i in range(len(p) - len(loop) + 1)):
                        cases.append(str(c))
                        seen[tuple(loop)] = seen.get(tuple(loop), 0) + 1
                        break
            cases.sort()
            if len(cases) < s["loop_min_cases"]:
                continue
            route = " -> ".join(codes.get(b, "?") for b in max(seen, key=seen.get))
            findings.append({
                "kind": "bottleneck", "key": "bottleneck:loop:" + ":".join(str(b) for b in cycle), "complaint_id": None,
                "institution_id": None, "bureau_ids": list(dict.fromkeys(cycle)),
                "evidence": {"scope": "handoff_cycle", "route": route, "cases": len(cases), "complaint_ids": cases,
                             "share": 1.0, "open": len(cases),
                             "explanation": f"{len(cases)} cases went round {route}: a repeated handoff loop",
                             "threshold": s["loop_min_cases"], "method": "workflow-graph", "path": "primary"}})
        return Result({"findings": findings, "method": "workflow-graph",
                       "graph": {"nodes": graph_nodes, "edges": g.number_of_edges()}}, 1.0)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("findings"), list)
