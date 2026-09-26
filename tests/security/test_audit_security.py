"""Security regression tests for the fail-closed audit chain."""

from assurance_system.constants import AuditEventType
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore


def test_sec_010_modified_event_detected_without_reset(tmp_path):
    store = EvidenceStore(str(tmp_path / "audit-security.sqlite3"))
    writer = AuditChainWriter(store)
    for index in range(5):
        writer.append_event("SECURITY_TEST_EVENT", {"index": index})

    with store._conn:
        store._conn.execute(
            "UPDATE audit_events SET payload_digest = ? WHERE event_id = ?",
            ("tampered", 3),
        )

    result = writer.verify_chain_integrity()

    assert result.intact is False
    events = store.query_audit_trail()
    assert any(event["event_type"] == AuditEventType.CHAIN_CORRUPT for event in events)
    original_ids = {event["event_id"] for event in events if event["event_id"] <= 5}
    assert original_ids == {1, 2, 3, 4, 5}
    modified = store._conn.execute(
        "SELECT payload_digest FROM audit_events WHERE event_id = ?", (3,)
    ).fetchone()
    assert modified["payload_digest"] == "tampered"
    store._conn.close()
