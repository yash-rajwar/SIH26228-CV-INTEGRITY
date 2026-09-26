import pathlib

from assurance_system.constants import AssessmentStatus
from assurance_system.fixtures.hostile import exact_duplicate
from assurance_system.workers import c2b_exact_hash


def _task(asset_paths: list[pathlib.Path], asset_directory: pathlib.Path) -> dict:
    return {
        "schema_version": "worker-input-v1",
        "task": "C2B_EXACT_HASH",
        "asset_paths": [str(path) for path in asset_paths],
        "asset_directory": str(asset_directory),
        "resource_limits": {
            "timeout_s": 30,
            "memory_mb": 512,
            "max_fds": 32,
        },
    }


def test_ut_c2b_001_known_duplicate_pair(tmp_path):
    manifest = exact_duplicate.generate_duplicates(
        str(tmp_path), seed=42, pair_count=1
    )
    names = manifest["expected_result"]["expected_duplicate_files"][0]
    paths = [tmp_path / name for name in names]

    result = c2b_exact_hash.run_assessment(_task(paths, tmp_path))

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["duplicate_group_count"] == 1
    duplicate_paths = next(iter(result["raw_signal"]["duplicate_groups"].values()))
    assert duplicate_paths == [str(path) for path in paths]


def test_ut_c2b_002_known_nonduplicate_control(tmp_path):
    manifest = exact_duplicate.generate_nonduplicates(
        str(tmp_path), seed=42, file_count=2
    )
    paths = [
        tmp_path / name for name in manifest["expected_result"]["expected_files"]
    ]

    result = c2b_exact_hash.run_assessment(_task(paths, tmp_path))

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["duplicate_group_count"] == 0
    assert len(result["raw_signal"]["file_digest_map"]) == 2


def test_ut_c2b_003_path_containment_violation_is_excluded(tmp_path):
    asset_directory = tmp_path / "assets"
    asset_directory.mkdir()
    valid_path = asset_directory / "valid.bin"
    valid_path.write_bytes(b"inside")
    outside_path = tmp_path / "outside.bin"
    outside_path.write_bytes(b"outside")

    result = c2b_exact_hash.run_assessment(
        _task([valid_path, outside_path], asset_directory)
    )

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["read_errors"] == [
        {"path": str(outside_path), "error": "PATH_CONTAINMENT_VIOLATION"}
    ]
    assert str(outside_path) not in result["raw_signal"]["file_digest_map"]
    assert str(valid_path) in result["raw_signal"]["file_digest_map"]


def test_ut_c2b_004_unreadable_file_does_not_hide_readable_results(tmp_path):
    valid_path = tmp_path / "valid.bin"
    valid_path.write_bytes(b"readable")
    missing_path = tmp_path / "missing.bin"

    result = c2b_exact_hash.run_assessment(
        _task([valid_path, missing_path], tmp_path)
    )

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["read_errors"][0]["path"] == str(missing_path)
    assert str(valid_path) in result["raw_signal"]["file_digest_map"]
    assert result["raw_signal"]["total_files_processed"] == 1


def test_ut_c2b_005_pdq_is_always_deferred(tmp_path):
    valid_path = tmp_path / "valid.bin"
    valid_path.write_bytes(b"content")

    result = c2b_exact_hash.run_assessment(_task([valid_path], tmp_path))

    assert result["raw_signal"]["pdq_status"] == AssessmentStatus.DEFERRED_IN_SCOPE
    assert any("DEFERRED_IN_SCOPE" in item for item in result["limitations"])
    assert any("DEFERRED_IN_SCOPE" in item for item in result["non_claims"])


def test_ut_c2b_006_coverage_gap_on_every_output(tmp_path):
    valid_path = tmp_path / "valid.bin"
    valid_path.write_bytes(b"content")
    missing_path = tmp_path / "missing.bin"
    outside_directory = tmp_path / "other"
    outside_directory.mkdir()
    outputs = [
        c2b_exact_hash.run_assessment(_task([valid_path], tmp_path)),
        c2b_exact_hash.run_assessment(_task([missing_path], tmp_path)),
        c2b_exact_hash.run_assessment(_task([valid_path], outside_directory)),
    ]

    for result in outputs:
        assert result["coverage_gap_clean_label"] is True
        assert result["raw_signal"]["pdq_status"] == AssessmentStatus.DEFERRED_IN_SCOPE
        assert result["limitations"] == c2b_exact_hash.C2B_LIMITATIONS
        assert result["non_claims"] == c2b_exact_hash.C2B_NON_CLAIMS


def test_repro_002_same_file_has_same_digest(tmp_path):
    path = tmp_path / "stable.bin"
    path.write_bytes(bytes(range(256)))
    task = _task([path], tmp_path)

    first = c2b_exact_hash.run_assessment(task)
    second = c2b_exact_hash.run_assessment(task)

    first_digest = first["raw_signal"]["file_digest_map"][str(path)]
    second_digest = second["raw_signal"]["file_digest_map"][str(path)]
    assert first_digest == second_digest
    assert len(first_digest) == 64


def test_empty_asset_list_is_completed_without_positive_claim(tmp_path):
    result = c2b_exact_hash.run_assessment(_task([], tmp_path))

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["raw_signal"]["total_files_processed"] == 0
    assert result["raw_signal"]["pdq_status"] == AssessmentStatus.DEFERRED_IN_SCOPE
    assert "Exact duplicate presence does not imply flooding attack or malicious intent." in (
        result["non_claims"]
    )
