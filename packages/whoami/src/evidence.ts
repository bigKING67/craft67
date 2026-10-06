import { buildChart, digest, element, type Chart, type Granularity } from "./chart.js";
import { ziweiTransforms } from "./ziwei-transforms.js";
import { ziweiFlyingTransforms } from "./ziwei-flying.js";
import { wealthReview } from "./wealth-review.js";
import { patternReview } from "./pattern-review.js";
import { externalPatternCandidates } from "./external-patterns.js";
import { InputError } from "./input.js";
import {
  BRANCH_GROUPS,
  completeBranchGroups,
  cycleRelations,
  monthlyCycles,
  pairBranchRelations,
  SEASONAL_GROUPS,
  type BranchRelation,
} from "./cycle-relations.js";

export type Fact = {
  id: string;
  candidate: string;
  system: "input" | "bazi" | "ziwei";
  label: string;
  value: unknown;
  source: string;
};
export type Rule = {
  id: string;
  candidate: string;
  label: string;
  factRefs: string[];
  guidance: string;
  source: string;
};
/**
 * v1、v2 是已发布冻结口径，仅用于重算既有报告与验收样例；新 context 默认 v3。
 * v2 相对 v1：新增 cycleRelations、patternReview、flyingTransforms 事实与 R-bazi-pattern-review 规则，
 * 本命 relations 扩展半合、拱合、破、两两相刑与三会（只增不删），R-bazi-timing 与 R-ziwei-transformations
 * 的 factRefs、guidance 随之扩展；其余事实与规则逐字节一致。
 * v3 相对 v2：patternReview 增加 extendedPatterns（建禄月劫、阳刃），新增 externalPatterns 外格候选事实，
 * R-bazi-pattern-review 的 factRefs 与 guidance 随之扩展。
 */
export const EVIDENCE_SCHEMAS = ["whoami.evidence.v1", "whoami.evidence.v2", "whoami.evidence.v3"] as const;
export type EvidenceSchema = (typeof EVIDENCE_SCHEMAS)[number];
export const CURRENT_EVIDENCE_SCHEMA: EvidenceSchema = "whoami.evidence.v3";
export const isEvidenceSchema = (value: unknown): value is EvidenceSchema =>
  EVIDENCE_SCHEMAS.includes(value as EvidenceSchema);

