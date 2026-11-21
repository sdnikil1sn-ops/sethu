"""Complaint intake: every channel writes to one durable queue; the worker turns queued items into complaints.

Channels (each a kind of source an admin sets up, feeding one bureau):
  api     a portal system posts JSON with its API key, a timestamp and a one-time nonce
  upload  an officer uploads a CSV or XLSX file; each row is checked and bad rows are reported
  manual  an officer types one complaint into a form
  spool   files dropped into a mounted folder (one subfolder per source); the fallback when a portal's API is down

Pipeline, for every item: validate and normalise (ComplaintIn), reject an exact duplicate (same bureau, typed
institution and text), resolve the institution through the existing cascade (unresolved names go to the
Unmatched names queue), flag a near duplicate for review, encrypt the complainant details, create the
complaint and its history, and audit it with the source and path that delivered it.

Nothing is dropped. An item is written to intake_items before anything else happens. While its source is
marked down, or when an attempt fails, it waits and is tried again with backoff; after the maximum it is
dead-lettered with the reason, for an admin to retry. A source whose primary is marked down is the stand-in
("fallback" path). No step makes a network call; the institution cascade and duplicate checks are local SQL.

Audit entries and logs carry identifiers, counts and reasons, never complaint text or complainant details.
"""
import csv
import hashlib
import io
import logging
import secrets
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.core.config import get_settings
from app.core.crypto import KeyringError
from app.db.session import SYSTEM, session_for
from app.modules.alerts import service as alerts
from app.modules.bureaus import service as bureaus
from app.modules.complaints import service as complaints
from app.modules.institutions import service as institutions
from app.modules.intake import repo
from app.modules.intake.schemas import ComplaintIn
from app.modules.users import service as users

log = logging.getLogger("sethu.intake")

# The API gateway: reads sources to check a key, records nonces, queues api items. Reads no complaints.
GATEWAY = Principal(subject="intake-gateway", name="intake-gateway", role="intake", bureau_id=None)

NEAR_DUPLICATE_SIMILARITY = 0.6   # pg_trgm similarity of the text, same bureau and institution
NEAR_DUPLICATE_DAYS = 180
COLUMNS = ("institution_name", "category", "body", "language", "filed_at", "external_ref",
           "complainant_name", "complainant_email", "complainant_phone")


class IntakeError(Exception):
    def __init__(self, status: int, message: str, headers: dict[str, str] | None = None):
        super().__init__(message)
        self.status = status
        self.headers = headers


class Held(Exception):
    """The item cannot be processed yet (its source is down or inactive): try again later."""


def key_hash(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def body_hash(body: str) -> str:
    return hashlib.sha256(body.encode()).hexdigest()


def fingerprint(bureau_id: UUID, c: ComplaintIn) -> str:
    """Same bureau, same typed institution, same text (after normalising spaces and case of the name)."""
    return hashlib.sha256(f"{bureau_id}|{c.institution_name.lower()}|{body_hash(c.body)}".encode()).hexdigest()


def safe_reason(e: Exception) -> str:
    """Why an attempt failed, without any submitted value: database and validation messages can quote the
    row, so only constraint and field names are kept."""
    if isinstance(e, Held | KeyringError | IntakeError):
        return str(e)
    if isinstance(e, ValidationError):
        return "invalid: " + "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}"
                                       for x in e.errors(include_input=False, include_url=False))
    if isinstance(e, DBAPIError) and getattr(e.orig, "diag", None) is not None:
        return f"database: {e.orig.diag.message_primary}"
    return type(e).__name__


# ---------------------------------------------------------------- receiving

