"""Task records that travel with the branch: contract, evidence summaries and the latest handoff.

They are committed with the task branch so the next member can continue from a clone.
They reference, but never replace, platform assignment/status or Git review.
"""
import json
import os
from pathlib import Path
import re
import uuid

from . import actors, records, sessions
from .models import WorkflowError, acceptance_items, canonical, digest, now, read_json, relative_path, task_ref, task_label
from .workspace import TASKS, code_identity, git, inspect, portable, succeeds

PLACEHOLDER = re.compile(r'^(todo|tbd|tba|wip|fixme|n/?a|none|null|\.{2,}|…+|-+|\?+|待定|待补充|待填写?|无|略|同上)$', re.I)
CHECK_FIELDS = ('check', 'cwd', 'status', 'exit_code', 'reason', 'started_at', 'ended_at',
                'duration_seconds', 'output_sha256', 'output_bytes')


def key(ref):
    return task_label(ref).replace(':', '-', 1)


def directory(root, ref):
    return root / TASKS / key(ref)


def target(root, ref, *parts):
    """Committable destination under the task directory; no symlinks, not Git-ignored."""
    path = directory(root, ref).joinpath(*parts)
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise WorkflowError('Task metadata path cannot contain a symlink')
    if git(root, 'check-ignore', '--no-index', path.relative_to(root).as_posix(), allowed=(0, 1)).strip():
        raise WorkflowError('Task metadata is Git-ignored; it must be committable with the task branch')
    return path


