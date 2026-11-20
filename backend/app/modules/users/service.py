"""People. Keycloak is the source of truth for who someone is; SETHU keeps a copy in app_users
(names on screens, alert e-mail, the actor of an action). `sync` brings that copy in step with
the token on every sign-in (`/api/v1/me`) and every action, so a role or bureau changed in
Keycloak reaches SETHU, and a bureau head's e-mail is there for alert mail."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit import service as audit
from app.core.auth import Principal
from app.modules.users import repo


def sync(session: Session, principal: Principal) -> UUID:
    """The person's app_users id, created or updated from the token. Audited when anything changes;
    the audit entry names the fields that changed, never their values."""
    found = repo.find(session, principal.subject)
    # A token without a name or e-mail claim keeps what SETHU already has.
    wanted = {
        "display_name": principal.full_name or (found and found["display_name"]) or principal.name,
        "email": (principal.email or "").strip().lower() or (found and found["email"]) or None,
        "role": principal.role,
        "bureau_id": principal.bureau_id,
    }
    if found is None:
        user_id = repo.insert(session, principal.subject, **wanted)
        audit.record(session, principal, "user.registered", entity_type="app_users", entity_id=str(user_id),
                     payload={"role": principal.role, "bureau_id": principal.bureau_id and str(principal.bureau_id),
                              "has_email": wanted["email"] is not None})
        return user_id
    changed = sorted(k for k, v in wanted.items() if found[k] != v)
    if changed:
        repo.update(session, found["id"], **wanted)
        audit.record(session, principal, "user.updated", entity_type="app_users", entity_id=str(found["id"]),
                     payload={"changed": changed, "role": principal.role,
                              "bureau_id": principal.bureau_id and str(principal.bureau_id),
                              "has_email": wanted["email"] is not None})
    return found["id"]


def recipients(session: Session, bureau_ids: list[UUID]) -> tuple[list[str], list[str]]:
    """Alert mail goes to the stored e-mail of each bureau's heads. Returns (addresses, codes of the
    bureaus with no head who has an address), so an alert can say who it cannot reach."""
    rows = repo.heads(session, bureau_ids)
    reached = {r["code"] for r in rows if r["email"]}
    return (sorted({r["email"] for r in rows if r["email"]}),
            sorted({r["code"] for r in rows} - reached))


def listing(session: Session) -> list[dict]:
    return [r | {"no_email": not r["email"]} for r in repo.listing(session)]
