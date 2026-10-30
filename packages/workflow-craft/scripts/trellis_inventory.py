#!/usr/bin/env python3
"""Read-only Trellis migration assessment; never imports, activates or rewrites tasks."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

MAX_BYTES = 1024 * 1024
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,199}\Z')
AUTHORITY_FILES = ('AGENTS.md', 'CLAUDE.md', 'PLANS.md', '.trellis/workflow.md', '.trellis/config.yaml')


def inventory(project):
    root = Path(project).resolve(strict=True)
    findings, sources, tasks, specs = [], {}, [], []

    def finding(code, path, severity='review'):
        item = dict(code=code, path=str(path), severity=severity)
        if item not in findings:
            findings.append(item)

    def read(relative, required=True):
        path = root / relative
        # Do not follow linked source directories, including links within the repo.
        if any(part.is_symlink() for part in (path, *path.parents) if part != root and root in part.parents):
            finding('symlink_not_read', relative, 'error')
            return None
        try:
            before = path.lstat()
            if not stat.S_ISREG(before.st_mode):
                finding('non_regular_file', relative, 'error')
                return None
            fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
            with os.fdopen(fd, 'rb') as stream:
                opened = os.fstat(stream.fileno())
                raw = stream.read(MAX_BYTES + 1)
                after = os.fstat(stream.fileno())
            identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
            if identity(before) != identity(opened) or identity(opened) != identity(after):
                finding('source_changed_during_read', relative, 'error')
                return None
            if len(raw) > MAX_BYTES:
                finding('file_exceeds_inventory_limit', relative, 'error')
                return None
            sources[relative] = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            return raw
        except FileNotFoundError:
            if required:
                finding('source_missing', relative, 'error')
        except OSError:
            finding('source_unreadable', relative, 'error')
        return None

    def files(relative):
        directory = root / relative
        if directory.is_symlink() or (root / '.trellis').is_symlink():
            finding('symlink_not_read', relative, 'error')
            return []
        if not directory.is_dir():
            finding('directory_missing', relative, 'error')
            return []
        result = []
        def walk_error(error):
            finding('directory_unreadable', relative, 'error')
        for current, directories, names in os.walk(directory, followlinks=False, onerror=walk_error):
            for name in list(directories):
                path = Path(current) / name
                if path.is_symlink():
                    finding('symlink_not_read', path.relative_to(root).as_posix(), 'error')
                    directories.remove(name)
            result.extend((Path(current) / name).relative_to(root).as_posix() for name in names)
        return sorted(result)

    def identifier(value, path, field, optional=False):
        if value is None and optional:
            return None
        if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
            finding('invalid_' + field, path, 'error')
            return None
        return value

    version_raw = read('.trellis/.version')
    try:
        version = version_raw.decode('utf-8').strip() if version_raw is not None else None
        if version is not None and not re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}(?:[-+][A-Za-z0-9.-]+)?', version):
            raise ValueError('invalid version')
    except (ValueError, UnicodeError):
        version = None
        finding('invalid_version', '.trellis/.version', 'error')
    for relative in AUTHORITY_FILES:
        read(relative, required=False)

    task_files = files('.trellis/tasks')
    artifacts = set(task_files)
    for relative in task_files:
        if Path(relative).name != 'task.json':
            continue
        raw = read(relative)
        if raw is None:
            continue
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('not an object')
        except (ValueError, UnicodeError):
            finding('invalid_task_json', relative, 'error')
            continue
        task_id = identifier(data.get('id'), relative, 'task_id')
        status_value = data.get('status')
        if status_value not in ('planning', 'in_progress', 'completed'):
            finding('unrecognized_task_status', relative)
            status_value = None  # Preserve original bytes via source hash, not an invented status.
        profile = data.get('workflow_profile')
        if profile not in (None, 'lite', 'full'):
            finding('unrecognized_workflow_profile', relative)
            profile = None
            effective = None
        else:
            effective = profile or 'full'
        archived = Path(relative).parts[2] == 'archive'
        if status_value == 'completed' and not archived:
            finding('completed_but_not_archived', relative, 'notice')
        if archived and status_value != 'completed':
            finding('archived_without_completed_status', relative)
        parent = identifier(data.get('parent'), relative, 'parent', optional=True)
        children = data.get('children', [])
        if not isinstance(children, list):
            finding('invalid_children', relative, 'error')
            children = []
        children = [identifier(child, relative, 'child') for child in children]
        children = [child for child in children if child is not None]
        if len(children) != len(set(children)):
            finding('duplicate_child_reference', relative)
        related = []
        for name in ('prd.md', 'design.md', 'implement.md', 'implement.jsonl', 'check.jsonl'):
            path = (Path(relative).parent / name).as_posix()
            if path in artifacts and read(path) is not None:
                related.append(path)
        tasks.append(dict(source=relative, directory=Path(relative).parent.name,
                          id=task_id, archived=archived, status=status_value,
                          declared_profile=data.get('workflow_profile') if data.get('workflow_profile') in ('lite', 'full') else None,
                          effective_profile=effective, legacy_profile_default=(data.get('workflow_profile') is None),
                          parent=parent, children=children, fields=sorted(data), artifacts=related))

    spec_files = files('.trellis/spec')
    for relative in spec_files:
        if read(relative) is not None:
            specs.append(relative)

    by_id, by_directory = defaultdict(list), defaultdict(list)
    for task in tasks:
        if task['id']:
            by_id[task['id']].append(task)
        by_directory[task['directory']].append(task)
    for members in by_id.values():
        if len(members) > 1:
            for task in members:
                finding('ambiguous_task_id', task['source'])
    for members in by_directory.values():
        if len(members) > 1:
            for task in members:
                finding('ambiguous_task_directory', task['source'])
    relations = []
    for task in tasks:
        references = ([('parent', task['parent'])] if task['parent'] else []) + [('child', child) for child in task['children']]
        for kind, target in references:
            # Trellis persists directory names, not task.json id, in these fields.
            matches = by_directory.get(target, [])
            resolved = matches[0] if len(matches) == 1 else None
            if resolved is None:
                finding('unresolved_' + kind, task['source'])
            elif resolved['source'] == task['source']:
                finding('self_relation', task['source'])
            elif kind == 'child' and task['archived'] and resolved['parent'] is None:
                # AIOS archive clears active children's backlinks; retain the history.
                finding('archived_parent_without_backlink', task['source'], 'notice')
            elif (kind == 'parent' and task['directory'] not in resolved['children']
                  or kind == 'child' and resolved['parent'] != task['directory']):
                finding('nonreciprocal_' + kind, task['source'])
            relations.append(dict(source=task['source'], kind=kind, target_directory=target,
                                  target_source=resolved['source'] if resolved else None))

    # A reciprocal parent/child pair can still belong to a cyclic task tree.
    for task in tasks:
        chain, current = [], task
        while current['source'] not in chain:
            chain.append(current['source'])
            matches = by_directory.get(current['parent'], [])
            if len(matches) != 1:
                break
            current = matches[0]
        else:
            for relative in chain[chain.index(current['source']):]:
                finding('cyclic_parent_relation', relative)

    # Capture drift instead of certifying a moving project as a frozen migration source.
    first_sources = dict(sources)
    for relative, expected in first_sources.items():
        if read(relative) is not None and sources[relative] != expected:
            finding('source_changed_during_inventory', relative, 'error')
    if files('.trellis/tasks') != task_files:
        finding('task_file_set_changed', '.trellis/tasks', 'error')
    if files('.trellis/spec') != spec_files:
        finding('spec_file_set_changed', '.trellis/spec', 'error')
    summary = dict(discovered_task_records=sum(Path(path).name == 'task.json' for path in task_files),
                   tasks=len(tasks), unarchived=sum(not row['archived'] for row in tasks),
                   archived=sum(row['archived'] for row in tasks), specs=len(specs),
                   statuses=dict(sorted(Counter(row['status'] or 'unrecognized' for row in tasks).items())),
                   declared_profiles=dict(sorted(Counter(row['declared_profile'] or 'missing_or_unrecognized' for row in tasks).items())),
                   relations=len(relations), findings=dict(sorted(Counter(row['code'] for row in findings).items())))
    return dict(schema='workflow-craft.trellis-inventory.v1',
                status='needs_review' if any(row['severity'] != 'notice' for row in findings) else 'ok',
                scope='task metadata, canonical planning artifacts, specs and project rule hashes',
                migration_ready=False, source_version=version, summary=summary, tasks=tasks,
                specs=specs, relations=relations, sources=first_sources, findings=findings,
                limitations=['not a full archive backup', 'no runtime sessions or credentials inspected',
                             'legacy profiles are observed with the existing full default, never rewritten',
                             'no imports, project checks, task execution, host activation or remote requests'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, help='Existing project containing .trellis; read only')
    args = parser.parse_args()
    try:
        result = inventory(args.project)
    except OSError:
        print(json.dumps(dict(status='error', message='Cannot read the explicit project directory')))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
