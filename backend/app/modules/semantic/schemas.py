from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Suggestion(BaseModel):
    """What the AI suggested for a case, how (path: model, fallback rules, or an officer must pick) and how sure."""
    kind: str
    suggested: str | None
    candidates: list[dict]
    path: str
    provider: str | None
    confidence: float | None
    model_version: str | None
    status: str
    created_at: datetime
    decided_at: datetime | None


class CaseSuggestions(BaseModel):
    category: Suggestion | None
    institution: Suggestion | None
    categories: list[str]


class CategoryIn(BaseModel):
    category: str = Field(min_length=1, max_length=100)


class InstitutionIn(BaseModel):
    institution_id: UUID


class Decided(BaseModel):
    decision: str | None = None
    suggested: str | None = None
    path: str | None = None


class ClassifierVersion(BaseModel):
    version: int
    status: str
    metrics: dict
    embedding_model: str
    embedding_version: str
    sha256: str
    created_at: datetime
    activated_at: datetime | None
    created_by: str | None


class Queued(BaseModel):
    task_id: str


class Activated(BaseModel):
    version: int
    previous: int | None
