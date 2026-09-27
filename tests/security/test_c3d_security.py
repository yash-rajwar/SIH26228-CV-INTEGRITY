"""Security-boundary tests for COMP-W-C3D."""

from __future__ import annotations

import ast
import json
import pathlib
import subprocess
import sys

import pytest

from assurance_system.constants import AssessmentStatus
from assurance_system.fixtures.hostile import pickle_payload


REPO_ROOT = pathlib.Path(__file__).parents[2]
WORKER_PATH = REPO_ROOT / "assurance_system" / "workers" / "c3d_safe_load.py"


def _base_task(model_path: pathlib.Path) -> dict:
    return {
        "schema_version": "worker-input-v1",
        "task": "C3D_SAFE_LOAD",
        "asset_paths": [str(model_path)],
        "format": "PYTORCH",
        "asset_directory": str(model_path.parent),
        "artifact_unit_definition_id": "pytorch-single-file-v1",
        "resource_limits": {
            "timeout_s": 60,
            "memory_mb": 4096,
            "max_fds": 32,
        },
        "identity_quality": "UNAVAILABLE",
    }


def _invoke_worker(tmp_path: pathlib.Path, task: dict) -> tuple[dict, int, str]:
    task_path = tmp_path / "security-task.json"
    result_path = tmp_path / "security-result.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "assurance_system.workers.c3d_safe_load",
            "--task-file",
            str(task_path),
            "--result-file",
            str(result_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result_path.is_file(), completed.stderr
    result = json.loads(result_path.read_text(encoding="utf-8"))
    return result, completed.returncode, completed.stderr[:1024]


def _import_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


def test_sec_001_hostile_pickle_boundary(tmp_path: pathlib.Path) -> None:
    fixture = pickle_payload.generate_hostile_pickle(
        str(tmp_path / "fix001-security"), seed=42
    )
    model_path = pathlib.Path(fixture["path"])

    result, returncode, _ = _invoke_worker(tmp_path, _base_task(model_path))

    assert returncode == 0
    assert result["assessment_status"] == AssessmentStatus.LOAD_BLOCKED
    assert result["raw_signal"]["fallback_attempted"] is False
    assert result["raw_signal"]["weights_only_flag_used"] is True
    assert result["access_mode"] == "BLACK_BOX"
    assert "does not prove malicious intent" in " ".join(result["non_claims"])


@pytest.mark.skip(reason="BLOCKED: TASK-022 — supervisor dispatch/orchestrator required")
def test_sec_002_oom_dispatch_requires_task_022() -> None:
    """SEC-002 requires real supervisor kill/continuation evidence."""


@pytest.mark.skip(reason="BLOCKED: TASK-022 — supervisor dispatch/orchestrator required")
def test_sec_003_timeout_dispatch_requires_task_022() -> None:
    """SEC-003 requires real supervisor timeout/continuation evidence."""


def test_supplemental_torch_import_is_not_module_level() -> None:
    tree = ast.parse(WORKER_PATH.read_text(encoding="utf-8"))
    top_level_imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level_imports.append(node.module)
    nested_torch_imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        and any(alias.name == "torch" for alias in node.names)
    ]
    assert "torch" not in top_level_imports
    assert len(nested_torch_imports) == 1


def test_supplemental_worker_has_no_network_import() -> None:
    tree = ast.parse(WORKER_PATH.read_text(encoding="utf-8"))
    assert _import_roots(tree).isdisjoint(
        {"socket", "requests", "urllib", "httpx", "aiohttp"}
    )


@pytest.mark.parametrize(
    "prohibited_key",
    ["key_path", "db_path", "PasswordValue", "api_secret", "CredentialBlob"],
)
def test_supplemental_prohibited_input_boundary(
    tmp_path: pathlib.Path, prohibited_key: str
) -> None:
    model_path = tmp_path / "unread.pt"
    model_path.write_bytes(b"")
    task = _base_task(model_path)
    sentinel = "MUST_NOT_LEAK"
    task["metadata"] = [{"nested": {prohibited_key: sentinel}}]

    result, returncode, stderr = _invoke_worker(tmp_path, task)

    assert returncode != 0
    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["raw_signal"] is None
    assert result["access_mode"] == "UNAVAILABLE"
    assert result["coverage_gap_clean_label"] is True
    assert "task input contains a prohibited field" in result["error_detail"]
    assert "Worker assessment failed" in stderr
    assert sentinel not in json.dumps(result)


def test_supplemental_worker_source_has_no_prohibited_output_fields() -> None:
    source = WORKER_PATH.read_text(encoding="utf-8")
    prohibited = {
        "risk_score",
        "aggregate_assurance",
        "compromise_probability",
        "threat_score",
        "malicious_probability",
    }
    assert all(field_name not in source for field_name in prohibited)
