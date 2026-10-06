from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .assurance import build_assurance_state
from .constants import ARTIFACT_PATHS, REMEDIATION_PHASES, SCHEMA_VERSION, SCORE_DIMENSIONS
from .contracts import ContractError, load_run, validate_run
from .jsonio import atomic_write_text, read_json, read_jsonl, write_json

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def _bullets(items: list[str], fallback: str = "无。") -> list[str]:
    return [f"- {item}" for item in items] if items else [f"- {fallback}"]


def _as_lines(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _score_level(total: int) -> str:
    if total >= 90:
        return "工程基础优秀，但仍应按证据处理剩余缺口"
    if total >= 80:
        return "整体良好，存在明确的局部或模块级优化空间"
    if total >= 70:
        return "基本可用，但关键工程链路需要系统性加固"
    if total >= 60:
        return "工程风险偏高，需要模块级重构和回归保护"
    return "工程风险高，需要先恢复正确性、可验证性和基本边界"


def _finding_sort(row: dict[str, Any]) -> tuple[int, int, str]:
    return (
        PRIORITY_ORDER.get(row["priority"], 99),
        SEVERITY_ORDER.get(row["severity"], 99),
        row["id"],
    )


def _score_copy(mode: str, assurance_level: str) -> tuple[str, str, str, str | None]:
    if assurance_level == "fast":
        return (
            "当前临时评分",
            "临时评分",
            "临时评分",
            "FAST 保证等级不形成最终评分；该数字仅为 provisional 结果。",
        )
    if mode == "focus":
        return (
            "当前 focused review 评分",
            "Focused scope 评分",
            "当前 focused scope 评分",
            "该分数只适用于本次 focused scope，不代表完整仓库综合评分。",
        )
    if mode == "diff":
        return (
            "当前 diff review 评分",
            "Diff scope 评分",
            "当前 diff scope 评分",
            "该分数只覆盖本次指定 diff，不代表完整仓库综合评分。",
        )
    return "当前项目综合评分", "综合评分", "当前项目综合评分", None


def _evidence_gaps(scorecard: dict[str, Any]) -> list[tuple[str, str]]:
    gaps: dict[str, str] = {}
    for dimension in scorecard["dimensions"]:
        for deduction in dimension["deductions"]:
            for reference in deduction["evidenceRefs"]:
                if reference.startswith("evidence-gap:"):
                    gaps.setdefault(reference, deduction["reason"])
    return list(gaps.items())


def _locations(row: dict[str, Any]) -> str:
    rendered: list[str] = []
    for location in row.get("locations", []):
        start = location["lineStart"]
        end = location.get("lineEnd", start)
        suffix = str(start) if start == end else f"{start}-{end}"
        rendered.append(f"`{location['path']}:{suffix}`")
    return ", ".join(rendered)


def _eligible_inspection(files: list[dict[str, Any]]) -> tuple[int, int, float | None]:
    inspected_dispositions = {"REVIEWED", "COVERED_BY_PARENT"}
    eligible_dispositions = inspected_dispositions | {"PENDING", "DEFERRED", "UNREADABLE"}
    inspected = sum(row["disposition"] in inspected_dispositions for row in files)
    eligible = sum(row["disposition"] in eligible_dispositions for row in files)
    percent = round(inspected * 100.0 / eligible, 2) if eligible else None
    return inspected, eligible, percent


def _finding_lines(row: dict[str, Any], decision_by_id: dict[str, str]) -> list[str]:
    return [
        f"### {row['id']} · {row['priority']} / {row['severity']} · {row['title']}",
        "",
        f"- **位置：** {_locations(row)}",
        f"- **问题证据：** {', '.join(f'`{item}`' for item in row['evidenceRefs'])}",
        f"- **根本原因：** {row['rootCause']}",
        f"- **当前实际影响：** {row['currentImpact']}",
        f"- **长期风险：** {row['longTermRisk']}",
        f"- **推荐方案：** {row['recommendation']}",
        f"- **处置：** `{decision_by_id[row['decisionId']]}`",
        f"- **修改成本：** {row['modificationCost']}",
        f"- **修改风险：** {row['modificationRisk']}",
        f"- **验证状态：** `{row['validationStatus']}` / `{row['confidence']}`",
        "- **验证方式：**",
        *_bullets(row["verification"]),
        "",
    ]


def render_report(data: dict[str, Any]) -> str:
    manifest = data["manifest"]
    review_scope = data["reviewScope"]
    quality_model = data["qualityModel"]
    coverage = data["coverage"]
    module_map = data["moduleMap"]
    dependency_map = data["dependencyMap"]
    candidates = data["candidates"]
    findings = sorted(data["findings"]["findings"], key=_finding_sort)
    confirmed_findings = [
        row for row in findings if row.get("validationStatus") == "CONFIRMED"
    ]
    likely_findings = [row for row in findings if row.get("validationStatus") == "LIKELY"]
    decisions = data["decisions"]["decisions"]
    scorecard = data["scorecard"]
    remediation = data["remediationPlan"]
    commands = data["commands"]
    total = scorecard["total"]
    top_findings = findings[:5]
    evidence_gaps = _evidence_gaps(scorecard)
    remaining_risks = quality_model["unknowns"]
    verified_claims = [
        f"`command:{receipt['name']}#{claim['id']}`（{claim['kind']}）"
        for receipt in commands
        for claim in receipt.get("evidenceClaims", [])
        if claim.get("status") == "VERIFIED"
    ]
    captured_artifacts = [
        (
            f"`command:{receipt['name']}#{artifact['id']}`："
            f"`{artifact['sha256']}`，{artifact['sizeBytes']} bytes"
        )
        for receipt in commands
        for artifact in receipt.get("evidenceArtifacts", [])
        if artifact.get("status") == "VERIFIED"
    ]
    registry = data.get("evidenceRegistry")
    if isinstance(registry, dict):
        captured_artifacts.extend(
            (
                f"`artifact:{artifact['id']}`（{artifact['kind']}，"
                f"{artifact['producer']}）：`{artifact['sha256']}`，"
                f"{artifact['sizeBytes']} bytes"
            )
            for artifact in registry.get("artifacts", [])
            if isinstance(artifact, dict)
        )
    delete_subjects = [row["subject"] for row in decisions if row["decision"] == "DELETE"]
    keep_subjects = [row["subject"] for row in decisions if row["decision"] == "KEEP"]
    decision_by_id = {row["id"]: row["decision"] for row in decisions}
    accounted_percent = scorecard.get("accountedPercent", scorecard["coveragePercent"])
    reviewed_percent = scorecard.get("reviewedPercent", scorecard["coveragePercent"])
    coverage_counts: dict[str, int] = defaultdict(int)
    for row in coverage["files"]:
        coverage_counts[row["disposition"]] += 1
    eligible_inspected, eligible_total, eligible_percent = _eligible_inspection(
        coverage["files"]
    )
    eligible_display = f"{eligible_percent}%" if eligible_percent is not None else "N/A"
    assurance = scorecard.get(
        "assurance",
        {
            "level": "standard",
            "completionStatus": "PARTIAL",
            "budget": {},
            "verifier": {"status": "NOT_REQUIRED", "evidenceRef": None},
            "unverifiedClaims": [],
            "skippedDimensions": [],
        },
    )
    summary_score, score_label, conclusion_score, score_limitation = _score_copy(
        review_scope["mode"], assurance["level"]
    )
    budget = assurance["budget"]
    budget_display = (
        f"files={budget.get('eligibleFiles', 'N/A')}/"
        f"{budget.get('maxEligibleFiles') or 'unlimited'}, "
        f"commands={budget.get('evidenceCommands', 'N/A')}/"
        f"{budget.get('maxEvidenceCommands') or 'unlimited'}, "
        f"candidates={budget.get('candidates', 'N/A')}/"
        f"{budget.get('maxCandidates') or 'unlimited'}"
    )

    identity_lines = [
        "# Review Craft 工程审查报告",
        "",
        "## 审查身份",
        "",
        f"- Run ID: `{manifest['runId']}`",
        f"- Repository: `{manifest['target']['repositoryName']}`",
        f"- Revision: `{manifest['target'].get('revision') or 'unversioned'}`",
        f"- Mode: `{review_scope['mode']}`",
        f"- Assurance: `{assurance['level'].upper()}`",
        f"- Completion status: `{assurance['completionStatus']}`",
        f"- Budget consumed: `{budget_display}`",
        f"- Independent verifier: `{assurance['verifier']['status']}`",
        (
            f"- Profile: `{review_scope['profile']['resolved']}` "
            f"({review_scope['profile']['confidence']})"
        ),
        f"- Dimensions: `{', '.join(review_scope['dimensions'])}`",
    ]
    if review_scope["diff"] is not None:
        identity_lines.extend(
            [
                f"- Diff base: `{review_scope['diff']['baseRevision']}`",
                f"- Changed paths: `{len(review_scope['diff']['changes'])}`",
            ]
        )
    identity_lines.extend(
        [
            f"- Source fingerprint: `{manifest['target']['sourceFingerprint']}`",
            f"- Evidence level: `{scorecard['evidenceLevel']}`",
            f"- Inventory classified: `{accounted_percent}%`",
            (
                f"- Eligible files inspected: `{eligible_display}` "
                f"(`{eligible_inspected}/{eligible_total}`)"
            ),
            f"- Reviewed inventory: `{reviewed_percent}%`",
            f"- Hard evidence gaps: `{len(evidence_gaps)}`",
            f"- Unverified claims: `{len(assurance['unverifiedClaims'])}`",
            f"- Skipped dimensions: `{len(assurance['skippedDimensions'])}`",
            f"- Score status: `{scorecard['status']}`",
            f"- Confidence: `{scorecard['confidence']}`",
            f"- Modules: `{len(module_map['modules'])}`",
            f"- Static dependency edges: `{len(dependency_map['edges'])}`",
            "",
        ]
    )
    lines = [
        *identity_lines,
        "# 第一部分：执行摘要",
        "",
        f"{summary_score}为 **{total}/100**。{_score_level(total)}。",
        "",
        f"- 已确认问题（Confirmed Findings）：`{len(confirmed_findings)}`",
        f"- 高概率问题（Likely Findings）：`{len(likely_findings)}`",
        f"- 证据缺口（Evidence Gaps）：`{len(evidence_gaps)}`",
        f"- 剩余风险（Remaining Risks）：`{len(remaining_risks)}`",
        "",
        *([score_limitation, ""] if score_limitation is not None else []),
        "最主要的已验证问题：",
        *_bullets(
            [
                f"{row['id']}（{row['validationStatus']}）：{row['title']}"
                for row in top_findings
            ]
        ),
        "",
        f"建议调整等级：`{remediation['changeClass']}`。",
        "",
        "不值得继续保留的实现：",
        *_bullets(delete_subjects),
        "",
        "# 第二部分：评分",
        "",
        "| 维度 | 得分 | 扣分依据 |",
        "|---|---:|---|",
    ]
    dimensions = {row["id"]: row for row in scorecard["dimensions"]}
    for identifier, label, maximum in SCORE_DIMENSIONS:
        row = dimensions[identifier]
        reasons = "<br>".join(
            f"-{item['points']}：{item['reason']}" for item in row["deductions"]
        ) or "无扣分"
        lines.append(f"| {label} | {row['awarded']}/{maximum} | {reasons} |")
    lines.extend(
        [
            "",
            f"**{score_label}：{total}/100**",
            "",
            "# 第三部分：问题清单",
            "",
            "## 已确认问题（Confirmed Findings）",
            "",
        ]
    )
    if not confirmed_findings:
        lines.append("没有通过验证门禁的正式问题。")
    for row in confirmed_findings:
        lines.extend(_finding_lines(row, decision_by_id))
    lines.extend(["## 高概率问题（Likely Findings）", ""])
    if not likely_findings:
        lines.append("没有通过 LIKELY 验证门禁的高概率问题。")
    for row in likely_findings:
        lines.extend(_finding_lines(row, decision_by_id))
    lines.extend(["## 证据缺口（Evidence Gaps）", ""])
    lines.extend(
        _bullets([f"`{reference}`：{reason}" for reference, reason in evidence_gaps])
    )
    lines.extend(["", "## 剩余风险（Remaining Risks）", ""])
    lines.extend(_bullets(remaining_risks))
    lines.append("")
    lines.extend(["# 第四部分：代码与模块处置建议", ""])
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in decisions:
        grouped[row["decision"]].append(row)
    disposition_sections = (
        ("DELETE", "应立即删除的内容"),
        ("MERGE", "应合并的重复实现"),
        ("REPLACE", "应替换的技术方案"),
        ("REWRITE", "应重写的高风险模块"),
        ("CLEAN_UP", "应保留但需要整理的模块"),
        ("KEEP", "当前设计良好、不建议修改的部分"),
        ("DEFER", "当前收益不足、应暂缓的内容"),
        ("MEASURE", "证据不足、应先测量的内容"),
        ("DOCUMENT", "实现合理但需要补充文档的内容"),
    )
    for decision, heading in disposition_sections:
        lines.extend([f"## {heading}", ""])
        rows = sorted(grouped.get(decision, []), key=lambda item: item["id"])
        lines.extend(
            _bullets([f"**{row['subject']}**：{row['rationale']}" for row in rows])
        )
        lines.append("")
    target = remediation["targetArchitecture"]
    lines.extend(["# 第五部分：目标方案", ""])
    for field, heading in (
        ("overview", "总体架构"),
        ("moduleBoundaries", "模块边界"),
        ("dependencyDirection", "依赖方向"),
        ("coreDataFlow", "核心数据流"),
        ("stateAndErrors", "状态与错误处理策略"),
        ("directoryStructure", "推荐目录结构"),
        ("testingStructure", "测试结构"),
        ("deliveryFlow", "构建、CI 和发布流程"),
    ):
        lines.extend([f"## {heading}", "", *_bullets(_as_lines(target[field])), ""])
    lines.extend(["# 第六部分：实施计划", ""])
    phase_titles = dict(REMEDIATION_PHASES)
    for phase in remediation["phases"]:
        lines.extend(
            [
                f"## {phase_titles[phase['id']]}",
                "",
                "### 修改范围",
                *_bullets(phase["modificationScope"]),
                "",
                "### 前置条件",
                *_bullets(phase["prerequisites"]),
                "",
                "### 预期收益",
                *_bullets(phase["expectedBenefits"]),
                "",
                "### 风险",
                *_bullets(phase["risks"]),
                "",
                "### 验收标准",
                *_bullets(phase["acceptanceCriteria"]),
                "",
            ]
        )
    lines.extend(
        [
            "# 最终结论",
            "",
            f"1. **{conclusion_score}：** {total}/100。",
            "2. **最值得优先处理的五个问题：**",
            *_bullets([f"{row['id']}：{row['title']}" for row in top_findings]),
            "3. **没有继续保留价值的旧实现：**",
            *_bullets(delete_subjects),
            "4. **不够漂亮但不值得重构的部分：**",
            *_bullets(keep_subjects),
            (
                f"5. **完成建议后的预计水平：** {remediation['targetScore']}/100，"
                f"目标证据等级 `{remediation['targetEvidenceLevel']}`；"
                "只有验收条件实际通过后才成立。"
            ),
            "",
            "## 覆盖与未决项",
            "",
            f"- 文件总数：{coverage['summary']['total']}",
            f"- 未决候选：{scorecard['unresolvedCandidates']}",
            f"- Candidate 总数：{len(candidates)}",
            f"- Finding 总数：{len(findings)}",
            f"- 已验证语义声明：{len(verified_claims)}",
            f"- 已捕获证据产物：{len(captured_artifacts)}",
            f"- 审查模式：{review_scope['mode']}",
            f"- 项目 Profile：{review_scope['profile']['resolved']}",
            f"- 保证等级：{assurance['level'].upper()}",
            f"- 完成状态：{assurance['completionStatus']}",
            f"- 预算消耗：{budget_display}",
            f"- 独立复核：{assurance['verifier']['status']}",
            f"- 模块数：{len(module_map['modules'])}",
            f"- 静态依赖边数：{len(dependency_map['edges'])}",
            "- Coverage dispositions:",
            *[
                f"  - {disposition}: `{coverage_counts.get(disposition, 0)}`"
                for disposition in (
                    "REVIEWED",
                    "COVERED_BY_PARENT",
                    "GENERATED",
                    "VENDORED",
                    "BINARY",
                    "OUT_OF_SCOPE",
                    "UNREADABLE",
                    "DEFERRED",
                )
            ],
            "",
            "### 已验证语义声明",
            *_bullets(verified_claims),
            "",
            "### 已捕获证据产物",
            *_bullets(captured_artifacts),
            "",
            "### 未验证声明",
            *_bullets(assurance["unverifiedClaims"]),
            "",
            "### 跳过维度",
            *_bullets(assurance["skippedDimensions"]),
        ]
    )
    if score_limitation is not None:
        conclusion_index = lines.index(f"1. **{conclusion_score}：** {total}/100。")
        lines.insert(conclusion_index + 1, f"   {score_limitation}")
    return "\n".join(lines).rstrip() + "\n"


def finalize_run(run_dir: Path, *, sealed_at: str) -> Path:
    run_dir = run_dir.expanduser().resolve(strict=True)
    manifest_path = run_dir / "review-manifest.json"
    manifest = read_json(manifest_path)
    schema_version = manifest.get("schemaVersion") if isinstance(manifest, dict) else None
    if schema_version != SCHEMA_VERSION:
        raise ContractError(
            [
                "finalize requires a current review-craft.run.v5 draft; "
                "review-craft.run.v3 and run.v4 remain validation-only historical data"
            ]
        )
    # Finalization is a write path, even when re-rendering an already sealed run.
    # Historical v1 agreements may be read by validate, never reused for this write.
    if manifest.get("configuration", {}).get("assuranceLevel") == "assured":
        current_data = load_run(run_dir)
        current_data["manifest"] = {**current_data["manifest"], "status": "draft"}
        _state, verification_errors = build_assurance_state(current_data, run_dir)
        if verification_errors:
            raise ContractError(verification_errors)
    scorecard_path = run_dir / ARTIFACT_PATHS["scorecard"]
    coverage = read_json(run_dir / ARTIFACT_PATHS["coverage"])
    scorecard = read_json(scorecard_path)
    total = sum(row["awarded"] for row in scorecard["dimensions"])
    files = coverage["files"]
    accounted = sum(1 for row in files if row.get("disposition") != "PENDING")
    reviewed = sum(
        row.get("disposition") in {"REVIEWED", "COVERED_BY_PARENT"} for row in files
    )
    scorecard["total"] = total
    scorecard["accountedPercent"] = (
        round(100 * accounted / len(files), 2) if files else 100.0
    )
    scorecard["reviewedPercent"] = (
        round(100 * reviewed / len(files), 2) if files else 100.0
    )
    scorecard["coveragePercent"] = scorecard["reviewedPercent"]
    candidates = read_jsonl(run_dir / ARTIFACT_PATHS["candidateLedger"])
    scorecard["unresolvedCandidates"] = sum(
        1
        for row in candidates
        if row.get("validation", {}).get("status") in {"PENDING", "BLOCKED"}
    )
    if "assuranceLevel" in manifest.get("configuration", {}):
        write_json(scorecard_path, scorecard)
        draft_data = load_run(run_dir)
        assurance, _verifier_errors = build_assurance_state(draft_data, run_dir)
        scorecard["assurance"] = assurance
    write_json(scorecard_path, scorecard)
    data = validate_run(run_dir, final=True)
    manifest = data["manifest"]
    manifest["status"] = "final"
    if not manifest.get("sealedAt"):
        manifest["sealedAt"] = sealed_at
    write_json(manifest_path, manifest)
    data["manifest"] = manifest
    report_path = run_dir / ARTIFACT_PATHS["report"]
    atomic_write_text(report_path, render_report(data))
    return report_path
