import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { CAPTION_SPEECH, captionSpeechCheck, earlierSpeech, judgeCaptionSpeech, strokeCoverage, strokeMask } from '../caption-speech.mjs';
import { assetPhrases } from '../qa.mjs';
import { runCutChecks } from '../cut-checks.mjs';

// Synthetic 360×640 grey frames: mid-grey picture, captions are white bars with
// a black outline drawn in the caption band (62–86 % of the height).
const W = 360, H = 640;
function frame(glyphs = []) {
  const f = new Uint8Array(W * H).fill(120);
  for (const [x0, y0, w, h] of glyphs) {
    for (let y = y0 - 3; y < y0 + h + 3; y++) for (let x = x0 - 3; x < x0 + w + 3; x++) f[y * W + x] = 10; // outline
    for (let y = y0; y < y0 + h; y++) for (let x = x0; x < x0 + w; x++) f[y * W + x] = 240; // stroke
  }
  return f;
}
// Two different "lines": strokes at different places in the same band row.
const lineA = Array.from({ length: 8 }, (_, i) => [40 + i * 36, 470, 6, 24]);
const lineB = Array.from({ length: 8 }, (_, i) => [58 + i * 36, 470, 6, 24]);

test('stroke mask: outlined light strokes in the band; none in a plain or unoutlined picture', () => {
  const caption = strokeMask(frame(lineA), W, H);
  assert.ok(caption.share >= CAPTION_SPEECH.text_min_share, `share ${caption.share}`);
  assert.equal(strokeMask(frame(), W, H).share, 0);
  const bright = new Uint8Array(W * H).fill(230); // a light picture without outlines is not text
  assert.equal(strokeMask(bright, W, H).share, 0);
});

test('stroke coverage: the same line (±1 px) is covered, another line is not', () => {
  const a = strokeMask(frame(lineA), W, H);
  assert.equal(strokeCoverage(a, a, W), 1);
  const shifted = strokeMask(frame(lineA.map(([x, y, w, h]) => [x + 1, y, w, h])), W, H);
  assert.ok(strokeCoverage(a, shifted, W) >= 0.8);
  assert.ok(strokeCoverage(a, strokeMask(frame(lineB), W, H), W) < 0.2);
});

test('earlier speech: the last piece within the look-back, at least min_speech_seconds', () => {
  const phrases = [{ start: 8, end: 9.2, text: '上一句' }, { start: 9.5, end: 9.9, text: '你们看' }, { start: 9.95, end: 11, text: '哇哦' }];
  assert.equal(earlierSpeech(phrases, 10).ph.text, '你们看');
  assert.equal(earlierSpeech(phrases, 9.6).ph.text, '上一句', '0.1 s of 你们看 is too short; 上一句 (8.6–9.2 s inside the look-back) is sampled');
  assert.equal(earlierSpeech([{ start: 5, end: 6, text: 'far' }], 10), null, 'nothing spoken in the second before the cut');
});

test('judge: the opening line already on screen during earlier speech warns; a new line, no text or no speech is clear', () => {
  const fps = 30, at = 10;
  const times = Array.from({ length: 36 }, (_, k) => at - 1.1 + k / fps);
  const phrases = [{ start: 9.4, end: 9.95, text: '你们看' }, { start: 9.95, end: 11, text: '哇哦' }];
  const window = lines => ({ frames: times.map(t => frame(t < at - 1 / fps / 2 ? lines[0] : lines[1])), times, width: W, height: H });
  const same = judgeCaptionSpeech(window([lineA, lineA]), { at, phrases });
  assert.equal(same.result, 'warn');
  assert.deepEqual([same.earlier_speech, same.opening_speech, same.coverage], ['你们看', '哇哦', 1]);
  const changed = judgeCaptionSpeech(window([lineA, lineB]), { at, phrases });
  assert.equal(changed.result, 'clear');
  assert.ok(changed.coverage < CAPTION_SPEECH.coverage);
  assert.equal(judgeCaptionSpeech(window([[], []]), { at, phrases }).reason, 'no_text');
  assert.equal(judgeCaptionSpeech(window([lineA, lineA]), { at, phrases: [{ start: 10, end: 11, text: '新的' }] }).reason, 'no_earlier_speech');
});

