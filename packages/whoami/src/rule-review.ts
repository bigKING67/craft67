import type { Chart } from "./chart.js";
import { buildEvidence, type Evidence } from "./evidence.js";
import type { wealthReview } from "./wealth-review.js";
import type { patternReview } from "./pattern-review.js";
import type { externalPatternCandidates } from "./external-patterns.js";

const POSITIONS: Record<string, string> = { year: "年", month: "月", day: "日", hour: "时" };
const describe = (p: { position: string; stem: string; tenGod: string }) =>
  `${POSITIONS[p.position]}干${p.stem}（${p.tenGod}）`;

export function wealthReviewFacts(e: Evidence) {
  return e.candidateIds.map(candidate => {
    const factId = `${candidate}.bazi.wealthReview`;
    // 同进程 buildEvidence 生成，事实类型与生成器对应。
    const value = e.facts.find(f => f.id === factId)!.value as ReturnType<typeof wealthReview>;
    return { candidate, factId, ruleId: `${candidate}.R-bazi-wealth-review`, value };
  });
}

export function wealthReviewSummary(w: ReturnType<typeof wealthReview>): string[] {
  return [
    `财格入口：${w.status === "candidate-only" ? "满足当前模块的候选入口，尚未确认成格" : "不满足当前模块入口，不代表无财或无格"}。`,
    `财印位置：${w.sealPlacement.conclusion}`,
    ...w.sealPlacement.pairs.filter(p => p.adjacent).map(p =>
      `相邻依据：${describe(p.wealth)}与${describe(p.seal)}。`),
    `财旺生官：${w.officerBranch.conclusion}`,
    ...w.officerBranch.checks.filter(x => w.officerBranch.blockers.includes(x.id)).map(x =>
      `反例：${x.positions.map(describe).join("、")}；本分支要求${x.condition}。`),
  ];
}

const ROLE_NAMES = { main: "本气", middle: "中气", residual: "余气" } as const;
const CATEGORY_NAMES = { support: "支持", risk: "风险", rescue: "救应" } as const;

