from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_roles
from app.core.params import Blank
from app.db.session import get_session
from app.modules.graph import schemas, service

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")


@router.get("", response_model=schemas.Graph)
def graph(
    filters: Annotated[schemas.Filters, Query()],
    finding_kind: Annotated[schemas.FindingKind | None, Blank] = None,
    expand: Annotated[list[UUID], Query(max_length=50)] = [],  # noqa: B006 - FastAPI copies query defaults
    _: Principal = Depends(READ),
    session: Session = Depends(get_session),
) -> dict:
    """Bureaus and institutions (aggregated), plus the complaints of the institutions in `expand`."""
    return service.build(session, filters.model_dump(), expand, finding_kind)
