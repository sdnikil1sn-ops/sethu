import time
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.auth import AuthError, Principal, decode_token, get_principal
from app.main import app

ISSUER, AUDIENCE = "http://issuer.test/realms/sethu", "sethu-api"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
BUREAU = str(uuid4())


def token(key=KEY, roles=("officer",), bureau=BUREAU, **overrides) -> str:
    now = int(time.time())
    claims = {"sub": "abc", "iss": ISSUER, "aud": AUDIENCE, "iat": now, "exp": now + 60,
              "preferred_username": "rao", "realm_access": {"roles": list(roles)}}
    if bureau:
        claims["bureau_id"] = bureau
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


def decode(tok: str) -> Principal:
    return decode_token(tok, KEY.public_key(), issuer=ISSUER, audience=AUDIENCE)


def test_valid_token_maps_to_principal():
    p = decode(token())
    assert (p.role, str(p.bureau_id), p.name) == ("officer", BUREAU, "rao")


def test_highest_role_wins():
    assert decode(token(roles=("officer", "admin", "offline_access"))).role == "admin"


@pytest.mark.parametrize("bad", [
    lambda: token(key=OTHER_KEY),                       # wrong signature
    lambda: token(exp=int(time.time()) - 10),           # expired
    lambda: token(aud="another-api"),                   # wrong audience
    lambda: token(iss="http://evil.test"),              # wrong issuer
    lambda: token(roles=("offline_access",)),           # no SETHU role
    lambda: token(bureau=None),                         # officer without a bureau
    lambda: token(bureau="not-a-uuid"),
    lambda: jwt.encode({"sub": "abc"}, "secret", algorithm="HS256"),  # algorithm confusion
])
def test_bad_tokens_are_rejected(bad):
    with pytest.raises(AuthError):
        decode(bad())


client = TestClient(app)


def test_liveness_needs_no_auth():
    assert client.get("/health/live").json() == {"status": "ok"}


def test_api_requires_a_token():
    assert client.get("/api/v1/me").status_code == 401
    assert client.get("/api/v1/audit/verify").status_code == 401


def test_me_and_role_gate():
    app.dependency_overrides[get_principal] = lambda: Principal("abc", "rao", "officer", None)
    try:
        assert client.get("/api/v1/me").json()["role"] == "officer"
        assert client.get("/api/v1/audit/verify").status_code == 403
    finally:
        app.dependency_overrides.clear()
