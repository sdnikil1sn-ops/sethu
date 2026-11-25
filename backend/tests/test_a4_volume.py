"""Optional: A4 at load-test volume on the test database (seed/volume.py). Skipped unless SETHU_A4_VOLUME is set to
a complaint count, for example 10000. The bounds are generous floors that catch a regression, not targets; the
measured numbers are in docs/AI-PIPELINE.md, A4 (scripts/measure_a4.py).

    $env:SETHU_A4_VOLUME = "10000"; pytest -s tests/test_a4_volume.py
"""
import os
import sys
import time
from pathlib import Path

import pytest

from app.db.session import SYSTEM, session_for
from app.modules.findings import service as findings
from app.modules.graph import service as graph
from app.modules.signals import service as signals
from tests.conftest import requires_db

SIZE = int(os.environ.get("SETHU_A4_VOLUME") or 0)
pytestmark = [requires_db, pytest.mark.skipif(not SIZE, reason="set SETHU_A4_VOLUME to a complaint count")]


def test_a4_at_volume(world):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "seed"))
    import volume
    volume.main(SIZE, 2000)          # the same database as `world` (SETHU_DATABASE_URL)
    timings = {}
    for name, job in (("graph.build", lambda s: graph.build_task(s, SYSTEM, force=True)),
                      ("findings.detect (bottleneck.detect)", lambda s: findings.detect(s, SYSTEM)),
                      ("signals.detect (warning.detect)", lambda s: signals.detect(s, SYSTEM))):
        started = time.perf_counter()
        with session_for(SYSTEM, world["engine"]) as s:
            job(s)
        timings[name] = round(time.perf_counter() - started, 1)
    print(f"\nA4 at {SIZE} complaints, seconds: {timings}")
    assert all(t < 600 for t in timings.values())
