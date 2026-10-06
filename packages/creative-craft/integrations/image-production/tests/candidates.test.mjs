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
import { createProject, readProject, editBatch, encode } from '../project.mjs';
import { demoInput } from '../fixtures.mjs';
import { candidateFixtures } from '../candidate-fixtures.mjs';
import { stageCandidate, listCandidates, inspectCandidate, acceptCandidate, discardCandidate, compareCandidate, unlockCandidate } from '../candidates.mjs';
import { renderProject } from '../render.mjs';
import { compositeRaster } from '../composite.mjs';

const tempRoot = await fs.realpath(os.tmpdir());
const exec = promisify(execFile);
async function fixture(t) {
  const directory = await fs.mkdtemp(path.join(tempRoot, 'craft-candidate-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const input = await demoInput(path.join(directory, 'source'));
  const sources = await candidateFixtures(path.join(directory, 'candidate-inputs'));
  const root = path.join(directory, 'project');
  await createProject(root, input);
  return { directory, root, input, sources };
}
const stage = (sources, id = 'pink', base_revision = 1) => ({ id, base_revision, target_id: 'background', source: sources.backgrounds[0], mode: 'replace', summary: 'Pink background candidate' });
const accept = (candidate_id = 'pink', base_revision = 1) => ({ candidate_id, base_revision, author: 'agent', summary: 'Accept background' });
const edit = (base_revision, operations) => ({ base_revision, author: 'human', summary: 'Human edit', operations });
const patch = (id, patch) => ({ type: 'update_object', id, patch });
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
const pixels = async file => sharp(await fs.readFile(file)).ensureAlpha().raw().toBuffer();

test('three staged candidates preserve the accepted revision and survive source removal/moving the project', async t => {
  const { root, directory, sources } = await fixture(t);
  const before = await readProject(root);
  assert.deepEqual(await listCandidates(root), []);
  for (let index = 0; index < 3; index++) await stageCandidate(root, { ...stage(sources, `option-${index + 1}`), source: sources.backgrounds[index] });
  const after = await readProject(root);
  assert.equal(after.sha256, before.sha256); assert.equal(after.document.revision, 1);
  await fs.rm(path.join(directory, 'candidate-inputs'), { recursive: true });
  const moved = path.join(directory, 'moved'); await fs.rename(root, moved);
  const candidates = await listCandidates(moved);
  assert.equal(candidates.length, 3); assert.ok(candidates.every(value => value.status === 'ready'));
  assert.equal((await readProject(moved)).sha256, before.sha256);
});

test('acceptance dry-run is read-only; commit changes only target binding and journals one new revision', async t => {
  const { root, sources } = await fixture(t);
  const before = await readProject(root);
  const staged = await stageCandidate(root, stage(sources));
  const files = await tree(root);
  const planned = await acceptCandidate(root, accept(), { dryRun: true });
  assert.equal(planned.dry_run, true); assert.deepEqual(await tree(root), files);
  const result = await acceptCandidate(root, accept());
  assert.equal(result.document.revision, 2);
  assert.deepEqual(result.document.change.candidate, { id: 'pink', sha256: staged.sha256 });
  for (const object of before.document.objects) {
    const now = result.document.objects.find(value => value.id === object.id);
    assert.deepEqual(now, object.id === 'background' ? { ...object, asset_id: staged.candidate.output.id } : object);
  }
  assert.deepEqual(result.document.assets.slice(0, before.document.assets.length), before.document.assets);
  assert.equal((await inspectCandidate(root, 'pink')).status, 'accepted');
  await assert.rejects(acceptCandidate(root, accept('pink', 2)), /already accepted/);
});

test('discard is terminal and does not change project; acceptance cannot be mixed with unrelated edits', async t => {
  const { root, sources } = await fixture(t);
  await stageCandidate(root, stage(sources));
  const before = (await readProject(root)).sha256;
  await assert.rejects(editBatch(root, edit(1, [{ type: 'accept_candidate', candidate_id: 'pink' }, patch('price', { text: '¥139' })])), /isolated/);
  await discardCandidate(root, { candidate_id: 'pink', author: 'human', summary: 'Discard this direction' });
  assert.equal((await inspectCandidate(root, 'pink')).status, 'discarded');
  await assert.rejects(acceptCandidate(root, accept()), /discarded/);
  await assert.rejects(discardCandidate(root, { candidate_id: 'pink', author: 'human', summary: 'Again' }), /already discarded/);
  assert.equal((await readProject(root)).sha256, before);
});

test('discard with maximum JSON-escaped summary remains readable and releases its decision lock', async t => {
  const { root, sources } = await fixture(t);
  const candidateId = 'x'.repeat(64), summary = '\u0000'.repeat(500);
  await stageCandidate(root, stage(sources, candidateId));
  const before = (await readProject(root)).sha256;
  const result = await discardCandidate(root, { candidate_id: candidateId, author: 'system', summary });
  assert.equal(result.status, 'discarded');
  assert.equal((await inspectCandidate(root, candidateId)).status, 'discarded');
  assert.equal((await listCandidates(root))[0].status, 'discarded');
  const decision = JSON.parse(await fs.readFile(path.join(root, 'candidates', candidateId, 'discard.json')));
  assert.equal(decision.summary, summary);
  await assert.rejects(fs.stat(path.join(root, 'candidates', candidateId, '.decision-lock')), { code: 'ENOENT' });
  assert.equal((await readProject(root)).sha256, before);
});

test('human edits make candidates stale; supplying current revision cannot silently rebase them', async t => {
  const { root, sources } = await fixture(t);
  await stageCandidate(root, stage(sources));
  await editBatch(root, edit(1, [patch('price', { text: '¥149' })]));
  const before = (await readProject(root)).sha256;
  assert.equal((await inspectCandidate(root, 'pink')).status, 'stale');
  await assert.rejects(acceptCandidate(root, accept()), /Revision conflict/);
  await assert.rejects(acceptCandidate(root, accept('pink', 2)), /Candidate base revision conflict/);
  await editBatch(root, edit(2, [patch('background', { locked: true })]));
  await assert.rejects(stageCandidate(root, stage(sources, 'locked', 3)), /locked/);
  await assert.rejects(acceptCandidate(root, accept('pink', 3)), /Candidate base revision conflict/);
  assert.notEqual((await readProject(root)).sha256, before); // Only explicit human lock changed it.
});

test('undo restores exact PNG while retaining consumed candidate history', async t => {
  const { root, sources, directory } = await fixture(t);
  const before = await renderProject(root, path.join(directory, 'before'));
  await stageCandidate(root, stage(sources)); await acceptCandidate(root, accept());
  await editBatch(root, edit(2, [{ type: 'revert_to', revision: 1 }]));
  const undo = await renderProject(root, path.join(directory, 'undo'));
  assert.equal(undo.receipt.outputs.png.sha256, before.receipt.outputs.png.sha256);
  const status = await inspectCandidate(root, 'pink');
  assert.equal(status.status, 'accepted'); assert.equal(status.applied_in_current, false); assert.equal(status.accepted_revision, 2);
  await assert.rejects(acceptCandidate(root, accept('pink', 3)), /already accepted/);
});

test('concurrent accept/discard cannot both win; competing candidates on one revision have one commit', async t => {
  const { root, sources } = await fixture(t);
  await stageCandidate(root, stage(sources));
  const results = await Promise.allSettled([acceptCandidate(root, accept()), discardCandidate(root, { candidate_id: 'pink', author: 'human', summary: 'Discard' })]);
  assert.equal(results.filter(value => value.status === 'fulfilled').length, 1);
  assert.match(results.find(value => value.status === 'rejected').reason.message, /decision in progress|already accepted|discarded/);
  const state = await inspectCandidate(root, 'pink'); assert.ok(['accepted', 'discarded'].includes(state.status)); assert.equal(state.decision_pending, false);
  const other = await fixture(t);
  await stageCandidate(other.root, stage(other.sources, 'a'));
  await stageCandidate(other.root, { ...stage(other.sources, 'b'), source: other.sources.backgrounds[1] });
  const commits = await Promise.allSettled([acceptCandidate(other.root, accept('a')), acceptCandidate(other.root, accept('b'))]);
  assert.equal(commits.filter(value => value.status === 'fulfilled').length, 1);
  assert.match(commits.find(value => value.status === 'rejected').reason.message, /Revision conflict/);
  assert.equal((await readProject(other.root)).document.revision, 2);
});

test('candidate IDs matching Object prototype names are ordinary IDs, not inherited decisions', async t => {
  const { root, sources } = await fixture(t);
  await stageCandidate(root, stage(sources, 'constructor'));
  assert.equal((await inspectCandidate(root, 'constructor')).status, 'ready');
  await acceptCandidate(root, accept('constructor'));
  assert.equal((await inspectCandidate(root, 'constructor')).status, 'accepted');
});

test('candidate output/mask/accepted-manifest tampering and abandoned decision locks fail closed', async t => {
  for (const mode of ['output', 'mask', 'manifest', 'lock']) {
    const { root, sources } = await fixture(t);
    await stageCandidate(root, stage(sources));
    let entry = await inspectCandidate(root, 'pink');
    if (mode === 'mask') {
      await acceptCandidate(root, accept());
      await stageCandidate(root, { ...stage(sources, 'clean', 2), source: sources.clean, mode: 'masked', edit: sources.edit });
      entry = await inspectCandidate(root, 'clean');
      const file = path.join(root, entry.candidate.edit.blend_mask.file);
      await fs.writeFile(file, Buffer.from('bad mask'));
      await assert.rejects(acceptCandidate(root, accept('clean', 2)), /digest mismatch/);
      assert.equal((await readProject(root)).document.revision, 2);
    } else if (mode === 'manifest') {
      await acceptCandidate(root, accept());
      const file = path.join(root, 'candidates/pink/candidate.json'); const value = JSON.parse(await fs.readFile(file, 'utf8')); value.summary = 'tampered'; await fs.writeFile(file, encode(value));
      await assert.rejects(readProject(root), /Accepted candidate digest mismatch/);
    } else if (mode === 'lock') {
      await fs.writeFile(path.join(root, 'candidates/pink/.decision-lock'), '{}');
      assert.equal((await inspectCandidate(root, 'pink')).status, 'decision_pending');
      await assert.rejects(acceptCandidate(root, accept()), /decision in progress/);
      assert.equal((await readProject(root)).document.revision, 1);
    } else {
      await fs.writeFile(path.join(root, entry.candidate.output.file), Buffer.from('bad output'));
      await assert.rejects(acceptCandidate(root, accept()), /digest mismatch/);
      assert.equal((await readProject(root)).document.revision, 1);
    }
  }
});

test('masked composite preserves protected/outside pixels even when proposal changes the whole image', async t => {
  const { root, sources, directory } = await fixture(t);
  await stageCandidate(root, stage(sources)); await acceptCandidate(root, accept());
  const original = await readProject(root);
  const asset = original.document.assets.find(asset => asset.id === original.document.objects.find(object => object.id === 'background').asset_id);
  const altered = path.join(directory, 'globally-changed.png');
  await fs.writeFile(altered, await sharp(sources.clean).modulate({ brightness: 0.6 }).png().toBuffer());
  const staged = await stageCandidate(root, { ...stage(sources, 'clean', 2), source: altered, mode: 'masked', edit: sources.edit });
  const before = await pixels(path.join(root, asset.render_file)), after = await pixels(path.join(root, staged.candidate.output.file));
  const protection = await sharp(await fs.readFile(sources.edit.protection_mask)).toColourspace('b-w').raw().toBuffer();
  const blend = await sharp(await fs.readFile(sources.edit.blend_mask)).toColourspace('b-w').raw().toBuffer();
  let changed = 0;
  for (let pixel = 0; pixel < 1_000_000; pixel++) {
    const at = pixel * 4;
    if (!before.subarray(at, at + 4).equals(after.subarray(at, at + 4))) { changed++; assert.equal(protection[pixel], 0); assert.ok(blend[pixel]); }
  }
  assert.ok(changed > 100); assert.equal(changed, staged.candidate.qa.changed_pixels);
  assert.equal(staged.candidate.qa.protected_changed_pixels, 0); assert.equal(staged.candidate.qa.outside_blend_changed_pixels, 0);
  const first = await renderProject(root, path.join(directory, 'before-local'));
  await acceptCandidate(root, accept('clean', 2));
  const second = await renderProject(root, path.join(directory, 'after-local'));
  const a = await pixels(path.join(first.output, 'image.png')), b = await pixels(path.join(second.output, 'image.png'));
  for (let pixel = 0; pixel < 1_000_000; pixel++) if (protection[pixel] || !blend[pixel]) {
    const at = pixel * 4; assert.ok(a.subarray(at, at + 4).equals(b.subarray(at, at + 4)), `Unexpected canvas change at ${pixel}`);
  }
});

test('soft blend uses premultiplied alpha; protected transparent pixels retain all RGBA bytes', async () => {
  const beforeData = Buffer.from([123, 45, 67, 0, 10, 20, 30, 200, 255, 0, 0, 255]);
  const afterData = Buffer.from([0, 255, 0, 255, 200, 200, 200, 255, 0, 0, 255, 128]);
  const png = data => sharp(data, { raw: { width: 3, height: 1, channels: 4 } }).png().toBuffer();
  const before = await png(beforeData), after = await png(afterData);
  const result = await compositeRaster(before, after, { width: 3, height: 1, context: { x: 0, y: 0, width: 3, height: 1 },
    generation: Buffer.from([255, 255, 255]), protection: Buffer.from([255, 0, 0]), blend: Buffer.from([255, 0, 128]) });
  const output = await sharp(result.png).ensureAlpha().raw().toBuffer();
  assert.deepEqual([...output.subarray(0, 8)], [...beforeData.subarray(0, 8)]);
  assert.deepEqual([...output.subarray(8)], [169, 0, 86, 191]);
  assert.equal(result.qa.protected_changed_pixels, 0); assert.equal(result.qa.outside_blend_changed_pixels, 0);
});

test('misaligned/color/soft-protection masks, invalid context and blend scope reject without publishing a candidate', async t => {
  const { root, sources, directory } = await fixture(t);
  await stageCandidate(root, stage(sources)); await acceptCandidate(root, accept());
  const before = (await readProject(root)).sha256;
  const base = { ...stage(sources, 'invalid', 2), source: sources.clean, mode: 'masked', edit: sources.edit };
  const color = path.join(directory, 'color.png'); await fs.writeFile(color, await sharp({ create: { width: 1000, height: 1000, channels: 3, background: '#888888' } }).png().toBuffer());
  const soft = path.join(directory, 'soft.png'); await fs.writeFile(soft, await sharp(Buffer.alloc(1_000_000, 128), { raw: { width: 1000, height: 1000, channels: 1 } }).toColourspace('b-w').png().toBuffer());
  const zero = path.join(directory, 'zero.png'); await fs.writeFile(zero, await sharp(Buffer.alloc(1_000_000), { raw: { width: 1000, height: 1000, channels: 1 } }).toColourspace('b-w').png().toBuffer());
  for (const edit of [
    { ...sources.edit, blend_mask: color }, { ...sources.edit, protection_mask: soft },
    { ...sources.edit, context: { x: 0, y: 0, width: 10, height: 10 } }, { ...sources.edit, generation_mask: zero },
    { ...sources.edit, blend_mask: zero },
  ]) await assert.rejects(stageCandidate(root, { ...base, edit }), /Mask must|binary|outside context|outside generation|No editable/);
  await assert.rejects(fs.stat(path.join(root, 'candidates/invalid')), /ENOENT/);
  assert.equal((await readProject(root)).sha256, before);
});

test('failed/cancelled staging does not touch accepted revision; immutable IDs cannot be reused', async t => {
  const { root, sources } = await fixture(t);
  const before = (await readProject(root)).sha256;
  const controller = new AbortController(); controller.abort();
  await assert.rejects(stageCandidate(root, stage(sources), { signal: controller.signal }), /abort/i);
  assert.equal((await readProject(root)).sha256, before);
  const staged = await stageCandidate(root, stage(sources));
  await assert.rejects(stageCandidate(root, { ...stage(sources), source: sources.backgrounds[1] }), /already exists|EEXIST/);
  assert.equal((await inspectCandidate(root, 'pink')).sha256, staged.sha256);
  assert.equal((await readProject(root)).sha256, before);
});

test('full poster comparison is read-only, labels stale basis, and its preview equals accepted render pixels', async t => {
  const { root, sources, directory } = await fixture(t);
  await stageCandidate(root, stage(sources));
  const files = await tree(root);
  const compared = await compareCandidate(root, 'pink', path.join(directory, 'compare'));
  assert.deepEqual(await tree(root), files);
  assert.equal(compared.report.basis_revision, 1); assert.equal(compared.report.visual_quality, 'UNVERIFIED');
  const meta = await sharp(await fs.readFile(path.join(compared.output, 'comparison.png'))).metadata();
  assert.deepEqual([meta.width, meta.height], [1280, 640]);
  await acceptCandidate(root, accept());
  const accepted = await renderProject(root, path.join(directory, 'accepted'), { previewMax: 640 });
  const previewReceipt = JSON.parse(await fs.readFile(path.join(compared.output, 'after/receipt.json'), 'utf8'));
  assert.equal(previewReceipt.outputs.png.sha256, accepted.receipt.outputs.png.sha256);
  assert.equal(previewReceipt.candidate_preview.status_at_check, 'ready');
  const other = await fixture(t); await stageCandidate(other.root, stage(other.sources)); await editBatch(other.root, edit(1, [patch('price', { text: '¥159' })]));
  const stale = await compareCandidate(other.root, 'pink', path.join(other.directory, 'stale'));
  assert.equal(stale.report.candidate_status_at_check, 'stale'); assert.equal(stale.report.current_revision_at_check, 2); assert.equal(stale.report.basis_revision, 1);
  const staleReceipt = JSON.parse(await fs.readFile(path.join(stale.output, 'after/receipt.json'), 'utf8'));
  assert.equal(staleReceipt.candidate_preview.status_at_check, 'stale');
});

async function observedPreview(root, directory, name, expected) {
  const before = await tree(root);
  const rendered = await renderProject(root, path.join(directory, name), { candidateId: 'pink', previewMax: 640 });
  const receipt = JSON.parse(await fs.readFile(path.join(rendered.output, 'receipt.json'), 'utf8'));
  assert.deepEqual(receipt, rendered.receipt);
  assert.equal(receipt.status, 'completed'); assert.equal(receipt.visual_quality, 'UNVERIFIED');
  assert.equal(receipt.revision, 1); // The image is still based on the immutable candidate basis.
  assert.equal(receipt.candidate_preview.id, 'pink');
  assert.ok(Number.isFinite(Date.parse(receipt.candidate_preview.checked_at)));
  for (const [key, value] of Object.entries(expected)) assert.equal(receipt.candidate_preview[key], value, key);
  assert.deepEqual(await tree(root), before);
  return receipt;
}

test('candidate render receipt preserves ready, stale and discarded state without changing preview pixels', async t => {
  const { root, directory, sources } = await fixture(t);
  await stageCandidate(root, stage(sources));
  const ready = await observedPreview(root, directory, 'ready-receipt', { status_at_check: 'ready', current_revision_at_check: 1,
    accepted_revision: null, applied_in_current: false, stale: false, decision_pending: false });
  await editBatch(root, edit(1, [patch('price', { text: '¥159' })]));
  const stale = await observedPreview(root, directory, 'stale-receipt', { status_at_check: 'stale', current_revision_at_check: 2,
    accepted_revision: null, applied_in_current: false, stale: true, decision_pending: false });
  await discardCandidate(root, { candidate_id: 'pink', author: 'agent', summary: 'Rejected visual direction' });
  const discarded = await observedPreview(root, directory, 'discarded-receipt', { status_at_check: 'discarded', current_revision_at_check: 2,
    accepted_revision: null, applied_in_current: false, stale: true, decision_pending: false });
  assert.equal(ready.outputs.png.sha256, stale.outputs.png.sha256);
  assert.equal(ready.outputs.png.sha256, discarded.outputs.png.sha256);
  await assert.rejects(acceptCandidate(root, accept('pink', 2)), /discarded/);
});

test('candidate render receipt separates pending decisions and accepted history from current application', async t => {
  const { root, directory, sources } = await fixture(t);
  await stageCandidate(root, stage(sources));
  const lock = path.join(root, 'candidates', 'pink', '.decision-lock');
  await fs.writeFile(lock, '{}');
  let pending;
  try { pending = await observedPreview(root, directory, 'pending-receipt', { status_at_check: 'decision_pending', current_revision_at_check: 1,
    accepted_revision: null, applied_in_current: false, stale: false, decision_pending: true }); }
  finally { await fs.unlink(lock); }
  await acceptCandidate(root, accept());
  const accepted = await observedPreview(root, directory, 'accepted-receipt', { status_at_check: 'accepted', current_revision_at_check: 2,
    accepted_revision: 2, applied_in_current: true, stale: true, decision_pending: false });
  await editBatch(root, edit(2, [{ type: 'revert_to', revision: 1 }]));
  const reverted = await observedPreview(root, directory, 'reverted-receipt', { status_at_check: 'accepted', current_revision_at_check: 3,
    accepted_revision: 2, applied_in_current: false, stale: true, decision_pending: false });
  assert.equal(pending.outputs.png.sha256, accepted.outputs.png.sha256);
  assert.equal(accepted.outputs.png.sha256, reverted.outputs.png.sha256);
  const current = await renderProject(root, path.join(directory, 'ordinary-current'));
  assert.equal(current.receipt.candidate_preview, undefined); assert.equal(current.receipt.visual_quality, 'UNVERIFIED');
});

test('candidate render fails closed when the decision record cannot be verified', async t => {
  const { root, directory, sources } = await fixture(t);
  await stageCandidate(root, stage(sources));
  await discardCandidate(root, { candidate_id: 'pink', author: 'agent', summary: 'Rejected' });
  const file = path.join(root, 'candidates', 'pink', 'discard.json');
  const decision = JSON.parse(await fs.readFile(file)); decision.candidate_sha256 = '0'.repeat(64);
  await fs.writeFile(file, encode(decision));
  const output = path.join(directory, 'invalid-decision');
  await assert.rejects(renderProject(root, output, { candidateId: 'pink' }), /Discard decision binding mismatch/);
  assert.equal(JSON.parse(await fs.readFile(path.join(output, 'receipt.json'))).status, 'failed');
  await assert.rejects(fs.access(path.join(output, 'image.png')), { code: 'ENOENT' });
});

test('CLI stage/list/read/compare/accept/discard execute real JSON tools without hidden revision changes', async t => {
  const { root, directory, sources } = await fixture(t);
  const cli = fileURLToPath(new URL('../cli.mjs', import.meta.url));
  const run = async (command, argument, flag) => {
    let file;
    if (argument && typeof argument === 'object') { file = path.join(directory, `${command}-${Math.random().toString(16).slice(2)}.json`); await fs.writeFile(file, encode(argument)); }
    else file = argument;
    return JSON.parse((await exec(process.execPath, [cli, command, root, ...[file, flag].filter(value => value !== undefined)], { timeout: 30000, maxBuffer: 2_000_000 })).stdout);
  };
  assert.equal((await run('candidate-stage', stage(sources))).status, 'ready');
  assert.equal((await run('candidate-list')).length, 1); assert.equal((await run('candidate-read', 'pink')).status, 'ready');
  assert.equal((await run('candidate-compare', { candidate_id: 'pink', output: path.join(directory, 'compare') })).report.status, 'completed');
  assert.equal((await run('candidate-accept', accept(), '--dry-run')).dry_run, true);
  assert.equal((await readProject(root)).document.revision, 1);
  assert.equal((await run('candidate-accept', accept())).document.revision, 2);
  await run('candidate-stage', { ...stage(sources, 'reject', 2), source: sources.backgrounds[1] });
  assert.equal((await run('candidate-discard', { candidate_id: 'reject', author: 'human', summary: 'Discard' })).status, 'discarded');
  assert.equal((await readProject(root)).document.revision, 2);
});

test('candidate list reports stray and interrupted entries in place; stray files do not use candidate slots', async t => {
  const { root, sources } = await fixture(t);
  await stageCandidate(root, stage(sources));
  await fs.writeFile(path.join(root, 'candidates', '.DS_Store'), '');
  await fs.mkdir(path.join(root, 'candidates', 'interrupted'));
  const listed = await listCandidates(root);
  assert.deepEqual(listed.map(item => item.candidate?.id ?? item.candidate_id), ['interrupted', 'pink']);
  assert.equal(listed[0].status, 'incomplete'); assert.equal(listed[1].status, 'ready');
  await assert.rejects(stageCandidate(root, stage(sources, 'interrupted')), /already exists/);
  await stageCandidate(root, { ...stage(sources, 'second'), source: sources.backgrounds[1] });
});

test('a stale decision lock is released only with an audit record and never while its holder runs', async t => {
  const { root, sources } = await fixture(t);
  await stageCandidate(root, stage(sources));
  const lock = path.join(root, 'candidates', 'pink', '.decision-lock');
  const unlock = { candidate_id: 'pink', author: 'human', summary: 'Release lock left by killed process' };
  await fs.writeFile(lock, JSON.stringify({ pid: process.pid, created_at: new Date().toISOString() }));
  await assert.rejects(unlockCandidate(root, unlock), /still running/);
  let dead = 999_999; while ((() => { try { process.kill(dead, 0); return true; } catch { return false; } })()) dead++;
  await fs.writeFile(lock, JSON.stringify({ pid: dead, created_at: new Date().toISOString() }));
  assert.equal((await inspectCandidate(root, 'pink')).decision_pending, true);
  await assert.rejects(discardCandidate(root, { candidate_id: 'pink', author: 'agent', summary: 'Discard' }), /decision in progress/);
  const result = await unlockCandidate(root, unlock);
  assert.equal(result.status, 'unlocked'); assert.equal(result.lock.pid, dead); assert.equal(result.candidate.decision_pending, false);
  assert.ok((await fs.readdir(path.join(root, 'candidates', 'pink'))).some(name => name.startsWith('lock-release-')));
  await assert.rejects(unlockCandidate(root, unlock), /No decision lock/);
  assert.equal((await discardCandidate(root, { candidate_id: 'pink', author: 'agent', summary: 'Discard' })).status, 'discarded');
});

test('replacement that only changes PNG encoding is not a raster change', async t => {
  const { root, directory } = await fixture(t);
  const project = await readProject(root);
  const asset = project.document.assets.find(a => a.id === project.document.objects.find(o => o.id === 'background').asset_id);
  const rendered = await fs.readFile(path.join(root, asset.render_file));
  const { data, info } = await sharp(rendered).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const reencoded = path.join(directory, 'reencoded.png');
  await sharp(data, { raw: { width: info.width, height: info.height, channels: 4 } }).png({ compressionLevel: 1 }).toFile(reencoded);
  await assert.rejects(stageCandidate(root, { ...stage({ backgrounds: [reencoded] }) }), /no raster change/);
});
