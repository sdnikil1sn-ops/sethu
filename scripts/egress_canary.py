"""Egress canary: fail if a SETHU container can reach the internet, or tries to while the stack is idle.

    python scripts/egress_canary.py [--project sethu] [--start] [--watch-attempts SECONDS] [--strict]

1. `--start`: `docker compose --profile dev up -d --build --wait` first (CI). Otherwise the running project is used.
2. `--watch-attempts N` (Linux host or Docker Desktop): counting-only firewall rules (no target, so nothing is
   changed) are put in the Docker host's DOCKER-USER chain for every network of the project; after N idle seconds
   any NEW connection from those networks to a public address fails the canary. Needs a privileged helper container
   (alpine) to enter the Docker host's network namespace, as loadtest/offline.sh does.
3. Every running container then tries a TCP connection to a public address and a DNS lookup of a public name.

Verdict: a container on internal networks only (app, data, ai) must reach nothing. `ai-worker` must exist, be on
internal networks only and reach nothing. Containers on the `edge` network (web, keycloak, mailpit) have an outbound
route by design (Docker publishes ports only from a non-internal network); they are listed, and fail only with
`--strict` (use it with loadtest/offline.sh on, which closes that route). Exit 0 pass, 1 fail, 2 could not run.
"""
import argparse
import json
import os
import subprocess
import sys
import time

PUBLIC_IP, PUBLIC_PORT, PUBLIC_NAME = "1.1.1.1", 443, "example.com"
PRIVATE = ("10.0.0.0-10.255.255.255", "172.16.0.0-172.31.255.255", "192.168.0.0-192.168.255.255",
           "127.0.0.0-127.255.255.255", "100.64.0.0-100.127.255.255", "169.254.0.0-169.254.255.255")
COMMENT = "sethu-egress-canary"
HELPER = "alpine:3@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf"   # nsenter, iptables
# One probe per available tool: Python (backend images), bash (Keycloak, PostgreSQL), busybox (alpine images).
PROBE = ("if command -v python3 >/dev/null; then python3 - <<'EOF'\n"
         "import socket\n"
         "def tcp():\n"
         "    try:\n"
         f"        socket.create_connection(('{PUBLIC_IP}', {PUBLIC_PORT}), timeout=4).close(); return 'yes'\n"
         "    except OSError: return 'no'\n"
         "def dns():\n"
         f"    try: socket.getaddrinfo('{PUBLIC_NAME}', 443); return 'yes'\n"
         "    except OSError: return 'no'\n"
         "print('tcp=' + tcp(), 'dns=' + dns())\n"
         "EOF\n"
         f"elif command -v bash >/dev/null; then "
         f"(timeout 5 bash -c '</dev/tcp/{PUBLIC_IP}/{PUBLIC_PORT}' 2>/dev/null && echo tcp=yes || echo tcp=no); "
         f"(getent hosts {PUBLIC_NAME} >/dev/null 2>&1 && echo dns=yes || echo dns=no); "
         f"elif command -v nc >/dev/null; then "
         f"(timeout 5 nc -z {PUBLIC_IP} {PUBLIC_PORT} 2>/dev/null && echo tcp=yes || echo tcp=no); "
         f"(nslookup {PUBLIC_NAME} >/dev/null 2>&1 && echo dns=yes || echo dns=no); "
         "else echo untestable; fi")


def sh(*args: str, check: bool = True) -> str:
    done = subprocess.run(args, capture_output=True, text=True,  # noqa: S603 - fixed docker commands, no shell
                          env=os.environ | {"MSYS_NO_PATHCONV": "1"})
    if check and done.returncode:
        raise RuntimeError(f"{' '.join(args[:3])}...: {done.stderr.strip()[-300:]}")
    return done.stdout


def containers(project: str) -> list[dict]:
    label = f"label=com.docker.compose.project={project}"
    ids = sh("docker", "ps", "-q", "--filter", label).split()
    net_ids = sh("docker", "network", "ls", "-q", "--filter", label).split()
    networks = {n["Name"]: n for n in json.loads(sh("docker", "network", "inspect", *net_ids))} if net_ids else {}
    found = []
    for i in ids:
        info = json.loads(sh("docker", "inspect", i))[0]
        names = info["NetworkSettings"]["Networks"]
        found.append({"name": info["Name"].lstrip("/"),
                      "service": info["Config"]["Labels"].get("com.docker.compose.service", "?"),
                      "networks": {n: bool(networks.get(n, {}).get("Internal")) for n in names}})
    return found


