from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Bureau(BaseModel):
    id: UUID
    code: str
    name: str
    active: bool
    created_at: datetime
    updated_at: datetime


class BureauRow(Bureau):
    cases: int
    people: int
    heads_with_email: int   # 0 means this bureau's alerts reach nobody


class BureauIn(BaseModel):
    code: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z][A-Za-z0-9-]*$")
    name: str = Field(min_length=3, max_length=200)


class BureauChange(BaseModel):
    name: str | None = Field(None, min_length=3, max_length=200)
    active: bool | None = None
