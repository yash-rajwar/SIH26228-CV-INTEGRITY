"""TASK-020 component acceptance and capability-contract tests."""

from __future__ import annotations

import copy
import json
import pathlib
import uuid

import pytest

from assurance_system.constants import AssessmentStatus, AuditEventType
from assurance_system.exceptions import CapabilityDeclarationError, StorageWriteError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.capability_declaration import CapabilityDeclaration
from assurance_system.supervisor.evidence_store import EvidenceStore


@pytest.fixture
def store(tmp_path: pathlib.Path):
    evidence_store = EvidenceStore(str(tmp_path / "capabilities.sqlite3"))
    yield evidence_store
    evidence_store._conn.close()


@pytest.fixture
def component(store: EvidenceStore) -> CapabilityDeclaration:
    return CapabilityDeclaration(store, AuditChainWriter(store))


def test_ut_cap_001_all_required_gaps_persist_and_are_audited(
    component: CapabilityDeclaration, store: EvidenceStore,
) -> None:
    records = component.emit_deferred_records("asset-001")
    persisted = {record["method_id"]: record for record in store.query_deferred()}

    assert set(persisted) == {
        "M07", "M03-PDQ", "M04", "M05", "M11", "TORCHSCRIPT", "SAFETENSORS",
        "TAIL_COMPLETENESS", "SYBIL_IDENTITY", "T05d", "ACTIVATION_SPACE",
        "NEURAL_CLEANSE", "B3D", "ABS", "AC",
    }
    assert sum(
        record["assessment_status"] == AssessmentStatus.DEFERRED_IN_SCOPE
        for record in persisted.values()
    ) >= 9
    assert persisted["M11"]["assessment_status"] == AssessmentStatus.REFERENCE_UNAVAILABLE
    assert persisted["TAIL_COMPLETENESS"]["assessment_status"] == "COMPLETENESS_UNAVAILABLE"
    assert persisted["M07"]["finite_battery_non_claim"] == 1
    assert "SYBIL_UNRELIABLE" in persisted["SYBIL_IDENTITY"]["non_claims"][0]
    assert len(records) == len(persisted)
    for record in records:
        restored = persisted[record["method_id"]]
        assert restored["asset_id"] == "asset-001"
        assert restored["limitations"] == record["limitations"]
        assert restored["non_claims"] == record["non_claims"]
    events = store.query_audit_trail()
    assert len(events) == len(records)
    assert all(
        event["event_type"] == AuditEventType.DEFERRED_IN_SCOPE_EMITTED
        for event in events
    )
    assert component._audit.verify_chain_integrity().intact


def test_ut_cap_002_t05d_is_a_persisted_permanent_non_claim(
    component: CapabilityDeclaration, store: EvidenceStore,
) -> None:
    component.emit_deferred_records("asset-002")
    t05d = next(
        record for record in store.query_deferred() if record["method_id"] == "T05d"
    )

    assert t05d["deferral_reason"].startswith("PERMANENT_NON_CLAIM:")
    assert "not a future deferred capability" in t05d["deferral_reason"]
    assert t05d["non_claims"][0] == (
        "T05d (clean-label poisoning) is NOT detectable under the current assessment "
        "scope; no detection claim is made for this attack class."
    )


@pytest.mark.skip(reason="BLOCKED: TASK-023 — list-deferred CLI is not implemented")
def test_ut_cap_003_list_deferred_cli() -> None:
    """CLI acceptance remains an explicit downstream integration dependency."""


def test_default_declaration_is_unavailable_with_no_advertised_methods(
    component: CapabilityDeclaration, store: EvidenceStore,
) -> None:
    declaration = component.declare_capabilities("asset-003")

    assert declaration["assessment_status"] == AssessmentStatus.UNAVAILABLE
    assert declaration["supported_capabilities"] == []
    assert declaration["limitations"]
    assert declaration["non_claims"]
    assert component.validate_declaration(declaration).valid
    assert store.query_audit_trail()[-1]["event_type"] == (
        AuditEventType.CAPABILITY_DECLARATION_EMITTED
    )
    assert store.query_deferred() == []


