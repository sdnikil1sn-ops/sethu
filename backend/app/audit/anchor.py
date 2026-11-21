"""Audit-chain anchors: the chain's latest entry number and hash, exported to a write-once place outside the
database, so tampering can be proven even if the database itself is replaced.

The worker appends one JSON line per hour to <SETHU_AUDIT_ANCHOR_DIR>/audit-anchor.jsonl. The operator makes
that directory append-only (a WORM share, or `chattr +a` on the file on a Linux host): the worker only ever
opens it for appending. `compare` checks every exported line against the live chain: each exported entry must
still exist with the same hash. A rewritten entry, a truncated chain or a database restored from somewhere
else all fail. Identifiers and hashes only.

    python -m app.audit.anchor export     # what the worker runs
    python -m app.audit.anchor compare    # prints the result; exit 1 on a mismatch
"""
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings

FILE = "audit-anchor.jsonl"


def _file() -> Path | None:
    folder = get_settings().audit_anchor_dir
    return Path(folder) / FILE if folder else None


def export(session: Session) -> dict:
    """Append the chain head. Returns what was written (or why nothing was)."""
    path = _file()
    if path is None:
        return {"exported": False, "reason": "SETHU_AUDIT_ANCHOR_DIR is not set"}
    head = session.execute(text(
        "SELECT seq, hash, (SELECT count(*) FROM sethu.audit_log) AS entries"
        " FROM sethu.audit_log ORDER BY seq DESC LIMIT 1")).mappings().first()
    if head is None:
        return {"exported": False, "reason": "the chain is empty"}
    line = {"exported_at": datetime.now(UTC).isoformat(), "seq": head["seq"], "hash": head["hash"],
            "entries": head["entries"]}
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)  # append only, never truncate
    try:
        os.write(fd, (json.dumps(line) + "\n").encode())
        os.fsync(fd)
    finally:
        os.close(fd)
    return {"exported": True} | line


def compare(session: Session) -> dict:
    """Every exported anchor against the live chain."""
    path = _file()
    if path is None:
        return {"configured": False, "ok": None, "anchors": 0, "problems": [], "latest": None}
    if not path.exists():
        return {"configured": True, "ok": None, "anchors": 0, "problems": ["no anchor exported yet"], "latest": None}
    anchors, problems = [], []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            a = json.loads(raw)
            anchors.append((int(a["seq"]), str(a["hash"]), a.get("exported_at")))
        except (ValueError, KeyError, TypeError):
            problems.append(f"line {n} of the anchor file is not a valid anchor")
    live = dict(session.execute(text("SELECT seq, hash FROM sethu.audit_log WHERE seq = ANY(:s)"),
                                {"s": [a[0] for a in anchors]}).all())
    top = session.execute(text("SELECT coalesce(max(seq), 0) FROM sethu.audit_log")).scalar_one()
    for seq, digest, when in anchors:
        if seq not in live:
            problems.append(f"entry {seq}, exported {when}, is missing: the chain was truncated or replaced")
        elif live[seq] != digest:
            problems.append(f"entry {seq}, exported {when}, has a different hash now: it was rewritten")
    latest = anchors[-1] if anchors else None
    return {"configured": True, "ok": not problems and bool(anchors), "anchors": len(anchors),
            "problems": problems[:20], "live_entries": top,
            "latest": {"seq": latest[0], "hash": latest[1], "exported_at": latest[2]} if latest else None}


def main(command: str) -> int:
    from app.db.session import SYSTEM, session_for

    with session_for(SYSTEM) as session:
        result = export(session) if command == "export" else compare(session)
    print(json.dumps(result, indent=2, default=str))
    return 1 if command == "compare" and result.get("ok") is False else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "compare"))
