import * as fs from 'node:fs/promises';
import path from 'node:path';
import { regularPath, readBytes, importRaster, saveAsset, readAsset } from './raster.mjs';
export { regularPath, importRaster } from './raster.mjs';
import { readCandidateEntry, verifyCandidateAgainst, readDiscard, decisionPending, withDecisionLock } from './candidate-store.mjs';
import { sha256, writeOnce } from '../local-production/content-store.mjs';
import { SCHEMA, LIMITS, validateDocument, record, id, number, string } from './document.mjs';
import { fontManifest, installedFont, checkGlyphs } from './font.mjs';
import { preparePhotoProject } from './photo-layout.mjs';

const fail = message => { throw new Error(message); };
export const encode = doc => Buffer.from(`${JSON.stringify(doc, null, 2)}\n`);
const revisionName = revision => `revisions/${String(revision).padStart(6, '0')}.json`;

async function verifyBindings(root, doc) {
  const font = await readBytes(path.join(root, doc.font.file), fontManifest.bytes);
  checkGlyphs(font, doc.objects.filter(object => object.kind === 'text').map(object => object.text));
  for (const asset of doc.assets) await readAsset(root, asset);
  return font;
}

async function checkTextLayout(root, doc, font) {
  const objects = doc.objects.filter(object => object.kind === 'text' && object.visible);
  if (!objects.length) return;
  const { compose } = await import('./render-worker.mjs');
  // Measure with the export engine without reading or writing temporary assets.
  await compose({ root, font, document: { ...doc, assets: [], objects } });
}

// Fail before decoding any asset; mkdir remains the exclusive claim.
async function newProjectRoot(root) {
  root = path.resolve(root);
  await regularPath(path.dirname(root), { directory: true });
  let exists = false;
  try { await fs.lstat(root); exists = true; }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  if (exists) fail('Project already exists');
  return root;
}

export async function createProject(root, input) {
  record(input, ['project_id', 'title', 'canvas', 'assets', 'objects'], 'create input');
  if (!Array.isArray(input.assets) || input.assets.length > LIMITS.assets) fail('Invalid asset inputs');
  root = await newProjectRoot(root);
  const imports = [];
  for (const asset of input.assets) imports.push(await importRaster(asset));
  return createPreparedProject(root, input, imports);
}

export async function createPhotoProject(root, brief, { dryRun = false } = {}) {
  root = await newProjectRoot(root);
  const prepared = await preparePhotoProject(brief);
  const result = await createPreparedProject(root, prepared.input, prepared.imports, { dryRun, checkText: true });
  return { ...result, layout: prepared.layout };
}

// Prepared imports remain internal so the new entry shares the same exclusive
// publication and cleanup path without decoding or reading the source twice.
async function createPreparedProject(root, input, imports, { dryRun = false, checkText = false } = {}) {
  const font = await installedFont();
  const doc = validateDocument({ schema: SCHEMA, project_id: input.project_id, title: input.title,
    revision: 1, parent_sha256: null, canvas: structuredClone(input.canvas), assets: imports.map(value => value.asset),
    font: { profile: fontManifest.profile, family: fontManifest.family, file: `fonts/${fontManifest.sha256}.otf`, sha256: fontManifest.sha256, weight: fontManifest.weight },
    objects: structuredClone(input.objects), change: { author: 'system', summary: 'Create local image project', operations: ['create'] } });
  checkGlyphs(font, doc.objects.filter(object => object.kind === 'text').map(object => object.text));
  if (checkText) await checkTextLayout(root, doc, font);
  if (dryRun) return { root, document: doc, sha256: sha256(encode(doc)), dry_run: true };
  // Only remove a directory this invocation created, never a user's project.
  await fs.mkdir(root);
  try {
    for (const folder of ['assets', 'fonts', 'revisions']) await fs.mkdir(path.join(root, folder));
    for (const imported of imports) await saveAsset(root, imported);
    await writeOnce(path.join(root, doc.font.file), { bytes: font }, { expected: fontManifest.sha256 });
    const bytes = encode(doc);
    await writeOnce(path.join(root, revisionName(1)), { bytes }, { expected: sha256(bytes), conflict: 'Project already exists' });
    return { root, document: doc, sha256: sha256(bytes) };
  } catch (error) { await fs.rm(root, { recursive: true, force: true }); throw error; }
}

