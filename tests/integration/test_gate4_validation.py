"""Explicit Gate-4 observations; real dispatch/storage/export, no network tests.

Fixture construction uses the existing seed-pinned generators. Test-only C3
unavailability injection is distinguished from the genuine fixture observations.
"""
from __future__ import annotations

import copy
import dataclasses
import json
import pathlib
import sys
import zipfile

import pytest

from assurance_system.export.exporter import EvidenceExporter
from assurance_system.fixtures.hostile import benign, coco_geometry, onnx_path_traversal, pickle_payload, yolo_geometry
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.interpretation import C5InterpretationEngine, T05D_NON_CLAIM_TEXT
from assurance_system.supervisor.orchestrator import SupervisorOrchestrator
from assurance_system.supervisor.provenance import ProvenanceBuilder
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator
from assurance_system.workers import c2a_structural

SEED = 26228
OBSERVATIONS = pathlib.Path(__file__).resolve().parents[2] / "build/task026-gate4/observations"
CASES = {
    "FIX-008": (coco_geometry.generate, "coco_geometry_violations.json", "COCO", "M01", "COMPLETED"),
    "FIX-008-CONTROL": (benign.generate_coco, "valid_coco.json", "COCO", "M01", "COMPLETED"),
    "FIX-009-D": (yolo_geometry.generate, "yolo_detection_violations.txt", "YOLO_DETECTION", "M01", "COMPLETED"),
    "FIX-009-S": (yolo_geometry.generate_segmentation, "yolo_segmentation_violations.txt", "YOLO_SEG", "M01", "COMPLETED"),
    "FIX-001": (pickle_payload.generate_hostile_pickle, "hostile_pickle.pt", "PYTORCH", "C3D", "LOAD_BLOCKED"),
    "FIX-015": (pickle_payload.generate_benign_pytorch, "benign_pytorch.pt", "PYTORCH", "C3D", "LOAD_SUCCESS"),
    "FIX-004": (onnx_path_traversal.generate_absolute_path, "absolute_external_data.onnx", "ONNX", "C3A", "ONNX_PATH_CONTAINMENT_VIOLATION"),
    "FIX-005": (onnx_path_traversal.generate_traversal_path, "traversal_external_data.onnx", "ONNX", "C3A", "ONNX_PATH_CONTAINMENT_VIOLATION"),
    "FIX-006": (onnx_path_traversal.generate_symlink_escape, "symlink_external_data.onnx", "ONNX", "C3A", "ONNX_PATH_CONTAINMENT_VIOLATION"),
    "FIX-016": (benign.generate_onnx, "valid_minimal.onnx", "ONNX", "C3C", "STRUCTURAL_VALID"),
}


@pytest.fixture
def pipeline(tmp_path):
    store = EvidenceStore(str(tmp_path / "gate4.sqlite3"))
    audit = AuditChainWriter(store)
    temporary = tmp_path / "worker-temp"
    temporary.mkdir()
    subject = SupervisorOrchestrator(store, audit, worker_temp_dir_base=temporary, python_executable=sys.executable)
    try:
        yield subject, store, audit
    finally:
        store._conn.close()


def _asset(asset_id, path, format_name):
    return {"asset_id": asset_id, "asset_paths": [str(path.resolve())],
            "format": format_name, "is_synthetic": True,
            "contributor_metadata": [{"contributor_id": "synthetic-source-1"}]}


def _submission(tmp_path, directory, assets):
    path = tmp_path / "submission.json"
    path.write_text(json.dumps({"schema_version": "submission-manifest-v1",
                               "asset_directory": str(directory.resolve()), "assets": assets}), encoding="utf-8")
    return path


def _export_and_check(store, audit, tmp_path, asset_id):
    # No post-hoc label injection: all records come from the production pipeline.
    bundle = EvidenceExporter(store, allowed_output_directory=tmp_path).export_bundle(asset_id, f"{asset_id}.zip")
    with zipfile.ZipFile(bundle) as archive:
        documents = {name: json.loads(archive.read(name)) for name in archive.namelist()}
    evidence, findings = documents["evidence_records.json"], documents["findings.json"]
    assert evidence and findings
    assert all(record["is_synthetic"] == 1 for record in evidence + findings)
    assert all(record["coverage_gap_clean_label"] == 1 and record["limitations"] and record["non_claims"] for record in evidence + findings)
    assert all(EvidenceSchemaValidator().validate_finding(record).valid for record in findings)
    assert documents["audit_trail.json"]["chain_verification"]["intact"] is True
    assert audit.verify_chain_integrity().intact
    assert "PIPELINE_RUN_COMPLETE" in {event["event_type"] for event in store.query_audit_trail()}
    assert len(documents["capabilities.json"]["deferred_records"]) == 15
    return documents


