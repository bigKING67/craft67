import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';
import { createPhotoProject, readProject, editBatch } from '../project.mjs';
import { renderProject } from '../render.mjs';
import { sha256 } from '../../local-production/content-store.mjs';

const exec = promisify(execFile);
const cli = fileURLToPath(new URL('../cli.mjs', import.meta.url));
const tempRoot = await fs.realpath(os.tmpdir());
async function fixture(t) {
  const directory = await fs.mkdtemp(path.join(tempRoot, 'craft-photo-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const source = path.join(directory, '商品 原图.png');
  const rgb = Buffer.from(Array.from({ length: 96 * 64 * 3 }, (_, i) => (i * 19 + Math.floor(i / 71)) % 256));
  await sharp(rgb, { raw: { width: 96, height: 64, channels: 3 } }).png().toFile(source);
  const brief = { project_id: 'photo-test', source, headline: '光与影', brand: '品牌', caption: '产品视觉探索', canvas: { width: 640, height: 800 } };
  return { directory, root: path.join(directory, '新工程'), source, brief };
}
async function tree(root) {
  const result = {};
  for (const entry of await fs.readdir(root, { withFileTypes: true })) {
    const file = path.join(root, entry.name);
    result[entry.name] = entry.isDirectory() ? await tree(file) : sha256(await fs.readFile(file));
  }
  return result;
}
async function run(...args) { return JSON.parse((await exec(process.execPath, [cli, ...args])).stdout); }
async function photoPixels(png, photo) {
  return sharp(png).extract({ left: photo.x, top: photo.y, width: photo.width, height: photo.height }).ensureAlpha().raw().toBuffer();
}
const batch = (base_revision, operations) => ({ base_revision, author: 'human', summary: 'Photo workflow test', operations });

test('create-photo CLI dry-run writes nothing and predicts the created document; source may be removed after creation', async t => {
  const { directory, root, source, brief } = await fixture(t);
  const input = path.join(directory, 'brief.json');
  await fs.writeFile(input, JSON.stringify(brief));
  const before = await tree(directory);
  const planned = await run('create-photo', root, input, '--dry-run');
  assert.equal(planned.dry_run, true);
  assert.deepEqual(await tree(directory), before);
  const created = await run('create-photo', root, input);
  assert.equal(created.sha256, planned.sha256);
  assert.deepEqual(created.document, planned.document);
  assert.equal(created.document.title, brief.project_id);
  const asset = created.document.assets[0];
  assert.deepEqual(await fs.readFile(path.join(root, asset.file)), await fs.readFile(source));
  assert.deepEqual(created.document.objects.map(o => o.id), ['photo', 'brand', 'headline', 'caption']);
  assert.equal(created.document.objects[0].locked, true);
  await fs.rm(source);
  const moved = path.join(directory, '迁移工程');
  await fs.rename(root, moved);
  assert.equal((await run('read', moved)).sha256, created.sha256);
});

test('native photo pixels survive render, independent text edit and undo exactly', async t => {
  const { directory, root, brief } = await fixture(t);
  await createPhotoProject(root, brief);
  const initial = await readProject(root);
  const photo = initial.document.objects[0];
  const normalized = await sharp(path.join(root, initial.document.assets[0].render_file)).ensureAlpha().raw().toBuffer();
  const render = async name => {
    const output = path.join(directory, name);
    await renderProject(root, output);
    const png = await fs.readFile(path.join(output, 'image.png'));
    assert.deepEqual(await photoPixels(png, photo), normalized);
    return png;
  };
  const first = await render('initial');
  const before = await tree(root);
  await assert.rejects(editBatch(root, batch(1, [{ type: 'update_object', id: 'photo', patch: { x: 1 } }])), /locked/);
  assert.deepEqual(await tree(root), before);
  await editBatch(root, batch(1, [{ type: 'update_object', id: 'headline', patch: { text: '看见光' } }]));
  assert.notEqual(sha256(await render('edited')), sha256(first));
  await editBatch(root, batch(2, [{ type: 'revert_to', revision: 1 }]));
  assert.deepEqual(await render('undone'), first);
  const reopened = await readProject(root);
  assert.equal(reopened.document.revision, 3);
  assert.equal(reopened.document.objects[0].locked, true);
});

test('one photo project retains native pixels across square and portrait revisions, relocking and undo', async t => {
  const { directory, root, brief } = await fixture(t);
  const created = await createPhotoProject(root, brief);
  const original = created.document;
  const photo = original.objects.find(object => object.id === 'photo');
  const source = await sharp(path.join(root, original.assets[0].render_file)).ensureAlpha().raw().toBuffer();
  const edit = async operations => {
    const current = await readProject(root), before = await tree(root);
    const spec = batch(current.document.revision, operations);
    const planned = await editBatch(root, spec, { dryRun: true });
    assert.deepEqual(await tree(root), before);
    const result = await editBatch(root, spec);
    assert.equal(result.sha256, planned.sha256);
    return result;
  };
  const lock = locked => edit([{ type: 'update_object', id: 'photo', patch: { locked } }]);
  const renders = [];
  const render = async name => {
    const current = await readProject(root);
    const object = current.document.objects.find(value => value.id === 'photo');
    assert.equal(object.locked, true);
    const result = await renderProject(root, path.join(directory, name));
    const png = await fs.readFile(path.join(result.output, 'image.png'));
    assert.deepEqual(await photoPixels(png, object), source);
    renders.push({ revision: current.document.revision, sha256: result.receipt.outputs.png.sha256 });
  };
  await render('4x5');
  for (const [name, width, height] of [['square', 640, 640], ['9x16', 648, 1152]]) {
    const left = Math.floor(width / 16), offset = Math.floor((height - 320 - photo.height) / 2);
    const operations = [
      { type: 'set_canvas', canvas: { width, height, background: original.canvas.background } },
      { type: 'update_object', id: 'photo', patch: { x: Math.floor((width - photo.width) / 2), y: offset + 320 } },
      ...original.objects.filter(object => object.kind === 'text').map(object => ({
        type: 'update_object', id: object.id, patch: { x: left, y: object.y + offset, width: width - 2 * left },
      })),
    ];
    const before = await tree(root);
    await assert.rejects(editBatch(root, batch((await readProject(root)).document.revision, operations)), /locked/);
    assert.deepEqual(await tree(root), before);
    await lock(false);
    if (name === 'square') {
      const unlocked = await tree(root), current = await readProject(root);
      for (const dryRun of [true, false]) {
        await assert.rejects(editBatch(root, batch(current.document.revision, [
          { type: 'set_canvas', canvas: { width: 80, height: 64, background: '#ffffff' } },
        ]), { dryRun }), /Invalid object\.|Object outside canvas/);
        assert.deepEqual(await tree(root), unlocked);
      }
      assert.equal((await readProject(root)).document.objects.find(object => object.id === 'photo').locked, false);
      await lock(true);
      assert.equal((await readProject(root)).document.objects.find(object => object.id === 'photo').locked, true);
      await lock(false);
    }
    await edit(operations);
    await lock(true);
    await render(name);
    const current = (await readProject(root)).document;
    assert.deepEqual(current.assets, original.assets);
    assert.deepEqual(current.font, original.font);
    for (const text of original.objects.filter(object => object.kind === 'text')) {
      const actual = current.objects.find(object => object.id === text.id);
      for (const key of ['text', 'font_size', 'line_height', 'color', 'align']) assert.equal(actual[key], text[key]);
    }
  }
  const beforeUndo = await tree(root), last = await readProject(root);
  for (const dryRun of [true, false]) {
    await assert.rejects(editBatch(root, batch(last.document.revision, [{ type: 'revert_to', revision: 1 }]), { dryRun }), /locked/);
    assert.deepEqual(await tree(root), beforeUndo);
  }
  await lock(false);
  await edit([{ type: 'revert_to', revision: 1 }]);
  await lock(true);
  await render('restored');
  assert.equal(renders.at(-1).sha256, renders[0].sha256);
  for (const item of renders) {
    const result = await renderProject(root, path.join(directory, `reopen-${item.revision}`), { revision: item.revision });
    assert.equal(result.receipt.outputs.png.sha256, item.sha256);
  }
});

test('minimal brief uses the default canvas; EXIF orientation keeps native size and original encoded bytes', async t => {
  const { directory, root, source } = await fixture(t);
  const rotated = path.join(directory, 'oriented.jpg');
  await sharp(source).jpeg().withMetadata({ orientation: 6 }).toFile(rotated);
  const created = await createPhotoProject(root, { project_id: 'minimal', source: rotated, headline: '光', title: '照片起稿' });
  assert.deepEqual(created.document.canvas, { width: 1280, height: 1600, background: '#ffffff' });
  assert.equal(created.document.objects.length, 2);
  const photo = created.document.objects[0];
  assert.deepEqual([photo.width, photo.height, photo.x, photo.y], [64, 96, 608, 912]);
  assert.deepEqual(await fs.readFile(path.join(root, created.document.assets[0].file)), await fs.readFile(rotated));
  await renderProject(root, path.join(directory, 'render'));
  const expected = await sharp(rotated).rotate().toColourspace('srgb').ensureAlpha().raw().toBuffer();
  assert.deepEqual(await photoPixels(path.join(directory, 'render/image.png'), photo), expected);
});

test('invalid briefs and text fail before publication in dry-run and create', async t => {
  const { directory, root, brief } = await fixture(t);
  const cases = [
    [{ ...brief, unknown: true }, /unsupported field/],
    [{ ...brief, source: 'relative.png' }, /absolute local path/],
    [{ ...brief, headline: '' }, /Invalid headline/],
    [{ ...brief, caption: null }, /Invalid caption/],
    [{ ...brief, canvas: null }, /must be an object/],
    [{ ...brief, canvas: { width: 639, height: 800 } }, /canvas.width/],
    [{ ...brief, canvas: { width: 8192, height: 8192 } }, /pixel limit/],
    [{ ...brief, headline: '文'.repeat(100) }, /Text overflow: headline/],
    [{ ...brief, brand: '品牌'.repeat(50) }, /Text overflow: brand/],
    [{ ...brief, caption: '说明'.repeat(50) }, /Text overflow: caption/],
    [{ ...brief, headline: '\u{10ffff}' }, /glyph/i],
  ];
  const before = await tree(directory);
  for (const [input, pattern] of cases) {
    for (const dryRun of [true, false]) await assert.rejects(createPhotoProject(root, input, { dryRun }), pattern);
  }
  assert.deepEqual(await tree(directory), before);
});

test('oversized and transparent sources are rejected; an explicit larger canvas preserves dimensions', async t => {
  const { directory, root, brief } = await fixture(t);
  const large = path.join(directory, 'large.png'), alpha = path.join(directory, 'alpha.png');
  await sharp({ create: { width: 641, height: 481, channels: 3, background: '#fefdfc' } }).png().toFile(large);
  await sharp({ create: { width: 64, height: 64, channels: 4, background: { r: 255, g: 0, b: 0, alpha: 0.9 } } }).png().toFile(alpha);
  const before = await tree(directory);
  for (const dryRun of [true, false]) {
    await assert.rejects(createPhotoProject(root, { ...brief, source: large }, { dryRun }), /No automatic resize or crop/);
    await assert.rejects(createPhotoProject(root, { ...brief, source: alpha }, { dryRun }), /requires an opaque photo/);
  }
  assert.deepEqual(await tree(directory), before);
  const created = await createPhotoProject(root, { ...brief, source: large, canvas: { width: 641, height: 801 } });
  assert.deepEqual(created.layout.photo, { x: 0, y: 320, width: 641, height: 481, scale: 1, cropped: false });
});

test('occupied destinations, symlinks and bad CLI flags do not alter any existing data', async t => {
  const { directory, root, source, brief } = await fixture(t);
  await fs.mkdir(root);
  await fs.writeFile(path.join(root, 'keep.txt'), 'existing user data');
  const link = path.join(directory, 'source-link.png');
  await fs.symlink(source, link);
  const input = path.join(directory, 'brief.json');
  await fs.writeFile(input, JSON.stringify(brief));
  const before = await tree(directory);
  for (const dryRun of [true, false]) {
    await assert.rejects(createPhotoProject(root, brief, { dryRun }), /Project already exists/);
    await assert.rejects(createPhotoProject(path.join(directory, 'new'), { ...brief, source: link }, { dryRun }), /Symlink/);
  }
  await assert.rejects(run('create-photo', path.join(directory, 'new'), input, '--invalid'), /optionally --dry-run/);
  assert.deepEqual(await tree(directory), before);
});
