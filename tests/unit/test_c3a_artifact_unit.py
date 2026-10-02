"""UT-C3A-001 through UT-C3A-007 and security boundaries."""

from __future__ import annotations

import importlib.util
import pathlib
import types

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

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["access_mode"] == "BLACK_BOX"
    assert result["artifact_unit_id"] == "onnx-main-referenced-external-data-v1"
    artifact_unit = result["raw_signal"]["artifact_unit"]
    assert artifact_unit["main_file"] == str(model_path.resolve())
    assert artifact_unit["external_files"] == []
    assert artifact_unit["artifact_unit_definition_id"] == "onnx-main-referenced-external-data-v1"


@pytest.mark.skipif(not ONNX_AVAILABLE, reason=ONNX_SKIP_REASON)
def test_ut_c3a_002_valid_onnx_with_internal_external_data(tmp_path):
    model_path = tmp_path / "external_data.onnx"
    data_path = tmp_path / "weights.bin"
    onnx_path_traversal._write_external_data_model(model_path, "weights.bin")
    data_path.write_bytes(b"\x00\x00\x80?")

    result = c3a_artifact_unit.run_assessment(_task(model_path, tmp_path, "ONNX"))

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["access_mode"] == "BLACK_BOX"
    assert result["artifact_unit_id"] == "onnx-main-referenced-external-data-v1"
    assert result["raw_signal"]["artifact_unit"]["external_files"] == [
        str(data_path.resolve())
    ]
    assert result["raw_signal"]["artifact_unit"][
        "artifact_unit_definition_id"
    ] == "onnx-main-referenced-external-data-v1"


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

    def forbidden_file_stat(_path):
        raise AssertionError("model file was inspected before containment rejection")

    monkeypatch.setattr(c3a_artifact_unit, "_load_onnx_module", forbidden_import)
    monkeypatch.setattr(c3a_artifact_unit.os.path, "isfile", forbidden_file_stat)
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


@pytest.mark.parametrize(
    "reference",
    [
        r"\rooted.bin",
        r"C:\absolute.bin",
        r"C:drive-relative.bin",
        r"\\server\share\data.bin",
        r"\\?\C:\extended.bin",
        "C:/mixed/absolute.bin",
    ],
)
def test_windows_rooted_drive_and_unc_references_are_rejected(reference):
    assert c3a_artifact_unit._is_absolute_reference(reference) is True


def test_mixed_separator_traversal_is_rejected_before_file_stat(tmp_path, monkeypatch):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"opaque")

    def forbidden_file_stat(_path):
        raise AssertionError("external file was inspected before traversal rejection")

    monkeypatch.setattr(c3a_artifact_unit.os.path, "isfile", forbidden_file_stat)
    external_files, violations, inconsistencies = (
        c3a_artifact_unit._resolve_external_files(
            [r"..\escape.bin", r"nested/..\escape.bin"],
            str(model_path),
            str(tmp_path),
        )
    )

    assert external_files == []
    assert inconsistencies == []
    assert [item["reason"] for item in violations] == [
        "TRAVERSAL_PATTERN",
        "TRAVERSAL_PATTERN",
    ]


def test_contained_mixed_separator_reference_resolves_canonically(tmp_path):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"opaque")
    nested = tmp_path / "nested"
    nested.mkdir()
    data_path = nested / "data.bin"
    data_path.write_bytes(b"data")

    external_files, violations, inconsistencies = (
        c3a_artifact_unit._resolve_external_files(
            [r"nested\data.bin"], str(model_path), str(tmp_path)
        )
    )

    assert external_files == [str(data_path.resolve())]
    assert violations == []
    assert inconsistencies == []


