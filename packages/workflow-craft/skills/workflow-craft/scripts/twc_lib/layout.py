"""One project data directory; legacy paths remain readable without a symlink."""
import os
import stat

from .models import WorkflowError

CURRENT = '.workflow'
LEGACY = '.team-workflow'
NAMES = (CURRENT, LEGACY)
TASK_PATHS = tuple(name + '/tasks' for name in NAMES)


def unsafe(path):
    if not os.path.lexists(path):
        return False
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def directory(root):
    """Select existing legacy state, otherwise the canonical default. Never choose between two."""
    found = [root / name for name in NAMES if os.path.lexists(root / name)]
    if len(found) > 1:
        raise WorkflowError('Both .workflow and .team-workflow exist; resolve the conflict explicitly')
    path = found[0] if found else root / CURRENT
    if unsafe(path) or (path.exists() and not path.is_dir()):
        raise WorkflowError('Workflow state directory cannot be a symlink, reparse point or non-directory')
    return path


def relative(root, suffix=''):
    return (directory(root) / suffix).relative_to(root).as_posix()


def historical_path(root, path):
    """Resolve an old logical reference after relocation, leaving its recorded bytes/hash intact."""
    if path.parts and path.parts[0] == LEGACY:
        selected = directory(root)
        if selected.name == CURRENT and selected.exists():
            return selected.relative_to(root).joinpath(*path.parts[1:])
    return path
