"""TASK-016 tests for the containment-first ONNX structural validator."""

from __future__ import annotations

import ast
import builtins
import importlib.util
import pathlib
import types

import pytest

from assurance_system.constants import AssessmentStatus, PF_002_NON_CLAIM
from assurance_system.fixtures.hostile import benign, onnx_path_traversal
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator
from assurance_system.workers import c3a_artifact_unit, c3c_onnx_structural


ONNX_AVAILABLE = importlib.util.find_spec("onnx") is not None
ONNX_SKIP_REASON = "BLOCKED: HOST-CAP-003 — onnx not installed"
PROHIBITED_OUTPUT_FIELDS = {
    "risk_score",
    "aggregate_assurance",
    "compromise_probability",
    "threat_score",
    "malicious_probability",
    "confidence_score",
    "trust_score",
    "safety_score",
}


def _task(model_path: pathlib.Path, asset_directory: pathlib.Path) -> dict:
    return {
        "schema_version": "worker-input-v1",
        "task": "COMP-W-C3C",
        "asset_paths": [str(model_path)],
        "format": "ONNX",
        "asset_directory": str(asset_directory),
        "artifact_unit_definition_id": "UNAVAILABLE",
        "resource_limits": {},
        "identity_quality": "UNAVAILABLE",
    }


class _FakeField:
    TYPE_MESSAGE = 11
    LABEL_REPEATED = 3

    def __init__(self, *, repeated: bool):
        self.type = self.TYPE_MESSAGE
        self.label = self.LABEL_REPEATED if repeated else 1


class _FakeTensor:
    DESCRIPTOR = types.SimpleNamespace(full_name="onnx.TensorProto")

    def __init__(self, location: str):
        self.name = "initializer"
        self.data_location = 1
        self.external_data = [
            types.SimpleNamespace(key="location", value=location)
        ]


class _FakeModel:
    DESCRIPTOR = types.SimpleNamespace(full_name="onnx.ModelProto")

    def __init__(self, external_reference: str | None = None):
        self.opset_import = [types.SimpleNamespace(version=17)]
        self.graph = types.SimpleNamespace(
            node=[types.SimpleNamespace()],
            input=[types.SimpleNamespace(name="input")],
            output=[types.SimpleNamespace(name="output")],
        )
        self._fields = []
        if external_reference is not None:
            self._fields = [
                (_FakeField(repeated=True), [_FakeTensor(external_reference)])
            ]

    def ListFields(self):
        return self._fields


def _fake_onnx(
    model: _FakeModel,
    *,
    load_error: Exception | None = None,
    checker_error: Exception | None = None,
):
    checker_calls = []

    def load(path, *, load_external_data):
        assert isinstance(path, str)
        assert load_external_data is False
        if load_error is not None:
            raise load_error
        return model

    def check_model(candidate):
        checker_calls.append(candidate)
        if checker_error is not None:
            raise checker_error

    return types.SimpleNamespace(
        TensorProto=types.SimpleNamespace(EXTERNAL=1),
        load=load,
        checker=types.SimpleNamespace(check_model=check_model),
        checker_calls=checker_calls,
    )


def _run_with_fake_onnx(tmp_path, monkeypatch, fake_onnx):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"opaque-test-placeholder")
    monkeypatch.setattr(
        c3c_onnx_structural, "_load_onnx_module", lambda: fake_onnx
    )
    return c3c_onnx_structural.run_assessment(
        _task(model_path, tmp_path)
    )


def _find_prohibited_fields(value) -> set[str]:
    found = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in PROHIBITED_OUTPUT_FIELDS:
                found.add(key)
            found.update(_find_prohibited_fields(nested))
    elif isinstance(value, (list, tuple)):
        for nested in value:
            found.update(_find_prohibited_fields(nested))
    return found


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3c_001_valid_onnx(tmp_path):
    benign.generate_onnx(str(tmp_path), seed=42)
    model_path = tmp_path / "valid_minimal.onnx"

    result = c3c_onnx_structural.run_assessment(_task(model_path, tmp_path))

    assert result["assessment_status"] == AssessmentStatus.STRUCTURAL_VALID
    assert result["raw_signal"]["structural_status"] == (
        AssessmentStatus.STRUCTURAL_VALID
    )


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3c_002_fix_004_absolute_external_path(tmp_path):
    onnx_path_traversal.generate_absolute_path(str(tmp_path), seed=42)
    model_path = tmp_path / "absolute_external_data.onnx"

    result = c3c_onnx_structural.run_assessment(_task(model_path, tmp_path))

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"][0]["reason"] == "ABSOLUTE_PATH"


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3c_003_fix_005_traversal(tmp_path):
    onnx_path_traversal.generate_traversal_path(str(tmp_path), seed=42)
    model_path = tmp_path / "traversal_external_data.onnx"

    result = c3c_onnx_structural.run_assessment(_task(model_path, tmp_path))

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"][0]["reason"] == (
        "TRAVERSAL_PATTERN"
    )


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3c_004_malformed_protobuf_is_structural_invalid(tmp_path):
    """MVP text says ASSESSMENT_ERROR; Architecture + Technical Specification
    require STRUCTURAL_INVALID; architecture authority is followed.
    """

    model_path = tmp_path / "malformed.onnx"
    model_path.write_bytes(b"not-an-onnx-protobuf")

    result = c3c_onnx_structural.run_assessment(_task(model_path, tmp_path))

    assert result["assessment_status"] == AssessmentStatus.STRUCTURAL_INVALID
    assert result["raw_signal"]["structural_status"] == (
        AssessmentStatus.STRUCTURAL_INVALID
    )


