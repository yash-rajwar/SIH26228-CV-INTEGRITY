"""Supported Win32 restricted-primary-token worker launch (ACC-2026-10-02-02).

No credentials, unrestricted fallback, asset parsing or deployment ACL mutation.
Filesystem access is enforced by deployment DACLs, not application-level checks.
This restricted derivative is not a claim of whole-host filesystem confinement.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import os
import pathlib
import secrets
import subprocess
import sys
import threading
import time

from assurance_system.supervisor.windows_job import CREATE_SUSPENDED


DENY_ONLY_SIDS = ("S-1-5-32-544", "S-1-5-11", "S-1-5-114")
_DISABLE_MAX_PRIVILEGE = 0x1
_TOKEN_QUERY = 0x8
_TOKEN_LAUNCH_ACCESS = 0x8B  # ASSIGN_PRIMARY | DUPLICATE | QUERY | ADJUST_DEFAULT
_GROUP_DENY_ONLY = 0x10
_TOKEN_USER, _TOKEN_GROUPS, _TOKEN_PRIVILEGES, _TOKEN_RESTRICTED_SIDS = 1, 2, 3, 11
_STARTF_USESTDHANDLES = 0x100
_EXTENDED_STARTUPINFO_PRESENT = 0x80000
_CREATE_UNICODE_ENVIRONMENT = 0x400
_CREATE_NO_WINDOW = 0x8000000
_PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x20002
_INFINITE, _WAIT_TIMEOUT = 0xFFFFFFFF, 258
_INVALID_HANDLE = ctypes.c_void_p(-1).value
_SE_FILE_OBJECT = 1
_DACL_SECURITY_INFORMATION = 0x4
_PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000
_SECURITY_DESCRIPTOR_REVISION = 1


class WindowsTokenError(RuntimeError):
    """Restricted launch cannot be established; caller must fail closed."""


class _SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", w.DWORD)]


class _LUID(ctypes.Structure):
    _fields_ = [("LowPart", w.DWORD), ("HighPart", w.LONG)]


class _LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Luid", _LUID), ("Attributes", w.DWORD)]


class _SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", w.DWORD), ("lpSecurityDescriptor", ctypes.c_void_p),
               ("bInheritHandle", w.BOOL)]


class _STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", w.DWORD), ("lpReserved", w.LPWSTR), ("lpDesktop", w.LPWSTR),
               ("lpTitle", w.LPWSTR), ("dwX", w.DWORD), ("dwY", w.DWORD),
               ("dwXSize", w.DWORD), ("dwYSize", w.DWORD),
               ("dwXCountChars", w.DWORD), ("dwYCountChars", w.DWORD),
               ("dwFillAttribute", w.DWORD), ("dwFlags", w.DWORD),
               ("wShowWindow", w.WORD), ("cbReserved2", w.WORD),
               ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
               ("hStdInput", w.HANDLE), ("hStdOutput", w.HANDLE),
               ("hStdError", w.HANDLE)]


class _STARTUPINFOEX(ctypes.Structure):
    _fields_ = [("StartupInfo", _STARTUPINFO), ("lpAttributeList", ctypes.c_void_p)]


class _PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", w.HANDLE), ("hThread", w.HANDLE),
               ("dwProcessId", w.DWORD), ("dwThreadId", w.DWORD)]


class _API:
    def __init__(self):
        if sys.platform != "win32":
            raise WindowsTokenError("restricted Windows launch requires win32")
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.a = ctypes.WinDLL("advapi32", use_last_error=True)
        self.u = ctypes.WinDLL("user32", use_last_error=True)
        self._configure()

    def _configure(self):
        pointer = ctypes.c_void_p
        signatures = [
            (self.k, "GetCurrentProcess", [], w.HANDLE),
            (self.k, "CloseHandle", [w.HANDLE], w.BOOL),
            (self.k, "LocalFree", [pointer], pointer),
            (self.k, "CreatePipe", [ctypes.POINTER(w.HANDLE), ctypes.POINTER(w.HANDLE),
                                   pointer, w.DWORD], w.BOOL),
            (self.k, "SetHandleInformation", [w.HANDLE, w.DWORD, w.DWORD], w.BOOL),
            (self.k, "CreateFileW", [w.LPCWSTR, w.DWORD, w.DWORD, pointer,
                                     w.DWORD, w.DWORD, w.HANDLE], w.HANDLE),
            (self.k, "InitializeProcThreadAttributeList", [pointer, w.DWORD,
                 w.DWORD, ctypes.POINTER(ctypes.c_size_t)], w.BOOL),
            (self.k, "UpdateProcThreadAttribute", [pointer, w.DWORD, ctypes.c_size_t,
                 pointer, ctypes.c_size_t, pointer, pointer], w.BOOL),
            (self.k, "DeleteProcThreadAttributeList", [pointer], None),
            (self.k, "WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD),
            (self.k, "GetExitCodeProcess", [w.HANDLE, ctypes.POINTER(w.DWORD)], w.BOOL),
            (self.k, "TerminateProcess", [w.HANDLE, w.UINT], w.BOOL),
            (self.k, "ResumeThread", [w.HANDLE], w.DWORD),
            (self.a, "OpenProcessToken", [w.HANDLE, w.DWORD,
                                          ctypes.POINTER(w.HANDLE)], w.BOOL),
            (self.a, "CreateRestrictedToken", [w.HANDLE, w.DWORD, w.DWORD, pointer,
                 w.DWORD, pointer, w.DWORD, pointer, ctypes.POINTER(w.HANDLE)], w.BOOL),
            (self.a, "ConvertStringSidToSidW", [w.LPCWSTR,
                                                ctypes.POINTER(pointer)], w.BOOL),
            (self.a, "ConvertSidToStringSidW", [pointer, ctypes.POINTER(pointer)], w.BOOL),
            (self.a, "GetTokenInformation", [w.HANDLE, ctypes.c_int, pointer,
                 w.DWORD, ctypes.POINTER(w.DWORD)], w.BOOL),
            (self.a, "SetTokenInformation", [w.HANDLE, ctypes.c_int, pointer, w.DWORD], w.BOOL),
            (self.a, "LookupPrivilegeNameW", [w.LPCWSTR, ctypes.POINTER(_LUID),
                 w.LPWSTR, ctypes.POINTER(w.DWORD)], w.BOOL),
            (self.a, "CreateProcessAsUserW", [w.HANDLE, w.LPCWSTR, w.LPWSTR,
                 pointer, pointer, w.BOOL, w.DWORD, pointer, w.LPCWSTR,
                 pointer, ctypes.POINTER(_PROCESS_INFORMATION)], w.BOOL),
            (self.a, "ConvertStringSecurityDescriptorToSecurityDescriptorW",
                 [w.LPCWSTR, w.DWORD, ctypes.POINTER(pointer), pointer], w.BOOL),
            (self.a, "GetSecurityDescriptorDacl", [pointer, ctypes.POINTER(w.BOOL),
                 ctypes.POINTER(pointer), ctypes.POINTER(w.BOOL)], w.BOOL),
            (self.a, "SetNamedSecurityInfoW", [w.LPWSTR, ctypes.c_int, w.DWORD,
                 pointer, pointer, pointer, pointer], w.DWORD),
            (self.u, "CreateWindowStationW", [w.LPCWSTR, w.DWORD, w.DWORD, pointer], w.HANDLE),
            (self.u, "GetProcessWindowStation", [], w.HANDLE),
            (self.u, "SetProcessWindowStation", [w.HANDLE], w.BOOL),
            (self.u, "CreateDesktopW", [w.LPCWSTR, w.LPCWSTR, pointer,
                  w.DWORD, w.DWORD, pointer], w.HANDLE),
            (self.u, "CloseDesktop", [w.HANDLE], w.BOOL),
            (self.u, "CloseWindowStation", [w.HANDLE], w.BOOL),
        ]
        for dll, name, arguments, result in signatures:
            function = getattr(dll, name)
            function.argtypes, function.restype = arguments, result

    @staticmethod
    def check(success, operation):
        if not success:
            raise WindowsTokenError(
                f"{operation} failed with WinError {ctypes.get_last_error()}"
            )

    def sid(self, value):
        result = ctypes.c_void_p()
        self.check(self.a.ConvertStringSidToSidW(value, ctypes.byref(result)),
                   "ConvertStringSidToSidW")
        return result

    def sid_text(self, value):
        result = ctypes.c_void_p()
        self.check(self.a.ConvertSidToStringSidW(value, ctypes.byref(result)),
                   "ConvertSidToStringSidW")
        try:
            return ctypes.wstring_at(result)
        finally:
            self.k.LocalFree(result)

    def token_information(self, token, category):
        size = w.DWORD()
        self.a.GetTokenInformation(token, category, None, 0, ctypes.byref(size))
        if not size.value:
            self.check(False, "GetTokenInformation size")
        buffer = ctypes.create_string_buffer(size.value)
        self.check(self.a.GetTokenInformation(token, category, buffer, size,
                   ctypes.byref(size)), "GetTokenInformation")
        return buffer

    def token_state(self, token):
        user = self.token_information(token, _TOKEN_USER)
        result = {"user_sid": self.sid_text(
            _SID_AND_ATTRIBUTES.from_buffer(user).Sid)}
        for label, category in (("groups", _TOKEN_GROUPS),
                                ("restricting_sids", _TOKEN_RESTRICTED_SIDS)):
            buffer = self.token_information(token, category)
            count = w.DWORD.from_buffer(buffer).value
            # TOKEN_GROUPS starts its pointer-aligned array after DWORD count.
            offset = ctypes.alignment(_SID_AND_ATTRIBUTES)
            items = (_SID_AND_ATTRIBUTES * count).from_buffer(buffer, offset)
            result[label] = {self.sid_text(item.Sid): int(item.Attributes)
                             for item in items}
        buffer = self.token_information(token, _TOKEN_PRIVILEGES)
        count = w.DWORD.from_buffer(buffer).value
        items = (_LUID_AND_ATTRIBUTES * count).from_buffer(buffer, ctypes.sizeof(w.DWORD))
        result["privileges"] = {}
        for item in items:
            size = w.DWORD(256)  # Win32 privilege-name buffer, not a resource limit.
            name = ctypes.create_unicode_buffer(size.value)
            self.check(self.a.LookupPrivilegeNameW(None, ctypes.byref(item.Luid),
                       name, ctypes.byref(size)), "LookupPrivilegeNameW")
            result["privileges"][name.value] = int(item.Attributes)
        return result

    def worker_default_security(self, token, user_sid):
        # The elevated caller's default owner/DACL may be Administrators-only.
        # Once that group is deny-only, the child's own startup objects must
        # instead be owned by and accessible to its user SID. This adjusts only
        # the derived token, never the trusted supervisor's primary token/DACL.
        descriptor = ctypes.c_void_p()
        sddl = ("D:P(A;;GA;;;SY)(A;;GA;;;BA)"
                f"(A;;GA;;;{user_sid})")
        self.check(self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, _SECURITY_DESCRIPTOR_REVISION, ctypes.byref(descriptor), None),
            "worker default security descriptor")
        owner = None
        try:
            owner = self.sid(user_sid)
            present, defaulted, dacl = w.BOOL(), w.BOOL(), ctypes.c_void_p()
            self.check(self.a.GetSecurityDescriptorDacl(descriptor, ctypes.byref(present),
                ctypes.byref(dacl), ctypes.byref(defaulted)), "worker default DACL")
            self.check(self.a.SetTokenInformation(token, 6, ctypes.byref(dacl),
                       ctypes.sizeof(dacl)), "SetTokenInformation default DACL")
            self.check(self.a.SetTokenInformation(token, 4, ctypes.byref(owner),
                       ctypes.sizeof(owner)), "SetTokenInformation owner")
        finally:
            if owner is not None:
                self.k.LocalFree(owner)
            self.k.LocalFree(descriptor)

    def grant_directory(self, directory, user_sid, rights="FA"):
        """Grant the token user a controlled supervisor-created IPC directory.

        Never called on submitted assets or deployment stores. Explicit user
        access is needed because Python 3.13 mode-0700 under the elevated
        built-in Administrator produces an Administrators-owned OWNER_RIGHTS ACL.
        """
        if rights not in {"FA", "GRGX"}:
            raise WindowsTokenError("invalid directory grant")
        descriptor = ctypes.c_void_p()
        sddl = f"D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;{rights};;;{user_sid})"
        self.check(self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, _SECURITY_DESCRIPTOR_REVISION, ctypes.byref(descriptor), None), "IPC descriptor")
        try:
            present, defaulted, dacl = w.BOOL(), w.BOOL(), ctypes.c_void_p()
            self.check(self.a.GetSecurityDescriptorDacl(descriptor, ctypes.byref(present),
                       ctypes.byref(dacl), ctypes.byref(defaulted)), "IPC DACL")
            error = self.a.SetNamedSecurityInfoW(str(directory), _SE_FILE_OBJECT,
                _DACL_SECURITY_INFORMATION | _PROTECTED_DACL_SECURITY_INFORMATION,
                None, None, dacl, None)
            if error:
                raise WindowsTokenError(f"SetNamedSecurityInfoW IPC DACL failed with WinError {error}")
        finally:
            self.k.LocalFree(descriptor)


class _Handle:
    def __init__(self, api, value):
        self.api, self.value, self.closed = api, int(value), False

    def __int__(self):
        return self.value

    def Close(self):
        if not self.closed:
            self.api.check(self.api.k.CloseHandle(self.value), "CloseHandle")
            self.closed = True


class _UserHandle(_Handle):
    def __init__(self, api, value, operation):
        super().__init__(api, value)
        self.operation = operation

    def Close(self):
        if not self.closed:
            self.api.check(getattr(self.api.u, self.operation)(self.value), self.operation)
            self.closed = True


def current_token_state() -> dict:
    """Read-only diagnostic of the calling process's actual primary token."""
    api, token = _API(), w.HANDLE()
    api.check(api.a.OpenProcessToken(api.k.GetCurrentProcess(), _TOKEN_QUERY,
                                    ctypes.byref(token)), "OpenProcessToken")
    try:
        return api.token_state(token)
    finally:
        api.k.CloseHandle(token)


