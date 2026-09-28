"""TASK-026-A vertical-slice contract tests.

These tests exercise the real supervisor, persistence, interpretation, CLI, and
export boundaries.  COCO scenarios retain a named HOST-CAP-001 skip when the
approved environment has no pycocotools installation; no parser substitute is
used because that would bypass the production worker boundary.
"""

from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import sys
import zipfile
from typing import Any

import pytest

from assurance_system.fixtures.hostile.coco_geometry import (
    generate as generate_fix_008,
    generate_valid as generate_valid_coco,
)
from assurance_system.fixtures.hostile.pickle_payload import (
    generate_hostile_pickle,
)
from assurance_system.fixtures.hostile.unavailable_injector import (
    inject_unavailable_at_c2_output,
    inject_unavailable_at_c3_output,
    inject_unavailable_at_c4_output,
    inject_unavailable_at_ingestion,
)
from assurance_system.interfaces.cli import AssuranceCLI
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.capability_declaration import CapabilityDeclaration
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.interpretation import C5InterpretationEngine
from assurance_system.supervisor.orchestrator import SupervisorOrchestrator
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator


_SEED = 26228
_PROHIBITED_SCORE_FIELDS = {
    "risk_score",
    "confidence_score",
    "trust_score",
    "safety_score",
}
_PROHIBITED_POSITIVE_STATES = {
    "CLEAN",
    "SAFE",
    "HEALTHY",
    "WITHIN_EXPECTED_PARAMETERS",
}
_EXPECTED_DEFERRED_METHOD_IDS = {
    "M07",
    "M03-PDQ",
    "M04",
    "M05",
    "M11",
    "TORCHSCRIPT",
    "SAFETENSORS",
    "TAIL_COMPLETENESS",
    "SYBIL_IDENTITY",
    "T05d",
    "ACTIVATION_SPACE",
    "NEURAL_CLEANSE",
    "B3D",
    "ABS",
    "AC",
}
_EXPECTED_BUNDLE_FILES = {
    "manifest.json",
    "findings.json",
    "evidence_records.json",
    "audit_trail.json",
    "provenance.json",
    "capabilities.json",
}


@pytest.fixture
def store(tmp_path: pathlib.Path):
    evidence_store = EvidenceStore(str(tmp_path / "vertical-slice.sqlite3"))
    try:
        yield evidence_store
    finally:
        evidence_store._conn.close()


def _orchestrator(
    store: EvidenceStore, tmp_path: pathlib.Path
) -> SupervisorOrchestrator:
    worker_directory = tmp_path / "worker-temporaries"
    worker_directory.mkdir(exist_ok=True)
    return SupervisorOrchestrator(
        store,
        AuditChainWriter(store),
        worker_temp_dir_base=worker_directory,
        python_executable=sys.executable,
    )


def _manifest(
    tmp_path: pathlib.Path,
    *,
    asset_id: str,
    asset_directory: pathlib.Path,
    asset_paths: list[pathlib.Path],
    format_name: str,
    is_synthetic: bool = True,
    contributor_metadata: list[dict[str, str]] | None = None,
) -> pathlib.Path:
    manifest_path = tmp_path / f"{asset_id}-submission.json"
    asset: dict[str, Any] = {
        "asset_id": asset_id,
        "asset_paths": [str(path.resolve()) for path in asset_paths],
        "format": format_name,
        "is_synthetic": is_synthetic,
    }
    if contributor_metadata is not None:
        asset["contributor_metadata"] = contributor_metadata
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "submission-manifest-v1",
                "asset_directory": str(asset_directory.resolve()),
                "assets": [asset],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return manifest_path


def _require_pycocotools() -> None:
    if importlib.util.find_spec("pycocotools") is None:
        pytest.skip(
            "BLOCKED: HOST-CAP-001 — pycocotools is not installed in the "
            "approved repository-local environment"
        )


def _assert_no_prohibited_score_fields(value: Any) -> None:
    if isinstance(value, dict):
        assert _PROHIBITED_SCORE_FIELDS.isdisjoint(value)
        for nested in value.values():
            _assert_no_prohibited_score_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_prohibited_score_fields(nested)


