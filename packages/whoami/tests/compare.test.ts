import { test } from 'node:test';
import assert from 'node:assert/strict';
import { compareBirths } from '../src/compare.js';
const birth={calendar:'solar',date:'1996-07-19',time:'09:40',gender:'female',place:'合成',longitude:120,timeZone:'Asia/Shanghai',timeBasis:'true-solar'};

test('同输入无差异；同一时辰更正仍识别起运与证据变化',()=>{
 const same=compareBirths(birth,birth,[2026]);assert.equal(same.status,'compared');
 if(same.status!=='compared')throw new Error('expected compared');
 assert.deepEqual(same.changedFacts,[]);assert(same.evidenceBinding.bindingMatch);
 const diff=compareBirths(birth,{...birth,time:'10:10'},[2026]);
 if(diff.status!=='compared')throw new Error('expected compared');
 assert.deepEqual(diff.changedInputFields,['time']);
 assert.deepEqual(diff.changedFacts.map(f=>f.key),['input.time','bazi.cycles']);
 assert(!diff.evidenceBinding.bindingMatch);
 assert(diff.unchangedFactKeys.includes('bazi.hour'));
});
test('跨时辰逐项比较四柱和紫微，不按候选ID假装同盘',()=>{
 const b={...birth,date:'1993-11-08',time:'14:20'};
 const r=compareBirths(b,{...b,time:'14:50'},[2026]);
 if(r.status!=='compared')throw new Error('expected compared');
 assert.notEqual(r.selected.before,r.selected.after);
 assert(r.changedFacts.some(f=>f.key==='bazi.hour'));
 assert(r.changedFacts.some(f=>f.key==='ziwei.base'));
 assert(r.changedFacts.every(f=>f.before?.factId.startsWith(r.selected.before)&&f.after?.factId.startsWith(r.selected.after)));
});
test('地点仅改显示文字可无事实差异但旧绑定仍不相同',()=>{
 const r=compareBirths(birth,{...birth,place:'另一个显示标签'},[2026]);
 if(r.status!=='compared')throw new Error('expected compared');
 assert.deepEqual(r.changedFacts,[]);assert.deepEqual(r.changedInputFields,['place']);
 assert(!r.evidenceBinding.bindingMatch);
});
test('多候选不自动配对，显式比较仍保留未定状态',()=>{
 const b={...birth,date:'1988-02-15',time:'23:00',timeBasis:'civil',uncertaintyMinutes:2};
 const r=compareBirths(b,b,[2026]);assert.equal(r.status,'needs-selection');
 assert.equal(r.before.candidates.length,2);assert.equal(r.before.status,'ambiguous');
 const selected=compareBirths(b,b,[2026],{beforeCandidate:r.before.candidates[0]!.id,afterCandidate:r.after.candidates[1]!.id});
 if(selected.status!=='compared')throw new Error('expected compared');
 assert.equal(selected.before.status,'ambiguous');assert.equal(selected.after.status,'ambiguous');
 assert(selected.changedFacts.some(f=>f.key==='bazi.day'));assert(selected.evidenceBinding.bindingMatch);
 assert.throws(()=>compareBirths(b,b,[2026],{beforeCandidate:'不存在'}),/候选不存在/);
});
test('未知时辰要求补资料，不产生空盘或自动选择',()=>{
 const r=compareBirths(birth,{...birth,time:null},[2026]);
 assert.equal(r.status,'needs-input');assert.equal(r.after.candidates.length,0);
 assert(!('changedFacts' in r));
 if(r.status==='needs-input')assert.equal(r.questions[0]!.side,'after');
});
test('单候选不确定区间仍保留警告，不修改用户输入',()=>{
 const b={...birth,uncertaintyMinutes:1};const original=JSON.stringify(b);
 const r=compareBirths(b,b,[2026]);assert.equal(JSON.stringify(b),original);
 assert.equal(r.status,'compared');assert.equal(r.before.status,'ambiguous');
 assert.equal(r.before.candidates.length,1);assert(r.before.warnings.length>0);
});
