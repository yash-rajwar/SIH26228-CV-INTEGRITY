"""All-box COCO and authorized-YOLO structural validation worker."""

# pycocotools (R27) ADOPT/ADAPT — BSD-style permissive license; see NOTICE for attribution.
# Geometry validation layer is an original project implementation on top of pycocotools.
# R01 code is NOT used here (no repository-wide license established).

from __future__ import annotations

from collections import Counter
import math
import os
from typing import Any

from assurance_system.config.loader import ConfigLoader
from assurance_system.constants import AssessmentStatus
from assurance_system.workers.base import (
    build_worker_output,
    is_within_directory,
    main as worker_main,
)

try:
    from pycocotools.coco import COCO

    _PYCOCOTOOLS_AVAILABLE = True
    _COCO_CLASS = COCO
except ImportError:
    COCO = None
    _PYCOCOTOOLS_AVAILABLE = False
    _COCO_CLASS = None


WORKER_ID = "COMP-W-C2A"
_WORKER_INPUT_SCHEMA = "worker-input-v1"
_PROHIBITED_INPUT_FIELDS = frozenset({"key_path", "db_path"})
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")
_COCO_REQUIRED_ROOT_FIELDS = ("images", "annotations", "categories")
_COCO_REQUIRED_ANNOTATION_FIELDS = ("id", "image_id", "category_id", "bbox")
_COORDINATE_NAMES = ("x", "y", "w", "h")
_MAX_ERROR_DETAIL_CHARS = 512

C2A_LIMITATIONS = [
    "Structural/geometry validation detects format violations only; it does not detect "
    "semantic poisoning, adversarial examples, or mislabelling that conforms to the format spec.",
    "Clean-label attacks (T05d) are not detectable by this method; they conform to valid format.",
    "Violation count is a structural observation; it does not imply attack count or attacker intent.",
    "Area-field check identifies non-positive declared area only; it does not verify polygon mask correctness.",
    "Category and image ID range validation requires all categories and images to be present "
    "in the same annotation file.",
]
C2A_NON_CLAIMS = [
    "STRUCTURAL_VALID does not imply annotation labels are semantically correct.",
    "STRUCTURAL_VALID does not imply the training distribution is unmanipulated.",
    "T05d (clean-label poisoning) is NOT covered by this method; no detection claim is made.",
    "Violation count does not imply attack attribution or malicious intent.",
]


def _contains_prohibited_input(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).casefold()
            if normalized in _PROHIBITED_INPUT_FIELDS or any(
                fragment in normalized for fragment in _PROHIBITED_INPUT_FRAGMENTS
            ):
                return True
            if _contains_prohibited_input(nested):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_prohibited_input(item) for item in value)
    return False


def _raw_signal(
    *,
    total_checked: int,
    violations: list[dict[str, Any]],
    format_name: str,
    task_variant: str | None,
) -> dict[str, Any]:
    counts = Counter(str(item["type"]) for item in violations)
    return {
        "total_annotations_checked": total_checked,
        "total_boxes_checked": total_checked,
        "violations": violations,
        "violation_count": len(violations),
        "violations_by_type": dict(sorted(counts.items())),
        "format": format_name,
        "task_variant": task_variant,
    }


def _output(
    assessment_status: str,
    *,
    raw_signal: dict[str, Any],
    error_detail: str | None = None,
    extra_limitations: list[str] | None = None,
) -> dict[str, Any]:
    limitations = list(C2A_LIMITATIONS)
    if extra_limitations:
        limitations.extend(extra_limitations)
    return build_worker_output(
        worker_id=WORKER_ID,
        assessment_status=assessment_status,
        raw_signal=raw_signal,
        limitations=limitations,
        non_claims=C2A_NON_CLAIMS,
        error_detail=error_detail,
    )


def _error_output(
    detail: str, *, format_name: str = "UNAVAILABLE", task_variant: str | None = None
) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ASSESSMENT_ERROR,
        raw_signal=_raw_signal(
            total_checked=0,
            violations=[],
            format_name=format_name,
            task_variant=task_variant,
        ),
        error_detail=detail[:_MAX_ERROR_DETAIL_CHARS],
    )


def _unsupported_output(task_variant: str | None) -> dict[str, Any]:
    variant = task_variant or "UNAVAILABLE"
    return _output(
        AssessmentStatus.UNSUPPORTED,
        raw_signal=_raw_signal(
            total_checked=0,
            violations=[],
            format_name=variant,
            task_variant=task_variant,
        ),
        extra_limitations=[f"Task variant {variant} is not in the frozen MVP scope."],
    )


def _append_violation(
    violations: list[dict[str, Any]], violation_type: str, **details: Any
) -> None:
    violations.append({"type": violation_type, **details})


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not math.isnan(value) and not math.isinf(
        value
    )


