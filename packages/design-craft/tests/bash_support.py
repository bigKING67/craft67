from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def bash_executable() -> str:
    configured = os.environ.get("DESIGN_CRAFT_BASH", "").strip()
    executable = shutil.which(configured or "bash")
    if executable is None:
        raise RuntimeError(
            "Git Bash is required; set DESIGN_CRAFT_BASH to Git for Windows bash.exe"
        )
    normalized = executable.replace("\\", "/").lower()
    if os.name == "nt" and normalized.endswith("/windows/system32/bash.exe"):
        raise RuntimeError("DESIGN_CRAFT_BASH resolved to WSL bash instead of Git Bash")
    return executable


def bash_path(path: Path, *, bash: str) -> str:
    if os.name != "nt":
        return str(path)
    result = subprocess.run(
        [
            bash,
            "--noprofile",
            "--norc",
            "-c",
            'cygpath -u "$1"',
            "design-craft-path",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    converted = result.stdout.strip()
    if result.returncode != 0 or not converted:
        raise RuntimeError(
            "Git Bash path conversion failed\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return converted


def bash_command(script: Path, *args: str) -> list[str]:
    bash = bash_executable()
    return [bash, bash_path(script, bash=bash), *args]
