#!/bin/bash
# Creates or resets the demo logins in the sethu realm (dev and demo only: the
# Compose service that runs this exists only under the `dev` profile).
# Safe to run again: existing demo users are overwritten, other users are untouched.
set -euo pipefail

# Demo logins share one password: they must never exist in production.
if [ "${SETHU_ENVIRONMENT:-dev}" = "prod" ]; then
  echo "refusing: SETHU_ENVIRONMENT is prod; demo users are for dev and demo stacks only" >&2
  exit 1
fi

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

# Sign-out sends people back to the app: allow the same addresses as sign-in ("+"). The realm
# file sets this too, but Keycloak reads that file only when it first creates the realm.
client=$(kcadm get clients -r sethu -q clientId=sethu-web --fields id --format csv --noquotes)
kcadm update "clients/$client" -r sethu -s 'attributes."post.logout.redirect.uris"=+'

# The password lives only in .env; the file in the repository holds a placeholder.
users=$(</demo/users.json)
printf '%s' "${users//__DEMO_USER_PASSWORD__/$DEMO_USER_PASSWORD}" > /tmp/users.json
kcadm create partialImport -r sethu -s ifResourceExists=OVERWRITE -o -f /tmp/users.json
echo "demo users imported"
