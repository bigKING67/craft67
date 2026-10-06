import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { buildChart } from "../src/chart.js";
import { contextFor, evidenceForReport } from "../src/evidence.js";
import { cycleRelations, pairBranchRelations, completeBranchGroups } from "../src/cycle-relations.js";

const birth = JSON.parse(readFileSync("examples/birth.json", "utf8"));
const bazi = (years: number[]) => buildChart(birth, years).candidates[0]!.bazi;
const has = (rs: { layer: string; kind: string; value: string }[], layer: string, kind: string, value: string) =>
  rs.some((r) => r.layer === layer && r.kind === kind && r.value === value);

test("2026 丙午在辛巳运：流年、大运与本命三层关系逐项列出", () => {
  const [y] = cycleRelations(bazi([2026]));
  assert.equal(y!.decadeStatus, "single");
  assert.deepEqual(y!.decades, [{ index: 3, pillar: "辛巳", coverage: "whole-year" }]);
  assert.equal(y!.lichunStart, "2026-02-04T04:02:08+08:00");
  for (const [layer, kind, value] of [
    ["流年-本命", "自刑", "午午"],
    ["流年-本命", "伏吟", "丙午丙午"],
    ["大运-本命", "六合", "巳申"],
    ["大运-本命", "五合", "辛丙"],
    ["大运-本命", "害", "巳寅"],
    ["流年-大运", "五合", "丙辛"],
    ["大运-本命组合", "三刑", "寅巳申"],
  ] as const)
    assert(has(y!.relations, layer, kind, value), `${layer} ${kind} ${value}`);
  // 本命已有的关系不重复算作岁运组合，也不输出吉凶或事件字段。
  assert(!y!.relations.some((r) => r.layer.endsWith("组合") && !r.positions.some((p) => p === "yearly" || p.startsWith("decade-"))));
  assert(!y!.relations.some((r) => r.layer === "流年参与组合" && r.kind === "三刑"));
  assert(!y!.relations.some((r) => "effect" in r || "score" in r));
});

test("起运前、首次起运与年内换运分别标记，不把年内换运写成单一大运", () => {
  const ys = cycleRelations(bazi([2001, 2003, 2023]));
  assert.equal(ys[0]!.decadeStatus, "before-first-decade");
  assert.deepEqual(ys[0]!.decades, []);
  assert.equal(ys[1]!.decadeStatus, "first-decade-starts-within-year");
  assert.equal(ys[2]!.decadeStatus, "switches-within-year");
  assert.deepEqual(ys[2]!.decades.map((d) => [d.pillar, d.coverage]), [["壬午", "part-year"], ["辛巳", "part-year"]]);
  // 2023 癸卯：本命年支辰、时支寅加流年卯补齐三会，只由流年参与。
  assert(ys[2]!.relations.some((r) => r.layer === "流年参与组合" && r.kind === "三会" && r.value === "寅卯辰"));
});

test("起运范围跨越立春年界时保留可能生效的大运分支", () => {
  const b = structuredClone(bazi([2024]));
  const rep = new Date(b.cycles.startInstant).getTime();
  const year = 365 * 24 * 3600 * 1000;
  b.cycles.uncertainty.status = "range";
  b.cycles.uncertainty.startInstant = {
    earliest: new Date(rep - year).toISOString(),
    latest: new Date(rep + year).toISOString(),
  };
  const [y] = cycleRelations(b);
  assert.equal(y!.decadeStatus, "start-uncertain");
  assert.deepEqual(y!.decades.map((d) => [d.pillar, d.coverage]), [["壬午", "possible-if-start-shifts"], ["辛巳", "part-year"]]);
});

test("末步大运之后与末步年内结束分别标记", () => {
  // 1901 年出生者第 10 步大运在 2099 上限内结束。
  const early = { ...birth, date: "1901-06-01" };
  const at = (years: number[]) => buildChart(early, years).candidates[0]!.bazi;
  const last = at([1950]).cycles.decades.at(-1)!;
  const endYear = Number(last.endExclusiveCivil.slice(0, 4));
  assert.equal(cycleRelations(at([endYear + 5]))[0]!.decadeStatus, "after-last-decade");
  const [y] = cycleRelations(at([endYear]));
  assert.equal(y!.decadeStatus, "last-decade-ends-within-year");
  assert.deepEqual(y!.decades.map((d) => d.index), [last.index]);
});

test("起运范围不确定时，首运是否全年生效不写成确定的年内起运", () => {
  const b = structuredClone(bazi([2003]));
  const rep = new Date(b.cycles.startInstant).getTime();
  b.cycles.uncertainty.status = "range";
  b.cycles.uncertainty.startInstant = {
    earliest: new Date(rep - 200 * 24 * 3600 * 1000).toISOString(),
    latest: b.cycles.startInstant,
  };
  assert.equal(cycleRelations(b)[0]!.decadeStatus, "start-uncertain");
});

