"""The egress canary's verdict (scripts/egress_canary.py), on made-up containers. The canary itself runs against a
live stack (CI job `egress-canary`; docs/AI-PIPELINE.md)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import egress_canary  # noqa: E402


def box(service, networks, tcp=False, dns=False):
    return {"service": service, "networks": networks, "reach": {"tcp": tcp, "dns": dns}}


INTERNAL = {"sethu_app": True, "sethu_data": True}
AI = {"sethu_ai": True, "sethu_data": True}
EDGE = {"sethu_edge": False, "sethu_app": True}


def test_a_sealed_stack_passes_and_edge_routes_are_only_noted():
    failures, notes = egress_canary.verdicts(
        [box("backend", INTERNAL), box("ai-worker", AI), box("web", EDGE, tcp=True, dns=True)], strict=False)
    assert failures == [] and any("web" in n and "by design" in n for n in notes)


def test_an_internal_container_that_reaches_out_fails():
    failures, _ = egress_canary.verdicts([box("ai-worker", AI), box("worker", INTERNAL, dns=True)], strict=False)
    assert failures == ["worker (sethu_app, sethu_data): reached the internet (dns)"]


def test_ai_worker_must_run_be_sealed_and_be_probed():
    assert egress_canary.verdicts([box("backend", INTERNAL)], strict=False)[0] == ["ai-worker is not running"]
    failures, _ = egress_canary.verdicts([box("ai-worker", {"sethu_edge": False, "sethu_ai": True})], strict=False)
    assert failures == ["ai-worker (sethu_ai, sethu_edge): ai-worker is on a network with a route out"]
    unprobed = box("ai-worker", AI)
    unprobed["reach"] = {"tcp": None, "dns": None}
    assert "could not be probed" in egress_canary.verdicts([unprobed], strict=False)[0][0]


def test_strict_fails_the_edge_too():
    failures, _ = egress_canary.verdicts([box("ai-worker", AI), box("web", EDGE, tcp=True)], strict=True)
    assert failures == ["web (sethu_app, sethu_edge): reached the internet (tcp)"]
