"""Alert outbox: approval of held alerts and delivery through an SMTP relay (a fake one here)."""
import email
import email.policy
import re
import socket
import socketserver
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.audit.service import verify
from app.core.auth import Principal, get_principal
from app.db.session import SYSTEM, session_for
from app.main import app
from app.modules.alerts import service
from app.modules.alerts.service import AlertError
from app.modules.overlaps import service as overlaps
from tests.conftest import requires_db
from tests.test_seed import COMPLAINTS

pytestmark = requires_db

HEADS = ["fernandes@sethu.test", "iyer@sethu.test", "mkulkarni@sethu.test"]  # PGRC and RB heads


class FakeSMTP(socketserver.ThreadingTCPServer):
    """Just enough SMTP for smtplib. Keeps every message; refuses the addresses in `refuse`."""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), SMTPSession)
        self.messages: list[email.message.Message] = []
        self.refuse: set[str] = set()


class SMTPSession(socketserver.StreamRequestHandler):
    def handle(self):
        def say(line):
            self.wfile.write(f"{line}\r\n".encode())

        say("220 fake relay")
        while line := self.rfile.readline():
            command = line.decode().strip()
            verb = command[:4].upper()
            if verb == "RCPT":
                address = command.split(":", 1)[1].strip().strip("<>")
                say("550 no such user" if address in self.server.refuse else "250 ok")
            elif verb == "DATA":
                say("354 go ahead")
                data = b""
                while (chunk := self.rfile.readline()) not in (b".\r\n", b""):
                    data += chunk
                self.server.messages.append(email.message_from_bytes(data, policy=email.policy.default))
                say("250 queued")
            elif verb == "QUIT":
                say("221 bye")
                return
            else:  # EHLO, HELO, MAIL, RSET, NOOP
                say("250 ok")


@pytest.fixture
def relay():
    server = FakeSMTP()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server
    server.shutdown()
    server.server_close()


def closed_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def approved(world):
    """The demo overlap (C-101 and C-102) approved by Ms. Rao: one alert in the outbox for three heads."""
    with session_for(SYSTEM, world["engine"]) as s:
        overlaps.detect(s, SYSTEM)
        demo = next(link["id"] for link in overlaps.links(s, SYSTEM)
                    if [c["ref"] for c in link["cases"]] == ["C-101", "C-102"])
    with session_for(world["rao"], world["engine"]) as s:
        overlaps.decide(s, world["rao"], demo, approve=True)
        world["alert"] = s.execute(text("SELECT id FROM sethu.alerts")).scalar_one()
    return world


def deliver(world, relay=None, port=None):
    return service.deliver(world["engine"], "127.0.0.1", port or relay.server_address[1])


def alert_row(world):
    with session_for(SYSTEM, world["engine"]) as s:
        return s.execute(text("SELECT status, sent_at, attempts, last_error FROM sethu.alerts")).one()


def audit_count(world, action):
    with session_for(SYSTEM, world["engine"]) as s:
        return s.execute(text("SELECT count(*) FROM sethu.audit_log WHERE action = :a"), {"a": action}).scalar_one()


def test_one_email_per_recipient_with_references_only(approved, relay):
    assert deliver(approved, relay) == {"sent": 1, "retry": 0, "failed": 0}
    assert sorted(m["To"] for m in relay.messages) == HEADS
    for message in relay.messages:
        assert message["From"] == "sethu-alerts@sethu.test"
        assert message["Subject"] == "Potential Overlapping Cases – Coordination Required: C-101 and C-102"
        body = message.get_content()
        assert "C-101 (PGRC)" in body and "C-102 (RB)" in body
        assert "Greenfield Institute of Technology" in body and "Faculty shortage" in body
        # No complaint text at all: no sentence of any of the 300 complaints, no name of a person.
        for c in COMPLAINTS:
            for sentence in re.split(r"[.।]", c["body"]):
                assert len(sentence.strip()) < 15 or sentence.strip() not in body, c["ref"]
        assert "Rao" not in body

    row = alert_row(approved)
    assert (row.status, row.attempts, row.last_error) == ("sent", 1, None) and row.sent_at
    assert audit_count(approved, "alert.delivered") == 3 and audit_count(approved, "alert.sent") == 1
    with session_for(SYSTEM, approved["engine"]) as s:
        assert verify(s).ok


