"""Reports: three tables over a date range, and CSV export. Every export is audited.

No report has a column for complaint text or complainant details, so an export cannot carry them.
"""
import csv
import io
from collections.abc import Callable
from datetime import date

from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.modules.reports import repo

# name -> (title, [(column, heading)], query)
REPORTS: dict[str, tuple[str, list[tuple[str, str]], Callable]] = {
    "institutions": ("Complaints by institution", [
        ("institution", "Institution"), ("permanent_id", "Permanent id"), ("state", "State"),
        ("district", "District"), ("cases", "Cases"), ("open", "Open"), ("overdue", "Overdue"),
        ("bureaus", "Bureaus with cases")], repo.institutions),
    "bureaus": ("Bureau performance", [
        ("bureau", "Bureau"), ("bureau_name", "Name"), ("filed", "Filed"), ("closed", "Closed"),
        ("median_days_to_close", "Median days to close"), ("overdue", "Overdue")], repo.bureaus),
    "overlaps": ("Overlap outcomes", [
        ("bureaus", "Bureaus"), ("suggested", "Suggested"), ("approved", "Approved"), ("rejected", "Rejected"),
        ("pending", "Awaiting review"), ("alerts_sent", "Alerts sent")], repo.overlaps),
}


def run(session: Session, principal: Principal, name: str, date_from: date | None, date_to: date | None) -> dict:
    title, columns, query = REPORTS[name]
    return {"name": name, "title": title, "date_from": date_from, "date_to": date_to,
            "scope": "all bureaus" if principal.bureau_id is None else "your bureau only",
            "columns": [{"key": k, "label": label} for k, label in columns],
            "rows": query(session, date_from, date_to)}


def _cell(value: object) -> str:
    text = "" if value is None else str(value)
    # A spreadsheet runs a cell starting with = + - @ as a formula: make such text inert.
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def export(session: Session, principal: Principal, name: str, date_from: date | None, date_to: date | None) -> str:
    """The report as CSV, audited in the same transaction."""
    report = run(session, principal, name, date_from, date_to)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([c["label"] for c in report["columns"]])
    for row in report["rows"]:
        writer.writerow([_cell(row[c["key"]]) for c in report["columns"]])
    audit.record(session, principal, "report.export", entity_type="report", entity_id=name,
                 payload={"report": name, "rows": len(report["rows"]), "scope": report["scope"],
                          "filters": {"date_from": date_from, "date_to": date_to}})
    return out.getvalue()