def _validate_coco(coco: Any) -> tuple[list[dict[str, Any]], int]:
    data = coco.dataset
    violations: list[dict[str, Any]] = []

    for field in _COCO_REQUIRED_ROOT_FIELDS:
        if field not in data:
            _append_violation(violations, "MISSING_ROOT_FIELD", field=field)

    category_id_set = {
        category["id"]
        for category in data.get("categories", [])
        if isinstance(category, dict) and "id" in category
    }
    image_id_set = {
        image["id"]
        for image in data.get("images", [])
        if isinstance(image, dict) and "id" in image
    }

    total_checked = 0
    for annotation_index, annotation in enumerate(coco.anns.values()):
        total_checked += 1
        annotation_id = annotation.get("id", f"index_{annotation_index}")
        location = {
            "annotation_id": annotation_id,
            "annotation_index": annotation_index,
        }

        for field in _COCO_REQUIRED_ANNOTATION_FIELDS:
            if field not in annotation:
                _append_violation(
                    violations,
                    "MISSING_ANNOTATION_FIELD",
                    **location,
                    field=field,
                )

        bbox = annotation.get("bbox", [])
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            _append_violation(violations, "INVALID_BBOX_FORMAT", **location)
            continue

        coordinate_is_valid: dict[str, bool] = {}
        for field, value in zip(_COORDINATE_NAMES, bbox, strict=True):
            coordinate_is_valid[field] = _is_finite_number(value)
            if not coordinate_is_valid[field]:
                _append_violation(
                    violations,
                    "INVALID_NUMERIC_VALUE",
                    **location,
                    field=field,
                    value=str(value),
                )

        x, y, width, height = bbox
        if (
            coordinate_is_valid["x"]
            and coordinate_is_valid["y"]
            and (x < 0 or y < 0)
        ):
            _append_violation(violations, "NEGATIVE_COORDINATE", **location)
        if coordinate_is_valid["w"] and width <= 0:
            _append_violation(
                violations, "NON_POSITIVE_WIDTH", **location, value=width
            )
        if coordinate_is_valid["h"] and height <= 0:
            _append_violation(
                violations, "NON_POSITIVE_HEIGHT", **location, value=height
            )
        if annotation.get("category_id") not in category_id_set:
            _append_violation(violations, "OUT_OF_RANGE_CATEGORY_ID", **location)
        if annotation.get("image_id") not in image_id_set:
            _append_violation(violations, "ORPHAN_ANNOTATION_IMAGE_ID", **location)
        if "area" in annotation:
            area = annotation["area"]
            if _is_finite_number(area) and area <= 0:
                _append_violation(
                    violations, "NON_POSITIVE_AREA", **location, area=area
                )

    return violations, total_checked


def _parse_yolo_number(
    value: str,
    *,
    field: str,
    line_number: int,
    violations: list[dict[str, Any]],
) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = math.nan
    if math.isnan(parsed) or math.isinf(parsed):
        _append_violation(
            violations,
            "INVALID_NUMERIC_VALUE",
            line=line_number,
            field=field,
            value=str(value),
        )
        return None
    return parsed


