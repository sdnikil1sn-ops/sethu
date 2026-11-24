"""Measure A3 with the real E5 model, offline: memory, latency, matching precision/recall at each threshold,
institution resolution accuracy, and category classification accuracy. Prints a report and writes JSON.

    docker run --rm --network none -m 3g -e PYTHONPATH=/w/backend \
        -v <repo>:/w:ro -v <folder with one .onnx and tokenizer.json>:/e5:ro \
        sethu-ai-worker python /w/scripts/measure_a3.py /e5 [/w/out.json]

Data: the seed (seed/*.csv, template-generated) and the hand-written cross-lingual set
(backend/tests/data/a3/eval.json). Both are synthetic; what the numbers do and do not show is in
docs/AI-PIPELINE.md ("A3, measured"). No text is printed, only ids, counts and numbers.
"""
import csv
import itertools
import json
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import numpy as np  # noqa: E402

from app.ai import classify  # noqa: E402
from app.ai.e5 import Encoder  # noqa: E402
from app.ai.glossary import Glossary  # noqa: E402

EVAL = json.loads((ROOT / "backend/tests/data/a3/eval.json").read_text(encoding="utf-8"))
SEED = {name: list(csv.DictReader((ROOT / f"seed/{name}.csv").open(encoding="utf-8")))
        for name in ("complaints", "institutions", "glossary")}
BOOT = [json.loads(x) for x in (ROOT / "backend/app/ai/data/category_bootstrap.jsonl").read_text("utf-8").splitlines()]


def rss() -> tuple[float, float]:
    """(current, peak) resident memory of this process in MB (Linux)."""
    found = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    return round(int(found["VmRSS"].split()[0]) / 1024, 1), round(int(found["VmHWM"].split()[0]) / 1024, 1)


def trigram(a: str, b: str) -> float:
    """pg_trgm's similarity(), near enough: words padded with two spaces in front and one behind."""
    def grams(t: str) -> set:
        out = set()
        for w in re.findall(r"\w+", t.lower()):
            w = f"  {w} "
            out |= {w[i:i + 3] for i in range(len(w) - 2)}
        return out
    x, y = grams(a), grams(b)
    return len(x & y) / len(x | y) if x | y else 0.0


def pr(scores: list[tuple[float, bool]], threshold: float) -> dict:
    tp = sum(s >= threshold and y for s, y in scores)
    fp = sum(s >= threshold and not y for s, y in scores)
    fn = sum(s < threshold and y for s, y in scores)
    return {"threshold": threshold, "precision": round(tp / (tp + fp), 3) if tp + fp else None,
            "recall": round(tp / (tp + fn), 3) if tp + fn else None, "tp": tp, "fp": fp, "fn": fn}


