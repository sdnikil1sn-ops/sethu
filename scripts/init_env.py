"""Create .env from .env.example, replacing every CHANGE_ME value with a random secret.

Usage:  python scripts/init_env.py          (refuses to overwrite an existing .env)
"""
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE, TARGET = ROOT / ".env.example", ROOT / ".env"


def ensure_keyring() -> None:
    """The dev keyring for complainant details (production: docs/RUNBOOK.md section 7)."""
    keys = ROOT / "secrets" / "complainant_keys.json"
    if not keys.exists():
        sys.path.insert(0, str(ROOT / "scripts"))
        import complainant_key  # a sibling script

        complainant_key.main(["new", str(keys)])


ADDED_LATER = ("KEYCLOAK_EVENTS_SECRET",)  # added to .env.example after first installs


def ensure_added_keys() -> None:
    """Append a generated value for any secret added since this .env was made; never replace one."""
    present = {line.split("=", 1)[0] for line in TARGET.read_text(encoding="utf-8").splitlines() if "=" in line}
    missing = [k for k in ADDED_LATER if k not in present]
    if missing:
        with open(TARGET, "a", encoding="utf-8", newline="\n") as f:
            f.writelines(f"{k}={secrets.token_urlsafe(32)}\n" for k in missing)
        print(f"Added to {TARGET}: {', '.join(missing)}")


def main() -> int:
    ensure_keyring()  # also on a machine that already has a .env
    if TARGET.exists():
        ensure_added_keys()
        print(".env already exists; delete it first if you really want new secrets.")
        return 1
    lines = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#") and line.endswith("CHANGE_ME"):  # may carry a prefix: Demo1-CHANGE_ME
            # URL-safe: these values are embedded in connection URLs.
            line = line.replace("CHANGE_ME", secrets.token_urlsafe(32))
        lines.append(line)
    TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {TARGET} with generated secrets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
