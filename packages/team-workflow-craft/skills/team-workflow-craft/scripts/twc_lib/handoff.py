"""Draft handoff material. Readiness is advisory and never merge authorization."""
from . import actors
from .context import binding, load_packet, platform_snapshot, stale_sources
from .models import WorkflowError, envelope, local_target, read_json, relative_path, save_local
from .policy import runtime_identity
from .workspace import code_identity, inspect, repository_identity


def draft(root, config, policy_hash, packet_path, evidence_paths=(), done=(), remaining=(), next_steps=(), online=False):
    packet = load_packet(root, packet_path)
    ref = packet.get('task_ref')
    source = config['coordination']
    if (not isinstance(ref, dict) or ref.get('provider') != source['provider']
            or ref.get('instance') != source['base_url'].rstrip('/')
            or ref.get('repository') != source['repository']):
        raise WorkflowError('Packet belongs to another configured instance/repository')
    current_binding = binding(root)
    if current_binding and current_binding.get('task_ref') != ref:
        raise WorkflowError('Packet does not match current workspace task binding')
    contract = packet.get('contract')
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
    if stale_sources(root, packet):
        blockers.append('task_or_interface_contract_changed')
    if packet.get('policy_sha256') != policy_hash:
        blockers.append('packet_policy_stale')
    if not done or remaining or not next_steps:
        blockers.append('completion_or_next_step_missing')
    if code['dirty']:
        blockers.append('uncommitted_work_not_portable')
    if not code['base_is_ancestor']:
        blockers.append('local_base_not_integrated')
    if not code['fingerprint_complete']:
        blockers.append('workspace_fingerprint_incomplete')
    valid_checks = set()
    evidence = []
    current_runtime = runtime_identity()
    for path in evidence_paths:
        record = read_json(relative_path(root, path, must_exist=True))
        if not isinstance(record, dict) or record.get('kind') != 'VerificationEvidence' or record.get('schema_version') != 1:
            raise WorkflowError('Expected VerificationEvidence v1')
        fresh = (record.get('task_ref') == ref and record.get('policy_sha256') == policy_hash
                 and record.get('toolchain') == current_runtime and record.get('after') is not None
                 and code_identity(record['after']) == code_identity(code))
        evidence.append(dict(path=path, status=record.get('status'), fresh=fresh,
                             actor=record.get('actor'),
                             provenance=record.get('provenance', 'unknown')))
        if not actors.attributed(record.get('actor'), ref['instance'], ref['provider']):
            unknowns.append('verification_actor_unverified')
        if not fresh:
            blockers.append('stale_or_unrelated_evidence')
        elif record.get('status') != 'passed':
            blockers.append('verification_not_passed')
        else:
            for check in record.get('checks', []):
                expected = config.get('checks', {}).get(check.get('check'))
                if (expected and check.get('status') == 'passed' and check.get('exit_code') == 0
                        and check.get('argv') == expected['argv']
                        and check.get('cwd') == expected.get('cwd', '.')):
                    valid_checks.add(check['check'])
    required = set(config.get('checks', {}))
    if not required or required - valid_checks:
        unknowns.append('required_verification_missing')
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
    handoff = envelope('Handoff', task_ref=ref, packet=packet_path, code=code,
                       actor=actor, prepared_by=packet.get('actor'),
                       integrator=contract.get('integrator') if contract else None,
                       done=list(done), remaining=list(remaining), next_steps=list(next_steps),
                       evidence=evidence, platform=platform, readiness=readiness,
                       blockers=sorted(set(blockers)), unknowns=sorted(set(unknowns)),
                       merge_authorized=False, published=False,
                       trust='local evidence is not proof of honest execution or server approval')
    md_path = local_target(root, 'handoffs', handoff['run_id'] + '.md')
    path = save_local(root, 'handoffs', handoff)
    lines = [f'# Handoff: {ref["repository"]} {ref["type"]}:{ref["number"]}', '',
             f'Readiness: {readiness}; draft only; merge authorization: false.', '',
             f'Instance: {ref["instance"]}', f'Branch: {code["branch"]}',
             f'Head: {code["head"]}', f'Base: {code["base"]}', '',
             f'Prepared by: {actors.label(packet.get("actor"))}',
             f'Handed off by: {actors.label(actor)}',
             f'Integrator (task contract, not merge authority): {handoff["integrator"] or "unknown"}', '',
             'Publish/share the branch, task/spec references and sanitized evidence through the approved platform.',
             'Local artifact paths below are not portable URLs; upload reviewed artifacts before another person takes over.']
    for label, rows in [('Completed', done), ('Remaining', remaining), ('Next steps', next_steps),
                        ('Blockers', handoff['blockers']), ('Unknown', handoff['unknowns']),
                        ('Evidence (local)', [f'{row["path"]} — executed by {actors.label(row["actor"])}'
                                              for row in evidence])]:
        lines.extend(['', f'## {label}', ''] + [f'- {row}' for row in rows])
    with md_path.open('x', encoding='utf-8') as stream:
        stream.write('\n'.join(lines) + '\n')
    return dict(handoff=path, markdown=str(md_path.relative_to(root)), **handoff)
