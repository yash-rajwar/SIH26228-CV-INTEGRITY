"""TASK-019 Part A replay and supervisor-boundary security tests."""

from __future__ import annotations

import pathlib

import pytest

from assurance_system.constants import AuditEventType
from assurance_system.exceptions import ReplayAttemptError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.provenance import ProvenanceBuilder


def test_sec_009_duplicate_replay_nonce_is_rejected_with_audit_event(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = EvidenceStore(str(tmp_path / "sec-009.sqlite3"))
    builder = ProvenanceBuilder(store, AuditChainWriter(store))
    nonce = "fedcba9876543210" * 2
    artifact_digest = "a" * 64
    evidence_digests = ["b" * 64]
    captured: list[tuple[str, dict]] = []

    try:
        builder.build_and_sign(
            artifact_digest, evidence_digests, replay_nonce=nonce
        )
        original = builder._audit.append_event

        def capture(event_type: str, payload: dict) -> str:
            captured.append((event_type, payload))
            return original(event_type, payload)

        monkeypatch.setattr(builder._audit, "append_event", capture)
        with pytest.raises(ReplayAttemptError):
            builder.build_and_sign(
                artifact_digest, evidence_digests, replay_nonce=nonce
            )

        assert [event_type for event_type, _payload in captured] == [
            AuditEventType.REPLAY_ATTEMPT_DETECTED
        ]
        assert (
            store._conn.execute(
                "SELECT COUNT(*) FROM provenance_records WHERE replay_nonce = ?",
                (nonce,),
            ).fetchone()[0]
            == 1
        )
        assert store.query_audit_trail()[-1]["event_type"] == (
            AuditEventType.REPLAY_ATTEMPT_DETECTED
        )
    finally:
        store._conn.close()


def test_provenance_remains_supervisor_only_and_unsigned() -> None:
    root = pathlib.Path(__file__).parents[2]
    provenance_source = (
        root / "assurance_system" / "supervisor" / "provenance.py"
    ).read_text(encoding="utf-8")
    workers = root / "assurance_system" / "workers"

    assert "import hmac" not in provenance_source
    assert "cryptography" not in provenance_source
    assert all(
        "supervisor.provenance" not in path.read_text(encoding="utf-8")
        for path in workers.rglob("*.py")
    )
