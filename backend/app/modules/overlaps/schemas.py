from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.db.paging import PageMeta


class LinkedCase(BaseModel):
    id: UUID
    ref: str
    bureau: str
    status: str
    filed_at: datetime


class Link(BaseModel):
    """A Tier 2 suggestion or decision. Carries case references, never complaint text."""
    id: UUID
    tier: int
    score: float | None
    reasons: list[str]
    signals: dict = {}   # e.g. {"trigram": 0.42, "semantic": 0.88, "fired": ["semantic"], "model": ...}
    status: Literal["proposed", "approved", "rejected"]
    created_at: datetime
    decided_at: datetime | None
    decided_by: str | None
    institution_id: UUID | None
    institution: str | None
    category: str | None
    cases: list[LinkedCase]
    can_decide: bool
    alert_status: str | None
    alert_recipients: list[str] | None


class Tier1Case(BaseModel):
    id: UUID
    ref: str
    bureau: str
    category: str | None


class Tier1Institution(BaseModel):
    institution_id: UUID
    institution: str
    state: str | None
    bureaus: list[str]
    cases: list[Tier1Case]
    pairs: int
    tier2_pairs: int


class LinkPage(PageMeta):
    items: list[Link]


class DecisionIn(BaseModel):
    decision: Literal["approve", "reject"]


class DetectOut(BaseModel):
    suggested: int


class DetectQueued(BaseModel):
    task_id: str


class DetectStatus(BaseModel):
    state: str                      # PENDING (queued or unknown), STARTED, SUCCESS, FAILURE
    suggested: int | None = None    # when it has finished
    skipped: bool = False           # another run was already going (its suggestions appear when it finishes)
