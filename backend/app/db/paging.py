"""One page of a list query, with a total that stays cheap on any filter.

The total is counted up to COUNT_CAP + 1 rows and no further: a broad filter over 100,000 complaints answers
"1,000+" (`total_capped`) instead of counting them all. `has_next` comes from fetching one row more than the page.
Callers pass the query without ORDER BY or LIMIT; values are always bound parameters.
"""
from typing import Any

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

COUNT_CAP = 1000
PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class PageMeta(BaseModel):
    total: int            # at most COUNT_CAP; see total_capped
    total_capped: bool    # true: there are more than `total` rows ("1,000+")
    has_next: bool
    limit: int
    offset: int


def page_params(limit: int = Query(PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
                offset: int = Query(0, ge=0, le=1_000_000)) -> tuple[int, int]:
    """FastAPI dependency: the page size and the offset."""
    return limit, offset


def capped_count(session: Session, sql: str, params: dict[str, Any], cap: int | None = None) -> tuple[int, bool]:
    cap = COUNT_CAP if cap is None else int(cap)
    n = session.execute(text(f"SELECT count(*) FROM ({sql} LIMIT {cap + 1}) AS counted"), params).scalar_one()  # noqa: S608
    return min(n, cap), n > cap


def page(session: Session, sql: str, order_by: str, params: dict[str, Any], limit: int, offset: int) -> dict:
    rows = [dict(r) for r in session.execute(
        text(f"{sql} ORDER BY {order_by} LIMIT :_limit OFFSET :_offset"),  # noqa: S608 - fixed text from code
        params | {"_limit": limit + 1, "_offset": offset}).mappings()]
    total, capped = capped_count(session, sql, params)
    return {"items": rows[:limit], "total": total, "total_capped": capped, "has_next": len(rows) > limit,
            "limit": limit, "offset": offset}
