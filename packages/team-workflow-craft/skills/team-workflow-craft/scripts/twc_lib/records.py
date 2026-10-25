"""Validate persisted task records at the read boundary, before consumers use them."""
from datetime import datetime
from pathlib import PurePosixPath, PureWindowsPath
import re

from .models import WorkflowError, canonical, digest


def command_hash(argv, cwd='.'):
    return digest(canonical(dict(argv=argv, cwd=cwd)))


def _require(condition, field):
    if not condition:
        raise WorkflowError(f'Invalid task metadata field: {field}')


def _strings(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _hash(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _time(value):
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value).tzinfo is not None
    except ValueError:
        return False


def _relative(value):
    return (isinstance(value, str) and bool(value) and not PurePosixPath(value).is_absolute()
            and not PureWindowsPath(value).drive and '\\' not in value
            and '..' not in PurePosixPath(value).parts)


def _local_fields(value):
    if isinstance(value, dict):
        _require(not {'root', 'remotes'}.intersection(value), 'local-only workspace fields')
        for item in value.values():
            _local_fields(item)
    elif isinstance(value, list):
        for item in value:
            _local_fields(item)


def _code(value, nullable=False):
    if value is None and nullable:
        return
    _require(isinstance(value, dict), 'code')
    for name in ('head', 'base', 'base_ref'):
        _require(isinstance(value.get(name), str), 'code.' + name)
    for name in ('dirty', 'fingerprint_complete'):
        _require(type(value.get(name)) is bool, 'code.' + name)
    _require(value.get('tree_sha256') is None or _hash(value['tree_sha256']), 'code.tree_sha256')
    _require(not value['fingerprint_complete'] or _hash(value.get('tree_sha256')), 'code.fingerprint_complete')


def _check(value, portable):
    _require(isinstance(value, dict), 'checks[]')
    _require(isinstance(value.get('check'), str) and bool(re.fullmatch(r'[A-Za-z0-9_-]+', value['check'])), 'check')
    _require(_relative(value.get('cwd')), 'check.cwd')
    if 'argv' in value:  # Published v2 records remain readable; lint detects non-portable legacy commands.
        _require(_strings(value['argv']) and bool(value['argv']) and all(value['argv']), 'check.argv')
        if portable:
            absolute = re.compile(r'(?:^|[=\s\"\x27])(?:/|[A-Za-z]:[\\/]|\\\\)')
            _require(not any(absolute.search(arg) for arg in value['argv']), 'check.argv contains local absolute paths')
        if 'command_sha256' in value:
            _require(value['command_sha256'] == command_hash(value['argv'], value['cwd']), 'check.command_sha256')
    else:
        _require(_hash(value.get('command_sha256')), 'check.command_sha256')
    status, code = value.get('status'), value.get('exit_code')
    _require(status in ('passed', 'failed', 'not_run', 'incomplete'), 'check.status')
    _require(code is None or type(code) is int, 'check.exit_code')
    _require(status != 'passed' or code == 0, 'passed check.exit_code')
    _require(status != 'failed' or (type(code) is int and code != 0), 'failed check.exit_code')
    _require(status != 'not_run' or code is None, 'not_run check.exit_code')
    for name in ('started_at', 'ended_at'):
        _require(name in value and (value[name] is None or _time(value[name])), 'check.' + name)
    _require(status not in ('passed', 'failed') or all(value[name] is not None for name in ('started_at', 'ended_at')),
             'executed check timestamps')
    _require(value.get('reason') is None or isinstance(value['reason'], str), 'check.reason')


def validate(value, ref, kind, *, portable=False):
    _require(isinstance(value, dict), kind)
    _require(value.get('kind') == kind and value.get('schema_version') == 2, kind + ' kind/schema_version')
    _require(value.get('task_ref') == ref, 'task_ref does not match its directory')
    _local_fields(value)
    _require(_hash(value.get('contract_sha256')), 'contract_sha256')
    if kind == 'TaskRecord':
        _require(type(value.get('revision')) is int and value['revision'] > 0, 'revision')
        contract = value.get('contract')
        _require(contract is None or isinstance(contract, dict), 'contract')
        if contract is not None:
            _require(isinstance(contract.get('goal'), str), 'contract.goal')
            _require(isinstance(contract.get('integrator'), str), 'contract.integrator')
            for name in ('scope', 'non_goals', 'dependencies', 'contracts'):
                _require(_strings(contract.get(name)), 'contract.' + name)
            _require(isinstance(contract.get('acceptance'), list), 'contract.acceptance')
        _require(isinstance(value.get('sources'), list), 'sources')
        for source in value['sources']:
            _require(isinstance(source, dict) and _relative(source.get('path')) and _hash(source.get('sha256')), 'sources[]')
        _require(isinstance(value.get('history'), list) and all(isinstance(row, dict) for row in value['history']), 'history')
        return value
    _require(_time(value.get('created_at')), 'created_at')
    _code(value.get('code'), nullable=kind == 'VerificationRecord')
    _require(value.get('actor') is None or isinstance(value['actor'], dict), 'actor')
    if kind == 'VerificationRecord':
        _require(_hash(value.get('policy_sha256')), 'policy_sha256')
        _require(isinstance(value.get('toolchain'), dict), 'toolchain')
        _require(_strings(value.get('drift')), 'drift')
        checks = value.get('checks')
        _require(isinstance(checks, list) and bool(checks), 'checks')
        for check in checks:
            _check(check, portable)
        _require(len({row['check'] for row in checks}) == len(checks), 'duplicate checks')
        states = {row['status'] for row in checks}
        expected = ('incomplete' if value['drift'] or 'incomplete' in states else 'failed' if 'failed' in states
                    else 'not_run' if 'not_run' in states else 'passed')
        _require(value.get('status') == expected, 'verification status disagrees with checks/drift')
    elif kind == 'Handoff':
        for name in ('done', 'remaining', 'next_steps', 'blockers', 'unknowns'):
            _require(_strings(value.get(name)), name)
        _require(value.get('readiness') in ('not_ready', 'advisory_ready', 'unknown'), 'readiness')
        _require(value.get('merge_authorized') is False and value.get('published') is False, 'handoff authority')
        _require(isinstance(value.get('checks'), dict), 'checks')
        for check in value['checks'].values():
            _require(isinstance(check, dict) and check.get('status') in
                     ('passed', 'failed', 'not_run', 'incomplete', 'stale', 'missing'), 'handoff check')
    return value
