#!/usr/bin/env python3
"""Deterministic design-craft source-completeness scorer."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


WEIGHTS = {
    "Visual Judgment": 20,
    "Product Fit": 15,
    "Engineering Quality": 15,
    "Performance": 15,
    "Architecture": 15,
    "Project Structure": 10,
    "Validation Evidence": 10,
}


@dataclass
class Dimension:
    name: str
    score: int
    weight: int
    evidence: list[str]
    gaps: list[str]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def has(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def runtime_text(root: Path, name: str) -> str:
    return read_text(root / "skills/design-craft/scripts" / name)


def active_product_ui_score_paths(root: Path) -> list[Path]:
    """Score only active project-neutral calibration cases.

    Historical project-specific cases can remain in the repo for provenance, but
    source scoring must not depend on or read them as active evidence.
    """

    rel_paths = [
        "evals/product-ui-taste/material-ops-home/score.json",
        "evals/product-ui-taste/before-after/generic-review-workbench-local-l4/score.before.json",
        "evals/product-ui-taste/before-after/generic-review-workbench-local-l4/score.after.json",
        "evals/product-ui-taste/before-after/ops-dashboard-decision-surface-l4/score.before.json",
        "evals/product-ui-taste/before-after/ops-dashboard-decision-surface-l4/score.after.json",
    ]
    return [root / rel_path for rel_path in rel_paths if (root / rel_path).is_file()]


def iter_product_ui_score_entries(root: Path):
    for score_path in active_product_ui_score_paths(root):
        try:
            payload = json.loads(score_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        entries = payload.get("cases")
        if entries is None:
            entries = [payload]
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            yield score_path, payload, entry


def has_product_ui_l2_case(root: Path) -> bool:
    for _score_path, payload, entry in iter_product_ui_score_entries(root):
        level = entry.get("evidence_level") or payload.get("evidence_level")
        if level in {"L2", "L3", "L4"} and entry.get("screenshot_sha256"):
            return True
    return False


def has_product_ui_l3_case(root: Path) -> bool:
    for _score_path, payload, entry in iter_product_ui_score_entries(root):
        level = entry.get("evidence_level") or payload.get("evidence_level")
        if level in {"L3", "L4"} and entry.get("responsive_viewports") and entry.get("state_checks"):
            return True
    return False


def has_product_ui_l4_before_after_case(root: Path) -> bool:
    case_ids = [
        "generic-review-workbench-local-l4",
        "ops-dashboard-decision-surface-l4",
    ]
    for case_id in case_ids:
        case_dir = root / "evals/product-ui-taste/before-after" / case_id
        if not (
            (case_dir / "screenshots.json").is_file()
            and (case_dir / "score.before.json").is_file()
            and (case_dir / "score.after.json").is_file()
        ):
            return False
    return True


def infer_root(target: Path) -> Path:
    target = target.expanduser().resolve()
    if target.is_file():
        target = target.parent
    if (target / "skills/design-craft/SKILL.md").is_file():
        return target
    if target.name == "design-craft" and (target / "SKILL.md").is_file():
        return target.parents[1]
    for parent in [target, *target.parents]:
        if (parent / "skills/design-craft/SKILL.md").is_file():
            return parent
    return target


def check_command(command: list[str], cwd: Path) -> bool:
    resolved_command = list(command)
    if resolved_command and resolved_command[0] == "bash":
        configured_bash = os.environ.get("DESIGN_CRAFT_BASH", "").strip()
        if configured_bash:
            resolved_command[0] = configured_bash
    try:
        result = subprocess.run(
            resolved_command,
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception:
        return False
    return result.returncode == 0


def score_dimension(name: str, weight: int, checks: list[tuple[bool, str, str]]) -> Dimension:
    passed = [label for ok, label, _gap in checks if ok]
    gaps = [gap for ok, _label, gap in checks if not ok]
    score = round(weight * len(passed) / len(checks)) if checks else 0
    return Dimension(name=name, score=score, weight=weight, evidence=passed, gaps=gaps)


def build_score(root: Path, run_smoke: bool) -> list[Dimension]:
    skill = read_text(root / "skills/design-craft/SKILL.md")
    validation = read_text(root / "skills/design-craft/references/validation-contract.md")
    design_system = read_text(root / "skills/design-craft/references/design-system-contract.md")
    system_review = read_text(root / "skills/design-craft/references/system-review.md")
    component_primitives = read_text(
        root / "skills/design-craft/references/component-primitive-selection.md"
    )
    component_primitive_expected = read_text(
        root
        / "evals/product-ui-taste/component-primitive-selection/decision.expected.md"
    )
    prototype_workflow = read_text(
        root / "skills/design-craft/references/prototype-workflow.md"
    )
    product_review = read_text(root / "skills/design-craft/references/product-ui-taste-review.md")
    taste_calibration = read_text(root / "skills/design-craft/references/taste-score-calibration.md")
    foundational_principles = read_text(root / "skills/design-craft/references/foundational-visual-principles.md")
    design_moves = read_text(root / "skills/design-craft/references/design-move-library.md")
    motion_quality = read_text(root / "skills/design-craft/references/motion-quality.md")
    motion_planning = read_text(root / "skills/design-craft/references/motion-audit-planning.md")
    motion_vocabulary = read_text(root / "skills/design-craft/references/motion-vocabulary.md")
    browser_evidence_helper = runtime_text(root, "design_craft_browser_evidence.py")
    route_helper = runtime_text(root, "design_craft_route.sh") + runtime_text(
        root, "design_craft_route_runtime.py"
    ) + read_text(root / "skills/design-craft/lib/design_craft/route_contract.py")
    audit_helper = runtime_text(root, "design_craft_audit.sh")
    report = read_text(root / "skills/design-craft/references/report-quality.md")
    surface = read_text(root / "skills/design-craft/references/surface-playbooks.md")
    source_map = read_text(root / "skills/design-craft/references/source-map.md")

    detector_smoke = False
    score_smoke = False
    pass_smoke = False
    critique_smoke = False
    motion_smoke = False
    motion_plan_smoke = False
    seed_smoke = False
    taste_review_smoke = False
    prototype_smoke = False
    system_review_smoke = False
    reference_smoke = False
    if run_smoke:
        detector_smoke = check_command(
            ["bash", "skills/design-craft/scripts/design_craft_detect.sh", "--target", "skills/design-craft", "--json-only"],
            root,
        )
        score_smoke = check_command(
            [sys.executable, "scripts/design_craft_score.py", "--target", str(root), "--no-smoke", "--json"],
            root,
        )
        pass_smoke = check_command(
            ["bash", "skills/design-craft/scripts/design_craft_pass.sh", "--target", "skills/design-craft", "--mode", "audit", "--skip-route", "--skip-score"],
            root,
        )
        critique_smoke = check_command(
            ["bash", "skills/design-craft/scripts/design_craft_audit.sh", "--target", "skills/design-craft", "--mode", "critique", "--skip-route", "--skip-score"],
            root,
        )
        motion_smoke = check_command(
            ["bash", "skills/design-craft/scripts/design_craft_pass.sh", "--target", "skills/design-craft", "--mode", "motion", "--skip-route", "--skip-score"],
            root,
        )
        motion_plan_smoke = check_command(
            [
                sys.executable,
                "skills/design-craft/scripts/design_craft_motion_plan.py",
                "--target",
                str(root),
                "--title",
                "Retarget the sheet from its presentation value",
                "--severity",
                "P1",
                "--category",
                "interruptibility",
                "--dry-run",
            ],
            root,
        )
        seed_smoke = check_command(
            ["bash", "skills/design-craft/scripts/design_craft_seed_design.sh", "--target", "skills/design-craft", "--dry-run"],
            root,
        )
        taste_review_smoke = check_command(
            ["bash", "skills/design-craft/scripts/design_craft_taste_review.sh", "--target", "skills/design-craft", "--context", "score smoke", "--evidence-level", "L0"],
            root,
        )
        prototype_smoke = check_command(
            [
                "bash",
                "skills/design-craft/scripts/design_craft_pass.sh",
                "--target",
                "skills/design-craft",
                "--mode",
                "prototype",
                "--skip-route",
                "--skip-detector",
                "--skip-score",
            ],
            root,
        )
        system_review_smoke = check_command(
            [
                "bash",
                "skills/design-craft/scripts/design_craft_pass.sh",
                "--target",
                "skills/design-craft",
                "--mode",
                "system-review",
                "--skip-route",
                "--skip-detector",
                "--skip-score",
            ],
            root,
        )
        reference_smoke = check_command(
            [
                sys.executable,
                "skills/design-craft/scripts/design_craft_reference.py",
                "--help",
            ],
            root,
        )

    return [
        score_dimension(
            "Visual Judgment",
            WEIGHTS["Visual Judgment"],
            [
                (has(root, "skills/design-craft/references/visual-judgment.md"), "visual-judgment reference exists", "Add visual-judgment reference."),
                ("anti-slop" in skill.lower() or "anti-slop" in read_text(root / "skills/design-craft/references/visual-judgment.md").lower(), "anti-slop encoded", "Encode anti-slop visual judgment."),
                ("design read" in skill.lower(), "design read required", "Require a concise design read for major visual work."),
                ("generic AI tells" in skill or "generic" in read_text(root / "skills/design-craft/references/visual-judgment.md").lower(), "generic-output guard present", "Add generic-output failure modes."),
                (has(root, "skills/design-craft/references/product-ui-taste-review.md"), "product UI taste review reference exists", "Add product UI taste review reference."),
                (has(root, "skills/design-craft/references/foundational-visual-principles.md"), "foundational visual principles reference exists", "Add compact CRAP/Gestalt visual principles."),
                ("Proximity" in foundational_principles and "Contrast" in foundational_principles, "foundational principles cover CRAP anchors", "Cover proximity, alignment, repetition, and contrast."),
                (has(root, "skills/design-craft/references/design-move-library.md"), "design move library exists", "Add a design move library for actionable redesign guidance."),
                ("Dashboard card soup" in design_moves and "Generic AI landing page" in design_moves, "design moves cover dashboard and landing repairs", "Cover concrete dashboard and landing design moves."),
                ("100-point score" in product_review, "100-point UI taste score present", "Add a concrete product UI scoring rubric."),
                ("Output contract" in product_review, "product UI review output contract present", "Add a structured product UI review output contract."),
                (has(root, "skills/design-craft/references/taste-score-calibration.md"), "taste score calibration reference exists", "Add taste score calibration examples."),
                ("Evidence levels" in taste_calibration, "taste evidence levels calibrated", "Define evidence levels for screenshot/browser taste scores."),
                (has(root, "skills/design-craft/references/intent-map.md"), "intent map reference exists", "Add an intent map for subjective frontend requests."),
                (has(root, "skills/design-craft/references/motion-quality.md"), "motion quality reference exists", "Add a motion-quality reference."),
                (has(root, "skills/design-craft/references/motion-audit-planning.md"), "motion audit-to-plan reference exists", "Add a codebase-wide motion audit and plan workflow."),
                ("Phase 1: motion recon" in motion_planning and "Phase 4: write executable plans" in motion_planning, "motion recon-to-plan workflow present", "Document recon, vetted prioritization, and executable motion plans."),
                (has(root, "skills/design-craft/templates/motion-plan/plan.md"), "motion implementation-plan template exists", "Add a self-contained motion plan template."),
                (has(root, "skills/design-craft/references/motion-vocabulary.md"), "motion vocabulary reference exists", "Add a motion-vocabulary reference."),
                ("scale(0)" in motion_quality and "transition-all" in motion_quality, "motion anti-patterns encoded", "Encode motion anti-patterns such as scale(0) and transition-all."),
                ("Origin-aware animation" in motion_vocabulary, "origin-aware motion vocabulary present", "Add origin-aware animation vocabulary."),
            ],
        ),
        score_dimension(
            "Product Fit",
            WEIGHTS["Product Fit"],
            [
                ("authority order" in skill.lower(), "authority order documented", "Document authority order."),
                ("DESIGN.md" in skill, "DESIGN.md precedence present", "Make DESIGN.md/style authority explicit."),
                ("report" in report.lower(), "report/data surface covered", "Add report/data-surface grammar."),
                ("surface-specific" in surface.lower() or "surface playbooks" in surface.lower(), "surface playbooks present", "Cover surface-specific product jobs."),
                (
                    "## Chart or report intent" in report
                    and "Count charts by independent conclusions" in report
                    and "two or three candidates" in report,
                    "project-neutral chart intent, selection, and composition contract present",
                    "Add chart/report scope separation plus evidence-led chart selection and composition.",
                ),
                (
                    "Lieflat Charts" in source_map
                    and "external reference only" in source_map
                    and "No source, templates, catalogs, tokens, media, or runtime" in source_map,
                    "restricted chart reference provenance and redistribution boundary present",
                    "Map the fixed chart reference without importing its restricted payload.",
                ),
                ("candidate_skills" in skill, "route candidate semantics present", "Separate route candidates from selected skills."),
                (has(root, "skills/design-craft/references/design-system-contract.md"), "design-system contract exists", "Add design-system contract reference."),
                (has(root, "skills/design-craft/references/component-primitive-selection.md"), "component primitive selection contract exists", "Add a framework-neutral component primitive decision contract."),
                ("keep | adopt | migrate | defer" in component_primitives, "component primitive decisions preserve project authority", "Record keep, adopt, migrate, or defer before changing primitive authority."),
                (
                    "Base UI is a supported project choice" in component_primitives
                    and "Base UI-only universal prescription" in component_primitives,
                    "Base UI support is conditional rather than exclusive",
                    "Support Base UI when project evidence selects it without imposing a universal migration.",
                ),
                (
                    has(root, "skills/design-craft/templates/developer-product/design.md")
                    and has(root, "skills/design-craft/templates/developer-product/design.dark.md"),
                    "original developer-product seed templates bundled",
                    "Bundle original light/dark developer-product seed templates.",
                ),
                (
                    "templates/developer-product/design.md" in skill
                    and "templates/developer-product/design.dark.md" in skill,
                    "developer-product seed routed from SKILL.md",
                    "Route the original developer-product seed templates from SKILL.md.",
                ),
                (
                    "default seed" in design_system.lower() and "developer-product" in design_system.lower(),
                    "default seed policy documented",
                    "Document when to use the bundled original developer-product seed.",
                ),
                (
                    has(root, "skills/design-craft/scripts/design_craft_seed_design.sh"),
                    "developer-product seed helper exists",
                    "Add a helper for seeding DESIGN.md from the bundled original templates.",
                ),
                (
                    "developer_product_seed_applicable" in route_helper
                    or "templates/developer-product" in route_helper,
                    "route summary reports developer-product seed applicability",
                    "Make route summaries say when the original seed is applicable.",
                ),
                ("theme parity" in design_system.lower(), "theme parity guidance present", "Cover light/dark token parity."),
                ("token layers" in design_system.lower(), "token layer guidance present", "Cover token role separation."),
                ("Page-type checks" in product_review, "page-type taste checks present", "Cover forms, tables, dashboards, modals, navigation, landing, and settings review."),
                (
                    has(root, "skills/design-craft/references/prototype-workflow.md")
                    and "ready_for_selection" in prototype_workflow
                    and "must not edit production behavior" in prototype_workflow,
                    "prototype divergence and selection boundary present",
                    "Add isolated multi-direction prototyping with an explicit selection gate.",
                ),
                ("emilkowalski-skills" in source_map, "Emil Kowalski upstream source mapped", "Map the emilkowalski/skills upstream in source-map."),
            ],
        ),
        score_dimension(
            "Engineering Quality",
            WEIGHTS["Engineering Quality"],
            [
                (has(root, "skills/design-craft/references/engineering-quality.md"), "engineering reference exists", "Add engineering-quality reference."),
                ("component" in read_text(root / "skills/design-craft/references/engineering-quality.md").lower(), "component boundary guidance present", "Add component boundary guidance."),
                ("observable" in skill.lower() or "errors" in read_text(root / "skills/design-craft/references/engineering-quality.md").lower(), "error observability covered", "Cover observable errors."),
                (has(root, "skills/design-craft/scripts/design_craft_route.sh"), "route runtime exists", "Add the canonical route runtime."),
                (has(root, "skills/design-craft/scripts/design_craft_pass.sh"), "pass runtime exists", "Add the canonical neutral pass runtime."),
                (has(root, "skills/design-craft/scripts/design_craft_detect.sh"), "detector runtime exists", "Add the canonical detector runtime."),
                (has(root, "skills/design-craft/scripts/design_craft_css_smell_scan.py"), "CSS smell scanner exists", "Add static CSS smell scanner."),
                (has(root, "skills/design-craft/scripts/design_craft_focus_audit.py"), "focus audit scanner exists", "Add static focus audit scanner."),
                (has(root, "skills/design-craft/scripts/design_craft_token_audit.py"), "token audit scanner exists", "Add token bypass scanner."),
            ],
        ),
        score_dimension(
            "Performance",
            WEIGHTS["Performance"],
            [
                (has(root, "skills/design-craft/references/performance-quality.md"), "performance reference exists", "Add performance-quality reference."),
                ("Web Vitals" in read_text(root / "skills/design-craft/references/performance-quality.md"), "Web Vitals covered", "Cover Web Vitals."),
                ("charts" in read_text(root / "skills/design-craft/references/performance-quality.md").lower(), "chart/table performance covered", "Cover chart/table performance."),
                ("measure" in skill.lower() or "baseline" in read_text(root / "skills/design-craft/references/impeccable-workflow.md").lower(), "measurement-first rule present", "Require measurement before optimization."),
                ("transform" in motion_quality and "opacity" in motion_quality, "motion performance properties covered", "Cover transform/opacity animation performance guidance."),
                ("prefers-reduced-motion" in motion_quality, "reduced-motion policy covered", "Cover reduced-motion handling for UI motion."),
            ],
        ),
        score_dimension(
            "Architecture",
            WEIGHTS["Architecture"],
            [
                (has(root, "skills/design-craft/references/architecture-quality.md"), "architecture reference exists", "Add architecture-quality reference."),
                (has(root, "upstreams.lock.json"), "upstream lock exists", "Add upstream lock file."),
                (has(root, "skills/design-craft/references/source-map.md"), "source map exists", "Add source-map reference."),
                (has(root, "scripts/upstream_absorption_report.py"), "upstream absorption report exists", "Add upstream absorption report script."),
                ("--remote-details" in read_text(root / "scripts/upstream_absorption_report.py"), "actionable remote upstream drift check exists", "Add remote commit/path detail reporting."),
                (
                    has(root, "docs/taste-skill-absorption.md")
                    and has(root, "scripts/design_craft_taste_absorption.py")
                    and has(root, "docs/impeccable-absorption.md")
                    and has(root, "scripts/design_craft_impeccable_absorption.py"),
                    "taste-skill and impeccable absorption matrices are machine-validated",
                    "Add strict capability and rejection matrices for both non-Emil upstreams.",
                ),
                (
                    "cumulative_status" in read_text(root / "upstreams.lock.json")
                    and "latest_range_status" in read_text(root / "upstreams.lock.json"),
                    "upstream cumulative and latest-range decisions are separated",
                    "Separate cumulative absorption from the latest reviewed commit range.",
                ),
                ("Open or update review issue" in read_text(root / ".github/workflows/upstream-audit.yml"), "daily upstream review issue workflow exists", "Add actionable scheduled upstream review notifications."),
                (has(root, "adapters/codex/README.md"), "Codex adapter docs exist", "Add Codex adapter docs."),
                (has(root, "adapters/codex/route-pack/README.md"), "Codex route-pack docs exist", "Add docs for Codex frontend route-pack portability."),
                (has(root, "scripts/design_craft_codex_route_pack.py"), "Codex route-pack helper exists", "Add a helper that audits or exports the local Codex frontend route pack."),
                (has(root, "adapters/cursor/README.md"), "Cursor adapter docs exist", "Add Cursor adapter docs."),
                (has(root, "adapters/claude/README.md"), "Claude adapter docs exist", "Add Claude adapter docs."),
                (has(root, "adapters/pi/README.md"), "Pi adapter docs exist", "Add Pi adapter docs."),
                (has(root, "scripts/design_craft_init_agent.sh"), "cross-agent init helper exists", "Add init helper for host-specific installs."),
                (has(root, "scripts/design_craft_doctor.sh"), "doctor helper exists", "Add doctor helper for portability checks."),
                (has(root, "skills/design-craft/COMPATIBILITY.json"), "route-pack compatibility contract exists", "Add a portable route-pack compatibility contract."),
                (has(root, "scripts/design_craft_sync_status.py"), "source/install and route-pack sync status exists", "Add a non-mutating sync status command."),
                (
                    has(root, "tools/design_craft/release/metadata.py")
                    and has(root, "tools/design_craft/release/evidence.py")
                    and has(root, "contracts/release/policy.json"),
                    "tiered release metadata and evidence contracts exist",
                    "Add explicit release levels with candidate/final metadata verification.",
                ),
                ("templates/developer-product/design.md" in source_map, "developer-product seed source map present", "Map the original developer-product templates in source-map."),
                (("data flow" in read_text(root / "skills/design-craft/references/architecture-quality.md").lower()) or ("data-flow" in read_text(root / "skills/design-craft/references/architecture-quality.md").lower()), "data-flow guidance present", "Add data-flow guidance."),
                ("migration" in read_text(root / "skills/design-craft/references/architecture-quality.md").lower(), "migration risk covered", "Add migration/compatibility guidance."),
            ],
        ),
        score_dimension(
            "Project Structure",
            WEIGHTS["Project Structure"],
            [
                (has(root, "skills/design-craft/references/project-structure.md"), "structure reference exists", "Add project-structure reference."),
                ("shared" in read_text(root / "skills/design-craft/references/project-structure.md").lower(), "shared abstraction rule present", "Define when shared abstractions are allowed."),
                ("directory" in skill.lower(), "directory governance trigger present", "Include directory governance in SKILL.md."),
                (has(root, "scripts/install_local.sh"), "installer exists", "Add local installer."),
                (has(root, "scripts/design_craft_install_verify.py"), "install parity/provenance verifier exists", "Add an install verifier."),
                (".design-craft-install.lock" in read_text(root / "scripts/install_local.sh") and "Atomic install failed" in read_text(root / "scripts/install_local.sh"), "installer is locked and atomic", "Use staging, locking, rollback, and atomic replacement."),
                (has(root, "LICENSE") and has(root, "LICENSES/Apache-2.0.txt"), "root and upstream licenses are preserved", "Add the root license and preserved upstream license texts."),
                (has(root, "scripts/design_craft_package_validate.py"), "publishable package boundary validator exists", "Add a Pi/npm package size and path validator."),
                (has(root, "scripts/design_craft_public_repo_validate.py"), "public repository privacy validator exists", "Add a repository-wide user-home path and license validator."),
                (has(root, "scripts/design_craft_workflow_validate.py"), "workflow and native runner contract validator exists", "Add a dedicated workflow pinning and native runner validator."),
                (has(root, "scripts/design_craft_lint.py") and "contract-tests:" in read_text(root / "Makefile"), "dependency-free lint and contract-test lanes exist", "Add dedicated syntax/data lint and isolated contract-test targets."),
                (
                    has(root, "tests/contract/test_installer.py")
                    and "TemporaryDirectory" in read_text(root / "tests/contract/test_installer.py"),
                    "installer integration uses isolated install roots",
                    "Verify install, locking, and rollback behavior in temporary roots.",
                ),
                (
                    set(json.loads(read_text(root / "package.json")).get("files", []))
                    == {"skills/design-craft", "LICENSE", "LICENSES", "README.md", "THIRD_PARTY_NOTICES.md", "VERSION"},
                    "package allowlist excludes repository-only content",
                    "Restrict package.json files to the canonical skill and legal metadata.",
                ),
            ],
        ),
        score_dimension(
            "Validation Evidence",
            WEIGHTS["Validation Evidence"],
            [
                (has(root, "scripts/validate.sh"), "validation script exists", "Add validation script."),
                (has(root, "scripts/design_craft_active_scope_validate.py"), "active-scope validator exists", "Add a validator that keeps active generic gates project-neutral."),
                ("browser validation" in validation.lower(), "browser validation contract present", "Document browser validation rules."),
                ("browser_screenshot_required" in validation and "browser_screenshot_ops" in validation, "screenshot evidence contract present", "Document screenshot artifact evidence rules."),
                (has(root, "skills/design-craft/references/system-review.md"), "system consistency review reference exists", "Add the two-level system consistency review contract."),
                (
                    "semantic component-family inventory" in system_review.lower()
                    and "same-state comparison" in system_review.lower()
                    and "state and theme matrix" in system_review.lower(),
                    "system review covers semantic families, same-state comparison, states, and themes",
                    "Cover semantic families, project exemplars, same-state sibling comparison, and state/theme evidence.",
                ),
                (
                    "`pass`" in system_review
                    and "`blocked`" in system_review
                    and "`incomplete`" in system_review
                    and "Screenshot attachment is not visual review" in validation,
                    "system review has explicit sign-off and screenshot false-pass guards",
                    "Define pass, blocked, and incomplete and reject screenshot presence as standalone review.",
                ),
                (
                    has(root, "evals/product-ui-taste/system-consistency-toolbar/input.md")
                    and has(root, "evals/product-ui-taste/system-consistency-toolbar/review.expected.md")
                    and "`blocked`" in read_text(root / "evals/product-ui-taste/system-consistency-toolbar/review.expected.md"),
                    "project-neutral system consistency golden case exists",
                    "Add a project-neutral golden case for a blocked same-family toolbar mismatch.",
                ),
                (
                    has(root, "evals/product-ui-taste/component-primitive-selection/input.md")
                    and has(root, "evals/product-ui-taste/component-primitive-selection/decision.expected.md"),
                    "project-neutral component primitive selection fixture exists",
                    "Add project-neutral existing-library, new-project, and Base UI application cases.",
                ),
                (
                    "Radix UI" in component_primitive_expected
                    and "Base UI" in component_primitive_expected
                    and "`defer`" in component_primitive_expected,
                    "component primitive fixture covers keep, defer, and conditional Base UI adoption",
                    "Cover existing Radix repair, evidence-gated selection, and existing Base UI use.",
                ),
                (has(root, "evals/golden-tasks/generic-review-workbench.md"), "generic golden task evidence exists", "Add at least one generic golden real-task card."),
                (has(root, "scripts/design_craft_score.py"), "score script exists", "Add deterministic score script."),
                (
                    has(root, "skills/design-craft/references/reference-workflow.md")
                    and has(root, "skills/design-craft/lib/design_craft/reference_contract.py")
                    and has(root, "skills/design-craft/lib/design_craft/peekpaper.py")
                    and has(root, "skills/design-craft/scripts/design_craft_reference.py")
                    and has(root, "skills/design-craft/contracts/visual-reference-card.schema.json")
                    and has(root, "skills/design-craft/contracts/visual-reference-catalog.schema.json")
                    and has(root, "skills/design-craft/contracts/visual-reference-pack.schema.json"),
                    "portable visual reference intelligence contract exists",
                    "Add source-independent cards, catalogs, packs, and a bounded discovery adapter.",
                ),
                (has(root, "scripts/design_craft_native_runtime_validate.py"), "native runtime evidence validator exists", "Add strict native runtime evidence validation."),
                (has(root, "scripts/design_craft_native_runtime_record.py") and "reactivecircus/android-emulator-runner@" in read_text(root / ".github/workflows/native-runtime.yml"), "native Simulator/Emulator evidence CI exists", "Add reproducible native runtime fixtures, recording, and CI."),
                (has(root, "tools/design_craft/release/native_bundle.py") and has(root, "contracts/release/native-bundle.schema.json") and "native_release_bundle" in read_text(root / "skills/design-craft/COMPATIBILITY.json"), "deterministic native Release bundle contract exists", "Bind Simulator, Emulator, and physical-device evidence into a deterministic Release asset."),
                (
                    "operational_95" in read_text(root / "contracts/release/policy.json")
                    and "certified_100" in read_text(root / "contracts/release/policy.json")
                    and "bypass_actors must be empty" in read_text(root / "scripts/design_craft_github_governance.py"),
                    "tiered exact-asset and no-bypass GitHub release governance exists",
                    "Require exact per-level Release assets and empty branch/tag bypass lists.",
                ),
                ("HOSTS = (\"codex\", \"pi\", \"cursor\", \"claude\")" in read_text(root / "scripts/design_craft_cross_agent_validate.py"), "four-host observed evidence contract exists", "Validate Cursor and Claude independently from Codex and Pi."),
                (
                    "design-craft.cross-agent-score.v5"
                    in read_text(
                        root
                        / "tools/design_craft/evaluation/cross_agent/contract.py"
                    )
                    and has(root, "scripts/design_craft_cross_agent_record.py")
                    and has(root, "contracts/evaluation/evidence-graph.json"),
                    "domain-projected current-source cross-agent evidence binding exists",
                    "Bind cross-agent scores to an exact behavior projection, prompt, scorecard, output, and runner-contract hashes.",
                ),
                (
                    has(root, "evals/comparative/emil-motion-ablation/variants.json")
                    and has(root, "evals/comparative/emil-motion-planning-ablation/variants.json")
                    and has(root, "evals/comparative/taste-visual-critique-ablation/variants.json")
                    and has(root, "evals/comparative/impeccable-production-ablation/variants.json")
                    and has(root, "scripts/design_craft_comparative_judge.py")
                    and has(root, "scripts/design_craft_comparative_validate.py"),
                    "blind no-skill/focused-upstream/design-craft ablations cover all three upstreams",
                    "Add same-host blind focused-upstream ablations with a controlled independent judge.",
                ),
                ("--require-current-source" in read_text(root / "scripts/design_craft_native_runtime_validate.py"), "current-source native evidence binding exists", "Bind native evidence to current skill and fixture trees."),
                ("focus-visible" in design_system.lower(), "focus-visible guidance present", "Cover keyboard focus states."),
                ("component state matrix" in design_system.lower(), "component state matrix present", "Cover shared component states."),
                (("voice" in design_system.lower()) and ("content" in design_system.lower()), "voice/content guidance present", "Cover action, error, toast, and empty-state copy."),
                (
                    "developer-product seed templates" in validation.lower(),
                    "developer-product seed validation contract present",
                    "Require delivery to report whether the original seed was used.",
                ),
                ("product UI taste score" in validation, "product UI score is distinct from source score", "Distinguish UI taste scores from the workflow source score."),
                (has(root, "skills/design-craft/scripts/design_craft_taste_review.sh"), "taste review runtime exists", "Add a stable product UI taste review runtime."),
                (has(root, "skills/design-craft/scripts/design_craft_browser_evidence.py"), "browser evidence helper exists", "Add a redacted DOM/computed-style evidence helper."),
                (has(root, "skills/design-craft/scripts/design_craft_l4_capture.py"), "L4 capture fallback exists", "Add a deterministic L4 screenshot capture fallback."),
                ("anti-inflation" in browser_evidence_helper and "validate_score_json" in browser_evidence_helper, "taste anti-inflation validator exists", "Add a validator for score anti-inflation rules."),
                ("design-craft.browser-evidence.v1" in browser_evidence_helper, "design-craft browser evidence schema exists", "Emit the design-craft browser evidence schema."),
                (has(root, "evals/product-ui-taste/material-ops-home/score.json"), "product UI taste golden case exists", "Add at least one product UI taste calibration case."),
                (has_product_ui_l2_case(root), "product UI taste L2 browser case exists", "Add at least one product UI taste case with browser screenshot and DOM/style evidence."),
                (has_product_ui_l3_case(root), "product UI taste L3 resilient case exists", "Add at least one product UI taste case with responsive and state evidence."),
                (has(root, "evals/product-ui-taste/before-after/README.md"), "L4 before/after eval scaffold exists", "Add L4 before/after eval scaffold."),
                (has_product_ui_l4_before_after_case(root), "project-neutral product UI taste L4 before/after cases exist", "Add completed project-neutral L4 before/after product UI cases."),
                (
                    has(root, "evals/product-ui-taste/prototype-divergence/input.md")
                    and has(root, "evals/product-ui-taste/prototype-divergence/plan.expected.md"),
                    "project-neutral prototype divergence golden case exists",
                    "Add a project-neutral prototype direction and selection-boundary case.",
                ),
                (has(root, "evals/cross-agent/README.md"), "cross-agent benchmark scaffold exists", "Add cross-agent benchmark scaffold."),
                (has(root, "scripts/design_craft_cross_agent_validate.py"), "cross-agent benchmark validator exists", "Add a validator for cross-agent benchmark task definitions."),
                (has(root, "evals/fixtures/css-smells/card-soup.css"), "static scanner fixture exists", "Add scanner fixtures."),
                ("critique" in audit_helper, "critique mode present", "Add a lightweight critique mode."),
                ("system-review" in audit_helper, "system-review mode present", "Add a full system consistency review mode."),
                ("prototype" in audit_helper, "prototype mode present", "Add an isolated prototype divergence mode."),
                ("motion" in audit_helper, "motion mode present", "Add a motion-specific quality pass."),
                ("太 AI" in read_text(root / "skills/design-craft/references/intent-map.md"), "subjective intent mapping present", "Map subjective user phrases to workflow modes."),
                (detector_smoke or not run_smoke, "detector smoke passes", "Fix detector smoke."),
                (score_smoke or not run_smoke, "score smoke passes", "Fix score script smoke."),
                (pass_smoke or not run_smoke, "pass wrapper smoke passes", "Fix pass wrapper smoke."),
                (critique_smoke or not run_smoke, "critique smoke passes", "Fix critique mode smoke."),
                (motion_smoke or not run_smoke, "motion pass smoke passes", "Fix motion pass smoke."),
                (motion_plan_smoke or not run_smoke, "motion plan scaffold smoke passes", "Fix motion-plan scaffold smoke."),
                (seed_smoke or not run_smoke, "seed helper smoke passes", "Fix developer-product seed helper smoke."),
                (taste_review_smoke or not run_smoke, "taste review wrapper smoke passes", "Fix taste review wrapper smoke."),
                (prototype_smoke or not run_smoke, "prototype wrapper smoke passes", "Fix prototype wrapper smoke."),
                (system_review_smoke or not run_smoke, "system-review wrapper smoke passes", "Fix system-review wrapper smoke."),
                (reference_smoke or not run_smoke, "visual-reference CLI smoke passes", "Fix visual-reference CLI smoke."),
            ],
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Score design-craft source completeness out of 100.")
    parser.add_argument("--target", default=None, help="Repo root or skill path to score.")
    parser.add_argument("--self", action="store_true", help="Score the repo containing this script.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--no-smoke", action="store_true", help="Skip command smoke checks.")
    args = parser.parse_args()

    if args.self:
        root = Path(__file__).resolve().parents[1]
    elif args.target:
        root = infer_root(Path(args.target))
    else:
        root = infer_root(Path.cwd())

    dimensions = build_score(root, run_smoke=not args.no_smoke)
    raw_total = sum(item.score for item in dimensions)
    # Operational maturity is intentionally scored by design_craft_maturity.py.
    # Keep the legacy cap fields at 100 for JSON consumers that still read them.
    cap, cap_reasons = 100, []
    total = raw_total

    if args.json:
        print(
            json.dumps(
                {
                    "schema": "design-craft.source-completeness.v1",
                    "metric": "source_completeness",
                    "root": str(root),
                    "score": total,
                    "raw_score": raw_total,
                    "maturity_cap": cap,
                    "maturity_cap_reasons": cap_reasons,
                    "max_score": 100,
                    "dimensions": [
                        {
                            "name": item.name,
                            "score": item.score,
                            "weight": item.weight,
                            "evidence": item.evidence,
                            "gaps": item.gaps,
                        }
                        for item in dimensions
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if total >= 80 else 1

    print(f"design-craft source completeness: {total}/100")
    if total != raw_total:
        print(f"raw heuristic score: {raw_total}/100")
        print(f"maturity cap: {cap}/100")
        for reason in cap_reasons:
            print(f"  - {reason}")
    print(f"root: {root}")
    for item in dimensions:
        print(f"\n{item.name}: {item.score}/{item.weight}")
        for evidence in item.evidence:
            print(f"  + {evidence}")
        for gap in item.gaps:
            print(f"  - {gap}")

    if total < 80:
        print("\nStatus: seed-quality; improve gaps before treating as the default design workflow.")
        return 1
    if total < 90:
        print("\nStatus: usable v0.x; add forward evals and deeper automation before calling it v1.")
    elif total < 94:
        print("\nStatus: advanced v0.3; run independent forward tests before calling it v1.")
    elif total < 97:
        print("\nStatus: v1 pre-release; run one live implementation task before calling it final v1.")
    else:
        print("\nStatus: release-quality; keep validating against real cross-platform product design tasks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
