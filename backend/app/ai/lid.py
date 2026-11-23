"""Language detection (task "language.detect"): fastText LID first, Unicode script second, "unknown" last.

The 22 languages of the Eighth Schedule plus English. `fasttext` says whether the lid.176 model can name the
language; the script detector can only narrow a text to the languages written in its script (Devanagari alone is
used for nine of them), so it is less sure when a script is shared. Neither is trained on Indian complaint text.
"""
import unicodedata
from pathlib import Path

from app.ai.memory import manager
from app.ai.providers import Provider, Result

# code: (name, scripts it is written in, does fastText lid.176 have it?)
LANGUAGES = {
    "as": ("Assamese", ("Beng",), True), "bn": ("Bengali", ("Beng",), True), "brx": ("Bodo", ("Deva",), False),
    "doi": ("Dogri", ("Deva",), False), "gu": ("Gujarati", ("Gujr",), True), "hi": ("Hindi", ("Deva", "Latn"), True),
    "kn": ("Kannada", ("Knda",), True), "ks": ("Kashmiri", ("Arab", "Deva"), False),
    "gom": ("Konkani", ("Deva",), True), "mai": ("Maithili", ("Deva",), False),
    "ml": ("Malayalam", ("Mlym",), True), "mni": ("Manipuri", ("Mtei", "Beng"), False),
    "mr": ("Marathi", ("Deva",), True), "ne": ("Nepali", ("Deva",), True), "or": ("Odia", ("Orya",), True),
    "pa": ("Punjabi", ("Guru",), True), "sa": ("Sanskrit", ("Deva",), True), "sat": ("Santali", ("Olck",), False),
    "sd": ("Sindhi", ("Arab", "Deva"), True), "ta": ("Tamil", ("Taml",), True), "te": ("Telugu", ("Telu",), True),
    "ur": ("Urdu", ("Arab",), True), "en": ("English", ("Latn",), True),
}

# Unicode block ranges of the scripts above (code points, inclusive).
SCRIPTS = {
    "Deva": [(0x0900, 0x097F), (0xA8E0, 0xA8FF)], "Beng": [(0x0980, 0x09FF)], "Guru": [(0x0A00, 0x0A7F)],
    "Gujr": [(0x0A80, 0x0AFF)], "Orya": [(0x0B00, 0x0B7F)], "Taml": [(0x0B80, 0x0BFF)], "Telu": [(0x0C00, 0x0C7F)],
    "Knda": [(0x0C80, 0x0CFF)], "Mlym": [(0x0D00, 0x0D7F)], "Arab": [(0x0600, 0x06FF), (0x0750, 0x077F)],
    "Olck": [(0x1C50, 0x1C7F)], "Mtei": [(0xABC0, 0xABFF), (0xAAE0, 0xAAFF)], "Latn": [(0x0041, 0x024F)],
}
# When a script is shared, the most likely language of an AICTE complaint first.
LIKELY = {"Deva": ["hi", "mr", "ne", "mai", "gom", "doi", "brx", "sa", "ks", "sd"], "Beng": ["bn", "as", "mni"],
          "Arab": ["ur", "ks", "sd"], "Latn": ["en", "hi"], "Mtei": ["mni"], "Olck": ["sat"]}
SHARED_SCRIPT_FACTOR = 0.6       # confidence when the script alone cannot tell its languages apart


def script_of(ch: str) -> str | None:
    cp = ord(ch)
    for script, ranges in SCRIPTS.items():
        if any(lo <= cp <= hi for lo, hi in ranges) and (script != "Latn" or unicodedata.category(ch)[0] == "L"):
            return script
    return None


def candidates(script: str) -> list[str]:
    return LIKELY.get(script) or [code for code, (_, scripts, _) in LANGUAGES.items() if script in scripts]


def detect_script(text: str) -> dict:
    """The dominant script, its candidate languages, and a confidence: the dominant script's share of the letters,
    times SHARED_SCRIPT_FACTOR when more than one language uses it."""
    counts: dict[str, int] = {}
    for ch in text:
        if (script := script_of(ch)) is not None:
            counts[script] = counts.get(script, 0) + 1
    total = sum(counts.values())
    if not total:
        return {"language": "unknown", "script": None, "candidates": [], "confidence": 0.0}
    script = max(counts, key=counts.get)
    langs = candidates(script)
    share = counts[script] / total
    return {"language": langs[0], "script": script, "candidates": langs,
            "confidence": round(share * (1 if len(langs) == 1 else SHARED_SCRIPT_FACTOR), 5)}


def model_file(path, patterns=("*.ftz", "*.bin")) -> Path:
    """The model file itself: the registry path is a file, or a folder (scripts/fetch_models.py) holding it."""
    path = Path(path)
    if path.is_file():
        return path
    for pattern in patterns:
        if found := sorted(path.glob(pattern)):
            return found[0]
    raise FileNotFoundError(f"no {' or '.join(patterns)} file in the model folder")


class ScriptLID(Provider):
    name = "script-lid"

    def run(self, payload: dict) -> Result:
        found = detect_script(payload["text"])
        return Result(found, found["confidence"])

    def validate(self, output: dict) -> bool:
        return output.get("language") in LANGUAGES


class FastTextLID(Provider):
    """fastText lid.176 (model "lid-176" in the registry). Unhealthy until the model is installed."""
    name = "fasttext-lid"
    model = "lid-176"

    def health(self) -> bool:
        try:
            import fasttext  # noqa: F401
        except ImportError:
            return False
        from app.ai import registry
        try:
            return self.model in registry.load_manifest(manager().models_dir)
        except registry.ModelIntegrityError:
            return False

    def run(self, payload: dict) -> Result:
        import fasttext
        model, _ = manager().acquire(self.model, lambda path: fasttext.load_model(str(model_file(path))))
        # The binding itself, not model.predict(): fastText 0.9.2's wrapper calls np.array(copy=False), which numpy 2
        # refuses. It returns (probability, label) pairs, best first.
        pairs = model.f.predict(" ".join(payload["text"].split()), 3, 0.0, "strict")
        codes = [label.removeprefix("__label__") for _, label in pairs]
        script = detect_script(payload["text"])["script"]
        return Result({"language": codes[0], "script": script, "candidates": codes}, float(pairs[0][0]))

    def validate(self, output: dict) -> bool:
        return output.get("language") in LANGUAGES      # a language outside the 22 + English falls through
