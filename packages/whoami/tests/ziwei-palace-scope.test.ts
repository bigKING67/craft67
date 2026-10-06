import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildChart } from "../src/chart.js";
import { contextFor } from "../src/evidence.js";
import { validateReport } from "../src/report.js";
import { assertZiweiPalaceScope, isZiweiPalaceFactId } from "../src/ziwei-palace-scope.js";

const input = { calendar: "solar", date: "2000-08-16", time: "04:00", place: "合成", longitude: 120, timeZone: "Asia/Shanghai", gender: "female" };
const z = buildChart(input, [2026]).candidates[0]!.ziwei;
const year = z.yearly[0]!;
const anchor = z.palaces.find((p) => year.palaceNames[p.index] === "官禄")!;
const header = `2026流年官禄落本命${anchor.name}${anchor.branch}`;
const outside = z.palaces.find((p) =>
  !anchor.surroundedIndices.includes(p.index) && p.majorStars.length,
)!;
const inside = z.palaces.find((p) => p.index === anchor.surroundedIndices[1])!;
const check = (text: string) => assertZiweiPalaceScope(text, z, "测试");
const scopeError = { code: "PALACE_SCOPE_MISMATCH" };

test("流年主题段落只允许引用该年该主题三方四正内的本命宫", () => {
  check(`${header}，三方四正另连${inside.name}${inside.branch}。联宫${inside.name}${inside.branch}需一并核对。`);
  assert.throws(() => check(`${header}。联宫另见${outside.name}${outside.majorStars[0]!.name}。`), scopeError);
  assert.throws(() => check(`${header}。另连${outside.name}${outside.branch}。`), scopeError);
});

test("段首写错流年主题落宫时直接拒绝", () => {
  const wrong = z.palaces.find((p) => p.index !== anchor.index)!;
  assert.throws(() => check(`2026流年官禄落本命${wrong.name}${wrong.branch}。`), scopeError);
});

test("同句标明三方四正之外可引背景；段落和下一个主题段落各自独立核对", () => {
  check(`${header}。${outside.name}${outside.majorStars[0]!.name}在三方四正之外，仅作本命背景。`);
  check(`${header}。\n\n${outside.name}${outside.majorStars[0]!.name}属于另一段落。`);
  check("本命背景：" + `${outside.name}${outside.branch}不在流年段落内。`);
  assert.throws(() => check(`${header}。此说不属实，${outside.name}${outside.majorStars[0]!.name}为联宫。`), scopeError);
  assert.throws(() => check(`${header}。迁移不属本题，${outside.name}${outside.majorStars[0]!.name}也是联宫依据。`), scopeError);
});

test("地支后接普通文字不算宫位引用；宫字和括号写法仍能识别", () => {
  check(`${header}。${outside.name}${outside.branch}见化禄仍需核对。`);
  assert.throws(() => check(`${header}。联宫另见${outside.name}宫${outside.majorStars[0]!.name}。`), scopeError);
  assert.throws(() => check(`${header}。联宫另见${outside.name}（${outside.majorStars[0]!.name}）。`), scopeError);
  assert.throws(() => check(`2026年流年官禄落本命${anchor.name}${anchor.branch}。另连${outside.name}${outside.branch}、官禄。`), scopeError);
  const variant = `2026 年的流年官禄宫落在本命${anchor.name}${anchor.name.endsWith("宫") ? "" : "宫"}（${anchor.branch}）`;
  check(`${variant}，联宫需核对。`);
  assert.throws(() => check(`${variant}。另见${outside.name}宫（${outside.branch}）。`), scopeError);
  assert.throws(() => check(`${variant}。另见${outside.name}宫位于${outside.branch}。`), scopeError);
  const wrong = z.palaces.find((p) => p.index !== anchor.index)!;
  assert.throws(() => check(`2026年流年官禄宫落在本命${wrong.name}（${wrong.branch}）。`), scopeError);
});

test("report-check 在 v6 报告正文中拦截流年联宫混入集合外宫位", () => {
  const birth = JSON.parse(readFileSync("examples/birth.json", "utf8"));
  const report = JSON.parse(readFileSync("examples/report.json", "utf8"));
  // 样例报告绑定历史 evidence v1。
  const e = contextFor(birth, [2024, 2025, 2026, 2027, 2028], "whoami.evidence.v1");
  validateReport(report, e);
  const candidate = e.candidateIds[0]!;
  const palaces = e.facts
    .filter((f) => f.candidate === candidate && isZiweiPalaceFactId(f.id))
    .map((f) => f.value as typeof z.palaces[number]);
  const yearly = (e.facts.find((f) => f.id === `${candidate}.ziwei.cycles`)!.value as { yearly: typeof z.yearly }).yearly;
  const y = yearly.find((v) => v.year === 2026)!;
  const a = palaces.find((p) => y.palaceNames[p.index] === "官禄")!;
  const o = palaces.find((p) => !a.surroundedIndices.includes(p.index) && p.majorStars.length)!;
  const claim = report.sections
    .flatMap((s: { claims: { text: string; factRefs: string[] }[] }) => s.claims)
    .find((c: { factRefs: string[] }) => c.factRefs.some((id) => id.includes(".ziwei.")))!;
  claim.text += `\n\n2026流年官禄落本命${a.name}${a.branch}，联宫另见${o.name}${o.majorStars[0]!.name}。`;
  assert.throws(() => validateReport(report, e), scopeError);
  const clean = JSON.parse(readFileSync("examples/report.json", "utf8"));
  const cleanTiming = clean.ziweiReasoning.find((r: { topic: string }) => r.topic === "ziwei-timing");
  cleanTiming.timingChain.withdrawalConditions += `\n\n2026流年官禄落本命${a.name}${a.branch}，联宫另见${o.name}${o.majorStars[0]!.name}。`;
  assert.throws(() => validateReport(clean, e), scopeError);
  const baziOnly = JSON.parse(readFileSync("examples/report.json", "utf8"));
  baziOnly.uncertainty += `\n\n2026流年官禄落本命${a.name}${a.branch}，联宫另见${o.name}${o.majorStars[0]!.name}。`;
  assert.throws(() => validateReport(baziOnly, e), scopeError);
});
