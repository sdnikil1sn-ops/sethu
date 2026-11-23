"""The model registry and the memory manager (AI Phase A1). No database needed."""
import json
import shutil
from pathlib import Path

import pytest

from app.ai import registry
from app.ai.memory import ModelManager

MODELS = Path(__file__).resolve().parents[2] / "models"   # the repository's models folder (stub-echo)


@pytest.fixture
def models(tmp_path) -> Path:
    """A copy of the repository's models folder plus a second small model, both in the manifest."""
    folder = tmp_path / "models"
    shutil.copytree(MODELS, folder)
    (folder / "other").mkdir()
    (folder / "other" / "weights.bin").write_bytes(b"\x00\x01" * 1000)
    (folder / "other" / "config.json").write_text('{"a": 1}')
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest["models"].append({"name": "other", "version": "2", "task": "stub.other", "license": "test",
                               "sha256": registry.digest(folder / "other"), "path": "other", "approx_memory_mb": 2})
    (folder / "manifest.json").write_text(json.dumps(manifest))
    return folder


def test_the_shipped_manifest_matches_its_files():
    assert registry.check_all(MODELS) == {"stub-echo": "ok"}


def test_a_changed_file_is_refused_and_named_without_its_content(models):
    (models / "stub-echo" / "stub.txt").write_text("tampered weights")
    verdicts = registry.check_all(models)
    assert verdicts["other"] == "ok"
    assert "checksum does not match" in verdicts["stub-echo"] and "tampered" not in verdicts["stub-echo"]
    with pytest.raises(registry.ModelIntegrityError):
        registry.verify(registry.load_manifest(models)["stub-echo"], models)


def test_a_folder_model_is_checked_file_by_file(models):
    (models / "other" / "extra.bin").write_bytes(b"x")            # an added file changes the folder's checksum
    assert "checksum does not match" in registry.check_all(models)["other"]


def test_paths_outside_the_folder_and_broken_manifests_are_refused(models, tmp_path):
    entry = registry.load_manifest(models)["stub-echo"]
    outside = registry.ModelEntry(**{**entry.__dict__, "path": "../secret.txt"})
    (tmp_path / "secret.txt").write_text("x")
    with pytest.raises(registry.ModelIntegrityError, match="leaves the models folder"):
        registry.verify(outside, models)
    (models / "manifest.json").write_text(json.dumps({"models": [{"name": "x"}]}))
    with pytest.raises(registry.ModelIntegrityError, match="missing one of"):
        registry.load_manifest(models)
    (models / "manifest.json").write_text("not json")
    assert list(registry.check_all(models)) == ["(manifest)"]


def test_one_model_at_a_time_and_idle_unload(models):
    now = [0.0]
    loads = []
    m = ModelManager(models, idle_seconds=60, clock=lambda: now[0])

    def loader(path):
        loads.append(Path(path).name)
        return object()

    first, entry = m.acquire("stub-echo", loader)
    assert entry.version == "1" and m.report()["loaded"] == "stub-echo"
    assert m.acquire("stub-echo", loader)[0] is first and loads == ["stub.txt"]   # loaded once, then reused
    m.acquire("other", loader)                                                    # replaces it: one slot
    assert m.report()["loaded"] == "other" and loads == ["stub.txt", "other"]
    now[0] = 59
    assert not m.unload_if_idle()
    now[0] = 120
    assert m.unload_if_idle() and m.report()["loaded"] is None


def test_a_model_that_fails_its_checksum_is_never_loaded(models):
    (models / "other" / "weights.bin").write_bytes(b"swapped")
    m = ModelManager(models, idle_seconds=60)
    with pytest.raises(registry.ModelIntegrityError):
        m.acquire("other", lambda path: pytest.fail("the loader must not be called"))
    with pytest.raises(registry.ModelIntegrityError, match="not in the manifest"):
        m.acquire("nope", lambda path: None)
    assert m.report()["loaded"] is None
