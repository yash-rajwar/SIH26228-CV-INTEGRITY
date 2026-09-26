import importlib.util
import json
import os
import pathlib
import subprocess
import sys

import pytest

from assurance_system.fixtures.hostile import (
    benign,
    coco_geometry,
    exact_duplicate,
    onnx_path_traversal,
    schema_violation,
    sybil_corpus,
)


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
