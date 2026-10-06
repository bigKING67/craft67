import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildChart } from "../src/chart.js";
import { contextFor } from "../src/evidence.js";
import { patternReview } from "../src/pattern-review.js";
import { ziweiFlyingTransforms } from "../src/ziwei-flying.js";

const birth = JSON.parse(readFileSync("examples/birth.json", "utf8"));
const candidate = () => buildChart(birth, [2026]).candidates[0]!;

test("宫干飞化按 iztro 十干四化表，落点与星曜所在宫一致，自化与化入对宫分开标记", () => {
  const z = candidate().ziwei;
  const f = ziweiFlyingTransforms(z);
  assert.equal(f.palaces.length, 12);
  for (const p of f.palaces) {
    assert.equal(p.flights.map((x) => x.mutagen).join(""), "禄权科忌");
    for (const flight of p.flights)
      for (const t of flight.targets) {
        const target = z.palaces.find((x) => x.index === t.palaceIndex)!;
        assert([...target.majorStars, ...target.minorStars].some((s) => s.name === flight.star));
        assert.equal(t.kind, t.palaceIndex === p.palaceIndex ? "self" : t.palaceIndex === (p.palaceIndex + 6) % 12 ? "opposite" : "other");
      }
  }
  // 壬干：天梁禄、紫微权、左辅科、武曲忌。
  const ren = f.palaces.find((p) => p.stem === "壬")!;
  assert.deepEqual(ren.flights.map((x) => x.star), ["天梁", "紫微", "左辅", "武曲"]);
  assert(f.selfTransforms.every((s) => f.palaces.find((p) => p.palaceIndex === s.palaceIndex)!.flights.some((x) => x.star === s.star && x.targets.some((t) => t.kind === "self"))));
  assert(f.convention.includes("庚"));
});

test("五格候选：入口按月支藏干十神，透干竞争与显干条件逐项列出，判断恒为 unresolved", () => {
  const r = patternReview(candidate().bazi);
  assert.equal(r.monthBranch, "申");
  assert.equal(r.judgment, "unresolved");
  const killer = r.patterns.find((p) => p.id === "killer")!;
  assert.equal(killer.status, "candidate-only");
  assert.deepEqual(killer.entry.map((h) => [h.stem, h.role, h.exposedAt.length]), [["壬", "middle", 0]]);
  assert.deepEqual(killer.competingExposed.map((h) => h.tenGod), ["偏财"]);
  const check = (p: typeof killer, id: string) => p.checks.find((c) => c.id === id)!;
  assert.equal(check(killer, "seal").prerequisite, "observed");
  // 财透而食神不透：七煞逢财无制的显干前提出现。
  assert.equal(check(killer, "wealth-no-control").prerequisite, "observed");
  // 食神格“食帶煞而無財”：财实际透出，mustBeAbsent.presentAt 列出透出位置，前提不成立。
  const food = r.patterns.find((p) => p.id === "food")!;
  const noWealth = check(food, "killer-no-wealth") as { prerequisite: string; mustBeAbsent?: { presentAt: { position: string }[] } };
  assert.deepEqual(noWealth.mustBeAbsent!.presentAt.map((x) => x.position), ["year", "hour"]);
  assert.equal(noWealth.prerequisite, "not-observed");
  assert.equal(check(killer, "food-control").prerequisite, "not-observed");
  assert(r.patterns.filter((p) => p.status === "outside-scope").every((p) => !p.checks.length));
  for (const p of r.patterns) for (const c of p.checks) assert(c.source.startsWith("https://donglishuzhai.net/chapter/") && c.quote.length > 0);
});

test("同一显干组合在不同强弱条件下方向相反时两行并列，不相互抵消", () => {
  // 人工改柱：月支卯（乙为丙之正印）、年干壬（七杀），检验印格 killer 与 killer-heavy 同时出现。
  const b = structuredClone(candidate().bazi);
  const month = b.pillars.find((p) => p.position === "month")!;
  month.branch = "卯";
  month.hiddenStems = [{ ...month.hiddenStems[0]!, stem: "乙", tenGod: "正印", element: "木" }];
  b.pillars.find((p) => p.position === "year")!.stem = "壬";
  b.pillars.find((p) => p.position === "year")!.tenGod = "七杀";
  const seal = patternReview(b).patterns.find((p) => p.id === "seal")!;
  const ids = seal.checks.filter((c) => c.prerequisite === "observed").map((c) => c.id);
  assert(ids.includes("killer") && ids.includes("killer-heavy"));
});

test("v2 context 带飞化与五格事实及规则；v1 不含", () => {
  const e = contextFor(birth, [2026]);
  const old = contextFor(birth, [2026], "whoami.evidence.v1");
  const c = e.candidateIds[0]!;
  for (const key of ["ziwei.flyingTransforms", "bazi.patternReview"]) {
    assert(e.facts.some((f) => f.id === `${c}.${key}`));
    assert(!old.facts.some((f) => f.id === `${c}.${key}`));
  }
  assert(e.rules.some((r) => r.id === `${c}.R-bazi-pattern-review`));
  assert(e.rules.find((r) => r.id === `${c}.R-ziwei-transformations`)!.factRefs.includes(`${c}.ziwei.flyingTransforms`));
});
