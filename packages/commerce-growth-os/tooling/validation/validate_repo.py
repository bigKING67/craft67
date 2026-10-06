#!/usr/bin/env python3
"""Validate the multi-skill repository, bundles, routing, and regression suites."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.manifest import ManifestError, load_manifest

MANIFEST = ROOT / "skill-pack.json"
BUILDER = ROOT / "tooling/build/build_skill_bundles.py"
ROUTING = ROOT / "tooling/validation/check_routing.py"
FALLBACK_SKILL_VALIDATOR = ROOT / "tooling/validation/quick_validate_skill.py"
RELEASE_CHECK = ROOT / "tooling/validation/check_release.py"
SCORER = ROOT / "tooling/evaluation/score_eval.py"
LINTER = ROOT / "tooling/evaluation/lint_answer.py"
SOURCE_CHECKER = ROOT / "tooling/evaluation/check_source_registry.py"
ECONOMICS_TEST = ROOT / "skills/commerce/commerce-commercial-strategy/scripts/test_unit_economics.py"
INSTALL_TEST = ROOT / "tooling/installation/test_install_skill_pack.py"
STRUCTURED_JUDGE = ROOT / "tooling/evaluation/run_structured_judge.py"
FORWARD_ROUTING_EVAL = ROOT / "tooling/evaluation/run_forward_routing_eval.py"
EXECUTION_EVAL = ROOT / "tooling/evaluation/run_execution_eval.py"
QUALITY_REGRESSION = ROOT / "tooling/evaluation/run_quality_regression.py"
CURRENTNESS_AUDIT = ROOT / "tooling/evaluation/audit_source_registry.py"
SKILL_PACK_DOCTOR = ROOT / "tooling/validation/skill_pack_doctor.py"
RELEASE_PACKAGER = ROOT / "tooling/build/package_release.py"
RELEASE_VERIFIER = ROOT / "tooling/build/verify_release.py"
CANONICAL_SOURCE_DIRS = (".github", "eval", "scripts", "shared", "skills", "tooling")
CANONICAL_ROOT_FILES = (".gitignore", "README.md", "skill-pack.json")


class ValidationError(RuntimeError):
    pass


def run(command: list[str], *, cwd: Path = ROOT, label: str | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        raise ValidationError(f"{label or command[0]} failed:\n{detail}")
    if label:
        print(f"passed: {label}")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValidationError(f"invalid frontmatter: {path}")
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def validate_sources(manifest: dict[str, Any]) -> None:
    names: set[str] = set()
    for skill in manifest["skills"]:
        name = skill["name"]
        if name in names:
            raise ValidationError(f"duplicate skill: {name}")
        names.add(name)
        source = ROOT / skill["source"]
        skill_md = source / "SKILL.md"
        agents = source / "agents/openai.yaml"
        if not skill_md.is_file() or not agents.is_file():
            raise ValidationError(f"missing skill entry files: {name}")
        frontmatter = parse_frontmatter(skill_md)
        if frontmatter.get("name") != name:
            raise ValidationError(f"frontmatter name mismatch: {name}")
        description = frontmatter.get("description", "")
        if not description:
            raise ValidationError(f"missing description: {name}")
        if len(description) > 500:
            raise ValidationError(f"description exceeds 500 characters: {name}")
        lines = skill_md.read_text(encoding="utf-8").splitlines()
        if len(lines) > 180:
            raise ValidationError(f"SKILL.md exceeds 180 lines: {name} ({len(lines)})")
        if "../" in skill_md.read_text(encoding="utf-8"):
            raise ValidationError(f"runtime parent-path dependency in {name}")
        targets: set[str] = set()
        for resource in skill.get("resources", []):
            source_path = ROOT / resource["source"]
            target = resource["target"]
            if not source_path.exists():
                raise ValidationError(f"missing resource for {name}: {resource['source']}")
            if target in targets:
                raise ValidationError(f"duplicate resource target for {name}: {target}")
            targets.add(target)

    if (ROOT / "SKILL.md").exists():
        raise ValidationError("multi-skill repository must not expose a root SKILL.md")


def canonical_source_files(root: Path) -> list[Path]:
    files = [root / name for name in CANONICAL_ROOT_FILES if (root / name).is_file()]
    for directory in CANONICAL_SOURCE_DIRS:
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if "__pycache__" in relative.parts or relative.parts[:2] == ("eval", "answers"):
                continue
            files.append(path)
    return sorted(set(files))


def validate_no_placeholders(root: Path = ROOT) -> None:
    pattern = re.compile(r"TODO|TBD|FIXME|utm_source=chatgpt\.com")
    excluded = Path("tooling/validation/validate_repo.py")
    hits: list[str] = []
    for path in canonical_source_files(root):
        relative = path.relative_to(root)
        if relative == excluded:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if pattern.search(line):
                hits.append(f"{relative}:{line_number}:{line}")
                if len(hits) >= 50:
                    break
        if len(hits) >= 50:
            break
    if hits:
        detail = "\n".join(hits)
        raise ValidationError(f"unresolved placeholder or forbidden source:\n{detail}")


def validate_placeholder_scope_self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="placeholder-scope-self-test-") as temp:
        root = Path(temp)
        ignored_answer = root / "eval/answers/ignored.txt"
        ignored_answer.parent.mkdir(parents=True)
        ignored_answer.write_text("TODO is allowed in generated evidence", encoding="utf-8")
        validate_no_placeholders(root)

        canonical_source = root / "skills/example/SKILL.md"
        canonical_source.parent.mkdir(parents=True)
        canonical_source.write_text("TODO must fail in canonical source", encoding="utf-8")
        try:
            validate_no_placeholders(root)
        except ValidationError:
            return
        raise AssertionError("canonical placeholder should fail validation")


def validate_reference_navigation() -> None:
    roots = [ROOT / "shared", ROOT / "skills"]
    for base in roots:
        for path in base.rglob("*.md"):
            if path.name == "SKILL.md":
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) > 100 and "## Contents" not in lines:
                raise ValidationError(f"long reference is missing Contents navigation: {path.relative_to(ROOT)}")


def validate_overlay_ownership() -> None:
    platform_root = ROOT / "shared/platform-overlays"
    expected_platform_domains = {"analytics", "content-social", "growth-performance", "operations"}
    actual_platform_domains = {path.name for path in platform_root.iterdir() if path.is_dir()}
    if actual_platform_domains != expected_platform_domains:
        raise ValidationError(
            f"platform overlay domains mismatch: expected {sorted(expected_platform_domains)}, "
            f"got {sorted(actual_platform_domains)}"
        )
    if list(platform_root.glob("*.md")):
        raise ValidationError("platform overlays must be owned by a professional domain directory")

    category_root = ROOT / "shared/category-overlays"
    category_files = sorted(category_root.glob("*.md"))
    if len(category_files) != 10:
        raise ValidationError(f"expected 10 category overlays, got {len(category_files)}")
    forbidden = re.compile(
        r"^## (SKU matrix|Channel split|Creator and content fit|Keyword directions|"
        r"Douyin|Tmall|Talent livestream)|Qianchuan|Juguang|Wanxiangtai",
        re.MULTILINE,
    )
    for path in category_files:
        if forbidden.search(path.read_text(encoding="utf-8")):
            raise ValidationError(f"category overlay duplicates specialist or platform methods: {path.name}")


def validate_bundle_links(bundle_root: Path, manifest: dict[str, Any]) -> None:
    path_pattern = re.compile(r"`((?:references|scripts)/[^`]+)`")
    for skill in manifest["skills"]:
        bundle = bundle_root / skill["name"]
        skill_text = (bundle / "SKILL.md").read_text(encoding="utf-8")
        for relative in path_pattern.findall(skill_text):
            candidate = bundle / relative
            if relative.endswith("/"):
                if not candidate.is_dir():
                    raise ValidationError(f"missing bundled directory for {skill['name']}: {relative}")
            elif not candidate.is_file():
                raise ValidationError(f"missing bundled file for {skill['name']}: {relative}")


def validate_bundle_isolation(bundle_root: Path) -> None:
    expected_platform_files = {
        "commerce-operations": 7,
        "commerce-analytics": 7,
        "content-creative-social-marketing": 6,
        "growth-performance-lifecycle-marketing": 7,
    }
    for skill_name, expected_count in expected_platform_files.items():
        platform_root = bundle_root / skill_name / "references/platform-overlays"
        files = list(platform_root.glob("*.md"))
        directories = [path for path in platform_root.iterdir() if path.is_dir()]
        if len(files) != expected_count or directories:
            raise ValidationError(
                f"platform bundle isolation failed for {skill_name}: "
                f"expected {expected_count} direct files, got {len(files)} files and {len(directories)} directories"
            )

    marketing_platforms = bundle_root / "consumer-marketing-os/references/platform-overlays"
    if {path.name for path in marketing_platforms.iterdir() if path.is_dir()} != {
        "content-social",
        "growth-performance",
    }:
        raise ValidationError("consumer-marketing-os must bundle only content-social and growth-performance overlays")

    for skill_name in ("commerce-commercial-strategy", "brand-strategy-communications"):
        if (bundle_root / skill_name / "references/platform-overlays").exists():
            raise ValidationError(f"{skill_name} must not bundle platform overlays")


def main() -> int:
    try:
        manifest = load_manifest(MANIFEST)
        validate_sources(manifest)
        validate_no_placeholders()
        validate_placeholder_scope_self_test()
        validate_reference_navigation()
        validate_overlay_ownership()

        with tempfile.TemporaryDirectory(prefix="skill-pack-validation-") as temp:
            run([sys.executable, str(BUILDER), "--output", temp], label="8 self-contained skill bundles")
            validate_bundle_links(Path(temp), manifest)
            print("passed: bundled reference links")
            validate_bundle_isolation(Path(temp))
            print("passed: bundle domain isolation")
            for skill in manifest["skills"]:
                run([sys.executable, str(FALLBACK_SKILL_VALIDATOR), str(Path(temp) / skill["name"])])
            print("passed: dependency-free Skill validator")

        run([sys.executable, str(ROUTING)], label="static routing-hint compatibility")
        run([sys.executable, str(RELEASE_CHECK)], label="manifest/tag release contract")
        run([sys.executable, str(STRUCTURED_JUDGE), "--validate-only"], label="structured judge contract")
        run([sys.executable, str(STRUCTURED_JUDGE), "--cases", str(ROOT / "eval/structured-judge/economics-regression-cases.json"), "--validate-only"], label="paired economics regression contract")
        run([sys.executable, "-B", str(ROOT / "tooling/evaluation/test_live_runtime.py")], label="live runtime provenance and cleanup regression")
        run([sys.executable, "-B", str(ROOT / "tooling/evaluation/test_app_server_runtime.py")], label="App Server explicit input and isolation regression")
        run([sys.executable, "-B", str(FORWARD_ROUTING_EVAL), "--self-test"], label="live selection runner self-test")
        run([sys.executable, "-B", str(EXECUTION_EVAL), "--self-test"], label="explicit execution runner self-test")
        run([sys.executable, "-B", str(STRUCTURED_JUDGE), "--self-test"], label="structured judge runner self-test")
        run([sys.executable, "-B", str(QUALITY_REGRESSION), "--self-test"], label="quality regression orchestrator self-test")
        run([sys.executable, "-B", str(CURRENTNESS_AUDIT), "--self-test"], label="official-source reachability self-test")
        run([sys.executable, "-B", str(SKILL_PACK_DOCTOR), "--self-test"], label="skill pack doctor self-test")
        run([sys.executable, "-B", str(RELEASE_PACKAGER), "--self-test"], label="deterministic release packaging self-test")
        run([sys.executable, "-B", str(RELEASE_VERIFIER), "--self-test"], label="offline release verifier self-test")
        run([sys.executable, str(SCORER), "--self-test"], label="legacy scorer self-test")
        run([sys.executable, str(SCORER), "--answer-dir", str(ROOT / "eval/golden-answers")], label="14 legacy golden answers")
        run([sys.executable, str(LINTER), "--self-test"], label="answer linter self-test")
        run([
            sys.executable,
            str(LINTER),
            "--answer-dir",
            str(ROOT / "eval/golden-answers"),
            "--cases",
            str(ROOT / "eval/cases.json"),
            "--json",
        ], label="14 legacy answer-quality contracts")
        run([
            sys.executable,
            str(SCORER),
            "--cases",
            str(ROOT / "eval/marketing/cases.json"),
            "--answer-dir",
            str(ROOT / "eval/marketing/golden-answers"),
        ], label="8 marketing golden answers")
        run([sys.executable, str(SOURCE_CHECKER), "--self-test"], label="source registry self-test")
        run([sys.executable, str(SOURCE_CHECKER), str(ROOT / "shared/currentness/currentness-official-sources.md")], label="official source registry")
        run([sys.executable, "-B", str(ECONOMICS_TEST)], cwd=ECONOMICS_TEST.parent, label="unit economics regression")
        run([sys.executable, "-B", str(INSTALL_TEST)], cwd=INSTALL_TEST.parent, label="transactional installer regression")
        print(f"repository validation passed: {len(manifest['skills'])} skills")
        return 0
    except (ValidationError, ManifestError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"validate_repo error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