export async function readProject(root, { revision } = {}) {
  root = await regularPath(root, { directory: true });
  const directory = await regularPath(path.join(root, 'revisions'), { directory: true });
  const files = await fs.readdir(directory);
  const revisions = files.filter(file => /^\d{6}\.json$/.test(file)).map(file => Number(file.slice(0, 6))).sort((a, b) => a - b);
  if (!revisions.length) fail('Incomplete project: no saved revision (interrupted create); inspect, remove the directory and create again');
  if (revisions.length > LIMITS.revisions || revisions.some((value, index) => value !== index + 1)) fail('Broken revision sequence');
  const latest = revisions.at(-1);
  revision ??= latest;
  number(revision, 'requested revision', 1, latest, true);
  let parent = null, selected, selectedBytes;
  const candidateDecisions = new Map();
  // Validate the complete ancestry of the requested revision, not only HEAD.
  for (let current = 1; current <= revision; current++) {
    const bytes = await readBytes(path.join(root, revisionName(current)), 1_000_000);
    const doc = validateDocument(JSON.parse(bytes.toString('utf8')));
    if (doc.revision !== current || doc.parent_sha256 !== parent) fail('Broken revision digest chain');
    if (selected && (doc.project_id !== selected.project_id || doc.title !== selected.title)) fail('Project identity changed');
    if (doc.change.candidate) {
      const { id, sha256: candidateDigest } = doc.change.candidate;
      if (candidateDecisions.has(id)) fail('Candidate accepted twice in history');
      const manifest = await readBytes(path.join(root, 'candidates', id, 'candidate.json'), 100_000);
      if (candidateDigest !== sha256(manifest)) fail('Accepted candidate digest mismatch');
      candidateDecisions.set(id, { sha256: candidateDigest, revision: current });
    }
    parent = sha256(bytes); selected = doc; selectedBytes = bytes;
  }
  const font = await verifyBindings(root, selected);
  return { root, document: selected, sha256: sha256(selectedBytes), latest_revision: latest, font, candidate_decisions: Object.fromEntries(candidateDecisions) };
}

function objectAt(doc, objectId) {
  id(objectId, 'object id');
  const index = doc.objects.findIndex(object => object.id === objectId);
  if (index < 0) fail(`Unknown object: ${objectId}`);
  return index;
}

export async function editBatch(root, batch, { dryRun = false } = {}) {
  record(batch, ['base_revision', 'author', 'summary', 'operations'], 'edit batch');
  if (!Array.isArray(batch.operations) || !batch.operations.length || batch.operations.length > LIMITS.operations) fail('Invalid edit operations');
  if (batch.operations.some(op => op?.type === 'accept_candidate')) {
    if (batch.operations.length !== 1) fail('Candidate acceptance must be isolated');
    const candidateId = batch.operations[0].candidate_id;
    id(candidateId, 'candidate id');
    if (!dryRun) return withDecisionLock(root, candidateId, () => applyBatch(root, batch, { dryRun }));
  }
  return applyBatch(root, batch, { dryRun });
}

export async function candidateDocument(root, project, candidateId, entry) {
  entry ??= await readCandidateEntry(root, candidateId);
  const object = await verifyCandidateAgainst(root, project, entry);
  if (object.locked) fail(`Object is locked: ${object.id}`);
  const doc = structuredClone(project.document);
  const output = entry.candidate.output;
  const existing = doc.assets.find(asset => asset.id === output.id);
  if (existing && JSON.stringify(existing) !== JSON.stringify(output)) fail('Candidate output asset id conflict');
  if (!existing) doc.assets.push(structuredClone(output));
  doc.objects.find(value => value.id === object.id).asset_id = output.id;
  doc.change = { author: 'system', summary: `Read-only preview of candidate ${candidateId}`, operations: ['candidate_preview'] };
  validateDocument(doc);
  return { document: doc, entry };
}

