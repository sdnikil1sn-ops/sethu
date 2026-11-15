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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
