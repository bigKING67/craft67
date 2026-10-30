"""Local execution progress; never platform assignment, approval, or merge authority."""
from . import actors, context, policy, records, sessions, tasks, workspace
from .models import WorkflowError, canonical, digest, now, relative_path, task_label, task_ref

STATES = ('planning', 'in_progress', 'paused', 'completed', 'archived')


def validate(value):
    def require(condition):
        if not condition:
            raise WorkflowError('Invalid task execution record')
    require(isinstance(value, dict) and value.get('schema_version') == 1)
    require(value.get('state') in STATES and isinstance(value.get('history'), list) and bool(value['history']))
    parent = value.get('parent')
    if parent is not None:
        task_label(parent)
    for row in value['history']:
        require(isinstance(row, dict) and row.get('state') in STATES and records._time(row.get('at'))
                and isinstance(row.get('actor'), dict) and isinstance(row.get('action'), str))
    require(value['history'][-1]['state'] == value['state'])
    completion = value.get('completion')
    require((value['state'] in ('completed', 'archived')) == (completion is not None))
    if completion is not None:
        require(isinstance(completion, dict) and records._time(completion.get('at')))
        for key in ('contract_sha256', 'policy_sha256'):
            require(records._hash(completion.get(key)))
        records._code(completion.get('code'))
        require(isinstance(completion.get('toolchain'), dict) and isinstance(completion.get('actor'), dict))
        require(records._strings(completion.get('reviewed')) and isinstance(completion.get('review_sources'), list))
        for source in completion['review_sources']:
            require(isinstance(source, dict) and records._relative(source.get('path')) and records._hash(source.get('sha256')))
        require(isinstance(completion.get('children'), dict))
        for key, sha in completion['children'].items():
            require(isinstance(key, str) and records._hash(sha))
        require(completion.get('authority') == 'local_execution_only' and completion.get('merge_authorized') is False)
    return value


def graph(root, config):
    folder = root / workspace.TASKS
    if folder.is_symlink():
        raise WorkflowError('Task directory cannot be a symlink')
    result = {}
    for path in sorted(folder.iterdir()) if folder.is_dir() else ():
        if path.is_symlink():
            raise WorkflowError('Task directory cannot contain a symlink')
        if not path.is_dir():
            continue
        ref = task_ref(config, path.name.replace('-', ':', 1))
        row = tasks.load(root, ref)
        if row is None:
            raise WorkflowError('Task directory is missing task.json')
        result[task_label(ref)] = row
    for label, row in result.items():
        chain, current = set(), label
        while current:
            if current in chain:
                raise WorkflowError('Task parent relationship is cyclic')
            chain.add(current)
            parent = (result[current].get('execution') or {}).get('parent')
            if parent is None:
                break
            current = task_label(parent)
            if parent != task_ref(config, current) or current not in result:
                raise WorkflowError('Task parent is missing or belongs to another project')
    return result


def children(tree, ref):
    return {label: row for label, row in tree.items() if (row.get('execution') or {}).get('parent') == ref}


def review_sources(root, paths):
    result = []
    for relative in dict.fromkeys(paths):
        path = relative_path(root, relative, must_exist=True)
        if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents) if root in p.parents):
            raise WorkflowError('Review evidence must be a regular repository file without symlinks')
        if workspace.git(root, 'check-ignore', '--no-index', relative, allowed=(0, 1)).strip():
            raise WorkflowError('Review evidence must be committable, not ignored')
        if path.stat().st_size > 4 * 1024 * 1024 or not path.stat().st_size:
            raise WorkflowError('Review evidence must be nonempty and at most 4 MiB')
        result.append(dict(path=relative, sha256=digest(path.read_bytes())))
    return result


def blockers(root, config, policy_hash, runtime, row, code, reviewed=(), sources=()):
    problems = []
    if not row.get('contract') or not row.get('acceptance'):
        problems.append('acceptance_missing')
    if tasks.stale_sources(root, row):
        problems.append('contract_sources_changed')
    if not code['base_is_ancestor'] or not code['fingerprint_complete']:
        problems.append('code_or_base_incomplete')
    if workspace.repository_identity(config, code) == 'mismatch':
        problems.append('repository_mismatch')
    states = tasks.check_states(config, row['task_ref'], row,
                                tasks.evidence(root, row['task_ref']), code, policy_hash, runtime)
    if any(state['status'] != 'passed' for state in states.values()):
        problems.append('required_checks_not_currently_passed')
    criteria = tasks.acceptance_states(row, states)
    manual = {item['id'] for item in criteria if item['status'] == 'needs_review'}
    if set(reviewed) != manual or (manual and not sources):
        problems.append('explicit_acceptance_review_missing_or_invalid')
    if any(item['status'] not in ('verified', 'needs_review') for item in criteria):
        problems.append('acceptance_not_verified')
    if sources:
        try:
            if review_sources(root, [source['path'] for source in sources]) != list(sources):
                problems.append('review_evidence_changed')
        except WorkflowError:
            problems.append('review_evidence_unavailable')
    return problems


