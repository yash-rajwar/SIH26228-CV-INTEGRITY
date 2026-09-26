"""Bounded compressed-expansion fixture (FIX-007)."""

import pathlib
import random
import zipfile


CI_UNCOMPRESSED_SIZE_BYTES = 10 * 1024 * 1024
FULL_SCALE_UNCOMPRESSED_SIZE_BYTES = 100 * 1024 * 1024


def generate(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    repeated_byte = bytes([random.randrange(0, 256)])
    archive_path = output / "bounded_archive_bomb.zip"
    archive_entry = zipfile.ZipInfo(
        "deep/nested/payload.bin", date_time=(2026, 1, 1, 0, 0, 0)
    )
    archive_entry.compress_type = zipfile.ZIP_DEFLATED
    archive_entry.external_attr = 0o600 << 16
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        archive.writestr(
            archive_entry,
            repeated_byte * CI_UNCOMPRESSED_SIZE_BYTES,
            compresslevel=9,
        )
    return {
        "fixture_id": "FIX-007",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "expected_behavior": (
                "ASSESSMENT_ERROR or resource limit trigger; supervisor continues"
            ),
            "uncompressed_size_bytes": CI_UNCOMPRESSED_SIZE_BYTES,
            "full_scale_documented_bytes": FULL_SCALE_UNCOMPRESSED_SIZE_BYTES,
        },
    }
