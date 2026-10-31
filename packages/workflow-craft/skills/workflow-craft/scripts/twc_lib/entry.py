"""Global discovery and explicit project pinning; never execute another runtime."""
from contextlib import contextmanager
import ctypes
import json
import os
from pathlib import Path
import shutil
import stat
import uuid

from . import policy, workspace
from .models import WorkflowError, read_json

HOST_PATHS = {'codex': '.agents/skills/workflow-craft',
              'pi': '.agents/skills/workflow-craft',
              'claude': '.claude/skills/workflow-craft'}
MARKER = '.twc-install.json'


def is_global():
    marker = policy.SKILL_ROOT / MARKER
    return marker.is_file() and read_json(marker).get('installation_scope') == 'global'


def safe_path(root, path):
    current = root
    for part in (".", *path.relative_to(root).parts):
        current = current / part
        reparse = current.exists() and getattr(current.lstat(), 'st_file_attributes', 0) & 0x400
        if current.is_symlink() or reparse or (current.exists() and not current.is_dir()):
            raise WorkflowError('Workflow entry contains a symlink or non-directory: ' + str(current))


def select(root, host='codex', apply=False):
    """Return a command location, without importing or running project code."""
    candidates = []
    for relative in dict.fromkeys(HOST_PATHS.values()):
        path = root / relative
        safe_path(root, path)
        legacy = path.with_name('team-workflow-craft')
        if legacy.exists() or legacy.is_symlink():
            raise WorkflowError('Legacy workflow entry requires explicit migration; no runtime selected')
        if path.exists():
            if policy.installation_integrity(path) != 'matched':
                raise WorkflowError('Project installation is unknown or drifted; restore its approved artifact')
            if not (path / 'scripts/twc.py').is_file():
                raise WorkflowError('Project installation has no CLI')
            identity = policy.runtime_identity(path)
            # The code-tree digest binds the candidate implementation. Do not
            # attribute this global process's protocol constant to older code.
            identity.pop("protocol_version")
            candidates.append((path, identity))
    state = root / '.team-workflow'
    safe_path(root, state)
    lock_path = state / 'toolchain.lock.json'
    if lock_path.is_symlink() or (state / 'config.toml').is_symlink():
        raise WorkflowError('Project policy or lock is a symlink')
    if candidates:
        preferred = root / HOST_PATHS[host]
        path, identity = next((row for row in candidates if row[0] == preferred), candidates[0])
        if any(other != identity for _, other in candidates):
            raise WorkflowError('Project host installations disagree; review the fixed project version')
        if lock_path.exists():
            lock = read_json(lock_path)
            if not isinstance(lock, dict) or any(lock.get(k) != v for k, v in identity.items()):
                raise WorkflowError('Project runtime does not match its toolchain lock; no global fallback')
        return dict(status='ok', action='use_project_runtime', applied=False,
                    skill=str(path / 'SKILL.md'), cli=str(path / 'scripts/twc.py'), runtime=identity,
                    host_loading='unverified')
    if state.exists():
        raise WorkflowError('Existing workflow has no fixed project runtime; restore the version in its lock')
    if policy.installation_integrity() != 'matched':
        raise WorkflowError('Pinning requires an unchanged installation from a verified fixed artifact')
    workspace.resolve(root, 'HEAD')
    target = root / HOST_PATHS[host]
    if not apply:
        return dict(status='attention_required', action='pin_project_runtime', applied=False,
                    target=str(target), runtime=policy.runtime_identity(),
                    next_steps=['choose_development_mode', 'pin_project_runtime_then_initialize'],
                    host_loading='unverified')
    # Only a new directory is written. User rules, state, global settings and
    # existing host entries are never upgraded or rewritten here.
    # Materialize and validate the immutable payload before touching the project.
    files = {p.relative_to(policy.SKILL_ROOT).as_posix(): p.read_bytes()
             for p in policy.SKILL_ROOT.rglob('*') if p.is_file()}
    marker = json.loads(files[MARKER])
    marker.pop('installation_scope', None)
    expected = {row['path']: (row['sha256'], row['size']) for row in marker['files']}
    from .models import digest
    if {name: (digest(data), len(data)) for name, data in files.items() if name != MARKER} != expected:
        raise WorkflowError('Source installation changed while pinning')
    files[MARKER] = (json.dumps(marker, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
    with pinning_parent(root, target.parent) as parent:
        stage = '.workflow-craft-entry-' + uuid.uuid4().hex
        if isinstance(parent, int):
            os.mkdir(stage, dir_fd=parent)
            descriptor = os.open(stage, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            published = False
            owned = os.fstat(descriptor)
            try:
                write_at(descriptor, files)
                check_destination(root, target, state, os.fstat(parent))
                os.rename(stage, target.name, src_dir_fd=parent, dst_dir_fd=parent)
                published = True
                return dict(select(root, host), applied=True)
            except BaseException:
                if published:
                    found = os.stat(target.name, dir_fd=parent, follow_symlinks=False)
                    if (found.st_dev, found.st_ino) == (owned.st_dev, owned.st_ino):
                        remove_at(parent, target.name)
                raise
            finally:
                os.close(descriptor)
                remove_at(parent, stage)
        else:
            staging = parent / stage
            staging.mkdir()
            published = False
            owned = staging.stat()
            try:
                for name, data in files.items():
                    path = staging / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                check_destination(root, target, state, parent.stat())
                staging.rename(target)
                published = True
                return dict(select(root, host), applied=True)
            except BaseException:
                if published and target.exists():
                    found = target.lstat()
                    if (found.st_dev, found.st_ino) == (owned.st_dev, owned.st_ino):
                        shutil.rmtree(target)
                raise
            finally:
                if staging.exists():
                    shutil.rmtree(staging)



def check_destination(root, target, state, held):
    safe_path(root, target)
    actual = target.parent.lstat()
    if not stat.S_ISDIR(actual.st_mode) or (actual.st_dev, actual.st_ino) != (held.st_dev, held.st_ino):
        raise WorkflowError('Installation parent changed while pinning')
    if target.exists() or state.exists() or state.is_symlink():
        raise WorkflowError('Project changed while pinning; no existing files replaced')


def write_at(parent, files):
    for name, data in files.items():
        descriptors = []
        directory = parent
        try:
            for part in Path(name).parts[:-1]:
                try:
                    os.mkdir(part, dir_fd=directory)
                except FileExistsError:
                    pass
                directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                descriptors.append(directory)
            fd = os.open(Path(name).name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644, dir_fd=directory)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
        finally:
            for fd in reversed(descriptors):
                os.close(fd)


def remove_at(parent, name):
    try:
        info = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return
    if stat.S_ISDIR(info.st_mode):
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            for child in os.listdir(fd):
                remove_at(fd, child)
        finally:
            os.close(fd)
        os.rmdir(name, dir_fd=parent)
    else:
        os.unlink(name, dir_fd=parent)


@contextmanager
def pinning_parent(root, parent):
    """Bind the new install to inspected directories during concurrent renames."""
    paths = [root]
    for part in parent.relative_to(root).parts:
        paths.append(paths[-1] / part)
    if os.name == 'nt':
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                           wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        close = kernel.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        close.restype = wintypes.BOOL
        handles = []
        try:
            for path in paths:
                if path != root:
                    path.mkdir(exist_ok=True)
                # No FILE_SHARE_DELETE: ancestors cannot be renamed/replaced
                # while writes through their inspected paths are in progress.
                handle = create(str(path), 0x80, 0x3, None, 3, 0x02200000, None)
                if handle == ctypes.c_void_p(-1).value:
                    raise WorkflowError('Cannot hold installation directory safely')
                handles.append(handle)
                safe_path(root, path)
            yield parent
        finally:
            for handle in reversed(handles):
                close(handle)
    else:
        descriptors = []
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            descriptor = os.open(root, flags)
            descriptors.append(descriptor)
            for part in parent.relative_to(root).parts:
                try:
                    os.mkdir(part, dir_fd=descriptor)
                except FileExistsError:
                    pass
                descriptor = os.open(part, flags, dir_fd=descriptor)
                descriptors.append(descriptor)
            safe_path(root, parent)
            yield descriptor
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)
