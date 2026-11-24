"""A3 with the REAL multilingual-e5-small: accuracy, latency and peak memory for matching, institution resolution
and classification on the hand-written multilingual set and the seed. Skipped unless the model is installed
(scripts/fetch_models.py small) and the libraries are present, i.e. inside the ai-worker image:

    docker compose run --rm --no-deps -v "${PWD}/backend/tests:/app/tests:ro" -v "${PWD}/seed:/seed:ro" \\
        -e SETHU_AI_MODELS_DIR=/models -e SETHU_SEED_DIR=/seed ai-worker \\
        sh -c "pip install --user pytest && python -m pytest -m real_models -s tests/test_ai_models_a3.py"

The assertions are floors that catch a broken install, not targets; the measured numbers are printed and recorded
in docs/AI-PIPELINE.md ("A3, measured"). scripts/measure_a3.py gives the full report (every threshold).
"""
import csv
import itertools
import json
import os
import time
from pathlib import Path

import pytest

from app.ai import classify, memory
from app.ai.e5 import E5Embed
from app.core.config import get_settings
from app.modules.semantic.service import held_out

pytestmark = pytest.mark.real_models
EVAL = json.loads((Path(__file__).parent / "data/a3/eval.json").read_text(encoding="utf-8"))
MODELS = os.environ.get("SETHU_AI_MODELS_DIR", "")
SEED = Path(os.environ.get("SETHU_SEED_DIR") or Path(__file__).resolve().parents[2] / "seed")
BOOT = Path(__file__).resolve().parents[1] / "app/ai/data/category_bootstrap.jsonl"


@pytest.fixture(scope="module")
def embed():
    if not MODELS or not (Path(MODELS) / "manifest.json").exists():
        pytest.skip("no real models (set SETHU_AI_MODELS_DIR)")
    get_settings().ai_models_dir = MODELS
    memory.manager.cache_clear()
    provider = E5Embed()
    if not provider.health():
        pytest.skip("multilingual-e5-small is not installed")

    def run(texts, kind="passage"):
        import numpy as np
        return np.asarray(provider.run({"texts": list(texts), "kind": kind}).output["vectors"])
    yield run
    memory.manager().unload()


def peak_mb():
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmHWM:"):
            return round(int(line.split()[1]) / 1024, 1)
    return None


def test_cross_lingual_matching(embed):
    texts = [(s["id"], lang, s["category"], s[lang]) for s in EVAL["scenarios"] for lang in ("en", "hi", "ta")]
    started = time.perf_counter()
    v = embed([t[3] for t in texts])
    per_text = (time.perf_counter() - started) / len(texts) * 1000
    pairs = [(float(v[i] @ v[j]), a[0] == b[0]) for (i, a), (j, b) in itertools.combinations(enumerate(texts), 2)
             if a[2] == b[2]]
    threshold = 0.88                                     # ai.match.complaints.e5_threshold (migration 0016)
    tp = sum(s >= threshold and y for s, y in pairs)
    fp = sum(s >= threshold and not y for s, y in pairs)
    fn = sum(s < threshold and y for s, y in pairs)
    precision, recall = tp / max(1, tp + fp), tp / max(1, tp + fn)
    print(f"\nmatching at {threshold}: precision {precision:.3f} recall {recall:.3f} (tp {tp} fp {fp} fn {fn}); "
          f"{per_text:.1f} ms per complaint; peak {peak_mb()} MB")
    assert precision >= 0.7 and recall >= 0.8


def test_institution_resolution(embed):
    institutions = list(csv.DictReader((SEED / "institutions.csv").open(encoding="utf-8")))
    labels = [(i["permanent_id"], label) for i in institutions
              for label in (i["name"], f"{i['name']}, {i['district']}", *filter(None, i["aliases"].split("|")))]
    lv = embed([x[1] for x in labels], "query")
    names = [n for n in EVAL["institution_names"] if n["expected"]]
    started = time.perf_counter()
    nv = embed([n["raw"] for n in names], "query")
    per_name = (time.perf_counter() - started) / len(names) * 1000
    right = {}
    for n, q in zip(names, nv, strict=True):
        best = max(zip(labels, lv @ q, strict=True), key=lambda x: x[1])[0][0]
        right.setdefault(n["kind"], []).append(best == n["expected"])
    summary = {k: f"{sum(v)}/{len(v)}" for k, v in right.items()}
    print(f"\nresolution top-1 by kind {summary}; {per_name:.1f} ms per name; peak {peak_mb()} MB")
    assert sum(right["misspelt"]) / len(right["misspelt"]) >= 0.8
    assert sum(right["regional"]) / len(right["regional"]) >= 0.6


def test_classification(embed):
    rows = [json.loads(line) for line in BOOT.read_text(encoding="utf-8").splitlines() if line.strip()]
    v = embed([r["text"] for r in rows])
    train = [i for i, r in enumerate(rows) if not held_out(r)]
    hold = [i for i, r in enumerate(rows) if held_out(r)]
    artifact, metrics = classify.train(v[train], [rows[i]["category"] for i in train], v[hold],
                                       [rows[i]["category"] for i in hold], "multilingual-e5-small", "test")
    hand = [(s[lang], s["category"]) for s in EVAL["scenarios"] for lang in ("en", "hi", "ta")]
    p = classify.predict(artifact, embed([h[0] for h in hand]))
    correct = sum(artifact["classes"][int(k)] == c for k, (_, c) in zip(p.argmax(axis=1), hand, strict=True))
    print(f"\nclassification: held-out (synthetic seed) {metrics['holdout_accuracy']:.3f} of "
          f"{metrics['holdout_size']}; hand-written multilingual {correct}/{len(hand)}; peak {peak_mb()} MB")
    assert metrics["holdout_accuracy"] >= 0.85 and correct / len(hand) >= 0.6
