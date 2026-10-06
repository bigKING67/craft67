import { InputError } from "./input.js";
import type { Evidence } from "./evidence.js";
import { EVENT_WORDS } from "./report-safety.js";

const KINDS = ["event", "pattern", "timing", "palace", "fact"] as const;
const STANCES = ["conditional", "unresolved", "fact-restatement"] as const;
type Kind = (typeof KINDS)[number];

// 含这些词的分句必须被清单整句覆盖，且覆盖断言须声明对应 kind。事件词在高风险措辞词表之上补充主题词。
const TRIGGERS: Record<Exclude<Kind, "fact">, RegExp> = {
  event: new RegExp(
    `${EVENT_WORDS}|跳槽|婚姻|离婚|分手|收入|进账|进财|支出|赚|亏|破财|财运|疾病|手术|意外|官司|事故|健康|吉凶|吉利|大吉|不吉|凶|有利|不利`,
    "u",
  ),
  // 只认具体格名与术语，避免“性格、价格、资格、风格”误触发。
  pattern:
    /(?:正官|七杀|偏官|正印|偏印|食神|伤官|正财|偏财|财|官|杀|印|建禄|月刃|羊刃|从|化)格|格局|成格|破格|败格|用神|喜用|忌神|身强|身弱|身旺|身衰|偏强|偏弱|旺衰/u,
  timing: /(?:19|20)\d{2}|今年|明年|后年|去年|流年|流月|大运|大限|起运|交运/u,
  palace: /(?:流年|流月|大限)[^。！？；\n]{0,12}(?:命宫|兄弟|夫妻|子女|财帛|疾厄|迁移|仆役|官禄|田宅|福德|父母)/u,
};
// 各 kind 至少须引用的事实（按 id 后缀）。日主等每盘都有的事实不能单独支撑格局判断。
const REQUIRED_FACTS: Record<Exclude<Kind, "event" | "fact">, RegExp> = {
  pattern: /\.bazi\.(?:patternReview|externalPatterns|wealthReview|monthExposure|rootDetails)$/u,
  timing: /\.(?:bazi\.(?:cycles|cycleRelations|monthlyCycles)|ziwei\.(?:cycles|transformations|monthly))$/u,
  palace: /\.ziwei\.(?:palace-\d+|cycles|monthly|transformations)$/u,
};

