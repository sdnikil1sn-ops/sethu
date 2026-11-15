"""Create .env from .env.example, replacing every CHANGE_ME with a random secret.

Usage:  python scripts/init_env.py          (refuses to overwrite an existing .env)
"""
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE, TARGET = ROOT / ".env.example", ROOT / ".env"


def main() -> int:
    if TARGET.exists():
        print(".env already exists; delete it first if you really want new secrets.")
        return 1
    lines = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if line.endswith("=CHANGE_ME"):
            # URL-safe: these values are embedded in connection URLs.
            line = line.replace("CHANGE_ME", secrets.token_urlsafe(32))
        lines.append(line)
    TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {TARGET} with generated secrets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
