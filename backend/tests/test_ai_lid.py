"""Language detection's script fallback and the 22 scheduled languages (AI Phase A2). No database needed."""
import json
from pathlib import Path

from app.ai import lid, translate

SAMPLES = json.loads((Path(__file__).parent / "data/multilingual/samples.json").read_text(encoding="utf-8"))["samples"]
SCHEDULED = {"as", "bn", "brx", "doi", "gu", "hi", "kn", "ks", "gom", "mai", "ml", "mni", "mr", "ne", "or", "pa",
             "sa", "sat", "sd", "ta", "te", "ur"}


def test_every_scheduled_language_has_a_script_and_a_translation_code():
    assert SCHEDULED | {"en"} == set(lid.LANGUAGES)
    for code, (_, scripts, _) in lid.LANGUAGES.items():
        assert all(s in lid.SCRIPTS for s in scripts), code
        assert any(code in lid.candidates(s) for s in scripts), code        # reachable from its own script
    assert SCHEDULED == set(translate.FLORES)


def test_the_script_of_each_sample_and_its_candidates():
    for s in SAMPLES:
        found = lid.detect_script(s["text"])
        assert found["script"] == s["script"] and s["language"] in found["candidates"], s["id"]
        if s["script"] in ("Taml", "Telu", "Knda"):                          # one language per script: sure
            assert found["language"] == s["language"] and found["confidence"] > 0.9
        if s["script"] == "Deva":                                            # nine languages share it: unsure
            assert found["language"] == "hi" and found["confidence"] < 0.61


def test_no_letters_is_unknown_and_never_passes():
    assert lid.detect_script("1234 ... !!!") == {"language": "unknown", "script": None, "candidates": [],
                                                 "confidence": 0.0}
    assert not lid.ScriptLID().validate({"language": "unknown"})


def test_fasttext_is_unhealthy_until_installed(tmp_path, monkeypatch):
    from app.ai import memory
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "ai_models_dir", str(tmp_path))
    memory.manager.cache_clear()
    try:
        assert lid.FastTextLID().health() is False      # no manifest (and no fasttext library here)
    finally:
        memory.manager.cache_clear()


def test_brahmic_scripts_are_written_in_devanagari_for_indictrans2():
    assert translate.to_devanagari("தமிழ்", "Taml") == "तमिऴ्"          # Tamil letters on their Devanagari slots
    assert translate.to_devanagari("हिंदी", "Deva") == "हिंदी"
    assert translate.tokenize("फीस, वापसी!") == "फीस , वापसी !"           # matras stay inside the word
    sentence, placeholders = translate.preprocess("Pay 1,50,000 at https://example.test/fees now.", "hin_Deva")
    assert "example.test" not in sentence and any("example.test" in v for v in placeholders.values())
