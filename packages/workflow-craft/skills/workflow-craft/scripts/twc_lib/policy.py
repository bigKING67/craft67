"""Project configuration, explicit command approval, and pinned runtime identity."""
import json
from pathlib import Path
import re
import tomllib
import uuid

from .models import WorkflowError, canonical, digest, read_json, relative_path
from .providers import from_config, PROVIDERS

SKILL_ROOT = Path(__file__).resolve().parents[2]


def runtime_identity(skill_root=None):
    skill_root = skill_root or SKILL_ROOT
    version_path = skill_root / 'VERSION'
    if not version_path.is_file():
        version_path = skill_root.parent.parent / 'VERSION'
    files = {}
    for path in sorted(skill_root.rglob('*')):
        if '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        if path.is_symlink():
            raise WorkflowError('Runtime contains a symlink')
        if path.is_file() and path.name not in ('VERSION', 'LICENSE', '.twc-install.json'):
            files[path.relative_to(skill_root).as_posix()] = digest(path.read_bytes())
    return dict(version=version_path.read_text(encoding='utf-8').strip(), protocol_version=3,
                runtime_tree_sha256=digest(canonical(files)))


def installation_integrity(skill_root=None):
    skill_root = skill_root or SKILL_ROOT
    marker = skill_root / '.twc-install.json'
    if not marker.exists():
        return 'not_installed_by_twc'
    if marker.is_symlink():
        return 'mismatch'
    try:
        data = read_json(marker)
        if not isinstance(data, dict) or data.get('schema') != 'workflow-craft.install.v1':
            return 'invalid_marker'
        rows = data['files']
        expected = {row['path']: (row['sha256'], row['size']) for row in rows}
        if len(rows) != len(expected):
            return 'invalid_marker'
        actual = {}
        for path in skill_root.rglob('*'):
            if path.is_symlink():
                return 'mismatch'
            if path.is_file() and path != marker:
                content = path.read_bytes()
                actual[path.relative_to(skill_root).as_posix()] = (digest(content), len(content))
        return 'matched' if actual == expected else 'mismatch'
    except (WorkflowError, OSError, TypeError, KeyError):
        return 'invalid_marker'


def strict_keys(value, keys, context):
    if not isinstance(value, dict) or set(value) - set(keys):
        raise WorkflowError(f'Unknown or invalid fields in {context}')


def load(root):
    path = relative_path(root, '.team-workflow/config.toml', must_exist=True)
    try:
        raw = path.read_bytes()
        config = tomllib.loads(raw.decode('utf-8'))
    except (OSError, ValueError) as exc:
        raise WorkflowError('Cannot parse project configuration') from exc
    validate_config(config)
    for check in config.get('checks', {}).values():
        if not relative_path(root, check.get('cwd', '.'), must_exist=True).is_dir():
            raise WorkflowError('Check cwd must be a directory inside the repository')
    return config, digest(raw)


def development_mode(config):
    return config.get('development_mode', 'team')  # Existing v1 projects already use team contracts.


def validate_config(config):
    strict_keys(config, ('schema_version', 'development_mode', 'project_id', 'workflow_owner',
                         'coordination', 'integration', 'permissions', 'checks'), 'config')
    if config.get('schema_version') not in (1, 2) or config.get('workflow_owner') not in ('workflow-craft', 'team-workflow-craft', 'trellis'):
        raise WorkflowError('Unsupported config schema or workflow owner')
    if config['schema_version'] == 2:
        if config.get('development_mode') not in ('personal', 'team'):
            raise WorkflowError('Choose development mode explicitly: personal or team')
        if not isinstance(config.get('project_id'), str) or not re.fullmatch(r'[a-f0-9]{32}', config['project_id']):
            raise WorkflowError('Project identity must be a stable 32-character hexadecimal id')
    elif 'development_mode' in config or 'project_id' in config:
        raise WorkflowError('Development mode and local project identity require config schema_version 2')
    source = config.get('coordination')
    if source is not None:
        validate_coordination(source)
    elif config['schema_version'] == 1:
        raise WorkflowError('Legacy team configuration requires coordination')
    integration = config.get('integration', {})
    strict_keys(integration, ('mode', 'require_fresh_base', 'base_ref'), 'integration')
    if integration.get('mode') != 'human-serialized' or integration.get('require_fresh_base') is not True:
        raise WorkflowError('This local checker supports only human-serialized with require_fresh_base=true; '
                            'this does not set the project merge strategy or certify merge queues')
    if not isinstance(integration.get('base_ref'), str) or not integration['base_ref'] or integration['base_ref'].startswith('-'):
        raise WorkflowError('integration.base_ref is required')
    permissions = config.get('permissions', {})
    strict_keys(permissions, ('auto_commit', 'auto_push', 'auto_publish_handoff', 'auto_merge'), 'permissions')
    if any(permissions.get(key) is not False for key in ('auto_commit', 'auto_push', 'auto_publish_handoff', 'auto_merge')):
        raise WorkflowError('Automatic external/Git write permissions must remain false')
    checks = config.get('checks', {})
    if not isinstance(checks, dict):
        raise WorkflowError('checks must be a TOML table')
    for name, check in checks.items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise WorkflowError('Invalid check name')
        strict_keys(check, ('argv', 'cwd', 'timeout_seconds'), 'check')
        argv = check.get('argv')
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x or '\0' in x for x in argv):
            raise WorkflowError('Each check requires a nonempty argv string array')
        cwd = check.get('cwd', '.')
        if not isinstance(cwd, str) or Path(cwd).is_absolute() or '..' in Path(cwd).parts or '\\' in cwd:
            raise WorkflowError('Check cwd must be a repository-relative directory')
        timeout = check.get('timeout_seconds', 300)
        if type(timeout) is not int or not 1 <= timeout <= 3600:
            raise WorkflowError('timeout_seconds must be an integer from 1 to 3600')
    return config


