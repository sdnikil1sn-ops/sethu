"""Reading text from attachments (task "ocr.read"): the ONNX OCR engine first, Tesseract second, a person last.

PDFs: the text a PDF carries is taken as is (pypdf, BSD); only pages without text are rendered (pypdfium2,
Apache-2.0/BSD) and read. PyMuPDF is not used (AGPL). Images and rendered pages are refused above
`ai.ocr.max_image_pixels`; PDFs are read up to `ai.ocr.max_pages` pages. Nothing here touches the network:
Tesseract runs as a local program with its language files linked from the checksum-verified registry.
"""
import io
import os
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from app.ai import registry
from app.ai.memory import manager
from app.ai.providers import Provider, Result

MIN_TEXT_PER_PAGE = 25          # a PDF page with fewer characters of text is treated as a scan
RENDER_SCALE = 2.0              # pdfium renders at 72 dpi x scale: 144 dpi, enough for printed text

# Detected language -> Tesseract traineddata names (registry models "tessdata-<name>"), English always added.
TESSERACT = {"hi": "hin", "mr": "mar", "ne": "nep", "sa": "san", "mai": "hin", "gom": "mar", "doi": "hin",
             "brx": "hin", "bn": "ben", "as": "asm", "gu": "guj", "kn": "kan", "ml": "mal", "pa": "pan",
             "or": "ori", "ta": "tam", "te": "tel", "ur": "urd", "sd": "snd", "en": "eng"}


class PageLimit(ValueError):
    """An attachment over the page or pixel limits; the message has numbers only."""


@dataclass
class Pages:
    embedded_text: str           # text the PDF itself carries (pages with enough of it)
    images: list                 # PNG bytes of the pages (or the image) to read with OCR
    pages: int


def pages(data: bytes, content_type: str, max_pages: int, max_pixels: int) -> Pages:
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = max_pixels          # Pillow itself refuses a decompression bomb past this
    if content_type != "application/pdf":
        with Image.open(io.BytesIO(data)) as image:
            if image.width * image.height > max_pixels:
                raise PageLimit(f"the image has {image.width * image.height} pixels, more than {max_pixels}")
            return Pages("", [_png(image.convert("RGB"))], 1)
    import pypdf
    import pypdfium2
    reader = pypdf.PdfReader(io.BytesIO(data))
    count = len(reader.pages)
    if count > max_pages:
        raise PageLimit(f"the PDF has {count} pages, more than {max_pages}")
    embedded, scanned = [], []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        (embedded.append(text) if len(text) >= MIN_TEXT_PER_PAGE and not garbled(text) else scanned.append(i))
    images = []
    if scanned:
        pdf = pypdfium2.PdfDocument(data)
        try:
            for i in scanned:
                width, height = pdf[i].get_size()
                if width * height * RENDER_SCALE ** 2 > max_pixels:
                    raise PageLimit(f"page {i + 1} would render to more than {max_pixels} pixels")
                images.append(_png(pdf[i].render(scale=RENDER_SCALE).to_pil()))
        finally:
            pdf.close()
    return Pages("\n".join(embedded), images, count)


def garbled(text: str) -> bool:
    """Embedded text that cannot be trusted, so the page is read with OCR instead. Indic text in PDFs often comes
    out in visual order (a vowel sign before its consonant: "िमली" for "मिली") or as NUL bytes for shaped glyphs
    (measured: a Chrome-made Hindi PDF read with pypdf, docs/AI-PIPELINE.md)."""
    if "\x00" in text or "\ufffd" in text:
        return True
    words = text.split()
    starts_with_sign = sum(1 for w in words if unicodedata.category(w[0]) in ("Mn", "Mc"))
    return bool(words) and starts_with_sign / len(words) > 0.02


