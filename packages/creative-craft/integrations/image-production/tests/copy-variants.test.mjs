import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import sharp from 'sharp';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { createPhotoProject, readProject, editBatch } from '../project.mjs';
import { copyVariants } from '../copy-variants.mjs';
import { sha256 } from '../../local-production/content-store.mjs';
const exec = promisify(execFile);
async function tree(root) {
  const result = {};
  for (const entry of await fs.readdir(root, { withFileTypes: true })) {
    const file = path.join(root, entry.name);
    result[entry.name] = entry.isDirectory() ? await tree(file) : sha256(await fs.readFile(file));
  }
  return result;
}
async function fixture(t) {
  const directory = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'craft-文案 同步-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const source = path.join(directory, 'source.png'), root = path.join(directory, 'project');
  await sharp({ create: { width: 96, height: 64, channels: 3, background: '#b98645' } }).png().toFile(source);
  const a = await createPhotoProject(root, { project_id: 'variants', source, headline: '原版', brand: '品牌', caption: '商品', canvas: { width: 640, height: 800 } });
  const b = await editBatch(root, { base_revision: 1, author: 'human', summary: 'Taller layout', operations: [{ type: 'set_canvas', canvas: { width: 640, height: 960, background: '#ffffff' } }] });
  return { directory, root, input: { output: path.join(directory, 'output'), variants: [{ name: 'square', revision: 1, sha256: a.sha256 }, { name: 'tall', revision: 2, sha256: b.sha256 }], updates: [{ id: 'headline', text: '新的标题' }] } };
}
test('CLI shares copy across editable layouts and leaves source, assets and geometry intact', async t => {
  const { directory, root, input } = await fixture(t), before = await tree(root);
  const file = path.join(directory, 'input.json'); await fs.writeFile(file, JSON.stringify(input));
  const result = JSON.parse((await exec(process.execPath, [fileURLToPath(new URL('../cli.mjs', import.meta.url)), 'copy-variants', root, file])).stdout);
  assert.equal(result.manifest.variants.length, 2);
  for (const variant of result.manifest.variants) {
    const original = await readProject(root, { revision: variant.source.revision });
    const project = await readProject(path.join(input.output, variant.project));
    assert.equal(project.document.revision, 2);
    assert.deepEqual(project.document.canvas, original.document.canvas);
    assert.deepEqual(project.document.assets, original.document.assets);
    for (const object of project.document.objects) {
      const previous = original.document.objects.find(v => v.id === object.id);
      assert.deepEqual(object, object.id === 'headline' ? { ...previous, text: '新的标题' } : previous);
    }
    const png = await fs.readFile(path.join(input.output, variant.export, 'image.png'));
    assert.equal(sha256(png), variant.png_sha256);
    const photo = project.document.objects.find(v => v.id === 'photo');
    const asset = project.document.assets.find(v => v.id === photo.asset_id);
    assert.deepEqual(await sharp(png).extract({ left: photo.x, top: photo.y, width: photo.width, height: photo.height }).ensureAlpha().raw().toBuffer(), await sharp(path.join(root, asset.render_file)).ensureAlpha().raw().toBuffer());
  }
  assert.deepEqual(await tree(root), before);
});
test('later-layout text overflow rolls back earlier exports and leaves original untouched', async t => {
  const { root, input } = await fixture(t);
  const narrow = await editBatch(root, { base_revision: 2, author: 'human', summary: 'Narrow title', operations: [{ type: 'update_object', id: 'headline', patch: { width: 150 } }] });
  input.variants[1] = { name: 'narrow', revision: 3, sha256: narrow.sha256 };
  const before = await tree(root);
  await assert.rejects(copyVariants(root, input), /text|fit|overflow/i);
  await assert.rejects(fs.stat(input.output), { code: 'ENOENT' });
  assert.deepEqual(await tree(root), before);
});
test('bindings, identities, text-only scope, destination ownership and cancellation fail closed', async t => {
  const { root, input } = await fixture(t), before = await tree(root);
  const cases = [
    value => value.variants[0].sha256 = '0'.repeat(64),
    value => value.variants[1].name = 'SQUARE',
    value => value.variants[0].name = '../escape',
    value => value.updates[0].id = 'missing',
    value => value.updates[0].id = 'photo',
    value => value.updates[0].width = 20,
    value => value.updates.push(value.updates[0]),
    value => value.output = path.join(root, 'nested'),
  ];
  for (const change of cases) {
    const value = structuredClone(input); change(value);
    await assert.rejects(copyVariants(root, value));
    await assert.rejects(fs.stat(input.output), { code: 'ENOENT' });
  }
  await assert.rejects(copyVariants(root, input, { signal: AbortSignal.abort() }), /cancelled/);
  await fs.mkdir(input.output); await fs.writeFile(path.join(input.output, 'keep'), 'user data');
  await assert.rejects(copyVariants(root, input), { code: 'EEXIST' });
  assert.equal(await fs.readFile(path.join(input.output, 'keep'), 'utf8'), 'user data');
  assert.deepEqual(await tree(root), before);
});
test('locked text stays locked and mid-run cancellation removes only owned outputs', async t => {
  const { root, input } = await fixture(t);
  const locked = await editBatch(root, { base_revision: 2, author: 'human', summary: 'Lock title', operations: [{ type: 'update_object', id: 'headline', patch: { locked: true } }] });
  const lockInput = structuredClone(input); lockInput.variants[1] = { name: 'locked', revision: 3, sha256: locked.sha256 };
  await assert.rejects(copyVariants(root, lockInput), /unlocked text/);
  await assert.rejects(fs.stat(input.output), { code: 'ENOENT' });
  const controller = new AbortController();
  const timer = setInterval(async () => { try { await fs.stat(path.join(input.output, 'square/project')); controller.abort(); } catch {} }, 5);
  try { await assert.rejects(copyVariants(root, input, { signal: controller.signal }), /cancel/i); }
  finally { clearInterval(timer); }
  await assert.rejects(fs.stat(input.output), { code: 'ENOENT' });
  assert.equal((await readProject(root)).sha256, locked.sha256);
});

