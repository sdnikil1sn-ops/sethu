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
    missing_recipients: list[str]  # bureaus with no head who has an e-mail address: shown, not dropped
    cases: list[str]
    created_at: datetime
    approved_at: datetime | None
    approved_by: str | None
    sent_at: datetime | None
    attempts: int
    last_error: str | None
    next_attempt_at: datetime | None  # after a failed send: not tried again before this
    can_decide: bool
    can_retry: bool


class AlertPage(BaseModel):
    items: list[Alert]
    mail_inbox_url: str | None  # the local mail catcher, in the dev profile only


class DecisionIn(BaseModel):
    decision: Literal["approve", "reject"]
