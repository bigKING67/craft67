import * as fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import { sha256, writeOnce } from '../local-production/content-store.mjs';
import { LIMITS, record, id, string } from './document.mjs';
import { readProject, editBatch } from './project.mjs';
import { importRaster, saveAsset, regularPath, readAsset, assertOutsideProject } from './raster.mjs';
import { importMask, compositeRaster } from './composite.mjs';
import { readExecution } from './provider-store.mjs';
import { inspectAlpha, requireAlpha } from './provider-alpha.mjs';
import { CANDIDATE_SCHEMA, candidateBytes, ensureDirectory, assertCandidateSlot, publishCandidate, readCandidateEntry, verifyCandidateAgainst, readDiscard, decisionPending, withDecisionLock, candidateIds, releaseDecisionLock, validateDecision } from './candidate-store.mjs';

// Re-encoding alone is not a change. Hidden RGB under alpha=0 still counts:
// resampling can bleed it into visible pixels (see the alpha acceptance probe).
async function sameDecodedPixels(a, b) {
  const [x, y] = await Promise.all([a, b].map(png => sharp(png).ensureAlpha().raw().toBuffer()));
  return x.equals(y);
}

export async function stageCandidate(root, input, { signal } = {}) {
  record(input, ['id', 'base_revision', 'target_id', 'source', 'mode', 'summary', 'edit', 'execution'], 'candidate input');
  id(input.id, 'candidate id'); id(input.target_id, 'target id'); string(input.summary, 'candidate summary', 500);
  if (!['replace', 'masked'].includes(input.mode)) throw new Error('Unsupported candidate mode');
  if (input.base_revision === undefined) throw new Error('Candidate needs an explicit base revision');
  signal?.throwIfAborted();
  const project = await readProject(root, { revision: input.base_revision });
  await assertCandidateSlot(root, input.id);
  const object = project.document.objects.find(object => object.id === input.target_id);
  if (!object || object.kind !== 'image') throw new Error('Candidate target must be an existing image object');
  if (object.locked) throw new Error(`Object is locked: ${object.id}`);
  const asset = project.document.assets.find(asset => asset.id === object.asset_id);
  const source = await importRaster({ id: 'candidate-source', source: input.source });
  const receipt = input.execution === undefined ? null : await readExecution(root, input.execution, source.asset);
  if (source.asset.width !== asset.width || source.asset.height !== asset.height) throw new Error('Candidate must align with target raster dimensions; resize explicitly before staging');
  let edit = null, qa = null, png = source.rendered;
  const masks = [];
  if (input.mode === 'masked') {
    record(input.edit, ['context', 'generation_mask', 'protection_mask', 'blend_mask'], 'edit input');
    edit = { coordinate_space: 'target-raster', width: asset.width, height: asset.height, context: structuredClone(input.edit.context) };
    for (const key of ['generation_mask', 'protection_mask', 'blend_mask']) {
      const mask = await importMask(input.edit[key], asset.width, asset.height, { protection: key === 'protection_mask' });
      edit[key] = { file: `masks/${mask.sha256}.png`, sha256: mask.sha256, width: mask.width, height: mask.height };
      masks.push({ key, ...mask });
    }
    const original = (await readAsset(root, asset)).rendered;
    const result = await compositeRaster(original, source.rendered, { ...edit,
      generation: masks.find(mask => mask.key === 'generation_mask').data, protection: masks.find(mask => mask.key === 'protection_mask').data,
      blend: masks.find(mask => mask.key === 'blend_mask').data }, { signal });
    png = result.png; qa = result.qa;
  } else {
    if (input.edit !== undefined) throw new Error('Replacement input must not carry mask metadata');
    if (sha256(png) === asset.render_sha256 || await sameDecodedPixels(png, (await readAsset(root, asset)).rendered)) throw new Error('Candidate makes no raster change');
  }
  if (receipt?.parameters.background === 'transparent') requireAlpha(await inspectAlpha(png));
  if (png.length > LIMITS.renderBytes) throw new Error('Candidate output byte limit exceeded');
  signal?.throwIfAborted();
  const hash = sha256(png);
  const output = { id: `image-${hash.slice(0, 32)}`, file: `assets/${hash}.png`, sha256: hash, format: 'png', width: asset.width, height: asset.height, render_file: `assets/${hash}.png`, render_sha256: hash };
  const candidate = { schema: CANDIDATE_SCHEMA, id: input.id, project_id: project.document.project_id, base_revision: project.document.revision,
    base_sha256: project.sha256, target_id: object.id, base_asset: asset, mode: input.mode, summary: input.summary,
    source: source.asset, output, edit, qa };
  if (input.execution !== undefined) candidate.execution = structuredClone(input.execution);
  await regularPath(path.join(root, 'assets'), { directory: true });
  await saveAsset(root, source);
  await saveAsset(root, { asset: output, original: png, rendered: png });
  if (masks.length) {
    await ensureDirectory(path.join(root, 'masks'));
    for (const mask of masks) await writeOnce(path.join(root, edit[mask.key].file), { bytes: mask.bytes }, { expected: mask.sha256 });
  }
  signal?.throwIfAborted();
  const result = await publishCandidate(root, candidate);
  const current = await readProject(root);
  return { candidate, sha256: result.sha256, status: current.sha256 === candidate.base_sha256 ? 'ready' : 'stale', current_revision: current.document.revision };
}

