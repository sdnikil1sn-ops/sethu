from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Alert(BaseModel):
    """An outbox row. The body carries case references, institution and category only."""
    id: UUID
    kind: str
    status: Literal["pending_approval", "approved", "sent", "rejected", "failed"]
    subject: str
    body: str
    recipients: list[str]
    cases: list[str]
    created_at: datetime
    approved_at: datetime | None
    approved_by: str | None
    sent_at: datetime | None
    attempts: int
    last_error: str | None
    can_decide: bool


class AlertPage(BaseModel):
    items: list[Alert]
    mail_inbox_url: str | None  # the local mail catcher, in the dev profile only


class DecisionIn(BaseModel):
    decision: Literal["approve", "reject"]
