"""Install or renew the edge TLS certificate without rebuilding (docs/RUNBOOK.md section 7, "TLS").

    python scripts/install_cert.py <fullchain.pem> <private-key.pem>

Copies the certificate (server first, then intermediates) and its key into SETHU_CERTS_DIR (default
infra/certs, git-ignored, mounted read-only into the web container), asks nginx to check them, and
reloads nginx. If nginx rejects them (wrong key, bad file) the previous pair is put back and nothing
is reloaded. The old pair is kept as server.crt.prev / server.key.prev. Standard library only.
"""
import os
import shutil
import ssl
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Compose reads COMPOSE_FILE / COMPOSE_PROJECT_NAME / COMPOSE_ENV_FILES itself when they are set.
COMPOSE = ["docker", "compose"] + ([] if os.environ.get("COMPOSE_FILE")
                                   else ["-f", "docker-compose.yml", "-f", "docker-compose.prod.yml"])


def check_pem(cert: Path, key: Path) -> str:
    """Refuses files that are not a PEM certificate and a PEM private key; returns a summary."""
    if "-----BEGIN CERTIFICATE-----" not in cert.read_text(encoding="ascii", errors="replace"):
        raise SystemExit(f"{cert}: not a PEM certificate")
    if "PRIVATE KEY-----" not in key.read_text(encoding="ascii", errors="replace"):
        raise SystemExit(f"{key}: not a PEM private key")
    try:  # first certificate in the chain; a private helper, so only for the summary
        info = ssl._ssl._test_decode_cert(str(cert))  # noqa: SLF001
    except Exception:  # noqa: BLE001
        return "(could not read the certificate's details; nginx checks it next)"
    expires = datetime.strptime(info["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC)
    if expires < datetime.now(UTC):
        raise SystemExit(f"{cert}: expired on {expires:%Y-%m-%d}")
    names = ", ".join(v for k, v in info.get("subjectAltName", ()) if k == "DNS")
    return f"for {names or 'no DNS names'}, expires {expires:%Y-%m-%d}"


def nginx(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([*COMPOSE, "exec", "-T", "web", "nginx", *args], cwd=ROOT,  # noqa: S603
                          capture_output=True, text=True, check=False)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    cert, key = Path(argv[0]), Path(argv[1])
    print("certificate", check_pem(cert, key))
    folder = Path(os.environ.get("SETHU_CERTS_DIR", ROOT / "infra" / "certs"))
    folder.mkdir(parents=True, exist_ok=True)
    live = {"server.crt": cert, "server.key": key}
    for name in live:
        if (folder / name).exists():
            shutil.copy2(folder / name, folder / f"{name}.prev")
    for name, source in live.items():
        # Written in place (same file), so the read-only mount in the running container sees it.
        (folder / name).write_bytes(source.read_bytes())
    (folder / "server.key").chmod(0o644)  # nginx runs as its own unprivileged user; the folder is 0700

    test = nginx("-t")
    if test.returncode != 0:
        for name in live:
            if (folder / f"{name}.prev").exists():
                (folder / name).write_bytes((folder / f"{name}.prev").read_bytes())
        print("nginx rejected the new pair; the previous one is back in place:\n" + test.stderr.strip())
        return 1
    reload = nginx("-s", "reload")
    if reload.returncode != 0:
        print("nginx accepted the files but did not reload:\n" + reload.stderr.strip())
        return 1
    print(f"installed in {folder} and nginx reloaded; no rebuild or restart was needed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