def completion_problems(root, config, policy_hash, runtime, tree, row, code, cache=None):
    cache = cache if cache is not None else {}
    label = task_label(row['task_ref'])
    if label in cache:
        return cache[label]
    execution = row.get('execution') or {}
    saved = execution.get('completion')
    if execution.get('state') not in ('completed', 'archived') or saved is None:
        return ['not_completed']
    problems = blockers(root, config, policy_hash, runtime, row, code, saved['reviewed'], saved['review_sources'])
    if (saved['contract_sha256'] != row['contract_sha256'] or saved['policy_sha256'] != policy_hash
            or saved['toolchain'] != runtime or workspace.code_identity(saved['code']) != workspace.code_identity(code)):
        problems.append('completion_context_changed')
    actual = children(tree, row['task_ref'])
    if set(actual) != set(saved['children']):
        problems.append('children_changed')
    for child_label, child in actual.items():
        child_completion = (child.get('execution') or {}).get('completion')
        if (saved['children'].get(child_label) != digest(canonical(child_completion))
                or completion_problems(root, config, policy_hash, runtime, tree, child, code, cache)):
            problems.append('child_not_currently_completed:' + child_label)
    cache[label] = problems
    return problems


def view(root, config, policy_hash, runtime, row, code=None, tree=None):
    execution = row.get('execution')
    if not execution:
        return dict(state='unmanaged', completion='not_recorded', authority='local_execution_only')
    tree = tree if tree is not None else graph(root, config)
    code = code or workspace.inspect(root, config['integration']['base_ref'])
    problems = completion_problems(root, config, policy_hash, runtime, tree, row, code)
    return dict(state=execution['state'], parent=execution['parent'],
                children=sorted(children(tree, row['task_ref'])),
                completion=('stale' if problems else 'current') if execution['completion'] else 'not_recorded',
                completion_problems=problems if execution['completion'] else [],
                reviewed_acceptance=(execution['completion'] or {}).get('reviewed', []),
                review_sources=(execution['completion'] or {}).get('review_sources', []),
                review_authority='local_attestation_unverified',
                authority='local_execution_only', merge_authorized=False)


def _save(root, row, state, action, actor, *, parent=None, completion=None):
    previous = row.get('execution')
    history = list(previous['history']) if previous else []
    event = dict(action=action, state=state, at=now(), actor=actor)
    if previous and previous['completion'] and action == 'reopen':
        event['previous_completion'] = previous['completion']
    history.append(event)
    row = dict(row, execution=dict(schema_version=1, state=state, parent=previous['parent'] if previous else parent,
                                   history=history, completion=completion))
    validate(row['execution'])
    tasks.write(tasks.target(root, row['task_ref'], 'task.json'), row)
    return row


def _owner(config):
    if config['workflow_owner'] == 'trellis':
        raise WorkflowError('Trellis owns this project lifecycle; explicit project cutover is required first')


@sessions.serialized
def create(root, config, policy_hash, task, contract_path, parent=None, session=None, offline=False):
    _owner(config)
    session = sessions.require(session)
    policy.require_lock(root)
    ref = task_ref(config, task)
    tree = graph(root, config)
    if task_label(ref) in tree:
        raise WorkflowError('Task already exists; start it to adopt/resume, do not recreate it')
    if actors.member_name(root)['status'] != 'available':
        raise WorkflowError('A member name is required to create a lifecycle task')
    parent_ref = task_ref(config, parent) if parent else None
    if parent_ref:
        parent_row = tree.get(task_label(parent_ref))
        if not parent_row or not parent_row.get('execution'):
            raise WorkflowError('Parent must be an existing lifecycle-managed task')
        if parent_row['execution']['state'] in ('completed', 'archived'):
            raise WorkflowError('Reopen the parent before adding a child')
    # New creation does not steal another task's binding in this session.
    prepared = context.prepare(root, config, policy_hash, task, contract_path, offline=offline, session=session)
    row = tasks.load(root, ref)
    _save(root, row, 'planning', 'create', prepared['actor'], parent=parent_ref)
    return dict(status='ok', task_ref=ref, execution_state='planning', session=session, merge_authorized=False)


