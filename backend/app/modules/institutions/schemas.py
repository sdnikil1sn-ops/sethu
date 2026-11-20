from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Institution(BaseModel):
    id: UUID
    permanent_id: str | None
    name: str
    state: str | None
    district: str | None


class InstitutionRow(Institution):
    """A list row with case counts; a search hit also has its score and why it matched."""
    complaints: int
    open: int
    score: float | None = None
    why: str | None = None


class Candidate(Institution):
    score: float
    reason: str


class CaseSummary(BaseModel):
    id: UUID
    ref: str
    bureau: str
    category: str | None
    status: str
    filed_at: datetime
    due_at: datetime | None
    closed_at: datetime | None


class Alias(BaseModel):
    alias: str
    source: str


class CategoryShare(BaseModel):
    category: str
    cases: int
    share: float


class BureauCount(BaseModel):
    bureau: str
    cases: int


class Volume(BaseModel):
    total: int
    last_12_months: int
    per_month: float


class Recurrence(BaseModel):
    repeat_cases: int
    share: float
    categories: list[str]
    window_days: int


class Disposal(BaseModel):
    closed: int
    median_days: float | None


class Trend(BaseModel):
    recent: int
    previous: int
    window_days: int
    direction: Literal["up", "down", "flat"]


class Dna(BaseModel):
    """Profile DNA: six measures from case summaries (no complaint text)."""
    category_mix: list[CategoryShare]
    volume: Volume
    recurrence: Recurrence
    disposal: Disposal
    bureaus: list[BureauCount]
    trend: Trend


class Profile(Institution):
    aliases: list[Alias]
    bureaus: list[str]
    open: int
    closed: int
    oldest_open: CaseSummary | None
    complaints: list[CaseSummary]
    dna: Dna


class QueueItem(BaseModel):
    id: UUID
    ref: str
    bureau: str
    institution_name_raw: str
    filed_at: datetime
    candidates: list[Candidate]


class ResolveIn(BaseModel):
    institution_id: UUID


class ResolveOut(BaseModel):
    ref: str
    institution_id: UUID
    alias_added: bool


class RunOut(BaseModel):
    resolved: int
    queued: int
