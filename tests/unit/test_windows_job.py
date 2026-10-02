"""Bounded target-host tests for ACC-2026-10-02-01 Windows Jobs."""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

from assurance_system.config.loader import ResourceLimits
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.orchestrator import SupervisorOrchestrator
from assurance_system.supervisor.windows_job import WindowsWorkerJob


pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Windows Job Object tests require win32"
)

_CAPABILITY_LIMIT_MB = 128
_TEST_TIMEOUT_SECONDS = 30


def _launch_in_job(script: str, memory_limit_mb: int):
    job = WindowsWorkerJob(memory_limit_mb)
    process = subprocess.Popen(
        [sys.executable, "-c", script],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(pathlib.Path.cwd()),
        close_fds=True,
        creationflags=job.creation_flags,
    )
    try:
        job.assign_and_resume(process)
        stdout, stderr = process.communicate(timeout=_TEST_TIMEOUT_SECONDS)
        observation = job.observe()
        return process.returncode, stdout, stderr, observation, job
    except Exception:
        job.close()
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=_TEST_TIMEOUT_SECONDS)
        raise


def test_windows_job_enforces_bounded_process_memory_and_terminates() -> None:
    script = """
import sys
blocks = []
print('ALLOCATOR_READY', flush=True)
try:
    while True:
        blocks.append(bytearray(8 * 1024 * 1024))
except MemoryError:
    print('MEMORY_ERROR', flush=True)
    raise SystemExit(42)
"""
    returncode, stdout, _stderr, observation, job = _launch_in_job(
        script, _CAPABILITY_LIMIT_MB
    )
    try:
        assert b"ALLOCATOR_READY" in stdout
        assert returncode != 0
        assert observation.process_memory_limit_hit is True
        assert observation.mechanism == (
            "WINDOWS_JOB_OBJECT_PROCESS_COMMITTED_MEMORY"
        )
        assert observation.configured_process_memory_bytes == (
            _CAPABILITY_LIMIT_MB * 1024 * 1024
        )
        assert 0 < observation.peak_process_memory_bytes <= (
            _CAPABILITY_LIMIT_MB * 1024 * 1024
        )
        assert job.assigned and job.resumed
    finally:
        job.close()
    assert job.closed


def test_windows_job_allows_bounded_child_below_limit() -> None:
    script = "data = bytearray(8 * 1024 * 1024); print(len(data), flush=True)"
    returncode, stdout, stderr, observation, job = _launch_in_job(
        script, _CAPABILITY_LIMIT_MB
    )
    try:
        assert returncode == 0, stderr.decode("utf-8", errors="replace")
        assert stdout.strip() == b"8388608"
        assert observation.process_memory_limit_hit is False
        assert 0 < observation.peak_process_memory_bytes < (
            _CAPABILITY_LIMIT_MB * 1024 * 1024
        )
    finally:
        job.close()
    assert job.closed


@pytest.mark.parametrize("failure", ["creation", "configuration", "assignment", "resume"])
def test_windows_setup_failure_never_executes_child(tmp_path, monkeypatch, failure):
    """A real suspended child must be reaped without executing its marker code."""

    marker = tmp_path / "child-executed.txt"
    processes = []
    jobs = []
    from assurance_system.supervisor.orchestrator import _launch_worker_process
    real_popen = _launch_worker_process
    original_signatures = WindowsWorkerJob._configure_signatures
    original_close = WindowsWorkerJob.close

    def configure_signatures(job):
        original_signatures(job)
        jobs.append(job)
        if failure == "creation":
            monkeypatch.setattr(job._kernel32, "CreateJobObjectW", lambda *_args: None)
        elif failure == "configuration":
            monkeypatch.setattr(job._kernel32, "SetInformationJobObject", lambda *_args: False)
        elif failure == "assignment":
            monkeypatch.setattr(job._kernel32, "AssignProcessToJobObject", lambda *_args: False)
        elif failure == "resume":
            monkeypatch.setattr(job._kernel32, "ResumeThread", lambda *_args: 0xFFFFFFFF)

    def capture_popen(command, **kwargs):
        assert kwargs["creationflags"] == WindowsWorkerJob.creation_flags
        script = (
            "import sys; from pathlib import Path; "
            "sys.stderr.write('CHILD_EXECUTED\\n'); sys.stderr.flush(); "
            f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')"
        )
        process = real_popen([command[0], "-c", script], **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(WindowsWorkerJob, "_configure_signatures", configure_signatures)
    monkeypatch.setattr(
        "assurance_system.supervisor.orchestrator._launch_worker_process", capture_popen
    )
    store = EvidenceStore(str(tmp_path / "failure.sqlite3"))
    subject = SupervisorOrchestrator(
        store, AuditChainWriter(store), worker_temp_dir_base=str(tmp_path),
        python_executable=sys.executable,
    )
    try:
        result = subject._dispatch_worker(
            "assurance_system.workers.c2b_exact_hash",
            {"task": "C2B_EXACT_HASH"},
            ResourceLimits(_TEST_TIMEOUT_SECONDS, _CAPABILITY_LIMIT_MB, 8),
        )
        assert result["assessment_status"] == "ASSESSMENT_ERROR"
        assert result["raw_signal"]["failure_reason"] == "SPAWN_ERROR"
        assert not marker.exists()
        assert jobs and all(job.closed for job in jobs)
        assert all(job._job_handle is None and job._completion_port is None for job in jobs)
        for process in processes:
            assert process.poll() is not None
            # KILL_ON_JOB_CLOSE may report exit zero for a never-resumed child;
            # the trusted setup failure and absent execution marker determine
            # failure here, rather than that platform-specific exit value.
            assert process.stderr.closed
            assert process._handle.closed
            assert b"CHILD_EXECUTED" not in process._stderr_bytes
        assert not list(tmp_path.glob("assurance-worker-*"))
        assert len(processes) == (0 if failure in {"creation", "configuration"} else 1)
    finally:
        for job in jobs:
            original_close(job)
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=_TEST_TIMEOUT_SECONDS)
            if not process._handle.closed:
                process._handle.Close()
        store._conn.close()
