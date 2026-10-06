// Acceptance of existing RGBA import/render/edit behavior. This synthetic
// matte is known ground truth, not segmentation or optical glass recovery.
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import assert from 'node:assert/strict';
import sharp from 'sharp';
import { createProject, readProject, editBatch, encode } from './project.mjs';
import { stageCandidate, acceptCandidate } from './candidates.mjs';
import { renderProject } from './render.mjs';
import { sha256 } from '../local-production/content-store.mjs';

const size = { width: 128, height: 192 };
const light = [246, 244, 239], dark = [23, 34, 49];
const gold = [226, 164, 62, 112], label = [238, 237, 221, 255];
const hex = rgb => `#${rgb.map(value => value.toString(16).padStart(2, '0')).join('')}`;
const update = patch => ({ type: 'update_object', id: 'product', patch });
const over = (rgba, background, opacity = 1) => rgba.slice(0, 3).map((value, channel) =>
  Math.round(value * rgba[3] / 255 * opacity + background[channel] * (1 - rgba[3] / 255 * opacity)));

async function fixture(directory) {
  await fs.mkdir(directory);
  const data = Buffer.alloc(size.width * size.height * 4);
  // Poison hidden RGB to catch compositing that treats transparent pixels as
  // visible or interpolates straight RGB instead of premultiplied color.
  for (let at = 0; at < data.length; at += 4) data.set([255, 0, 255, 0], at);
  const rect = (x, y, width, height, rgba) => {
    for (let row = y; row < y + height; row++) for (let col = x; col < x + width; col++) data.set(rgba, (row * size.width + col) * 4);
  };
  rect(28, 52, 72, 124, gold);
  for (let col = 0; col < 4; col++) {
    rect(24 + col, 52, 1, 124, [...gold.slice(0, 3), col * 28]);
    rect(103 - col, 52, 1, 124, [...gold.slice(0, 3), col * 28]);
  }
  rect(44, 16, 44, 36, [190, 196, 202, 255]);
  rect(24, 16, 64, 12, [190, 196, 202, 255]);
  rect(36, 112, 56, 40, label);
  rect(44, 124, 40, 4, [32, 38, 45, 255]);
  rect(44, 138, 40, 4, [32, 38, 45, 255]);
  const product = path.join(directory, 'product.png');
  const background = path.join(directory, 'background.png'), proposed = path.join(directory, 'dark.png');
  await fs.writeFile(product, await sharp(data, { raw: { ...size, channels: 4 } }).png().toBuffer(), { flag: 'wx' });
  const neutralData = Buffer.from(data);
  for (let at = 0; at < neutralData.length; at += 4) if (neutralData[at + 3] === 0) neutralData.fill(0, at, at + 3);
  const neutral = path.join(directory, 'hidden-rgb-neutral.png');
  await fs.writeFile(neutral, await sharp(neutralData, { raw: { ...size, channels: 4 } }).png().toBuffer(), { flag: 'wx' });
  for (const [file, rgb] of [[background, light], [proposed, dark]]) {
    await fs.writeFile(file, await sharp({ create: { width: 384, height: 384, channels: 4, background: hex(rgb) } }).png().toBuffer(), { flag: 'wx' });
  }
  const object = { id: 'product', kind: 'image', locked: false, visible: true, x: 128, y: 112, width: 128, height: 192, opacity: 1, asset_id: 'product', fit: 'contain' };
  const input = { project_id: 'alpha-acceptance', title: '已知透明度合成验收', canvas: { width: 384, height: 384, background: hex(light) },
    assets: [{ id: 'background', source: background }, { id: 'product', source: product }], objects: [
      { ...object, id: 'background', x: 0, y: 0, width: 384, height: 384, asset_id: 'background', fit: 'fill' }, object,
      { id: 'caption', kind: 'text', locked: true, visible: true, x: 16, y: 16, width: 352, height: 30, opacity: 1,
        text: 'RGBA 工程验收 · 合成素材', font_size: 18, color: '#8a8a8a', align: 'left', line_height: 1.25 },
    ] };
  return { input, product, proposed, neutral, data };
}

