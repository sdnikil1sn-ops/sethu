"""Settings come only from environment variables. No defaults for secrets.

In production (`SETHU_ENVIRONMENT=prod`) the settings are checked when they are first read,
so the API and the worker refuse to start on a missing, placeholder or dev value instead of
running half-configured. See docs/RUNBOOK.md, "Production configuration".
"""
import ipaddress
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from pydantic import AliasChoices, Field, PrivateAttr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.crypto import KeyringError, load_keyring

# Values that must never be a production secret: the .env.example placeholder, the test
# stack's password, and the usual defaults. Compared case-insensitively, also as a substring.
DEV_SECRETS = ("change_me", "changeme", "seedtest", "password", "postgres", "secret", "admin", "sethu", "demo")
MIN_SECRET_LENGTH = 16


class Settings(BaseSettings):
    # hide_input_in_errors: a refusal must name the variable, never echo the settings (they hold secrets).
    model_config = SettingsConfigDict(env_prefix="SETHU_", extra="ignore", hide_input_in_errors=True)

    environment: Literal["dev", "test", "prod"] = "dev"
    _inline_passwords: set[str] = PrivateAttr(default_factory=set)  # which settings carried a password inline
    debug: bool = False                 # FastAPI debug pages (tracebacks in responses); never in prod

    # Runtime connection: the least-privilege role, subject to Row-Level Security.
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    # Production: passwords come from secret files (/run/secrets/...), put into the URLs at start.
    database_password_file: str | None = None
    redis_password_file: str | None = None
    smtp_password_file: str | None = None

    # OIDC (Keycloak). The issuer is what the browser sees; the JWKS URL is the
    # internal address the API uses, so no request ever leaves the deployment.
    oidc_issuer: str
    oidc_audience: str = "sethu-api"
    oidc_jwks_url: str

    # Sign-in events: the confidential realm client `sethu-events` (view-events only), read on the internal network.
    keycloak_events_secret: str | None = None
    keycloak_events_secret_file: str | None = None

    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    # none: plain (Mailpit in dev only); starttls: upgrade on 587; tls: implicit TLS on 465.
    # The relay's certificate is always verified (system CAs, or smtp_ca_file).
    smtp_security: Literal["none", "starttls", "tls"] = "none"
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_ca_file: str | None = None
    alert_from: str = "sethu-alerts@sethu.test"
    alert_max_attempts: int = 10         # spans about 4 hours (an hour-long relay outage heals itself); then `failed`
    alert_retry_base_seconds: int = 60   # backoff: 1, 2, 4, 8, 16 minutes...
    alert_retry_max_seconds: int = 3600  # ...but never more than an hour between attempts

    sla_days: int = 21

    # Audit-chain anchors (app/audit/anchor.py): a write-once directory outside the database. The worker
    # appends; the backend reads it to compare. Empty: no export.
    audit_anchor_dir: str | None = None

    # Semantic overlap signal (app/modules/overlaps): a local ONNX model baked into the image, never downloaded at
    # run time. Off, or with no model directory, overlap detection is trigram only, as before.
    semantic_overlap: bool = True
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache_dir: str | None = None     # set in the image: /opt/sethu/models
    semantic_threshold: float = 0.75           # cosine similarity, inside the rules; calibrated on the seed (RUNBOOK)

    # Complaint intake (app/modules/intake). No setting here makes a network call.
    intake_spool_dir: str | None = None       # fallback channel: a mounted folder, one subfolder per spool source
    intake_max_attempts: int = 6              # then the item is dead-lettered, with the reason
    intake_retry_base_seconds: int = 60
    intake_retry_max_seconds: int = 3600
    intake_clock_skew_seconds: int = 300      # an API request's timestamp must be this close to now
    intake_rate_per_minute: int = 60          # API requests per source per minute (a source may set its own)
    intake_max_upload_bytes: int = 2_000_000
    intake_max_rows: int = 5000
    intake_max_xlsx_expanded_bytes: int = 20_000_000   # what an XLSX may expand to

    # Keyring for complainant details (app/core/crypto.py): a JSON file mounted as a secret.
    complainant_keys_file: str | None = None

    # Deadlock and bottleneck detection (app/modules/findings/service.py).
    detect_batch: int = 500           # new findings or overlap links per transaction (the audit lock is held to commit)
    stalled_transfer_days: int = 7     # a transfer nobody acknowledged for this long is a finding
    bottleneck_min_open: int = 3       # queues smaller than this are never a bottleneck
    bottleneck_share: float = 0.6      # more than this share overdue (or, for a bureau, older than its median)
    spike_min_count: int = 5           # a state and category with fewer complaints in 30 days is never a spike
    spike_ratio: float = 3.0           # ...and it must be at least this many times its 90-day baseline (per 30 days)

    # AI layer (app/ai, docs/AI-PIPELINE.md). Models come only from the read-only models folder; never downloaded.
    ai_models_dir: str = "/models"                 # holds manifest.json and the model files
    ai_idle_unload_seconds: int = 300              # a loaded model is unloaded after this long unused
    ai_timeout_seconds: float = 30.0               # a provider slower than this falls through to the next
    ai_circuit_failures: int = 3                   # failures in a row that open a provider's circuit...
    ai_circuit_cooldown_seconds: int = 60          # ...for this long; then one trial call is let through
    ai_default_min_confidence: float = 0.5         # when app_settings has no ai.<task>.min_confidence
    ai_routes: dict[str, list[str]] = {"stub.echo": ["stub-model", "stub-rules"]}   # task: providers in order
    ai_endpoints: dict[str, str] = {}              # provider: URL of a model server inside the `ai` zone
    # The libraries' own offline switches; production refuses to start unless both are "1".
    hf_hub_offline: str | None = Field(None, validation_alias=AliasChoices("HF_HUB_OFFLINE", "hf_hub_offline"))
    transformers_offline: str | None = Field(
        None, validation_alias=AliasChoices("TRANSFORMERS_OFFLINE", "transformers_offline"))

    @model_validator(mode="after")
    def _production_ready(self) -> "Settings":
        self._inline_passwords = {name for name, url in (("SETHU_DATABASE_URL", self.database_url),
                                                        ("SETHU_REDIS_URL", self.redis_url)) if urlsplit(url).password}
        if self.smtp_password:
            self._inline_passwords.add("SETHU_SMTP_PASSWORD")
        if self.database_password_file:
            self.database_url = with_password(self.database_url, read_secret("SETHU_DATABASE_PASSWORD_FILE",
                                                                             self.database_password_file))
        if self.redis_password_file:
            self.redis_url = with_password(self.redis_url, read_secret("SETHU_REDIS_PASSWORD_FILE",
                                                                       self.redis_password_file))
        if self.smtp_password_file:
            self.smtp_password = read_secret("SETHU_SMTP_PASSWORD_FILE", self.smtp_password_file) or None
        if self.keycloak_events_secret:
            self._inline_passwords.add("SETHU_KEYCLOAK_EVENTS_SECRET")
        if self.keycloak_events_secret_file:
            self.keycloak_events_secret = read_secret("SETHU_KEYCLOAK_EVENTS_SECRET_FILE",
                                                      self.keycloak_events_secret_file) or None
        if self.environment == "prod" and (problems := production_problems(self)):
            raise ValueError("refusing to start in production: " + "; ".join(problems))
        return self


