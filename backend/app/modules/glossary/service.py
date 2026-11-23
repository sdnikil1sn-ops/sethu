"""The glossary: term normalisation for complaints (app/ai/glossary.py), NOT translation. An admin uploads the
whole list as CSV or XLSX; every row is checked and the file is taken only if all rows pass (the error report names
row and field). Each upload is a new version (older ones are kept); the newest is used. Audited."""
import csv
import io
import re
import zipfile

from sqlalchemy.orm import Session

from app.ai.glossary import Glossary, normalise
from app.audit import service as audit
from app.core.auth import Principal
from app.modules.glossary import repo

COLUMNS = ("language", "term", "english", "type", "notes", "needs_review")
TYPES = {"category", "document", "fee", "approval", "institution", "person", "place", "action", "general"}
LANGUAGE = re.compile(r"^[a-z]{2,3}(-latn)?$")
ENGLISH = re.compile(r"^[a-z0-9][a-z0-9 /&-]{0,79}$")
MAX_BYTES, MAX_ROWS, MAX_EXPANDED = 1_000_000, 5000, 10_000_000
_cache: dict[int, Glossary] = {}


class GlossaryError(Exception):
    def __init__(self, status: int, message: str, errors: list[dict] | None = None):
        super().__init__(message)
        self.status, self.errors = status, errors or []


def current(session: Session) -> Glossary:
    """The newest version as a matcher, built once per version in this process."""
    version = repo.current_version(session)
    if version not in _cache:
        _cache.clear()
        _cache[version] = Glossary([(t["term"], t["english"]) for t in repo.terms(session, version)], version)
    return _cache[version]


def listing(session: Session) -> dict:
    version = repo.current_version(session)
    return {"version": version, "terms": repo.terms(session, version), "versions": repo.versions(session)}


def _table(data: bytes, filename: str) -> list[list[str]]:
    if data[:2] == b"PK" or filename.lower().endswith(".xlsx"):
        import openpyxl
        try:
            if sum(i.file_size for i in zipfile.ZipFile(io.BytesIO(data)).infolist()) > MAX_EXPANDED:
                raise GlossaryError(413, f"the spreadsheet expands to more than {MAX_EXPANDED} bytes")
            sheet = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True).worksheets[0]
            rows = []
            for row in sheet.iter_rows(values_only=True):
                rows.append(["" if v is None else str(v) for v in row])
                if len(rows) > MAX_ROWS + 1:
                    raise GlossaryError(413, f"more than {MAX_ROWS} rows")
            return rows
        except GlossaryError:
            raise
        except Exception as e:  # noqa: BLE001 - any parser failure means the file is unreadable
            raise GlossaryError(422, f"not a readable XLSX file ({type(e).__name__})") from None
    try:
        return list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error):
        raise GlossaryError(422, "not a readable UTF-8 CSV file") from None


def check(data: bytes, filename: str) -> tuple[list[dict], list[dict]]:
    """Rows ready to store, and errors as {row, field, problem} (row 1 is the first after the header)."""
    if len(data) > MAX_BYTES:
        raise GlossaryError(413, f"file is larger than {MAX_BYTES} bytes")
    table = _table(data, filename)
    if not table:
        raise GlossaryError(422, "the file is empty")
    header = [h.strip().lower() for h in table[0]]
    missing = [c for c in COLUMNS[:4] if c not in header]
    if missing:
        raise GlossaryError(422, f"header: missing {', '.join(missing)} (columns: {', '.join(COLUMNS)})")
    if len(table) > MAX_ROWS + 1:
        raise GlossaryError(413, f"more than {MAX_ROWS} rows")
    rows, errors, seen = [], [], set()
    for n, raw in enumerate(table[1:], start=1):
        if not any(c.strip() for c in raw):
            continue
        cell = {h: (raw[i].strip() if i < len(raw) else "") for i, h in enumerate(header) if h in COLUMNS}
        row = {"language": cell.get("language", "").lower(), "term": cell.get("term", ""),
               "english": cell.get("english", "").lower(), "type": cell.get("type", "").lower(),
               "notes": cell.get("notes") or None,
               "needs_review": cell.get("needs_review", "").lower() in ("true", "yes", "1")}
        rules = (
            ("language", LANGUAGE.match(row["language"]), "a code such as hi, ta or hi-latn"),
            ("term", 0 < len(row["term"]) <= 200 and normalise(row["term"]), "1 to 200 characters"),
            ("english", ENGLISH.match(row["english"]), "lower-case English, up to 80 characters"),
            ("type", row["type"] in TYPES, "one of " + ", ".join(sorted(TYPES))),
            ("notes", row["notes"] is None or len(row["notes"]) <= 300, "up to 300 characters"),
        )
        problems = [(field, problem) for field, ok, problem in rules if not ok]
        key = (row["language"], normalise(row["term"]))
        if not problems and key in seen:
            problems.append(("term", "repeated in this file"))
        seen.add(key)
        errors += [{"row": n, "field": f, "problem": p} for f, p in problems]
        if not problems:
            rows.append(row)
    return rows, errors


def upload(session: Session, principal: Principal, data: bytes, filename: str) -> dict:
    rows, errors = check(data, filename)
    if errors:
        raise GlossaryError(422, f"{len(errors)} problem(s); nothing was stored", errors)
    if not rows:
        raise GlossaryError(422, "no terms in the file")
    version = repo.current_version(session) + 1
    repo.insert_version(session, version, rows)
    audit.record(session, principal, "glossary.uploaded", entity_type="glossary_terms", entity_id=str(version),
                 payload={"version": version, "terms": len(rows),
                          "languages": sorted({r["language"] for r in rows}),
                          "needs_review": sum(r["needs_review"] for r in rows)})
    return {"version": version, "terms": len(rows), "errors": []}
