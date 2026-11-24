"""Overlap detection: the system suggests, a person decides.

Tier 1: open cases at one institution held by two or more bureaus. Shown, never
stored, and no link is suggested.
Tier 2: two open cases in different bureaus at the same institution, in the same
category, filed within 30 days of each other, whose texts are similar. Stored as a
`proposed` link (the suggestion) until an officer or head of either bureau
approves or rejects it. Approving queues an alert to both bureau heads.

Matching, inside the rules, is AI task "match.complaints" through the A1 router (provenance, circuit breaker,
confidence threshold): e5-match (cosine of the two complaints' E5 vectors, any languages) -> text-match (pg_trgm
similarity, same language only: what SETHU used before A3) -> a person (the pair is suggested, marked for officer
review, only if a signal crossed its threshold). Each pair is judged once per `match_key` (model version, both
thresholds, category, institution), so a run only judges new or changed pairs. Every suggestion stores its
evidence in `signals` (method, similarity, confidence, agreement, model version, the shared institution and
category, both complaint ids, the ai_runs row) and an explanation in `reasons`. The vectors are made by the
ai-worker (app/modules/semantic), stay in the database under the text's Row-Level Security, and are never returned
by an API or logged. With SETHU_SEMANTIC_OVERLAP off or no E5 vectors, matching is exactly the trigram rule.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import router
from app.ai import suggestions as feedback
from app.ai.e5 import MODEL as E5
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
METHOD = {"e5": "E5 meaning similarity (any language)", "text": "text similarity (trigram fallback)",
          "officer": "no confident answer: an officer decides"}


class OverlapError(Exception):
    """A request that cannot be carried out. `status` is the HTTP status to answer with."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def match_settings(session: Session) -> dict:
    return {key: float(router.setting(session, f"ai.match.complaints.{key}", default)) for key, default in (
        ("e5_threshold", 0.88), ("trigram_threshold", SIMILARITY_THRESHOLD), ("confidence_span", 0.06),
        ("agreement_bonus", 0.15), ("disagreement_penalty", 0.25))}


def active_embedding(session: Session) -> dict | None:
    """{"model", "version"} of the E5 vectors the ai-worker makes now (it writes this setting), or None."""
    found = router.setting(session, "ai.embedding.active", None)
    return found if isinstance(found, dict) and found.get("model") == E5 and found.get("version") else None


def detect(session: Session, principal: Principal) -> dict:
    """Judge new or changed rule-allowed pairs and store each match as a suggestion. Safe to repeat. Judges at
    most `detect_batch` pairs; {"more": True} means call again in a new transaction (the worker does)."""
    s, batch = match_settings(session), get_settings().detect_batch
    active = active_embedding(session)
    model, version = (active["model"], active["version"]) if active else (None, None)
    todo = []
    for p in repo.candidates(session, WINDOW_DAYS, model, version):
        vectors = f"{model}@{version}" if p["semantic"] is not None else "no-vectors"
        key = (f"{vectors}|e5>={s['e5_threshold']:g}|trgm>={s['trigram_threshold']:g}"
               f"|{p['category']}|{p['institution_id']}")
        if p["last_key"] != key:
            todo.append((p, key))
    created = []
    for p, key in todo[:batch]:
        created += _judge(session, principal, p, key, s, version)
    ref = repo.refs(session, [c for row in created for c in (row["a"], row["b"])])
    for row in created:
        audit.record(session, principal, "overlap.suggested", entity_type="overlap_links", entity_id=str(row["id"]),
                     payload={"cases": sorted([ref[row["a"]], ref[row["b"]]]), "tier": 2, "score": row["score"],
                              "method": row["signals"]["method"], "confidence": row["signals"]["confidence"],
                              "model_version": row["signals"].get("model_version")})
    return {"suggested": len(created)} | ({"more": True} if len(todo) > batch else {})


def _judge(session: Session, principal: Principal, p: dict, key: str, s: dict, version: str | None) -> list[dict]:
    a, b = p["complaint_a"], p["complaint_b"]
    semantic = None if p["semantic"] is None else float(p["semantic"])
    trigram = float(p["trigram"])
    pair = {"semantic": semantic, "trigram": trigram, "same_language": bool(p["same_language"])}
    r = router.run(session, principal, "match.complaints", {"pair": pair, "settings": s, "model_version": version},
                   subject_type="complaint_pair", subject_id=f"{a}:{b}")
    if r["status"] == "ok":
        out = r["output"]
        matched, method, score, confidence = out["matched"], out["method"], out["score"], r["confidence"]
        agreement = out.get("agreement")
    else:   # last resort: suggest only, for an officer, when a signal crossed its threshold
        matched = (semantic is not None and semantic >= s["e5_threshold"]) or trigram >= s["trigram_threshold"]
        method, score, confidence, agreement = "officer", max(trigram, semantic or 0.0), None, None
    repo.save_evaluation(session, a, b, key, matched, method, score, confidence, r["run_id"])
    if not matched:
        return []
    signals = {"method": method, "similarity": score, "confidence": confidence, "agreement": agreement,
               "trigram": trigram, "semantic": semantic, "same_language": pair["same_language"],
               "fired": [n for n, v, t in (("trigram", trigram, s["trigram_threshold"]),
                                            ("semantic", semantic, s["e5_threshold"])) if v is not None and v >= t],
               "model": E5 if semantic is not None else None,
               "model_version": version if semantic is not None else None,
               "thresholds": {"e5": s["e5_threshold"], "trigram": s["trigram_threshold"]},
               "shared": {"institution_id": str(p["institution_id"]), "category": p["category"]},
               "complaints": [str(a), str(b)], "run_id": r["run_id"]}
    reasons = ["same institution", f"same category: {p['category']}", f"filed {p['days_apart']} days apart",
               f"text similarity {trigram:.2f}" + (" (fired)" if trigram >= s["trigram_threshold"] else "")]
    if semantic is not None:
        reasons.append(f"meaning similarity {semantic:.2f}" + (" (fired)" if semantic >= s["e5_threshold"] else ""))
    reasons.append(f"decided by: {METHOD[method]}"
                   + (f", confidence {confidence:.2f}" if confidence is not None else "")
                   + (f", the two signals {agreement}" if agreement in ("agree", "disagree") else ""))
    link_id = repo.insert_link(session, a, b, score, reasons, signals)
    return [{"id": link_id, "a": a, "b": b, "score": score, "signals": signals}] if link_id else []


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
    keep = ("id", "tier", "score", "reasons", "signals", "status", "created_at", "decided_at", "decided_by",
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
    method = (link["signals"] or {}).get("method")
    feedback.record(session, principal, "overlap", link["a_id"], "accepted" if approve else "rejected",
                    actor_id=actor, suggested="overlap", old="proposed", new="approved" if approve else "rejected",
                    suggested_path={"e5": "model", "text": "fallback", "officer": "officer"}.get(method, "fallback"),
                    overlap_link_id=link_id)
    return _shape(principal, repo.links(session, link_id=link_id)[0])
