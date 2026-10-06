import * as fs from 'node:fs/promises';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import assert from 'node:assert/strict';
import { createProject, readProject, editBatch, encode } from './project.mjs';
import { renderProject } from './render.mjs';
import { demoInput } from './fixtures.mjs';
import { sha256 } from '../local-production/content-store.mjs';

const parent = path.resolve(new URL('../../dist/', import.meta.url).pathname);
await fs.mkdir(parent, { recursive: true });
const output = path.resolve(process.argv[2] ?? path.join(parent, `image-p0-${new Date().toISOString().slice(0, 10)}-${randomUUID().slice(0, 8)}`));
await fs.mkdir(output);
const root = path.join(output, 'project');
const input = await demoInput(path.join(output, 'source-assets'));
await fs.writeFile(path.join(output, 'create.json'), encode(input), { flag: 'wx' });
const created = await createProject(root, input);
const renders = [];
const render = async name => {
  const result = await renderProject(root, path.join(output, name));
  renders.push({ name, revision: result.receipt.revision, ...result.receipt.outputs.png });
  return result;
};
const edit = async (summary, operations, author = 'agent') => {
  const current = await readProject(root);
  const batch = { base_revision: current.document.revision, author, summary, operations };
  await fs.writeFile(path.join(output, `edit-${current.document.revision + 1}.json`), encode(batch), { flag: 'wx' });
  return editBatch(root, batch);
};
const initial = await render('01-initial');
await edit('Change headline and price', [{ type: 'update_object', id: 'headline', patch: { text: '自在新生\n轻盈日常' } }, { type: 'update_object', id: 'price', patch: { text: '¥139' } }]);
await render('02-copy-price');
await edit('Enlarge product', [{ type: 'update_object', id: 'product', patch: { x: 555, y: 227, width: 390, height: 602 } }]);
await render('03-product-scale');
await edit('Move headline upward', [{ type: 'update_object', id: 'headline', patch: { y: 176 } }], 'human');
await render('04-headline-move');
await edit('Undo headline move', [{ type: 'revert_to', revision: 3 }], 'human');
const undo = await render('05-undo');
assert.equal(undo.receipt.outputs.png.sha256, renders.find(item => item.name === '03-product-scale').sha256);
const reopened = await readProject(root);
const reopen = await render('06-reopen');
assert.equal(reopen.receipt.outputs.png.sha256, undo.receipt.outputs.png.sha256);
await assert.rejects(editBatch(root, { base_revision: 1, author: 'agent', summary: 'stale edit', operations: [{ type: 'update_object', id: 'price', patch: { text: '¥9' } }] }), /Revision conflict/);
await assert.rejects(editBatch(root, { base_revision: reopened.document.revision, author: 'agent', summary: 'locked edit', operations: [{ type: 'update_object', id: 'logo', patch: { x: 1 } }] }), /locked/);
await renderProject(root, path.join(output, '07-preview'), { previewMax: 640 });
const adaptation = (width, height) => [
  { type: 'set_canvas', canvas: { width, height, background: '#e4e8dc' } },
  { type: 'update_object', id: 'background', patch: { width, height } },
  { type: 'update_object', id: 'headline', patch: { x: 70, y: 198, width: 650, height: 220 } },
  { type: 'update_object', id: 'description', patch: { x: 75, y: 430 } },
  { type: 'update_object', id: 'price', patch: { x: 75, y: 520 } },
  { type: 'update_object', id: 'note', patch: { x: 78, y: 630 } },
  { type: 'update_object', id: 'product', patch: { x: Math.round((width - 350) / 2), y: 650, width: 350, height: 550 } },
  { type: 'update_object', id: 'footer', patch: { x: 60, y: height - 65, width: width - 120, font_size: 16 } },
];
// Both target sizes deliberately reflow objects; resizing only a PNG is not
// accepted as an editable layout adaptation.
const portrait45 = adaptation(960, 1200);
portrait45.find(op => op.id === 'product').patch = { x: 510, y: 468, width: 350, height: 550 };
portrait45.find(op => op.id === 'headline').patch.width = 650;
await edit('Reflow to 4:5', portrait45);
await render('08-portrait-4x5');
await edit('Reflow to 9:16', adaptation(900, 1600));
await render('09-portrait-9x16');
const final = await readProject(root);
assert.deepEqual(final.document.assets, created.document.assets);
assert.deepEqual(final.document.objects.find(object => object.id === 'logo'), created.document.objects.find(object => object.id === 'logo'));
for (const asset of final.document.assets) assert.equal(sha256(await fs.readFile(path.join(root, asset.file))), asset.sha256);
const report = { status: 'PASS', output, project: root, final_revision: final.document.revision, initial_png_sha256: initial.receipt.outputs.png.sha256,
  checks: ['create', 'copy-price-edit', 'product-scale', 'headline-move', 'undo-png-parity', 'reopen-png-parity', 'stale-rejection', 'locked-rejection', 'preview', '4:5-layout', '9:16-layout', 'original-assets-preserved', 'logo-object-preserved'],
  renders, visual_quality: 'UNVERIFIED', fixture: 'synthetic, no model/API call' };
await fs.writeFile(path.join(output, 'smoke-report.json'), encode(report), { flag: 'wx' });
console.log(JSON.stringify(report, null, 2));
