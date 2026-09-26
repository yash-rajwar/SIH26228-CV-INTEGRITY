"""YOLO detection geometry fixture (FIX-009-D)."""

import pathlib
import random


# Part A boundary: segmentation is scheduled for Part B; pose/OBB are not in MVP.
YOLO_SEG_POSE_OBB_BLOCKED = True

EXPECTED_VIOLATIONS = {
    "INVALID_CLASS_ID": 1,
    "NEGATIVE_CLASS_ID": 1,
    "WRONG_FIELD_COUNT": 1,
    "INVALID_NUMERIC_VALUE": 1,
    "OUT_OF_RANGE_COORDINATE": 1,
    "NON_POSITIVE_DIMENSION": 1,
}


def generate(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# synthetic seed {seed}",
        "class-x 0.5 0.5 0.2 0.2",
        "-1 0.5 0.5 0.2 0.2",
        "0 0.5 0.5 0.2",
        "0 NaN 0.5 0.2 0.2",
        "0 1.5 0.5 0.2 0.2",
        "0 0.5 0.5 0.0 0.2",
        "0 0.5 0.5 0.2 0.2",
    ]
    (output / "yolo_detection_violations.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return {
        "fixture_id": "FIX-009-D",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {"violations_by_type": dict(EXPECTED_VIOLATIONS)},
    }


def generate_segmentation(output_dir: str, seed: int) -> dict:
    raise NotImplementedError("PART B: YOLO_SEG fixture not implemented")


def generate_pose(output_dir: str, seed: int) -> dict:
    raise NotImplementedError("UNSUPPORTED: YOLO_POSE is outside the frozen MVP scope")


def generate_obb(output_dir: str, seed: int) -> dict:
    raise NotImplementedError("UNSUPPORTED: YOLO_OBB is outside the frozen MVP scope")
