"""Dashboard: counts, trend and a "needs attention" list. Read only, nothing to audit."""
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.dashboard import repo
from app.modules.findings import service as findings

WEEKS = 27  # this week and the 26 before it: a little over six months
OVERDUE_SHOWN = 15


def overview(session: Session) -> dict:
    overdue = repo.overdue_cases(session, OVERDUE_SHOWN)
    pending = repo.pending(session)
    totals = repo.by_bureau(session)
    return {
        "generated_at": datetime.now(UTC),
        "totals": {k: sum(r[k] for r in totals) for k in ("total", "open", "overdue")},
        "by_bureau": totals,
        "by_status": repo.by_column(session, "status"),
        "by_category": repo.by_column(session, "category"),
        "weekly": repo.weekly(session, WEEKS),
        "attention": pending | {
            "findings_open": findings.open_count(session),
            "overdue_total": overdue["total"] + overdue["total_capped"],   # COUNT_CAP + 1 means "1,000+"
            "overdue": overdue["items"],
        },
    }
