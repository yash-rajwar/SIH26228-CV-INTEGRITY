import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).parent.parent.parent

REQUIRED_PATHS = [
    "assurance_system/__init__.py",
    "assurance_system/exceptions.py",
    "assurance_system/constants.py",
    "assurance_system/config/__init__.py",
    "assurance_system/config/loader.py",
    "assurance_system/config/system_config.yaml",
    "assurance_system/config/resource_limits.yaml",
    "assurance_system/config/supported_formats.yaml",
    "assurance_system/schema/evidence_record_v1.schema.json",
    "assurance_system/schema/worker_input_v1.schema.json",
    "assurance_system/schema/worker_output_v1.schema.json",
    "assurance_system/schema/provenance_record_v1.schema.json",
    "assurance_system/schema/finding_v1.schema.json",
    "assurance_system/schema/deferred_record_v1.schema.json",
    "assurance_system/supervisor/__init__.py",
    "assurance_system/supervisor/orchestrator.py",
    "assurance_system/supervisor/schema_validator.py",
    "assurance_system/supervisor/reference_manager.py",
    "assurance_system/supervisor/audit_chain.py",
    "assurance_system/supervisor/evidence_store.py",
    "assurance_system/supervisor/provenance.py",
    "assurance_system/supervisor/interpretation.py",
    "assurance_system/supervisor/capability_declaration.py",
    "assurance_system/workers/__init__.py",
    "assurance_system/workers/base.py",
    "assurance_system/workers/c2a_structural.py",
    "assurance_system/workers/c2b_exact_hash.py",
    "assurance_system/workers/c2c_concentration.py",
    "assurance_system/workers/c2d_image_hash.py",
    "assurance_system/workers/c3a_artifact_unit.py",
    "assurance_system/workers/c3b_model_hash.py",
    "assurance_system/workers/c3c_onnx_structural.py",
    "assurance_system/workers/c3d_safe_load.py",
    "assurance_system/interfaces/__init__.py",
    "assurance_system/interfaces/cli.py",
    "assurance_system/interfaces/dashboard.py",
    "assurance_system/interfaces/exporter.py",
    "assurance_system/fixtures/__init__.py",
    "assurance_system/fixtures/generator.py",
    "assurance_system/fixtures/hostile/__init__.py",
    "assurance_system/fixtures/hostile/pickle_payload.py",
    "assurance_system/fixtures/hostile/onnx_path_traversal.py",
    "assurance_system/fixtures/hostile/archive_bomb.py",
    "assurance_system/fixtures/hostile/coco_geometry.py",
    "assurance_system/fixtures/hostile/yolo_geometry.py",
    "cli.py",
    "pyproject.toml",
    "requirements.txt",
    "wheelhouse/README.md",
    "artifact_unit_defs/README.md",
    ".gitignore",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
    "tests/negative/__init__.py",
    "tests/security/__init__.py",
    "tests/offline/__init__.py",
]


@pytest.mark.parametrize("rel_path", REQUIRED_PATHS)
def test_required_path_exists(rel_path):
    full = REPO_ROOT / rel_path
    assert full.exists(), f"Required path missing: {rel_path}"


def test_no_prohibited_directory_exists():
    prohibited = ["src/", "app/", "backend/", "frontend/"]
    for name in prohibited:
        assert not (REPO_ROOT / name).exists(), (
            f"Prohibited directory found (not in approved layout): {name}"
        )


def test_assurance_system_importable():
    import assurance_system  # noqa: F401
