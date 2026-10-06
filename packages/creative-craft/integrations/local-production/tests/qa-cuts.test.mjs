import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { captionBand, captionCutCheck, decodeWindow, judgeCutPoint, splitFrames, CAPTION_BAND } from '../burned-captions.mjs';
import { detectShots, extractFrame, frameMid, qaOptions } from '../qa.mjs';
import { run } from '../project.mjs';
import { mediaTool } from '../media-analysis.mjs';
import { DIP, fragmentCutCheck, judgeDip, judgeFragment, lumaDips } from '../cut-fragments.mjs';
import { burnedCaptionCheck, cutFragmentCheck, cutPointChecks, summarizeCutChecks } from '../cut-checks.mjs';
import { captionSource } from '../verify-smoke.mjs';

// Self-authored synthetic sources only (ffmpeg lavfi), no customer media.
const scratch = async t => {
  const dir = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'creative-qa-cuts-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  return dir;
};
const docWith = (asset, items) => ({ canvas: { width: 360, height: 640, fps: 30 }, assets: [{ id: 'src', file: asset, video: true }],
  tracks: [{ id: 'v_main', kind: 'video' }], items: items.map((item, i) => ({ id: `m${i}`, track_id: 'v_main', kind: 'media', asset_id: 'src', volume: 0, ...item })) });

test('cut-point judgement: in-point before a caption change warns, at it is aligned; out-point after one warns', () => {
  const change = [{ source_seconds: 1.5, kind: 'caption' }], frame = 1 / 30;
  // Suggestions are the changed frame's midpoint (not its start; µs precision, not 4 decimals).
  assert.deepEqual(judgeCutPoint('in', 1.3, change, { frame }), { result: 'warn', suggested_source_seconds: 1.516667, suggested_shift_seconds: 0.216667 });
  assert.equal(judgeCutPoint('in', 1.3, [{ source_seconds: 1.5, frame_mid_seconds: 1.51, kind: 'caption' }], { frame }).suggested_source_seconds, 1.51);
  assert.equal(judgeCutPoint('out', 1.7, change, { frame }).suggested_source_seconds, 1.516667);
  // An in-point a hair before the changed frame (24.4333 < 733/30) still shows frame 732: warn, suggest frame 733's midpoint.
  const real = [{ source_seconds: 24.433333, frame_mid_seconds: 24.45, kind: 'caption' }];
  assert.deepEqual(judgeCutPoint('in', 24.4333, real, { frame }), { result: 'warn', suggested_source_seconds: 24.45, suggested_shift_seconds: 0.0167 });
  assert.equal(judgeCutPoint('in', 24.45, real, { frame }).result, 'aligned', 'the midpoint shows the changed frame first');
  assert.equal(judgeCutPoint('out', 24.45, real, { frame }).result, 'aligned', 'out at the midpoint: last shown frame is 732');
  assert.equal(judgeCutPoint('out', 24.4667, real, { frame }).result, 'warn', 'out a hair after frame 733 ends shows it');
  assert.deepEqual(judgeCutPoint('in', 1.5, change, { frame }), { result: 'aligned' });
  assert.deepEqual(judgeCutPoint('in', 0.9, change, { frame }), { result: 'clear' }, 'more than 0.5 s inside the item');
  assert.equal(judgeCutPoint('out', 1.7, change, { frame }).result, 'warn');
  assert.equal(judgeCutPoint('out', 1.5, change, { frame }).result, 'aligned');
  assert.equal(judgeCutPoint('in', 1.3, [{ source_seconds: 1.5, kind: 'shot' }], { frame }).result, 'clear', 'full-frame shot changes are not caption changes');
  assert.deepEqual(captionBand(), CAPTION_BAND);
  assert.throws(() => captionBand({ top: 0.8, bottom: 0.82 }), /Caption band/);
  assert.throws(() => qaOptions({ sceneThreshold: 1.5 }), /Scene threshold/);
  assert.equal(qaOptions().production, null);
  assert.equal(qaOptions({ production: '/p/prod' }).production, '/p/prod'); // passed to the review page's sign-off command
  assert.throws(() => qaOptions({ production: '' }), /Production/);
});