def read_secret(variable: str, path: str) -> str:
    """The content of a secret file, without surrounding whitespace. The error names the variable only."""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        raise ValueError(f"{variable}: the secret file cannot be read") from None


def with_password(url: str, password: str) -> str:
    """The URL with this password, URL-encoded (secret files may hold any character)."""
    parts = urlsplit(url)
    user = parts.username or ""
    host = parts.hostname or ""
    netloc = f"{user}:{quote(password, safe='')}@{host}" + (f":{parts.port}" if parts.port else "")
    return urlunsplit(parts._replace(netloc=netloc))


def remote_url(url: str) -> bool:
    """True unless the URL names a service inside this deployment: a one-word Compose service name, localhost, or a
    loopback or private address. Anything with a dotted name or a public address could leave AICTE."""
    host = urlsplit(url).hostname or ""
    if not host:
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "." in host          # "localhost" and Compose service names have no dot
    return not (address.is_loopback or address.is_private) or address.is_link_local


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
        if why := _weak(unquote(urlsplit(url).password or "")):
            problems.append(f"the password in {name} is {why}")
    for name in sorted(s._inline_passwords):  # production passwords live in secret files, not the environment
        problems.append(f"{name} carries a password: use the matching *_PASSWORD_FILE secret instead")
    if not s.database_password_file:
        problems.append("SETHU_DATABASE_PASSWORD_FILE is not set")
    if not s.redis_password_file:
        problems.append("SETHU_REDIS_PASSWORD_FILE is not set")
    if urlsplit(s.oidc_issuer).scheme != "https":
        problems.append("SETHU_OIDC_ISSUER is not https")
    if s.smtp_host in ("mailpit", "localhost", "127.0.0.1", ""):
        problems.append("SETHU_SMTP_HOST is the dev mail catcher or empty")
    if s.alert_from.lower().endswith(("@sethu.test", ".test")):
        problems.append("SETHU_ALERT_FROM uses the test domain")
    if s.smtp_security == "none":
        problems.append("SETHU_SMTP_SECURITY is none: mail must use starttls or tls")
    if s.smtp_username and not s.smtp_password:
        problems.append("SETHU_SMTP_USERNAME is set but SETHU_SMTP_PASSWORD is missing")
    if s.smtp_ca_file and not Path(s.smtp_ca_file).is_file():
        problems.append("SETHU_SMTP_CA_FILE does not exist")
    for flag, value in (("HF_HUB_OFFLINE", s.hf_hub_offline), ("TRANSFORMERS_OFFLINE", s.transformers_offline)):
        if value != "1":
            problems.append(f"{flag} is not 1: AI libraries must not reach a model hub")
    for provider in sorted(p for p, url in s.ai_endpoints.items() if remote_url(url)):
        problems.append(f"SETHU_AI_ENDPOINTS: provider {provider} points outside the deployment")
    if not s.complainant_keys_file:
        problems.append("SETHU_COMPLAINANT_KEYS_FILE is not set")
    else:
        try:
            load_keyring(s.complainant_keys_file)
        except KeyringError as e:
            problems.append(f"SETHU_COMPLAINANT_KEYS_FILE: {e}")
    return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
