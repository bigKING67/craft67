import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createProject, editBatch, loadProject, readProject, run, validateV2 } from '../project.mjs';
import { compose } from '../composition.mjs';
import { renderProject } from '../render.mjs';
import { CAPTION_FONT, installCaptionFont } from '../caption-font.mjs';
import { TEMPLATES, runtimeTemplate, templateProvenance, useMinimumText, useRuntimeTemplates } from '../templates.mjs';
import { copyBoundTemplates } from '../template-binding.mjs';

const runtimeDir = fileURLToPath(new URL('../templates/', import.meta.url));
const fixtures = fileURLToPath(new URL('../../../tests/fixtures/edit-document-v2/', import.meta.url));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const batch = (base_revision, operations) => ({ base_revision, author: 'agent', summary: 'test', operations });
const card = { id: 'card', track_id: 'v_gfx', kind: 'graphic', template: 'title-card', vars: { title: '开场', subtitle: '副标题' }, start_frame: 0, frames: 12 };
const strap = { id: 'strap', track_id: 'v_gfx', kind: 'graphic', template: 'lower-third', vars: { title: '主讲人' }, start_frame: 12, frames: 12 };

async function tempDir(t, prefix) {
  const dir = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), prefix));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  return dir;
}
async function project(t, items = [card]) {
  const dir = await tempDir(t, 'template-binding-');
  const clip = path.join(dir, 'clip.mp4'), root = path.join(dir, 'project');
  await run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=128x72:rate=24:duration=1', '-pix_fmt', 'yuv420p', clip]);
  await createProject(root, { project_id: 'pinned', title: '模板固定', canvas: { width: 128, height: 72, fps: 24 }, assets: [{ id: 'clip', path: clip }],
    tracks: [{ id: 'v_main', kind: 'video', locked: false }, { id: 'v_gfx', kind: 'video', locked: false }],
    items: [{ id: 'one', track_id: 'v_main', kind: 'media', asset_id: 'clip', start_frame: 0, frames: 24, source_in_seconds: 0, volume: 0 }, ...items] });
  return root;
}
// Compiled HTML of one revision from its own template set.
const htmlOf = async (root, revision) => { const { doc, templates } = await loadProject(root, revision); return compose(doc, undefined, { templates }).html; };
const stored = async root => (await fs.readdir(path.join(root, 'templates'))).sort();
const revisionCount = async root => (await fs.readdir(path.join(root, 'revisions'))).filter(n => n.endsWith('.json')).length;
// A simulated execution-layer upgrade: title-card v3 drops the subtitle var and widens the gap.
async function runtimeWith(t, name, change) {
  const dir = await tempDir(t, 'template-runtime-');
  for (const file of await fs.readdir(runtimeDir)) await fs.copyFile(path.join(runtimeDir, file), path.join(dir, file));
  const template = JSON.parse(await fs.readFile(path.join(dir, `${name}.json`), 'utf8'));
  change(template);
  await fs.writeFile(path.join(dir, `${name}.json`), JSON.stringify(template, null, 2));
  return dir;
}
const upgradedRuntime = t => runtimeWith(t, 'title-card', v3 => {
  v3.version = 3;
  delete v3.vars.subtitle;
  v3.html = v3.html.replace('<span class="gfx-title-card-subtitle">{{subtitle}}</span>', '');
  v3.css = v3.css.replace('gap:1.2em', 'gap:2em');
});
// A compatible upgrade (same vars): only the layout changes.
const widerGap = (t, name = 'title-card') => runtimeWith(t, name, v3 => { v3.version = 3; v3.css = v3.css.replace(/gap:[0-9.]+em|padding:1em/, 'gap:2em'); });

