#!/usr/bin/env python3
"""Build or verify offline candidates using existing package gates; never publish."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from versions import inspect_package

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = ('review-craft', '3d-craft')
MANIFEST = 'candidate.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def version_for(package):
    entry = next(p for p in json.loads((ROOT / 'catalog.json').read_text())['packages'] if p['name'] == package)
    version, errors = inspect_package(ROOT, entry)
    if errors:
        raise ValueError('; '.join(errors))
    return version


def verify(directory, package, expected_sha):
    manifest = json.loads((directory / MANIFEST).read_text())
    if (manifest['schema'] != 'craft67.candidate.v1' or manifest['package'] != package
            or manifest['source_sha'] != expected_sha or manifest['status'] != 'offline-candidate'
            or manifest['package_path'] != f'packages/{package}'
            or manifest['version'] != version_for(package)):
        raise ValueError('candidate identity does not match the requested source/package/version')
    files = manifest['files']
    extension = '.tgz' if package == 'review-craft' else '.zip'
    if not isinstance(files, dict) or not any(name.endswith(extension) for name in files):
        raise ValueError('candidate has no package archive')
    if {p.name for p in directory.iterdir()} != set(files) | {MANIFEST}:
        raise ValueError('candidate file set differs from manifest')
    for name, checksum in files.items():
        path = directory / name
        if (Path(name).name != name or '\\' in name or path.is_symlink()
                or not path.is_file() or digest(path) != checksum):
            raise ValueError(f'candidate file is invalid or changed: {name}')
    return manifest


def build(package, directory):
    if directory == ROOT or ROOT in directory.parents:
        raise ValueError('candidate output must be outside the repository')
    if directory.exists():
        raise ValueError('candidate output must not exist; refusing to overwrite')
    if git('status', '--porcelain', '--untracked-files=all'):
        raise ValueError('candidate build requires a clean worktree')
    source_sha, version = git('rev-parse', 'HEAD'), version_for(package)
    directory.mkdir(parents=True)
    if package == 'review-craft':
        command = [sys.executable, 'scripts/release_gate.py',
                   '--package-output', str(directory / 'review-craft.tgz'),
                   '--package-receipt', str(directory / 'package-receipt.json')]
    else:
        command = [sys.executable, 'scripts/release_gate.py', '--output-dir', str(directory), '--json']
    subprocess.run(command, cwd=ROOT / 'packages' / package, check=True)
    if git('rev-parse', 'HEAD') != source_sha or git('status', '--porcelain', '--untracked-files=all'):
        raise ValueError('source changed during candidate build')
    files = {p.name: digest(p) for p in sorted(directory.iterdir()) if p.is_file()}
    manifest = {'schema': 'craft67.candidate.v1', 'status': 'offline-candidate',
                'package': package, 'version': version, 'source_sha': source_sha,
                'package_path': f'packages/{package}', 'files': files,
                'limitations': ['Not a tag or Release; no global installation.',
                                'Real host, model, browser and visual acceptance are not established by this build.']}
    (directory / MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n')
    return verify(directory, package, source_sha)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'verify'))
    parser.add_argument('--package', choices=SUPPORTED, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--expected-sha', help='Required for verification of a downloaded candidate.')
    args = parser.parse_args()
    try:
        directory = args.directory.expanduser().resolve()
        if args.action == 'build':
            manifest = build(args.package, directory)
        else:
            if not args.expected_sha or args.expected_sha != git('rev-parse', 'HEAD'):
                raise ValueError('verification requires the expected full source SHA checked out locally')
            manifest = verify(directory, args.package, args.expected_sha)
        print(json.dumps(manifest, indent=2))
    except (OSError, ValueError, KeyError, TypeError, StopIteration, subprocess.CalledProcessError) as error:
        print(f'candidate {args.action} failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
