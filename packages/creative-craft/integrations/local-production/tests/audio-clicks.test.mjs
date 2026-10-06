// Cut-point audio (0.8.0): cut-edge declick, equal-power crossfade, the click
// QA heuristic and the 512-point lane limit with the extra points. Gains are
// sampled with HyperFrames' own lane sampler (as the engine bakes them into the
// PCM); the click cases go through a real AAC encode/decode like a render.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { sampleAutomationLane } from '@hyperframes/core/audio-automation';
import { CROSSFADE_SEGMENTS, CUT_DECLICK_SECONDS, MAX_VOLUME_POINTS, checkVolumeAutomation, envelopeIndex, itemEnvelope, volumeEnvelope } from '../timeline.mjs';
import { compose } from '../composition.mjs';
import { CLICK_FLOOR, CLICK_RATIO, audioCutPoints, clickCheck, clickScore, cutPointClicks, judgeClicks } from '../audio-clicks.mjs';
import { ebur128Summary } from '../media-analysis.mjs';
import { audibleItems } from '../timeline.mjs';
import { ffmpeg, tempDir } from './media-fixtures.mjs';

const RATE = 48000, FPS = 30;
const sha = c => c.repeat(64);
const asset = (id, c, audio = true) => ({ id, sha256: sha(c), file: `assets/${sha(c)}.media`, duration: 60, video: true, audio, width: 64, height: 36, origin: { kind: 'import' } });
const doc = items => ({ schema_version: 'creative-craft.edit-document.v2', project_id: 'clicks', title: 'clicks', revision: 1, parent_sha256: null,
  canvas: { width: 640, height: 360, fps: FPS }, assets: [asset('a', 'a'), asset('b', 'b')],
  tracks: [{ id: 'v', kind: 'video', locked: false }, { id: 'm', kind: 'audio', locked: false }], items,
  change: { author: 'system', summary: 'test', operations_sha256: null } });
const media = (id, asset_id, start_frame, frames, source_in_seconds, extra = {}) =>
  ({ id, track_id: 'v', kind: 'media', asset_id, start_frame, frames, source_in_seconds, volume: 1, fit: 'cover', ...extra });

// Gain of one item at output time t, sampled from its lane the way the engine does.
function gainOf(d, item, index) {
  const envelope = volumeEnvelope(d, item, index), start = item.start_frame / FPS, end = (item.start_frame + item.frames) / FPS;
  const lane = envelope && { target: 'volume', points: envelope.map(([t, v]) => ({ t: t - start, v })) };
  return t => t < start || t >= end ? 0 : lane ? sampleAutomationLane(lane, t - start) : item.volume;
}
// Mono mix of the items, each playing `signal(asset_id, sourceSeconds)` × its gain.
function mix(d, signal, seconds, declickSeconds) {
  const index = envelopeIndex(d, { declickSeconds }), x = new Float32Array(Math.round(seconds * RATE));
  for (const item of audibleItems(d)) {
    const gain = gainOf(d, item, index), start = item.start_frame / FPS;
    const from = Math.round(start * RATE), to = Math.min(x.length, Math.round((item.start_frame + item.frames) / FPS * RATE));
    for (let n = from; n < to; n++) x[n] += gain(n / RATE) * signal(item.asset_id, item.source_in_seconds + n / RATE - start);
  }
  return x;
}
async function aacRoundTrip(dir, name, x) {
  const raw = path.join(dir, `${name}.f32`), file = path.join(dir, `${name}.m4a`);
  await fs.writeFile(raw, Buffer.from(x.buffer));
  await ffmpeg('-f', 'f32le', '-ar', String(RATE), '-ac', '1', '-i', raw, '-c:a', 'aac', '-b:a', '192k', '-n', file);
  return file;
}
const db = (p, ref) => 10 * Math.log10(p / ref);
const power = (x, from, to) => { let sum = 0; for (let n = Math.round(from * RATE); n < Math.round(to * RATE); n++) sum += x[n] ** 2; return sum / (Math.round(to * RATE) - Math.round(from * RATE)); };

