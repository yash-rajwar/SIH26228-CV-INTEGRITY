"""UT-REF-001 through UT-REF-003 and COMP-REF security boundaries."""

from __future__ import annotations

import pathlib

import pytest

from assurance_system.constants import AuditEventType, ReferenceHealth
from assurance_system.exceptions import AuditWriteError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.reference_manager import (
    REFERENCE_CATEGORY_VIOLATION,
    ReferenceManager,
)


@pytest.fixture
def store(tmp_path: pathlib.Path):
    evidence_store = EvidenceStore(str(tmp_path / "reference-health.sqlite3"))
    yield evidence_store
    evidence_store._conn.close()


@pytest.fixture
def manager(store: EvidenceStore) -> ReferenceManager:
    return ReferenceManager(store, AuditChainWriter(store))


def _complete_gate_records(reference_id: str) -> dict[str, dict]:
    return {
        f"R{index}": {
            "reference_id": reference_id,
            "artifact_digest": "a" * 64,
            "passed": True,
        }
        for index in range(8)
    }


def _capture_audit_events(
    manager: ReferenceManager, monkeypatch: pytest.MonkeyPatch
) -> list[tuple[str, dict]]:
    captured: list[tuple[str, dict]] = []
    original = manager._audit.append_event

    def capture(event_type: str, payload: dict) -> str:
        captured.append((event_type, payload))
        return original(event_type, payload)

    monkeypatch.setattr(manager._audit, "append_event", capture)
    return captured


def test_ut_ref_001_unregistered_reference_is_unavailable(
    manager: ReferenceManager,
) -> None:
    assert manager.get_reference_health("any-id") == ReferenceHealth.UNAVAILABLE


def test_ut_ref_002_format_asset_cannot_be_promoted(
    manager: ReferenceManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = _capture_audit_events(manager, monkeypatch)
    assert (
        manager.register_reference(
            reference_id="coco-val2017",
            format_category=ReferenceHealth.FORMAT_ASSET,
        )
        == ReferenceHealth.FORMAT_ASSET
    )
    captured.clear()

    result = manager.attempt_health_promotion(
        "coco-val2017", _complete_gate_records("coco-val2017")
    )

    assert result == ReferenceHealth.FORMAT_ASSET
    assert result != ReferenceHealth.HEALTH_VERIFIED
    assert captured == [
        (
            REFERENCE_CATEGORY_VIOLATION,
            {
                "reference_id": "coco-val2017",
                "previous_state": ReferenceHealth.FORMAT_ASSET,
                "new_state": ReferenceHealth.FORMAT_ASSET,
                "reason": "FORMAT_ASSET_CANNOT_BE_HEALTH_VERIFIED",
            },
        )
    ]


def test_ut_ref_003_staleness_transition_is_audited(
    manager: ReferenceManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager.register_reference("model-reference", "MODEL_REFERENCE")
    captured = _capture_audit_events(manager, monkeypatch)
    reason = "scheduled review interval expired"

    result = manager.register_staleness_event("model-reference", reason)

    assert result == ReferenceHealth.STALE_SUSPECTED
    assert (
        manager.get_reference_health("model-reference")
        == ReferenceHealth.STALE_SUSPECTED
    )
    assert captured == [
        (
            AuditEventType.REFERENCE_HEALTH_TRANSITION,
            {
                "reference_id": "model-reference",
                "previous_state": ReferenceHealth.HEALTH_UNVERIFIED,
                "new_state": ReferenceHealth.STALE_SUSPECTED,
                "reason": reason,
            },
        )
    ]


def test_supplemental_complete_r0_r7_promotes_verified(
    manager: ReferenceManager, store: EvidenceStore
) -> None:
    manager.register_reference("verified-reference", "MODEL_REFERENCE")
    gate_records = _complete_gate_records("verified-reference")

    result = manager.attempt_health_promotion("verified-reference", gate_records)

    assert result == ReferenceHealth.HEALTH_VERIFIED
    row = store.query_reference_health("verified-reference")
    assert row is not None
    assert row["health_state"] == ReferenceHealth.HEALTH_VERIFIED
    assert row["gate_completion_record"] == gate_records
    assert row["last_verified_timestamp"]


def test_supplemental_incomplete_gates_remain_unverified(
    manager: ReferenceManager,
) -> None:
    manager.register_reference("incomplete-reference", "MODEL_REFERENCE")
    gate_records = _complete_gate_records("incomplete-reference")
    gate_records.pop("R7")

    result = manager.attempt_health_promotion(
        "incomplete-reference", gate_records
    )

    assert result == ReferenceHealth.HEALTH_UNVERIFIED
    assert result != ReferenceHealth.HEALTH_VERIFIED


def test_supplemental_audit_failure_propagates_and_rolls_back(
    manager: ReferenceManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_audit(_event_type: str, _payload: dict) -> str:
        raise AuditWriteError("simulated audit failure")

    monkeypatch.setattr(manager._audit, "append_event", fail_audit)

    with pytest.raises(AuditWriteError, match="simulated audit failure"):
        manager.register_reference("rollback-reference", "MODEL_REFERENCE")

    assert (
        manager.get_reference_health("rollback-reference")
        == ReferenceHealth.UNAVAILABLE
    )


def test_supplemental_workers_do_not_import_reference_manager() -> None:
    workers_dir = pathlib.Path(__file__).parents[2] / "assurance_system" / "workers"
    matches = [
        path
        for path in workers_dir.rglob("*.py")
        if "reference_manager" in path.read_text(encoding="utf-8")
    ]
    assert matches == []
