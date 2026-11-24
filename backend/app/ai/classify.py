"""Category classification (task "classify.category"): E5 vector + logistic regression -> keyword and glossary-tag
rules -> an officer picks.

The classifier is plain multinomial logistic regression written with numpy (no scikit-learn: it would add about
100 MB to the image for one small model). Its weights are an artifact of a fixed JSON shape, stored in
sethu.classifier_versions with the SHA-256 of its canonical form. `load` refuses anything else: another format,
bytes (a pickle, for example), a wrong checksum, wrong shapes or a non-finite number. Probabilities are
calibrated with one temperature fitted on the held-out set.
"""
import hashlib
import json
import math

from app.ai.providers import NotApplicable, Provider, Result

FORMAT = "sethu-logreg-json-1"
DIM = 384

# The rules: English keywords (in the text or its translation) and the A2 glossary's English tags, per category.
RULES: dict[str, dict[str, list[str]]] = {
    "Faculty shortage": {"words": ["faculty", "teacher", "teachers", "lecturer", "lecturers", "professor",
                                   "sanctioned post", "sanctioned posts", "vacant", "guest lecturer"],
                         "tags": ["faculty", "faculty shortage"]},
    "Fee refund": {"words": ["refund", "refunded", "withdrew admission", "withdrew", "excess fee", "extra fee",
                             "receipt", "caution deposit"], "tags": ["fee refund"]},
    "Infrastructure": {"words": ["laboratory", "lab", "machines", "computers", "practicals", "drinking water",
                                 "toilet", "toilets", "building", "infrastructure", "water supply"],
                       "tags": ["infrastructure"]},
    "Ragging": {"words": ["ragging", "ragged", "anti-ragging", "seniors", "harassment", "humiliating"],
                "tags": ["ragging", "harassment"]},
    "Admission irregularity": {"words": ["management quota", "merit list", "capitation", "donation", "seats",
                                         "admission irregularity", "notified fee"],
                               "tags": ["admission irregularity", "admission"]},
    "Scholarship delay": {"words": ["scholarship", "scholarships", "post-matric", "stipend"],
                          "tags": ["scholarship", "scholarship not received"]},
    "Examination": {"words": ["result", "results", "examination", "exam", "revaluation", "question paper",
                              "invigilator", "marks"],
                    "tags": ["examination", "examination result", "revaluation"]},
    "Placement misrepresentation": {"words": ["placement", "placed", "job offer", "offer", "brochure",
                                              "brochures", "package"], "tags": ["placement"]},
}
TAG_WEIGHT = 2


class ArtifactError(ValueError):
    pass


