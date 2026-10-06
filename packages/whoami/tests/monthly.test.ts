import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildChart } from "../src/chart.js";
import { contextFor, monthlyLabels } from "../src/evidence.js";
import { monthlyCycles } from "../src/cycle-relations.js";
import { checkAnswer } from "../src/answer-check.js";

const birth = JSON.parse(readFileSync("examples/birth.json", "utf8"));
const code = (c: string) => ({ code: c });

test("八字流月按节切分 12 个月，月柱与关系按传统表列出", () => {
  const [y] = monthlyCycles(buildChart(birth, [2025]).candidates[0]!.bazi);
  assert.equal(y!.months.length, 12);
  assert.deepEqual(y!.months.map((m) => m.pillar).slice(0, 3), ["戊寅", "己卯", "庚辰"]);
  const wu = y!.months[4]!;
  assert.equal(wu.pillar, "壬午");
  assert.equal(wu.start, "2025-06-05T17:56:32+08:00");
  assert.equal(wu.endExclusive, y!.months[5]!.start);
  const has = (m: typeof wu, layer: string, kind: string, value: string) =>
    m.relations.some((r) => r.layer === layer && r.kind === kind && r.value === value);
  assert(has(wu, "流月-本命", "冲", "壬丙"));
  assert(has(wu, "流月-本命", "自刑", "午午"));
  const shen = y!.months[6]!;
  assert(has(shen, "流月-本命", "伏吟", "甲申甲申"));
  assert(has(shen, "流月-本命", "反吟", "甲申庚寅"));
  assert(has(shen, "流月-流年", "六合", "申巳"));
  assert(has(shen, "流月-大运", "六合", "申巳"));
});

test("紫微流月按农历月，闰月拆成两段并标注口径", () => {
  const z = buildChart(birth, [2025], "month").candidates[0]!.ziwei.monthly!;
  const leap = z.filter((m) => m.leap);
  assert.deepEqual(leap.map((m) => [m.label, m.solarStart, m.stem + m.branch]), [
    ["闰六月上半", "2025-07-25", "癸未"],
    ["闰六月下半", "2025-08-09", "甲申"],
  ]);
  assert(leap.every((m) => m.leapConvention?.includes("另一派")));
  assert.equal(z.find((m) => m.label === "六月")!.stem + z.find((m) => m.label === "六月")!.branch, "癸未");
  assert.equal(z.filter((m) => !m.leap).length, 12);
});

test("年度粒度输出不变；月度粒度只新增流月事实并标记 granularity", () => {
  const year = contextFor(birth, [2026]);
  const month = contextFor(birth, [2026], undefined, "month");
  assert(!("granularity" in year));
  assert.equal(month.granularity, "month");
  assert.equal(month.chartId, year.chartId);
  const added = month.facts.filter((f) => !year.facts.some((g) => g.id === f.id)).map((f) => f.id.split(".").slice(1).join("."));
  assert.deepEqual(added.sort(), ["bazi.monthlyCycles", "ziwei.monthly"]);
  const byId = new Map(month.facts.map((f) => [f.id, f]));
  for (const f of year.facts) assert.deepEqual(byId.get(f.id), f);
  assert.equal(monthlyLabels(year), undefined);
  assert(monthlyLabels(month)!.has("八字流月甲午"));
  assert.throws(() => contextFor(birth, [2026], "whoami.evidence.v1", "month"), code("INVALID_ARGUMENT"));
});

test("answer-check：流月标签须有月度证据且真实存在，公历月仍拒绝并提示改写", () => {
  const year = contextFor(birth, [2026]);
  const month = contextFor(birth, [2026], undefined, "month");
  const text = "2026年八字流月甲午（芒种至小暑）与本命的关系只作条件性参考。";
  assert.throws(() => checkAnswer(text, year), code("UNSUPPORTED_TIME_GRANULARITY"));
  assert.equal(checkAnswer(text, month).status, "valid");
  assert.throws(() => checkAnswer("2026年八字流月丙子的事业判断。", month), code("MONTH_NOT_IN_EVIDENCE"));
  assert.throws(() => checkAnswer("2026年7月事业会有结果。", month), (e: Error) =>
    (e as Error & { code: string }).code === "UNSUPPORTED_TIME_GRANULARITY" && e.message.includes("八字流月<干支>"));
});

