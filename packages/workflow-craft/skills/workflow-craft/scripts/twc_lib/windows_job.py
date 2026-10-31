"""Windows check process trees, assigned before project code is allowed to run.

The small Python launcher waits on stdin until it belongs to our Job Object.
Its private result file distinguishes spawn errors from a check's exit code;
stdout/stderr remain exclusively the check's output. No shell is inserted.
This is lifecycle management, not a sandbox for hostile project code.
"""
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time


class BasicLimits(ctypes.Structure):
    _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                ('flags', w.DWORD), ('min_working_set', ctypes.c_size_t),
                ('max_working_set', ctypes.c_size_t), ('active_limit', w.DWORD),
                ('affinity', ctypes.c_size_t), ('priority', w.DWORD), ('scheduling', w.DWORD)]


class IOCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in
                ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic', BasicLimits), ('io', IOCounters),
                ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_longlong) for name in
                ('user_time', 'kernel_time', 'period_user', 'period_kernel')] + [
                (name, w.DWORD) for name in ('page_faults', 'total', 'active', 'terminated')]


def _api():
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateJobObjectW': ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
        'SetInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
        'QueryInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
        'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
        'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
        'TerminateJobObject': ([w.HANDLE, w.UINT], w.BOOL),
        'CloseHandle': ([w.HANDLE], w.BOOL),
    }
    for name, (args, result) in signatures.items():
        getattr(api, name).argtypes = args
        getattr(api, name).restype = result
    return api


def _checked(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


class WindowsJob:
    def __init__(self):
        self.api = _api()
        self.handle = _checked(self.api.CreateJobObjectW(None, None))
        self.temp = None
        try:
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
            _checked(self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
            self.temp = tempfile.TemporaryDirectory(prefix='workflow-check-')
            self.report = Path(self.temp.name) / 'result.json'
        except BaseException:
            self.close()
            raise

    def start(self, argv, *, cwd, env):
        process = subprocess.Popen([sys.executable, '-I', '-S', '-u', str(Path(__file__).resolve())],
                                   cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        try:
            handle = _checked(self.api.OpenProcess(0x0101, False, process.pid))  # SET_QUOTA | TERMINATE
            try:
                _checked(self.api.AssignProcessToJobObject(self.handle, handle))
            finally:
                self.api.CloseHandle(handle)
            # Project code cannot start before successful assignment. EOF without
            # this message exits the launcher without executing any command.
            process.stdin.write(json.dumps(dict(argv=argv, report=str(self.report))).encode('utf-8'))
            process.stdin.close()
            return process
        except BaseException:
            process.kill()
            process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()
            raise

    def alive(self):
        stats = Accounting()
        _checked(self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(stats), ctypes.sizeof(stats), None))
        return stats.active != 0

    def stop(self):
        _checked(self.api.TerminateJobObject(self.handle, 1))
        deadline = time.monotonic() + 5
        while self.alive():
            if time.monotonic() >= deadline:
                raise OSError('Windows job termination did not finish')
            time.sleep(0.01)

    def outcome(self):
        try:
            value = json.loads(self.report.read_text(encoding='utf-8'))
            if (set(value) != {'status', 'reason', 'exit_code'}
                    or value['status'] not in ('passed', 'failed', 'not_run', 'incomplete')
                    or (value['status'] in ('passed', 'failed') and type(value['exit_code']) is not int)
                    or (value['status'] == 'passed' and value['exit_code'] != 0)):
                raise ValueError('Invalid launcher outcome')
            return value
        except (OSError, ValueError, TypeError):
            return dict(status='incomplete', reason='launcher_result_missing_or_invalid', exit_code=None)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None
        if self.temp:
            self.temp.cleanup()
            self.temp = None


def _launch():
    message = sys.stdin.buffer.read()
    if not message:
        return
    payload = json.loads(message)
    try:
        code = subprocess.call(payload['argv'], stdin=subprocess.DEVNULL)
        result = dict(status='passed' if code == 0 else 'failed', reason=None, exit_code=code)
    except FileNotFoundError:
        result = dict(status='not_run', reason='executable_or_cwd_missing', exit_code=None)
    except (OSError, subprocess.SubprocessError):
        result = dict(status='incomplete', reason='execution_error', exit_code=None)
    Path(payload['report']).write_text(json.dumps(result), encoding='utf-8')


if __name__ == '__main__':
    _launch()
