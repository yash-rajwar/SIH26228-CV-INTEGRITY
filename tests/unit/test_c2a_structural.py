import json
import pathlib

import pytest

from assurance_system.constants import AssessmentStatus
from assurance_system.fixtures.hostile import coco_geometry, yolo_geometry
from assurance_system.workers import c2a_structural


class _TestOnlyCOCO:
    """Small adapter for geometry-loop tests; never used by production code."""

    def __init__(self, annotation_path: str):
        self.dataset = json.loads(
            pathlib.Path(annotation_path).read_text(encoding="utf-8")
        )
        annotations = self.dataset.get("annotations", [])
        self.anns = {
            annotation.get("id", f"index_{index}"): annotation
            for index, annotation in enumerate(annotations)
        }


def _enable_test_coco(monkeypatch) -> None:
    monkeypatch.setattr(c2a_structural, "_PYCOCOTOOLS_AVAILABLE", True)
    monkeypatch.setattr(c2a_structural, "_COCO_CLASS", _TestOnlyCOCO)


def _task(path: pathlib.Path, format_name: str = "COCO") -> dict:
    return {
        "schema_version": "worker-input-v1",
        "task": "C2A_STRUCTURAL",
        "asset_paths": [str(path)],
        "format": format_name,
        "task_variant": format_name if format_name.startswith("YOLO") else None,
        "asset_directory": str(path.parent),
        "resource_limits": {
            "timeout_s": 30,
            "memory_mb": 512,
            "max_fds": 32,
        },
    }


def _write_coco(path: pathlib.Path, annotations: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "images": [{"id": 1, "width": 100, "height": 100}],
                "categories": [{"id": 1, "name": "synthetic"}],
                "annotations": annotations,
            },
            allow_nan=True,
        ),
        encoding="utf-8",
    )


def _valid_annotation(annotation_id: int) -> dict:
    return {
        "id": annotation_id,
        "image_id": 1,
        "category_id": 1,
        "bbox": [10, 10, 20, 20],
        "area": 400,
    }


def test_ut_c2a_001_valid_coco(monkeypatch, tmp_path):
    _enable_test_coco(monkeypatch)
    manifest = coco_geometry.generate_valid(str(tmp_path), seed=42)
    result = c2a_structural.run_assessment(
        _task(tmp_path / "valid_coco.json")
    )

    assert manifest["is_synthetic"] is True
    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["violation_count"] == 0
    assert result["coverage_gap_clean_label"] is True


def test_ut_c2a_002_fix_008_detects_manifest_violations(monkeypatch, tmp_path):
    _enable_test_coco(monkeypatch)
    manifest = coco_geometry.generate(str(tmp_path), seed=42)
    result = c2a_structural.run_assessment(
        _task(tmp_path / "coco_geometry_violations.json")
    )

    expected = manifest["expected_result"]
    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["violations_by_type"] == expected[
        "violations_by_type"
    ]
    assert result["raw_signal"]["violation_count"] >= expected["violation_count"]


def test_ut_c2a_003_empty_annotations(monkeypatch, tmp_path):
    _enable_test_coco(monkeypatch)
    annotation_path = tmp_path / "empty.json"
    _write_coco(annotation_path, [])

    result = c2a_structural.run_assessment(_task(annotation_path))

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["total_annotations_checked"] == 0
    assert any("empty" in limitation.casefold() for limitation in result["limitations"])


def test_ut_c2a_004_checks_every_annotation(monkeypatch, tmp_path):
    _enable_test_coco(monkeypatch)
    annotations = [_valid_annotation(index + 1) for index in range(100)]
    annotations[50]["bbox"][0] = -1
    annotations[99]["bbox"][0] = -2
    annotation_path = tmp_path / "one_hundred.json"
    _write_coco(annotation_path, annotations)

    result = c2a_structural.run_assessment(_task(annotation_path))
    negative_indices = {
        violation["annotation_index"]
        for violation in result["raw_signal"]["violations"]
        if violation["type"] == "NEGATIVE_COORDINATE"
    }

    assert result["raw_signal"]["total_annotations_checked"] == 100
    assert negative_indices == {50, 99}


