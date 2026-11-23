"""Translation to English (task "translate.to_en"): IndicTrans2 first, the glossary second, "untranslated" last.

IndicTrans2 (AI4Bharat, MIT): the distilled Indic-to-English model (about 200M parameters), run with CTranslate2 at
int8, the smallest form that keeps its quality published. The model folder (registry name
"indictrans2-indic-en-dist-200m", put there by scripts/fetch_models.py) holds a CTranslate2 model directory and
`vocab/model.SRC` (SentencePiece). It is loaded only from the checksum-verified registry; no remote code runs.

The steps follow the reference CTranslate2 path, AI4Bharat/IndicTrans2 @ 4f08e39, inference/engine.py:
punctuation normalisation and placeholders for numbers, URLs and e-mail addresses (vendored, app/ai/vendor/
indictrans2), tokenising, Brahmic scripts transliterated to Devanagari, SentencePiece, "<src> eng_Latn" tags,
beam 5, then pieces joined and placeholders restored. Two steps are simplified here and listed in
app/ai/vendor/indictrans2/README.md: the indic-nlp-library normaliser (nukta and similar variants) and Moses
detokenisation. Their effect on quality is not yet measured.
"""
import math
import re
import unicodedata
from pathlib import Path

from app.ai.memory import manager
from app.ai.providers import Provider, Result
from app.ai.vendor.indictrans2.normalize_punctuation import punc_norm
from app.ai.vendor.indictrans2.normalize_regex_inference import normalize as placeholders

# ISO code (as language detection gives it) -> IndicTrans2 FLORES code. Every scheduled language is covered.
FLORES = {"as": "asm_Beng", "bn": "ben_Beng", "brx": "brx_Deva", "doi": "doi_Deva", "gu": "guj_Gujr",
          "hi": "hin_Deva", "kn": "kan_Knda", "ks": "kas_Arab", "gom": "gom_Deva", "mai": "mai_Deva",
          "ml": "mal_Mlym", "mni": "mni_Beng", "mr": "mar_Deva", "ne": "npi_Deva", "or": "ory_Orya",
          "pa": "pan_Guru", "sa": "san_Deva", "sat": "sat_Olck", "sd": "snd_Arab", "ta": "tam_Taml",
          "te": "tel_Telu", "ur": "urd_Arab"}
# Start of each Brahmic block; IndicTrans2 writes these scripts in Devanagari (U+0900) before SentencePiece.
BRAHMIC = {"Beng": 0x0980, "Guru": 0x0A00, "Gujr": 0x0A80, "Orya": 0x0B00, "Taml": 0x0B80, "Telu": 0x0C00,
           "Knda": 0x0C80, "Mlym": 0x0D00}
SENTENCE_END = re.compile(r"(?<=[।॥.!?])\s+")
MAX_INPUT_TOKENS = 160          # as the reference: longer input is cut, so sentences are translated one by one


def to_devanagari(text: str, script: str) -> str:
    """Offset mapping between Brahmic blocks, as indic-nlp-library's UnicodeIndicTransliterator does for the
    regular range (a character outside its block's first 0x7F code points is left as is)."""
    base = BRAHMIC.get(script)
    if base is None:
        return text
    return "".join(chr(0x0900 + ord(c) - base) if base <= ord(c) < base + 0x80 else c for c in text)


def tokenize(text: str) -> str:
    """Punctuation and symbols split from words (the reference's trivial tokeniser, simplified)."""
    out = []
    for ch in text:
        out.append(f" {ch} " if unicodedata.category(ch)[0] in "PS" else ch)
    return " ".join("".join(out).split())


def detokenize(text: str) -> str:
    text = re.sub(r"\s+([.,;:!?%)\]])", r"\1", text)
    return re.sub(r"([(\[])\s+", r"\1", text)


def preprocess(sentence: str, flores: str) -> tuple[str, dict]:
    iso = flores.split("_")[0][:2]
    sentence, mapping = placeholders(punc_norm(sentence, iso))
    script = flores.split("_")[1]
    return to_devanagari(tokenize(unicodedata.normalize("NFC", sentence)), script), mapping


class IndicTrans2(Provider):
    name = "indictrans2"
    model = "indictrans2-indic-en-dist-200m"

    def health(self) -> bool:
        try:
            import ctranslate2  # noqa: F401
            import sentencepiece  # noqa: F401
        except ImportError:
            return False
        from app.ai import registry
        try:
            return self.model in registry.load_manifest(manager().models_dir)
        except registry.ModelIntegrityError:
            return False

    @staticmethod
    def _load(path):
        import os

        import ctranslate2
        import sentencepiece as spm
        root = Path(path)          # the published archive: a CTranslate2 directory (model.bin) and vocab/model.SRC
        ct2_dir = next(root.rglob("model.bin")).parent
        spm_src = spm.SentencePieceProcessor(model_file=str(next(root.rglob("model.SRC"))))
        translator = ctranslate2.Translator(str(ct2_dir), device="cpu", compute_type="int8", inter_threads=1,
                                            intra_threads=max(1, (os.cpu_count() or 2) - 1))
        return translator, spm_src

    def run(self, payload: dict) -> Result:
        flores = FLORES.get(payload["language"])
        if flores is None:
            raise ValueError("no IndicTrans2 code for this language")
        (translator, spm_src), _ = manager().acquire(self.model, self._load)
        sentences = [s for s in SENTENCE_END.split(payload["text"].strip()) if s]
        prepared = [preprocess(s, flores) for s in sentences]
        batch = [[flores, "eng_Latn", *spm_src.encode(p, out_type=str)][:MAX_INPUT_TOKENS] for p, _ in prepared]
        results = translator.translate_batch(batch, beam_size=5, max_decoding_length=256, return_scores=True)
        english, scores = [], []
        for result, (_, mapping) in zip(results, prepared, strict=True):
            text = "".join(result.hypotheses[0]).replace("▁", " ").strip()
            for key, value in mapping.items():
                text = text.replace(key, value)
            english.append(detokenize(text))
            scores.append(result.scores[0])          # length-normalised log-probability
        confidence = math.exp(sum(scores) / len(scores)) if scores else 0.0
        return Result({"text": " ".join(english)}, round(min(confidence, 1.0), 5))

    def validate(self, output: dict) -> bool:
        text = output.get("text")
        return isinstance(text, str) and 0 < len(text) <= 20000


class GlossaryTranslate(Provider):
    """Fallback: no translation, only the known terms the glossary finds (payload["glossary"]). Its confidence is
    the share of the text the terms cover, so a text it barely covers falls through to "untranslated"."""
    name = "glossary"

    def run(self, payload: dict) -> Result:
        found = payload["glossary"].tag(payload["text"])
        return Result({"text": None, "tags": found["tags"]}, found["coverage"])

    def validate(self, output: dict) -> bool:
        return bool(output.get("tags"))


class GlossaryTag(Provider):
    """Task "glossary.tag": the English tags of the terms found. Deterministic; never unsure (coverage is reported
    in the output, not as confidence)."""
    name = "glossary-tags"

    def run(self, payload: dict) -> Result:
        return Result(payload["glossary"].tag(payload["text"]), 1.0)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("tags"), list)
