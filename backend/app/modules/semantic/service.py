"""AI Phase A3 in the ai-worker (docs/AI-PIPELINE.md, "A3"): E5 vectors, classification, semantic institution
resolution, the category classifier's training, and the officer's decisions on the case page. Every model call
goes through the A1 router (provenance, circuit breaker, confidence threshold).

Pipeline stages after A2's (app/modules/enrichment/service.py), over the same batch, one model at a time:
    embed (E5, the ORIGINAL text) -> classify the category -> resolve the institution by meaning
Background job `maintain` (ai queue, every 30 s): vectors for complaints that have none of the installed E5
version (filed before A3, or after a model upgrade; resumable, batch by batch), the registry's name vectors, and a
first classifier when there is none.

Vectors are labelled with model and version. The setting "ai.embedding.active" names the version the worker makes
now; matching (app/modules/overlaps) compares only vectors of exactly that version. The bge-small vectors made
before A3 keep their label and are never compared with E5 ones.
"""
import hashlib
import json
import logging
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai import classify, registry, router
from app.ai import suggestions as feedback
from app.ai.e5 import MODEL, E5Embed
from app.ai.memory import manager
from app.audit import service as audit
from app.core.auth import Principal
from app.db.session import SYSTEM, session_for
from app.modules.complaints import service as complaints
from app.modules.enrichment import service as enrichment
from app.modules.institutions import service as institutions
from app.modules.semantic import repo

log = logging.getLogger("sethu.semantic")
BOOTSTRAP = Path(__file__).resolve().parents[2] / "ai/data/category_bootstrap.jsonl"
TOP = 3
TRAIN_BATCH = 64


class SemanticError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


# --- the installed model and the active version -----------------------------------------------------------

def installed_version() -> str | None:
    """The E5 version in the registry, or None (not installed, or the libraries are missing)."""
    if not E5Embed().health():
        return None
    try:
        return registry.load_manifest(manager().models_dir)[MODEL].version
    except (registry.ModelIntegrityError, KeyError):
        return None


def active(session: Session) -> dict | None:
    found = router.setting(session, "ai.embedding.active", None)
    return found if isinstance(found, dict) and found.get("model") == MODEL and found.get("version") else None


def _mark_active(session: Session, version: str) -> None:
    if (active(session) or {}).get("version") == version:
        return
    session.execute(text("""
        INSERT INTO sethu.app_settings (key, value) VALUES ('ai.embedding.active', CAST(:v AS jsonb))
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()"""),
        {"v": json.dumps({"model": MODEL, "version": version})})
    audit.record(session, SYSTEM, "ai.embedding.activated", entity_type="app_settings",
                 entity_id="ai.embedding.active", payload={"model": MODEL, "version": version})


def _embed(session: Session, texts: list[str], kind: str, subject_type: str, subject_id: str):
    """(vectors, version) through the router, or None when E5 gave no answer (its fallbacks then apply)."""
    r = router.run(session, SYSTEM, "embed.text", {"texts": texts, "kind": kind}, subject_type=subject_type,
                   subject_id=subject_id)
    if r["status"] != "ok":
        return None
    return r["output"]["vectors"], r["output"]["model_version"]


# --- complaint vectors: the pipeline stage and the re-embed job ----------------------------------------------

def embed_complaints(ids: list[UUID], engine=None) -> int:
    """Pipeline stage: vectors of these complaints' original text, in one model call."""
    if not ids:
        return 0
    with session_for(SYSTEM, engine) as s:
        rows = repo.missing_vectors(s, MODEL, installed_version() or "-", len(ids), ids)
        if not rows:
            return 0
        got = _embed(s, [r["body"] for r in rows], "passage", "complaints", f"batch of {len(rows)}")
        if got is None:
            return 0
        repo.store_vectors(s, MODEL, got[1], [(r["id"], v) for r, v in zip(rows, got[0], strict=True)])
        _mark_active(s, got[1])
    return len(rows)