def checksum(artifact: dict) -> str:
    return hashlib.sha256(json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(artifact, sha256: str) -> dict:
    """The artifact, checked: a dict of exactly this shape whose canonical JSON hashes to `sha256`."""
    if not isinstance(artifact, dict):
        raise ArtifactError("a classifier artifact must be a JSON object (never bytes or a pickle)")
    if artifact.get("format") != FORMAT:
        raise ArtifactError(f"unknown classifier format {str(artifact.get('format'))[:40]!r}")
    if checksum(artifact) != sha256:
        raise ArtifactError("classifier artifact does not match its checksum")
    keys = {"format", "classes", "mean", "coef", "intercept", "temperature", "embedding_model", "embedding_version"}
    if set(artifact) != keys:
        raise ArtifactError("classifier artifact has missing or extra fields")
    classes, coef = artifact["classes"], artifact["coef"]
    numbers = [*artifact["mean"], *artifact["intercept"], artifact["temperature"], *(x for row in coef for x in row)]
    if not (isinstance(classes, list) and len(classes) >= 2 and all(isinstance(c, str) for c in classes)
            and len(artifact["mean"]) == DIM and len(coef) == len(classes) and all(len(r) == DIM for r in coef)
            and len(artifact["intercept"]) == len(classes)
            and all(isinstance(x, int | float) and math.isfinite(x) for x in numbers)
            and artifact["temperature"] > 0):
        raise ArtifactError("classifier artifact has the wrong shape or a non-finite number")
    return artifact


def predict(artifact: dict, vectors):
    """Calibrated class probabilities, one row per vector (numpy)."""
    import numpy as np
    x = np.asarray(vectors, dtype=np.float64) - np.asarray(artifact["mean"])
    logits = (x @ np.asarray(artifact["coef"]).T + np.asarray(artifact["intercept"])) / artifact["temperature"]
    logits -= logits.max(axis=1, keepdims=True)
    p = np.exp(logits)
    return p / p.sum(axis=1, keepdims=True)


def train(vectors, labels: list[str], holdout_vectors, holdout_labels: list[str], embedding_model: str,
          embedding_version: str, l2: float = 1e-3, steps: int = 1500, rate: float = 2.0) -> tuple[dict, dict]:
    """Fit on (vectors, labels), calibrate a temperature on the held-out set, return (artifact, metrics)."""
    import numpy as np
    classes = sorted(set(labels))
    x = np.asarray(vectors, dtype=np.float64)
    mean = x.mean(axis=0)
    x = x - mean
    y = np.zeros((len(labels), len(classes)))
    y[np.arange(len(labels)), [classes.index(label) for label in labels]] = 1
    w, b = np.zeros((len(classes), x.shape[1])), np.zeros(len(classes))
    for _ in range(steps):                     # full-batch gradient descent on the softmax loss with L2
        z = x @ w.T + b
        z -= z.max(axis=1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(axis=1, keepdims=True)
        g = (p - y) / len(labels)
        w -= rate * (g.T @ x + l2 * w)
        b -= rate * g.sum(axis=0)
    artifact = {"format": FORMAT, "classes": classes, "mean": [round(float(v), 7) for v in mean],
                "coef": [[round(float(v), 7) for v in row] for row in w], "intercept": [round(float(v), 7) for v in b],
                "temperature": 1.0, "embedding_model": embedding_model, "embedding_version": embedding_version}
    known = [i for i, label in enumerate(holdout_labels) if label in classes]
    if known:
        hv = np.asarray(holdout_vectors)[known]
        hy = np.array([classes.index(holdout_labels[i]) for i in known])

        def nll(t: float) -> float:
            p = predict(artifact | {"temperature": t}, hv)
            return float(-np.log(np.maximum(p[np.arange(len(hy)), hy], 1e-12)).mean())

        artifact["temperature"] = min((0.25 * k for k in range(1, 41)), key=nll)
    return artifact, evaluate(artifact, holdout_vectors, holdout_labels) | {"trained_on": len(labels)}


def evaluate(artifact: dict, vectors, labels: list[str]) -> dict:
    """Accuracy and mean top probability on a labelled set (a label the classifier does not know counts wrong)."""
    if not labels:
        return {"holdout_accuracy": None, "holdout_size": 0, "mean_confidence": None}
    p = predict(artifact, vectors)
    picked = [artifact["classes"][i] for i in p.argmax(axis=1)]
    return {"holdout_accuracy": round(sum(a == b for a, b in zip(picked, labels, strict=True)) / len(labels), 4),
            "holdout_size": len(labels), "mean_confidence": round(float(p.max(axis=1).mean()), 4)}


class CategoryModel(Provider):
    """payload {"vector", "artifact", "sha256", "version"}: the active classifier on the complaint's E5 vector."""
    name = "category-e5"
    model = "category-classifier"

    def run(self, payload: dict) -> Result:
        if payload.get("vector") is None or payload.get("artifact") is None:
            raise NotApplicable("no E5 vector for the complaint, or no active classifier")
        artifact = load(payload["artifact"], payload["sha256"])
        p = predict(artifact, [payload["vector"]])[0]
        order = sorted(range(len(p)), key=lambda i: -p[i])[:3]
        top = [{"category": artifact["classes"][i], "score": round(float(p[i]), 5)} for i in order]
        return Result({"category": top[0]["category"], "top": top, "method": "model",
                       "model_version": f"classifier-v{payload['version']}"}, top[0]["score"])

    def validate(self, output: dict) -> bool:
        return isinstance(output.get("category"), str) and bool(output.get("top"))


def rule_scores(text: str, tags: list[str]) -> dict[str, int]:
    words = " " + " ".join("".join(ch if ch.isalnum() or ch == "-" else " " for ch in text.lower()).split()) + " "
    tagset = {t.lower() for t in tags}
    return {category: sum(words.count(f" {w} ") for w in rule["words"]) + TAG_WEIGHT * len(tagset & set(rule["tags"]))
            for category, rule in RULES.items()}


class CategoryRules(Provider):
    """payload {"text" (original plus English translation), "tags" (glossary English tags)}. Confidence
    top / (top + second + 1): one keyword alone gives 0.5, so it needs two clear hits to pass 0.6."""
    name = "category-rules"

    def run(self, payload: dict) -> Result:
        scores = rule_scores(payload.get("text") or "", payload.get("tags") or [])
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        if ranked[0][1] == 0:
            raise NotApplicable("no keyword or glossary tag of any category")
        total = ranked[0][1] + ranked[1][1] + 1
        top = [{"category": c, "score": round(n / total, 5)} for c, n in ranked[:3] if n]
        return Result({"category": ranked[0][0], "top": top, "method": "rules"}, round(ranked[0][1] / total, 5))

    def validate(self, output: dict) -> bool:
        return output.get("category") in RULES
