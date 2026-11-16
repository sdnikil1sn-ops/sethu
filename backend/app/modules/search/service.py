"""Top-bar search. Composes the institutions and complaints services; holds no SQL of its own."""
from sqlalchemy.orm import Session

from app.modules.complaints import service as complaints
from app.modules.institutions import service as institutions


def search(session: Session, q: str, limit: int) -> dict:
    return {"q": q, "institutions": institutions.lookup(session, q, limit),
            "complaints": complaints.lookup(session, q, limit)}