test("本命已完整的组合不记为岁运组合；只有岁运为补齐所必需时才列出", () => {
  const natalComplete = [{ position: "year", branch: "申" }, { position: "month", branch: "子" }, { position: "day", branch: "辰" }];
  assert.deepEqual(completeBranchGroups([...natalComplete, { position: "yearly", branch: "子" }], ["yearly"]), []);
  const needs = [{ position: "year", branch: "申" }, { position: "yearly", branch: "子" }, { position: "decade-2", branch: "辰" }];
  assert.deepEqual(completeBranchGroups(needs, ["yearly", "decade-2"]).map((g) => g.kind), ["三合"]);
  assert.deepEqual(completeBranchGroups([...needs, { position: "day", branch: "辰" }], ["yearly", "decade-2"]), []);
});

test("v2 扩展关系：半合含旺支、拱合为生墓、破与三刑组内两两相刑", () => {
  const kinds = (a: string, b: string) =>
    pairBranchRelations({ position: "a", branch: a }, { position: "b", branch: b }, true).map((r) => r.kind);
  assert.deepEqual(kinds("申", "子"), ["半合"]);
  assert.deepEqual(kinds("申", "辰"), ["拱合"]);
  assert.deepEqual(kinds("卯", "午"), ["破"]);
  assert.deepEqual(kinds("巳", "申"), ["六合", "破", "刑"]);
  assert.deepEqual(kinds("寅", "申"), ["冲", "刑"]);
  assert.deepEqual(pairBranchRelations({ position: "a", branch: "巳" }, { position: "b", branch: "申" }).map((r) => r.kind), ["六合"]);
});

test("成对与成组地支关系沿用本命口径", () => {
  assert.deepEqual(pairBranchRelations({ position: "a", branch: "子" }, { position: "b", branch: "卯" }).map((r) => r.kind), ["刑"]);
  assert.deepEqual(pairBranchRelations({ position: "a", branch: "午" }, { position: "b", branch: "午" }).map((r) => r.kind), ["自刑"]);
  const members = [{ position: "month", branch: "申" }, { position: "day", branch: "子" }, { position: "yearly", branch: "辰" }];
  assert.deepEqual(completeBranchGroups(members, ["yearly"]).map((g) => g.kind), ["三合"]);
  assert.deepEqual(completeBranchGroups(members, ["decade-1"]), []);
});

test("evidence v2 新增 cycleRelations 并由 R-bazi-timing 关联；v1 保持冻结，v2 本命关系只扩展不删改", () => {
  const e = contextFor(birth, [2026], "whoami.evidence.v2");
  const old = contextFor(birth, [2026], "whoami.evidence.v1");
  const c = e.candidateIds[0]!;
  assert.equal(e.schema, "whoami.evidence.v2");
  assert.equal(old.schema, "whoami.evidence.v1");
  assert(e.facts.some((f) => f.id === `${c}.bazi.cycleRelations`));
  assert(!old.facts.some((f) => f.id === `${c}.bazi.cycleRelations`));
  assert(e.rules.find((r) => r.id === `${c}.R-bazi-timing`)!.factRefs.includes(`${c}.bazi.cycleRelations`));
  const byId = new Map(e.facts.map((f) => [f.id, f]));
  // v2 本命 relations 扩展了半合、拱合、破、两两相刑与三会；其余共有事实逐字节一致，v1 关系全部保留。
  for (const f of old.facts) {
    if (f.id.endsWith(".bazi.relations")) {
      const extended = byId.get(f.id)!.value as unknown[];
      for (const r of f.value as unknown[]) assert(extended.some((x) => JSON.stringify(x) === JSON.stringify(r)));
      continue;
    }
    assert.deepEqual(byId.get(f.id), f);
  }
  assert.equal(e.chartId, old.chartId);
  assert.notEqual(e.evidenceId, old.evidenceId);
});

test("report-check 按报告绑定的 evidence 版本重算：v1 历史报告有效，新模板为 v2", () => {
  const run = (args: string[]) =>
    spawnSync(process.execPath, ["--import", "tsx", "src/cli.ts", ...args], { encoding: "utf8" });
  const legacy = run(["report-check", "--input", "examples/birth.json", "--report", "examples/report.json", "--years", "2024,2025,2026,2027,2028"]);
  assert.equal(legacy.status, 0, legacy.stderr);
  assert.equal(JSON.parse(legacy.stdout).evidenceSchema, "whoami.evidence.v1");
  const template = run(["report-template", "--input", "examples/birth.json", "--years", "2026"]);
  assert.equal(JSON.parse(template.stdout).evidenceId, contextFor(birth, [2026]).evidenceId);
  // 月度 v2 报告在默认 v3 下仍须按 v2 重算。
  const monthV2 = contextFor(birth, [2025], "whoami.evidence.v2", "month");
  const bound = evidenceForReport(buildChart(birth, [2025], "month"), { evidenceId: monthV2.evidenceId });
  assert.equal(bound.schema, "whoami.evidence.v2");
  assert.equal(bound.evidenceId, monthV2.evidenceId);
  const wrongGranularity = run(["report-check", "--input", "examples/birth.json", "--report", "examples/report.json", "--years", "2024,2025,2026,2027,2028", "--granularity", "month"]);
  assert.equal(JSON.parse(wrongGranularity.stderr).code, "GRANULARITY_MISMATCH");
});
