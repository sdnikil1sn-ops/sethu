-- Give a database role the password now in its secret file (docs/RUNBOOK.md section 7, "Secrets").
-- Piped into psql inside the postgres container, which has the file mounted:
--   ... exec -T postgres psql -U postgres -d sethu -v ON_ERROR_STOP=1 \
--         -v role=sethu_app -v file=/run/secrets/sethu_app_password < infra/postgres/rotate_role.sql
-- The password is read inside the container: it is never on a command line or in a log.
\set pw `tr -d '\r\n' < :file`
ALTER ROLE :"role" PASSWORD :'pw';
\unset pw
