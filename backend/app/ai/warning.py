"""National early warning (task "warning.detect"): DBSCAN over place and time -> weekly Z-score -> baseline ratio.

Each provider gets the same payload: complaints of the recent and baseline windows (id, category group, state,
days ago, bureau) and the state centroids, and returns signals of one shape (group, states, window, members,
score, explanation). They are labelled "Emerging signal: requires verification": a comparison with the past,
not a forecast.

dbscan  Complaints of the last `recent_days` per category group as points: place from the state's centroid
        (bundled table from the map data, app/ai/data/state_centroids.json), time from the filing day, scaled so
        `km_per_unit` kilometres and `days_per_unit` days are one unit; DBSCAN with `eps` and `min_samples`.
        A cluster becomes a signal when it has at least `min_members` complaints and the baseline would explain
        at most `max_baseline_share` of them (the same states and group, `baseline_days` before, scaled to the
        cluster's window): normal volume in a big state is dense too and must not count.
zscore  Per state and category group: weekly counts over the baseline give a mean and a standard deviation;
        the recent window's count against mean x weeks, with the deviation floored at `z_sd_floor` per week so a
        quiet baseline (all zeros) cannot make a huge score. A signal needs `z_min_count` complaints and z of at
        least `z_threshold`.
ratio   The rule used before A4 (app/modules/findings): recent count at least `ratio_min_count` and at least
        `ratio_threshold` times the baseline scaled to the recent window.

DBSCAN is written here with numpy: scikit-learn would add about 194 MB (with SciPy) to the image for one
algorithm (measured, docs/AI-PIPELINE.md).
"""
import json
import math
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from app.ai.providers import NotApplicable, Provider, Result

LABEL = "Emerging signal: requires verification"
CENTROIDS = Path(__file__).parent / "data/state_centroids.json"
EARTH_KM = 6371.0
ALIASES = {"jammu and kashmir": "Jammu & Kashmir", "andaman and nicobar islands": "Andaman & Nicobar",
           "andaman and nicobar": "Andaman & Nicobar", "nct of delhi": "Delhi", "orissa": "Odisha",
           "pondicherry": "Puducherry", "uttaranchal": "Uttarakhand"}


@lru_cache
def centroids() -> dict[str, tuple[float, float]]:
    found = json.loads(CENTROIDS.read_text(encoding="utf-8"))["centroids"]
    return {k: (v[0], v[1]) for k, v in found.items()}


def state_key(name: str | None) -> str | None:
    """The centroid table's name for a state as complaints spell it (None when unknown)."""
    if not name:
        return None
    table = centroids()
    clean = " ".join(name.split())
    if clean in table:
        return clean
    low = clean.lower().replace("&", "and")
    return ALIASES.get(low) or next((k for k in table if k.lower().replace("&", "and") == low), None)


def dbscan(points, eps: float, min_samples: int) -> list[int]:
    """Labels per point: a cluster number from 0, or -1 for noise. Plain DBSCAN (Ester et al. 1996): a core point
    has at least `min_samples` points (itself included) within `eps`; clusters grow from core points."""
    import numpy as np
    n = len(points)
    labels = [-1] * n
    if n == 0:
        return labels
    x = np.asarray(points, dtype=float).reshape(n, -1)
    neighbours = []
    for start in range(0, n, 512):          # block by block: memory stays at 512 x n distances, not n x n
        d2 = ((x[start:start + 512, None, :] - x[None, :, :]) ** 2).sum(axis=2)
        neighbours += [np.flatnonzero(row <= eps * eps) for row in d2]
    core = [len(nb) >= min_samples for nb in neighbours]
    cluster = 0
    for i in range(n):
        if labels[i] != -1 or not core[i]:
            continue
        labels[i] = cluster
        stack = list(neighbours[i])
        while stack:
            j = int(stack.pop())
            if labels[j] == -1:
                labels[j] = cluster
                if core[j]:
                    stack.extend(int(k) for k in neighbours[j] if labels[k] == -1)
        cluster += 1
    return labels


def _project(lat: float, lon: float, lat0: float, lon0: float) -> tuple[float, float]:
    """Kilometres east and north of (lat0, lon0): equirectangular, good to a few per cent across India."""
    return (math.radians(lon - lon0) * EARTH_KM * math.cos(math.radians((lat + lat0) / 2)),
            math.radians(lat - lat0) * EARTH_KM)


def _signal(method: str, group: str, rows: list[dict], score: float, explanation: dict, params: dict) -> dict:
    days = [r["days_ago"] for r in rows]
    return {"method": method, "category_group": group, "categories": sorted({r["category"] for r in rows}),
            "states": sorted({r["state"] for r in rows}), "window_days_ago": [max(days), min(days)],
            "complaint_ids": [str(r["id"]) for r in sorted(rows, key=lambda r: (r["days_ago"], str(r["id"])))],
            "bureau_ids": sorted({str(r["bureau_id"]) for r in rows}), "members": len(rows),
            "score": round(score, 3), "explanation": explanation | {"label": LABEL}, "parameters": params}


def _split(payload: dict):
    recent_days = payload["settings"]["recent_days"]
    recent = [r for r in payload["complaints"] if r["days_ago"] < recent_days]
    baseline = [r for r in payload["complaints"] if recent_days <= r["days_ago"] < recent_days
                + payload["settings"]["baseline_days"]]
    return recent, baseline


