from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core import jobs
from app.core.auth import Principal, require_roles
from app.db.session import get_session
from app.modules.institutions import service as institutions
from app.modules.semantic import schemas, service
from app.modules.users import service as users

router = APIRouter(tags=["ai"])

READ = require_roles("officer", "bureau_head", "oversight", "admin", "auditor")   # and it can read the case's text
DECIDE = require_roles("officer", "bureau_head")       # and the database checks the bureau holds the case
ADMIN = require_roles("admin")
SEE_CLASSIFIERS = require_roles("admin", "oversight")


def _run(work):
    try:
        return work()
    except service.SemanticError as e:
        raise HTTPException(e.status, str(e)) from e


@router.get("/api/v1/cases/{complaint_id}/suggestions", response_model=schemas.CaseSuggestions)
def suggestions(complaint_id: UUID, _: Principal = Depends(READ), session: Session = Depends(get_session)) -> dict:
    """The AI's suggested category and institution for the case, with the path that produced them."""
    return service.for_case(session, complaint_id)


@router.post("/api/v1/cases/{complaint_id}/suggestions/category", response_model=schemas.Decided)
def decide_category(complaint_id: UUID, body: schemas.CategoryIn, principal: Principal = Depends(DECIDE),
                    session: Session = Depends(get_session)) -> dict:
    """Accept the suggestion (send it back), keep the current category, or choose another."""
    return _run(lambda: service.decide_category(session, principal, complaint_id, body.category))


@router.post("/api/v1/cases/{complaint_id}/suggestions/institution", response_model=schemas.Decided)
def decide_institution(complaint_id: UUID, body: schemas.InstitutionIn, principal: Principal = Depends(DECIDE),
                       session: Session = Depends(get_session)) -> dict:
    """Link the case to the suggested institution or another one (the same as the resolution queue)."""
    if institutions.resolve_by_officer(session, principal, complaint_id, body.institution_id) is None:
        raise HTTPException(404, "unresolved case or institution not found")
    return {"decision": "linked", "suggested": None, "path": None}


@router.get("/api/v1/ai/classifier", response_model=list[schemas.ClassifierVersion])
def classifiers(_: Principal = Depends(SEE_CLASSIFIERS), session: Session = Depends(get_session)) -> list[dict]:
    return service.classifiers(session)


@router.post("/api/v1/ai/classifier/retrain", response_model=schemas.Queued, status_code=202)
def retrain(principal: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> dict:
    """Queue training on the ai-worker. The new version is activated only if it does no worse on the held-out
    set than the active one."""
    by = users.sync(session, principal)
    task_id = jobs.queue("sethu.ai.retrain_classifier", {"requested_by": str(by)}, on="ai")
    audit.record(session, principal, "classifier.retrain_requested", entity_type="jobs", entity_id=task_id,
                 payload={"job": "ai.retrain_classifier"})
    return {"task_id": task_id}


@router.post("/api/v1/ai/classifier/{version}/activate", response_model=schemas.Activated)
def activate(version: int, principal: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> dict:
    """Roll back (or forward) to a stored version."""
    return _run(lambda: service.activate(session, principal, version))


@router.post("/api/v1/ai/reembed", response_model=schemas.Queued, status_code=202)
def reembed(principal: Principal = Depends(ADMIN), session: Session = Depends(get_session)) -> dict:
    """Run the maintenance job now (it also runs every 30 s): registry vectors and a re-embed batch."""
    task_id = jobs.queue("sethu.ai.maintain", on="ai")
    audit.record(session, principal, "ai.reembed_requested", entity_type="jobs", entity_id=task_id,
                 payload={"job": "ai.maintain"})
    return {"task_id": task_id}
