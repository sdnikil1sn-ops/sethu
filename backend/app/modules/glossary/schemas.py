from datetime import datetime

from pydantic import BaseModel


class Term(BaseModel):
    language: str
    term: str
    english: str
    type: str
    notes: str | None
    needs_review: bool


class Version(BaseModel):
    version: int
    terms: int
    created_at: datetime


class GlossaryOut(BaseModel):
    version: int
    terms: list[Term]
    versions: list[Version]


class UploadOut(BaseModel):
    version: int
    terms: int
    errors: list[dict]
