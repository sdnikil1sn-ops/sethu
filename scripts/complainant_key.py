"""Manage the keyring for complainant details (docs/RUNBOOK.md, "Complainant details: keys").

    python scripts/complainant_key.py new <file>           create a keyring with one new key (refuses to overwrite)
    python scripts/complainant_key.py add <file>           add a new key and make it the active one
    python scripts/complainant_key.py remove <file> <id>   drop an old key (never the active one)
    python scripts/complainant_key.py show <file>          key ids and which is active (never the keys)

Standard library only. Keys are 32 random bytes from `secrets`. The file holds keys in the clear: keep
it outside the repository (secrets/ is git-ignored), in a folder only its owner can open, and back it up
apart from the database backups (a backup and its key together are the data).
"""
import base64
import json
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path


def _write(path: Path, ring: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ring, indent=2) + "\n", encoding="utf-8")
    try:  # the folder is 0700 (scripts/init_secrets.py); the file 0644 so the container's user can read it
        path.chmod(0o644)
    except OSError:  # Windows
        pass


def _new_key(ring: dict) -> str:
    key_id = f"k{datetime.now(UTC):%Y%m%d}"
    n = 1
    while f"{key_id}-{n}" in ring["keys"]:
        n += 1
    key_id = f"{key_id}-{n}"
    ring["keys"][key_id] = base64.b64encode(secrets.token_bytes(32)).decode()
    ring["active"] = key_id
    return key_id


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("new", "add", "remove", "show"):
        print(__doc__)
        return 2
    command, path = argv[0], Path(argv[1])
    if command == "new":
        if path.exists():
            print(f"{path} exists; use `add` to rotate. Never overwrite a keyring: data encrypted with it is lost.")
            return 1
        ring = {"active": "", "keys": {}}
        print(f"created {path}, active key {_new_key(ring)}")
        _write(path, ring)
        return 0
    ring = json.loads(path.read_text(encoding="utf-8"))
    if command == "show":
        print(json.dumps({"active": ring["active"], "keys": sorted(ring["keys"])}, indent=2))
        return 0
    if command == "add":
        key_id = _new_key(ring)
        _write(path, ring)
        print(f"added {key_id}, now active. Restart the backend and worker, then re-encrypt (RUNBOOK).")
        return 0
    key_id = argv[2] if len(argv) > 2 else ""
    if key_id == ring["active"] or key_id not in ring["keys"]:
        print("refusing: that is the active key, or not in the keyring")
        return 1
    del ring["keys"][key_id]
    _write(path, ring)
    print(f"removed {key_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
