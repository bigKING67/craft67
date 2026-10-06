import { object, InputError } from "./input.js";
import { monthlyLabels, type Evidence } from "./evidence.js";
import { isDeepStrictEqual } from "node:util";
import { wealthReviewFacts, wealthReviewSummary } from "./rule-review.js";
import { ziweiLayerFacts, describeLayerEntry } from "./ziwei-layer-review.js";
import {
  assertZiweiPalaceScope,
  scopeForText,
  ziweiScopes,
} from "./ziwei-palace-scope.js";
import {
  assertNoUnresolvedPremiseUpgrade,
  assertSafeReportText,
  requiredReasoningTopics,
} from "./report-safety.js";
import {
  monthlyLabelMentions,
  referencedRelativeYears,
  validIsoDate,
  validateReportTemporalText,
} from "./report-time.js";

export const SECTION_IDS = [
  "summary",
  "character",
  "career",
  "wealth",
  "relationships",
  "timing",
  "advice",
] as const;
const TITLES: Record<string, string> = {
  summary: "核心结论",
  character: "性格倾向",
  career: "事业",
  wealth: "财运",
  relationships: "感情与家庭",
  timing: "大运、大限与流年",
  advice: "建议",
};
const BAZI_CORE_TOPICS = [
  "strength",
  "pattern",
  "climate",
  "balance",
  "selection",
] as const;
export const BAZI_TOPICS = [...BAZI_CORE_TOPICS, "bazi-timing"] as const;
const BAZI_TITLES: Record<(typeof BAZI_TOPICS)[number], string> = {
  strength: "旺衰",
  pattern: "格局",
  climate: "调候",
  balance: "扶抑",
  selection: "用神取舍",
  "bazi-timing": "运年与边界",
};
const BAZI_TOPIC_RULE_SUFFIXES: Record<
  (typeof BAZI_TOPICS)[number],
  readonly string[]
> = {
  strength: [".R-bazi-structure", ".R-bazi-root-review"],
  pattern: [
    ".R-bazi-structure",
    ".R-bazi-wealth-review",
    ".R-bazi-pattern-review",
    ".R-bazi-month-exposure",
  ],
  climate: [".R-bazi-structure"],
  balance: [
    ".R-bazi-structure",
    ".R-bazi-root-review",
    ".R-bazi-wealth-review",
  ],
  selection: [
    ".R-bazi-structure",
    ".R-bazi-root-review",
    ".R-bazi-wealth-review",
    ".R-bazi-pattern-review",
    ".R-bazi-month-exposure",
  ],
  "bazi-timing": [".R-bazi-timing"],
};
export const ZIWEI_TOPICS = [
  "ziwei-structure",
  "ziwei-career",
  "ziwei-wealth",
  "ziwei-relationships",
  "ziwei-timing",
] as const;
const ZIWEI_TITLES: Record<(typeof ZIWEI_TOPICS)[number], string> = {
  "ziwei-structure": "本命结构",
  "ziwei-career": "事业联宫",
  "ziwei-wealth": "财运联宫",
  "ziwei-relationships": "关系联宫",
  "ziwei-timing": "限运与四化",
};
const ZIWEI_TOPIC_RULE_SUFFIXES: Record<
  (typeof ZIWEI_TOPICS)[number],
  readonly string[]
> = {
  "ziwei-structure": [
    ".R-ziwei-事业",
    ".R-ziwei-财运",
    ".R-ziwei-关系",
  ],
  "ziwei-career": [".R-ziwei-事业"],
  "ziwei-wealth": [".R-ziwei-财运"],
  "ziwei-relationships": [".R-ziwei-关系"],
  "ziwei-timing": [".R-ziwei-transformations"],
};
const ZIWEI_TOPIC_PALACE: Partial<
  Record<(typeof ZIWEI_TOPICS)[number], string>
> = {
  "ziwei-structure": "命宫",
  "ziwei-career": "官禄",
  "ziwei-wealth": "财帛",
  "ziwei-relationships": "夫妻",
};
const ZIWEI_SECTION_TOPIC: Partial<
  Record<(typeof SECTION_IDS)[number], (typeof ZIWEI_TOPICS)[number]>
> = {
  summary: "ziwei-structure",
  character: "ziwei-structure",
  career: "ziwei-career",
  wealth: "ziwei-wealth",
  relationships: "ziwei-relationships",
  timing: "ziwei-timing",
};
const CROSS_SYSTEM_TARGETS = [
  "general",
  "career",
  "wealth",
  "relationships",
  "timing",
] as const;
type CrossSystemTarget = (typeof CROSS_SYSTEM_TARGETS)[number];
const CROSS_SYSTEM_TARGET_TITLES: Record<CrossSystemTarget, string> = {
  general: "综合结构",
  career: "事业",
  wealth: "财运",
  relationships: "关系",
  timing: "限运与流年",
};
const CROSS_SYSTEM_TARGET_TOPIC: Record<
  CrossSystemTarget,
  (typeof ZIWEI_TOPICS)[number]
