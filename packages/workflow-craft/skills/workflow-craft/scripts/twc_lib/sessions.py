"""Session-local bindings and a worktree-wide lock for tool-owned mutations."""
from contextlib import contextmanager
from functools import wraps
import errno
import os
import re
import threading

from .models import WorkflowError, digest, local_target, read_json

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
    target = root / '.team-workflow/local' / category / filename
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
def workspace_lock(root):
    """Serialize tool writes/check execution; raw Git/editor changes remain detectable drift."""
    if os.name == 'nt':
        import msvcrt

        def lock(stream, release=False):
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK if release else msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        def lock(stream, release=False):
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN if release else fcntl.LOCK_EX | fcntl.LOCK_NB)
    key = str(root.resolve())
    held = getattr(_held, 'roots', set())
    if key in held:
        yield
        return
    target = local_target(root, '', 'mutation.lock')
    with target.open('a+b') as stream:
        os.chmod(target, 0o600)
        try:
            lock(stream)
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise
            raise WorkflowError('Workspace is busy with another workflow mutation/check; retry after it ends or use a separate worktree') from exc
        _held.roots = held | {key}
        try:
            yield
        finally:
            _held.roots = held
            lock(stream, release=True)


def serialized(function):
    @wraps(function)
    def run(root, *args, **kwargs):
        with workspace_lock(root):
            return function(root, *args, **kwargs)
    return run
