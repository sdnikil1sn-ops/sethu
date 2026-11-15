"""Database access. Every request runs in one transaction that carries the
caller's identity, so Row-Level Security applies even if a query forgets a filter.
"""
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from fastapi import Depends
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.auth import Principal, get_principal
from app.core.config import get_settings

SYSTEM = Principal(subject="system", name="system", role="system", bureau_id=None)


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True, pool_size=10)


def apply_context(session: Session, principal: Principal) -> None:
    """Transaction-local settings read by the sethu.ctx_* functions."""
    session.execute(
        text(
            "SELECT set_config('app.user_id', :u, true),"
            "       set_config('app.role', :r, true),"
            "       set_config('app.bureau_id', :b, true)"
        ),
        {
            "u": principal.subject,
            "r": principal.role,
            "b": str(principal.bureau_id) if principal.bureau_id else "",
        },
    )


@contextmanager
def session_for(principal: Principal, engine: Engine | None = None) -> Iterator[Session]:
    """One transaction scoped to a principal. Commits on success, rolls back on error."""
    with Session(engine or get_engine()) as session, session.begin():
        apply_context(session, principal)
        yield session


def get_session(principal: Principal = Depends(get_principal)) -> Iterator[Session]:
    with session_for(principal) as session:
        yield session