def probe(container: str) -> dict:
    out = sh("docker", "exec", container, "sh", "-c", PROBE, check=False)
    if "untestable" in out or "tcp=" not in out:
        return {"tcp": None, "dns": None}
    return {"tcp": "tcp=yes" in out, "dns": "dns=yes" in out}


def verdicts(found: list[dict], strict: bool) -> tuple[list[str], list[str]]:
    """Failures and notes for containers with their networks and probe results. Pure: tested on its own."""
    failures, notes = [], []
    services = {c["service"] for c in found}
    if "ai-worker" not in services:
        failures.append("ai-worker is not running")
    for c in found:
        internal_only = all(c["networks"].values())
        reached = [k for k in ("tcp", "dns") if c["reach"].get(k)]
        where = f"{c['service']} ({', '.join(sorted(c['networks']))})"
        if c["service"] == "ai-worker" and not internal_only:
            failures.append(f"{where}: ai-worker is on a network with a route out")
        if c["reach"].get("tcp") is None:
            (failures if c["service"] == "ai-worker" else notes).append(f"{where}: could not be probed (no tool)")
        elif reached and (internal_only or strict or c["service"] == "ai-worker"):
            failures.append(f"{where}: reached the internet ({', '.join(reached)})")
        elif reached:
            notes.append(f"{where}: has an outbound route by design (edge network); --strict with offline.sh on")
        else:
            notes.append(f"{where}: no route out")
    return failures, notes


def host_rules(project: str, action: str) -> str:
    """Add, read or remove the counting rules on the Docker host (via a privileged helper container)."""
    bridges = [f"br-{n[:12]}" for n in sh("docker", "network", "ls", "-q", "--filter",
                                           f"label=com.docker.compose.project={project}").split()]
    matches = " ".join(f"-m iprange ! --dst-range {r}" for r in PRIVATE)
    rules = [f"-i {b} -m conntrack --ctstate NEW {matches} -m comment --comment {COMMENT}" for b in bridges]
    script = {"add": " && ".join(f"iptables -I DOCKER-USER 1 {r}" for r in rules),
              "read": "iptables -L DOCKER-USER -v -x -n | grep " + COMMENT + " || true",
              "remove": " ; ".join(f"while iptables -D DOCKER-USER {r} 2>/dev/null; do :; done" for r in rules)}[action]
    return sh("docker", "run", "--rm", "--privileged", "--pid=host", "--network=none", HELPER,
              "nsenter", "-t", "1", "-m", "-n", "sh", "-c", script or "true")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if a SETHU container can reach the internet.")
    parser.add_argument("--project", default="sethu")
    parser.add_argument("--start", action="store_true", help="docker compose --profile dev up first")
    parser.add_argument("--watch-attempts", type=int, default=0, metavar="SECONDS")
    parser.add_argument("--strict", action="store_true", help="edge containers must not reach out either")
    args = parser.parse_args()
    try:
        if args.start:
            sh("docker", "compose", "-p", args.project, "--profile", "dev", "up", "-d", "--build", "--wait")
        failures, attempts = [], 0
        if args.watch_attempts:
            host_rules(args.project, "add")
            try:
                time.sleep(args.watch_attempts)
                counted = host_rules(args.project, "read")
                attempts = sum(int(line.split()[0]) for line in counted.splitlines() if line.strip())
            finally:
                host_rules(args.project, "remove")
            if attempts:
                failures.append(f"{attempts} outbound connection attempt(s) to public addresses in "
                                f"{args.watch_attempts} idle seconds")
        found = containers(args.project)
        for c in found:
            c["reach"] = probe(c["name"])
    except (RuntimeError, OSError, ValueError) as e:
        print(f"egress canary could not run: {e}")
        return 2
    more, notes = verdicts(found, args.strict)
    failures += more
    for line in notes:
        print("  ok   " + line)
    for line in failures:
        print("  FAIL " + line)
    print(("FAIL" if failures else "PASS") + f": {len(found)} containers checked"
          + (f", {attempts} attempts counted in {args.watch_attempts} s" if args.watch_attempts else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
