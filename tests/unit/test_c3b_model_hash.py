"""UT-C3B-001 through UT-C3B-004, REPRO-003, and security boundaries."""

from __future__ import annotations

import builtins
import hashlib
import pathlib
from typing import Any

import pytest

from assurance_system.constants import AssessmentStatus, PF_002_NON_CLAIM
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator
from assurance_system.workers import c3b_model_hash


# Input-contract logic test only; this is not an ONNX identity definition or
# evidence that ONNX identity validation is complete.
TEST_ONLY_DEFINITION_ID = "test-only-artifact-unit-v1"
_MISSING = object()
_PROHIBITED_OUTPUT_FIELDS = {
    "risk_score",
    "aggregate_assurance",
    "compromise_probability",
    "overall_score",
    "threat_score",
    "malicious_probability",
    "confidence_score",
    "trust_score",
    "safety_score",
}


def _artifact_unit(main_file: pathlib.Path, *external_files: pathlib.Path):
    return {
        "main_file": str(main_file),
        "external_files": [str(path) for path in external_files],
        "artifact_unit_definition_id": TEST_ONLY_DEFINITION_ID,
    }


def _task(
    artifact_unit: Any,
    asset_directory: pathlib.Path,
    reference_digest: Any = _MISSING,
):
    task = {
        "schema_version": "worker-input-v1",
        "task": "COMP-W-C3B",
        "asset_paths": [],
        "format": "ONNX",
        "asset_directory": str(asset_directory),
        "artifact_unit_definition_id": "UNAVAILABLE",
        "artifact_unit": artifact_unit,
        "resource_limits": {},
        "identity_quality": "UNAVAILABLE",
    }
    if reference_digest is not _MISSING:
        task["reference_digest"] = reference_digest
    return task


def _file_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_combined(*paths: pathlib.Path) -> str:
    digest_by_path = {str(path): _file_digest(path) for path in paths}
    concatenated = "".join(
        digest_by_path[path] for path in sorted(digest_by_path)
    )
    return hashlib.sha256(concatenated.encode("ascii")).hexdigest()


def _contains_key(value: Any, keys: set[str]) -> bool:
    if isinstance(value, dict):
        return any(
            key in keys or _contains_key(nested, keys)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(_contains_key(item, keys) for item in value)
    return False


def _contains_digest_result(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            "digest" in str(key).casefold() or _contains_digest_result(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(_contains_digest_result(item) for item in value)
    return False


def _known_unit(tmp_path: pathlib.Path):
    main_file = tmp_path / "model.bin"
    external_file = tmp_path / "weights.bin"
    main_file.write_bytes(b"model-header")
    external_file.write_bytes(b"external-weights")
    return main_file, external_file, _artifact_unit(main_file, external_file)


def test_ut_c3b_001_known_unit_matches_independent_expected_digest(tmp_path):
    """Input-contract/hash-logic test; not ONNX identity validation."""

    main_file, external_file, artifact_unit = _known_unit(tmp_path)
    result = c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path))

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["combined_artifact_unit_digest"] == (
        _expected_combined(main_file, external_file)
    )
    assert result["raw_signal"]["per_file_digests"] == {
        str(main_file): _file_digest(main_file),
        str(external_file): _file_digest(external_file),
    }


def test_ut_c3b_002_tampered_member_changes_combined_digest(tmp_path):
    """Input-contract/hash-logic test; not ONNX identity validation."""

    _, external_file, artifact_unit = _known_unit(tmp_path)
    before = c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path))
    external_file.write_bytes(b"tampered-external-weights")
    after = c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path))

    assert before["raw_signal"]["combined_artifact_unit_digest"] != (
        after["raw_signal"]["combined_artifact_unit_digest"]
    )


def test_ut_c3b_003_unavailable_definition_is_ambiguous_without_digest(tmp_path):
    main_file = tmp_path / "model.bin"
    main_file.write_bytes(b"model")
    artifact_unit = _artifact_unit(main_file)
    artifact_unit["artifact_unit_definition_id"] = "UNAVAILABLE"

    result = c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path))

    assert result["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
    assert result["access_mode"] == "UNAVAILABLE"
    assert result["artifact_unit_id"] == "UNAVAILABLE"
    assert _contains_digest_result(result) is False


def test_ut_c3b_004_pf_002_fields_are_present_on_every_outcome(tmp_path):
    main_file, _, artifact_unit = _known_unit(tmp_path)
    unavailable = dict(artifact_unit)
    unavailable["artifact_unit_definition_id"] = "UNAVAILABLE"
    outside = tmp_path.parent / "outside-c3b.bin"
    outside.write_bytes(b"outside")
    missing = tmp_path / "missing.bin"

    outputs = [
        c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path)),
        c3b_model_hash.run_assessment(_task(unavailable, tmp_path)),
        c3b_model_hash.run_assessment(_task(_artifact_unit(outside), tmp_path)),
        c3b_model_hash.run_assessment(_task(_artifact_unit(missing), tmp_path)),
    ]

    for result in outputs:
        assert result["pf_002_non_claim"] == PF_002_NON_CLAIM
        assert result["hash_match_not_safe"] is True
        assert result["hash_match_not_semantically_equivalent"] is True
        assert result["hash_match_not_causal_execution_proof"] is True
        assert result["non_claims"]
        assert result["limitations"]
        assert result["coverage_gap_clean_label"] is True
        assert isinstance(result["access_mode"], str) and result["access_mode"]

    assert main_file.exists()


