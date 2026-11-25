"""Relationship graph build (task "graph.build"): NetworkX with Louvain communities -> recursive-CTE traversal ->
direct links only.

graph-networkx  An undirected weighted graph from the edge rows (sethu.graph_edges): the whole graph with
                complaints when it has at most `node_cap` nodes, else the institution-bureau graph only (each
                complaint folded into the weight between its institution and bureau; transfers between bureaus).
                Louvain (networkx.community.louvain_communities, fixed `seed`, `resolution`) gives communities;
                only institutions' and bureaus' communities are returned (never complaints').
graph-cte       No communities: the screen's N-hop links come from a recursive CTE over the same edge table
                (app/modules/graph/repo.py, ego()).
graph-direct    Direct links only (one hop).
"""
import time

from app.ai.memory import rss_mb
from app.ai.providers import Provider, Result


def build(edges: list[tuple[str, str, float]]):
    import networkx as nx
    g = nx.Graph()
    for u, v, w in edges:
        if g.has_edge(u, v):
            g[u][v]["weight"] += w
        else:
            g.add_edge(u, v, weight=w)
    return g


def communities(g, seed: int, resolution: float) -> list[set]:
    import networkx as nx
    found = nx.community.louvain_communities(g, weight="weight", resolution=resolution, seed=seed)
    # Numbered by their smallest member, so the same graph gives the same numbers on every run.
    return sorted(found, key=lambda c: min(c))


class GraphNetworkX(Provider):
    """payload {"edges": [(u, v, weight)], "capped": bool, "seed", "resolution"}; node ids "c:", "i:", "b:"."""
    name = "graph-networkx"

    def health(self) -> bool:
        try:
            import networkx  # noqa: F401
        except ImportError:
            return False
        return True

    def run(self, payload: dict) -> Result:
        import networkx as nx
        started = time.perf_counter()
        g = build(payload["edges"])
        groups = communities(g, payload["seed"], payload["resolution"]) if g.number_of_nodes() else []
        modularity = nx.community.modularity(g, groups, weight="weight") if groups and g.number_of_edges() else None
        member = {n: i for i, c in enumerate(groups) for n in c if n[:2] in ("i:", "b:")}
        return Result({"method": "louvain", "communities": member, "count": len(groups),
                       "modularity": modularity and round(modularity, 5), "nodes": g.number_of_nodes(),
                       "edges": g.number_of_edges(), "capped": payload["capped"],
                       "seconds": round(time.perf_counter() - started, 3), "rss_mb": rss_mb()}, 1.0)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("communities"), dict)


class GraphCTE(Provider):
    name = "graph-cte"

    def run(self, payload: dict) -> Result:
        return Result({"method": "cte", "communities": None, "nodes": None, "edges": len(payload["edges"]),
                       "capped": payload["capped"]}, 1.0)


class GraphDirect(Provider):
    name = "graph-direct"

    def run(self, payload: dict) -> Result:
        return Result({"method": "direct", "communities": None, "nodes": None, "edges": len(payload["edges"]),
                       "capped": payload["capped"]}, 1.0)
