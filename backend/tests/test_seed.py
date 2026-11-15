"""The seed data must contain exactly the detections promised in
docs/04-MOCK-DATA-SPEC.md. The detectors are not built yet, so each rule below
is the simplest reading of the spec, applied to the CSV files and compared with
the answer key in the seed_tags column.
"""
import hashlib
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import pytest
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for the seed package

from seed import generate, load  # noqa: E402

from app.audit.service import verify  # noqa: E402
from app.db.session import SYSTEM, session_for  # noqa: E402
from tests.conftest import requires_db  # noqa: E402

INSTITUTIONS, USERS, COMPLAINTS, ACTIONS = (load.rows(name) for name in generate.FILES)
STATE = {i["permanent_id"]: i["state"] for i in INSTITUTIONS}
NAME = {i["permanent_id"]: i["name"] for i in INSTITUTIONS}
HISTORY = defaultdict(list)
for _a in ACTIONS:
    HISTORY[_a["complaint_ref"]].append(_a)


def tagged(prefix: str) -> set[str]:
    return {c["ref"] for c in COMPLAINTS if any(t.startswith(prefix) for t in c["seed_tags"].split(";"))}


def tagged_pairs(prefix: str) -> set[frozenset]:
    groups = defaultdict(set)
    for c in COMPLAINTS:
        for t in c["seed_tags"].split(";"):
            if t.startswith(prefix):
                groups[t].add(c["ref"])
    return {frozenset(g) for g in groups.values()}


def cross_bureau_pairs(same_category: bool) -> set[frozenset]:
    """Tier 1: same institution, different bureaus. Tier 2: also the same category."""
    return {
        frozenset((a["ref"], b["ref"]))
        for a, b in combinations(COMPLAINTS, 2)
        if a["institution_pid"] == b["institution_pid"] and a["bureau"] != b["bureau"]
        and (a["category"] == b["category"]) == same_category
    }


def duplicate_pairs() -> set[frozenset]:
    by_hash = defaultdict(set)
    for c in COMPLAINTS:
        by_hash[hashlib.sha256(c["body"].encode()).hexdigest()].add(c["ref"])
    return {frozenset(refs) for refs in by_hash.values() if len(refs) > 1}


def deadlocks() -> set[str]:
    """Transferred away and back to where it started, with no hop acknowledged."""
    found = set()
    for ref, history in HISTORY.items():
        hops = [a for a in history if a["action"] == "transferred"]
        if len(hops) > 1 and hops[-1]["to_bureau"] == hops[0]["from_bureau"] \
                and not any(h["acknowledged_days_ago"] for h in hops):
            found.add(ref)
    return found


def not_closed(min_age: float) -> set[str]:
    return {c["ref"] for c in COMPLAINTS if c["status"] != "closed" and float(c["filed_days_ago"]) > min_age}


def silent() -> set[str]:
    return {ref for ref in not_closed(0) if min(float(a["days_ago"]) for a in HISTORY[ref]) > 30}


def spikes() -> set[tuple[str, str]]:
    """Last 21 days against the average 21-day count of the 159 days before."""
    recent, earlier = Counter(), Counter()
    for c in COMPLAINTS:
        cell = (STATE[c["institution_pid"]], c["category"])
        (recent if float(c["filed_days_ago"]) <= 21 else earlier)[cell] += 1
    return {cell for cell, n in recent.items() if n >= 5 and n >= 4 * earlier[cell] * 21 / 159}


def test_files_are_what_the_generator_produces():
    built = generate.build()
    assert built == generate.build()
    for name in generate.FILES:
        on_disk = (generate.HERE / f"{name}.csv").read_text(encoding="utf-8")
        assert on_disk == generate.render(built[name]), f"run `python seed/generate.py` and commit {name}.csv"


def test_volume():
    assert len(INSTITUTIONS) == 40 and len(set(STATE.values())) == 6
    assert len(COMPLAINTS) == 300 == len({c["ref"] for c in COMPLAINTS})
    assert all(1 <= int(c["filed_days_ago"]) <= 180 for c in COMPLAINTS)
    assert {c["bureau"] for c in COMPLAINTS} == {"PGRC", "RB"}
    assert Counter(u["role"] for u in USERS) == {"officer": 12, "bureau_head": 3, "admin": 1, "auditor": 1}
    assert len({u["desk"] for u in USERS if u["desk"]}) == 3
    assert all(u["email"].endswith("@sethu.test") for u in USERS)
    assert all(HISTORY[c["ref"]][0]["action"] == "filed" for c in COMPLAINTS)


def test_demo_records():
    demo = {c["ref"]: c for c in COMPLAINTS if c["ref"] in ("C-101", "C-102", "C-103")}
    assert [(c["bureau"], c["filed_days_ago"], c["institution_name_raw"], c["category"]) for c in demo.values()] == [
        ("PGRC", "12", "Greenfield Institute of Technology", "Faculty shortage"),
        ("RB", "6", "Greenfield Inst. of Tech., Pune", "Faculty shortage"),
        ("PGRC", "3", "GIT Pune", "Fee refund"),
    ]
    greenfield = INSTITUTIONS[0]
    assert (greenfield["name"], greenfield["district"], greenfield["state"]) == (
        "Greenfield Institute of Technology", "Pune", "Maharashtra")
    assert {c["institution_pid"] for c in demo.values()} == {greenfield["permanent_id"]}
    assert greenfield["aliases"].split("|") == generate.GREENFIELD_ALIASES