def _png(image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


# Detected language -> RapidOCR recogniser group (registry model "rapidocr-<group>": det.onnx, rec.onnx, keys.txt,
# PaddleOCR models in ONNX form). Languages without a group (Bengali, Assamese, Gujarati, Malayalam, Punjabi, Odia,
# ...) have no recogniser in RapidOCR: the provider refuses them and Tesseract reads them.
RAPID_GROUP = {"hi": "devanagari", "mr": "devanagari", "ne": "devanagari", "sa": "devanagari", "mai": "devanagari",
               "gom": "devanagari", "doi": "devanagari", "brx": "devanagari", "ta": "ta", "te": "te", "kn": "ka",
               "en": "en"}


class RapidOCR(Provider):
    """PaddleOCR's models on ONNX Runtime (RapidOCR, Apache-2.0): chosen over PaddlePaddle after measuring both
    (docs/AI-PIPELINE.md, "OCR engine"). Models only from the registry: rapidocr never downloads with model paths."""
    name = "rapidocr"

    def health(self) -> bool:
        try:
            import rapidocr  # noqa: F401
        except ImportError:
            return False
        try:
            return any(n.startswith("rapidocr-") for n in registry.load_manifest(manager().models_dir))
        except registry.ModelIntegrityError:
            return False

    @staticmethod
    def _load(path):
        from rapidocr import RapidOCR as Engine
        folder = Path(path)
        keys = next(folder.rglob("*.txt"), None)     # PP-OCRv5 recognisers carry their characters inside the model
        return Engine(params={
            "Det.model_path": str(next(folder.rglob("*det*.onnx"))),
            "Rec.model_path": str(next(folder.rglob("*rec*.onnx"))),
            **({"Rec.rec_keys_path": str(keys)} if keys else {}), "Global.use_cls": False,
            "Global.log_level": "warning",
            "EngineConfig.onnxruntime.intra_op_num_threads": max(1, (os.cpu_count() or 2) - 1)})

    def run(self, payload: dict) -> Result:
        group = RAPID_GROUP.get(payload.get("language") or "")
        if group is None:
            raise LookupError("no RapidOCR recogniser for this language")
        engine, _ = manager().acquire(f"rapidocr-{group}", self._load)
        texts, scores = [], []
        for image in payload["images"]:
            result = engine(image)
            texts.append(" ".join(result.txts or []))
            scores += list(result.scores or [])
        return Result({"text": "\n".join(texts)}, round(sum(scores) / len(scores), 5) if scores else 0.0)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("text"), str) and bool(output["text"].strip())


class TesseractOCR(Provider):
    """Tesseract 5 with the language files from the registry (models "tessdata-hin", "tessdata-tam", ...)."""
    name = "tesseract"

    def health(self) -> bool:
        if not shutil.which("tesseract"):
            return False
        try:
            return any(n.startswith("tessdata-") for n in registry.load_manifest(manager().models_dir))
        except registry.ModelIntegrityError:
            return False

    def run(self, payload: dict) -> Result:
        program = shutil.which("tesseract")
        if program is None:
            raise FileNotFoundError("tesseract is not installed")
        langs = [TESSERACT.get(payload.get("language") or "", "eng"), "eng"]
        langs = list(dict.fromkeys(langs))
        models = registry.load_manifest(manager().models_dir)
        texts, confidences = [], []
        with tempfile.TemporaryDirectory(prefix="tessdata-") as tessdata:
            for lang in langs:
                entry = models.get(f"tessdata-{lang}")
                if entry is None:
                    raise FileNotFoundError(f"tessdata-{lang} is not installed")
                path = registry.verify(entry, manager().models_dir)          # checked, then linked
                source = path if path.is_file() else next(path.glob("*.traineddata"))
                os.symlink(source, Path(tessdata) / f"{lang}.traineddata")
            for image in payload["images"]:
                done = subprocess.run(  # noqa: S603 - a fixed program and arguments; the image goes in on stdin
                    [program, "stdin", "stdout", "--tessdata-dir", tessdata, "-l", "+".join(langs),
                     "--psm", "6", "-c", "tessedit_create_tsv=1"],   # a setting: the tessdata folder has no configs
                    input=image, capture_output=True, timeout=300, check=True)
                words = [line.split("\t") for line in done.stdout.decode().splitlines()[1:]]
                words = [w for w in words if len(w) == 12 and w[11].strip() and float(w[10]) >= 0]
                texts.append(" ".join(w[11] for w in words))
                confidences += [float(w[10]) / 100 for w in words]
        confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return Result({"text": "\n".join(texts)}, round(confidence, 5))

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("text"), str) and bool(output["text"].strip())