def _assert_no_positive_state(value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_positive_state(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_positive_state(nested)
    elif isinstance(value, str):
        assert value not in _PROHIBITED_POSITIVE_STATES


class _CLIConfig:
    @staticmethod
    def load() -> dict[str, Any]:
        return {"system": {"evidence_store": {"path": "unused-test-store.db"}}}


def _cli(store: EvidenceStore, output: io.StringIO) -> AssuranceCLI:
    return AssuranceCLI(
        config_loader=_CLIConfig(),
        evidence_store_factory=lambda _path: store,
        stdout=output,
        stderr=output,
    )


def test_vs_001_valid_coco_submission_completes_vertical_slice(
    store: EvidenceStore, tmp_path: pathlib.Path
) -> None:
    """VS-001: a valid COCO fixture reaches evidence, C5, and audit storage."""

    _require_pycocotools()
    fixture_directory = tmp_path / "valid-coco"
    generate_valid_coco(str(fixture_directory), _SEED)
    annotation_path = fixture_directory / "valid_coco.json"
    source = json.loads(annotation_path.read_text(encoding="utf-8"))
    manifest_path = _manifest(
        tmp_path,
        asset_id="vs-001-valid-coco",
        asset_directory=fixture_directory,
        asset_paths=[annotation_path],
        format_name="COCO",
        contributor_metadata=[{"contributor_id": "synthetic-source-1"}],
    )

    summary = _orchestrator(store, tmp_path).run_pipeline(str(manifest_path))

    c2a = store.query_evidence("vs-001-valid-coco", "M01")
    assert c2a is not None
    assert c2a["assessment_status"] == "COMPLETED"
    assert c2a["raw_signal"]["violation_count"] == 0
    # The frozen worker contract represents all-box coverage with exact counts,
    # not a new all_boxes_processed output field.
    all_boxes_processed = c2a["raw_signal"]["total_boxes_checked"] == len(
        source["annotations"]
    )
    assert all_boxes_processed is True

    findings = store.query_findings("vs-001-valid-coco")
    assert len(findings) == 1
    finding = findings[0]
    # C2C is deliberately statistics-only, so the authoritative C5 vocabulary
    # uses this bounded state rather than the stale packet alias.
    assert finding["detection_status"] == "COMPLETED_STATISTICS_ONLY"
    assert finding["interpretation_status"] == "STATISTICS_REPORTED"
    assert finding["analyst_disposition_prompt"] == "ACCEPT_WITH_CONTEXT"
    assert finding["limitations"]
    assert finding["non_claims"]
    assert finding["coverage_gap_clean_label"] == 1
    _assert_no_prohibited_score_fields(finding)

    event_types = [event["event_type"] for event in store.query_audit_trail()]
    assert "PIPELINE_RUN_START" in event_types
    assert "EVIDENCE_RECORD_WRITTEN" in event_types
    assert "FINDING_WRITTEN" in event_types
    assert "PIPELINE_RUN_COMPLETE" in event_types
    assert summary.evidence_records_written == 4
    assert summary.findings_written == 1


def test_vs_002_fix_008_preserves_all_geometry_violations(
    store: EvidenceStore, tmp_path: pathlib.Path
) -> None:
    """VS-002: FIX-008 detects every seeded all-box geometry violation."""

    _require_pycocotools()
    fixture_directory = tmp_path / "fix-008"
    fixture_manifest = generate_fix_008(str(fixture_directory), _SEED)
    annotation_path = fixture_directory / "coco_geometry_violations.json"
    source = json.loads(annotation_path.read_text(encoding="utf-8"))
    manifest_path = _manifest(
        tmp_path,
        asset_id="vs-002-fix-008",
        asset_directory=fixture_directory,
        asset_paths=[annotation_path],
        format_name="COCO",
        contributor_metadata=[{"contributor_id": "synthetic-source-1"}],
    )

    _orchestrator(store, tmp_path).run_pipeline(str(manifest_path))

    c2a = store.query_evidence("vs-002-fix-008", "M01")
    assert c2a is not None
    expected = fixture_manifest["expected_result"]
    signal = c2a["raw_signal"]
    assert signal["violation_count"] == expected["violation_count"]
    assert signal["violations_by_type"] == expected["violations_by_type"]
    assert signal["total_boxes_checked"] == len(source["annotations"])

    finding = store.query_findings("vs-002-fix-008")[0]
    assert finding["detection_status"] == "ANOMALY_DETECTED"
    assert finding["interpretation_status"] == "REQUIRES_INVESTIGATION"
    assert finding["analyst_disposition_prompt"] == "ESCALATE"
    assert finding["anomaly_not_malicious_non_claim"] == 1
    assert any(
        "does not establish malicious intent" in statement
        for statement in finding["non_claims"]
    )
    _assert_no_prohibited_score_fields(finding)


def test_vs_003_fix_001_hostile_pickle_is_blocked_without_fallback(
    store: EvidenceStore, tmp_path: pathlib.Path
) -> None:
    """VS-003: the real C3 worker chain blocks FIX-001 and C5 escalates."""

    fixture_directory = tmp_path / "fix-001"
    fixture_manifest = generate_hostile_pickle(str(fixture_directory), _SEED)
    model_path = pathlib.Path(fixture_manifest["path"])
    manifest_path = _manifest(
        tmp_path,
        asset_id="vs-003-fix-001",
        asset_directory=fixture_directory,
        asset_paths=[model_path],
        format_name="PYTORCH",
    )

    _orchestrator(store, tmp_path).run_pipeline(str(manifest_path))

    c3d = store.query_evidence("vs-003-fix-001", "C3D")
    assert c3d is not None
    assert c3d["assessment_status"] == "LOAD_BLOCKED"
    assert c3d["raw_signal"]["fallback_attempted"] is False
    finding = store.query_findings("vs-003-fix-001")[0]
    assert finding["detection_status"] == "ANOMALY_DETECTED"
    assert finding["interpretation_status"] == "REQUIRES_INVESTIGATION"
    assert finding["analyst_disposition_prompt"] == "ESCALATE"
    assert finding["anomaly_not_malicious_non_claim"] == 1
    assert any(
        "does not establish malicious intent" in statement
        for statement in finding["non_claims"]
    )
    for prohibited_claim in ("CONFIRMED_MALICIOUS", "PROVEN_ATTACK"):
        assert prohibited_claim not in json.dumps(finding, sort_keys=True)
    _assert_no_prohibited_score_fields(finding)


def test_vs_004_unavailable_propagates_at_every_declared_layer() -> None:
    """VS-004: FIX-013 failures remain UNAVAILABLE through actual C5 logic."""

    ingestion = inject_unavailable_at_ingestion(
        {"schema_version": "worker-input-v1", "task": "SYNTHETIC"}
    )
    c2 = inject_unavailable_at_c2_output()
    c3 = inject_unavailable_at_c3_output()
    c4 = inject_unavailable_at_c4_output()
    injected_records = {
        "INGESTION": {
            **c2,
            "worker_id": "COMP-INGEST-SYNTHETIC",
            "assessment_status": ingestion["injected_assessment_status"],
            "limitations": ["Synthetic ingestion unavailability was injected."],
            "non_claims": ["No ingestion success conclusion is available."],
        },
        "C2": c2,
        "C3": c3,
        "C4": {
            **c3,
            "worker_id": "COMP-C4-SYNTHETIC",
            "assessment_status": c4["signing_status"],
            "limitations": list(c4["limitations"]),
            "non_claims": list(c4["non_claims"]),
        },
        "C5": {
            **c2,
            "worker_id": "COMP-C5-SYNTHETIC",
        },
    }
    engine = C5InterpretationEngine(EvidenceSchemaValidator())

    for layer, record in injected_records.items():
        finding = engine.produce_finding(
            asset_id=f"fix-013-{layer.casefold()}",
            method_id="FIX-013",
            evidence_records=[record],
            c4_binding=c4 if layer == "C4" else None,
            reference_health="UNAVAILABLE",
            access_mode="UNAVAILABLE",
        )
        assert finding["detection_status"] == "UNAVAILABLE", layer
        assert finding["interpretation_status"] == "UNAVAILABLE", layer
        assert finding["analyst_disposition_prompt"] == (
            "UNAVAILABLE_NO_DECISION"
        ), layer
        assert finding["limitations"], layer
        assert finding["non_claims"], layer
        assert set(record["limitations"]).issubset(finding["limitations"])
        assert set(record["non_claims"]).issubset(finding["non_claims"])
        _assert_no_positive_state(finding)
        _assert_no_prohibited_score_fields(finding)


def test_vs_005_capability_declaration_persists_every_deferred_record(
    store: EvidenceStore,
) -> None:
    """VS-005: COMP-CAP persists explicit reasons and bounded scope notes."""

    records = CapabilityDeclaration(
        store, AuditChainWriter(store)
    ).emit_deferred_records("vs-005-capabilities")

    assert {record["method_id"] for record in records} == (
        _EXPECTED_DEFERRED_METHOD_IDS
    )
    persisted = store.query_deferred()
    declared_by_id = {record["record_id"]: record for record in records}
    assert {record["record_id"] for record in persisted} == set(declared_by_id)
    for record in persisted:
        declared = declared_by_id[record["record_id"]]
        for field in (
            "schema_version",
            "asset_id",
            "method_id",
            "assessment_status",
            "deferral_reason",
            "limitations",
            "non_claims",
        ):
            assert record[field] == declared[field]
        assert record["finite_battery_non_claim"] == int(
            declared["finite_battery_non_claim"]
        )
        assert record["created_at"]
        assert record["deferral_reason"]
        # The frozen deferred schema expresses the packet's requested scope note
        # through non-empty limitations and non-claims; it has no scope_note key.
        assert record["limitations"]
        assert record["non_claims"]
        assert record["assessment_status"] in {
            "DEFERRED_IN_SCOPE",
            "REFERENCE_UNAVAILABLE",
            "COMPLETENESS_UNAVAILABLE",
        }
        _assert_no_positive_state(record)
        _assert_no_prohibited_score_fields(record)


def test_vs_006_cli_list_deferred_displays_complete_records(
    store: EvidenceStore,
) -> None:
    """VS-006: the real CLI exposes every complete deferred record."""

    expected = CapabilityDeclaration(
        store, AuditChainWriter(store)
    ).emit_deferred_records("vs-006-cli")
    output = io.StringIO()

    assert _cli(store, output).run(["list-deferred"]) == 0

    rendered = output.getvalue()
    records = json.loads(rendered)
    assert {record["method_id"] for record in records} == (
        _EXPECTED_DEFERRED_METHOD_IDS
    )
    assert records == store.query_deferred()
    assert {record["record_id"] for record in records} == {
        record["record_id"] for record in expected
    }
    assert all(record["deferral_reason"] for record in records)
    assert all(record["limitations"] for record in records)
    assert all(record["non_claims"] for record in records)
    _assert_no_positive_state(records)
    _assert_no_prohibited_score_fields(records)


def test_vs_007_cli_export_preserves_unavailable_and_deferred_records(
    store: EvidenceStore,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """VS-007: CLI export preserves fail-closed and deferred state verbatim."""

    asset_directory = tmp_path / "missing-model"
    asset_directory.mkdir()
    missing_model = asset_directory / "missing.pt"
    manifest_path = _manifest(
        tmp_path,
        asset_id="vs-007-export",
        asset_directory=asset_directory,
        asset_paths=[missing_model],
        format_name="PYTORCH",
    )
    _orchestrator(store, tmp_path).run_pipeline(str(manifest_path))
    finding_before = store.query_findings("vs-007-export")
    deferred_before = [
        record
        for record in store.query_deferred()
        if record["asset_id"] == "vs-007-export"
    ]
    assert finding_before[0]["detection_status"] == "UNAVAILABLE"
    assert deferred_before

    monkeypatch.chdir(tmp_path)
    output = io.StringIO()
    assert _cli(store, output).run(
        [
            "export-bundle",
            "--asset-id",
            "vs-007-export",
            "--output",
            "vertical-slice.zip",
        ]
    ) == 0

    bundle_path = tmp_path / output.getvalue().strip()
    with zipfile.ZipFile(bundle_path, "r") as archive:
        assert set(archive.namelist()) == _EXPECTED_BUNDLE_FILES
        findings = json.loads(archive.read("findings.json").decode("utf-8"))
        evidence = json.loads(
            archive.read("evidence_records.json").decode("utf-8")
        )
        capabilities = json.loads(
            archive.read("capabilities.json").decode("utf-8")
        )

    assert findings == finding_before
    assert findings[0]["detection_status"] == "UNAVAILABLE"
    assert capabilities["deferred_records"] == deferred_before
    assert all(
        record["assessment_status"]
        in {
            "DEFERRED_IN_SCOPE",
            "REFERENCE_UNAVAILABLE",
            "COMPLETENESS_UNAVAILABLE",
        }
        for record in capabilities["deferred_records"]
    )
    assert any(
        record["assessment_status"] in {"ASSESSMENT_ERROR", "UNAVAILABLE"}
        for record in evidence
    )
    _assert_no_prohibited_score_fields(
        {
            "findings": findings,
            "evidence": evidence,
            "capabilities": capabilities,
        }
    )

