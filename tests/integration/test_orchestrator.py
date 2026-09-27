"""TASK-022 supervisor orchestration integration and contract tests."""

from __future__ import annotations

import datetime
import json
import pathlib
from typing import Any

import pytest

from assurance_system.config.loader import ResourceLimits
from assurance_system.constants import AssessmentStatus, AuditEventType
from assurance_system.exceptions import (
    AuditWriteError,
    IngestError,
    PipelineError,
    SchemaViolationError,
)
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.orchestrator import (
    PipelineRunSummary,
    SupervisorOrchestrator,
    _C2_WORKERS,
    _C3A,
    _C3B,
    _C3C,
    _C3D,
    _RunCounters,
)


def _timestamp() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _worker_result(
    worker_id: str = "COMP-W-C2B",
    status: str = AssessmentStatus.COMPLETED,
    raw_signal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "worker-output-v1",
        "worker_id": worker_id,
        "assessment_status": status,
        "raw_signal": raw_signal if raw_signal is not None else {"count": 0},
        "access_mode": "BLACK_BOX" if "C3" in worker_id else "UNAVAILABLE",
        "artifact_unit_id": "UNAVAILABLE",
        "coverage_gap_clean_label": True,
        "limitations": ["Assessment is limited to the declared method scope."],
        "non_claims": ["No malicious-intent conclusion is established."],
        "dependency_declaration": {
            "co_firing_detectors": [],
            "independence_established": False,
        },
        "assessment_timestamp": _timestamp(),
        "error_detail": None,
    }


def _task(task_name: str = "C2B_EXACT_HASH") -> dict[str, Any]:
    return {
        "schema_version": "worker-input-v1",
        "task": task_name,
        "asset_paths": ["C:/submitted/asset.bin"],
        "format": "COCO",
        "asset_directory": "C:/submitted",
        "artifact_unit_definition_id": "UNAVAILABLE",
        "resource_limits": {
            "timeout_s": 5,
            "memory_mb": 64,
            "max_fds": 8,
        },
        "identity_quality": "UNTRUSTED",
    }


@pytest.fixture
def store(tmp_path: pathlib.Path):
    evidence_store = EvidenceStore(str(tmp_path / "orchestrator.sqlite3"))
    yield evidence_store
    evidence_store._conn.close()


@pytest.fixture
def orchestrator(store: EvidenceStore) -> SupervisorOrchestrator:
    return SupervisorOrchestrator(store, AuditChainWriter(store))


def test_supervisor_initializes_required_dependencies(
    orchestrator: SupervisorOrchestrator,
) -> None:
    assert orchestrator._store is not None
    assert orchestrator._audit is not None
    assert orchestrator._schema is not None
    assert orchestrator._reference_manager is not None
    assert orchestrator._provenance is not None
    assert orchestrator._capabilities is not None
    assert orchestrator._interpretation is not None


def test_invalid_resource_configuration_fails_closed(
    store: EvidenceStore,
) -> None:
    class InvalidConfig:
        @staticmethod
        def get_resource_limits(_task_name: str) -> ResourceLimits:
            return ResourceLimits(
                timeout_seconds=0,
                memory_limit_mb=64,
                max_file_descriptors=8,
            )

    subject = SupervisorOrchestrator(
        store,
        AuditChainWriter(store),
        config_loader=InvalidConfig(),
    )
    with pytest.raises(PipelineError, match="resource limits"):
        subject._resource_limits("C2B_EXACT_HASH")