def reembed(limit: int = 1000, engine=None) -> dict:
    """Vectors for complaints with none of the installed version, newest first, each batch committed on its own:
    an interrupted run loses at most the batch it was in, and the next run carries on where it stopped."""
    version = installed_version()
    if version is None:
        return {"embedded": 0, "left": None, "reason": "E5 not installed"}
    with session_for(SYSTEM, engine) as s:
        batch = int(router.setting(s, "ai.embed.reembed_batch", 64))
    done = 0
    while done < limit:
        with session_for(SYSTEM, engine) as s:
            rows = repo.missing_vectors(s, MODEL, version, min(batch, limit - done))
            if not rows:
                break
            got = _embed(s, [r["body"] for r in rows], "passage", "complaints", f"re-embed batch of {len(rows)}")
            if got is None:
                break
            repo.store_vectors(s, MODEL, got[1], [(r["id"], v) for r, v in zip(rows, got[0], strict=True)])
            _mark_active(s, got[1])
        done += len(rows)
    with session_for(SYSTEM, engine) as s:
        left = len(repo.missing_vectors(s, MODEL, version, 1_000_000))
    if done:
        log.info("complaints re-embedded", extra={"count": done, "left": left, "version": version})
    return {"embedded": done, "left": left}


def refresh_registry(engine=None, limit: int = 2000) -> dict:
    """Vectors for every registry name, "name, district" and alias (any script) of the installed version,
    computed once; labels gone from the registry lose theirs. Runs with each maintenance tick."""
    version = installed_version()
    if version is None:
        return {"added": 0, "removed": 0}
    with session_for(SYSTEM, engine) as s:
        removed = repo.registry_drop_stale(s, MODEL, version)
        rows = repo.registry_missing(s, MODEL, version, limit)
        got = _embed(s, [r["label"] for r in rows], "query", "institution_registry", f"{len(rows)} names") \
            if rows else None
        if got:
            repo.registry_store(s, MODEL, got[1], [(r["institution_id"], r["label"], v)
                                                   for r, v in zip(rows, got[0], strict=True)])
    return {"added": len(rows) if got else 0, "removed": removed}


def stages(ids: list[UUID], engine=None) -> None:
    """The A3 stages of the enrichment pipeline, on one batch: embed, classify, resolve the institution."""
    embed_complaints(ids, engine)
    classify_complaints(ids, engine)
    resolve_institutions(ids, engine)


def maintain(engine=None) -> dict:
    """The background job: registry vectors, a batch of re-embedding, and a first classifier."""
    done = {"registry": refresh_registry(engine), "reembed": reembed(engine=engine)}
    with session_for(SYSTEM, engine) as s:
        none_yet = not repo.classifier_versions(s)
    if none_yet and done["reembed"].get("left") is not None:
        done["classifier"] = retrain(None, engine)
    return done


# --- classification stage ----------------------------------------------------------------------------------

def classify_complaints(ids: list[UUID], engine=None) -> int:
    """Suggest a category for each complaint, once per (classifier version, vector version)."""
    with session_for(SYSTEM, engine) as s:
        clf, act = repo.active_classifier(s), active(s)
        keys = feedback.attempt_keys(s, "category", ids)
    usable = clf if clf and act and clf["embedding_version"] == act["version"] else None
    key = f"classifier-{usable['version'] if usable else 0}|{act['version'] if act else '-'}"
    done = 0
    for cid in ids:
        if keys.get(cid) == key:
            continue
        with session_for(SYSTEM, engine) as s:
            inp = repo.classify_inputs(s, cid)
            vector = repo.vector_of(s, cid, MODEL, act["version"]) if act else None
            payload = {"vector": vector, "artifact": usable and usable["artifact"],
                       "sha256": usable and usable["sha256"], "version": usable and usable["version"],
                       "text": "\n".join(t for t in (inp["body"], inp["translated_text"]) if t),
                       "tags": list(inp["tags"] or [])}
            r = router.run(s, SYSTEM, "classify.category", payload, subject_type="complaint", subject_id=str(cid))
            if r["status"] == "ok":
                out = r["output"]
                feedback.store(s, cid, "category", suggested=out["category"], candidates=out["top"],
                               path="model" if r["provider"] == "category-e5" else "fallback",
                               provider=r["provider"], confidence=r["confidence"],
                               model_version=out.get("model_version"), attempt_key=key, run_id=r["run_id"])
            else:
                feedback.store(s, cid, "category", suggested=None, candidates=[], path="officer", provider=None,
                               confidence=None, model_version=None, attempt_key=key, run_id=r["run_id"])
                enrichment.add_review(s, "category", cid, "category not suggested with enough confidence: "
                                      "an officer picks it", r["run_id"])
        done += 1
    return done


# --- institution resolution stage --------------------------------------------------------------------------

