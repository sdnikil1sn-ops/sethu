"""Settings come only from environment variables. No defaults for secrets."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SETHU_", extra="ignore")

    environment: Literal["dev", "test", "prod"] = "dev"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
