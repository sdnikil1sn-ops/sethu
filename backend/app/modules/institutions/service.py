"""Institution list, profile and name resolution.

Resolution cascade (docs/ARCHITECTURE.md section 5), steps 1 to 3:
  1. a permanent ID written in the typed name;
  2. the typed name is exactly a known spelling, once abbreviations are expanded
     (with the district, when the complainant wrote one);
  3. fuzzy match: pg_trgm picks candidates, a similarity ratio scores them, and
     only a score of 95+ that is clear of the runner-up is accepted.
Anything else stays `unresolved` and shows in the officer queue with the best
five candidates. Fully deterministic: no AI model is involved.
"""
import re
from difflib import SequenceMatcher
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.modules.institutions import repo

AUTO_ACCEPT = 95.0     # minimum fuzzy score to link without a person
RUNNER_UP_GAP = 5.0    # and the next institution must be at least this far behind
TOP = 5                # candidates shown to the officer

PERMANENT_ID = re.compile(r"\b\d-\d{6,}\b")
ABBREVIATIONS = {
    "inst": "institute", "instt": "institute", "tech": "technology", "coll": "college", "engg": "engineering",
    "engr": "engineering", "mgmt": "management", "poly": "polytechnic", "arch": "architecture",
    "pharm": "pharmacy", "univ": "university", "sci": "science", "govt": "government", "&": "and",
}


def normalize(name: str) -> str:
    """Lower case, punctuation dropped, common abbreviations written out."""
    return " ".join(ABBREVIATIONS.get(t, t) for t in re.findall(r"[a-z0-9&]+", name.lower()))


def _candidate(inst: dict, score: float, reason: str) -> dict:
    return {k: inst[k] for k in ("id", "permanent_id", "name", "state", "district")} | {
        "score": round(score, 1), "reason": reason}


def rank(session: Session, raw: str) -> tuple[dict | None, list[dict]]:
    """Run the cascade on one typed name.

    Returns (decision, candidates). decision is None when a person must choose;
    candidates are the best matches, highest score first.
    """
    pid = PERMANENT_ID.search(raw)
    if pid and (inst := repo.by_permanent_id(session, pid.group())):
        return ({"institution_id": inst["id"], "step": "permanent_id", "score": 100.0},
                [_candidate(inst, 100, "permanent id")])

    wanted = normalize(raw)
    if not wanted:
        return None, []
    best: dict[UUID, dict] = {}
    exact: set[UUID] = set()

    def offer(inst: dict, score: float, reason: str) -> None:
        if score > best.get(inst["id"], {"score": -1.0})["score"]:
            best[inst["id"]] = _candidate(inst, score, reason)

    for row in repo.candidates(session, wanted, 25):
        spellings = (normalize(row["label"]), normalize(f"{row['label']} {row['district'] or ''}"))
        if wanted in spellings:
            exact.add(row["id"])
            offer(row, 100, "known spelling")
        else:
            offer(row, max(SequenceMatcher(None, wanted, s).ratio() for s in spellings) * 100, "similar spelling")

    # Acronyms ("SCE Nagpur") are only ever a suggestion: too many colleges share initials.
    first, _, rest = raw.strip().partition(" ")
    first = first.strip(".,")
    if first.isalpha() and first.isupper() and 2 <= len(first) <= 6:
        for inst in repo.by_acronym(session, first):
            offer(inst, 90 if rest and normalize(rest) == normalize(inst["district"] or "") else 75, "acronym")

    ranked = sorted(best.values(), key=lambda c: (-c["score"], c["name"]))
    if len(exact) == 1:
        return {"institution_id": next(iter(exact)), "step": "alias", "score": 100.0}, ranked
    if not exact and ranked and ranked[0]["score"] >= AUTO_ACCEPT and (
            len(ranked) == 1 or ranked[0]["score"] - ranked[1]["score"] >= RUNNER_UP_GAP):
        return {"institution_id": ranked[0]["id"], "step": "fuzzy", "score": ranked[0]["score"]}, ranked
    return None, ranked


def resolve_pending(session: Session, principal: Principal, limit: int = 500) -> dict[str, int]:
    """Run the cascade over unresolved complaints the caller can write. Safe to repeat."""
    pending = repo.unresolved(session, limit)
    resolved = 0
    for c in pending:
        decision, _ = rank(session, c["institution_name_raw"])
        if decision and repo.set_resolution(session, c["id"], decision["institution_id"], "auto"):
            audit.record(session, principal, "institution.resolve", entity_type="complaints",
                         entity_id=str(c["id"]),
                         payload={"ref": c["ref"], "institution_id": str(decision["institution_id"]),
                                  "step": decision["step"], "score": decision["score"]})
            resolved += 1
    return {"resolved": resolved, "queued": len(pending) - resolved}


def queue(session: Session, limit: int = 50) -> list[dict]:
    """Unresolved complaints visible to the caller, each with candidates to pick from."""
    return [c | {"candidates": rank(session, c["institution_name_raw"])[1][:TOP]}
            for c in repo.unresolved(session, limit)]


def resolve_by_officer(session: Session, principal: Principal, complaint_id: UUID,
                       institution_id: UUID) -> dict | None:
    """An officer's choice from the queue. The typed name becomes an alias, so the
    same spelling resolves by itself next time. None if either id is not found."""
    if not repo.get(session, institution_id):
        return None
    row = repo.set_resolution(session, complaint_id, institution_id, "officer")
    if not row:
        return None
    alias_added = repo.add_alias(session, institution_id, row["institution_name_raw"].strip(), "officer")
    audit.record(session, principal, "institution.resolve", entity_type="complaints", entity_id=str(complaint_id),
                 payload={"ref": row["ref"], "institution_id": str(institution_id), "step": "officer",
                          "alias_added": alias_added})
    return {"ref": row["ref"], "institution_id": institution_id, "alias_added": alias_added}


def list_institutions(session: Session, q: str | None, state: str | None, limit: int, offset: int) -> list[dict]:
    """All institutions by name, or the ones matching q (names and aliases), best first."""
    if not (q and q.strip()):
        return repo.list_institutions(session, state, limit, offset)
    found: dict[UUID, dict] = {}
    for row in repo.candidates(session, q.strip(), limit * 3):
        found.setdefault(row["id"], row | {"matched": row["label"], "score": round(row["similarity"] * 100, 1)})
    # Nothing looks alike (an unknown acronym, say): fall back to the cascade's suggestions.
    results = list(found.values()) or rank(session, q)[1]
    return [r for r in results if not state or r["state"] == state][:limit]


def profile(session: Session, institution_id: UUID) -> dict | None:
    inst = repo.get(session, institution_id)
    if not inst:
        return None
    cases = repo.summaries(session, institution_id)
    still_open = [c for c in cases if c["status"] != "closed"]
    return inst | {
        "aliases": repo.aliases(session, institution_id),
        "bureaus": sorted({c["bureau"] for c in cases}),
        "open": len(still_open),
        "closed": len(cases) - len(still_open),
        "oldest_open": min(still_open, key=lambda c: c["filed_at"], default=None),
        "complaints": cases,
    }