def institution_settings(session: Session) -> dict:
    return {key: float(router.setting(session, f"ai.institution.resolve.{key}", default)) for key, default in (
        ("e5_threshold", 0.93), ("e5_margin", 0.03), ("fuzzy_threshold", institutions.AUTO_ACCEPT),
        ("fuzzy_margin", institutions.RUNNER_UP_GAP))}


def resolve_institutions(ids: list[UUID], engine=None) -> int:
    """For complaints still unresolved: exact name or abbreviation first (deterministic), then E5 against the
    registry's names and aliases, then the alias dictionary and spelling. A link is made automatically only under
    the rules in app/ai/semantic.py; otherwise the officer queue gets the top three with their scores."""
    with session_for(SYSTEM, engine) as s:
        pending = institutions.unresolved_among(s, ids)
        keys = feedback.attempt_keys(s, "institution", [c["id"] for c in pending])
        rules = institution_settings(s)
    key = f"e5-{installed_version() or 'none'}"
    done = 0
    for c in pending:
        if keys.get(c["id"]) == key:
            continue
        with session_for(SYSTEM, engine) as s:
            _resolve_one(s, c, key, rules)
        done += 1
    return done


def _resolve_one(s: Session, c: dict, key: str, rules: dict) -> None:
    cid, raw = c["id"], c["institution_name_raw"]
    decision, ranked = institutions.rank(s, raw)
    if decision and decision["step"] in ("permanent_id", "alias"):      # exact name, alias or abbreviation
        institutions.auto_link(s, SYSTEM, cid, decision)
        return
    e5, version = [], None
    got = _embed(s, [raw], "query", "complaint", str(cid)) if installed_version() else None
    if got:
        version = got[1]
        e5 = repo.nearest_institutions(s, got[0][0], MODEL, version, 5)
    fuzzy = [{"institution_id": x["id"], "name": x["name"], "label": x["name"], "score": x["score"],
              "reason": x["reason"]} for x in ranked[:5]]
    r = router.run(s, SYSTEM, "institution.resolve",
                   {"e5": e5, "fuzzy": fuzzy, "acronym": institutions.is_acronym(raw), "settings": rules,
                    "model_version": version}, subject_type="complaint", subject_id=str(cid))
    out = r["output"] or {}
    path = {"institution-e5": "model", "institution-fuzzy": "fallback"}.get(r["provider"], "officer")
    top = out.get("top") or (e5 or fuzzy)[:TOP]
    for t in top:
        t["institution_id"] = str(t["institution_id"])
        t.setdefault("method", out.get("method") or ("e5" if e5 else "fuzzy"))
    status = "suggested"
    if r["status"] == "ok" and out.get("auto"):
        institutions.auto_link(s, SYSTEM, cid, {"institution_id": UUID(str(out["institution_id"])),
                                                "step": out["method"], "score": top[0]["score"]})
        status = "auto_linked"
    feedback.store(s, cid, "institution", suggested=top[0]["institution_id"] if top else None, candidates=top,
                   path=path, provider=r["provider"], confidence=r["confidence"], model_version=version,
                   attempt_key=key, run_id=r["run_id"], status=status)
    if status == "suggested":
        why = out.get("why") or "no confident match"
        enrichment.add_review(s, "institution", cid, f"institution not linked automatically ({why}): pick one of "
                              "the candidates in the resolution queue", r["run_id"])


# --- the classifier: bootstrap, training, activation, rollback ----------------------------------------------

@lru_cache
def bootstrap() -> list[dict]:
    return [json.loads(line) for line in BOOTSTRAP.read_text(encoding="utf-8").splitlines() if line.strip()]


def held_out(row: dict) -> bool:
    """A fixed fifth of the bootstrap set, chosen by the text's hash: the same for every version, so versions
    are compared on the same examples. Never trained on."""
    return int(hashlib.sha256(row["text"].encode()).hexdigest()[:8], 16) % 5 == 0


