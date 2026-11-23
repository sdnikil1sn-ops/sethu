"""Overlap detection: the system suggests, a person decides.

Tier 1: open cases at one institution held by two or more bureaus. Shown, never
stored, and no link is suggested.
Tier 2: two open cases in different bureaus at the same institution, in the same
category, filed within 30 days of each other, whose texts are similar. Stored as a
`proposed` link (the suggestion) until an officer or head of either bureau
approves or rejects it. Approving queues an alert to both bureau heads.

Signals, inside the rules: pg_trgm text similarity always; with SETHU_SEMANTIC_OVERLAP on and the model present,
also the cosine similarity of the two complaints' embeddings (English only), which catches paraphrases trigram
misses. Either signal can raise a suggestion; each suggestion records both values and which fired. The
embeddings come from a local ONNX model baked into the image (no download at run time), are computed by the
worker only, stay in the database under the same Row-Level Security as the text, and are never returned by an
API or logged. With the setting off or the model missing, detection is exactly the trigram rule.
"""
import logging
from functools import lru_cache
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.core.config import get_settings
from app.modules.complaints import service as complaints
from app.modules.overlaps import repo
from app.modules.users import service as users

# pg_trgm's own default for "similar". On the seeded data the six planted pairs score
# 0.34 to 0.62 and cross-bureau pairs in different categories at most 0.26.
SIMILARITY_THRESHOLD = 0.30
WINDOW_DAYS = 30
BANNER = "Potential Overlapping Cases – Coordination Required"


log = logging.getLogger("sethu.overlaps")
EMBED_BATCH = 64


@lru_cache
def _embedder():
    """The local model, or None (setting off, no model directory, or the library missing): trigram only."""
    s = get_settings()
    if not (s.semantic_overlap and s.embedding_cache_dir):
        return None
    try:
        import onnxruntime
        from fastembed import TextEmbedding  # only the worker image needs it at run time

        onnxruntime.disable_telemetry_events()     # no telemetry, ever (the worker has no route out anyway)
        onnxruntime.set_default_logger_severity(3)  # errors only: its native lines bypass the JSON logs
        from loguru import logger as loguru  # fastembed's logger: send it through the JSON logs, not stderr

        loguru.remove()
        loguru.add(lambda m: logging.getLogger("fastembed").log(m.record["level"].no, m.record["message"]),
                   level="INFO")

        return TextEmbedding(s.embedding_model, cache_dir=s.embedding_cache_dir)
    except Exception as e:  # noqa: BLE001 - any failure means: carry on with trigram
        log.warning("semantic overlap signal unavailable, using trigram only", extra={"reason": type(e).__name__})
        return None


def semantic_on() -> bool:
    return _embedder() is not None


def embed_pending(session: Session, limit: int = 500) -> int:
    """Embed complaints that have no vector for the current model. Worker only (needs every bureau's text).
    Logs counts, never text or vectors."""
    model = _embedder()
    if model is None:
        return 0
    name, done = get_settings().embedding_model, 0
    while done < limit:
        rows = repo.unembedded(session, name, min(EMBED_BATCH, limit - done))
        if not rows:
            break
        vectors = model.embed([r["body"] for r in rows])
        repo.store_embeddings(session, name, [(r["id"], [float(x) for x in v]) for r, v in zip(rows, vectors,
                                                                                                strict=True)])
        done += len(rows)
    if done:
        log.info("complaints embedded", extra={"count": done, "model": name})
    return done