async function pixels(file) { return sharp(await fs.readFile(file)).ensureAlpha().raw().toBuffer(); }
function rgbAt(data, x, y) { return [...data.subarray((y * 384 + x) * 4, (y * 384 + x) * 4 + 3)]; }
function close(actual, expected, tolerance, description) {
  const error = Math.max(...actual.map((value, index) => Math.abs(value - expected[index])));
  assert.ok(error <= tolerance, `${description}: ${actual} != ${expected}; error ${error}`);
  return error;
}
function checkIdentity(rendered, source, background) {
  const counts = { transparent: 0, translucent: 0, opaque: 0, max_channel_error: 0 };
  for (let y = 0; y < size.height; y++) for (let x = 0; x < size.width; x++) {
    const rgba = [...source.subarray((y * size.width + x) * 4, (y * size.width + x) * 4 + 4)];
    counts[rgba[3] === 0 ? 'transparent' : rgba[3] === 255 ? 'opaque' : 'translucent']++;
    counts.max_channel_error = Math.max(counts.max_channel_error,
      close(rgbAt(rendered, x + 128, y + 112), over(rgba, background), 1, `identity pixel ${x},${y}`));
  }
  for (const name of ['transparent', 'translucent', 'opaque']) assert.ok(counts[name] > 0);
  return counts;
}
function checkProbes(rendered, object) {
  const scale = object.fit === 'fill' ? null : Math[object.fit === 'cover' ? 'max' : 'min'](object.width / size.width, object.height / size.height);
  const sx = scale ?? object.width / size.width, sy = scale ?? object.height / size.height;
  const dx = (object.width - size.width * sx) / 2, dy = (object.height - size.height * sy) / 2;
  const probes = [[8, 88, [255, 0, 255, 0]], [64, 88, gold], [64, 120, label], [64, 125, [32, 38, 45, 255]]];
  for (const [x, y, rgba] of probes) {
    const cx = Math.floor(object.x + dx + (x + 0.5) * sx), cy = Math.floor(object.y + dy + (y + 0.5) * sy);
    close(rgbAt(rendered, cx, cy), over(rgba, dark, object.opacity), 2, `${object.fit} alpha probe ${cx},${cy}`);
  }
  // A crop must clip at the object box; contain must leave its letterbox clear.
  close(rgbAt(rendered, 100, 320), dark, 0, 'outside object crop');
  if (object.fit === 'contain' && object.width === object.height) close(rgbAt(rendered, 100, 180), dark, 0, 'contain letterbox');
}

