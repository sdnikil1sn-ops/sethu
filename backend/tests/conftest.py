"""Tests run against a real PostgreSQL database, because the guarantees under
test (hash chain, append-only, Row-Level Security) live in the database.

Required environment:
  MIGRATION_DATABASE_URL  owner role (sethu_owner)
  SETHU_DATABASE_URL      runtime role (sethu_app)
  SETHU_TEST_DB_WIPE_OK   must be "1": these tests EMPTY EVERY TABLE, including
                          the audit log. Point them at a throwaway database only.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

os.environ.setdefault("SETHU_ENVIRONMENT", "test")
os.environ.setdefault("SETHU_OIDC_ISSUER", "http://issuer.test/realms/sethu")
os.environ.setdefault("SETHU_OIDC_JWKS_URL", "http://issuer.test/certs")
os.environ.setdefault("SETHU_DATABASE_URL", "postgresql+psycopg://unset/unset")

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
    "alerts, overlap_links, case_actions, complaints, institution_aliases, "
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
