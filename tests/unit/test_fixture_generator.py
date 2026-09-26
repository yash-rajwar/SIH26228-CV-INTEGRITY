import importlib.util
import json
import os
import pathlib
import pickle
import subprocess
import sys
import zipfile

import pytest

from assurance_system.fixtures.hostile import (
    benign,
    coco_geometry,
    exact_duplicate,
    onnx_path_traversal,
    pickle_payload,
    schema_violation,
    sybil_corpus,
    yolo_geometry,
)


TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None


def _tree_bytes(root: pathlib.Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_repro_006_coco_generation_is_byte_identical(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    coco_geometry.generate_coco_geometry(str(first), seed=42)
    coco_geometry.generate_coco_geometry(str(second), seed=42)
    assert _tree_bytes(first) == _tree_bytes(second)


def test_fix_008_manifest_lists_all_geometry_violations(tmp_path):
    manifest = coco_geometry.generate(str(tmp_path), seed=42)
    assert manifest["is_synthetic"] is True
    assert set(manifest["expected_result"]["violations_by_type"]) == set(
        coco_geometry.EXPECTED_VIOLATIONS
    )
    assert manifest["expected_result"]["violation_count"] == 9


def test_fix_010_duplicate_groups_match(tmp_path):
    manifest = exact_duplicate.generate_duplicates(str(tmp_path), seed=42)
    expected = manifest["expected_result"]
    assert expected["expected_duplicate_group_count"] == 3
    for group in expected["expected_duplicate_files"]:
        contents = [(tmp_path / filename).read_bytes() for filename in group]
        assert len(set(contents)) == 1


def test_fix_011_nonduplicate_control_is_distinct(tmp_path):
    manifest = exact_duplicate.generate_nonduplicates(str(tmp_path), seed=42)
    files = manifest["expected_result"]["expected_files"]
    contents = [(tmp_path / filename).read_bytes() for filename in files]
    assert manifest["expected_result"]["expected_duplicate_group_count"] == 0
    assert len(set(contents)) == len(contents)


def test_fix_012_single_source_hhi(tmp_path):
    manifest = sybil_corpus.generate_single_source(str(tmp_path), seed=42)
    assert manifest["is_synthetic"] is True
    assert manifest["expected_result"]["expected_hhi"] == 1.0


def test_fix_018_prohibited_aggregate_field_is_present():
    field_name = "_".join(("risk", "score"))
    record = schema_violation.make_risk_score_record()
    assert field_name in record
    assert record["is_synthetic"] is True


def test_fix_019_false_coverage_gap_label_is_present():
    record = schema_violation.make_false_coverage_gap_record()
    assert record["coverage_gap_clean_label"] is False
    assert record["is_synthetic"] is True


def test_fixture_generator_cli_smoke(tmp_path):
    repository_root = pathlib.Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        value
        for value in (
            str(repository_root),
            environment.get("PYTHONPATH", ""),
        )
        if value
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "assurance_system.fixtures.generator",
            "coco-geometry",
            "--output",
            str(tmp_path),
            "--seed",
            "42",
        ],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["is_synthetic"] is True


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="BLOCKED: torch not installed")
def test_fix_001_hostile_pickle_triggers_unpickling_error(tmp_path):
    import torch

    fixture = pickle_payload.generate_hostile_pickle(str(tmp_path / "first"), seed=42)
    repeated = pickle_payload.generate_hostile_pickle(
        str(tmp_path / "second"), seed=42
    )
    payload = pathlib.Path(fixture["path"]).read_bytes()
    assert payload == pathlib.Path(repeated["path"]).read_bytes()
    assert payload
    assert pickle_payload.HOSTILE_FIXTURE_WARNING.encode("utf-8") in payload
    assert fixture["is_synthetic"] is True
    with pytest.raises((RuntimeError, pickle.UnpicklingError)):
        torch.load(fixture["path"], weights_only=True, map_location="cpu")


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="BLOCKED: torch not installed")
def test_fix_002_scaled_archive_is_weights_only_loadable(tmp_path):
    import torch

    fixture = pickle_payload.generate_oom_trigger(
        str(tmp_path / "first"), seed=42, memory_limit_mb=8
    )
    repeated = pickle_payload.generate_oom_trigger(
        str(tmp_path / "second"), seed=42, memory_limit_mb=8
    )
    path = pathlib.Path(fixture["path"])
    assert path.read_bytes() == pathlib.Path(repeated["path"]).read_bytes()
    declared_bytes = fixture["expected_result"]["declared_storage_bytes"]
    with zipfile.ZipFile(path, "r") as archive:
        storage = next(
            info for info in archive.infolist() if info.filename.endswith("/data/0")
        )
    assert storage.file_size == declared_bytes
    assert declared_bytes > 8 * 1024 * 1024
    loaded = torch.load(path, weights_only=True, map_location="cpu")
    assert loaded.numel() == fixture["expected_result"]["declared_shape"][0]


