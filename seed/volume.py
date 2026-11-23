"""Bring a seeded dev or test database up to a load-test volume of complaints (mock data only).

    python seed/volume.py [total] [institutions]   # defaults 100000 and 2000; refuses SETHU_ENVIRONMENT=prod

Adds mock institutions (`LT-` permanent ids) and complaints (with their 'filed' history rows) using set-based SQL
in one transaction as the system principal. The shape follows the real problem rather than the 43-institution
demo seed: about 9,000 AICTE institutions exist, so complaints are spread thin, with hot spots. 30% go to the
seeded institutions (a few hundred each), the rest across the added ones (dozens each). They cover the active
bureaus, eight categories and two years of filing dates; as in a working system, complaints of the last
60 days are in every state and older ones are closed except a stuck 3%, with texts drawn from a word list, so
trigram and the detectors have real work without every pair looking alike. One audit entry records the batch
(counts only). Complainant details are left empty: encrypting 100,000 of them through the keyring adds nothing
to the measurement. Used by loadtest/ (docs/LOAD-AND-DRILLS.md).
"""
import sys

from sqlalchemy import text

from app.audit.service import record
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for

CATEGORIES = ["Admission irregularity", "Examination", "Faculty shortage", "Fee refund", "Infrastructure",
              "Placement misrepresentation", "Ragging", "Scholarship delay"]
WORDS = ("refund deposit hostel library faculty semester fees receipt scholarship examination results placement "
         "laboratory canteen transport ragging warden principal registrar accounts admission merit quota donation "
         "certificate delay salary attendance internship syllabus grievance committee affiliation approval seats "
         "counselling transfer migration marksheet revaluation backlog stipend bus campus security water "
         "electricity classroom computers internet sports medical insurance uniform books notice website "
         "helpline email letter office").split()
STATES = ["Maharashtra", "Karnataka", "Tamil Nadu", "Uttar Pradesh", "Rajasthan", "Gujarat", "Kerala", "Telangana",
          "West Bengal", "Madhya Pradesh"]

INSTITUTIONS = """
INSERT INTO sethu.institutions (permanent_id, name, state, district, pin)
SELECT 'LT-' || lpad(g::text, 5, '0'),
       'Load Test ' || (ARRAY['Institute of Technology', 'College of Engineering', 'School of Management',
                              'Polytechnic', 'College of Pharmacy'])[1 + g % 5] || ' ' || g,
       (CAST(:states AS text[]))[1 + g % 10], 'District ' || (g % 97), lpad((400000 + g)::text, 6, '0')
  FROM generate_series(1, CAST(:n AS int)) g
ON CONFLICT (permanent_id) DO NOTHING
"""
ADD = """
WITH inst AS (SELECT id, name, row_number() OVER (ORDER BY coalesce(permanent_id LIKE 'LT-%', false), name) - 1 AS n
                FROM sethu.institutions),
     hot AS (SELECT count(*) AS c FROM sethu.institutions WHERE coalesce(permanent_id NOT LIKE 'LT-%', true)),
     cold AS (SELECT count(*) AS c FROM sethu.institutions WHERE permanent_id LIKE 'LT-%'),
     bur AS (SELECT id, row_number() OVER (ORDER BY code) - 1 AS n FROM sethu.bureaus WHERE active),
     nb AS (SELECT count(*) AS c FROM bur),
     picks AS (
       SELECT g, CASE WHEN g % 10 < 3 OR (SELECT c FROM cold) = 0 THEN g % (SELECT c FROM hot)
                      ELSE (SELECT c FROM hot) + (g * 7919) % (SELECT c FROM cold) END AS i
         FROM generate_series(CAST(:start AS int), CAST(:stop AS int)) g),
     rows AS (
       SELECT g, inst.id AS institution_id, inst.name,
              (SELECT id FROM bur WHERE n = (g / 7) % (SELECT c FROM nb)) AS bureau_id,
              (CAST(:categories AS text[]))[1 + g % 8] AS category,
              CASE WHEN (g * 37) % 730 <= 60
                   THEN (ARRAY['open','open','in_progress','replied','closed'])[1 + (g / 3) % 5]
                   WHEN g % 33 = 0 THEN 'open'          -- about 3% of older ones are stuck: the overdue backlog
                   ELSE 'closed' END AS status,
              now() - make_interval(days => (g * 37) % 730, hours => g % 24) AS filed_at
         FROM picks JOIN inst ON inst.n = picks.i)
INSERT INTO sethu.complaints (id, ref, source, bureau_id, institution_id, institution_name_raw, resolution_state,
                              category, status, language, body, body_sha256, filed_at, due_at, closed_at)
SELECT gen_random_uuid(), 'LT-' || lpad(g::text, 6, '0'), 'load-test', bureau_id, institution_id, name, 'auto',
       category, status, 'en', b.body, md5(b.body), filed_at, filed_at + interval '21 days',
       CASE WHEN status = 'closed' THEN filed_at + make_interval(days => 5 + g % 40) END
  FROM rows
 CROSS JOIN LATERAL (
   SELECT 'Load test complaint ' || g || ' (' || category || '): '
          || string_agg((CAST(:words AS text[]))[1 + abs(hashtext(g::text || '.' || w)) % :nwords], ' ') || '.' AS body
     FROM generate_series(1, 18) w) b
"""
FILED = """
INSERT INTO sethu.case_actions (complaint_id, action, to_bureau_id, note, created_at)
SELECT id, 'filed', bureau_id, 'Received via load-test', filed_at FROM sethu.complaints
 WHERE source = 'load-test' AND NOT EXISTS (SELECT 1 FROM sethu.case_actions a WHERE a.complaint_id = complaints.id)
"""


def main(total: int = 100_000, institutions: int = 2000) -> dict:
    if get_settings().environment == "prod":
        raise SystemExit("refusing: SETHU_ENVIRONMENT is prod (load-test data is for dev and test only)")
    with session_for(SYSTEM) as s:
        s.execute(text(INSTITUTIONS), {"n": institutions, "states": STATES})
        have = s.execute(text("SELECT count(*) FROM sethu.complaints")).scalar_one()
        start = s.execute(text("SELECT count(*) FROM sethu.complaints WHERE source = 'load-test'")).scalar_one() + 1
        add = max(0, total - have)
        if add:
            s.execute(text(ADD), {"start": start, "stop": start + add - 1, "categories": CATEGORIES,
                                  "words": WORDS, "nwords": len(WORDS)})
            s.execute(text(FILED))
            record(s, SYSTEM, "load.seeded", payload={"added": add, "total": total, "institutions": institutions})
        return {"before": have, "added": add,
                "after": s.execute(text("SELECT count(*) FROM sethu.complaints")).scalar_one(),
                "institutions": s.execute(text("SELECT count(*) FROM sethu.institutions")).scalar_one()}


if __name__ == "__main__":
    print(main(*[int(a) for a in sys.argv[1:3]]))
