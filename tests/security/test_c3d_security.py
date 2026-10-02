"""Security-boundary tests for COMP-W-C3D."""

from __future__ import annotations

import ast
import dataclasses
import json
import pathlib
import subprocess
import sys
import threading
import time

import pytest

from assurance_system.config.loader import ConfigLoader
from assurance_system.constants import AssessmentStatus, AuditEventType
from assurance_system.fixtures.hostile import pickle_payload
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.orchestrator import SupervisorOrchestrator
from assurance_system.supervisor.interpretation import T05D_NON_CLAIM_TEXT
from assurance_system.supervisor.windows_job import WindowsWorkerJob


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


_SEC_002_MEMORY_LIMIT_MB = 768


class _BoundedMemoryConfig(ConfigLoader):
    def get_resource_limits(self, task_type):
        limits = super().get_resource_limits(task_type)
        if task_type == "C3D_SAFE_LOAD":
            return dataclasses.replace(
                limits, memory_limit_mb=_SEC_002_MEMORY_LIMIT_MB
            )
        return limits


def test_sec_002_oom_dispatch_requires_task_022(tmp_path, monkeypatch) -> None:
    """Real FIX-002 crosses the enforced Job ceiling through COMP-SUP."""

    if sys.platform != "win32":
        pytest.skip(
            "SEC-002 Windows acceptance requires the approved Windows target"
        )

    oom_fixture = pickle_payload.generate_oom_trigger(
        str(tmp_path / "fix002"),
        seed=42,
        memory_limit_mb=_SEC_002_MEMORY_LIMIT_MB,
    )
    benign_fixture = pickle_payload.generate_benign_pytorch(
        str(tmp_path / "fix015"), seed=42
    )
    manifest = tmp_path / "submission.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "submission-manifest-v1",
                "asset_directory": str(tmp_path.resolve()),
                "assets": [
                    {
                        "asset_id": "fix002-model",
                        "asset_paths": [oom_fixture["path"]],
                        "format": "PYTORCH",
                        "is_synthetic": True,
                        "artifact_unit_definition_id": "pytorch-single-file-v1",
                    },
                    {
                        "asset_id": "fix015-control",
                        "asset_paths": [benign_fixture["path"]],
                        "format": "PYTORCH",
                        "is_synthetic": True,
                        "artifact_unit_definition_id": "pytorch-single-file-v1",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    real_popen = subprocess.Popen
    processes = []

    def capture_process(command, **kwargs):
        process = real_popen(command, **kwargs)
        processes.append((command[2], process, pathlib.Path(kwargs["cwd"])))
        return process

    monkeypatch.setattr(
        "assurance_system.supervisor.orchestrator.subprocess.Popen",
        capture_process,
    )
    jobs = []

    def create_job(limits):
        job = WindowsWorkerJob(limits.memory_limit_mb)
        jobs.append(job)
        return job

    worker_temp = tmp_path / "worker-temp"
    worker_temp.mkdir()
    store = EvidenceStore(str(tmp_path / "sec002.sqlite3"))
    audit = AuditChainWriter(store)
    subject = SupervisorOrchestrator(
        store,
        audit,
        config_loader=_BoundedMemoryConfig(),
        worker_temp_dir_base=str(worker_temp),
        python_executable=sys.executable,
    )
    monkeypatch.setattr(subject, "_create_worker_containment", create_job)
    try:
        summary = subject.run_pipeline(str(manifest))
        evidence = store.query_evidence("fix002-model", "C3D")
        finding = store.query_findings("fix002-model")[0]
        control = store.query_evidence("fix015-control", "C3D")
        audit_events = store.query_audit_trail()
        c3d_processes = [
            process
            for module, process, _directory in processes
            if module == "assurance_system.workers.c3d_safe_load"
        ]

        assert oom_fixture["expected_result"]["configured_memory_limit_mb"] == (
            _SEC_002_MEMORY_LIMIT_MB
        )
        assert oom_fixture["expected_result"]["declared_storage_bytes"] > (
            _SEC_002_MEMORY_LIMIT_MB * 1024 * 1024
        )
        assert summary.assets_processed == 2
        assert summary.workers_dispatched == summary.evidence_records_written == 6
        assert summary.worker_results_rejected == 0
        assert summary.findings_written == 2
        assert summary.provenance_records_written == 2
        assert len(c3d_processes) == 2
        assert c3d_processes[0].returncode != 0
        assert c3d_processes[1].returncode == 0
        assert all(process.poll() is not None for process in c3d_processes)
        assert all(process.stderr.closed for process in c3d_processes)
        assert all(process._handle.closed for _, process, _ in processes)
        assert all(job.closed for job in jobs)
        assert list(worker_temp.iterdir()) == []
        assert all(not directory.exists() for _, _, directory in processes)

        assert evidence["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
        assert evidence["access_mode"] == "UNAVAILABLE"
        assert evidence["coverage_gap_clean_label"] == 1
        assert evidence["is_synthetic"] == 1
        assert evidence["record_digest"]
        assert evidence["limitations"] and evidence["non_claims"]
        signal = evidence["raw_signal"]
        assert signal["failure_reason"] == "MEMORY_LIMIT_EXCEEDED", (
            evidence["limitations"], evidence["non_claims"], signal
        )
        assert signal["resource_limit_mechanism"] == (
            "WINDOWS_JOB_OBJECT_PROCESS_COMMITTED_MEMORY"
        )
        assert signal["configured_process_memory_bytes"] == (
            _SEC_002_MEMORY_LIMIT_MB * 1024 * 1024
        )
        assert signal["process_memory_limit_hit"] is True
        assert 0 < signal["peak_process_memory_bytes"] <= (
            _SEC_002_MEMORY_LIMIT_MB * 1024 * 1024
        )

        assert finding["detection_status"] == "UNAVAILABLE"
        assert finding["interpretation_status"] == "UNAVAILABLE"
        assert finding["analyst_disposition_prompt"] == "UNAVAILABLE_NO_DECISION"
        assert finding["coverage_gap_clean_label"] == 1
        assert finding["global_backdoor_absence_not_established"] == 1
        assert T05D_NON_CLAIM_TEXT in finding["non_claims"]
        assert control["assessment_status"] == AssessmentStatus.LOAD_SUCCESS
        assert control["raw_signal"]["weights_only_flag_used"] is True
        assert control["raw_signal"]["fallback_attempted"] is False
        assert audit.verify_chain_integrity().intact
        assert audit_events[-1]["event_type"] == AuditEventType.PIPELINE_RUN_COMPLETE
        assert AuditEventType.PIPELINE_RUN_ERROR not in {
            event["event_type"] for event in audit_events
        }
        assert subject._pipeline_active is False
        assert subject._accepted_records == subject._asset_synthetic == {}

        report = {
            "fixture_id": oom_fixture["fixture_id"],
            "fixture_seed": 42,
            "configured_memory_limit_mb": _SEC_002_MEMORY_LIMIT_MB,
            "declared_storage_bytes": oom_fixture["expected_result"][
                "declared_storage_bytes"
            ],
            "worker_exit_code": c3d_processes[0].returncode,
            "control_worker_exit_code": c3d_processes[1].returncode,
            "summary": dataclasses.asdict(summary),
            "evidence": evidence,
            "finding": finding,
            "control_evidence": control,
            "audit_events": audit_events,
        }
        (tmp_path / "sec002-observed.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    finally:
        for _module, process, _directory in processes:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=_CHILD_CLEANUP_DEADLINE_SECONDS)
        for job in jobs:
            job.close()
        store._conn.close()


_CI_TIMEOUT_SECONDS = 1
_CHILD_READY_DEADLINE_SECONDS = 30
_CHILD_CLEANUP_DEADLINE_SECONDS = 10
_READY_SIGNAL = b"C3D_TEST_LOAD_READY\n"


class _ShortTimeoutConfig(ConfigLoader):
    """Override only the named C3D timeout for this bounded test."""

    def get_resource_limits(self, task_type):
        limits = super().get_resource_limits(task_type)
        if task_type == "C3D_SAFE_LOAD":
            return dataclasses.replace(limits, timeout_seconds=_CI_TIMEOUT_SECONDS)
        return limits


def _run_controlled_c3d_pipeline(tmp_path, monkeypatch, condition):
    """Real supervisor/IPC/store/audit/C5, with a test-only child load hook.

    No dispatcher response is mocked. The child runs unchanged C3D main(),
    imports real Torch, and checks the restricted-load flags before executing
    FIX-003 or raising a bounded MemoryError without allocating large memory.
    This is dispatch evidence, not proof of a naturally hanging checkpoint or
    target-host OOM enforcement. All other workers run without instrumentation.
    """

    model_fixture = pickle_payload.generate_benign_pytorch(
        str(tmp_path / "model"), seed=42
    )
    hang_fixture = pickle_payload.generate_hang_trigger(
        str(tmp_path / "fix003"), seed=42
    )
    control = tmp_path / "labels.txt"
    control.write_text("0 0.5 0.5 0.25 0.25\n", encoding="utf-8")
    manifest = tmp_path / "submission.json"
    manifest.write_text(
        json.dumps({
            "schema_version": "submission-manifest-v1",
            "asset_directory": str(tmp_path.resolve()),
            "assets": [
                {"asset_id": "controlled-model", "asset_paths": [model_fixture["path"]],
                 "format": "PYTORCH", "is_synthetic": True,
                 "artifact_unit_definition_id": "pytorch-single-file-v1"},
                {"asset_id": "continuation-control", "asset_paths": [str(control)],
                 "format": "YOLO_DETECTION", "is_synthetic": True},
            ],
        }),
        encoding="utf-8",
    )
    # Test-only startup instrumentation; it never enters a production module.
    bootstrap = f"""
import runpy
import sys
import torch
from assurance_system.workers import c3d_safe_load
def controlled_load(path, *, weights_only, map_location):
    assert weights_only is True and map_location == 'cpu'
    sys.stderr.write({_READY_SIGNAL.decode()!r})
    sys.stderr.flush()
    if {condition!r} == 'timeout':
        runpy.run_path({hang_fixture['path']!r})
    raise MemoryError('bounded test-only allocator failure; no large allocation')
torch.load = controlled_load
c3d_safe_load.main()
"""
    real_popen = subprocess.Popen
    processes = []
    readiness = []
    readiness_messages = []
    readiness_state = {}
    watchdogs = []
    watchdog_fired = threading.Event()

    def launch(command, **kwargs):
        is_c3d = command[2] == "assurance_system.workers.c3d_safe_load"
        actual_command = (
            [command[0], "-c", bootstrap, *command[3:]] if is_c3d else command
        )
        process = real_popen(actual_command, **kwargs)
        processes.append((process, pathlib.Path(kwargs["cwd"]), is_c3d))
        if is_c3d:
            received = []
            ready = threading.Event()

            def await_child_load():
                try:
                    received.append(process.stderr.readline())
                finally:
                    ready.set()

            reader = threading.Thread(target=await_child_load, daemon=True)
            reader.start()
            # The production dispatcher creates Windows workers suspended and
            # assigns them to their Job before returning from Popen. Waiting in
            # this Popen wrapper would deadlock before that trusted resume step.
            readiness_state[process] = (ready, reader, received)
        return process

    monkeypatch.setattr(
        "assurance_system.supervisor.orchestrator.subprocess.Popen", launch
    )
    worker_temp = tmp_path / "worker-temp"
    worker_temp.mkdir()
    store = EvidenceStore(str(tmp_path / "dispatch.sqlite3"))
    audit = AuditChainWriter(store)
    subject = SupervisorOrchestrator(
        store, audit, config_loader=_ShortTimeoutConfig(),
        worker_temp_dir_base=str(worker_temp), python_executable=sys.executable,
    )
    collection_times = []
    real_collect = subject._collect_worker

    def collect(pending):
        if pending.task_spec["task"] == "C3D_SAFE_LOAD":
            ready, reader, received = readiness_state[pending.process]
            if not ready.wait(_CHILD_READY_DEADLINE_SECONDS):
                pending.process.kill()
                pending.process.wait(timeout=_CHILD_CLEANUP_DEADLINE_SECONDS)
                reader.join(timeout=_CHILD_CLEANUP_DEADLINE_SECONDS)
                pytest.fail(
                    "C3D did not reach the controlled load under the safety deadline"
                )
            reader.join(timeout=_CHILD_CLEANUP_DEADLINE_SECONDS)
            readiness_messages.extend(received)
            if received != [_READY_SIGNAL] and received != [
                _READY_SIGNAL.replace(b"\n", b"\r\n")
            ]:
                if pending.process.poll() is None:
                    pending.process.kill()
                pending.process.wait(timeout=_CHILD_CLEANUP_DEADLINE_SECONDS)
                pytest.fail("child did not reach restricted load: " + repr(received))
            readiness.append(True)
            if condition == "timeout":
                def safety_kill():
                    if pending.process.poll() is None:
                        watchdog_fired.set()
                        try:
                            pending.process.kill()
                        except OSError:
                            pass  # Child may have exited between poll() and kill().

                watchdog = threading.Timer(
                    _CI_TIMEOUT_SECONDS + _CHILD_CLEANUP_DEADLINE_SECONDS,
                    safety_kill,
                )
                watchdog.daemon = True
                watchdog.start()
                watchdogs.append(watchdog)
        started = time.monotonic()
        result = real_collect(pending)
        if pending.task_spec["task"] == "C3D_SAFE_LOAD":
            collection_times.append(time.monotonic() - started)
        return result

    monkeypatch.setattr(subject, "_collect_worker", collect)
    try:
        summary = subject.run_pipeline(str(manifest))
        evidence = store.query_evidence("controlled-model", "C3D")
        finding = store.query_findings("controlled-model")[0]
        audit_events = store.query_audit_trail()
        control_evidence = store.query_evidence("continuation-control", "M02")
        assert summary.assets_processed == 2
        assert summary.workers_dispatched == summary.evidence_records_written == 7
        assert summary.findings_written == 2
        assert summary.worker_results_rejected == 0
        assert summary.provenance_records_written == 1
        assert readiness == [True], readiness_messages
        assert not watchdog_fired.is_set(), "test safety watchdog, not supervisor, killed child"
        assert audit.verify_chain_integrity().intact
        assert audit_events[-1]["event_type"] == AuditEventType.PIPELINE_RUN_COMPLETE
        assert AuditEventType.PIPELINE_RUN_ERROR not in {
            event["event_type"] for event in audit_events
        }
        assert control_evidence["assessment_status"] == AssessmentStatus.COMPLETED
        assert evidence["record_digest"] and evidence["is_synthetic"] == 1
        assert evidence["coverage_gap_clean_label"] == 1
        assert evidence["limitations"] and evidence["non_claims"]
        assert evidence["dependency_declaration"]["independence_established"] is False
        assert finding["detection_status"] == "UNAVAILABLE"
        assert finding["interpretation_status"] == "UNAVAILABLE"
        assert finding["analyst_disposition_prompt"] == "UNAVAILABLE_NO_DECISION"
        assert finding["coverage_gap_clean_label"] == 1
        assert finding["global_backdoor_absence_not_established"] == 1
        assert T05D_NON_CLAIM_TEXT in finding["non_claims"]
        assert subject._pipeline_active is False
        assert subject._accepted_records == subject._asset_synthetic == {}
        assert list(worker_temp.iterdir()) == []
        for process, directory, _is_c3d in processes:
            assert process.poll() is not None
            assert not directory.exists()
        c3d_process = next(process for process, _, is_c3d in processes if is_c3d)
        # Persist observable evidence before checking observed pipe cleanup.
        report = {
            "condition": condition,
            "fixture_id": hang_fixture["fixture_id"] if condition == "timeout" else "FIX-015",
            "fixture_seed": 42,
            "test_only_load_instrumentation": True,
            "target_host_oom_capability_proven": False,
            "timeout_seconds": _CI_TIMEOUT_SECONDS,
            "collection_elapsed_seconds": collection_times[0],
            "worker_pid": c3d_process.pid, "worker_exit_code": c3d_process.returncode,
            "worker_stderr_closed": c3d_process.stderr.closed,
            "summary": dataclasses.asdict(summary), "evidence": evidence,
            "finding": finding, "audit_events": audit_events,
        }
        (tmp_path / "dispatch-observed.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        assert c3d_process.stderr.closed, "supervisor leaked worker stderr pipe"
        return report
    finally:
        # Test safety net never substitutes for the asserted supervisor cleanup.
        for watchdog in watchdogs:
            watchdog.cancel()
            watchdog.join(timeout=_CHILD_CLEANUP_DEADLINE_SECONDS)
        for process, _, _ in processes:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=_CHILD_CLEANUP_DEADLINE_SECONDS)
            if process.stderr is not None:
                process.stderr.close()
        store._conn.close()


def test_sec_003_timeout_dispatch_requires_task_022(tmp_path, monkeypatch) -> None:
    report = _run_controlled_c3d_pipeline(tmp_path, monkeypatch, "timeout")
    assert report["worker_exit_code"] != 0
    assert report["collection_elapsed_seconds"] >= _CI_TIMEOUT_SECONDS
    assert report["collection_elapsed_seconds"] < (
        _CI_TIMEOUT_SECONDS + _CHILD_CLEANUP_DEADLINE_SECONDS
    )
    assert report["evidence"]["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert report["evidence"]["raw_signal"] == {"failure_reason": "TIMEOUT"}
    assert report["evidence"]["access_mode"] == "UNAVAILABLE"


def test_supplemental_bounded_memory_error_is_not_oom_acceptance(tmp_path, monkeypatch):
    report = _run_controlled_c3d_pipeline(tmp_path, monkeypatch, "memory_error")
    assert report["worker_exit_code"] == 0, report
    assert report["evidence"]["assessment_status"] == AssessmentStatus.LOAD_ERROR
    signal = report["evidence"]["raw_signal"]
    assert signal["load_detail"] == "SAFE_LOAD_ERROR: MemoryError"
    assert signal["weights_only_flag_used"] is True
    assert signal["fallback_attempted"] is False
    if sys.platform == "win32":
        assert signal["resource_limits_applied"] is False


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
