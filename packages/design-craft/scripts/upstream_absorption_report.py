#!/usr/bin/env python3
"""Report upstream submodule drift and candidate absorption surfaces."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from design_craft_absorption_common import (
    CUMULATIVE_STATUSES,
    LATEST_RANGE_STATUSES,
    LEGACY_DECISION_BY_CUMULATIVE_STATUS,
    LOCK_SCHEMA,
)


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ChangedFile:
    status: str
    path: str
    category: str


@dataclass
class RemoteCommit:
    sha: str
    date: str
    title: str
    url: str


@dataclass
class UpstreamReport:
    name: str
    repo: str
    path: str
    license: str
    locked_commit: str
    reviewed_commit: str
    absorbed_commit: str
    cumulative_status: str
    reviewed_through_commit: str
    behavior_absorbed_through_commit: str
    latest_range_base_commit: str
    latest_range_head_commit: str
    latest_range_status: str
    reviewed_at: str
    decision: str
    decision_notes: str
    current_commit: str | None
    remote_commit: str | None
    remote_ref: str | None
    exists: bool
    is_git_repo: bool
    lock_commit_available: bool
    drift: bool
    remote_drift: bool | None
    locked_remote_drift: bool | None
    reviewed_remote_drift: bool | None
    remote_compare_status: str | None
    remote_ahead_by: int | None
    remote_compare_url: str | None
    remote_recommendation: str | None
    remote_commits: list[RemoteCommit]
    remote_changed_files: list[ChangedFile]
    remote_detail_error: str | None
    dirty: bool
    status: list[str]
    changed_files: list[ChangedFile]
    notes: list[str]
    remote_detail_source: str | None = None


def run_git(path: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=check,
    )


def git_output(path: Path, args: list[str]) -> str | None:
    result = run_git(path, args)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def remote_head(repo: str) -> tuple[str | None, str | None, str | None]:
    try:
        result = subprocess.run(
            ["git", "ls-remote", repo, "HEAD", "refs/heads/main", "refs/heads/master"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception as exc:
        return None, None, str(exc)

    if result.returncode != 0:
        return None, None, result.stderr.strip() or f"git ls-remote exited {result.returncode}"

    refs: dict[str, str] = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2:
            refs[fields[1]] = fields[0]

    for ref in ("HEAD", "refs/heads/main", "refs/heads/master"):
        if ref in refs:
            return refs[ref], ref, None
    return None, None, "remote did not return HEAD, main, or master"


def github_repo_slug(repo: str) -> str | None:
    patterns = (
        r"^https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$",
        r"^git@github\.com:([^/]+/[^/]+?)(?:\.git)?$",
        r"^ssh://git@github\.com/([^/]+/[^/]+?)(?:\.git)?/?$",
    )
    for pattern in patterns:
        match = re.match(pattern, repo.strip())
        if match:
            return match.group(1)
    return None


def github_compare(
    repo: str,
    base: str,
    head: str,
    upstream_name: str,
) -> tuple[str | None, int | None, str | None, list[RemoteCommit], list[ChangedFile], str | None]:
    slug = github_repo_slug(repo)
    if not slug:
        return None, None, None, [], [], "remote details currently support GitHub repositories only"

    api_url = f"https://api.github.com/repos/{slug}/compare/{quote(base, safe='')}...{quote(head, safe='')}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "design-craft-upstream-audit",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        request = Request(api_url, headers=headers)
        with urlopen(request, timeout=30) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
    except HTTPError as exc:
        return None, None, api_url, [], [], f"GitHub compare returned HTTP {exc.code}"
    except (URLError, TimeoutError, OSError) as exc:
        return None, None, api_url, [], [], f"GitHub compare failed: {exc}"

    if len(raw) > 4 * 1024 * 1024:
        return None, None, api_url, [], [], "GitHub compare payload exceeded 4 MiB"
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, None, api_url, [], [], f"GitHub compare returned invalid JSON: {exc}"

    commits: list[RemoteCommit] = []
    for item in payload.get("commits", [])[:100]:
        commit = item.get("commit", {}) if isinstance(item, dict) else {}
        committer = commit.get("committer", {}) if isinstance(commit, dict) else {}
        message = commit.get("message", "") if isinstance(commit, dict) else ""
        commits.append(
            RemoteCommit(
                sha=str(item.get("sha", "")),
                date=str(committer.get("date", "")),
                title=str(message).splitlines()[0] if message else "",
                url=str(item.get("html_url", "")),
            )
        )

    status_map = {
        "added": "A",
        "modified": "M",
        "removed": "D",
        "renamed": "R",
        "copied": "C",
        "changed": "M",
    }
    files: list[ChangedFile] = []
    for item in payload.get("files", [])[:300]:
        if not isinstance(item, dict):
            continue
        path = str(item.get("filename", ""))
        if not path:
            continue
        status = status_map.get(str(item.get("status", "")), "?")
        files.append(ChangedFile(status=status, path=path, category=categorize_changed_file(upstream_name, path)))

    incomplete = []
    if len(payload.get("files", [])) >= 300:
        incomplete.append("file list reached the 300-entry limit")
    if payload.get("total_commits", len(payload.get("commits", []))) > len(commits):
        incomplete.append("commit list is truncated")
    return (
        str(payload.get("status", "")) or None,
        payload.get("ahead_by") if isinstance(payload.get("ahead_by"), int) else None,
        str(payload.get("html_url", "")) or api_url,
        commits,
        files,
        "Incomplete GitHub compare: " + "; ".join(incomplete) if incomplete else None,
    )


def categorize_changed_file(upstream_name: str, file_path: str) -> str:
    normalized = file_path.lower()
    parts = set(normalized.split("/"))

    repository_operations_prefixes = (
        ".github/",
        "scripts/github/",
        "tests/github-",
        "tests/github/",
    )
    if normalized.startswith(repository_operations_prefixes):
        return "repository_operations_only"

    candidate_keywords = {
        "skill",
        "skills",
        "reference",
        "references",
        "scripts",
        "script",
        "tests",
        "test",
    }
    if parts & candidate_keywords:
        return "candidate_absorb"

    if upstream_name == "impeccable" and (
        normalized.startswith("cli/engine/rules/")
        or normalized.startswith("site/content/skills/")
        or normalized.startswith("site/content/reference/")
        or normalized.startswith("skill/reference/")
        or normalized.startswith("skill/scripts/")
    ):
        return "candidate_absorb"

    if upstream_name == "taste-skill" and normalized.startswith("skills/"):
        return "candidate_absorb"

    provenance_names = {
        "license",
        "readme.md",
        "changelog.md",
        "store_listing.md",
        "marketplace.json",
        "plugin.json",
        "funding.yml",
    }
    if Path(normalized).name in provenance_names:
        return "provenance_only"

    provenance_prefixes = (
        "assets/",
        "extension/icons/",
        ".github/",
        "examples/",
    )
    if normalized.startswith(provenance_prefixes):
        return "provenance_only"

    return "manual_review"


def recommend_remote_decision(files: list[ChangedFile]) -> str:
    if not files:
        return "manual_review"
    categories = {item.category for item in files}
    if "candidate_absorb" in categories:
        return "absorption_review"
    if "manual_review" in categories:
        return "manual_review"
    return "provenance_only"


def parse_name_status(text: str, upstream_name: str) -> list[ChangedFile]:
    files: list[ChangedFile] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        status = fields[0]
        # Rename/copy status emits old and new paths; categorize the resulting path.
        path = fields[-1]
        files.append(
            ChangedFile(
                status=status,
                path=path,
                category=categorize_changed_file(upstream_name, path),
            )
        )
    return files


def local_compare(path: Path, base: str, head: str, name: str) -> tuple[list[RemoteCommit], list[ChangedFile]]:
    """Read a complete forward range without fetching or changing the checkout."""
    if not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (base, head)):
        raise ValueError("local comparison requires full commit SHAs")

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(path), *args], capture_output=True,
            timeout=30, check=True,
        )
        # Git emits UTF-8 paths on Windows too. Decode explicitly and avoid
        # text-mode newline translation for legal POSIX filename bytes.
        return result.stdout.decode("utf-8", errors="surrogateescape")

    git("merge-base", "--is-ancestor", base, head)
    # NUL delimiters preserve tabs/newlines and non-ASCII filenames. Disable
    # rename heuristics and override submodule ignores so local Git settings
    # cannot silently change coverage.
    fields = git(
        "diff", "--no-ext-diff", "--no-renames", "--ignore-submodules=none",
        "--name-status", "-z", base, head,
    ).split("\0")
    if fields[-1] == "":
        fields.pop()
    if len(fields) % 2:
        raise ValueError("invalid local name-status output")
    files = [ChangedFile(fields[i], fields[i + 1], categorize_changed_file(name, fields[i + 1]))
             for i in range(0, len(fields), 2)]
    commits = []
    for sha in git("rev-list", "--reverse", f"{base}..{head}").splitlines():
        date, title = git("show", "-s", "--format=%cI%x00%s", sha).rstrip("\n").split("\0", 1)
        commits.append(RemoteCommit(sha, date, title, ""))
    return commits, files


def build_report(
    root: Path,
    check_remote: bool = False,
    fetch_remote_details: bool = False,
) -> list[UpstreamReport]:
    lock_path = root / "upstreams.lock.json"
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    if payload.get("schema") != LOCK_SCHEMA:
        raise ValueError(f"upstream lock schema must be {LOCK_SCHEMA}")
    reports: list[UpstreamReport] = []

    for name, meta in payload.get("upstreams", {}).items():
        rel_path = meta.get("path", "")
        upstream_path = root / rel_path
        locked = meta.get("commit", "")
        reviewed = meta.get("reviewed_through_commit", meta.get("reviewed_commit", ""))
        absorbed = meta.get(
            "behavior_absorbed_through_commit", meta.get("absorbed_commit", "")
        )
        cumulative_status = meta.get("cumulative_status", "")
        latest_range_base = meta.get("latest_range_base_commit", "")
        latest_range_head = meta.get("latest_range_head_commit", "")
        latest_range_status = meta.get("latest_range_status", "")
        reviewed_at = meta.get("reviewed_at", "")
        decision = meta.get("decision", "")
        decision_notes = meta.get("notes", "")
        notes: list[str] = []
        status_lines: list[str] = []
        changed_files: list[ChangedFile] = []

        exists = upstream_path.exists()
        is_git_repo = False
        lock_available = False
        current: str | None = None
        dirty = False
        drift = False
        remote_commit: str | None = None
        remote_ref: str | None = None
        remote_drift: bool | None = None
        locked_remote_drift: bool | None = None
        reviewed_remote_drift: bool | None = None
        remote_compare_status: str | None = None
        remote_ahead_by: int | None = None
        remote_compare_url: str | None = None
        remote_recommendation: str | None = None
        remote_commits: list[RemoteCommit] = []
        remote_changed_files: list[ChangedFile] = []
        remote_detail_error: str | None = None
        remote_detail_source: str | None = None

        if cumulative_status not in CUMULATIVE_STATUSES:
            notes.append("lock cumulative_status is invalid")
        if latest_range_status not in LATEST_RANGE_STATUSES:
            notes.append("lock latest_range_status is invalid")
        expected_legacy = LEGACY_DECISION_BY_CUMULATIVE_STATUS.get(cumulative_status)
        if expected_legacy and decision != expected_legacy:
            notes.append(
                f"legacy decision must be {expected_legacy} for cumulative_status={cumulative_status}"
            )
        if not reviewed or not reviewed_at:
            notes.append("review metadata is incomplete")
        if cumulative_status != "deferred" and not absorbed:
            notes.append("non-deferred cumulative states require behavior_absorbed_through_commit")
        if meta.get("reviewed_commit") != reviewed:
            notes.append("reviewed_commit must alias reviewed_through_commit")
        if meta.get("absorbed_commit") != absorbed:
            notes.append("absorbed_commit must alias behavior_absorbed_through_commit")
        if latest_range_head != reviewed:
            notes.append("latest range head must match reviewed_through_commit")

        if check_remote:
            remote_commit, remote_ref, remote_error = remote_head(meta.get("repo", ""))
            if remote_error:
                notes.append(f"remote check failed: {remote_error}")

        if not exists:
            notes.append("path missing; initialize submodules before absorption review")
        else:
            current = git_output(upstream_path, ["rev-parse", "HEAD"])
            is_git_repo = current is not None
            if not is_git_repo:
                notes.append("path exists but is not a git checkout")
            else:
                lock_available = run_git(upstream_path, ["cat-file", "-e", f"{locked}^{{commit}}"]).returncode == 0
                dirty_status = git_output(upstream_path, ["status", "--short"]) or ""
                status_lines = [line for line in dirty_status.splitlines() if line.strip()]
                dirty = bool(status_lines)
                drift = bool(current and locked and current != locked)

                if dirty:
                    notes.append("submodule working tree has local changes; review before updating locks")
                if not lock_available:
                    notes.append("locked commit is not available in the local checkout")
                elif drift:
                    diff_text = git_output(upstream_path, ["diff", "--name-status", f"{locked}..HEAD"]) or ""
                    changed_files = parse_name_status(diff_text, name)
                else:
                    notes.append("upstream lock matches current checkout")

                if remote_commit:
                    remote_drift = remote_commit != current
                    locked_remote_drift = remote_commit != locked
                    reviewed_remote_drift = remote_commit != reviewed
                    if remote_drift:
                        notes.append("remote head differs from current checkout")
                    else:
                        notes.append("remote head matches current checkout")
                    if reviewed_remote_drift:
                        notes.append("remote head has not been reviewed")
                        if fetch_remote_details and reviewed:
                            (
                                remote_compare_status,
                                remote_ahead_by,
                                remote_compare_url,
                                remote_commits,
                                remote_changed_files,
                                remote_detail_error,
                            ) = github_compare(meta.get("repo", ""), reviewed, remote_commit, name)
                            remote_detail_source = "github_compare"
                            if remote_detail_error:
                                api_error = remote_detail_error
                                try:
                                    remote_commits, remote_changed_files = local_compare(
                                        upstream_path, reviewed, remote_commit, name
                                    )
                                except (ValueError, OSError, subprocess.SubprocessError):
                                    remote_recommendation = "manual_review"
                                    notes.append("complete local comparison unavailable; details remain incomplete")
                                else:
                                    remote_detail_source = "local_git"
                                    remote_detail_error = None
                                    remote_compare_status = "ahead"
                                    remote_ahead_by = len(remote_commits)
                                    notes.append(api_error + "; recovered complete range from local Git")
                            if remote_detail_error:
                                notes.append(remote_detail_error)
                            else:
                                remote_recommendation = recommend_remote_decision(remote_changed_files)

        reports.append(
            UpstreamReport(
                name=name,
                repo=meta.get("repo", ""),
                path=rel_path,
                license=meta.get("license", ""),
                locked_commit=locked,
                reviewed_commit=reviewed,
                absorbed_commit=absorbed,
                cumulative_status=cumulative_status,
                reviewed_through_commit=reviewed,
                behavior_absorbed_through_commit=absorbed,
                latest_range_base_commit=latest_range_base,
                latest_range_head_commit=latest_range_head,
                latest_range_status=latest_range_status,
                reviewed_at=reviewed_at,
                decision=decision,
                decision_notes=decision_notes,
                current_commit=current,
                remote_commit=remote_commit,
                remote_ref=remote_ref,
                exists=exists,
                is_git_repo=is_git_repo,
                lock_commit_available=lock_available,
                drift=drift,
                remote_drift=remote_drift,
                locked_remote_drift=locked_remote_drift,
                reviewed_remote_drift=reviewed_remote_drift,
                remote_compare_status=remote_compare_status,
                remote_ahead_by=remote_ahead_by,
                remote_compare_url=remote_compare_url,
                remote_recommendation=remote_recommendation,
                remote_commits=remote_commits,
                remote_changed_files=remote_changed_files,
                remote_detail_error=remote_detail_error,
                dirty=dirty,
                status=status_lines,
                changed_files=changed_files,
                notes=notes,
                remote_detail_source=remote_detail_source,
            )
        )

    return reports


def print_text(reports: list[UpstreamReport]) -> None:
    for index, report in enumerate(reports):
        if index:
            print()
        print(f"{report.name}:")
        print(f"  repo: {report.repo}")
        print(f"  path: {report.path}")
        print(f"  license: {report.license}")
        print(f"  locked_commit: {report.locked_commit}")
        print(f"  reviewed_commit: {report.reviewed_commit or 'unavailable'}")
        print(f"  absorbed_commit: {report.absorbed_commit or 'unavailable'}")
        print(f"  cumulative_status: {report.cumulative_status or 'unavailable'}")
        print(
            "  behavior_absorbed_through_commit: "
            f"{report.behavior_absorbed_through_commit or 'unavailable'}"
        )
        print(
            "  latest_range: "
            f"{report.latest_range_base_commit or 'unavailable'}.."
            f"{report.latest_range_head_commit or 'unavailable'}"
        )
        print(f"  latest_range_status: {report.latest_range_status or 'unavailable'}")
        print(f"  reviewed_at: {report.reviewed_at or 'unavailable'}")
        print(f"  legacy_decision: {report.decision or 'unavailable'}")
        if report.decision_notes:
            print(f"  decision_notes: {report.decision_notes}")
        print(f"  current_commit: {report.current_commit or 'unavailable'}")
        if report.remote_commit:
            print(f"  remote_ref: {report.remote_ref}")
            print(f"  remote_commit: {report.remote_commit}")
        print(f"  drift: {str(report.drift).lower()}")
        if report.remote_drift is not None:
            print(f"  remote_drift: {str(report.remote_drift).lower()}")
            print(f"  locked_remote_drift: {str(report.locked_remote_drift).lower()}")
            print(f"  reviewed_remote_drift: {str(report.reviewed_remote_drift).lower()}")
        if report.remote_compare_status:
            print(f"  remote_compare_status: {report.remote_compare_status}")
            print(f"  remote_ahead_by: {report.remote_ahead_by}")
            print(f"  remote_recommendation: {report.remote_recommendation}")
            print(f"  remote_compare_url: {report.remote_compare_url}")
        if report.remote_detail_source:
            print(f"  remote_detail_source: {report.remote_detail_source}")
        if report.remote_detail_error:
            print(f"  remote_detail_error: {report.remote_detail_error}")
        print(f"  dirty: {str(report.dirty).lower()}")
        for note in report.notes:
            print(f"  note: {note}")

        if report.status:
            print("  working_tree_status:")
            for line in report.status:
                print(f"    {line}")

        if report.changed_files:
            counts: dict[str, int] = {}
            for changed in report.changed_files:
                counts[changed.category] = counts.get(changed.category, 0) + 1
            print("  changed_file_counts:")
            for category in ("candidate_absorb", "manual_review", "repository_operations_only", "provenance_only"):
                if category in counts:
                    print(f"    {category}: {counts[category]}")
            print("  changed_files:")
            for changed in report.changed_files:
                print(f"    {changed.status}\t{changed.category}\t{changed.path}")

        if report.remote_commits:
            print("  remote_commits:")
            for commit in report.remote_commits:
                print(f"    {commit.sha[:12]}\t{commit.date}\t{commit.title}")
        if report.remote_changed_files:
            print("  remote_changed_files:")
            for changed in report.remote_changed_files:
                print(f"    {changed.status}\t{changed.category}\t{changed.path}")


def render_markdown_summary(reports: list[UpstreamReport]) -> str:
    lines = [
        "# design-craft upstream audit",
        "",
        "| Upstream | Cumulative | Latest range | Reviewed | Remote | State | Recommendation |",
        "|---|---|---|---|---|---|---|",
    ]
    for report in reports:
        state = "current"
        if report.reviewed_remote_drift is True:
            state = "review required"
        elif report.remote_commit is None:
            state = "remote unavailable"
        lines.append(
            "| {name} | {cumulative} | {latest} | `{reviewed}` | `{remote}` | {state} | {recommendation} |".format(
                name=report.name,
                cumulative=report.cumulative_status or "unavailable",
                latest=report.latest_range_status or "unavailable",
                reviewed=(report.reviewed_commit or "unavailable")[:12],
                remote=(report.remote_commit or "unavailable")[:12],
                state=state,
                recommendation=report.remote_recommendation or "none",
            )
        )

    for report in reports:
        if report.reviewed_remote_drift is not True:
            continue
        lines.extend(["", f"## {report.name}"])
        if report.remote_compare_url:
            lines.append(f"- Compare: {report.remote_compare_url}")
        if report.remote_detail_source:
            lines.append(f"- Detail source: {report.remote_detail_source}")
        for note in report.notes:
            if "recovered complete range" in note:
                lines.append(f"- Coverage: {note}")
        if report.remote_detail_error:
            lines.append(f"- Detail error: {report.remote_detail_error}")
        if report.remote_commits:
            lines.append("- Commits:")
            for commit in report.remote_commits:
                lines.append(f"  - `{commit.sha[:12]}` {commit.title}")
        if report.remote_changed_files:
            lines.append("- Changed files:")
            for changed in report.remote_changed_files:
                lines.append(f"  - `{changed.status}` `{changed.category}` `{changed.path}`")
    return "\n".join(lines) + "\n"


def run_self_check() -> list[str]:
    errors: list[str] = []
    if github_repo_slug("https://github.com/emilkowalski/skills.git") != "emilkowalski/skills":
        errors.append("failed to parse HTTPS GitHub repository")
    if github_repo_slug("git@github.com:pbakaus/impeccable.git") != "pbakaus/impeccable":
        errors.append("failed to parse SSH GitHub repository")
    cases = {
        "README.md": "provenance_only",
        "scripts/github/sheriff.mjs": "repository_operations_only",
        "tests/github-sheriff.test.mjs": "repository_operations_only",
        "skills/apple-design/SKILL.md": "candidate_absorb",
    }
    for path, expected in cases.items():
        observed = categorize_changed_file("emilkowalski-skills", path)
        if observed != expected:
            errors.append(f"{path}: expected {expected}, got {observed}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report pinned upstream drift and optional GitHub compare details without modifying submodule checkouts."
    )
    parser.add_argument("--root", default=str(ROOT), help="design-craft repo root")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--remote", action="store_true", help="Also check remote HEAD/main/master with git ls-remote")
    parser.add_argument(
        "--remote-details",
        action="store_true",
        help="For unreviewed GitHub ranges, include commit titles and changed paths from the compare API",
    )
    parser.add_argument("--summary-file", help="Write a concise Markdown audit summary to this path")
    parser.add_argument("--check", action="store_true", help="Run offline parser/classification self-checks")
    parser.add_argument(
        "--fail-on-unreviewed",
        action="store_true",
        help="Exit non-zero when remote HEAD differs from reviewed_commit or lock review metadata is incomplete",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if args.check:
        errors = run_self_check()
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        return 0
    try:
        reports = build_report(
            root,
            check_remote=args.remote or args.remote_details,
            fetch_remote_details=args.remote_details,
        )
    except Exception as exc:
        print(f"failed to build upstream absorption report: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([asdict(report) for report in reports], ensure_ascii=False, indent=2))
    else:
        print_text(reports)
    if args.summary_file:
        summary_path = Path(args.summary_file).expanduser()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(render_markdown_summary(reports), encoding="utf-8")
    if args.fail_on_unreviewed:
        invalid = [
            report.name
            for report in reports
            if not report.reviewed_commit
            or not report.reviewed_at
            or report.cumulative_status not in CUMULATIVE_STATUSES
            or report.latest_range_status not in LATEST_RANGE_STATUSES
            or report.decision
            != LEGACY_DECISION_BY_CUMULATIVE_STATUS.get(report.cumulative_status)
            or (
                report.cumulative_status != "deferred"
                and not report.behavior_absorbed_through_commit
            )
            or report.latest_range_head_commit != report.reviewed_through_commit
            or report.reviewed_remote_drift is True
        ]
        if invalid:
            print("unreviewed upstream state: " + ", ".join(invalid), file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
