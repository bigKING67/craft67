import * as fs from 'node:fs/promises';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { sha256, writeOnce } from '../local-production/content-store.mjs';
import { LIMITS, record, id, number, string, digest, validateAsset } from './document.mjs';
import { regularPath, readBytes, readAsset } from './raster.mjs';
import { maskBytes, compositeRaster, validateContext } from './composite.mjs';
import { validateExecution, readExecution } from './provider-store.mjs';
import { inspectAlpha, requireAlpha } from './provider-alpha.mjs';

export const CANDIDATE_SCHEMA = 'creative-craft.local-image-candidate.v1';
export const candidateBytes = value => Buffer.from(`${JSON.stringify(value, null, 2)}\n`);
export const candidateDirectory = (root, candidateId) => { id(candidateId, 'candidate id'); return path.join(root, 'candidates', candidateId); };

export async function ensureDirectory(directory) {
  await regularPath(path.dirname(directory), { directory: true });
  try { await fs.mkdir(directory); } catch (error) { if (error.code !== 'EEXIST') throw error; }
  await regularPath(directory, { directory: true });
}

// Only candidate-shaped directories count; stray entries such as .DS_Store do not.
export async function candidateIds(root) {
  const directory = path.join(root, 'candidates');
  try { await regularPath(directory, { directory: true }); }
  catch (error) { if (error.code === 'ENOENT') return []; throw error; }
  const valid = name => { try { id(name); return true; } catch { return false; } };
  return (await fs.readdir(directory, { withFileTypes: true })).filter(entry => entry.isDirectory() && valid(entry.name)).map(entry => entry.name).sort();
}

