from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InstitutionHit(BaseModel):
    id: UUID
    permanent_id: str | None
    name: str
    state: str | None
    district: str | None
    score: float
    why: str


class ComplaintHit(BaseModel):
    """Summary fields only. `why` says complaint text matched only where the caller may read it."""
    id: UUID
    ref: str
    bureau: str
    institution_id: UUID | None
    institution: str | None
    category: str
    status: str
    filed_at: datetime
    readable: bool
    why: list[str]


class ComplaintHits(BaseModel):
    total: int
    items: list[ComplaintHit]


class Results(BaseModel):
    q: str
    institutions: list[InstitutionHit]
    complaints: ComplaintHits
