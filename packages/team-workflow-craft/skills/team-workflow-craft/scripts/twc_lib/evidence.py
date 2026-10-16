"""Execute explicitly approved checks and bind results to observable code state."""
import hashlib
import os
import signal
import subprocess
import threading
import time

from . import actors
from .context import binding
from .models import WorkflowError, envelope, local_target, now, relative_path, save_local
from .policy import load, require_lock, runtime_identity
from .workspace import code_identity, inspect


def _stop(process):
    if os.name == 'posix':
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        # No claim of Windows process-tree isolation without native acceptance.
        process.kill()
    process.wait(timeout=5)


def _group_alive(process):
    if os.name != 'posix':
        return None
    try:
        os.killpg(process.pid, 0)
        return True
    except ProcessLookupError:
        return False


def execute(root, name, check, token_env, identity_token_env=None):
    started = now()
    start = time.monotonic()
    output_hash = hashlib.sha256()
    output_size = 0
    reader_failed = False

    def drain(stream):
        nonlocal output_size, reader_failed
        try:
            for block in iter(lambda: stream.read(65536), b''):
                output_size += len(block)
                output_hash.update(block)
        except OSError:
            reader_failed = True

    result = dict(check=name, argv=check['argv'], cwd=check.get('cwd', '.'),
                  started_at=started, ended_at=None, exit_code=None, status='not_run',
                  reason=None, log_ref=None, output_retention='digest_only')
    env = dict(os.environ)
    for name_to_remove in {token_env, identity_token_env, 'TWC_CNB_TOKEN', 'TWC_GITEA_TOKEN', 'TWC_CNB_IDENTITY_TOKEN'}:
        env.pop(name_to_remove, None)  # Platform credentials are not needed by project tests.
    process = None
    reader = None
    try:
        process = subprocess.Popen(check['argv'], cwd=relative_path(root, result['cwd'], must_exist=True),
                                   env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, start_new_session=os.name == 'posix')
        reader = threading.Thread(target=drain, args=(process.stdout,), daemon=True)
        reader.start()
        try:
            result['exit_code'] = process.wait(timeout=check.get('timeout_seconds', 300))
            result['status'] = 'passed' if result['exit_code'] == 0 else 'failed'
        except subprocess.TimeoutExpired:
            result.update(status='incomplete', reason='timeout')
            _stop(process)
            result['exit_code'] = process.returncode
        except KeyboardInterrupt:
            result.update(status='incomplete', reason='cancelled')
            _stop(process)
            result['exit_code'] = process.returncode
        alive = _group_alive(process)
        if alive is True:
            if result['status'] == 'passed':
                result.update(status='incomplete', reason='child_process_still_running')
            _stop(process)
        elif alive is None and result['status'] == 'passed':
            result.update(status='incomplete', reason='process_tree_completion_unverified')
        reader.join(timeout=2)
        if reader.is_alive():
            # A descendant retained stdout after the parent exited. Do not certify completion.
            result.update(status='incomplete', reason='child_process_output_still_open')
            _stop(process)
            reader.join(timeout=2)
        if reader_failed:
            result.update(status='incomplete', reason='output_read_failed')
    except FileNotFoundError:
        result.update(status='not_run', reason='executable_or_cwd_missing')
    except (OSError, subprocess.SubprocessError):
        result.update(status='incomplete', reason='execution_error')
        if process is not None and process.poll() is None:
            _stop(process)
    finally:
        if process is not None and process.stdout is not None and (reader is None or not reader.is_alive()):
            process.stdout.close()
    result.update(ended_at=now(), duration_seconds=round(time.monotonic() - start, 3),
                  output_sha256=output_hash.hexdigest(), output_bytes=output_size)
    return result


def verify(root, config, policy_hash, selected=(), execute_commands=False, approved_policy=None, online=False):
    checks = config.get('checks', {})
    names = list(selected) if selected else list(checks)
    if len(set(names)) != len(names) or any(name not in checks for name in names):
        raise WorkflowError('Unknown or duplicate check selection')
    plan = dict(status='not_run', policy_sha256=policy_hash, checks={name: checks[name] for name in names},
                side_effects='executes project code; may write files, use network/services or databases',
                approval='--execute --approved-policy <exact policy_sha256>')
    if not execute_commands:
        return plan
    if not names:
        raise WorkflowError('No approved checks configured; an empty check set cannot pass')
    if approved_policy != policy_hash:
        raise WorkflowError('Execution requires explicit approval of the current policy_sha256')
    require_lock(root)
    from .models import local_directory
    local_directory(root)  # Fail before executing if evidence cannot safely be written.
    before = inspect(root, config['integration']['base_ref'])
    bound = binding(root)
    source = config['coordination']
    if bound:
        ref = bound.get('task_ref')
        expected = dict(provider=source['provider'], instance=source['base_url'].rstrip('/'),
                        repository=source['repository'])
        if not isinstance(ref, dict) or any(ref.get(key) != value for key, value in expected.items()):
            raise WorkflowError('Task binding belongs to another platform/repository; prepare with explicit --rebind')
    record = envelope('VerificationEvidence', task_ref=bound.get('task_ref') if bound else None,
                      actor=actors.snapshot(root, config, online),
                      before=before, after=None, policy_sha256=policy_hash,
                      toolchain=runtime_identity(), checks=[], status='incomplete',
                      provenance='local_execution_unattested', ci_refs=[], drift=[])
    target = local_target(root, 'evidence', record['run_id'] + '.json')
    if target.exists():
        raise WorkflowError('Evidence destination already exists')
    for name in names:
        result = execute(root, name, checks[name], source.get('token_env', f'TWC_{source["provider"].upper()}_TOKEN'),
                         source.get('identity_token_env'))
        record['checks'].append(result)
        if result['status'] != 'passed':
            break
        try:
            _, latest_hash = load(root)
            if latest_hash != policy_hash:
                record['drift'].append('policy_changed_during_execution')
                break
        except WorkflowError:
            record['drift'].append('policy_unreadable_after_execution')
            break
    completed = {check['check'] for check in record['checks']}
    for name in names:
        if name not in completed:
            record['checks'].append(dict(check=name, argv=checks[name]['argv'], cwd=checks[name].get('cwd', '.'),
                                         started_at=None, ended_at=None, exit_code=None, status='not_run',
                                         reason='earlier_check_did_not_complete', log_ref=None))
    try:
        record['after'] = inspect(root, config['integration']['base_ref'])
        if code_identity(before) != code_identity(record['after']):
            record['drift'].append('code_changed_during_execution')
        if not before['fingerprint_complete'] or not record['after']['fingerprint_complete']:
            record['drift'].append('workspace_fingerprint_incomplete')
        _, current_policy = load(root)
        if current_policy != policy_hash:
            record['drift'].append('policy_changed_during_execution')
        if runtime_identity() != record['toolchain']:
            record['drift'].append('runtime_changed_during_execution')
        if binding(root) != bound:
            record['drift'].append('workspace_task_binding_changed')
        record['git_identity_after'] = actors.git_identity(root)
        if record['git_identity_after'] != record['actor']['git']:
            record['drift'].append('git_identity_changed_during_execution')
    except WorkflowError:
        record['drift'].append('state_unreadable_after_execution')
    states = {row['status'] for row in record['checks']}
    if record['drift'] or 'incomplete' in states:
        record['status'] = 'incomplete'
    elif 'failed' in states:
        record['status'] = 'failed'
    elif 'not_run' in states:
        record['status'] = 'not_run'
    else:
        record['status'] = 'passed'
    path = save_local(root, 'evidence', record)
    return dict(evidence=path, **record)
