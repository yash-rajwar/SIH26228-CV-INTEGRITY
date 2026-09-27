"""Unit and contract tests for COMP-W-C3D."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from assurance_system.constants import AssessmentStatus, PF_002_NON_CLAIM
from assurance_system.fixtures.hostile import pickle_payload


REPO_ROOT = pathlib.Path(__file__).parents[2]
_MISSING = object()
_PF_002_BOOLEAN_FIELDS = (
    "hash_match_not_safe",
    "hash_match_not_semantically_equivalent",
    "hash_match_not_causal_execution_proof",
)


def _base_task(tmp_path: pathlib.Path) -> dict:
    asset_directory = tmp_path / "assets"
    asset_directory.mkdir(exist_ok=True)
    model_path = asset_directory / "placeholder.pt"
    model_path.write_bytes(b"")
    return {
        "schema_version": "worker-input-v1",
        "task": "C3D_SAFE_LOAD",
        "asset_paths": [str(model_path)],
        "format": "PYTORCH",
        "asset_directory": str(asset_directory),
        "artifact_unit_definition_id": "pytorch-single-file-v1",
        "resource_limits": {
            "timeout_s": 60,
            "memory_mb": 4096,
            "max_fds": 32,
        },
        "identity_quality": "UNAVAILABLE",
    }


def _invoke_worker(tmp_path: pathlib.Path, task: dict) -> tuple[dict, int, str]:
    task_path = tmp_path / "task.json"
    result_path = tmp_path / "result.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "assurance_system.workers.c3d_safe_load",
            "--task-file",
            str(task_path),
            "--result-file",
            str(result_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result_path.is_file(), completed.stderr
    result = json.loads(result_path.read_text(encoding="utf-8"))
    return result, completed.returncode, completed.stderr[:1024]


def _assert_pf_002_fields(result: dict) -> None:
    assert result["pf_002_non_claim"] == PF_002_NON_CLAIM
    for field_name in _PF_002_BOOLEAN_FIELDS:
        assert result[field_name] is True


def _assert_early_error_contract(result: dict) -> None:
    assert result["worker_id"] == "COMP-W-C3D"
    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert isinstance(result["raw_signal"], dict)
    assert result["raw_signal"]["fallback_attempted"] is False
    assert result["access_mode"] == "UNAVAILABLE"
    assert result["coverage_gap_clean_label"] is True
    assert result["limitations"]
    assert result["non_claims"]
    _assert_pf_002_fields(result)


def _assert_base_failure_contract(result: dict, returncode: int, stderr: str) -> None:
    assert returncode != 0
    assert result["worker_id"] == "C3D_SAFE_LOAD"
    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["raw_signal"] is None
    assert result["access_mode"] == "UNAVAILABLE"
    assert result["coverage_gap_clean_label"] is True
    assert result["limitations"]
    assert result["non_claims"]
    assert "Worker assessment failed" in stderr


def test_supplemental_module_exports_contract() -> None:
    from assurance_system.workers import c3d_safe_load

    assert callable(c3d_safe_load.run_assessment)
    assert callable(c3d_safe_load.main)


@pytest.mark.parametrize(
    "prohibited_key",
    ["key_path", "db_path"],
)
def test_supplemental_prohibited_direct_key_is_rejected(
    tmp_path: pathlib.Path, prohibited_key: str
) -> None:
    task = _base_task(tmp_path)
    sentinel = "VALUE_MUST_NOT_APPEAR"
    task[prohibited_key] = sentinel

    result, returncode, stderr = _invoke_worker(tmp_path, task)

    _assert_base_failure_contract(result, returncode, stderr)
    assert "task input contains a prohibited field" in result["error_detail"]
    assert sentinel not in json.dumps(result)


@pytest.mark.parametrize(
    "nested_key",
    ["PasswordHint", "api_secret_value", "serviceCredential"],
)
def test_supplemental_nested_sensitive_key_is_rejected(
    tmp_path: pathlib.Path, nested_key: str
) -> None:
    task = _base_task(tmp_path)
    sentinel = "NESTED_VALUE_MUST_NOT_APPEAR"
    task["metadata"] = [{"nested": {nested_key: sentinel}}]

    result, returncode, stderr = _invoke_worker(tmp_path, task)

    _assert_base_failure_contract(result, returncode, stderr)
    assert "task input contains a prohibited field" in result["error_detail"]
    assert sentinel not in json.dumps(result)


def test_supplemental_wrong_schema_is_base_rejection(tmp_path: pathlib.Path) -> None:
    task = _base_task(tmp_path)
    task["schema_version"] = "worker-input-v0"

    result, returncode, stderr = _invoke_worker(tmp_path, task)

    _assert_base_failure_contract(result, returncode, stderr)
    assert "unrecognized worker input schema_version" in result["error_detail"]


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("task", "C3C_ONNX_STRUCTURAL"),
        ("format", "ONNX"),
        ("artifact_unit_definition_id", "UNAVAILABLE"),
        ("identity_quality", "INVALID"),
    ],
)
def test_supplemental_invalid_required_field_is_rejected(
    tmp_path: pathlib.Path, field_name: str, field_value: str
) -> None:
    task = _base_task(tmp_path)
    task[field_name] = field_value

    result, returncode, _ = _invoke_worker(tmp_path, task)

    assert returncode == 0
    _assert_early_error_contract(result)


@pytest.mark.parametrize(
    "asset_paths",
    [[], "not-a-list", [123], ["one.pt", "two.pt"]],
)
def test_supplemental_malformed_asset_paths_are_rejected(
    tmp_path: pathlib.Path, asset_paths
) -> None:
    task = _base_task(tmp_path)
    task["asset_paths"] = asset_paths

    result, returncode, _ = _invoke_worker(tmp_path, task)

    assert returncode == 0
    _assert_early_error_contract(result)


def test_supplemental_outside_path_is_assessment_error(tmp_path: pathlib.Path) -> None:
    task = _base_task(tmp_path)
    outside_path = tmp_path / "outside.pt"
    outside_path.write_bytes(b"")
    task["asset_paths"] = [str(outside_path)]

    result, returncode, _ = _invoke_worker(tmp_path, task)

    assert returncode == 0
    _assert_early_error_contract(result)
    assert result["assessment_status"] != AssessmentStatus.LOAD_BLOCKED
    assert result["error_detail"] == "PATH_CONTAINMENT_VIOLATION"


@pytest.mark.parametrize(
    "resource_limits",
    [
        _MISSING,
        {},
        {"memory_mb": 4096, "max_fds": 32},
        {"timeout_s": 60, "max_fds": 32},
        {"timeout_s": 60, "memory_mb": 4096},
        {"timeout_s": True, "memory_mb": 4096, "max_fds": 32},
        {"timeout_s": 0, "memory_mb": 4096, "max_fds": 32},
        {"timeout_s": -1, "memory_mb": 4096, "max_fds": 32},
        {"timeout_s": "60", "memory_mb": 4096, "max_fds": 32},
        {
            "timeout_s": 60,
            "memory_mb": 4096,
            "max_fds": 32,
            "timeout_seconds": 60,
        },
    ],
)
def test_supplemental_invalid_resource_limits_are_rejected(
    tmp_path: pathlib.Path, resource_limits
) -> None:
    task = _base_task(tmp_path)
    if resource_limits is _MISSING:
        task.pop("resource_limits")
    else:
        task["resource_limits"] = resource_limits

    result, returncode, _ = _invoke_worker(tmp_path, task)

    assert returncode == 0
    _assert_early_error_contract(result)


def test_ut_c3d_001_hostile_pickle_is_load_blocked(tmp_path: pathlib.Path) -> None:
    fixture = pickle_payload.generate_hostile_pickle(
        str(tmp_path / "fix001"), seed=42
    )
    model_path = pathlib.Path(fixture["path"])
    task = _base_task(tmp_path)
    task["asset_paths"] = [str(model_path)]
    task["asset_directory"] = str(model_path.parent)

    result, returncode, _ = _invoke_worker(tmp_path, task)

    assert returncode == 0
    assert result["assessment_status"] == AssessmentStatus.LOAD_BLOCKED
    assert result["raw_signal"]["fallback_attempted"] is False
    assert result["raw_signal"]["weights_only_flag_used"] is True
    assert result["coverage_gap_clean_label"] is True
    assert result["access_mode"] == "BLACK_BOX"
    assert "does not prove malicious intent" in " ".join(result["non_claims"])
    _assert_pf_002_fields(result)


def test_ut_c3d_002_benign_model_loads_restricted(tmp_path: pathlib.Path) -> None:
    fixture = pickle_payload.generate_benign_pytorch(
        str(tmp_path / "fix015"), seed=42
    )
    model_path = pathlib.Path(fixture["path"])
    task = _base_task(tmp_path)
    task["asset_paths"] = [str(model_path)]
    task["asset_directory"] = str(model_path.parent)

    result, returncode, _ = _invoke_worker(tmp_path, task)

    assert returncode == 0
    assert result["assessment_status"] == AssessmentStatus.LOAD_SUCCESS
    assert result["raw_signal"]["fallback_attempted"] is False
    assert result["raw_signal"]["weights_only_flag_used"] is True
    assert result["raw_signal"]["map_location"] == "cpu"
    assert result["coverage_gap_clean_label"] is True
    assert result["access_mode"] == "BLACK_BOX"
    non_claims = " ".join(result["non_claims"])
    assert "behavioral safety" in non_claims
    assert "global backdoor absence" in non_claims
    assert "causal execution proof" in non_claims
    _assert_pf_002_fields(result)


def test_supplemental_empty_file_maps_to_load_error(tmp_path: pathlib.Path) -> None:
    task = _base_task(tmp_path)

    result, returncode, _ = _invoke_worker(tmp_path, task)

    assert returncode == 0
    assert result["assessment_status"] == AssessmentStatus.LOAD_ERROR
    assert result["raw_signal"]["fallback_attempted"] is False
    assert result["raw_signal"]["weights_only_flag_used"] is True
    assert result["access_mode"] == "BLACK_BOX"
    assert result["error_detail"] is None
    _assert_pf_002_fields(result)