def test_a_second_run_does_not_resend(approved, relay):
    deliver(approved, relay)
    assert deliver(approved, relay) == {"sent": 0, "retry": 0, "failed": 0}
    assert len(relay.messages) == 3 and audit_count(approved, "alert.delivered") == 3


def test_two_workers_never_hold_the_same_alert(approved, relay):
    with session_for(SYSTEM, approved["engine"]) as busy:  # another worker is in the middle of sending it
        busy.execute(text("SELECT id FROM sethu.alerts FOR UPDATE"))
        assert deliver(approved, relay) == {"sent": 0, "retry": 0, "failed": 0}
    assert relay.messages == []
    assert deliver(approved, relay)["sent"] == 1 and len(relay.messages) == 3


def test_a_failed_send_stays_approved_and_is_retried_without_duplicates(approved, relay):
    # The relay is down: nothing sent, the alert waits.
    assert deliver(approved, port=closed_port()) == {"sent": 0, "retry": 1, "failed": 0}
    row = alert_row(approved)
    assert (row.status, row.sent_at, row.attempts) == ("approved", None, 1)
    assert row.last_error.startswith("ConnectionRefusedError")

    # The relay refuses the second head: the first is reached, the alert still waits.
    relay.refuse = {HEADS[1]}
    assert deliver(approved, relay) == {"sent": 0, "retry": 1, "failed": 0}
    assert [m["To"] for m in relay.messages] == [HEADS[0]]
    row = alert_row(approved)
    assert (row.status, row.sent_at, row.attempts) == ("approved", None, 2)
    assert "SMTPRecipientsRefused" in row.last_error

    # Back to normal: only the two not yet reached get an email, and the alert is sent.
    relay.refuse = set()
    assert deliver(approved, relay) == {"sent": 1, "retry": 0, "failed": 0}
    assert sorted(m["To"] for m in relay.messages) == HEADS
    row = alert_row(approved)
    assert (row.status, row.attempts, row.last_error) == ("sent", 3, None)
    assert audit_count(approved, "alert.send_failed") == 2 and audit_count(approved, "alert.delivered") == 3
    with session_for(SYSTEM, approved["engine"]) as s:
        assert verify(s).ok


def test_mail_only_goes_to_sethu_users(world, relay):
    with session_for(SYSTEM, world["engine"]) as s:
        s.execute(text("INSERT INTO sethu.alerts (kind, status, recipients, subject, body) VALUES"
                       " ('sla', 'approved', '[\"iyer@sethu.test\", \"someone@elsewhere.example\"]', 's', 'b')"))
    assert deliver(world, relay) == {"sent": 0, "retry": 0, "failed": 1}
    assert relay.messages == []
    row = alert_row(world)
    assert row.status == "failed" and row.last_error == "not a SETHU user: someone@elsewhere.example"


@pytest.fixture
def held(world):
    """Two alerts waiting for approval: one about C-101 (PGRC only), one about the C-101/C-102 overlap."""
    with session_for(SYSTEM, world["engine"]) as s:
        overlaps.detect(s, SYSTEM)
        link = next(link["id"] for link in overlaps.links(s, SYSTEM)
                    if [c["ref"] for c in link["cases"]] == ["C-101", "C-102"])
        world["held"] = {
            kind: s.execute(text(
                "INSERT INTO sethu.alerts (kind, overlap_link_id, complaint_id, recipients, subject, body)"
                " VALUES (:kind, :link, :case, '[\"fernandes@sethu.test\"]', :kind, 'C-101') RETURNING id"),
                {"kind": kind, "link": link if kind == "overlap" else None,
                 "case": world["case"]["C-101"] if kind == "sla" else None}).scalar_one()
            for kind in ("sla", "overlap")}
        world["third"] = s.execute(text(
            "INSERT INTO sethu.bureaus (code, name) VALUES ('XB', 'XB') RETURNING id")).scalar_one()
    return world


def kinds(world, principal):
    with session_for(principal, world["engine"]) as s:
        return sorted(a["kind"] for a in service.listing(s, principal))


