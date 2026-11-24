"""scripts/fetch_models.py small: installs what is missing, skips what is intact, keeps going past a failure."""
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import fetch_models  # noqa: E402


@pytest.fixture
def fake(monkeypatch, tmp_path):
    """Two small models whose 'downloads' write known bytes; `bad` names URLs that fail to download."""
    content = {f"https://example.test/{n}.bin": n.encode() for n in ("a", "b", "c")}
    sha = {u: hashlib.sha256(b).hexdigest() for u, b in content.items()}
    u = list(content)
    monkeypatch.setattr(fetch_models, "MODELS", tmp_path)
    monkeypatch.setattr(fetch_models, "SMALL", [
        ("m-one", "1", "ocr.read", "test", 5, [(u[0], sha[u[0]]), (u[1], sha[u[1]])]),
        ("m-two", "1", "ocr.read", "test", 5, [(u[2], sha[u[2]])]),
    ])
    state = {"bad": set(), "calls": 0}

    def download(url, target, tries=6):
        state["calls"] += 1
        if url in state["bad"]:
            raise SystemExit(f"could not download {url}")
        target.write_bytes(content[url])
        return hashlib.sha256(content[url]).hexdigest()

    monkeypatch.setattr(fetch_models, "download", download)
    return state, content, tmp_path


def test_installs_then_skips_intact_models(fake):
    state, _, _ = fake
    assert fetch_models.small() == {"installed": ["m-one", "m-two"], "skipped": [], "failed": []}
    calls = state["calls"]
    assert fetch_models.small() == {"installed": [], "skipped": ["m-one", "m-two"], "failed": []}
    assert state["calls"] == calls          # nothing downloaded the second time


def test_reinstalls_a_model_whose_files_changed(fake):
    _, _, models = fake
    fetch_models.small()
    (models / "m-two" / "1" / "c.bin").write_bytes(b"tampered")
    assert fetch_models.small() == {"installed": ["m-two"], "skipped": ["m-one"], "failed": []}


def test_checksum_mismatch_fails_that_model_only(fake, monkeypatch):
    _, _, models = fake
    small = fetch_models.SMALL
    name, version, task, licence, mem, files = small[0]
    monkeypatch.setattr(fetch_models, "SMALL", [(name, version, task, licence, mem,
                                                [files[0], (files[1][0], "0" * 64)]), small[1]])
    assert fetch_models.small() == {"installed": ["m-two"], "skipped": [], "failed": ["m-one"]}
    assert not (models / "m-one" / "1" / "b.bin").exists()      # the mismatched file is deleted
    assert "m-one" not in (models / "manifest.json").read_text()  # and nothing is recorded


def test_download_failure_does_not_stop_the_rest(fake, capsys):
    state, content, _ = fake
    state["bad"].add(list(content)[0])
    assert fetch_models.small() == {"installed": ["m-two"], "skipped": [], "failed": ["m-one"]}
    out = capsys.readouterr().out
    assert "failed: 1 (m-one)" in out and "docker compose restart ai-worker" in out


def test_pinned_list_matches_what_the_providers_look_up():
    names = {name for name, *_ in fetch_models.SMALL}
    assert names == {"lid-176", "rapidocr-en", "rapidocr-devanagari", "rapidocr-ta", "rapidocr-te",
                     *(f"tessdata-{lang}" for lang in ("eng", "hin", "mar", "tam", "tel", "kan", "ben"))}
    for *_, files in fetch_models.SMALL:
        for url, sha in files:
            assert url.startswith("https://") and len(sha) == 64 and int(sha, 16) >= 0