test('create and edit pin the templates graphics use; dry-run reports new bindings without writing', async t => {
  const root = await project(t), runtime = runtimeTemplate('title-card');
  const first = await readProject(root);
  assert.deepEqual(first.graphic_templates, [{ id: 'title-card', version: 2, sha256: runtime.sha256, file: `templates/${runtime.sha256}.json` }]);
  const file = path.join(root, first.graphic_templates[0].file);
  assert.ok((await fs.lstat(file)).isFile());
  assert.deepEqual(await fs.readFile(file), Buffer.from(runtime.bytes), 'normalized execution-layer bytes, content-addressed');
  // Shipped templates are already in normalized form, so bindings made before
  // normalization (raw source bytes) have the same digest and stay valid.
  assert.deepEqual(Buffer.from(runtime.bytes), await fs.readFile(path.join(runtimeDir, 'title-card.json')));
  assert.deepEqual(templateProvenance(first), [{ id: 'title-card', version: 2, sha256: runtime.sha256, pinned: true, source: 'project', file: first.graphic_templates[0].file }]);

  const add = batch(1, [{ type: 'add_item', item: strap }]);
  const dry = await editBatch(root, add, { dryRun: true });
  const lower = runtimeTemplate('lower-third');
  assert.deepEqual(dry.diff.graphic_templates, { added: [{ id: 'lower-third', version: 2, sha256: lower.sha256 }], removed: [], changed: [] });
  assert.deepEqual(await stored(root), [`${runtime.sha256}.json`], 'dry-run writes no template file');
  assert.equal(await revisionCount(root), 1);
  await editBatch(root, add);
  const second = await readProject(root);
  assert.deepEqual(second.graphic_templates.map(b => b.id), ['lower-third', 'title-card']);
  assert.deepEqual(second.graphic_templates.find(b => b.id === 'title-card'), first.graphic_templates[0], 'existing binding unchanged');
  assert.deepEqual(await stored(root), [`${lower.sha256}.json`, `${runtime.sha256}.json`].sort());

  // Removing the last graphic that uses a template drops its binding (the stored file stays).
  const removed = await editBatch(root, batch(2, [{ type: 'remove_item', item_id: 'strap' }]));
  assert.deepEqual(removed.diff.graphic_templates.removed, ['lower-third']);
  assert.deepEqual((await readProject(root)).graphic_templates, first.graphic_templates);
  await editBatch(root, batch(3, [{ type: 'remove_item', item_id: 'card' }]));
  assert.deepEqual((await readProject(root)).graphic_templates, [], 'field kept once pinned, now empty');
});

