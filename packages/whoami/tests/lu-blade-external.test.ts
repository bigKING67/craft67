import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { element, hiddenStemsOf, tenGod } from "../src/chart.js";
import { contextFor } from "../src/evidence.js";
import { patternReview } from "../src/pattern-review.js";
import { externalPatternCandidates } from "../src/external-patterns.js";

// 由四柱干支构造命盘；十神与藏干用 chart 同一套表计算。
const POS = ["year", "month", "day", "hour"] as const;
function bazi(pillars: string) {
  const [y, m, d, h] = pillars.split(" ");
  // 只接受真实存在的六十甲子柱（干支阴阳一致），避免测试引擎不可能产生的命盘。
  for (const v of [y!, m!, d!, h!])
    assert.equal("甲丙戊庚壬".includes(v[0]!), "子寅辰午申戌".includes(v[1]!), `非法干支柱 ${v}`);
  const day = d![0]!;
  return {
    dayMaster: day,
    pillars: [y!, m!, d!, h!].map((v, i) => ({
      position: POS[i]!,
      value: v,
      stem: v[0]!,
      branch: v[1]!,
      element: element(v[0]!),
      tenGod: i === 2 ? "日主" : tenGod(day, v[0]!),
      hiddenStems: hiddenStemsOf(v[1]!).map((s) => ({ stem: s, element: element(s), tenGod: tenGod(day, s) })),
    })),
  } as unknown as Parameters<typeof patternReview>[0];
}
const ext = (p: string) => patternReview(bazi(p), { v3: true }).extendedPatterns!;
const pattern = (p: string, id: string) => ext(p).find((x) => x.id === id)!;
const check = (p: ReturnType<typeof pattern>, id: string) => p.checks.find((c) => c.id === id)!;

test("阳刃按刃位入格：丙日午月、戊日午月为阳刃，丁日午月为建禄", () => {
  assert.equal(pattern("壬申 甲午 丙寅 丁酉", "blade").entry[0]!.kind, "阳刃");
  // 午本气丁为戊之正印，按十神会漏判；按刃位仍是阳刃。
  assert.equal(pattern("庚子 戊午 戊辰 甲寅", "blade").status, "candidate-only");
  assert.equal(pattern("庚子 丙午 丁卯 甲辰", "blade").status, "outside-scope");
  assert.equal(pattern("庚子 丙午 丁卯 甲辰", "lu").entry[0]!.kind, "建禄");
  assert.equal(pattern("庚子 戊寅 乙卯 甲申", "lu").entry[0]!.kind, "月劫");
  // 月劫按同五行阳干之禄：己日巳月是（戊禄在巳），己日辰月虽本气戊为劫财却不是。
  assert.equal(pattern("甲子 己巳 己巳 甲子", "lu").entry[0]!.kind, "月劫");
  assert.equal(pattern("甲子 戊辰 己巳 甲子", "lu").status, "outside-scope");
  assert.equal(pattern("庚子 戊申 丙午 甲午", "lu").status, "outside-scope");
});

test("阳刃露煞透刃与煞被合：壬煞与丁刃同透即五合", () => {
  const blade = pattern("壬申 甲午 丙寅 丁酉", "blade");
  assert.equal(check(blade, "killer-blade").prerequisite, "observed");
  const combined = check(blade, "killer-combined") as { prerequisite: string; combined?: { pairs: { stems: string }[] } };
  assert.equal(combined.prerequisite, "observed");
  assert.equal(combined.combined!.pairs[0]!.stems, "壬丁");
  assert.equal(check(blade, "no-officer-killer").prerequisite, "not-observed");
  assert.equal(check(pattern("庚子 甲午 丙寅 己亥", "blade"), "no-officer-killer").prerequisite, "observed");
});

