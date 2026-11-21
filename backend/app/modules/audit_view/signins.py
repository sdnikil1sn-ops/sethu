"""Sign-in events from Keycloak, read-only, for the Audit log screen.

Keycloak records login and admin events (both realms, docs/RUNBOOK.md "Sign-in events"). The backend reads
them with the confidential client `sethu-events`, whose service account holds only `view-events`, over the
internal network (the same address the token keys come from). Nothing is stored in SETHU: the rows are
Keycloak's, kept for its retention (90 days). Returned: time, event type, username, client, IP address and
error code. Never a token, password or session id.
"""
import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime

from app.core.config import get_settings

FAILED = ("LOGIN_ERROR", "CODE_TO_TOKEN_ERROR", "REFRESH_TOKEN_ERROR", "LOGOUT_ERROR", "CLIENT_LOGIN_ERROR",
          "UPDATE_PASSWORD_ERROR", "RESET_PASSWORD_ERROR")


class Unavailable(Exception):
    """Keycloak cannot be asked (no client secret configured, or it did not answer)."""


def _realm_url() -> str:
    jwks = get_settings().oidc_jwks_url  # http://keycloak:8080/auth/realms/sethu/protocol/openid-connect/certs
    shaped = "/realms/" in jwks and "/protocol/openid-connect/" in jwks
    if not jwks.startswith(("http://", "https://")) or not shaped:
        raise Unavailable("SETHU_OIDC_JWKS_URL is not a Keycloak realm's http(s) certs address")
    return jwks.split("/protocol/openid-connect/")[0]


def _call(request: urllib.request.Request) -> object:
    try:
        with urllib.request.urlopen(request, timeout=10) as r:  # noqa: S310 - internal Keycloak address from settings
            return json.loads(r.read())
    except Exception as e:  # noqa: BLE001 - shown as "unavailable", never with the response
        raise Unavailable(f"Keycloak did not answer ({type(e).__name__})") from None


def fetch(failed_only: bool, limit: int) -> list[dict]:
    secret = get_settings().keycloak_events_secret
    if not secret:
        raise Unavailable("sign-in events are not configured (SETHU_KEYCLOAK_EVENTS_SECRET)")
    realm = _realm_url()
    token = _call(urllib.request.Request(  # noqa: S310 - http(s) only, checked in _realm_url
        realm + "/protocol/openid-connect/token", method="POST",
        data=urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": "sethu-events",
                                     "client_secret": secret}).encode()))["access_token"]
    query = [("max", str(limit))] + ([("type", t) for t in FAILED] if failed_only else [])
    admin = realm.replace("/realms/", "/admin/realms/", 1)
    events = _call(urllib.request.Request(  # noqa: S310 - http(s) only, checked in _realm_url
        admin + "/events?" + urllib.parse.urlencode(query),
                                          headers={"Authorization": f"Bearer {token}"}))
    return [shape(e) for e in events]


def shape(e: dict) -> dict:
    details = e.get("details") or {}
    return {"time": datetime.fromtimestamp(e["time"] / 1000, UTC), "type": e.get("type"),
            "username": details.get("username"), "client": e.get("clientId"), "ip": e.get("ipAddress"),
            "error": e.get("error")}
