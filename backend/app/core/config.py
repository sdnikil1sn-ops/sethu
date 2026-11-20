"""Settings come only from environment variables. No defaults for secrets.

In production (`SETHU_ENVIRONMENT=prod`) the settings are checked when they are first read,
so the API and the worker refuse to start on a missing, placeholder or dev value instead of
running half-configured. See docs/RUNBOOK.md, "Production configuration".
"""
from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Values that must never be a production secret: the .env.example placeholder, the test
# stack's password, and the usual defaults. Compared case-insensitively, also as a substring.
DEV_SECRETS = ("change_me", "changeme", "seedtest", "password", "postgres", "secret", "admin", "sethu", "demo")
MIN_SECRET_LENGTH = 16


class Settings(BaseSettings):
    # hide_input_in_errors: a refusal must name the variable, never echo the settings (they hold secrets).
    model_config = SettingsConfigDict(env_prefix="SETHU_", extra="ignore", hide_input_in_errors=True)

    environment: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False                 # FastAPI debug pages (tracebacks in responses); never in prod

    # Runtime connection: the least-privilege role, subject to Row-Level Security.
    database_url: str
    redis_url: str = "redis://redis:6379/0"

    # OIDC (Keycloak). The issuer is what the browser sees; the JWKS URL is the
    # internal address the API uses, so no request ever leaves the deployment.
    oidc_issuer: str
    oidc_audience: str = "sethu-api"
    oidc_jwks_url: str

    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    alert_from: str = "sethu-alerts@sethu.test"

    sla_days: int = 21

    # Deadlock and bottleneck detection (app/modules/findings/service.py).
    stalled_transfer_days: int = 7     # a transfer nobody acknowledged for this long is a finding
    bottleneck_min_open: int = 3       # queues smaller than this are never a bottleneck
    bottleneck_share: float = 0.6      # more than this share overdue (or, for a bureau, older than its median)
    spike_min_count: int = 5           # a state and category with fewer complaints in 30 days is never a spike
    spike_ratio: float = 3.0           # ...and it must be at least this many times its 90-day baseline (per 30 days)

    @model_validator(mode="after")
    def _production_ready(self) -> "Settings":
        if self.environment == "prod" and (problems := production_problems(self)):
            raise ValueError("refusing to start in production: " + "; ".join(problems))
        return self


def _weak(secret: str | None) -> str | None:
    """Why a secret is unfit for production, or None if it is fine."""
    if not secret:
        return "missing"
    if len(secret) < MIN_SECRET_LENGTH:
        return f"shorter than {MIN_SECRET_LENGTH} characters"
    if any(word in secret.lower() for word in DEV_SECRETS):
        return "a placeholder or dev value"
    return None


def production_problems(s: Settings) -> list[str]:
    """Everything wrong with these settings for production. Names variables, never values."""
    problems = []
    if s.debug:
        problems.append("SETHU_DEBUG is on")
    for name, url in (("SETHU_DATABASE_URL", s.database_url), ("SETHU_REDIS_URL", s.redis_url)):
        if why := _weak(urlsplit(url).password):
            problems.append(f"the password in {name} is {why}")
    if urlsplit(s.oidc_issuer).scheme != "https":
        problems.append("SETHU_OIDC_ISSUER is not https")
    if s.smtp_host in ("mailpit", "localhost", "127.0.0.1", ""):
        problems.append("SETHU_SMTP_HOST is the dev mail catcher or empty")
    if s.alert_from.lower().endswith(("@sethu.test", ".test")):
        problems.append("SETHU_ALERT_FROM uses the test domain")
    return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