def _record(name, value):
    OBSERVATIONS.mkdir(parents=True, exist_ok=True)
    (OBSERVATIONS / f"{name}.json").write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


@pytest.mark.parametrize("fixture_id", list(CASES))
def test_experiment_and_synthetic_export(pipeline, tmp_path, fixture_id):
    subject, store, audit = pipeline
    generator, filename, format_name, method, status = CASES[fixture_id]
    directory = tmp_path / "assets"
    manifest = generator(str(directory), SEED)
    assert manifest["seed"] == SEED and manifest["is_synthetic"] is True
    if fixture_id == "FIX-006":
        # Required setup is expressly part of the existing FIX-006 manifest.
        outside = tmp_path / "outside.bin"
        outside.write_bytes(b"synthetic-outside-data")
        (directory / "external.bin").symlink_to(outside)
    path = directory / filename
    summary = subject.run_pipeline(str(_submission(tmp_path, directory, [_asset(fixture_id, path, format_name)])))
    result = store.query_evidence(fixture_id, method)
    assert result["assessment_status"] == status
    if method == "M01":
        expected = manifest["expected_result"]
        signal = result["raw_signal"]
        expected_types = expected.get("violations_by_type", {})
        assert signal["violations_by_type"] == expected_types
        assert signal["violation_count"] == sum(expected_types.values())
        if format_name == "COCO":
            checked = len(json.loads(path.read_text(encoding="utf-8"))["annotations"])
        else:
            checked = sum(bool(line.strip()) and not line.strip().startswith("#") for line in path.read_text(encoding="utf-8").splitlines())
        assert signal["total_boxes_checked"] == checked
    if method == "C3D":
        assert result["raw_signal"]["fallback_attempted"] is False
    if fixture_id in {"FIX-004", "FIX-005", "FIX-006"}:
        assert summary.workers_dispatched == 1  # C3 containment stops the chain.
        assert store.query_evidence(fixture_id, "C3B") is None
    exported = _export_and_check(store, audit, tmp_path, fixture_id)
    assert not list(subject._worker_temp_dir_base.iterdir())
    _record(fixture_id, {"fixture_manifest": manifest, "summary": dataclasses.asdict(summary),
                         "observed": result, "exported": exported, "temp_cleanup": True})


@pytest.mark.parametrize("model_kind", ["onnx", "hostile-pickle"])
def test_int_001_002_combined_assets_complete(pipeline, tmp_path, model_kind):
    subject, store, audit = pipeline
    directory = tmp_path / "assets"
    coco = directory / "coco"
    benign.generate_coco(str(coco), SEED)
    model = directory / "model"
    if model_kind == "onnx":
        benign.generate_onnx(str(model), SEED)
        model_asset = _asset("model", model / "valid_minimal.onnx", "ONNX")
    else:
        pickle_payload.generate_hostile_pickle(str(model), SEED)
        model_asset = _asset("model", model / "hostile_pickle.pt", "PYTORCH")
    # Hostile model first proves that the later C2 asset is actually processed.
    summary = subject.run_pipeline(str(_submission(tmp_path, directory, [model_asset, _asset("data", coco / "valid_coco.json", "COCO")])))
    assert summary.assets_processed == 2 and summary.workers_dispatched == 7
    assert summary.evidence_records_written == 7 and summary.findings_written == 2
    assert summary.worker_results_rejected == 0
    if model_kind == "onnx":
        assert store.query_evidence("model", "C3A")["assessment_status"] == "COMPLETED"
        assert store.query_evidence("model", "C3B")["assessment_status"] == "COMPLETED"
        assert store.query_evidence("model", "C3C")["assessment_status"] == "STRUCTURAL_VALID"
    else:
        blocked = store.query_evidence("model", "C3D")
        assert blocked["assessment_status"] == "LOAD_BLOCKED"
        assert blocked["raw_signal"]["fallback_attempted"] is False
        assert store.query_findings("model")[0]["detection_status"] == "ANOMALY_DETECTED"
    data = store.query_evidence("data", "M01")
    assert data["assessment_status"] == "COMPLETED" and data["raw_signal"]["violation_count"] == 0
    assert store.query_findings("data")[0]["detection_status"] == "COMPLETED_STATISTICS_ONLY"
    exports = {asset_id: _export_and_check(store, audit, tmp_path, asset_id) for asset_id in ("model", "data")}
    assert not list(subject._worker_temp_dir_base.iterdir())
    _record(f"INT-{model_kind}", {"summary": dataclasses.asdict(summary), "exports": exports, "temp_cleanup": True})


