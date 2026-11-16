# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
WORKDIR /src
COPY pyproject.toml ./
COPY app ./app
RUN --mount=type=cache,target=/root/.cache/pip \
    PIP_DEFAULT_TIMEOUT=60 PIP_RETRIES=10 pip install --prefix=/install .

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
