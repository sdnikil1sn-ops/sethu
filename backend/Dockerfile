# syntax=docker/dockerfile:1
# Base images are pinned by digest (docs/RUNBOOK.md, "Pinned dependencies": how to update).
ARG PYTHON=python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

FROM ${PYTHON} AS build
WORKDIR /src
ENV PIP_DEFAULT_TIMEOUT=60 PIP_RETRIES=10
COPY requirements.lock requirements-build.lock ./
# Every dependency comes from the lock file, each file checked against its SHA-256 (--require-hashes). This
# layer is rebuilt only when a lock file changes, so a code change needs no network. pip does not retry a
# download that breaks mid-stream (a poor network), so the install is retried whole; the cache mount keeps
# what already arrived, so each try gets further.
RUN --mount=type=cache,target=/root/.cache/pip \
    for try in 1 2 3 4 5 6; do \
      pip install --require-hashes -r requirements-build.lock \
      && pip install --require-hashes --prefix=/install -r requirements.lock && ok=1 && break; \
      echo "pip install failed (try $try), retrying"; sleep $((try * 10)); \
    done && [ "$ok" = 1 ]
COPY pyproject.toml ./
COPY app ./app
# The application itself; no downloads (--no-deps, setuptools already here).
RUN pip install --no-cache-dir --prefix=/install --no-deps --no-build-isolation .

# The embedding model, pinned and hash-checked (models.lock.json); fetched once, kept in a cache mount, and
# rebuilt only when the lock file changes. Run time never downloads it.
FROM ${PYTHON} AS model
WORKDIR /m
COPY models.lock.json fetch_model.py ./
RUN --mount=type=cache,target=/root/.cache/sethu-models \
    python fetch_model.py models.lock.json /root/.cache/sethu-models /models

FROM ${PYTHON} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 SETHU_EMBEDDING_CACHE_DIR=/opt/sethu/models
# Debian security fixes released after the base image was built (the base digest stays pinned).
RUN for try in 1 2 3 4 5; do \
      apt-get update && apt-get upgrade -y --no-install-recommends && ok=1 && break; sleep $((try * 5)); \
    done && [ "$ok" = 1 ] && rm -rf /var/lib/apt/lists/* \
 && useradd --system --uid 10001 --no-create-home sethu
COPY --from=build /install /usr/local
COPY --from=model /models /opt/sethu/models
WORKDIR /app
COPY alembic.ini ./
COPY alembic ./alembic
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD \
  python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]

# The ai-worker image (docs/AI-PIPELINE.md): the runtime plus the AI engines, pinned with hashes
# (requirements-ai.lock: RapidOCR on ONNX Runtime, CTranslate2, SentencePiece, pypdf, pypdfium2, fastText) and the
# Tesseract program. No model is in the image: models come from the read-only, checksum-verified models folder.
FROM runtime AS ai
USER root
COPY requirements-ai.lock ./
RUN for try in 1 2 3 4 5; do       apt-get update && apt-get install -y --no-install-recommends tesseract-ocr && ok=1 && break; sleep $((try * 5));     done && [ "$ok" = 1 ] && rm -rf /var/lib/apt/lists/*  && for try in 1 2 3 4 5 6; do       pip install --no-cache-dir --require-hashes --no-deps -r requirements-ai.lock && ok2=1 && break; sleep $((try * 10));     done && [ "$ok2" = 1 ] && rm requirements-ai.lock
USER 10001
CMD ["celery", "-A", "app.ai.tasks:celery", "worker", "-Q", "ai", "--pool", "solo", "-n", "ai@%h", "--loglevel", "INFO"]

# The default target stays the runtime (backend, worker, scheduler, migrate).
FROM runtime
