from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Institution(BaseModel):
    id: UUID
    permanent_id: str | None
    name: str
    state: str | None
    district: str | None


class InstitutionRow(Institution):
    """A list row (with case counts) or a search hit (with score and the spelling that matched)."""
    complaints: int | None = None
    open: int | None = None
    score: float | None = None
    matched: str | None = None


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


class Profile(Institution):
    aliases: list[Alias]
    bureaus: list[str]
    open: int
    closed: int
    oldest_open: CaseSummary | None
    complaints: list[CaseSummary]


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
