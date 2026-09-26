"""Seed-pinned byte-identity fixtures (FIX-010 and FIX-011)."""

import pathlib
import random


DEFAULT_DUPLICATE_PAIR_COUNT = 3
DEFAULT_NON_DUPLICATE_COUNT = 6
SYNTHETIC_FILE_SIZE_BYTES = 256


def generate_duplicates(
    output_dir: str, seed: int, pair_count: int = DEFAULT_DUPLICATE_PAIR_COUNT
) -> dict:
    random.seed(seed)
    rng = random.Random(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    groups: list[list[str]] = []
    for group_number in range(pair_count):
        content = rng.randbytes(SYNTHETIC_FILE_SIZE_BYTES)
        names = [
            f"duplicate_{group_number:02d}_a.bin",
            f"duplicate_{group_number:02d}_b.bin",
        ]
        for name in names:
            (output / name).write_bytes(content)
        groups.append(names)
    return {
        "fixture_id": "FIX-010",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "expected_duplicate_group_count": pair_count,
            "expected_duplicate_files": groups,
        },
    }


def generate_nonduplicates(
    output_dir: str, seed: int, file_count: int = DEFAULT_NON_DUPLICATE_COUNT
) -> dict:
    random.seed(seed)
    rng = random.Random(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files: list[str] = []
    contents: set[bytes] = set()
    for file_number in range(file_count):
        content = rng.randbytes(SYNTHETIC_FILE_SIZE_BYTES)
        while content in contents:
            content = rng.randbytes(SYNTHETIC_FILE_SIZE_BYTES)
        contents.add(content)
        name = f"distinct_{file_number:02d}.bin"
        (output / name).write_bytes(content)
        files.append(name)
    return {
        "fixture_id": "FIX-011",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "expected_duplicate_group_count": 0,
            "expected_files": files,
        },
    }


def generate(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    duplicate_manifest = generate_duplicates(str(output / "duplicates"), seed)
    control_manifest = generate_nonduplicates(str(output / "controls"), seed)
    return {
        "fixture_id": "FIX-010",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            **duplicate_manifest["expected_result"],
            "control_fixture": {
                "fixture_id": control_manifest["fixture_id"],
                **control_manifest["expected_result"],
            },
        },
    }
