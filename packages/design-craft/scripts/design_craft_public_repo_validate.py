#!/usr/bin/env python3
"""Validate public-repository privacy, licensing, and portability hygiene."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


SCHEMA = "design-craft.public-repo-verification.v1"
ROOT = Path(__file__).resolve().parents[1]
SELF_PATH = "scripts/design_craft_public_repo_validate.py"
POLICY_PATH = "docs/public-history-policy.md"
HISTORY_BASELINE = "d4380a0b8b848c03402f263a09d59bb36cfabdc4"
SKIP_PREFIXES = ("upstreams/", ".git/")
TEXT_SUFFIXES = {
    "",
    ".cjs",
    ".css",
    ".html",
    ".java",
    ".js",
    ".json",
    ".kt",
    ".kts",
    ".md",
    ".mjs",
    ".plist",
    ".py",
    ".sh",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
USER_HOME_PATTERN = re.compile(
    r"(?:/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|[A-Za-z]:\\Users\\[^\\\s]+)"
)


def repository_paths() -> tuple[list[str], list[str]]:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        return [], [f"cannot enumerate repository files: {detail}"]
    paths = [item.decode("utf-8") for item in completed.stdout.split(b"\0") if item]
    return paths, []


def path_errors(paths: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for relative in sorted(paths):
        if relative == SELF_PATH or relative.startswith(SKIP_PREFIXES):
            continue
        path = ROOT / relative
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in USER_HOME_PATTERN.finditer(text):
            errors.append(f"public file exposes a user-home path: {relative}: {match.group(0)}")
    return errors


def added_history_path_errors(diff: str) -> list[str]:
    errors: list[str] = []
    current_path = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_path = line.removeprefix("+++ b/")
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if current_path == SELF_PATH:
            continue
        for match in USER_HOME_PATTERN.finditer(line[1:]):
            errors.append(
                "public history adds a user-home path after the privacy baseline: "
                f"{match.group(0)}"
            )
    return errors


def history_errors() -> list[str]:
    policy = ROOT / POLICY_PATH
    if not policy.is_file():
        return [f"missing public history policy: {POLICY_PATH}"]
    policy_text = policy.read_text(encoding="utf-8")
    if HISTORY_BASELINE not in policy_text:
        return [f"{POLICY_PATH} must record the privacy baseline {HISTORY_BASELINE}"]
    # A snapshot import starts a new history. Scan all package history in craft67,
    # including the initial commit; standalone repositories retain their baseline.
    catalog_path = ROOT.parent.parent / "catalog.json"
    monorepo = False
    if catalog_path.is_file():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        monorepo = any(
            entry.get("name") == "design-craft"
            and (catalog_path.parent / entry.get("path", "")).resolve() == ROOT.resolve()
            for entry in catalog.get("packages", [])
        )
    if not monorepo:
        baseline = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{HISTORY_BASELINE}^{{commit}}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if baseline.returncode != 0:
            return [f"public history baseline is unavailable: {HISTORY_BASELINE}"]
    revision = "HEAD" if monorepo else f"{HISTORY_BASELINE}..HEAD"
    diff = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "log",
            "--format=",
            "--unified=0",
            "--no-ext-diff",
            "--relative",
            "--root",
            revision,
            "--",
            ".",
            ":(exclude)upstreams",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if diff.returncode != 0:
        return [diff.stderr.strip() or "cannot inspect public history after the privacy baseline"]
    return added_history_path_errors(diff.stdout)


def runtime_identifier_errors() -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "evals/native-runtime").glob("*observed.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid native runtime evidence {path.relative_to(ROOT)}: {exc}")
            continue
        runtime_id = payload.get("runtime_id")
        if payload.get("runtime_id_kind") != "sha256" or not isinstance(
            runtime_id, str
        ) or not re.fullmatch(r"sha256:[0-9a-f]{64}", runtime_id):
            errors.append(
                f"public native evidence exposes an unredacted runtime identifier: {path.relative_to(ROOT)}"
            )
    return errors


def license_errors() -> list[str]:
    errors: list[str] = []
    required = (
        "LICENSE",
        "LICENSES/Apache-2.0.txt",
        "LICENSES/MIT-upstreams.txt",
        "LICENSES/NOTICE-impeccable.md",
        "LICENSES/VERCEL-DESIGN-NOTICE.md",
        "THIRD_PARTY_NOTICES.md",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            errors.append(f"missing public license or notice file: {relative}")

    try:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"package.json is invalid: {exc}")
        package = {}
    if package.get("license") != "MIT":
        errors.append("package.json license must match the root MIT license")

    root_license = (ROOT / "LICENSE").read_text(encoding="utf-8") if (ROOT / "LICENSE").is_file() else ""
    if "MIT License" not in root_license or "Copyright (c) 2026 bigKING67" not in root_license:
        errors.append("root LICENSE must contain the complete design-craft MIT grant")

    notices = (
        (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        if (ROOT / "THIRD_PARTY_NOTICES.md").is_file()
        else ""
    )
    for token in (
        "LICENSES/MIT-upstreams.txt",
        "LICENSES/Apache-2.0.txt",
        "LICENSES/NOTICE-impeccable.md",
        "LICENSES/VERCEL-DESIGN-NOTICE.md",
    ):
        if token not in notices:
            errors.append(f"THIRD_PARTY_NOTICES.md must reference {token}")
    for relative in (
        "skills/design-craft/templates/developer-product/design.md",
        "skills/design-craft/templates/developer-product/design.dark.md",
    ):
        path = ROOT / relative
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if "source: original-design-craft" not in text:
            errors.append(f"current developer-product seed must declare original authorship: {relative}")
    for relative in (
        "skills/design-craft/templates/vercel-geist/design.md",
        "skills/design-craft/templates/vercel-geist/design.dark.md",
    ):
        path = ROOT / relative
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if "Legacy path" not in text or "name: Geist" in text:
            errors.append(f"legacy Vercel path must not redistribute the historical snapshot: {relative}")
    return errors


def validate() -> dict:
    paths, errors = repository_paths()
    errors.extend(path_errors(paths))
    errors.extend(history_errors())
    errors.extend(runtime_identifier_errors())
    errors.extend(license_errors())
    return {
        "schema": SCHEMA,
        "root": str(ROOT),
        "files_scanned": len(paths),
        "history_baseline": HISTORY_BASELINE,
        "ok": not errors,
        "errors": errors,
    }


def self_check() -> list[str]:
    errors: list[str] = []
    safe = "artifact: ~/.browser67/runtime/runs/example.png"
    unsafe = "/" + "Users" + "/example/private.png"
    if USER_HOME_PATTERN.search(safe):
        errors.append("public path validator rejected a home-relative path")
    if not USER_HOME_PATTERN.search(unsafe):
        errors.append("public path validator did not reject a macOS user-home path")
    windows = "C:" + "\\Users\\example\\private.png"
    if not USER_HOME_PATTERN.search(windows):
        errors.append("public path validator did not reject a Windows user-home path")
    sample_diff = (
        "+++ b/example.md\n"
        "+safe: ~/.browser67/example.png\n"
        "+private: /Users/example/private.png\n"
    )
    if len(added_history_path_errors(sample_diff)) != 1:
        errors.append("public history validator did not isolate new absolute paths")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.check and not args.validate:
        args.validate = True

    errors = self_check() if args.check else []
    payload = validate() if args.validate else {
        "schema": SCHEMA,
        "root": str(ROOT),
        "files_scanned": 0,
        "ok": True,
        "errors": [],
    }
    errors.extend(payload["errors"])
    payload["errors"] = errors
    payload["ok"] = not errors

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif payload["ok"]:
        print(f"public repository verified: {payload['files_scanned']} files scanned")
    else:
        print("\n".join(errors), file=sys.stderr)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