const normalize = (s: string) => s.replace(/\r\n?/gu, "\n").trim();
// 小标题（“一、身强还是身弱”“## 2027 年财运”）只是导航，不作判断。
const HEADING = /^(?:#{1,6}\s|[一二三四五六七八九十]+、|\d+[.、)]|[（(][一二三四五六七八九十\d]+[)）])/u;
// 登记为条件性或未决的事件、格局判断，所在句须带条件或限定语；否则多半是把确定判断登记成了条件性。
const HEDGE =
  /如果|若|假如|除非|一旦|取决|视乎|视情况|而定|条件|可能|或许|也许|倾向|未必|不一定|不确定|尚未|未定|未决|待|须|需要|要看|还要看|是否|能否|会改变|范围|入口|候选|分支|不宜|不能|不等于|并非|不是|不代表|只能|仅|参考|线索|保留|较难|偏向/u;
const TRAILING = /[。！？；!?;，,.\s]+$/u;

/** 按句末标点、分号与换行切句，再按逗号切成分句；整句覆盖规则下，切得越细越不容易被半句断言蒙混。 */
const sentences = (text: string) =>
  text
    .split(/(?<=[。！？；!?;\n])|(?<=\.)(?=\s|$)/u)
    .map((s) => s.trim())
    .filter((s) => s && !(HEADING.test(s) && s.length <= 24 && !/[。！？]/u.test(s)));
const unitsOf = (sentence: string) =>
  sentence
    .split(/(?<=[，,])/u)
    .map((s) => s.replace(TRAILING, "").trim())
    .filter(Boolean);

function field(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new InputError("INVALID_AUDIT", `${label} 必须是对象`);
  return value as Record<string, unknown>;
}

/**
 * 快速档断言清单：宿主逐句登记答复中的判断及其类型、把握与依据，代码核对覆盖、一致与真实性。
 * 含触发词的每个分句须被某条断言原文整句包含。只能发现漏报、错类与无据引用，不能理解语义；
 * 宿主把确定性判断登记为 conditional 时无法识别。
 */
export function checkAnswerAudit(answer: string, raw: unknown, evidence: Evidence) {
  const audit = field(raw, "audit");
  if (audit.schema !== "whoami.answer-audit.v1")
    throw new InputError("INVALID_AUDIT", "audit.schema 必须是 whoami.answer-audit.v1");
  if (audit.evidenceId !== evidence.evidenceId)
    throw new InputError("AUDIT_STALE", "audit.evidenceId 与当前 context 不一致；须按同一输入、年份与粒度重新核对");
  const text = normalize(answer);
  if (audit.answer !== undefined && (typeof audit.answer !== "string" || normalize(audit.answer) !== text))
    throw new InputError("INVALID_AUDIT", "audit.answer 须与受检答复逐字一致");
  if (!Array.isArray(audit.claims) || !audit.claims.length)
    throw new InputError("INVALID_AUDIT", "audit.claims 须为非空数组");
  const facts = new Set(evidence.facts.map((f) => f.id));
  // 收集全部问题一次报告，避免宿主逐个补登记反复重跑；单条格式有误的断言不参与覆盖计算。
  const issues: { code: string; message: string }[] = [];
  const validate = (rawClaim: unknown, i: number) => {
    const label = `audit.claims[${i}]`;
    const claim = field(rawClaim, label);
    const claimText = typeof claim.text === "string" ? normalize(claim.text) : "";
    if (!claimText || !text.includes(claimText))
      throw new InputError("INVALID_AUDIT", `${label}.text 须为答复中逐字存在的片段`);
    const kinds = claim.kinds;
    if (
      !Array.isArray(kinds) ||
      !kinds.length ||
      kinds.some((k) => !KINDS.includes(k as Kind)) ||
      new Set(kinds).size !== kinds.length
    )
      throw new InputError("INVALID_AUDIT", `${label}.kinds 须为 ${KINDS.join("/")} 中不重复的非空数组`);
    if (!STANCES.includes(claim.stance as (typeof STANCES)[number]))
      throw new InputError("INVALID_AUDIT", `${label}.stance 须为 ${STANCES.join("/")}`);
    // 命盘事实（含大运干支、流年宫职等时间或宫位事实）可登记为 fact-restatement；事件与格局判断不可。
    const isFact = kinds.includes("fact");
    if ((claim.stance === "fact-restatement") !== isFact || (isFact && (kinds.includes("event") || kinds.includes("pattern"))))
      throw new InputError(
        "AUDIT_KIND_MISMATCH",
        `${label} 只有命盘事实（kinds 含 fact，可兼 timing/palace）登记为 fact-restatement；事件与格局判断须为 conditional 或 unresolved`,
      );
    const refs = claim.factRefs;
    if (!Array.isArray(refs) || !refs.length || refs.some((r) => typeof r !== "string" || !facts.has(r)))
      throw new InputError("INVALID_AUDIT", `${label}.factRefs 须为当前 context 中真实存在的事实 ID`);
    for (const kind of kinds as Kind[]) {
      if (kind === "event" || kind === "fact") continue;
      if (!(refs as string[]).some((r) => REQUIRED_FACTS[kind].test(r)))
        throw new InputError("AUDIT_KIND_MISMATCH", `${label} 声明为 ${kind}，但未引用对应的命盘事实`);
    }
    return { text: claimText, kinds: kinds as Kind[] };
  };
  const claims = audit.claims.flatMap((rawClaim, i) => {
    try {
      return [validate(rawClaim, i)];
    } catch (error) {
      if (!(error instanceof InputError)) throw error;
      issues.push({ code: error.code, message: error.message });
      return [];
    }
  });
  let covered = 0;
  for (const sentence of sentences(text)) {
    let sentenceJudged = false;
    for (const unit of unitsOf(sentence)) {
      const triggered = (Object.keys(TRIGGERS) as (keyof typeof TRIGGERS)[]).filter((k) => TRIGGERS[k].test(unit));
      if (!triggered.length) continue;
      // 断言原文须整句包含该分句；只登记片段（如“2026”）不能覆盖整句。可以按整段登记。
      const covering = claims.filter((c) => c.text.includes(unit));
      if (!covering.length) {
        issues.push({ code: "AUDIT_COVERAGE_GAP", message: `“${unit.slice(0, 40)}”含${triggered.join("/")}判断，未被任何断言整句登记` });
        continue;
      }
      const declared = new Set(covering.flatMap((c) => c.kinds));
      const missing = triggered.filter((k) => !declared.has(k));
      if (missing.length)
        issues.push({ code: "AUDIT_KIND_MISMATCH", message: `“${unit.slice(0, 40)}”含${missing.join("/")}判断，覆盖它的断言未声明这些类型` });
      if (triggered.includes("event") || triggered.includes("pattern")) sentenceJudged = true;
      covered += 1;
    }
    if (sentenceJudged && !HEDGE.test(sentence))
      issues.push({
        code: "AUDIT_STANCE_MISMATCH",
        message: `“${sentence.slice(0, 40)}”含事件或格局判断并登记为条件性/未决，但句中没有条件或限定语`,
      });
  }
  if (issues.length)
    throw new InputError(
      issues[0]!.code,
      `断言清单有 ${issues.length} 处问题：${issues.slice(0, 8).map((x, i) => `${i + 1}. [${x.code}] ${x.message}`).join("；")}${issues.length > 8 ? "；……" : ""}`,
    );
  return { claims: claims.length, unitsCovered: covered };
}