test('an execution-layer template change leaves pinned revisions alone until rebind_template', async t => {
  const root = await project(t), original = runtimeTemplate('title-card').sha256;
  const before = await htmlOf(root, 1);
  const restore = useRuntimeTemplates(await upgradedRuntime(t));
  t.after(restore);
  const upgraded = runtimeTemplate('title-card').sha256;
  assert.notEqual(upgraded, original);
  const rev1 = await readProject(root, 1);
  assert.equal(await htmlOf(root, 1), before, 'old revision re-compiles to identical HTML from its bound bytes');
  assert.throws(() => validateV2(rev1, { templates: TEMPLATES }), /has no var subtitle/, 'the runtime template would reject these vars');
  // Other operations keep the binding.
  const moved = await editBatch(root, batch(1, [{ type: 'move_item', item_id: 'card', start_frame: 2 }]));
  assert.deepEqual(moved.diff.graphic_templates, { added: [], removed: [], changed: [] });
  assert.equal((await readProject(root)).graphic_templates[0].sha256, original);
  // rebind_template: vars are checked against the new bytes; alone; used; not a no-op.
  await assert.rejects(editBatch(root, batch(2, [{ type: 'rebind_template', template: 'title-card' }])), /has no var subtitle/);
  await editBatch(root, batch(2, [{ type: 'set_item_props', item_id: 'card', props: { vars: { title: '开场' } } }]));
  await assert.rejects(editBatch(root, batch(3, [{ type: 'rebind_template', template: 'title-card' }, { type: 'move_item', item_id: 'card', start_frame: 0 }])), /only operation/);
  await assert.rejects(editBatch(root, batch(3, [{ type: 'move_item', item_id: 'card', start_frame: 0 }, { type: 'rebind_template', template: 'title-card' }])), /only operation/);
  await assert.rejects(editBatch(root, batch(3, [{ type: 'rebind_template', template: 'lower-third' }])), /not used by any graphic/);
  const dry = await editBatch(root, batch(3, [{ type: 'rebind_template', template: 'title-card' }]), { dryRun: true });
  assert.deepEqual(dry.diff.graphic_templates.changed, [{ id: 'title-card', from: { version: 2, sha256: original }, to: { version: 3, sha256: upgraded } }]);
  assert.deepEqual(await stored(root), [`${original}.json`]);
  await editBatch(root, batch(3, [{ type: 'rebind_template', template: 'title-card' }]));
  const rebound = await readProject(root);
  assert.deepEqual(rebound.graphic_templates, [{ id: 'title-card', version: 3, sha256: upgraded, file: `templates/${upgraded}.json` }]);
  const html = await htmlOf(root);
  assert.ok(html.includes('data-template-version="3"') && html.includes('gap:2em') && !html.includes('副标题'));
  await assert.rejects(editBatch(root, batch(4, [{ type: 'rebind_template', template: 'title-card' }])), /already bound to the current template bytes \(no change\)/);
  // revert_to restores the target's bindings with its content: revision 1's
  // vars and template bytes, and the same compiled HTML.
  const reverted = await editBatch(root, batch(4, [{ type: 'revert_to', revision: 1 }]));
  assert.deepEqual(reverted.diff.graphic_templates.changed, [{ id: 'title-card', from: { version: 3, sha256: upgraded }, to: { version: 2, sha256: original } }]);
  const back = await readProject(root);
  assert.deepEqual([back.graphic_templates, back.items], [rev1.graphic_templates, rev1.items]);
  assert.equal(await htmlOf(root), before);
  // Reverting to the rebound revision brings its bytes back.
  await editBatch(root, batch(5, [{ type: 'revert_to', revision: 4 }]));
  assert.equal((await readProject(root)).graphic_templates[0].sha256, upgraded);
  restore();
  // Back on the shipped runtime: pinned revisions still render their own bytes.
  assert.match(await htmlOf(root), /gap:2em/);
  assert.equal(await htmlOf(root, 1), before);
  assert.equal(await htmlOf(root, 5), before);
});

