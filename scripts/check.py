#!/usr/bin/env python3
"""Run existing package gates from their package directories; never install or publish."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    packages = json.loads((ROOT / 'catalog.json').read_text())['packages']
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', choices=[p['name'] for p in packages], action='append')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    for package in packages:
        if args.package and package['name'] not in args.package:
            continue
        for command in package['checks']:
            print(f"[{package['name']}] {' '.join(command)}", flush=True)
            if not args.list:
                result = subprocess.run(command, cwd=ROOT / package['path'], env=env)
                if result.returncode:
                    return result.returncode
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
