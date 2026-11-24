"""Put a model into models/ and record it in models/manifest.json. For a machine WITH internet access only.

SETHU never downloads a model at run time. On a connected machine (a developer laptop, a build host), fetch the
files here, check them, then copy the whole models/ folder to the AICTE host, where it is mounted read-only into the
ai-worker. This script refuses to run inside a container or with SETHU_ENVIRONMENT=prod.

    python scripts/fetch_models.py add NAME VERSION TASK LICENSE MEMORY_MB URL [URL ...] [--sha256 FILE_SHA256 ...]
    python scripts/fetch_models.py record NAME VERSION TASK LICENSE MEMORY_MB    # a folder unpacked by hand
    python scripts/fetch_models.py check            # recompute every model's checksum against the manifest
    python scripts/fetch_models.py small            # every small model SETHU uses, in one run (about 202 MB)

Each URL (https only) is saved under models/NAME/VERSION/. Give --sha256 for each file when the publisher lists
one (strongly advised): a file that does not match is deleted and nothing is recorded. The manifest gets the
folder's checksum, computed exactly as the ai-worker does (backend/app/ai/registry.py, digest()).
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MODELS = Path(os.environ.get("SETHU_MODELS_DIR") or ROOT / "models")   # the folder copied to the host
sys.path.insert(0, str(ROOT / "backend"))
from app.ai.registry import FIELDS, ModelIntegrityError, check_all, digest, load_manifest, verify  # noqa: E402

# `small`: the models the providers look up (app/ai/lid.py, ocr.py, e5.py), with each file's SHA-256 pinned (taken
# from copies downloaded and checked on 2026-11-23). Not here: IndicTrans2 (gated: docs/AI-PIPELINE.md) and a
# RapidOCR Kannada model (only PP-OCRv4 has one, and it was not shown to work; Tesseract reads Kannada).
# Tesseract needs no script or OSD data: SETHU runs it with --psm 6 and an explicit language.
RAPID = "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv5"
TESS = "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0"
E5 = "https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx"
DET = (f"{RAPID}/det/ch_PP-OCRv5_det_mobile.onnx", "4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae")
SMALL = [  # name, version, task, licence, approx memory MB, [(url, sha256), ...]
    ("lid-176", "1", "language.detect", "CC-BY-SA-3.0 (fastText)", 5,
     [("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz",
       "8f3472cfe8738a7b6099e8e999c3cbfae0dcd15696aac7d7738a8039db603e83")]),
    *[(f"rapidocr-{group}", "PP-OCRv5", "ocr.read", "Apache-2.0 (PaddleOCR models)", 200,
       [DET, (f"{RAPID}/rec/{group}_PP-OCRv5_rec_mobile.onnx", sha)]) for group, sha in (
        ("en", "c3461add59bb4323ecba96a492ab75e06dda42467c9e3d0c18db5d1d21924be8"),
        ("devanagari", "d6f0a906580e3fa6b324a318718f1f31f268b6ea8ef985f91c2012a37f52c91e"),   # Hindi, Marathi
        ("ta", "a42448808b7dea87597336f12438935f40353f1949e8360acd9e06b4da21bfe1"),
        ("te", "a3690451b50028a09a3316a1274f7c05728151ea3f8fd392696397a7fefcbd92"))],
    *[(f"tessdata-{lang}", "4.1.0-fast", "ocr.read", "Apache-2.0 (tessdata_fast)", 60,
       [(f"{TESS}/{lang}.traineddata", sha)]) for lang, sha in (
        ("eng", "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2"),
        ("hin", "4c73ffc59d497c186b19d1e90f5d721d678ea6b2e277b719bee4e2af12271825"),
        ("mar", "0ba3f2d116972e72fe9e176bc84c38e81dfb6670f4ed1f7f6c8e16a27da7cb61"),
        ("tam", "d02fbec24be4b07e32e80d0ccfc3b6b67a3c5d61c9d0a7c8532677990912c6ec"),
        ("tel", "d10691fddd5b67802e1c12800ebb321d3b8bcd8d24a2ac3ff206f93188c04ab5"),
        ("kan", "bd31e6b6ae93271e3bcf5383d306d8eefbb91542937cd6d735a5930c970e61d8"),
        ("ben", "31163084c279aaebd376216f0c3d5c17ad4b5fee8db49dae79c20000b5de5964"))],
    # A3: multilingual-e5-small (MIT), the publisher's int8 ONNX build and its tokenizer, at a pinned revision. The
    # hashes are the publisher's (Hugging Face LFS) and matched our download on 2026-11-24. 135 MB.
    ("multilingual-e5-small", "614241f-int8", "embed.text", "MIT (intfloat/multilingual-e5-small)", 550,
     [(f"{E5}/model_qint8_avx512_vnni.onnx", "dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88"),
      (f"{E5}/tokenizer.json", "0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39")]),
]


def refuse_if_deployed() -> None:
    if Path("/.dockerenv").exists() or os.environ.get("SETHU_ENVIRONMENT") == "prod":
        raise SystemExit("refusing: fetch models on a connected build machine, never in a container or production")


def download(url: str, target: Path, tries: int = 6) -> str:
    if urlsplit(url).scheme != "https":
        raise SystemExit(f"refusing a non-https URL: {url}")
    for attempt in range(1, tries + 1):
        try:
            h = hashlib.sha256()
            with urllib.request.urlopen(url, timeout=120) as r, target.open("wb") as f:  # noqa: S310 - https only
                for block in iter(lambda: r.read(1 << 20), b""):
                    h.update(block)
                    f.write(block)
            return h.hexdigest()
        except OSError as e:
            print(f"  {target.name}: attempt {attempt} failed ({type(e).__name__}), retrying")
            time.sleep(min(60, 5 * attempt))
    raise SystemExit(f"could not download {url}")


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
    record(args)


def record(args) -> None:
    """Record models/NAME/VERSION (downloaded here, or unpacked by hand) in the manifest with its checksum."""
    folder = MODELS / args.name / args.version
    if not folder.is_dir() or not any(folder.rglob("*")):
        raise SystemExit(f"{folder} is empty")
    manifest_file = MODELS / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else {"models": []}
    entry = {"name": args.name, "version": args.version, "task": args.task, "license": args.license,
             "sha256": digest(folder), "path": f"{args.name}/{args.version}", "approx_memory_mb": args.memory_mb}
    assert set(entry) == set(FIELDS)  # noqa: S101 - the manifest's shape, checked here as the registry checks it
    manifest["models"] = [m for m in manifest["models"] if m["name"] != args.name] + [entry]
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"recorded {args.name} {args.version} in models/manifest.json; copy models/ to the host")


def installed(name: str, version: str) -> bool:
    """In the manifest at this version, with files that still match its checksum."""
    try:
        entry = load_manifest(MODELS).get(name)
        return entry is not None and entry.version == version and verify(entry, MODELS) is not None
    except ModelIntegrityError:
        return False


def small() -> dict[str, list[str]]:
    """Install every model in SMALL that is not already installed and intact; one failure does not stop the rest."""
    done: dict[str, list[str]] = {"installed": [], "skipped": [], "failed": []}
    for name, version, task, licence, memory_mb, files in SMALL:
        if installed(name, version):
            done["skipped"].append(name)
            continue
        print(f"{name} {version}:")
        try:
            add(argparse.Namespace(name=name, version=version, task=task, license=licence, memory_mb=memory_mb,
                                   urls=[u for u, _ in files], sha256=[h for _, h in files]))
            done["installed"].append(name)
        except (SystemExit, OSError) as e:      # download gave up, or a checksum did not match
            print(f"  failed: {e}")
            done["failed"].append(name)
    for outcome, names in done.items():
        print(f"{outcome}: {len(names)}{' (' + ', '.join(names) + ')' if names else ''}")
    print("Then restart the ai-worker so it loads them:\n"
          "  docker compose restart ai-worker\n"
          "  (production: docker compose -f docker-compose.yml -f docker-compose.prod.yml restart ai-worker)")
    return done


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
    r = sub.add_parser("record", help="record a folder already in models/NAME/VERSION (an unpacked archive)")
    for name in ("name", "version", "task", "license"):
        r.add_argument(name)
    r.add_argument("memory_mb", type=int)
    sub.add_parser("check")
    sub.add_parser("small", help="install every small model SETHU uses (skips those already intact)")
    args = parser.parse_args()
    if args.command == "add":
        add(args)
    elif args.command == "record":
        record(args)
    elif args.command == "small":
        sys.exit(1 if small()["failed"] else 0)
    else:
        results = check_all(MODELS)
        for name, verdict in results.items():
            print(f"{name}: {verdict}")
        sys.exit(0 if all(v == "ok" for v in results.values()) else 1)


if __name__ == "__main__":
    main()
