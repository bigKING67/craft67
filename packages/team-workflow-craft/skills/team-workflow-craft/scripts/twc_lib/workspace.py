"""Read the entire Git root; create new worktrees only on explicit request."""
import hashlib
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit, urlunsplit

from .models import WorkflowError, canonical, digest


def git(root, *args, allowed=(0,), stdin=None):
    try:
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, input=stdin,
                                timeout=30, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkflowError('Git unavailable or timed out') from exc
    if result.returncode not in allowed:
        # Raw stderr may contain credential-bearing remote URLs.
        raise WorkflowError(f'Git {args[0]} failed (exit {result.returncode})')
    return result.stdout


def succeeds(root, *args):
    try:
        git(root, *args)
        return True
    except WorkflowError:
        return False


def root_for(path):
    return Path(os.fsdecode(git(path, 'rev-parse', '--show-toplevel')).strip()).resolve()


def resolve(root, ref):
    if not ref or ref.startswith('-') or any(c in ref for c in '\n\r\0'):
        raise WorkflowError('Invalid Git revision')
    value = git(root, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}')
    return value.decode().strip()


def resolve_base(root, ref):
    """Resolve integration.base_ref; a bare branch absent locally may use its only remote-tracking copy.

    A member who cloned a task branch has origin/main but no local main.
    """
    if succeeds(root, 'rev-parse', '--verify', '-q', '--end-of-options', ref + '^{commit}'):
        return resolve(root, ref), ref
    if ref and not ref.startswith(('-', 'refs/')) and '/' not in ref:
        remotes = git(root, 'remote').decode().split()
        found = [f'{name}/{ref}' for name in remotes
                 if succeeds(root, 'rev-parse', '--verify', '-q', f'refs/remotes/{name}/{ref}^{{commit}}')]
        if len(found) == 1:
            return resolve(root, found[0]), found[0]
    raise WorkflowError(f'integration.base_ref "{ref}" does not resolve in this clone; fetch it, or set base_ref '
                        f'to a remote-tracking ref such as origin/{ref}')


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


TASKS = '.team-workflow/tasks'
CODE_PATHS = ('--', '.', ':(exclude)' + TASKS)


def _in_scope(path, scope):
    return any(path == item.rstrip('/') or path.startswith(item.rstrip('/') + '/') for item in scope)


def _blob_id(algorithm, data):
    return hashlib.new(algorithm, b'blob %d\0' % len(data) + data).hexdigest()


def _tree(root, changes):
    """Content identity of the working tree, excluding TWC task metadata.

    Equal content gives an equal hash whether it is committed, staged or only in the
    working tree, so committing task evidence does not invalidate the evidence itself.
    """
    algorithm = git(root, 'rev-parse', '--show-object-format', allowed=(0, 128)).decode().strip() or 'sha1'
    if algorithm not in ('sha1', 'sha256'):
        return None, False
    file_mode = git(root, 'config', '--bool', 'core.fileMode', allowed=(0, 1)).decode().strip() != 'false'
    entries, complete, regular = {}, True, []
    for row in git(root, 'ls-files', '-s', '-z', *CODE_PATHS).split(b'\0'):
        if not row:
            continue
        meta, path = row.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        if stage != '0':
            complete = False  # Unresolved merge entries have no single content.
        entries[os.fsdecode(path)] = (mode, oid)
    for item in changes:
        for name in filter(None, (item.get('from'), item['path'])):
            path = root / name
            if path.is_symlink():
                entries[name] = ('120000', _blob_id(algorithm, os.fsencode(os.readlink(path))))
            elif path.is_file():
                indexed = entries.get(name, ('100644',))[0]
                mode = ('100755' if os.stat(path).st_mode & 0o100 else '100644') if file_mode else indexed
                entries[name] = (mode, None)
                regular.append(name)
            elif path.exists():
                complete = False  # Dirty submodule/nested repository contents are not bound.
            else:
                entries.pop(name, None)
    if regular:
        # Same clean filters (eol, LFS) Git applies on add; without -w no Git objects are written.
        names = sorted(set(regular))
        if any('\n' in name for name in names):
            return None, False
        oids = git(root, 'hash-object', '--stdin-paths', stdin=os.fsencode('\n'.join(names)) + b'\n').decode().split()
        if len(oids) != len(names):
            return None, False
        for name, oid in zip(names, oids):
            entries[name] = (entries[name][0], oid)
    return digest(canonical(sorted([path, *value] for path, value in entries.items()))), complete


def inspect(root, base_ref, scope=()):
    head = resolve(root, 'HEAD')
    base, resolved_ref = resolve_base(root, base_ref)
    branch = git(root, 'symbolic-ref', '--short', '-q', 'HEAD', allowed=(0, 1)).decode().strip() or None
    status = ('status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignore-submodules=none')
    changes = paths_from_status(git(root, *status, *CODE_PATHS))
    task_changes = [row['path'] for row in paths_from_status(git(root, *status, '--', TASKS))]
    tree, complete = _tree(root, changes)
    staged = [os.fsdecode(path) for path in git(root, 'diff', '--cached', '--name-only', '-z', *CODE_PATHS).split(b'\0') if path]
    remotes = {}
    for name in git(root, 'remote').decode().splitlines():
        url = git(root, 'remote', 'get-url', name).decode().strip()
        remotes[name] = safe_remote(url)
    merge_base = git(root, 'merge-base', base, head, allowed=(0, 1)).decode().strip() or None
    outside = [item['path'] for item in changes if scope and not _in_scope(item['path'], scope)]
    shared = [item['path'] for item in changes if item['path'] in ('catalog.json', 'package-lock.json', 'uv.lock', '.cnb.yml')
              or item['path'].startswith(('.github/', '.gitea/', 'migrations/'))]
    return dict(root=str(root), head=head, base=base, base_ref=base_ref, base_ref_resolved=resolved_ref, branch=branch,
                base_is_ancestor=merge_base == base, merge_base=merge_base, remote_freshness='unverified',
                remotes=remotes, dirty=bool(changes), changes=changes, outside_scope=outside, shared_paths=shared,
                staged=staged, staged_outside_scope=[path for path in staged if scope and not _in_scope(path, scope)],
                task_metadata_changes=task_changes, tree_sha256=tree, fingerprint_complete=complete and tree is not None)


def code_identity(snapshot):
    return {key: snapshot.get(key) for key in ('tree_sha256', 'base', 'fingerprint_complete')}


def portable(snapshot):
    """Code facts safe to commit: no local absolute paths, remotes or file listings."""
    return {key: snapshot.get(key) for key in ('branch', 'head', 'base', 'base_ref', 'base_is_ancestor',
                                                'tree_sha256', 'fingerprint_complete', 'dirty')}


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
    base = resolve_base(root, base_ref)[0]
    plan = dict(action='create_worktree', destination=str(destination), branch=branch, base=base,
                applied=False, service_isolation='not_provided')
    if apply:
        git(root, 'worktree', 'add', '-b', branch, str(destination), base)
        plan['applied'] = True
    return plan
