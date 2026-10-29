#!/usr/bin/env python3
"""Local team workflow tools. All commands emit JSON; no model or agent calls."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
if sys.version_info < (3, 11):
    print(json.dumps(dict(status='error', required_python='>=3.11',
                          python='.'.join(map(str, sys.version_info[:3])),
                          message='Python 3.11+ is required; select a supported interpreter.')))
    raise SystemExit(2)

from twc_lib import actors, context, evidence, handoff, policy, tasks, workspace
from twc_lib.models import WorkflowError
from twc_lib.providers import ProviderError


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--project', default='.', help='Path inside the target Git worktree')
    cli.add_argument('--version', action='version', version=policy.runtime_identity()['version'])
    commands = cli.add_subparsers(dest='command', required=True)
    doctor = commands.add_parser('doctor', help='Inspect Git, config, lock and optional platform capability')
    diagnosis = doctor.add_mutually_exclusive_group()
    diagnosis.add_argument('--online', action='store_true', help='Read the configured collaboration platform')
    diagnosis.add_argument('--local', action='store_true', help='Read-only member setup check; works before init, no network')
    init = commands.add_parser('init', help='Preview a minimal project configuration; no host rule edits')
    init.add_argument('--base-url', required=True)
    init.add_argument('--provider', choices=('gitea', 'cnb'), default='gitea')
    init.add_argument('--repository', required=True)
    init.add_argument('--base-ref', default='origin/main')
    init.add_argument('--workflow-owner', choices=('team-workflow-craft', 'trellis'), default='team-workflow-craft')
    mutation = init.add_mutually_exclusive_group()
    mutation.add_argument('--dry-run', action='store_true')
    mutation.add_argument('--apply', action='store_true')
    prepare = commands.add_parser('prepare', help='Write task records and binding; reads the platform unless --offline',
                                  description='Write task records, a local packet and binding. Reads platform task and identity by default; --offline skips platform reads, not local writes.')
    prepare.add_argument('--task', required=True)
    prepare.add_argument('--contract', help='Repository-relative JSON contract; no duplicate owner/status')
    prepare.add_argument('--offline', action='store_true', help='Skip platform reads; still write local task records, packet and binding')
    prepare.add_argument('--rebind', action='store_true', help='Explicitly replace the task binding; use --offline to skip platform reads')
    prepare.add_argument('--update-contract', action='store_true',
                         help='Record a reviewed contract change; older evidence becomes stale')
    resume = commands.add_parser('resume', help='Read-only start-of-session view: contract, acceptance, evidence, last handoff')
    resume.add_argument('--task', help='issue:N or pr:N; default is the local binding or the task this branch changed')
    lint = commands.add_parser('check', help='Lint committed task records; deterministic and safe for CI')
    lint.add_argument('--task')
    ws = commands.add_parser('workspace', help='Inspect or explicitly create an isolated worktree')
    ws_commands = ws.add_subparsers(dest='workspace_command', required=True)
    inspect = ws_commands.add_parser('inspect')
    inspect.add_argument('--scope', action='append', default=[])
    create = ws_commands.add_parser('create')
    create.add_argument('--path', required=True)
    create.add_argument('--branch', required=True)
    mutation = create.add_mutually_exclusive_group()
    mutation.add_argument('--apply', action='store_true')
    mutation.add_argument('--dry-run', action='store_true')
    verify = commands.add_parser('verify', help='Preview checks or explicitly execute an approved policy')
    verify.add_argument('--check', action='append', default=[])
    verify.add_argument('--execute', action='store_true')
    verify.add_argument('--approved-policy')
    verify.add_argument('--online', action='store_true', help='Read the current platform operator before executing checks')
    verify.add_argument('--task', help='Record shareable evidence for this task; default is the current task')
    transfer = commands.add_parser('handoff', help='Generate local handoff drafts; publishing is unsupported')
    transfer.add_argument('--draft', action='store_true')
    transfer.add_argument('--publish', action='store_true', help='Unsupported; fails without sending a request')
    transfer.add_argument('--task', help='issue:N or pr:N; default is the current task')
    transfer.add_argument('--done', action='append', default=[])
    transfer.add_argument('--remaining', action='append', default=[])
    transfer.add_argument('--next', dest='next_steps', action='append', default=[])
    transfer.add_argument('--online', action='store_true')
    return cli


def project_entries(root, identity):
    """Only inspect project-specific discovery paths, not unrelated user profiles/accounts."""
    entries = []
    for directory, hosts in (('.agents', ['codex', 'pi']), ('.claude', ['claude'])):
        path = root / directory / 'skills/team-workflow-craft'
        # Parent links must not turn a project-only check into a global profile scan.
        linked = any(part.is_symlink() for part in (root / directory, path.parent, path))
        entry = dict(path=str(path), hosts=hosts, exists=path.exists(), symlink=linked,
                     is_current=not linked and path.resolve() == policy.SKILL_ROOT.resolve())
        if linked:
            entry['matches_runtime'] = False
        elif path.exists():
            try:
                entry['matches_runtime'] = policy.runtime_identity(path) == identity
            except (WorkflowError, OSError):
                entry['matches_runtime'] = False
        entries.append(entry)
    return entries


def local_doctor(root):
    """Member setup check before or after init; never contacts the platform or runs project checks."""
    state = root / '.team-workflow'
    member = actors.member_name(root)
    config_path, lock_path = state / 'config.toml', state / 'toolchain.lock.json'
    identity = policy.runtime_identity()
    integrity = policy.installation_integrity()
    entries = project_entries(root, identity)
    config_status, lock_status = 'missing', 'missing'
    if (state.is_symlink() or (state.exists() and not state.is_dir())
            or config_path.is_symlink() or lock_path.is_symlink()):
        config_status, lock_status = 'unsafe_path', 'not_checked'
    else:
        if config_path.exists():
            try:
                policy.load(root)
                config_status = 'valid'
            except (WorkflowError, OSError, ValueError, KeyError, TypeError):
                config_status = 'invalid'
        if lock_path.exists():
            try:
                lock_status = policy.lock_status(root)['status']
            except (WorkflowError, OSError, ValueError, KeyError, TypeError):
                lock_status = 'invalid'
    posix = os.name == 'posix'
    base_ref = dict(status='not_checked')
    if config_status == 'valid':
        configured = policy.load(root)[0]['integration']['base_ref']
        try:
            base_ref = dict(status='resolved', configured=configured,
                            resolved=workspace.resolve_base(root, configured)[1])
        except WorkflowError:
            base_ref = dict(status='unresolved', configured=configured)
    entry_drift = integrity in ('mismatch', 'invalid_marker') or any(
        row.get('matches_runtime') is False for row in entries)
    next_steps = []
    if member['status'] != 'available':
        next_steps.append('configure_member_name')
        member['message'] = actors.MEMBER_NAME_PROMPT
    if config_status != 'valid':
        next_steps.append('initialize_project' if config_status == 'missing' else 'review_project_config')
    if lock_status != 'matched':
        next_steps.append('review_toolchain_lock')
    if entry_drift:
        next_steps.append('review_project_installation')
    if base_ref['status'] == 'unresolved':
        next_steps.append('fetch_or_fix_integration_base_ref')
    if not posix:
        next_steps.append('qualify_native_process_tree_verification')
    next_steps.append('confirm_skill_loading_in_new_session')
    attention = (member['status'] != 'available' or config_status != 'valid'
                 or lock_status != 'matched' or not posix or entry_drift
                 or base_ref['status'] == 'unresolved')
    return dict(status='attention_required' if attention else 'ok', scope='member_local_preflight',
                project=str(root), python=sys.version.split()[0], git=shutil.which('git'), os=sys.platform,
                project_config=config_status, base_ref=base_ref, toolchain=dict(status=lock_status), runtime=identity,
                installation_integrity=integrity, project_entries=entries,
                member=member,
                verification=dict(implementation='posix_process_group' if posix else 'unsupported'),
                host_loading='unverified', platform=dict(status='not_requested'), next_steps=next_steps)


def doctor(root, config, policy_hash, online):
    lock = policy.lock_status(root)
    code = workspace.inspect(root, config['integration']['base_ref'])
    code['repository_identity'] = workspace.repository_identity(config, code)
    integrity = policy.installation_integrity()
    actor = actors.snapshot(root, config, online)
    report = dict(status='ok' if lock['status'] == 'matched' else 'attention_required',
                  python=sys.version.split()[0], git=shutil.which('git'), runtime_path=str(policy.SKILL_ROOT),
                  toolchain=lock, policy_sha256=policy_hash, workspace=code, binding=context.binding(root),
                  host_loading='unverified', server_gates='unverified', platform=dict(status='not_requested'),
                  installation_integrity=integrity, actor=actor)
    if actor['git']['status'] != 'available':
        report['status'] = 'attention_required'
    report['project_entries'] = project_entries(root, lock['actual'])
    for entry in report['project_entries']:
        if entry.get('matches_runtime') is False or entry['symlink']:
            report['status'] = 'attention_required'
    if integrity in ('mismatch', 'invalid_marker') or code['repository_identity'] == 'mismatch':
        report['status'] = 'attention_required'
    report['discovery_scope'] = 'project paths only; global same-name conflicts and live loading unverified'
    if online:
        api = context.provider(config)
        platform = {key: context.observe(call) for key, call in (
            ('repository', api.get_repository), ('version', api.get_version))}
        platform['identity'] = actor['platform']
        # User/repository payloads may contain private metadata unrelated to diagnosis.
        repo_fields = ('path', 'visibility_level') if config['coordination']['provider'] == 'cnb' else ('full_name', 'default_branch')
        for key, fields in [('repository', repo_fields),
                            ('version', ('version',))]:
            if platform[key].get('data'):
                platform[key]['data'] = {field: platform[key]['data'].get(field) for field in fields}
        report['platform'] = platform
        if any(row['status'] != 'observed' for key, row in platform.items()
               if not (key == 'version' and config['coordination']['provider'] == 'cnb'
                       and row['status'] == 'unsupported')):
            report['status'] = 'attention_required'
    return report


def run(args):
    if args.command == 'handoff' and args.publish:
        raise WorkflowError('Publishing is unsupported; share reviewed drafts through the configured platform manually')
    root = workspace.root_for(Path(args.project))
    if args.command == 'doctor' and args.local:
        return local_doctor(root)
    if args.command == 'init':
        workspace.resolve(root, args.base_ref)
        return policy.init(root, args.base_url, args.repository, args.base_ref, args.workflow_owner, args.apply, args.provider)
    config, policy_hash = policy.load(root)
    if args.command == 'doctor':
        return doctor(root, config, policy_hash, args.online)
    if args.command == 'workspace':
        if args.workspace_command == 'inspect':
            return dict(**workspace.inspect(root, config['integration']['base_ref'], args.scope), binding=context.binding(root))
        return workspace.create(root, args.path, args.branch, config['integration']['base_ref'], args.apply)
    if args.command == 'prepare':
        return context.prepare(root, config, policy_hash, args.task, args.contract, args.offline, args.rebind,
                               args.update_contract)
    if args.command == 'resume':
        return tasks.resume(root, config, policy_hash, policy.runtime_identity(), context.binding(root), args.task)
    if args.command == 'check':
        return tasks.check(root, config, args.task)
    if args.command == 'verify':
        return evidence.verify(root, config, policy_hash, args.check, args.execute, args.approved_policy, args.online,
                               args.task)
    return handoff.draft(root, config, policy_hash, args.task, args.done, args.remaining, args.next_steps, args.online)


def main():
    try:
        result = run(parser().parse_args())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get('kind') == 'VerificationEvidence' and result['status'] != 'passed':
            return 1
        if result.get('status') == 'attention_required':
            return 1
        return 0
    except (WorkflowError, ProviderError) as exc:
        print(json.dumps(dict(error=getattr(exc, 'code', 'workflow_error'), message=str(exc))))
        return 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # Do not echo arbitrary config, remote response or command output on malformed input.
        print(json.dumps(dict(error='invalid_input_or_state', message=type(exc).__name__)))
        return 2
    except KeyboardInterrupt:
        print(json.dumps(dict(error='cancelled', message='Operation cancelled')))
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