export async function runAlphaAcceptance(output) {
  output = path.resolve(output);
  await fs.mkdir(output); // Never reuse or replace another acceptance run.
  const root = path.join(output, 'project'), renders = [];
  try {
    const sources = await fixture(path.join(output, 'source-assets'));
    await fs.writeFile(path.join(output, 'create.json'), encode(sources.input), { flag: 'wx' });
    const created = await createProject(root, sources.input);
    const originalAsset = created.document.assets.find(asset => asset.id === 'product');
    assert.deepEqual(await pixels(path.join(root, originalAsset.render_file)), sources.data);
    const render = async (name, options) => {
      const result = await renderProject(root, path.join(output, name), options);
      renders.push({ name, revision: result.receipt.revision, ...result.receipt.outputs.png });
      return { ...result, data: await pixels(path.join(result.output, 'image.png')) };
    };
    const edit = async (summary, operations) => {
      const current = await readProject(root);
      const spec = { base_revision: current.document.revision, author: 'human', summary, operations };
      await fs.writeFile(path.join(output, `edit-${spec.base_revision + 1}.json`), encode(spec), { flag: 'wx' });
      await editBatch(root, spec);
    };
    const initial = await render('01-light');
    const lightCheck = checkIdentity(initial.data, sources.data, light);
    const spec = { id: 'dark-background', base_revision: 1, target_id: 'background', mode: 'replace', summary: 'Dark background behind unchanged RGBA product', source: sources.proposed };
    await fs.writeFile(path.join(output, 'stage-dark.json'), encode(spec), { flag: 'wx' });
    await stageCandidate(root, spec);
    const candidate = await render('02-dark-candidate', { candidateId: spec.id });
    assert.equal((await readProject(root)).sha256, created.sha256);
    const accept = { candidate_id: spec.id, base_revision: 1, author: 'human', summary: 'Accept dark background' };
    await fs.writeFile(path.join(output, 'accept-dark.json'), encode(accept), { flag: 'wx' });
    await acceptCandidate(root, accept);
    const accepted = await render('03-dark-accepted');
    assert.equal(accepted.receipt.outputs.png.sha256, candidate.receipt.outputs.png.sha256);
    const darkCheck = checkIdentity(accepted.data, sources.data, dark);
    let opaqueChanged = 0, translucentChanged = 0;
    for (let y = 0; y < size.height; y++) for (let x = 0; x < size.width; x++) {
      const alpha = sources.data[(y * size.width + x) * 4 + 3];
      if (rgbAt(initial.data, x + 128, y + 112).some((v, channel) => v !== rgbAt(accepted.data, x + 128, y + 112)[channel])) {
        if (alpha === 255) opaqueChanged++;
        else if (alpha > 0) translucentChanged++;
      }
    }
    assert.equal(opaqueChanged, 0); assert.equal(translucentChanged, lightCheck.translucent);
    await edit('Move and enlarge independent product', [update({ x: 96, y: 96, width: 192, height: 288 })]);
    const scaled = await render('04-scaled');
    let outsideChanged = 0;
    for (let y = 0; y < 384; y++) for (let x = 0; x < 384; x++) {
      if (x >= 96 && x < 288 && y >= 96 && y < 384) continue; // Union of old/new boxes.
      const at = (y * 384 + x) * 4;
      if (!accepted.data.subarray(at, at + 4).equals(scaled.data.subarray(at, at + 4))) outsideChanged++;
    }
    assert.equal(outsideChanged, 0);
    const scaleHead = (await readProject(root)).sha256;
    const neutralSpec = { id: 'hidden-rgb-neutral', base_revision: 3, target_id: 'product', mode: 'replace', summary: 'Only invisible RGB differs; scaled pixels must be identical', source: sources.neutral };
    await fs.writeFile(path.join(output, 'stage-hidden-rgb-neutral.json'), encode(neutralSpec), { flag: 'wx' });
    await stageCandidate(root, neutralSpec);
    const neutralPreview = await render('04b-hidden-rgb-neutral', { candidateId: neutralSpec.id });
    assert.equal(neutralPreview.receipt.outputs.png.sha256, scaled.receipt.outputs.png.sha256);
    assert.equal((await readProject(root)).sha256, scaleHead);
    // Interior probes avoid conflating a resampler's edge filter with optical
    // truth. Actual interpolation/crop pixels remain in the inspection sheet.
    const scaledObject = (await readProject(root)).document.objects.find(object => object.id === 'product');
    for (const [x, y, rgba] of [[64, 88, gold], [64, 120, label]]) close(rgbAt(scaled.data, 96 + x * 1.5, 96 + y * 1.5), over(rgba, dark), 2, 'scaled alpha');
    await edit('Set product opacity and crop to square', [update({ height: 192, opacity: 0.5, fit: 'cover' })]);
    const cropped = await render('05-cover-half-opacity'); checkProbes(cropped.data, { ...scaledObject, height: 192, opacity: 0.5, fit: 'cover' });
    await edit('Contain whole product in square', [update({ opacity: 1, fit: 'contain' })]);
    const contained = await render('06-contain'); checkProbes(contained.data, { ...scaledObject, height: 192, opacity: 1, fit: 'contain' });
    await edit('Undo geometry and opacity changes', [{ type: 'revert_to', revision: 2 }]);
    const undo = await render('07-undo'), reopen = await render('08-reopen');
    assert.equal(undo.receipt.outputs.png.sha256, accepted.receipt.outputs.png.sha256);
    assert.equal(reopen.receipt.outputs.png.sha256, accepted.receipt.outputs.png.sha256);
    const final = await readProject(root);
    assert.deepEqual(final.document.assets.find(asset => asset.id === 'product'), originalAsset);
    assert.deepEqual(final.document.font, created.document.font);
    assert.deepEqual(final.document.objects.filter(object => object.id !== 'background'), created.document.objects.filter(object => object.id !== 'background'));
    assert.equal(sha256(await fs.readFile(sources.product)), originalAsset.sha256);
    // Copy only the self-contained project; no original fixture path is needed.
    const relocated = path.join(output, 'relocated-project'); await fs.cp(root, relocated, { recursive: true, errorOnExist: true, force: false });
    const portable = await renderProject(relocated, path.join(output, '09-relocated'));
    assert.equal(portable.receipt.outputs.png.sha256, accepted.receipt.outputs.png.sha256);
    const tiles = [initial, accepted, scaled, cropped, contained, undo].map((item, index) => ({ input: path.join(item.output, 'image.png'), left: index % 3 * 384, top: Math.floor(index / 3) * 384 }));
    await fs.writeFile(path.join(output, 'comparison.png'), await sharp({ create: { width: 1152, height: 768, channels: 4, background: '#ffffff' } }).composite(tiles).png().toBuffer(), { flag: 'wx' });
    const report = { status: 'PASS', output, project: root, final_revision: final.document.revision, product_sha256: originalAsset.sha256,
      alpha_checks: { light: lightCheck, dark: darkCheck, opaque_canvas_pixels_changed_on_background_edit: opaqueChanged,
        translucent_canvas_pixels_changed_on_background_edit: translucentChanged, outside_union_pixels_changed_on_product_move: outsideChanged,
        hidden_rgb_scaled_png_parity: 'PASS' },
      checks: ['import-rgba-byte-parity', 'light-dark-source-over', 'stage-keeps-current-revision', 'candidate-accept-png-parity', 'opaque-label-preserved',
        'translucency-follows-background', 'move-scale-outside-pixels-preserved', 'hidden-rgb-resampling-invariance', 'scaled-alpha', 'object-opacity', 'cover-clip', 'contain-letterbox',
        'undo-reopen-png-parity', 'relocated-png-parity', 'product-font-preserved'],
      renders, comparison_order: ['light', 'dark', 'scaled', 'cover-half-opacity', 'contain', 'undo'],
      fixture: 'Synthetic known RGBA matte; no real product, Provider call, segmentation or optical recovery', visual_quality: 'UNVERIFIED' };
    await fs.writeFile(path.join(output, 'acceptance-report.json'), encode(report), { flag: 'wx' });
    return report;
  } catch (error) {
    await fs.writeFile(path.join(output, 'acceptance-report.json'), encode({ status: 'FAIL', error: error.message, renders }), { flag: 'wx' });
    throw error;
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const parent = fileURLToPath(new URL('../../dist/', import.meta.url));
  await fs.mkdir(parent, { recursive: true });
  const output = process.argv[2] ?? path.join(parent, `image-alpha-${new Date().toISOString().slice(0, 10)}-${randomUUID().slice(0, 8)}`);
  const report = await runAlphaAcceptance(output);
  console.log(JSON.stringify({ status: report.status, output: report.output, checks: report.checks.length, alpha_checks: report.alpha_checks }, null, 2));
}
