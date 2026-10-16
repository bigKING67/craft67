"""Small exchange contracts and safe local artifact boundaries."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import uuid


class WorkflowError(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode()


def envelope(kind, **fields):
    return dict(schema_version=1, kind=kind, run_id=uuid.uuid4().hex, created_at=now(), **fields)


def read_json(path):
    try:
        path = Path(path)
        if path.stat().st_size > 4 * 1024 * 1024:
            raise WorkflowError('JSON artifact exceeds 4 MiB')
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise WorkflowError('Cannot read JSON artifact') from exc


def relative_path(root, value, *, must_exist=False):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or '\\' in str(value):
        raise WorkflowError('Expected a repository-relative path without traversal')
    target = root / path
    if not target.resolve().is_relative_to(root.resolve()):
        raise WorkflowError('Path escapes repository')
    if must_exist and not target.exists():
        raise WorkflowError('Referenced path does not exist')
    return target


def local_directory(root):
    path = root / '.team-workflow' / 'local'
    for candidate in (root / '.team-workflow', path):
        if candidate.is_symlink():
            raise WorkflowError('Workflow state directory cannot be a symlink')
    # A tracked local directory would leak task snapshots or execution output.
    from .workspace import git
    if git(root, 'ls-files', '--', '.team-workflow/local').strip():
        raise WorkflowError('Local workflow state is tracked; fix ignore/tracking before writing')
    if git(root, 'check-ignore', '--no-index', '.team-workflow/local/probe', allowed=(0, 1)).strip() == b'':
        raise WorkflowError('Ignore .team-workflow/local/ before writing workflow artifacts')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def save_local(root, category, value, suffix='json'):
    run_id = value['run_id']
    if not re.fullmatch(r'[a-f0-9]{32}', run_id):
        raise WorkflowError('Invalid run identifier')
    path = local_target(root, category, f'{run_id}.{suffix}')
    with path.open('x', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return str(path.relative_to(root))


def local_target(root, category, filename):
    """Preflight the actual destination; an ignored probe alone proves nothing."""
    from .workspace import git
    if category not in ('', 'packets', 'evidence', 'handoffs') or not re.fullmatch(r'[A-Za-z0-9_.-]+', filename):
        raise WorkflowError('Invalid local artifact destination')
    base = local_directory(root) / category
    if base.is_symlink():
        raise WorkflowError('Artifact directory cannot be a symlink')
    path = base / filename
    if path.is_symlink():
        raise WorkflowError('Artifact destination cannot be a symlink')
    relative = path.relative_to(root).as_posix()
    if (git(root, 'ls-files', '--', relative).strip()
            or not git(root, 'check-ignore', '--no-index', relative, allowed=(0, 1)).strip()):
        raise WorkflowError('Actual workflow artifact must be untracked and Git ignored')
    base.mkdir(exist_ok=True, mode=0o700)
    return path


def task_ref(config, value):
    match = re.fullmatch(r'(issue|pr):([1-9][0-9]*)', value)
    if not match:
        raise WorkflowError('Task must be issue:<positive number> or pr:<positive number>')
    source = config['coordination']
    return dict(provider=source['provider'], instance=source['base_url'].rstrip('/'),
                repository=source['repository'], type=match[1], number=int(match[2]))


def validate_contract(value, root):
    if not isinstance(value, dict):
        raise WorkflowError('Contract must be a JSON object')
    allowed = {'goal', 'non_goals', 'scope', 'dependencies', 'acceptance', 'integrator',
               'contracts', 'complexity', 'risk'}
    if set(value) - allowed:
        raise WorkflowError('Unknown contract fields; owner/status belong to the collaboration platform')
    for name in ('goal', 'integrator'):
        if not isinstance(value.get(name), str) or not value[name].strip():
            raise WorkflowError(f'Contract requires {name}')
    for name in ('non_goals', 'scope', 'dependencies', 'acceptance', 'contracts'):
        items = value.get(name)
        if not isinstance(items, list) or any(not isinstance(x, str) or not x.strip() for x in items):
            raise WorkflowError(f'Contract requires a string array: {name}')
    if not value['scope'] or not value['acceptance']:
        raise WorkflowError('Contract scope and acceptance cannot be empty')
    for path in value['scope']:
        relative_path(root, path)
    if value.get('complexity') not in ('L0', 'L1', 'L2'):
        raise WorkflowError('complexity must be L0/L1/L2')
    if value.get('risk') not in ('normal', 'elevated', 'critical'):
        raise WorkflowError('risk must be normal/elevated/critical')
    if any(not x.startswith(('https://', 'http://')) for x in value['dependencies']):
        raise WorkflowError('Dependencies must be authoritative task/spec URLs')
    for path in value['contracts']:
        relative_path(root, path, must_exist=True)
    return value