class RestrictedWindowsProcess:
    """Small process adapter for COMP-SUP; always restricted and suspended.

    communicate/poll/wait/kill follow the bytes-mode Popen contract used here.
    The initial thread cannot resume until WindowsWorkerJob assigns the process.
    """

    def __init__(self, command, *, stdin, stdout, stderr, close_fds, cwd, env,
                 creationflags):
        if (stdin, stdout, stderr, close_fds, creationflags) != (
            subprocess.DEVNULL, subprocess.DEVNULL, subprocess.PIPE, True,
            CREATE_SUSPENDED,
        ):
            raise WindowsTokenError("unsupported worker launch contract")
        if not command or not env or any(key.upper() in {
            "ASSURANCE_KEY_PATH", "ASSURANCE_DB_PATH"} for key in env):
            raise WindowsTokenError("invalid restricted worker environment")
        directory = pathlib.Path(cwd).resolve(strict=True)
        if not directory.is_dir() or directory.is_symlink():
            raise WindowsTokenError("worker IPC directory is invalid")
        self.args, self.returncode, self.pid = command, None, None
        self.stdin = self.stdout = self.stderr = None
        self._api = api = _API()
        self._handles = []
        self._handle = self._thread_handle = None
        self._desktop = self._station = None
        self._reader = None
        self._stderr_bytes = b""
        self._read_error = None
        token = original = None
        sids = []
        attributes_initialized = False
        attribute_buffer = None
        read_handle = None

        def own(value):
            handle = _Handle(api, value)
            self._handles.append(handle)
            return handle

        try:
            raw_token = w.HANDLE()
            api.check(api.a.OpenProcessToken(api.k.GetCurrentProcess(),
                _TOKEN_LAUNCH_ACCESS, ctypes.byref(raw_token)), "OpenProcessToken")
            original = own(raw_token.value)
            for text in DENY_ONLY_SIDS:
                sids.append(api.sid(text))
            disabled = (_SID_AND_ATTRIBUTES * len(DENY_ONLY_SIDS))(
                *(_SID_AND_ATTRIBUTES(sid, 0) for sid in sids))
            api.check(api.a.CreateRestrictedToken(int(original),
                _DISABLE_MAX_PRIVILEGE, len(disabled), disabled,
                0, None, 0, None, ctypes.byref(raw_token)),
                "CreateRestrictedToken")
            token = own(raw_token.value)
            self.token_state = api.token_state(int(token))
            for sid in DENY_ONLY_SIDS:
                attributes = self.token_state["groups"].get(sid)
                # A SID absent in the caller cannot provide positive access.
                if attributes is not None and not attributes & _GROUP_DENY_ONLY:
                    raise WindowsTokenError("required group is not deny-only")
            if set(self.token_state["privileges"]) - {"SeChangeNotifyPrivilege"}:
                raise WindowsTokenError("unnecessary worker privileges remain")
            api.worker_default_security(int(token), self.token_state["user_sid"])
            api.grant_directory(directory, self.token_state["user_sid"])

            desktop_name = self._create_private_desktop()

            security = _SECURITY_ATTRIBUTES(ctypes.sizeof(_SECURITY_ATTRIBUTES), None, True)
            raw_read, raw_write = w.HANDLE(), w.HANDLE()
            api.check(api.k.CreatePipe(ctypes.byref(raw_read), ctypes.byref(raw_write),
                                     ctypes.byref(security), 0), "CreatePipe")
            read_handle, write_handle = own(raw_read.value), own(raw_write.value)
            api.check(api.k.SetHandleInformation(int(read_handle), 1, 0),
                      "SetHandleInformation")
            null_handles = []
            for access in (0x80000000, 0x40000000):  # GENERIC_READ / GENERIC_WRITE
                raw = api.k.CreateFileW("NUL", access, 3, ctypes.byref(security), 3, 0, None)
                if raw in (None, _INVALID_HANDLE):
                    api.check(False, "CreateFileW NUL")
                null_handles.append(own(raw))
            size = ctypes.c_size_t()
            api.k.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
            attribute_buffer = ctypes.create_string_buffer(size.value)
            api.check(api.k.InitializeProcThreadAttributeList(attribute_buffer, 1, 0,
                      ctypes.byref(size)), "InitializeProcThreadAttributeList")
            attributes_initialized = True
            inherited = (w.HANDLE * 3)(int(null_handles[0]), int(null_handles[1]),
                                      int(write_handle))
            api.check(api.k.UpdateProcThreadAttribute(attribute_buffer, 0,
                _PROC_THREAD_ATTRIBUTE_HANDLE_LIST, inherited, ctypes.sizeof(inherited),
                None, None), "UpdateProcThreadAttribute handle list")
            startup = _STARTUPINFOEX()
            startup.StartupInfo.cb = ctypes.sizeof(startup)
            startup.StartupInfo.dwFlags = _STARTF_USESTDHANDLES
            startup.StartupInfo.lpDesktop = desktop_name
            startup.StartupInfo.hStdInput = int(null_handles[0])
            startup.StartupInfo.hStdOutput = int(null_handles[1])
            startup.StartupInfo.hStdError = int(write_handle)
            startup.lpAttributeList = ctypes.cast(attribute_buffer, ctypes.c_void_p)
            information = _PROCESS_INFORMATION()
            environment = ctypes.create_unicode_buffer(
                "\0".join(f"{key}={value}" for key, value in sorted(
                    env.items(), key=lambda item: item[0].upper())) + "\0\0")
            command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
            api.check(api.a.CreateProcessAsUserW(int(token), str(command[0]), command_line,
                None, None, True, CREATE_SUSPENDED | _EXTENDED_STARTUPINFO_PRESENT |
                _CREATE_UNICODE_ENVIRONMENT | _CREATE_NO_WINDOW, environment, str(directory),
                ctypes.byref(startup), ctypes.byref(information)), "CreateProcessAsUserW")
            self._handle = own(information.hProcess)
            self._thread_handle = own(information.hThread)
            self.pid = int(information.dwProcessId)
            import msvcrt  # Windows-only stdlib; transfers ownership to the file object.
            fd = msvcrt.open_osfhandle(int(read_handle), os.O_RDONLY | os.O_BINARY)
            read_handle.closed = True
            try:
                self.stderr = os.fdopen(fd, "rb", buffering=0)
            except Exception:
                os.close(fd)
                raise
        except BaseException:
            if self._handle is not None:
                self.kill()
                self.wait()
            if self.stderr is not None:
                self.stderr.close()
            for handle in reversed(self._handles):
                handle.Close()
            raise
        finally:
            if attributes_initialized:
                api.k.DeleteProcThreadAttributeList(attribute_buffer)
            for sid in sids:
                api.k.LocalFree(sid)
            for handle in self._handles:
                if handle not in (self._handle, self._thread_handle, self._desktop,
                                  self._station) and not handle.closed:
                    handle.Close()

    def _create_private_desktop(self):
        # Microsoft recommends a separate desktop for restricted applications.
        # This avoids access to the shared interactive/RDP desktop without
        # changing its DACL. It is not a general Windows sandbox guarantee.
        api = self._api
        name = "assurance-worker-" + secrets.token_hex(16)
        descriptor = ctypes.c_void_p()
        sddl = ("D:P(A;;GA;;;SY)(A;;GA;;;BA)"
                f"(A;;GA;;;{self.token_state['user_sid']})")
        api.check(api.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, _SECURITY_DESCRIPTOR_REVISION, ctypes.byref(descriptor), None),
            "private desktop security descriptor")
        previous = None
        switched = False
        try:
            previous = api.u.GetProcessWindowStation()
            api.check(previous, "GetProcessWindowStation")
            security = _SECURITY_ATTRIBUTES(ctypes.sizeof(_SECURITY_ATTRIBUTES), descriptor, False)
            station = api.u.CreateWindowStationW(name, 1, 0xF037F, ctypes.byref(security))
            api.check(station, "CreateWindowStationW")
            self._station = _UserHandle(api, station, "CloseWindowStation")
            self._handles.append(self._station)
            api.check(api.u.SetProcessWindowStation(station), "SetProcessWindowStation")
            switched = True
            desktop = api.u.CreateDesktopW("worker", None, None, 0, 0xF01FF,
                                           ctypes.byref(security))
            api.check(desktop, "CreateDesktopW")
            self._desktop = _UserHandle(api, desktop, "CloseDesktop")
            self._handles.append(self._desktop)
            return name + "\\worker"
        finally:
            try:
                if switched:
                    api.check(api.u.SetProcessWindowStation(previous),
                              "restore supervisor window station")
            finally:
                api.k.LocalFree(descriptor)

    def close_isolation_handles(self):
        if self.poll() is None:
            raise WindowsTokenError("cannot close isolation handles of live worker")
        for handle in (self._thread_handle, self._desktop, self._station):
            if handle is not None:
                handle.Close()

    def poll(self):
        if self.returncode is not None:
            return self.returncode
        status = self._api.k.WaitForSingleObject(int(self._handle), 0)
        if status == _WAIT_TIMEOUT:
            return None
        self._api.check(status == 0, "WaitForSingleObject")
        code = w.DWORD()
        self._api.check(self._api.k.GetExitCodeProcess(int(self._handle),
            ctypes.byref(code)), "GetExitCodeProcess")
        self.returncode = int(code.value)
        return self.returncode

    def wait(self, timeout=None):
        if self.returncode is None:
            milliseconds = _INFINITE if timeout is None else max(0, int(timeout * 1000))
            status = self._api.k.WaitForSingleObject(int(self._handle), milliseconds)
            if status == _WAIT_TIMEOUT:
                raise subprocess.TimeoutExpired(self.args, timeout)
            self._api.check(status == 0, "WaitForSingleObject")
        return self.poll()

    def kill(self):
        if self.poll() is None:
            success = self._api.k.TerminateProcess(int(self._handle), 1)
            if not success and self.poll() is None:
                self._api.check(False, "TerminateProcess")

    terminate = kill

    def _read_stderr(self):
        try:
            chunks = []
            while chunk := self.stderr.read(65536):
                chunks.append(chunk)
            self._stderr_bytes = b"".join(chunks)
        except Exception as exc:
            self._read_error = exc
        finally:
            self.stderr.close()

    def communicate(self, input=None, timeout=None):
        if input is not None:
            raise WindowsTokenError("worker stdin is DEVNULL")
        started = time.monotonic()
        if self._reader is None:
            self._reader = threading.Thread(target=self._read_stderr, daemon=True)
            self._reader.start()
        self.wait(timeout=timeout)
        remaining = None if timeout is None else max(0, timeout - (time.monotonic() - started))
        self._reader.join(remaining)
        if self._reader.is_alive():
            raise subprocess.TimeoutExpired(self.args, timeout)
        if self._read_error is not None:
            raise WindowsTokenError("worker stderr collection failed") from self._read_error
        if self._thread_handle is not None:
            self._thread_handle.Close()
        return None, self._stderr_bytes
