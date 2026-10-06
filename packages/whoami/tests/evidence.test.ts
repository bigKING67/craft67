import { test } from "node:test";
import assert from "node:assert/strict";
import { buildChart } from "../src/chart.js";
import { buildEvidence } from "../src/evidence.js";

const input = { calendar: "solar", date: "2000-08-16", time: "04:00", place: "合成", longitude: 120, timeZone: "Asia/Shanghai", gender: "female" };
const chart = buildChart(input, [2026]);
const evidence = buildEvidence(chart);
const details = (e: typeof evidence, candidate = e.candidateIds[0]) => e.facts.find(f => f.id === `${candidate}.bazi.rootDetails`)!.value as Array<{ position: string; branch: string; hiddenStem: string; sameStemAsDayMaster: boolean; clashSources: Array<{ position: string; branch: string }> }>;

test("寅申冲保留寅中丙根，并区别午中丁与日主同干", () => {
  assert.deepEqual(details(evidence), [
    { position: "day", branch: "午", hiddenStem: "丁", element: "火", tenGod: "劫财", sameStemAsDayMaster: false, clashSources: [] },
    { position: "hour", branch: "寅", hiddenStem: "丙", element: "火", tenGod: "比肩", sameStemAsDayMaster: true, clashSources: [{position: "month", branch: "申"}] },
  ]);
});

test("移除直接冲只改变关系，不删除藏干事实", () => {
  // 仅验证事实联结：人工改写的盘面 fixture 不是可用于真人解读的排盘。
  const c = structuredClone(chart);
  c.candidates[0]!.bazi.pillars[1]!.branch = "酉";
  const roots = details(buildEvidence(c));
  assert.equal(roots.length, 2);
  assert.deepEqual(roots[1]!.clashSources, []);
  assert.equal(roots[1]!.hiddenStem, "丙");
});

test("不同柱的重复冲源保留位置，不只按地支去重", () => {
  const c = structuredClone(chart);
  c.candidates[0]!.bazi.pillars[0]!.branch = "申";
  assert.deepEqual(details(buildEvidence(c))[1]!.clashSources, [
    { position: "year", branch: "申" }, { position: "month", branch: "申" },
  ]);
});

test("候选盘根事实与规则引用相互隔离", () => {
  const c = structuredClone(chart);
  const second = structuredClone(c.candidates[0]!);
  second.id = "C2-test";
  second.bazi.pillars[1]!.branch = "酉";
  c.candidates.push(second);
  const e = buildEvidence(c);
  assert.equal(details(e)[1]!.clashSources.length, 1);
  assert.equal(details(e, second.id)[1]!.clashSources.length, 0);
  for (const r of e.rules.filter(r => r.id.endsWith("R-bazi-root-review"))) {
    assert(r.factRefs.every(id => e.facts.some(f => f.id === id && f.candidate === r.candidate)));
  }
});

test("没有同五行藏干时不补造根，不输出旺衰结论", () => {
  const c = structuredClone(chart);
  c.candidates[0]!.bazi.dayMaster = "辛";
  for (const p of c.candidates[0]!.bazi.pillars) p.hiddenStems = p.hiddenStems.filter(s => s.element !== "金");
  assert.deepEqual(details(buildEvidence(c)), []);
});

const exposure = (e: typeof evidence, candidate = e.candidateIds[0]) => e.facts.find(f => f.id === `${candidate}.bazi.monthExposure`)!.value as { monthBranch: string; dayMaster: string; hiddenStems: Array<{stem:string; tenGod:string; matchesDayMaster:boolean; exposedAt:string[]}> };

test("申月庚透年时、壬戊未透，保留十神与全部位置", () => {
  assert.deepEqual(exposure(evidence), {
    monthBranch: "申", dayMaster: "丙", hiddenStems: [
      {stem:"庚",element:"金",tenGod:"偏财",matchesDayMaster:false,exposedAt:["year","hour"]},
      {stem:"壬",element:"水",tenGod:"七杀",matchesDayMaster:false,exposedAt:[]},
      {stem:"戊",element:"土",tenGod:"食神",matchesDayMaster:false,exposedAt:[]},
    ],
  });
});
test("同五行异干不算透出；另干透出不隐藏并存线索", () => {
  const c=structuredClone(chart);
  c.candidates[0]!.bazi.pillars[0]!.stem="辛";
  c.candidates[0]!.bazi.pillars[1]!.stem="壬";
  const h=exposure(buildEvidence(c)).hiddenStems;
  assert.deepEqual(h.map(x=>x.exposedAt), [["hour"],["month"],[]]);
});
test("日干同字单列，不因日主出现就伪造年/月/时透干", () => {
  const c=structuredClone(chart);
  c.candidates[0]!.bazi.dayMaster="壬";
  c.candidates[0]!.bazi.pillars[2]!.stem="壬";
  const h=exposure(buildEvidence(c)).hiddenStems.find(x=>x.stem==="壬")!;
  assert.equal(h.matchesDayMaster,true);
  assert.deepEqual(h.exposedAt,[]);
});
test("新增候选透干不污染另一候选，规则引用完整", () => {
  const c=structuredClone(chart);
  const second=structuredClone(c.candidates[0]!); second.id="C2-exposure";
  second.bazi.pillars[0]!.stem="壬"; c.candidates.push(second);
  const e=buildEvidence(c);
  assert.deepEqual(exposure(e).hiddenStems[1]!.exposedAt,[]);
  assert.deepEqual(exposure(e,second.id).hiddenStems[1]!.exposedAt,["year"]);
  for(const r of e.rules.filter(r=>r.id.endsWith("R-bazi-month-exposure")))
    assert(r.factRefs.every(id=>e.facts.some(f=>f.id===id&&f.candidate===r.candidate)));
});

test("缺少或提供地点来源均显式进入证据", () => {
  const missing = buildEvidence(buildChart(input, [2026]));
  assert.deepEqual(
    missing.facts.find((fact) => fact.id.endsWith(".input.provenance"))!.value,
    {
      status: "unverified",
      missing: ["placeSource", "longitudeSource", "timeZoneSource"],
    },
  );
  const provided = buildEvidence(
    buildChart(
      {
        ...input,
        provenance: {
          longitudeSource: "公开地名库",
          timeZoneSource: "IANA tzdb",
        },
      },
      [2026],
    ),
  );
  assert.deepEqual(
    provided.facts.find((fact) => fact.id.endsWith(".input.provenance"))!
      .value,
    {
      status: "partial",
      longitudeSource: "公开地名库",
      timeZoneSource: "IANA tzdb",
      missing: ["placeSource"],
    },
  );
  const verifiedOnly = buildEvidence(
    buildChart(
      { ...input, provenance: { verifiedAt: "2026-09-23" } },
      [2026],
    ),
  );
  assert.deepEqual(
    verifiedOnly.facts.find((fact) =>
      fact.id.endsWith(".input.provenance"),
    )!.value,
    {
      status: "unverified",
      verifiedAt: "2026-09-23",
      missing: ["placeSource", "longitudeSource", "timeZoneSource"],
    },
  );
  const complete = buildEvidence(
    buildChart(
      {
        ...input,
        provenance: {
          placeSource: "出生记录",
          longitudeSource: "公开地名库",
          timeZoneSource: "IANA tzdb",
        },
      },
      [2026],
    ),
  );
  assert.deepEqual(
    complete.facts.find((fact) =>
      fact.id.endsWith(".input.provenance"),
    )!.value,
    {
      status: "provided",
      placeSource: "出生记录",
      longitudeSource: "公开地名库",
      timeZoneSource: "IANA tzdb",
    },
  );
});
