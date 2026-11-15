#!/bin/bash
# Runs once, as the Postgres superuser, when the data volume is first created.
# Creates least-privilege roles, the schema and the extensions. Tables are
# created later by Alembic running as sethu_owner.
set -euo pipefail

: "${SETHU_OWNER_PASSWORD:?}" "${SETHU_APP_PASSWORD:?}" "${SETHU_AUDITOR_PASSWORD:?}" "${KEYCLOAK_DB_PASSWORD:?}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v owner_pw="$SETHU_OWNER_PASSWORD" -v app_pw="$SETHU_APP_PASSWORD" \
     -v auditor_pw="$SETHU_AUDITOR_PASSWORD" -v kc_pw="$KEYCLOAK_DB_PASSWORD" <<'SQL'
CREATE ROLE sethu_owner   LOGIN PASSWORD :'owner_pw';
CREATE ROLE sethu_app     LOGIN PASSWORD :'app_pw';
CREATE ROLE sethu_auditor LOGIN PASSWORD :'auditor_pw';
CREATE ROLE keycloak      LOGIN PASSWORD :'kc_pw';

CREATE DATABASE keycloak OWNER keycloak;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO sethu_owner, sethu_app, sethu_auditor;

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA sethu AUTHORIZATION sethu_owner;

ALTER ROLE sethu_owner   SET search_path = sethu, public;
ALTER ROLE sethu_app     SET search_path = sethu, public;
ALTER ROLE sethu_auditor SET search_path = sethu, public;

-- The runtime role can never bypass Row-Level Security or create objects.
ALTER ROLE sethu_app NOBYPASSRLS NOCREATEDB NOCREATEROLE;
SQL
