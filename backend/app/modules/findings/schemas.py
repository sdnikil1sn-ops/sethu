from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class Finding(BaseModel):
    """Identifiers, bureaus and the numbers used. Never complaint text."""
    id: UUID
    kind: Literal["transfer_loop", "stalled_transfer", "bottleneck", "category_spike", "deadline_escalation"]
    status: Literal["open", "resolved", "dismissed"]
    first_seen: datetime
    decided_at: datetime | None
    decided_by: str | None
    evidence: dict[str, Any]
    complaint_id: UUID | None
    ref: str | None
    institution_id: UUID | None
    institution: str | None
    bureaus: list[str]
    alert_id: UUID | None
    alert_status: str | None


class DecisionIn(BaseModel):
    status: Literal["open", "dismissed"]


class DetectOut(BaseModel):
    created: int
    reopened: int
    resolved: int


class TrendRow(BaseModel):
    institution_id: UUID
    institution: str
    state: str | None
    district: str | None
    recent: int
    previous: int
    bureaus: list[str]


class Trend(BaseModel):
    days: int
    items: list[TrendRow]
