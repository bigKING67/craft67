// Run from any cwd after building whoami: node examples/acceptance/cross-system/verify-facts.mjs
// Synthetic inputs only; no network, persistence, or model call.
import assert from 'node:assert/strict';
import { Solar, Lunar } from 'lunar-typescript';
import iztro from 'iztro';
import { buildChart } from '../../../dist/chart.js';

const input = {
  calendar: 'solar', date: '1993-11-08', time: '14:20', gender: 'female',
  place: '合成东经120度', longitude: 120, timeZone: 'Asia/Shanghai', timeBasis: 'true-solar',
};
iztro.astro.config({ yearDivide: 'normal', ageDivide: 'normal', horoscopeDivide: 'normal', dayDivide: 'forward', algorithm: 'default' });
const natal = iztro.astro.bySolar('1993-11-08', 7, '女', true, 'zh-CN');
const expected = [
  ['2026-02-03', '乙巳', '乙巳'],
  ['2026-02-10', '丙午', '乙巳'],
  ['2026-02-17', '丙午', '丙午'],
];
const yearBoundaries = expected.map(([date, baziExpected, ziweiExpected]) => {
  const [year, month, day] = date.split('-').map(Number);
  const lunar = Solar.fromYmdHms(year, month, day, 12, 0, 0).getLunar();
  const h = natal.horoscope(date, 6);
  const baziYear = lunar.getYearInGanZhiExact();
  const ziweiYear = h.yearly.heavenlyStem + h.yearly.earthlyBranch;
  assert.equal(baziYear, baziExpected);
  assert.equal(ziweiYear, ziweiExpected);
  return { date, clock: '12:00 +08:00', baziYear, ziweiYear };
});
const changedBirth = ['14:20', '14:50'].map(time => {
  const c = buildChart({ ...input, time }, [2026, 2027, 2028]);
  const a = c.candidates[0];
  return { time, chartId: c.chartId, candidate: a.id, pillars: a.bazi.pillars.map(p => p.value), soulPalace: a.ziwei.soulPalace, bodyPalace: a.ziwei.bodyPalace };
});
assert.deepEqual(changedBirth[0].pillars, ['癸酉', '癸亥', '癸巳', '己未']);
assert.deepEqual(changedBirth[1].pillars, ['癸酉', '癸亥', '癸巳', '庚申']);
assert.notEqual(changedBirth[0].chartId, changedBirth[1].chartId);
assert.deepEqual(changedBirth.map(x => [x.soulPalace, x.bodyPalace]), [['卯', '巳'], ['寅', '午']]);
const l = Solar.fromYmd(2026, 2, 10).getLunar();
console.log(JSON.stringify({
  status: 'pass', scope: 'calendar facts and input identity, not semantic classification',
  lichunFixedUTC8: l.getJieQiTable()['立春'].toYmdHms(),
  lunarNewYear: Lunar.fromYmd(2026, 1, 1).getSolar().toYmd(), yearBoundaries, changedBirth,
}, null, 2));
