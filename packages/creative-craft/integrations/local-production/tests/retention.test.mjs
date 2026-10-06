import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { planRetention, applyRetention, withRetentionLock, occupied } from '../retention.mjs';
async function setup(t) {
  const root = await fs.realpath(await fs.mkdtemp(path.join(os.tmpdir(), 'creative-retention-')));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  for (let i = 1; i <= 4; i++) {
    const run = path.join(root, `2026-10-0${i}T00-00-00-000Z`);
    await fs.mkdir(run); await fs.writeFile(path.join(run, 'summary.json'), JSON.stringify({ status: 'passed', fixture: 'synthetic technical scenarios; not real creative evaluation' }));
    await fs.writeFile(path.join(run, 'sample.mp4'), 'synthetic');
  }
  return { root, first: path.join(root, '2026-10-01T00-00-00-000Z') };
}
test('dry run is read-only; apply retains latest two, summaries, and is repeatable', async t => {
  const { root, first } = await setup(t), p = await planRetention(root);
  assert.equal(p.candidates.length, 2); assert.equal(p.bytes, 18);
  assert.equal(await fs.readFile(path.join(first, 'sample.mp4'), 'utf8'), 'synthetic');
  const result = await withRetentionLock(root, () => applyRetention(p, async () => false));
  assert.equal(result.removedFiles, 2); assert.equal((await planRetention(root)).bytes, 0);
  assert.ok(await fs.readFile(path.join(first, 'summary.json')));
  assert.ok(await fs.readFile(path.join(root, p.retained[0], 'sample.mp4')));
});
test('failed and incomplete runs remain; unknown names never enter plan', async t => {
  const { root, first } = await setup(t);
  await fs.writeFile(path.join(first, 'summary.json'), '{"status":"failed"}');
  const second = path.join(root, '2026-10-02T00-00-00-000Z'); await fs.unlink(path.join(second, 'summary.json'));
  await fs.mkdir(path.join(root, 'user-project'));
  assert.equal((await planRetention(root)).candidates.length, 0);
  assert.ok(await fs.readFile(path.join(first, 'sample.mp4')));
});
for (const mode of ['pin', 'unknown', 'symlink']) test(`preserves ${mode} run`, async t => {
  const { root, first } = await setup(t);
  if (mode === 'pin') await fs.writeFile(path.join(first, '.keep'), '');
  if (mode === 'unknown') await fs.writeFile(path.join(first, 'unique.blob'), 'data');
  if (mode === 'symlink') await fs.symlink(path.join(root, 'user-file'), path.join(first, 'link'));
  const p = await planRetention(root); assert.ok(p.skipped.includes(path.basename(first)));
  await withRetentionLock(root, () => applyRetention(p, async () => false));
  assert.ok(await fs.readFile(path.join(first, 'sample.mp4')));
});
test('busy runs defer and plan drift prevents deletion', async t => {
  const { root, first } = await setup(t), p = await planRetention(root);
  assert.equal((await applyRetention(p, async () => true)).removedFiles, 0);
  await fs.writeFile(path.join(first, 'sample.mp4'), 'changed');
  await assert.rejects(applyRetention(p, async () => false), /plan changed/);
  assert.equal(await fs.readFile(path.join(first, 'sample.mp4'), 'utf8'), 'changed');
});
test('one lock covers smoke/retention; failure releases lock', async t => {
  const { root } = await setup(t);
  await assert.rejects(withRetentionLock(root, async () => {
    await assert.rejects(withRetentionLock(root, async () => {}), { code: 'EEXIST' });
    throw new Error('synthetic failure');
  }), /synthetic failure/);
  await withRetentionLock(root, async () => {});
});
test('real macOS lsof detects a process using a run', { skip: process.platform !== 'darwin' }, async t => {
  const { first } = await setup(t);
  const child = spawn(process.execPath, ['-e', 'setInterval(()=>{},1000)'], { cwd: first, stdio: 'ignore' });
  await once(child, 'spawn');
  try { assert.equal(await occupied(first), true); }
  finally { const done = once(child, 'exit'); child.kill(); await done; }
  assert.equal(await occupied(first), false);
});
