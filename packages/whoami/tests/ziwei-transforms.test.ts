import { test } from "node:test";
import assert from "node:assert/strict";
import { buildChart } from "../src/chart.js";
import { ziweiTransforms } from "../src/ziwei-transforms.js";
import { buildEvidence } from "../src/evidence.js";
const input={calendar:"solar",date:"2000-08-16",time:"04:00",place:"合成",longitude:120,timeZone:"Asia/Shanghai",gender:"female"};
const chart=buildChart(input,[2025,2026]);
const z=chart.candidates[0]!.ziwei;
test("丙年禄权科忌依序落天同天机文昌廉贞，区分生年与流年",()=>{
  const r=ziweiTransforms(z);
  const year=r.yearly.find(x=>x.year===2026)!;
  assert.deepEqual(year.transformations.map(x=>[x.mutagen,x.star,x.targets[0]!.natalPalace]),[
    ["禄","天同","疾厄"],["权","天机","兄弟"],["科","文昌","福德"],["忌","廉贞","官禄"],
  ]);
  assert.equal(r.origin.find(x=>x.mutagen==="忌")!.stars[0],"天同");
  assert.equal(r.decadals[0]!.decadalLifePalace,"夫妻");
  assert.equal(r.decadals[0]!.transformations[0]!.targets[0]!.natalPalace,"子女");
});
test("流年宫职按固定宫位索引联结，不按当前数组位置",()=>{
  const copy=structuredClone(z);copy.palaces.reverse();
  const r=ziweiTransforms(copy);
  for(const y of r.yearly) for(const t of y.transformations) for(const p of t.targets)
    assert.equal(p.scopePalace,z.yearly.find(v=>v.year===y.year)!.palaceNames[p.palaceIndex]);
  assert(r.yearly.find(x=>x.year===2025)!.transformations.some(x=>x.targets.some(p=>p.natalPalace!==p.scopePalace)));
});
test("大限年份闭区间不重复交界年",()=>{
  const end=ziweiTransforms(buildChart(input,[2031]).candidates[0]!.ziwei);
  const next=ziweiTransforms(buildChart(input,[2032]).candidates[0]!.ziwei);
  assert.deepEqual(end.decadals.map(x=>x.yearRangeInclusive),[[2022,2031]]);
  assert.deepEqual(next.decadals.map(x=>x.yearRangeInclusive),[[2032,2041]]);
});
test("缺星与重名不静默选第一个宫",()=>{
  const missing=structuredClone(z);
  for(const p of missing.palaces)p.majorStars=p.majorStars.filter(s=>s.name!=="天同");
  const m=ziweiTransforms(missing).yearly.find(y=>y.year===2026)!.transformations[0]!;
  assert.equal(m.status,"missing-star");assert.deepEqual(m.targets,[]);
  const duplicate=structuredClone(z);
  duplicate.palaces[0]!.majorStars.push({name:"天同",brightness:"",mutagen:""});
  const d=ziweiTransforms(duplicate).yearly.find(y=>y.year===2026)!.transformations[0]!;
  assert.equal(d.status,"ambiguous-star");assert.equal(d.targets.length,2);
});
test("缺少四化槽保留缺失标识，缺流年宫职不补本命宫名",()=>{
  const copy=structuredClone(z);copy.yearly[0]!.mutagen=[];copy.yearly[1]!.palaceNames=[];
  const r=ziweiTransforms(copy);
  assert(r.yearly[0]!.transformations.every(x=>x.status==="missing-transform"&&x.star===null));
  assert(r.yearly[1]!.transformations.every(x=>x.targets.every(t=>t.scopePalace===null)));
});
test("不请求流年时仍给生年层，且不列无关大限",()=>{
  const copy=structuredClone(z);copy.yearly=[];
  const r=ziweiTransforms(copy);assert.equal(r.origin.length,4);assert.deepEqual(r.decadals,[]);
});
test("不改变原盘，证据与规则引用均在当前候选",()=>{
  const before=JSON.stringify(z);ziweiTransforms(z);assert.equal(JSON.stringify(z),before);
  const c=structuredClone(chart);const second=structuredClone(c.candidates[0]!);second.id="C2-transform";c.candidates.push(second);
  const e=buildEvidence(c);
  for(const rule of e.rules.filter(r=>r.id.endsWith("R-ziwei-transformations")))
    assert(rule.factRefs.every(id=>e.facts.some(f=>f.id===id&&f.candidate===rule.candidate)));
});
