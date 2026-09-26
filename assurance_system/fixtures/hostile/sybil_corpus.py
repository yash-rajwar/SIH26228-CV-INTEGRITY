"""Contributor-concentration fixtures for FIX-012."""

import json
import math
import pathlib
import random


ITEM_COUNT = 100
CONTRIBUTOR_COUNT = 10


def _write(path: pathlib.Path, records: list[dict]) -> None:
    path.write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def generate_single_source(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = [
        {"item_id": f"synthetic-{index:03d}", "contributor_id": "source-000"}
        for index in range(ITEM_COUNT)
    ]
    _write(output / "single_source.json", records)
    return {
        "fixture_id": "FIX-012",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "expected_hhi": 1.0,
            "expected_entropy": 0.0,
            "expected_sybil_unreliable": True,
        },
    }


def generate_multi_source(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "item_id": f"synthetic-{index:03d}",
            "contributor_id": f"source-{index % CONTRIBUTOR_COUNT:03d}",
        }
        for index in range(ITEM_COUNT)
    ]
    _write(output / "multi_source.json", records)
    return {
        "fixture_id": "FIX-012-CONTROL",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "expected_hhi": 1.0 / CONTRIBUTOR_COUNT,
            "expected_entropy_bits_approx": round(math.log2(CONTRIBUTOR_COUNT), 2),
        },
    }


def generate(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    primary = generate_single_source(str(output), seed)
    control = generate_multi_source(str(output), seed)
    return {
        **primary,
        "expected_result": {
            **primary["expected_result"],
            "control_fixture": control["expected_result"],
        },
    }
