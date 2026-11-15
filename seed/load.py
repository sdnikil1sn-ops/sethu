"""Load the seed CSV files into an empty SETHU database.

    python seed/load.py            # needs SETHU_DATABASE_URL (see docs/RUNBOOK.md)

Everything goes through session_for(SYSTEM): one transaction, Row-Level
Security applies, and every inserted row has an audit entry in that same
transaction. "Days ago" in the files is measured from the moment of loading.
"""
import csv
import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.audit.service import record
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for

HERE = Path(__file__).parent
BUREAUS = {"PGRC": "Public Grievance Redressal Cell", "RB": "Regional Bureau (Western Region)"}


def rows(name: str) -> list[dict[str, str]]:
    with open(HERE / f"{name}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def insert(s: Session, table: str, audit_action: str, payload: dict, **values) -> str:
    """Insert one row and its audit entry. `table` is always a literal from this file."""
    row_id = s.execute(
        text(f"INSERT INTO sethu.{table} ({', '.join(values)})"  # noqa: S608
             f" VALUES ({', '.join(':' + k for k in values)}) RETURNING id"),
        values,
    ).scalar_one()
    entity = payload.pop("entity", (table, row_id))
    record(s, SYSTEM, audit_action, entity_type=entity[0], entity_id=str(entity[1]),
           payload=payload | {"seed": True})
    return row_id


def load(engine: Engine | None = None, now: datetime | None = None) -> dict[str, int]:
    now = now or datetime.now(UTC)

    def ago(days: str) -> datetime | None:
        return now - timedelta(days=float(days)) if days else None

    with session_for(SYSTEM, engine) as s:
        # The ledger and case history are append-only, so a second load cannot be undone.
        if s.execute(text("SELECT EXISTS (SELECT 1 FROM sethu.complaints)")).scalar_one():
            raise RuntimeError("complaints already exist; seed only an empty database (docs/RUNBOOK.md section 5)")

        # Bureau ids are derived from the code, so the bureau_id set on Keycloak users survives a reseed.
        for code, name in BUREAUS.items():
            if not s.execute(text("SELECT 1 FROM sethu.bureaus WHERE code = :c"), {"c": code}).first():
                insert(s, "bureaus", "bureau.created", {"code": code},
                       id=uuid5(NAMESPACE_URL, f"sethu:bureau:{code}"), code=code, name=name)
        bureau = {r.code: r.id for r in s.execute(text("SELECT code, id FROM sethu.bureaus"))}
        bureau[""] = None

        # users.csv "desk" has no column yet; it shows up in the assignment notes instead.
        user = {"": None}
        for u in rows("users"):
            user[u["username"]] = insert(
                s, "app_users", "user.created", {"role": u["role"], "bureau": u["bureau"]},
                subject=f"seed:{u['username']}", display_name=u["display_name"], email=u["email"],
                role=u["role"], bureau_id=bureau[u["bureau"]])

        known_name = {}  # exact canonical name or alias -> institution id
        for i in rows("institutions"):
            iid = insert(s, "institutions", "institution.created", {"permanent_id": i["permanent_id"]},
                         permanent_id=i["permanent_id"], name=i["name"], state=i["state"],
                         district=i["district"], pin=i["pin"])
            known_name[i["name"]] = iid
            for alias in filter(None, i["aliases"].split("|")):
                insert(s, "institution_aliases", "institution.alias_added", {"entity": ("institutions", iid)},
                       institution_id=iid, alias=alias, source="seed")
                known_name[alias] = iid

        complaint = {}
        for c in rows("complaints"):
            filed = ago(c["filed_days_ago"])
            # Only exact names are linked here. Typos and abbreviations stay unresolved
            # for the resolution cascade; institution_pid in the CSV is the answer key.
            iid = known_name.get(c["institution_name_raw"])
            complaint[c["ref"]] = insert(
                s, "complaints", "complaint.created",
                {"ref": c["ref"], "bureau": c["bureau"], "source": c["source"], "resolved": iid is not None},
                ref=c["ref"], source=c["source"], bureau_id=bureau[c["bureau"]], institution_id=iid,
                institution_name_raw=c["institution_name_raw"],
                resolution_state="auto" if iid else "unresolved", category=c["category"], status=c["status"],
                language=c["language"], body=c["body"],
                body_sha256=hashlib.sha256(c["body"].encode()).hexdigest(), filed_at=filed,
                due_at=filed + timedelta(days=get_settings().sla_days), closed_at=ago(c["closed_days_ago"]))

        actions = rows("actions")
        for a in actions:
            cid = complaint[a["complaint_ref"]]
            insert(s, "case_actions", f"case.{a['action']}",
                   {"entity": ("complaints", cid), "ref": a["complaint_ref"], "from": a["from_bureau"],
                    "to": a["to_bureau"], "acknowledged": bool(a["acknowledged_days_ago"])},
                   complaint_id=cid, action=a["action"], from_bureau_id=bureau[a["from_bureau"]],
                   to_bureau_id=bureau[a["to_bureau"]], actor_id=user[a["actor"]], note=a["note"] or None,
                   acknowledged_at=ago(a["acknowledged_days_ago"]), created_at=ago(a["days_ago"]))

        counts = {"bureaus": len(BUREAUS), "users": len(user) - 1, "institutions": len(rows("institutions")),
                  "complaints": len(complaint), "case_actions": len(actions)}
        record(s, SYSTEM, "seed.loaded", payload=counts)
    return counts


if __name__ == "__main__":
    print(load())
