from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core import jobs
from app.core.auth import Principal, require_roles
from app.core.params import Blank
from app.db.session import get_session
from app.modules.graph import schemas, service

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")
ADMIN = require_roles("admin")
NodeId = Annotated[str, Query(pattern=r"^[bic]:[A-Za-z0-9-]{1,40}$")]


@router.get("", response_model=schemas.Graph)
def graph(
    filters: Annotated[schemas.Filters, Query()],
    finding_kind: Annotated[schemas.FindingKind | None, Blank] = None,
    expand: Annotated[list[UUID], Query(max_length=50)] = [],  # noqa: B006 - FastAPI copies query defaults
    min_confidence: Annotated[float | None, Query(ge=0, le=1)] = None,
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> dict:
    """Bureaus and institutions (aggregated, coloured by community), plus the complaints of the institutions in
    `expand`; overlap links below `min_confidence` are left out."""
    return service.build(session, filters.model_dump(), expand, finding_kind, min_confidence)


@router.get("/ego/{institution_id}", response_model=schemas.Ego)
def ego(institution_id: UUID, hops: Annotated[int | None, Query(ge=1, le=5)] = None,
        min_confidence: Annotated[float | None, Query(ge=0, le=1)] = None,
        _: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    """An institution's neighbourhood (its cases, their overlaps, the institutions they lead to), for large data."""
    return service.ego(session, institution_id, hops, min_confidence)


@router.get("/explain", response_model=schemas.Explanation)
def explain(source: NodeId, target: NodeId,
            kind: Literal["holds", "about", "transfer", "overlap_proposed", "overlap_approved"],
            _: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    """Why two nodes are linked. Evidence cases the viewer may not read carry the restricted marker instead."""
    try:
        return service.explain(session, source, target, kind)
    except (service.GraphError, ValueError) as e:
        raise HTTPException(getattr(e, "status", 422), str(e)) from e


@router.post("/build", response_model=schemas.Queued, status_code=202)
def build(principal: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> dict:
    """Queue a graph build now (it also runs every 5 minutes, rebuilding when something changed)."""
    task_id = jobs.queue("sethu.graph.build", {"force": True})
    audit.record(session, principal, "graph.build_requested", entity_type="jobs", entity_id=task_id,
                 payload={"job": "graph.build"})
    return {"task_id": task_id}