> = {
  general: "ziwei-structure",
  career: "ziwei-career",
  wealth: "ziwei-wealth",
  relationships: "ziwei-relationships",
  timing: "ziwei-timing",
};
const BAZI_GLOSSARY = [
  ["日主", "八字日柱的天干，是传统分析其他干支关系时的参照点，不等于完整人格。"],
  ["月令", "出生月份的地支及其季节背景；它很重要，但不能单独决定旺衰或格局。"],
  ["藏干／透干", "藏干是地支中传统分配的天干；透干是相关天干出现在可见天干位置。出现不等于作用已经成立。"],
  ["通根", "日主同五行在地支藏干中有线索；是否足以发挥仍要结合月令、位置、冲合与制化。"],
  ["十神", "其他干支相对日主形成的传统关系标签，如财、官、印、食伤；不是固定性格或现实事件。"],
  ["旺衰", "对日主承受支持与负荷能力的传统判断，不是精确分数或现实成功概率。"],
  ["格局", "围绕月令、透藏和组合条件形成的结构取法；看到某个组合不等于已经成格。"],
  ["调候", "从寒暖燥湿角度讨论传统取用，不能当作实际天气或健康诊断。"],
  ["扶抑", "在强弱假设下讨论扶助或制约方向；前提改变时，取舍也应重审。"],
  ["用神／喜忌", "某一传统取法下的条件性取舍，不是唯一答案，也不是现实决策指令。"],
  ["大运／流年", "八字中的阶段与年度层；边界按本报告口径计算，不能直接等同具体事件时间。"],
] as const;
const ZIWEI_GLOSSARY = [
  ["命宫／身宫", "紫微盘中的结构参照宫位，用于组织主题，不是对命运或身体的字面判决。"],
  ["主星／辅星", "宫位中的传统星曜分类；单颗星不能脱离宫位、关联宫和时间层直接下结论。"],
  ["三方四正", "与目标宫位一同联读的关联宫位范围，不是多份独立证据或概率加成。"],
  ["四化", "禄、权、科、忌四种传统变化标签；不同时间层可并存，不自动等于吉凶事件。"],
  ["大限／流年", "紫微的阶段与年度层；大限按盘中年龄区间，流年按农历年标签，不能混成本命结论。"],
  ["本命宫位／流年宫职", "前者是星曜在原盘的物理位置，后者是同一位置在某年的主题职责，两层不能互相替代。"],
] as const;
type BaziReasoning = {
  candidate: string;
  topic: (typeof BAZI_TOPICS)[number];
  status: "conditional" | "unresolved";
  conclusion: string;
  supportRefs: string[];
  counterRefs: string[];
  counterReview: string;
  conditions: string;
  alternatives: string;
  ruleRefs: string[];
  years?: number[];
  timingChain?: BaziTimingChain;
};
type BaziTimingChain = {
  target: "career" | "wealth" | "relationships" | "general";
  cycleRefs: string[];
  annualReviews: {
    year: number;
    pillar: string;
    boundary: "lichun";
    natalRefs: string[];
    review: string;
  }[];
  crossLayerReview: string;
  missingLinks: string[];
  realityBasis: {
    status: "not-provided" | "provided";
    summary: string;
    source: string | null;
  };
  withdrawalConditions: string;
};
type ZiweiReasoning = {
  candidate: string;
  topic: (typeof ZIWEI_TOPICS)[number];
  status: "conditional" | "unresolved";
  conclusion: string;
  supportRefs: string[];
  counterRefs: string[];
  counterReview: string;
  conditions: string;
  alternatives: string;
  ruleRefs: string[];
  timingChain?: ZiweiTimingChain;
};
type ZiweiTimingChain = {
  target: "career" | "wealth" | "relationships" | "general";
  years: number[];
  transformationRefs: string[];
  cycleRefs: string[];
  palaceRefs: string[];
  crossLayerReview: string;
  missingLinks: string[];
  realityBasis: {
    status: "not-provided" | "provided";
    summary: string;
    source: string | null;
  };
  withdrawalConditions: string;
};
type Claim = {
  text: string;
  kind: "interpretation" | "advice";
  factRefs: string[];
  ruleRefs: string[];
  reasoningRefs: ReasoningRef[];
  premiseStatus: "conditional" | "unresolved" | "not-applicable";
  conditions: string;
  confidence: "low" | "medium" | "high";
};
type ReasoningRef = {
  candidate: string;
  topic:
    | (typeof BAZI_TOPICS)[number]
    | (typeof ZIWEI_TOPICS)[number];
};
export type Report = {
  schema: "whoami.report.v6" | "whoami.report.v5" | "whoami.report.v4" | "whoami.report.v3";
  chartId: string;
  evidenceId: string;
  mode: "bazi" | "ziwei" | "combined";
  timeReference: {
    asOfDate: string;
    timeZone: string;
  } | null;
  title: string;
  uncertainty: string;
  sections: { id: string; claims: Claim[] }[];
  baziReasoning: BaziReasoning[];
  ziweiReasoning: ZiweiReasoning[];
  crossSystem: {
    target?: CrossSystemTarget;
    years?: number[];
    relationship: "supports" | "complements" | "conflicts" | "insufficient";
    text: string;
    factRefs: string[];
    reasoningRefs: ReasoningRef[];
    premiseStatus: "conditional" | "unresolved";
  }[];
  assertions: { factRef: string; value: unknown }[];
};
function string(v: unknown, label: string): string {
  if (typeof v !== "string" || !v.trim())
    throw new InputError("INVALID_REPORT", `${label} 需要非空文字`);
  return v;
}
function reportText(v: unknown, label: string): string {
  const value = string(v, label);
  assertSafeReportText(value, label);
  return value;
}
const REASONING_NARRATIVE_FIELDS = [
  "conclusion",
  "counterReview",
  "conditions",
  "alternatives",
] as const;
function recordReasoningNarrative(
  seen: Map<string, Map<string, string>>,
  candidate: string,
  topic: string,
  values: string[],
  systemLabel: string,
) {
  const normalized = JSON.stringify(
    values.map((value) => value.trim().replace(/\s+/gu, " ")),
  );
  let candidateNarratives = seen.get(candidate);
  if (!candidateNarratives) {
    candidateNarratives = new Map();
    seen.set(candidate, candidateNarratives);
  }
  const previousTopic = candidateNarratives.get(normalized);
  if (previousTopic !== undefined)
    throw new InputError(
      "DUPLICATE_REASONING_NARRATIVE",
      `${systemLabel}论证 ${topic} 不能整段复用同一候选 ${previousTopic} 的 conclusion、counterReview、conditions 与 alternatives`,
    );
  candidateNarratives.set(normalized, topic);
}
function array(v: unknown, label: string): unknown[] {
  if (!Array.isArray(v))
    throw new InputError("INVALID_REPORT", `${label} 需要数组`);
  return v;
}
function referencedEvidenceYears(text: string, evidenceYears: number[]) {
  const years = new Set<number>();
  for (const match of text.matchAll(
    /((?:19|20)\d{2})\s*(?:-|–|—|~|～|至)\s*((?:19|20)\d{2})/gu,
  )) {
    const start = Number(match[1]);
    const end = Number(match[2]);
    const lower = Math.min(start, end);
    const upper = Math.max(start, end);
    for (const year of evidenceYears)
      if (year >= lower && year <= upper) years.add(year);
  }
  for (const match of text.matchAll(/(?:19|20)\d{2}/gu)) {
    const year = Number(match[0]);
    if (evidenceYears.includes(year)) years.add(year);
  }
  return [...years].sort((a, b) => a - b);
}
export function validateReport(raw: unknown, evidence: Evidence): Report {
  const r = object(raw, "报告");
  if (!["bazi", "ziwei", "combined"].includes(String(r.mode)))
    throw new InputError("INVALID_REPORT", "mode 无效");
  const legacyBaziV3 =
    r.schema === "whoami.report.v3" && r.mode === "bazi";
  const legacyBaziV4 =
    r.schema === "whoami.report.v4" && r.mode === "bazi";
  if (
    r.schema !== "whoami.report.v6" &&
    r.schema !== "whoami.report.v5" &&
    !legacyBaziV3 &&
    !legacyBaziV4
  )
    throw new InputError(
      "INVALID_REPORT",
      "报告 schema 无效；新报告须使用 v6，v5 仅兼容不含相对时间的既有报告，八字单体系 v3/v4 仅作兼容读取",
    );
  if (r.chartId !== evidence.chartId || r.evidenceId !== evidence.evidenceId)
    throw new InputError(
      "STALE_REPORT",
      "报告绑定的出生资料、计算版本或流年范围已变，必须重新分析",
    );
  let timeReference: Report["timeReference"] = null;
  if (r.schema === "whoami.report.v6") {
    const rawReference = object(r.timeReference, "timeReference");
    const asOfDate = string(rawReference.asOfDate, "timeReference.asOfDate");
    const timeZone = string(rawReference.timeZone, "timeReference.timeZone");
    if (!validIsoDate(asOfDate))
      throw new InputError(
        "INVALID_REPORT",
        "timeReference.asOfDate 必须是有效的 YYYY-MM-DD 日期",
      );
    try {
      new Intl.DateTimeFormat("en-US", { timeZone }).format(0);
    } catch {
      throw new InputError(
        "INVALID_REPORT",
        "timeReference.timeZone 必须是有效的 IANA 时区",
      );
    }
    timeReference = { asOfDate, timeZone };
  } else if (r.timeReference !== undefined)
    throw new InputError(
      "INVALID_REPORT",
      "timeReference 只属于 whoami.report.v6；旧报告不能靠追加字段冒充迁移",
    );
  const referenceYear = timeReference
    ? Number(timeReference.asOfDate.slice(0, 4))
    : null;
  const monthly = monthlyLabels(evidence);
  const temporalText = (
    value: unknown,
    label: string,
    role: "prose" | "title" | "reality-source" = "prose",
  ) =>
    validateReportTemporalText(
      reportText(value, label),
      label,
      evidence.years,
      referenceYear,
      {
        role,
        asOfDate: timeReference?.asOfDate,
        birth: evidence.input,
        monthlyLabels: monthly,
      },
    );
  temporalText(r.title, "title", "title");
  temporalText(r.uncertainty, "uncertainty");
  const factMap = new Map(evidence.facts.map((f) => [f.id, f]));
  const ruleMap = new Map(evidence.rules.map((x) => [x.id, x]));
  const refs = (v: unknown, map: Map<string, unknown>, label: string) =>
    array(v, label).map((x) => {
      if (typeof x !== "string" || !map.has(x))
        throw new InputError(
          "INVALID_REFERENCE",
          `${label} 引用了不存在的依据`,
        );
      return x;
    });
  const reasoning = array(r.baziReasoning, "baziReasoning");
  if (r.mode === "ziwei" && reasoning.length)
    throw new InputError("MODE_MISMATCH", "紫微单体系不能混入八字论证");
  const reasoningSeen = new Set<string>();
  const baziNarratives = new Map<string, Map<string, string>>();
  const reasoningStatuses = new Map<string, "conditional" | "unresolved">();
  const reasoningFactRefs = new Map<string, Set<string>>();
  const baziTimingYears = new Map<string, Set<number>>();
  for (const item of reasoning) {
    const a = object(item, "八字论证");
    const candidate = string(a.candidate, "candidate");
    const topic = string(a.topic, "topic");
    const key = `${candidate}:${topic}`;
    if (!evidence.candidateIds.includes(candidate) ||
        !BAZI_TOPICS.includes(topic as BaziReasoning["topic"]) || reasoningSeen.has(key))
      throw new InputError("INVALID_REPORT", "八字论证候选/主题未知或重复");
    if (topic === "bazi-timing" && r.schema !== "whoami.report.v6")
      throw new InputError(
        "INVALID_REPORT",
        "bazi-timing 只属于 whoami.report.v6；旧报告不能靠追加主题冒充迁移",
      );
    reasoningSeen.add(key);
    if (!["conditional", "unresolved"].includes(String(a.status)))
      throw new InputError("INVALID_REPORT", "八字论证必须注明条件性判断或未决");
    reasoningStatuses.set(
      key,
      a.status as "conditional" | "unresolved",
    );
    const narrative = REASONING_NARRATIVE_FIELDS.map((field) =>
      temporalText(a[field], `八字论证.${field}`)
    );
    recordReasoningNarrative(
      baziNarratives,
      candidate,
      topic,
      narrative,
      "八字",
    );
    const support = refs(a.supportRefs, factMap, "supportRefs");
    const counter = refs(a.counterRefs, factMap, "counterRefs");
    if (!support.length)
      throw new InputError("UNSUPPORTED_CLAIM", "八字论证须有盘面依据，未决也须说明基于哪些事实");
    const all = [...support, ...counter];
    if (new Set(support).size !== support.length || new Set(counter).size !== counter.length)
      throw new InputError("INVALID_REFERENCE", "单侧依据不可重复计数");
    if (all.some(id => factMap.get(id)!.candidate !== candidate || factMap.get(id)!.system !== "bazi"))
      throw new InputError("INVALID_REFERENCE", "八字论证不能混入另一候选或体系的事实");
    const rules = refs(a.ruleRefs, ruleMap, "baziReasoning.ruleRefs");
    if (!rules.length || rules.some(id => ruleMap.get(id)!.candidate !== candidate ||
        !ruleMap.get(id)!.factRefs.some(f => all.includes(f))))
      throw new InputError("UNSUPPORTED_CLAIM", "八字论证的每条规则须关联本候选的引用事实");
    const typedTopic = topic as BaziReasoning["topic"];
    if (typedTopic !== "bazi-timing" && a.years !== undefined)
      throw new InputError(
        "INVALID_REPORT",
        "只有 bazi-timing 可以填写 years",
      );
    if (typedTopic !== "bazi-timing" && a.timingChain !== undefined)
      throw new InputError(
        "INVALID_REPORT",
        "只有 bazi-timing 可以填写 timingChain",
      );
    if (typedTopic === "bazi-timing") {
      const years = array(a.years, "baziReasoning.years").map((year) => {
        if (!Number.isInteger(year) || !evidence.years.includes(year as number))
          throw new InputError(
            "INVALID_REPORT",
            "baziReasoning.years 只能填写当前证据包内的流年",
          );
        return year as number;
      });
      if (
        new Set(years).size !== years.length ||
        years.some((year, index) => index > 0 && year <= years[index - 1]!)
      )
        throw new InputError(
          "INVALID_REPORT",
          "baziReasoning.years 必须去重并按升序排列",
        );
      const mentionedYears = [...new Set([
        ...referencedEvidenceYears(narrative.join("\n"), evidence.years),
        ...referencedRelativeYears(narrative.join("\n"), referenceYear),
      ])];
      if (mentionedYears.some((year) => !years.includes(year)))
        throw new InputError(
          "MISSING_TIMING_YEAR",
          "bazi-timing 论证文字涉及的年份必须全部纳入 years",
        );
      baziTimingYears.set(candidate, new Set(years));
    }
    if (
      !rules.some((id) =>
        BAZI_TOPIC_RULE_SUFFIXES[typedTopic].some((suffix) =>
          id.endsWith(suffix)
        )
      )
    )
      throw new InputError(
        "MISSING_TOPIC_RULE",
        `${topic} 必须引用当前候选对应的八字主题规则`,
      );
    const hasFact = (suffix: string) => all.some((id) => id.endsWith(suffix));
    const hasTopicEvidence = {
      strength:
        hasFact(".bazi.month") && hasFact(".bazi.rootDetails"),
      pattern:
        hasFact(".bazi.monthExposure") ||
        hasFact(".bazi.patternReview") ||
        hasFact(".bazi.externalPatterns"),
      climate: hasFact(".bazi.month"),
      balance:
        hasFact(".bazi.rootDetails") || hasFact(".bazi.relations"),
      selection:
        hasFact(".bazi.monthExposure") ||
        hasFact(".bazi.wealthReview") ||
        hasFact(".bazi.patternReview") ||
        hasFact(".bazi.externalPatterns") ||
        hasFact(".bazi.rootDetails"),
      "bazi-timing": hasFact(".bazi.cycles"),
    }[typedTopic];
    if (!hasTopicEvidence)
      throw new InputError(
        "MISSING_TOPIC_EVIDENCE",
        `${topic} 缺少当前八字主题要求的结构化事实锚点`,
      );
    if (typedTopic === "bazi-timing") {
      if (a.timingChain === undefined)
        throw new InputError(
          "INVALID_REPORT",
          "bazi-timing 必须填写 timingChain",
        );
      const chain = object(a.timingChain, "baziReasoning.timingChain");
      if (
        !["career", "wealth", "relationships", "general"].includes(
          String(chain.target),
        )
      )
        throw new InputError(
          "INVALID_REPORT",
          "bazi timingChain.target 必须是事业、财运、关系或综合主题",
        );
      const chainRefs = (
        value: unknown,
        label: string,
        matches: (id: string) => boolean,
      ) => {
        const ids = refs(value, factMap, label);
        if (
          !ids.length ||
          new Set(ids).size !== ids.length ||
          ids.some(
            (id) =>
              !matches(id) ||
              factMap.get(id)!.candidate !== candidate ||
              factMap.get(id)!.system !== "bazi" ||
              !all.includes(id),
          )
        )
          throw new InputError(
            "INVALID_REFERENCE",
            `${label} 必须非空、同候选、类型正确、不可重复，并已纳入本项论证依据`,
          );
        return ids;
      };
      const cycleRefs = chainRefs(
        chain.cycleRefs,
        "bazi timingChain.cycleRefs",
        (id) => id.endsWith(".bazi.cycles"),
      );
      const annualFacts = new Map<
        number,
        { pillar: string; boundary: string }
      >();
      for (const id of cycleRefs) {
        const value = factMap.get(id)!.value;
        if (!value || typeof value !== "object" || Array.isArray(value))
          throw new InputError(
            "FACT_MISMATCH",
            "八字运年事实结构无效，不能建立 timingChain",
          );
        const yearly = (value as { yearly?: unknown }).yearly;
        if (!Array.isArray(yearly))
          throw new InputError(
            "FACT_MISMATCH",
            "八字运年事实缺少逐年列表，不能建立 timingChain",
          );
        for (const rawAnnual of yearly) {
          if (!rawAnnual || typeof rawAnnual !== "object" || Array.isArray(rawAnnual))
            continue;
          const annual = rawAnnual as {
            year?: unknown;
            pillar?: unknown;
            boundary?: unknown;
          };
          if (
            Number.isInteger(annual.year) &&
            typeof annual.pillar === "string" &&
            typeof annual.boundary === "string"
          )
            annualFacts.set(annual.year as number, {
              pillar: annual.pillar,
              boundary: annual.boundary,
            });
        }
      }
      const years = a.years as number[];
      const annualReviews = array(
        chain.annualReviews,
        "bazi timingChain.annualReviews",
      );
      if (annualReviews.length !== years.length)
        throw new InputError(
          "INVALID_REPORT",
          "bazi timingChain.annualReviews 必须逐项覆盖 years",
        );
      annualReviews.forEach((rawAnnual, index) => {
        const annual = object(
          rawAnnual,
          `bazi timingChain.annualReviews[${index}]`,
        );
        const expectedYear = years[index]!;
        if (annual.year !== expectedYear)
          throw new InputError(
            "INVALID_REPORT",
            "bazi timingChain.annualReviews 必须与 years 同序且逐年唯一",
          );
        const expected = annualFacts.get(expectedYear);
        if (!expected)
          throw new InputError(
            "FACT_MISMATCH",
            `八字周期事实没有 ${expectedYear} 年，不能建立逐年复核`,
          );
        const pillar = string(
          annual.pillar,
          `bazi timingChain.annualReviews[${index}].pillar`,
        );
        if (pillar !== expected.pillar || annual.boundary !== expected.boundary)
          throw new InputError(
            "FACT_MISMATCH",
            `${expectedYear} 年干支或年度边界与八字周期事实不一致`,
          );
        const natalRefs = chainRefs(
          annual.natalRefs,
          `bazi timingChain.annualReviews[${index}].natalRefs`,
          (id) => /\.bazi\.(?:year|month|day|hour|relations)$/u.test(id),
        );
        if (!natalRefs.length)
          throw new InputError(
            "INVALID_REFERENCE",
            "八字逐年复核必须引用本命四柱或干支关系事实",
          );
        const review = temporalText(
          annual.review,
          `bazi timingChain.annualReviews[${index}].review`,
        );
        if (!review.includes(String(expectedYear)) || !review.includes(pillar))
          throw new InputError(
            "INVALID_REPORT",
            "八字逐年复核文字必须明确写出对应年份与干支",
          );
      });
      temporalText(
        chain.crossLayerReview,
        "bazi timingChain.crossLayerReview",
      );
      temporalText(
        chain.withdrawalConditions,
        "bazi timingChain.withdrawalConditions",
      );
      const missingLinks = array(
        chain.missingLinks,
        "bazi timingChain.missingLinks",
      ).map((item, index) =>
        temporalText(item, `bazi timingChain.missingLinks[${index}]`),
      );
      if (new Set(missingLinks).size !== missingLinks.length)
        throw new InputError(
          "INVALID_REPORT",
          "bazi timingChain.missingLinks 不能重复",
        );
      const reality = object(
        chain.realityBasis,
        "bazi timingChain.realityBasis",
      );
      if (!["not-provided", "provided"].includes(String(reality.status)))
        throw new InputError(
          "INVALID_REPORT",
          "bazi timingChain.realityBasis.status 无效",
        );
      temporalText(
        reality.summary,
        "bazi timingChain.realityBasis.summary",
      );
      if (reality.status === "not-provided") {
        if (reality.source !== null || !missingLinks.length)
          throw new InputError(
            "INVALID_REPORT",
            "八字现实资料未提供时 source 必须为 null，并明确至少一个未闭合环节",
          );
        if (a.status !== "unresolved")
          throw new InputError(
            "PREMISE_STATUS_MISMATCH",
            "现实触发资料未绑定时 bazi-timing 必须保持 unresolved",
          );
      } else {
        temporalText(
          reality.source,
          "bazi timingChain.realityBasis.source",
          "reality-source",
        );
        if (a.status === "conditional" && missingLinks.length)
          throw new InputError(
            "PREMISE_STATUS_MISMATCH",
            "bazi-timing 收窄为 conditional 前必须清空未闭合环节",
          );
      }
      if (a.status === "unresolved" && !missingLinks.length)
        throw new InputError(
          "PREMISE_STATUS_MISMATCH",
          "未决的 bazi-timing 必须明确至少一个未闭合环节",
        );
    }
    reasoningFactRefs.set(key, new Set(all));
  }
  const requiredBaziTopics = r.schema === "whoami.report.v6"
    ? BAZI_TOPICS
    : BAZI_CORE_TOPICS;
  if (r.mode !== "ziwei" && evidence.candidateIds.some(candidate =>
      requiredBaziTopics.some(topic => !reasoningSeen.has(`${candidate}:${topic}`))))
    throw new InputError(
      "MISSING_REASONING",
      r.schema === "whoami.report.v6"
        ? "每张候选必须分别说明旺衰、格局、调候、扶抑、用神取舍与运年边界"
        : "每张候选必须分别说明旺衰、格局、调候、扶抑与用神取舍",
    );
  const ziweiReasoning = legacyBaziV3
    ? []
    : array(r.ziweiReasoning, "ziweiReasoning");
  if (r.mode === "bazi" && ziweiReasoning.length)
    throw new InputError("MODE_MISMATCH", "八字单体系不能混入紫微论证");
  const ziweiReasoningSeen = new Set<string>();
  const ziweiNarratives = new Map<string, Map<string, string>>();
  const ziweiTimingYears = new Map<string, Set<number>>();
  for (const item of ziweiReasoning) {
    const a = object(item, "紫微论证");
    const candidate = string(a.candidate, "candidate");
    const topic = string(a.topic, "topic");
    const key = `${candidate}:${topic}`;
    if (
      !evidence.candidateIds.includes(candidate) ||
      !ZIWEI_TOPICS.includes(topic as ZiweiReasoning["topic"]) ||
      ziweiReasoningSeen.has(key)
    )
      throw new InputError("INVALID_REPORT", "紫微论证候选/主题未知或重复");
    ziweiReasoningSeen.add(key);
    if (!["conditional", "unresolved"].includes(String(a.status)))
      throw new InputError("INVALID_REPORT", "紫微论证必须注明条件性判断或未决");
    reasoningStatuses.set(
      key,
      a.status as "conditional" | "unresolved",
    );
    const narrative = REASONING_NARRATIVE_FIELDS.map((field) =>
      temporalText(a[field], `紫微论证.${field}`)
    );
    recordReasoningNarrative(
      ziweiNarratives,
      candidate,
      topic,
      narrative,
      "紫微",
    );
    const support = refs(a.supportRefs, factMap, "ziweiReasoning.supportRefs");
    const counter = refs(a.counterRefs, factMap, "ziweiReasoning.counterRefs");
    if (!support.length)
      throw new InputError(
        "UNSUPPORTED_CLAIM",
        "紫微论证须有盘面依据，未决也须说明基于哪些事实",
      );
    const all = [...support, ...counter];
    if (
      new Set(support).size !== support.length ||
      new Set(counter).size !== counter.length
    )
      throw new InputError("INVALID_REFERENCE", "单侧依据不可重复计数");
    if (
      all.some(
        (id) =>
          factMap.get(id)!.candidate !== candidate ||
          factMap.get(id)!.system !== "ziwei",
      )
    )
      throw new InputError(
        "INVALID_REFERENCE",
        "紫微论证不能混入另一候选或体系的事实",
      );
    if (topic !== "ziwei-timing" && a.timingChain !== undefined)
      throw new InputError(
        "INVALID_REPORT",
        "只有 ziwei-timing 可以填写 timingChain",
      );
    if (
      topic === "ziwei-timing" &&
      (r.schema === "whoami.report.v5" || r.schema === "whoami.report.v6")
    ) {
      const chain = object(a.timingChain, "ziweiReasoning.timingChain");
      if (
        !["career", "wealth", "relationships", "general"].includes(
          String(chain.target),
        )
      )
        throw new InputError(
          "INVALID_REPORT",
          "timingChain.target 必须是事业、财运、关系或综合主题",
        );
      const years = array(chain.years, "timingChain.years").map((year) => {
        if (!Number.isInteger(year) || !evidence.years.includes(year as number))
          throw new InputError(
            "INVALID_REPORT",
            "timingChain.years 必须是当前证据包内的流年",
          );
        return year as number;
      });
      if (!years.length || new Set(years).size !== years.length)
        throw new InputError(
          "INVALID_REPORT",
          "timingChain.years 必须非空且不能重复",
        );
      ziweiTimingYears.set(candidate, new Set(years));
      const chainRefs = (
        value: unknown,
        label: string,
        matches: (id: string) => boolean,
      ) => {
        const ids = refs(value, factMap, label);
        if (
          !ids.length ||
          new Set(ids).size !== ids.length ||
          ids.some(
            (id) =>
              !matches(id) ||
              factMap.get(id)!.candidate !== candidate ||
              factMap.get(id)!.system !== "ziwei" ||
              !all.includes(id),
          )
        )
          throw new InputError(
            "INVALID_REFERENCE",
            `${label} 必须非空、同候选、类型正确、不可重复，并已纳入本项论证依据`,
          );
        return ids;
      };
      chainRefs(
        chain.transformationRefs,
        "timingChain.transformationRefs",
        (id) => id.endsWith(".ziwei.transformations"),
      );
      chainRefs(
        chain.cycleRefs,
        "timingChain.cycleRefs",
        (id) => id.endsWith(".ziwei.cycles"),
      );
      const palaceRefs = chainRefs(
        chain.palaceRefs,
        "timingChain.palaceRefs",
        (id) => /\.ziwei\.palace-\d+$/u.test(id),
      );
      const targetPalace = {
        career: "官禄",
        wealth: "财帛",
        relationships: "夫妻",
        general: null,
      }[chain.target as ZiweiTimingChain["target"]];
      if (
        targetPalace &&
        !palaceRefs.some((id) => {
          const value = factMap.get(id)!.value;
          return Boolean(
            value &&
            typeof value === "object" &&
            (value as { name?: unknown }).name === targetPalace,
          );
        })
      )
        throw new InputError(
          "INVALID_REFERENCE",
          `timingChain.target=${chain.target as string} 必须引用对应的${targetPalace}宫事实`,
        );
      temporalText(chain.crossLayerReview, "timingChain.crossLayerReview");
      temporalText(
        chain.withdrawalConditions,
        "timingChain.withdrawalConditions",
      );
      const missingLinks = array(
        chain.missingLinks,
        "timingChain.missingLinks",
      ).map((item, index) =>
        temporalText(item, `timingChain.missingLinks[${index}]`),
      );
      if (new Set(missingLinks).size !== missingLinks.length)
        throw new InputError(
          "INVALID_REPORT",
          "timingChain.missingLinks 不能重复",
        );
      const reality = object(chain.realityBasis, "timingChain.realityBasis");
      if (!["not-provided", "provided"].includes(String(reality.status)))
        throw new InputError(
          "INVALID_REPORT",
          "timingChain.realityBasis.status 无效",
        );
      temporalText(reality.summary, "timingChain.realityBasis.summary");
      if (reality.status === "not-provided") {
        if (reality.source !== null || !missingLinks.length)
          throw new InputError(
            "INVALID_REPORT",
            "现实资料未提供时 source 必须为 null，并明确至少一个未闭合环节",
          );
        if (a.status !== "unresolved")
          throw new InputError(
            "PREMISE_STATUS_MISMATCH",
            "现实触发资料未绑定时 ziwei-timing 必须保持 unresolved",
          );
      } else {
        temporalText(
          reality.source,
          "timingChain.realityBasis.source",
          "reality-source",
        );
        if (a.status === "conditional" && missingLinks.length)
          throw new InputError(
            "PREMISE_STATUS_MISMATCH",
            "ziwei-timing 收窄为 conditional 前必须清空未闭合环节",
          );
      }
    }
    const rules = refs(
      a.ruleRefs,
      ruleMap,
      "ziweiReasoning.ruleRefs",
    );
    if (
      !rules.length ||
      rules.some(
        (id) =>
          ruleMap.get(id)!.candidate !== candidate ||
          !ruleMap.get(id)!.factRefs.some((fact) => all.includes(fact)),
      )
    )
      throw new InputError(
        "UNSUPPORTED_CLAIM",
        "紫微论证的每条规则须关联本候选的引用事实",
      );
    const typedTopic = topic as ZiweiReasoning["topic"];
    if (
      !rules.some((id) =>
        ZIWEI_TOPIC_RULE_SUFFIXES[typedTopic].some((suffix) =>
          id.endsWith(suffix)
        )
      )
    )
      throw new InputError(
        "MISSING_TOPIC_RULE",
        `${topic} 必须引用当前候选对应的紫微主题规则`,
      );
    const targetPalace = ZIWEI_TOPIC_PALACE[typedTopic];
    if (targetPalace) {
      const topicFacts = all.map((id) => factMap.get(id)!);
      const hasTargetPalace = topicFacts.some((fact) =>
        /\.ziwei\.palace-\d+$/u.test(fact.id) &&
        Boolean(
          fact.value &&
          typeof fact.value === "object" &&
          (fact.value as { name?: unknown }).name === targetPalace,
        )
      );
      const hasStructureBase = topicFacts.some((fact) =>
        fact.id.endsWith(".ziwei.base")
      );
      if (!hasTargetPalace || (typedTopic === "ziwei-structure" && !hasStructureBase))
        throw new InputError(
          "MISSING_TOPIC_EVIDENCE",
          typedTopic === "ziwei-structure"
            ? "ziwei-structure 必须同时引用本命基础与命宫事实"
            : `${topic} 必须引用对应的${targetPalace}宫事实`,
          );
    }
    reasoningFactRefs.set(key, new Set(all));
  }
  if (
    r.mode !== "bazi" &&
    evidence.candidateIds.some((candidate) =>
      ZIWEI_TOPICS.some(
        (topic) => !ziweiReasoningSeen.has(`${candidate}:${topic}`),
      ),
    )
  )
    throw new InputError(
      "MISSING_REASONING",
      "每张候选必须分别说明紫微本命结构、事业、财运、关系与限运四化",
    );
  const validatePremise = (
    rawRefs: unknown,
    rawStatus: unknown,
    factRefs: string[],
    text: string,
    label: string,
    requiredZiweiTopic?: (typeof ZIWEI_TOPICS)[number],
  ) => {
    const candidatesBySystem = {
      bazi: new Set<string>(),
      ziwei: new Set<string>(),
    };
    for (const id of factRefs) {
      const fact = factMap.get(id)!;
      if (fact.system === "bazi" || fact.system === "ziwei")
        candidatesBySystem[fact.system].add(fact.candidate);
    }
    const links = array(rawRefs, `${label}.reasoningRefs`).map((raw) => {
      const link = object(raw, `${label}.reasoningRef`);
      const topic =
        typeof link.topic === "string"
          ? link.topic
          : "";
      const system = BAZI_TOPICS.includes(topic as BaziReasoning["topic"])
        ? "bazi"
        : ZIWEI_TOPICS.includes(topic as ZiweiReasoning["topic"])
          ? "ziwei"
          : null;
      if (
        typeof link.candidate !== "string" ||
        !system
      )
        throw new InputError(
          "INVALID_REASONING_LINK",
          `${label} 的论证引用格式无效`,
        );
      const value = {
        candidate: link.candidate,
        topic: topic as ReasoningRef["topic"],
        system,
      };
      const key = `${value.candidate}:${value.topic}`;
      if (
        !reasoningStatuses.has(key) ||
        !candidatesBySystem[system].has(value.candidate)
      )
        throw new InputError(
          "INVALID_REASONING_LINK",
          `${label} 引用了未声明、另一候选、另一体系或与本项事实无关的论证`,
        );
      return value;
    });
    const keys = links.map((link) => `${link.candidate}:${link.topic}`);
    if (new Set(keys).size !== keys.length)
      throw new InputError(
        "INVALID_REASONING_LINK",
        `${label} 的论证引用不能重复`,
      );
    for (const system of ["bazi", "ziwei"] as const)
      if (
        [...candidatesBySystem[system]].some(
          (candidate) =>
            !links.some(
              (link) =>
                link.candidate === candidate && link.system === system,
            ),
        )
      )
        throw new InputError(
          "MISSING_REASONING_LINK",
          `${label} 的每个${system === "bazi" ? "八字" : "紫微"}候选事实都必须绑定具体论证前提`,
        );
    if (
      !candidatesBySystem.bazi.size &&
      !candidatesBySystem.ziwei.size &&
      links.length
    )
      throw new InputError(
        "INVALID_REASONING_LINK",
        `${label} 没有八字或紫微事实，不应绑定论证`,
      );
    const requiredTopics = requiredReasoningTopics(text);
    for (const candidate of candidatesBySystem.bazi)
      for (const topic of requiredTopics)
        if (
          !links.some(
            (link) => link.candidate === candidate && link.topic === topic,
          )
        )
          throw new InputError(
            "MISSING_REASONING_LINK",
            `${label} 提到${BAZI_TITLES[topic]}，但未绑定该候选的对应论证`,
          );
    if (r.schema === "whoami.report.v6")
      for (const candidate of candidatesBySystem.bazi) {
        const citesCycles = factRefs.some((id) => {
          const fact = factMap.get(id)!;
          return (
            fact.candidate === candidate &&
            fact.system === "bazi" &&
            /\.bazi\.(?:cycles|cycleRelations|monthlyCycles)$/u.test(fact.id)
          );
        });
        if (
          citesCycles &&
          !links.some(
            (link) =>
              link.candidate === candidate && link.topic === "bazi-timing",
          )
        )
          throw new InputError(
            "MISSING_REASONING_LINK",
            `${label} 引用了八字大运、流年或岁运关系事实，但未绑定该候选的 bazi-timing 论证`,
          );
      }
    // 流月：引用流月事实须绑定该体系运限论证；正文写出流月标签须引用对应体系的流月事实。
    for (const candidate of candidatesBySystem.ziwei)
      if (
        factRefs.includes(`${candidate}.ziwei.monthly`) &&
        !links.some((l) => l.candidate === candidate && l.topic === "ziwei-timing")
      )
        throw new InputError(
          "MISSING_REASONING_LINK",
          `${label} 引用了紫微流月事实，但未绑定该候选的 ziwei-timing 论证`,
        );
    const mentionedSystems = new Set(
      // 与 temporalText 使用同一份上下文，保证屏蔽口径一致。
      monthlyLabelMentions(
        text,
        { role: "prose", asOfDate: timeReference?.asOfDate, birth: evidence.input, monthlyLabels: monthly },
        label,
      ).map((m) => m.system),
    );
    for (const [system, key] of [["八字", ".bazi.monthlyCycles"], ["紫微", ".ziwei.monthly"]] as const)
      if (mentionedSystems.has(system) && !factRefs.some((id) => id.endsWith(key)))
        throw new InputError(
          "MISSING_TOPIC_EVIDENCE",
          `${label} 写出了${system}流月，但未引用该体系的流月事实`,
        );
    if (requiredZiweiTopic)
      for (const candidate of candidatesBySystem.ziwei)
        if (
          !links.some(
            (link) =>
              link.candidate === candidate &&
              link.topic === requiredZiweiTopic,
          )
        )
          throw new InputError(
            "MISSING_REASONING_LINK",
            `${label} 属于${ZIWEI_TITLES[requiredZiweiTopic]}主题，但未绑定该候选的对应紫微论证`,
          );
    const mentionedYears = [...new Set([
      ...referencedEvidenceYears(text, evidence.years),
      ...referencedRelativeYears(text, referenceYear),
    ])].sort((a, b) => a - b);
    if (r.schema === "whoami.report.v6" && mentionedYears.length)
      for (const candidate of candidatesBySystem.bazi) {
        if (
          !links.some(
            (link) =>
              link.candidate === candidate && link.topic === "bazi-timing",
          )
        )
          throw new InputError(
            "MISSING_REASONING_LINK",
            `${label} 提到当前证据范围内的具体年份，但未绑定该候选的 bazi-timing 论证`,
          );
        const covered = baziTimingYears.get(candidate);
        if (!covered || mentionedYears.some((year) => !covered.has(year)))
          throw new InputError(
            "MISSING_TIMING_YEAR",
            `${label} 提到的年份未全部纳入该候选 bazi-timing.years`,
          );
      }
    if (mentionedYears.length)
      for (const candidate of candidatesBySystem.ziwei) {
        if (
          !links.some(
            (link) =>
              link.candidate === candidate &&
              link.topic === "ziwei-timing",
          )
        )
          throw new InputError(
            "MISSING_REASONING_LINK",
            `${label} 提到当前证据范围内的具体年份，但未绑定该候选的 ziwei-timing 论证`,
          );
        const covered = ziweiTimingYears.get(candidate);
        if (
          !covered ||
          mentionedYears.some((year) => !covered.has(year))
        )
          throw new InputError(
            "MISSING_TIMING_YEAR",
            `${label} 提到的年份未全部纳入该候选 timingChain.years`,
          );
      }
    const expected = !links.length
      ? "not-applicable"
      : links.some(
            (link) =>
              reasoningStatuses.get(`${link.candidate}:${link.topic}`) ===
              "unresolved",
          )
        ? "unresolved"
        : "conditional";
    if (rawStatus !== expected)
      throw new InputError(
        "PREMISE_STATUS_MISMATCH",
        `${label}.premiseStatus 必须与所引八字与紫微论证状态一致`,
      );
    if (expected === "unresolved")
      assertNoUnresolvedPremiseUpgrade(text, label);
    return links.map(({ candidate, topic }) => ({ candidate, topic }));
  };
  const sections = array(r.sections, "sections");
  const seen = new Set<string>();
  const candidateCoverage = new Map<string, Set<"bazi" | "ziwei">>();
  for (const s0 of sections) {
    const s = object(s0, "section");
    const id = string(s.id, "section.id");
    if (
      !SECTION_IDS.includes(id as (typeof SECTION_IDS)[number]) ||
      seen.has(id)
    )
      throw new InputError("INVALID_REPORT", "章节缺失、重复或未知");
    seen.add(id);
    const claims = array(s.claims, "claims");
    if (!claims.length)
      throw new InputError("INVALID_REPORT", "章节不能没有解读");
    for (const c0 of claims) {
      const c = object(c0, "claim");
      temporalText(c.text, "claim.text");
      temporalText(c.conditions, "claim.conditions");
      if (
        !["interpretation", "advice"].includes(String(c.kind)) ||
        !["low", "medium", "high"].includes(String(c.confidence))
      )
        throw new InputError("INVALID_REPORT", "claim 类型或置信度无效");
      const fr = refs(c.factRefs, factMap, "factRefs");
      validatePremise(
        c.reasoningRefs,
        c.premiseStatus,
        fr,
        `${c.text as string}\n${c.conditions as string}`,
        `section.${id}.claim`,
        ZIWEI_SECTION_TOPIC[id as (typeof SECTION_IDS)[number]],
      );
      for (const ref of fr) {
        const fact = factMap.get(ref)!;
        if (fact.system === "bazi" || fact.system === "ziwei") {
          const covered = candidateCoverage.get(fact.candidate) ?? new Set();
          covered.add(fact.system);
          candidateCoverage.set(fact.candidate, covered);
        }
      }
      const rr = refs(c.ruleRefs, ruleMap, "ruleRefs");
      if (!fr.length || !rr.length)
        throw new InputError(
          "UNSUPPORTED_CLAIM",
          "每项解读/建议必须引用事实和规则",
        );
      const allowedSystem =
        r.mode === "combined" ? ["bazi", "ziwei", "input"] : [r.mode, "input"];
      if (fr.some((ref) => !allowedSystem.includes(factMap.get(ref)!.system)))
        throw new InputError("MODE_MISMATCH", "单体系报告引用了另一体系");
      if (!rr.every((ref) => {
        const rule = ruleMap.get(ref)!;
        return rule.factRefs.some((factRef) => {
          if (!fr.includes(factRef)) return false;
          const fact = factMap.get(factRef)!;
          return fact.candidate === rule.candidate;
        });
      }))
        throw new InputError("UNSUPPORTED_CLAIM", "每条引用规则均须关联引用事实");
    }
  }
  if (seen.size !== SECTION_IDS.length)
    throw new InputError("INVALID_REPORT", "七个报告章节必须完整");
  const cross = array(r.crossSystem, "crossSystem");
  if (r.mode === "combined" && !cross.length)
    throw new InputError("INVALID_REPORT", "综合报告必须说明体系关系");
  if (r.mode !== "combined" && cross.length)
    throw new InputError("MODE_MISMATCH", "单体系报告不应伪造跨体系印证");
  for (const x0 of cross) {
    const x = object(x0, "crossSystem item");
    const text = temporalText(x.text, "crossSystem.text");
    if (
      !["supports", "complements", "conflicts", "insufficient"].includes(
        String(x.relationship),
      )
    )
      throw new InputError("INVALID_REPORT", "体系关系无效");
    let target: CrossSystemTarget | undefined;
    let years: number[] = [];
    if (r.schema === "whoami.report.v6") {
      if (!CROSS_SYSTEM_TARGETS.includes(x.target as CrossSystemTarget))
        throw new InputError(
          "CROSS_SYSTEM_SCOPE_MISMATCH",
          "v6 跨体系判断必须声明 general/career/wealth/relationships/timing 之一作为 target",
        );
      target = x.target as CrossSystemTarget;
      years = array(x.years, "crossSystem.years").map((year) => {
        if (!Number.isInteger(year) || !evidence.years.includes(year as number))
          throw new InputError(
            "CROSS_SYSTEM_SCOPE_MISMATCH",
            "crossSystem.years 只能填写当前证据包内的流年",
          );
        return year as number;
      });
      if (
        new Set(years).size !== years.length ||
        years.some((year, index) => index > 0 && year <= years[index - 1]!)
      )
        throw new InputError(
          "CROSS_SYSTEM_SCOPE_MISMATCH",
          "crossSystem.years 必须去重并按升序排列",
        );
      const mentionedYears = [...new Set([
        ...referencedEvidenceYears(text, evidence.years),
        ...referencedRelativeYears(text, referenceYear),
      ])].sort((a, b) => a - b);
      if (!isDeepStrictEqual(years, mentionedYears))
        throw new InputError(
          "CROSS_SYSTEM_SCOPE_MISMATCH",
          "crossSystem.years 必须与正文涉及的 evidence 年份完全一致",
        );
      if (target === "timing" && !years.length)
        throw new InputError(
          "CROSS_SYSTEM_SCOPE_MISMATCH",
          "target=timing 必须声明至少一个当前证据年份",
        );
    }
    const rr = refs(x.factRefs, factMap, "crossSystem.factRefs");
    const links = validatePremise(
      x.reasoningRefs,
      x.premiseStatus,
      rr,
      text,
      "crossSystem",
    );
    for (const ref of rr) {
      const fact = factMap.get(ref)!;
      if (fact.system === "bazi" || fact.system === "ziwei") {
        const covered = candidateCoverage.get(fact.candidate) ?? new Set();
        covered.add(fact.system);
        candidateCoverage.set(fact.candidate, covered);
      }
    }
    if (
      !["bazi", "ziwei"].every((system) =>
        rr.some((ref) => factMap.get(ref)!.system === system),
      )
    )
      throw new InputError(
        "UNSUPPORTED_CLAIM",
        "综合判断必须同时引用两体系事实",
      );
    const candidates = new Set(rr.map(ref => factMap.get(ref)!.candidate));
    if ([...candidates].some(candidate => !["bazi", "ziwei"].every(system =>
      rr.some(ref => factMap.get(ref)!.candidate === candidate && factMap.get(ref)!.system === system))))
      throw new InputError("CANDIDATE_MISMATCH", "跨体系判断须在同一候选内分别提供两体系事实，不可拼盘印证");
    const strongRelationship = x.relationship !== "insufficient";
    if (r.schema === "whoami.report.v6" && strongRelationship) {
      if (x.premiseStatus !== "conditional")
        throw new InputError(
          "UNRESOLVED_CROSS_SYSTEM_RELATIONSHIP",
          "前提仍为 unresolved 时，跨体系关系只能标为 insufficient",
        );
      if (candidates.size !== 1)
        throw new InputError(
          "CROSS_SYSTEM_SCOPE_MISMATCH",
          "supports/complements/conflicts 每项只能比较一个候选",
        );
      const candidate = [...candidates][0]!;
      const requiredTopic = CROSS_SYSTEM_TARGET_TOPIC[target!];
      if (
        !links.some(
          (link) =>
            link.candidate === candidate && link.topic === requiredTopic,
        )
      )
        throw new InputError(
          "CROSS_SYSTEM_SCOPE_MISMATCH",
          `target=${target} 必须绑定 ${requiredTopic} 论证`,
        );
      for (const system of ["bazi", "ziwei"] as const) {
        const hasDirectReasoningEvidence = links.some((link) => {
          const linkSystem = BAZI_TOPICS.includes(
            link.topic as BaziReasoning["topic"],
          )
            ? "bazi"
            : "ziwei";
          if (link.candidate !== candidate || linkSystem !== system)
            return false;
          const evidenceRefs = reasoningFactRefs.get(
            `${link.candidate}:${link.topic}`,
          );
          return Boolean(evidenceRefs && rr.some((ref) => evidenceRefs.has(ref)));
        });
        if (!hasDirectReasoningEvidence)
          throw new InputError(
            "CROSS_SYSTEM_SCOPE_MISMATCH",
            `跨体系强关系的${system === "bazi" ? "八字" : "紫微"}事实必须直接落在所绑定论证的依据中`,
          );
      }
      const ziweiFacts = rr
        .map((ref) => factMap.get(ref)!)
        .filter(
          (fact) => fact.candidate === candidate && fact.system === "ziwei",
        );
      const hasPalace = (name: string) =>
        ziweiFacts.some(
          (fact) =>
            /\.ziwei\.palace-\d+$/u.test(fact.id) &&
            Boolean(
              fact.value &&
              typeof fact.value === "object" &&
              (fact.value as { name?: unknown }).name === name,
            ),
        );
      const hasTargetEvidence = {
        general:
          ziweiFacts.some((fact) => fact.id.endsWith(".ziwei.base")) &&
          hasPalace("命宫"),
        career: hasPalace("官禄"),
        wealth: hasPalace("财帛"),
        relationships: hasPalace("夫妻"),
        timing:
          ziweiFacts.some((fact) => /\.ziwei\.(?:cycles|monthly)$/u.test(fact.id)) &&
          ziweiFacts.some((fact) =>
            fact.id.endsWith(".ziwei.transformations")
          ),
      }[target!];
      if (!hasTargetEvidence)
        throw new InputError(
          "CROSS_SYSTEM_SCOPE_MISMATCH",
          `target=${target} 缺少直接引用的对应紫微主题事实`,
        );
      if (years.length) {
        const baziHasCycles = rr.some((ref) => {
          const fact = factMap.get(ref)!;
          return (
            fact.candidate === candidate &&
            fact.system === "bazi" &&
            /\.bazi\.(?:cycles|cycleRelations|monthlyCycles)$/u.test(fact.id)
          );
        });
        // 与八字侧一致：年度运限或流月事实都可作为紫微运限依据。
        const ziweiHasCycles = ziweiFacts.some((fact) =>
          /\.ziwei\.(?:cycles|monthly)$/u.test(fact.id)
        );
        const ziweiHasTransformations = ziweiFacts.some((fact) =>
          fact.id.endsWith(".ziwei.transformations")
        );
        const hasBaziTimingLink = links.some(
          (link) =>
            link.candidate === candidate && link.topic === "bazi-timing",
        );
        const hasZiweiTimingLink = links.some(
          (link) =>
            link.candidate === candidate && link.topic === "ziwei-timing",
        );
        if (
          !baziHasCycles ||
          !ziweiHasCycles ||
          !ziweiHasTransformations ||
          !hasBaziTimingLink ||
          !hasZiweiTimingLink
        )
          throw new InputError(
            "MISSING_CROSS_SYSTEM_TIMING",
            "带年份的强关系必须同时引用八字运年、紫微运限与四化事实，并绑定 bazi-timing 与 ziwei-timing",
          );
      }
    }
  }
  const requiredSystems: readonly ("bazi" | "ziwei")[] =
    r.mode === "combined"
      ? ["bazi", "ziwei"]
      : [r.mode as "bazi" | "ziwei"];
  if (
    evidence.candidateIds.some((id) =>
      requiredSystems.some(
        (system) => !candidateCoverage.get(id)?.has(system),
      ),
    )
  )
    throw new InputError(
      "MISSING_CANDIDATE",
      "报告遗漏候选盘在当前模式下的命盘事实；输入元数据不能代替实际分析",
    );
  for (const a0 of array(r.assertions, "assertions")) {
    const a = object(a0, "assertion");
    const f = factMap.get(string(a.factRef, "assertion.factRef"));
    if (f && r.mode !== "combined" && f.system !== r.mode && f.system !== "input")
      throw new InputError("MODE_MISMATCH", "单体系报告的事实断言引用了另一体系");
    if (!f || !isDeepStrictEqual(a.value, f.value))
      throw new InputError(
        "FACT_MISMATCH",
        "报告的结构化事实断言与计算结果不一致",
      );
  }
  if (r.schema === "whoami.report.v6") {
    const scopes = ziweiScopes(evidence);
    const ziweiHints = (factRefs: string[], links: ReasoningRef[]) => [
      ...factRefs
        .map((id) => factMap.get(id))
        .filter((f) => f?.system === "ziwei")
        .map((f) => f!.candidate),
      ...links
        .filter((l) => ZIWEI_TOPICS.includes(l.topic as ZiweiReasoning["topic"]))
        .map((l) => l.candidate),
    ];
    // 多候选且线索不唯一的文本无法确定宫位归属，不做自动核对。
    const checkTexts = (texts: string[], hints: string[], label: string) => {
      const scope = scopeForText(scopes, hints);
      if (scope)
        for (const text of texts) assertZiweiPalaceScope(text, scope, label);
    };
    checkTexts([r.title as string, r.uncertainty as string], [], "report");
    for (const section of r.sections as Report["sections"])
      section.claims.forEach((claim, i) =>
        checkTexts(
          [claim.text, claim.conditions],
          ziweiHints(claim.factRefs, claim.reasoningRefs),
          `${section.id}.claims[${i}]`,
        ),
      );
    const chainTexts = (chain?: {
      crossLayerReview: string;
      withdrawalConditions: string;
      realityBasis: { summary: string };
      missingLinks: string[];
    }) =>
      chain
        ? [
            chain.crossLayerReview,
            chain.withdrawalConditions,
            chain.realityBasis.summary,
            ...chain.missingLinks,
          ]
        : [];
    for (const item of [
      ...(r.baziReasoning as BaziReasoning[]),
      ...(ziweiReasoning as ZiweiReasoning[]),
    ])
      checkTexts(
        [
          item.conclusion,
          item.counterReview,
          item.conditions,
          item.alternatives,
          ...chainTexts(item.timingChain),
        ],
        [item.candidate],
        `${item.topic}(${item.candidate})`,
      );
    for (const [i, item] of (r.crossSystem as Report["crossSystem"]).entries())
      checkTexts(
        [item.text],
        ziweiHints(item.factRefs, item.reasoningRefs),
        `crossSystem[${i}]`,
      );
  }
  return {
    ...r,
    timeReference,
    ziweiReasoning,
  } as unknown as Report;
}
export function reportTemplate(e: Evidence, mode: Report["mode"] = "combined") {
  return {
    schema: "whoami.report.v6",
    chartId: e.chartId,
    evidenceId: e.evidenceId,
    mode,
    timeReference: { asOfDate: "", timeZone: "" },
    title: "whoami 命理解读",
    uncertainty: "",
    sections: SECTION_IDS.map((id) => ({ id, claims: [] })),
    baziReasoning: mode === "ziwei" ? [] : e.candidateIds.flatMap(candidate =>
      BAZI_TOPICS.map(topic => ({ candidate, topic, status: "unresolved", conclusion: "",
        supportRefs: [], counterRefs: [], counterReview: "", conditions: "", alternatives: "", ruleRefs: [],
        ...(topic === "bazi-timing" ? {
          years: [...e.years],
          timingChain: {
            target: "general",
            cycleRefs: [],
            annualReviews: e.years.map(year => {
              const cycle = e.facts.find(fact =>
                fact.candidate === candidate && fact.id.endsWith(".bazi.cycles")
              );
              const yearly = cycle?.value && typeof cycle.value === "object"
                ? (cycle.value as { yearly?: { year: number; pillar: string; boundary: "lichun" }[] }).yearly
                : undefined;
              const annual = yearly?.find(item => item.year === year);
              return {
                year,
                pillar: annual?.pillar ?? "",
                boundary: annual?.boundary ?? "lichun",
                natalRefs: [],
                review: "",
              };
            }),
            crossLayerReview: "",
            missingLinks: [],
            realityBasis: { status: "not-provided", summary: "", source: null },
            withdrawalConditions: "",
          },
        } : {}) }))),
    ziweiReasoning: mode === "bazi" ? [] : e.candidateIds.flatMap(candidate =>
      ZIWEI_TOPICS.map(topic => ({ candidate, topic, status: "unresolved", conclusion: "",
        supportRefs: [], counterRefs: [], counterReview: "", conditions: "", alternatives: "", ruleRefs: [],
        ...(topic === "ziwei-timing" ? { timingChain: {
          target: "general", years: [...e.years], transformationRefs: [], cycleRefs: [], palaceRefs: [],
          crossLayerReview: "", missingLinks: [],
          realityBasis: { status: "not-provided", summary: "", source: null },
          withdrawalConditions: "",
        } } : {}) }))),
    crossSystem: [],
    assertions: [],
  };
}

