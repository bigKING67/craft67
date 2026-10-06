import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildChart } from '../src/chart.js';
import { ziweiTransforms } from '../src/ziwei-transforms.js';
import { ziweiLayerReview, describeLayerEntry } from '../src/ziwei-layer-review.js';
const input={calendar:'solar',date:'1996-07-19',time:'09:40',gender:'female',place:'合成',longitude:120,timeZone:'Asia/Shanghai',timeBasis:'true-solar'};
const value=ziweiTransforms(buildChart(input,[2026,2027,2028]).candidates[0]!.ziwei);

test('天同生年禄与大限忌、流年四化均保留；相同禄不累计打分',()=>{
 const r=ziweiLayerReview(value);
 assert.deepEqual(r[0]!.contrasts.find(x=>x.star==='天同')!.entries.map(e=>[e.layer,e.mutagen]),[['生年','禄'],['大限2018—2027','忌'],['流年2026','禄']]);
 assert.deepEqual(r[1]!.contrasts.find(x=>x.star==='天同')!.entries.map(e=>e.mutagen),['禄','忌','权']);
});
test('2028切换大限，不把上一大限天同忌带到新范围',()=>{
 const r=ziweiLayerReview(value)[2]!;
 assert(!r.contrasts.some(x=>x.star==='天同'));
 assert(r.contrasts.every(x=>x.entries.every(e=>!e.layer.includes('2018—2027'))));
 assert(!r.contrasts.some(x=>x.star==='太阴')); // 只见流年权，无其他层异化，不制造差异。
 assert.deepEqual(r.contrasts.find(x=>x.star==='天机')!.entries.map(e=>e.mutagen),['权','忌']);
});
test('本命宫位与流年宫职分别保留，不生成大限宫职',()=>{
 const x=ziweiLayerReview(value)[0]!.contrasts.find(x=>x.star==='天同')!;
 const annual=x.entries.find(e=>e.layer==='流年2026')!;
 assert.equal(annual.natalPalace,'夫妻');assert.equal(annual.yearlyPalace,'迁移');
 assert(!('yearlyPalace' in x.entries.find(e=>e.layer.startsWith('大限'))!));
 assert(describeLayerEntry({...annual,yearlyPalace:null}).includes('流年宫职未定位'));
});
test('缺失和歧义不取第一个目标，定位缺口继续显示',()=>{
 const t=structuredClone(value);
 t.origin[0]!.status='unresolved';
 t.yearly[0]!.transformations[0]!.status='ambiguous-star';
 t.decadals[0]!.transformations[3]!.status='missing-star';
 const r=ziweiLayerReview(t)[0]!;
 assert.equal(r.gaps.length,3);
 assert(!r.contrasts.some(x=>x.star==='天同'));
 assert.deepEqual(r.gaps.map(g=>g.status),['unresolved','missing-star','ambiguous-star']);
});
test('未请求年份不制造差异，比较不改写原证据',()=>{
 const before=JSON.stringify(value);ziweiLayerReview(value);assert.equal(JSON.stringify(value),before);
 assert.deepEqual(ziweiLayerReview({...value,yearly:[]}),[]);
});

test('无跨层差异的星也保留流年宫职缺失，不拿本命宫名补齐',()=>{
 const t=structuredClone(value);
 const taiyin=t.yearly[2]!.transformations.find(x=>x.star==='太阴')!;
 taiyin.targets[0]!.scopePalace=null;
 const r=ziweiLayerReview(t)[2]!;
 assert(!r.contrasts.some(x=>x.star==='太阴'));
 assert(r.gaps.some(g=>g.star==='太阴'&&g.status==='missing-yearly-palace'));
 assert.equal(taiyin.targets[0]!.natalPalace,'夫妻');
});
