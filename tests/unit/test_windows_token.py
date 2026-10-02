"""Real supported Win32 token/IPC tests; no mocked access denials."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from assurance_system.supervisor import windows_token as token_module
from assurance_system.supervisor.orchestrator import _launch_worker_process, SupervisorOrchestrator
from assurance_system.supervisor.windows_job import WindowsWorkerJob, close_reaped_process_handle
from assurance_system.supervisor.windows_token import DENY_ONLY_SIDS, RestrictedWindowsProcess, WindowsTokenError

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Win32 token tests require Windows")
_PROBE_MEMORY_MB = 128
_PROBE_TIMEOUT_S = 30


def launch(script, directory):
    env = SupervisorOrchestrator._clean_worker_environment(None, directory)
    return _launch_worker_process([sys.executable, "-c", script],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        close_fds=True, cwd=str(directory), env=env, creationflags=4)


def reap(process, job):
    job.close()
    if process.poll() is None:
        process.kill()
    process.communicate(timeout=_PROBE_TIMEOUT_S)
    close_reaped_process_handle(process)
    assert process.stderr.closed and process._handle.closed
    assert all(handle.closed for handle in process._handles)


def test_restricted_token_created_before_job_resume_and_ipc_works(tmp_path):
    asset = tmp_path / "read-only-input.txt"
    asset.write_text("submitted-local-input", encoding="utf-8")
    directory = tmp_path / "worker"
    directory.mkdir()
    result = directory / "result.json"
    script = f"""
import json, os
from pathlib import Path
from assurance_system.supervisor.windows_token import current_token_state
report = current_token_state()
report['asset'] = Path({str(asset)!r}).read_text(encoding='utf-8')
report['private_env'] = any(key in os.environ for key in ['ASSURANCE_KEY_PATH','ASSURANCE_DB_PATH'])
Path({str(result)!r}).write_text(json.dumps(report), encoding='utf-8')
"""
    job = WindowsWorkerJob(_PROBE_MEMORY_MB)
    process = launch(script, directory)
    try:
        assert not result.exists()
        assert process.poll() is None
        for sid in DENY_ONLY_SIDS:
            assert process.token_state["groups"][sid] & 0x10
            assert not process.token_state["groups"][sid] & 0x4
        assert set(process.token_state["privileges"]) <= {"SeChangeNotifyPrivilege"}
        job.assign_and_resume(process)
        _, stderr = process.communicate(timeout=_PROBE_TIMEOUT_S)
        assert process.returncode == 0, stderr.decode(errors="replace")
        report = json.loads(result.read_text())
        assert report["groups"] == process.token_state["groups"]
        assert report["privileges"] == process.token_state["privileges"]
        assert report["asset"] == "submitted-local-input"
        assert report["private_env"] is False
        assert job.assigned and job.resumed
    finally:
        reap(process, job)
        asset.unlink()


@pytest.mark.parametrize("operation", ["OpenProcessToken", "CreateRestrictedToken",
    "SetTokenInformation", "SetNamedSecurityInfoW", "CreateWindowStationW",
    "CreateDesktopW", "CreateProcessAsUserW", "CreatePipe", "UpdateProcThreadAttribute"])
def test_token_setup_failures_close_handles_never_execute(tmp_path, monkeypatch, operation):
    marker = tmp_path / "executed.txt"
    configured = token_module._API._configure
    real_handle = token_module._Handle
    handles = []

    def configure(api):
        configured(api)
        dll = api.a if operation in {"OpenProcessToken", "CreateRestrictedToken",
            "CreateProcessAsUserW", "SetTokenInformation", "SetNamedSecurityInfoW"} else api.k
        if operation in {"CreateWindowStationW", "CreateDesktopW"}:
            dll = api.u
        monkeypatch.setattr(dll, operation,
                           lambda *_args: 5 if operation == "SetNamedSecurityInfoW" else False)

    def own(*args):
        handle = real_handle(*args)
        handles.append(handle)
        return handle

    monkeypatch.setattr(token_module._API, "_configure", configure)
    monkeypatch.setattr(token_module, "_Handle", own)
    with pytest.raises(WindowsTokenError, match=operation):
        launch(f"from pathlib import Path; Path({str(marker)!r}).write_text('executed')", tmp_path)
    assert not marker.exists()
    assert all(handle.closed for handle in handles)


def test_windows_never_falls_back_to_unrestricted_popen(tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise WindowsTokenError("restricted setup unavailable")
    def forbidden(*args, **kwargs):
        pytest.fail("unrestricted fallback attempted")
    monkeypatch.setattr("assurance_system.supervisor.orchestrator.RestrictedWindowsProcess", unavailable)
    monkeypatch.setattr("assurance_system.supervisor.orchestrator.subprocess.Popen", forbidden)
    with pytest.raises(WindowsTokenError):
        launch("raise SystemExit(0)", tmp_path)


def test_non_windows_launch_keeps_existing_popen_contract(monkeypatch):
    captured = []
    sentinel = object()
    monkeypatch.setattr("assurance_system.supervisor.orchestrator.sys.platform", "linux")
    def capture(command, **kwargs):
        captured.append((command, kwargs))
        return sentinel
    monkeypatch.setattr("assurance_system.supervisor.orchestrator.subprocess.Popen", capture)
    assert _launch_worker_process(["python", "-m", "worker"], close_fds=True) is sentinel
    assert captured == [(["python", "-m", "worker"], {"close_fds": True})]


def test_restricted_worker_timeout_and_cleanup(tmp_path):
    job = WindowsWorkerJob(_PROBE_MEMORY_MB)
    process = launch("import time; time.sleep(30)", tmp_path)
    try:
        job.assign_and_resume(process)
        with pytest.raises(subprocess.TimeoutExpired):
            process.communicate(timeout=0.1)
        process.kill()
        process.communicate(timeout=_PROBE_TIMEOUT_S)
        assert process.returncode != 0
    finally:
        reap(process, job)


def test_only_designated_standard_handles_are_inherited(tmp_path):
    import ctypes
    from ctypes import wintypes
    import msvcrt
    import os
    decoy = open(tmp_path / "supervisor-only.txt", "wb")
    handle = msvcrt.get_osfhandle(decoy.fileno())
    os.set_handle_inheritable(handle, True)
    script = f"""
import ctypes, json
from ctypes import wintypes
from pathlib import Path
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.GetHandleInformation.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
k.GetHandleInformation.restype = wintypes.BOOL
flags = wintypes.DWORD()
valid = bool(k.GetHandleInformation({handle}, ctypes.byref(flags)))
Path('result.json').write_text(json.dumps({{'decoy_inherited':valid}}))
"""
    job = WindowsWorkerJob(_PROBE_MEMORY_MB)
    process = launch(script, tmp_path)
    try:
        job.assign_and_resume(process)
        _, stderr = process.communicate(timeout=_PROBE_TIMEOUT_S)
        assert process.returncode == 0, stderr
        assert json.loads((tmp_path / "result.json").read_text())["decoy_inherited"] is False
    finally:
        reap(process, job)
        decoy.close()