@sessions.serialized
def transition(root, config, policy_hash, action, task=None, session=None, reviewed=(), review_evidence=()):
    _owner(config)
    session = sessions.require(session)
    policy.require_lock(root)
    if policy.load(root)[1] != policy_hash:
        raise WorkflowError('Project policy changed; reload before changing task execution')
    bound = context.binding(root, session)
    if action == 'finish':
        # Explicitly end this session's pointer, even after a branch switch; no task state write.
        sessions.clear(root, session)
        return dict(status='ok', session=session, task_state_changed=False, binding_cleared=bool(bound))
    tree = graph(root, config)
    if action in ('start', 'reopen') and task:
        ref = task_ref(config, task)
        if bound and bound.get('task_ref') != ref:
            raise WorkflowError('Session is bound to another task; finish that session binding first')
    else:
        ref = tasks.current(root, config, task, bound, session=session)[0]
        if not bound or ref != bound.get('task_ref'):
            raise WorkflowError('Start this task in the current session before changing its execution state')
    row = tree.get(task_label(ref)) if ref else None
    if row is None:
        raise WorkflowError('Task record missing; create or prepare its contract first')
    previous = row.get('execution')
    state = previous['state'] if previous else 'unmanaged'
    actor = actors.snapshot(root, config, online=False)
    if actor['member']['status'] != 'available':
        raise WorkflowError('A member name is required to record task execution progress')
    if action == 'start':
        if state in ('completed', 'archived'):
            raise WorkflowError('Task is completed/archived; explicitly reopen using task reopen --task')
        code = workspace.inspect(root, config['integration']['base_ref'])
        # Explicit start is the deliberate branch/worktree binding operation.
        sessions.path(root, session, writing=True)
        row = _save(root, row, 'in_progress', 'start', actor) if state != 'in_progress' else row
        sessions.write(root, dict(task_ref=ref, branch=code['branch']), session)
    elif action == 'pause':
        if state != 'in_progress':
            raise WorkflowError('Only an in-progress task can be paused')
        row = _save(root, row, 'paused', 'pause', actor)
        sessions.clear(root, session)
    elif action == 'reopen':
        if state not in ('completed', 'archived'):
            raise WorkflowError('Only completed/archived execution can be reopened')
        code = workspace.inspect(root, config['integration']['base_ref'])
        sessions.path(root, session, writing=True)
        row = _save(root, row, 'in_progress', 'reopen', actor)
        sessions.write(root, dict(task_ref=ref, branch=code['branch']), session)
    elif action in ('complete', 'archive'):
        required = 'in_progress' if action == 'complete' else 'completed'
        if state != required:
            raise WorkflowError('Task must be ' + required + ' before ' + action)
        runtime = policy.runtime_identity()
        code = workspace.inspect(root, config['integration']['base_ref'])
        if action == 'archive':
            problems = completion_problems(root, config, policy_hash, runtime, tree, row, code)
            completion = previous['completion']
        else:
            if len(set(reviewed)) != len(reviewed) or (review_evidence and not reviewed):
                raise WorkflowError('Review evidence must accompany distinct explicit acceptance IDs')
            if any(relative_path(root, path) == tasks.directory(root, ref) / 'task.json' for path in review_evidence):
                raise WorkflowError('The task record being changed cannot serve as its own review evidence')
            sources = review_sources(root, review_evidence)
            problems = blockers(root, config, policy_hash, runtime, row, code, reviewed, sources)
            descendants = children(tree, ref)
            for label, child in descendants.items():
                if completion_problems(root, config, policy_hash, runtime, tree, child, code):
                    problems.append('child_not_currently_completed:' + label)
            completion = dict(at=now(), actor=actor, contract_sha256=row['contract_sha256'],
                              policy_sha256=policy_hash, toolchain=runtime, code=workspace.portable(code),
                              reviewed=list(reviewed), review_sources=sources,
                              children={label: digest(canonical(child['execution']['completion']))
                                        for label, child in descendants.items() if child.get('execution')},
                              authority='local_execution_only', merge_authorized=False)
        if problems:
            return dict(status='attention_required', task_ref=ref, execution_state=state, blockers=problems,
                        applied=False, merge_authorized=False)
        if (policy.load(root)[1] != policy_hash or policy.runtime_identity() != runtime
                or graph(root, config) != tree
                or workspace.code_identity(workspace.inspect(root, config['integration']['base_ref'])) != workspace.code_identity(code)
                or context.binding(root, session) != bound
                or review_sources(root, [source['path'] for source in completion['review_sources']]) != completion['review_sources']):
            raise WorkflowError('Completion inputs changed during validation; no transition was written')
        row = _save(root, row, 'completed' if action == 'complete' else 'archived', action, actor, completion=completion)
        if action == 'archive':
            sessions.clear(root, session)
    else:
        raise WorkflowError('Unknown lifecycle transition')
    return dict(status='ok', task_ref=ref, execution_state=row['execution']['state'], session=session,
                authority='local_execution_only', merge_authorized=False)


def listing(root, config, policy_hash):
    tree = graph(root, config)
    runtime = policy.runtime_identity()
    code = workspace.inspect(root, config['integration']['base_ref'])
    return dict(status='ok', tasks=[dict(task=label, goal=(row.get('contract') or {}).get('goal'),
                                       execution=view(root, config, policy_hash, runtime, row, code, tree))
                                   for label, row in tree.items()])