class OverlapError(Exception):
    """A request that cannot be carried out. `status` is the HTTP status to answer with."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def detect(session: Session, principal: Principal) -> dict[str, int]:
    """Find new Tier 2 pairs and store them as suggestions. Safe to repeat. Stores at most `detect_batch`
    (the strongest first); `suggested == detect_batch` means call again in a new transaction (the worker does)."""
    s = get_settings()
    created = repo.suggest_tier2(session, SIMILARITY_THRESHOLD, WINDOW_DAYS,
                                 s.semantic_threshold if semantic_on() else None, s.embedding_model, s.detect_batch)
    ref = repo.refs(session, [c for row in created for c in (row["complaint_a"], row["complaint_b"])])
    for row in created:
        audit.record(session, principal, "overlap.suggested", entity_type="overlap_links", entity_id=str(row["id"]),
                     payload={"cases": sorted([ref[row["complaint_a"]], ref[row["complaint_b"]]]), "tier": 2,
                              "score": float(row["score"]), "signals": row["signals"]})
    return {"suggested": len(created)}


def tier1(session: Session, institution_id: UUID | None = None) -> list[dict]:
    """Institutions with open cases in two or more bureaus, with those cases."""
    found: dict[UUID, dict] = {}
    for p in repo.tier1_pairs(session, institution_id):
        inst = found.setdefault(p["institution_id"], {
            "institution_id": p["institution_id"], "institution": p["institution"], "state": p["state"],
            "cases": {}, "pairs": 0, "tier2_pairs": 0})
        inst["pairs"] += 1
        inst["tier2_pairs"] += p["tier2"]
        for side in ("a", "b"):
            inst["cases"][p[f"{side}_id"]] = {"id": p[f"{side}_id"], "ref": p[f"{side}_ref"],
                                              "bureau": p[f"{side}_bureau"], "category": p[f"{side}_category"]}
    return [inst | {"cases": sorted(inst["cases"].values(), key=lambda c: c["ref"]),
                    "bureaus": sorted({c["bureau"] for c in inst["cases"].values()})} for inst in found.values()]


def _can_decide(principal: Principal, link: dict) -> bool:
    return (link["status"] == "proposed" and principal.role in ("officer", "bureau_head")
            and principal.bureau_id in (link["a_bureau_id"], link["b_bureau_id"]))


def _cases(link: dict) -> list[dict]:
    """The two cases of a link, in reference order (the stored order is by id, which means nothing to people)."""
    return sorted(({"id": link[f"{side}_id"], "ref": link[f"{side}_ref"], "bureau": link[f"{side}_bureau"],
                    "status": link[f"{side}_status"], "filed_at": link[f"{side}_filed_at"]} for side in ("a", "b")),
                  key=lambda c: c["ref"])


def _shape(principal: Principal, link: dict) -> dict:
    keep = ("id", "tier", "score", "reasons", "status", "created_at", "decided_at", "decided_by",
            "institution_id", "institution", "category", "alert_status", "alert_recipients")
    return {k: link[k] for k in keep} | {"cases": _cases(link), "can_decide": _can_decide(principal, link)}


def links(session: Session, principal: Principal, status: str | None = None,
          institution_id: UUID | None = None, bureau: str | None = None, tier: int | None = None) -> list[dict]:
    """bureau: links where either case is held by that bureau."""
    rows = repo.links(session, status=status, institution_id=institution_id, bureau=bureau, tier=tier)
    return [_shape(principal, row) for row in rows]


def links_page(session: Session, principal: Principal, limit: int, offset: int, status: str | None = None,
               institution_id: UUID | None = None, bureau: str | None = None, tier: int | None = None) -> dict:
    found = repo.links_page(session, limit, offset, status=status, institution_id=institution_id, bureau=bureau,
                            tier=tier)
    return found | {"items": [_shape(principal, row) for row in found["items"]]}


def linked_case_ids(session: Session) -> list[UUID]:
    """For the case list's "overlapping only" filter."""
    return repo.linked_case_ids(session)


def decide(session: Session, principal: Principal, link_id: UUID, approve: bool) -> dict:
    """Approve or reject a suggestion. The link, the alert (on approval) and the audit
    entry are written in the caller's transaction: all of them or none."""
    found = repo.links(session, link_id=link_id)
    if not found:  # Row-Level Security hides links the caller's bureau is not a party to
        raise OverlapError(404, "overlap suggestion not found")
    link = found[0]
    if link["status"] != "proposed":
        raise OverlapError(409, f"this suggestion was already {link['status']}")
    if not _can_decide(principal, link):
        raise OverlapError(403, "only an officer or head of one of the two bureaus can decide this")

    actor = complaints.actor_id(session, principal)
    if not repo.decide(session, link_id, "approved" if approve else "rejected", actor):
        raise OverlapError(409, "this suggestion was decided a moment ago")
    first, second = _cases(link)
    cases = [first["ref"], second["ref"]]
    payload: dict = {"cases": cases, "tier": link["tier"]}
    if approve:
        recipients, missing = users.recipients(session, [link["a_bureau_id"], link["b_bureau_id"]])
        # References only. Complaint text never goes into an alert.
        body = (f"{BANNER}\n\n"
                f"Case {first['ref']} ({first['bureau']}) and case {second['ref']} ({second['bureau']}) "
                f"appear to concern the same matter.\n"
                f"Institution: {link['institution']}\nCategory: {link['category']}\n\n"
                f"Open SETHU to see your bureau's case and coordinate with the other bureau.")
        alert_id = repo.insert_alert(session, link_id, recipients, missing, f"{BANNER}: {cases[0]} and {cases[1]}",
                                     body, actor)
        payload |= {"alert_id": str(alert_id), "recipients": len(recipients), "missing_recipients": missing}
    audit.record(session, principal, "overlap.approve" if approve else "overlap.reject",
                 entity_type="overlap_links", entity_id=str(link_id), payload=payload)
    return _shape(principal, repo.links(session, link_id=link_id)[0])
