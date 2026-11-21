"""Regression tests for the Phase 5 security review (docs/SECURITY-REVIEW.md): each test names its finding."""
import io
import json
import os
import threading
import zipfile

import openpyxl
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.audit.service import record, verify
from app.core.config import get_settings
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.intake import service as intake

KEYRING_LIKE = '{"active": "k1", "keys": {"k1": "c2VjcmV0LWtleS1tYXRlcmlhbC1kby1ub3QtbGVhaw=="}}'


def test_a01_001_a_link_in_the_spool_folder_is_refused_unread(world, tmp_path):
    """OWASP-A01-001: a symbolic link dropped into the spool folder must not be followed (it could point at a
    mounted secret, whose content would come back in the error file)."""
    secret = tmp_path / "secret.json"
    secret.write_text(KEYRING_LIKE, encoding="utf-8")
    inbox = tmp_path / "spool" / "pgrc-spool"
    inbox.mkdir(parents=True)
    try:
        os.symlink(secret, inbox / "steal.csv")
    except (OSError, NotImplementedError):
        pytest.skip("this machine cannot create symbolic links (Windows without developer mode); CI runs it")
    assert intake.spool(world["engine"], str(tmp_path / "spool"))["files"] == 0
    written = "".join(p.read_text(encoding="utf-8") for p in (inbox / "rejected").glob("*.errors.txt"))
    assert "not a regular file" in written and "c2VjcmV0" not in written and "active" not in written


def test_a01_001_an_unknown_header_is_not_echoed(tmp_path):
    """OWASP-A01-001 (second half): whatever a file's first line holds is not written back in the error."""
    with pytest.raises(intake.IntakeError) as refused:
        intake.parse_rows(KEYRING_LIKE.encode() + b"\n1,2\n", "x.csv")
    assert "c2VjcmV0" not in str(refused.value) and "keys" not in str(refused.value)
    assert "more that are not column names" in str(refused.value)
    with pytest.raises(intake.IntakeError) as named:
        intake.parse_rows(b"institution_name,category,body,colour\n", "x.csv")
    assert "unknown colour" in str(named.value)            # a column-like name is still named, to help


def _xlsx(rows: int = 1, pad: int = 0) -> bytes:
    book = openpyxl.Workbook()
    book.active.append(["institution_name", "category", "body"])
    for n in range(rows):
        book.active.append(["Greenfield Institute of Technology", "Fee refund", f"Row {n} " + "x" * 30])
    out = io.BytesIO()
    book.save(out)
    if not pad:
        return out.getvalue()
    padded = io.BytesIO()   # the same workbook, with a sheet that expands to `pad` bytes of spaces
    with zipfile.ZipFile(io.BytesIO(out.getvalue())) as src, zipfile.ZipFile(padded, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item)
            if item.filename == "xl/worksheets/sheet1.xml":
                data = data.replace(b"<sheetData>", b"<sheetData>" + b" " * pad, 1)
            dst.writestr(item, data)
    return padded.getvalue()


def test_a06_001_a_spreadsheet_that_expands_too_far_is_refused_before_parsing():
    """OWASP-A06-001: a small XLSX (a zip) that expands to more than the limit is refused unparsed."""
    bomb = _xlsx(pad=get_settings().intake_max_xlsx_expanded_bytes + 1_000_000)
    assert len(bomb) < get_settings().intake_max_upload_bytes          # it passes the upload size check
    with pytest.raises(intake.IntakeError) as refused:
        intake.parse_rows(bomb, "bomb.xlsx")
    assert refused.value.status == 413 and "expands to more than" in str(refused.value)


def test_a06_001_the_row_limit_is_enforced_while_reading(monkeypatch):
    monkeypatch.setattr(get_settings(), "intake_max_rows", 50)
    with pytest.raises(intake.IntakeError) as refused:
        intake.parse_rows(_xlsx(rows=500), "many.xlsx")
    assert refused.value.status == 413 and "more than 50 rows" in str(refused.value)


def test_a10_001_concurrent_writers_keep_the_audit_chain_whole(app_engine):
    """The chain under concurrent writers (the review's audit-chain check): every entry gets its own number in
    order and the chain verifies."""
    def write(n: int) -> None:
        for i in range(10):
            with session_for(SYSTEM, app_engine) as s:
                record(s, SYSTEM, "test.concurrent", payload={"writer": n, "i": i})

    threads = [threading.Thread(target=write, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    with session_for(SYSTEM, app_engine) as s:
        seqs = s.execute(text("SELECT seq FROM sethu.audit_log ORDER BY seq")).scalars().all()
        assert seqs == list(range(seqs[0], seqs[0] + len(seqs))) and len(seqs) >= 80
        assert verify(s).ok


def test_a02_001_the_api_description_is_not_under_the_proxied_path():
    """OWASP-A02-001: OpenAPI and the docs page are served at the backend's own /docs, which the edge does not
    proxy (it forwards /api/ only); nothing under /api describes the API."""
    client = TestClient(app)
    assert client.get("/api/docs").status_code == 404 and client.get("/api/openapi.json").status_code == 404
    assert client.get("/docs").status_code == 200
    assert "/api/v1/intake/submissions" in json.loads(client.get("/openapi.json").text)["paths"]