def _enqueue(session: Session, principal: Principal, source: dict, c: ComplaintIn, channel: str,
             received_by: UUID | None) -> dict:
    if not source["active"]:
        raise IntakeError(409, f"source {source['name']} is not active")
    if source["channel"] != channel:
        raise IntakeError(409, f"source {source['name']} does not take {channel} intake")
    fp = fingerprint(source["bureau_id"], c)
    if (same := complaints.same_text(session, source["bureau_id"], c.institution_name.lower(), c.body)) is not None:
        raise IntakeError(409, f"duplicate of {same['ref']}")
    if repo.waiting_with(session, source["id"], fp, c.external_ref):
        raise IntakeError(409, "already received from this source")
    item_id = uuid4()
    path = "fallback" if source["standing_in"] else "primary"
    repo.insert_item(session, id=item_id, source_id=source["id"], bureau_id=source["bureau_id"], channel=channel,
                     path=path, fingerprint=fp, external_ref=c.external_ref, received_by=received_by,
                     payload_enc=complaints.keyring().encrypt(c.model_dump(mode="json"), str(item_id)))
    audit.record(session, principal, "intake.received", entity_type="intake_items", entity_id=str(item_id),
                 payload={"source": source["name"], "channel": channel, "path": path,
                          "external_ref": c.external_ref})
    return {"id": item_id, "path": path}


def submit_api(session: Session, api_key: str, timestamp: str, nonce: str, body: dict) -> dict:
    """The intake API, as the gateway principal. Refuses a wrong key, a stale or future timestamp and a
    nonce this source has used before (a replay). A source that is marked down still has its items queued:
    they wait, and are processed when it is back."""
    found = repo.sources(session, key=key_hash(api_key)) if api_key else []
    if not found or found[0]["channel"] != "api":
        raise IntakeError(401, "unknown API key")
    source = found[0]
    try:
        age = abs(datetime.now(UTC).timestamp() - int(timestamp))
    except ValueError:
        raise IntakeError(401, "X-Sethu-Timestamp must be Unix seconds") from None
    if age > get_settings().intake_clock_skew_seconds:
        raise IntakeError(401, "request timestamp is too old or in the future")
    if not 16 <= len(nonce) <= 128 or not nonce.isascii():
        raise IntakeError(401, "X-Sethu-Nonce must be 16 to 128 characters")
    limit = source["rate_per_minute"] or get_settings().intake_rate_per_minute
    # shortcut: counted, not locked; two requests at the very same moment can pass one over the limit.
    if repo.recent_requests(session, source["id"], 60) >= limit:
        log.warning("intake quota reached", extra={"source": source["name"]})
        raise IntakeError(429, f"more than {limit} requests in a minute from this source; try again shortly",
                          headers={"Retry-After": "60"})
    if not repo.use_nonce(session, source["id"], nonce):
        # Logged, not audited: the refusal rolls the request's transaction back.
        log.warning("intake replay refused", extra={"source": source["name"]})
        raise IntakeError(409, "this nonce was already used: replayed request refused")
    try:
        c = ComplaintIn.model_validate(body)
    except ValidationError as e:
        raise IntakeError(422, safe_reason(e)) from None
    return _enqueue(session, GATEWAY, source, c, "api", None)


def _own_source(session: Session, principal: Principal, channel: str) -> dict:
    found = [s for s in repo.sources(session, channel=channel, bureau_id=principal.bureau_id) if s["active"]]
    if not found:
        raise IntakeError(409, f"your bureau has no active {channel} source: ask an admin to add one")
    return found[0]  # highest priority first


def manual(session: Session, principal: Principal, c: ComplaintIn) -> dict:
    source = _own_source(session, principal, "manual")
    return _enqueue(session, principal, source, c, "manual", users.sync(session, principal))


def parse_rows(data: bytes, filename: str) -> list[dict]:
    """Rows of a CSV or XLSX file as dicts keyed by the header. Raises IntakeError for an unreadable file."""
    settings = get_settings()
    if len(data) > settings.intake_max_upload_bytes:
        raise IntakeError(413, f"file is larger than {settings.intake_max_upload_bytes} bytes")
    if data[:2] == b"PK" or filename.lower().endswith(".xlsx"):
        import openpyxl  # only for spreadsheets

        try:
            sheet = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True).worksheets[0]
            table = [["" if v is None else str(v) for v in row] for row in sheet.iter_rows(values_only=True)]
        except Exception as e:  # noqa: BLE001 - any parser failure means the file is unreadable
            raise IntakeError(422, f"not a readable XLSX file ({type(e).__name__})") from None
    else:
        try:
            table = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
        except (UnicodeDecodeError, csv.Error):
            raise IntakeError(422, "not a readable UTF-8 CSV file") from None
    if not table:
        raise IntakeError(422, "the file is empty")
    header = [h.strip().lower() for h in table[0]]
    missing = [c for c in ("institution_name", "category", "body") if c not in header]
    unknown = [h for h in header if h and h not in COLUMNS]
    if missing or unknown:
        raise IntakeError(422, f"header: missing {missing or 'nothing'}, unknown {unknown or 'nothing'}")
    rows = [dict(zip(header, r, strict=False)) for r in table[1:] if any(v.strip() for v in r)]
    if len(rows) > settings.intake_max_rows:
        raise IntakeError(413, f"more than {settings.intake_max_rows} rows")
    return rows