def test_int_003_c3_unavailable_through_supervisor(pipeline, tmp_path, monkeypatch):
    subject, store, audit = pipeline
    directory = tmp_path / "assets"
    benign.generate_onnx(str(directory), SEED)
    collect = subject._collect_worker
    injected = []
    def inject_after_real_collection(pending):
        result = collect(pending)
        if result["worker_id"] == "COMP-W-C3B":
            result["assessment_status"] = "UNAVAILABLE"
            result["raw_signal"] = {"comparison_result": "UNAVAILABLE"}
            result["limitations"] = ["Test-only C3 unavailability injection."]
            injected.append(result)
        return result
    monkeypatch.setattr(subject, "_collect_worker", inject_after_real_collection)
    summary = subject.run_pipeline(str(_submission(tmp_path, directory, [_asset("unavailable", directory / "valid_minimal.onnx", "ONNX")])))
    assert len(injected) == 1 and summary.worker_results_rejected == 0
    assert store.query_evidence("unavailable", "C3B")["assessment_status"] == "UNAVAILABLE"
    finding = store.query_findings("unavailable")[0]
    assert finding["detection_status"] == "UNAVAILABLE"
    assert finding["analyst_disposition_prompt"] == "UNAVAILABLE_NO_DECISION"
    _record("INT-unavailable", {"test_only_injection": True, "summary": dataclasses.asdict(summary),
                               "exported": _export_and_check(store, audit, tmp_path, "unavailable")})


@pytest.mark.parametrize("fixture_id", ["FIX-008", "FIX-009-D", "FIX-009-S"])
def test_repro_001_same_annotations_same_violations(tmp_path, fixture_id):
    generator, filename, format_name, _, _ = CASES[fixture_id]
    generator(str(tmp_path), SEED)
    task = {"schema_version": "worker-input-v1", "task": "C2A_STRUCTURAL",
            "asset_paths": [str(tmp_path / filename)], "asset_directory": str(tmp_path),
            "format": format_name, "task_variant": format_name if format_name.startswith("YOLO") else None,
            "resource_limits": {}}
    first, second = c2a_structural.run_assessment(task), c2a_structural.run_assessment(task)
    assert first["assessment_status"] == second["assessment_status"] == "COMPLETED"
    assert first["raw_signal"]["violations"] == second["raw_signal"]["violations"]
    assert first["raw_signal"]["violations"]


@pytest.mark.parametrize("worker,status,signal", [
    ("COMP-W-C2A", "COMPLETED", {"violation_count": 0}),
    ("COMP-W-C2A", "COMPLETED", {"violation_count": 9}),
    ("COMP-W-C2C", "COMPLETED", {"hhi": 1.0}),
    ("COMP-W-C3B", "COMPLETED", {"comparison_result": "MATCH"}),
    ("COMP-W-C3B", "UNAVAILABLE", {"comparison_result": "UNAVAILABLE"}),
])
def test_repro_004_same_semantic_finding(worker, status, signal):
    evidence = [{"worker_id": worker, "assessment_status": status, "raw_signal": signal,
                 "limitations": ["Synthetic bounded evidence."], "non_claims": ["No intent established."], "is_synthetic": True}]
    before = copy.deepcopy(evidence)
    arguments = {"asset_id": "repro-004", "method_id": "repro-004", "evidence_records": evidence,
                 "c4_binding": None, "reference_health": "UNAVAILABLE", "access_mode": "BLACK_BOX"}
    engine = C5InterpretationEngine()
    first, second = engine.produce_finding(**arguments), engine.produce_finding(**arguments)
    assert first["finding_id"] != second["finding_id"]
    assert evidence == before
    # These are the ONLY exclusions: no semantic field or nested ID is stripped.
    for finding in (first, second):
        assert EvidenceSchemaValidator().validate_finding(finding).valid
        assert T05D_NON_CLAIM_TEXT in finding["non_claims"]
        assert finding["coverage_gap_clean_label"] == 1
    assert {key: value for key, value in first.items() if key not in {"finding_id", "created_at"}} == {
        key: value for key, value in second.items() if key not in {"finding_id", "created_at"}}


def test_repro_005_identical_canonical_bytes():
    record = {"z": [1, {"nested": "é"}], "a": {"value": False, "missing": None}}
    first, second = ProvenanceBuilder.canonicalize(record), ProvenanceBuilder.canonicalize(record)
    assert first == second == json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
