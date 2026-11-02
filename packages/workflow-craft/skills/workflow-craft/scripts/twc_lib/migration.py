"""Explicit, content-approved directory relocation. No record or Git history rewriting."""
import os
import stat
import ctypes
import sys

from . import layout, policy, sessions
from .models import WorkflowError, canonical, digest
from .workspace import git


def rename_directory(source, target):
    """Atomic no-replace rename, including an empty destination created after preflight."""
    if os.name == 'nt':
        os.rename(source, target)  # Windows refuses an existing destination.
        return
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == 'darwin':
        rename = library.renamex_np
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        result = rename(os.fsencode(source), os.fsencode(target), 0x4)  # RENAME_EXCL
    elif sys.platform.startswith('linux') and hasattr(library, 'renameat2'):
        rename = library.renameat2
        rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        result = rename(-100, os.fsencode(source), -100, os.fsencode(target), 1)  # NOREPLACE
    else:
        raise WorkflowError('Atomic no-replace directory migration is unavailable on this platform')
    if result:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))


def inventory(directory):
    rows = []
    for path in sorted(directory.rglob('*')):
        if layout.unsafe(path):
            raise WorkflowError('Migration cannot relocate symlinks or reparse points')
        info = path.stat()
        name = path.relative_to(directory).as_posix()
        if stat.S_ISDIR(info.st_mode):
            rows.append([name, 'directory', stat.S_IMODE(info.st_mode)])
        elif stat.S_ISREG(info.st_mode):
            # The compatibility mutex is runtime state, not task content.
            if name != 'local/mutation.lock':
                rows.append([name, digest(path.read_bytes()), stat.S_IMODE(info.st_mode)])
        else:
            raise WorkflowError('Migration requires regular files and directories')
    return rows


def migrate(root, apply=False, approved_inventory=None):
    source = layout.directory(root)
    if not source.exists():
        raise WorkflowError('No existing workflow to migrate; initialize a new project instead')
    policy.load(root)  # Refuse foreign/invalid configuration before any writes.
    if source.name == layout.CURRENT:
        return dict(action='migrate_directory', status='ok', applied=False, changed=False,
                    directory=layout.CURRENT)
    policy.require_lock(root)
    if git(root, 'ls-files', '--', layout.relative(root, 'local')).strip():
        raise WorkflowError('Local workflow state is tracked; fix tracking before migration')
    if git(root, 'check-ignore', '--no-index', '.workflow/config.toml', allowed=(0, 1)).strip():
        raise WorkflowError('The destination workflow configuration is Git-ignored')
    if apply:
        # The stable Git mutex outlives relocation; the old local mutex is closed
        # before rename because native Windows cannot move its open directory.
        with sessions.workspace_lock(root, relocating=True):
            policy.load(root)
            policy.require_lock(root)
            rows = inventory(source)
            sha = digest(canonical(rows))
            if approved_inventory != sha:
                raise WorkflowError('Migration requires the current --approved-inventory from its preview')
            target = root / layout.CURRENT
            if os.path.lexists(target) or layout.directory(root) != source:
                raise WorkflowError('Workflow directory changed after migration preview')
            rename_directory(source, target)
        report = dict(applied=True)
    else:
        rows = inventory(source)
        sha = digest(canonical(rows))
        report = dict(applied=False)
    return dict(report, action='migrate_directory', status='ok', changed=True,
                source=layout.LEGACY, target=layout.CURRENT, inventory_sha256=sha,
                entries=len(rows), preserved='all file bytes, modes, local state, actors and historical evidence',
                effects=['code paths changed; existing evidence must be assessed normally',
                         'external scripts and command argv referencing the old directory need explicit updates'],
                approval='--apply --approved-inventory <inventory_sha256>')