def row_to_complaint(row: dict) -> ComplaintIn:
    person = {k: row.get(f"complainant_{k}", "").strip() or None for k in ("name", "email", "phone")}
    fields = {k: row[k] for k in ("institution_name", "category", "body", "language", "filed_at", "external_ref")
              if (row.get(k) or "").strip()}
    return ComplaintIn(**fields, complainant=person if any(person.values()) else None)


def take_file(session: Session, principal: Principal, source: dict, data: bytes, filename: str,
              channel: str, received_by: UUID | None) -> dict:
    """Queue every good row of a file; report the others by row and field (never their content)."""
    errors, accepted = [], 0
    rows = parse_rows(data, filename)
    for n, row in enumerate(rows, start=1):
        try:
            with session.begin_nested():  # a refused row leaves nothing behind
                _enqueue(session, principal, source, row_to_complaint(row), channel, received_by)
            accepted += 1
        except ValidationError as e:
            errors += [{"row": n, "field": ".".join(map(str, x["loc"])), "message": x["msg"]}
                       for x in e.errors(include_input=False, include_url=False)]
        except IntakeError as e:
            errors.append({"row": n, "field": "-", "message": str(e)})
    audit.record(session, principal, "intake.file", entity_type="intake_sources", entity_id=str(source["id"]),
                 payload={"source": source["name"], "channel": channel, "rows": len(rows), "accepted": accepted,
                          "rejected": len({e["row"] for e in errors}), "sha256": hashlib.sha256(data).hexdigest()})
    return {"accepted": accepted, "rejected": len({e["row"] for e in errors}), "errors": errors}


def upload(session: Session, principal: Principal, data: bytes, filename: str) -> dict:
    source = _own_source(session, principal, "upload")
    return take_file(session, principal, source, data, filename, "upload", users.sync(session, principal))


def spool(engine=None, folder: str | None = None) -> dict:
    """Take files dropped into the spool folder: <folder>/<source name>/*.csv|*.xlsx, for active spool sources.
    A file is moved to processed/ once its rows are queued (with <file>.errors.csv beside it if some rows were
    refused), or to rejected/ with <file>.errors.txt if it cannot be read at all. Nothing is deleted."""
    root = folder or get_settings().intake_spool_dir
    counts = {"files": 0, "accepted": 0, "rejected": 0}
    if not root or not Path(root).is_dir():
        return counts
    with session_for(SYSTEM, engine) as session:
        sources = [s for s in repo.sources(session, channel="spool") if s["active"]]
    for source in sources:
        inbox = Path(root) / source["name"]
        for f in sorted(p for p in inbox.glob("*") if p.is_file() and p.suffix.lower() in (".csv", ".xlsx")):
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
            try:
                with session_for(SYSTEM, engine) as session:
                    result = take_file(session, SYSTEM, source, f.read_bytes(), f.name, "spool", None)
            except IntakeError as e:
                done = inbox / "rejected"
                done.mkdir(exist_ok=True)
                (done / f"{stamp}-{f.name}.errors.txt").write_text(str(e) + "\n", encoding="utf-8")
                shutil.move(f, done / f"{stamp}-{f.name}")
                log.warning("spool file rejected", extra={"source": source["name"], "reason": str(e)})
                continue
            done = inbox / "processed"
            done.mkdir(exist_ok=True)
            if result["errors"]:
                with open(done / f"{stamp}-{f.name}.errors.csv", "w", newline="", encoding="utf-8") as out:
                    w = csv.DictWriter(out, fieldnames=["row", "field", "message"])
                    w.writeheader()
                    w.writerows(result["errors"])
            shutil.move(f, done / f"{stamp}-{f.name}")
            counts["files"] += 1
            counts["accepted"] += result["accepted"]
            counts["rejected"] += result["rejected"]
    return counts


