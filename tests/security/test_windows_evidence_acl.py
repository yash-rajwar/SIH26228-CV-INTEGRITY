"""SEC-008: real Windows deployment ACL + production restricted-worker denial.

Never provisions ACLs during tests/application startup. The separately authorized
deployment script must already have been applied. No mocked AccessDenied.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import uuid

import pytest

from assurance_system.config.loader import ConfigLoader
from assurance_system.fixtures.hostile.coco_geometry import generate_valid
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.orchestrator import SupervisorOrchestrator, _launch_worker_process
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator
from assurance_system.supervisor.windows_job import WindowsWorkerJob, close_reaped_process_handle
from assurance_system.supervisor.windows_token import DENY_ONLY_SIDS

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="SEC-008 Windows acceptance requires deployed Windows target")
_REPO = pathlib.Path(__file__).resolve().parents[2]
_SEED = 26228
_PROBE_MEMORY_MB = 128
_PROBE_TIMEOUT_S = 30


def _database():
    configured = ConfigLoader().load()["system"]["evidence_store"]["path"]
    database = pathlib.Path(configured).resolve()
    assert database.is_file(), "SEC-008 deployment database missing"
    return database


def test_sec008_deployment_acl_is_explicit_and_inheritable():
    database = _database()
    assert database.parent == pathlib.Path("C:/var/assurance/evidence-store")
    command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
               str(_REPO / "scripts/windows/provision_sec008_evidence_acl.ps1"),
               "-Mode", "Verify", "-SnapshotPath", str(_REPO / "build/task026-sec008/acl-before.json")]
    shell_environment = {key: value for key, value in os.environ.items()
                         if key.upper() != "PSMODULEPATH"}
    verified = subprocess.run(command, capture_output=True, text=True,
                              env=shell_environment, timeout=_PROBE_TIMEOUT_S)
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "evidence.db" in verified.stdout


def test_sec008_real_supervisor_write_and_restricted_worker_os_denial(tmp_path, monkeypatch):
    database = _database()
    asset_id = "sec008-synthetic-" + uuid.uuid4().hex
    asset_directory = tmp_path / "coco"
    generate_valid(str(asset_directory), _SEED)
    submission = tmp_path / "submission.json"
    submission.write_text(json.dumps({
        "schema_version": "submission-manifest-v1",
        "asset_directory": str(asset_directory),
        "assets": [{"asset_id": asset_id, "asset_paths": [str(asset_directory / "valid_coco.json")],
                    "format": "COCO", "is_synthetic": True,
                    "contributor_metadata": [{"contributor_id": "synthetic-source-1"}]}],
    }), encoding="utf-8")
    store = EvidenceStore(str(database))
    audit = AuditChainWriter(store)
    subject = SupervisorOrchestrator(store, audit, worker_temp_dir_base=tmp_path,
                                    python_executable=sys.executable)
    processes = []
    def capture(command, **kwargs):
        process = _launch_worker_process(command, **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr("assurance_system.supervisor.orchestrator._launch_worker_process", capture)
    accepted = []
    real_accept = subject._accept_worker_result
    def accept(raw, asset, method):
        assert subject._schema.validate_worker_output(raw, {
            "M01": "C2A_STRUCTURAL", "M02": "C2B_EXACT_HASH",
            "M06": "C2C_CONCENTRATION", "M15": "C2D_IMAGE_HASH"}[method]).valid
        accepted.append(raw)
        return real_accept(raw, asset, method)
    monkeypatch.setattr(subject, "_accept_worker_result", accept)
    try:
        summary = subject.run_pipeline(str(submission))
        assert summary.workers_dispatched == 4 and summary.evidence_records_written == 4
        assert summary.findings_written == 1
        for method, task in (("M01", "C2A_STRUCTURAL"), ("M02", "C2B_EXACT_HASH"),
                             ("M06", "C2C_CONCENTRATION"), ("M15", "C2D_IMAGE_HASH")):
            record = store.query_evidence(asset_id, method)
            assert record is not None
            assert record["coverage_gap_clean_label"] == 1
        assert len(accepted) == 4
        assert store.query_evidence(asset_id, "M01")["assessment_status"] == "COMPLETED"
        assert EvidenceSchemaValidator().validate_finding(store.query_findings(asset_id)[0]).valid
        assert audit.verify_chain_integrity().intact
        assert database.with_name(database.name + "-wal").exists()
        assert database.with_name(database.name + "-shm").exists()
        assert all(process.returncode == 0 and process._handle.closed and
                   process.stderr.closed and all(handle.closed for handle in process._handles)
                   for process in processes)
    finally:
        store._conn.close()
    # Only the explicitly controlled supervisor pipeline write precedes this
    # frozen baseline. The worker probe never changes the deployed database.
    probe_store = EvidenceStore(str(database))
    sidecars = [database.with_name(database.name + suffix) for suffix in ("-wal", "-shm")]
    assert all(path.is_file() for path in sidecars)
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    sidecar_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sidecars}
    directory = pathlib.Path(tempfile.mkdtemp(prefix="sec008-worker-", dir=tmp_path))
    marker = database.parent / ("sec008-denied-" + uuid.uuid4().hex + ".txt")
    result_file = directory / "result.json"
    script = f"""
import ctypes, json, sqlite3
from ctypes import wintypes
from pathlib import Path
from assurance_system.supervisor.windows_token import current_token_state
report = {{'token': current_token_state()}}
for name, path, mode in [('marker', {str(marker)!r}, 'x'), ('database_write', {str(database)!r}, 'r+b')]:
    try:
        with open(path, mode):
            pass  # Never write database bytes even if open unexpectedly succeeds.
        report[name] = {{'allowed':True}}
    except OSError as exc:
        report[name] = {{'allowed':False, 'winerror':exc.winerror, 'errno':exc.errno}}
