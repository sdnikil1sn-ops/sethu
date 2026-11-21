"""Tests run against a real PostgreSQL database, because the guarantees under
test (hash chain, append-only, Row-Level Security) live in the database.

Required environment:
  MIGRATION_DATABASE_URL  owner role (sethu_owner)
  SETHU_DATABASE_URL      runtime role (sethu_app)
  SETHU_TEST_DB_WIPE_OK   must be "1": these tests EMPTY EVERY TABLE, including
                          the audit log. Point them at a throwaway database only.
"""
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

os.environ.setdefault("SETHU_ENVIRONMENT", "test")
os.environ.setdefault("SETHU_OIDC_ISSUER", "http://issuer.test/realms/sethu")
os.environ.setdefault("SETHU_OIDC_JWKS_URL", "http://issuer.test/certs")
os.environ.setdefault("SETHU_DATABASE_URL", "postgresql+psycopg://unset/unset")

# A throwaway keyring for complainant details, made fresh for each test run.
TEST_KEYRING = Path(tempfile.mkdtemp(prefix="sethu-test-keys-")) / "complainant_keys.json"
TEST_KEYRING.write_text(json.dumps({"active": "test-1", "keys": {"test-1": base64.b64encode(os.urandom(32)).decode()}}))
os.environ.setdefault("SETHU_COMPLAINANT_KEYS_FILE", str(TEST_KEYRING))

BACKEND = Path(__file__).resolve().parents[1]
OWNER_URL = os.environ.get("MIGRATION_DATABASE_URL")
HAVE_DB = (
    bool(OWNER_URL)
    and "unset" not in os.environ["SETHU_DATABASE_URL"]
    and os.environ.get("SETHU_TEST_DB_WIPE_OK") == "1"
)
SKIP_REASON = "set MIGRATION_DATABASE_URL, SETHU_DATABASE_URL and SETHU_TEST_DB_WIPE_OK=1"

requires_db = pytest.mark.skipif(not HAVE_DB, reason=SKIP_REASON)

TABLES = (
    "intake_nonces, intake_items, intake_sources, "
    "findings, alerts, overlap_links, case_actions, complaints, institution_aliases, "
    "institutions, app_users, bureaus, audit_log"
)


@pytest.fixture(scope="session")
def owner_engine():
    if not HAVE_DB:
        pytest.skip(SKIP_REASON)
    subprocess.run(  # noqa: S603
        [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, check=True
    )
    engine = create_engine(OWNER_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def app_engine(owner_engine):
    engine = create_engine(os.environ["SETHU_DATABASE_URL"])
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_db(request):
    if "owner_engine" not in request.fixturenames and "app_engine" not in request.fixturenames:
        yield
        return
    owner = request.getfixturevalue("owner_engine")
    with owner.begin() as conn:
        conn.execute(text("ALTER TABLE sethu.audit_log DISABLE TRIGGER audit_log_no_truncate"))
        conn.execute(text(f"TRUNCATE {', '.join('sethu.' + t.strip() for t in TABLES.split(','))} CASCADE"))
        conn.execute(text("ALTER TABLE sethu.audit_log ENABLE TRIGGER audit_log_no_truncate"))
    yield


@pytest.fixture
def world(app_engine):
    """The seeded database, the demo people and a way to look a case up by reference."""
    from app.core.auth import Principal
    from app.db.session import SYSTEM, session_for
    from tests.test_seed import load

    load.load(app_engine)
    with session_for(SYSTEM, app_engine) as s:
        bureau = {r.code: r.id for r in s.execute(text("SELECT code, id FROM sethu.bureaus"))}
        case = {r.ref: r.id for r in s.execute(text("SELECT ref, id FROM sethu.complaints"))}

    def person(username, role, code=None):
        return Principal(str(load.user_id(username)), username, role, bureau[code] if code else None)

    return {
        "engine": app_engine, "bureau": bureau, "case": case,
        "rao": person("rao", "officer", "PGRC"), "fernandes": person("fernandes", "bureau_head", "PGRC"),
        "iyer": person("iyer", "bureau_head", "RB"), "menon": person("menon", "oversight"),
        "das": person("das", "auditor"),
    }