def test_fix_003_hang_trigger_times_out_under_control(tmp_path):
    fixture = pickle_payload.generate_hang_trigger(str(tmp_path / "first"), seed=42)
    repeated = pickle_payload.generate_hang_trigger(
        str(tmp_path / "second"), seed=42
    )
    assert pathlib.Path(fixture["path"]).read_bytes() == pathlib.Path(
        repeated["path"]
    ).read_bytes()
    process = subprocess.Popen(
        [sys.executable, fixture["path"]],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    timed_out = False
    try:
        process.wait(timeout=0.25)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    assert timed_out is True
    assert fixture["expected_result"]["assessment_status"] == "ASSESSMENT_ERROR"


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="BLOCKED: torch not installed")
def test_fix_015_benign_pytorch_loads_with_weights_only(tmp_path):
    import torch

    fixture = pickle_payload.generate_benign_pytorch(str(tmp_path / "first"), seed=42)
    repeated = pickle_payload.generate_benign_pytorch(
        str(tmp_path / "second"), seed=42
    )
    assert pathlib.Path(fixture["path"]).read_bytes() == pathlib.Path(
        repeated["path"]
    ).read_bytes()
    loaded = torch.load(fixture["path"], weights_only=True, map_location="cpu")
    assert tuple(loaded["weight"].shape) == (3, 3)
    assert bool(torch.count_nonzero(loaded["weight"])) is False
    assert fixture["expected_result"]["expected_fallback_attempted"] is False


def test_fix_009_s_is_reproducible_and_lists_segmentation_violations(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_manifest = yolo_geometry.generate_segmentation(str(first), seed=42)
    second_manifest = yolo_geometry.generate_segmentation(str(second), seed=42)
    assert _tree_bytes(first) == _tree_bytes(second)
    assert first_manifest == {
        **second_manifest,
        "path": str(first / "yolo_segmentation_violations.txt"),
    }
    assert first_manifest["is_synthetic"] is True
    assert first_manifest["expected_result"]["violations_by_type"] == (
        yolo_geometry.SEGMENTATION_EXPECTED_VIOLATIONS
    )


def test_yolo_pose_and_obb_remain_outside_frozen_scope(tmp_path):
    with pytest.raises(NotImplementedError, match="UNSUPPORTED"):
        yolo_geometry.generate_pose(str(tmp_path), seed=42)
    with pytest.raises(NotImplementedError, match="UNSUPPORTED"):
        yolo_geometry.generate_obb(str(tmp_path), seed=42)


@pytest.mark.skipif(
    importlib.util.find_spec("onnx") is None,
    reason="BLOCKED: onnx package not installed",
)
def test_onnx_fixture_family_and_benign_control(tmp_path):
    hostile_manifest = onnx_path_traversal.generate(str(tmp_path / "hostile"), 42)
    benign_manifest = benign.generate_onnx(str(tmp_path / "benign"), 42)
    assert hostile_manifest["is_synthetic"] is True
    assert benign_manifest["expected_result"]["expected_assessment_status"] == (
        "STRUCTURAL_VALID"
    )