def test_dispatch_uses_controlled_subprocess_environment_and_cleans_up(
    orchestrator: SupervisorOrchestrator,
    store: EvidenceStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    result = _worker_result()

    class FakeProcess:
        returncode: int | None = None

        def __init__(self, command: list[str], **kwargs: Any):
            captured["command"] = command
            captured["kwargs"] = kwargs
            captured["cwd"] = pathlib.Path(kwargs["cwd"])
            self._result_path = pathlib.Path(
                command[command.index("--result-file") + 1]
            )

        def communicate(self, timeout: int):
            captured["timeout"] = timeout
            self._result_path.write_text(json.dumps(result), encoding="utf-8")
            self.returncode = 0
            return b"", b""

        def poll(self):
            return self.returncode

        def kill(self) -> None:
            self.returncode = -9

        def wait(self) -> int:
            return int(self.returncode or 0)

    monkeypatch.setenv("ASSURANCE_KEY_PATH", "C:/private/key.bin")
    monkeypatch.setenv("ASSURANCE_DB_PATH", "C:/private/evidence.db")
    monkeypatch.setattr(
        "assurance_system.supervisor.orchestrator.subprocess.Popen", FakeProcess
    )

    limits = ResourceLimits(5, 64, 8)
    actual = orchestrator._dispatch_worker(
        "assurance_system.workers.c2b_exact_hash", _task(), limits
    )

    assert actual == result
    assert captured["command"][:3] == [
        orchestrator._python_executable,
        "-m",
        "assurance_system.workers.c2b_exact_hash",
    ]
    assert "shell" not in captured["kwargs"]
    assert captured["kwargs"]["stdin"] is not None
    assert captured["kwargs"]["stdout"] is not None
    assert captured["kwargs"]["stderr"] is not None
    assert captured["kwargs"]["close_fds"] is True
    assert "ASSURANCE_KEY_PATH" not in captured["kwargs"]["env"]
    assert "ASSURANCE_DB_PATH" not in captured["kwargs"]["env"]
    assert captured["timeout"] == limits.timeout_seconds
    assert not captured["cwd"].exists()
    assert store.query_audit_trail()[-1]["event_type"] == (
        AuditEventType.WORKER_DISPATCHED
    )


def test_valid_result_is_validated_then_written_and_audited(
    orchestrator: SupervisorOrchestrator, store: EvidenceStore
) -> None:
    raw = _worker_result()
    assert store.query_evidence("asset-1", "M02") is None

    record_id = orchestrator._accept_worker_result(raw, "asset-1", "M02")

    persisted = store.query_evidence("asset-1", "M02")
    assert persisted is not None
    assert persisted["record_id"] == record_id
    assert persisted["record_digest"]
    assert persisted["worker_id"] == "COMP-W-C2B"
    assert [event["event_type"] for event in store.query_audit_trail()] == [
        AuditEventType.WORKER_RESULT_ACCEPTED,
        AuditEventType.EVIDENCE_RECORD_WRITTEN,
    ]


def test_invalid_result_is_rejected_without_evidence_write(
    orchestrator: SupervisorOrchestrator, store: EvidenceStore
) -> None:
    invalid = _worker_result()
    invalid["limitations"] = []

    with pytest.raises(SchemaViolationError):
        orchestrator._accept_worker_result(invalid, "asset-2", "M02")

    assert store.query_evidence("asset-2", "M02") is None
    assert [event["event_type"] for event in store.query_audit_trail()] == [
        AuditEventType.WORKER_RESULT_REJECTED_SCHEMA_VIOLATION
    ]


def test_worker_output_alone_has_no_persistence_authority(
    store: EvidenceStore,
) -> None:
    _worker_result()
    assert store.query_evidence("asset-3", "M02") is None
    assert store.query_audit_trail() == []


def test_audit_failure_is_not_swallowed_after_evidence_write(
    orchestrator: SupervisorOrchestrator,
    store: EvidenceStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_audit(_event_type: str, _payload: dict) -> str:
        raise AuditWriteError("simulated audit failure")

    monkeypatch.setattr(orchestrator._audit, "append_event", fail_audit)
    with pytest.raises(AuditWriteError, match="simulated audit failure"):
        orchestrator._accept_worker_result(
            _worker_result(), "asset-audit", "M02"
        )
    assert store.query_evidence("asset-audit", "M02") is not None


def test_pipeline_failure_is_audited_and_raised(
    orchestrator: SupervisorOrchestrator,
    store: EvidenceStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_manifest(_path: str) -> dict:
        raise IngestError("invalid manifest")

    monkeypatch.setattr(orchestrator, "_load_manifest", fail_manifest)
    with pytest.raises(PipelineError, match="failed closed"):
        orchestrator.run_pipeline("not-used.json")

    assert [event["event_type"] for event in store.query_audit_trail()] == [
        AuditEventType.PIPELINE_RUN_START,
        AuditEventType.PIPELINE_RUN_ERROR,
    ]


def test_c2_batch_starts_every_worker_before_collection(
    orchestrator: SupervisorOrchestrator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class Token:
        def __init__(self, task_name: str):
            self.task_name = task_name

    def fake_start(_module: str, task_spec: dict, _limits: ResourceLimits):
        events.append("start:" + task_spec["task"])
        return Token(task_spec["task"])

    def fake_collect(token: Token) -> dict:
        events.append("collect:" + token.task_name)
        return {"task": token.task_name}

    monkeypatch.setattr(orchestrator, "_start_worker", fake_start)
    monkeypatch.setattr(orchestrator, "_collect_worker", fake_collect)
    limits = ResourceLimits(5, 64, 8)
    requests = [
        (worker, {"task": worker.task_name}, limits) for worker in _C2_WORKERS
    ]

    orchestrator._dispatch_batch(requests)

    assert events[:4] == ["start:" + worker.task_name for worker in _C2_WORKERS]
    assert events[4:] == ["collect:" + worker.task_name for worker in _C2_WORKERS]


def test_c3a_containment_violation_stops_downstream_chain(
    orchestrator: SupervisorOrchestrator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    violation = _worker_result(
        "COMP-W-C3A",
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION,
        {"violations": [{"reason": "TRAVERSAL_PATTERN"}]},
    )
    violation["access_mode"] = "UNAVAILABLE"

    def fake_run_one(worker, _asset, _counters, **_kwargs):
        calls.append(worker.worker_id)
        return violation, violation

    monkeypatch.setattr(orchestrator, "_run_one_worker", fake_run_one)
    evidence, _accepted = orchestrator._run_c3(
        {"asset_id": "model-1", "format": "ONNX"}, _RunCounters()
    )

    assert calls == ["COMP-W-C3A"]
    assert evidence == [violation]
    assert evidence[0]["assessment_status"] == (
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
    )
    assert evidence[0]["access_mode"] == "UNAVAILABLE"


@pytest.mark.parametrize(
    ("format_name", "expected_tail"),
    [("ONNX", "COMP-W-C3C"), ("PYTORCH", "COMP-W-C3D")],
)
def test_c3_normal_sequence_uses_format_applicable_tail_batch(
    orchestrator: SupervisorOrchestrator,
    monkeypatch: pytest.MonkeyPatch,
    format_name: str,
    expected_tail: str,
) -> None:
    events: list[str] = []
    artifact_unit = {
        "main_file": "C:/submitted/model.bin",
        "external_files": [],
        "artifact_unit_definition_id": "UNAVAILABLE",
    }

    def fake_run_one(worker, _asset, _counters, **_kwargs):
        events.append(worker.worker_id)
        if worker is _C3A:
            record = _worker_result(
                "COMP-W-C3A", raw_signal={"artifact_unit": artifact_unit}
            )
        else:
            record = _worker_result("COMP-W-C3B")
        return record, record

    def fake_task_spec(worker, _asset, **_kwargs):
        return {"task": worker.task_name}, ResourceLimits(5, 64, 8)

    def fake_batch(requests):
        events.append("batch:" + ",".join(item[0].worker_id for item in requests))
        return [_worker_result(item[0].worker_id) for item in requests]

    def fake_process(_asset_id, items, _counters):
        records = [item[2] for item in items]
        return records, records

    monkeypatch.setattr(orchestrator, "_run_one_worker", fake_run_one)
    monkeypatch.setattr(orchestrator, "_task_spec", fake_task_spec)
    monkeypatch.setattr(orchestrator, "_dispatch_batch", fake_batch)
    monkeypatch.setattr(orchestrator, "_process_results", fake_process)

    evidence, _accepted = orchestrator._run_c3(
        {"asset_id": "model-2", "format": format_name}, _RunCounters()
    )

    assert events == [
        "COMP-W-C3A",
        "COMP-W-C3B",
        "batch:" + expected_tail,
    ]
    assert [record["worker_id"] for record in evidence] == [
        "COMP-W-C3A",
        "COMP-W-C3B",
        expected_tail,
    ]


def test_c3_tail_batch_starts_c3c_and_c3d_before_collection(
    orchestrator: SupervisorOrchestrator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class Token:
        def __init__(self, name: str):
            self.name = name

    def fake_start(_module: str, task_spec: dict, _limits: ResourceLimits):
        events.append("start:" + task_spec["task"])
        return Token(task_spec["task"])

    def fake_collect(token: Token) -> dict:
        events.append("collect:" + token.name)
        return {"task": token.name}

    monkeypatch.setattr(orchestrator, "_start_worker", fake_start)
    monkeypatch.setattr(orchestrator, "_collect_worker", fake_collect)
    limits = ResourceLimits(5, 64, 8)
    orchestrator._dispatch_batch(
        [
            (_C3C, {"task": _C3C.task_name}, limits),
            (_C3D, {"task": _C3D.task_name}, limits),
        ]
    )

    assert events == [
        "start:C3C_ONNX_STRUCTURAL",
        "start:C3D_SAFE_LOAD",
        "collect:C3C_ONNX_STRUCTURAL",
        "collect:C3D_SAFE_LOAD",
    ]


def test_run_pipeline_delegates_finding_to_existing_c5_engine(
    orchestrator: SupervisorOrchestrator,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset_directory = tmp_path / "assets"
    asset_directory.mkdir()
    asset_path = asset_directory / "labels.txt"
    asset_path.write_text("0 0.5 0.5 0.25 0.25\n", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "submission-manifest-v1",
                "asset_directory": str(asset_directory.resolve()),
                "assets": [
                    {
                        "asset_id": "asset-c5",
                        "asset_paths": [str(asset_path.resolve())],
                        "format": "YOLO_DETECTION",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    evidence = _worker_result("COMP-W-C2B")
    calls: list[dict[str, Any]] = []

    monkeypatch.setattr(
        orchestrator._capabilities, "declare_capabilities", lambda *_args: {}
    )
    monkeypatch.setattr(
        orchestrator, "_emit_deferred_in_scope_records", lambda _asset_id: []
    )
    monkeypatch.setattr(
        orchestrator,
        "_run_c2",
        lambda _asset, _counters: ([evidence], [evidence]),
    )
    monkeypatch.setattr(orchestrator, "_build_provenance", lambda _records: None)

    def fake_finding(**kwargs):
        calls.append(kwargs)
        return {"finding_id": "finding-c5"}

    monkeypatch.setattr(orchestrator._interpretation, "produce_finding", fake_finding)
    monkeypatch.setattr(orchestrator, "_persist_finding", lambda _finding: "finding-c5")

    summary = orchestrator.run_pipeline(str(manifest_path))

    assert isinstance(summary, PipelineRunSummary)
    assert len(calls) == 1
    assert calls[0]["asset_id"] == "asset-c5"
    assert calls[0]["evidence_records"] == [evidence]
    assert calls[0]["c4_binding"] is None


def test_assessment_error_is_complete_and_does_not_expose_sensitive_detail(
    orchestrator: SupervisorOrchestrator,
) -> None:
    secret_detail = "C:/private/keys/root.bin token=do-not-expose"
    result = orchestrator._build_assessment_error(
        _task(), "TIMEOUT", secret_detail
    )

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["coverage_gap_clean_label"] is True
    assert result["limitations"]
    assert result["non_claims"]
    assert secret_detail not in json.dumps(result)
    assert result["error_detail"] == "TIMEOUT"