export function buildEvidence(chart: Chart, schema: EvidenceSchema = CURRENT_EVIDENCE_SCHEMA) {
  // 版本逐级只增不删：v2 ⊇ v1，v3 ⊇ v2。v1、v2 已发布冻结，见 tests/evidence-freeze.test.ts。
  const level = EVIDENCE_SCHEMAS.indexOf(schema) + 1;
  const v2 = level >= 2;
  const v3 = level >= 3;
  // 流月事实只在 v2 且显式请求月度粒度时加入；v1 为冻结口径，不接受月度粒度。
  const monthly = "granularity" in chart && chart.granularity === "month";
  if (monthly && !v2)
    throw new InputError("INVALID_ARGUMENT", "月度粒度只能生成当前版本 evidence");
  if (chart.status === "needs-input")
    throw new InputError("MISSING_TIME", chart.questions[0]!);
  const facts: Fact[] = [],
    rules: Rule[] = [];
  const add = (
    candidate: string,
    system: Fact["system"],
    key: string,
    label: string,
    value: unknown,
    source: string,
  ) => {
    const id = `${candidate}.${system}.${key}`;
    facts.push({ id, candidate, system, label, value, source });
    return id;
  };
  for (const c of chart.candidates) {
    const id = c.id;
    const provenanceMissing = [
      "placeSource",
      "longitudeSource",
      "timeZoneSource",
    ].filter(
      (key) =>
        !chart.input.provenance?.[
          key as "placeSource" | "longitudeSource" | "timeZoneSource"
        ],
    );
    add(
      id,
      "input",
      "time",
      "代表性时间及校正",
      c.representativeTime,
      "NOAA + IANA tzdata",
    );
    add(
      id,
      "input",
      "provenance",
      "地点、经度与时区来源",
      {
        status:
          provenanceMissing.length === 3
            ? "unverified"
            : provenanceMissing.length
              ? "partial"
              : "provided",
        ...(chart.input.provenance ?? {}),
        ...(provenanceMissing.length ? { missing: provenanceMissing } : {}),
      },
      chart.input.provenance
        ? "用户提供的来源元数据；仅记录，不自动认定来源内容正确"
        : "未提供来源元数据",
    );
    const pillarRefs = c.bazi.pillars.map((p) =>
      add(
        id,
        "bazi",
        p.position,
        `${p.position} 柱`,
        p,
        "lunar-typescript + whoami 五鼠遁/十神关系",
      ),
    );
    const dm = add(
      id,
      "bazi",
      "dayMaster",
      "日主",
      c.bazi.dayMaster,
      "lunar-typescript; declared day boundary",
    );
    const month = c.bazi.pillars.find((p) => p.position === "month")!;
    const monthExposureRef = add(
      id,
      "bazi",
      "monthExposure",
      "月支藏干及年/月/时同干透出（不判成格）",
      {
        monthBranch: month.branch,
        dayMaster: c.bazi.dayMaster,
        hiddenStems: month.hiddenStems.map((hidden) => ({
          stem: hidden.stem,
          element: hidden.element,
          tenGod: hidden.tenGod,
          matchesDayMaster: hidden.stem === c.bazi.dayMaster,
          exposedAt: c.bazi.pillars
            .filter((p) => p.position !== "day" && p.stem === hidden.stem)
            .map((p) => p.position),
        })),
      },
      "whoami：既有月支藏干与年/月/时天干精确匹配；日干匹配单列，未算月令司权或格局",
    );
    const wealthRef = add(
      id, "bazi", "wealthReview", "月令财星透出的条件核对（非成败裁定）",
      wealthReview(c.bazi),
      "whoami 显干前提检测；传统条件见《子平真诠·论用神成败救应》原文转录",
    );
    const patternRef = v2
      ? add(
          id, "bazi", "patternReview", "正官/七杀/印/食神/伤官格候选的显干条件核对（非成败裁定）",
          patternReview(c.bazi, { v3 }),
          "whoami 显干前提检测；条件与引文取《子平真诠》论用神成败救应及各格章节（东篱书斋转录本）",
        )
      : null;
    const externalRef = v3
      ? add(
          id, "bazi", "externalPatterns", "外格候选的入口与排除条件（非成格裁定）",
          externalPatternCandidates(c.bazi),
          "whoami 干支前提检测；条件与引文取《子平真诠》论外格用舍、论杂格（东篱书斋转录本），无阈值处注明解释",
        )
      : null;
    const roots = c.bazi.pillars
      .filter((p) =>
        p.hiddenStems.some((s) => s.element === element(c.bazi.dayMaster)),
      )
      .map((p) => p.position);
    const rootRef = add(
      id,
      "bazi",
      "roots",
      "同五行藏干所在柱（仅通根线索）",
      roots,
      "传统藏干表；不计强弱权重",
    );
    const counts: Record<string, number> = {
      木: 0,
      火: 0,
      土: 0,
      金: 0,
      水: 0,
    };
    for (const p of c.bazi.pillars)
      counts[p.element] = (counts[p.element] ?? 0) + 1;
    const countRef = add(
      id,
      "bazi",
      "visibleElements",
      "四个天干五行出现数",
      counts,
      "unweighted descriptive counts",
    );
    const relationRefs: string[] = [];
    const relations: BranchRelation[] = [];
    for (let i = 0; i < 4; i++)
      for (let j = i + 1; j < 4; j++)
        relations.push(...pairBranchRelations(c.bazi.pillars[i]!, c.bazi.pillars[j]!, v2));
    relations.push(
      ...completeBranchGroups(c.bazi.pillars, [], v2 ? [...BRANCH_GROUPS, ...SEASONAL_GROUPS] : BRANCH_GROUPS),
    );
    relationRefs.push(
      add(
        id,
        "bazi",
        "relations",
        "地支关系（不自动判化局或事件）",
        relations,
        v2
          ? "传统合冲刑害破关系表：成对关系含半合、拱合、破与三刑组内两两相刑，成组关系含三合、三刑、三会；不判化局"
          : "传统合冲刑害关系表；首版仅列全三合/全三刑与成对关系",
      ),
    );
    const rootDetailRef = add(
      id,
      "bazi",
      "rootDetails",
      "同五行藏干与直接六冲来源（不裁定根气有效性）",
      c.bazi.pillars.flatMap((p) =>
        p.hiddenStems
          .filter((s) => s.element === element(c.bazi.dayMaster))
          .map((s) => ({
            position: p.position,
            branch: p.branch,
            hiddenStem: s.stem,
            element: s.element,
            tenGod: s.tenGod,
            sameStemAsDayMaster: s.stem === c.bazi.dayMaster,
            clashSources: relations
              .filter((r) => r.kind === "冲" && r.positions.includes(p.position))
              .flatMap((r) => r.positions.filter((position) => position !== p.position))
              .map((position) => ({
                position,
                branch: c.bazi.pillars.find((other) => other.position === position)!.branch,
              })),
          })),
      ),
      "whoami：既有藏干事实与直接六冲关系联结；无旺衰、根气权重或冲毁裁定",
    );
    const cycleRef = add(
      id,
      "bazi",
      "cycles",
      "起运与大运流年",
      c.bazi.cycles,
      "lunar-typescript Yun sect=2; whoami absolute-time adapter",
    );
    rules.push({
      id: `${id}.R-bazi-structure`,
      candidate: id,
      label: "旺衰、格局与用神分开论证",
      factRefs: [dm, pillarRefs[1]!, monthExposureRef, rootRef, rootDetailRef, countRef, ...pillarRefs],
      guidance:
        "先结合月令、透干与藏干通根说明支持/反对理由。五行计数只是描述，不能据数量判旺衰或缺什么补什么。格局、调候与扶抑分列依据，存在冲突时说明适用条件；证据不足则不确定，不自动给唯一用神。",
      source: "references/analysis.md#八字",
    });
    rules.push({
      id: `${id}.R-bazi-wealth-review`,
      candidate: id,
      label: "财格候选分清出现、作用与成败",
      factRefs: [wealthRef, monthExposureRef, rootDetailRef, ...pillarRefs, ...relationRefs],
      guidance: "逐项说明已出现的显干前提与尚未裁定的旺衰、位置及制化条件。支持、风险和救应线索必须同时保留；not-observed 不等于无作用，outside-scope 不等于无格。不能从某个组合出现直接输出成格、破格或救应完成，最终仍需说明未决条件。",
      source: "references/analysis.md#财格候选复核",
    });
    if (patternRef)
      rules.push({
        id: `${id}.R-bazi-pattern-review`,
        candidate: id,
        label: "五格候选分清入口、显干条件与成败",
        factRefs: [patternRef, ...(externalRef ? [externalRef] : []), monthExposureRef, dm, ...pillarRefs, ...relationRefs],
        guidance: "先说明月支藏干哪一个十神构成候选、是否透出及有无竞争透干，再逐项引用已出现的支持、风险与救应条件。同一显干组合在不同强弱条件下方向相反时须按条件分支说明，不能只取有利一侧；金水季节、次序例外、合化与位置由宿主论证。不能从组合出现直接输出成格、败格或救应完成。" +
          (externalRef
            ? "建禄月劫与阳刃按禄位、刃位入格，用神另取财官煞食；外格只在正格论证不成立后才讨论，blocked 表示原文排除条件已出现，interpretation 条目是 whoami 的复算定义。"
            : ""),
        source: "references/analysis.md#五格候选复核",
      });
    rules.push({
      id: `${id}.R-bazi-month-exposure`,
      candidate: id,
      label: "月令藏干透出与格局成败分开核验",
      factRefs: [dm, monthExposureRef, ...pillarRefs, ...relationRefs],
      guidance:
        "先逐个核对月支藏干及年/月/时同一天干的透出位置；同五行不同干不算本项透出，日干同字单列。透干仅提供格局分析线索；多干同透全部保留，不按出现次数选唯一用神，未透也不等于无格。月令司权、会支变化、成败救应及制化有效性仍需另行论证。《子平真诠》的月令用神语境不得直接替代调候或扶抑用神。",
      source: "references/analysis.md#月令透干复核",
    });
    rules.push({
      id: `${id}.R-bazi-root-review`,
      candidate: id,
      label: "藏干存在与根气作用分开核对",
      factRefs: [dm, rootRef, rootDetailRef, ...relationRefs, ...pillarRefs],
      guidance:
        "先核对具体柱、地支和藏干，再讨论对日主的支持。同五行与同天干分别列出；直接受冲的根仍是盘面事实，不能直接删除，未列直接六冲也不等于根气有效或身强。结合月令、透干及其他关系提出支持、反证与待核条件；不把多条同源描述重复计为独立证据，不自动裁定旺衰、从格或用神。",
      source: "references/analysis.md#通根复核",
    });
    const cycleRelationRef = v2
      ? add(
          id,
          "bazi",
          "cycleRelations",
          "流年、当年大运与本命的干支关系（不判化合成败或事件）",
          cycleRelations(c.bazi),
          "传统干合干冲、合冲刑害、伏吟反吟关系表；流年按 lunar-typescript 立春时刻，大运按起运范围对齐",
        )
      : null;
    const monthlyRef = monthly
      ? add(
          id,
          "bazi",
          "monthlyCycles",
          "八字流月（按节切分）及其与本命、流年、大运的干支关系",
          monthlyCycles(c.bazi),
          "lunar-typescript 节气时刻与月柱；关系表同 cycleRelations，不判化合成败或事件",
        )
      : null;
    const timingGuidance =
      "将具体运年与本命柱联系，区分触发线索、替代解释及现实条件；冲不等于灾、合不等于吉，不从关系表直接推断具体人生事件。";
    rules.push({
      id: `${id}.R-bazi-timing`,
      candidate: id,
      label: "本命与运年联读",
      factRefs: [
        cycleRef,
        ...(cycleRelationRef ? [cycleRelationRef] : []),
        ...(monthlyRef ? [monthlyRef] : []),
        ...relationRefs,
        ...pillarRefs,
      ],
      guidance: v2
        ? timingGuidance +
          "cycleRelations 只列组合是否出现：合是否化、冲是否成立、年内换运前后的差异及起运不确定时的分支仍须宿主论证。" +
          (monthlyRef
            ? "monthlyCycles 的流月只能叠加在本命、大运与流年判断之上，按节气起止表达，不能改写为公历月或单独断事。"
            : "")
        : timingGuidance,
      source: "references/analysis.md#八字",
    });
    const base = add(
      id,
      "ziwei",
      "base",
      "命身宫与五行局",
      {
        soulPalace: c.ziwei.soulPalace,
        bodyPalace: c.ziwei.bodyPalace,
        soul: c.ziwei.soul,
        body: c.ziwei.body,
        fiveElementsClass: c.ziwei.fiveElementsClass,
        settings: c.ziwei.settings,
      },
      "iztro@2.6.1",
    );
    const palaceRefs = c.ziwei.palaces.map((p) =>
      add(id, "ziwei", `palace-${p.index}`, `${p.name}宫`, p, "iztro@2.6.1"),
    );
    const dynamic = add(
      id,
      "ziwei",
      "cycles",
      "大限与流年",
      { decadals: c.ziwei.decadals, yearly: c.ziwei.yearly },
      "iztro@2.6.1; lunar-new-year boundary",
    );
    const transformRef = add(
      id, "ziwei", "transformations", "生年、大限、流年四化落宫（分层）",
      ziweiTransforms(c.ziwei), "iztro@2.6.1 运限输出 + whoami 星名/本命宫位联结",
    );
    const flyingRef = v2
      ? add(
          id, "ziwei", "flyingTransforms", "本命十二宫宫干飞化与自化落点（不判吉凶）",
          ziweiFlyingTransforms(c.ziwei), "iztro@2.6.1 十干四化表 + whoami 星名/本命宫位联结",
        )
      : null;
    const ziweiMonthlyRef = monthly && c.ziwei.monthly
      ? add(
          id, "ziwei", "monthly", "紫微流月（农历月）宫职、四化与流月星",
          c.ziwei.monthly, "iztro@2.6.1 流月运限；闰月按 iztro 前 15 日归上月、其后归下月",
        )
      : null;
    rules.push({
      id: `${id}.R-ziwei-transformations`, candidate: id,
      label: "四化分层与落宫核对",
      factRefs: [
        transformRef,
        base,
        dynamic,
        ...(flyingRef ? [flyingRef] : []),
        ...(ziweiMonthlyRef ? [ziweiMonthlyRef] : []),
        ...palaceRefs,
      ],
      guidance: "逐项核对四化来自生年、大限还是流年，以及星曜、本命落宫和已提供的流年宫职。大限年龄与年份均沿用虚岁/农历年口径，不当作生日或公历元旦切换。不能将大限命宫误作所有四化落宫；缺星、重名和未提供宫职保持未知，不用化忌直接断灾或化禄直接断财。" +
        (flyingRef
          ? "宫干飞化与自化是本命宫之间的结构线索，须说明从哪宫化出、落入哪宫及所用十干四化口径；不能把飞化落点直接当作运限事件，也不能与生年、运限四化混为一层。"
          : "") +
        (ziweiMonthlyRef
          ? "流月四化只叠加在生年、大限与流年层之上，按农历月表达；闰月两段须说明所用口径并保留另一派分支。"
          : ""),
      source: "references/analysis.md#四化落宫复核",
    });
    for (const [topic, names] of Object.entries({
      事业: ["命宫", "官禄", "财帛", "迁移"],
      财运: ["财帛", "官禄", "田宅", "福德"],
      关系: ["夫妻", "命宫", "福德", "迁移"],
    })) {
      const indices = new Set<number>();
      for (const p of c.ziwei.palaces.filter((p) => names.includes(p.name)))
        for (const index of p.surroundedIndices) indices.add(index);
      rules.push({
        id: `${id}.R-ziwei-${topic}`,
        candidate: id,
        label: `紫微${topic}联宫`,
        factRefs: [base, dynamic, transformRef, ...[...indices].map((i) => palaceRefs[i]!)],
        guidance:
          "从主题宫主辅星、四化、三方四正和命身宫形成条件性解释，再对照大限流年；不可仅凭单星下结论，空宫不能自行填入对宫星而不标明借星。",
        source: "https://iztro.com/learn/palace",
      });
    }
  }
  const evidenceId = digest({
    chartId: chart.chartId,
    years: chart.years,
    facts,
    rules,
  });
  return {
    schema,
    chartId: chart.chartId,
    evidenceId,
    status: chart.status,
    input: chart.input,
    years: chart.years,
    ...(monthly ? { granularity: "month" as const } : {}),
    warnings: chart.warnings,
    candidateIds: chart.candidates.map((c) => c.id),
    facts,
    rules,
    limits: [
      "确定性排盘不证明现实预测有效。",
      "不同命理体系的同向解读不是独立统计验证。",
      "规则依据仅支持传统解释，不构成医疗、投资或婚姻决策的事实证明。",
    ],
  };
}
export type Evidence = ReturnType<typeof buildEvidence>;
export function contextFor(
  raw: unknown,
  years?: number[],
  schema?: EvidenceSchema,
  granularity: Granularity = "year",
) {
  return buildEvidence(buildChart(raw, years, granularity), schema);
}
/** 按报告已绑定的 evidenceId 选用对应版本重算；都不匹配时返回当前版本，由报告校验给出 STALE_REPORT。 */
export function evidenceForReport(
  chart: Chart,
  report: unknown,
  current: Evidence = buildEvidence(chart),
) {
  const bound =
    report && typeof report === "object"
      ? (report as { evidenceId?: unknown }).evidenceId
      : undefined;
  if (bound === current.evidenceId) return current;
  // v1 不接受月度粒度；月度报告仍须能按 v2 等已发布版本重算。
  const month = "granularity" in chart && chart.granularity === "month";
  for (const schema of EVIDENCE_SCHEMAS) {
    if (schema === CURRENT_EVIDENCE_SCHEMA || (month && schema === "whoami.evidence.v1")) continue;
    const older = buildEvidence(chart, schema);
    if (older.evidenceId === bound) return older;
  }
  return current;
}