def test_repro_003_same_unit_and_moved_copy_have_same_combined_digest(tmp_path):
    """Input-contract/hash-logic test; not ONNX identity validation."""

    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    first_main, first_external, first_unit = _known_unit(first)
    second_main = second / first_main.name
    second_external = second / first_external.name
    second_main.write_bytes(first_main.read_bytes())
    second_external.write_bytes(first_external.read_bytes())
    second_unit = _artifact_unit(second_main, second_external)

    first_result = c3b_model_hash.run_assessment(_task(first_unit, first))
    repeat_result = c3b_model_hash.run_assessment(_task(first_unit, first))
    moved_result = c3b_model_hash.run_assessment(_task(second_unit, second))

    assert first_result["raw_signal"]["combined_artifact_unit_digest"] == (
        repeat_result["raw_signal"]["combined_artifact_unit_digest"]
    )
    assert first_result["raw_signal"]["combined_artifact_unit_digest"] == (
        moved_result["raw_signal"]["combined_artifact_unit_digest"]
    )


@pytest.mark.parametrize(
    "artifact_unit",
    [
        None,
        {},
        {"main_file": "model.bin"},
        {
            "main_file": "model.bin",
            "external_files": "weights.bin",
            "artifact_unit_definition_id": TEST_ONLY_DEFINITION_ID,
        },
        {
            "main_file": "",
            "external_files": [],
            "artifact_unit_definition_id": TEST_ONLY_DEFINITION_ID,
        },
    ],
)
def test_none_and_malformed_units_are_ambiguous_without_digest(
    tmp_path, artifact_unit
):
    result = c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path))

    assert result["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
    assert _contains_digest_result(result) is False


def test_missing_member_returns_assessment_error_without_partial_digest(tmp_path):
    main_file = tmp_path / "model.bin"
    missing_file = tmp_path / "missing.bin"
    main_file.write_bytes(b"model")

    result = c3b_model_hash.run_assessment(
        _task(_artifact_unit(main_file, missing_file), tmp_path)
    )

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "ARTIFACT_MEMBER_READ_FAILED: FileNotFoundError"
    assert _contains_digest_result(result) is False


def test_outside_member_is_rejected_before_any_file_is_opened(
    tmp_path, monkeypatch
):
    asset_directory = tmp_path / "assets"
    outside_directory = tmp_path / "outside"
    asset_directory.mkdir()
    outside_directory.mkdir()
    main_file = asset_directory / "model.bin"
    outside_file = outside_directory / "weights.bin"
    main_file.write_bytes(b"model")
    outside_file.write_bytes(b"outside")

    def forbidden_open(*_args, **_kwargs):
        raise AssertionError("artifact member opened before full containment check")

    monkeypatch.setattr(builtins, "open", forbidden_open)
    result = c3b_model_hash.run_assessment(
        _task(_artifact_unit(main_file, outside_file), asset_directory)
    )

    assert result["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert _contains_digest_result(result) is False


def test_reference_digest_absent_is_unavailable(tmp_path):
    _, _, artifact_unit = _known_unit(tmp_path)
    result = c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path))

    assert result["raw_signal"]["reference_digest_provided"] is False
    assert result["raw_signal"]["comparison_result"] == "UNAVAILABLE"


def test_matching_reference_digest_is_match(tmp_path):
    _, _, artifact_unit = _known_unit(tmp_path)
    baseline = c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path))
    digest = baseline["raw_signal"]["combined_artifact_unit_digest"]

    result = c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path, digest))

    assert result["raw_signal"]["comparison_result"] == "MATCH"


def test_different_reference_digest_is_different(tmp_path):
    _, _, artifact_unit = _known_unit(tmp_path)
    result = c3b_model_hash.run_assessment(
        _task(artifact_unit, tmp_path, "0" * 64)
    )

    assert result["raw_signal"]["comparison_result"] == "DIFFERENT"


def test_valid_c3b_output_passes_schema_validation(tmp_path):
    _, _, artifact_unit = _known_unit(tmp_path)
    result = c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path))

    validation = EvidenceSchemaValidator().validate_worker_output(
        result, "C3B_MODEL_HASH"
    )
    assert validation.valid is True, validation.reason


def test_outputs_contain_no_prohibited_score_fields(tmp_path):
    _, _, artifact_unit = _known_unit(tmp_path)
    outputs = [
        c3b_model_hash.run_assessment(_task(artifact_unit, tmp_path)),
        c3b_model_hash.run_assessment(_task(None, tmp_path)),
    ]

    assert all(
        not _contains_key(output, _PROHIBITED_OUTPUT_FIELDS) for output in outputs
    )


def test_prohibited_input_fails_closed_without_digest(tmp_path):
    _, _, artifact_unit = _known_unit(tmp_path)
    task = _task(artifact_unit, tmp_path)
    task["secret_token"] = "must-not-be-consumed"

    result = c3b_model_hash.run_assessment(task)

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "PROHIBITED_INPUT_FIELD"
    assert _contains_digest_result(result) is False