class DBSCANWarning(Provider):
    name = "warning-dbscan"

    def run(self, payload: dict) -> Result:
        s = payload["settings"]
        params = {k: s[k] for k in ("km_per_unit", "days_per_unit", "eps", "min_samples", "min_members",
                                    "max_baseline_share", "recent_days", "baseline_days")}
        recent, baseline = _split(payload)
        located = [r for r in recent if state_key(r["state"])]
        if len(located) < s["min_samples"]:
            raise NotApplicable(f"only {len(located)} located complaints in the recent window")
        if len(located) > s["max_points"]:      # neighbour lists grow with the square of a dense group
            raise NotApplicable(f"{len(located)} recent complaints: above max_points {s['max_points']}")
        table = centroids()
        lat0 = sum(v[0] for v in table.values()) / len(table)
        lon0 = sum(v[1] for v in table.values()) / len(table)
        base = defaultdict(int)
        for r in baseline:
            base[(r["group"], r["state"])] += 1
        signals = []
        by_group: dict[str, list[dict]] = defaultdict(list)
        for r in located:
            by_group[r["group"]].append(r)
        for group, rows in sorted(by_group.items()):
            pts = []
            for r in rows:
                east, north = _project(*table[state_key(r["state"])], lat0, lon0)
                pts.append((east / s["km_per_unit"], north / s["km_per_unit"], r["days_ago"] / s["days_per_unit"]))
            labels = dbscan(pts, s["eps"], s["min_samples"])
            for c in sorted(set(labels) - {-1}):
                members = [r for r, lab in zip(rows, labels, strict=True) if lab == c]
                span = max(r["days_ago"] for r in members) - min(r["days_ago"] for r in members) + 1
                states = sorted({r["state"] for r in members})
                expected = sum(base[(group, st)] for st in states) * span / s["baseline_days"]
                if len(members) < s["min_members"] or expected > s["max_baseline_share"] * len(members):
                    continue
                signals.append(_signal("dbscan", group, members, len(members) / max(expected, 0.5), {
                    "why": f"{len(members)} complaints in {', '.join(states)} within {span} days form one dense "
                           f"cluster in place and time; the {s['baseline_days']} days before would explain "
                           f"{expected:.1f}",
                    "expected_from_baseline": round(expected, 2), "span_days": span,
                    "per_state": {st: sum(r["state"] == st for r in members) for st in states}}, params))
        return Result({"signals": signals, "method": "dbscan"}, 1.0)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("signals"), list)


class ZScoreWarning(Provider):
    name = "warning-zscore"

    def run(self, payload: dict) -> Result:
        s = payload["settings"]
        params = {k: s[k] for k in ("z_threshold", "z_min_count", "z_sd_floor", "recent_days", "baseline_days")}
        recent, baseline = _split(payload)
        weeks = max(1, s["baseline_days"] // 7)
        if not baseline:
            raise NotApplicable("no baseline complaints")
        recent_weeks = s["recent_days"] / 7
        cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for r in recent:
            cells[(r["group"], r["state"])].append(r)
        weekly: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0] * weeks)
        for r in baseline:
            w = min(weeks - 1, int((r["days_ago"] - s["recent_days"]) // 7))
            weekly[(r["group"], r["state"])][w] += 1
        signals = []
        for (group, state), rows in sorted(cells.items()):
            if len(rows) < s["z_min_count"] or not state:
                continue
            counts = weekly[(group, state)]
            mean = sum(counts) / weeks
            sd = math.sqrt(sum((c - mean) ** 2 for c in counts) / max(1, weeks - 1))
            sd_window = math.sqrt(recent_weeks) * max(sd, s["z_sd_floor"])
            expected = mean * recent_weeks
            z = (len(rows) - expected) / sd_window
            if z < s["z_threshold"]:
                continue
            signals.append(_signal("zscore", group, rows, z, {
                "why": f"{len(rows)} complaints in {state} in {s['recent_days']} days against {expected:.1f} "
                       f"expected from {weeks} baseline weeks: z = {z:.1f}",
                "expected": round(expected, 2), "weekly_mean": round(mean, 3), "weekly_sd": round(sd, 3),
                "sd_used": round(max(sd, s["z_sd_floor"]), 3), "floored": sd < s["z_sd_floor"], "z": round(z, 2)},
                params))
        return Result({"signals": signals, "method": "zscore"}, 1.0)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("signals"), list)


class RatioWarning(Provider):
    name = "warning-ratio"

    def run(self, payload: dict) -> Result:
        s = payload["settings"]
        params = {k: s[k] for k in ("ratio_threshold", "ratio_min_count", "recent_days", "baseline_days")}
        recent, baseline = _split(payload)
        base = defaultdict(int)
        for r in baseline:
            base[(r["group"], r["state"])] += 1
        cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for r in recent:
            cells[(r["group"], r["state"])].append(r)
        signals = []
        for (group, state), rows in sorted(cells.items()):
            expected = base[(group, state)] * s["recent_days"] / s["baseline_days"]
            if not state or len(rows) < s["ratio_min_count"] or (expected and len(rows) < s["ratio_threshold"]
                                                                   * expected):
                continue
            ratio = len(rows) / expected if expected else None
            signals.append(_signal("ratio", group, rows, ratio or float(len(rows)), {
                "why": f"{len(rows)} complaints in {state} in {s['recent_days']} days, "
                       + (f"{ratio:.1f} times the baseline ({expected:.1f})" if ratio else "none before"),
                "expected": round(expected, 2), "ratio": ratio and round(ratio, 2)}, params))
        return Result({"signals": signals, "method": "ratio"}, 1.0)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("signals"), list)