def test_ut_c3c_005_pf_002_and_ef_004_non_claims(tmp_path, monkeypatch):
    fake_onnx = _fake_onnx(_FakeModel())
    result = _run_with_fake_onnx(tmp_path, monkeypatch, fake_onnx)

    assert result["assessment_status"] == AssessmentStatus.STRUCTURAL_VALID
    assert result["pf_002_non_claim"] == PF_002_NON_CLAIM
    assert result["hash_match_not_safe"] is True
    assert result["hash_match_not_semantically_equivalent"] is True
    assert result["hash_match_not_causal_execution_proof"] is True
    assert result["ef_004_non_claim"] == (
        c3c_onnx_structural.EF_004_NON_CLAIM
    )
    assert result["raw_signal"]["ef_004_non_claim"] == (
        c3c_onnx_structural.EF_004_NON_CLAIM
    )
    assert result["coverage_gap_clean_label"] is True
    assert result["access_mode"] == "BLACK_BOX"
    assert result["limitations"]
    assert result["non_claims"]
    assert result["assessment_status"] not in {"SAFE", "CLEAN", "HEALTHY"}
    assert _find_prohibited_fields(result) == set()


def test_onnx_unavailable_fails_closed(tmp_path, monkeypatch):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"contained")

    def unavailable():
        raise ImportError("not installed")

    monkeypatch.setattr(c3c_onnx_structural, "_load_onnx_module", unavailable)
    result = c3c_onnx_structural.run_assessment(_task(model_path, tmp_path))

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["assessment_status"] != AssessmentStatus.STRUCTURAL_VALID
    assert result["error_detail"] == "ONNX_UNAVAILABLE: HOST-CAP-003"
    assert result["access_mode"] == "UNAVAILABLE"


def test_model_outside_asset_directory_is_rejected_before_import_or_read(
    tmp_path, monkeypatch
):
    asset_directory = tmp_path / "assets"
    outside_directory = tmp_path / "outside"
    asset_directory.mkdir()
    outside_directory.mkdir()
    model_path = outside_directory / "model.onnx"
    model_path.write_bytes(b"must-not-be-read")

    def forbidden_import():
        raise AssertionError("ONNX import occurred before model containment")

    def forbidden_open(*_args, **_kwargs):
        raise AssertionError("outside model was opened before containment rejection")

    monkeypatch.setattr(
        c3c_onnx_structural, "_load_onnx_module", forbidden_import
    )
    monkeypatch.setattr(builtins, "open", forbidden_open)
    result = c3c_onnx_structural.run_assessment(
        _task(model_path, asset_directory)
    )

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"] == [
        {"ref": str(model_path), "reason": "MODEL_FILE_OUTSIDE_ASSET_DIR"}
    ]
    assert result["access_mode"] == "UNAVAILABLE"


def test_external_absolute_path_reuses_c3a_helper_without_outside_stat(
    tmp_path, monkeypatch
):
    outside = tmp_path.parent / "outside.bin"
    fake_onnx = _fake_onnx(_FakeModel(str(outside.resolve())))

    def forbidden_file_stat(_path):
        raise AssertionError("outside target was stat'ed")

    monkeypatch.setattr(c3a_artifact_unit.os.path, "isfile", forbidden_file_stat)
    result = _run_with_fake_onnx(tmp_path, monkeypatch, fake_onnx)

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"][0]["reason"] == "ABSOLUTE_PATH"
    assert fake_onnx.checker_calls == []


