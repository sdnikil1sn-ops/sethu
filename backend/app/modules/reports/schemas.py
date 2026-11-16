from datetime import date
from typing import Any

from pydantic import BaseModel


class Column(BaseModel):
    key: str
    label: str


class Report(BaseModel):
    """Counts and reference data only: no complaint text, no complainant details."""
    name: str
    title: str
    date_from: date | None
    date_to: date | None
    scope: str
    columns: list[Column]
    rows: list[dict[str, Any]]
