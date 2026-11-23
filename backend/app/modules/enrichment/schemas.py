from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AttachmentOut(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    sha256: str


class Attachment(AttachmentOut):
    ocr_status: str              # pending, done, review (a person must read it) or skipped
    created_at: datetime


class Enrichment(BaseModel):
    """What the AI pipeline found. The complaint's own text is unchanged; this sits beside it."""
    status: str                  # pending, done, review
    language: str | None
    language_confidence: float | None
    language_candidates: list[str]
    translated_text: str | None
    translation_path: str | None  # not_needed, model, glossary (terms only), untranslated
    tags: list[str]
    glossary_version: int | None
    glossary_coverage: float | None
    ocr_text: str | None
    ocr_path: str | None          # embedded, primary, fallback, manual
    updated_at: datetime


class ReviewItem(BaseModel):
    id: UUID
    kind: str
    complaint_id: UUID
    ref: str
    bureau: str
    attachment_id: UUID | None
    reason: str
    status: str
    created_at: datetime
    resolved_at: datetime | None


class ReviewDone(BaseModel):
    id: UUID
    kind: str
    complaint_id: UUID
    status: str
