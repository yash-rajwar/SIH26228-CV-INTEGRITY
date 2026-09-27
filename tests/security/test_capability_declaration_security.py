"""TASK-020 security invariants for bounded declarations and missing coverage."""

from __future__ import annotations

import ast
import copy
import pathlib

import pytest

from assurance_system.constants import AssessmentStatus, AuditEventType
from assurance_system.exceptions import AuditWriteError, CapabilityDeclarationError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.capability_declaration import CapabilityDeclaration
from assurance_system.supervisor.evidence_store import EvidenceStore


@pytest.fixture
def capability(tmp_path: pathlib.Path):
    store = EvidenceStore(str(tmp_path / "capability-security.sqlite3"))
    manager = CapabilityDeclaration(store, AuditChainWriter(store))
    try:
        yield manager, store
    finally:
        store._conn.close()


@pytest.mark.parametrize(
    "requested",
    [
        ["MALWARE_DETECTION"],
        ["MODEL_SAFETY_GUARANTEE"],
        ["COMPLETE_INTEGRITY_ASSURANCE"],
        ["INTEGRITY_PROBABILITY"],
        ["CONFIDENCE_SCORE"],
        ["M03-PDQ"],
        ["C3C"],
        ["YOLO_POSE"],
        ["YOLO_OBB"],
        ["M02", "M02"],
        [{"method_id": "M02", "assessment_status": "COMPLETED"}],
        "M02",
    ],
)
def test_unsupported_or_inflated_requests_fail_before_audit_and_write(
    capability, requested
) -> None:
    manager, store = capability

    with pytest.raises(CapabilityDeclarationError):
        manager.declare_capabilities("asset-1", requested)

    assert store.query_deferred() == []
    assert store.query_audit_trail() == []


@pytest.mark.parametrize(
    "change",
    [
        lambda record: record.update({"risk_score": 1}),
        lambda record: record.update({"aggregate_assurance": 1}),
        lambda record: record.update({"assessment_status": "CLEAN"}),
        lambda record: record.update({"assessment_status": "SAFE"}),
        lambda record: record.update({"assessment_status": "HEALTHY"}),
        lambda record: record.update({"assessment_status": "COMPLETED"}),
        lambda record: record.update({"non_claims": []}),
        lambda record: record.update({"non_claims": ["Complete integrity assured."]}),
        lambda record: record.update({"limitations": []}),
        lambda record: record.update({"finite_battery_non_claim": 0}),
        lambda record: record.update({"schema_version": "unrecognized-v2"}),
    ],
)
def test_deferred_validation_rejects_promoted_results_and_removed_non_claims(
    capability, change
) -> None:
    manager, store = capability
    record = manager.declare_capabilities("asset-1")["deferred_records"][0]
    change(record)

    assert manager.validate_deferred_record(record).valid is False
    assert store.query_deferred() == []
    assert len(store.query_audit_trail()) == 1


@pytest.mark.parametrize(
    "change",
    [
        lambda declaration: declaration.update({"confidence": 1.0}),
        lambda declaration: declaration.update({"non_claims": []}),
        lambda declaration: declaration.update({"assessment_status": "COMPLETED"}),
        lambda declaration: declaration["supported_capabilities"][0].update(
            {"assessment_status": "SAFE"}
        ),
        lambda declaration: declaration["supported_capabilities"][0].update(
            {"non_claims": []}
        ),
        lambda declaration: declaration["supported_capabilities"][0].update(
            {"method_id": "MALWARE_DETECTION"}
        ),
        lambda declaration: declaration["supported_capabilities"][0].update(
            {"raw_signal": {"risk_score": 1}}
        ),
        lambda declaration: declaration["deferred_records"].pop(),
        lambda declaration: declaration["deferred_records"][0].update(
            {"asset_id": "another-asset"}
        ),
    ],
)
def test_declaration_validation_rejects_nested_assurance_and_coverage_tampering(
    capability, change
) -> None:
    manager, _store = capability
    declaration = copy.deepcopy(manager.declare_capabilities("asset-1", ["M02"]))
    change(declaration)

    assert manager.validate_declaration(declaration).valid is False


def test_capability_scopes_never_assert_detection_or_completed_assurance(
    capability,
) -> None:
    manager, _store = capability
    declaration = manager.declare_capabilities(
        "asset-1", ["M01", "M02", "M06", "M15", "C3A", "C3B", "C3D"]
    )
    expected_non_claims = {
        "No malware detection claim is made.",
        "No model safety guarantee is established.",
        "Complete integrity assurance is not established.",
        "No probability or confidence of integrity is reported.",
    }

    for record in [declaration, *declaration["supported_capabilities"]]:
        assert record["assessment_status"] == AssessmentStatus.UNAVAILABLE
        assert expected_non_claims <= set(record["non_claims"])
        assert record["limitations"]


@pytest.mark.parametrize("operation", ["declaration", "emission"])
def test_audit_failure_propagates_without_a_successful_return(
    capability, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    manager, store = capability
    events: list[str] = []

    def unavailable_audit(event_type: str, payload: dict) -> str:
        events.append(event_type)
        raise AuditWriteError("injected append failure")

    monkeypatch.setattr(manager._audit, "append_event", unavailable_audit)

    with pytest.raises(AuditWriteError, match="injected append failure"):
        if operation == "declaration":
            manager.declare_capabilities("asset-1", ["M02"])
        else:
            manager.emit_deferred_records("asset-1")

    assert store.query_audit_trail() == []
    if operation == "declaration":
        assert events == [AuditEventType.CAPABILITY_DECLARATION_EMITTED]
        assert store.query_deferred() == []
    else:
        assert events == [AuditEventType.DEFERRED_IN_SCOPE_EMITTED]
        # Existing store and audit APIs commit separately; no batch rollback claim.
        assert len(store.query_deferred()) == 1


@pytest.mark.parametrize("fault", ["missing-field", "empty-non-claims"])
def test_schema_gate_rejects_malformed_generated_batch_before_persistence(
    capability, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    manager, store = capability
    original = manager._deferred_record

    def malformed_record(asset_id: str, spec: tuple) -> dict:
        record = original(asset_id, spec)
        if fault == "missing-field":
            record.pop("limitations")
        else:
            record["non_claims"] = []
        return record

    monkeypatch.setattr(manager, "_deferred_record", malformed_record)

    with pytest.raises(CapabilityDeclarationError):
        manager.emit_deferred_records("asset-1")

    assert store.query_deferred() == []
    assert store.query_audit_trail() == []


def test_component_has_no_artifact_execution_signing_or_network_dependency() -> None:
    root = pathlib.Path(__file__).parents[2]
    source = (
        root / "assurance_system" / "supervisor" / "capability_declaration.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    prohibited_roots = {
        "torch", "onnx", "onnxruntime", "pickle", "subprocess", "socket",
        "requests", "urllib", "http", "hmac", "cryptography",
    }
    assert all(module.split(".")[0] not in prohibited_roots for module in imported_modules)
    assert all(
        not module.startswith("assurance_system.workers")
        and module != "assurance_system.supervisor.provenance"
        for module in imported_modules
    )
    assert all(
        "supervisor.capability_declaration" not in path.read_text(encoding="utf-8")
        for path in (root / "assurance_system" / "workers").rglob("*.py")
    )
