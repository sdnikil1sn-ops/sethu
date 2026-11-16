from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Entry(BaseModel):
    """Identifiers and decisions only: payloads never hold complaint text."""
    seq: int
    ts: datetime
    actor: str
    actor_name: str
    actor_role: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    payload: dict[str, Any]
    prev_hash: str
    hash: str


class EntryPage(BaseModel):
    items: list[Entry]
    actions: list[str]  # every action in the ledger, for the filter


class ChainReport(BaseModel):
    ok: bool
    checked: int
    broken_seq: int | None
    reason: str | None
    row: Entry | None  # the first row that fails, as stored now
