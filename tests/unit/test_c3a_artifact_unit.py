"""UT-C3A-001 through UT-C3A-007 and security boundaries."""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

from assurance_system.constants import AssessmentStatus, PF_002_NON_CLAIM
from assurance_system.fixtures.hostile import benign, onnx_path_traversal
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator
from assurance_system.workers import c3a_artifact_unit


ONNX_AVAILABLE = importlib.util.find_spec("onnx") is not None
ONNX_SKIP_REASON = "BLOCKED: HOST-CAP-003 — onnx not installed"


def _task(model_path: pathlib.Path, asset_directory: pathlib.Path, format_name: str):
    return {
        "schema_version": "worker-input-v1",
        "task": "COMP-W-C3A",
        "asset_paths": [str(model_path)],
        "format": format_name,
        "asset_directory": str(asset_directory),
        "artifact_unit_definition_id": "UNAVAILABLE",
        "resource_limits": {},
        "identity_quality": "UNAVAILABLE",
    }


def _representative_outputs(tmp_path: pathlib.Path, monkeypatch):
    pytorch_path = tmp_path / "model.PTH"
    pytorch_path.write_bytes(b"not-loaded-by-c3a")
    onnx_path = tmp_path / "model.onnx"
    onnx_path.write_bytes(b"header-not-parsed-without-onnx")

    def unavailable():
        raise ImportError("onnx unavailable for test")

    monkeypatch.setattr(c3a_artifact_unit, "_load_onnx_module", unavailable)
    return [
        c3a_artifact_unit.run_assessment(
            _task(pytorch_path, tmp_path, "PyTorch")
        ),
        c3a_artifact_unit.run_assessment(
            _task(pytorch_path, tmp_path, "TorchScript")
        ),
        c3a_artifact_unit.run_assessment(_task(onnx_path, tmp_path, "ONNX")),
        c3a_artifact_unit.run_assessment(
            {"schema_version": "not-worker-input-v1"}
        ),
    ]


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3a_001_valid_onnx_without_external_data(tmp_path):
    benign.generate_onnx(str(tmp_path), seed=42)
    model_path = tmp_path / "valid_minimal.onnx"

    result = c3a_artifact_unit.run_assessment(_task(model_path, tmp_path, "ONNX"))

    assert result["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
    artifact_unit = result["raw_signal"]["artifact_unit"]
    assert artifact_unit["main_file"] == str(model_path.resolve())
    assert artifact_unit["external_files"] == []
    assert artifact_unit["artifact_unit_definition_id"] == "UNAVAILABLE"


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3a_002_valid_onnx_with_internal_external_data(tmp_path):
    model_path = tmp_path / "external_data.onnx"
    data_path = tmp_path / "weights.bin"
    onnx_path_traversal._write_external_data_model(model_path, "weights.bin")
    data_path.write_bytes(b"\x00\x00\x80?")

    result = c3a_artifact_unit.run_assessment(_task(model_path, tmp_path, "ONNX"))

    assert result["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
    assert result["raw_signal"]["artifact_unit"]["external_files"] == [
        str(data_path.resolve())
    ]
    assert result["raw_signal"]["artifact_unit"][
        "artifact_unit_definition_id"
    ] == "UNAVAILABLE"


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3a_003_fix_004_absolute_path_is_rejected(tmp_path):
    onnx_path_traversal.generate_absolute_path(str(tmp_path), seed=42)
    model_path = tmp_path / "absolute_external_data.onnx"

    result = c3a_artifact_unit.run_assessment(_task(model_path, tmp_path, "ONNX"))

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"][0]["reason"] == "ABSOLUTE_PATH"


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3a_004_fix_005_traversal_is_rejected(tmp_path):
    onnx_path_traversal.generate_traversal_path(str(tmp_path), seed=42)
    model_path = tmp_path / "traversal_external_data.onnx"

    result = c3a_artifact_unit.run_assessment(_task(model_path, tmp_path, "ONNX"))

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"][0]["reason"] == "TRAVERSAL_PATTERN"


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3a_005_fix_006_symlink_escape_is_rejected(tmp_path):
    asset_directory = tmp_path / "assets"
    outside_directory = tmp_path / "outside"
    asset_directory.mkdir()
    outside_directory.mkdir()
    onnx_path_traversal.generate_symlink_escape(str(asset_directory), seed=42)
    outside_file = outside_directory / "external.bin"
    outside_file.write_bytes(b"outside")
    try:
        (asset_directory / "external.bin").symlink_to(outside_file)
    except (NotImplementedError, OSError):
        pytest.skip("BLOCKED: host symlink creation unavailable")

    model_path = asset_directory / "symlink_external_data.onnx"
    result = c3a_artifact_unit.run_assessment(
        _task(model_path, asset_directory, "ONNX")
    )

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"][0]["reason"] == "SYMLINK_ESCAPE"


def test_ut_c3a_006_access_mode_is_non_null_everywhere(tmp_path, monkeypatch):
    for result in _representative_outputs(tmp_path, monkeypatch):
        assert isinstance(result["access_mode"], str)
        assert result["access_mode"]
        assert result["coverage_gap_clean_label"] is True
        assert EvidenceSchemaValidator().validate_worker_output(
            result, "C3A_ARTIFACT_UNIT"
        ).valid is True


def test_ut_c3a_007_pf_002_fields_are_present_everywhere(tmp_path, monkeypatch):
    for result in _representative_outputs(tmp_path, monkeypatch):
        assert result["pf_002_non_claim"] == PF_002_NON_CLAIM
        assert result["hash_match_not_safe"] is True
        assert result["hash_match_not_semantically_equivalent"] is True
        assert result["hash_match_not_causal_execution_proof"] is True


def test_outside_onnx_model_is_rejected_before_import_or_read(tmp_path, monkeypatch):
    asset_directory = tmp_path / "assets"
    outside_directory = tmp_path / "outside"
    asset_directory.mkdir()
    outside_directory.mkdir()
    outside_model = outside_directory / "model.onnx"
    outside_model.write_bytes(b"must-not-be-read")

    def forbidden_import():
        raise AssertionError("ONNX import occurred before containment rejection")

    monkeypatch.setattr(c3a_artifact_unit, "_load_onnx_module", forbidden_import)
    result = c3a_artifact_unit.run_assessment(
        _task(outside_model, asset_directory, "ONNX")
    )

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"][0]["reason"] == (
        "MODEL_FILE_OUTSIDE_ASSET_DIR"
    )


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_missing_external_file_is_artifact_unit_ambiguous(tmp_path):
    model_path = tmp_path / "missing_external.onnx"
    onnx_path_traversal._write_external_data_model(model_path, "missing.bin")

    result = c3a_artifact_unit.run_assessment(_task(model_path, tmp_path, "ONNX"))

    assert result["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
    assert "EXTERNAL_FILE_MISSING:missing.bin" in result["raw_signal"]["reason"]


def test_onnx_unavailable_returns_assessment_error(tmp_path, monkeypatch):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"contained")

    def unavailable():
        raise ImportError("not installed")

    monkeypatch.setattr(c3a_artifact_unit, "_load_onnx_module", unavailable)
    result = c3a_artifact_unit.run_assessment(_task(model_path, tmp_path, "ONNX"))

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "ONNX_UNAVAILABLE: HOST-CAP-003"


def test_pytorch_uses_frozen_single_file_definition_without_loading(tmp_path):
    model_path = tmp_path / "model.PT"
    model_path.write_bytes(b"opaque-untrusted-model")

    result = c3a_artifact_unit.run_assessment(
        _task(model_path, tmp_path, "PyTorch")
    )

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["artifact_unit_id"] == "pytorch-single-file-v1"
    assert result["raw_signal"]["artifact_unit"] == {
        "main_file": str(model_path.resolve()),
        "external_files": [],
        "artifact_unit_definition_id": "pytorch-single-file-v1",
    }


def test_pytorch_wrong_suffix_is_unsupported(tmp_path):
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"opaque")

    result = c3a_artifact_unit.run_assessment(
        _task(model_path, tmp_path, "PyTorch")
    )

    assert result["assessment_status"] == AssessmentStatus.UNSUPPORTED


def test_torchscript_remains_deferred_in_scope(tmp_path):
    model_path = tmp_path / "model.ts"
    model_path.write_bytes(b"opaque")

    result = c3a_artifact_unit.run_assessment(
        _task(model_path, tmp_path, "TorchScript")
    )

    assert result["assessment_status"] == AssessmentStatus.DEFERRED_IN_SCOPE
    assert result["artifact_unit_id"] == "UNAVAILABLE"
