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
from collections import Counter
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from statistics import median
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import suggestions
from app.audit import service as audit
from app.core.auth import Principal
from app.modules.institutions import repo
from app.modules.users import service as users

AUTO_ACCEPT = 95.0     # minimum fuzzy score to link without a person
RUNNER_UP_GAP = 5.0    # and the next institution must be at least this far behind
TOP = 3                # candidates shown to the officer

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
    if is_acronym(raw):
        for inst in repo.by_acronym(session, first):
            offer(inst, 90 if rest and normalize(rest) == normalize(inst["district"] or "") else 75, "acronym")

    ranked = sorted(best.values(), key=lambda c: (-c["score"], c["name"]))
    if len(exact) == 1:
        return {"institution_id": next(iter(exact)), "step": "alias", "score": 100.0}, ranked
    if not exact and ranked and ranked[0]["score"] >= AUTO_ACCEPT and (
            len(ranked) == 1 or ranked[0]["score"] - ranked[1]["score"] >= RUNNER_UP_GAP):
        return {"institution_id": ranked[0]["id"], "step": "fuzzy", "score": ranked[0]["score"]}, ranked
    return None, ranked


def is_acronym(raw: str) -> bool:
    """"SCE Nagpur", "GIT": too many colleges share initials, so such a name is never linked automatically."""
    first = raw.strip().partition(" ")[0].strip(".,")
    return first.isalpha() and first.isupper() and 2 <= len(first) <= 6


def auto_link(session: Session, principal: Principal, complaint_id: UUID, decision: dict) -> bool:
    """Link an unresolved complaint without a person (the cascade's rules allowed it). Audited."""
    row = repo.set_resolution(session, complaint_id, decision["institution_id"], "auto")
    if row:
        audit.record(session, principal, "institution.resolve", entity_type="complaints", entity_id=str(complaint_id),
                     payload={"ref": row["ref"], "institution_id": str(decision["institution_id"]),
                              "step": decision["step"], "score": decision["score"]})
    return bool(row)


def unresolved_among(session: Session, ids: list[UUID]) -> list[dict]:
    return repo.unresolved(session, len(ids), ids) if ids else []


def resolve_pending(session: Session, principal: Principal, limit: int = 500) -> dict[str, int]:
    """Run the deterministic cascade over unresolved complaints the caller can write. Safe to repeat. (The
    ai-worker adds the E5 step for what is left: app/modules/semantic.)"""
    pending = repo.unresolved(session, limit)
    resolved = 0
    for c in pending:
        decision, _ = rank(session, c["institution_name_raw"])
        if decision and auto_link(session, principal, c["id"], decision):
            resolved += 1
    return {"resolved": resolved, "queued": len(pending) - resolved}


def queue(session: Session, limit: int = 50) -> list[dict]:
    """Unresolved complaints visible to the caller, each with its top three candidates: the AI's (E5, with the
    cosine score) when the ai-worker made a suggestion, then the spelling cascade's."""
    out = []
    for c in repo.unresolved(session, limit):
        found = suggestions.get(session, c["id"], "institution")
        ai = [{"id": UUID(t["institution_id"]), "permanent_id": None, "name": t.get("name") or t.get("label"),
               "state": None, "district": None,
               "score": round(float(t["score"]) * 100, 1) if t.get("method") == "e5" else float(t["score"]),
               "reason": "meaning match (E5)" if t.get("method") == "e5" else t.get("reason") or "similar spelling"}
              for t in (found or {}).get("candidates") or []]
        seen = {a["id"] for a in ai}
        merged = ai + [x for x in rank(session, c["institution_name_raw"])[1] if x["id"] not in seen]
        out.append(c | {"candidates": merged[:TOP]})
    return out


def resolve_by_officer(session: Session, principal: Principal, complaint_id: UUID,
                       institution_id: UUID) -> dict | None:
    """An officer's choice from the queue or the case page. The typed name becomes an alias, so the same
    spelling resolves by itself next time; an open AI suggestion is marked accepted or changed (ai_feedback).
    None if either id is not found."""
    if not repo.get(session, institution_id):
        return None
    row = repo.set_resolution(session, complaint_id, institution_id, "officer")
    if not row:
        return None
    alias_added = repo.add_alias(session, institution_id, row["institution_name_raw"].strip(), "officer")
    audit.record(session, principal, "institution.resolve", entity_type="complaints", entity_id=str(complaint_id),
                 payload={"ref": row["ref"], "institution_id": str(institution_id), "step": "officer",
                          "alias_added": alias_added})
    suggestions.decide(session, principal, complaint_id, "institution", str(institution_id), None,
                       users.sync(session, principal) if principal.role != "system" else None)
    return {"ref": row["ref"], "institution_id": institution_id, "alias_added": alias_added}


