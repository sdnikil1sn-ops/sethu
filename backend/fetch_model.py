"""Fetch the embedding model named in models.lock.json at image build time, and verify it. Standard library only.

    python fetch_model.py models.lock.json <cache dir> <output dir>

Each file comes from the pinned revision, is retried on a poor network (with a resumable download into the
cache dir, which a Docker cache mount keeps between builds), and must match its SHA-256 or the build fails.
The output dir is laid out as the Hugging Face cache that fastembed reads offline (HF_HUB_OFFLINE=1):
models--<org>--<name>/snapshots/<revision>/<files> and refs/main. Nothing is fetched at run time.
"""
import hashlib
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://huggingface.co/{repo}/resolve/{revision}/{name}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, attempts: int = 8) -> None:
    for n in range(1, attempts + 1):
        have = dest.stat().st_size if dest.exists() else 0
        request = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})  # noqa: S310 - https only
        try:
            with urllib.request.urlopen(request, timeout=60) as r:  # noqa: S310 - fixed https host
                with open(dest, "ab" if have and r.status == 206 else "wb") as out:
                    shutil.copyfileobj(r, out, 1 << 20)
            return
        except urllib.error.HTTPError as e:
            if e.code == 416:  # what is cached is already longer than the file: start again
                dest.unlink()
                continue
            print(f"  attempt {n} failed (HTTP {e.code}); retrying", flush=True)
            time.sleep(min(60, 2 ** n))
        except Exception as e:  # noqa: BLE001 - any network failure is retried
            print(f"  attempt {n} failed ({type(e).__name__}); retrying", flush=True)
            time.sleep(min(60, 2 ** n))
    raise SystemExit(f"could not download {url}")


def main(lock_path: str, cache: str, out: str) -> None:
    lock = json.loads(Path(lock_path).read_text())
    cache_dir, out_dir = Path(cache), Path(out)
    cache_dir.mkdir(parents=True, exist_ok=True)
    snapshot = out_dir / f"models--{lock['repo'].replace('/', '--')}" / "snapshots" / lock["revision"]
    snapshot.mkdir(parents=True, exist_ok=True)
    for name, digest in lock["files"].items():
        cached = cache_dir / f"{digest}"
        if not (cached.exists() and sha256(cached) == digest):
            print(f"fetching {name}", flush=True)
            fetch(BASE.format(repo=lock["repo"], revision=lock["revision"], name=name), cached)
        got = sha256(cached)
        if got != digest:
            cached.unlink()
            raise SystemExit(f"{name}: sha256 {got} does not match the lock file ({digest})")
        shutil.copyfile(cached, snapshot / name)
    refs = snapshot.parent.parent / "refs"
    refs.mkdir(exist_ok=True)
    (refs / "main").write_text(lock["revision"])
    print(f"model {lock['model']} at {lock['revision'][:12]} verified ({len(lock['files'])} files)")


if __name__ == "__main__":
    main(*sys.argv[1:4])
