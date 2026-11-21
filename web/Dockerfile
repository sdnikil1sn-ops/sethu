# syntax=docker/dockerfile:1
# Base images are pinned by digest (docs/RUNBOOK.md, "Pinned dependencies": how to update).
FROM node:22-alpine@sha256:1314fb30ec37592d5845e5a160d522c0e680972aa534549940b8d73bde88481a AS build
WORKDIR /src
COPY package.json package-lock.json ./
# npm ci installs exactly package-lock.json (integrity hashes checked). Retried whole on a poor network; the
# cache mount keeps what already arrived.
RUN --mount=type=cache,target=/root/.npm \
    for try in 1 2 3 4 5; do npm ci --no-audit --no-fund && ok=1 && break; \
      echo "npm ci failed (try $try), retrying"; sleep $((try * 10)); done && [ "$ok" = 1 ]
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.29-alpine@sha256:0c79d56aee561a1d81c63f00eee5fb5fe29279560cdc55e91425133104c7fbe6
# The base image's own packages, brought up to date (security fixes released after the image was built).
USER root
RUN for try in 1 2 3 4 5; do apk upgrade --no-cache && ok=1 && break; sleep $((try * 5)); done && [ "$ok" = 1 ]
USER 101
COPY --from=build /src/dist /usr/share/nginx/html
EXPOSE 8080