def test_expected_detections():
    tier2 = cross_bureau_pairs(same_category=True)
    assert len(tier2) == 6 and tier2 == tagged_pairs("tier2:")
    assert frozenset(("C-101", "C-102")) in tier2

    duplicates = duplicate_pairs()
    assert len(duplicates) == 5 and duplicates == tagged_pairs("dup:")

    assert deadlocks() == {"C-090"}
    assert len(silent()) == 8 and silent() == tagged("silent")
    assert spikes() == {(generate.SPIKE_STATE, generate.SPIKE_CATEGORY)}


def test_other_seeded_patterns():
    tier1_only = cross_bureau_pairs(same_category=False)
    assert len(tier1_only) == 10 and tier1_only == tagged_pairs("tier1:")
    assert len(not_closed(21)) == 25 and not_closed(21) == tagged("overdue")
    variants = {c["ref"] for c in COMPLAINTS if c["institution_name_raw"] != NAME[c["institution_pid"]]}
    assert len(variants) == 40 and variants == tagged("variant")
    hindi = [c for c in COMPLAINTS if c["language"] == "hi"]
    assert len(hindi) == 15 and all("ऀ" <= c["body"][0] <= "ॿ" or c["body"][0].isdigit() for c in hindi)


def test_negative_cases_raise_nothing():
    negatives = tagged("neg-") | tagged("transfer-ack")
    assert len(tagged("neg-")) == 6 and len(tagged("transfer-ack")) == 7
    flagged = set().union(*cross_bureau_pairs(True), *cross_bureau_pairs(False), *duplicate_pairs(),
                          deadlocks(), silent())
    assert not negatives & flagged
    by_tag = {tag: [c for c in COMPLAINTS if c["seed_tags"] == tag]
              for tag in ("neg-similar-text", "neg-same-bureau", "neg-same-category")}
    a, b = by_tag["neg-similar-text"]  # similar text, different states and institutions
    assert STATE[a["institution_pid"]] != STATE[b["institution_pid"]] and a["body"] != b["body"]
    assert a["body"].split()[:6] == b["body"].split()[:6]
    a, b = by_tag["neg-same-bureau"]  # same institution and category, one bureau
    assert (a["institution_pid"], a["bureau"], a["category"]) == (b["institution_pid"], b["bureau"], b["category"])
    a, b = by_tag["neg-same-category"]  # same category across bureaus, different institutions
    assert a["category"] == b["category"] and a["bureau"] != b["bureau"]
    assert a["institution_pid"] != b["institution_pid"]


@requires_db
def test_loader_writes_actions_and_audit(app_engine):
    counts = load.load(app_engine)
    assert counts["complaints"] == 300 and counts["case_actions"] == len(ACTIONS)

    with session_for(SYSTEM, app_engine) as s:
        def scalar(sql):
            return s.execute(text(sql)).scalar_one()

        assert scalar("SELECT count(*) FROM sethu.case_actions") == len(ACTIONS)
        assert scalar("SELECT count(*) FROM sethu.audit_log WHERE action = 'complaint.created'") == 300
        assert scalar("SELECT count(*) FROM sethu.audit_log WHERE action LIKE 'case.%'") == len(ACTIONS)
        assert scalar("SELECT count(*) FROM sethu.audit_log WHERE payload::text LIKE '%sanctioned%'") == 0
        chain = verify(s)
        assert chain.ok and chain.checked == scalar("SELECT count(*) FROM sethu.audit_log")

        # The same detections, read back from the database.
        assert scalar("SELECT count(*) FROM (SELECT 1 FROM sethu.complaints GROUP BY body_sha256"
                      " HAVING count(*) > 1) d") == 5
        assert scalar("SELECT count(*) FROM sethu.complaints a JOIN sethu.complaints b"
                      " ON a.institution_id = b.institution_id AND a.category = b.category"
                      " AND a.bureau_id <> b.bureau_id AND a.id < b.id") == 6
        assert scalar("SELECT count(*) FROM sethu.complaints WHERE status <> 'closed' AND due_at < now()") == 25
        assert scalar("SELECT count(*) FROM sethu.complaints c WHERE status <> 'closed' AND NOT EXISTS"
                      " (SELECT 1 FROM sethu.case_actions a WHERE a.complaint_id = c.id"
                      "  AND a.created_at > now() - interval '30 days')") == 8
        assert scalar("SELECT count(*) FROM sethu.case_actions a JOIN sethu.complaints c ON c.id = a.complaint_id"
                      " WHERE c.ref = 'C-090' AND a.action = 'transferred' AND a.acknowledged_at IS NULL") == 2
        assert scalar("SELECT count(DISTINCT institution_id) FROM sethu.complaints"
                      " WHERE ref IN ('C-101', 'C-102', 'C-103')") == 1
        assert scalar("SELECT count(*) FROM sethu.complaints WHERE resolution_state = 'unresolved'") == 38

    with pytest.raises(RuntimeError, match="already exist"):
        load.load(app_engine)
