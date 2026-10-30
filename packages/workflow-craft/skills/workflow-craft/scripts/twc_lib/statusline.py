"""Read one project mode for a host UI, without inspecting tasks or executing checks."""
import os
from pathlib import Path
import subprocess
import tomllib

from .models import WorkflowError
from .policy import development_mode, validate_config

LABELS = {'personal': 'Workflow: solo', 'team': 'Workflow: team',
          'unconfigured': 'Workflow: 未配置', 'invalid': 'Workflow: 配置错误',
          'unavailable': 'Workflow: 不可用'}


def read_mode(project):
    """Use the actual Git worktree root, including subdirectories and linked worktrees."""
    if not isinstance(project, str) or not project or '\0' in project:
        return 'unavailable'
    try:
        result = subprocess.run(['git', '-C', project, 'rev-parse', '--show-toplevel'],
                                capture_output=True, timeout=1,
                                env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
        if result.returncode != 0:
            return 'unconfigured'
        root = Path(os.fsdecode(result.stdout).strip())
        directory = root / '.team-workflow'
        path = directory / 'config.toml'
        if directory.is_symlink() or path.is_symlink():
            return 'invalid'
        if not path.exists():
            return 'unconfigured'
        with path.open('rb') as stream:
            raw = stream.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return 'unavailable'
        config = tomllib.loads(raw.decode('utf-8'))
        validate_config(config)
        return development_mode(config)
    except (UnicodeError, ValueError, WorkflowError):
        return 'invalid'
    except (OSError, subprocess.TimeoutExpired):
        return 'unavailable'


def render(project):
    return LABELS[read_mode(project)]
