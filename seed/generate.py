"""Deterministic mock data for SETHU (docs/04-MOCK-DATA-SPEC.md).

    python seed/generate.py        # rewrites the four CSV files next to this script

Standard library only. Every record is synthetic. Dates are stored as
"days ago" so the files never go stale: the loader turns them into timestamps
relative to the moment it runs.
"""
import csv
import io
import random
from collections import Counter
from pathlib import Path

SEED = 26264
HERE = Path(__file__).parent
FILES = ("bureaus", "institutions", "users", "complaints", "actions")

# Bureaus are data: the loader reads bureaus.csv and the application never names a code.
# `source` is the intake channel written into a seeded complaint.
BUREAUS = [
    {"code": "PGRC", "name": "Public Grievance Redressal Cell", "source": "pgrc-portal"},
    {"code": "RB", "name": "Regional Bureau (Western Region)", "source": "rb-register"},
    {"code": "NRB", "name": "Regional Bureau (Northern Region)", "source": "nrb-register"},
    {"code": "AB", "name": "Approval Bureau", "source": "ab-register"},
]
SOURCE = {b["code"]: b["source"] for b in BUREAUS}

STATES = {
    "Maharashtra": ["Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubballi", "Mangaluru"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota"],
}
SPIKE_STATE, SPIKE_CATEGORY = "Uttar Pradesh", "Fee refund"

# Invented words, so no name matches a real college. Index 0 is the demo institution.
PREFIXES = (
    "Greenfield Sunmere Riverton Lakemont Hillcroft Silverbrook Blueharbor Maplestone Northvale Eastmere "
    "Westhollow Southmoor Redmere Goldmere Pinehollow Clearbrook Brightmoor Starmont Oakmere Meadowvale "
    "Stonemere Highmoor Crestvale Farhaven Summerton Thornvale Evermere Lotusvale Banyanmere Ashmere "
    "Saffronvale Indigomere Coralvale Ambermoor Jadehollow Opalcrest Cedarmont Willowmere Falconcrest Mistvale"
).split()
KINDS = [
    "Institute of Technology", "College of Engineering", "Institute of Management Studies",
    "College of Pharmacy", "Polytechnic College", "School of Architecture",
]
SHORT = {"Institute": "Inst.", "Technology": "Tech.", "College": "Coll.", "Engineering": "Engg.",
         "Management": "Mgmt.", "Polytechnic": "Poly.", "Architecture": "Arch.", "Pharmacy": "Pharm."}
GREENFIELD_ALIASES = ["Greenfield Inst. of Tech., Pune", "GIT Pune", "Greenfield Institute of Tech"]

CATEGORIES = [
    "Faculty shortage", "Fee refund", "Infrastructure", "Ragging",
    "Admission irregularity", "Scholarship delay", "Examination", "Placement misrepresentation",
]
DEPTS = ["Mechanical Engineering", "Civil Engineering", "Computer Science", "Electronics",
         "Electrical Engineering", "Information Technology", "Pharmacy", "Management Studies"]
MONTHS = ["January", "February", "March", "April", "July", "August", "September", "November"]

# Two English wordings per category: a Tier 2 pair uses both with the same details.
EN = {
    "Faculty shortage": [
        "Students of the {dept} department report that {n} sanctioned faculty posts have been vacant since "
        "{month}. Classes for semester {sem} are being taken by guest lecturers.",
        "The {dept} department is running {n} teachers short of the approved strength. Several semester {sem} "
        "subjects have had no regular faculty since {month}.",
    ],
    "Fee refund": [
        "A student of {dept} withdrew admission in {month} and the refund of Rs {amount} is still pending after "
        "{n} months. The college has not replied to written requests.",
        "Refund of Rs {amount} has not been paid {n} months after a {dept} seat was cancelled in {month}. "
        "The accounts office keeps asking the family to come back later.",
    ],
    "Infrastructure": [
        "The {dept} laboratory has {n} machines out of order since {month}. Semester {sem} practicals are being "
        "signed off without being conducted.",
        "Practicals for semester {sem} in {dept} cannot be held because {n} lab machines have not worked since "
        "{month}. The hostel water supply is also irregular.",
    ],
    "Ragging": [
        "Semester {sem} students of {dept} report {n} ragging incidents in the hostel since {month}. "
        "The anti-ragging committee has not met.",
        "There have been {n} incidents of ragging against semester {sem} {dept} students since {month} and no "
        "action has been taken by the committee.",
    ],
    "Admission irregularity": [
        "In {month}, {n} management quota seats in {dept} were filled without a merit list and Rs {amount} was "
        "demanded over the approved fee.",
        "{n} seats in {dept} were given outside the merit list in {month}. Parents were asked for Rs {amount} "
        "beyond the notified fee.",
    ],
    "Scholarship delay": [
        "Scholarships of Rs {amount} for {n} students of {dept} have been pending since {month}. The college "
        "says the forms for semester {sem} were not forwarded.",
        "{n} {dept} students have not received their scholarship of Rs {amount} since {month} because the "
        "college did not forward the semester {sem} forms.",
    ],
    "Examination": [
        "Results of the semester {sem} {dept} examination held in {month} have not been declared for {n} months. "
        "Revaluation requests are unanswered.",
        "{dept} students are still waiting, {n} months on, for semester {sem} results of the {month} "
        "examination. Nobody answers revaluation requests.",
    ],
    "Placement misrepresentation": [
        "The college advertised {n}0 percent placement for {dept} in {month}, but most semester {sem} students "
        "received no offer.",
        "Brochures issued in {month} claim {n}0 percent placement in {dept}. Hardly any semester {sem} student "
        "was actually placed.",
    ],
}
HI = {
    "Faculty shortage": "संस्थान के एक विभाग में {n} स्वीकृत शिक्षक पद {month} से खाली हैं। सेमेस्टर {sem} की "
                        "कक्षाएं नियमित रूप से नहीं हो रही हैं।",
    "Fee refund": "प्रवेश रद्द करने के {n} महीने बाद भी {amount} रुपये की फीस वापस नहीं की गई है। संस्थान कोई "
                  "लिखित उत्तर नहीं दे रहा है। सेमेस्टर {sem}।",
    "Infrastructure": "सेमेस्टर {sem} की प्रयोगशाला में {n} उपकरण खराब पड़े हैं और छात्रावास में पानी की समस्या है। "
                      "शुल्क {amount} रुपये लिया गया है।",
    "Ragging": "सेमेस्टर {sem} के छात्रों ने छात्रावास में रैगिंग की {n} घटनाओं की शिकायत की है, पर समिति ने कोई "
               "कार्रवाई नहीं की। पहली शिकायत {month} में दी गई थी।",
    "Admission irregularity": "प्रबंधन कोटे की {n} सीटें मेरिट सूची के बिना भरी गई हैं और {amount} रुपये अतिरिक्त "
                              "मांगे गए। सेमेस्टर {sem}।",
    "Scholarship delay": "{n} छात्रों की {amount} रुपये की छात्रवृत्ति सेमेस्टर {sem} से लंबित है।",
    "Examination": "सेमेस्टर {sem} के परिणाम {n} महीने से घोषित नहीं हुए हैं और पुनर्मूल्यांकन के आवेदन लंबित हैं। "
                   "परीक्षा शुल्क {amount} रुपये था।",
    "Placement misrepresentation": "संस्थान ने विज्ञापन में {n}0 प्रतिशत प्लेसमेंट का दावा किया, जबकि सेमेस्टर {sem} "
                                   "के अधिकांश छात्रों को कोई प्रस्ताव नहीं मिला। शुल्क {amount} रुपये।",
}

# username, display name, role, bureau, desk. rao, iyer, fernandes, menon, admin and das are the demo
# logins: infra/demo-users/users.json must list the same usernames, roles and bureaus.
USERS = [
    ("rao", "Anita Rao", "officer", "PGRC", ""), ("mdutta", "Meera Dutta", "officer", "PGRC", ""),
    ("kjoshi", "Kiran Joshi", "officer", "PGRC", ""), ("averma", "Arjun Verma", "officer", "PGRC", ""),
    ("dpillai", "Divya Pillai", "officer", "PGRC", ""), ("rbose", "Rohan Bose", "officer", "PGRC", ""),
    ("snair", "Sneha Nair", "officer", "RB", "RB-D1"), ("vpatel", "Vikram Patel", "officer", "RB", "RB-D1"),
    ("pmathew", "Pooja Mathew", "officer", "RB", "RB-D2"), ("fkhan", "Farhan Khan", "officer", "RB", "RB-D2"),
    ("greddy", "Gauri Reddy", "officer", "RB", "RB-D3"), ("dgupta", "Dev Gupta", "officer", "RB", "RB-D3"),
    ("fernandes", "Maria Fernandes", "bureau_head", "PGRC", ""), ("iyer", "Suresh Iyer", "bureau_head", "RB", ""),
    ("mkulkarni", "Manoj Kulkarni", "bureau_head", "RB", ""),
    ("rbhat", "Ravi Bhat", "bureau_head", "NRB", ""), ("squreshi", "Sana Qureshi", "bureau_head", "AB", ""),
    ("tsingh", "Tara Singh", "officer", "NRB", ""), ("mkapoor", "Mohan Kapoor", "officer", "NRB", ""),
    ("lmenezes", "Lina Menezes", "officer", "AB", ""), ("vsharma", "Vivek Sharma", "officer", "AB", ""),
    ("menon", "Kavita Menon", "oversight", "", ""), ("admin", "Asha Chopra", "admin", "", ""),
    ("das", "Arun Das", "auditor", "", ""),
]


def variant(name: str, city: str, kind: int, rng: random.Random) -> str:
    """One of four ways people mistype an institution name."""
    short = " ".join(SHORT.get(w, w) for w in name.split())
    if kind == 0:  # abbreviation, with city
        return f"{short}, {city}"
    if kind == 1:  # acronym and city, like "GIT Pune"
        return "".join(w[0] for w in name.split() if w != "of") + " " + city
    if kind == 2:  # typo: two neighbouring letters swapped
        i = rng.choice([i for i in range(1, len(name.split()[0]) - 1) if name[i] != name[i + 1]])
        return name[:i] + name[i + 1] + name[i] + name[i + 2:]
    return short  # abbreviation, city missing


def build() -> dict[str, list[dict]]:
    rng = random.Random(SEED)  # noqa: S311 - reproducible test data, not security

    institutions = []
    for i, prefix in enumerate(PREFIXES):
        state = list(STATES)[i % 6]
        institutions.append({
            "permanent_id": f"1-9{i + 1:07d}",
            "name": f"{prefix} {KINDS[0 if i == 0 else rng.randrange(len(KINDS))]}",
            "state": state,
            "district": STATES[state][(i // 6) % 4],
            "pin": f"{(i % 6 + 1) * 110000 + i:06d}",
            "aliases": "|".join(GREENFIELD_ALIASES) if i == 0 else "",
            # Bureau that receives this institution's ordinary complaints. Keeping each
            # institution in one bureau is what stops accidental cross-bureau overlaps.
            "home": ("PGRC", "RB")[(i + i // 6) % 2],  # alternates within each state
        })
    greenfield, tier2_insts, tier1_insts = institutions[0], institutions[1:6], institutions[6:15]
    ordinary = institutions[15:]

    users = [{"username": u, "display_name": n, "email": f"{u}@sethu.test", "role": r, "bureau": b, "desk": d}
             for u, n, r, b, d in USERS]
    codes = [b["code"] for b in BUREAUS]
    officers = {b: [u for u in users if u["role"] == "officer" and u["bureau"] == b] for b in codes}
    head = {b: next(u["username"] for u in users if u["role"] == "bureau_head" and u["bureau"] == b) for b in codes}

    complaints: list[dict] = []
    actions: list[dict] = []
    seen: set[str] = set()
    recent: Counter = Counter()  # (state, category) filed in the last 3 weeks
    numbers = [n for n in range(1, 301) if n not in (90, 101, 102, 103)]
    rng.shuffle(numbers)

    def details() -> dict:
        return {"dept": rng.choice(DEPTS), "month": rng.choice(MONTHS), "n": rng.randint(2, 9),
                "sem": rng.randint(1, 8), "amount": rng.randrange(20, 190) * 500}

    def fresh(category: str, lang: str = "en") -> str:
        while True:
            text = (HI[category] if lang == "hi" else rng.choice(EN[category])).format(**details())
            if text not in seen:
                seen.add(text)
                return text

    def pick(pool, **want) -> dict:
        return rng.choice([i for i in pool if all(i[k] == v for k, v in want.items())])

    def category_for(inst: dict, exclude: tuple = ()) -> str:
        # Only the seeded spike may touch the spike cell, so its ratio stays exact, and no
        # other state and category may bunch up in the last 3 weeks and look like a spike.
        banned = set(exclude) | ({SPIKE_CATEGORY} if inst["state"] == SPIKE_STATE else set())
        banned |= {c for c in CATEGORIES if recent[inst["state"], c] >= 3}
        return rng.choice([c for c in CATEGORIES if c not in banned])

    def add(inst, category, days, status, tags, *, bureau=None, raw=None, body=None, lang="en", ref=None,
            flow="normal", sent_from="PGRC") -> dict:
        bureau = bureau or inst["home"]
        c = {
            "ref": ref or f"C-{numbers.pop():03d}",
            "source": SOURCE[sent_from if flow == "misrouted" else bureau],
            "bureau": bureau,
            "institution_pid": inst["permanent_id"],
            "institution_name_raw": raw or inst["name"],
            "category": category,
            "status": status,
            "language": lang,
            "body": body or fresh(category, lang),
            "filed_days_ago": days,
            "closed_days_ago": "",
            # The bureau still waiting for its transfer to be acknowledged (C-090: RB sent it back).
            "transferred_from": "RB" if flow == "loop" else "",
            "seed_tags": tags,
        }
        seen.add(c["body"])
        recent[inst["state"], category] += days <= 21
        complaints.append(c)

        def act(action, at, actor="", note="", frm="", to="", ack="", assignee=""):
            actions.append({"complaint_ref": c["ref"], "action": action, "days_ago": round(at, 2),
                            "from_bureau": frm, "to_bureau": to, "actor": actor, "assignee": assignee,
                            "note": note, "acknowledged_days_ago": ack})

        def assign(at, b):
            o = rng.choice(officers[b])
            act("assigned", at, head[b], f"Desk {o['desk']}" if o["desk"] else "", assignee=o["username"])

        def transfer(at, frm, to, acknowledged):
            act("transferred", at, head[frm], "Outside this bureau's remit", frm, to, at - 1 if acknowledged else "")
            if acknowledged:
                act("acknowledged", at - 1, head[to], "Transfer accepted")

        def close(replied_at, closed_at):
            act("replied", replied_at, head[bureau], "Reply sent to complainant")
            act("closed", closed_at, head[bureau], "Disposed")
            c["closed_days_ago"] = closed_at

        act("filed", days, note=f"Received via {c['source']}")
        if flow == "misrouted":  # filed at the wrong bureau (PGRC unless said), handed over, accepted
            transfer(days - 1, sent_from, bureau, True)
            assign(days - 2.2, bureau)
            close(days - 6, days - 9)
        elif flow == "roundtrip":  # there and back, every hop acknowledged: not a deadlock
            assign(days - 0.2, "PGRC")
            transfer(days - 2, "PGRC", "RB", True)
            transfer(days - 6, "RB", "PGRC", True)
            close(days - 10, days - 12)
        elif flow == "loop":  # C-090: there and back, nobody acknowledged
            assign(days - 0.2, "PGRC")
            transfer(30, "PGRC", "RB", False)
            transfer(18, "RB", "PGRC", False)
        elif status != "open":
            assign(days - 0.2, bureau)
            if flow == "active":
                act("note", rng.randint(1, 15), head[bureau], "Reminder sent to institution")
            if status == "replied":
                act("replied", round(days / 2, 2), head[bureau], "Reply sent to complainant")
            if status == "closed":
                replied = days - rng.randint(2, 8)
                close(replied, replied - rng.randint(1, 10))
        return c

    def two_wordings(category: str) -> tuple[str, str]:
        d = details()
        return EN[category][0].format(**d), EN[category][1].format(**d)

    # Fixed demo records (docs/03-DEMO-STORY.md).
    add(greenfield, "Faculty shortage", 12, "in_progress", "demo;tier2:1", bureau="PGRC", ref="C-101",
        body="Students of the Mechanical Engineering department say that required faculty posts are vacant. "
             "Seven sanctioned posts have been unfilled for two semesters and classes are being combined.")
    add(greenfield, "Faculty shortage", 6, "open", "demo;tier2:1;tier1:10;variant", bureau="RB", ref="C-102",
        raw=GREENFIELD_ALIASES[0],
        body="As a parent I wish to report that the college shows more faculty on its records than it actually "
             "has. Several faculty posts in Mechanical Engineering are vacant and teachers who left are still "
             "listed.")
    add(greenfield, "Fee refund", 3, "open", "demo;tier1:10;variant", bureau="PGRC", ref="C-103",
        raw=GREENFIELD_ALIASES[1],
        body="The fee refund for a student who withdrew admission in the first month is still pending. "
             "The college has not replied to three written requests.")

    # Cross-bureau pairs. These institutions hold nothing else.
    for n, inst in enumerate(tier2_insts, start=2):
        category = category_for(inst, exclude=(SPIKE_CATEGORY,))
        first = rng.randint(8, 20)
        for bureau, days, body in zip(("PGRC", "RB"), (first, first - rng.randint(2, 7)), two_wordings(category),
                                      strict=True):
            add(inst, category, days, rng.choice(["open", "in_progress"]), f"tier2:{n}", bureau=bureau, body=body)
    for n, inst in enumerate(tier1_insts, start=1):
        cat_a = category_for(inst, exclude=(SPIKE_CATEGORY,))
        first = rng.randint(8, 20)
        add(inst, cat_a, first, "in_progress", f"tier1:{n}", bureau="PGRC")
        add(inst, category_for(inst, exclude=(SPIKE_CATEGORY, cat_a)), first - rng.randint(2, 7), "open",
            f"tier1:{n}", bureau="RB")

    # Exact duplicates: same text filed twice with the same bureau.
    for n in range(1, 6):
        inst = rng.choice(ordinary)
        category, first = category_for(inst), rng.randint(6, 20)
        body = fresh(category)
        add(inst, category, first, "in_progress", f"dup:{n}", body=body)
        add(inst, category, first - rng.randint(1, 5), "open", f"dup:{n}", body=body)

    # Transfers: one deadlock, and acknowledged ones that must not be flagged.
    add(pick(ordinary, home="PGRC"), "Infrastructure", 40, "transferred", "deadlock;overdue", ref="C-090",
        flow="loop")
    for _ in range(2):
        inst = pick(ordinary, home="PGRC")
        add(inst, category_for(inst), rng.randint(40, 150), "closed", "transfer-ack", flow="roundtrip")
    for _ in range(5):
        inst = pick(ordinary, home="RB")
        add(inst, category_for(inst), rng.randint(30, 150), "closed", "transfer-ack", flow="misrouted")

    # Silent (nothing for 30+ days) and overdue-but-active cases. With C-090: 25 overdue.
    for n in range(8):
        inst = rng.choice(ordinary)
        add(inst, category_for(inst), rng.randint(35, 120), ("open", "in_progress")[n % 2], "silent;overdue")
    for _ in range(16):
        inst = rng.choice(ordinary)
        add(inst, category_for(inst), rng.randint(22, 90), "in_progress", "overdue", flow="active")

    # Regional spike: 15 over the earlier 159 days (about 2 per 3 weeks), then 9 in the last 3 weeks.
    for _ in range(15):
        add(pick(ordinary, state=SPIKE_STATE), SPIKE_CATEGORY, rng.randint(22, 180), "closed", "spike-baseline")
    for _ in range(9):
        add(pick(ordinary, state=SPIKE_STATE), SPIKE_CATEGORY, rng.randint(1, 20),
            rng.choice(["open", "in_progress"]), "spike")

    # Negative cases: near misses that must not be flagged.
    a = pick(ordinary, home="PGRC", state="Gujarat")
    b = pick(ordinary, home="RB", state="Tamil Nadu")
    d = details()
    add(a, "Examination", 9, "open", "neg-similar-text", body=EN["Examination"][0].format(**d))
    add(b, "Examination", 7, "open", "neg-similar-text", body=EN["Examination"][0].format(**d | {"n": d["n"] + 1}))
    inst = rng.choice(ordinary)
    category = category_for(inst)
    for days, body in zip((10, 5), two_wordings(category), strict=True):
        add(inst, category, days, "open", "neg-same-bureau", body=body)
    add(pick(ordinary, home="PGRC", state="Rajasthan"), "Ragging", 8, "open", "neg-same-category")
    add(pick(ordinary, home="RB", state="Karnataka"), "Ragging", 4, "open", "neg-same-category")

    # Ordinary traffic fills the rest. The first 38 carry a name variant (40 with the demo's two),
    # the next 15 are in Hindi.
    for n in range(len(numbers)):
        inst = rng.choice(ordinary)
        days = rng.randint(1, 180)
        # A case filed exactly 21 days ago falls due at the moment of loading, so day 21 is closed too.
        status = "closed" if days > 20 else rng.choice(["open", "in_progress", "replied"])
        if n < 38:
            add(inst, category_for(inst), days, status, "variant",
                raw=variant(inst["name"], inst["district"], n % 4, rng))
        else:
            add(inst, category_for(inst), days, status, "hindi" if n < 53 else "", lang="hi" if n < 53 else "en")

    # Two more bureaus, NRB and AB, so cross-bureau behaviour is not only ever PGRC and RB. Added
    # last, with references from C-301, so every record above stays exactly as it was. Each case is
    # placed on purpose: no state and category reaches 5 in 30 days (no new spike), nothing is
    # overdue, no new bureau holds 3 open cases (no new bottleneck), and every cross-bureau pair is tagged.
    extra_refs = (f"C-{n}" for n in range(301, 400))
    state_of = {i["permanent_id"]: i["state"] for i in institutions}

    def quiet(inst: dict, exclude: tuple = ()) -> str:
        """A category this state saw fewer than 3 times in the last 30 days."""
        busy = Counter(c["category"] for c in complaints
                       if state_of[c["institution_pid"]] == inst["state"] and int(c["filed_days_ago"]) <= 30)
        return rng.choice([c for c in CATEGORIES if busy[c] < 3 and c not in exclude
                           and (inst["state"], c) != (SPIKE_STATE, SPIKE_CATEGORY)])

    new_insts = []
    for prefix, home in (("Rosemere", "RB"), ("Sandalvale", "NRB"), ("Tealcrest", "AB")):
        i = len(institutions)
        state = list(STATES)[i % 6]
        new_insts.append({
            "permanent_id": f"1-9{i + 1:07d}", "name": f"{prefix} {rng.choice(KINDS)}", "state": state,
            "district": STATES[state][(i // 6) % 4], "pin": f"{(i % 6 + 1) * 110000 + i:06d}", "aliases": "",
            "home": home,
        })
        institutions.append(new_insts[-1])
        state_of[new_insts[-1]["permanent_id"]] = state
    shared, nrb_home, ab_home = new_insts

    # A Tier 2 pair between RB and NRB at an institution that holds nothing else.
    category, first = quiet(shared), rng.randint(8, 14)
    for bureau, days, body in zip(("RB", "NRB"), (first, first - rng.randint(2, 5)), two_wordings(category),
                                  strict=True):
        add(shared, category, days, "open", "tier2:7", bureau=bureau, body=body, ref=next(extra_refs))
    # A third bureau at a Tier 1 institution (PGRC and RB already there), in a different category.
    t1 = tier1_insts[0]
    taken = tuple({c["category"] for c in complaints if c["institution_pid"] == t1["permanent_id"]})
    add(t1, quiet(t1, exclude=taken), rng.randint(3, 6), "open", "tier1:1", bureau="NRB", ref=next(extra_refs))
    # Closed history, so both new bureaus have a disposal time.
    for inst, bureau in ((nrb_home, "NRB"), (nrb_home, "NRB"), (nrb_home, "NRB"), (ab_home, "AB"), (ab_home, "AB")):
        add(inst, category_for(inst), rng.randint(40, 150), "closed", "", bureau=bureau, ref=next(extra_refs))
    # A handover between the two new bureaus, acknowledged: must not be flagged.
    add(ab_home, category_for(ab_home), rng.randint(40, 120), "closed", "transfer-ack", bureau="AB",
        flow="misrouted", sent_from="NRB", ref=next(extra_refs))
    add(ab_home, quiet(ab_home), rng.randint(1, 4), "open", "", bureau="AB", ref=next(extra_refs))

    for i in institutions:
        del i["home"]
    complaints.sort(key=lambda c: c["ref"])
    order = {c["ref"]: n for n, c in enumerate(complaints)}
    actions.sort(key=lambda a: (order[a["complaint_ref"]], -a["days_ago"]))
    bureaus = [{"code": b["code"], "name": b["name"]} for b in BUREAUS]
    return {"bureaus": bureaus, "institutions": institutions, "users": users, "complaints": complaints,
            "actions": actions}


def render(rows: list[dict]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


if __name__ == "__main__":
    for name, rows in build().items():
        (HERE / f"{name}.csv").write_text(render(rows), encoding="utf-8", newline="\n")
        print(f"{name}.csv: {len(rows)} rows")
