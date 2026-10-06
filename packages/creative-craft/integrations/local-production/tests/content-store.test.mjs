import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { sha256, writeOnce } from '../content-store.mjs';

test('writeOnce publishes atomically, reuses or refuses existing files and never replaces them', async t => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'content-store-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const bytes = Buffer.from('one'), target = path.join(dir, `${sha256(bytes)}.bin`);
  assert.equal(await writeOnce(target, { bytes }, { expected: sha256(bytes) }), true);
  assert.equal(await writeOnce(target, { bytes }, { expected: sha256(bytes) }), false, 'identical content is reused');
  await assert.rejects(writeOnce(target, { bytes }, { conflict: 'taken' }), /taken/);
  // Content that does not match its address never lands; an existing file is not replaced.
  const other = path.join(dir, 'other.bin');
  await assert.rejects(writeOnce(other, { bytes: Buffer.from('two') }, { expected: sha256(bytes), mismatch: 'changed' }), /changed/);
  await assert.rejects(fs.access(other), { code: 'ENOENT' });
  await fs.writeFile(other, 'tampered');
  await assert.rejects(writeOnce(other, { bytes }, { expected: sha256(bytes), mismatch: 'changed' }), /changed/);
  assert.equal(await fs.readFile(other, 'utf8'), 'tampered');
  // Copies from a source file go through the same path; no temporary files remain.
  const source = path.join(dir, 'source'), copy = path.join(dir, 'copy.bin');
  await fs.writeFile(source, bytes);
  await writeOnce(copy, { source }, { expected: sha256(bytes) });
  assert.deepEqual(await fs.readFile(copy), bytes);
  assert.deepEqual((await fs.readdir(dir)).filter(n => n.startsWith('.pending-')), []);
});