test('cut-edge declick: hard edges ramp over 4 ms, explicit fades/crossfades and source-origin in points do not', () => {
  const d = doc([media('one', 'a', 0, 30, 2), media('two', 'b', 30, 30, 0), media('three', 'a', 60, 30, 5, { fade_in_frames: 3, fade_out_frames: 3 }),
    media('four', 'b', 87, 30, 1, { transition_in: { kind: 'crossfade', frames: 3 } })]);
  const index = envelopeIndex(d), lane = id => itemEnvelope(d, d.items.find(i => i.id === id), 'audio', index);
  assert.equal(CUT_DECLICK_SECONDS, 0.004);
  assert.deepEqual(lane('one'), [[0, 0], [0.004, 1], [1 - 0.004, 1], [1, 0]], 'cut into the source: both edges ramp (no sound before it does not matter)');
  assert.deepEqual(lane('two'), [[1, 1], [2 - 0.004, 1], [2, 0]], 'source origin: the in edge keeps its attack');
  assert.ok(!lane('three').some(([t]) => Math.abs(t - 2 - 0.004) < 1e-9), 'explicit fades replace the declick');
  // three is the crossfade predecessor of four: its tail is the equal-power fade.
  assert.equal(lane('four').length, CROSSFADE_SEGMENTS + 1 + 2, 'crossfade in, then a declicked out edge');
  // Declick off (test injection) leaves constant lanes constant.
  assert.equal(itemEnvelope(d, d.items[0], 'audio', envelopeIndex(d, { declickSeconds: 0 })), null);
  // Pictures keep their linear opacity crossfade and get no declick.
  assert.deepEqual(itemEnvelope(d, d.items[3], 'visual', index), [[87 / 30, 0], [87 / 30 + 3 / 30, 1], [117 / 30, 1]]);
  assert.equal(itemEnvelope(d, d.items[0], 'visual', index), null);
});

