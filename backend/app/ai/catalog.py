"""Every provider SETHU_AI_ROUTES may name, made fresh per call (providers hold no state; the router keeps circuits
by name). Real engines are unhealthy until their library and model are installed, so their task falls through to
the next provider: rules, the glossary, or a person."""
from app.ai.classify import CategoryModel, CategoryRules
from app.ai.e5 import E5Embed
from app.ai.lid import FastTextLID, ScriptLID
from app.ai.ocr import RapidOCR, TesseractOCR
from app.ai.providers import StubProvider
from app.ai.semantic import E5Institution, E5Match, FuzzyInstitution, TextMatch
from app.ai.translate import GlossaryTag, GlossaryTranslate, IndicTrans2

PROVIDERS = {
    "stub-model": lambda: StubProvider("stub-model", confidence=0.9, model="stub-echo"),
    "stub-rules": lambda: StubProvider("stub-rules", confidence=0.7),
    "fasttext-lid": FastTextLID,
    "script-lid": ScriptLID,
    "rapidocr": RapidOCR,
    "tesseract": TesseractOCR,
    "indictrans2": IndicTrans2,
    "glossary": GlossaryTranslate,
    "glossary-tags": GlossaryTag,
    "e5": E5Embed,
    "e5-match": E5Match,
    "text-match": TextMatch,
    "institution-e5": E5Institution,
    "institution-fuzzy": FuzzyInstitution,
    "category-e5": CategoryModel,
    "category-rules": CategoryRules,
}
