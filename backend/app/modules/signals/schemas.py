from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class MemberCase(BaseModel):
    """A case in the signal: summary only; `restricted` instead of a link when the viewer may not read it."""
    id: UUID
    ref: str
    bureau: str
    state: str | None
    category: str | None
    filed_at: datetime
    readable: bool
    restricted: str | None = None


class Signal(BaseModel):
    id: UUID
    label: str                       # "Emerging signal: requires verification"
    category_group: str
    categories: list[str]
    states: list[str]
    window_start: date
    window_end: date
    method: Literal["dbscan", "zscore", "ratio"]
    path: str
    score: float | None
    members: int
    explanation: dict
    parameters: dict
    status: Literal["new", "acknowledged", "dismissed", "actioned"]
    status_reason: str | None
    decided_at: datetime | None
    decided_by: str | None
    first_seen: datetime
    last_seen: datetime
    bureaus: list[str]
    cases: list[MemberCase]


class DecisionIn(BaseModel):
    status: Literal["acknowledged", "dismissed", "actioned"]
    reason: str | None = Field(None, max_length=500)


class StateRow(BaseModel):
    state: str
    map_name: str | None             # the state's name in the bundled map, when it is there
    complaints: int
    open: int
    recent: int
    institutions: int
    signals: int


class MapStates(BaseModel):
    recent_days: int
    label: str
    states: list[StateRow]


class StateInstitution(BaseModel):
    id: UUID
    name: str
    district: str | None
    complaints: int
    open: int


class MapState(BaseModel):
    state: str
    institutions: list[StateInstitution]
    signals: list[Signal]


class Queued(BaseModel):
    task_id: str
