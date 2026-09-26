"""Seed-pinned COCO geometry and malformed-JSON fixtures."""

import json
import pathlib
import random


EXPECTED_VIOLATIONS = {
    "MISSING_ANNOTATION_FIELD": 1,
    "INVALID_BBOX_FORMAT": 1,
    "INVALID_NUMERIC_VALUE": 1,
    "NEGATIVE_COORDINATE": 1,
    "NON_POSITIVE_WIDTH": 1,
    "NON_POSITIVE_HEIGHT": 1,
    "OUT_OF_RANGE_CATEGORY_ID": 1,
    "ORPHAN_ANNOTATION_IMAGE_ID": 1,
    "NON_POSITIVE_AREA": 1,
}


def _write_json(path: pathlib.Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=True) + "\n",
        encoding="utf-8",
    )


def _valid_coco(seed: int) -> dict:
    random.seed(seed)
    image_name = f"synthetic-{random.Random(seed).randrange(1_000_000):06d}.jpg"
    return {
        "images": [{"id": 1, "file_name": image_name, "width": 100, "height": 100}],
        "categories": [{"id": 1, "name": "synthetic-object"}],
        "annotations": [
            {
                "id": 1,
                "image_id": 1,
                "category_id": 1,
                "bbox": [10, 10, 20, 20],
                "area": 400,
            }
        ],
    }


def generate(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    data = _valid_coco(seed)
    data["annotations"].extend(
        [
            {"image_id": 1, "category_id": 1, "bbox": [1, 1, 2, 2], "area": 4},
            {"id": 3, "image_id": 1, "category_id": 1, "bbox": [1, 2, 3]},
            {"id": 4, "image_id": 1, "category_id": 1, "bbox": [float("nan"), 1, 2, 2]},
            {"id": 5, "image_id": 1, "category_id": 1, "bbox": [-1, 1, 2, 2]},
            {"id": 6, "image_id": 1, "category_id": 1, "bbox": [1, 1, 0, 2]},
            {"id": 7, "image_id": 1, "category_id": 1, "bbox": [1, 1, 2, 0]},
            {"id": 8, "image_id": 1, "category_id": 999, "bbox": [1, 1, 2, 2]},
            {"id": 9, "image_id": 999, "category_id": 1, "bbox": [1, 1, 2, 2]},
            {"id": 10, "image_id": 1, "category_id": 1, "bbox": [1, 1, 2, 2], "area": 0},
        ]
    )
    _write_json(output / "coco_geometry_violations.json", data)
    (output / "malformed_coco.json").write_text(
        '{"images": [{"id": 1}], "annotations": [', encoding="utf-8"
    )
    _write_json(output / "valid_coco.json", _valid_coco(seed))
    return {
        "fixture_id": "FIX-008",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "assessment_status": "COMPLETED",
            "violations_by_type": dict(EXPECTED_VIOLATIONS),
            "violation_count": sum(EXPECTED_VIOLATIONS.values()),
            "related_fixture": {
                "fixture_id": "FIX-017",
                "file": "malformed_coco.json",
                "assessment_status": "ASSESSMENT_ERROR",
            },
        },
    }


def generate_coco_geometry(output_dir: str, seed: int) -> dict:
    """Named entry point used by REPRO-006."""

    return generate(output_dir, seed)


def generate_valid(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "valid_coco.json", _valid_coco(seed))
    return {
        "fixture_id": "FIX-008-CONTROL",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {"assessment_status": "COMPLETED", "violation_count": 0},
    }
