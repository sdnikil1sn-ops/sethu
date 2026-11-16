#!/bin/bash
# Creates or resets the demo logins in the sethu realm (dev and demo only: the
# Compose service that runs this exists only under the `dev` profile).
# Safe to run again: existing demo users are overwritten, other users are untouched.
set -euo pipefail

: "${DEMO_USER_PASSWORD:?add DEMO_USER_PASSWORD to .env (see .env.example)}"
: "${KEYCLOAK_ADMIN_USER:?}" "${KEYCLOAK_ADMIN_PASSWORD:?}"

kcadm() { /opt/keycloak/bin/kcadm.sh "$@" --config /tmp/kcadm.config; }
login() {
  kcadm config credentials --server http://keycloak:8080/auth --realm master         --user "$KEYCLOAK_ADMIN_USER" --password "$KEYCLOAK_ADMIN_PASSWORD"
}

for ((try = 1; try <= 60; try++)); do      # Keycloak takes a minute or two on first start
  login >/dev/null 2>&1 && break
  echo "waiting for keycloak ($try/60)"
  sleep 5
done
login                                      # once more, loudly: shows the real error if it never worked

# Keycloak drops attributes it has no profile entry for, bureau_id included. Let
# administrators (only) set them; users still cannot change their own bureau.
kcadm update users/profile -r sethu -s unmanagedAttributePolicy=ADMIN_EDIT

# The password lives only in .env; the file in the repository holds a placeholder.
users=$(</demo/users.json)
printf '%s' "${users//__DEMO_USER_PASSWORD__/$DEMO_USER_PASSWORD}" > /tmp/users.json
kcadm create partialImport -r sethu -s ifResourceExists=OVERWRITE -o -f /tmp/users.json
echo "demo users imported"