connection = None
try:
    connection = sqlite3.connect(Path({str(database)!r}).as_uri() + '?mode=rw', uri=True, timeout=0)
    connection.execute('BEGIN IMMEDIATE')
    connection.execute('CREATE TABLE sec008_probe_should_not_exist (value INTEGER)')
    report['sqlite_write'] = {{'allowed':True}}
except sqlite3.Error as exc:
    report['sqlite_write'] = {{'allowed':False, 'code':getattr(exc,'sqlite_errorcode',None), 'message':str(exc)}}
finally:
    if connection is not None:
        connection.rollback()
        connection.close()
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.CreateFileW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
k.CreateFileW.restype = wintypes.HANDLE
k.CloseHandle.argtypes = [wintypes.HANDLE]
for name, path, disposition in [('marker_native',{str(marker)!r},1),('database_native',{str(database)!r},3)]:
    handle = k.CreateFileW(path, 0x40000000, 3, None, disposition, 0, None)
    valid = handle not in (None, ctypes.c_void_p(-1).value)
    report[name] = {{'allowed':valid,'winerror':ctypes.get_last_error()}}
    if valid: k.CloseHandle(handle)
report['sidecar_denials'] = {{}}
for path in {list(map(str, sidecars))!r}:
    report['sidecar_denials'][path] = {{}}
    for name, access in [('write', 0x40000000), ('write_dac', 0x40000)]:
        handle = k.CreateFileW(path, access, 3, None, 3, 0, None)
        valid = handle not in (None, ctypes.c_void_p(-1).value)
        report['sidecar_denials'][path][name] = {{'allowed':valid,'winerror':ctypes.get_last_error()}}
        if valid: k.CloseHandle(handle)
handle = k.CreateFileW({str(database)!r}, 0x40000, 3, None, 3, 0, None)  # WRITE_DAC, no DACL mutation.
valid = handle not in (None, ctypes.c_void_p(-1).value)
report['database_write_dac'] = {{'allowed':valid,'winerror':ctypes.get_last_error()}}
if valid: k.CloseHandle(handle)
k.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
k.OpenProcess.restype = wintypes.HANDLE
parent = k.OpenProcess(0x40, False, {__import__('os').getpid()})  # PROCESS_DUP_HANDLE
report['supervisor_handle_duplication'] = {{'allowed':bool(parent),'winerror':ctypes.get_last_error()}}
if parent: k.CloseHandle(parent)
Path({str(result_file)!r}).write_text(json.dumps(report), encoding='utf-8')
"""
    job = WindowsWorkerJob(_PROBE_MEMORY_MB)
    process = None
    try:
        process = _launch_worker_process([sys.executable, "-c", script],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            close_fds=True, cwd=str(directory),
            env=subject._clean_worker_environment(directory), creationflags=job.creation_flags)
        assert not result_file.exists()
        job.assign_and_resume(process)
        _, stderr = process.communicate(timeout=_PROBE_TIMEOUT_S)
        assert process.returncode == 0, stderr.decode(errors="replace")
        report = json.loads(result_file.read_text(encoding="utf-8"))
        evidence = _REPO / "build/task026-sec008"
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / "sec008-probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        for name in ("marker", "database_write"):
            assert report[name]["allowed"] is False and report[name]["errno"] == 13
            assert report[name]["winerror"] in {None, 5}  # CRT open may omit WinError.
        for name in ("marker_native", "database_native"):
            assert report[name] == {"allowed": False, "winerror": 5}
        for results in report["sidecar_denials"].values():
            assert results == {"write": {"allowed": False, "winerror": 5},
                               "write_dac": {"allowed": False, "winerror": 5}}
        assert report["sqlite_write"]["allowed"] is False
        assert report["sqlite_write"]["code"] in {8, 14}  # SQLITE_READONLY / CANTOPEN
        assert report["database_write_dac"] == {"allowed": False, "winerror": 5}
        assert report["supervisor_handle_duplication"] == {"allowed": False, "winerror": 5}
        for sid in DENY_ONLY_SIDS:
            assert report["token"]["groups"][sid] & 0x10
            assert not report["token"]["groups"][sid] & 0x4
        assert set(report["token"]["privileges"]) <= {"SeChangeNotifyPrivilege"}
        assert not marker.exists()
        after = hashlib.sha256(database.read_bytes()).hexdigest()
        assert before == after
        assert sidecar_hashes == {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sidecars}
        report.update({"database_sha256_before_probe": before, "database_sha256_after_probe": after,
                       "sidecar_sha256_unchanged": sidecar_hashes,
                       "asset_id": asset_id, "supervisor_write": "ALLOWED", "pipeline": "COMPLETE",
                       "worker_exit_code": process.returncode})
        evidence = _REPO / "build/task026-sec008"
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / "sec008-observed.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    finally:
        probe_store._conn.close()
        job.close()
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=_PROBE_TIMEOUT_S)
            close_reaped_process_handle(process)
            assert all(handle.closed for handle in process._handles)
        shutil.rmtree(directory)
    verification_store = EvidenceStore(str(database))
    try:
        assert verification_store._conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert AuditChainWriter(verification_store).verify_chain_integrity().intact
        assert not verification_store._conn.execute(
            "SELECT name FROM sqlite_master WHERE name='sec008_probe_should_not_exist'").fetchall()
    finally:
        verification_store._conn.close()
