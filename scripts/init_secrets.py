"""Create the production secret files (docs/RUNBOOK.md section 7, "Secrets").

    python scripts/init_secrets.py [directory]                 default: ./secrets (or SETHU_SECRETS_DIR)
    python scripts/init_secrets.py rotate <name> [directory]   a new random value, then the steps to apply it

Creates each missing file with a random value; never overwrites one (a database or key already uses
it). Standard library only. Compose mounts each file read-only into only the containers that need it
(/run/secrets/<name>). Values never go into .env, the image or an environment variable.

Permissions: the directory is 0700 (only its owner on the host can open it); the files are 0644 so
each container's own user (PostgreSQL, Redis, Keycloak, the backend) can read the ones mounted into it.
"""
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANDOM = (  # name -> what uses it
    ("postgres_superuser_password", "PostgreSQL bootstrap superuser"),
    ("sethu_owner_password", "migrations (sethu_owner)"),
    ("sethu_app_password", "backend and worker (sethu_app)"),
    ("sethu_auditor_password", "direct read access for auditors"),
    ("keycloak_db_password", "Keycloak's database"),
    ("keycloak_admin_password", "Keycloak bootstrap administrator"),
    ("redis_password", "Redis, backend and worker"),
    ("backup_key", "encrypts the database backups (keep a copy OFF this host)"),
)


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")
    try:
        path.chmod(0o644)
    except OSError:  # Windows
        pass


# Database roles whose password a secret file holds: rotated with infra/postgres/rotate_role.sql.
ROLES = {"sethu_owner_password": "sethu_owner", "sethu_app_password": "sethu_app",
         "sethu_auditor_password": "sethu_auditor", "keycloak_db_password": "keycloak",
         "postgres_superuser_password": "postgres"}
RESTART = {"sethu_owner_password": "migrate (next run)", "sethu_app_password": "backend worker",
           "sethu_auditor_password": "(nothing: direct auditor logins use it)", "keycloak_db_password": "keycloak",
           "postgres_superuser_password": "(nothing)", "redis_password": "redis backend worker"}
COMPOSE = "docker compose -f docker-compose.yml -f docker-compose.prod.yml"


def rotate(name: str, folder: Path) -> int:
    path = folder / name
    if name not in ROLES and name != "redis_password":
        print(f"{name}: rotate it as docs/RUNBOOK.md section 7 says (keys, SMTP and the Keycloak admin differ)")
        return 1
    if not path.exists():
        print(f"{path} does not exist")
        return 1
    _write(path, secrets.token_urlsafe(32) + "\n")  # same file, so the mounted copy changes at once
    print(f"new value written to {name} (not shown). Now:")
    if name in ROLES:
        print(f"  {COMPOSE} exec -T postgres psql -U postgres -d sethu -v ON_ERROR_STOP=1 "
              f"-v role={ROLES[name]} -v file=/run/secrets/{name} < infra/postgres/rotate_role.sql")
    else:
        _write(folder / "redis_conf", f"requirepass {path.read_text(encoding='utf-8').strip()}\n")
        print("  (redis_conf rewritten with it)")
    print(f"  {COMPOSE} restart {RESTART[name]}")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["rotate"]:
        if len(argv) < 2:
            print(__doc__)
            return 2
        default = Path(os.environ.get("SETHU_SECRETS_DIR", ROOT / "secrets"))
        return rotate(argv[1], Path(argv[2]) if len(argv) > 2 else default)
    folder = Path(argv[0]) if argv else Path(os.environ.get("SETHU_SECRETS_DIR", ROOT / "secrets"))
    folder.mkdir(parents=True, exist_ok=True)
    try:
        folder.chmod(0o700)
    except OSError:
        pass
    for name, use in RANDOM:
        path = folder / name
        if path.exists():
            print(f"kept     {name}")
            continue
        # URL-safe: some of these are embedded in connection URLs.
        _write(path, secrets.token_urlsafe(32) + "\n")
        print(f"created  {name}  ({use})")
    redis_conf = folder / "redis_conf"
    if not redis_conf.exists():  # Redis reads its password from a config file, made from redis_password
        _write(redis_conf, f"requirepass {(folder / 'redis_password').read_text(encoding='utf-8').strip()}\n")
        print("created  redis_conf  (Redis; same password as redis_password)")
    smtp = folder / "smtp_password"
    if not smtp.exists():
        _write(smtp, "")
        print("created  smtp_password  (EMPTY: put the relay's password in it if the relay needs a login)")
    keys = folder / "complainant_keys.json"
    if not keys.exists():
        sys.path.insert(0, str(ROOT / "scripts"))
        import complainant_key  # a sibling script

        complainant_key.main(["new", str(keys)])
    print(f"\nSecrets are in {folder}. Back them up apart from the database backups.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
