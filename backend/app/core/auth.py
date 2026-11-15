"""Authentication (Keycloak-issued JWT) and role checks.

The API trusts nothing from the client except a signed token. Role and bureau
come from token claims, and are pushed into the database session so that
Row-Level Security enforces them a second time.
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings

# Highest privilege first: a user holding several roles acts as the first match.
ROLE_PRECEDENCE = ("admin", "oversight", "auditor", "bureau_head", "officer")
BUREAU_SCOPED = {"bureau_head", "officer"}
ALGORITHMS = ["RS256", "ES256"]

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    name: str
    role: str
    bureau_id: UUID | None


class AuthError(Exception):
    pass


def principal_from_claims(claims: dict[str, Any]) -> Principal:
    granted = set((claims.get("realm_access") or {}).get("roles") or [])
    role = next((r for r in ROLE_PRECEDENCE if r in granted), None)
    if role is None:
        raise AuthError("token carries no SETHU role")

    bureau_id: UUID | None = None
    raw = claims.get("bureau_id")
    if raw:
        try:
            bureau_id = UUID(str(raw))
        except ValueError as exc:
            raise AuthError("bureau_id claim is not a UUID") from exc
    if role in BUREAU_SCOPED and bureau_id is None:
        raise AuthError(f"role {role} requires a bureau_id claim")

    subject = claims.get("sub")
    if not subject:
        raise AuthError("token has no subject")
    return Principal(
        subject=str(subject),
        name=str(claims.get("preferred_username") or subject),
        role=role,
        bureau_id=bureau_id,
    )


def decode_token(token: str, key: Any, *, issuer: str, audience: str) -> Principal:
    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=ALGORITHMS,
            issuer=issuer,
            audience=audience,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthError(f"invalid token: {exc}") from exc
    return principal_from_claims(claims)


@lru_cache
def _jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_keys=True, lifespan=600)


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> Principal:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    try:
        key = _jwks_client(settings.oidc_jwks_url).get_signing_key_from_jwt(credentials.credentials)
        return decode_token(
            credentials.credentials,
            key.key,
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
        )
    except (AuthError, jwt.PyJWTError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from exc


def require_roles(*roles: str):
    allowed = set(roles)

    def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "role not permitted")
        return principal

    return dependency