def main(model_dir: str, out: str | None) -> None:
    report: dict = {"model_files_mb": {p.name: round(p.stat().st_size / 1e6, 1) for p in Path(model_dir).iterdir()}}
    report["rss_before_load_mb"] = rss()[0]
    t = time.perf_counter()
    enc = Encoder(model_dir)
    report["load_seconds"] = round(time.perf_counter() - t, 2)
    report["rss_after_load_mb"] = rss()[0]

    def embed(texts, kind="passage"):
        return enc.embed(list(texts), kind)

    # --- latency ---
    sample = [c["body"] for c in SEED["complaints"][:64]]
    embed(sample[:4])
    t = time.perf_counter()
    for text in sample[:32]:
        embed([text])
    report["latency_ms_per_complaint_single"] = round((time.perf_counter() - t) / 32 * 1000, 1)
    t = time.perf_counter()
    embed(sample)
    report["latency_ms_per_complaint_batch16"] = round((time.perf_counter() - t) / len(sample) * 1000, 1)
    names = [i["name"] for i in SEED["institutions"]]
    t = time.perf_counter()
    for n in names[:20]:
        embed([n], "query")
    report["latency_ms_per_name"] = round((time.perf_counter() - t) / 20 * 1000, 1)

    # --- matching: the cross-lingual set ---
    sc = EVAL["scenarios"]
    texts = [(s["id"], lang, s["category"], s[lang]) for s in sc for lang in ("en", "hi", "ta")]
    v = embed([x[3] for x in texts])
    cross: list[tuple[float, bool, str, float]] = []      # (cosine, same matter, language pair, trigram)
    for (i, a), (j, b) in itertools.combinations(enumerate(texts), 2):
        if a[2] != b[2]:
            continue                                         # the rules only compare cases in one category
        cross.append((float(v[i] @ v[j]), a[0] == b[0], "-".join(sorted((a[1], b[1]))), trigram(a[3], b[3])))
    # --- matching: the seed (template paraphrases; hard negatives share a template) ---
    comp = SEED["complaints"]
    cv = embed([c["body"] for c in comp])
    pairs = {}
    for c in comp:
        for tag in c["seed_tags"].split(";"):
            if tag.startswith("tier2:"):
                pairs.setdefault(tag, []).append(comp.index(c))
    positive = {tuple(sorted(x)) for x in pairs.values() if len(x) == 2}
    seed_scores = []
    for i, j in itertools.combinations(range(len(comp)), 2):
        if comp[i]["category"] == comp[j]["category"] and comp[i]["body"] != comp[j]["body"]:
            seed_scores.append((float(cv[i] @ cv[j]), (i, j) in positive, trigram(comp[i]["body"], comp[j]["body"])))
    grid = [round(0.78 + k / 100, 2) for k in range(19)]
    report["match"] = {
        "cross_lingual_pairs": len(cross), "cross_lingual_positive": sum(y for _, y, _, _ in cross),
        "seed_pairs": len(seed_scores), "seed_positive": sum(y for _, y, _ in seed_scores),
        "cross_lingual": [pr([(s, y) for s, y, _, _ in cross], t) for t in grid],
        "seed": [pr([(s, y) for s, y, _ in seed_scores], t) for t in grid],
        "by_language_pair": {},
        "trigram_cross_lingual_at_0.30": pr([(g, y) for _, y, _, g in cross], 0.30),
        "trigram_seed_at_0.30": pr([(g, y) for _, y, g in seed_scores], 0.30),
    }
    # Seed pairs inside the overlap rules (same institution and category, different bureaus, both open, <= 30 days)
    inside = [(float(cv[i] @ cv[j]), (i, j) in positive) for i, j in itertools.combinations(range(len(comp)), 2)
              if comp[i]["institution_pid"] == comp[j]["institution_pid"] and comp[i]["category"] == comp[j]["category"]
              and comp[i]["bureau"] != comp[j]["bureau"] and "closed" not in (comp[i]["status"], comp[j]["status"])
              and abs(int(comp[i]["filed_days_ago"]) - int(comp[j]["filed_days_ago"])) <= 30]
    report["match"]["seed_inside_rules"] = {"pairs": len(inside), "positive": sum(y for _, y in inside),
                                            "cosines": sorted(round(s, 3) for s, _ in inside)}
    # The whole chain as the router runs it: e5-match -> text-match (same language only) -> officer.
    from app.ai.providers import NotApplicable
    from app.ai.semantic import E5Match, TextMatch

    def chain(cos: float, tri: float, same: bool, settings: dict) -> tuple[bool, str]:
        payload = {"pair": {"semantic": cos, "trigram": tri, "same_language": same}, "settings": settings}
        for provider in (E5Match(), TextMatch()):
            try:
                r = provider.run(payload)
            except NotApplicable:
                continue
            if r.confidence >= 0.5:
                return r.output["matched"], r.output["method"]
        return cos >= settings["e5_threshold"] or tri >= settings["trigram_threshold"], "officer"

    report["match"]["chain"] = []
    for th in (0.86, 0.87, 0.88, 0.89, 0.90):
        st = {"e5_threshold": th, "trigram_threshold": 0.30, "confidence_span": 0.06, "agreement_bonus": 0.15,
              "disagreement_penalty": 0.25}
        decided = [(chain(s, g, lp.split("-")[0] == lp.split("-")[1], st), y, lp) for s, y, lp, g in cross]
        tp = sum(m and y for (m, _), y, _ in decided)
        fp = sum(m and not y for (m, _), y, _ in decided)
        fn = sum(not m and y for (m, _), y, _ in decided)
        report["match"]["chain"].append({
            "threshold": th, "precision": round(tp / (tp + fp), 3) if tp + fp else None,
            "recall": round(tp / (tp + fn), 3), "tp": tp, "fp": fp, "fn": fn,
            "by_method": {m: sum(meth == m for (_, meth), _, _ in decided) for m in ("e5", "text", "officer")},
            "fn_by_language_pair": {lp: sum(not m and y and p == lp for (m, _), y, p in decided)
                                    for lp in sorted({x[2] for x in cross})},
            "fp_by_language_pair": {lp: sum(m and not y and p == lp for (m, _), y, p in decided)
                                    for lp in sorted({x[2] for x in cross})}})
    for lp in sorted({x[2] for x in cross}):
        pos = [s for s, y, p, _ in cross if p == lp and y]
        neg = [s for s, y, p, _ in cross if p == lp and not y]
        report["match"]["by_language_pair"][lp] = {
            "positive_min": round(min(pos), 3) if pos else None, "positive_mean": round(float(np.mean(pos)), 3)
            if pos else None, "negative_max": round(max(neg), 3) if neg else None,
            "negative_mean": round(float(np.mean(neg)), 3) if neg else None}

    # --- institution resolution ---
    from app.modules.institutions.service import ABBREVIATIONS, normalize  # pure functions
    labels = []
    for inst in SEED["institutions"]:
        labels += [(inst["permanent_id"], inst["name"]), (inst["permanent_id"], f"{inst['name']}, {inst['district']}")]
        labels += [(inst["permanent_id"], a) for a in inst["aliases"].split("|") if a]
    lv = embed([x[1] for x in labels], "query")
    names_eval = EVAL["institution_names"]
    nv = embed([n["raw"] for n in names_eval], "query")
    rows = []
    for n, q in zip(names_eval, nv, strict=True):
        sims: dict[str, float] = {}
        for (pid, _), vec in zip(labels, lv, strict=True):
            sims[pid] = max(sims.get(pid, -1.0), float(q @ vec))
        ranked = sorted(sims.items(), key=lambda kv: -kv[1])
        exact = {pid for pid, label in labels if normalize(label) == normalize(n["raw"])}
        fuzzy: dict[str, float] = {}
        for pid, label in labels:
            fuzzy[pid] = max(fuzzy.get(pid, 0), SequenceMatcher(None, normalize(n["raw"]), normalize(label)).ratio())
        fr = sorted(fuzzy.items(), key=lambda kv: -kv[1])
        first = n["raw"].strip().partition(" ")[0].strip(".,")
        rows.append({"kind": n["kind"], "expected": n["expected"], "top": ranked[0][0], "score": ranked[0][1],
                     "lead": ranked[0][1] - ranked[1][1], "top3": [p for p, _ in ranked[:3]],
                     "exact": sorted(exact), "fuzzy_top": fr[0][0], "fuzzy_score": fr[0][1] * 100,
                     "fuzzy_lead": (fr[0][1] - fr[1][1]) * 100,
                     "acronym": first.isalpha() and first.isupper() and 2 <= len(first) <= 6})
    assert ABBREVIATIONS                                     # the deterministic steps are the real ones
    res: dict = {"names": len(rows), "by_kind": {}, "rules": []}
    for kind in sorted({r["kind"] for r in rows}):
        rk = [r for r in rows if r["kind"] == kind]
        known = [r for r in rk if r["expected"]]
        res["by_kind"][kind] = {
            "n": len(rk), "e5_top1": sum(r["top"] == r["expected"] for r in known),
            "e5_top3": sum(r["expected"] in r["top3"] for r in known),
            "fuzzy_top1": sum(r["fuzzy_top"] == r["expected"] for r in known),
            "exact_step": sum(len(r["exact"]) == 1 for r in rk),
            "score_min_correct": round(min((r["score"] for r in known if r["top"] == r["expected"]), default=0), 3),
            "score_max": round(max(r["score"] for r in rk), 3)}
    for threshold, margin in itertools.product([0.88, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95], [0.01, 0.02, 0.03, 0.05]):
        auto = [r for r in rows if not r["acronym"] and r["score"] >= threshold and r["lead"] >= margin]
        right = sum(r["top"] == r["expected"] for r in auto)
        res["rules"].append({"threshold": threshold, "margin": margin, "auto_linked": len(auto), "auto_correct": right,
                             "auto_wrong": len(auto) - right,
                             "auto_unknown": sum(r["expected"] is None for r in auto),
                             "auto_by_kind": {k: sum(r["kind"] == k for r in auto) for k in res["by_kind"]}})
    # The chain as shipped: exact/abbreviation -> E5 (auto at 0.93, lead 0.03) -> fuzzy (95, 5) -> officer queue.
    outcome = []
    for r in rows:
        if len(r["exact"]) == 1:
            outcome.append(("exact", r["exact"][0] == r["expected"], r))
        elif not r["acronym"] and r["score"] >= 0.93 and r["lead"] >= 0.03:
            outcome.append(("e5", r["top"] == r["expected"], r))
        else:
            outcome.append(("queue", r["expected"] is None or r["expected"] in r["top3"], r))
    res["chain_0.93_0.03"] = {
        "auto_linked": sum(o != "queue" for o, _, _ in outcome),
        "auto_wrong": sum(o != "queue" and not ok for o, ok, _ in outcome),
        "queued": sum(o == "queue" for o, _, _ in outcome),
        "queued_with_right_in_top3": sum(o == "queue" and ok and r["expected"] is not None for o, ok, r in outcome),
        "queued_unknown": sum(o == "queue" and r["expected"] is None for o, _, r in outcome),
        "by_kind": {k: {o: sum(oo == o and r["kind"] == k for oo, _, r in outcome) for o in ("exact", "e5", "queue")}
                    for k in res["by_kind"]}}
    fuzzy_auto = [r for r in rows if not r["acronym"] and r["fuzzy_score"] >= 95 and r["fuzzy_lead"] >= 5]
    res["fuzzy_auto_95_5"] = {"auto_linked": len(fuzzy_auto),
                              "auto_correct": sum(r["fuzzy_top"] == r["expected"] for r in fuzzy_auto)}
    report["resolve"] = res

    # --- classification ---
    import hashlib

    def held(text: str) -> bool:
        return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16) % 5 == 0

    bv = embed([b["text"] for b in BOOT])
    tr = [i for i, b in enumerate(BOOT) if not held(b["text"])]
    ho = [i for i, b in enumerate(BOOT) if held(b["text"])]
    t = time.perf_counter()
    artifact, metrics = classify.train(bv[tr], [BOOT[i]["category"] for i in tr], bv[ho],
                                       [BOOT[i]["category"] for i in ho], "multilingual-e5-small", "measure")
    train_s = round(time.perf_counter() - t, 2)
    sc_texts = [(s[lang], s["category"], lang) for s in sc for lang in ("en", "hi", "ta")]
    p = classify.predict(artifact, embed([x[0] for x in sc_texts]))
    picked = [artifact["classes"][i] for i in p.argmax(axis=1)]
    glossary = Glossary([(g["term"], g["english"]) for g in SEED["glossary"]], 1)
    rules_pick = []
    for text_, _, _ in sc_texts:
        scores = classify.rule_scores(text_, glossary.tag(text_)["tags"])
        best = max(scores.items(), key=lambda kv: kv[1])
        rules_pick.append(best[0] if best[1] else None)
    # The chain: the model if its calibrated probability >= 0.6, else the rules if theirs >= 0.6, else an officer.
    from app.ai.classify import CategoryRules
    chain_pick = []
    for k, (text_, _, _) in enumerate(sc_texts):
        if p[k].max() >= 0.6:
            chain_pick.append(("model", artifact["classes"][int(p[k].argmax())]))
            continue
        try:
            rr = CategoryRules().run({"text": text_, "tags": glossary.tag(text_)["tags"]})
            chain_pick.append(("rules", rr.output["category"]) if rr.confidence >= 0.6 else ("officer", None))
        except NotApplicable:
            chain_pick.append(("officer", None))
    report["classify_chain"] = {lang: {
        "n": sum(lg == lang for _, _, lg in sc_texts),
        **{f"{path}_answered": sum(pp == path and lg == lang for (pp, _), (_, _, lg) in zip(chain_pick, sc_texts,
                                                                                             strict=True))
           for path in ("model", "rules", "officer")},
        "answered_correct": sum(c == cat and lg == lang for (_, c), (_, cat, lg) in zip(chain_pick, sc_texts,
                                                                                         strict=True))}
        for lang in ("en", "hi", "ta")}
    report["classify_errors"] = [{"category": cat, "picked": pk, "lang": lg}
                                 for pk, (_, cat, lg) in zip(picked, sc_texts, strict=True) if pk != cat]
    report["classify"] = {
        "train_seconds": train_s, "bootstrap": len(BOOT), "train": len(tr), "holdout": len(ho), **metrics,
        "temperature": artifact["temperature"],
        "artifact_kb": round(len(json.dumps(artifact)) / 1024, 1),
        "handwritten_by_language": {lang: {
            "model_correct": sum(pk == c for pk, (_, c, lg) in zip(picked, sc_texts, strict=True) if lg == lang),
            "rules_correct": sum(rp == c for rp, (_, c, lg) in zip(rules_pick, sc_texts, strict=True) if lg == lang),
            "rules_no_answer": sum(rp is None for rp, (_, _, lg) in zip(rules_pick, sc_texts, strict=True)
                                   if lg == lang),
            "n": sum(lg == lang for _, _, lg in sc_texts),
            "model_mean_confidence": round(float(np.mean([p[k].max() for k, x in enumerate(sc_texts)
                                                          if x[2] == lang])), 3)} for lang in ("en", "hi", "ta")}}
    report["rss_peak_mb"] = rss()[1]
    report["rss_end_mb"] = rss()[0]
    text_out = json.dumps(report, indent=1, default=lambda o: o.item())    # numpy scalars
    if out:
        Path(out).write_text(text_out)
    print(text_out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
