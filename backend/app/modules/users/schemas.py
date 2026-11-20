from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Person(BaseModel):
    id: UUID
    display_name: str
    email: str | None
    role: str
    bureau: str | None
    active: bool
    updated_at: datetime
    no_email: bool   # flagged on the admin screen: alert mail cannot reach this person