async function applyBatch(root, batch, { dryRun }) {
  const current = await readProject(root);
  if (batch.base_revision !== current.document.revision) fail(`Revision conflict: expected ${current.document.revision}, received ${batch.base_revision}`);
  if (current.document.revision >= LIMITS.revisions) fail(`Revision limit reached (${LIMITS.revisions}); create a new project from the current document to continue editing`);
  let doc = structuredClone(current.document);
  const imports = [];
  let candidateChange;
  // Revert and lock changes are isolated so a batch cannot unlock, alter, then
  // relock an object while disguising the change as a protected edit.
  for (const op of batch.operations) {
    if (op?.type === 'revert_to' && batch.operations.length !== 1) fail('Revert must be an isolated operation');
    if (op?.type === 'update_object' && Object.hasOwn(op.patch ?? {}, 'locked') &&
        (batch.operations.length !== 1 || Object.keys(op.patch).length !== 1)) fail('Lock changes must be isolated');
  }
  for (const op of batch.operations) {
    const fields = { add_asset: ['asset'], add_object: ['object'], update_object: ['id', 'patch'], remove_object: ['id'], reorder_objects: ['ids'], set_canvas: ['canvas'], revert_to: ['revision'], accept_candidate: ['candidate_id'] }[op?.type];
    if (!Array.isArray(fields)) fail(`Unsupported operation: ${op?.type}`);
    record(op, ['type', ...fields], 'operation');
    switch (op.type) {
      case 'accept_candidate': {
        if (Object.hasOwn(current.candidate_decisions, op.candidate_id)) fail('Candidate already accepted');
        const entry = await readCandidateEntry(root, op.candidate_id);
        if (await readDiscard(entry)) fail('Candidate is discarded');
        if (dryRun && await decisionPending(entry)) fail('Candidate decision in progress');
        const prepared = await candidateDocument(root, current, op.candidate_id, entry);
        doc = prepared.document;
        candidateChange = { id: op.candidate_id, sha256: entry.sha256 };
        break;
      }
      case 'add_asset': { const imported = await importRaster(op.asset); doc.assets.push(imported.asset); imports.push(imported); break; }
      case 'add_object': doc.objects.push(structuredClone(op.object)); break;
      case 'update_object': {
        const index = objectAt(doc, op.id), object = doc.objects[index];
        const mutable = Object.keys(object).filter(key => !['id', 'kind'].includes(key));
        record(op.patch, mutable, 'object patch');
        if (!Object.keys(op.patch).length) fail('Empty object patch');
        if (object.locked && !Object.hasOwn(op.patch, 'locked')) fail(`Object is locked: ${op.id}`);
        doc.objects[index] = { ...object, ...structuredClone(op.patch) }; break;
      }
      case 'remove_object': {
        const index = objectAt(doc, op.id); if (doc.objects[index].locked) fail(`Object is locked: ${op.id}`);
        doc.objects.splice(index, 1); break;
      }
      case 'reorder_objects': {
        if (!Array.isArray(op.ids) || op.ids.length !== doc.objects.length || new Set(op.ids).size !== op.ids.length) fail('Reorder must include every object exactly once');
        const ordered = op.ids.map(value => doc.objects[objectAt(doc, value)]);
        for (let index = 0; index < doc.objects.length; index++) if (doc.objects[index].locked && ordered[index].id !== doc.objects[index].id) fail('Cannot reorder a locked object');
        doc.objects = ordered; break;
      }
      case 'set_canvas': doc.canvas = structuredClone(op.canvas); break;
      case 'revert_to': {
        number(op.revision, 'revert revision', 1, current.document.revision - 1, true);
        const previous = (await readProject(root, { revision: op.revision })).document;
        for (const [index, locked] of current.document.objects.entries()) {
          if (!locked.locked) continue;
          const earlier = previous.objects.find(object => object.id === locked.id);
          if (!earlier || JSON.stringify({ ...earlier, locked: true }) !== JSON.stringify(locked)) fail(`Revert would change locked object: ${locked.id}`);
          if (previous.objects[index]?.id !== locked.id) fail(`Revert would reorder locked object: ${locked.id}`);
        }
        doc.canvas = structuredClone(previous.canvas); doc.assets = structuredClone(previous.assets); doc.objects = structuredClone(previous.objects);
        // Lock state is an explicit current policy, not an undo side effect.
        for (const object of doc.objects) {
          const now = current.document.objects.find(value => value.id === object.id);
          object.locked = now?.locked ?? false;
        }
        break;
      }
      default: fail(`Unsupported operation: ${op.type}`);
    }
  }
  doc.revision++; doc.parent_sha256 = current.sha256;
  doc.change = { author: batch.author, summary: batch.summary, operations: batch.operations.map(op => op.type) };
  if (candidateChange) doc.change.candidate = candidateChange;
  validateDocument(doc);
  checkGlyphs(current.font, doc.objects.filter(object => object.kind === 'text').map(object => object.text));
  // Unlocking changes no pixels and must remain possible to repair a locked
  // legacy layout. Isolation and patch validation above prohibit other changes.
  const unlockOnly = batch.operations.length === 1 && batch.operations[0].type === 'update_object' && batch.operations[0].patch.locked === false;
  if (!unlockOnly) await checkTextLayout(current.root, doc, current.font);
  if (dryRun) return { dry_run: true, document: doc, sha256: sha256(encode(doc)) };
  await regularPath(path.join(root, 'assets'), { directory: true });
  for (const imported of imports) await saveAsset(root, imported);
  const bytes = encode(doc);
  // Immutable exclusive publication makes concurrent edits on the same base
  // have one winner. No mutable HEAD pointer or user-file replacement.
  await writeOnce(path.join(current.root, revisionName(doc.revision)), { bytes }, { expected: sha256(bytes), conflict: 'Revision conflict: another edit was published' });
  return { root: current.root, document: doc, sha256: sha256(bytes) };
}