/** Deterministic view of existing evidence; no new traditional judgments. */
export function renderRuleReview(chart: Chart): string {
  const e = buildEvidence(chart); // 缺时辰沿用既有拒绝行为，不生成空盘解读。
  const lines = [
    "# 八字规则复核：财格、五格、建禄阳刃与外格候选",
    "",
    "这是现有财格，正官、七杀、印、食神、伤官五格，建禄月劫、阳刃与外格候选规则的确定性摘要，不是完整八字或紫微分析，不判整体吉凶，也不预测现实事件。",
    "",
    `命盘状态：${chart.status}；候选数：${chart.candidates.length}。所有候选分别保留，不择优选盘。`,
    `证据年份：${e.years.join("、")}。下列规则只检查本命，不据年份推断流年事件。`,
    "",
    ...chart.warnings.map(w => `- 注意：${w}`),
  ];
  for (const { candidate, factId, value: w } of wealthReviewFacts(e)) {
    const c = chart.candidates.find(c => c.id === candidate)!;
    lines.push("", `## 候选 ${c.id}`, "",
      `四柱：${c.bazi.pillars.map(p => `${POSITIONS[p.position]}柱${p.value}`).join("、")}。`,
      `财格入口：${w.status}。${w.scope}。`, "");
    if (w.candidates.length) {
      lines.push(...w.candidates.map(x => `- 月支${w.monthBranch}藏${x.stem}（${x.tenGod}），透于${x.exposedAt.map(p => POSITIONS[p]).join("、")}干。`));
      const observed = w.checks.filter(x => x.prerequisite === "observed");
      lines.push("", "已见的显干前提（不等于作用成立）：", "",
        ...(observed.length ? observed.map(x => `- ${x.label}：${x.groups.flatMap(g => g.positions.map(describe)).join("、")}。待核：${x.pending}。`) : ["- 八组额外显干前提均未见。"]),
        "", `未见显干前提：${w.checks.filter(x => x.prerequisite === "not-observed").map(x => x.label).join("、") || "无"}。未见不等于藏干无作用。`);
    } else {
      lines.push("入口未满足，不代表无财或无格；未透取用、会支变化等不在本模块内。");
    }
    lines.push("", `财印位置：${w.sealPlacement.status}。${w.sealPlacement.conclusion}`, "",
      ...w.sealPlacement.pairs.map(p => `- ${describe(p.wealth)}与${describe(p.seal)}：${p.adjacent ? "相邻" : `隔${p.between.map(x => POSITIONS[x]).join("、")}柱`}。`),
      "", `财旺生官分支：${w.officerBranch.status}。${w.officerBranch.conclusion}`, "",
      ...w.officerBranch.checks.filter(x => w.officerBranch.blockers.includes(x.id)).map(x =>
        `- 阻断依据：${x.condition}；反例为${x.positions.map(describe).join("、")}。`),
      "", "尚需论证：身强弱、财官实际作用、合化及救应、藏干影响。财印相邻或财官分支阻断不能直接推成整格失败；未见反例也不能推成成格。",
      "", `依据：\`${factId}\`；规则：\`${c.id}.R-bazi-wealth-review\`。`);
    const patternFact = e.facts.find(f => f.id === `${candidate}.bazi.patternReview`);
    if (patternFact) {
      const r = patternFact.value as ReturnType<typeof patternReview>;
      const candidates = r.patterns.filter(p => p.status === "candidate-only");
      lines.push("", "### 五格候选（正官、七杀、印、食神、伤官）", "",
        ...(candidates.length ? [] : ["- 月支藏干不含这五类十神；入口外不代表无格。"]));
      for (const p of candidates) {
        const observed = p.checks.filter(x => x.prerequisite === "observed");
        lines.push(
          `- **${p.label}**：月支${r.monthBranch}藏${p.entry.map(h => `${h.stem}（${h.tenGod}，${ROLE_NAMES[h.role]}${h.exposedAt.length ? `，透于${h.exposedAt.map(x => POSITIONS[x]).join("、")}干` : "，未透"}）`).join("、")}。` +
            (p.competingExposed.length ? `月令另有${p.competingExposed.map(h => `${h.stem}（${h.tenGod}）`).join("、")}透出，透者作主须另证。` : ""),
          ...(observed.length
            ? observed.map(x => `  - ${CATEGORY_NAMES[x.category]}·${x.label}：「${x.quote}」（[原文](${x.source})）。待核：${x.pending}。`)
            : ["  - 所列显干条件均未见；未见不等于藏干无作用。"]),
        );
      }
      for (const p of (r.extendedPatterns ?? []).filter(x => x.status === "candidate-only")) {
        const observed = p.checks.filter(x => x.prerequisite === "observed");
        lines.push(
          `- **${p.label}**：${p.entry.map(e => `月支${e.branch}为${e.kind}（${e.rule}）`).join("；")}。` +
            (p.useGodCandidates.length ? `月令另有${p.useGodCandidates.map(h => `${h.stem}（${h.tenGod}）`).join("、")}透出，可作用神入口。` : "用神须另取透干会支的财官煞食。"),
          ...(observed.length
            ? observed.map(x => `  - ${CATEGORY_NAMES[x.category]}·${x.label}：「${x.quote}」（[原文](${x.source})）。待核：${x.pending}。`)
            : ["  - 所列显干条件均未见；未见不等于藏干无作用。"]),
        );
      }
      lines.push("", `五格结论：${r.judgment}。支持、风险与救应并列保留，不计分、不抵消。依据：\`${patternFact.id}\`；规则：\`${c.id}.R-bazi-pattern-review\`。`);
    }
    const externalFact = e.facts.find(f => f.id === `${candidate}.bazi.externalPatterns`);
    if (externalFact) {
      const x = externalFact.value as ReturnType<typeof externalPatternCandidates>;
      const shown = x.candidates.filter(k => k.status !== "not-observed");
      lines.push("", "### 外格候选（原书存疑，须先论证正格不成立）", "",
        ...x.gate.map(g => `- 通则·${g.condition}：${g.observed ? "是" : "否"}。`),
        ...(shown.length
          ? shown.map(k => `- **${k.label}**：${k.status === "blocked" ? `排除条件已出现（${k.blockers.filter(b => b.observed).map(b => b.condition).join("；")}）` : `入口可见（${k.entry.map(c => c.condition + (c.interpretation ? `，按 whoami 解释：${c.interpretation}` : "")).join("；")}）`}。待核：${k.pending}。`)
          : ["- 所列外格入口均不全。"]),
        "", `外格结论：${x.judgment}。依据：\`${externalFact.id}\`。`);
    }
  }
  lines.push("", "## 核对与来源", "",
    `chartId：\`${e.chartId}\``, `evidenceId：\`${e.evidenceId}\``, "",
    "细项可用相同输入与年份运行 context，按上述事实 ID 核对。出生资料变化后必须重新计算。",
    "",
    "传统来源：[论用神成败救应](https://donglishuzhai.net/chapter/3722.html)、[论用神变化](https://donglishuzhai.net/chapter/3723.html)、[论财](https://donglishuzhai.net/chapter/3746.html)、[论正官](https://donglishuzhai.net/chapter/3744.html)、[论印](https://donglishuzhai.net/chapter/3748.html)、[论食神](https://donglishuzhai.net/chapter/3750.html)、[论偏官](https://donglishuzhai.net/chapter/3752.html)、[论伤官](https://donglishuzhai.net/chapter/3754.html)、[论用神](https://donglishuzhai.net/chapter/3721.html)、[论阳刃](https://donglishuzhai.net/chapter/3756.html)、[论建禄月劫](https://donglishuzhai.net/chapter/3758.html)、[论外格用舍](https://donglishuzhai.net/chapter/3735.html)、[论杂格](https://donglishuzhai.net/chapter/3760.html)。当前采用原文转录，未完成影印校勘；工程检查不证明传统理论或现实预测有效。",
    "");
  return lines.join("\n");
}
