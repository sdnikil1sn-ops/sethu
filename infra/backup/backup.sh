#!/bin/bash
# Encrypted backups of the SETHU and Keycloak databases (docs/RUNBOOK.md section 5).
#
#   backup.sh loop             run once now, then every BACKUP_INTERVAL_HOURS; prune past BACKUP_KEEP_DAYS
#   backup.sh once             one backup now
#   backup.sh list             the backups in /backups
#   backup.sh restore <stamp>  restore both databases from <stamp> into EMPTY databases (a wiped volume)
#   backup.sh counts [db]      row counts per table, to compare before and after a restore
#
# Each database is dumped with pg_dump (custom format) and encrypted with gpg (AES-256, with an
# integrity check) under the passphrase in /run/secrets/backup_key. Nothing unencrypted is written.
# Runs in the postgres image (same pg_dump version as the server), as the postgres user.
set -euo pipefail

DIR=/backups
DATABASES="sethu keycloak"
export PGHOST=${PGHOST:-postgres} PGUSER=${PGUSER:-postgres}
if [ -n "${PGPASSWORD_FILE:-}" ]; then
  PGPASSWORD="$(tr -d '\r\n' < "$PGPASSWORD_FILE")"
  export PGPASSWORD
fi
KEY=${BACKUP_KEY_FILE:-/run/secrets/backup_key}
export GNUPGHOME=$(mktemp -d)   # gpg needs a writable home; nothing is kept in it
GPG=(gpg --batch --yes --quiet --pinentry-mode loopback --passphrase-file "$KEY")

log() { echo "$(date -u +%FT%TZ) backup: $*"; }

backup_once() {
  [ -s "$KEY" ] || { log "no backup key at $KEY"; return 1; }
  local stamp; stamp=$(date -u +%Y%m%dT%H%M%SZ)
  for db in $DATABASES; do
    local out="$DIR/$stamp-$db.dump.gpg"
    # Written under a temporary name and renamed only when complete: a half backup is never listed.
    # Explicit check: `set -e` does not apply inside a function called as `backup_once || ...`.
    if ! pg_dump --format=custom --dbname="$db" \
         | "${GPG[@]}" --symmetric --cipher-algo AES256 --output "$out.part"; then
      rm -f "$out.part"
      log "dump of $db failed"
      return 1
    fi
    mv "$out.part" "$out"
    log "wrote $(basename "$out") ($(stat -c %s "$out") bytes)"
  done
  touch "$DIR/last-success"
  record_run true
}

# For /metrics (sethu.job_runs): this service connects as the database superuser, so it may write the row.
record_run() {
  psql -d sethu -q -v ok="$1" -c "INSERT INTO sethu.job_runs (name, last_run_at, last_ok_at, last_ok, failures)
      VALUES ('backup', now(), CASE WHEN :'ok' THEN now() END, :'ok', CASE WHEN :'ok' THEN 0 ELSE 1 END)
      ON CONFLICT (name) DO UPDATE SET last_run_at = now(), last_ok = :'ok', runs = sethu.job_runs.runs + 1,
        last_ok_at = CASE WHEN :'ok' THEN now() ELSE sethu.job_runs.last_ok_at END,
        failures = sethu.job_runs.failures + CASE WHEN :'ok' THEN 0 ELSE 1 END"     || log "could not record the run for /metrics"
}

prune() {
  local days=${BACKUP_KEEP_DAYS:-14}
  find "$DIR" -maxdepth 1 -name '*.dump.gpg' -mtime +"$days" -print -delete | sed 's/^/pruned /'
  find "$DIR" -maxdepth 1 -name '*.part' -mmin +600 -delete   # left by a run that died
}

counts() {
  local db=${1:-sethu}
  psql -d "$db" -tA -F ' ' -c "SELECT format('SELECT %L, count(*) FROM %I.%I', schemaname || '.' || tablename, schemaname, tablename)
      FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY 1" \
    | sed 's/$/;/' | psql -d "$db" -tA -F ' '
}

restore() {
  local stamp=${1:?usage: backup.sh restore <stamp> (see backup.sh list)}
  for db in $DATABASES; do
    [ -f "$DIR/$stamp-$db.dump.gpg" ] || { log "missing $stamp-$db.dump.gpg"; exit 1; }
    # Only into an empty database: the audit ledger is append-only, so never merge into or drop a live one.
    local tables
    tables=$(psql -d "$db" -tAc "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')")
    [ "$tables" = 0 ] || { log "refusing: database $db already has $tables tables (restore into a wiped volume)"; exit 1; }
  done
  for db in $DATABASES; do
    # --clean --if-exists replaces the empty schema and extensions the init script created.
    "${GPG[@]}" --decrypt "$DIR/$stamp-$db.dump.gpg" \
      | pg_restore --dbname="$db" --clean --if-exists --single-transaction --exit-on-error
    log "restored $db from $stamp"
  done
  psql -d sethu -tAc "SELECT 'verify chain: ok=' || ok || ' checked=' || checked || coalesce(' broken at ' || broken_seq, '') FROM sethu.audit_verify()"
}

case "${1:-loop}" in
  once) backup_once ;;
  list) ls -l "$DIR" ;;
  counts) counts "${2:-sethu}" ;;
  restore) restore "${2:-}" ;;
  loop)
    hours=${BACKUP_INTERVAL_HOURS:-24}
    until pg_isready -q; do sleep 5; done
    while true; do
      backup_once || { log "FAILED (see above); next try in $hours h"; record_run false; }
      prune
      sleep $((hours * 3600))
    done ;;
  *) echo "unknown command $1"; exit 2 ;;
esac