def test_ut_c2a_005_malformed_coco_fails_closed(monkeypatch, tmp_path):
    _enable_test_coco(monkeypatch)
    annotation_path = tmp_path / "malformed.json"
    annotation_path.write_text('{"broken"', encoding="utf-8")

    result = c2a_structural.run_assessment(_task(annotation_path))

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"]
    assert result["coverage_gap_clean_label"] is True


def test_ut_c2a_006_nan_coordinate_is_recorded(monkeypatch, tmp_path):
    _enable_test_coco(monkeypatch)
    annotation = _valid_annotation(1)
    annotation["bbox"][0] = float("nan")
    annotation_path = tmp_path / "nan.json"
    _write_coco(annotation_path, [annotation])

    result = c2a_structural.run_assessment(_task(annotation_path))

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert "INVALID_NUMERIC_VALUE" in result["raw_signal"]["violations_by_type"]


def test_ut_c2a_007_security_labels_on_every_output(tmp_path):
    label_path = tmp_path / "valid.txt"
    label_path.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    outputs = [
        c2a_structural.run_assessment(_task(label_path, "YOLO_DETECTION")),
        c2a_structural.run_assessment(
            {**_task(label_path, "YOLO_POSE"), "task_variant": "YOLO_POSE"}
        ),
        c2a_structural.run_assessment(
            {**_task(label_path, "YOLO_DETECTION"), "schema_version": "unknown"}
        ),
    ]

    for result in outputs:
        assert result["coverage_gap_clean_label"] is True
        assert result["limitations"]
        assert result["non_claims"] == c2a_structural.C2A_NON_CLAIMS
        assert any("T05d" in non_claim for non_claim in result["non_claims"])


def _yolo_detection_authorized() -> bool:
    config = c2a_structural.ConfigLoader().load()
    return "YOLO_DETECTION" in config["supported_formats"]["yolo_task_variants"]


@pytest.mark.skipif(
    not _yolo_detection_authorized(),
    reason="BLOCKED: PRE-05 — YOLO_DETECTION not in confirmed format list",
)
def test_ut_c2a_008_yolo_detection_valid(tmp_path):
    label_path = tmp_path / "valid.txt"
    label_path.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    result = c2a_structural.run_assessment(_task(label_path, "YOLO_DETECTION"))

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["violation_count"] == 0


@pytest.mark.skipif(
    not _yolo_detection_authorized(),
    reason="BLOCKED: PRE-05 — YOLO_DETECTION not in confirmed format list",
)
def test_ut_c2a_009_yolo_detection_violations(tmp_path):
    manifest = yolo_geometry.generate(str(tmp_path), seed=42)

    result = c2a_structural.run_assessment(
        _task(tmp_path / "yolo_detection_violations.txt", "YOLO_DETECTION")
    )

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["violations_by_type"] == manifest[
        "expected_result"
    ]["violations_by_type"]


def test_yolo_segmentation_violations_match_fixture(tmp_path):
    manifest = yolo_geometry.generate_segmentation(str(tmp_path), seed=42)

    result = c2a_structural.run_assessment(
        _task(tmp_path / "yolo_segmentation_violations.txt", "YOLO_SEG")
    )

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["violations_by_type"] == manifest[
        "expected_result"
    ]["violations_by_type"]


def test_coco_unavailable_returns_assessment_error(monkeypatch, tmp_path):
    annotation_path = tmp_path / "valid.json"
    _write_coco(annotation_path, [_valid_annotation(1)])
    monkeypatch.setattr(c2a_structural, "_PYCOCOTOOLS_AVAILABLE", False)
    monkeypatch.setattr(c2a_structural, "_COCO_CLASS", None)

    result = c2a_structural.run_assessment(_task(annotation_path))

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "PYCOCOTOOLS_UNAVAILABLE_PRE01_BLOCKED"


def test_file_size_limit_is_enforced_before_parsing(tmp_path):
    label_path = tmp_path / "oversized.txt"
    label_path.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    task = _task(label_path, "YOLO_DETECTION")
    task["resource_limits"]["max_file_size_bytes"] = 1

    result = c2a_structural.run_assessment(task)

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "FILE_SIZE_EXCEEDED"
