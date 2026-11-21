#!/bin/sh
# Offline run: block every new outbound connection from a Compose project's networks, keep traffic between its
# containers and answers to the published ports (the browser on this machine). docs/LOAD-AND-DRILLS.md.
#
#   sh loadtest/offline.sh on  [project]   # default project: sethu
#   sh loadtest/offline.sh probe [project] # try to reach the internet from web and keycloak (should fail when on)
#   sh loadtest/offline.sh off [project]
#
# Works on a Linux host or Docker Desktop (it enters the Docker VM with a privileged helper container and edits
# the DOCKER-USER chain, which Docker leaves to the operator). Dev and test stacks only.
set -eu
action=${1:-}
project=${2:-sethu}
export MSYS_NO_PATHCONV=1

bridges() {
  for net in $(docker network ls --filter "label=com.docker.compose.project=$project" --format '{{.ID}}'); do
    echo "br-$(echo "$net" | cut -c1-12)"
  done
}

vm() { docker run --rm --privileged --pid=host alpine:3 nsenter -t 1 -m -n sh -c "$1"; }

rule() { echo "-i $1 ! -o $1 -m conntrack --ctstate NEW -m comment --comment sethu-offline -j DROP"; }

case "$action" in
  on)
    for br in $(bridges); do vm "iptables -C DOCKER-USER $(rule "$br") 2>/dev/null || iptables -I DOCKER-USER 1 $(rule "$br")"; done
    vm "iptables -S DOCKER-USER | grep sethu-offline" ;;
  off)
    for br in $(bridges); do vm "while iptables -D DOCKER-USER $(rule "$br") 2>/dev/null; do :; done"; done
    vm "iptables -S DOCKER-USER | grep -c sethu-offline || true" ;;
  probe)
    # A TCP connection to a public address; no data is sent.
    for svc in web keycloak; do
      if docker exec "$project-$svc-1" sh -c 'timeout 5 bash -c "</dev/tcp/1.1.1.1/443" 2>/dev/null || timeout 5 nc -z 1.1.1.1 443' >/dev/null 2>&1
      then echo "$svc: internet reachable"; else echo "$svc: no route out"; fi
    done ;;
  *) echo "usage: offline.sh on|off|probe [project]"; exit 2 ;;
esac
