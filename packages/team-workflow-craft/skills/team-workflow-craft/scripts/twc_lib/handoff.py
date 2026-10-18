"""Draft handoff material on the task branch. Readiness is advisory and never merge authorization."""
from . import actors, tasks
from .context import binding, platform_snapshot
from .models import WorkflowError, envelope
from .policy import runtime_identity
from .workspace import inspect, portable, repository_identity


def draft(root, config, policy_hash, task=None, done=(), remaining=(), next_steps=(), online=False):
    for text in (*done, *remaining, *next_steps):
        if tasks.placeholder(text):
            raise WorkflowError('Handoff entries must describe real work; placeholder text is rejected')
    current_binding = binding(root)
    ref = tasks.current(root, config, task, current_binding)[0]
    if not ref:
        raise WorkflowError('No current task; pass --task issue:<N>|pr:<N> or run prepare first')
    source = config['coordination']
    if (not isinstance(ref, dict) or ref.get('provider') != source['provider']
            or ref.get('instance') != source['base_url'].rstrip('/')
            or ref.get('repository') != source['repository']):
        raise WorkflowError('Task belongs to another configured instance/repository')
    if task and current_binding and current_binding.get('task_ref') != ref:
        raise WorkflowError('Requested task does not match the current workspace task binding')
    record = tasks.load(root, ref)
    if not record:
        raise WorkflowError('Task record missing; run prepare for this task first')
    contract = record.get('contract')
    code = inspect(root, config['integration']['base_ref'], contract.get('scope', ()) if contract else ())
    blockers, unknowns = [], []
    actor = actors.snapshot(root, config, online)
    if not actors.attributed(actor, ref['instance'], ref['provider']):
        unknowns.append('handoff_actor_unverified')
    if actor['git']['status'] != 'available':
        unknowns.append('git_identity_incomplete')
    code['repository_identity'] = repository_identity(config, code)
    if code['repository_identity'] == 'mismatch':
        blockers.append('configured_repository_differs_from_git_remote')
    elif code['repository_identity'] != 'matched':
        unknowns.append('git_remote_identity_unverified')
    if not contract:
        blockers.append('task_contract_missing')
    if tasks.stale_sources(root, record):
        blockers.append('task_or_interface_contract_changed')
    if not done or not next_steps:
        blockers.append('completion_or_next_step_missing')
    if remaining:
        blockers.append('work_remaining')
    if code['dirty']:
        blockers.append('uncommitted_work_not_portable')
    if not code['base_is_ancestor']:
        blockers.append('local_base_not_integrated')
    if not code['fingerprint_complete']:
        blockers.append('workspace_fingerprint_incomplete')
    rows = tasks.evidence(root, ref)
    runtime = runtime_identity()
    states = tasks.check_states(config, ref, record, rows, code, policy_hash, runtime)
    criteria = tasks.acceptance_states(record, states)
    if any(row['status'] in ('failed', 'incomplete') for row in states.values()):
        blockers.append('verification_not_passed')
    if not states or any(row['status'] in ('missing', 'stale') for row in states.values()):
        unknowns.append('required_verification_missing')
    if rows and not any(tasks.fresh(row, ref, record, code, policy_hash, runtime) for _, row in rows):
        blockers.append('stale_or_unrelated_evidence')
    if any(row['status'] in ('pending', 'failed', 'unknown_check') for row in criteria):
        blockers.append('acceptance_not_verified')
    if any(row['status'] == 'needs_review' for row in criteria):
        unknowns.append('acceptance_needs_human_review')
    for row in states.values():
        if row['status'] == 'passed' and not actors.attributed(row['actor'], ref['instance'], ref['provider']):
            unknowns.append('verification_actor_unverified')
    platform = platform_snapshot(config, ref) if online else dict(status='not_refreshed', data=None)
    if platform.get('status') != 'observed':
        unknowns.append('platform_not_current')
    elif ref['type'] == 'pr':
        change = platform.get('change', {})
        data = change.get('data') or {}
        if change.get('status') != 'observed':
            unknowns.append('pr_not_current')
        elif (data.get('head') or {}).get('sha') != code['head'] or (data.get('base') or {}).get('sha') != code['base']:
            blockers.append('platform_head_or_base_differs')
    else:
        unknowns.append('issue_has_no_verified_delivery_pr')
    readiness = 'not_ready' if blockers else 'unknown' if unknowns else 'advisory_ready'
    open_criteria = [f'{row["id"]} ({row["status"]}): {row["text"]}' for row in criteria if row['status'] != 'verified']
    handoff = envelope('Handoff', task_ref=ref, task_revision=record['revision'],
                       contract_sha256=record['contract_sha256'], code=portable(code),
                       actor=actor, prepared_by=record.get('recorded_by'),
                       integrator=contract.get('integrator') if contract else None,
                       done=list(done), remaining=list(remaining) + open_criteria, next_steps=list(next_steps),
                       acceptance=criteria, checks=states, platform=dict(status=platform.get('status')),
                       readiness=readiness, blockers=sorted(set(blockers)), unknowns=sorted(set(unknowns)),
                       merge_authorized=False, published=False,
                       trust='local evidence is not proof of honest execution or server approval')
    folder = tasks.directory(root, ref)
    lines = [f'# Handoff: {ref["repository"]} {ref["type"]}:{ref["number"]}', '',
             f'Readiness: {readiness}; draft only; merge authorization: false.', '',
             f'Instance: {ref["instance"]}', f'Branch: {code["branch"]}',
             f'Head: {code["head"]}', f'Base: {code["base"]}', f'Task revision: {record["revision"]}', '',
             f'Prepared by: {actors.label(record.get("recorded_by"))}',
             f'Handed off by: {actors.label(actor)}',
             f'Integrator (task contract, not merge authority): {handoff["integrator"] or "unknown"}', '',
             'Commit this directory on the task branch and push it; the next member runs `resume`.']
    for label, items in [('Completed', done), ('Remaining', handoff['remaining']), ('Next steps', next_steps),
                         ('Acceptance', [f'{row["id"]} [{row["status"]}] {row["text"]}' for row in criteria]),
                         ('Blockers', handoff['blockers']), ('Unknown', handoff['unknowns']),
                         ('Evidence', [f'{name}: {row["status"]} — {row["evidence"] or "none"}'
                                       f'{" — executed by " + actors.label(row["actor"]) if row["evidence"] else ""}'
                                       for name, row in states.items()])]:
        lines.extend(['', f'## {label}', ''] + [f'- {item}' for item in items])
    tasks.write(tasks.target(root, ref, 'handoff.json'), handoff)
    tasks.write(tasks.target(root, ref, 'handoff.md'), '\n'.join(lines) + '\n', text=True)
    relative = folder.relative_to(root).as_posix()
    return dict(handoff=relative + '/handoff.json', markdown=relative + '/handoff.md',
                next_step=tasks.commit_hint(root, ref), **handoff)
