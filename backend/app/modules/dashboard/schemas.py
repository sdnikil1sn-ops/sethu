from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class Count(BaseModel):
    key: str
    label: str
    total: int
    open: int
    overdue: int


class Totals(BaseModel):
    total: int
    open: int
    overdue: int


class Week(BaseModel):
    week: date
    filed: int


class OverdueCase(BaseModel):
    """Summary fields only: no complaint text."""
    id: UUID
    ref: str
    bureau: str
    institution: str | None
    category: str
    status: str
    due_at: datetime


class Attention(BaseModel):
    # The counts below stop at app.db.paging.COUNT_CAP + 1; the screen shows more than COUNT_CAP as "1,000+".
    overlaps_to_review: int
    overlaps_confirmed: int
    alerts_to_approve: int
    alerts_unsent: int
    findings_open: int
    overdue_total: int
    overdue: list[OverdueCase]


class Overview(BaseModel):
    generated_at: datetime
    totals: Totals
    by_bureau: list[Count]
    by_status: list[Count]
    by_category: list[Count]
    weekly: list[Week]
    attention: Attention