def test_only_explicit_bounded_operations_are_declared(
    component: CapabilityDeclaration,
) -> None:
    declaration = component.declare_capabilities(
        "asset-004", ["C3D", "M02", "M01", "M06", "M15", "C3A", "C3B"]
    )

    assert {record["method_id"] for record in declaration["supported_capabilities"]} == {
        "M01", "M02", "M06", "M15", "C3A", "C3B", "C3D",
    }
    assert all(
        record["assessment_status"] == AssessmentStatus.UNAVAILABLE
        and record["limitations"] and record["non_claims"]
        for record in declaration["supported_capabilities"]
    )
    assert all(record["assessment_status"] != "COMPLETED"
               for record in declaration["supported_capabilities"])
    assert component.validate_declaration(declaration).valid
    assert "C3C" not in {
        record["method_id"] for record in declaration["supported_capabilities"]
    }


@pytest.mark.parametrize("requested", ["M02", ["M02", "M02"], [None], {"M02": True}])
def test_malformed_requests_cannot_create_capability_events(
    component: CapabilityDeclaration, store: EvidenceStore, requested,
) -> None:
    with pytest.raises(CapabilityDeclarationError):
        component.declare_capabilities("asset-005", requested)
    assert store.query_audit_trail() == []


def test_deferred_records_conform_to_committed_schema(
    component: CapabilityDeclaration,
) -> None:
    schema_path = pathlib.Path(__file__).parents[2] / (
        "assurance_system/schema/deferred_record_v1.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    records = component.emit_deferred_records("asset-006")

    for record in records:
        assert set(record) == set(schema["required"])
        assert record["schema_version"] == schema["schema_version"]
        assert uuid.UUID(record["record_id"]).version == 4
        for key, value in record.items():
            allowed_type = schema["properties"][key]["type"]
            if allowed_type == "string":
                assert isinstance(value, str) and value.strip()
            elif allowed_type == "array":
                assert isinstance(value, list) and value
                assert all(isinstance(item, str) and item.strip() for item in value)
            else:
                assert type(value) is bool
        assert component.validate_deferred_record(record).valid


def test_schema_and_coverage_gaps_cannot_be_dropped(
    component: CapabilityDeclaration,
) -> None:
    declaration = component.declare_capabilities("asset-007", ["M02"])
    for key in declaration:
        invalid = copy.deepcopy(declaration)
        invalid.pop(key)
        assert not component.validate_declaration(invalid).valid
    invalid = copy.deepcopy(declaration)
    invalid["deferred_records"].pop()
    assert not component.validate_declaration(invalid).valid
    invalid = copy.deepcopy(declaration)
    invalid["deferred_records"][1] = copy.deepcopy(invalid["deferred_records"][0])
    assert not component.validate_declaration(invalid).valid


@pytest.mark.parametrize("asset_id", [None, "", "   ", 42])
def test_invalid_asset_id_fails_before_emission(
    component: CapabilityDeclaration, store: EvidenceStore, asset_id,
) -> None:
    with pytest.raises(CapabilityDeclarationError):
        component.emit_deferred_records(asset_id)
    with pytest.raises(CapabilityDeclarationError):
        component.declare_capabilities(asset_id)
    assert store.query_deferred() == []
    assert store.query_audit_trail() == []


def test_store_failure_propagates_without_false_emission_event(
    component: CapabilityDeclaration, store: EvidenceStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_write(_record: dict) -> str:
        raise StorageWriteError("simulated storage failure")

    monkeypatch.setattr(store, "write_deferred_record", fail_write)
    with pytest.raises(StorageWriteError, match="simulated storage failure"):
        component.emit_deferred_records("asset-008")
    assert store.query_audit_trail() == []
