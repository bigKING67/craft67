// Explicit opt-in: real producer + Chrome (PRODUCER_HEADLESS_SHELL_PATH).
// Two renders started together in one process (red and blue sources) both
// complete with their own colour over the whole first frame (top, centre and
// bottom regions): only the browser capture is serialized (withRenderLock),
// preparation, lint and the checks run concurrently, and the captures no
// longer corrupt each other (measured before the lock: the picture covered
// only the top of the frame, black below).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { createProject } from '../project.mjs';
import { renderProject } from '../render.mjs';
import { REGION, frameColour, synthVideo, tempDir } from './media-fixtures.mjs';

test('two concurrent renders in one process keep their own picture', { timeout: 240000 }, async t => {
  assert.ok(process.env.PRODUCER_HEADLESS_SHELL_PATH, 'Set PRODUCER_HEADLESS_SHELL_PATH for this integration check');
  process.env.HF_DE_STALL_MS ??= '15000';
  const dir = await tempDir('render-concurrency-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const make = async color => {
    const clip = await synthVideo(path.join(dir, `${color}.mp4`), { size: '320x240', seconds: 1, color }), root = path.join(dir, color);
    await createProject(root, { project_id: color, title: color, canvas: { width: 320, height: 240, fps: 30 }, assets: [{ id: 'clip', path: clip }],
      tracks: [{ id: 'v', kind: 'video', locked: false }],
      items: [{ id: 'one', track_id: 'v', kind: 'media', asset_id: 'clip', start_frame: 0, frames: 30, source_in_seconds: 0, volume: 0 }] });
    return root;
  };
  const roots = { red: await make('red'), blue: await make('blue') };
  const receipts = await Promise.all(Object.entries(roots).map(([color, root]) => renderProject(root, path.join(dir, `${color}-render`), { preview: true })));
  assert.deepEqual(receipts.map(r => r.status), ['completed', 'completed']);
  for (const color of Object.keys(roots)) {
    const video = path.join(dir, `${color}-render`, 'video.mp4');
    for (const frame of [0, 15, 29]) {
      for (const region of ['top', 'centre', 'bottom']) assert.equal(await frameColour(video, frame, REGION[region]), color, `${color} frame ${frame} ${region}`);
    }
  }
});