def retrain(requested_by: UUID | None, engine=None) -> dict:
    """Train a new version from the bootstrap set plus officers' accepted corrections, evaluate it on the
    held-out set, and activate it only if it does no worse than the active one. The previous version stays."""
    version = installed_version()
    if version is None:
        return {"status": "skipped", "reason": "E5 not installed: classification uses the keyword rules"}
    rows = bootstrap()
    vectors: list = []
    with session_for(SYSTEM, engine) as s:
        for i in range(0, len(rows), TRAIN_BATCH):
            got = _embed(s, [r["text"] for r in rows[i:i + TRAIN_BATCH]], "passage", "classifier_training",
                         f"bootstrap {i}-{i + TRAIN_BATCH}")
            if got is None or got[1] != version:
                return {"status": "skipped", "reason": "E5 gave no vectors"}
            vectors += got[0]
        fixes = repo.corrections(s, MODEL, version)
    train_x = [v for r, v in zip(rows, vectors, strict=True) if not held_out(r)] + [json.loads(f["vector"])
                                                                                     for f in fixes]
    train_y = [r["category"] for r in rows if not held_out(r)] + [f["category"] for f in fixes]
    hold_x = [v for r, v in zip(rows, vectors, strict=True) if held_out(r)]
    hold_y = [r["category"] for r in rows if held_out(r)]
    artifact, metrics = classify.train(train_x, train_y, hold_x, hold_y, MODEL, version)
    metrics |= {"bootstrap": len(rows) - len(hold_y), "corrections": len(fixes)}
    with session_for(SYSTEM, engine) as s:
        current = repo.active_classifier(s)
        previous = None
        if current and current["embedding_version"] == version:
            previous = classify.evaluate(classify.load(current["artifact"], current["sha256"]), hold_x,
                                         hold_y)["holdout_accuracy"]
        better = previous is None or metrics["holdout_accuracy"] >= previous
        metrics["compared_with"] = {"version": current and current["version"], "holdout_accuracy": previous}
        if better:
            repo.deactivate_classifiers(s)
        number = repo.insert_classifier(s, artifact=artifact, sha256=classify.checksum(artifact), model=MODEL,
                                        version=version, metrics=metrics, status="active" if better else "rejected",
                                        created_by=requested_by)
        audit.record(s, SYSTEM, "classifier.trained", entity_type="classifier_versions", entity_id=str(number),
                     payload={"version": number, "activated": better, "holdout_accuracy": metrics["holdout_accuracy"],
                              "previous_version": current and current["version"], "previous_accuracy": previous,
                              "corrections": len(fixes), "requested_by": requested_by and str(requested_by),
                              "sha256": classify.checksum(artifact)})
    return {"status": "activated" if better else "kept previous", "version": number, "metrics": metrics}


def activate(session: Session, principal: Principal, version: int) -> dict:
    """Admin rollback (or roll forward) to a stored version. Its artifact is checked before it is used."""
    found = repo.classifier(session, version)
    if found is None:
        raise SemanticError(404, "no such classifier version")
    if found["status"] == "active":
        raise SemanticError(409, "this version is already active")
    if found["status"] == "rejected":
        raise SemanticError(409, "this version did worse than the one active when it was trained: retrain instead")
    try:
        classify.load(found["artifact"], found["sha256"])
    except classify.ArtifactError as e:
        raise SemanticError(422, f"refused: {e}") from e
    current = repo.active_classifier(session)
    repo.deactivate_classifiers(session)
    repo.activate_classifier(session, version)
    audit.record(session, principal, "classifier.activated", entity_type="classifier_versions",
                 entity_id=str(version), payload={"version": version, "previous": current and current["version"]})
    return {"version": version, "previous": current and current["version"]}


def classifiers(session: Session) -> list[dict]:
    return repo.classifier_versions(session)


def coverage(session: Session) -> dict:
    """For the AI health screen: vectors per model and version, against all complaints."""
    return {"complaints": repo.complaint_count(session), "vectors": repo.vector_counts(session),
            "active": active(session)}


# --- the case page: suggestions and the officer's decisions --------------------------------------------------

def for_case(session: Session, complaint_id: UUID) -> dict:
    return {"category": feedback.get(session, complaint_id, "category"),
            "institution": feedback.get(session, complaint_id, "institution"),
            "categories": sorted(set(classify.RULES) | set(complaints.options(session).get("categories") or []))}


def decide_category(session: Session, principal: Principal, complaint_id: UUID, category: str) -> dict:
    """Accept the suggested category, keep the current one (reject), or set another (change). The bureau holding
    the case decides (the database checks); the change, the feedback row and the audit entries are one
    transaction."""
    found = feedback.get(session, complaint_id, "category")
    if found is None:
        raise SemanticError(404, "no category suggestion for this case")
    if found["status"] != "suggested":
        raise SemanticError(409, f"this suggestion was already {found['status']}")
    try:
        old = complaints.set_category(session, principal, complaint_id, category)
    except complaints.CaseError as e:
        raise SemanticError(e.status, str(e)) from e
    return feedback.decide(session, principal, complaint_id, "category", category, old,
                           complaints.actor_id(session, principal)) or {}
