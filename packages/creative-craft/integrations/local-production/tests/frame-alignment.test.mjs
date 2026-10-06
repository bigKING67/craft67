import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { createProject, digest, editBatch, loadProject, verifyAssets } from '../project.mjs';
import { carryAlignment, legacyAlignment } from '../frame-alignment.mjs';
import { renderAlignment } from '../qa.mjs';
import { alignmentOf, bindAlignment, compiledView, correctionOf } from '../source-frames.mjs';
import { agedProject, synthRedThenBlue, tempDir } from './media-fixtures.mjs';

// A 0.6.0-style project: 'src' (audio before video) holds a stale frame_rate,
// 'clean' a valid one; both items are written at the truncated 1.0333.
async function aged(t) {
  const dir = await tempDir('frame-alignment-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const primed = await synthRedThenBlue(path.join(dir, 'primed.mkv'), { switchFrame: 30, seconds: 2, acodec: 'aac',
    audioArgs: ['-itsoffset', '-0.067'], args: ['-avoid_negative_ts', 'disabled'] });
  const clean = await synthRedThenBlue(path.join(dir, 'clean.mp4'), { switchFrame: 31, seconds: 2 });
  const root = path.join(dir, 'project');
  const item = (id, asset, start) => ({ id, track_id: 'v', kind: 'media', asset_id: asset, start_frame: start, frames: 10, source_in_seconds: 1.0333, volume: 0 });
  const created = await createProject(root, { project_id: 'aged', title: 'aged', canvas: { width: 320, height: 180, fps: 30 },
    assets: [{ id: 'src', path: primed }, { id: 'clean', path: clean }], tracks: [{ id: 'v', kind: 'video', locked: false }],
    items: [item('old', 'src', 0), item('new', 'clean', 10)] });
  assert.ok(!('frame_rate' in created.assets[0]), 'the 0.7.0 import does not record it');
  assert.equal(created.assets[1].frame_rate, '30/1');
  return { dir, root, revision: await agedProject(root) };
}

test('loadProject decides frame alignment once and binds it: a stale frame_rate is not applied, a valid one is', { timeout: 60000 }, async t => {
  const { root, revision } = await aged(t), before = await digest(revision);
  const { doc, alignment, verified } = await loadProject(root);
  assert.equal(doc.assets[0].frame_rate, '30/1');
  assert.equal(alignmentOf(doc), alignment);
  assert.equal(alignment.length, 2);
  const [stale, valid] = alignment;
  assert.deepEqual(valid, { asset_id: 'clean', frame_rate: '30/1', applied: true });
  assert.deepEqual({ ...stale, reason: undefined }, { asset_id: 'src', frame_rate: '30/1', applied: false, reason: undefined });
  assert.match(stale.reason, /video stream starts at 0 s, after the earliest stream start -0\.\d+ s \(media time 0\)/);
  assert.deepEqual([...verified.keys()].sort(), ['clean', 'src'], 'the files of both assets were digest-checked');

  // Every compiledView of the loaded document uses that decision (no option to pass or forget).
  const view = compiledView(doc);
  assert.equal(view.items[0].source_in_seconds, 1.0333, 'stale asset: written in-point kept');
  assert.equal(correctionOf(view.items[0]), null);
  assert.equal(view.items[1].source_in_seconds, 1.033433333, 'valid asset: corrected to frame 31 + 0.1 ms');
  assert.equal(compiledView(view), view, 'the view is final');
  assert.equal(alignmentOf(view), alignment);
  // A document that was not loaded (a copy built in memory) gets the structural view: every frame_rate applied.
  assert.equal(compiledView(structuredClone(doc)).items[0].source_in_seconds, 1.033433333);
  assert.equal(await digest(revision), before, 'the project revision is not rewritten');
});

test('alignment binding is checked; edit batches carry it; QA takes the receipt or the legacy default', { timeout: 60000 }, async t => {
  const { root } = await aged(t);
  const { doc, alignment } = await loadProject(root);
  const plain = structuredClone(doc);
  assert.throws(() => bindAlignment(plain, alignment.slice(1)), /does not describe this document/);
  assert.throws(() => bindAlignment(plain, [alignment[0], { ...alignment[1], frame_rate: '25/1' }]), /does not describe this document/);
  assert.throws(() => bindAlignment(compiledView(doc), alignment), /compiled view cannot be bound/);

  // carryAlignment: the same bytes keep their decision, new imports are applied, anything else is refused.
  assert.deepEqual(carryAlignment(plain, [[doc, alignment]]), alignment);
  const imported = { ...plain, assets: [...plain.assets, { ...plain.assets[1], id: 'fresh', sha256: 'a'.repeat(64) }] };
  assert.deepEqual(carryAlignment(imported, [[doc, alignment]], new Set(['a'.repeat(64)])).at(-1), { asset_id: 'fresh', frame_rate: '30/1', applied: true });
  assert.throws(() => carryAlignment(imported, [[doc, alignment]]), /asset fresh was not determined/);

  // An edit batch on the aged project compiles the new revision with the carried decision (its font runs need it).
  await editBatch(root, { base_revision: 1, author: 'agent', summary: 'trim', operations: [{ type: 'trim_item', item_id: 'new', tail_frames: 2 }] });
  const next = await loadProject(root);
  assert.equal(next.doc.revision, 2);
  assert.deepEqual(next.alignment, alignment);

  // QA: the receipt's alignment as recorded; a receipt without one (before 0.7.0) applied every frame_rate.
  assert.deepEqual(renderAlignment({ frame_alignment: alignment }, doc), { alignment, source: 'receipt' });
  assert.deepEqual(renderAlignment({}, doc), { alignment: legacyAlignment(doc), source: 'legacy-default' });
  assert.ok(legacyAlignment(doc).every(e => e.applied));
  const legacyView = compiledView(bindAlignment({ ...doc }, legacyAlignment(doc)));
  assert.equal(legacyView.items[0].source_in_seconds, 1.033433333, 'legacy renders corrected every asset with frame_rate');
});

test('asset files are digest-checked before any probe result is used, once per render, per file', { timeout: 60000 }, async t => {
  const { dir, root } = await aged(t);
  const { doc, templates, verified } = await loadProject(root);
  // A copy of the project whose 'clean' asset bytes were changed: same sha256 in
  // the document, different file. Concurrent loads do not share each other's outcome.
  const copy = path.join(dir, 'copy');
  await fs.cp(root, copy, { recursive: true });
  const file = path.join(copy, doc.assets[1].file);
  await fs.chmod(file, 0o644);
  await fs.appendFile(file, Buffer.from('tampered'));
  const [intact, tampered] = await Promise.allSettled([loadProject(root), loadProject(copy)]);
  assert.equal(intact.status, 'fulfilled');
  assert.deepEqual(intact.value.alignment, alignmentOf(doc));
  assert.equal(tampered.status, 'rejected');
  assert.match(tampered.reason.message, /Asset changed: clean/);

  // verifyAssets reuses loadProject's checks: a file it verified is not hashed again; others are.
  await assert.rejects(verifyAssets(copy, doc, templates), /Asset changed: clean/);
  const reused = await verifyAssets(copy, doc, templates, { verified: new Map([...verified].map(([id]) => [id, path.join(copy, 'reused')])) });
  assert.equal(reused.get('clean'), path.join(copy, 'reused'));
});
