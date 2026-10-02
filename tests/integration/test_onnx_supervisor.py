"""Real ONNX identity pipeline through production worker isolation and storage."""
from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import pathlib
import sys

import pytest

from assurance_system.constants import AssessmentStatus, AuditEventType, PF_002_NON_CLAIM
from assurance_system.fixtures.hostile import benign, onnx_path_traversal
from assurance_system.supervisor import orchestrator as supervisor_module
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.orchestrator import SupervisorOrchestrator
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator
from assurance_system.supervisor.windows_token import DENY_ONLY_SIDS, RestrictedWindowsProcess

pytestmark = pytest.mark.skipif(importlib.util.find_spec("onnx") is None,
                              reason="BLOCKED: HOST-CAP-003 — onnx not installed")
_ID = "onnx-main-referenced-external-data-v1"
_SEED = 26228


@pytest.mark.parametrize("missing_external", [False, True])
def test_real_onnx_supervisor_identity_and_incomplete_unit_failure(tmp_path, monkeypatch, missing_external):
    assets = tmp_path / "assets"
    assets.mkdir()
    if missing_external:
        model = assets / "missing.onnx"
        onnx_path_traversal._write_external_data_model(model, "absent.bin")
    else:
        benign.generate_onnx(str(assets), seed=_SEED)
        model = assets / "valid_minimal.onnx"
    asset_id = "e2-real-onnx-missing" if missing_external else "e2-real-onnx-valid"
    submission = tmp_path / "submission.json"
    submission.write_text(json.dumps({"schema_version": "submission-manifest-v1",
        "asset_directory": str(assets), "assets": [{"asset_id": asset_id, "asset_paths": [str(model)],
        "format": "ONNX", "is_synthetic": True}]}), encoding="utf-8")
    temp_base = tmp_path / "worker-temporaries"
    temp_base.mkdir()
    store = EvidenceStore(str(tmp_path / "onnx.sqlite3"))
    audit = AuditChainWriter(store)
    subject = SupervisorOrchestrator(store, audit, worker_temp_dir_base=temp_base, python_executable=sys.executable)
    normalized = subject._load_manifest(str(submission))
    assert normalized["assets"][0]["artifact_unit_definition_id"] == _ID
    processes, jobs, dispatched_tasks, c5_inputs = [], [], [], []
    launch = supervisor_module._launch_worker_process
    def capture_launch(command, **kwargs):
        task_file = pathlib.Path(command[command.index("--task-file") + 1])
        dispatched_tasks.append(json.loads(task_file.read_text(encoding="utf-8")))
        process = launch(command, **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(supervisor_module, "_launch_worker_process", capture_launch)
    create_job = subject._create_worker_containment
    def capture_job(limits):
        job = create_job(limits)
        if job is not None:
            jobs.append(job)
        return job
    monkeypatch.setattr(subject, "_create_worker_containment", capture_job)
    produce = subject._interpretation.produce_finding
    def capture_finding(**kwargs):
        c5_inputs.extend(kwargs["evidence_records"])
        return produce(**kwargs)
    monkeypatch.setattr(subject._interpretation, "produce_finding", capture_finding)
    try:
        summary = subject.run_pipeline(str(submission))
        assert summary.workers_dispatched == 3 and summary.evidence_records_written == 3
        assert summary.worker_results_rejected == 0 and summary.findings_written == 1
        records = {worker.worker_id: store.query_evidence(asset_id, worker.method_id)
                   for worker in (supervisor_module._C3A, supervisor_module._C3B, supervisor_module._C3C)}
        assert {record["worker_id"] for record in c5_inputs} == set(records)
        for record in records.values():
            assert record is not None and record["is_synthetic"] == 1
            assert record["coverage_gap_clean_label"] == 1
        for record in c5_inputs:
            assert record["pf_002_non_claim"] == PF_002_NON_CLAIM
            assert record["hash_match_not_safe"] is True
            assert record["hash_match_not_semantically_equivalent"] is True
            assert record["hash_match_not_causal_execution_proof"] is True
        c3a, c3b, c3c = (records[name] for name in ("COMP-W-C3A", "COMP-W-C3B", "COMP-W-C3C"))
        if missing_external:
            assert c3a["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
            assert c3b["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
            assert "combined_artifact_unit_digest" not in c3b["raw_signal"]
            assert next(task for task in dispatched_tasks if task["task"] == "C3B_MODEL_HASH")["artifact_unit"] is None
        else:
            assert c3a["assessment_status"] == c3b["assessment_status"] == AssessmentStatus.COMPLETED
            assert c3c["assessment_status"] == AssessmentStatus.STRUCTURAL_VALID
            assert c3a["artifact_unit_id"] == c3b["artifact_unit_id"] == _ID
            inner = hashlib.sha256(model.read_bytes()).hexdigest()
            expected = hashlib.sha256(inner.encode("ascii")).hexdigest()
            assert c3b["raw_signal"]["combined_artifact_unit_digest"] == expected
        finding = store.query_findings(asset_id)[0]
        assert EvidenceSchemaValidator().validate_finding(finding).valid
        assert finding["pf_002_non_claim"] == ("C4_BINDING_UNAVAILABLE" if missing_external else PF_002_NON_CLAIM)
        assert audit.verify_chain_integrity().intact
        events = [event["event_type"] for event in store.query_audit_trail()]
        assert AuditEventType.WORKER_RESULT_REJECTED_SCHEMA_VIOLATION not in events
        assert AuditEventType.PIPELINE_RUN_COMPLETE in events
        assert all(process.returncode == 0 for process in processes)
        if sys.platform == "win32":
            assert len(jobs) == len(processes) == 3
            assert all(isinstance(process, RestrictedWindowsProcess) for process in processes)
            for process in processes:
                assert all(process.token_state["groups"][sid] & 0x10 for sid in DENY_ONLY_SIDS)
                assert process._handle.closed and process.stderr.closed
                assert all(handle.closed for handle in process._handles)
            assert all(job.assigned and job.resumed and job.closed for job in jobs)
        assert not list(temp_base.iterdir())
        evidence = pathlib.Path(__file__).resolve().parents[2] / "build/e2-onnx"
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / ("supervisor-missing.json" if missing_external else "supervisor-valid.json")).write_text(
            json.dumps({"summary": dataclasses.asdict(summary), "records": records, "finding": finding,
                        "audit_intact": True, "worker_exit_codes": [process.returncode for process in processes],
                        "windows_restricted_launcher": sys.platform == "win32", "temp_cleanup": True}, indent=2), encoding="utf-8")
    finally:
        store._conn.close()
