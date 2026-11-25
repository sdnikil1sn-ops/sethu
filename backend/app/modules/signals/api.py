from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core import jobs
from app.core.auth import Principal, require_roles
from app.core.params import Blank
from app.db.session import get_session
from app.modules.signals import schemas, service

router = APIRouter(tags=["signals"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")   # Row-Level Security narrows
DECIDE = require_roles("oversight", "bureau_head")                                 # and the database checks which
ADMIN = require_roles("admin")
State = Annotated[str, Query(min_length=2, max_length=100)]


@router.get("/api/v1/signals", response_model=list[schemas.Signal])
def signals(status: Annotated[Literal["new", "acknowledged", "dismissed", "actioned"] | None, Blank] = None,
            state: Annotated[str | None, Query(max_length=100)] = None,
            _: Principal = Depends(READ), session: Session = Depends(get_session)) -> list[dict]:
    """Emerging signals the caller may see, newest first, each with its explanation and member cases."""
    return service.listing(session, status, state)


@router.post("/api/v1/signals/{signal_id}/decision", response_model=schemas.Signal)
def decide(signal_id: UUID, body: schemas.DecisionIn, principal: Principal = Depends(DECIDE),
           session: Session = Depends(get_session)) -> dict:
    try:
        return service.decide(session, principal, signal_id, body.status, body.reason)
    except service.SignalError as e:
        raise HTTPException(e.status, str(e)) from e


@router.post("/api/v1/signals/detect", response_model=schemas.Queued, status_code=202)
def detect(principal: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> dict:
    task_id = jobs.queue("sethu.signals.detect")
    audit.record(session, principal, "signal.detect_requested", entity_type="jobs", entity_id=task_id,
                 payload={"job": "signals.detect"})
    return {"task_id": task_id}


@router.get("/api/v1/map/states", response_model=schemas.MapStates)
def map_states(_: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    """Complaint density per state (summary counts) and the signals the caller may see, for the India map."""
    return service.map_states(session)


@router.get("/api/v1/map/state", response_model=schemas.MapState)
def map_state(state: State, _: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    """One state's institutions (to their profiles) and its signals (to their evidence)."""
    return service.map_state(session, state)