# ---------------------------------------------------------------- processing

def _create(session: Session, item: dict) -> dict:
    """One attempt at turning a queued item into a complaint. Raises to have it retried."""
    if not item["source_active"] or item["source_down"]:
        raise Held(f"source {item['source']} is {'marked down' if item['source_down'] else 'not active'}")
    c = ComplaintIn(**complaints.keyring().decrypt(item["payload_enc"], str(item["id"])))
    name = c.institution_name.lower()
    complaints.lock_text(session, item["fingerprint"])  # two items with the same text: one at a time
    if (same := complaints.same_text(session, item["bureau_id"], name, c.body)) is not None:
        return {"status": "duplicate", "duplicate_of": same["id"], "ref": same["ref"]}
    decision, _ = institutions.rank(session, c.institution_name)
    iid = decision["institution_id"] if decision else None
    near = complaints.similar_text(session, item["bureau_id"], iid, name, c.body,
                                   NEAR_DUPLICATE_SIMILARITY, NEAR_DUPLICATE_DAYS)
    created = complaints.create(
        session, SYSTEM, bureau_id=item["bureau_id"], source=item["source"], institution_name_raw=c.institution_name,
        category=c.category, body=c.body, language=c.language, filed_at=c.filed_at or datetime.now(UTC),
        complainant=c.complainant.model_dump() if c.complainant else None, institution_id=iid,
        audit_extra={"intake_item": str(item["id"]), "channel": item["channel"], "path": item["path"],
                     "institution_step": decision and decision["step"],
                     "near_duplicate_of": near and near["ref"]})
    return {"status": "done", "complaint_id": created["id"], "ref": created["ref"],
            "near_duplicate_of": near and near["id"]}


def process_one(session: Session) -> str | None:
    """Claim the next due item and try it. Returns what happened, or None when nothing is due."""
    item = repo.claim_next(session)
    if item is None:
        return None
    settings = get_settings()
    try:
        with session.begin_nested():
            outcome = _create(session, item)
    except Exception as e:  # noqa: BLE001 - any failure is retried, then dead-lettered; never lost
        reason = safe_reason(e)
        attempts = item["attempts"] + 1
        dead = attempts >= settings.intake_max_attempts
        later = None if dead else alerts.backoff(attempts, settings.intake_retry_base_seconds,
                                                 settings.intake_retry_max_seconds)
        repo.failed(session, item["id"], reason, later)
        repo.health(session, item["source_id"], ok=False)
        audit.record(session, SYSTEM, "intake.dead_lettered" if dead else "intake.attempt_failed",
                     entity_type="intake_items", entity_id=str(item["id"]),
                     payload={"source": item["source"], "attempts": attempts, "reason": reason,
                              "retry_in_seconds": later})
        log.warning("intake attempt failed", extra={"item": str(item["id"]), "attempts": attempts, "dead": dead})
        return "dead" if dead else "retry"
    if outcome["status"] == "duplicate":
        repo.finish(session, item["id"], status="duplicate", duplicate_of=outcome["duplicate_of"])
        audit.record(session, SYSTEM, "intake.duplicate", entity_type="intake_items", entity_id=str(item["id"]),
                     payload={"source": item["source"], "duplicate_of": outcome["ref"]})
    else:
        near = outcome["near_duplicate_of"]
        repo.finish(session, item["id"], status="done", complaint_id=outcome["complaint_id"],
                    near_duplicate_of=near, review_state="pending" if near else None, last_error=None)
    repo.health(session, item["source_id"], ok=True)
    return outcome["status"]


def process_due(engine=None, limit: int = 100) -> dict[str, int]:
    """Process due items, one transaction each. Safe to run from several workers at once."""
    counts: dict[str, int] = {}
    for _ in range(limit):
        with session_for(SYSTEM, engine) as session:
            outcome = process_one(session)
        if outcome is None:
            break
        counts[outcome] = counts.get(outcome, 0) + 1
    with session_for(SYSTEM, engine) as session:
        repo.forget_nonces(session, 2 * get_settings().intake_clock_skew_seconds)
    return counts


