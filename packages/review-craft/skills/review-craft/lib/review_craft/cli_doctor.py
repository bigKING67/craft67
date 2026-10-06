from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import tempfile

from . import __version__


def command_doctor(args: argparse.Namespace) -> int:
    temporary_directory = tempfile.gettempdir()
    temporary_directory_writable = os.access(temporary_directory, os.W_OK)
    payload = {
        "version": __version__,
        "python": platform.python_version(),
        "pythonSupported": sys.version_info >= (3, 10),
        "git": shutil.which("git"),
        "temporaryDirectory": temporary_directory,
        "temporaryDirectoryWritable": temporary_directory_writable,
        "ready": bool(
            sys.version_info >= (3, 10)
            and shutil.which("git")
            and temporary_directory_writable
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True) if args.json else payload)
    return 0 if payload["ready"] else 2
