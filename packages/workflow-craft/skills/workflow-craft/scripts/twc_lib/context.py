"""Rebuildable task snapshots, never a second owner/status database."""
from . import actors, sessions, tasks
from .models import (WorkflowError, digest, envelope, local_target, now,
                     read_json, relative_path, save_local, task_ref, validate_contract)
from .providers import from_config, ProviderError
from .workspace import inspect, repository_identity


def provider(config):
    return from_config(config)


def observe(call):
    try:
        return dict(status='observed', observed_at=now(), data=call())
    except ProviderError as exc:
        return dict(status=exc.code, observed_at=now(), data=None)


def platform_snapshot(config, ref, offline=False):
    if ref['type'] == 'local':
        return dict(status='not_applicable', observed_at=now(), data=None)
    if offline:
        return dict(status='offline', observed_at=now(), data=None)
    api = provider(config)
    if ref['type'] == 'pr':
        change = observe(lambda: api.get_change(ref['number']))
        task = dict(change)
        task['change'] = change
        task['reviews'] = observe(lambda: api.get_reviews(ref['number']))
        data = change.get('data') or {}
        sha = (data.get('head') or {}).get('sha')
        task['checks'] = observe(lambda: api.get_checks(sha)) if sha else dict(status='unknown', data=None)
        task['checks_coverage'] = 'head_commit_statuses_only; merge-preview and server gates unverified'
        return task
    return observe(lambda: api.get_task(ref['number']))


def binding(root, session=None):
    value = sessions.read(root, session)
    if value is None:
        return None
    # Legacy v2 bindings already point to a local packet containing the prepared branch.
    packet = value.get('packet')
    if 'branch' not in value and isinstance(packet, str) and packet.startswith('.team-workflow/local/packets/'):
        source = relative_path(root, packet)
        if source.is_file():
            snapshot = read_json(source)
            if isinstance(snapshot, dict) and isinstance(snapshot.get('code'), dict) and 'branch' in snapshot['code']:
                value['branch'] = snapshot['code']['branch']
    return value


@sessions.serialized
def prepare(root, config, policy_hash, task, contract_path=None, offline=False, rebind=False, update_contract=False,
            session=None):
    from .policy import load, require_lock
    require_lock(root)
    if load(root)[1] != policy_hash:
        raise WorkflowError('Project policy changed before prepare; reload it')
    session = sessions.selected(session)
    ref = task_ref(config, task)
    current = None if rebind else binding(root, session)
    if current and not rebind:
        tasks.current(root, config, bound=current)
        if current.get('task_ref') != ref:
            raise WorkflowError('Workspace is bound to a different task; use another worktree or explicit --rebind')
    sessions.path(root, session, writing=True)
    existing = tasks.load(root, ref)
    if existing and existing.get('execution'):
        sessions.require(session)
        if existing['execution']['state'] in ('completed', 'archived'):
            raise WorkflowError('Reopen the completed/archived task before changing its contract or binding')
    contract = None
    sources = []
    if contract_path:
        path = relative_path(root, contract_path, must_exist=True)
        contract = validate_contract(read_json(path), root, personal=(ref['type'] == 'local'
                                     and config.get('development_mode') == 'personal'))
        sources.append(dict(path=contract_path, sha256=digest(path.read_bytes())))
        for name in contract['contracts']:
            path = relative_path(root, name, must_exist=True)
            if not path.is_file():
                raise WorkflowError('Contract references must name files')
            sources.append(dict(path=name, sha256=digest(path.read_bytes())))
    code = inspect(root, config['integration']['base_ref'], contract['scope'] if contract else ())
    code['repository_identity'] = repository_identity(config, code)
    if code['repository_identity'] == 'mismatch':
        raise WorkflowError('Configured repository differs from the Git remote on this instance')
    platform = platform_snapshot(config, ref, offline)
    if platform['status'] == 'observed':
        is_pr = bool(platform['data'].get('pull_request'))
        if ref['type'] == 'issue' and is_pr:
            raise WorkflowError('Issue number is a pull request; use pr:<number>')
    actor = actors.snapshot(root, config, online=not offline and ref['type'] != 'local')
    record, record_status = tasks.upsert(root, ref, contract, sources if contract else [], actor, update_contract)
    packet = envelope('WorkPacket', task_ref=ref, workflow_owner=config['workflow_owner'], actor=actor,
                      contract=contract, sources=sources, platform=platform, code=code,
                      policy_sha256=policy_hash, authority='derived_snapshot',
                      warnings=[('Local task contract; no platform assignment or approval is implied.' if ref['type'] == 'local'
                                 else 'Refresh platform facts before assignment/integration; dependencies are references, not resolved.')])
    path = save_local(root, 'packets', packet)
    sessions.write(root, dict(task_ref=ref, packet=path, branch=code['branch']), session)
    return dict(packet=path, task_ref=ref, platform_status=platform['status'],
                contract_status='provided' if record['contract'] else 'missing', code=code, actor=actor,
                task_record=(tasks.directory(root, ref) / 'task.json').relative_to(root).as_posix(),
                task_record_status=record_status, revision=record['revision'], acceptance=record['acceptance'],
                next_step='commit the task record on the task branch: ' + tasks.commit_hint(root, ref))
