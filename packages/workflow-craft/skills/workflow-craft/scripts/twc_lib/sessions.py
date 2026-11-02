"""Session-local bindings and a worktree-wide lock for tool-owned mutations."""
from contextlib import contextmanager
from functools import wraps
import errno
import os
from pathlib import Path
import re
import threading

from .models import WorkflowError, digest, local_target, read_json
from . import layout

_held = threading.local()


def selected(session=None):
    value = session if session is not None else os.environ.get('TWC_SESSION_ID')
    if value is not None and (not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value)):
        raise WorkflowError('Session must be a stable short identifier, not a path')
    return value


def require(session=None):
    value = selected(session)
    if value is None:
        raise WorkflowError('Task lifecycle requires --session or TWC_SESSION_ID; reuse it within this host session')
    return value


def path(root, session=None, *, writing=False):
    session = selected(session)
    category = 'sessions' if session else ''
    filename = digest(session.encode()) + '.json' if session else 'binding.json'
    if writing:
        return local_target(root, category, filename)
    target = layout.directory(root) / 'local' / category / filename
    if any(part.is_symlink() for part in (target, *target.parents) if root in part.parents):
        raise WorkflowError('Session binding path cannot contain a symlink')
    return target


def read(root, session=None):
    session = selected(session)
    target = path(root, session)
    if not target.exists():
        return None
    value = read_json(target)
    if not isinstance(value, dict) or (session and value.get('session') != session):
        raise WorkflowError('Invalid session binding')
    return None if value.get('cleared') is True else value


def write(root, value, session=None):
    from .tasks import write as atomic_write
    session = selected(session)
    target = path(root, session, writing=True)
    atomic_write(target, dict(value, session=session))
    os.chmod(target, 0o600)


def clear(root, session=None):
    write(root, dict(cleared=True), require(session))


@contextmanager
def file_lock(target):
    if os.name == 'nt':
        import msvcrt

        def lock(stream, release=False):
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK if release else msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        def lock(stream, release=False):
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN if release else fcntl.LOCK_EX | fcntl.LOCK_NB)
    if layout.unsafe(target) or (target.exists() and not target.is_file()):
        raise WorkflowError('Workflow mutex cannot be a symlink, reparse point or non-file')
    with target.open('a+b') as stream:
        os.chmod(target, 0o600)
        try:
            lock(stream)
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise
            raise WorkflowError('Workspace is busy with another workflow mutation/check; retry after it ends or use a separate worktree') from exc
        try:
            yield
        finally:
            lock(stream, release=True)


@contextmanager
def workspace_lock(root, *, relocating=False):
    """The worktree Git mutex survives relocation; also respect older runtime locks."""
    key = str(root.resolve())
    held = getattr(_held, 'roots', set())
    if key in held:
        yield
        return
    from .workspace import git
    target = Path(os.fsdecode(git(root, 'rev-parse', '--git-path', 'workflow-craft-mutation.lock')).strip())
    if not target.is_absolute():
        target = root / target
    with file_lock(target):
        local = (layout.directory(root) / 'local/mutation.lock' if relocating
                 else local_target(root, '', 'mutation.lock'))
        if layout.unsafe(local.parent):
            raise WorkflowError('Workflow local directory cannot be a symlink or reparse point')
        _held.roots = held | {key}
        try:
            if relocating:
                if os.path.lexists(local):
                    with file_lock(local):
                        pass  # Upgraded lock rejects old writers; drain a writer already in flight.
                yield
            else:
                with file_lock(local):
                    yield
        finally:
            _held.roots = held


def serialized(function):
    @wraps(function)
    def run(root, *args, **kwargs):
        with workspace_lock(root):
            return function(root, *args, **kwargs)
    return run
