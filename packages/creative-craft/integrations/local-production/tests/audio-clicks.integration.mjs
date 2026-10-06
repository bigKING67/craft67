// Explicit opt-in: real producer + Chrome (PRODUCER_HEADLESS_SHELL_PATH).
// Cut-point audio through the real renderer (0.8.0): a hard cut between two
// out-of-phase stretches of one 440 Hz tone and an equal-power crossfade into a
// 660 Hz tone. The render must carry no click at the cut (QA cut-point-clicks
// pass), keep the crossfade mid-point within 0.5 dB of either side, and the
// same render with its audio swapped for the hard splice (no declick, the
// fault the declick prevents) must warn at the cut with both items cited.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { createProject, digest, run } from '../project.mjs';
import { renderProject } from '../render.mjs';
import { qaRender } from '../qa.mjs';
import { mediaTool } from '../media-analysis.mjs';
import { ffmpeg, tempDir } from './media-fixtures.mjs';

const RATE = 48000;
const tone = async (file, hz) => ffmpeg('-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=30:duration=6', '-f', 'lavfi', '-i', `sine=frequency=${hz}:sample_rate=${RATE}:duration=6`,
  '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', file);
const pcm = async (file, from, length) => {
  const { stdout } = await run(mediaTool('ffmpeg'), ['-v', 'error', '-i', file, '-vn', '-ac', '1', '-ar', String(RATE), '-f', 'f32le', '-'], { encoding: 'buffer', maxBuffer: 64 * 1024 * 1024 });
  const x = new Float32Array(stdout.buffer.slice(stdout.byteOffset, stdout.byteOffset + stdout.length));
  let sum = 0;
  for (let n = Math.round(from * RATE); n < Math.round((from + length) * RATE); n++) sum += x[n] ** 2;
  return sum / Math.round(length * RATE);
};

test('cut-point audio through the renderer: declicked hard cut, equal-power crossfade, click QA on a hard splice', async t => {
  const dir = await tempDir('creative-audio-cuts-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const low = path.join(dir, 'low.mp4'), high = path.join(dir, 'high.mp4'), root = path.join(dir, 'project');
  await tone(low, 440); await tone(high, 660);
  // left: 440 Hz from 1.1 s; right: the same tone a quarter period later (hard cut at 1.0 s);
  // third: 660 Hz crossfading in over right's last 6 frames (1.8–2.0 s), to 3.0 s.
  await createProject(root, { project_id: 'audio-cuts', title: 'audio cuts', canvas: { width: 320, height: 180, fps: 30 },
    assets: [{ id: 'low', path: low }, { id: 'high', path: high }], tracks: [{ id: 'v', kind: 'video', locked: false }],
    items: [{ id: 'left', track_id: 'v', kind: 'media', asset_id: 'low', start_frame: 0, frames: 30, source_in_seconds: 1.1, volume: 1, fit: 'cover' },
      { id: 'right', track_id: 'v', kind: 'media', asset_id: 'low', start_frame: 30, frames: 30, source_in_seconds: 2.3 + 1 / (4 * 440), volume: 1, fit: 'cover' },
      { id: 'third', track_id: 'v', kind: 'media', asset_id: 'high', start_frame: 54, frames: 36, source_in_seconds: 1, volume: 1, fit: 'cover',
        transition_in: { kind: 'crossfade', frames: 6 } }] });
  const renderDir = path.join(dir, 'render');
  const receipt = await renderProject(root, renderDir, { preview: true });
  assert.equal(receipt.status, 'completed');
  const video = path.join(renderDir, 'video.mp4');

  const qa = await qaRender(root, renderDir, path.join(dir, 'qa'));
  const clicks = qa.checks.find(c => c.id === 'cut-point-clicks');
  assert.equal(clicks.category, 'audio');
  assert.deepEqual(clicks.measured.cut_points.map(p => [p.time_seconds, p.items.map(i => `${i.item_id} ${i.edge}`)]),
    [[1, ['left out', 'right in']], [1.8, ['third in']], [2, ['right out']]]);
  assert.equal(clicks.status, 'pass', JSON.stringify(clicks.measured.cut_points));

  // Equal-power crossfade: 440 Hz alone, 50/50 at 1.9 s, 660 Hz alone (50 ms = 11 beat periods).
  const before = await pcm(video, 1.5 - 0.025, 0.05), mid = await pcm(video, 1.9 - 0.025, 0.05), after = await pcm(video, 2.5 - 0.025, 0.05);
  const deviation = { mid_vs_before_db: 10 * Math.log10(mid / before), mid_vs_after_db: 10 * Math.log10(mid / after) };
  for (const value of Object.values(deviation)) assert.ok(Math.abs(value) <= 0.5, JSON.stringify(deviation));

  // Fault injection: the same picture with the hard splice as its sound.
  const spliced = path.join(renderDir, 'spliced.mp4');
  const expr = `if(lt(t\\,1)\\,0.125*sin(2*PI*440*(t+1.1))\\,if(lt(t\\,2)\\,0.125*sin(2*PI*440*(t+1.3)+PI/2)\\,0.125*sin(2*PI*660*(t-0.8))))`;
  await ffmpeg('-i', video, '-f', 'lavfi', '-i', `aevalsrc=${expr}:s=${RATE}:d=3`, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', spliced);
  await fs.rename(spliced, video);
  const tampered = JSON.parse(await fs.readFile(path.join(renderDir, 'receipt.json'), 'utf8'));
  tampered.output.sha256 = await digest(video);
  await fs.writeFile(path.join(renderDir, 'receipt.json'), JSON.stringify(tampered, null, 2));
  const bad = (await qaRender(root, renderDir, path.join(dir, 'qa-spliced'))).checks.find(c => c.id === 'cut-point-clicks');
  assert.equal(bad.status, 'warn', JSON.stringify(bad.measured.cut_points));
  // The splice also jumps from 440 to 660 Hz at 2.0 s (no crossfade): a second click.
  assert.deepEqual(bad.refs, [{ time_seconds: 1, item_id: 'left' }, { time_seconds: 1, item_id: 'right' }, { time_seconds: 2, item_id: 'right' }]);
  assert.equal(bad.measured.cut_points.find(p => p.time_seconds === 1.8).click, false);
  console.log(JSON.stringify({ render: clicks.measured.cut_points.map(p => [p.time_seconds, p.ratio, p.peak]),
    spliced: bad.measured.cut_points.map(p => [p.time_seconds, p.ratio, p.peak]), crossfade: deviation }));
});