def validate_coordination(source):
    strict_keys(source, ('provider', 'instance_alias', 'base_url', 'repository', 'assignment', 'token_env', 'identity_token_env'), 'coordination')
    if source.get('provider') not in PROVIDERS or source.get('assignment') != 'human-confirmed':
        raise WorkflowError('Supported providers are Gitea/CNB with human-confirmed assignment')
    for name in ('base_url', 'repository', 'instance_alias'):
        if not isinstance(source.get(name), str) or not source[name].strip():
            raise WorkflowError(f'Missing coordination.{name}')
    token_env = source.get('token_env', f'TWC_{source["provider"].upper()}_TOKEN')
    if not isinstance(token_env, str) or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', token_env):
        raise WorkflowError('Invalid token_env name')
    if 'identity_token_env' in source:
        identity_env = source['identity_token_env']
        if (source['provider'] != 'cnb' or not isinstance(identity_env, str)
                or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', identity_env)):
            raise WorkflowError('identity_token_env requires CNB and a valid environment variable name')
    from_config(dict(coordination=source))  # Validate without sending any request.


def lock_status(root):
    actual = runtime_identity()
    path = root / '.team-workflow/toolchain.lock.json'
    if not path.exists():
        return dict(status='missing', actual=actual)
    lock = read_json(path)
    if not isinstance(lock, dict):
        raise WorkflowError('Invalid toolchain lock')
    expected = {key: lock.get(key) for key in actual}
    return dict(status='matched' if expected == actual else 'mismatch', expected=expected, actual=actual,
                authenticity='local_pin_only')


def require_lock(root):
    status = lock_status(root)
    if status['status'] != 'matched':
        raise WorkflowError('Toolchain lock is missing or mismatched; approve a fixed runtime before execution')


def init(root, base_url, repository, base_ref, owner='workflow-craft', apply=False, provider='gitea', mode=None):
    if mode not in ('personal', 'team'):
        raise WorkflowError('Choose development mode explicitly: personal or team')
    if bool(base_url) != bool(repository):
        raise WorkflowError('Platform connection requires both --base-url and --repository')
    if base_url:
        from_config(dict(coordination=dict(provider=provider, base_url=base_url, repository=repository)))
    if owner not in ('workflow-craft', 'trellis'):
        raise WorkflowError('Invalid workflow owner')
    q = json.dumps
    identity_line = 'identity_token_env = "TWC_CNB_IDENTITY_TOKEN"\n' if provider == 'cnb' else ''
    coordination = f'''[coordination]
provider = {q(provider)}
instance_alias = "company"
base_url = {q(base_url.rstrip('/'))}
repository = {q(repository)}
assignment = "human-confirmed"
token_env = {q(f'TWC_{provider.upper()}_TOKEN')}
{identity_line}
''' if base_url else ''
    content = f'''schema_version = 2
development_mode = {q(mode)}
project_id = {q(uuid.uuid4().hex)}
workflow_owner = {q(owner)}

{coordination}
[integration]
# Local handoff-checking profile, not the project's merge/queue strategy.
mode = "human-serialized"
require_fresh_base = true
base_ref = {q(base_ref)}

[permissions]
# This tool never performs these writes; host/user authorization is separate.
auto_commit = false
auto_push = false
auto_publish_handoff = false
auto_merge = false

# Add project-approved [checks.<name>] with argv, cwd and timeout_seconds.
# No commands are executed or guessed during init.
'''
    lock = dict(schema_version=1, skill='workflow-craft', **runtime_identity())
    files = {'config.toml': content, 'toolchain.lock.json': json.dumps(lock, indent=2) + '\n', '.gitignore': 'local/\n'}
    directory = root / '.team-workflow'
    if directory.exists() or directory.is_symlink():
        raise WorkflowError('.team-workflow already exists; inspect and edit existing configuration explicitly')
    plan = dict(action='init', files={'.team-workflow/' + name: text for name, text in files.items()}, applied=False,
                host_rules='AGENTS.md/CLAUDE.md are not modified')
    if apply:
        directory.mkdir(mode=0o755)
        for name, text in files.items():
            with (directory / name).open('x', encoding='utf-8') as stream:
                stream.write(text)
        plan['applied'] = True
    return plan