test('check: out-points and assets without an analysis are not judged, decoded or counted', async () => {
  const check = captionSpeechCheck(point => point.item.asset_id === 'film' ? [{ start: 1, end: 2, text: 'x' }] : null);
  const item = { id: 'a', asset_id: 'film' };
  assert.equal(check.applies({ item, edge: 'out', source_seconds: 5 }), false);
  assert.deepEqual(check.skip({ item, edge: 'out', source_seconds: 5 }), { reason: 'out_point' });
  assert.equal(check.applies({ item: { ...item, asset_id: 'other' }, edge: 'in', source_seconds: 5 }), false);
  assert.deepEqual(check.skip({ item: { ...item, asset_id: 'other' }, edge: 'in', source_seconds: 5 }), { reason: 'no_analysis' });
  assert.deepEqual(check.range({ item, edge: 'in', source_seconds: 5 }), [3.9, 5.1]);
  // A decode failure leaves skipped points not_applicable; only judged in-points count.
  const doc = { canvas: { fps: 30 }, assets: [{ id: 'film', file: 'f.mp4' }, { id: 'other', file: 'o.mp4' }], tracks: [{ id: 'v', kind: 'video' }],
    items: [{ id: 'a', track_id: 'v', kind: 'media', asset_id: 'film', start_frame: 0, frames: 30, source_in_seconds: 5 },
      { id: 'b', track_id: 'v', kind: 'media', asset_id: 'other', start_frame: 30, frames: 30, source_in_seconds: 9 }] };
  const [result] = await runCutChecks(doc, '/nowhere', [check], { decode: async () => { throw new Error('decode failed'); } });
  assert.deepEqual(result.measured.points.map(e => [e.item_id, e.edge, e.result, e.reason ?? null]),
    [['a', 'in', 'unknown', null], ['a', 'out', 'not_applicable', 'out_point'], ['b', 'in', 'not_applicable', 'no_analysis'], ['b', 'out', 'not_applicable', 'out_point']]);
  assert.equal(result.applicable, 1);
  assert.equal(result.status, 'unknown');
  assert.match(result.observation, /1 of 1 cut point\(s\) were not checked \(a in\)/);
});

test('judge: a cut inside a phrase opens on that phrase (no earlier speech); speech beyond the look-ahead is none', () => {
  const fps = 30, at = 10, times = Array.from({ length: 36 }, (_, k) => at - 1.1 + k / fps);
  const window = { frames: times.map(() => frame(lineA)), times, width: W, height: H };
  const inside = judgeCaptionSpeech(window, { at, phrases: [{ start: 9, end: 11, text: '一整句' }] });
  assert.deepEqual([inside.result, inside.reason, inside.opening_speech], ['clear', 'no_earlier_speech', '一整句']);
  const silent = judgeCaptionSpeech(window, { at, phrases: [{ start: 9.2, end: 9.9, text: '上一句' }, { start: 13, end: 14, text: '很久以后' }] });
  assert.deepEqual([silent.result, silent.opening_speech], ['warn', null]);
});

test('qa --analysis: phrases per asset by media SHA-256; a foreign, duplicate or phrase-less analysis is refused', async t => {
  const dir = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'creative-caption-speech-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const sha = 'a'.repeat(64), doc = { assets: [{ id: 'film', sha256: sha }, { id: 'other', sha256: 'b'.repeat(64) }] };
  const write = async (name, value) => { const file = path.join(dir, name); await fs.writeFile(file, JSON.stringify(value)); return file; };
  const analysis = (media, phrases) => ({ schema: 'creative-craft.footage-analysis.v1', media: { sha256: media, path_basename: 'take.mp4' }, speech: { phrases } });
  const good = await write('a.json', analysis(sha, [{ start: 1, end: 2, text: '一句' }]));
  assert.deepEqual([...(await assetPhrases(doc, [good])).entries()], [['film', [{ start: 1, end: 2, text: '一句' }]]]);
  await assert.rejects(assetPhrases(doc, [await write('b.json', analysis('c'.repeat(64), [{ start: 1, end: 2, text: 'x' }]))]), /not an asset of this revision/);
  await assert.rejects(assetPhrases(doc, [await write('c.json', analysis(sha, []))]), /no ASR phrases/);
  await assert.rejects(assetPhrases(doc, [good, good]), /more than one --analysis/);
  await assert.rejects(assetPhrases(doc, [await write('e.json', analysis(sha, [{ from: 1, to: 2, text: 'x' }]))]), /speech\.phrases\[0\] needs numeric start < end and a text/);
  await assert.rejects(assetPhrases(doc, [await write('d.json', { schema: 'other' })]), /not a creative-craft\.footage-analysis\.v1 file/);
});