def test_a_bureau_sees_only_alerts_it_is_party_to(held):
    assert kinds(held, held["fernandes"]) == ["overlap", "sla"]  # PGRC: both concern its case C-101
    assert kinds(held, held["iyer"]) == ["overlap"]              # RB: party to the overlap only
    assert kinds(held, Principal("u-x", "x", "bureau_head", held["third"])) == []
    assert kinds(held, held["menon"]) == kinds(held, held["das"]) == ["overlap", "sla"]


def test_heads_of_a_concerned_bureau_and_oversight_approve_held_alerts(held, relay):
    sla, overlap = held["held"]["sla"], held["held"]["overlap"]
    with session_for(held["iyer"], held["engine"]) as s:  # RB cannot see the PGRC-only alert
        with pytest.raises(AlertError) as hidden:
            service.decide(s, held["iyer"], sla, approve=True)
        assert hidden.value.status == 404
    with session_for(held["rao"], held["engine"]) as s:  # an officer can see it but not decide
        assert not any(a["can_decide"] for a in service.listing(s, held["rao"]))
        assert s.execute(text("UPDATE sethu.alerts SET status = 'approved'")).rowcount == 0

    assert deliver(held, relay)["sent"] == 0  # held alerts are never sent

    with session_for(held["fernandes"], held["engine"]) as s:
        decided = service.decide(s, held["fernandes"], sla, approve=True)
        assert (decided["status"], decided["approved_by"], decided["can_decide"]) == (
            "approved", "Maria Fernandes", False)
        with pytest.raises(AlertError) as again:
            service.decide(s, held["fernandes"], sla, approve=False)
        assert again.value.status == 409
    with session_for(held["menon"], held["engine"]) as s:  # oversight decides any alert
        assert service.decide(s, held["menon"], overlap, approve=False)["status"] == "rejected"

    # Approving does not allow rewriting the alert.
    with session_for(SYSTEM, held["engine"]) as s:
        s.execute(text("UPDATE sethu.alerts SET status = 'pending_approval' WHERE id = :i"), {"i": overlap})
    with pytest.raises(DBAPIError), session_for(held["iyer"], held["engine"]) as s:
        s.execute(text("UPDATE sethu.alerts SET status = 'approved', recipients = '[\"x@elsewhere.example\"]'"
                       " WHERE id = :i"), {"i": overlap})

    assert deliver(held, relay) == {"sent": 1, "retry": 0, "failed": 0}  # the approved one only
    assert [m["To"] for m in relay.messages] == ["fernandes@sethu.test"]
    with session_for(SYSTEM, held["engine"]) as s:
        actions = s.execute(text("SELECT action, actor FROM sethu.audit_log WHERE action IN"
                                 " ('alert.approve', 'alert.reject') ORDER BY seq")).all()
        assert [tuple(a) for a in actions] == [("alert.approve", held["fernandes"].subject),
                                               ("alert.reject", held["menon"].subject)]
        assert verify(s).ok


def test_api_lists_and_decides_by_role(held):
    client, sla = TestClient(app), held["held"]["sla"]
    try:
        app.dependency_overrides[get_principal] = lambda: held["iyer"]
        page = client.get("/api/v1/alerts").json()
        assert [a["kind"] for a in page["items"]] == ["overlap"] and page["mail_inbox_url"] is None
        assert page["items"][0]["cases"] == ["C-101", "C-102"]
        for who in (held["rao"], held["das"]):
            app.dependency_overrides[get_principal] = lambda who=who: who
            assert client.post(f"/api/v1/alerts/{sla}/decision", json={"decision": "approve"}).status_code == 403
        app.dependency_overrides[get_principal] = lambda: held["fernandes"]
        assert len(client.get("/api/v1/alerts", params={"status": "pending_approval"}).json()["items"]) == 2
        done = client.post(f"/api/v1/alerts/{sla}/decision", json={"decision": "approve"})
        assert done.status_code == 200 and done.json()["status"] == "approved"
        assert client.get("/api/v1/alerts", params={"status": "nonsense"}).status_code == 422
    finally:
        app.dependency_overrides.clear()
