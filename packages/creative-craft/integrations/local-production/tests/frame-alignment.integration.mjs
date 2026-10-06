// Explicit opt-in: real producer + Chrome (PRODUCER_HEADLESS_SHELL_PATH).
// A 0.6.0 project holding frame_rate on an MKV whose audio starts before the
// video renders without the truncation correction (renderer behaviour), the
// receipt records why, and QA compiles the same view.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { createProject, digest } from '../project.mjs';
import { renderProject } from '../render.mjs';
import { qaRender } from '../qa.mjs';
import { agedProject, frameColour, synthRedThenBlue, tempDir } from './media-fixtures.mjs';

test('a stale frame_rate from a 0.6.0 project is not applied at render; receipt and QA record it', { timeout: 180000 }, async t => {
  assert.ok(process.env.PRODUCER_HEADLESS_SHELL_PATH, 'Set PRODUCER_HEADLESS_SHELL_PATH for this integration check');
  process.env.HF_DE_STALL_MS ??= '15000';
  const dir = await tempDir('frame-alignment-render-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  // Red 0–1 s, blue from 1 s; audio starts before the video (negative start).
  const primed = await synthRedThenBlue(path.join(dir, 'primed.mkv'), { switchFrame: 30, seconds: 3, acodec: 'aac',
    audioArgs: ['-itsoffset', '-0.067'], args: ['-avoid_negative_ts', 'disabled'] });
  const root = path.join(dir, 'project');
  await createProject(root, { project_id: 'aged', title: 'aged', canvas: { width: 320, height: 180, fps: 30 }, assets: [{ id: 'src', path: primed }],
    tracks: [{ id: 'v', kind: 'video', locked: false }],
    items: [{ id: 'one', track_id: 'v', kind: 'media', asset_id: 'src', start_frame: 0, frames: 15, source_in_seconds: 1.0333, volume: 0.5, fit: 'cover' }] });
  const revision = await agedProject(root), before = await digest(revision);

  const output = path.join(dir, 'render');
  const receipt = await renderProject(root, output, { preview: true });
  assert.equal(receipt.status, 'completed');
  assert.equal(receipt.frame_alignment.length, 1);
  assert.deepEqual({ ...receipt.frame_alignment[0], reason: undefined }, { asset_id: 'src', frame_rate: '30/1', applied: false, reason: undefined });
  assert.match(receipt.frame_alignment[0].reason, /after the earliest stream start -0\.\d+ s \(media time 0\)/);
  assert.deepEqual(JSON.parse(await fs.readFile(path.join(output, 'receipt.json'), 'utf8')).frame_alignment, receipt.frame_alignment);
  // The written in-point is compiled as is (the stale rate would give 1.033433333).
  const html = await fs.readFile(path.join(output, 'index.html'), 'utf8');
  assert.equal(/<video[^>]*data-media-start="([^"]+)"/.exec(html)[1], '1.0333');
  assert.equal(JSON.parse(await fs.readFile(path.join(output, 'project.json'), 'utf8')).assets[0].frame_rate, '30/1', 'snapshot keeps the document as written');
  assert.equal(await frameColour(path.join(output, 'video.mp4'), 0), 'red', 'renderer behaviour: video time 1.0333 + earliest start (< 1 s)');
  assert.equal(await digest(revision), before, 'the project revision is not rewritten');

  const qa = await qaRender(root, output, path.join(dir, 'qa'));
  for (const id of ['cut-boundary-fragments', 'burned-caption-cut-points']) {
    const check = qa.checks.find(c => c.id === id);
    assert.deepEqual(check.measured.frame_alignment, receipt.frame_alignment, id);
    assert.equal(check.measured.frame_alignment_source, 'receipt', id);
    const point = check.measured.points.find(p => p.edge === 'in');
    assert.equal(point.source_seconds, 1.0333, `${id}: judged at the written in-point`);
    assert.ok(!('compiled_source_seconds' in point) && !('source_frame' in point), `${id}: no correction`);
  }

  // A receipt without frame_alignment (a 0.6.0 render, which corrected every
  // asset with frame_rate): QA compiles that way, without probing again, and says so.
  const receiptFile = path.join(output, 'receipt.json'), legacy = JSON.parse(await fs.readFile(receiptFile, 'utf8'));
  delete legacy.frame_alignment;
  await fs.writeFile(receiptFile, JSON.stringify(legacy));
  const legacyQa = await qaRender(root, output, path.join(dir, 'qa-legacy'));
  for (const id of ['cut-boundary-fragments', 'burned-caption-cut-points']) {
    const check = legacyQa.checks.find(c => c.id === id);
    assert.equal(check.measured.frame_alignment_source, 'legacy-default', id);
    assert.deepEqual(check.measured.frame_alignment, [{ asset_id: 'src', frame_rate: '30/1', applied: true }], id);
    const point = check.measured.points.find(p => p.edge === 'in');
    assert.equal(point.compiled_source_seconds, 1.033433, `${id}: judged as the legacy render compiled it`);
  }
});
