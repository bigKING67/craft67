"""Read the entire Git root; create new worktrees only on explicit request."""
import hashlib
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit, urlunsplit

from .models import WorkflowError, digest


def git(root, *args, allowed=(0,)):
    try:
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                                timeout=30, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkflowError('Git unavailable or timed out') from exc
    if result.returncode not in allowed:
        # Raw stderr may contain credential-bearing remote URLs.
        raise WorkflowError(f'Git {args[0]} failed (exit {result.returncode})')
    return result.stdout


def root_for(path):
    return Path(os.fsdecode(git(path, 'rev-parse', '--show-toplevel')).strip()).resolve()


def resolve(root, ref):
    if not ref or ref.startswith('-') or any(c in ref for c in '\n\r\0'):
        raise WorkflowError('Invalid Git revision')
    value = git(root, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}')
    return value.decode().strip()


def safe_remote(value):
    if '://' in value:
        url = urlsplit(value)
        host = url.hostname or ''
        try:
            port = f':{url.port}' if url.port else ''
        except ValueError:
            return '<invalid remote>'
        return urlunsplit((url.scheme, host + port, url.path, '', ''))
    # SCP-style ssh remote: username is not needed in a shared artifact.
    return value.split('@', 1)[-1].split('?', 1)[0].split('#', 1)[0]


def paths_from_status(raw):
    fields = raw.split(b'\0')
    changes = []
    i = 0
    while i < len(fields) and fields[i]:
        item = fields[i]
        code, path = item[:2].decode('ascii'), os.fsdecode(item[3:])
        entry = dict(status=code, path=path)
        if 'R' in code or 'C' in code:
            i += 1
            entry['from'] = os.fsdecode(fields[i])
        changes.append(entry)
        i += 1
    return changes


def inspect(root, base_ref, scope=()):
    head, base = resolve(root, 'HEAD'), resolve(root, base_ref)
    branch = git(root, 'symbolic-ref', '--short', '-q', 'HEAD', allowed=(0, 1)).decode().strip() or None
    raw = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignore-submodules=none')
    changes = paths_from_status(raw)
    state = hashlib.sha256(raw)
    # Hash content rather than only status: two edits at one HEAD are not the same sample.
    state.update(git(root, 'diff', '--binary', '--no-ext-diff', '--no-textconv', '--ignore-submodules=none', 'HEAD', '--'))
    complete = True
    for item in changes:
        path = root / item['path']
        state.update(os.fsencode(item['path']))
        if path.is_symlink():
            state.update(os.fsencode(os.readlink(path)))
        elif path.is_file():
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    state.update(block)
        elif path.exists():
            # Dirty submodule/nested repository contents cannot be bound by the parent's diff.
            complete = False
    staged = digest(git(root, 'diff', '--cached', '--binary', '--no-ext-diff', '--no-textconv', '--ignore-submodules=none', '--'))
    state.update(staged.encode())
    remotes = {}
    for name in git(root, 'remote').decode().splitlines():
        url = git(root, 'remote', 'get-url', name).decode().strip()
        remotes[name] = safe_remote(url)
    merge_base = git(root, 'merge-base', base, head, allowed=(0, 1)).decode().strip() or None
    outside = [item['path'] for item in changes if scope and not any(
        item['path'] == path.rstrip('/') or item['path'].startswith(path.rstrip('/') + '/') for path in scope)]
    shared = [item['path'] for item in changes if item['path'] in ('catalog.json', 'package-lock.json', 'uv.lock', '.cnb.yml')
              or item['path'].startswith(('.github/', '.gitea/', 'migrations/'))]
    return dict(root=str(root), head=head, base=base, base_ref=base_ref, branch=branch,
                base_is_ancestor=merge_base == base, remote_freshness='unverified', remotes=remotes,
                dirty=bool(changes), changes=changes, outside_scope=outside, shared_paths=shared,
                fingerprint=state.hexdigest(), fingerprint_complete=complete)


def code_identity(snapshot):
    return {key: snapshot[key] for key in ('head', 'base', 'fingerprint', 'fingerprint_complete')}


def repository_identity(config, snapshot):
    """Match the configured platform to a Git remote without probing SSH aliases/network."""
    source = config['coordination']
    expected = urlsplit(source['base_url'])
    repo = source['repository'].strip('/').lower()
    paths = {repo, expected.path.strip('/').lower() + '/' + repo}
    known_mismatch = False
    for remote in snapshot['remotes'].values():
        if '://' in remote:
            parts = urlsplit(remote)
            host, path = parts.hostname, parts.path.strip('/')
        elif ':' in remote and not remote.startswith('/'):
            host, path = remote.split(':', 1)
        else:
            continue
        if host and host.lower() == expected.hostname.lower():
            if path.removesuffix('.git').lower() in paths:
                return 'matched'
            known_mismatch = True
    return 'mismatch' if known_mismatch else 'unverified'


def create(root, destination, branch, base_ref, apply=False):
    destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise WorkflowError('Worktree destination already exists')
    if destination.resolve().is_relative_to(root.resolve()):
        raise WorkflowError('Create a sibling worktree, not one nested inside the current repository')
    if any(p.is_symlink() for p in (destination, *destination.parents)):
        raise WorkflowError('Worktree destination cannot traverse symlinks')
    if not destination.parent.is_dir():
        raise WorkflowError('Worktree parent directory must already exist')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', branch):
        raise WorkflowError('Invalid branch name')
    git(root, 'check-ref-format', '--branch', branch)
    base = resolve(root, base_ref)
    plan = dict(action='create_worktree', destination=str(destination), branch=branch, base=base,
                applied=False, service_isolation='not_provided')
    if apply:
        git(root, 'worktree', 'add', '-b', branch, str(destination), base)
        plan['applied'] = True
    return plan
