"""Accuracy and latency of the REAL models on the multilingual samples (AI Phase A2). Skipped unless the models are
installed (scripts/fetch_models.py) and the AI libraries are present, i.e. inside the ai-worker image:

    docker compose run --rm --no-deps -v "${PWD}/backend/tests:/app/tests:ro" -e SETHU_AI_MODELS_DIR=/models \\
        ai-worker sh -c "pip install --user pytest && python -m pytest -m real_models -s tests/test_ai_models.py"

Each task's numbers are printed (language right or wrong, OCR character error rate, seconds per call) and the
process's peak memory at the end. The assertions are floors, not targets: they catch a broken install.
"""
import json
import os
import time
from pathlib import Path

import pytest

from app.ai import memory
from app.ai.lid import FastTextLID
from app.ai.memory import rss_mb
from app.ai.ocr import RapidOCR, TesseractOCR
from app.ai.translate import IndicTrans2
from app.core.config import get_settings

pytestmark = pytest.mark.real_models
DATA = Path(__file__).parent / "data/multilingual"
SAMPLES = json.loads((DATA / "samples.json").read_text(encoding="utf-8"))["samples"]
MODELS = os.environ.get("SETHU_AI_MODELS_DIR", "")


@pytest.fixture(autouse=True)
def real_models(monkeypatch):
    if not MODELS or not (Path(MODELS) / "manifest.json").exists():
        pytest.skip("no real models (set SETHU_AI_MODELS_DIR)")
    monkeypatch.setattr(get_settings(), "ai_models_dir", MODELS)
    memory.manager.cache_clear()
    yield
    memory.manager().unload()


def edit_distance(a: str, b: str) -> int:
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, row[0] = row[0], i
        for j, cb in enumerate(b, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (ca != cb))
    return row[-1]


def cer(got: str, want: str) -> float:
    got, want = " ".join(got.split()), " ".join(want.split())
    return edit_distance(got, want) / max(1, len(want))


def peak_mb() -> float | None:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        return None
    return None


def timed(fn):
    start = time.perf_counter()
    out = fn()
    return out, round(time.perf_counter() - start, 3)


def test_language_detection_with_fasttext():
    lid = FastTextLID()
    if not lid.health():
        pytest.skip("fastText or lid-176 not installed")
    right, rows = 0, []
    for s in SAMPLES:
        if s["script"] == "Latn" and s["language"] != "en":
            continue                     # romanised Hindi: fastText's lid.176 is not trained for it
        result, secs = timed(lambda s=s: lid.run({"text": s["text"]}))
        ok = result.output["language"] == s["language"]
        right += ok
        rows.append(f"{s['id']}: {result.output['language']} ({result.confidence:.2f}) {'ok' if ok else 'WRONG'} "
                    f"{secs}s")
    print("\nlanguage.detect fastText:", *rows, sep="\n  ")
    print(f"  peak memory {peak_mb()} MB, now {rss_mb()} MB")
    assert right >= len(rows) - 1                       # at most one miss (Marathi and Hindi look alike)


@pytest.mark.parametrize("engine", [RapidOCR, TesseractOCR])
def test_ocr_on_the_rendered_samples(engine):
    provider = engine()
    if not provider.health():
        pytest.skip(f"{provider.name} or its models not installed")
    rows, scores = [], []
    for s in SAMPLES:
        if s["script"] == "Latn" and s["language"] != "en":
            continue
        image = (DATA / f"{s['id']}.png").read_bytes()
        try:
            result, secs = timed(lambda s=s, image=image: provider.run({"images": [image], "language": s["language"]}))
        except Exception as e:  # noqa: BLE001 - a language this engine has no model for: reported, not failed
            rows.append(f"{s['id']}: not supported ({type(e).__name__})")
            continue
        rate = cer(result.output["text"], s["text"])
        scores.append(rate)
        rows.append(f"{s['id']}: CER {rate:.3f}, confidence {result.confidence:.2f}, {secs}s")
    print(f"\nocr.read {provider.name}:", *rows, sep="\n  ")
    print(f"  peak memory {peak_mb()} MB, now {rss_mb()} MB")
    assert scores and min(scores) < 0.2                 # it reads at least one sample nearly right


def test_translation_with_indictrans2():
    mt = IndicTrans2()
    if not mt.health():
        pytest.skip("IndicTrans2 or CTranslate2 not installed")
    rows = []
    for s in SAMPLES:
        if s["language"] == "en" or s["script"] == "Latn":
            continue
        result, secs = timed(lambda s=s: mt.run({"text": s["text"], "language": s["language"]}))
        rows.append(f"{s['id']}: ({result.confidence:.2f}, {secs}s) {result.output['text']}")
    print("\ntranslate.to_en IndicTrans2:", *rows, sep="\n  ")
    print(f"  peak memory {peak_mb()} MB, now {rss_mb()} MB")
    assert all("scholarship" in r.lower() or "stipend" in r.lower() for r in rows if "-1" in r)
