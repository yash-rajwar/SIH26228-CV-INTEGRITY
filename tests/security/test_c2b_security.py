from assurance_system.constants import AssessmentStatus
from assurance_system.workers import c2b_exact_hash


def _task(paths, asset_directory):
    return {
        "schema_version": "worker-input-v1",
        "task": "C2B_EXACT_HASH",
        "asset_paths": [str(path) for path in paths],
        "asset_directory": str(asset_directory),
        "resource_limits": {
            "timeout_s": 30,
            "memory_mb": 512,
            "max_fds": 32,
        },
    }


def test_sec_c2b_001_all_paths_outside_fail_closed(tmp_path):
    asset_directory = tmp_path / "assets"
    asset_directory.mkdir()
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    result = c2b_exact_hash.run_assessment(
        _task([first, second], asset_directory)
    )

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "ALL_FILES_FAILED"
    assert len(result["raw_signal"]["read_errors"]) == 2
    assert all(
        item["error"] == "PATH_CONTAINMENT_VIOLATION"
        for item in result["raw_signal"]["read_errors"]
    )
    assert result["raw_signal"]["pdq_status"] == AssessmentStatus.DEFERRED_IN_SCOPE


def test_sec_c2b_002_prohibited_input_field_fails_closed(tmp_path):
    path = tmp_path / "valid.bin"
    path.write_bytes(b"content")
    task = _task([path], tmp_path)
    task["key_path"] = "must-not-reach-worker"

    result = c2b_exact_hash.run_assessment(task)

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "PROHIBITED_INPUT_FIELD"
    assert result["coverage_gap_clean_label"] is True
    assert result["raw_signal"]["pdq_status"] == AssessmentStatus.DEFERRED_IN_SCOPE
