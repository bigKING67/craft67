#!/usr/bin/env python3
"""Display the configured workflow mode; --claude reads Claude Code's stdin JSON."""
import argparse
import json
import sys

sys.dont_write_bytecode = True


def main():
    if sys.version_info < (3, 11):
        print('Workflow: 不可用')
        return 0
    from twc_lib.statusline import render

    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--project', default='.', help='Path inside the current Git worktree')
    source.add_argument('--claude', action='store_true', help='Read workspace.current_dir, or cwd, from stdin JSON')
    args = parser.parse_args()
    project = args.project
    if args.claude:
        try:
            raw = sys.stdin.buffer.read(64 * 1024 + 1)
            if len(raw) > 64 * 1024:
                raise ValueError('oversized host input')
            value = json.loads(raw)
            workspace = value.get('workspace', {}) if isinstance(value, dict) else {}
            project = (workspace.get('current_dir') if isinstance(workspace, dict) else None)
            project = project or (value.get('cwd') if isinstance(value, dict) else None)
        except (OSError, ValueError):
            project = None
    print(render(project))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
