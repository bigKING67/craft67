"""Project-scoped onboarding and explicit mode transitions; never rewrite task history."""
import json
import os
import uuid

from . import context, policy, tasks
from .models import WorkflowError, digest, relative_path, task_label

MODE_PROMPT = '这个项目准备怎样开发？请选择个人开发（推荐，可使用多个 Agent）或团队协作（多人分工、交接与评审）。'


def describe(config=None):
    if config is None:
        return dict(status='selection_required', current=None, recommended='personal',
                    choices=['personal', 'team'], message=MODE_PROMPT)
    return dict(status='configured', current=policy.development_mode(config),
                source='legacy_team_config' if config['schema_version'] == 1 else 'project_config')


def config_text(config):
    """Serialize the validated TOML subset without dropping checks or other settings."""
    lines = []

    def table(value, path=()):
        if path:
            lines.extend(['', '[' + '.'.join(json.dumps(key) for key in path) + ']'])
        for key, item in value.items():
            if not isinstance(item, dict):
                lines.append(f'{json.dumps(key)} = {json.dumps(item, ensure_ascii=False)}')
        for key, item in value.items():
            if isinstance(item, dict):
                table(item, (*path, key))

    table(config)
    return '\n'.join(lines) + '\n'


def change(root, selected=None, *, apply=False, approved_policy=None,
           provider=None, base_url=None, repository=None):
    config, sha = policy.load(root)
    report = dict(action='mode', development_mode=describe(config), policy_sha256=sha, applied=False)
    if selected is None:
        if apply or any((provider, base_url, repository)):
            raise WorkflowError('Choose --set personal or --set team before changing project configuration')
        return report
    if selected not in ('personal', 'team'):
        raise WorkflowError('Choose development mode explicitly: personal or team')
    updated = dict(config, schema_version=2, development_mode=selected,
                   project_id=config.get('project_id') or uuid.uuid4().hex)
    if any((provider, base_url, repository)):
        if not all((provider, base_url, repository)):
            raise WorkflowError('Adding a platform requires --provider, --base-url and --repository together')
        old = config.get('coordination')
        source = dict(provider=provider, base_url=base_url.rstrip('/'), repository=repository,
                      instance_alias='company', assignment='human-confirmed', token_env=f'TWC_{provider.upper()}_TOKEN')
        if provider == 'cnb':
            source['identity_token_env'] = 'TWC_CNB_IDENTITY_TOKEN'
        policy.validate_coordination(source)
        if old and any(old[key] != source[key] for key in ('provider', 'base_url', 'repository')):
            raise WorkflowError('Mode changes cannot replace an existing platform or reassign historical tasks')
        updated['coordination'] = old or source
    policy.validate_config(updated)
    # Invalid/stale bindings must be reviewed, never silently erased during a mode change.
    ref = tasks.current(root, config, bound=context.binding(root))[0]
    record = tasks.load(root, ref) if ref else None
    previous = tasks.latest_handoff(root, ref) if ref else None
    current_task = None if ref is None else dict(
        task=task_label(ref), integrator=(record.get('contract') or {}).get('integrator') if record else None,
        last_handoff=None if previous is None else {
            key: previous.get(key) for key in ('readiness', 'remaining', 'next_steps', 'blockers', 'unknowns')})
    unchanged = updated == config
    path = relative_path(root, '.team-workflow/config.toml', must_exist=True)
    if path.is_symlink() or (root / '.team-workflow').is_symlink():
        raise WorkflowError('Project configuration cannot be a symlink')
    content = path.read_text() if unchanged else config_text(updated)
    report.update(target_mode=selected, current_task=current_task, changed=not unchanged,
                  files={'.team-workflow/config.toml': content},
                  effects=[] if unchanged else ['previous_verification_becomes_stale'],
                  preserved=['task_records', 'actors', 'evidence', 'bindings', 'checks', 'platform_connection',
                             'existing_task_integrator_and_platform_requirements'],
                  approval='--apply --approved-policy <policy_sha256>; requires the user to choose this project mode')
    if apply:
        if approved_policy != sha:
            raise WorkflowError('Mode change requires approval of the current policy_sha256')
        if digest(path.read_bytes()) != sha:
            raise WorkflowError('Project configuration changed after mode preview; inspect it again')
        if not unchanged:
            temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
            try:
                with temporary.open('x', encoding='utf-8') as stream:
                    stream.write(content)
                os.chmod(temporary, path.stat().st_mode & 0o777)
                os.replace(temporary, path)
            finally:
                if temporary.exists():
                    temporary.unlink()
        report['applied'] = True
    return report
