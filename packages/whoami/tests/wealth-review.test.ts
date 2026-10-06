import { test } from "node:test";
import assert from "node:assert/strict";
import { buildChart, element, tenGod } from "../src/chart.js";
import { wealthReview } from "../src/wealth-review.js";
import { buildEvidence } from "../src/evidence.js";
const chart = buildChart({calendar:"solar",date:"2000-08-16",time:"04:00",place:"合成",longitude:120,timeZone:"Asia/Shanghai",gender:"female"},[2026]);
const base = chart.candidates[0]!.bazi;
// Synthetic structural fixtures; no claim that modified pillars form a calendar date.
function fixture(year: string, month: string, hour: string) {
  const b=structuredClone(base);
  for(const [position,stem] of [["year",year],["month",month],["hour",hour]]) {
    const p=b.pillars.find(p=>p.position===position)!;
    p.stem=stem!;p.element=element(stem!);p.tenGod=tenGod(b.dayMaster,stem!);
  }
  return b;
}
const check=(b: typeof base,id:string)=>wealthReview(b).checks.find(c=>c.id===id)!;
test("真实计算样例保留偏财两透与偏印线索，仍为未决",()=>{
  const r=wealthReview(base);
  assert.deepEqual(r.candidates,[{stem:"庚",tenGod:"偏财",exposedAt:["year","hour"]}]);
  assert.equal(check(base,"seal").prerequisite,"observed");
  assert.equal(check(base,"food").prerequisite,"not-observed"); // 戊仅藏于地支。
  assert.equal(r.judgment,"unresolved");
});
test("同五行异干不能触发月藏财星透出入口",()=>{
  const r=wealthReview(fixture("辛","甲","辛"));
  assert.equal(r.status,"outside-scope");assert.deepEqual(r.checks,[]);
});
test("支持与风险同时保留，不抵消",()=>{
  const b=fixture("庚","戊","壬");
  for(const id of ["food","killer","killer-food"]) assert.equal(check(b,id).prerequisite,"observed");
  assert.equal(wealthReview(b).judgment,"unresolved");
});
test("救应组合缺任一前提不能记为已见",()=>{
  for(const [id,b] of [["robber-food",fixture("庚","戊","甲")],["robber-officer",fixture("庚","癸","甲")],["killer-food",fixture("庚","壬","甲")]] as const)
    assert.equal(check(b,id).prerequisite,"not-observed");
});
test("食神不能偷换伤官，劫财不能偷换日主或比肩",()=>{
  assert.equal(check(fixture("庚","己","丁"),"food").prerequisite,"not-observed");
  assert.equal(check(fixture("庚","戊","丙"),"robber-food").prerequisite,"not-observed");
  assert.equal(check(fixture("庚","戊","丁"),"robber-food").prerequisite,"observed");
  assert.equal(check(fixture("庚","癸","丁"),"robber-officer").prerequisite,"observed");
});
test("日干本身不会导致比劫同透",()=>{
  assert.equal(check(base,"peer").prerequisite,"not-observed");
});
test("纯函数和证据引用保持候选隔离",()=>{
  const before=JSON.stringify(base);wealthReview(base);assert.equal(JSON.stringify(base),before);
  const c=structuredClone(chart);const second=structuredClone(c.candidates[0]!);
  second.id="C2-wealth";second.bazi=fixture("辛","甲","辛");c.candidates.push(second);
  const e=buildEvidence(c);
  for(const r of e.rules.filter(x=>x.id.endsWith("R-bazi-wealth-review")))
    assert(r.factRefs.every(id=>e.facts.some(f=>f.id===id&&f.candidate===r.candidate)));
  const values=e.facts.filter(f=>f.id.endsWith(".wealthReview")).map(f=>(f.value as ReturnType<typeof wealthReview>).status);
  assert.deepEqual(values,["candidate-only","outside-scope"]);
});

