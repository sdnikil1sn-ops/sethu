"""Bureaus are data, managed by admins. A bureau is deactivated, never deleted: its cases and
history keep pointing at it, and a deactivated bureau can no longer receive transfers. The code is
fixed once created (people's `bureau_id` in Keycloak and the seed refer to the bureau's id)."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.modules.bureaus import repo


class BureauError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def listing(session: Session) -> list[dict]:
    return repo.listing(session)


def create(session: Session, principal: Principal, code: str, name: str) -> dict:
    code, name = code.strip().upper(), name.strip()
    if repo.by_code(session, code):
        raise BureauError(409, f"a bureau with the code {code} already exists")
    bureau_id = repo.insert(session, code, name)
    audit.record(session, principal, "bureau.created", entity_type="bureaus", entity_id=str(bureau_id),
                 payload={"code": code, "name": name})
    return repo.get(session, bureau_id)


def update(session: Session, principal: Principal, bureau_id: UUID, name: str | None, active: bool | None) -> dict:
    found = repo.get(session, bureau_id)
    if found is None:
        raise BureauError(404, "bureau not found")
    wanted = {"name": name.strip() if name is not None else found["name"],
              "active": found["active"] if active is None else active}
    changed = sorted(k for k, v in wanted.items() if found[k] != v)
    if not changed:
        return found
    if not repo.update(session, bureau_id, **wanted):
        raise BureauError(403, "only an admin can change a bureau")
    audit.record(session, principal, "bureau.updated", entity_type="bureaus", entity_id=str(bureau_id),
                 payload={"code": found["code"], "changed": changed} | {k: wanted[k] for k in changed})
    return repo.get(session, bureau_id)
