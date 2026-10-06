// Explicit opt-in: real producer + Chrome (PRODUCER_HEADLESS_SHELL_PATH).
// Media time 0 is the earliest stream start, for the renderer as for QA; the
// import records frame_rate only when that is the video start. A fixture that
// cannot be built as intended fails the test (with the probed starts); nothing
// is skipped.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { createProject, ffprobeJson } from '../project.mjs';
import { renderProject } from '../render.mjs';
import { streamStart } from '../source-frames.mjs';
import { ffmpeg, frameColour, synthRedThenBlue, tempDir } from './media-fixtures.mjs';

// Exact starts per stream type, in seconds (null when unusable).
const starts = async file => Object.fromEntries((await ffprobeJson(file)).streams.map(s => [s.codec_type, streamStart(s)?.seconds ?? null]));
const exact = async file => (await ffprobeJson(file)).streams.map(s => { const start = streamStart(s); return start && `${start.p}/${start.q}`; });

async function firstFrame(dir, name, file, sourceIn) {
  const root = path.join(dir, `${name}-project`), output = path.join(dir, `${name}-render`);
  const doc = await createProject(root, { project_id: name, title: name, canvas: { width: 320, height: 180, fps: 30 }, assets: [{ id: 'src', path: file }],
    tracks: [{ id: 'v', kind: 'video', locked: false }],
    items: [{ id: 'one', track_id: 'v', kind: 'media', asset_id: 'src', start_frame: 0, frames: 10, source_in_seconds: sourceIn, volume: 0.5, fit: 'cover' }] });
  const receipt = await renderProject(root, output, { preview: true });
  assert.equal(receipt.status, 'completed');
  const html = await fs.readFile(path.join(output, 'index.html'), 'utf8');
  return { asset: doc.assets[0], receipt, mediaStart: Number(/<video[^>]*data-media-start="([^"]+)"/.exec(html)[1]),
    colour: await frameColour(path.join(output, 'video.mp4'), 0) };
}

// A source whose streams all start at 0.5 s, red frames 0–21, blue from frame
// 22 (22/30 = 0.7333… s): frame_rate is recorded and the truncated in-point
// 0.7333 is corrected to frame 22 (+0.1 ms), the first blue frame, 0.5 s into
// the file; frame 21 (in-point 0.72) is still red.
async function assertShiftedStartCorrected(dir, name, file) {
  const probed = await starts(file);
  assert.ok(Object.values(probed).every(s => s === 0.5) && (await exact(file)).every(Boolean),
    `fixture ${name}: every stream must start at 0.5 s, ffprobe reports ${JSON.stringify(probed)}`);
  const truncated = await firstFrame(dir, name, file, 0.7333);
  assert.equal(truncated.asset.frame_rate, '30/1', name);
  assert.deepEqual(truncated.receipt.frame_alignment, [{ asset_id: 'src', frame_rate: '30/1', applied: true }], name);
  assert.equal(truncated.mediaStart, 0.733433333, `${name}: corrected to frame 22 + 0.1 ms`);
  assert.equal(truncated.colour, 'blue', `${name}: frame 22 (first blue) is on screen: media time 0 = the 0.5 s video start`);
  assert.equal((await firstFrame(dir, `${name}-21`, file, 0.72)).colour, 'red', `${name}: frame 21 is still red`);
}

