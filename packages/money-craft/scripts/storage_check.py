#!/usr/bin/env python3
"""Read-only repository storage inventory; never remove research or environments."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[1]


def size(path):
    total = 0
    seen = set()  # hard links share blocks; count each inode once
    for directory, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
        for name in files:
            stat = (Path(directory) / name).lstat()
            if (stat.st_dev, stat.st_ino) in seen:
                continue
            seen.add((stat.st_dev, stat.st_ino))
            total += stat.st_blocks * 512
    return total


def inventory(root=ROOT, now=None):
    now = time.time() if now is None else now
    local = root / 'local'
    categories = []
    review = []
    if local.is_symlink():
        raise ValueError('refusing symlinked local directory')
    if local.exists():
        for path in sorted(local.iterdir()):
            if not path.is_dir() or path.is_symlink():
                continue
            categories.append({'path': str(path.relative_to(root)), 'allocated_bytes': size(path)})
            if path.name not in {'skill-evals', 'acceptance'}:
                continue
            for run in sorted(path.iterdir()):
                if not run.is_dir() or run.is_symlink():
                    continue
                match = re.match(r'^(\d{8})-', run.name)
                if not match:
                    continue
                try:
                    date = dt.datetime.strptime(match[1], '%Y%m%d').replace(tzinfo=dt.timezone.utc)
                except ValueError:
                    continue
                if now - date.timestamp() >= 30 * 86400:
                    review.append(str(run.relative_to(root)))
    return {'schema': 'money-craft.storage-inventory.v1', 'read_only': True,
            'categories': categories, 'older_than_30_days_review_only': review,
            'note': 'Age is inferred from run names, not last use. Review is not deletion eligibility. '
                    'Category totals are allocated blocks, not exclusive APFS disk usage.'}


if __name__ == '__main__':
    print(json.dumps(inventory(), indent=2))
