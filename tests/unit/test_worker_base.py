"""UT-BASE-001 through UT-BASE-008."""

import json
import os
import pathlib
import subprocess
import sys

import pytest

from assurance_system.workers.base import build_worker_output, is_within_directory


_REQUIRED_OUTPUT_FIELDS = {
    "schema_version",
    "worker_id",
    "assessment_status",
    "raw_signal",
    "access_mode",
    "artifact_unit_id",
    "coverage_gap_clean_label",
    "limitations",
    "non_claims",
    "dependency_declaration",
    "assessment_timestamp",
    "error_detail",
}


def _valid_output(**overrides):
    arguments = {
        "worker_id": "COMP-W-TEST",
        "assessment_status": "COMPLETED",
        "raw_signal": {"x": 1},
        "limitations": ["lim1"],
        "non_claims": ["nc1"],
    }
    arguments.update(overrides)
    return build_worker_output(**arguments)


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    repository_root = str(pathlib.Path(__file__).resolve().parents[2])
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        repository_root + os.pathsep + existing if existing else repository_root
    )
    return env


def test_ut_base_001_builds_complete_output():
    result = _valid_output()
    assert isinstance(result, dict)
    assert _REQUIRED_OUTPUT_FIELDS.issubset(result)
    assert result["coverage_gap_clean_label"] is True
    assert result["schema_version"] == "worker-output-v1"


def test_ut_base_002_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations must be non-empty"):
        _valid_output(limitations=[])


def test_ut_base_003_rejects_empty_non_claims():
    with pytest.raises(ValueError, match="non_claims must be non-empty"):
        _valid_output(non_claims=[])


def test_ut_base_004_accepts_contained_path():
    assert is_within_directory("/tmp/assets/file.json", "/tmp/assets") is True


def test_ut_base_005_rejects_path_traversal():
    assert (
        is_within_directory("/tmp/assets/../etc/passwd", "/tmp/assets") is False
    )


def test_ut_base_006_rejects_symlink_escape(tmp_path):
    asset_directory = tmp_path / "assets"
    outside_directory = tmp_path / "outside"
    asset_directory.mkdir()
    outside_directory.mkdir()
    outside_file = outside_directory / "secret.txt"
    outside_file.write_text("outside", encoding="utf-8")
    link = asset_directory / "escape.txt"
    link.symlink_to(outside_file)
    assert is_within_directory(str(link), str(asset_directory)) is False


def test_ut_base_007_crash_writes_assessment_error(tmp_path):
    script = tmp_path / "crashing_worker.py"
    script.write_text(
        "from assurance_system.workers.base import main\n"
        "def run_assessment(_task):\n"
        "    raise RuntimeError('test crash')\n"
        "if __name__ == '__main__':\n"
        "    main(run_assessment)\n",
        encoding="utf-8",
    )
    task_path = tmp_path / "task.json"
    result_path = tmp_path / "result.json"
    task_path.write_text(
        json.dumps({"schema_version": "worker-input-v1", "task": "COMP-W-TEST"}),
        encoding="utf-8",
    )

    process = subprocess.Popen(
        [
            sys.executable,
            str(script),
            "--task-file",
            str(task_path),
            "--result-file",
            str(result_path),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        cwd=str(tmp_path),
        env=_subprocess_env(),
    )
    stdout, _ = process.communicate(timeout=10)
    result = json.loads(result_path.read_text(encoding="utf-8"))

    assert process.returncode == 1
    assert stdout == b""
    assert result["assessment_status"] == "ASSESSMENT_ERROR"
    assert result["error_detail"] is not None


def test_ut_base_008_timeout_kill_does_not_hang_or_leave_files(tmp_path):
    worker_dir = tmp_path / "worker"
    worker_dir.mkdir()
    script = worker_dir / "sleeping_worker.py"
    script.write_text(
        "import time\n"
        "from assurance_system.workers.base import main\n"
        "def run_assessment(_task):\n"
        "    time.sleep(120)\n"
        "if __name__ == '__main__':\n"
        "    main(run_assessment)\n",
        encoding="utf-8",
    )
    task_path = worker_dir / "task.json"
    result_path = worker_dir / "result.json"
    task_path.write_text(
        json.dumps({"schema_version": "worker-input-v1", "task": "COMP-W-TEST"}),
        encoding="utf-8",
    )
    process = subprocess.Popen(
        [
            sys.executable,
            str(script),
            "--task-file",
            str(task_path),
            "--result-file",
            str(result_path),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        close_fds=True,
        cwd=str(worker_dir),
        env=_subprocess_env(),
    )
    try:
        process.communicate(timeout=2)
        pytest.fail("sleeping worker unexpectedly completed")
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)

    timeout_result = build_worker_output(
        worker_id="COMP-W-TEST",
        assessment_status="ASSESSMENT_ERROR",
        raw_signal=None,
        limitations=["Worker exceeded the configured timeout."],
        non_claims=["No positive assurance conclusion is available."],
        error_detail="TIMEOUT: exceeded 2 seconds",
    )
    result_path.write_text(json.dumps(timeout_result), encoding="utf-8")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["assessment_status"] == "ASSESSMENT_ERROR"
    assert process.poll() is not None

    for path in worker_dir.iterdir():
        path.unlink()
    assert list(worker_dir.iterdir()) == []
