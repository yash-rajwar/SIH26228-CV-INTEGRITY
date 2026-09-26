"""UT-AUD-001 through UT-AUD-005."""

import pytest

from assurance_system.constants import AuditEventType
from assurance_system.exceptions import AuditWriteError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore


@pytest.fixture
def store(tmp_path):
    evidence_store = EvidenceStore(str(tmp_path / "audit.sqlite3"))
    yield evidence_store
    evidence_store._conn.close()


@pytest.fixture
def writer(store):
    return AuditChainWriter(store)


def _append_events(writer, count):
    for index in range(count):
        writer.append_event("TEST_EVENT", {"index": index})


def test_ut_aud_001_events_link_to_predecessor(store, writer):
    _append_events(writer, 3)
    events = store.query_audit_trail()
    assert events[0]["previous_event_digest"] == writer.GENESIS_HASH
    assert events[1]["previous_event_digest"] == events[0]["chain_link_hash"]
    assert events[2]["previous_event_digest"] == events[1]["chain_link_hash"]
    assert writer.verify_chain_integrity().intact is True


def test_ut_aud_002_corruption_is_flagged_without_deletion(store, writer):
    _append_events(writer, 2)
    with store._conn:
        store._conn.execute(
            "UPDATE audit_events SET chain_link_hash = ? WHERE event_id = ?",
            ("tampered", 1),
        )

    result = writer.verify_chain_integrity()

    assert result.intact is False
    assert result.violations
    events = store.query_audit_trail()
    assert any(event["event_type"] == AuditEventType.CHAIN_CORRUPT for event in events)
    assert store._conn.execute(
        "SELECT COUNT(*) FROM audit_events WHERE event_id = ?", (1,)
    ).fetchone()[0] == 1


def test_ut_aud_003_write_error_propagates(store, writer, monkeypatch):
    def fail_write(_event_type, _payload):
        raise AuditWriteError("simulated failure")

    monkeypatch.setattr(store, "write_audit_event", fail_write)
    with pytest.raises(AuditWriteError, match="simulated failure"):
        writer.append_event("TEST_EVENT", {"test": True})


def test_ut_aud_004_no_destructive_recovery_methods():
    for method_name in ("reset", "clear", "truncate"):
        assert not hasattr(AuditChainWriter, method_name)


def test_ut_aud_005_sequence_gap_is_detected(store, writer):
    _append_events(writer, 3)
    with store._conn:
        store._conn.execute("DELETE FROM audit_events WHERE event_id = ?", (2,))

    result = writer.verify_chain_integrity()

    assert result.intact is False
    assert any(
        violation["violation_type"] == "SEQUENCE_GAP"
        for violation in result.violations
    )
    events = store.query_audit_trail()
    assert any(
        event["event_type"] == AuditEventType.SEQUENCE_GAP_DETECTED
        for event in events
    )
