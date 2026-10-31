"""Execute explicitly approved checks and bind results to observable code state."""
import hashlib
import os
import signal
import subprocess
import threading
import time

from . import actors, tasks
from .context import binding
from . import sessions
from .models import WorkflowError, envelope, local_target, now, relative_path, save_local, task_ref, task_label
from .policy import load, require_lock, runtime_identity
from .workspace import code_identity, inspect


def _stop(process, job=None):
    if job is not None:
        job.stop()
    elif os.name == 'posix':
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        process.kill()
    process.wait(timeout=5)


def _group_alive(process, job=None):
    if job is not None:
        return job.alive()
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
    job = None
    try:
        cwd = relative_path(root, result['cwd'], must_exist=True)
        if os.name == 'nt':
            from .windows_job import WindowsJob
            job = WindowsJob()
            process = job.start(check['argv'], cwd=cwd, env=env)
        else:
            process = subprocess.Popen(check['argv'], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       start_new_session=os.name == 'posix')
        reader = threading.Thread(target=drain, args=(process.stdout,), daemon=True)
        reader.start()
        try:
            result['exit_code'] = process.wait(timeout=check.get('timeout_seconds', 300))
            result['status'] = 'passed' if result['exit_code'] == 0 else 'failed'
            if job is not None:
                result.update(job.outcome())
        except subprocess.TimeoutExpired:
            result.update(status='incomplete', reason='timeout')
            _stop(process, job)
            result['exit_code'] = process.returncode
        except KeyboardInterrupt:
            result.update(status='incomplete', reason='cancelled')
            _stop(process, job)
            result['exit_code'] = process.returncode
        alive = _group_alive(process, job)
        if alive is True:
            if result['status'] == 'passed':
                result.update(status='incomplete', reason='child_process_still_running')
            _stop(process, job)
        elif alive is None and result['status'] == 'passed':
            result.update(status='incomplete', reason='process_tree_completion_unverified')
        reader.join(timeout=2)
        if reader.is_alive():
            # A descendant retained stdout after the parent exited. Do not certify completion.
            result.update(status='incomplete', reason='child_process_output_still_open')
            _stop(process, job)
            reader.join(timeout=2)
        if reader_failed:
            result.update(status='incomplete', reason='output_read_failed')
    except FileNotFoundError:
        result.update(status='not_run', reason='executable_or_cwd_missing')
    except (OSError, subprocess.SubprocessError):
        result.update(status='incomplete', reason='execution_error')
        if process is not None:
            try:
                _stop(process, job)
            except (OSError, subprocess.SubprocessError):
                result.update(status='incomplete', reason='process_cleanup_failed')
    finally:
        if job is not None:
            try:
                job.close()
            except OSError:
                result.update(status='incomplete', reason='process_cleanup_failed')
        if process is not None and process.stdout is not None and (reader is None or not reader.is_alive()):
            process.stdout.close()
    result.update(ended_at=now(), duration_seconds=round(time.monotonic() - start, 3),
                  output_sha256=output_hash.hexdigest(), output_bytes=output_size)
    return result


def verify(root, config, policy_hash, selected=(), execute_commands=False, approved_policy=None, online=False,
           task=None, session=None):
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
    with sessions.workspace_lock(root):
        return _verify(root, config, policy_hash, checks, names, online, task, session)


def _verify(root, config, policy_hash, checks, names, online, task, session):
    require_lock(root)
    if load(root)[1] != policy_hash:
        raise WorkflowError('Project policy changed before verification; review the current policy')
    from .models import local_directory
    local_directory(root)  # Fail before executing if evidence cannot safely be written.
    before = inspect(root, config['integration']['base_ref'])
    bound = binding(root, session)
    source = config.get('coordination', {})
    if bound:
        ref = bound.get('task_ref')
        if ref != task_ref(config, task_label(ref)):
            raise WorkflowError('Task binding belongs to another platform/repository; prepare with explicit --rebind')
    ref = tasks.current(root, config, task, bound, before, session)[0]
    if task and bound and bound.get('task_ref') != ref:
        raise WorkflowError('Requested task does not match the current workspace task binding')
    task_record = tasks.load(root, ref) if ref else None
    if task_record and task_record.get('execution'):
        sessions.require(session)
        if not bound or bound.get('task_ref') != ref or task_record['execution']['state'] != 'in_progress':
            raise WorkflowError('Start the lifecycle task in this session before recording verification')
    if task_record:
        tasks.preflight(root, ref)  # Fail before executing if the summary cannot be committed.
    record = envelope('VerificationEvidence', task_ref=ref,
                      contract_sha256=task_record['contract_sha256'] if task_record else None,
                      actor=actors.snapshot(root, config, online),
                      before=before, after=None, policy_sha256=policy_hash,
                      toolchain=runtime_identity(), checks=[], status='incomplete',
                      provenance='local_execution_unattested', ci_refs=[], drift=[])
    target = local_target(root, 'evidence', record['run_id'] + '.json')
    if target.exists():
        raise WorkflowError('Evidence destination already exists')
    for name in names:
        result = execute(root, name, checks[name], source.get('token_env', f'TWC_{source.get("provider", "local").upper()}_TOKEN'),
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
        if binding(root, session) != bound:
            record['drift'].append('workspace_task_binding_changed')
        if ref and (tasks.load(root, ref) or {}).get('contract_sha256') != record['contract_sha256']:
            record['drift'].append('task_contract_changed_during_execution')
        if task_record and (tasks.load(root, ref) or {}).get('execution') != task_record.get('execution'):
            record['drift'].append('task_execution_changed_during_execution')
        record['git_identity_after'] = actors.git_identity(root)
        if record['git_identity_after'] != record['actor']['git']:
            record['drift'].append('git_identity_changed_during_execution')
        record['member_after'] = actors.member_name(root)
        if record['member_after'] != record['actor']['member']:
            record['drift'].append('member_name_changed_during_execution')
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
    shared = tasks.save_evidence(root, ref, task_record, record) if task_record else None
    return dict(evidence=path, task_evidence=shared,
                next_step=tasks.commit_hint(root, ref) if shared else 'prepare a task to record shareable evidence',
                **record)
