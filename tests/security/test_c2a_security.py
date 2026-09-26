from assurance_system.constants import AssessmentStatus
from assurance_system.workers import c2a_structural


def _task(path, asset_directory):
    return {
        "schema_version": "worker-input-v1",
        "task": "C2A_STRUCTURAL",
        "asset_paths": [str(path)],
        "format": "YOLO_DETECTION",
        "task_variant": "YOLO_DETECTION",
        "asset_directory": str(asset_directory),
        "resource_limits": {
            "timeout_s": 30,
            "memory_mb": 512,
            "max_fds": 32,
        },
    }


def test_sec_c2a_001_path_outside_asset_directory_fails_closed(tmp_path):
    asset_directory = tmp_path / "assets"
    asset_directory.mkdir()
    outside_path = tmp_path / "outside.txt"
    outside_path.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    result = c2a_structural.run_assessment(
        _task(outside_path, asset_directory)
    )

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "PATH_CONTAINMENT_VIOLATION"
    assert result["coverage_gap_clean_label"] is True


def test_sec_c2a_002_prohibited_input_field_fails_closed(tmp_path):
    label_path = tmp_path / "valid.txt"
    label_path.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    task = _task(label_path, tmp_path)
    task["key_path"] = "must-not-reach-worker"

    result = c2a_structural.run_assessment(task)

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "PROHIBITED_INPUT_FIELD"
    assert result["coverage_gap_clean_label"] is True
