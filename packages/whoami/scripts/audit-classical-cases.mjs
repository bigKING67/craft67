// Read-only structural audit. Does not reconstruct dates or infer strength/useful elements.
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { LunarUtil } from 'lunar-typescript';
import { STEMS, BRANCHES, element, tenGod } from '../dist/chart.js';

const data = JSON.parse(readFileSync(new URL('../references/classical-strength-cases.json', import.meta.url), 'utf8'));
const ids = new Set();
const cases = data.cases.map(c => {
  assert.equal(typeof c.id, 'string');
  assert(!ids.has(c.id), `Duplicate case: ${c.id}`);
  ids.add(c.id);
  assert.equal(c.pillars.length, 4, c.id);
  for (const value of c.pillars) {
    assert.equal(typeof value, 'string');
    assert.equal(value.length, 2);
    assert(STEMS.includes(value[0]) && BRANCHES.includes(value[1]), value);
    assert.equal(STEMS.indexOf(value[0]) % 2, BRANCHES.indexOf(value[1]) % 2, value);
  }
  const dm = c.pillars[2][0];
  // Five-rat and five-tiger stem consistency; no absolute calendar or birth-time claim.
  const hourBranch = BRANCHES.indexOf(c.pillars[3][1]);
  assert.equal(c.pillars[3][0], STEMS[((STEMS.indexOf(dm) % 5) * 2 + hourBranch) % 10], `${c.id}: hour`);
  const monthOffset = (BRANCHES.indexOf(c.pillars[1][1]) + 10) % 12;
  const firstMonthStem = (STEMS.indexOf(c.pillars[0][0]) % 5 * 2 + 2) % 10;
  assert.equal(c.pillars[1][0], STEMS[(firstMonthStem + monthOffset) % 10], `${c.id}: month`);
  return {
    id: c.id,
    dayMaster: dm,
    pillars: c.pillars.map((value, i) => ({
      position: ['year', 'month', 'day', 'hour'][i], value,
      tenGod: i === 2 ? '日主' : tenGod(dm, value[0]),
      hiddenStems: LunarUtil.ZHI_HIDE_GAN[value[1]].map(stem => ({ stem, element: element(stem), tenGod: tenGod(dm, stem) })),
    })),
  };
});
console.log(JSON.stringify({ scope: 'structural-only; no chartId, birthday, strength label or historical outcome validation', hiddenStemOrder: 'descriptive library order, not strength weights', cases }, null, 2));
