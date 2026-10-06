#!/usr/bin/env python3
"""Read package versions from their existing authority and reject mirror drift."""
import argparse
import json
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
NUMBER = r'(?:0|[1-9][0-9]*)'
PRERELEASE = rf'(?:{NUMBER}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)'
SEMVER = re.compile(rf'{NUMBER}\.{NUMBER}\.{NUMBER}(?:-{PRERELEASE}(?:\.{PRERELEASE})*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?')


def inspect_package(root, package):
    directory = root / package['path']
    source = package['version_source']
    text = (directory / source['path']).read_text()
    if source['format'] == 'text':
        version = text.strip()
    elif source['format'] == 'json':
        version = json.loads(text)[source['field']]
    else:
        raise ValueError(f"unsupported version format: {source['format']}")
    errors = []
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        errors.append(f'invalid package version: {version!r}')
    mirrors = {}
    for name in ('package.json', 'package-lock.json'):
        path = directory / name
        if path.exists():
            metadata = json.loads(path.read_text())
            mirrors[name] = metadata.get('version')
            if name == 'package-lock.json' and 'packages' in metadata:
                mirrors['package-lock.json packages[""]'] = metadata['packages'].get('', {}).get('version')
    pyproject = directory / 'pyproject.toml'
    if pyproject.exists():
        project = tomllib.loads(pyproject.read_text()).get('project', {})
        if 'version' in project:
            mirrors['pyproject.toml project.version'] = project['version']
    for name, value in mirrors.items():
        if value != version:
            errors.append(f'{name}: {value!r} differs from {version!r}')
    return version, errors


def main():
    packages = json.loads((ROOT / 'catalog.json').read_text())['packages']
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', choices=[p['name'] for p in packages], action='append')
    parser.add_argument('--check', action='store_true', help='Emit a machine-readable consistency report.')
    args = parser.parse_args()
    versions, errors = {}, []
    for package in packages:
        if args.package and package['name'] not in args.package:
            continue
        try:
            version, problems = inspect_package(ROOT, package)
            versions[package['name']] = version
            errors.extend(f"{package['name']}: {problem}" for problem in problems)
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(f"{package['name']}: {error}")
    if args.check:
        print(json.dumps({'ok': not errors, 'versions': versions, 'errors': errors}, indent=2))
    else:
        for name, version in versions.items():
            print(f'{name:22} {version:12} {name}/v{version}')
        for error in errors:
            print(f'ERROR: {error}')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