test('cut-point judgement: an edge aligned on a caption change is not warned by a further change inside (short_line); a shot step on the edge is not caption alignment', () => {
  const frame = 1 / 30;
  // Real case (test in 111.683333): the in frame is a full-frame shot step, the next caption change 0.4 s later. A shot is not caption
  // alignment (a new shot can carry the old line on): warn, marked edge_on_shot_change.
  const opening = [{ source_seconds: 111.666667, kind: 'shot' }, { source_seconds: 112.066667, frame_mid_seconds: 112.083333, kind: 'caption' }];
  const onShot = judgeCutPoint('in', 111.683333, opening, { frame });
  assert.deepEqual(onShot, { result: 'warn', suggested_source_seconds: 112.083333, suggested_shift_seconds: 0.4, edge_on_shot_change: true });
  assert.equal(judgeCutPoint('in', 111.683333, [opening[0]], { frame }).result, 'clear', 'a shot step alone is not caption alignment');
  // The same in-point on a caption change: aligned, the next change recorded as short_line.
  assert.deepEqual(judgeCutPoint('in', 111.683333, [{ ...opening[0], kind: 'caption' }, opening[1]], { frame }),
    { result: 'aligned', short_line: { source_seconds: 112.066667, frame_mid_seconds: 112.083333, shown_seconds: 0.4 } });
  // Real case (hook out 60.116667): the first frame not shown is the change at 60.1; the switch to the spoken line at 59.633 stays.
  const closing = [{ source_seconds: 59.633333, frame_mid_seconds: 59.65, kind: 'caption' }, { source_seconds: 60.1, frame_mid_seconds: 60.116667, kind: 'caption' }];
  assert.deepEqual(judgeCutPoint('out', 60.116667, closing, { frame }),
    { result: 'aligned', short_line: { source_seconds: 59.633333, frame_mid_seconds: 59.65, shown_seconds: 0.466667 } });
  // Not on a change frame: still a warning (out one frame later shows frame 60.1 → the next line flashes).
  assert.equal(judgeCutPoint('out', 60.15, closing, { frame }).result, 'warn');
  assert.equal(judgeCutPoint('in', 111.65, opening, { frame }).result, 'warn');
  // The observation counts the short lines without warning.
  const texts = captionCutCheck().summary(2);
  const entry = (edge, source, judged) => ({ item_id: 'hook', edge, source_seconds: source, output_seconds: 0, ...judged });
  const summary = summarizeCutChecks([entry('out', 60.116667, judgeCutPoint('out', 60.116667, closing, { frame })), entry('in', 1, { result: 'clear' })], texts);
  assert.equal(summary.status, 'pass');
  assert.match(summary.observation, /1 aligned cut point\(s\) have another caption change within 0\.5 s inside \(not warned.*hook out-point at source 60\.116667 s, change at 59\.633333 s, edge line 0\.466667 s/);
  const warned = summarizeCutChecks([entry('in', 111.683333, onShot)], texts);
  assert.equal(warned.status, 'warn');
  assert.match(warned.observation, /1 warned cut point\(s\) sit on a source shot change \(hook in\): the new line may simply start with the shot cut; check by eye\./);
});

test('burned-in caption check: caption switching after the in-point warns with the change time; aligned cut and caption-free source pass', { timeout: 60000 }, async t => {
  const dir = await scratch(t);
  await captionSource(path.join(dir, 'caption.mp4'), { changeAt: 1.5 });
  await captionSource(path.join(dir, 'plain.mp4'), {});
  const late = await burnedCaptionCheck(docWith('caption.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: 1.3 }]), dir);
  assert.equal(late.status, 'warn', late.observation);
  const point = late.measured.points.find(p => p.edge === 'in');
  assert.equal(point.result, 'warn');
  assert.ok(Math.abs(point.suggested_source_seconds - 45.5 / 30) < 1e-3, `midpoint of the first changed frame (45): ${JSON.stringify(point)}`);
  assert.deepEqual(late.refs, [{ time_seconds: 0, item_id: 'm0' }]);
  assert.match(late.measured.method, /not OCR/);
  assert.match(late.observation, /m0 in-point at source 1\.300000 s → 1\.516667 s/, 'times in the text: 6 decimals, the suggestion a frame midpoint');
  // Out-point 1.3 + 1 s = 2.3 s: the change at 1.5 s is 0.8 s before it (outside the window).
  assert.equal(late.measured.points.find(p => p.edge === 'out').result, 'clear');
  const aligned = await burnedCaptionCheck(docWith('caption.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: 1.5 }]), dir);
  assert.equal(aligned.status, 'pass', aligned.observation);
  assert.equal(aligned.measured.points.find(p => p.edge === 'in').result, 'aligned');
  const flash = await burnedCaptionCheck(docWith('caption.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: 0.7 }]), dir);
  assert.equal(flash.measured.points.find(p => p.edge === 'out').result, 'warn', 'next line flashes before the out-point 1.7 s');
  const plain = await burnedCaptionCheck(docWith('plain.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: 1.3 }]), dir);
  assert.equal(plain.status, 'pass', plain.observation);
  // A band that misses the caption row sees nothing.
  const elsewhere = await burnedCaptionCheck(docWith('caption.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: 1.3 }]), dir, { band: { top: 0.1, bottom: 0.3 } });
  assert.equal(elsewhere.status, 'pass');
});

test('shot detection finds a 0.6 s shot inside one file', { timeout: 60000 }, async t => {
  const dir = await scratch(t), file = path.join(dir, 'short.mp4');
  await captionSource(file, { duration: 4, shortShot: [2, 2.6] });
  const shots = await detectShots(file, 4);
  assert.equal(shots.length, 3, JSON.stringify(shots));
  assert.ok(Math.abs(shots[1].start - 2) < 0.04 && Math.abs(shots[1].end - 2.6) < 0.04, JSON.stringify(shots));
  assert.equal((await detectShots(file, 4, 0.99)).length, 1, 'threshold is configurable');
});

test('variable frame rate source: every decoded frame keeps its own source time', { timeout: 60000 }, async t => {
  const dir = await scratch(t), file = path.join(dir, 'vfr.mp4');
  // 30 fps until 1 s, then 15 fps; the caption switches at 3.0 s inside the 15 fps part.
  await captionSource(file, { duration: 3, changeAt: 3, slowFrom: 1 });
  const window = await decodeWindow(file, 2.5, 3.6);
  assert.equal(window.frames.length, window.times.length);
  assert.ok(window.frames.length >= 8, `frames ${window.frames.length}`);
  const gaps = window.times.slice(1).map((time, i) => Math.round((time - window.times[i]) * 1000));
  assert.ok(gaps.every(g => g === 67), `15 fps part decodes one frame per 1/15 s: ${gaps}`);
  const late = await burnedCaptionCheck(docWith('vfr.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: 2.8 }]), dir);
  const point = late.measured.points.find(p => p.edge === 'in');
  assert.equal(point.result, 'warn', JSON.stringify(point));
  assert.ok(Math.abs(point.suggested_source_seconds - (3 + 1 / 30)) < 1e-3, `midpoint of the 1/15 s frame at 3.0 s: ${JSON.stringify(point)}`);
  const aligned = await burnedCaptionCheck(docWith('vfr.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: 3 }]), dir);
  assert.equal(aligned.measured.points.find(p => p.edge === 'in').result, 'aligned', aligned.observation);
});

test('frame/time count mismatch is refused instead of truncated', () => {
  const log = '[Parsed_showinfo_2 @ 0x1] n:0 pts:2 pts_time:1.0 s:4x2\n[Parsed_showinfo_2 @ 0x1] n:1 pts:3 pts_time:1.5\n', frame = 8, timing = { start: 0.5, time_base: { num: 1, den: 2 } };
  assert.deepEqual(splitFrames(Buffer.alloc(2 * frame), log, timing).times, [0.5, 1]);
  assert.throws(() => splitFrames(Buffer.alloc(3 * frame), log, timing), /decoded 3 frame\(s\) but showinfo reported 2/);
  assert.throws(() => splitFrames(Buffer.alloc(frame + 3), log, timing), /not trustworthy/);
});

test('frame times are integer pts × the ffprobe time base, never the printed pts_time', async t => {
  // pts_time text is deliberately wrong: only pts and the time base count.
  const tagged = lines => lines.map(line => `[Parsed_showinfo_1 @ 0x1] ${line}`).join('\n');
  const log = tagged(['config in time_base: 1/30000, frame_rate: 30000/1001', 'n:   0 pts:  733733 pts_time:24.4578 s:4x2', 'n:   1 pts:  734734 pts_time:24.49']);
  const timing = { start: 0, time_base: { num: 1, den: 30000 } };
  assert.deepEqual(splitFrames(Buffer.alloc(16), log, timing).times, [733733 / 30000, 734734 / 30000]);
  assert.throws(() => splitFrames(Buffer.alloc(16), log, { start: 0, time_base: { num: 1, den: 15360 } }), /showinfo time base 1\/30000 differs from the stream time base 1\/15360/);
  assert.throws(() => splitFrames(Buffer.alloc(16), log.replace('pts:  734734', 'pts:NOPTS'), timing), /frame line has no integer pts/);
  assert.throws(() => splitFrames(Buffer.alloc(16), log.replace(' s:4x2', ''), timing), /no frame size/);
  assert.throws(() => splitFrames(Buffer.alloc(16), log), /needs the stream time_base/);
  // Real decode of a 30000/1001 fps file: every time is exactly k × 1001/30000.
  const dir = await scratch(t), file = path.join(dir, 'ntsc.mp4');
  await run(mediaTool('ffmpeg'), ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'testsrc2=size=64x64:rate=30000/1001:duration=2', '-c:v', 'libx264', '-video_track_timescale', '30000', file]);
  const window = await decodeWindow(file, 0.5, 1);
  assert.ok(window.times.length >= 10, `frames ${window.times.length}`);
  assert.ok(window.times.every(time => Number.isInteger(Math.round(time * 30000)) && Math.abs(time * 30000 / 1001 - Math.round(time * 30000 / 1001)) < 1e-9), JSON.stringify(window.times));
});

test('an in-point even 1e-7 s before a frame start shows the previous frame (no tolerance toward later frames)', () => {
  const frame = 1 / 30, change = [{ source_seconds: 1.5, kind: 'caption' }];
  assert.equal(judgeCutPoint('in', 1.5 - 1e-7, change, { frame }).result, 'warn', 'frame 44 is shown first; the caption changes one frame later');
  assert.equal(judgeCutPoint('in', 1.5, change, { frame }).result, 'aligned');
  assert.equal(judgeCutPoint('out', 1.5 + frame + 1e-7, change, { frame }).result, 'warn', 'out-point 1e-7 s after frame 45 + 1 frame still shows frame 45');
  assert.equal(judgeCutPoint('out', 1.5 + frame, change, { frame }).result, 'warn', 'last shown frame is 45, the changed one');
  assert.equal(judgeCutPoint('out', 1.5, change, { frame }).result, 'aligned');
  const times = Array.from({ length: 120 }, (_, k) => k / 30);
  const fragment = judgeFragment('in', { times, changes: [30], at: 1 - 1e-7, step: frame, frame, first: 1 - 1e-7, last: 2.9, itemFrames: 58 });
  assert.equal(fragment.result, 'warn', JSON.stringify(fragment));
  assert.equal(judgeFragment('in', { times, changes: [30], at: 1, step: frame, frame, first: 1, last: 2.9, itemFrames: 58 }).result, 'aligned');
});

test('summary: any warn wins, otherwise any unchecked point makes the check unknown', { timeout: 60000 }, async t => {
  const dir = await scratch(t);
  await captionSource(path.join(dir, 'caption.mp4'), { changeAt: 1.5 });
  // m0 reads caption.mp4; m1's asset file does not exist, so both its points are unchecked.
  const doc = sourceIn => {
    const d = docWith('caption.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: sourceIn }, { start_frame: 30, frames: 30, source_in_seconds: 0 }]);
    d.assets.push({ id: 'gone', file: 'missing.mp4', video: true });
    d.items[1].asset_id = 'gone';
    return d;
  };
  const mixed = await burnedCaptionCheck(doc(1.3), dir);
  assert.equal(mixed.status, 'warn', mixed.observation);
  assert.match(mixed.observation, /2 of 4 cut point\(s\) were not checked \(m1 in, m1 out\)/);
  const partial = await burnedCaptionCheck(doc(1.5), dir);
  assert.equal(partial.status, 'unknown', partial.observation);
  assert.match(partial.observation, /2 analysed point\(s\).*incomplete\. 2 of 4 cut point\(s\) were not checked/);
  assert.deepEqual(partial.measured.points.map(p => p.result), ['aligned', 'clear', 'unknown', 'unknown']);
});

// Synthetic CFR file: red frames 0–44, blue from frame 45 on (a cut at frame 45).
const colourCut = async (file, { cutFrame = 45, seconds = 3, fps = 30 } = {}) => run(mediaTool('ffmpeg'), ['-v', 'error', '-n', '-f', 'lavfi', '-i',
  `color=c=red:s=64x64:r=${fps}:d=${seconds},drawbox=x=0:y=0:w=64:h=64:color=blue:t=fill:enable='gte(n,${cutFrame})'`, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', file]);
const pixel = async png => {
  const { stdout } = await run(mediaTool('ffmpeg'), ['-v', 'error', '-i', png, '-vf', 'scale=1:1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], { encoding: 'buffer' });
  return stdout[0] > stdout[2] ? 'red' : 'blue';
};

test('QA samples are frame-exact: last frame before a cut and first frame after it', { timeout: 60000 }, async t => {
  const dir = await scratch(t), file = path.join(dir, 'cut.mp4');
  await colourCut(file);
  const colours = {};
  for (const frame of [0, 43, 44, 45, 46, 89]) {
    const png = path.join(dir, `f${frame}.png`);
    await extractFrame(file, frame, 30, png);
    colours[frame] = await pixel(png);
  }
  assert.deepEqual(colours, { 0: 'red', 43: 'red', 44: 'red', 45: 'blue', 46: 'blue', 89: 'blue' });
  assert.equal(frameMid(45, 30), 45.5 / 30);
});

// Synthetic source (30 fps, 5 s): moving test pattern, colour bars from 1.5 s
// (frame 45) to 3.0 s, a 2-frame white flash on frames 90–91, then the test
// pattern again from frame 92.
const shotsSource = file => run(mediaTool('ffmpeg'), ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'testsrc2=size=360x640:rate=30:duration=5',
  '-f', 'lavfi', '-i', 'smptehdbars=size=360x640:rate=30:duration=5', '-filter_complex',
  "[0:v][1:v]overlay=enable='between(n,45,89)',drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='between(n,90,91)'[v]",
  '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', file]);

test('cut-boundary fragments: judgement rules', () => {
  const frame = 1 / 30, times = Array.from({ length: 120 }, (_, k) => k / 30), base = { times, step: frame, frame };
  // Shot changes at frames 30, 50 (a 0.67 s shot), 75 and 100 (a 0.83 s shot).
  const changes = [30, 50, 75, 100];
  const at = (edge, source, first, last) => judgeFragment(edge, { ...base, changes, at: source, first, last, itemFrames: Math.round((last - first) / frame) + 1 });
  assert.deepEqual(at('in', 0.8, 0.8, 2.766667), { result: 'warn', kind: 'fragment', fragment_frames: 6, source_frames: 6, change_seconds: 1, change_mid_seconds: 1.016667,
    suggested_source_in_seconds: 1.016667, suggested_shift_seconds: 0.216667 }, 'opens with 6 frames of the previous shot');
  assert.equal(at('in', 0.99999, 0.99999, 2.98).fragment_frames, 1, 'a hair before frame 30 (1.0 s) still shows frame 29');
  assert.equal(at('in', 1.016667, 1.016667, 2.98).result, 'aligned', 'midpoint of the first frame of the shot');
  assert.equal(at('in', 1.1, 1.1, 3).result, 'clear', 'the 0.67 s shot is shown from frame 33 on: mostly inside the item');
  // Out-point 1.7 s (last shown frame 50, the first of the new shot): ends with 1 frame of the next shot.
  assert.deepEqual(at('out', 1.7, 0, 1.666667), { result: 'warn', kind: 'fragment', fragment_frames: 1, source_frames: 1, change_seconds: 1.666667, change_mid_seconds: 1.683333,
    suggested_source_out_seconds: 1.683333, suggested_frames: 50, drop_output_frames: 1 });
  assert.equal(at('out', 1.6666667, 0, 1.633333).result, 'aligned', 'the change is the first frame after the cut');
  assert.equal(at('out', 3.3, 1.6, 3.266667).result, 'clear', 'the 0.83 s shot 75–99 cut 1 frame early is mostly shown, not a fragment');
});

test('cut-boundary fragments: a short shot shown whole on the cut side is aligned, a partly shown one is a flash', () => {
  const frame = 1 / 30, times = Array.from({ length: 120 }, (_, k) => k / 30);
  // A 0.33 s shot on frames 30–39 between two long shots.
  const judge = (edge, at, first, frames) => judgeFragment(edge, { times, changes: [30, 40], at, step: frame, frame, first, last: first + (frames - 1) * frame, itemFrames: frames });
  const fromFirst = judge('in', 1, 1, 40);
  assert.deepEqual([fromFirst.result, fromFirst.change_seconds], ['aligned', 1.333333], 'in-point on the short shot\'s first frame: nothing of it lies before the cut');
  const late = judge('in', 1.05, 1.05, 40);
  assert.deepEqual([late.result, late.kind, late.fragment_frames, late.source_frames], ['warn', 'flash', 9, 9], 'frame 30 lies before the cut: the rest is a flash');
  const toLast = judge('out', 40 / 30, 0.5, 25);
  assert.deepEqual([toLast.result, toLast.change_seconds], ['aligned', 1], 'out-point right after the short shot\'s last frame (frame 40 starts the next shot)');
  const early = judge('out', 1.3, 0.5, 24);
  assert.deepEqual([early.result, early.kind, early.fragment_frames, early.suggested_frames], ['warn', 'flash', 9, 15], 'frame 39 lies after the cut: the shown part is a flash');
});

test('cut-boundary fragments count output frames through speed and source vs canvas frame rate', () => {
  // 60 fps source, item at speed 2 on a 30 fps canvas: one output frame steps 4 source frames.
  const frame = 1 / 60, step = 2 / 30, times = Array.from({ length: 180 }, (_, k) => k / 60);
  const judged = judgeFragment('in', { times, changes: [60], at: 0.8, step, frame, first: 0.8, last: 0.8 + 29 * step, itemFrames: 30 });
  assert.deepEqual([judged.result, judged.fragment_frames, judged.source_frames], ['warn', 3, 12], '12 source frames before 1.0 s fill output frames 0–2');
  assert.equal(judged.suggested_source_in_seconds, 1.008333);
  // Out: item from 0.2 s, 13 output frames (source 0.2 … 1.0); the last output frame shows frame 60, the next shot.
  const out = judgeFragment('out', { times, changes: [60], at: 0.2 + 13 * step, step, frame, first: 0.2, last: 0.2 + 12 * step, itemFrames: 13 });
  assert.deepEqual([out.result, out.fragment_frames, out.source_frames, out.suggested_frames, out.drop_output_frames], ['warn', 1, 1, 12, 1], 'the one shown source frame of the next shot is frame 60');
});

test('cut-boundary fragments on a synthetic source: shot tail, flash and next-shot head warn; aligned cuts pass', { timeout: 60000 }, async t => {
  const dir = await scratch(t);
  await shotsSource(path.join(dir, 'shots.mp4'));
  const items = [
    { start_frame: 0, frames: 30, source_in_seconds: 1.3 }, // m0: opens with 6 frames of the test pattern
    { start_frame: 30, frames: 30, source_in_seconds: 1.5 }, // m1: in-point on the bars' first frame
    { start_frame: 60, frames: 30, source_in_seconds: 2.95 }, // m2: 2 bars frames + the 2-frame white flash
    { start_frame: 90, frames: 40, source_in_seconds: 0.2 }, // m3: ends with 1 frame of the bars
    { start_frame: 130, frames: 30, source_in_seconds: 0.5 }, // m4: ends exactly before the bars
  ];
  const result = await cutFragmentCheck(docWith('shots.mp4', items), dir);
  const point = (id, edge) => result.measured.points.find(p => p.item_id === id && p.edge === edge);
  assert.equal(result.status, 'warn', result.observation);
  assert.deepEqual(result.measured.points.filter(p => p.result === 'warn').map(p => `${p.item_id}:${p.edge}`), ['m0:in', 'm2:in', 'm2:out', 'm3:out'], result.observation);
  assert.equal(point('m0', 'in').fragment_frames, 6);
  assert.ok(Math.abs(point('m0', 'in').suggested_source_in_seconds - 45.5 / 30) < 1e-3, JSON.stringify(point('m0', 'in')));
  assert.equal(point('m1', 'in').result, 'aligned');
  assert.equal(point('m2', 'in').kind, 'flash');
  assert.equal(point('m2', 'in').fragment_frames, 4, 'two bars frames and the two-frame flash');
  assert.ok(Math.abs(point('m2', 'in').suggested_source_in_seconds - 92.5 / 30) < 1e-3, JSON.stringify(point('m2', 'in')));
  assert.equal(point('m3', 'out').fragment_frames, 1);
  assert.equal(point('m3', 'out').suggested_frames, 39);
  assert.equal(point('m4', 'out').result, 'aligned');
  // m2 also ends with the flash and 0.88 s of the following shot: keep only its 2 bars frames.
  assert.deepEqual([point('m2', 'out').kind, point('m2', 'out').suggested_frames], ['flash', 2]);
  assert.deepEqual(result.refs.map(r => r.item_id), ['m0', 'm2', 'm2', 'm3']);
  assert.deepEqual([result.measured.thresholds.shot_mad, result.measured.thresholds.scene_jump], [30, 30]);
  assert.match(result.observation, /m0 in-point opens with 6 output frame\(s\) \(6 source frame\(s\)\) of the previous source shot: source in 1.300000 s → 1.516667 s/);
});

test('both cut-point checks share one decode per cut point and match the checks run alone', { timeout: 60000 }, async t => {
  const dir = await scratch(t);
  await captionSource(path.join(dir, 'caption.mp4'), { changeAt: 1.5, duration: 4 });
  const doc = docWith('caption.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: 1.3 }, { start_frame: 30, frames: 30, source_in_seconds: 2.2 }]);
  const calls = [];
  const decode = (...args) => { calls.push(args.slice(0, 3)); return decodeWindow(...args); };
  const shared = await cutPointChecks(doc, dir, { decode });
  assert.equal(calls.length, 4, 'one decode for each of the 4 cut points');
  // The shared range is the union of both checks' ranges (fragments need about ±1 s, captions 0.5 s).
  assert.ok(calls.every(([, from, to]) => to - from > 2), JSON.stringify(calls));
  const alone = [await burnedCaptionCheck(doc, dir), await cutFragmentCheck(doc, dir)];
  assert.deepEqual([shared.burned, shared.fragments], alone);
  assert.equal(shared.burned.status, 'warn', shared.burned.observation);
});

test('judgements base the suggested shift on the written value, so written + shift is the suggestion', () => {
  const frame = 1 / 30, change = [{ source_seconds: 1.5, kind: 'caption' }];
  // Plays 1.3001 (compiled), written 1.2999.
  assert.deepEqual(judgeCutPoint('in', 1.3001, change, { frame, written: 1.2999 }), { result: 'warn', suggested_source_seconds: 1.516667, suggested_shift_seconds: 0.216767 });
  const times = Array.from({ length: 120 }, (_, k) => k / 30);
  const judged = judgeFragment('in', { times, changes: [30], at: 0.8001, written: 0.7999, step: frame, frame, first: 0.8001, last: 1.8, itemFrames: 30 });
  assert.deepEqual([judged.suggested_source_in_seconds, judged.suggested_shift_seconds], [1.016667, 0.216767]);
});

test('a corrected in-point is reported and suggested in the document\'s terms', { timeout: 60000 }, async t => {
  const dir = await scratch(t);
  await shotsSource(path.join(dir, 'shots.mp4'));
  await captionSource(path.join(dir, 'caption.mp4'), { changeAt: 1.5, duration: 4 });
  // 1.2999 is 0.1 ms below frame 39 (1.3 s): compiled to 1.3001, which still opens
  // with 6 frames before the change at frame 45.
  const withRate = file => {
    const doc = docWith(file, [{ start_frame: 0, frames: 30, source_in_seconds: 1.2999 }]);
    Object.assign(doc.assets[0], { frame_rate: '30/1', duration: 4 });
    return doc;
  };
  const fragments = await cutFragmentCheck(withRate('shots.mp4'), dir);
  const inPoint = fragments.measured.points.find(p => p.edge === 'in');
  assert.deepEqual([inPoint.source_seconds, inPoint.compiled_source_seconds, inPoint.source_frame, inPoint.result, inPoint.fragment_frames],
    [1.2999, 1.3001, 39, 'warn', 6], JSON.stringify(inPoint));
  assert.ok(Math.abs(inPoint.suggested_source_in_seconds - 45.5 / 30) < 1e-3);
  assert.equal(Math.round((inPoint.source_seconds + inPoint.suggested_shift_seconds) * 1e6) / 1e6, inPoint.suggested_source_in_seconds, 'written + shift = suggestion');
  assert.match(fragments.observation, /source in 1\.299900 s \(compiled 1\.300100 s\) → 1\.516667 s/);
  const outPoint = fragments.measured.points.find(p => p.edge === 'out');
  assert.deepEqual([outPoint.source_seconds, outPoint.compiled_source_seconds], [2.2999, 2.3001]);
  assert.ok(!('document_source_seconds' in inPoint), 'the document value is source_seconds');
  const burned = await burnedCaptionCheck(withRate('caption.mp4'), dir);
  const captionIn = burned.measured.points.find(p => p.edge === 'in');
  assert.deepEqual([captionIn.source_seconds, captionIn.compiled_source_seconds, captionIn.result], [1.2999, 1.3001, 'warn'], JSON.stringify(captionIn));
  assert.equal(Math.round((captionIn.source_seconds + captionIn.suggested_shift_seconds) * 1e6) / 1e6, captionIn.suggested_source_seconds, 'written + shift = suggestion');
  assert.match(burned.observation, /m0 in-point at source 1\.299900 s \(compiled 1\.300100 s\) → 1\.516667 s/);
  // Uncorrected: no compiled field, the observation as before.
  const plain = await burnedCaptionCheck(docWith('caption.mp4', [{ start_frame: 0, frames: 30, source_in_seconds: 1.3 }]), dir);
  assert.ok(plain.measured.points.every(p => !('compiled_source_seconds' in p)));
});

test('cut-check summary: warn wins, then unknown with the unchecked points, else pass', () => {
  const texts = { scope: '3 source cut point(s)', finding: 'thing', describe: e => `${e.item_id} ${e.edge}`, pass: 'all clear',
    warned: (count, details, unchecked) => `${count} warned: ${details}.${unchecked}` };
  const point = (item_id, edge, result, extra = {}) => ({ item_id, edge, result, output_seconds: 1, ...extra });
  const warn = summarizeCutChecks([point('a', 'in', 'warn'), point('b', 'out', 'unknown', { error: 'boom' }), point('c', 'in', 'clear')], { ...texts, sampleAt: () => 's-1' });
  assert.deepEqual(warn, { status: 'warn', observation: '1 warned: a in. 1 of 3 cut point(s) were not checked (b out): boom.', refs: [{ time_seconds: 1, item_id: 'a', sample_id: 's-1' }] });
  const unknown = summarizeCutChecks([point('b', 'out', 'unknown', { error: 'boom' }), point('c', 'in', 'aligned')], texts);
  assert.equal(unknown.status, 'unknown');
  assert.match(unknown.observation, /^No thing found at the 1 analysed point\(s\) of 3 source cut point\(s\), but the check is incomplete\. 1 of 2/);
  assert.deepEqual(summarizeCutChecks([point('c', 'in', 'clear')], texts), { status: 'pass', observation: 'all clear' });
});

test('lumaDips: a short dip to black and back (also with a held, noisy black); not a darker next shot, a shallow or a long dip, or one cut by the window edge', () => {
  const times = Array.from({ length: 120 }, (_, k) => k / 30);
  const series = shape => times.map((_, k) => shape(k));
  const fade = (k, a, b, top = 120, bottom = 3, after = 110) => k < a ? top : k <= b ? bottom : after;
  // Real shape: 119.6 → 96.7 → 73 → 49.2 → 24.7 → 3 → 22.6 → 44.4 → 66.4 → 88.2 → 109.6.
  const real = [119.6, 96.7, 73.0, 49.2, 24.7, 3.0, 22.6, 44.4, 66.4, 88.2, 109.6];
  const mean = series(k => k < 50 ? 119.6 + (k % 2) * 0.3 : k < 61 ? real[k - 50] : 109.6 - (k % 2) * 0.2);
  assert.deepEqual(lumaDips(mean, times), [{ start: 51, min: 55, end: 60, end_seconds: 2, ref: 109.6, min_luma: 3 }]);
  // Held black with noise at the bottom: one dip, darkest frame first.
  const held = series(k => k < 40 ? 120 : k < 44 ? 120 - (k - 39) * 25 : k < 52 ? 4 + (k % 3) * 0.5 : k < 56 ? 4 + (k - 51) * 26 : 108);
  assert.deepEqual(lumaDips(held, times).map(d => [d.start, d.end]), [[40, 55]]);
  assert.deepEqual(lumaDips(series(k => fade(k, 40, 200)), times), [], 'a darker next shot does not recover');
  assert.deepEqual(lumaDips(series(k => k < 40 ? 120 : k < 45 ? 85 : 120), times), [], '35 levels: too shallow');
  assert.deepEqual(lumaDips(series(k => k < 40 ? 120 : k < 44 ? 120 - (k - 39) * 25 : k < 95 ? 10 : 110), times), [], 'longer than max_seconds: a black segment, not a dip');
  assert.deepEqual(lumaDips(mean.slice(53), times.slice(53)), [], 'the window starts inside the dip');
  // At the file's own edges a dark run is open on that side and judged against the other: an opening fade-up, a closing fade-out.
  const fadeUp = series(k => k < 3 ? 2 : k < 8 ? 2 + (k - 2) * 22 : 112);
  assert.deepEqual(lumaDips(fadeUp, times), [], 'window edge that is not the file start: not judged');
  assert.deepEqual(lumaDips(fadeUp, times, DIP, { fileStart: true }), [{ start: 0, min: 2, end: 7, end_seconds: 7 / 30, ref: 112, min_luma: 2 }]);
  const fadeOut = series(k => k < 112 ? 115 : 115 - (k - 111) * 14);
  assert.deepEqual(lumaDips(fadeOut, times, DIP, { fileEnd: true }).map(d => [d.start, d.min, d.end, d.end_seconds, d.ref]), [[112, 119, 120, 4, 115]]);
  assert.deepEqual(lumaDips(fadeOut, times), []);
  assert.deepEqual(lumaDips(series(() => 3), times, DIP, { fileStart: true, fileEnd: true }), [], 'dark throughout: no settled level');
  assert.deepEqual(lumaDips(series(k => k < 90 ? 82 : 41), times, DIP, { fileEnd: true }), [], 'a hard cut to a darker last shot is not a fade-out (open side: ≤ open_ratio)');
  // A bright first frame before a dip from frame 1: frame 0 is the settled level (not part of the dip).
  assert.deepEqual(lumaDips(series(k => k === 0 ? 118 : k < 4 ? 118 - k * 38 : k < 9 ? 4 + (k - 3) * 22 : 114), times, DIP, { fileStart: true }).map(d => [d.start, d.end, d.ref]), [[1, 8, 114]]);
  // An out-point inside an opening fade-up: ending before the dip would end before the item starts, so no suggestion.
  const openDips = lumaDips(fadeUp, times, DIP, { fileStart: true });
  const closing = judgeDip('out', { times, dips: openDips, at: 5.5 / 30, step: 1 / 30, frame: 1 / 30, first: 1.5 / 30, itemFrames: 4 });
  assert.deepEqual([closing.output_frames, closing.suggested_source_seconds], [4, null]);
  assert.equal(DIP.max_seconds, 1.5);
  // Edges in the dip [51, 60): in-point on frame 53 opens with frames 53–59 (7 output frames); out-point after frame 51 ends with 1.
  const dips = lumaDips(mean, times), frame = 1 / 30, at = k => (k + 0.5) / 30;
  assert.deepEqual(judgeDip('in', { times, dips, at: at(53), step: frame, frame, first: at(53), itemFrames: 30 }),
    { start_seconds: 1.7, min_seconds: 1.833333, end_seconds: 2, ref_luma: 109.6, min_luma: 3, output_frames: 7, suggested_source_seconds: 2.016667 });
  assert.equal(judgeDip('in', { times, dips, at: at(60), step: frame, frame, first: at(60), itemFrames: 30 }), null, 'first recovered frame: clear');
  assert.equal(judgeDip('out', { times, dips, at: at(52), step: frame, frame, first: at(30), itemFrames: 22 }).output_frames, 1);
  assert.equal(judgeDip('out', { times, dips, at: at(51), step: frame, frame, first: at(30), itemFrames: 21 }), null, 'last shown frame 50 is before the dip');
});

test('cut-boundary-fragments: an in-point inside a source dip to black warns with the output time and fading frames', () => {
  const real = [119.6, 96.7, 73.0, 49.2, 24.7, 3.0, 22.6, 44.4, 66.4, 88.2, 109.6];
  const level = k => k < 50 ? 119.6 : k < 61 ? real[k - 50] : 109.6;
  const check = fragmentCutCheck(), item = { id: 'wear', source_in_seconds: (53 + 0.5) / 30, frames: 60 };
  const point = { item, edge: 'in', source_seconds: item.source_in_seconds };
  const [from, to] = check.range(point);
  const ks = Array.from({ length: 200 }, (_, k) => k).filter(k => k / 30 >= from && k / 30 < to);
  const window = { frames: ks.map(k => new Uint8Array(64).fill(Math.round(level(k)))), times: ks.map(k => k / 30), width: 8, height: 8 };
  const judged = check.analyse(point, window, 30, [from, to]);
  assert.equal(judged.result, 'warn');
  assert.equal(judged.kind, 'dip');
  assert.deepEqual([judged.dip.output_frames, judged.dip.output_duration_seconds, judged.dip.suggested_source_seconds], [7, 0.233333, 2.016667]);
  const texts = check.summary(1), summary = summarizeCutChecks([{ item_id: 'wear', edge: 'in', source_seconds: item.source_in_seconds, output_seconds: 10.333333, ...judged }], texts);
  assert.equal(summary.status, 'warn');
  assert.match(summary.observation, /wear in-point at output 10\.333 s opens fading up from a source dip to black for 7 output frame\(s\) \(0\.233333 s\).*start at 2\.016667 s/);
});
