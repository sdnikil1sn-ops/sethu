import re
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

SPACES = re.compile(r"\s+")


def tidy(value: str) -> str:
    """Normalise free text: trimmed, runs of whitespace (newlines too) made one space."""
    return SPACES.sub(" ", value).strip()


class Complainant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9 ()-]{6,20}$")

    @field_validator("name", "phone", mode="before")
    @classmethod
    def _tidy(cls, v):
        return tidy(v) or None if isinstance(v, str) else v

    @field_validator("email", mode="before")
    @classmethod
    def _email(cls, v):
        return v.strip().lower() or None if isinstance(v, str) else v


class ComplaintIn(BaseModel):
    """One complaint as any channel delivers it. The same rules apply to the API, an uploaded or spooled
    file row and the manual form."""
    model_config = ConfigDict(extra="forbid")
    institution_name: str = Field(min_length=3, max_length=300)
    category: str = Field(min_length=3, max_length=100)
    body: str = Field(min_length=20, max_length=10_000)
    language: Literal["en", "hi"] = "en"
    filed_at: datetime | None = None
    external_ref: str | None = Field(default=None, max_length=100, pattern=r"^[A-Za-z0-9._:/-]+$")
    complainant: Complainant | None = None

    @field_validator("institution_name", "category", "body", mode="before")
    @classmethod
    def _tidy(cls, v):
        return tidy(v) if isinstance(v, str) else v

    @field_validator("filed_at")
    @classmethod
    def _not_future(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        v = v if v.tzinfo else v.replace(tzinfo=UTC)
        if v > datetime.now(UTC):
            raise ValueError("filed_at is in the future")
        return v


class Accepted(BaseModel):
    id: UUID
    status: Literal["queued"] = "queued"
    path: str


class RowError(BaseModel):
    row: int            # 1 is the first data row, after the header
    field: str
    message: str


class UploadResult(BaseModel):
    accepted: int
    rejected: int
    errors: list[RowError]


class SourceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,40}$")
    channel: Literal["api", "upload", "manual", "spool"]
    bureau: str = Field(min_length=2, max_length=10)
    priority: int = Field(default=1, ge=1, le=9)
    fallback: str | None = None


class SourcePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    priority: int | None = Field(default=None, ge=1, le=9)
    fallback: str | None = None
    clear_fallback: bool = False
    active: bool | None = None
    marked_down: bool | None = None


class Source(BaseModel):
    id: UUID
    name: str
    channel: str
    bureau: str
    priority: int
    fallback: str | None
    active: bool
    marked_down: bool
    has_key: bool
    last_success_at: datetime | None
    last_failure_at: datetime | None
    failures: int
    pending: int
    dead: int


class IssuedKey(BaseModel):
    source: str
    api_key: str        # shown once; only its hash is stored


class Item(BaseModel):
    id: UUID
    source: str
    bureau: str
    channel: str
    path: str
    status: str
    attempts: int
    next_attempt_at: datetime | None
    last_error: str | None
    ref: str | None
    duplicate_of: str | None
    near_duplicate_of: str | None
    review_state: str | None
    created_at: datetime
    can_retry: bool = False
