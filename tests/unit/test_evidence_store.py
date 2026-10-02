"""UT-STORE-001 through UT-STORE-006."""

import pytest

from assurance_system.exceptions import SchemaViolationError, StorageWriteError
from assurance_system.supervisor.evidence_store import EvidenceStore


@pytest.fixture
def store(tmp_path):
    evidence_store = EvidenceStore(str(tmp_path / "evidence.sqlite3"))
    yield evidence_store
    evidence_store._conn.close()


@pytest.fixture
def evidence_record():
    return {
        "record_id": "record-001",
        "schema_version": "1.0.0",
        "asset_id": "asset-001",
        "method_id": "M01",
        "assessment_status": "COMPLETED",
        "raw_signal": {"count": 3},
        "access_mode": "BLACK_BOX",
        "artifact_unit_id": "artifact-001",
        "coverage_gap_clean_label": 1,
        "limitations": ["test"],
        "non_claims": ["test"],
        "dependency_declaration": {"reference": "UNAVAILABLE"},
        "assessment_timestamp": "2026-09-27T00:00:00Z",
        "worker_id": "worker-test",
        "record_digest": "digest-001",
        "is_synthetic": 0,
    }


def test_ut_store_001_round_trip(store, evidence_record):
    assert store.write_evidence_record(evidence_record) == "record-001"
    restored = store.query_evidence("asset-001", "M01")
    assert restored is not None
    for field, value in evidence_record.items():
        assert restored[field] == value


def test_ut_store_002_missing_required_field_rejected(store, evidence_record):
    evidence_record.pop("asset_id")
    with pytest.raises(SchemaViolationError):
        store.write_evidence_record(evidence_record)
    count = store._conn.execute("SELECT COUNT(*) FROM evidence_records").fetchone()[0]
    assert count == 0


def test_ut_store_003_prohibited_aggregate_rejected(store, evidence_record):
    evidence_record["risk_score"] = 0.25
    with pytest.raises(SchemaViolationError):
        store.write_evidence_record(evidence_record)
    count = store._conn.execute("SELECT COUNT(*) FROM evidence_records").fetchone()[0]
    assert count == 0


def test_ut_store_004_false_clean_label_rejected(store, evidence_record):
    evidence_record["coverage_gap_clean_label"] = False
    with pytest.raises(SchemaViolationError):
        store.write_evidence_record(evidence_record)
    count = store._conn.execute("SELECT COUNT(*) FROM evidence_records").fetchone()[0]
    assert count == 0


def test_ut_store_005_duplicate_replay_nonce_rejected(store):
    first = {
        "provenance_id": "provenance-001",
        "schema_version": "1.0.0",
        "artifact_unit_digest": "artifact-digest",
        "evidence_record_digests": ["evidence-digest"],
        "signing_key_id": "test-key",
        "signature": None,
        "signature_algorithm": None,
        "sequence_number": 1,
        "replay_nonce": "nonce-001",
        "pf_002_non_claim": "test non-claim",
        "signing_status": "SIGNING_UNAVAILABLE",
        "timestamp": "2026-09-27T00:00:00Z",
    }
    second = dict(first, provenance_id="provenance-002")
    store.write_provenance_record(first)
    with pytest.raises(StorageWriteError):
        store.write_provenance_record(second)
    count = store._conn.execute(
        "SELECT COUNT(*) FROM provenance_records"
    ).fetchone()[0]
    assert count == 1


def test_ut_store_006_wal_mode_enabled(store):
    assert store._confirm_wal_mode() is True


def test_dashboard_read_queries_are_select_only_decoded_and_ordered(store, evidence_record):
    store.write_evidence_record(dict(evidence_record, record_id="z-record"))
    store.write_evidence_record(dict(evidence_record, record_id="a-record"))
    for index, name in enumerate(("z-provenance", "a-provenance")):
        store.write_provenance_record({
            "provenance_id": name, "schema_version": "v1.0",
            "artifact_unit_digest": "a" * 64, "evidence_record_digests": ["e" * 64],
            "signing_key_id": "UNAVAILABLE", "sequence_number": index + 1,
            "replay_nonce": name, "pf_002_non_claim": "test non-claim",
            "signing_status": "SIGNING_UNAVAILABLE", "timestamp": "2026-10-02T00:00:00Z",
        })
    statements = []
    before = store._conn.total_changes
    store._conn.set_trace_callback(statements.append)
    evidence = store.query_all_evidence()
    provenance = store.query_provenance_records()
    state = store.query_chain_state()
    store._conn.set_trace_callback(None)
    assert all(sql.strip().upper().startswith("SELECT") for sql in statements)
    assert store._conn.total_changes == before
    assert [row["record_id"] for row in evidence] == ["a-record", "z-record"]
    assert evidence[0]["raw_signal"] == {"count": 3}
    assert evidence[0]["limitations"] == ["test"]
    assert [row["provenance_id"] for row in provenance] == ["a-provenance", "z-provenance"]
    assert provenance[0]["evidence_record_digests"] == ["e" * 64]
    assert state == {"last_event_id": 0, "last_chain_link_hash": "GENESIS", "last_sequence_number": 0}