/**
 * 月度 evidence 中可被正文引用的流月标签，按所属年份（八字立春年、紫微农历年）列出允许的起止说明：
 * 八字为“起节至止节”，紫微为农历月名（闰月含“闰六月上半”等分段名）。年度 evidence 返回 undefined。
 */
export function monthlyLabels(
  evidence: Evidence,
): Map<string, { year: number; range: string }[]> | undefined {
  if (!("granularity" in evidence) || evidence.granularity !== "month") return undefined;
  const labels = new Map<string, { year: number; range: string }[]>();
  const add = (tag: string, year: number, range: string) => {
    const list = labels.get(tag) ?? [];
    if (!list.some((e) => e.year === year && e.range === range)) list.push({ year, range });
    labels.set(tag, list);
  };
  for (const fact of evidence.facts) {
    if (fact.id.endsWith(".bazi.monthlyCycles"))
      for (const y of fact.value as ReturnType<typeof monthlyCycles>)
        for (const m of y.months) add(`八字流月${m.pillar}`, y.year, `${m.startJie}至${m.endJie}`);
    if (fact.id.endsWith(".ziwei.monthly"))
      for (const m of fact.value as { year: number; stem: string; branch: string; label: string }[])
        add(`紫微流月${m.stem}${m.branch}`, m.year, m.label);
  }
  return labels;
}
