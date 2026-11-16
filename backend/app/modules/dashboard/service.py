"""Dashboard: counts, trend and a "needs attention" list. Read only, nothing to audit."""
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.dashboard import repo

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
            "overdue_total": overdue[0]["total"] if overdue else 0,
            "overdue": [{k: v for k, v in r.items() if k != "total"} for r in overdue],
        },
    }