test("建禄用官遇伤而伤被合", () => {
  // 甲日寅月建禄；年辛为正官，月壬为偏印，时丁为伤官，丁壬五合。
  const lu = pattern("辛酉 壬寅 甲子 丁卯", "lu");
  assert.equal(lu.entry[0]!.kind, "建禄");
  assert.equal(check(lu, "officer-hurt").prerequisite, "observed");
  const combined = check(lu, "officer-hurt-combined") as { prerequisite: string; combined?: { pairs: { stems: string }[] } };
  assert.equal(combined.prerequisite, "observed");
  assert.equal(combined.combined!.pairs[0]!.stems, "丁壬");
  // 伤官、七杀不可能与日干五合（日干只合其正财或正官），“合日干不爲合去”在这两项上是结构性的。
  assert.deepEqual(lu.useGodCandidates.map((h) => h.tenGod), []);
});

test("外格：排除条件出现即 blocked，入口齐全才 entry-observed，无阈值处标注解释", () => {
  const find = (p: string, id: string) => externalPatternCandidates(bazi(p)).candidates.find((c) => c.id === id)!;
  // 一方秀气：甲日卯月，地支全寅卯辰，干无官煞。
  assert.equal(find("丙寅 丁卯 甲辰 丙寅", "one-element").status, "entry-observed");
  assert.equal(find("庚寅 丁卯 甲辰 丙寅", "one-element").status, "blocked");
  // 化格：丁壬相合，卯月本气乙属木，地支全亥卯未。
  // 丁壬合，寅月本气甲属木，地支全寅卯辰；合化之壬虽为丁之正官，不计入干头官煞。
  assert.equal(find("辛亥 壬寅 丁卯 甲辰", "transform").status, "entry-observed");
  // 地支丑寅巳子不全木局，入口不全。
  assert.equal(find("辛丑 壬寅 丁巳 庚子", "transform").status, "not-observed");
  // 从财：透印即不从。
  assert.equal(find("庚申 甲申 丙申 庚申", "follow-wealth").status, "blocked");
  const noRoot = find("庚申 庚申 丙申 庚申", "follow-wealth");
  assert.equal(noRoot.status, "entry-observed");
  assert(noRoot.entry.some((c) => c.interpretation));
  // 朝阳：辛日时干戊，干头无木火。
  assert.equal(find("庚子 庚子 辛亥 戊子", "facing-sun").status, "entry-observed");
  assert.equal(find("丙子 庚子 辛亥 戊子", "facing-sun").status, "blocked");
  const noisy = externalPatternCandidates(bazi("庚申 庚申 丙申 庚申"));
  assert.equal(noisy.gate[0]!.observed, true);
  assert.equal(noisy.monthMainTenGod, "偏财");
  // 入口不全时不因排除条件出现而列为 blocked：庚日见丙丁巳午但无申子辰，井栏为 not-observed。
  assert.equal(find("丙寅 庚寅 庚午 丁亥", "well-rail").status, "not-observed");
  // 通则“干头无官煞”适用于所有外格：朝阳入口齐全但透七杀丁即 blocked。
  assert.equal(find("丁卯 庚子 辛亥 戊子", "facing-sun").status, "blocked");
});

test("evidence v3 带建禄阳刃与外格事实；v2 不含且保持冻结", () => {
  const birth = JSON.parse(readFileSync("examples/birth.json", "utf8"));
  const v3 = contextFor(birth, [2026]);
  const v2 = contextFor(birth, [2026], "whoami.evidence.v2");
  const c = v3.candidateIds[0]!;
  assert.equal(v3.schema, "whoami.evidence.v3");
  assert(v3.facts.some((f) => f.id === `${c}.bazi.externalPatterns`));
  assert(!v2.facts.some((f) => f.id === `${c}.bazi.externalPatterns`));
  const pr = (e: typeof v3) => e.facts.find((f) => f.id === `${c}.bazi.patternReview`)!.value as Record<string, unknown>;
  assert("extendedPatterns" in pr(v3));
  assert(!("extendedPatterns" in pr(v2)));
  assert(v3.rules.find((r) => r.id === `${c}.R-bazi-pattern-review`)!.factRefs.includes(`${c}.bazi.externalPatterns`));
});