function accepted(entry, project) {
  const decision = Object.hasOwn(project.candidate_decisions, entry.candidate.id) ? project.candidate_decisions[entry.candidate.id] : undefined;
  if (decision && decision.sha256 !== entry.sha256) throw new Error('Accepted candidate digest mismatch');
  return decision;
}

export async function inspectCandidate(root, candidateId) {
  const current = await readProject(root);
  const entry = await readCandidateEntry(root, candidateId);
  const base = entry.candidate.base_revision === current.document.revision ? current : await readProject(root, { revision: entry.candidate.base_revision });
  await verifyCandidateAgainst(root, base, entry);
  const decision = accepted(entry, current), discarded = await readDiscard(entry), pending = await decisionPending(entry);
  if (decision && discarded) throw new Error('Inconsistent candidate decisions');
  const stale = current.sha256 !== entry.candidate.base_sha256;
  const status = decision ? 'accepted' : discarded ? 'discarded' : pending ? 'decision_pending' : stale ? 'stale' : 'ready';
  const object = current.document.objects.find(object => object.id === entry.candidate.target_id);
  return { candidate: entry.candidate, sha256: entry.sha256, status, current_revision: current.document.revision, accepted_revision: decision?.revision ?? null,
    applied_in_current: !!decision && object?.asset_id === entry.candidate.output.id, stale, decision_pending: pending };
}

export async function listCandidates(root) {
  await readProject(root);
  const ids = await candidateIds(root);
  if (ids.length > 64) throw new Error('Candidate count limit exceeded');
  const results = [];
  // One damaged entry is reported in place; candidate-read/accept stay strict.
  for (const candidateId of ids) {
    try { results.push(await inspectCandidate(root, candidateId)); }
    catch (error) {
      const incomplete = error.code === 'ENOENT' && path.basename(error.path ?? '') === 'candidate.json';
      results.push({ candidate_id: candidateId, status: incomplete ? 'incomplete' : 'unreadable',
        error: incomplete ? 'candidate.json missing (interrupted staging); inspect and remove the directory to reuse this ID' : error.message });
    }
  }
  return results;
}

export async function unlockCandidate(root, input) {
  record(input, ['candidate_id', 'author', 'summary'], 'unlock input');
  await readProject(root);
  const released = await releaseDecisionLock(root, input.candidate_id, input.author, input.summary);
  return { status: 'unlocked', ...released, candidate: await inspectCandidate(root, input.candidate_id) };
}

export async function discardCandidate(root, input) {
  record(input, ['candidate_id', 'author', 'summary'], 'discard input');
  return withDecisionLock(root, input.candidate_id, async () => {
    const project = await readProject(root), entry = await readCandidateEntry(root, input.candidate_id);
    if (entry.candidate.project_id !== project.document.project_id) throw new Error('Candidate project identity mismatch');
    if (accepted(entry, project)) throw new Error('Candidate already accepted');
    if (await readDiscard(entry)) throw new Error('Candidate already discarded');
    validateDecision(input.author, input.summary);
    const decision = { candidate_id: input.candidate_id, candidate_sha256: entry.sha256, author: input.author, summary: input.summary };
    await writeOnce(path.join(entry.directory, 'discard.json'), { bytes: candidateBytes(decision) }, { conflict: 'Candidate already discarded' });
    return { status: 'discarded', ...decision, project_revision: project.document.revision };
  });
}

export async function acceptCandidate(root, input, options) {
  record(input, ['candidate_id', 'base_revision', 'author', 'summary'], 'accept input');
  return editBatch(root, { base_revision: input.base_revision, author: input.author, summary: input.summary,
    operations: [{ type: 'accept_candidate', candidate_id: input.candidate_id }] }, options);
}

export async function compareCandidate(root, candidateId, output) {
  const inspected = await inspectCandidate(root, candidateId);
  output = path.resolve(output);
  await regularPath(path.dirname(output), { directory: true });
  await assertOutsideProject(root, output);
  await fs.mkdir(output);
  // Candidate storage does not load the renderer unless comparison is requested.
  const { renderProject } = await import('./render.mjs');
  try {
    const before = await renderProject(root, path.join(output, 'before'), { revision: inspected.candidate.base_revision, previewMax: 640 });
    const after = await renderProject(root, path.join(output, 'after'), { candidateId, previewMax: 640 });
    const a = await fs.readFile(path.join(before.output, 'image.png')), b = await fs.readFile(path.join(after.output, 'image.png'));
    const width = before.receipt.outputs.png.width, height = before.receipt.outputs.png.height;
    const png = await sharp({ create: { width: width * 2, height, channels: 4, background: '#ffffff' } }).composite([{ input: a, left: 0, top: 0 }, { input: b, left: width, top: 0 }]).png().toBuffer();
    await writeOnce(path.join(output, 'comparison.png'), { bytes: png });
    const report = { status: 'completed', candidate_id: candidateId, candidate_sha256: inspected.sha256, basis_revision: inspected.candidate.base_revision,
      current_revision_at_check: inspected.current_revision, candidate_status_at_check: inspected.status, panels: { left: 'before/image.png', right: 'after/image.png' },
      image_sha256: sha256(png), protection_qa: inspected.candidate.qa, visual_quality: 'UNVERIFIED' };
    await writeOnce(path.join(output, 'comparison.json'), { bytes: candidateBytes(report) });
    return { output, report };
  } catch (error) {
    await writeOnce(path.join(output, 'comparison.json'), { bytes: candidateBytes({ status: 'failed', error: error.message, visual_quality: 'UNVERIFIED' }) });
    throw error;
  }
}
