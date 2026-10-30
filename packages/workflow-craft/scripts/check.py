#!/usr/bin/env python3
"""Offline package gate: syntax, Skill links/contracts, regression and artifact smoke."""
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/workflow-craft'


def main():
    for directory in (ROOT / 'scripts', ROOT / 'tests', SKILL / 'scripts'):
        for file in directory.rglob('*.py'):
            ast.parse(file.read_text(encoding='utf-8'), filename=str(file))
    entry = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    if not entry.startswith('---\nname: workflow-craft\ndescription: '):
        raise ValueError('Invalid Skill identity/frontmatter')
    for file in [SKILL / 'SKILL.md', *SKILL.glob('references/*.md'), ROOT / 'README.md', *ROOT.glob('docs/*.md')]:
        for link in re.findall(r'\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
            if '://' not in link and not link.startswith('#') and not (file.parent / link.split('#')[0]).exists():
                raise ValueError(f'Broken local link in {file.relative_to(ROOT)}: {link}')
    for file in SKILL.glob('assets/**/*.json'):
        json.loads(file.read_text(encoding='utf-8'))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    return subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'],
                          cwd=ROOT, env=env).returncode


if __name__ == '__main__':
    raise SystemExit(main())