def test_external_symlink_escape_is_rejected_before_file_stat(tmp_path, monkeypatch):
    asset_directory = tmp_path / "assets"
    outside_directory = tmp_path / "outside"
    asset_directory.mkdir()
    outside_directory.mkdir()
    model_path = asset_directory / "model.onnx"
    model_path.write_bytes(b"opaque")
    outside_file = outside_directory / "data.bin"
    outside_file.write_bytes(b"outside")
    link_path = asset_directory / "data.bin"
    try:
        link_path.symlink_to(outside_file)
    except (NotImplementedError, OSError):
        pytest.skip("BLOCKED: host symlink creation unavailable")

    def forbidden_file_stat(_path):
        raise AssertionError("escaped external file was inspected")

    monkeypatch.setattr(c3a_artifact_unit.os.path, "isfile", forbidden_file_stat)
    external_files, violations, inconsistencies = (
        c3a_artifact_unit._resolve_external_files(
            ["data.bin"], str(model_path), str(asset_directory)
        )
    )

    assert external_files == []
    assert inconsistencies == []
    assert violations == [{"ref": "data.bin", "reason": "SYMLINK_ESCAPE"}]


def test_recursive_tensor_walker_reviews_nested_and_repeated_message_fields():
    class FakeField:
        TYPE_MESSAGE = 11
        LABEL_REPEATED = 3

        def __init__(self, *, repeated: bool):
            self.type = self.TYPE_MESSAGE
            self.label = self.LABEL_REPEATED if repeated else 1

    class FakeMessage:
        DESCRIPTOR = types.SimpleNamespace(full_name="onnx.FakeContainer")

        def __init__(self, fields):
            self._fields = fields

        def ListFields(self):
            return self._fields

    class FakeTensor:
        DESCRIPTOR = types.SimpleNamespace(full_name="onnx.TensorProto")

        def __init__(self, name: str, location: str):
            self.name = name
            self.data_location = 1
            self.external_data = [
                types.SimpleNamespace(key="location", value=location)
            ]

    direct = FakeTensor("initializer", "initializer.bin")
    nested = FakeTensor("nested_attribute", "nested.bin")
    nested_container = FakeMessage([(FakeField(repeated=False), nested)])
    root = FakeMessage(
        [(FakeField(repeated=True), [direct, nested_container])]
    )
    fake_onnx = types.SimpleNamespace(
        TensorProto=types.SimpleNamespace(EXTERNAL=1)
    )

    references, inconsistencies = c3a_artifact_unit._external_references(
        root, fake_onnx
    )

    assert references == ["initializer.bin", "nested.bin"]
    assert inconsistencies == []


def test_recursive_tensor_walker_supports_modern_protobuf_cardinality_api():
    class ModernField:
        TYPE_MESSAGE = 11

        def __init__(self, *, repeated: bool):
            self.type = self.TYPE_MESSAGE
            self.is_repeated = repeated

    class FakeMessage:
        DESCRIPTOR = types.SimpleNamespace(full_name="onnx.FakeContainer")

        def __init__(self, fields):
            self._fields = fields

        def ListFields(self):
            return self._fields

    class FakeTensor:
        DESCRIPTOR = types.SimpleNamespace(full_name="onnx.TensorProto")

        def __init__(self, name: str, location: str):
            self.name = name
            self.data_location = 1
            self.external_data = [
                types.SimpleNamespace(key="location", value=location)
            ]

    repeated_field = ModernField(repeated=True)
    singular_field = ModernField(repeated=False)
    assert not hasattr(repeated_field, "label")
    assert not hasattr(singular_field, "label")

    direct = FakeTensor("initializer", "initializer.bin")
    nested = FakeTensor("nested_attribute", "nested.bin")
    nested_container = FakeMessage([(singular_field, nested)])
    root = FakeMessage([(repeated_field, [direct, nested_container])])
    fake_onnx = types.SimpleNamespace(
        TensorProto=types.SimpleNamespace(EXTERNAL=1)
    )

    references, inconsistencies = c3a_artifact_unit._external_references(
        root, fake_onnx
    )

    assert references == ["initializer.bin", "nested.bin"]
    assert inconsistencies == []


