from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CaseRow(BaseModel):
    """The fields every authenticated role may see for any case (sethu.complaint_summaries)."""
    id: UUID
    ref: str
    bureau: str
    bureau_name: str
    category: str | None
    status: str
    institution_id: UUID | None
    institution: str | None
    state: str | None
    filed_at: datetime
    due_at: datetime | None
    closed_at: datetime | None
    overdue: bool
    days_remaining: int | None
    readable: bool


class CasePage(BaseModel):
    total: int
    items: list[CaseRow]


class Action(BaseModel):
    id: UUID
    ref: str
    action: str
    from_bureau: str | None
    to_bureau: str | None
    actor: str | None
    assignee: str | None
    note: str | None
    created_at: datetime
    acknowledged_at: datetime | None


class Case(CaseRow):
    """Detail. The fields below stay empty unless the caller may read the complaint."""
    body: str | None
    institution_name_raw: str | None
    language: str | None
    source: str | None
    resolution_state: str | None
    history: list[Action]
    can_act: bool
    awaiting_acknowledgement: bool


class Timeline(BaseModel):
    actions: list[Action]
    hidden_cases: int


class Bureau(BaseModel):
    id: UUID
    code: str
    name: str


class Options(BaseModel):
    bureaus: list[Bureau]
    categories: list[str]
    states: list[str]
    statuses: list[str]


class Assignee(BaseModel):
    id: UUID
    display_name: str
    role: str


class ActionIn(BaseModel):
    action: Literal["assign", "note", "reply", "transfer", "acknowledge", "close"]
    note: str | None = Field(None, max_length=2000)
    to_bureau: str | None = Field(None, max_length=20)
    assignee_id: UUID | None = None


class Filters(BaseModel):
    bureau: str | None = Field(None, max_length=20)
    category: str | None = Field(None, max_length=100)
    status: Literal["open", "in_progress", "transferred", "replied", "closed"] | None = None
    institution_id: UUID | None = None
    state: str | None = Field(None, max_length=100)
    filed_from: date | None = None
    filed_to: date | None = None
    overdue: bool | None = None
    q: str | None = Field(None, max_length=200)