def test_symlink_escape_is_classified_by_c3a_helper_without_target_stat(
    tmp_path, monkeypatch
):
    asset_directory = tmp_path / "assets"
    outside_directory = tmp_path / "outside"
    asset_directory.mkdir()
    outside_directory.mkdir()
    model_path = asset_directory / "model.onnx"
    model_path.write_bytes(b"opaque-test-placeholder")
    outside_file = outside_directory / "external.bin"
    outside_file.write_bytes(b"outside")
    try:
        (asset_directory / "external.bin").symlink_to(outside_file)
    except (NotImplementedError, OSError):
        pytest.skip("BLOCKED: host symlink creation unavailable")

    def forbidden_file_stat(_path):
        raise AssertionError("escaped symlink target was stat'ed")

    fake_onnx = _fake_onnx(_FakeModel("external.bin"))
    monkeypatch.setattr(c3a_artifact_unit.os.path, "isfile", forbidden_file_stat)
    monkeypatch.setattr(
        c3c_onnx_structural, "_load_onnx_module", lambda: fake_onnx
    )
    result = c3c_onnx_structural.run_assessment(
        _task(model_path, asset_directory)
    )

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"] == [
        {"ref": "external.bin", "reason": "SYMLINK_ESCAPE"}
    ]
    assert fake_onnx.checker_calls == []


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_sec_006_symlink_escape_through_c3a_helper(tmp_path):
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

    result = c3c_onnx_structural.run_assessment(
        _task(asset_directory / "symlink_external_data.onnx", asset_directory)
    )

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert result["raw_signal"]["violations"][0]["reason"] == "SYMLINK_ESCAPE"


def test_checker_receives_in_memory_model_and_metadata_is_reported(
    tmp_path, monkeypatch
):
    model = _FakeModel()
    fake_onnx = _fake_onnx(model)
    result = _run_with_fake_onnx(tmp_path, monkeypatch, fake_onnx)

    assert fake_onnx.checker_calls == [model]
    assert result["raw_signal"]["opset_version"] == 17
    assert result["raw_signal"]["graph_node_count"] == 1
    assert result["raw_signal"]["graph_input_names"] == ["input"]
    assert result["raw_signal"]["graph_output_names"] == ["output"]


def test_checker_failure_is_structural_invalid_and_detail_is_bounded(
    tmp_path, monkeypatch
):
    fake_onnx = _fake_onnx(
        _FakeModel(), checker_error=ValueError("x" * 4096)
    )
    result = _run_with_fake_onnx(tmp_path, monkeypatch, fake_onnx)

    assert result["assessment_status"] == AssessmentStatus.STRUCTURAL_INVALID
    assert result["raw_signal"]["structural_status"] == (
        AssessmentStatus.STRUCTURAL_INVALID
    )
    assert result["error_detail"] == "CHECKER_FAILED: ValueError"
    assert len(result["error_detail"]) <= 512
    assert result["access_mode"] == "BLACK_BOX"


def test_load_failure_is_structural_invalid_without_host_path(
    tmp_path, monkeypatch
):
    fake_onnx = _fake_onnx(
        _FakeModel(), load_error=OSError(f"cannot read {tmp_path}")
    )
    result = _run_with_fake_onnx(tmp_path, monkeypatch, fake_onnx)

    assert result["assessment_status"] == AssessmentStatus.STRUCTURAL_INVALID
    assert result["error_detail"] == "LOAD_FAILED: OSError"
    assert str(tmp_path) not in result["error_detail"]


def test_valid_output_passes_schema_validation(tmp_path, monkeypatch):
    result = _run_with_fake_onnx(
        tmp_path, monkeypatch, _fake_onnx(_FakeModel())
    )

    validation = EvidenceSchemaValidator().validate_worker_output(
        result, "C3C_ONNX_STRUCTURAL"
    )
    assert validation.valid is True, validation.reason


def test_all_representative_outputs_exclude_prohibited_fields(tmp_path, monkeypatch):
    valid = _run_with_fake_onnx(
        tmp_path, monkeypatch, _fake_onnx(_FakeModel())
    )
    invalid = _run_with_fake_onnx(
        tmp_path,
        monkeypatch,
        _fake_onnx(_FakeModel(), checker_error=ValueError("invalid")),
    )

    for result in (valid, invalid):
        assert _find_prohibited_fields(result) == set()


def test_worker_source_has_no_onnxruntime_or_execution_imports():
    source_path = pathlib.Path(c3c_onnx_structural.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert "onnxruntime" not in imported_roots
    assert "torch" not in imported_roots
    assert "numpy" not in imported_roots
    assert imported_roots <= {"__future__", "assurance_system", "onnx", "os", "typing"}


def test_c3a_external_reference_helpers_are_reused_by_identity():
    assert c3c_onnx_structural.extract_external_references is (
        c3a_artifact_unit._external_references
    )
    assert c3c_onnx_structural.resolve_external_files is (
        c3a_artifact_unit._resolve_external_files
    )