def test_unexpected_resolver_error_stays_in_c3a_output_contract(tmp_path, monkeypatch):
    model_path = tmp_path / "model.pt"
    model_path.write_bytes(b"opaque")

    def fail_closed(_model_path, _asset_directory):
        raise RuntimeError(f"do not expose {tmp_path}")

    monkeypatch.setattr(
        c3a_artifact_unit, "resolve_pytorch_artifact_unit", fail_closed
    )
    result = c3a_artifact_unit.run_assessment(
        _task(model_path, tmp_path, "PyTorch")
    )

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "UNEXPECTED_RESOLUTION_ERROR: RuntimeError"
    assert str(tmp_path) not in result["error_detail"]
    assert result["pf_002_non_claim"] == PF_002_NON_CLAIM
    assert result["hash_match_not_safe"] is True
    assert result["coverage_gap_clean_label"] is True


def test_onnx_load_error_does_not_expose_absolute_host_path(tmp_path, monkeypatch):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"not-a-protobuf")

    class FailingOnnx:
        @staticmethod
        def load(path, *, load_external_data):
            assert load_external_data is False
            raise OSError(f"cannot parse {path}")

    monkeypatch.setattr(
        c3a_artifact_unit, "_load_onnx_module", lambda: FailingOnnx
    )
    result = c3a_artifact_unit.run_assessment(
        _task(model_path, tmp_path, "ONNX")
    )

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "ONNX_LOAD_HEADER_FAILED: OSError"
    assert str(tmp_path) not in result["error_detail"]


def test_error_detail_is_bounded():
    result = c3a_artifact_unit._assessment_error("x" * 4096)
    assert len(result["error_detail"]) == 512


def test_non_onnx_raw_signals_are_deterministic(tmp_path):
    model_path = tmp_path / "model.pth"
    model_path.write_bytes(b"opaque")
    pytorch_task = _task(model_path, tmp_path, "PyTorch")
    torchscript_task = _task(model_path, tmp_path, "TorchScript")

    assert (
        c3a_artifact_unit.run_assessment(pytorch_task)["raw_signal"]
        == c3a_artifact_unit.run_assessment(pytorch_task)["raw_signal"]
    )
    assert (
        c3a_artifact_unit.run_assessment(torchscript_task)["raw_signal"]
        == c3a_artifact_unit.run_assessment(torchscript_task)["raw_signal"]
    )


def test_pytorch_multiple_non_regular_and_outside_inputs_fail_closed(tmp_path):
    valid = tmp_path / "valid.pt"
    second = tmp_path / "second.pth"
    valid.write_bytes(b"one")
    second.write_bytes(b"two")

    multiple_task = _task(valid, tmp_path, "PyTorch")
    multiple_task["asset_paths"] = [str(valid), str(second)]
    assert c3a_artifact_unit.run_assessment(multiple_task)[
        "assessment_status"
    ] == AssessmentStatus.ASSESSMENT_ERROR

    directory_path = tmp_path / "directory.pt"
    directory_path.mkdir()
    assert c3a_artifact_unit.run_assessment(
        _task(directory_path, tmp_path, "PyTorch")
    )["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS

    asset_directory = tmp_path / "assets"
    outside_directory = tmp_path / "outside"
    asset_directory.mkdir()
    outside_directory.mkdir()
    outside_model = outside_directory / "outside.pt"
    outside_model.write_bytes(b"outside")
    assert c3a_artifact_unit.run_assessment(
        _task(outside_model, asset_directory, "PyTorch")
    )["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS


def test_torchscript_deferral_does_not_stat_or_load_model(tmp_path, monkeypatch):
    model_path = tmp_path / "model.ts"
    model_path.write_bytes(b"opaque")

    def forbidden_file_stat(_path):
        raise AssertionError("TorchScript model was inspected")

    def forbidden_import():
        raise AssertionError("TorchScript attempted ONNX import")

    monkeypatch.setattr(c3a_artifact_unit.os.path, "isfile", forbidden_file_stat)
    monkeypatch.setattr(c3a_artifact_unit, "_load_onnx_module", forbidden_import)
    result = c3a_artifact_unit.run_assessment(
        _task(model_path, tmp_path, "TorchScript")
    )

    assert result["assessment_status"] == AssessmentStatus.DEFERRED_IN_SCOPE
