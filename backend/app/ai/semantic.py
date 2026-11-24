"""Decisions made from E5 similarities (docs/AI-PIPELINE.md, "A3"). The similarities themselves are computed by
pgvector from stored vectors, so these providers load no model and run in any process.

match.complaints   e5-match (cosine of the two complaints' E5 vectors) -> text-match (pg_trgm, what SETHU used
                   before A3) -> a person (the pair is suggested for an officer only if a signal fired).
institution.resolve  institution-e5 (cosine of the typed name to registry names and aliases) -> institution-fuzzy
                   (the alias dictionary and spelling ratio) -> the officer queue.

Matching confidence: 0.5 at the threshold, rising to 1 at `confidence_span` away from it (either side: a clear
"no" is as confident as a clear "yes"). When both signals exist and the texts share a language, agreement adds
`agreement_bonus` and disagreement takes off `disagreement_penalty`. Trigram cannot compare texts in different
languages, so then it is not consulted (and cannot veto a cross-lingual match).

Institution rules: a name that is an acronym ("GIT Pune") is never linked automatically; otherwise a link needs the
top score at or over the threshold AND ahead of the next institution by the margin. Anything else goes to an
officer with the top three candidates and their scores.
"""
from app.ai.e5 import MODEL
from app.ai.providers import NotApplicable, Provider, Result
from app.core.config import get_settings


def _clamp(x: float) -> float:
    return round(min(1.0, max(0.0, x)), 5)


def _distance_confidence(score: float, threshold: float, span: float) -> float:
    return 0.5 + min(0.5, abs(score - threshold) / span * 0.5)


def _adjust(confidence: float, matched: bool, other: bool | None, s: dict) -> tuple[float, str]:
    if other is None:
        return _clamp(confidence), "not compared"
    if other == matched:
        return _clamp(confidence + s["agreement_bonus"]), "agree"
    return _clamp(confidence - s["disagreement_penalty"]), "disagree"


class E5Match(Provider):
    """payload {"pair": {"semantic", "trigram", "same_language"}, "settings": {...}, "model_version"}."""
    name = "e5-match"
    model = MODEL

    def health(self) -> bool:
        return get_settings().semantic_overlap      # SETHU_SEMANTIC_OVERLAP=false: trigram only

    def run(self, payload: dict) -> Result:
        pair, s = payload["pair"], payload["settings"]
        if pair.get("semantic") is None:
            raise NotApplicable("no vectors of the active model for both complaints")
        score, threshold = float(pair["semantic"]), s["e5_threshold"]
        matched = score >= threshold
        text_says = pair["trigram"] >= s["trigram_threshold"] if pair.get("same_language") else None
        confidence, agreement = _adjust(_distance_confidence(score, threshold, s["confidence_span"]), matched,
                                        text_says, s)
        return Result({"matched": matched, "method": "e5", "score": round(score, 5), "agreement": agreement,
                       "model_version": payload.get("model_version")}, confidence)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("matched"), bool) and output.get("method") == "e5"


class TextMatch(Provider):
    """pg_trgm similarity of the two original texts (computed in the database). Same-language pairs only."""
    name = "text-match"

    def run(self, payload: dict) -> Result:
        pair, s = payload["pair"], payload["settings"]
        if not pair.get("same_language"):
            raise NotApplicable("texts in different languages: trigram similarity cannot compare them")
        score, threshold = float(pair["trigram"]), s["trigram_threshold"]
        matched = score >= threshold
        e5_says = None if pair.get("semantic") is None else pair["semantic"] >= s["e5_threshold"]
        confidence, agreement = _adjust(_distance_confidence(score, threshold, s["confidence_span"]), matched,
                                        e5_says, s)
        return Result({"matched": matched, "method": "text", "score": round(score, 5), "agreement": agreement},
                      confidence)

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("matched"), bool) and output.get("method") == "text"


def _institution_decision(candidates: list[dict], acronym: bool, threshold: float, margin: float) -> dict:
    """The top three, and whether the rules allow linking the first without a person."""
    ranked = sorted(candidates, key=lambda c: -c["score"])
    top = ranked[0]["score"] if ranked else 0.0
    lead = top - (ranked[1]["score"] if len(ranked) > 1 else 0.0)
    auto = bool(ranked) and not acronym and top >= threshold and lead >= margin
    why = ("acronym: never linked automatically" if acronym else
           "clear match" if auto else f"below the threshold {threshold:g}" if top < threshold else
           f"too close to the next candidate (lead {lead:.3f} < {margin:g})")
    return {"auto": auto, "institution_id": ranked[0]["institution_id"] if auto else None,
            "top": ranked[:3], "lead": round(lead, 5), "why": why}


class E5Institution(Provider):
    """payload {"e5": [{"institution_id", "label", "score"}], "acronym", "settings", "model_version"}: the best
    cosine per institution (already computed by pgvector)."""
    name = "institution-e5"
    model = MODEL

    def run(self, payload: dict) -> Result:
        if not payload.get("e5"):
            raise NotApplicable("no E5 vector for the name or the registry")
        s = payload["settings"]
        found = _institution_decision(payload["e5"], payload["acronym"], s["e5_threshold"], s["e5_margin"])
        return Result(found | {"method": "e5", "model_version": payload.get("model_version")},
                      _clamp(found["top"][0]["score"]))

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("auto"), bool) and bool(output.get("top"))


class FuzzyInstitution(Provider):
    """payload {"fuzzy": [{"institution_id", "label", "score" (0-100)}], "acronym", "settings"}: the alias
    dictionary and spelling ratio of the deterministic cascade (app/modules/institutions)."""
    name = "institution-fuzzy"

    def run(self, payload: dict) -> Result:
        if not payload.get("fuzzy"):
            raise NotApplicable("no similar spelling in the registry")
        s = payload["settings"]
        found = _institution_decision(payload["fuzzy"], payload["acronym"], s["fuzzy_threshold"], s["fuzzy_margin"])
        return Result(found | {"method": "fuzzy"}, _clamp(found["top"][0]["score"] / 100))

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("auto"), bool) and bool(output.get("top"))
