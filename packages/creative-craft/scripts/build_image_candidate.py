#!/usr/bin/env python3
"""Build a local image source candidate, excluding credentials and dependencies."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    selected = []
    for directory in ['integrations/image-production', 'skills/creative-craft']:
        for file in (ROOT / directory).rglob('*'):
            relative = file.relative_to(ROOT)
            if any(p in {'node_modules', '__pycache__', '.git'} for p in relative.parts):
                continue
            if file.is_symlink():
                raise ValueError(f'Symlink not supported: {relative}')
            if file.is_file() and file.suffix not in {'.pyc', '.pyo'}:
                if file.suffix not in {'.mjs', '.py', '.json', '.md', '.txt', '.otf', '.yaml', '.yml'} and file.name not in {'VERSION'}:
                    raise ValueError(f'Unexpected candidate input: {relative}')
                selected.append(file)
    selected += [ROOT / name for name in ['integrations/local-production/content-store.mjs', 'LICENSE', 'THIRD_PARTY_NOTICES.md']]
    entries = {str(f.relative_to(ROOT)): f.read_bytes() for f in sorted(selected)}
    font = json.loads(entries['integrations/image-production/fonts/manifest.json'])
    font_path = 'integrations/image-production/fonts/' + font['file']
    if hashlib.sha256(entries[font_path]).hexdigest() != font['sha256']:
        raise ValueError('Bound font differs from manifest')
    entries['README.md'] = b'''# Creative Craft image local candidate

This local source candidate includes the image executor, its shared content store,
source Skill, font and licenses. It excludes node_modules, user assets, auth,
settings and previous dist evidence. It is not a published or globally installed package.

Requirements: Node >=22 and npm. For provider-specific operations, Python >=3.11
is additionally needed. Provider calls and credentials are outside local acceptance.
From the extracted directory:

```sh
cd integrations/image-production
npm ci --ignore-scripts --no-audit --no-fund
node cli.mjs create-photo /absolute/new-project /absolute/brief.json --dry-run
node cli.mjs create-photo /absolute/new-project /absolute/brief.json
node cli.mjs render /absolute/new-project /absolute/new-export
```

Read integrations/image-production/PHOTO-WORKFLOW.md for authorized cropping,
reviewed template inputs, editing, history and shared-copy exports. Supply the
absolute path of this extracted cli.mjs to your agent. Loading the source Skill
alone does not install or discover the executor. No global installation is needed.
Font is bundled and hash-bound; dependencies install from the included lockfile.

candidate.json binds the exact source bytes, including uncommitted working files.
The recorded Git HEAD alone cannot reproduce these files. Verify its hashes before
installation. Same-host isolated acceptance does not prove Windows/Linux support.
Historical dist links in source guides are not bundled and are not prerequisites.
Keep the previous candidate to roll back; this archive does not migrate projects.
'''
    manifest = {'schema': 'creative-craft.image-candidate.v1',
                'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'working_tree_snapshot': True,
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in entries.items()}}
    entries['candidate.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    # Exclusive archive creation never replaces an earlier candidate.
    with args.output.open('xb') as stream:
        try:
            with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
                for name, data in sorted(entries.items()):
                    archive.writestr('creative-craft-image/' + name, data)
        except BaseException:
            # Only this invocation created the file; never leave a partial candidate.
            args.output.unlink()
            raise
    print(json.dumps({'file': str(args.output), 'files': len(entries), 'bytes': args.output.stat().st_size,
                      'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
