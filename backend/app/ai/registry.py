"""The model registry: `models/manifest.json` lists every model the AI layer may load, with its SHA-256.

Models sit in a read-only folder mounted into the ai-worker (`SETHU_AI_MODELS_DIR`). They are put there on a
connected machine with `scripts/fetch_models.py`, never downloaded at run time. A model whose files do not match the
manifest's checksum is refused: `verify()` raises, so it can never be loaded.

manifest.json:  {"models": [{"name", "version", "task", "license", "sha256", "path", "approx_memory_mb"}, ...]}
`path` is relative to the models folder; a file is hashed as is, a folder as the SHA-256 of its files' relative
paths and SHA-256s, sorted (`digest()`; scripts/fetch_models.py writes the same value).
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

FIELDS = ("name", "version", "task", "license", "sha256", "path", "approx_memory_mb")


class ModelIntegrityError(Exception):
    """A model that must not be loaded. The message names the model, never file contents."""


@dataclass(frozen=True)
class ModelEntry:
    name: str
    version: str
    task: str
    license: str
    sha256: str
    path: str
    approx_memory_mb: int


def load_manifest(models_dir: str | Path) -> dict[str, ModelEntry]:
    """Every model in the manifest, by name. An unreadable manifest or an entry missing a field is refused."""
    file = Path(models_dir) / "manifest.json"
    try:
        entries = json.loads(file.read_text(encoding="utf-8"))["models"]
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise ModelIntegrityError(f"the model manifest cannot be read ({type(e).__name__})") from None
    models = {}
    for raw in entries:
        if not isinstance(raw, dict) or set(FIELDS) - set(raw):
            raise ModelIntegrityError("a manifest entry is missing one of: " + ", ".join(FIELDS))
        entry = ModelEntry(**{f: raw[f] for f in FIELDS})
        models[entry.name] = entry
    return models


def digest(path: Path) -> str:
    """SHA-256 of a file, or of a folder: each file's relative path and SHA-256, sorted, one per line."""
    if path.is_file():
        return _file_sha256(path)
    lines = sorted(f"{f.relative_to(path).as_posix()} {_file_sha256(f)}" for f in path.rglob("*") if f.is_file())
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify(entry: ModelEntry, models_dir: str | Path) -> Path:
    """The model's path if its files match the manifest; ModelIntegrityError otherwise."""
    root = Path(models_dir).resolve()
    given = root / entry.path
    path = given.resolve()
    if root not in path.parents or given.is_symlink():
        raise ModelIntegrityError(f"model {entry.name}: its path leaves the models folder")
    if not path.exists():
        raise ModelIntegrityError(f"model {entry.name}: not found in the models folder")
    if digest(path) != entry.sha256.lower():
        raise ModelIntegrityError(f"model {entry.name} {entry.version}: checksum does not match the manifest")
    return path


def check_all(models_dir: str | Path) -> dict[str, str]:
    """For the start-up check and the health screen: each model's name and "ok" or why it is refused."""
    try:
        models = load_manifest(models_dir)
    except ModelIntegrityError as e:
        return {"(manifest)": str(e)}
    result = {}
    for name, entry in models.items():
        try:
            verify(entry, models_dir)
            result[name] = "ok"
        except ModelIntegrityError as e:
            result[name] = str(e)
    return result
