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
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.audit.service import record
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.modules.complaints import service as complaints_service
from app.modules.glossary import service as glossary

HERE = Path(__file__).parent


class ProductionRefused(RuntimeError):
    """Mock data never goes into a production database."""


def user_id(username: str) -> UUID:
    """Also the Keycloak id of the demo logins (infra/demo-users/users.json), so a token's
    `sub` matches the seeded app_users row."""
    return uuid5(NAMESPACE_URL, f"sethu:user:{username}")


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
    if get_settings().environment == "prod":
        raise ProductionRefused("SETHU_ENVIRONMENT is prod: the seed loader only loads mock data into dev or test")
    now = now or datetime.now(UTC)

    def ago(days: str) -> datetime | None:
        return now - timedelta(days=float(days)) if days else None

    with session_for(SYSTEM, engine) as s:
        # The ledger and case history are append-only, so a second load cannot be undone.
        if s.execute(text("SELECT EXISTS (SELECT 1 FROM sethu.complaints)")).scalar_one():
            raise RuntimeError("complaints already exist; seed only an empty database (docs/RUNBOOK.md section 5)")

        # Bureau ids are derived from the code, so the bureau_id set on Keycloak users survives a reseed.
        bureaus_created = 0
        for b in rows("bureaus"):
            code, name = b["code"], b["name"]
            if not s.execute(text("SELECT 1 FROM sethu.bureaus WHERE code = :c"), {"c": code}).first():
                bureaus_created += 1
                insert(s, "bureaus", "bureau.created", {"code": code},
                       id=uuid5(NAMESPACE_URL, f"sethu:bureau:{code}"), code=code, name=name)
        bureau = {r.code: r.id for r in s.execute(text("SELECT code, id FROM sethu.bureaus"))}
        bureau[""] = None

        # users.csv "desk" has no column; the desk is written in the assignment note.
        user = {"": None}
        for u in rows("users"):
            user[u["username"]] = insert(
                s, "app_users", "user.created", {"role": u["role"], "bureau": u["bureau"]},
                subject=str(user_id(u["username"])), display_name=u["display_name"], email=u["email"],
                role=u["role"], bureau_id=bureau[u["bureau"]])

        # Intake sources (no API keys: an admin issues those on the Intake screen). Fallbacks come first in the file.
        source = {"": None}
        for r in rows("sources"):
            source[r["name"]] = insert(
                s, "intake_sources", "intake.source_created",
                {"name": r["name"], "channel": r["channel"], "bureau": r["bureau"], "fallback": r["fallback"] or None},
                name=r["name"], channel=r["channel"], bureau_id=bureau[r["bureau"]], priority=int(r["priority"]),
                fallback_source_id=source[r["fallback"]])

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

        keys = complaints_service.keyring()  # complainant details are stored only encrypted
        complaint = {}
        for c in rows("complaints"):
            filed = ago(c["filed_days_ago"])
            # Only exact names are linked here. Typos and abbreviations stay unresolved
            # for the resolution cascade; institution_pid in the CSV is the answer key.
            iid = known_name.get(c["institution_name_raw"])
            cid = uuid4()  # chosen here: the encryption binds the details to this complaint's id
            details = {"name": c["complainant_name"], "email": c["complainant_email"], "phone": c["complainant_phone"]}
            complaint[c["ref"]] = insert(
                s, "complaints", "complaint.created",
                {"ref": c["ref"], "bureau": c["bureau"], "source": c["source"], "resolved": iid is not None},
                id=cid, complainant_enc=keys.encrypt(details, str(cid)), ref=c["ref"], source=c["source"], bureau_id=bureau[c["bureau"]], institution_id=iid,
                institution_name_raw=c["institution_name_raw"],
                resolution_state="auto" if iid else "unresolved", category=c["category"], status=c["status"],
                language=c["language"], body=c["body"],
                body_sha256=hashlib.sha256(c["body"].encode()).hexdigest(), filed_at=filed,
                due_at=filed + timedelta(days=get_settings().sla_days), closed_at=ago(c["closed_days_ago"]),
                transferred_from_bureau_id=bureau[c["transferred_from"]])

        actions = rows("actions")
        for a in actions:
            cid = complaint[a["complaint_ref"]]
            insert(s, "case_actions", f"case.{a['action']}",
                   {"entity": ("complaints", cid), "ref": a["complaint_ref"], "from": a["from_bureau"],
                    "to": a["to_bureau"], "acknowledged": bool(a["acknowledged_days_ago"])},
                   complaint_id=cid, action=a["action"], from_bureau_id=bureau[a["from_bureau"]],
                   to_bureau_id=bureau[a["to_bureau"]], actor_id=user[a["actor"]],
                   assignee_id=user[a["assignee"]], note=a["note"] or None,
                   acknowledged_at=ago(a["acknowledged_days_ago"]), created_at=ago(a["days_ago"]))

        counts = {"bureaus": bureaus_created, "users": len(user) - 1, "institutions": len(rows("institutions")),
                  "complaints": len(complaint), "case_actions": len(actions), "sources": len(source) - 1}
        # The starter glossary (term normalisation, not translation), through the same checked, audited path as an
        # admin's upload. Production loads it the same way: Admin > Glossary, seed/glossary.csv.
        counts["glossary_terms"] = glossary.upload(s, SYSTEM, (HERE / "glossary.csv").read_bytes(),
                                                   "glossary.csv")["terms"]
        record(s, SYSTEM, "seed.loaded", payload=counts)
    return counts


if __name__ == "__main__":
    print(load())
