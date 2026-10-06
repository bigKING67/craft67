#!/usr/bin/env python3
"""Validate the current catalog and Git submodule pins; optionally emit the CI matrix."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.PIPE).strip()


def contained_file(root, relative):
    if not isinstance(relative, str) or not relative:
        return False
    path = PurePosixPath(relative)
    return (not path.is_absolute() and '..' not in path.parts and '\\' not in relative
            and (root / relative).resolve().is_relative_to(root.resolve())
            and (root / relative).is_file())


def inspect_layout(root, check_checkouts=False):
    catalog = json.loads((root / 'catalog.json').read_text())
    if catalog.get('schema_version') != 1:
        raise ValueError('unsupported catalog schema_version')
    packages = catalog['packages']
    if not isinstance(packages, list) or not packages:
        raise ValueError('catalog packages must be a non-empty list')
    errors, names, skills, matrix = [], set(), set(), []
    for package in packages:
        name, relative = package['name'], package['path']
        if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            errors.append(f'invalid package name: {name!r}')
            continue
        if name in names:
            errors.append(f'duplicate package: {name}')
        names.add(name)
        if relative != f'packages/{name}':
            errors.append(f'package path must be packages/{name}')
            continue
        directory = root / relative
        if not directory.is_dir() or directory.is_symlink() or not directory.resolve().is_relative_to(root.resolve()):
            errors.append(f'missing or symlinked package directory: {relative}')
            continue
        if (directory / '.git').exists():
            errors.append(f'nested main repository: {name}')
        entries = package['skills']
        if not isinstance(entries, list) or not entries:
            errors.append(f'package has no Skill entries: {name}')
            continue
        for skill in entries:
            skill_name = skill['name']
            if not isinstance(skill_name, str) or not skill_name:
                errors.append(f'invalid Skill name: {name}')
                continue
            if skill_name in skills:
                errors.append(f'duplicate Skill: {skill_name}')
            skills.add(skill_name)
            if not contained_file(directory, skill['path']):
                errors.append(f'missing or escaping Skill entry: {skill_name}')
        commands = package['checks']
        if (not isinstance(commands, list) or not commands
                or any(not isinstance(command, list) or not command
                       or any(not isinstance(arg, str) or not arg for arg in command) for command in commands)):
            errors.append(f'invalid check commands: {name}')
        source = package['version_source']
        if (not contained_file(directory, source['path'])
                or source['format'] not in ('text', 'json')
                or (source['format'] == 'json' and not isinstance(source.get('field'), str))):
            errors.append(f'invalid version source: {name}')
        matrix.append({'package': name, 'path': relative})
    actual = {p.name for p in (root / 'packages').iterdir() if p.is_dir()}
    if actual != names:
        errors.append(f'package directory/catalog mismatch: {sorted(actual ^ names)}')

    # Gitlinks in the current index are the pin authority, not the import snapshot.
    links = {}
    for entry in git(root, 'ls-files', '--stage', '-z').split('\0'):
        if not entry:
            continue
        meta, path = entry.split('\t', 1)
        mode, commit, stage = meta.split()
        if stage != '0':
            errors.append(f'unmerged index entry: {path}')
        if mode == '160000':
            links[path] = commit
    registered = set()
    if (root / '.gitmodules').exists():
        result = subprocess.run(['git', '-C', str(root), 'config', '-f', '.gitmodules',
                                 '--get-regexp', r'^submodule\..*\.path$'], capture_output=True, text=True)
        if result.returncode not in (0, 1):
            raise ValueError('cannot parse .gitmodules')
        for line in result.stdout.splitlines():
            key, path = line.split(None, 1)
            if path in registered:
                errors.append(f'duplicate submodule path: {path}')
            registered.add(path)
            url = git(root, 'config', '-f', '.gitmodules', '--get', key[:-4] + 'url')
            if (not url or '..' in PurePosixPath(path).parts or '\\' in path
                    or not (root / path).resolve().is_relative_to(root.resolve())
                    or not any(path.startswith(f'packages/{name}/') for name in names)):
                errors.append(f'invalid submodule registration: {path}')
    if registered != set(links):
        errors.append(f'submodule registration/gitlink mismatch: {sorted(registered ^ set(links))}')
    if check_checkouts:
        for path, commit in links.items():
            checkout = root / path
            if not (checkout / '.git').exists():
                errors.append(f'uninitialized upstream checkout: {path}')
            elif git(checkout, 'rev-parse', 'HEAD') != commit:
                errors.append(f'upstream checkout differs from index pin: {path}')
    return {'ok': not errors, 'packages': len(packages), 'skills': len(skills),
            'upstreams': len(links), 'checkouts_checked': check_checkouts, 'errors': errors}, {'include': matrix}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-checkouts', action='store_true')
    parser.add_argument('--matrix', action='store_true', help='Emit validated GitHub Actions matrix JSON.')
    args = parser.parse_args()
    try:
        report, matrix = inspect_layout(ROOT, args.check_checkouts)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.CalledProcessError) as error:
        report, matrix = {'ok': False, 'errors': [str(error)]}, None
    if args.matrix and not report['ok']:
        print(json.dumps(report), file=sys.stderr)
    else:
        print(json.dumps(matrix if args.matrix else report, ensure_ascii=False))
    return int(not report['ok'])


if __name__ == '__main__':
    raise SystemExit(main())
