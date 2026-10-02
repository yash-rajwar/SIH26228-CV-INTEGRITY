"""Windows Job Object containment for supervisor-dispatched workers.

This module is imported on every platform but may only be instantiated on
Windows. It implements ACC-2026-10-02-01 without changing worker IPC or output
contracts. The configured limit is committed process memory, not RSS/RLIMIT_AS.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import dataclasses
import sys
import threading
from typing import Any


CREATE_SUSPENDED = 0x00000004
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_ASSOCIATE_COMPLETION_PORT_INFORMATION = 7
_JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO = 4
_JOB_OBJECT_MSG_PROCESS_MEMORY_LIMIT = 9
_TH32CS_SNAPTHREAD = 0x00000004
_THREAD_SUSPEND_RESUME = 0x0002
_WAIT_TIMEOUT = 258
_JOB_TERMINATION_EXIT_CODE = 0xE0000001
_COMPLETION_POLL_MS = 100
_COMPLETION_DRAIN_SECONDS = 2


class WindowsJobError(RuntimeError):
    """A Windows containment primitive could not be established safely."""


def close_reaped_process_handle(process: Any) -> None:
    """Release Popen's Windows handle after the child has been reaped.

    Popen otherwise retains this handle until garbage collection. Use its
    idempotent Handle.Close() so its later destructor cannot double-close it.
    """

    if sys.platform != "win32":
        return
    handle = getattr(process, "_handle", None)
    if handle is not None:
        if process.poll() is None:
            raise WindowsJobError("cannot close the handle of a live worker")
        handle.Close()


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _JOBOBJECT_ASSOCIATE_COMPLETION_PORT(ctypes.Structure):
    _fields_ = [
        ("CompletionKey", ctypes.c_void_p),
        ("CompletionPort", wintypes.HANDLE),
    ]


class _THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]


@dataclasses.dataclass(frozen=True)
class WindowsJobObservation:
    mechanism: str
    configured_process_memory_bytes: int
    peak_process_memory_bytes: int
    process_memory_limit_hit: bool


class WindowsWorkerJob:
    """Own a configured Job and completion port for one worker process."""

    mechanism = "WINDOWS_JOB_OBJECT_PROCESS_COMMITTED_MEMORY"
    creation_flags = CREATE_SUSPENDED

    def __init__(self, memory_limit_mb: int) -> None:
        if sys.platform != "win32":
            raise WindowsJobError("Windows Job Objects require win32")
        if type(memory_limit_mb) is not int or memory_limit_mb <= 0:
            raise WindowsJobError("memory_limit_mb must be a positive integer")

        self.configured_process_memory_bytes = memory_limit_mb * 1024 * 1024
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_signatures()
        self._job_handle: int | None = None
        self._completion_port: int | None = None
        self._assigned = False
        self._resumed = False
        self._closed = False
        self._memory_limit_hit = threading.Event()
        self._monitor_stop = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        self._monitor_complete = threading.Event()
        self._monitor_error: Exception | None = None
        self._peak_at_limit = 0

        try:
            job = self._kernel32.CreateJobObjectW(None, None)
            if not job:
                self._raise_last_error("CreateJobObjectW")
            self._job_handle = int(job)

            port = self._kernel32.CreateIoCompletionPort(
                wintypes.HANDLE(_INVALID_HANDLE_VALUE), None, 0, 1
            )
            if not port:
                self._raise_last_error("CreateIoCompletionPort")
            self._completion_port = int(port)

            association = _JOBOBJECT_ASSOCIATE_COMPLETION_PORT(
                None, wintypes.HANDLE(self._completion_port)
            )
            self._set_information(
                _JOB_OBJECT_ASSOCIATE_COMPLETION_PORT_INFORMATION, association
            )

            limits = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            limits.BasicLimitInformation.LimitFlags = (
                _JOB_OBJECT_LIMIT_PROCESS_MEMORY
                | _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            )
            limits.ProcessMemoryLimit = self.configured_process_memory_bytes
            self._set_information(_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, limits)
        except Exception:
            self.close()
            raise

    def _configure_signatures(self) -> None:
        kernel32 = self._kernel32
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.QueryInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.CreateIoCompletionPort.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
            ctypes.c_size_t,
            wintypes.DWORD,
        ]
        kernel32.CreateIoCompletionPort.restype = wintypes.HANDLE
        kernel32.GetQueuedCompletionStatus.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_void_p),
            wintypes.DWORD,
        ]
        kernel32.GetQueuedCompletionStatus.restype = wintypes.BOOL
        kernel32.PostQueuedCompletionStatus.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.c_size_t,
            ctypes.c_void_p,
        ]
        kernel32.PostQueuedCompletionStatus.restype = wintypes.BOOL
        kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateJobObject.restype = wintypes.BOOL
        kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        kernel32.Thread32First.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(_THREADENTRY32),
        ]
        kernel32.Thread32First.restype = wintypes.BOOL
        kernel32.Thread32Next.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(_THREADENTRY32),
        ]
        kernel32.Thread32Next.restype = wintypes.BOOL
        kernel32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenThread.restype = wintypes.HANDLE
        kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
        kernel32.ResumeThread.restype = wintypes.DWORD
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

    @staticmethod
    def _handle(value: int) -> wintypes.HANDLE:
        return wintypes.HANDLE(value)

    @staticmethod
    def _raise_last_error(operation: str) -> None:
        error = ctypes.get_last_error()
        raise WindowsJobError(f"{operation} failed with WinError {error}")

    def _set_information(self, information_class: int, value: Any) -> None:
        if self._job_handle is None:
            raise WindowsJobError("Job handle is unavailable")
        if not self._kernel32.SetInformationJobObject(
            self._handle(self._job_handle),
            information_class,
            ctypes.byref(value),
            ctypes.sizeof(value),
        ):
            self._raise_last_error("SetInformationJobObject")

    def _initial_thread_id(self, process_id: int) -> int:
        snapshot = self._kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPTHREAD, 0)
        snapshot_value = int(snapshot) if snapshot else 0
        if not snapshot_value or snapshot_value == _INVALID_HANDLE_VALUE:
            self._raise_last_error("CreateToolhelp32Snapshot")
        try:
            entry = _THREADENTRY32()
            entry.dwSize = ctypes.sizeof(entry)
            present = self._kernel32.Thread32First(snapshot, ctypes.byref(entry))
            while present:
                if entry.th32OwnerProcessID == process_id:
                    return int(entry.th32ThreadID)
                present = self._kernel32.Thread32Next(snapshot, ctypes.byref(entry))
        finally:
            self._kernel32.CloseHandle(snapshot)
        raise WindowsJobError("suspended worker initial thread was not found")

    def assign_and_resume(self, process: Any) -> None:
        """Assign a suspended Popen child and resume only after assignment."""

        if self._closed or self._job_handle is None:
            raise WindowsJobError("Job is closed")
        process_handle = getattr(process, "_handle", None)
        process_id = getattr(process, "pid", None)
        if process_handle is None or type(process_id) is not int:
            raise WindowsJobError("Popen process handle is unavailable")

        if not self._kernel32.AssignProcessToJobObject(
            self._handle(self._job_handle), wintypes.HANDLE(int(process_handle))
        ):
            self._raise_last_error("AssignProcessToJobObject")
        self._assigned = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_limit_notifications,
            name=f"assurance-job-monitor-{process_id}",
            daemon=True,
        )
        self._monitor_thread.start()

        thread_id = self._initial_thread_id(process_id)
        thread = self._kernel32.OpenThread(_THREAD_SUSPEND_RESUME, False, thread_id)
        if not thread:
            self._raise_last_error("OpenThread")
        try:
            previous_suspend_count = self._kernel32.ResumeThread(thread)
            if previous_suspend_count == 0xFFFFFFFF:
                self._raise_last_error("ResumeThread")
            if previous_suspend_count != 1:
                raise WindowsJobError(
                    "ResumeThread observed an unexpected suspend count"
                )
            self._resumed = True
        finally:
            self._kernel32.CloseHandle(thread)

    def _query_limits(self) -> _JOBOBJECT_EXTENDED_LIMIT_INFORMATION:
        if self._job_handle is None:
            raise WindowsJobError("Job handle is unavailable")
        limits = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        returned = wintypes.DWORD()
        if not self._kernel32.QueryInformationJobObject(
            self._handle(self._job_handle),
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
            ctypes.byref(returned),
        ):
            self._raise_last_error("QueryInformationJobObject")
        return limits

    def _monitor_limit_notifications(self) -> None:
        try:
            while not self._monitor_stop.is_set():
                if self._completion_port is None:
                    return
                message = wintypes.DWORD()
                completion_key = ctypes.c_size_t()
                overlapped = ctypes.c_void_p()
                ctypes.set_last_error(0)
                success = self._kernel32.GetQueuedCompletionStatus(
                    self._handle(self._completion_port),
                    ctypes.byref(message),
                    ctypes.byref(completion_key),
                    ctypes.byref(overlapped),
                    _COMPLETION_POLL_MS,
                )
                if not success:
                    error = ctypes.get_last_error()
                    if error == _WAIT_TIMEOUT:
                        continue
                    raise WindowsJobError(
                        f"GetQueuedCompletionStatus failed with WinError {error}"
                    )
                if message.value == _JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO:
                    return
                if message.value != _JOB_OBJECT_MSG_PROCESS_MEMORY_LIMIT:
                    if self._monitor_stop.is_set():
                        return
                    continue
                limits = self._query_limits()
                self._peak_at_limit = int(limits.PeakProcessMemoryUsed)
                self._memory_limit_hit.set()
                if self._job_handle is None or not self._kernel32.TerminateJobObject(
                    self._handle(self._job_handle), _JOB_TERMINATION_EXIT_CODE
                ):
                    self._raise_last_error("TerminateJobObject")
                return
        except Exception as exc:
            self._monitor_error = exc
        finally:
            self._monitor_complete.set()

    def observe(self) -> WindowsJobObservation:
        """Return peak accounting and whether the process limit was reached."""

        if self._closed or self._job_handle is None or self._completion_port is None:
            raise WindowsJobError("Job observation requested after close")

        # Job messages are ordered on the completion port. Waiting for the
        # active-process-zero message lets an earlier memory-limit message be
        # classified before monitor shutdown after Popen.communicate() returns.
        self._monitor_complete.wait(_COMPLETION_DRAIN_SECONDS)
        self._stop_monitor()
        if self._monitor_error is not None:
            raise WindowsJobError("Job notification monitor failed") from self._monitor_error
        limits = self._query_limits()
        return WindowsJobObservation(
            mechanism=self.mechanism,
            configured_process_memory_bytes=self.configured_process_memory_bytes,
            peak_process_memory_bytes=max(
                self._peak_at_limit, int(limits.PeakProcessMemoryUsed)
            ),
            process_memory_limit_hit=self._memory_limit_hit.is_set(),
        )

    def _stop_monitor(self) -> None:
        self._monitor_stop.set()
        monitor = self._monitor_thread
        if monitor is None:
            return
        if monitor.is_alive() and self._completion_port is not None:
            self._kernel32.PostQueuedCompletionStatus(
                self._handle(self._completion_port), 0, 0, None
            )
        if monitor is not threading.current_thread():
            monitor.join(timeout=2)
            if monitor.is_alive():
                raise WindowsJobError("Job notification monitor did not stop")

    def close(self) -> None:
        """Close owned handles; closing the Job terminates any live member."""

        if self._closed:
            return
        stop_error: Exception | None = None
        try:
            self._stop_monitor()
        except Exception as exc:
            stop_error = exc
        finally:
            self._closed = True
            if self._job_handle is not None:
                self._kernel32.CloseHandle(self._handle(self._job_handle))
                self._job_handle = None
            if self._completion_port is not None:
                self._kernel32.CloseHandle(self._handle(self._completion_port))
                self._completion_port = None
        if stop_error is not None:
            raise stop_error

    @property
    def assigned(self) -> bool:
        return self._assigned

    @property
    def resumed(self) -> bool:
        return self._resumed

    @property
    def closed(self) -> bool:
        return self._closed

    def __enter__(self) -> "WindowsWorkerJob":
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.close()
