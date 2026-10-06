#!/usr/bin/env python3
"""Audit the historical migration snapshot; requires initialized upstream checkouts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path)
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'catalog.json').read_text())['packages']
    origins = json.loads((ROOT / 'docs/migration-sources.json').read_text())['packages']
    errors, names, changes = [], [], {}
    if {p['name'] for p in catalog} != {p['name'] for p in origins}:
        errors.append('catalog and migration package sets differ')
    for package in catalog:
        path = ROOT / package['path']
        if (path / '.git').exists():
            errors.append(f"nested main repository: {package['name']}")
        for skill in package['skills']:
            names.append(skill['name'])
            if not (path / skill['path']).is_file():
                errors.append(f"missing Skill: {skill['name']}")
    if len(catalog) != 10 or len(names) != 18 or len(set(names)) != 18:
        errors.append('expected 10 packages and 18 unique Skills')
    modules = 0
    for package in origins:
        for module in package['submodules']:
            path = ROOT / package['path'] / module['path']
            relative = path.relative_to(ROOT).as_posix()
            modules += 1
            if git(path, 'rev-parse', 'HEAD') != module['commit']:
                errors.append(f'upstream pin mismatch: {relative}')
            if git(ROOT, 'config', '-f', '.gitmodules', '--get', f'submodule.{relative}.url') != module['url']:
                errors.append(f'upstream URL mismatch: {relative}')
        if args.source_root:
            original_name = '3D-Craft' if package['name'] == '3d-craft' else package['name']
            source = args.source_root / original_name
            if git(source, 'rev-parse', 'HEAD') != package['source_commit']:
                errors.append(f'original HEAD changed: {original_name}')
            digest = hashlib.sha256()
            changed = []
            for entry in git(source, 'ls-files', '--stage', '-z').split('\0'):
                if not entry:
                    continue
                meta, relative = entry.split('\t', 1)
                mode, _, _ = meta.split()
                if mode == '160000' or relative in package['excluded_tracked_paths']:
                    continue
                old = source / relative
                data = str(old.readlink()).encode() if old.is_symlink() else old.read_bytes()
                digest.update(relative.encode() + b'\0' + mode.encode() + b'\0' + hashlib.sha256(data).digest())
                new = ROOT / package['path'] / relative
                new_data = (str(new.readlink()).encode() if new.is_symlink() else new.read_bytes()) if new.exists() else None
                if data != new_data:
                    changed.append(relative)
            if digest.hexdigest() != package['source_tree_sha256']:
                errors.append(f'original source content changed: {original_name}')
            changes[package['name']] = changed
    print(json.dumps({'ok': not errors, 'packages': len(catalog), 'skills': len(names),
                      'upstreams': modules, 'adapted_original_paths': changes, 'errors': errors}, indent=2))
    return int(bool(errors))

if __name__ == '__main__':
    raise SystemExit(main())
