"""TASK-019 Part A: UT-C4-001 through UT-C4-006."""

from __future__ import annotations

import json
import pathlib

import pytest

from assurance_system.constants import (
    AuditEventType,
    CANONICALIZATION_ALGORITHM_ID,
    PF_002_NON_CLAIM,
    SigningStatus,
)
from assurance_system.exceptions import AuditWriteError, ReplayAttemptError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.provenance import (
    ProvenanceBuilder,
    SequenceState,
)
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator


ARTIFACT_DIGEST = "a" * 64
EVIDENCE_DIGESTS = ["b" * 64, "c" * 64]


@pytest.fixture
def store(tmp_path: pathlib.Path):
    evidence_store = EvidenceStore(str(tmp_path / "provenance.sqlite3"))
    yield evidence_store
    evidence_store._conn.close()


@pytest.fixture
def builder(store: EvidenceStore) -> ProvenanceBuilder:
    return ProvenanceBuilder(store, AuditChainWriter(store))


def _capture_audit_events(
    builder: ProvenanceBuilder, monkeypatch: pytest.MonkeyPatch
) -> list[tuple[str, dict]]:
    captured: list[tuple[str, dict]] = []
    original = builder._audit.append_event

    def capture(event_type: str, payload: dict) -> str:
        captured.append((event_type, payload))
        return original(event_type, payload)

    monkeypatch.setattr(builder._audit, "append_event", capture)
    return captured


def test_ut_c4_001_builds_canonical_provenance_with_pf_002(
    builder: ProvenanceBuilder, store: EvidenceStore
) -> None:
    record = builder.build_and_sign(
        ARTIFACT_DIGEST,
        EVIDENCE_DIGESTS,
        timestamp="2026-09-27T00:00:00Z",
    )

    assert record["pf_002_non_claim"] == PF_002_NON_CLAIM
    assert record["canonicalization_algorithm"] == CANONICALIZATION_ALGORITHM_ID
    assert len(record["replay_nonce"]) == 32
    assert record["sequence_number"] == 1
    assert EvidenceSchemaValidator().validate_provenance_record(record).valid

    expected = json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    assert builder.canonicalize(record) == expected

    persisted = store._conn.execute(
        "SELECT pf_002_non_claim FROM provenance_records"
    ).fetchone()
    assert persisted is not None
    assert persisted[0] == PF_002_NON_CLAIM


def test_ut_c4_002_duplicate_nonce_is_rejected_and_audited(
    builder: ProvenanceBuilder, monkeypatch: pytest.MonkeyPatch
) -> None:
    nonce = "0123456789abcdef" * 2
    builder.build_and_sign(
        ARTIFACT_DIGEST, EVIDENCE_DIGESTS, replay_nonce=nonce
    )
    captured = _capture_audit_events(builder, monkeypatch)

    with pytest.raises(ReplayAttemptError, match="Duplicate"):
        builder.build_and_sign(
            ARTIFACT_DIGEST, EVIDENCE_DIGESTS, replay_nonce=nonce
        )

    assert captured == [
        (
            AuditEventType.REPLAY_ATTEMPT_DETECTED,
            {"replay_nonce": nonce, "action": "REJECTED"},
        )
    ]


def test_ut_c4_003_sequence_gap_is_audited_and_recovered(
    builder: ProvenanceBuilder, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = _capture_audit_events(builder, monkeypatch)
    state = SequenceState(sequence_number=4)

    record = builder.build_and_sign(
        ARTIFACT_DIGEST, EVIDENCE_DIGESTS, sequence_state=state
    )

    gap_events = [
        event
        for event in captured
        if event[0] == AuditEventType.SEQUENCE_GAP_DETECTED
    ]
    assert gap_events == [
        (
            AuditEventType.SEQUENCE_GAP_DETECTED,
            {"expected": 1, "received": 4, "gap_size": 3},
        )
    ]
    assert record["sequence_number"] == 1
    assert state.sequence_number == 2
    assert state.last_record_digest


@pytest.mark.skip(
    reason=(
        "TASK-019 Part B only: PRE-02 selected HMAC-SHA256, but PRE-08 "
        "key-path and ACL provisioning remains unresolved"
    )
)
def test_ut_c4_004_hmac_signing_path() -> None:
    """Reserved conditional acceptance test; signing is outside Part A."""


@pytest.mark.skip(
    reason=(
        "NOT APPLICABLE: PRE-02 selected HMAC-SHA256, so Ed25519 was not "
        "selected for the MVP crypto profile"
    )
)
def test_ut_c4_005_ed25519_signing_path() -> None:
    """Reserved conditional test for the PRE-02 mechanism not selected."""


def test_ut_c4_006_key_unavailable_is_explicit_and_pipeline_continues(
    builder: ProvenanceBuilder, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = _capture_audit_events(builder, monkeypatch)

    record = builder.build_and_sign(ARTIFACT_DIGEST, EVIDENCE_DIGESTS)
    second = builder.build_and_sign(ARTIFACT_DIGEST, ["d" * 64])

    assert record["signature"] is None
    assert record["signature_algorithm"] is None
    assert record["signing_key_id"] == "UNAVAILABLE"
    assert record["signing_status"] == SigningStatus.SIGNING_UNAVAILABLE
    assert second["sequence_number"] == 2
    assert [event_type for event_type, _payload in captured] == [
        AuditEventType.SIGNING_UNAVAILABLE,
        AuditEventType.PROVENANCE_RECORD_WRITTEN,
        AuditEventType.SIGNING_UNAVAILABLE,
        AuditEventType.PROVENANCE_RECORD_WRITTEN,
    ]


def test_audit_write_error_is_never_swallowed(
    builder: ProvenanceBuilder, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_audit(_event_type: str, _payload: dict) -> str:
        raise AuditWriteError("simulated audit failure")

    monkeypatch.setattr(builder._audit, "append_event", fail_audit)

    with pytest.raises(AuditWriteError, match="simulated audit failure"):
        builder.build_and_sign(ARTIFACT_DIGEST, EVIDENCE_DIGESTS)
