"""multilingual-e5-small: sentence vectors for complaint matching, institution names and classification.

Registry name "multilingual-e5-small" (MIT licence, intfloat). It runs on ONNX Runtime with the `tokenizers` library,
both already in the image: no new dependency, no download, no telemetry. The model folder holds the official ONNX
export and its tokenizer.json (scripts/fetch_models.py small).

E5 needs a prefix: "passage: " for a document (complaint text) and "query: " for a short text compared with others
of its kind (an institution name; E5's advice for symmetric tasks). Vectors are mean-pooled over the tokens and
L2-normalised, so a dot product is the cosine similarity. 384 dimensions; text past 512 tokens is cut.
"""
import math
from pathlib import Path

from app.ai.memory import manager
from app.ai.providers import Provider, Result

MODEL = "multilingual-e5-small"
DIM = 384
MAX_TOKENS = 512
BATCH = 16
PREFIX = {"query": "query: ", "passage": "passage: "}


class Encoder:
    """The loaded model: one ONNX Runtime session and the tokenizer. Built by the memory manager, one at a time."""

    def __init__(self, folder: str | Path):
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        ort.disable_telemetry_events()          # no telemetry, ever (the ai zone has no route out anyway)
        ort.set_default_logger_severity(3)
        folder = Path(folder)
        onnx = sorted(folder.glob("*.onnx"))
        if len(onnx) != 1 or not (folder / "tokenizer.json").is_file():
            raise FileNotFoundError("the model folder must hold exactly one .onnx file and tokenizer.json")
        opts = ort.SessionOptions()
        opts.enable_cpu_mem_arena = False      # memory goes back between batches instead of staying at the peak
        self.np = np
        self.session = ort.InferenceSession(str(onnx[0]), opts, providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.session.get_inputs()}
        self.tokenizer = Tokenizer.from_file(str(folder / "tokenizer.json"))
        self.tokenizer.enable_truncation(MAX_TOKENS)
        self.tokenizer.enable_padding(pad_id=self.tokenizer.token_to_id("<pad>"), pad_token="<pad>")  # noqa: S106

    def embed(self, texts: list[str], kind: str):
        """Unit vectors, one row per text (numpy float32, shape (n, 384))."""
        np = self.np
        rows = []
        for i in range(0, len(texts), BATCH):
            enc = self.tokenizer.encode_batch([PREFIX[kind] + " ".join(t.split()) for t in texts[i:i + BATCH]])
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feed = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self.inputs:
                feed["token_type_ids"] = np.zeros_like(ids)
            hidden = self.session.run(None, feed)[0]
            m = mask[..., None].astype(np.float32)
            v = (hidden * m).sum(axis=1) / np.maximum(m.sum(axis=1), 1.0)
            rows.append(v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12))
        return np.vstack(rows).astype(np.float32) if rows else np.zeros((0, DIM), dtype=np.float32)


def installed() -> bool:
    """The libraries import and the model is in the manifest (its checksum is checked when it loads)."""
    try:
        import onnxruntime  # noqa: F401
        import tokenizers  # noqa: F401
    except ImportError:
        return False
    from app.ai import registry
    try:
        return MODEL in registry.load_manifest(manager().models_dir)
    except registry.ModelIntegrityError:
        return False


class E5Embed(Provider):
    """Task "embed.text": {"texts": [...], "kind": "passage" | "query"} -> {"vectors", "model", "model_version"}.
    Unhealthy until the model is installed; with no vector the tasks that need one use their fallback."""
    name = "e5"
    model = MODEL

    def health(self) -> bool:
        return installed()

    def run(self, payload: dict) -> Result:
        encoder, entry = manager().acquire(MODEL, Encoder)
        vectors = encoder.embed(list(payload["texts"]), payload.get("kind", "passage"))
        return Result({"vectors": vectors.tolist(), "model": MODEL, "model_version": entry.version}, 1.0)

    def validate(self, output: dict) -> bool:
        vectors = output.get("vectors")
        return isinstance(vectors, list) and all(
            len(v) == DIM and all(math.isfinite(x) for x in v) for v in vectors) and bool(output.get("model_version"))