test("流月补齐的三合等组合、按月命名的大运状态与紫微流月四化宫职", () => {
  const [y] = monthlyCycles(buildChart(birth, [2026]).candidates[0]!.bazi);
  const zi = y!.months.find((m) => m.pillar === "庚子")!;
  assert.equal(zi.startJie, "大雪");
  assert.equal(zi.endJie, "小寒");
  // 本命年支辰、月支申加流月子补齐申子辰。
  assert(zi.relations.some((r) => r.layer === "流月参与组合" && r.kind === "三合" && r.value === "申子辰"));
  const early = { ...birth, date: "1901-06-01" };
  const months = monthlyCycles(buildChart(early, [1950]).candidates[0]!.bazi).flatMap((x) => x.months);
  assert(months.every((m) => !m.decadeStatus.endsWith("-year")));
  const z = buildChart(birth, [2026], "month").candidates[0]!.ziwei;
  const m = z.monthly!.find((x) => x.stem + x.branch === "丁酉")!;
  for (const t of m.transformations)
    for (const target of t.targets) {
      assert.equal(target.scopePalace, m.palaceNames[target.palaceIndex]);
      assert.equal(target.natalPalace, z.palaces[target.palaceIndex]!.name);
    }
});

test("流月标签：须写体系、同名流月须写年份、年份须匹配、括号起止须一致", () => {
  const two = contextFor(birth, [2025, 2026], undefined, "month");
  assert.throws(() => checkAnswer("流月甲午需要留意。", two), code("AMBIGUOUS_MONTH_SYSTEM"));
  assert.throws(() => checkAnswer("流月壬午需要留意。", contextFor(birth, [2026])), code("UNSUPPORTED_TIME_GRANULARITY"));
  // 壬午只在 2025；写成 2026 年不成立。
  assert.equal(checkAnswer("2025年八字流月壬午只作参考。", two).status, "valid");
  assert.throws(() => checkAnswer("2026年八字流月壬午只作参考。", two), code("MONTH_NOT_IN_EVIDENCE"));
  assert.throws(() => checkAnswer("2026年八字流月己亥（立秋至白露）只作参考。", two), code("MONTH_RANGE_MISMATCH"));
  assert.equal(checkAnswer("2026年八字流月己亥（立冬至大雪）只作参考。", two).status, "valid");
  assert.throws(() => checkAnswer("2026年紫微流月丁酉（农历九月）只作参考。", two), code("MONTH_RANGE_MISMATCH"));
  assert.equal(checkAnswer("2025年紫微流月癸未（闰六月）只作参考。", two).status, "valid");
  const decade = contextFor(birth, [2020, 2025], undefined, "month");
  assert.throws(() => checkAnswer("八字流月壬午只作参考。", decade), code("AMBIGUOUS_MONTH_YEAR"));
});

test("紫微流月段首同样核对落宫与三方四正集合", () => {
  const m = contextFor(birth, [2026], undefined, "month");
  const z = buildChart(birth, [2026], "month").candidates[0]!.ziwei;
  const month = z.monthly!.find((x) => x.stem + x.branch === "丁酉")!;
  const anchor = z.palaces.find((p) => month.palaceNames[p.index] === "官禄")!;
  const outside = z.palaces.find((p) => !anchor.surroundedIndices.includes(p.index))!;
  const inside = z.palaces.find((p) => p.index === anchor.surroundedIndices[1])!;
  const head = `2026年紫微流月丁酉（农历八月）的官禄落本命${anchor.name}（${anchor.branch}）`;
  assert.equal(checkAnswer(`${head}，另连${inside.name}${inside.branch}。`, m).status, "valid");
  assert.throws(() => checkAnswer(`${head}，另见${outside.name}${outside.branch}。`, m), code("PALACE_SCOPE_MISMATCH"));
  const wrong = z.palaces.find((p) => p.index !== anchor.index)!;
  assert.throws(() => checkAnswer(`2026年紫微流月丁酉的官禄落本命${wrong.name}（${wrong.branch}）。`, m), code("PALACE_SCOPE_MISMATCH"));
});
