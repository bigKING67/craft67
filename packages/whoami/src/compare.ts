import { isDeepStrictEqual } from "node:util";
import { buildChart, type Chart } from "./chart.js";
import { buildEvidence, type Fact } from "./evidence.js";
import { InputError } from "./input.js";

type Selection = { beforeCandidate?: string; afterCandidate?: string };
const summarize = (chart: Chart) => ({
  chartId: chart.chartId, status: chart.status, input: chart.input, warnings: chart.warnings,
  candidates: chart.candidates.map(c => ({
    id: c.id, pillars: c.bazi.pillars.map(p => p.value),
    soulPalace: c.ziwei.soulPalace, bodyPalace: c.ziwei.bodyPalace,
    representativeTime: c.representativeTime,
  })),
});

export function compareBirths(before: unknown, after: unknown, years?: number[], selection: Selection = {}) {
  const a = buildChart(before, years);
  const b = buildChart(after, a.years); // 两端使用同一已解析年份范围。
  const base = { schema: "whoami.compare.v1", years: a.years, before: summarize(a), after: summarize(b) };
  if (a.status === "needs-input" || b.status === "needs-input")
    return { ...base, status: "needs-input" as const, questions: [
      ...(a.status === "needs-input" ? [{ side: "before", questions: a.questions }] : []),
      ...(b.status === "needs-input" ? [{ side: "after", questions: b.questions }] : []),
    ] };

  const select = (chart: Chart, id: string | undefined, side: string) => {
    if (id !== undefined && !chart.candidates.some(c => c.id === id))
      throw new InputError("INVALID_CANDIDATE", `${side} 候选不存在；请使用该侧列出的完整候选ID`);
    return id ?? (chart.candidates.length === 1 ? chart.candidates[0]!.id : undefined);
  };
  const aId = select(a, selection.beforeCandidate, "before");
  const bId = select(b, selection.afterCandidate, "after");
  if (!aId || !bId)
    return { ...base, status: "needs-selection" as const,
      questions: [
        ...(!aId ? ["before有多个候选，请指定 --before-candidate；选择只用于对照，不代表确认出生时辰。"] : []),
        ...(!bId ? ["after有多个候选，请指定 --after-candidate；选择只用于对照，不代表确认出生时辰。"] : []),
      ] };

  const ae = buildEvidence(a), be = buildEvidence(b);
  const facts = (all: Fact[], id: string) => new Map(all.filter(f => f.candidate === id)
    .map(f => [f.id.slice(id.length + 1), f]));
  const af = facts(ae.facts, aId), bf = facts(be.facts, bId);
  const keys = [...new Set([...af.keys(), ...bf.keys()])];
  const unchangedFactKeys = keys.filter(key => af.has(key) && bf.has(key) && isDeepStrictEqual(af.get(key)!.value, bf.get(key)!.value));
  const unchanged = new Set(unchangedFactKeys);
  const changedFacts = keys.filter(key => !unchanged.has(key)).map(key => {
    const left = af.get(key), right = bf.get(key), f = right ?? left!;
    return { key, system: f.system, label: f.label,
      change: !left ? "added" : !right ? "removed" : "changed",
      before: left ? { factId: left.id, value: left.value } : null,
      after: right ? { factId: right.id, value: right.value } : null };
  });
  const inputKeys = [...new Set([...Object.keys(a.input), ...Object.keys(b.input)])] as (keyof typeof a.input)[];
  const bindingMatch = ae.chartId === be.chartId && ae.evidenceId === be.evidenceId;
  return {
    ...base, status: "compared" as const,
    selected: { before: aId, after: bId },
    changedInputFields: inputKeys.filter(key => !isDeepStrictEqual(a.input[key], b.input[key])),
    // 始终按当前 evidence 版本对照；绑定旧版本的报告须按 evidenceSchema 另行 report-check。
    evidenceBinding: { schema: ae.schema, before: ae.evidenceId, after: be.evidenceId, bindingMatch,
      meaning: bindingMatch ? "两端证据绑定相同；未提交报告，不代表其结构、正文或候选选择已通过校验。"
        : "两端证据绑定不同；绑定旧证据的报告不能直接作为新输入的已校验报告，须核对受影响内容后重新校验。" },
    changedFacts, unchangedFactKeys,
    limits: [
      "按同名事实项比较值，不把事实相同当作自然语言解释已获验证；不自动改写报告或替换证据ID。",
      "候选ID只属于各自命盘；多候选必须明确选择比较组合，不因排列次序或ID相似自动配对。",
      "比较沿用既有采样与真太阳时近似；单候选也可能来自不确定时间区间，保留两侧状态和警告。",
    ],
  };
}
