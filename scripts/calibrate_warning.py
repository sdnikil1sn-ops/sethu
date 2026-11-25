"""Calibrate the early-warning parameters on the seed (seed/complaints.csv), with no database: run DBSCAN, the
Z-score and the ratio rule over a grid and print what each finds. Counts and states only.

    python scripts/calibrate_warning.py

The seed's planted answers: the Uttar Pradesh / Fee refund spike (tag "spike", 9 in the last 20 days over a
baseline of about 2 per 3 weeks) and the Karnataka + Tamil Nadu cluster (tag "cluster:2", 4 + 4 in six days).
Complaints whose institution name is a variant are left out: in the database they wait for resolution, so they
have no state yet.
"""
import csv
import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.ai.warning import DBSCANWarning, RatioWarning, ZScoreWarning  # noqa: E402

DEFAULTS = {"recent_days": 30, "baseline_days": 90, "km_per_unit": 500.0, "days_per_unit": 10.0, "eps": 1.0,
            "min_samples": 6, "min_members": 8, "max_points": 30000, "max_baseline_share": 0.5, "z_threshold": 3.0,
            "z_min_count": 5, "z_sd_floor": 1.0, "ratio_min_count": 5, "ratio_threshold": 3.0}


def complaints() -> list[dict]:
    state = {i["permanent_id"]: i["state"] for i in csv.DictReader((ROOT / "seed/institutions.csv").open())}
    rows = []
    for c in csv.DictReader((ROOT / "seed/complaints.csv").open(encoding="utf-8")):
        if "variant" in c["seed_tags"]:
            continue
        rows.append({"id": c["ref"], "category": c["category"], "group": c["category"],
                     "state": state[c["institution_pid"]], "bureau_id": c["bureau"],
                     "days_ago": int(c["filed_days_ago"]), "tags": c["seed_tags"]})
    return rows


def found(provider, payload) -> list[str]:
    out = provider.run(payload).output["signals"]
    return [f"{s['category_group']} {'+'.join(s['states'])} n={s['members']} score={s['score']}" for s in out]


def main() -> None:
    rows = complaints()
    payload = {"complaints": rows, "settings": dict(DEFAULTS)}
    print("defaults:")
    for p in (DBSCANWarning(), ZScoreWarning(), RatioWarning()):
        print(f"  {p.name}: {found(p, payload)}")
    print("DBSCAN grid (km_per_unit, days_per_unit, min_samples): signals")
    for km, days, ms in itertools.product((400, 500, 600, 800), (5, 7, 10, 14), (4, 5, 6, 7, 8)):
        s = dict(DEFAULTS) | {"km_per_unit": float(km), "days_per_unit": float(days), "min_samples": ms}
        print(f"  {km:>4} {days:>3} {ms}: {found(DBSCANWarning(), {'complaints': rows, 'settings': s})}")
    print("Z-score grid (threshold, floor): signals")
    for z, floor in itertools.product((2.0, 2.5, 3.0, 3.5), (0.5, 1.0, 1.5)):
        s = dict(DEFAULTS) | {"z_threshold": z, "z_sd_floor": floor}
        print(f"  {z} {floor}: {found(ZScoreWarning(), {'complaints': rows, 'settings': s})}")


if __name__ == "__main__":
    main()