export async function assertCandidateSlot(root, candidateId) {
  const ids = await candidateIds(root);
  try { await fs.lstat(candidateDirectory(root, candidateId)); throw new Error('Candidate already exists'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  if (ids.length >= 64) throw new Error('Candidate count limit exceeded');
}

export function validateDecision(author, summary) {
  if (!['human', 'agent', 'system'].includes(author)) throw new Error('Invalid decision author');
  string(summary, 'decision summary', 500);
}

function validateMask(binding, width, height) {
  record(binding, ['file', 'sha256', 'width', 'height'], 'mask binding'); digest(binding.sha256);
  if (binding.file !== `masks/${binding.sha256}.png` || binding.width !== width || binding.height !== height) throw new Error('Invalid mask binding');
}

export function validateCandidate(candidate) {
  record(candidate, ['schema', 'id', 'project_id', 'base_revision', 'base_sha256', 'target_id', 'base_asset', 'mode', 'summary', 'source', 'output', 'edit', 'qa', 'execution'], 'candidate');
  if (candidate.schema !== CANDIDATE_SCHEMA) throw new Error('Unsupported candidate schema');
  id(candidate.id, 'candidate id'); id(candidate.project_id, 'project id'); id(candidate.target_id, 'target id');
  number(candidate.base_revision, 'base revision', 1, LIMITS.revisions, true); digest(candidate.base_sha256); string(candidate.summary, 'candidate summary', 500);
  for (const asset of [candidate.base_asset, candidate.source, candidate.output]) validateAsset(asset);
  if (candidate.execution !== undefined) validateExecution(candidate.execution);
  const { width, height } = candidate.base_asset;
  if ([candidate.source, candidate.output].some(asset => asset.width !== width || asset.height !== height)) throw new Error('Candidate must align with target raster dimensions');
  if (candidate.output.format !== 'png' || candidate.output.sha256 !== candidate.output.render_sha256) throw new Error('Candidate output must be a canonical PNG');
  if (!['replace', 'masked'].includes(candidate.mode)) throw new Error('Unsupported candidate mode');
  if (candidate.mode === 'replace') {
    if (candidate.edit !== null || candidate.qa !== null) throw new Error('Replacement has no mask protection guarantee');
  } else {
    record(candidate.edit, ['coordinate_space', 'width', 'height', 'context', 'generation_mask', 'protection_mask', 'blend_mask'], 'candidate edit');
    if (candidate.edit.coordinate_space !== 'target-raster' || candidate.edit.width !== width || candidate.edit.height !== height) throw new Error('Unsupported mask coordinate space');
    validateContext(candidate.edit.context, width, height);
    for (const key of ['generation_mask', 'protection_mask', 'blend_mask']) validateMask(candidate.edit[key], width, height);
    record(candidate.qa, ['color_space', 'alpha_blend', 'protected_pixels', 'outside_blend_pixels', 'changed_pixels', 'protected_changed_pixels', 'outside_blend_changed_pixels'], 'composite QA');
    if (candidate.qa.color_space !== 'srgb' || candidate.qa.alpha_blend !== 'premultiplied') throw new Error('Unsupported composite QA profile');
    for (const key of ['protected_pixels', 'outside_blend_pixels', 'changed_pixels', 'protected_changed_pixels', 'outside_blend_changed_pixels']) number(candidate.qa[key], key, 0, width * height, true);
    if (candidate.qa.protected_changed_pixels || candidate.qa.outside_blend_changed_pixels || !candidate.qa.changed_pixels) throw new Error('Candidate protection QA failed');
  }
  return candidate;
}

async function boundBytes(root, binding, { rendered = false, limit = LIMITS.sourceBytes } = {}) {
  const file = rendered ? binding.render_file : binding.file;
  const expected = rendered ? binding.render_sha256 : binding.sha256;
  const bytes = await readBytes(path.join(root, file), limit);
  if (sha256(bytes) !== expected) throw new Error(`Candidate binding digest mismatch: ${file}`);
  return bytes;
}

export async function readCandidateEntry(root, candidateId) {
  const directory = candidateDirectory(root, candidateId);
  const bytes = await readBytes(path.join(directory, 'candidate.json'), 100_000);
  const candidate = validateCandidate(JSON.parse(bytes.toString('utf8')));
  if (candidate.id !== candidateId) throw new Error('Candidate identity mismatch');
  const { original: source, rendered } = await readAsset(root, candidate.source);
  const receipt = candidate.execution === undefined ? null : await readExecution(root, candidate.execution, candidate.source);
  const { original: output } = await readAsset(root, candidate.output);
  if (receipt?.parameters.background === 'transparent') requireAlpha(await inspectAlpha(output));
  let masks;
  if (candidate.mode === 'masked') {
    const { width, height } = candidate.edit;
    masks = {};
    for (const key of ['generation_mask', 'protection_mask', 'blend_mask']) {
      const bytes = await boundBytes(root, candidate.edit[key]);
      masks[key] = await maskBytes(bytes, width, height, { protection: key === 'protection_mask' });
    }
  }
  return { directory, candidate, sha256: sha256(bytes), source, rendered, output, masks };
}

export async function verifyCandidateAgainst(root, project, entry) {
  const candidate = entry.candidate, doc = project.document;
  if (candidate.project_id !== doc.project_id || candidate.base_revision !== doc.revision || candidate.base_sha256 !== project.sha256) throw new Error('Candidate base revision conflict: re-read and restage explicitly');
  const object = doc.objects.find(object => object.id === candidate.target_id);
  if (!object || object.kind !== 'image') throw new Error('Candidate target must be an existing image object');
  const asset = doc.assets.find(asset => asset.id === object.asset_id);
  if (JSON.stringify(asset) !== JSON.stringify(candidate.base_asset)) throw new Error('Candidate target asset binding changed');
  let expected;
  if (candidate.mode === 'replace') expected = entry.rendered;
  else {
    const original = await boundBytes(root, candidate.base_asset, { rendered: true, limit: LIMITS.renderBytes });
    const result = await compositeRaster(original, entry.rendered, { ...candidate.edit,
      generation: entry.masks.generation_mask.data, protection: entry.masks.protection_mask.data, blend: entry.masks.blend_mask.data });
    expected = result.png;
    if (JSON.stringify(result.qa) !== JSON.stringify(candidate.qa)) throw new Error('Candidate QA does not match recomputed composite');
  }
  if (sha256(expected) !== candidate.output.sha256 || !expected.equals(entry.output)) throw new Error('Candidate output differs from recomputed result');
  return object;
}

export async function readDiscard(entry) {
  const file = path.join(entry.directory, 'discard.json');
  let bytes;
  // 500 UTF-16 units may each need a six-byte JSON escape; fields and IDs fit
  // in the remaining space. Keep every accepted summary readable after writing.
  try { bytes = await readBytes(file, 4096); } catch (error) { if (error.code === 'ENOENT') return null; throw error; }
  const value = JSON.parse(bytes.toString('utf8'));
  record(value, ['candidate_id', 'candidate_sha256', 'author', 'summary'], 'discard');
  if (value.candidate_id !== entry.candidate.id || value.candidate_sha256 !== entry.sha256) throw new Error('Discard decision binding mismatch');
  validateDecision(value.author, value.summary);
  return value;
}

export async function decisionPending(entry) {
  try { await readBytes(path.join(entry.directory, '.decision-lock'), 2000); return true; }
  catch (error) { if (error.code === 'ENOENT') return false; throw error; }
}

export async function withDecisionLock(root, candidateId, run) {
  const directory = await regularPath(candidateDirectory(root, candidateId), { directory: true });
  const file = path.join(directory, '.decision-lock');
  try { await fs.writeFile(file, candidateBytes({ pid: process.pid, created_at: new Date().toISOString() }), { flag: 'wx' }); }
  catch (error) { if (error.code === 'EEXIST') throw new Error('Candidate decision in progress; inspect before recovery'); throw error; }
  try { return await run(); } finally { await fs.unlink(file); }
}

// Manual recovery for a lock left by a killed process. Decisions are re-derived
// from history/discard.json, so releasing the lock never fabricates an outcome.
export async function releaseDecisionLock(root, candidateId, author, summary) {
  validateDecision(author, summary);
  const directory = await regularPath(candidateDirectory(root, candidateId), { directory: true });
  const file = path.join(directory, '.decision-lock');
  let bytes;
  try { bytes = await readBytes(file, 2000); } catch (error) { if (error.code === 'ENOENT') throw new Error('No decision lock to release'); throw error; }
  let holder = null;
  try { holder = JSON.parse(bytes.toString('utf8')); } catch {}
  if (Number.isSafeInteger(holder?.pid) && holder.pid > 0) {
    let alive = true;
    try { process.kill(holder.pid, 0); } catch (error) { alive = error.code === 'EPERM'; }
    if (alive) throw new Error('Decision lock holder process is still running');
  }
  const released = { candidate_id: candidateId, author, summary, released_at: new Date().toISOString(), lock_sha256: sha256(bytes), lock: holder };
  await writeOnce(path.join(directory, `lock-release-${randomUUID()}.json`), { bytes: candidateBytes(released) });
  await fs.unlink(file);
  return released;
}

export async function publishCandidate(root, candidate) {
  validateCandidate(candidate);
  await assertCandidateSlot(root, candidate.id);
  await ensureDirectory(path.join(root, 'candidates'));
  const directory = candidateDirectory(root, candidate.id);
  await fs.mkdir(directory);
  try {
    if ((await candidateIds(root)).length > 64) throw new Error('Candidate count limit exceeded');
    const bytes = candidateBytes(candidate);
    await writeOnce(path.join(directory, 'candidate.json'), { bytes }, { expected: sha256(bytes), conflict: 'Candidate already exists' });
    return { directory, candidate, sha256: sha256(bytes) };
  } catch (error) { await fs.rm(directory, { recursive: true, force: true }); throw error; }
}
