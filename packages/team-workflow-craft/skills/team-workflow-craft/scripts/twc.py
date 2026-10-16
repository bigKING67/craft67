#!/usr/bin/env python3
"""Local team workflow tools. All commands emit JSON; no model or agent calls."""
import argparse
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
from twc_lib import actors, context, evidence, handoff, policy, workspace
from twc_lib.models import WorkflowError
from twc_lib.providers import ProviderError


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--project', default='.', help='Path inside the target Git worktree')
    cli.add_argument('--version', action='version', version=policy.runtime_identity()['version'])
    commands = cli.add_subparsers(dest='command', required=True)
    doctor = commands.add_parser('doctor', help='Inspect Git, config, lock and optional platform capability')
    doctor.add_argument('--online', action='store_true', help='Read the configured collaboration platform')
    init = commands.add_parser('init', help='Preview a minimal project configuration; no host rule edits')
    init.add_argument('--base-url', required=True)
    init.add_argument('--provider', choices=('gitea', 'cnb'), default='gitea')
    init.add_argument('--repository', required=True)
    init.add_argument('--base-ref', default='origin/main')
    init.add_argument('--workflow-owner', choices=('team-workflow-craft', 'trellis'), default='team-workflow-craft')
    mutation = init.add_mutually_exclusive_group()
    mutation.add_argument('--dry-run', action='store_true')
    mutation.add_argument('--apply', action='store_true')
    prepare = commands.add_parser('prepare', help='Prepare a rebuildable task snapshot')
    prepare.add_argument('--task', required=True)
    prepare.add_argument('--contract', help='Repository-relative JSON contract; no duplicate owner/status')
    prepare.add_argument('--offline', action='store_true')
    prepare.add_argument('--rebind', action='store_true', help='Explicitly switch this workspace to another task')
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
    transfer = commands.add_parser('handoff', help='Generate local handoff drafts; v0.1 cannot publish')
    transfer.add_argument('--draft', action='store_true')
    transfer.add_argument('--publish', action='store_true', help='Unsupported in v0.1; fails without sending a request')
    transfer.add_argument('--packet', required=True)
    transfer.add_argument('--evidence', action='append', default=[])
    transfer.add_argument('--done', action='append', default=[])
    transfer.add_argument('--remaining', action='append', default=[])
    transfer.add_argument('--next', dest='next_steps', action='append', default=[])
    transfer.add_argument('--online', action='store_true')
    return cli


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
    # Only inspect project-specific discovery paths, not unrelated user profiles/accounts.
    paths = [root / '.agents/skills/team-workflow-craft', root / '.claude/skills/team-workflow-craft']
    report['project_entries'] = [dict(path=str(p), exists=p.exists(), symlink=p.is_symlink(),
                                      is_current=p.resolve() == policy.SKILL_ROOT.resolve()) for p in paths]
    for path, entry in zip(paths, report['project_entries']):
        if path.exists() and not path.is_symlink():
            try:
                entry['matches_runtime'] = policy.runtime_identity(path) == lock['actual']
            except (WorkflowError, OSError):
                entry['matches_runtime'] = False
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
        return context.prepare(root, config, policy_hash, args.task, args.contract, args.offline, args.rebind)
    if args.command == 'verify':
        return evidence.verify(root, config, policy_hash, args.check, args.execute, args.approved_policy, args.online)
    return handoff.draft(root, config, policy_hash, args.packet, args.evidence,
                         args.done, args.remaining, args.next_steps, args.online)


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