test("原示例财印相邻风险与隔位并存，不以隔位抵消相邻",()=>{
  const r=wealthReview(base).sealPlacement;
  assert.equal(r.status,"adjacent-risk");
  assert.deepEqual(r.pairs.map(p=>[p.wealth.position,p.seal.position,p.adjacent,p.between]),[
    ["year","month",true,[]],["hour","month",false,["day"]],
  ]);
  assert.equal(wealthReview(base).judgment,"unresolved");
});
test("论财正例显干配置通过不相邻窄条件，日主仍占柱位",()=>{
  // 原文乙未、甲申、丙申、庚寅；这里只复用其显干与申月结构，不冒充历法反查。
  const r=wealthReview(fixture("乙","甲","庚")).sealPlacement;
  assert.equal(r.status,"no-adjacent-pair");
  assert.equal(r.pairs.length,2);
  assert.deepEqual(r.pairs.map(p=>p.between),[["month","day"],["day"]]);
});
test("论财反例年财月印相邻；正偏财印保留各自身份",()=>{
  // 原文乙未、己卯、庚寅、辛巳的显干与月支结构。
  const b=fixture("乙","己","辛");b.dayMaster="庚";
  for(const p of b.pillars) p.tenGod=tenGod("庚",p.stem);
  const m=b.pillars.find(p=>p.position==="month")!;
  m.branch="卯";m.hiddenStems=[{stem:"乙",tenGod:"正财",element:"木"}];
  const r=wealthReview(b).sealPlacement;
  assert.equal(r.status,"adjacent-risk");
  assert.equal(r.pairs[0]!.wealth.tenGod,"正财");
  assert.equal(r.pairs[0]!.seal.tenGod,"正印");
});
test("缺印与入口外不能当作位置良好，藏干不偷换显干",()=>{
  assert.equal(wealthReview(fixture("庚","戊","壬")).sealPlacement.status,"not-applicable");
  assert.equal(wealthReview(fixture("辛","甲","辛")).sealPlacement.status,"not-applicable");
});
test("位置取柱名而非数组顺序，月令以外的显财也参加检查",()=>{
  const b=fixture("辛","甲","庚");
  assert.equal(wealthReview(b).sealPlacement.status,"adjacent-risk");
  const expected=wealthReview(b).sealPlacement.pairs.map(p=>JSON.stringify(p)).sort();
  b.pillars.reverse();
  assert.deepEqual(wealthReview(b).sealPlacement.pairs.map(p=>JSON.stringify(p)).sort(),expected);
});

test("财官同透而伤官透出时阻止直接采用纯财官分支",()=>{
  const r=wealthReview(fixture("庚","癸","己"));
  assert.equal(r.officerBranch.status,"blocked");
  assert.deepEqual(r.officerBranch.blockers,["no-visible-hurting"]);
  assert.deepEqual(r.officerBranch.checks[0]!.positions,[{position:"hour",stem:"己",tenGod:"伤官"}]);
  assert.equal(r.judgment,"unresolved"); // 分支阻断不升级为全局破格。
});
test("财官杀同透给出七杀反例，不能把七杀当正官",()=>{
  assert.deepEqual(wealthReview(fixture("庚","癸","壬")).officerBranch.blockers,["no-visible-killer"]);
  assert.equal(wealthReview(fixture("庚","戊","壬")).officerBranch.status,"not-applicable");
});
test("食神不偷换伤官，显干无反例仍不能判成立",()=>{
  const r=wealthReview(fixture("庚","癸","戊")).officerBranch;
  assert.equal(r.status,"pending");assert.deepEqual(r.blockers,[]);
  assert(r.checks.every(c=>c.result==="not-observed"));
  // 基础申月仍藏壬杀；显干未见不等于全盘无杀或已经不混杀。
  assert(base.pillars.find(p=>p.position==="month")!.hiddenStems.some(h=>h.tenGod==="七杀"));
});
test("入口外保留观察但不阻断，缺官不能当检查通过",()=>{
  const r=wealthReview(fixture("辛","癸","己")).officerBranch;
  assert.equal(r.status,"not-applicable");assert.deepEqual(r.blockers,[]);
  assert.equal(r.checks[0]!.result,"counterexample");
  assert.equal(wealthReview(base).officerBranch.status,"not-applicable");
});
test("财官分支候选隔离且不修改输入",()=>{
  const c=structuredClone(chart);c.candidates[0]!.bazi=fixture("庚","癸","己");
  const second=structuredClone(c.candidates[0]!);second.id="C2-officer";
  second.bazi=fixture("庚","癸","戊");c.candidates.push(second);
  const before=JSON.stringify(c);const e=buildEvidence(c);
  assert.equal(JSON.stringify(c),before);
  assert.deepEqual(e.facts.filter(f=>f.id.endsWith('.wealthReview')).map(f=>(f.value as ReturnType<typeof wealthReview>).officerBranch.status),["blocked","pending"]);
});
