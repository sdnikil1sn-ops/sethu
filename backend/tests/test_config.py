"""Production configuration: the backend refuses unsafe settings, and the seed loader and the
demo-user import refuse a production configuration. No database needed."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))  # repo root, for the seed package
from seed import load  # noqa: E402

STRONG = "Zq8vN3kLp0TwXy7RbD2m"  # 20 characters, no dev word (test value only)
GOOD = {
    "environment": "prod",
    "database_url": f"postgresql+psycopg://sethu_app:{STRONG}@postgres:5432/sethu",
    "redis_url": f"redis://:{STRONG}a@redis:6379/0",
    "oidc_issuer": "https://sethu.aicte.example/auth/realms/sethu",
    "oidc_jwks_url": "http://keycloak:8080/auth/realms/sethu/protocol/openid-connect/certs",
    "smtp_host": "relay.aicte.example",
    "alert_from": "sethu-alerts@aicte.example",
}


def settings(**changes) -> Settings:
    return Settings(_env_file=None, **(GOOD | changes))


def refused(**changes) -> str:
    with pytest.raises(ValidationError) as e:
        settings(**changes)
    return str(e.value)


def test_a_complete_production_configuration_starts():
    assert settings().environment == "prod"


@pytest.mark.parametrize(("changes", "says"), [
    ({"debug": True}, "SETHU_DEBUG is on"),
    ({"database_url": "postgresql+psycopg://sethu_app:@postgres:5432/sethu"}, "SETHU_DATABASE_URL is missing"),
    ({"database_url": "postgresql+psycopg://sethu_app:CHANGE_ME@postgres/sethu"}, "SETHU_DATABASE_URL is shorter"),
    ({"database_url": "postgresql+psycopg://sethu_app:CHANGE_ME_CHANGE_ME_1@postgres/sethu"},
     "SETHU_DATABASE_URL is a placeholder or dev value"),
    ({"database_url": "postgresql+psycopg://sethu_app:seedtest-seedtest-seedtest@postgres/sethu"},
     "SETHU_DATABASE_URL is a placeholder or dev value"),
    ({"redis_url": "redis://redis:6379/0"}, "SETHU_REDIS_URL is missing"),  # the built-in default
    ({"oidc_issuer": "http://localhost:8080/auth/realms/sethu"}, "SETHU_OIDC_ISSUER is not https"),
    ({"smtp_host": "mailpit"}, "SETHU_SMTP_HOST is the dev mail catcher"),
    ({"alert_from": "sethu-alerts@sethu.test"}, "SETHU_ALERT_FROM uses the test domain"),
])
def test_each_unsafe_value_is_refused_by_name(changes, says):
    message = refused(**changes)
    assert says in message
    assert "CHANGE_ME" not in message and "seedtest" not in message  # names the variable, never the value
    assert STRONG not in message and "input_value" not in message      # nor echoes the other settings


def test_all_problems_are_reported_at_once():
    message = refused(debug=True, smtp_host="mailpit", oidc_issuer="http://x/auth/realms/sethu")
    assert all(s in message for s in ("SETHU_DEBUG", "SETHU_SMTP_HOST", "SETHU_OIDC_ISSUER"))


def test_dev_and_test_keep_working_with_dev_values():
    for environment in ("dev", "test"):
        dev = settings(environment=environment, debug=True, smtp_host="mailpit", alert_from="a@sethu.test",
                       database_url="postgresql+psycopg://sethu_app:seedtest@127.0.0.1/sethu",
                       redis_url="redis://redis:6379/0", oidc_issuer="http://localhost:8080/auth/realms/sethu")
        assert dev.environment == environment


def test_the_seed_loader_refuses_production(monkeypatch):
    monkeypatch.setattr(load, "get_settings", settings)
    with pytest.raises(load.ProductionRefused, match="SETHU_ENVIRONMENT is prod"):
        load.load(engine=None)  # refused before any connection is made


def _shell() -> str | None:
    """A working POSIX shell (Git's sh on Windows, where `bash` may be the WSL launcher)."""
    sh = shutil.which("sh")
    try:
        ok = sh and subprocess.run([sh, "-c", "echo ok"], capture_output=True, text=True, timeout=10).stdout  # noqa: S603
    except OSError:
        return None
    return sh if ok and ok.strip() == "ok" else None


@pytest.mark.skipif(_shell() is None, reason="needs a POSIX shell")
def test_the_demo_user_import_refuses_production():
    script = (ROOT / "infra/demo-users/import.sh").read_text(encoding="utf-8")
    run = subprocess.run([_shell(), "-s"], input=script, capture_output=True, text=True,  # noqa: S603
                         env={"SETHU_ENVIRONMENT": "prod"}, timeout=30)
    assert run.returncode == 1 and "refusing: SETHU_ENVIRONMENT is prod" in run.stderr
    # In dev it gets past the guard (and then stops for want of the variables it needs).
    dev = subprocess.run([_shell(), "-s"], input=script, capture_output=True, text=True,  # noqa: S603
                         env={"SETHU_ENVIRONMENT": "dev"}, timeout=30)
    assert "refusing" not in dev.stderr and "DEMO_USER_PASSWORD" in dev.stderr