test('outputs inside the source project are refused, including case-variant spellings', async t => {
  const { directory, root, input } = await fixture(t), before = await tree(root);
  const { renderProject } = await import('../render.mjs');
  await assert.rejects(renderProject(root, path.join(root, 'revisions', '000099.json')), /outside the project/);
  await assert.rejects(copyVariants(root, { ...input, output: path.join(root, 'variants') }), /outside the project/);
  const alias = path.join(directory, 'PROJECT');
  if (await fs.stat(alias).then(() => true, () => false)) await assert.rejects(copyVariants(root, { ...input, output: path.join(alias, 'variants') }), /outside the project/);
  assert.deepEqual(await tree(root), before); await readProject(root);
});

test('a large photo whose normalized PNG exceeds the source byte limit still produces variants', async t => {
  const { directory } = await fixture(t);
  const source = path.join(directory, 'large.jpg'), root = path.join(directory, 'large-project');
  await sharp({ create: { width: 3000, height: 3000, channels: 3, noise: { type: 'gaussian', mean: 128, sigma: 60 } } }).jpeg({ quality: 90 }).toFile(source);
  const created = await createPhotoProject(root, { project_id: 'large', source, headline: '大图', canvas: { width: 3000, height: 3400 } });
  const project = await readProject(root);
  assert.ok((await fs.stat(path.join(root, project.document.assets[0].render_file))).size > 20_000_000);
  const result = await copyVariants(root, { output: path.join(directory, 'large-output'), variants: [{ name: 'only', revision: 1, sha256: created.sha256 }], updates: [{ id: 'headline', text: '新的大图' }] });
  assert.equal(result.manifest.variants.length, 1);
});
