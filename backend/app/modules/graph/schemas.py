from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Filters(BaseModel):
    state: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=100)
    bureau: str | None = Field(None, max_length=20)
    filed_from: date | None = None
    filed_to: date | None = None
    institution_id: UUID | None = None


FindingKind = Literal["transfer_loop", "stalled_transfer", "bottleneck", "category_spike", "deadline_escalation"]


class Node(BaseModel):
    """Metadata only. `kind` decides which of the optional fields are set."""
    id: str
    kind: Literal["bureau", "institution", "complaint"]
    label: str
    findings: list[str]
    name: str | None = None                 # bureau
    cases: int | None = None                # bureau, institution
    open: int | None = None
    institution_id: UUID | None = None      # institution
    state: str | None = None
    overdue: int | bool | None = None
    bureaus: list[str] | None = None
    multi_bureau: bool | None = None        # cases in several bureaus: highlighted as a cluster
    expanded: bool | None = None
    overlaps: dict[str, int] | None = None  # proposed and approved links among its cases
    complaint_id: UUID | None = None        # complaint
    status: str | None = None
    category: str | None = None
    bureau: str | None = None
    filed_at: str | None = None


class Edge(BaseModel):
    id: str
    source: str
    target: str
    kind: Literal["holds", "about", "transfer", "overlap_proposed", "overlap_approved"]
    count: int


class Graph(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    expanded_limit: int