test('click QA: two out-of-phase sines spliced at a hard cut click without the declick and not with it', async t => {
  const dir = await tempDir('creative-clicks-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  // Same 440 Hz tone in both assets, a quarter period apart: the splice steps by ~0.7 of the amplitude.
  const signal = (id, s) => 0.5 * Math.sin(2 * Math.PI * 440 * s + (id === 'b' ? Math.PI / 2 : 0));
  const d = doc([media('left', 'a', 0, 30, 1.1), media('right', 'b', 30, 30, 2.3)]);
  const points = audioCutPoints(d, audibleItems(d), 2);
  assert.deepEqual(points.map(p => [p.time, p.items]), [[1, [{ item_id: 'left', edge: 'out' }, { item_id: 'right', edge: 'in' }]]]);
  const verdicts = {};
  for (const [name, declickSeconds] of [['off', 0], ['on', undefined]]) {
    const file = await aacRoundTrip(dir, name, mix(d, signal, 2, declickSeconds));
    verdicts[name] = judgeClicks(await cutPointClicks(file, points));
  }
  const [off] = verdicts.off.measured.cut_points, [on] = verdicts.on.measured.cut_points;
  assert.equal(verdicts.off.status, 'warn', JSON.stringify(off));
  assert.deepEqual(verdicts.off.refs, [{ time_seconds: 1, item_id: 'left' }, { time_seconds: 1, item_id: 'right' }]);
  assert.match(verdicts.off.observation, /1\.000 s \(left out, right in\)/);
  assert.ok(off.ratio > 10 * CLICK_RATIO && off.peak > 10 * CLICK_FLOOR, JSON.stringify(off));
  assert.equal(verdicts.on.status, 'pass', JSON.stringify(on));
  assert.ok(on.ratio < CLICK_RATIO / 2 && on.peak < CLICK_FLOOR, JSON.stringify(on));
  assert.equal(judgeClicks([]).status, 'not_applicable');
});

test('click QA: a cut past the end of the audio is unknown, not pass; a failed or timed-out decode is unknown', async t => {
  const dir = await tempDir('creative-clicks-short-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  // 2 s of picture, 1 s of sound.
  const file = path.join(dir, 'short-audio.mp4');
  await ffmpeg('-f', 'lavfi', '-i', 'color=black:s=64x36:r=30:d=2', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1:sample_rate=48000',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-n', file);
  const points = [0.5, 1.5].map((time, k) => ({ time, frame: time * 30, items: [{ item_id: `i${k}`, edge: 'out' }, { item_id: `i${k + 1}`, edge: 'in' }] }));
  const scored = await cutPointClicks(file, points);
  assert.equal(scored[0].click, false);
  assert.match(scored[1].unknown, /outside the decoded audio \(0–1(\.\d+)? s\)/);
  const verdict = judgeClicks(scored);
  assert.equal(verdict.status, 'unknown');
  assert.match(verdict.observation, /No click at the 1 analysed cut point\(s\), but the check is incomplete\. 1 of 2 cut point\(s\) were not checked: 1\.500 s \(i1 out, i2 in\) outside the decoded audio/);
  assert.deepEqual(verdict.measured.cut_points[1], { time_seconds: 1.5, items: points[1].items, click: null, unknown: scored[1].unknown });
  // A click elsewhere still warns.
  assert.equal(judgeClicks([{ ...scored[0], click: true }, scored[1]]).status, 'warn');
  // Decode failure and timeout: unknown with the reason (QA reports the other checks as usual).
  const missing = await clickCheck(path.join(dir, 'missing.mp4'), points);
  assert.equal(missing.status, 'unknown');
  assert.match(missing.observation, /Click analysis could not run on 2 audible cut point\(s\): Audio decode for click analysis failed/);
  const slow = await clickCheck(file, points, { timeout: 1 });
  assert.equal(slow.status, 'unknown');
  assert.match(slow.observation, /timed out/);
});

test('ebur128Summary: one parser for QA and analyze, -inf as -Infinity, missing as null', () => {
  const frame = '[Parsed_ebur128_0 @ 0x1] t: 0.1  TARGET:-23 LUFS    M:-120.7 S:-120.7     I: -70.0 LUFS       LRA:   0.0 LU';
  const summary = '[Parsed_ebur128_0 @ 0x1] Summary:\n\n  Integrated loudness:\n    I:         -16.2 LUFS\n    Threshold: -26.4 LUFS\n\n  True peak:\n    Peak:       -1.5 dBFS';
  assert.deepEqual(ebur128Summary(`${frame}\n${summary}`), { integrated_lufs: -16.2, true_peak_dbtp: -1.5 });
  assert.deepEqual(ebur128Summary(`${frame}\n${summary.replace('-16.2', '-inf').replace('-1.5', '-inf')}`), { integrated_lufs: -Infinity, true_peak_dbtp: -Infinity });
  assert.deepEqual(ebur128Summary(frame), { integrated_lufs: null, true_peak_dbtp: null }, 'frame lines alone are no summary');
});

test('click score: a continuous tone, a low tone at full scale through the declick and a tone onset after silence', () => {
  const tone = (hz, amp, phase = 0) => Float32Array.from({ length: RATE }, (_, n) => amp * Math.sin(2 * Math.PI * hz * n / RATE + phase));
  assert.equal(clickScore(tone(440, 0.5), RATE, 0, 0.5).click, false, 'no discontinuity, no click');
  // A 100 Hz full-scale tone through a 4 ms ramp to zero and back: the ramp corner
  // has a large ratio (the tone itself is very smooth) but stays under the floor.
  const ramped = tone(100, 1, Math.PI / 2).map((v, n) => v * Math.min(1, Math.abs(n - RATE / 2) / (CUT_DECLICK_SECONDS * RATE)));
  const corner = clickScore(ramped, RATE, 0, 0.5);
  assert.ok(corner.peak < CLICK_FLOOR && !corner.click, JSON.stringify(corner));
  // A hard onset into the peak of a tone after silence is a click.
  const onset = tone(440, 0.5, Math.PI / 2).map((v, n) => n < RATE / 2 ? 0 : v);
  assert.equal(clickScore(onset, RATE, 0, 0.5).click, true);
});

test('equal-power crossfade: mid-point power within 0.5 dB of either end for uncorrelated equal-level signals', () => {
  // 400 Hz and 600 Hz at the same level (uncorrelated over whole beat periods),
  // and two independent noises; crossfade 12 frames (0.4 s) at 1.0–1.4 s.
  const lcg = seed => { let s = seed; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32 - 0.5) * 1.2; };
  const noises = { a: Float32Array.from({ length: 3 * RATE }, lcg(1)), b: Float32Array.from({ length: 3 * RATE }, lcg(7)) };
  const d = doc([media('out', 'a', 0, 42, 0), media('in', 'b', 30, 42, 0, { transition_in: { kind: 'crossfade', frames: 12 } })]);
  const tones = (id, s) => 0.4 * Math.sin(2 * Math.PI * (id === 'a' ? 400 : 600) * s);
  const noise = (id, s) => noises[id][Math.round(s * RATE)];
  const measured = {};
  for (const [name, signal, half] of [['tones', tones, 0.025], ['noise', noise, 0.05]]) {
    const x = mix(d, signal, 2.4, 0);
    const before = power(x, 0.9 - half, 0.9 + half), mid = power(x, 1.2 - half, 1.2 + half), after = power(x, 1.5 - half, 1.5 + half);
    measured[name] = { mid_vs_before_db: db(mid, before), mid_vs_after_db: db(mid, after) };
    for (const value of Object.values(measured[name])) assert.ok(Math.abs(value) <= 0.5, `${name}: ${JSON.stringify(measured[name])}`);
  }
  // The lanes themselves: summed power gA² + gB² over the whole overlap.
  const index = envelopeIndex(d), [ga, gb] = d.items.map(i => gainOf(d, i, index));
  let worst = 0;
  for (let t = 1; t <= 1.4; t += 0.0005) worst = Math.max(worst, Math.abs(10 * Math.log10(ga(t) ** 2 + gb(t) ** 2)));
  assert.ok(worst < 0.05, `piecewise-linear sin/cos with ${CROSSFADE_SEGMENTS} segments deviates ${worst.toFixed(3)} dB`);
  assert.ok(Math.abs(ga(1.2) - Math.SQRT1_2) < 1e-6 && Math.abs(gb(1.2) - Math.SQRT1_2) < 1e-6);
});

test('same-asset crossfade: equal gain keeps a correlated signal level at the mid-point (equal power would rise ~3 dB)', () => {
  // Two adjacent stretches of one 400 Hz asset, source positions continuous
  // across the overlap (the same samples on both sides: fully correlated).
  const d = doc([media('out', 'a', 0, 42, 0), media('in', 'a', 30, 42, 1, { transition_in: { kind: 'crossfade', frames: 12 } })]);
  const index = envelopeIndex(d), lanes = d.items.map(i => itemEnvelope(d, i, 'audio', index));
  assert.deepEqual(lanes[0].filter(([t]) => t >= 1 && t <= 1.4), [[1, 1], [1.4, 0]], 'outgoing: linear');
  assert.deepEqual(lanes[1].slice(0, 2), [[1, 0], [1.4, 1]], 'incoming: linear');
  const x = mix(d, (id, s) => 0.4 * Math.sin(2 * Math.PI * 400 * s), 2.4, 0), half = 0.025;
  const before = power(x, 0.9 - half, 0.9 + half), mid = power(x, 1.2 - half, 1.2 + half), after = power(x, 1.5 - half, 1.5 + half);
  const measured = { mid_vs_before_db: db(mid, before), mid_vs_after_db: db(mid, after) };
  for (const value of Object.values(measured)) assert.ok(Math.abs(value) <= 0.5, JSON.stringify(measured));
  // The amplitudes sum to 1 across the whole overlap.
  const [ga, gb] = d.items.map(i => gainOf(d, i, index));
  for (let t = 1; t < 1.4; t += 0.01) assert.ok(Math.abs(ga(t) + gb(t) - 1) < 1e-6, String(t));
  // The same two stretches from different assets keep the equal-power curve.
  const other = doc([media('out', 'a', 0, 42, 0), media('in', 'b', 30, 42, 1, { transition_in: { kind: 'crossfade', frames: 12 } })]);
  const otherIndex = envelopeIndex(other);
  assert.equal(itemEnvelope(other, other.items[1], 'audio', otherIndex).length, CROSSFADE_SEGMENTS + 1 + 2, 'equal-power in, declicked out edge');
});

test('512-point lane limit counts the declick and equal-power points; edit-time validation and compilation agree', () => {
  // A ducked bed from its source origin (no in-edge declick) under k one-frame
  // speech items (4 duck points each); it ends with the last one, so that
  // interval adds 2 points: 4k points without the out-edge declick, 4k + 1 with it.
  const build = k => {
    const d = doc([...Array.from({ length: k }, (_, j) => media(`s${j}`, 'a', 1 + 3 * j, 1, 0)),
      { id: 'bed', track_id: 'm', kind: 'media', asset_id: 'b', start_frame: 0, frames: 3 * k - 1, source_in_seconds: 0, volume: 0.5 }]);
    d.tracks[1].duck = { under_track_id: 'v', depth_db: -12, attack_frames: 0, release_frames: 0 };
    return d;
  };
  const lengthOf = (d, declickSeconds) => itemEnvelope(d, d.items.at(-1), 'audio', envelopeIndex(d, { declickSeconds })).length;
  const d = build(MAX_VOLUME_POINTS / 4);
  assert.deepEqual([lengthOf(d, 0), lengthOf(d)], [MAX_VOLUME_POINTS, MAX_VOLUME_POINTS + 1], 'the out-edge declick adds one point');
  // 512 points without the declick: the lane compiles without it (no error) and says so.
  const skipped = [{ item_id: 'bed', track_id: 'm', points: MAX_VOLUME_POINTS + 1, points_without_declick: MAX_VOLUME_POINTS }];
  assert.deepEqual(checkVolumeAutomation(d), { skipped_lanes: skipped }, 'create/edit validation (project.mjs) skips the same lane');
  const compiled = compose(d);
  assert.deepEqual(compiled.declick, { skipped_lanes: skipped }, 'compilation records the skipped lane');
  const lane = JSON.parse(compiled.html.match(/id="a-bed"[^>]*data-automation="([^"]*)"/)[1].replaceAll('&quot;', '"')).lanes[0].points;
  assert.equal(lane.length, MAX_VOLUME_POINTS);
  assert.deepEqual(volumeEnvelope(d, d.items.at(-1)), itemEnvelope(d, d.items.at(-1), 'audio', envelopeIndex(d, { declickSeconds: 0 })));
  // Other lanes keep their declick.
  assert.equal(itemEnvelope(d, d.items[0], 'audio').length, 3, 'source origin in edge, declicked out edge');
  assert.deepEqual(checkVolumeAutomation(build(MAX_VOLUME_POINTS / 4 - 1)), { skipped_lanes: [] });
  assert.deepEqual(compose(build(MAX_VOLUME_POINTS / 4 - 1)).declick, { skipped_lanes: [] });
  // Over the limit even without the declick: refused by both.
  const limit = /Volume automation for item bed on track m has 516 points \(max 512\) even without the cut-edge declick/;
  assert.throws(() => checkVolumeAutomation(build(MAX_VOLUME_POINTS / 4 + 1)), limit);
  assert.throws(() => compose(build(MAX_VOLUME_POINTS / 4 + 1)), limit);
  // A crossfade contributes CROSSFADE_SEGMENTS + 1 points per side.
  const x = doc([media('p', 'a', 0, 30, 1), media('q', 'b', 24, 30, 1, { transition_in: { kind: 'crossfade', frames: 6 } })]), index = envelopeIndex(x);
  assert.deepEqual(x.items.map(i => itemEnvelope(x, i, 'audio', index).length), [2 + CROSSFADE_SEGMENTS + 1, CROSSFADE_SEGMENTS + 1 + 2]);
});

test('split join: back-to-back halves of one source get no declick at the seam, so the level does not dip', () => {
  // "one" split at 1 s: the second half continues the source exactly (2.0 = 1.0 + 30 / 30 × 1).
  const d = doc([media('one', 'a', 0, 30, 1), media('two', 'a', 30, 30, 2)]), index = envelopeIndex(d);
  assert.deepEqual(itemEnvelope(d, d.items[0], 'audio', index), [[0, 0], [0.004, 1], [1, 1]], 'declicked in edge, no ramp at the seam');
  assert.deepEqual(itemEnvelope(d, d.items[1], 'audio', index), [[1, 1], [2 - 0.004, 1], [2, 0]]);
  // Envelope of the mixed signal (a continuous 440 Hz tone, half-period windows): no dip around the seam.
  const x = mix(d, (id, s) => 0.5 * Math.sin(2 * Math.PI * 440 * s), 2), half = 1 / 880;
  const peak = (from, to) => { let p = 0; for (let n = Math.round(from * RATE); n < Math.round(to * RATE); n++) p = Math.max(p, Math.abs(x[n])); return p; };
  for (let t = 0.98; t < 1.02; t += half) assert.ok(peak(t, t + half) > 0.49, `envelope dips at ${t.toFixed(4)} s`);
  // Within one source frame (1/30 s) still continuous; speed counts.
  const near = doc([media('one', 'a', 0, 30, 1), media('two', 'a', 30, 30, 2 + 0.9 / 30)]);
  assert.equal(itemEnvelope(near, near.items[1], 'audio').length, 3);
  const fast = doc([media('one', 'a', 0, 30, 1, { speed: 2 }), media('two', 'a', 30, 30, 3, { speed: 2 })]);
  assert.equal(itemEnvelope(fast, fast.items[1], 'audio').length, 3, '3.0 = 1.0 + 30 / 30 × 2');
  // Not a split: a source jump > 1 frame, another asset, volume or speed, a gap, or a fade on one side.
  for (const [name, items] of [
    ['jump', [media('one', 'a', 0, 30, 1), media('two', 'a', 30, 30, 2 + 1.5 / 30)]],
    ['asset', [media('one', 'a', 0, 30, 1), media('two', 'b', 30, 30, 2)]],
    ['volume', [media('one', 'a', 0, 30, 1), media('two', 'a', 30, 30, 2, { volume: 0.5 })]],
    ['speed', [media('one', 'a', 0, 30, 1), media('two', 'a', 30, 30, 2, { speed: 1.5 })]],
    ['gap', [media('one', 'a', 0, 30, 1), media('two', 'a', 31, 30, 2 + 1 / 30)]],
    ['fade', [media('one', 'a', 0, 30, 1, { fade_out_frames: 3 }), media('two', 'a', 30, 30, 2)]],
  ]) {
    const other = doc(items), lane = itemEnvelope(other, other.items[1], 'audio');
    assert.deepEqual(lane.slice(0, 2).map(([, v]) => v / other.items[1].volume), [0, 1], `${name}: the in edge keeps its declick`);
  }
});

test('crossfade curve follows source continuity: equal gain over the same samples, equal power otherwise', () => {
  const incoming = (asset_id, source) => {
    const d = doc([media('out', 'a', 0, 42, 0), media('in', asset_id, 30, 42, source, { transition_in: { kind: 'crossfade', frames: 12 } })]);
    return { outgoing: itemEnvelope(d, d.items[0], 'audio').filter(([t]) => t >= 1), incoming: itemEnvelope(d, d.items[1], 'audio').slice(0, -2) };
  };
  // 1. same asset, both sides play source 1.0 s at t = 1 s (the same samples): equal gain.
  assert.deepEqual(incoming('a', 1), { outgoing: [[1, 1], [1.4, 0]], incoming: [[1, 0], [1.4, 1]] });
  // 2. same asset at another source time (5 s): uncorrelated, equal power on both sides.
  const other = incoming('a', 5);
  assert.equal(other.incoming.length, CROSSFADE_SEGMENTS + 1);
  assert.equal(other.outgoing.length, CROSSFADE_SEGMENTS + 1);
  assert.ok(Math.abs(other.incoming[CROSSFADE_SEGMENTS / 2][1] - Math.SQRT1_2) < 1e-6);
  // 3. another asset: equal power.
  assert.deepEqual(incoming('b', 1), other);
});

test('split_item itself yields a seam without declick ramps', async () => {
  const { applyOperations } = await import('../operations.mjs');
  const base = doc([media('one', 'a', 0, 60, 1)]);
  const split = await applyOperations(base, [{ type: 'split_item', item_id: 'one', at_frame: 30, new_item_id: 'two' }], { importAsset: async () => { throw new Error('no import'); }, imports: [] });
  const [left, right] = split.items, index = envelopeIndex(split);
  assert.deepEqual([left.id, right.id], ['one', 'two']);
  const seam = 1; // output seconds
  const ramps = env => env.filter(([t]) => Math.abs(t - seam) <= CUT_DECLICK_SECONDS + 1e-9).map(([, v]) => v);
  assert.ok(ramps(itemEnvelope(split, left, 'audio', index)).every(v => v === 1), 'left half keeps full gain up to the seam');
  assert.ok(ramps(itemEnvelope(split, right, 'audio', index)).every(v => v === 1), 'right half starts at full gain at the seam');
});