def write(path, value, text=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    with temporary.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value if text else json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    os.replace(temporary, path)


def contract_hash(contract, sources):
    return digest(canonical(dict(contract=contract, sources=sources)))


def load(root, ref):
    path = directory(root, ref) / 'task.json'
    if path.is_symlink():
        raise WorkflowError('Task record cannot be a symlink')
    if not path.exists():
        return None
    value = read_json(path)
    records.validate(value, ref, 'TaskRecord')
    try:
        derived = acceptance_items(value.get('contract'))
    except WorkflowError:
        derived = None
    if (value.get('contract_sha256') != contract_hash(value.get('contract'), value.get('sources'))
            or value.get('acceptance') != derived):
        raise WorkflowError(f'Task record {key(ref)} was edited outside prepare; review and rerun prepare --update-contract')
    return value


def upsert(root, ref, contract, sources, actor, update=False):
    """Record the contract once; later changes must be explicit and invalidate older evidence."""
    existing = load(root, ref)
    if contract is None and update:
        raise WorkflowError('--update-contract requires --contract')
    if existing and contract is None:
        return existing, 'unchanged'
    sha = contract_hash(contract, sources)
    if existing and existing['contract_sha256'] == sha:
        return existing, 'unchanged'
    if existing and existing['contract'] is not None and not update:
        raise WorkflowError('Task contract or referenced files changed since the recorded revision; '
                            'review the change and rerun prepare with --update-contract')
    history = list(existing.get('history', [])) if existing else []
    if existing:
        history.append(dict(revision=existing['revision'], contract_sha256=existing['contract_sha256'],
                            superseded_at=now()))
    value = dict(schema_version=2, kind='TaskRecord', task_ref=ref,
                 revision=existing['revision'] + 1 if existing else 1,
                 contract=contract, acceptance=acceptance_items(contract), sources=sources,
                 contract_sha256=sha, recorded_by=actor, recorded_at=now(), history=history,
                 authority='derived from the platform task and repository files; not an owner/status record')
    if existing and existing.get('execution'):
        value['execution'] = existing['execution']
    write(target(root, ref, 'task.json'), value)
    return value, 'updated' if existing else 'created'


def stale_sources(root, task):
    stale = []
    for source in (task or {}).get('sources', []):
        path = relative_path(root, source['path'])
        if not path.is_file() or digest(path.read_bytes()) != source['sha256']:
            stale.append(source['path'])
    return stale


def preflight(root, ref):
    target(root, ref, 'evidence', 'probe.json')
    target(root, ref, 'handoff.json')


def save_evidence(root, ref, task, record):
    """Commit-safe summary: hashes and statuses only, no local paths, remotes or output."""
    summary = dict(schema_version=2, kind='VerificationRecord', run_id=record['run_id'],
                   created_at=record['created_at'], task_ref=ref,
                   contract_sha256=task['contract_sha256'], policy_sha256=record['policy_sha256'],
                   toolchain=record['toolchain'], actor=record['actor'], provenance=record['provenance'],
                   status=record['status'], drift=record['drift'],
                   code=portable(record['after']) if record.get('after') else None,
                   checks=[dict({name: row.get(name) for name in CHECK_FIELDS},
                                command_sha256=records.command_hash(row['argv'], row.get('cwd', '.')))
                           for row in record['checks']])
    stamp = re.sub(r'\D', '', record['created_at'][:26])
    path = target(root, ref, 'evidence', f'{stamp}-{record["run_id"]}.json')
    if path.exists():
        raise WorkflowError('Evidence destination already exists')
    write(path, summary)
    return path.relative_to(root).as_posix()


def evidence(root, ref):
    folder = directory(root, ref) / 'evidence'
    if folder.is_symlink():
        raise WorkflowError('Evidence directory cannot be a symlink')
    rows = []
    for path in folder.glob('*.json') if folder.is_dir() else ():
        if path.is_symlink():
            raise WorkflowError('Evidence record cannot be a symlink')
        rows.append((path.relative_to(root).as_posix(), records.validate(read_json(path), ref, 'VerificationRecord')))
    # Chronological by recorded time (UTC ISO, microseconds); file names only break ties.
    return sorted(rows, key=lambda row: (str(row[1].get('created_at', '')) if isinstance(row[1], dict) else '', row[0]))


def same_context(row, ref, task, code, policy_hash, runtime):
    return (isinstance(row, dict) and row.get('kind') == 'VerificationRecord' and row.get('schema_version') == 2
            and row.get('task_ref') == ref and row.get('contract_sha256') == task['contract_sha256']
            and row.get('policy_sha256') == policy_hash and row.get('toolchain') == runtime
            and isinstance(row.get('code'), dict)
            and code_identity(row['code']) == code_identity(code))


def fresh(row, ref, task, code, policy_hash, runtime):
    return same_context(row, ref, task, code, policy_hash, runtime) and not row.get('drift')


def check_states(config, ref, task, rows, code, policy_hash, runtime):
    """Newest fresh observation per configured check; older passes do not outlive a newer failure."""
    states = {name: dict(status='missing', evidence=None, actor=None) for name in config.get('checks', {})}
    for path, row in rows:
        if not same_context(row, ref, task, code, policy_hash, runtime):
            # Recorded, but for other code, contract, policy or toolchain: rerun, not "never ran".
            for check in row.get('checks', []) if isinstance(row, dict) else ():
                state = states.get(check.get('check'))
                if state and state['status'] == 'missing' and check.get('status') != 'not_run':
                    state.update(status='stale', evidence=path, actor=row.get('actor'))
            continue
        for check in row.get('checks', []):
            expected = config.get('checks', {}).get(check.get('check'))
            if not expected or (check.get('status') == 'not_run' and check.get('started_at') is None
                                and check.get('reason') == 'earlier_check_did_not_complete'):
                continue
            command = check.get('command_sha256') or records.command_hash(check['argv'], check['cwd'])
            matches = command == records.command_hash(expected['argv'], expected.get('cwd', '.'))
            passed = matches and check.get('status') == 'passed' and check.get('exit_code') == 0
            states[check['check']] = dict(status='incomplete' if row.get('drift') else 'passed' if passed
                                          else check['status'] if check['status'] in ('failed', 'not_run')
                                          else 'incomplete', evidence=path, actor=row.get('actor'))
    return states


def acceptance_states(task, states):
    result = []
    for item in task.get('acceptance', []):
        if not item['checks']:
            status = 'needs_review'
        elif any(name not in states for name in item['checks']):
            status = 'unknown_check'
        elif all(states[name]['status'] == 'passed' for name in item['checks']):
            status = 'verified'
        elif any(states[name]['status'] in ('failed', 'incomplete') for name in item['checks']):
            status = 'failed'
        else:
            status = 'pending'
        result.append(dict(item, status=status))
    return result


def latest_handoff(root, ref):
    path = directory(root, ref) / 'handoff.json'
    if path.is_symlink():
        raise WorkflowError('Handoff record cannot be a symlink')
    return records.validate(read_json(path), ref, 'Handoff') if path.exists() else None


def touched(root, code):
    """Task directories changed on this branch since it left the integration base."""
    names = set()
    if code.get('merge_base'):
        raw = git(root, 'diff', '--name-only', '-z', code['merge_base'], 'HEAD', '--', TASKS)
        names.update(os.fsdecode(path) for path in raw.split(b'\0') if path)
    names.update(code.get('task_metadata_changes', []))
    prefix = TASKS + '/'
    return sorted({name[len(prefix):].split('/', 1)[0] for name in names if name.startswith(prefix)})


def current(root, config, explicit=None, bound=None, code=None, session=None):
    """Explicit task → local binding → the single task directory this branch changed."""
    if bound:
        code = code or inspect(root, config['integration']['base_ref'])
        ref = bound.get('task_ref')
        if ref != task_ref(config, task_label(ref)):
            raise WorkflowError('Task belongs to another configured instance/repository; prepare with --rebind')
        if ('branch' not in bound or bound['branch'] != code['branch']
                or not (directory(root, ref) / 'task.json').is_file()):
            raise WorkflowError('Task binding conflicts with this branch; review the current task and run prepare --rebind')
    if explicit:
        return task_ref(config, explicit), 'explicit', []
    if bound:
        return bound.get('task_ref'), 'binding', []
    if sessions.selected(session):
        return None, 'session_unbound', []
    code = code or inspect(root, config['integration']['base_ref'])
    candidates = touched(root, code)
    if len(candidates) == 1:
        match = re.fullmatch(r'(issue|pr)-([1-9][0-9]*)|(local)-([a-z0-9][a-z0-9_-]{0,63})', candidates[0])
        if match:
            return task_ref(config, candidates[0].replace('-', ':', 1)), 'branch_changes', candidates
    return None, 'unresolved', candidates


def placeholder(text):
    core = text.strip().strip('。.;；:：')
    return not core or bool(PLACEHOLDER.fullmatch(core))


def commit_hint(root, ref):
    folder = directory(root, ref).relative_to(root).as_posix()
    return f'git add -- {folder} && git commit -m "twc: update {key(ref)}" -- {folder}'


def resume(root, config, policy_hash, runtime, bound, explicit=None, session=None):
    """Read-only start-of-session view of where the task stands."""
    member = actors.member_name(root)
    member_actions = []
    if member['status'] != 'available':
        member['message'] = actors.MEMBER_NAME_PROMPT
        member_actions.append('configure_member_name')
    ref, resolved_by, candidates = current(root, config, explicit, bound, session=session)
    if not ref:
        if sessions.selected(session):
            return dict(status='no_task', resolved_by=resolved_by, candidates=[], member=member,
                        session=sessions.selected(session),
                        next_actions=member_actions + ['task list', 'resume --task <existing-task>',
                                                       'task start --task <reviewed-task> when resumption is authorized'])
        return dict(status='no_task', resolved_by=resolved_by, candidates=candidates, member=member,
                    next_actions=member_actions + ['prepare --task local:<slug>|issue:<N>|pr:<N> [--contract <path>]' if not candidates
                                                   else 'resume --task <one of the candidates>'])
    task = load(root, ref)
    if not task:
        return dict(status='no_task_record', task_ref=ref, resolved_by=resolved_by, member=member,
                    next_actions=member_actions + [f'prepare --task {task_label(ref)} --contract <path>'])
    scope = (task.get('contract') or {}).get('scope', ())
    code = inspect(root, config['integration']['base_ref'], scope)
    states = check_states(config, ref, task, evidence(root, ref), code, policy_hash, runtime)
    criteria = acceptance_states(task, states)
    handoff = latest_handoff(root, ref)
    since = []
    start = (handoff or {}).get('code', {}).get('head') if isinstance((handoff or {}).get('code'), dict) else None
    if isinstance(start, str) and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', start):
        if succeeds(root, 'merge-base', '--is-ancestor', '--end-of-options', start, 'HEAD'):
            since = git(root, 'log', '--format=%h %an: %s', '-n', '20', f'{start}..HEAD').decode(
                'utf-8', errors='replace').splitlines()
    stale = stale_sources(root, task)
    actions = []
    if not code['base_is_ancestor']:
        actions.append('integrate_latest_base')
    if stale:
        actions.append('review_contract_change_then_prepare_--update-contract')
    if code['staged_outside_scope']:
        actions.append('review_staged_files_outside_scope_before_commit')
    rerun = sorted(name for name, row in states.items() if row['status'] != 'passed')
    if rerun:
        actions.append('verify: ' + ', '.join(rerun))
    actions += [f'review {row["id"]}: {row["text"]}' for row in criteria if row['status'] == 'needs_review']
    if code['dirty']:
        actions.append('commit_code_changes_with_pathspec')
    if code['task_metadata_changes']:
        actions.append('commit_task_metadata: ' + commit_hint(root, ref))
    if not actions:
        actions.append('handoff --draft --done ... --next ...')
    from . import lifecycle
    execution = lifecycle.view(root, config, policy_hash, runtime, task, code)
    return dict(status='ok', task_ref=ref, resolved_by=resolved_by, revision=task['revision'], execution=execution,
                session=sessions.selected(session),
                goal=(task.get('contract') or {}).get('goal'), integrator=(task.get('contract') or {}).get('integrator'),
                acceptance=criteria, checks=states, stale_sources=stale,
                code=dict(portable(code), staged_outside_scope=code['staged_outside_scope'],
                          outside_scope=code['outside_scope'], task_metadata_changes=code['task_metadata_changes']),
                last_handoff=None if not handoff else {name: handoff.get(name) for name in (
                    'created_at', 'readiness', 'done', 'remaining', 'next_steps', 'blockers', 'unknowns')},
                handed_off_by=None if not handoff else handoff.get('actor'),
                commits_since_handoff=since, member=member, next_actions=member_actions + actions)


def _validate_record(path, value, ref, kind):
    try:
        records.validate(value, ref, kind, portable=True)
    except WorkflowError as exc:
        return [f'{path}: {exc}']
    return []


def check(root, config, explicit=None):
    """Deterministic structure lint of committed task metadata; safe to run in CI."""
    problems = []
    if git(root, 'ls-files', '--', '.team-workflow/local').strip():
        problems.append('.team-workflow/local is tracked; it holds local-only snapshots')
    base = root / TASKS
    if base.is_symlink():
        return dict(status='attention_required', tasks=[], problems=['task directory is a symlink'])
    names = [key(task_ref(config, explicit))] if explicit else sorted(
        path.name for path in base.iterdir() if path.is_dir()) if base.is_dir() else []
    reports = []
    for name in names:
        rows = []
        match = re.fullmatch(r'(issue|pr)-([1-9][0-9]*)|(local)-([a-z0-9][a-z0-9_-]{0,63})', name)
        if not match:
            reports.append(dict(task=name, problems=['directory name is not local-<slug>, issue-<N> or pr-<N>']))
            continue
        ref = task_ref(config, name.replace('-', ':', 1))
        try:
            task = load(root, ref)
            if not task:
                rows.append('task.json missing')
            else:
                unknown = sorted({c for item in task['acceptance'] for c in item['checks']} - set(config.get('checks', {})))
                if unknown:
                    rows.append('acceptance references unconfigured checks: ' + ', '.join(unknown))
            for path, value in evidence(root, ref):
                rows += _validate_record(path, value, ref, 'VerificationRecord')
            handoff = latest_handoff(root, ref)
            if handoff:
                rows += _validate_record(f'{name}/handoff.json', handoff, ref, 'Handoff')
                if any(placeholder(item) for field in ('done', 'next_steps') for item in handoff.get(field, [])
                       if isinstance(item, str)):
                    rows.append('handoff contains placeholder text')
        except WorkflowError as exc:
            rows.append(str(exc))
        reports.append(dict(task=name, problems=rows))
    try:
        from . import lifecycle
        lifecycle.graph(root, config)
    except WorkflowError as exc:
        problems.append(str(exc))
    status = 'attention_required' if problems or any(row['problems'] for row in reports) else 'ok'
    return dict(status=status, tasks=reports, problems=problems)
