from datetime import date, datetime
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
    community: int | None = None            # A4: Louvain community of an institution or bureau (latest build)


class Edge(BaseModel):
    id: str
    source: str
    target: str
    kind: Literal["holds", "about", "transfer", "overlap_proposed", "overlap_approved"]
    count: int
    confidence: float | None = None         # A4: overlap edges carry A3's method, confidence and model version
    method: str | None = None
    model_version: str | None = None


class Graph(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    expanded_limit: int
    build: dict | None = None               # the latest graph build: version, method, communities, when


class EgoNode(BaseModel):
    id: str
    kind: Literal["institution", "complaint"]
    depth: int
    label: str | None = None
    bureau: str | None = None
    readable: bool | None = None


class EgoEdge(BaseModel):
    source: str
    target: str
    kind: str
    method: str | None
    confidence: float | None
    model_version: str | None


class Ego(BaseModel):
    institution_id: UUID
    hops: int
    min_confidence: float
    nodes: list[EgoNode]
    edges: list[EgoEdge]
    capped: bool
    method: str


class EvidenceCase(BaseModel):
    """A case behind a link: its summary always; its source channel only if the viewer may read the case, else
    the restricted marker."""
    id: UUID
    ref: str
    bureau: str
    status: str
    filed_at: datetime
    readable: bool
    source: str | None = None
    restricted: str | None = None


class Explanation(BaseModel):
    kind: str
    status: str | None = None
    method: str
    confidence: float | None
    model: str | None
    model_version: str | None
    similarity: float | None = None
    reasons: list[str]
    evidence: list[EvidenceCase]


class Queued(BaseModel):
    task_id: str
