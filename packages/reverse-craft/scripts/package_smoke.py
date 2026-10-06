#!/usr/bin/env python3
"""Verify the exact private npm candidate and exercise its isolated CLI."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def expected_files():
    tracked = subprocess.check_output(
        ['git', 'ls-files', '-z', 'skills/reverse-craft'], cwd=ROOT, text=True
    ).split('\0')
    paths = {p for p in tracked if p and Path(p).name != '.npmignore'}
    paths.update(('package.json', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'VERSION'))
    return {name: (ROOT / name).read_bytes() for name in paths}


def extract_verified(archive_path, destination, expected):
    if archive_path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('compressed package exceeds 2 MiB')
    destination.mkdir(parents=True)
    with tarfile.open(archive_path, 'r:gz') as archive:
        members = archive.getmembers()
        if len(members) != len(expected):
            raise ValueError('package file count differs from source allowlist')
        seen = set()
        for member in members:
            name = member.name.removeprefix('package/')
            if (member.name != 'package/' + name or name not in expected or name in seen
                    or not member.isfile() or member.size != len(expected[name])):
                raise ValueError(f'unexpected package member: {member.name}')
            seen.add(name)
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f'missing package payload: {name}')
            with stream:
                content = stream.read()
            if content != expected[name]:
                raise ValueError(f'package bytes differ from source: {name}')
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)


def smoke(archive_path):
    with tempfile.TemporaryDirectory(prefix='reverse-craft-package-') as temporary:
        temporary = Path(temporary)
        installed = temporary / 'installed'
        extract_verified(archive_path, installed, expected_files())
        cli = installed / 'skills/reverse-craft/scripts/reverse_craft.py'
        home = str(temporary / 'case-home')

        def run(*args):
            return json.loads(subprocess.check_output(
                [sys.executable, '-I', str(cli), *args], cwd=temporary, text=True))

        scenario = json.loads((ROOT / 'tests/scenarios/01-apk-signature.json').read_text())
        routed = run('route', '--hint', scenario['hint'], '--json')
        if routed['primary']['id'] != scenario['expected_route']:
            raise ValueError('packaged route does not match the scenario contract')
        case = run('case', 'init', '--title', 'candidate-smoke', '--scope', 'synthetic offline fixture', '--home', home)
        case_id = case['case']['id']
        artifact = temporary / 'fixture.txt'
        artifact.write_text('Synthetic package fixture.\n')
        evidence = run('evidence', 'add', '--case', case_id, '--file', str(artifact), '--kind', 'text', '--home', home)
        finding = run('finding', 'add', '--case', case_id, '--title', 'Fixture observed', '--severity', 'info',
                      '--evidence', evidence['evidence']['id'], '--status', 'confirmed',
                      '--reproduction', 'Read fixture.txt and compare its synthetic fixture text.', '--home', home)
        run('path', 'add', '--case', case_id, '--title', 'Fixture path', '--finding', finding['finding']['id'],
            '--status', 'confirmed', '--validation', 'Read the bound synthetic fixture.', '--home', home)
        run('report', 'render', '--case', case_id, '--home', home)
        run('case', 'validate', '--case', case_id, '--json', '--home', home)
        run('case', 'seal', '--case', case_id, '--home', home)
        run('case', 'validate', '--case', case_id, '--json', '--home', home)
    return {'schema': 'reverse-craft.package-smoke.v1', 'valid': True,
            'version': (ROOT / 'VERSION').read_text().strip(),
            'artifact_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
            'checks': ['source-allowlist-and-byte-parity', 'isolated-cli-route',
                       'case-evidence-finding-path-report', 'case-validation-and-seal'],
            'limitations': ['No real host, browser67 or target-environment acceptance.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(smoke(args.package.resolve()), indent=2))
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as error:
        print(f'package smoke failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
