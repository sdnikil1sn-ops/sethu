"""Put a model into models/ and record it in models/manifest.json. For a machine WITH internet access only.

SETHU never downloads a model at run time. On a connected machine (a developer laptop, a build host), fetch the
files here, check them, then copy the whole models/ folder to the AICTE host, where it is mounted read-only into the
ai-worker. This script refuses to run inside a container or with SETHU_ENVIRONMENT=prod.

    python scripts/fetch_models.py add NAME VERSION TASK LICENSE MEMORY_MB URL [URL ...] [--sha256 FILE_SHA256 ...]
    python scripts/fetch_models.py check            # recompute every model's checksum against the manifest

Each URL (https only) is saved under models/NAME/VERSION/. Give --sha256 for each file when the publisher lists
one (strongly advised): a file that does not match is deleted and nothing is recorded. The manifest gets the
folder's checksum, computed exactly as the ai-worker does (backend/app/ai/registry.py, digest()).
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
sys.path.insert(0, str(ROOT / "backend"))
from app.ai.registry import FIELDS, check_all, digest  # noqa: E402


def refuse_if_deployed() -> None:
    if Path("/.dockerenv").exists() or os.environ.get("SETHU_ENVIRONMENT") == "prod":
        raise SystemExit("refusing: fetch models on a connected build machine, never in a container or production")


def download(url: str, target: Path) -> str:
    if urlsplit(url).scheme != "https":
        raise SystemExit(f"refusing a non-https URL: {url}")
    h = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=60) as r, target.open("wb") as f:  # noqa: S310 - https only, checked
        for block in iter(lambda: r.read(1 << 20), b""):
            h.update(block)
            f.write(block)
    return h.hexdigest()


def add(args) -> None:
    folder = MODELS / args.name / args.version
    folder.mkdir(parents=True, exist_ok=True)
    expected = args.sha256 or []
    for i, url in enumerate(args.urls):
        target = folder / Path(urlsplit(url).path).name
        got = download(url, target)
        if i < len(expected) and got != expected[i].lower():
            target.unlink()
            raise SystemExit(f"{target.name}: SHA-256 does not match the publisher's; deleted, nothing recorded")
        print(f"{target.name}  {got}")
    manifest_file = MODELS / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else {"models": []}
    entry = {"name": args.name, "version": args.version, "task": args.task, "license": args.license,
             "sha256": digest(folder), "path": f"{args.name}/{args.version}", "approx_memory_mb": args.memory_mb}
    assert set(entry) == set(FIELDS)  # noqa: S101 - the manifest's shape, checked here as the registry checks it
    manifest["models"] = [m for m in manifest["models"] if m["name"] != args.name] + [entry]
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"recorded {args.name} {args.version} in models/manifest.json; copy models/ to the host")


def main() -> None:
    refuse_if_deployed()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("add")
    for name in ("name", "version", "task", "license"):
        a.add_argument(name)
    a.add_argument("memory_mb", type=int)
    a.add_argument("urls", nargs="+")
    a.add_argument("--sha256", nargs="*")
    sub.add_parser("check")
    args = parser.parse_args()
    if args.command == "add":
        add(args)
    else:
        results = check_all(MODELS)
        for name, verdict in results.items():
            print(f"{name}: {verdict}")
        sys.exit(0 if all(v == "ok" for v in results.values()) else 1)


if __name__ == "__main__":
    main()