def list_institutions(session: Session, q: str | None, state: str | None, limit: int, offset: int) -> list[dict]:
    """All institutions by name, or the ones matching q (the same search as the top bar), best first.
    Each row carries its case counts across all bureaus."""
    state = (state or "").strip() or None
    if not (q and q.strip()):
        return repo.list_institutions(session, state, limit, offset)
    hits = [h for h in lookup(session, q, 200) if not state or h["state"] == state][offset:offset + limit]
    found = repo.counts(session, [h["id"] for h in hits])
    return [h | {"complaints": found.get(h["id"], {}).get("complaints", 0),
                 "open": found.get(h["id"], {}).get("open", 0)} for h in hits]


def lookup(session: Session, q: str, limit: int) -> list[dict]:
    """The one institution search, used by the Institutions screen and the top-bar search.
    Matches name or alias (pg_trgm), permanent id, initials, city (district) or state; each hit says why."""
    q = q.strip()
    if not q:
        return []
    found: dict[UUID, dict] = {}

    def add(row: dict, score: float, why: str) -> None:
        if row["id"] not in found or score > found[row["id"]]["score"]:
            found[row["id"]] = {k: row[k] for k in ("id", "permanent_id", "name", "state", "district")} | {
                "score": round(score, 1), "why": why}

    for row in repo.candidates(session, q, limit * 3):
        exact = row["label"].lower() == q.lower()
        what = "name" if row["label"] == row["name"] else f"also known as \"{row['label']}\""
        # A match on one word of a long name ("Greenfeild", "Pune") counts for less than the whole name.
        add(row, 100 if exact else max(row["similarity"] * 100, row["word"] * 70),
            f"{what}: {'same spelling' if exact else 'similar spelling'}")
    for row in repo.in_place(session, q, limit):
        if row["in_district"]:
            add(row, 80, f"city: {row['district']}")
        else:
            add(row, 70, f"state: {row['state']}")
    if (pid := PERMANENT_ID.search(q)) and (inst := repo.by_permanent_id(session, pid.group())):
        add(inst, 100, "permanent id")
    first = q.split(" ")[0].strip(".,")
    if first.isalpha() and 2 <= len(first) <= 6:
        for inst in repo.by_acronym(session, first):
            add(inst, 75, f"initials {first.upper()}")
    return sorted(found.values(), key=lambda r: (-r["score"], r["name"]))[:limit]


RECURRENCE_DAYS = 180  # a complaint "recurs" if the same category was raised here this recently
TREND_DAYS = 90


def dna(cases: list[dict], now: datetime) -> dict:
    """Profile DNA: six measures from case summaries only (no text), counts not judgements.

    category_mix  cases per category, largest first
    volume        all cases, the last 12 months, and the monthly average over those 12 months
    recurrence    cases whose category was already raised here in the 180 days before
    disposal      closed cases and the median days from filing to closing
    bureaus       cases per bureau
    trend         the last 90 days against the 90 before
    """
    total = len(cases)
    by_category = Counter(c["category"] or "Uncategorised" for c in cases)
    last_year = sum(c["filed_at"] >= now - timedelta(days=365) for c in cases)

    repeats, seen = [], {}
    for c in sorted(cases, key=lambda c: c["filed_at"]):
        key = c["category"] or "Uncategorised"
        if key in seen and c["filed_at"] - seen[key] <= timedelta(days=RECURRENCE_DAYS):
            repeats.append(key)
        seen[key] = c["filed_at"]

    days = [(c["closed_at"] - c["filed_at"]).total_seconds() / 86400 for c in cases if c["closed_at"]]
    recent = sum(c["filed_at"] >= now - timedelta(days=TREND_DAYS) for c in cases)
    previous = sum(now - timedelta(days=2 * TREND_DAYS) <= c["filed_at"] < now - timedelta(days=TREND_DAYS)
                   for c in cases)
    return {
        "category_mix": [{"category": k, "cases": n, "share": round(n / total, 2)}
                         for k, n in sorted(by_category.items(), key=lambda kv: (-kv[1], kv[0]))],
        "volume": {"total": total, "last_12_months": last_year, "per_month": round(last_year / 12, 1)},
        "recurrence": {"repeat_cases": len(repeats), "share": round(len(repeats) / total, 2) if total else 0.0,
                       "categories": sorted(set(repeats)), "window_days": RECURRENCE_DAYS},
        "disposal": {"closed": len(days), "median_days": round(median(days), 1) if days else None},
        "bureaus": [{"bureau": b, "cases": n} for b, n in sorted(Counter(c["bureau"] for c in cases).items())],
        "trend": {"recent": recent, "previous": previous, "window_days": TREND_DAYS,
                  "direction": "up" if recent > previous else "down" if recent < previous else "flat"},
    }


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
        "dna": dna(cases, datetime.now(UTC)),
    }