# ---------------------------------------------------------------- administration

def list_sources(session: Session) -> list[dict]:
    return repo.sources(session)


def _by_name(session: Session, name: str | None) -> dict | None:
    if not name:
        return None
    found = repo.sources(session, name=name)
    if not found:
        raise IntakeError(422, f"no source named {name}")
    return found[0]


def create_source(session: Session, principal: Principal, name: str, channel: str, bureau: str, priority: int,
                  fallback: str | None) -> dict:
    found = bureaus.by_code(session, bureau)
    if found is None:
        raise IntakeError(422, f"no bureau {bureau}")
    if repo.sources(session, name=name):
        raise IntakeError(409, f"a source named {name} exists")
    fb = _by_name(session, fallback)
    source_id = repo.insert_source(session, name=name, channel=channel, bureau_id=found["id"], priority=priority,
                                   fallback_source_id=fb and fb["id"])
    audit.record(session, principal, "intake.source_created", entity_type="intake_sources", entity_id=str(source_id),
                 payload={"name": name, "channel": channel, "bureau": bureau.upper(), "priority": priority,
                          "fallback": fallback})
    return repo.sources(session, id=source_id)[0]


def update_source(session: Session, principal: Principal, source_id: UUID, changes: dict) -> dict:
    if not repo.sources(session, id=source_id):
        raise IntakeError(404, "source not found")
    values = {k: changes[k] for k in ("priority", "active", "marked_down", "rate_per_minute")
              if changes.get(k) is not None}
    if changes.get("clear_fallback"):
        values["fallback_source_id"] = None
    elif changes.get("fallback"):
        fb = _by_name(session, changes["fallback"])
        if fb["id"] == source_id:
            raise IntakeError(422, "a source cannot be its own fallback")
        values["fallback_source_id"] = fb["id"]
    if values:
        repo.update_source(session, source_id, **values)
        audit.record(session, principal, "intake.source_updated", entity_type="intake_sources",
                     entity_id=str(source_id),
                     payload={k: (str(v) if isinstance(v, UUID) else v) for k, v in values.items()})
    return repo.sources(session, id=source_id)[0]


def issue_key(session: Session, principal: Principal, source_id: UUID) -> dict:
    """A new API key for an api source, replacing any old one. Only its hash is kept; it is shown once."""
    found = repo.sources(session, id=source_id)
    if not found:
        raise IntakeError(404, "source not found")
    if found[0]["channel"] != "api":
        raise IntakeError(409, "only an api source has a key")
    api_key = "sethu_" + secrets.token_urlsafe(32)
    repo.update_source(session, source_id, key_sha256=key_hash(api_key))
    audit.record(session, principal, "intake.key_issued", entity_type="intake_sources", entity_id=str(source_id),
                 payload={"source": found[0]["name"]})  # never the key, nor its hash
    return {"source": found[0]["name"], "api_key": api_key}


def list_items(session: Session, principal: Principal, status: str | None, review: bool) -> list[dict]:
    return [r | {"can_retry": r["status"] == "dead" and principal.role == "admin"}
            for r in repo.items(session, status, review, 200)]


def retry(session: Session, principal: Principal, item_id: UUID) -> dict:
    if not repo.retry(session, item_id):
        raise IntakeError(409, "only a dead-lettered item can be retried")
    audit.record(session, principal, "intake.retry", entity_type="intake_items", entity_id=str(item_id),
                 payload={"status": "pending"})
    return repo.item(session, item_id)


def mark_reviewed(session: Session, principal: Principal, item_id: UUID) -> dict:
    if not repo.reviewed(session, item_id, users.sync(session, principal)):
        raise IntakeError(409, "nothing to review on this item, or it is another bureau's")
    audit.record(session, principal, "intake.near_duplicate_reviewed", entity_type="intake_items",
                 entity_id=str(item_id), payload={"review_state": "reviewed"})
    return repo.item(session, item_id)
