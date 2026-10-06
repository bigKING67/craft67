import { test } from 'node:test';
import assert from 'node:assert/strict';
import { captionBox, graphicBox, insideSafeArea, textEm } from '../safe-area.mjs';

const landscape = { width: 1280, height: 720 }, portrait = { width: 720, height: 1280 };
const style = { fontHeight: .04, centerY: .8, color: '#ffffff', strokeWidth: .0015, weight: 700 };

test('text width estimate: full-width CJK 1 em, other characters 0.55 em, spaces 0.3 em', () => {
  assert.equal(Math.round(textEm('主讲人 ab，Ｑ') * 100) / 100, 6.4);
});
test('caption boxes follow the compiled caption CSS and wrap inside 7%–93%', () => {
  const plain = captionBox(landscape, { text: '口播：第一句' });
  assert.deepEqual([plain.left, plain.right, plain.bottom, plain.lines], [0.07, 0.93, 0.92, 1]);
  assert.ok(insideSafeArea(plain));
  assert.ok(insideSafeArea(captionBox(landscape, { text: '品牌：让细节先说话', style })));
  // Large two-line caption centred at 90% height spills past the bottom margin.
  const low = captionBox(landscape, { text: '第一行字幕\n第二行字幕', style: { ...style, fontHeight: .08, centerY: .9 } });
  assert.equal(low.lines, 2);
  assert.ok(!insideSafeArea(low) && low.bottom > 0.95);
  // A long line wraps (more lines, taller box) instead of widening.
  assert.ok(captionBox(portrait, { text: '很'.repeat(40), style }).lines >= 2);
});
test('graphic boxes are the placement box only (load-time guarantee, no text-fit estimate)', () => {
  const lower = graphicBox({ template: 'lower-third', vars: { title: '一'.repeat(16), subtitle: '二'.repeat(24) } });
  assert.deepEqual(lower, { left: 0.06, top: 0.7, right: 0.84, bottom: 0.9 }, 'no placement = template default (bottom)');
  assert.deepEqual(graphicBox({ template: 'lower-third', vars: { title: '一', placement: 'upper' } }), { left: 0.06, top: 0.14, right: 0.84, bottom: 0.34 });
  assert.deepEqual(graphicBox({ template: 'title-card', vars: { title: '一', placement: 'top' } }), { left: 0.1, top: 0.08, right: 0.9, bottom: 0.28 });
  assert.ok(insideSafeArea(lower));
  assert.ok(insideSafeArea(graphicBox({ template: 'title-card', vars: { title: '一'.repeat(12) } })));
});
