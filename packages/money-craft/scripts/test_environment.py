#!/usr/bin/env python3
"""Run a bounded local test with disposable dependencies and persistent evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = {
    'report': ROOT / 'skills/money-craft/requirements-report.txt',
    'data': ROOT / 'skills/money-craft/requirements-yfinance.txt',
}


class Interrupted(Exception):
    def __init__(self, signum):
        self.signum = signum


def interrupt(signum, _frame):
    raise Interrupted(signum)


def execute(argv, env, deadline):
    """Reap the owned process group before its temporary environment is removed."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise subprocess.TimeoutExpired(argv[0], 0)
    process = subprocess.Popen(argv, env=env, start_new_session=True)
    try:
        return process.wait(timeout=remaining)
    finally:
        # Also stop descendants if the command exited without waiting for them.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def run(output: Path, command: list[str], runtime: str, timeout: int) -> int:
    if os.name != 'posix':
        raise ValueError('managed test environments currently support macOS/Linux only')
    output = output.absolute()
    if output.resolve() != output:
        raise ValueError('output path must not contain symlinks or parent traversal')
    output.mkdir(parents=True, exist_ok=False)
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    for sig in handlers:
        signal.signal(sig, interrupt)
    started = time.monotonic()
    deadline = started + timeout
    status, code = 'ERROR', 1
    scratch = None
    try:
        with tempfile.TemporaryDirectory(prefix='money-craft-test-') as directory:
            scratch = Path(directory)
            env = os.environ.copy()
            # Runtime data and cache are disposable; output/evidence is separate.
            for name, child in [('MONEY_CRAFT_DATA_HOME', 'data'),
                                ('MONEY_CRAFT_CACHE_HOME', 'cache'), ('TMPDIR', 'tmp')]:
                path = scratch / child
                path.mkdir()
                env[name] = str(path)
            env['MONEY_CRAFT_TEST_OUTPUT'] = str(output)
            env['PIP_CACHE_DIR'] = str(scratch / 'pip-cache')
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            python = sys.executable
            if runtime != 'none':
                python = str(scratch / 'venv/bin/python')
                code = execute([sys.executable, '-m', 'venv', str(scratch / 'venv')], env, deadline)
                if code:
                    status = 'SETUP_FAILED'
                else:
                    env['VIRTUAL_ENV'] = str(scratch / 'venv')
                    env['PATH'] = str(scratch / 'venv/bin') + os.pathsep + env.get('PATH', '')
                    if runtime in REQUIREMENTS:
                        code = execute([python, '-m', 'pip', 'install', '--disable-pip-version-check',
                                        '-r', str(REQUIREMENTS[runtime])], env, deadline)
                        if code:
                            status = 'SETUP_FAILED'
            else:
                code = 0
            # Explicitly selected test interpreter cannot fall back to user venvs.
            env['MONEY_CRAFT_REPORT_PYTHON'] = python
            env['MONEY_CRAFT_DATA_PYTHON'] = python
            if code == 0:
                argv = [arg.replace('{python}', python).replace('{output}', str(output)) for arg in command]
                code = execute(argv, env, deadline)
                status = 'COMMAND_SUCCEEDED' if code == 0 else 'COMMAND_FAILED'
    except subprocess.TimeoutExpired:
        status, code = 'TIMEOUT', 124
    except Interrupted as exc:
        status, code = 'INTERRUPTED', 128 + exc.signum
    finally:
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
        cleaned = scratch is not None and not scratch.exists()
        if not cleaned:
            status, code = 'CLEANUP_FAILED', 1
        receipt = {'schema': 'money-craft.test-environment.v1', 'status': status,
                   'exit_code': code, 'runtime': runtime, 'temporary_environment_removed': cleaned,
                   'elapsed_seconds': round(time.monotonic() - started, 3),
                   'semantic_verdict': 'NOT_ASSESSED'}
        # No command arguments, environment values, credentials or raw logs in this receipt.
        with (output / 'test-environment-receipt.json').open('x') as stream:
            json.dump(receipt, stream, indent=2)
            stream.write('\n')
    return code if code >= 0 else 128 - code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True, help='new persistent evidence directory')
    parser.add_argument('--runtime', choices=('none', 'empty', 'report', 'data'), default='none')
    parser.add_argument('--timeout', type=int, default=900, help='total setup and command timeout in seconds')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.timeout <= 0:
        parser.error('a command and a positive timeout are required')
    try:
        return run(args.output_dir, command, args.runtime, args.timeout)
    except (OSError, ValueError) as exc:
        print(f'test environment failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