test('media time 0 is the earliest stream start; frame_rate only when that is the video start (MKV)', { timeout: 180000 }, async t => {
  assert.ok(process.env.PRODUCER_HEADLESS_SHELL_PATH, 'Set PRODUCER_HEADLESS_SHELL_PATH for this integration check');
  process.env.HF_DE_STALL_MS ??= '15000';
  const dir = await tempDir('source-start-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));

  // 1. Video and audio both start at 0.5 s (MKV keeps the offset).
  await assertShiftedStartCorrected(dir, 'shifted-mkv',
    await synthRedThenBlue(path.join(dir, 'shifted.mkv'), { switchFrame: 22, seconds: 2, acodec: 'aac', args: ['-output_ts_offset', '0.5'] }));

  // 2. Audio starting 67 ms before the video (MKV keeps a negative start; the
  // reproduction from the stall investigation): no frame_rate, the written
  // in-point is compiled as is and the renderer shows video time in-point − 0.067.
  // Red frames 0..29 (0–1 s), blue from 1 s.
  const primed = await synthRedThenBlue(path.join(dir, 'primed.mkv'), { switchFrame: 30, seconds: 3, acodec: 'aac',
    audioArgs: ['-itsoffset', '-0.067'], args: ['-avoid_negative_ts', 'disabled'] });
  const primedStarts = await starts(primed);
  assert.ok(primedStarts.video === 0 && primedStarts.audio < -0.06, `fixture: ${JSON.stringify(primedStarts)}`);
  // 1.0333 is 0.03 ms below frame 31 (1.03333…): the 0.6.0 rule recorded 30/1 and
  // corrected it; video time 1.0333 − 0.067 = 0.966 is red either way.
  const early = await firstFrame(dir, 'primed', primed, 1.0333);
  assert.ok(!('frame_rate' in early.asset));
  assert.deepEqual(early.receipt.frame_alignment, []);
  assert.equal(early.mediaStart, 1.0333, 'written in-point kept');
  assert.equal(early.colour, 'red', 'video time 0.966: still the red second');
  // 1.06 − 0.067 = 0.993 is red as well; 1.1 − 0.067 = 1.033 is blue.
  assert.equal((await firstFrame(dir, 'primed-106', primed, 1.06)).colour, 'red');
  assert.equal((await firstFrame(dir, 'primed-110', primed, 1.1)).colour, 'blue');
});

test('MP4 with every stream at the same non-zero start (edit list): the renderer takes it as media time 0', { timeout: 180000 }, async t => {
  assert.ok(process.env.PRODUCER_HEADLESS_SHELL_PATH, 'Set PRODUCER_HEADLESS_SHELL_PATH for this integration check');
  process.env.HF_DE_STALL_MS ??= '15000';
  const dir = await tempDir('source-start-mp4-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));

  // 1. H.264 + ALAC (no encoder priming) muxed with -output_ts_offset 0.5: the
  // MP4 muxer writes an empty edit, both streams start at 0.5 s.
  await assertShiftedStartCorrected(dir, 'offset-mp4',
    await synthRedThenBlue(path.join(dir, 'offset.mp4'), { switchFrame: 22, seconds: 2, acodec: 'alac', args: ['-output_ts_offset', '0.5'] }));

  // 2. Video-only MP4 remuxed with -itsoffset 0.5 (stream copy, empty edit list).
  const plain = await synthRedThenBlue(path.join(dir, 'plain.mp4'), { switchFrame: 22, seconds: 2 });
  await ffmpeg('-y', '-itsoffset', '0.5', '-i', plain, '-c', 'copy', path.join(dir, 'edit-list.mp4'));
  await assertShiftedStartCorrected(dir, 'edit-list-mp4', path.join(dir, 'edit-list.mp4'));

  // 3. H.264 + AAC under the same offset: the AAC priming (1024 samples at
  // 44.1 kHz) puts the audio start 23.2 ms before the video (0.47678 s), so
  // media time 0 is the audio start, no frame_rate is recorded and in-point X
  // shows video time X − 0.0232: 0.75 is still frame 21 (red; it would be blue
  // if media time 0 were the video start), 0.76 is frame 22 (blue).
  const primed = await synthRedThenBlue(path.join(dir, 'aac-offset.mp4'), { switchFrame: 22, seconds: 2, acodec: 'aac', args: ['-output_ts_offset', '0.5'] });
  const primedStarts = await starts(primed);
  assert.ok(primedStarts.video === 0.5 && primedStarts.audio > 0.47 && primedStarts.audio < 0.48, `fixture: ${JSON.stringify(primedStarts)}`);
  const at075 = await firstFrame(dir, 'aac-075', primed, 0.75);
  assert.ok(!('frame_rate' in at075.asset));
  assert.equal(at075.colour, 'red', 'video time 0.7268: frame 21');
  assert.equal((await firstFrame(dir, 'aac-076', primed, 0.76)).colour, 'blue', 'video time 0.7368: frame 22');
});
