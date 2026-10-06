import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';
import { sha256 } from '../../local-production/content-store.mjs';
import { createProject, readProject, editBatch, encode, importRaster } from '../project.mjs';
import { renderProject } from '../render.mjs';
import { demoInput } from '../fixtures.mjs';

const exec = promisify(execFile);
const tempRoot = await fs.realpath(os.tmpdir());
async function fixture(t, prepare = () => {}) {
  const directory = await fs.mkdtemp(path.join(tempRoot, 'craft-image-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const input = await demoInput(path.join(directory, 'source'));
  prepare(input);
  const root = path.join(directory, 'project');
  await createProject(root, input);
  return { directory, root, input };
}
const batch = (base_revision, operations) => ({ base_revision, author: 'agent', summary: 'Test image edit', operations });
const update = (id, patch) => ({ type: 'update_object', id, patch });
async function tree(root) {
  const result = {};
  async function walk(directory) {
    for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
      const file = path.join(directory, entry.name);
      if (entry.isDirectory()) await walk(file);
      else result[path.relative(root, file)] = sha256(await fs.readFile(file));
    }
  }
  await walk(root); return result;
}
async function pixels(file) { return sharp(await fs.readFile(file)).ensureAlpha().raw().toBuffer({ resolveWithObject: true }); }

test('create copies original assets and font; project reopens without input files', async t => {
  const { directory, root, input } = await fixture(t);
  const before = await readProject(root);
  await assert.rejects(createProject(root, input), /Project already exists/);
  assert.equal((await readProject(root)).sha256, before.sha256);
  await fs.rm(path.join(directory, 'source'), { recursive: true });
  const after = await readProject(root);
  assert.equal(after.sha256, before.sha256);
  const moved = path.join(directory, 'moved-project');
  await fs.rename(root, moved);
  assert.equal((await readProject(moved)).sha256, before.sha256);
  await assert.rejects(createProject(moved, { project_id: 'x', title: 'x', assets: [], canvas: before.document.canvas, objects: before.document.objects }), /Project already exists/);
  const invalid = path.join(directory, 'invalid-project');
  await assert.rejects(createProject(invalid, { project_id: 'x', title: 'x', assets: [], canvas: before.document.canvas, objects: before.document.objects }), /Missing asset/);
  await assert.rejects(fs.lstat(invalid), { code: 'ENOENT' });
  assert.equal((await readProject(moved)).sha256, before.sha256);
});

test('batch validation and dry-run do not publish revisions or imported assets', async t => {
  const { root, input } = await fixture(t);
  const before = await tree(root);
  const extra = { ...input.assets[1], id: 'extra' };
  await assert.rejects(editBatch(root, batch(1, [{ type: 'add_asset', asset: extra }, update('product', { x: 9999 })])), /Invalid object.x/);
  assert.deepEqual(await tree(root), before);
  const planned = await editBatch(root, batch(1, [{ type: 'add_asset', asset: extra }, update('headline', { text: '中文改字' })]), { dryRun: true });
  assert.equal(planned.document.revision, 2);
  assert.equal(planned.dry_run, true);
  assert.deepEqual(await tree(root), before);
});

test('edit preflight rejects text overflow before publishing any revision or new asset', async t => {
  const { root, directory } = await fixture(t);
  const before = await tree(root);
  const source = path.join(directory, 'extra.png');
  await fs.writeFile(source, await sharp({ create: { width: 3, height: 3, channels: 3, background: '#123456' } }).png().toBuffer());
  const cases = [
    [{ text: '标题'.repeat(100) }, /Text overflow: headline/],
    [{ height: 10 }, /Text overflow: headline/],
    [{ width: 10 }, /narrower than glyph/],
    [{ font_size: 100 }, /Text overflow: headline/],
    [{ line_height: 2 }, /Text overflow: headline/],
  ];
  for (const [patch, error] of cases) for (const dryRun of [true, false]) {
    await assert.rejects(editBatch(root, batch(1, [
      { type: 'add_asset', asset: { id: 'extra', source } }, update('headline', patch),
    ]), { dryRun }), error);
    assert.deepEqual(await tree(root), before);
  }
  assert.equal((await readProject(root)).document.revision, 1);
});

test('text preflight measures the final batch and visible objects with the render engine', async t => {
  const { root, directory } = await fixture(t);
  const hidden = batch(1, [update('headline', { visible: false, height: 10 })]);
  await editBatch(root, hidden);
  const before = await tree(root);
  for (const dryRun of [true, false]) {
    await assert.rejects(editBatch(root, batch(2, [update('headline', { visible: true })]), { dryRun }), /Text overflow: headline/);
    assert.deepEqual(await tree(root), before);
  }
  // An intermediate operation may overflow; only the complete batch is published.
  const repair = batch(2, [update('headline', { visible: true }), update('headline', { text: '春日焕新\n轻盈日常', height: 220 })]);
  const planned = await editBatch(root, repair, { dryRun: true });
  assert.deepEqual(await tree(root), before);
  const edited = await editBatch(root, repair);
  assert.equal(edited.sha256, planned.sha256);
  const rendered = await renderProject(root, path.join(directory, 'repaired'));
  assert.equal(rendered.receipt.qa.text_measurements.headline.height, 180);
});

test('legacy overflowing text can be explicitly unlocked and repaired but not restored', async t => {
  const { root, directory } = await fixture(t, input => Object.assign(input.objects.find(object => object.id === 'headline'), { locked: true, height: 10 }));
  const unlock = batch(1, [update('headline', { locked: false })]);
  const before = await tree(root);
  const planned = await editBatch(root, unlock, { dryRun: true });
  assert.deepEqual(await tree(root), before);
  assert.equal((await editBatch(root, unlock)).sha256, planned.sha256);
  await editBatch(root, batch(2, [update('headline', { height: 220 })]));
  const repaired = await tree(root);
  for (const dryRun of [true, false]) {
    await assert.rejects(editBatch(root, batch(3, [{ type: 'revert_to', revision: 1 }]), { dryRun }), /Text overflow: headline/);
    assert.deepEqual(await tree(root), repaired);
  }
  assert.equal((await renderProject(root, path.join(directory, 'repaired'))).receipt.status, 'completed');
});

test('stale edits fail; concurrent batches on one base have exactly one winner', async t => {
  const { root } = await fixture(t);
  const attempts = await Promise.allSettled([
    editBatch(root, batch(1, [update('price', { text: '¥139' })])),
    editBatch(root, batch(1, [update('price', { text: '¥149' })])),
  ]);
  assert.equal(attempts.filter(value => value.status === 'fulfilled').length, 1);
  assert.match(attempts.find(value => value.status === 'rejected').reason.message, /Revision conflict/);
  assert.equal((await readProject(root)).document.revision, 2);
  const before = await tree(root);
  await assert.rejects(editBatch(root, batch(1, [update('price', { text: '¥9' })])), /Revision conflict/);
  assert.deepEqual(await tree(root), before);
});

test('asset/object add, geometry edit, reordering, removal and canvas adaptation survive reopening', async t => {
  const { root, input } = await fixture(t);
  const current = (await readProject(root)).document;
  const copy = { ...current.objects.find(object => object.id === 'product'), id: 'product-copy', asset_id: 'product-copy', x: 100, width: 100, height: 200 };
  await editBatch(root, batch(1, [{ type: 'add_asset', asset: { ...input.assets[1], id: 'product-copy' } }, { type: 'add_object', object: copy }]));
  const added = (await readProject(root)).document;
  assert.equal(added.objects.at(-1).asset_id, 'product-copy');
  assert.equal(added.assets.at(-1).sha256, current.assets.find(asset => asset.id === 'product').sha256);
  const ids = added.objects.map(object => object.id);
  [ids[2], ids[3]] = [ids[3], ids[2]];
  await editBatch(root, batch(2, [{ type: 'reorder_objects', ids }, { type: 'remove_object', id: 'product-copy' },
    { type: 'set_canvas', canvas: { width: 960, height: 1200, background: '#ffffff' } }, update('background', { width: 960, height: 1200 }), update('footer', { y: 1135 })]));
  const reopened = (await readProject(root)).document;
  assert.equal(reopened.objects[2].id, 'headline');
  assert.equal(reopened.objects.some(object => object.id === 'product-copy'), false);
  assert.deepEqual([reopened.canvas.width, reopened.canvas.height], [960, 1200]);
  assert.equal(reopened.objects.find(object => object.id === 'footer').y, 1135);
});

test('locks block edits/removal/reorder and cannot be bypassed in the same batch', async t => {
  const { root } = await fixture(t);
  await assert.rejects(editBatch(root, batch(1, [update('logo', { x: 1 })])), /locked/);
  await assert.rejects(editBatch(root, batch(1, [{ type: 'remove_object', id: 'logo' }])), /locked/);
  await assert.rejects(editBatch(root, batch(1, [update('logo', { locked: false }), update('logo', { x: 1 })])), /isolated/);
  await assert.rejects(editBatch(root, batch(1, [update('logo', { locked: false, x: 1 })])), /isolated/);
  const doc = (await readProject(root)).document;
  await assert.rejects(editBatch(root, batch(1, [{ type: 'reorder_objects', ids: doc.objects.map(object => object.id).reverse() }])), /locked/);
  await editBatch(root, batch(1, [update('logo', { locked: false })]));
  await editBatch(root, batch(2, [update('logo', { x: 10 })]));
  assert.equal((await readProject(root)).document.objects.find(object => object.id === 'logo').x, 10);
});

test('undo creates a new revision, keeps current locks and rejects reverting protected changes', async t => {
  const { root } = await fixture(t);
  await editBatch(root, batch(1, [update('price', { text: '¥139' })]));
  await editBatch(root, batch(2, [update('product', { locked: true })]));
  const undone = await editBatch(root, batch(3, [{ type: 'revert_to', revision: 1 }]));
  assert.equal(undone.document.revision, 4);
  assert.equal(undone.document.objects.find(object => object.id === 'price').text, '¥129');
  assert.equal(undone.document.objects.find(object => object.id === 'product').locked, true);
  await editBatch(root, batch(4, [update('product', { locked: false })]));
  await editBatch(root, batch(5, [update('product', { x: 570 })]));
  await editBatch(root, batch(6, [update('product', { locked: true })]));
  await assert.rejects(editBatch(root, batch(7, [{ type: 'revert_to', revision: 1 }])), /Revert would change locked/);
  assert.equal((await readProject(root)).document.revision, 7);
});

test('undo cannot reorder a currently locked object; explicit unlock permits recovery', async t => {
  const { root } = await fixture(t);
  const original = (await readProject(root)).document.objects.map(object => object.id);
  const reordered = [...original], a = original.indexOf('product'), b = original.indexOf('headline');
  [reordered[a], reordered[b]] = [reordered[b], reordered[a]];
  await editBatch(root, batch(1, [{ type: 'reorder_objects', ids: reordered }]));
  await editBatch(root, batch(2, [update('product', { locked: true })]));
  const before = await tree(root);
  await assert.rejects(editBatch(root, batch(3, [{ type: 'reorder_objects', ids: original }])), /locked/);
  for (const dryRun of [true, false]) {
    await assert.rejects(editBatch(root, batch(3, [{ type: 'revert_to', revision: 1 }]), { dryRun }), /locked/);
    assert.deepEqual(await tree(root), before);
  }
  await editBatch(root, batch(3, [update('product', { locked: false })]));
  const restored = await editBatch(root, batch(4, [{ type: 'revert_to', revision: 1 }]));
  assert.deepEqual(restored.document.objects.map(object => object.id), original);
  assert.equal(restored.document.objects.find(object => object.id === 'product').locked, false);
  assert.equal((await readProject(root)).sha256, restored.sha256);
});

test('asset, font, ancestry and symlink tampering fail closed', async t => {
  for (const mode of ['asset', 'font', 'history', 'symlink']) {
    const { root } = await fixture(t);
    const doc = (await readProject(root)).document;
    if (mode === 'history') {
      await editBatch(root, batch(1, [update('price', { text: '¥139' })]));
      const file = path.join(root, 'revisions/000001.json');
      const previous = JSON.parse(await fs.readFile(file, 'utf8')); previous.objects.find(object => object.id === 'price').text = '¥1';
      await fs.writeFile(file, encode(previous));
      await assert.rejects(readProject(root), /digest chain/);
    } else {
      const file = path.join(root, mode === 'font' ? doc.font.file : doc.assets[0].file);
      if (mode === 'symlink') {
        const copy = `${file}.copy`; await fs.rename(file, copy); await fs.symlink(copy, file);
        await assert.rejects(readProject(root), /Symlink/);
      } else {
        const handle = await fs.open(file, 'r+'); await handle.write(Buffer.from([0]), 0, 1, 0); await handle.close();
        await assert.rejects(readProject(root), /digest mismatch/);
      }
    }
  }
});

test('untrusted raster boundary rejects URL/SVG/animation and preserves oriented JPEG originals', async t => {
  const { directory } = await fixture(t);
  await assert.rejects(importRaster({ id: 'remote', source: 'https://example.com/product.png' }), /local file/);
  const svg = path.join(directory, 'unsafe.svg');
  await fs.writeFile(svg, '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"/>');
  await assert.rejects(importRaster({ id: 'svg', source: svg }), /single-frame PNG/);
  const gif = Buffer.from('47494638396101000100800000ff000000000021f90400010000002c000000000100010000020244010021f90400010000002c00000000010001000002024c01003b', 'hex');
  const animated = await sharp(gif, { animated: true }).webp().toBuffer();
  assert.equal((await sharp(animated).metadata()).pages, 2);
  const animation = path.join(directory, 'animated.webp'); await fs.writeFile(animation, animated);
  await assert.rejects(importRaster({ id: 'animation', source: animation }), /single-frame/);
  const jpeg = await sharp({ create: { width: 30, height: 10, channels: 3, background: '#abcabc' } }).jpeg().withMetadata({ orientation: 6 }).toBuffer();
  const file = path.join(directory, 'oriented.jpg'); await fs.writeFile(file, jpeg);
  const imported = await importRaster({ id: 'oriented', source: file });
  assert.equal(imported.asset.sha256, sha256(jpeg));
  assert.deepEqual([imported.asset.width, imported.asset.height], [10, 30]);
});

test('out-of-bounds/unsupported fields/missing glyphs fail without changing the project', async t => {
  const { root } = await fixture(t);
  const before = await tree(root);
  for (const patch of [{ x: 980 }, { rotation: 30 }, { text: 'missing\u{10FFFF}' }]) {
    await assert.rejects(editBatch(root, batch(1, [update(patch.text ? 'headline' : 'product', patch)])));
    assert.deepEqual(await tree(root), before);
  }
  await assert.rejects(editBatch(root, batch(1, [{ type: 'set_canvas', canvas: { width: 8192, height: 8192, background: '#ffffff' } }])), /pixel limit/);
  await assert.rejects(editBatch(root, batch(1, [{ type: 'constructor' }])), /Unsupported operation/);
  await assert.rejects(editBatch(root, batch(1, [{ type: 'add_object', object: { id: 'invalid', kind: 'constructor' } }])), /Unsupported object kind/);
  assert.deepEqual(await tree(root), before);
});

test('real Chinese rendering: copy/price change preserves all pixels outside those boxes and logo pixels', async t => {
  const { root, directory } = await fixture(t);
  const first = await renderProject(root, path.join(directory, 'before'));
  await editBatch(root, batch(1, [update('headline', { text: '自在新生\n轻盈日常' }), update('price', { text: '¥139' })]));
  const second = await renderProject(root, path.join(directory, 'after'));
  const a = await pixels(path.join(first.output, 'image.png')), b = await pixels(path.join(second.output, 'image.png'));
  assert.deepEqual(a.info, b.info);
  let changes = 0;
  for (let y = 0; y < a.info.height; y++) for (let x = 0; x < a.info.width; x++) {
    const at = (y * a.info.width + x) * 4;
    if (!a.data.subarray(at, at + 4).equals(b.data.subarray(at, at + 4))) {
      changes++;
      assert.ok((x >= 70 && x < 550 && y >= 202 && y < 422) || (x >= 75 && x < 515 && y >= 590 && y < 680), `Unexpected changed pixel ${x},${y}`);
    }
  }
  assert.ok(changes > 1000, 'Chinese text/price actually changed');
  assert.equal(second.receipt.qa.font_glyphs, 'PASS');
  assert.equal(second.receipt.visual_quality, 'UNVERIFIED');
  assert.match(await fs.readFile(path.join(second.output, 'image.svg'), 'utf8'), /<path/);
});

test('preview is a resize of the same rendered PNG; undo/reopen PNG bytes are identical', async t => {
  const { root, directory } = await fixture(t);
  const first = await renderProject(root, path.join(directory, 'initial'));
  const preview = await renderProject(root, path.join(directory, 'preview'), { previewMax: 640 });
  const expected = await sharp(await fs.readFile(path.join(first.output, 'image.png'))).resize({ width: 640, height: 640, fit: 'inside', withoutEnlargement: true }).png({ compressionLevel: 9 }).toBuffer();
  assert.equal(preview.receipt.outputs.png.sha256, sha256(expected));
  await editBatch(root, batch(1, [update('product', { x: 555, y: 227, width: 390, height: 602 }), update('headline', { y: 176 })]));
  await renderProject(root, path.join(directory, 'changed'));
  await editBatch(root, batch(2, [{ type: 'revert_to', revision: 1 }]));
  const undo = await renderProject(root, path.join(directory, 'undo'));
  assert.equal(undo.receipt.outputs.png.sha256, first.receipt.outputs.png.sha256);
  const reopened = await renderProject(root, path.join(directory, 'reopen'));
  assert.equal(reopened.receipt.outputs.png.sha256, first.receipt.outputs.png.sha256);
  await assert.rejects(renderProject(root, first.output), /EEXIST/);
  assert.equal(sha256(await fs.readFile(path.join(first.output, 'image.png'))), first.receipt.outputs.png.sha256);
});

test('explicit Chinese newline equals two independently positioned text lines in actual pixels', async t => {
  const { root, directory } = await fixture(t);
  const first = await renderProject(root, path.join(directory, 'multiline'));
  const original = (await readProject(root)).document.objects.find(object => object.id === 'headline');
  const [line1, line2] = original.text.split('\n');
  const lineHeight = original.font_size * original.line_height;
  await editBatch(root, batch(1, [update('headline', { text: line1, height: lineHeight }),
    { type: 'add_object', object: { ...original, id: 'headline-line2', text: line2, y: original.y + lineHeight, height: lineHeight } }]));
  const explicit = await renderProject(root, path.join(directory, 'two-objects'));
  assert.equal(explicit.receipt.outputs.png.sha256, first.receipt.outputs.png.sha256);
  assert.equal(first.receipt.qa.text_measurements.headline.height, lineHeight * 2);
});

test('image contain/cover/fill produce their declared geometry in real pixels', async t => {
  const directory = await fs.mkdtemp(path.join(tempRoot, 'craft-image-fit-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const red = await sharp({ create: { width: 40, height: 40, channels: 3, background: '#ff0000' } }).png().toBuffer();
  const blue = await sharp({ create: { width: 40, height: 40, channels: 3, background: '#0000ff' } }).png().toBuffer();
  const source = path.join(directory, 'tile.png');
  await fs.writeFile(source, await sharp({ create: { width: 80, height: 40, channels: 3, background: '#ffffff' } }).composite([{ input: red, left: 0, top: 0 }, { input: blue, left: 40, top: 0 }]).png().toBuffer());
  const root = path.join(directory, 'project');
  await createProject(root, { project_id: 'fit', title: 'Image fit test', canvas: { width: 100, height: 100, background: '#ffffff' }, assets: [{ id: 'tile', source }],
    objects: [{ id: 'tile', kind: 'image', locked: false, visible: true, x: 10, y: 10, width: 80, height: 80, opacity: 1, asset_id: 'tile', fit: 'contain' }] });
  const rgb = (data, x, y) => [...data.subarray((y * 100 + x) * 4, (y * 100 + x) * 4 + 3)];
  for (const [index, fit] of ['contain', 'cover', 'fill'].entries()) {
    if (index) await editBatch(root, batch(index, [update('tile', { fit })]));
    const rendered = await renderProject(root, path.join(directory, fit));
    const { data } = await pixels(path.join(rendered.output, 'image.png'));
    assert.deepEqual(rgb(data, 30, 20), fit === 'contain' ? [255, 255, 255] : [255, 0, 0]);
    assert.deepEqual(rgb(data, 30, 40), [255, 0, 0]);
    assert.deepEqual(rgb(data, 70, 40), [0, 0, 255]);
  }
});

test('text overflow/narrow glyph/cancel/timeout leave failure receipts, no output images and unchanged source', async t => {
  // General create can load legacy structurally valid but overflowing layouts.
  // Render must still reject them independently of edit-time preflight.
  const { root, directory } = await fixture(t, input => { input.objects.find(object => object.id === 'headline').height = 10; });
  const before = await tree(root);
  await assert.rejects(renderProject(root, path.join(directory, 'overflow')), /Text overflow/);
  const receipt = JSON.parse(await fs.readFile(path.join(directory, 'overflow/receipt.json'), 'utf8'));
  assert.equal(receipt.status, 'failed'); assert.equal(receipt.outputs, undefined);
  await assert.rejects(fs.stat(path.join(directory, 'overflow/image.png')), /ENOENT/);
  assert.deepEqual(await tree(root), before);
  const narrow = await fixture(t, input => { input.objects.find(object => object.id === 'headline').width = 10; });
  const narrowBefore = await tree(narrow.root);
  await assert.rejects(renderProject(narrow.root, path.join(directory, 'narrow')), /narrower than glyph/);
  assert.deepEqual(await tree(narrow.root), narrowBefore);
  await editBatch(root, batch(1, [update('headline', { height: 220 })]));
  const unchanged = await tree(root);
  const controller = new AbortController(); controller.abort();
  await assert.rejects(renderProject(root, path.join(directory, 'cancelled'), { signal: controller.signal }), /cancelled/);
  assert.equal(JSON.parse(await fs.readFile(path.join(directory, 'cancelled/receipt.json'), 'utf8')).status, 'cancelled');
  await assert.rejects(renderProject(root, path.join(directory, 'timeout'), { timeoutMs: 1 }), /timed out/);
  assert.equal(JSON.parse(await fs.readFile(path.join(directory, 'timeout/receipt.json'), 'utf8')).status, 'failed');
  for (const output of ['cancelled', 'timeout']) assert.deepEqual(await fs.readdir(path.join(directory, output)), ['receipt.json']);
  assert.deepEqual(await tree(root), unchanged);
});

test('CLI commands create/read/edit/dry-run/render/preview share the same document operations', async t => {
  const directory = await fs.mkdtemp(path.join(tempRoot, 'craft-image-cli-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const input = await demoInput(path.join(directory, 'source'));
  const root = path.join(directory, 'project'), createFile = path.join(directory, 'create.json'), editFile = path.join(directory, 'edit.json');
  await fs.writeFile(createFile, encode(input)); await fs.writeFile(editFile, encode(batch(1, [update('price', { text: '¥139' })])));
  const cli = fileURLToPath(new URL('../cli.mjs', import.meta.url));
  const run = async (...args) => JSON.parse((await exec(process.execPath, [cli, ...args], { timeout: 30000, maxBuffer: 1_000_000 })).stdout);
  assert.equal((await run('create', root, createFile)).document.revision, 1);
  assert.equal((await run('edit', root, editFile, '--dry-run')).dry_run, true);
  assert.equal((await run('read', root)).document.revision, 1);
  assert.equal((await run('edit', root, editFile)).document.revision, 2);
  assert.equal((await run('read', root, '1')).document.revision, 1);
  assert.equal((await run('render', root, path.join(directory, 'export'))).receipt.status, 'completed');
  assert.equal((await run('preview', root, path.join(directory, 'preview'))).receipt.outputs.png.width, 640);
});

test('CLI historical render and preview bind the selected revision without changing current layout or locks', async t => {
  const { root, directory } = await fixture(t);
  const original = await readProject(root);
  const initial = await renderProject(root, path.join(directory, 'initial'));
  const initialPreview = await renderProject(root, path.join(directory, 'initial-preview'), { previewMax: 640 });
  await editBatch(root, batch(1, [update('price', { text: '¥139' }),
    { type: 'set_canvas', canvas: { width: 1200, height: 1200, background: '#ffffff' } }]));
  const current = await readProject(root), before = await tree(root);
  const cli = fileURLToPath(new URL('../cli.mjs', import.meta.url));
  const run = async (...args) => JSON.parse((await exec(process.execPath, [cli, ...args], { timeout: 30000, maxBuffer: 1_000_000 })).stdout);
  for (const [command, expected] of [['render', initial], ['preview', initialPreview]]) {
    const result = await run(command, root, path.join(directory, `history-${command}`), '--revision', '1');
    assert.equal(result.receipt.revision, 1);
    assert.equal(result.receipt.project_sha256, original.sha256);
    assert.equal(result.receipt.outputs.png.sha256, expected.receipt.outputs.png.sha256);
    assert.deepEqual(result.receipt.canvas, original.document.canvas);
    assert.deepEqual(await tree(root), before);
  }
  const latest = await run('render', root, path.join(directory, 'latest'));
  assert.equal(latest.receipt.revision, 2);
  assert.equal(latest.receipt.project_sha256, current.sha256);
  assert.equal(latest.receipt.outputs.png.width, 1200);
  assert.notEqual(latest.receipt.outputs.png.sha256, initial.receipt.outputs.png.sha256);
  assert.equal((await run('read', root)).sha256, current.sha256);
  assert.deepEqual(await tree(root), before);
});

test('CLI revision option rejects invalid and extra arguments before creating output', async t => {
  const { root, directory } = await fixture(t), before = await tree(root);
  const cli = fileURLToPath(new URL('../cli.mjs', import.meta.url));
  const options = [[], ['0'], ['-1'], ['1.5'], ['NaN'], ['1e0'], ['0x1'], [''], ['9007199254740993'], ['2'], ['1', '--revision', '1'], ['1', 'extra']];
  let index = 0;
  for (const command of ['render', 'preview']) for (const value of options) {
    const output = path.join(directory, `rejected-${index++}`);
    await assert.rejects(exec(process.execPath, [cli, command, root, output, '--revision', ...value]), error => {
      assert.equal(error.code, 1);
      assert.equal(JSON.parse(error.stderr).status, 'failed');
      return true;
    });
    await assert.rejects(fs.stat(output), { code: 'ENOENT' });
    assert.deepEqual(await tree(root), before);
  }
  await assert.rejects(exec(process.execPath, [cli, 'read', root, '1', '--revision', '1']), /Usage:/);
  for (const flag of ['--unknown', '']) {
    const output = path.join(directory, `unknown-${index++}`);
    await assert.rejects(exec(process.execPath, [cli, 'render', root, output, flag]), /optionally --revision/);
    await assert.rejects(fs.stat(output), { code: 'ENOENT' });
  }
  assert.deepEqual(await tree(root), before);
});

test('an interrupted create is reported as incomplete rather than a broken history', async t => {
  const directory = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'craft-incomplete-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const root = path.join(directory, 'project');
  await fs.mkdir(root); for (const folder of ['assets', 'fonts', 'revisions']) await fs.mkdir(path.join(root, folder));
  await assert.rejects(readProject(root), /Incomplete project/);
});

test('OS alias directories under the filesystem root are accepted; nested symlinks are still refused', async t => {
  const alias = os.tmpdir(); // /var/folders/... on macOS, where /var -> /private/var
  const directory = await fs.mkdtemp(path.join(alias, 'craft-alias-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const input = await demoInput(path.join(directory, 'source'));
  const root = path.join(directory, 'project');
  const created = await createProject(root, input);
  assert.equal((await readProject(root)).sha256, created.sha256);
  await fs.symlink(root, path.join(directory, 'linked'));
  await assert.rejects(readProject(path.join(directory, 'linked')), /Symlink paths are unsupported/);
});

test('editing past the revision limit fails with an actionable message', async t => {
  const { root } = await fixture(t);
  const { LIMITS } = await import('../document.mjs');
  const revisions = path.join(root, 'revisions');
  let previous = await fs.readFile(path.join(revisions, '000001.json')), doc = JSON.parse(previous);
  for (let revision = 2; revision <= LIMITS.revisions; revision++) {
    doc = { ...doc, revision, parent_sha256: sha256(previous), change: { author: 'agent', summary: 'Filler', operations: ['update_object'] } };
    previous = encode(doc);
    await fs.writeFile(path.join(revisions, `${String(revision).padStart(6, '0')}.json`), previous);
  }
  await assert.rejects(editBatch(root, { base_revision: LIMITS.revisions, author: 'agent', summary: 'One more', operations: [{ type: 'update_object', id: 'headline', patch: { y: 90 } }] }), /Revision limit reached/);
});
