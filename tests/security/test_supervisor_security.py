"""TASK-022 supervisor trust-boundary security review."""

from __future__ import annotations

import ast
import pathlib
import re


REPO_ROOT = pathlib.Path(__file__).parents[2]
PRODUCTION_ROOT = REPO_ROOT / "assurance_system"
ORCHESTRATOR_PATH = PRODUCTION_ROOT / "supervisor" / "orchestrator.py"


def _production_python_files() -> list[pathlib.Path]:
    files = sorted(PRODUCTION_ROOT.rglob("*.py"))
    assert files
    return files


def test_supervisor_popen_contract_is_controlled() -> None:
    tree = ast.parse(ORCHESTRATOR_PATH.read_text(encoding="utf-8"))
    popen_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Popen"
    ]
    assert len(popen_calls) == 1
    keywords = {keyword.arg: keyword.value for keyword in popen_calls[0].keywords}
    assert "shell" not in keywords
    assert {
        "stdin",
        "stdout",
        "stderr",
        "close_fds",
        "cwd",
        "env",
    }.issubset(keywords)
    assert isinstance(keywords["close_fds"], ast.Constant)
    assert keywords["close_fds"].value is True


def test_supervisor_imports_no_network_model_or_asset_parser() -> None:
    tree = ast.parse(ORCHESTRATOR_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "socket",
            "urllib",
            "http",
            "requests",
            "torch",
            "onnx",
            "onnxruntime",
            "cv2",
            "PIL",
            "numpy",
            "pickle",
        }
    )


def test_supervisor_never_calls_worker_analysis_in_process() -> None:
    source = ORCHESTRATOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    worker_imports = {
        module
        for module in imported_modules
        if module.startswith("assurance_system.workers")
    }
    assert worker_imports == {"assurance_system.workers.base"}
    assert "run_assessment(" not in source
    assert "torch.load(" not in source
    assert "onnx.load(" not in source


def test_workers_have_no_evidence_store_write_path() -> None:
    workers = PRODUCTION_ROOT / "workers"
    for path in workers.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "EvidenceStore" not in source, path
        assert "write_evidence_record" not in source, path


def test_production_guards_have_zero_matches() -> None:
    patterns = {
        "unrestricted load": re.compile(r"weights_only\s*=\s*False"),
        "prohibited score": re.compile(r"\brisk_score\b"),
        "subprocess shell": re.compile(r"shell\s*=\s*True"),
    }
    matches: dict[str, list[str]] = {name: [] for name in patterns}
    for path in _production_python_files():
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for name, pattern in patterns.items():
                if pattern.search(line):
                    matches[name].append(
                        f"{path.relative_to(REPO_ROOT)}:{line_number}"
                    )
    assert matches == {name: [] for name in patterns}


def test_secret_paths_are_only_removed_not_read() -> None:
    tree = ast.parse(ORCHESTRATOR_PATH.read_text(encoding="utf-8"))
    environment_reads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "os"
        and node.value.attr == "environ"
    ]
    assert environment_reads == []
    source = ORCHESTRATOR_PATH.read_text(encoding="utf-8")
    assert 'clean_env.pop("ASSURANCE_KEY_PATH", None)' in source
    assert 'clean_env.pop("ASSURANCE_DB_PATH", None)' in source
