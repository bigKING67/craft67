import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import assert from 'node:assert/strict';
import { createProject, readProject, editBatch, encode } from './project.mjs';
import { demoInput } from './fixtures.mjs';
import { candidateFixtures } from './candidate-fixtures.mjs';
import { stageCandidate, inspectCandidate, acceptCandidate, discardCandidate, compareCandidate } from './candidates.mjs';
import { renderProject } from './render.mjs';

const parent = fileURLToPath(new URL('../../dist/', import.meta.url));
await fs.mkdir(parent, { recursive: true });
const output = path.resolve(process.argv[2] ?? path.join(parent, `image-p1-${new Date().toISOString().slice(0, 10)}-${randomUUID().slice(0, 8)}`));
await fs.mkdir(output);
const input = await demoInput(path.join(output, 'source-assets'));
const sources = await candidateFixtures(path.join(output, 'candidate-inputs'));
const root = path.join(output, 'project');
const created = await createProject(root, input);
const renders = [];
const render = async name => {
  const result = await renderProject(root, path.join(output, name));
  renders.push({ name, revision: result.receipt.revision, ...result.receipt.outputs.png });
  return result;
};
await render('01-initial');
for (let index = 0; index < 3; index++) {
  const spec = { id: `background-${index + 1}`, base_revision: 1, target_id: 'background', mode: 'replace', summary: `Synthetic background option ${index + 1}`, source: sources.backgrounds[index] };
  await fs.writeFile(path.join(output, `stage-${spec.id}.json`), encode(spec));
  await stageCandidate(root, spec);
  await compareCandidate(root, spec.id, path.join(output, `compare-${spec.id}`));
}
assert.equal((await readProject(root)).sha256, created.sha256);
await acceptCandidate(root, { candidate_id: 'background-1', base_revision: 1, author: 'agent', summary: 'Accept warm background, preserve foreground objects' });
await discardCandidate(root, { candidate_id: 'background-2', author: 'human', summary: 'Discard cool direction' });
await render('02-selected-background');
await editBatch(root, { base_revision: 2, author: 'human', summary: 'Human changes price to 149', operations: [{ type: 'update_object', id: 'price', patch: { text: '¥149' } }] });
const beforeLocal = await render('03-human-price');
const priceHead = (await readProject(root)).sha256;
await assert.rejects(acceptCandidate(root, { candidate_id: 'background-3', base_revision: 1, author: 'agent', summary: 'Old candidate must fail' }), /Revision conflict/);
await assert.rejects(acceptCandidate(root, { candidate_id: 'background-3', base_revision: 3, author: 'agent', summary: 'No silent rebasing' }), /Candidate base revision conflict/);
assert.equal((await readProject(root)).sha256, priceHead);
const localSpec = { id: 'remove-clutter', base_revision: 3, target_id: 'background', source: sources.clean, mode: 'masked', summary: 'Remove small background leaf; preserve product/logo regions', edit: sources.edit };
await fs.writeFile(path.join(output, 'stage-remove-clutter.json'), encode(localSpec));
const masked = await stageCandidate(root, localSpec);
await compareCandidate(root, 'remove-clutter', path.join(output, 'compare-local-edit'));
assert.equal((await readProject(root)).sha256, priceHead);
await acceptCandidate(root, { candidate_id: 'remove-clutter', base_revision: 3, author: 'agent', summary: 'Accept bounded local cleanup' });
await render('04-masked-edit');
await editBatch(root, { base_revision: 4, author: 'human', summary: 'Undo local cleanup', operations: [{ type: 'revert_to', revision: 3 }] });
const undo = await render('05-undo-local');
assert.equal(undo.receipt.outputs.png.sha256, beforeLocal.receipt.outputs.png.sha256);
const reopen = await render('06-reopen');
assert.equal(reopen.receipt.outputs.png.sha256, undo.receipt.outputs.png.sha256);
const final = await readProject(root);
for (const object of created.document.objects.filter(object => object.id !== 'background' && object.id !== 'price')) assert.deepEqual(final.document.objects.find(value => value.id === object.id), object);
assert.equal(final.document.objects.find(object => object.id === 'price').text, '¥149');
const localState = await inspectCandidate(root, 'remove-clutter');
assert.equal(localState.status, 'accepted'); assert.equal(localState.applied_in_current, false);
const report = { status: 'PASS', output, project: root, final_revision: final.document.revision,
  checks: ['three-candidates', 'stage-no-revision-change', 'full-poster-compare', 'accept', 'discard', 'human-price-preserved', 'stale-rejection', 'no-silent-rebase',
    'masked-composite', 'protected-pixels-unchanged', 'outside-blend-unchanged', 'undo-png-parity', 'reopen-png-parity', 'foreground-objects-preserved'],
  protection_qa: masked.candidate.qa, renders, fixture: 'synthetic local assets, no Provider call', visual_quality: 'UNVERIFIED', agent_behavior: 'UNVERIFIED: deterministic script' };
await fs.writeFile(path.join(output, 'smoke-report.json'), encode(report));
console.log(JSON.stringify(report, null, 2));
