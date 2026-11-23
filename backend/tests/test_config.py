"""Production configuration: the backend refuses unsafe settings, and the seed loader and the
demo-user import refuse a production configuration. No database needed."""
import base64
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from pydantic import ValidationError

from app.core.config import Settings

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))  # repo root, for the seed package
from seed import load  # noqa: E402

STRONG = "Zq8vN3kLp0TwXy7RbD2m"  # 20 characters, no dev word (test value only)
SECRETS = Path(tempfile.mkdtemp(prefix="sethu-test-secrets-"))
(SECRETS / "app").write_text(STRONG + "\n")  # a trailing newline, as editors leave one
(SECRETS / "redis").write_text(STRONG + "a")
(SECRETS / "keys.json").write_text(json.dumps({"active": "k", "keys": {"k": base64.b64encode(bytes(32)).decode()}}))
GOOD = {
    "environment": "prod",
    "database_url": "postgresql+psycopg://sethu_app@postgres:5432/sethu",
    "database_password_file": str(SECRETS / "app"),
    "redis_url": "redis://redis:6379/0",
    "redis_password_file": str(SECRETS / "redis"),
    "complainant_keys_file": str(SECRETS / "keys.json"),
    "oidc_issuer": "https://sethu.aicte.example/auth/realms/sethu",
    "oidc_jwks_url": "http://keycloak:8080/auth/realms/sethu/protocol/openid-connect/certs",
    "smtp_host": "relay.aicte.example",
    "smtp_security": "starttls",
    "alert_from": "sethu-alerts@aicte.example",
    # AI Phase A1: production now also requires the AI libraries' offline switches (the image sets both).
    "hf_hub_offline": "1",
    "transformers_offline": "1",
}


for name, value in (("empty", ""), ("short", "CHANGE_ME"), ("placeholder", "CHANGE_ME_CHANGE_ME_1"),
                    ("seedtest", "seedtest-seedtest-seedtest")):
    (SECRETS / name).write_text(value)


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
    ({"database_password_file": str(SECRETS / "empty")}, "SETHU_DATABASE_URL is missing"),
    ({"database_password_file": str(SECRETS / "short")}, "SETHU_DATABASE_URL is shorter"),
    ({"database_password_file": str(SECRETS / "placeholder")}, "SETHU_DATABASE_URL is a placeholder or dev value"),
    ({"database_password_file": str(SECRETS / "seedtest")}, "SETHU_DATABASE_URL is a placeholder or dev value"),
    ({"redis_password_file": None}, "SETHU_REDIS_PASSWORD_FILE is not set"),
    ({"database_password_file": None}, "SETHU_DATABASE_PASSWORD_FILE is not set"),
    ({"database_url": f"postgresql+psycopg://sethu_app:{STRONG}@postgres/sethu"},
     "SETHU_DATABASE_URL carries a password: use the matching *_PASSWORD_FILE secret instead"),
    ({"smtp_password": STRONG}, "SETHU_SMTP_PASSWORD carries a password"),
    ({"complainant_keys_file": None}, "SETHU_COMPLAINANT_KEYS_FILE is not set"),
    ({"complainant_keys_file": str(SECRETS / "short")}, "SETHU_COMPLAINANT_KEYS_FILE: the keyring is not valid"),
    ({"oidc_issuer": "http://localhost:8080/auth/realms/sethu"}, "SETHU_OIDC_ISSUER is not https"),
    ({"smtp_host": "mailpit"}, "SETHU_SMTP_HOST is the dev mail catcher"),
    ({"alert_from": "sethu-alerts@sethu.test"}, "SETHU_ALERT_FROM uses the test domain"),
    ({"smtp_security": "none"}, "SETHU_SMTP_SECURITY is none"),
    ({"smtp_username": "relay-user"}, "SETHU_SMTP_USERNAME is set but SETHU_SMTP_PASSWORD is missing"),
    ({"smtp_ca_file": "/no/such/ca.pem"}, "SETHU_SMTP_CA_FILE does not exist"),
    ({"hf_hub_offline": None}, "HF_HUB_OFFLINE is not 1"),
    ({"transformers_offline": "0"}, "TRANSFORMERS_OFFLINE is not 1"),
    ({"ai_endpoints": {"ocr": "https://api.example.com/v1/ocr"}}, "provider ocr points outside the deployment"),
    ({"ai_endpoints": {"ocr": "http://8.8.8.8:8000"}}, "provider ocr points outside the deployment"),
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
                       smtp_security="none",
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


def test_passwords_come_from_secret_files_url_encoded():
    (SECRETS / "odd").write_text("p@ss/word:with%chars-0123456789\n")
    loaded = settings(database_password_file=str(SECRETS / "odd"))
    assert urlsplit(loaded.database_url).password == "p%40ss%2Fword%3Awith%25chars-0123456789"  # noqa: S105 - test value
    assert urlsplit(loaded.redis_url).password == STRONG + "a"
    (SECRETS / "smtp").write_text("relay-secret-0123456789\n")
    assert settings(smtp_password_file=str(SECRETS / "smtp")).smtp_password == "relay-secret-0123456789"  # noqa: S105


def test_an_unreadable_secret_file_is_named_not_shown():
    message = refused(database_password_file=str(SECRETS / "does-not-exist"))
    assert "SETHU_DATABASE_PASSWORD_FILE: the secret file cannot be read" in message


def test_ai_endpoints_inside_the_deployment_are_allowed():
    inside = {"ocr": "http://ocr-server:8000", "mt": "http://localhost:9000", "nlp": "http://172.20.0.5:8080"}
    assert settings(ai_endpoints=inside).ai_endpoints == inside
    message = refused(ai_endpoints={"a": "http://model.internal.example:80", "b": "http://169.254.169.254/"})
    assert "provider a points outside" in message and "provider b points outside" in message
    assert "model.internal" not in message                                # the URL itself is never echoed
