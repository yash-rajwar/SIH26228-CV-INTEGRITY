"""
test_repository_structure.py
Authority: 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md TASK-002 acceptance criteria
           10_TECHNICAL_SPECIFICATION_SIH26228.md §2.2 (module structure is authoritative)

Verifies that every path required by the technical specification exists.
This test can run from Day 1 without any implementation being in place.
It fails if any required path is missing or if extraneous architecture is present.
"""

import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent


REQUIRED_PATHS = [
    # Package roots
    "assurance_system/__init__.py",
    "assurance_system/exceptions.py",
    "assurance_system/constants.py",

    # Config
    "assurance_system/config/__init__.py",
    "assurance_system/config/loader.py",
    "assurance_system/config/system_config.yaml",
    "assurance_system/config/resource_limits.yaml",
    "assurance_system/config/supported_formats.yaml",

    # Schema
    "assurance_system/schema/evidence_record_v1.schema.json",
    "assurance_system/schema/worker_input_v1.schema.json",
    "assurance_system/schema/worker_output_v1.schema.json",
    "assurance_system/schema/provenance_record_v1.schema.json",
    "assurance_system/schema/finding_v1.schema.json",
    "assurance_system/schema/deferred_record_v1.schema.json",

    # Supervisor
    "assurance_system/supervisor/__init__.py",
    "assurance_system/supervisor/orchestrator.py",
    "assurance_system/supervisor/schema_validator.py",
    "assurance_system/supervisor/reference_manager.py",
    "assurance_system/supervisor/audit_chain.py",
    "assurance_system/supervisor/evidence_store.py",
    "assurance_system/supervisor/provenance.py",
    "assurance_system/supervisor/interpretation.py",
    "assurance_system/supervisor/capability_declaration.py",

    # Workers
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

    # Interfaces
    "assurance_system/interfaces/__init__.py",
    "assurance_system/interfaces/cli.py",
    "assurance_system/interfaces/dashboard.py",
    "assurance_system/interfaces/exporter.py",

    # Fixtures
    "assurance_system/fixtures/__init__.py",
    "assurance_system/fixtures/generator.py",
    "assurance_system/fixtures/hostile/__init__.py",
    "assurance_system/fixtures/hostile/pickle_payload.py",
    "assurance_system/fixtures/hostile/onnx_path_traversal.py",
    "assurance_system/fixtures/hostile/archive_bomb.py",
    "assurance_system/fixtures/hostile/coco_geometry.py",
    "assurance_system/fixtures/hostile/yolo_geometry.py",

    # Top-level
    "cli.py",
    "pyproject.toml",
    "requirements.txt",
    "wheelhouse/README.md",
    "artifact_unit_defs/README.md",

    # Tests
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
    "tests/negative/__init__.py",
    "tests/security/__init__.py",
    "tests/offline/__init__.py",

    # Docs
    "docs/SETUP.md",
    "docs/ARCHITECTURE_SPECIFICATION.md",
    "docs/TECHNICAL_SPECIFICATION.md",
    "docs/MVP_IMPLEMENTATION_PLAN.md",

    # Project control
    ".gitignore",
    "NOTICES.md",
]


@pytest.mark.parametrize("rel_path", REQUIRED_PATHS)
def test_required_path_exists(rel_path):
    """Every path in the authoritative module structure must exist."""
    target = REPO_ROOT / rel_path
    assert target.exists(), (
        f"Required path missing: {rel_path}\n"
        f"Expected at: {target}\n"
        f"See: 10_TECHNICAL_SPECIFICATION_SIH26228.md §2.2"
    )


def test_no_prohibited_directories():
    """
    No extraneous enterprise-style directories should exist.
    Implementation agents must not create directories outside the approved layout.
    """
    prohibited = ["src", "app", "backend", "frontend", "services", "containers"]
    for name in prohibited:
        target = REPO_ROOT / name
        assert not target.exists(), (
            f"Prohibited directory found: {name}/\n"
            "Implementation must not invent layout outside §10 §2.2."
        )