def _check_yolo_line(
    line: str, line_number: int, task_variant: str
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    parts = line.split()
    try:
        class_id = int(parts[0])
    except (IndexError, ValueError):
        _append_violation(violations, "INVALID_CLASS_ID", line=line_number)
        return violations

    if class_id < 0:
        _append_violation(violations, "NEGATIVE_CLASS_ID", line=line_number)

    if task_variant == "YOLO_DETECTION":
        if len(parts) != 5:
            _append_violation(
                violations,
                "WRONG_FIELD_COUNT",
                expected=5,
                found=len(parts),
                line=line_number,
            )
            return violations
        values: dict[str, float | None] = {}
        for field, value in zip(("cx", "cy", "w", "h"), parts[1:], strict=True):
            values[field] = _parse_yolo_number(
                value,
                field=field,
                line_number=line_number,
                violations=violations,
            )
        for field, value in values.items():
            if value is not None and not 0.0 <= value <= 1.0:
                _append_violation(
                    violations,
                    "OUT_OF_RANGE_COORDINATE",
                    line=line_number,
                    field=field,
                    value=value,
                )
        if any(values[field] is not None and values[field] <= 0 for field in ("w", "h")):
            _append_violation(violations, "NON_POSITIVE_DIMENSION", line=line_number)

    elif task_variant == "YOLO_SEG":
        coordinate_count = len(parts) - 1
        if coordinate_count < 6:
            _append_violation(
                violations,
                "INVALID_POLYGON_FORMAT",
                reason="TOO_FEW_COORDINATES",
                line=line_number,
            )
        if coordinate_count % 2 != 0:
            _append_violation(
                violations,
                "INVALID_POLYGON_FORMAT",
                reason="ODD_COORDINATE_COUNT",
                line=line_number,
            )
        for coordinate_index, value in enumerate(parts[1:]):
            parsed = _parse_yolo_number(
                value,
                field=f"coordinate_{coordinate_index}",
                line_number=line_number,
                violations=violations,
            )
            if parsed is not None and not 0.0 <= parsed <= 1.0:
                _append_violation(
                    violations,
                    "OUT_OF_RANGE_COORDINATE",
                    line=line_number,
                    field=f"coordinate_{coordinate_index}",
                    value=parsed,
                )

    return violations


def _parse_yolo_label_file(
    path: str, task_variant: str, asset_dir: str
) -> tuple[list[dict[str, Any]], int]:
    if not is_within_directory(path, asset_dir):
        raise ValueError("PATH_CONTAINMENT_VIOLATION")

    violations: list[dict[str, Any]] = []
    total_checked = 0
    with open(path, "r", encoding="utf-8", errors="replace") as label_file:
        for line_number, line in enumerate(label_file, start=1):
            normalized = line.strip()
            if not normalized or normalized.startswith("#"):
                continue
            total_checked += 1
            violations.extend(
                _check_yolo_line(normalized, line_number, task_variant)
            )
    return violations, total_checked


def _configured_file_size_limit(task: dict[str, Any], config: dict[str, Any]) -> int:
    resource_limits = task.get("resource_limits", {})
    if not isinstance(resource_limits, dict):
        raise ValueError("resource_limits must be an object")
    limit = resource_limits.get(
        "max_file_size_bytes",
        config["system"]["coco_annotation_file_max_size_bytes"],
    )
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("max_file_size_bytes must be a positive integer")
    return limit


def _preflight_paths(
    asset_paths: list[str], asset_directory: str, file_size_limit: int
) -> str | None:
    for path in asset_paths:
        if not isinstance(path, str) or not is_within_directory(path, asset_directory):
            return "PATH_CONTAINMENT_VIOLATION"
        try:
            if os.path.getsize(path) > file_size_limit:
                return "FILE_SIZE_EXCEEDED"
        except OSError as exc:
            return f"FILE_ACCESS_ERROR: {type(exc).__name__}: {exc}"
    return None


def run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    """Assess every annotation in the submitted COCO or authorized YOLO files."""

    if not isinstance(task, dict) or task.get("schema_version") != _WORKER_INPUT_SCHEMA:
        return _error_output("UNRECOGNISED_SCHEMA_VERSION")
    if _contains_prohibited_input(task):
        return _error_output("PROHIBITED_INPUT_FIELD")

    asset_paths = task.get("asset_paths")
    asset_directory = task.get("asset_directory")
    if (
        not isinstance(asset_paths, list)
        or not asset_paths
        or not isinstance(asset_directory, str)
        or not asset_directory
    ):
        return _error_output("INVALID_TASK_INPUT")

    try:
        config = ConfigLoader().load()
        file_size_limit = _configured_file_size_limit(task, config)
    except Exception as exc:
        return _error_output(
            f"CONFIGURATION_ERROR: {type(exc).__name__}: {exc}"
        )

    format_name = str(task.get("format", "")).upper()
    task_variant_value = task.get("task_variant")
    task_variant = (
        str(task_variant_value).upper() if task_variant_value is not None else None
    )
    if format_name.startswith("YOLO"):
        task_variant = task_variant or format_name

    preflight_error = _preflight_paths(
        asset_paths, asset_directory, file_size_limit
    )
    if preflight_error is not None:
        return _error_output(
            preflight_error,
            format_name=format_name or "UNAVAILABLE",
            task_variant=task_variant,
        )

    all_violations: list[dict[str, Any]] = []
    total_checked = 0
    if format_name == "COCO":
        if not _PYCOCOTOOLS_AVAILABLE or _COCO_CLASS is None:
            return _error_output(
                "PYCOCOTOOLS_UNAVAILABLE_PRE01_BLOCKED",
                format_name="COCO",
            )
        for path in asset_paths:
            try:
                coco = _COCO_CLASS(path)
            except Exception as exc:
                return _error_output(
                    f"COCO_LOAD_ERROR: {type(exc).__name__}: {exc}",
                    format_name="COCO",
                )
            violations, checked = _validate_coco(coco)
            all_violations.extend(violations)
            total_checked += checked
        task_variant = None

    elif format_name.startswith("YOLO"):
        authorized_variants = config["supported_formats"]["yolo_task_variants"]
        if task_variant not in authorized_variants:
            return _unsupported_output(task_variant)
        for path in asset_paths:
            try:
                violations, checked = _parse_yolo_label_file(
                    path, task_variant, asset_directory
                )
            except (OSError, ValueError) as exc:
                return _error_output(
                    f"YOLO_LOAD_ERROR: {type(exc).__name__}: {exc}",
                    format_name=task_variant,
                    task_variant=task_variant,
                )
            all_violations.extend(violations)
            total_checked += checked
        format_name = task_variant

    else:
        return _unsupported_output(task_variant or format_name or None)

    empty_limitations = None
    if total_checked == 0:
        empty_limitations = [
            "The submitted annotation input was empty; zero annotations were checked."
        ]
    return _output(
        AssessmentStatus.COMPLETED,
        raw_signal=_raw_signal(
            total_checked=total_checked,
            violations=all_violations,
            format_name=format_name,
            task_variant=task_variant,
        ),
        extra_limitations=empty_limitations,
    )


def main() -> None:
    worker_main(run_assessment)


if __name__ == "__main__":
    main()
