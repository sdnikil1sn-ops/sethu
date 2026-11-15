import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.audit import service as audit
from app.core.auth import Principal
from app.db.session import session_for
from tests.conftest import requires_db

pytestmark = requires_db

AUDITOR = Principal(subject="u-auditor", name="auditor", role="auditor", bureau_id=None)


def _append(engine, n: int) -> None:
    for i in range(n):
        with session_for(AUDITOR, engine) as s:
            audit.record(s, AUDITOR, "test.event", entity_type="thing", entity_id=str(i),
                         payload={"i": i, "note": "pipe | and \"quotes\""})


def test_chain_is_valid_and_sequential(app_engine):
    _append(app_engine, 5)
    with session_for(AUDITOR, app_engine) as s:
        status = audit.verify(s)
        seqs = [r[0] for r in s.execute(text("SELECT seq FROM sethu.audit_log ORDER BY seq"))]
    assert status.ok and status.checked == 5 and status.broken_seq is None
    assert seqs == [1, 2, 3, 4, 5]


def test_client_cannot_choose_seq_or_hash(app_engine):
    with session_for(AUDITOR, app_engine) as s:
        s.execute(text(
            "INSERT INTO sethu.audit_log (seq, ts, actor, action, prev_hash, hash)"
            " VALUES (999, '2000-01-01', 'x', 'forged', 'aa', 'bb')"))
        row = s.execute(text("SELECT seq, hash, extract(year from ts) FROM sethu.audit_log")).one()
        assert row[0] == 1 and row[1] != "bb" and row[2] > 2020
        assert audit.verify(s).ok


@pytest.mark.parametrize("statement", [
    "UPDATE sethu.audit_log SET action = 'changed'",
    "DELETE FROM sethu.audit_log",
    "TRUNCATE sethu.audit_log",
])
def test_runtime_role_cannot_rewrite_history(app_engine, statement):
    _append(app_engine, 2)
    with pytest.raises(DBAPIError), session_for(AUDITOR, app_engine) as s:
        s.execute(text(statement))
    with session_for(AUDITOR, app_engine) as s:
        assert audit.verify(s).checked == 2


def test_tampering_by_a_privileged_user_is_detected(app_engine, owner_engine):
    _append(app_engine, 4)
    with owner_engine.begin() as conn:  # someone with owner rights bypasses the triggers
        conn.execute(text("ALTER TABLE sethu.audit_log DISABLE TRIGGER audit_log_no_change"))
        conn.execute(text("UPDATE sethu.audit_log SET payload = '{\"i\": 99}' WHERE seq = 3"))
        conn.execute(text("ALTER TABLE sethu.audit_log ENABLE TRIGGER audit_log_no_change"))
    with session_for(AUDITOR, app_engine) as s:
        status = audit.verify(s)
    assert not status.ok and status.broken_seq == 3 and status.checked == 2


def test_deleted_row_is_detected(app_engine, owner_engine):
    _append(app_engine, 4)
    with owner_engine.begin() as conn:
        conn.execute(text("ALTER TABLE sethu.audit_log DISABLE TRIGGER audit_log_no_change"))
        conn.execute(text("DELETE FROM sethu.audit_log WHERE seq = 2"))
        conn.execute(text("ALTER TABLE sethu.audit_log ENABLE TRIGGER audit_log_no_change"))
    with session_for(AUDITOR, app_engine) as s:
        status = audit.verify(s)
    assert not status.ok and status.broken_seq == 3
