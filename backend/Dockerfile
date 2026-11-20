# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
WORKDIR /src
ENV PIP_DEFAULT_TIMEOUT=60 PIP_RETRIES=10
COPY pyproject.toml ./
# Dependencies first, against an empty package: this layer is rebuilt only when pyproject.toml
# changes, so a code change needs no network (and the demo machine can rebuild offline).
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install "setuptools>=69" \
 && mkdir app && touch app/__init__.py \
 && pip install --prefix=/install . \
 && rm -rf app build *.egg-info
COPY app ./app
# The real code, over the placeholder. No downloads: dependencies and setuptools are already here.
RUN pip install --no-cache-dir --prefix=/install --no-deps --no-build-isolation --force-reinstall .

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --system --uid 10001 --no-create-home sethu
COPY --from=build /install /usr/local
WORKDIR /app
COPY alembic.ini ./
COPY alembic ./alembic
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD \
  python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
