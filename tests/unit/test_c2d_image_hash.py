import pathlib

from assurance_system.constants import AssessmentStatus
from assurance_system.workers import c2d_image_hash


def _task(asset_paths: list[pathlib.Path], asset_directory: pathlib.Path) -> dict:
    return {
        "schema_version": "worker-input-v1",
        "task": "C2D_IMAGE_HASH",
        "asset_paths": [str(path) for path in asset_paths],
        "asset_directory": str(asset_directory),
        "resource_limits": {
            "timeout_s": 30,
            "memory_mb": 512,
            "max_fds": 32,
        },
    }


def test_ut_c2d_001_deterministic_sha256(tmp_path):
    image_path = tmp_path / "known-image.bin"
    image_path.write_bytes(bytes(range(256)))
    task = _task([image_path], tmp_path)

    first = c2d_image_hash.run_assessment(task)
    second = c2d_image_hash.run_assessment(task)

    first_digest = first["raw_signal"]["per_image_digests"][str(image_path)]
    second_digest = second["raw_signal"]["per_image_digests"][str(image_path)]
    assert first_digest == second_digest
    assert len(first_digest) == 64


def test_ut_c2d_002_coverage_gap_on_completed_and_error_outputs(tmp_path):
    image_path = tmp_path / "image.bin"
    image_path.write_bytes(b"image bytes")
    missing_path = tmp_path / "missing.bin"

    completed = c2d_image_hash.run_assessment(_task([image_path], tmp_path))
    failed = c2d_image_hash.run_assessment(_task([missing_path], tmp_path))

    assert completed["assessment_status"] == AssessmentStatus.COMPLETED
    assert failed["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert completed["coverage_gap_clean_label"] is True
    assert failed["coverage_gap_clean_label"] is True
    assert completed["non_claims"] == c2d_image_hash.C2D_NON_CLAIMS
    assert failed["non_claims"] == c2d_image_hash.C2D_NON_CLAIMS


def test_ut_c2d_003_t05d_non_claim_is_permanent(tmp_path):
    image_path = tmp_path / "image.bin"
    image_path.write_bytes(b"image bytes")

    result = c2d_image_hash.run_assessment(_task([image_path], tmp_path))

    assert any("T05d" in non_claim for non_claim in result["non_claims"])
    assert (
        "T05d (clean-label poisoning) is NOT covered by any method in this assessment."
        in result["non_claims"]
    )


def test_ut_c2d_004_pdq_deferred_and_identical_files_grouped(tmp_path):
    first_path = tmp_path / "first.bin"
    second_path = tmp_path / "second.bin"
    first_path.write_bytes(b"identical image bytes")
    second_path.write_bytes(b"identical image bytes")

    result = c2d_image_hash.run_assessment(
        _task([first_path, second_path], tmp_path)
    )

    signal = result["raw_signal"]
    assert signal["pdq_status"] == AssessmentStatus.DEFERRED_IN_SCOPE
    assert signal["duplicate_image_count"] == 2
    assert list(signal["duplicate_groups"].values()) == [
        [str(first_path), str(second_path)]
    ]


def test_path_containment_violation_is_not_opened(tmp_path):
    asset_directory = tmp_path / "assets"
    asset_directory.mkdir()
    outside_path = tmp_path / "outside.bin"
    outside_path.write_bytes(b"outside")

    result = c2d_image_hash.run_assessment(
        _task([outside_path], asset_directory)
    )

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["raw_signal"]["read_errors"] == [
        {"path": str(outside_path), "error": "PATH_CONTAINMENT_VIOLATION"}
    ]


def test_prohibited_input_is_rejected_recursively(tmp_path):
    image_path = tmp_path / "image.bin"
    image_path.write_bytes(b"image bytes")
    task = _task([image_path], tmp_path)
    task["nested"] = {"credential_hint": "not-a-real-credential"}

    result = c2d_image_hash.run_assessment(task)

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["error_detail"] == "PROHIBITED_INPUT_FIELD"
    assert result["raw_signal"]["pdq_status"] == AssessmentStatus.DEFERRED_IN_SCOPE
