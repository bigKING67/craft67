import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { createProject } from '../project.mjs';
import { renderProject, withRenderLock } from '../render.mjs';
import { synthVideo, tempDir } from './media-fixtures.mjs';

const tick = ms => new Promise(resolve => setTimeout(resolve, ms));

test('captures in one process run one at a time, in call order', async () => {
  const events = [];
  const job = (name, ms) => withRenderLock(async () => { events.push(`start ${name}`); await tick(ms); events.push(`end ${name}`); return name; });
  assert.deepEqual(await Promise.all([job('a', 30), job('b', 5), job('c', 1)]), ['a', 'b', 'c']);
  assert.deepEqual(events, ['start a', 'end a', 'start b', 'end b', 'start c', 'end c']);
});

test('a failing capture does not block later ones', async () => {
  await assert.rejects(withRenderLock(async () => { throw new Error('boom'); }), /boom/);
  assert.equal(await withRenderLock(async () => 'next'), 'next');
});

test('a task cancelled while waiting rejects at once and never runs; a running task is not abandoned', async () => {
  let release;
  const holder = withRenderLock(() => new Promise(resolve => { release = resolve; }));
  const controller = new AbortController(), ran = [];
  const waiting = withRenderLock(async () => { ran.push('cancelled task'); }, controller.signal);
  const started = Date.now();
  controller.abort();
  await assert.rejects(waiting, { name: 'AbortError' });
  assert.ok(Date.now() - started < 100, 'rejected without waiting for the lock');
  // Aborting the signal of a running task does not release the lock before the task settles.
  const running = new AbortController(), order = [];
  const busy = withRenderLock(async () => { order.push('busy start'); await tick(30); order.push('busy end'); }, running.signal);
  const after = withRenderLock(async () => { order.push('after'); });
  release();
  await holder;
  await tick(5);
  running.abort();
  await Promise.all([busy, after]);
  assert.deepEqual(order, ['busy start', 'busy end', 'after']);
  assert.deepEqual(ran, [], 'the cancelled task never ran');
});

test('a render cancelled while another holds the capture lock returns cancelled at once', { timeout: 60000 }, async t => {
  const dir = await tempDir('render-lock-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const clip = await synthVideo(path.join(dir, 'clip.mp4'), { size: '320x180', seconds: 1 }), root = path.join(dir, 'project');
  await createProject(root, { project_id: 'lock', title: 'lock', canvas: { width: 320, height: 180, fps: 30 }, assets: [{ id: 'clip', path: clip }],
    tracks: [{ id: 'v', kind: 'video', locked: false }],
    items: [{ id: 'one', track_id: 'v', kind: 'media', asset_id: 'clip', start_frame: 0, frames: 15, source_in_seconds: 0, volume: 0 }] });
  // A long capture holds the lock (stand-in for another render's executeRenderJob).
  let release;
  const holder = withRenderLock(() => new Promise(resolve => { release = resolve; }));
  t.after(() => release());
  const controller = new AbortController(), output = path.join(dir, 'render');
  const pending = renderProject(root, output, { preview: true, signal: controller.signal });
  // Wait until the render is queued for the capture (preparation and lint done outside the lock).
  for (let i = 0; i < 500 && !(await fs.stat(path.join(output, 'captions.vtt')).catch(() => null)); i++) await tick(20);
  await tick(1500); // lint and the producer import (measured well under 1 s here)
  const cancelled = Date.now();
  controller.abort();
  await assert.rejects(pending, { name: 'AbortError' });
  assert.ok(Date.now() - cancelled < 1000, 'returned without waiting for the lock holder');
  const receipt = JSON.parse(await fs.readFile(path.join(output, 'receipt.json'), 'utf8'));
  assert.equal(receipt.status, 'cancelled');
  assert.ok(receipt.lint, 'preparation and lint ran before queueing for the capture');
  await assert.rejects(fs.access(path.join(output, 'video.mp4')), { code: 'ENOENT' });
  release();
  await holder;
});