function cycleUncertaintyFacts(e: Evidence) {
  return e.facts.flatMap((fact) => {
    if (!fact.id.endsWith(".bazi.cycles") || !fact.value || typeof fact.value !== "object")
      return [];
    const cycles = fact.value as {
      uncertainty?: {
        status?: string;
        sampleCount?: number;
        distinctStartCount?: number;
        birthOffsetMinutes?: { min?: number; max?: number };
        solarShiftMinutes?: { min?: number; max?: number };
        startCivil?: { earliest?: string; latest?: string };
      };
    };
    if (cycles.uncertainty?.status !== "range") return [];
    return [{
      candidate: fact.candidate,
      factId: fact.id,
      uncertainty: cycles.uncertainty,
    }];
  });
}

export function renderReport(raw: unknown, e: Evidence): string {
  const r = validateReport(raw, e);
  const factMap = new Map(
    e.facts.map((f, i) => [f.id, { ...f, number: i + 1 }]),
  );
  const referenceLinks = (ids: string[]) =>
    ids
      .map((id) => {
        const f = factMap.get(id)!;
        return `[${f.label}](#fact-${f.number})`;
      })
      .join("、");
  const confidence = { low: "较低", medium: "中等", high: "较高" };
  const relation = {
    supports: "同向支持",
    complements: "互补",
    conflicts: "存在分歧",
    insufficient: "依据不足",
  };
  const candidateLabel = (candidate: string) => {
    const index = e.candidateIds.indexOf(candidate);
    if (index < 0) return candidate;
    return e.candidateIds.length === 1 ? "当前命盘" : `候选 ${index + 1}`;
  };
  const premiseDisplay = (item: {
    premiseStatus: Claim["premiseStatus"];
    reasoningRefs: ReasoningRef[];
  }) => {
    if (item.premiseStatus === "not-applicable") return null;
    const grouped = new Map<string, string[]>();
    const systems = new Set<"八字" | "紫微">();
    for (const ref of item.reasoningRefs) {
      const topics = grouped.get(ref.candidate) ?? [];
      if (BAZI_TOPICS.includes(ref.topic as BaziReasoning["topic"])) {
        systems.add("八字");
        topics.push(
          `八字·${BAZI_TITLES[ref.topic as BaziReasoning["topic"]]}`,
        );
      } else {
        systems.add("紫微");
        topics.push(
          `紫微·${ZIWEI_TITLES[ref.topic as ZiweiReasoning["topic"]]}`,
        );
      }
      grouped.set(ref.candidate, topics);
    }
    const refs = [...grouped]
      .map(([candidate, topics]) => `${candidateLabel(candidate)}：${topics.join("、")}`)
      .join("；");
    const status = item.premiseStatus === "unresolved" ? "未决" : "条件性";
    const scope = [...systems].join("与");
    return {
      status,
      summary:
        status === "未决"
          ? `${scope}论证前提仍未决`
          : `${scope}论证前提为条件性`,
      details: `${scope}论证前提：${status}（${refs}）。`,
    };
  };
  const lines = [
    `# ${r.title}`,
    "",
    "## 资料与口径",
    "",
    `${e.input.calendar === "solar" ? "公历" : "农历"} ${e.input.date}${e.input.leapMonth ? "（闰月）" : ""} ${e.input.time}；${e.input.place}（${e.input.longitude}°），${e.input.timeZone}。`,
    `时间口径：${e.input.timeBasis === "true-solar" ? "真太阳时" : "当地法定时间"}；${e.input.dayBoundary === "zi" ? "23:00 子初换日" : "00:00 午夜换日"}。`,
    ...(r.timeReference
      ? [`报告相对时间基准：${r.timeReference.asOfDate}（${r.timeReference.timeZone}）；“今年／明年”等相对年份均按此日期解析。`]
      : []),
    `资料来源：${[
      `地点=${e.input.provenance?.placeSource ?? "未核验"}`,
      `经度=${e.input.provenance?.longitudeSource ?? "未核验"}`,
      `时区=${e.input.provenance?.timeZoneSource ?? "未核验"}`,
      e.input.provenance?.verifiedAt &&
        `核对时间=${e.input.provenance.verifiedAt}`,
    ].filter(Boolean).join("；")}。`,
    "",
    r.uncertainty,
    "",
    ...e.warnings.map((w) => `> ${w}`),
    "",
  ];
  const glossary = [
    ...(r.mode === "ziwei" ? [] : BAZI_GLOSSARY),
    ...(r.mode === "bazi" ? [] : ZIWEI_GLOSSARY),
  ];
  const supportingLines: string[] = [];
  supportingLines.push(
    "## 术语速查",
    "",
    "以下解释只说明这些词在本报告中的用法，帮助阅读，不替代正文中的具体依据与条件。",
    "",
    "| 术语 | 白话解释 |",
    "|---|---|",
    ...glossary.map(([term, meaning]) => `| ${term} | ${meaning} |`),
    "",
  );
  const cycleReviews = r.mode === "ziwei" ? [] : cycleUncertaintyFacts(e);
  if (cycleReviews.length) {
    supportingLines.push(
      "## 出生时间与起运范围（自动生成）",
      "",
      "以下范围直接来自当前候选内的全部分钟采样。cycles 顶层起运值只是代表样本，不能写成已经确认的唯一时点。",
      "",
    );
    for (const review of cycleReviews) {
      const u = review.uncertainty;
      supportingLines.push(
        `### ${candidateLabel(review.candidate)}`,
        "",
        `- 采样：${u.sampleCount} 个样本，${u.distinctStartCount} 个不同起运结果。`,
        `- 出生时间偏移：${u.birthOffsetMinutes?.min} 至 ${u.birthOffsetMinutes?.max} 分钟；太阳时筛查偏移：${u.solarShiftMinutes?.min} 至 ${u.solarShiftMinutes?.max} 分钟。`,
        `- 起运民用时间范围：${u.startCivil?.earliest} 至 ${u.startCivil?.latest}。`,
        `- 核对依据：${referenceLinks([review.factId])}。`,
        "",
      );
    }
  }
  const coreReviews = r.mode === "ziwei" ? [] : wealthReviewFacts(e);
  if (coreReviews.length) {
    supportingLines.push("## 核心规则复核（自动生成）", "",
      "以下内容直接来自计算证据，覆盖当前财格规则，不是完整格局裁定。正文如提出成格或救应判断，必须回应这里的反例与未决条件；程序不会自动认证正文已完成论证。", "");
    for (const review of coreReviews) {
      supportingLines.push(`### ${candidateLabel(review.candidate)}`, "",
        ...wealthReviewSummary(review.value).map(line => `- ${line}`), "",
        `核对依据：${referenceLinks([review.factId])}。`, "");
    }
  }
  const ziweiReviews = r.mode === "bazi" ? [] : ziweiLayerFacts(e);
  if (ziweiReviews.length) {
    supportingLines.push("## 四化分层核对（自动生成）", "",
      "按请求的农历年份标签，列出同星在生年、对应大限与流年中的不同四化。它们同时保留，不是吉凶评分，不自动抵消，也不证明现实事件；未列出差异不等于已判吉凶。", "");
    for (const review of ziweiReviews) {
      supportingLines.push(`### ${candidateLabel(review.candidate)}`, "");
      for (const year of review.years) {
        supportingLines.push(`**${year.year}年范围**`, "");
        if (!year.contrasts.length) supportingLines.push("本轮可定位项未见同星不同四化；仍需核对作用条件与下列缺口。", "");
        for (const contrast of year.contrasts)
          supportingLines.push(`- ${contrast.star}：${contrast.entries.map(describeLayerEntry).join("；")}。`);
        if (year.contrasts.length) supportingLines.push("");
        for (const gap of year.gaps)
          supportingLines.push(`- 定位缺口：${gap.layer}化${gap.mutagen}，${gap.star ?? "星名缺失"}（${gap.status}），${gap.status === "missing-yearly-palace" ? "本命落宫已定位，流年宫职不补猜" : "不推断唯一落宫"}。`);
        if (year.gaps.length) supportingLines.push("");
      }
      supportingLines.push(`核对依据：${referenceLinks([review.factId])}。大限宫职未计算，不由本命宫名补猜。`, "");
    }
  }
  for (const id of SECTION_IDS) {
    const s = r.sections.find((x) => x.id === id)!;
    lines.push(`## ${TITLES[id]}`, "");
    for (const c of s.claims) {
      const premise = premiseDisplay(c);
      lines.push(
        c.text,
        "",
        `> **解释边界**：传统解释把握为${confidence[c.confidence]}（非发生概率）${premise ? `；${premise.summary}` : ""}。${c.conditions}`,
        "",
        "<details>",
        `<summary>查看本段命盘依据${premise ? "与论证主题" : ""}</summary>`,
        "",
        `命盘依据：${referenceLinks(c.factRefs)}。`,
        ...(premise ? [premise.details] : []),
        "",
        "</details>",
        "",
      );
    }
  }
  if (r.crossSystem.length) {
    lines.push("## 八字与紫微对照", "");
    for (const x of r.crossSystem) {
      const premise = premiseDisplay(x);
      const scope = x.target
        ? `> **对照范围**：${CROSS_SYSTEM_TARGET_TITLES[x.target]}；${
            x.years?.length
              ? `${x.years.join("、")} 年`
              : "不限定具体流年"
          }。`
        : null;
      lines.push(
        `**${relation[x.relationship]}**：${x.text}`,
        ...(scope ? ["", scope] : []),
        ...(premise ? ["", `> **对照边界**：${premise.summary}。`] : []),
        "",
        "<details>",
        `<summary>查看对照依据${premise ? "与论证主题" : ""}</summary>`,
        "",
        `命盘依据：${referenceLinks(x.factRefs)}。`,
        ...(premise ? [premise.details] : []),
        "",
        "</details>",
        "",
      );
    }
  }
  lines.push(...supportingLines);
  if (r.baziReasoning.length) {
    lines.push("## 八字判断的依据与分歧", "");
    for (const a of r.baziReasoning) {
      lines.push(`### ${BAZI_TITLES[a.topic]}（${candidateLabel(a.candidate)}）`, "",
        `**${a.status === "unresolved" ? "尚未定论" : "条件性判断"}**：${a.conclusion}`, "",
        ...(a.topic === "bazi-timing"
          ? [`适用年份：${a.years?.length ? a.years.join("、") : "未请求具体流年"}。`]
          : []),
        `判断依据：${referenceLinks(a.supportRefs)}。`,
        `反证核对：${a.counterReview}${a.counterRefs.length ? ` 相关依据：${referenceLinks(a.counterRefs)}。` : ""}`,
        `成立条件／资料缺口：${a.conditions}`,
        `替代解释与取舍：${a.alternatives}`);
      if (a.timingChain) {
        const target = {
          career: "事业",
          wealth: "财运",
          relationships: "关系",
          general: "综合",
        }[a.timingChain.target];
        lines.push(
          `作用链目标：${target}。`,
          `大运／流年事实：${referenceLinks(a.timingChain.cycleRefs)}。`,
          ...a.timingChain.annualReviews.map(annual =>
            `${annual.review} 年度边界：立春；本命依据：${referenceLinks(annual.natalRefs)}。`
          ),
          `本命—大运—流年复核：${a.timingChain.crossLayerReview}`,
          `现实触发资料：${a.timingChain.realityBasis.status === "provided" ? `已提供（${a.timingChain.realityBasis.source}）` : "未提供"}；${a.timingChain.realityBasis.summary}`,
          `未闭合环节：${a.timingChain.missingLinks.length ? a.timingChain.missingLinks.join("；") : "无"}`,
          `撤回条件：${a.timingChain.withdrawalConditions}`,
        );
      }
      lines.push("");
    }
  }
  if (r.ziweiReasoning.length) {
    lines.push("## 紫微判断的依据与分歧", "");
    for (const a of r.ziweiReasoning) {
      lines.push(
        `### ${ZIWEI_TITLES[a.topic]}（${candidateLabel(a.candidate)}）`,
        "",
        `**${a.status === "unresolved" ? "尚未定论" : "条件性判断"}**：${a.conclusion}`,
        "",
        `判断依据：${referenceLinks(a.supportRefs)}。`,
        `反证核对：${a.counterReview}${a.counterRefs.length ? ` 相关依据：${referenceLinks(a.counterRefs)}。` : ""}`,
        `成立条件／资料缺口：${a.conditions}`,
        `替代解释与取舍：${a.alternatives}`,
      );
      if (a.timingChain) {
        const target = {
          career: "事业",
          wealth: "财运",
          relationships: "关系",
          general: "综合",
        }[a.timingChain.target];
        lines.push(
          `作用链目标：${target}；年份：${a.timingChain.years.join("、")}。`,
          `四化层依据：${referenceLinks(a.timingChain.transformationRefs)}。`,
          `大限／流年依据：${referenceLinks(a.timingChain.cycleRefs)}。`,
          `主题宫依据：${referenceLinks(a.timingChain.palaceRefs)}。`,
          `跨层复核：${a.timingChain.crossLayerReview}`,
          `现实触发资料：${a.timingChain.realityBasis.status === "provided" ? `已提供（${a.timingChain.realityBasis.source}）` : "未提供"}；${a.timingChain.realityBasis.summary}`,
          `未闭合环节：${a.timingChain.missingLinks.length ? a.timingChain.missingLinks.join("；") : "无"}`,
          `撤回条件：${a.timingChain.withdrawalConditions}`,
        );
      }
      lines.push("");
    }
  }
  const used = new Set(
    r.sections
      .flatMap((s) => s.claims.flatMap((c) => c.factRefs))
      .concat(r.crossSystem.flatMap((x) => x.factRefs),
        r.baziReasoning.flatMap(a => [...a.supportRefs, ...a.counterRefs]),
        r.ziweiReasoning.flatMap(a => [...a.supportRefs, ...a.counterRefs])),
  );
  for (const review of coreReviews) used.add(review.factId);
  for (const review of ziweiReviews) used.add(review.factId);
  for (const review of cycleReviews) used.add(review.factId);
  lines.push("## 可核对的命盘依据", "");
  lines.push(
    "<details>",
    "<summary>展开计算事实与来源</summary>",
    "",
    `命盘版本：${e.chartId}；证据包：${e.evidenceId}。`,
    "",
  );
  for (const f of e.facts.filter((f) => used.has(f.id)))
    lines.push(
      `<a id="fact-${factMap.get(f.id)!.number}"></a>`,
      "",
      `### ${f.label}（${f.candidate}）`,
      "",
      `来源：${f.source}；引用标识：${f.id}`,
      "",
      "```json",
      JSON.stringify(f.value, null, 2),
      "```",
      "",
    );
  const usedRules = new Set(
    r.sections.flatMap((s) => s.claims.flatMap((c) => c.ruleRefs))
      .concat(
        r.baziReasoning.flatMap(a => a.ruleRefs),
        r.ziweiReasoning.flatMap(a => a.ruleRefs),
      ),
  );
  for (const review of coreReviews) usedRules.add(review.ruleId);
  for (const review of ziweiReviews) usedRules.add(review.ruleId);
  lines.push("### 所用分析规则", "");
  for (const rule of e.rules.filter((rule) => usedRules.has(rule.id)))
    lines.push(`- ${rule.label}：${rule.guidance}（${rule.id}）`);
  lines.push("", "</details>");
  lines.push(
    "",
    "本报告是传统命理框架下的条件性解读，不是对现实事件的保证。计算一致性与传统解释质量，不等于现实预测能力。",
    "",
  );
  return lines.join("\n");
}