test('rebind_template and revert_to never change the template bytes of graphics on locked tracks', async t => {
  const root = await project(t), original = runtimeTemplate('title-card').sha256;
  t.after(useRuntimeTemplates(await widerGap(t)));
  await editBatch(root, batch(1, [{ type: 'edit_track', track_id: 'v_gfx', locked: true }]));
  await assert.rejects(editBatch(root, batch(2, [{ type: 'rebind_template', template: 'title-card' }]), { dryRun: true }), /Track is locked: v_gfx \(graphic card would render template title-card from different bytes\)/);
  await editBatch(root, batch(2, [{ type: 'edit_track', track_id: 'v_gfx', locked: false }]));
  await editBatch(root, batch(3, [{ type: 'rebind_template', template: 'title-card' }]));
  await editBatch(root, batch(4, [{ type: 'edit_track', track_id: 'v_gfx', locked: true }]));
  // Same items on the locked track, but revision 1 renders them from other bytes.
  await assert.rejects(editBatch(root, batch(5, [{ type: 'revert_to', revision: 1 }])), /Track is locked: v_gfx \(graphic card would render template title-card/);
  await editBatch(root, batch(5, [{ type: 'revert_to', revision: 4 }]));
  assert.notEqual((await readProject(root)).graphic_templates[0].sha256, original);
});

test('missing, altered, symlinked or invalid bound templates fail the read and the render', async t => {
  const root = await project(t), [binding] = (await readProject(root)).graphic_templates;
  const file = path.join(root, binding.file), good = await fs.readFile(file), output = path.join(path.dirname(root), 'render');
  await fs.writeFile(file, good.toString('utf8').replace('gap:1.2em', 'gap:9em'));
  await assert.rejects(readProject(root), /bound file hash mismatch/);
  await assert.rejects(renderProject(root, output, { preview: true }), /bound file hash mismatch/);
  await assert.rejects(fs.access(output), { code: 'ENOENT' }, 'nothing rendered');
  await fs.unlink(file);
  await assert.rejects(readProject(root), /bound file missing/);
  await fs.symlink(path.join(runtimeDir, 'title-card.json'), file); // Same bytes, but a link.
  await assert.rejects(readProject(root), /must be a regular file/);
  await fs.unlink(file);
  await fs.writeFile(file, good);
  await readProject(root);

  // Template rules run again on load: hash-consistent but invalid bytes are refused.
  // Raw (pre-normalization) bindings are accepted only while the current
  // normalization leaves them unchanged; otherwise they fail as a rule difference.
  const revision = path.join(root, 'revisions/000001.json'), doc = JSON.parse(await fs.readFile(revision, 'utf8'));
  const bind = async template => {
    const bytes = Buffer.from(JSON.stringify(template)), digest = sha(bytes);
    await fs.writeFile(path.join(root, `templates/${digest}.json`), bytes);
    doc.graphic_templates = [{ ...binding, sha256: digest, file: `templates/${digest}.json` }];
    await fs.writeFile(revision, `${JSON.stringify(doc, null, 2)}\n`);
  };
  const base = JSON.parse(good.toString('utf8'));
  await bind({ ...base, css: `${base.css}.gfx-title-card-title{zoom:.5}` });
  await assert.rejects(readProject(root), /fails template validation: .*could change text size/);
  await bind({ ...base, vars: { ...base.vars, subtitle: { ...base.vars.subtitle, font_em: 1.5 } } });
  await assert.rejects(readProject(root), /bound raw \(pre-normalization\) bytes differ from the current template rules/);
  await bind({ ...base, vars: { ...base.vars, subtitle: { ...base.vars.subtitle, font_em: 3.1 } } });
  assert.match(await htmlOf(root), /--fs-subtitle:3.1em/, 'raw bytes that normalization leaves unchanged render as bound');
});

test('a stricter minimum text rule changes the execution layer but not pinned revisions', async t => {
  const root = await project(t), before = await htmlOf(root, 1), original = runtimeTemplate('title-card').sha256;
  assert.match(before, /--fs-subtitle:3em/);
  const restore = useMinimumText(3.05);
  t.after(restore);
  assert.notEqual(runtimeTemplate('title-card').sha256, original, 'runtime bytes are re-normalized');
  assert.equal(await htmlOf(root, 1), before, 'the bound bytes are not rewritten by the new rule');
  // Adopting the new rule is an explicit rebind; the new binding stores normalized bytes.
  await editBatch(root, batch(1, [{ type: 'rebind_template', template: 'title-card' }]));
  const [binding] = (await readProject(root)).graphic_templates;
  assert.equal(binding.sha256, runtimeTemplate('title-card').sha256);
  assert.match(await htmlOf(root), /--fs-subtitle:3.05em/);
  restore();
  assert.match(await htmlOf(root), /--fs-subtitle:3.05em/, 'still rendered from its own bytes after the rule changes back');
  assert.equal(await htmlOf(root, 1), before);
});

test('historical revisions without bindings render with runtime templates and gain bindings on their next edit', async t => {
  const doc = JSON.parse(await fs.readFile(path.join(fixtures, 'valid/p2-packaging.json'), 'utf8'));
  Object.assign(doc, { revision: 1, parent_sha256: null, caption_font: { ...CAPTION_FONT } });
  assert.ok(!('graphic_templates' in doc));
  const root = await tempDir(t, 'template-legacy-');
  await fs.mkdir(path.join(root, 'revisions'));
  await fs.writeFile(path.join(root, 'revisions/000001.json'), `${JSON.stringify(doc, null, 2)}\n`);
  await installCaptionFont(root);
  const legacy = await readProject(root);
  assert.ok(compose(legacy).html.includes('gfx-lower-third'));
  assert.deepEqual(templateProvenance(legacy).map(p => [p.id, p.pinned, p.source]), [['lower-third', false, 'runtime']]);
  // It already renders the execution-layer bytes, so a rebind would change nothing.
  await assert.rejects(editBatch(root, batch(1, [{ type: 'rebind_template', template: 'lower-third' }])), /revision 1 is not pinned and already renders lower-third from the current template bytes \(no change\)/);
  const result = await editBatch(root, batch(1, [{ type: 'move_item', item_id: 'lower', start_frame: 2 }]));
  assert.match(result.notes.join(' '), /predates graphic template pinning; this revision binds lower-third/);
  assert.deepEqual(result.diff.graphic_templates.added.map(b => b.id), ['lower-third']);
  const pinned = await readProject(root);
  assert.equal(pinned.graphic_templates[0].sha256, runtimeTemplate('lower-third').sha256);
  assert.ok(!('graphic_templates' in await readProject(root, 1)), 'the historical revision is not rewritten');
  // Reverting to the unpinned revision binds what it renders with now: the
  // current execution-layer bytes, with a note.
  const restore = useRuntimeTemplates(await widerGap(t, 'lower-third'));
  const reverted = await editBatch(root, batch(2, [{ type: 'revert_to', revision: 1 }]));
  assert.match(reverted.notes.join(' '), /Revision 1 predates graphic template pinning; reverting to it binds lower-third to the current execution-layer template bytes/);
  assert.equal((await readProject(root)).graphic_templates[0].sha256, runtimeTemplate('lower-third').sha256);
  assert.notEqual(runtimeTemplate('lower-third').sha256, pinned.graphic_templates[0].sha256);
  restore();
  // Removing the last graphic drops its binding.
  const none = await editBatch(root, batch(3, [{ type: 'remove_item', item_id: 'lower' }]));
  assert.deepEqual(none.diff.graphic_templates.removed, ['lower-third']);
});

test('render directories receive the bound template files for independent replay', async t => {
  const root = await project(t, [card, strap]), destination = await tempDir(t, 'template-render-');
  const doc = await readProject(root);
  await copyBoundTemplates(root, destination, doc);
  for (const binding of doc.graphic_templates) {
    assert.deepEqual(await fs.readFile(path.join(destination, binding.file)), await fs.readFile(path.join(root, binding.file)));
  }
  assert.deepEqual(templateProvenance(doc).map(p => [p.id, p.pinned, p.source]), [['lower-third', true, 'project'], ['title-card', true, 'project']]);
  // Unbound documents cannot compile against bindings that were never loaded.
  const detached = structuredClone(doc);
  assert.throws(() => compose(detached), /pinned to this revision are not loaded/);
  assert.throws(() => validateV2(detached), /pinned to this revision are not loaded/, 'a clone never skips var typing silently');
});

test('an edit batch reads each bound template file once (the loaded base set is reused)', async t => {
  const root = await project(t, [card, strap]);
  const { promises } = await import('node:fs'), { syncBuiltinESMExports } = await import('node:module');
  const original = promises.readFile, reads = [];
  promises.readFile = function (file, ...rest) {
    if (String(file).startsWith(path.join(root, 'templates'))) reads.push(path.basename(String(file)));
    return original.call(this, file, ...rest);
  };
  syncBuiltinESMExports();
  t.after(() => { promises.readFile = original; syncBuiltinESMExports(); });
  await editBatch(root, batch(1, [{ type: 'move_item', item_id: 'strap', start_frame: 13 }]));
  assert.equal(reads.length, 2, `one read per binding, got ${reads.join(', ')}`);
});
