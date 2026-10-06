import * as fs from 'node:fs/promises';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { bindCaptionFont, installCaptionFont, planCaptionFont, validateCaptionFont, verifyCaptionFont, activeCaptions } from './caption-font.mjs';
import { SCHEMA_V1, SCHEMA_V2, fail, id, integer, keys, number, text, validateCanvas, validateCaptionStyle, validateAssetFields, validateNewAssetOrigin,
  validateV2, validateTemplateBindings, migrateV1 } from './edit-document.mjs';
import { applyOperations, diffDocuments, operationsSha256 } from './operations.mjs';
import { checkVolumeAutomation } from './timeline.mjs';
import { TEMPLATES, TEMPLATE_ID, runtimeTemplate } from './templates.mjs';
import { checkLockedTemplates, installTemplates, loadPinnedTemplates, planTemplateBindings, renderedTemplateSha, usedTemplates } from './template-binding.mjs';
import { mediaTool } from './media-analysis.mjs';
import { digest, sha256, writeOnce } from './content-store.mjs';
import { bindAlignment, probedFrameRate } from './source-frames.mjs';
import { carryAlignment, frameAlignment } from './frame-alignment.mjs';

export const run = promisify(execFile);
export const SCHEMA = SCHEMA_V1;
export { SCHEMA_V2, validateV2, validateCaptionStyle, migrateV1, digest };
export const readJson = async file => JSON.parse(await fs.readFile(file, 'utf8'));
// One identity for this tool: qa.json's tool and the review page's generator.
export const TOOL = { name: 'creative-craft-local-production', version: JSON.parse(await fs.readFile(new URL('./package.json', import.meta.url), 'utf8')).version };
const serialize = doc => `${JSON.stringify(doc, null, 2)}\n`;

// This is a local single-user tool, not a filesystem sandbox for hostile users.
export async function safePath(value) {
  const absolute = path.resolve(value);
  let cursor = path.parse(absolute).root;
  for (const part of absolute.slice(cursor.length).split(path.sep).filter(Boolean)) {
    cursor = path.join(cursor, part);
    const stat = await fs.lstat(cursor).catch(e => { if (e.code !== 'ENOENT') throw e; });
    if (stat?.isSymbolicLink()) fail(`Symlink not allowed: ${cursor}`);
  }
  return absolute;
}

// Single ffprobe invocation shared by import probing and render QA.
export async function ffprobeJson(file) {
  const { stdout } = await run(mediaTool('ffprobe'),
    ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', file],
    { timeout: 30000, maxBuffer: 4 * 1024 * 1024 });
  return JSON.parse(stdout);
}

// The video flag, width and height come from the first video stream of any
// kind, cover art included (unchanged since local-edit.v1). { frameRate: true }
// (EditDocument v2 asset import) adds frame_rate when probedFrameRate trusts
// it, which requires that same first video stream to be the picture (not cover
// art), so frame_rate, width and height always describe one stream.
export async function probe(file, { frameRate = false } = {}) {
  const result = await ffprobeJson(file);
  const video = result.streams.find(s => s.codec_type === 'video');
  const audio = result.streams.find(s => s.codec_type === 'audio');
  const duration = Number(result.format.duration);
  if (!number(duration, 0.001, 1800)) fail('Media duration must be 0–1800 seconds');
  const rate = frameRate ? probedFrameRate(result) : null;
  return { duration, video: Boolean(video), audio: Boolean(audio),
    width: video?.width ?? 0, height: video?.height ?? 0, ...(rate ? { frame_rate: rate } : {}) };
}

export function validate(project) {
  keys(project, ['schema_version', 'project_id', 'revision', 'parent_sha256', 'title', 'canvas', 'assets', 'clips', 'audio', 'caption_font']);
  if ('caption_font' in project) validateCaptionFont(project.caption_font);
  if (project.schema_version !== SCHEMA || !id(project.project_id) || !text(project.title) ||
      !integer(project.revision, 1, 999999)) fail('Invalid project identity');
  if (project.revision === 1 ? project.parent_sha256 !== null :
      typeof project.parent_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(project.parent_sha256)) fail('Invalid parent digest');
  validateCanvas(project.canvas);
  const { fps } = project.canvas;
  if (!Array.isArray(project.assets) || !project.assets.length || project.assets.length > 100 ||
      !Array.isArray(project.clips) || !project.clips.length || project.clips.length > 500 ||
      !Array.isArray(project.audio) || project.audio.length > 32) fail('Invalid project collections');
  const assets = new Map();
  for (const asset of project.assets) {
    validateAssetFields(asset);
    if (assets.has(asset.id)) fail('Invalid asset');
    assets.set(asset.id, asset);
  }
  const ids = new Set();
  let frames = 0;
  for (const clip of project.clips) {
    keys(clip, ['id', 'asset_id', 'in_seconds', 'frames', 'volume', 'fit', 'captions']);
    const asset = assets.get(clip.asset_id);
    if (!id(clip.id) || ids.has(clip.id) || !asset?.video || !number(clip.in_seconds, 0, 1800) ||
        !integer(clip.frames, 1, 600 * fps) || clip.in_seconds + clip.frames / fps > asset.duration + 0.001 ||
        !number(clip.volume, 0, 1) || !['contain', 'cover'].includes(clip.fit) || !Array.isArray(clip.captions) || clip.captions.length > 500) fail('Invalid clip or source range');
    ids.add(clip.id);
    for (const caption of clip.captions) {
      keys(caption, ['from', 'to', 'text', 'style']);
      if ('style' in caption) validateCaptionStyle(caption.style);
      if (!number(caption.from, 0, asset.duration) || !number(caption.to, 0, asset.duration) ||
          caption.to <= caption.from || !text(caption.text)) fail('Invalid source-timed caption');
    }
    frames += clip.frames;
  }
  if (frames > 600 * fps) fail('Output exceeds 10 minutes');
  for (const track of project.audio) {
    keys(track, ['id', 'asset_id', 'in_seconds', 'start_frame', 'frames', 'volume']);
    const asset = assets.get(track.asset_id);
    if (!id(track.id) || ids.has(track.id) || !asset?.audio || !number(track.in_seconds, 0, 1800) ||
        !integer(track.start_frame, 0, 600 * fps) || !integer(track.frames, 1, 600 * fps) ||
        track.in_seconds + track.frames / fps > asset.duration + 0.001 || !number(track.volume, 0, 1)) fail('Invalid audio range');
    ids.add(track.id);
  }
  return { frames, duration: frames / fps };
}

// Either document generation; v1 revisions stay readable and renderable.
// options (v2 only): { templates } or { structuralOnly } as for validateV2.
export const validateDocument = (doc, options) => doc?.schema_version === SCHEMA_V2 ? validateV2(doc, options) : validate(doc);

const revisionName = (revision) => `${String(revision).padStart(6, '0')}.json`;
// One revision with its template set and frame alignment:
// {doc, templates, alignment, verified}. templates is the bound set of a
// pinned revision, the execution-layer set of an unpinned v2 revision and null
// for v1. Callers that compile, check fonts or validate the document again pass
// it on explicitly. alignment (v2; null for v1, whose assets have no
// frame_rate) is decided here once, the same way: every asset with frame_rate
// has its file digest-checked (a changed or missing file fails the load, like a
// bound template) and re-probed (frameAlignment); doc is bound to the result,
// so every compiledView of it uses it. verified: Map asset id → real path of
// the files checked here (verifyAssets does not hash them again).
export async function loadProject(root, revision) {
  root = await safePath(root);
  const revisions = await safePath(path.join(root, 'revisions'));
  const names = (await fs.readdir(revisions)).filter(n => /^\d{6}\.json$/.test(n)).sort();
  if (!names.length) fail('No project revisions');
  const name = revision === undefined ? names.at(-1) : revisionName(revision);
  if (!names.includes(name)) fail('Revision not found');
  const file = await safePath(path.join(revisions, name));
  const project = JSON.parse(await fs.readFile(file, 'utf8'));
  let templates = null;
  if (project?.schema_version === SCHEMA_V2) {
    // Pinned templates: only the binding list's shape is checked before the
    // bound bytes are loaded (hash + template rules); a missing or altered
    // binding file fails here. Then one full validation types the graphic vars.
    if ('graphic_templates' in project) templates = await loadPinnedTemplates(root, [...validateTemplateBindings(project.graphic_templates).values()]);
    else templates = TEMPLATES;
  }
  validateDocument(project, { templates });
  if (revisionName(project.revision) !== name) fail('Revision filename mismatch');
  if (project.revision > 1) {
    const previous = await safePath(path.join(revisions, revisionName(project.revision - 1)));
    if (await digest(previous) !== project.parent_sha256) fail('Parent revision changed');
  }
  if (project.schema_version !== SCHEMA_V2) return { doc: project, templates, alignment: null, verified: new Map() };
  const verified = await checkAssetFiles(root, project.assets.filter(a => a.frame_rate));
  const alignment = await frameAlignment(project, verified);
  return { doc: bindAlignment(project, alignment), templates, alignment, verified };
}

// The document only (CLI read, callers that need no template set).
export const readProject = async (root, revision) => (await loadProject(root, revision)).doc;

async function publish(root, project) {
  const dir = await safePath(path.join(root, 'revisions')), bytes = serialize(project);
  // Atomic, no-replace publication. Two writers cannot publish the same revision.
  await writeOnce(path.join(dir, revisionName(project.revision)), { bytes }, { expected: sha256(bytes), conflict: 'Revision conflict; read the latest project' });
}

// v2: true for EditDocument v2 imports (create, add_asset), which record
// frame_rate; local-edit.v1 assets have no such field and are not probed for it.
async function importAsset(file, { v2 }) {
  if (typeof file !== 'string') fail('Invalid import');
  const source = await safePath(file);
  if (!(await fs.stat(source)).isFile()) fail('Source must be a file');
  const sha256 = await digest(source);
  return { source, asset: { file: `assets/${sha256}.media`, sha256, ...await probe(source, { frameRate: v2 }) } };
}

// Content-addressed copies; an existing identical file is reused, never replaced.
async function copyImports(root, imports) {
  for (const { source, asset } of imports) {
    await writeOnce(path.join(root, asset.file), { source }, { expected: asset.sha256, mismatch: 'Source changed during import' });
  }
}

// The spec format selects the project format, so existing hosts keep working:
// a v1 spec (clips/audio) creates a local-edit.v1 project that still accepts the
// v1 CLI and operations, and migrates on its first v2 edit batch; a v2 spec
// (tracks/items) creates an edit-document.v2 project.
// Everything createProject checks before it writes: spec keys, asset imports
// (probe and digest; nothing is copied), document and template validation and
// the volume-automation compile limits. apply-cuts uses it to refuse a spec it
// would otherwise write.
export async function prepareProject(spec) {
  const v1 = spec && typeof spec === 'object' && 'clips' in spec;
  keys(spec, v1 ? ['project_id', 'title', 'canvas', 'assets', 'clips', 'audio'] : ['project_id', 'title', 'canvas', 'assets', 'tracks', 'items']);
  if (!Array.isArray(spec.assets) || !spec.assets.length || spec.assets.length > (v1 ? 100 : 200)) fail('Invalid assets');
  const imports = [];
  for (const item of spec.assets) {
    keys(item, v1 ? ['id', 'path'] : ['id', 'path', 'origin']);
    if (!id(item.id)) fail('Invalid import');
    const origin = item.origin ?? { kind: 'import' };
    if (!v1) validateNewAssetOrigin(origin);
    const imported = await importAsset(item.path, { v2: !v1 });
    imported.asset = { id: item.id, ...imported.asset, ...(v1 ? {} : { origin }) };
    imports.push(imported);
  }
  let project;
  if (v1) {
    project = { schema_version: SCHEMA, project_id: spec.project_id, revision: 1, parent_sha256: null,
      title: spec.title, canvas: spec.canvas, assets: imports.map(i => i.asset), clips: spec.clips, audio: spec.audio ?? [] };
    validate(project);
  } else {
    project = { schema_version: SCHEMA_V2, project_id: spec.project_id, revision: 1, parent_sha256: null, title: spec.title,
      canvas: spec.canvas, assets: imports.map(i => i.asset), tracks: spec.tracks, items: spec.items,
      change: { author: 'system', summary: 'Created project', operations_sha256: null } };
  }
  // Graphics pin the execution-layer template bytes they are validated against.
  const { writes: templateWrites, templates } = v1 ? { writes: [], templates: null } : planTemplateBindings(null, project);
  validateDocument(project, { templates });
  if (!v1) checkVolumeAutomation(project); // Compile limits fail here, not at render.
  return { project, imports, templateWrites, templates };
}

export async function createProject(root, spec) {
  const { project, imports, templateWrites, templates } = await prepareProject(spec);
  root = await safePath(root);
  await fs.mkdir(root); // Existing projects are never replaced.
  await fs.mkdir(path.join(root, 'assets'));
  await fs.mkdir(path.join(root, 'revisions'));
  await copyImports(root, imports);
  // Not bound to a frame alignment: every asset was probed by the import rule
  // just now, so the structural view (each recorded frame_rate applied) is the
  // one loadProject will decide for these bytes.
  await bindCaptionFont(root, project, templates);
  await installTemplates(root, templateWrites);
  await publish(root, project);
  return project;
}

export async function editProject(root, expectedRevision, operations) {
  const project = await readProject(root);
  if (project.schema_version !== SCHEMA) fail('This project is edit-document.v2; v1 operations are not supported. Submit an edit batch (edit PROJECT BATCH.json)');
  if (project.revision !== expectedRevision) fail('Revision conflict; read the latest project');
  if (!Array.isArray(operations) || !operations.length || operations.length > 100) fail('Invalid operations');
  const next = structuredClone(project);
  for (const op of operations) {
    if (op.type === 'reorder') {
      keys(op, ['type', 'clip_ids']);
      if (!Array.isArray(op.clip_ids) || op.clip_ids.length !== next.clips.length || new Set(op.clip_ids).size !== next.clips.length) fail('Reorder must name every clip once');
      next.clips = op.clip_ids.map(key => next.clips.find(c => c.id === key) ?? fail('Unknown clip'));
    } else if (op.type === 'update_clip') {
      keys(op, ['type', 'clip_id', 'changes']);
      keys(op.changes, ['in_seconds', 'frames', 'volume', 'fit', 'captions', 'asset_id']);
      const clip = next.clips.find(c => c.id === op.clip_id) ?? fail('Unknown clip');
      if (op.changes.asset_id && op.changes.asset_id !== clip.asset_id && !('captions' in op.changes)) clip.captions = [];
      Object.assign(clip, op.changes);
    } else if (op.type === 'replace_clips') {
      keys(op, ['type', 'clips']);
      next.clips = op.clips;
    } else if (op.type === 'set_audio') {
      keys(op, ['type', 'audio']);
      next.audio = op.audio;
    } else fail('Unknown edit operation');
  }
  next.revision += 1;
  next.parent_sha256 = await digest(await safePath(path.join(root, 'revisions', revisionName(project.revision))));
  validate(next);
  await publish(root, next);
  return next;
}

const asV2 = doc => doc.schema_version === SCHEMA_V2 ? structuredClone(doc) : migrateV1(doc);

// Whole-document restore as a new revision. Locked tracks are frozen: a revert
// that would change any item on a currently locked track (or drop the track) is
// refused, and the track's own settings are kept from the current revision.
async function revertContent(root, base, op) {
  keys(op, ['type', 'revision']);
  if (!integer(op.revision, 1, base.revision - 1)) fail('revert_to requires an earlier revision');
  const loaded = await loadProject(root, op.revision), target = asV2(loaded.doc);
  // Template bindings come from the target (planTemplateBindings); graphics on
  // locked tracks must keep their template bytes (checkLockedTemplates).
  for (const track of base.tracks.filter(t => t.locked)) {
    const on = doc => JSON.stringify(doc.items.filter(i => i.track_id === track.id));
    if (!target.tracks.some(t => t.id === track.id) || on(base) !== on(target)) fail(`Track is locked: ${track.id}`);
  }
  // Lock state is current editorial intent, not history: a revert never unlocks,
  // and a locked track keeps its whole current definition (duck, name, …).
  const locked = new Map(base.tracks.filter(t => t.locked).map(t => [t.id, t]));
  const tracks = target.tracks.map(t => locked.has(t.id) ? structuredClone(locked.get(t.id)) : t);
  const next = { ...structuredClone(base), title: target.title, canvas: target.canvas, assets: target.assets, tracks, items: target.items };
  if (target.caption_font && !next.caption_font) next.caption_font = target.caption_font;
  return { next, target: { doc: target, templates: loaded.templates ?? TEMPLATES, alignment: loaded.alignment } };
}

// rebind_template {template}: the explicit, single-operation decision that moves
// one used template's binding to the current execution-layer bytes. Refused
// when the revision already renders it from those bytes (bound to them, or an
// unpinned historical revision, which renders the execution layer) and, via
// checkLockedTemplates, when a graphic using it is on a locked track.
function checkRebind(base, op) {
  keys(op, ['type', 'template']);
  if (typeof op.template !== 'string' || !TEMPLATE_ID.test(op.template)) fail('rebind_template requires a template id');
  if (!usedTemplates(base).includes(op.template)) fail(`rebind_template: template ${op.template} is not used by any graphic in revision ${base.revision}`);
  if (renderedTemplateSha(base, op.template) === runtimeTemplate(op.template).sha256) {
    fail(base.graphic_templates ? `rebind_template: ${op.template} is already bound to the current template bytes (no change)`
      : `rebind_template: revision ${base.revision} is not pinned and already renders ${op.template} from the current template bytes (no change)`);
  }
  return op.template;
}

// Edit batch v2: {base_revision, author, summary, operations[]}. All-or-nothing:
// every operation and the resulting document validate before anything is
// written. A v1 project first gets a pure migration revision (author
// "migration"), then the edit revision on top. dryRun returns the diff and
// writes nothing (add_asset only probes).
export async function editBatch(root, batch, { dryRun = false } = {}) {
  keys(batch, ['base_revision', 'author', 'summary', 'operations']);
  if (!integer(batch.base_revision, 1, 999999) || !['agent', 'human', 'system'].includes(batch.author) || !text(batch.summary) ||
      !Array.isArray(batch.operations) || !batch.operations.length || batch.operations.length > 100) fail('Invalid edit batch');
  root = await safePath(root);
  const { doc: latest, templates: latestTemplates, alignment: latestAlignment } = await loadProject(root);
  if (latest.revision !== batch.base_revision) fail('Revision conflict; read the latest project');
  let base = latest, baseTemplates = latestTemplates, baseAlignment = latestAlignment, baseSha = await digest(await safePath(path.join(root, 'revisions', revisionName(latest.revision)))), migration = null;
  if (latest.schema_version === SCHEMA) {
    migration = { ...migrateV1(latest), revision: latest.revision + 1, parent_sha256: baseSha,
      change: { author: 'migration', summary: `Migrated ${SCHEMA} revision ${latest.revision} to ${SCHEMA_V2}`, operations_sha256: null } };
    validateV2(migration);
    // v1 assets carry no frame_rate: the migration's alignment is empty.
    [base, baseTemplates, baseAlignment] = [bindAlignment(migration, []), TEMPLATES, []];
    baseSha = sha256(serialize(migration));
  }
  // A lock change is its own revision, so unlock-then-edit cannot hide in one batch.
  if (batch.operations.length > 1 && batch.operations.some(op => op?.type === 'edit_track' && 'locked' in op)) {
    fail('Changing a track lock must be the only operation in its batch');
  }
  const imports = [], alone = type => batch.operations.some(op => op?.type === type) &&
    (batch.operations.length === 1 || fail(`${type} must be the only operation in its batch`));
  let next, revert = null, rebind = null;
  if (alone('revert_to')) ({ next, target: revert } = await revertContent(root, base, batch.operations[0]));
  else if (alone('rebind_template')) { rebind = checkRebind(base, batch.operations[0]); next = structuredClone(base); }
  else next = await applyOperations(base, batch.operations, { importAsset: file => importAsset(file, { v2: true }), imports });
  const operations_sha256 = operationsSha256(batch.operations);
  Object.assign(next, { revision: base.revision + 1, parent_sha256: baseSha,
    change: { author: batch.author, summary: batch.summary, operations_sha256 } });
  // Template bindings: kept as they are unless rebound or reverted; new
  // templates pinned to the execution-layer bytes; unused ones dropped. Vars are
  // typed against them; graphics on locked tracks keep their template bytes.
  const { writes: templateWrites, notes, templates } = planTemplateBindings(base, next, { baseTemplates, rebind, revert });
  checkLockedTemplates(base, next);
  validateV2(next, { templates });
  // Frame alignment of the new revision (its font runs are compiled below): the
  // decisions loadProject made for the same bytes, new imports applied.
  bindAlignment(next, carryAlignment(next, [[base, baseAlignment], ...(revert ? [[revert.doc, revert.alignment]] : [])],
    new Set(imports.map(i => i.asset.sha256))));
  // Same envelope code as compilation: refused before dry-run or publish, and
  // the lanes that compile without the cut-edge declick (512-point limit) reported.
  const declick = checkVolumeAutomation(next);
  // Fixed caption font: bound when captions or graphics are introduced. Legacy projects that
  // already had captions without a binding keep the system-font contract.
  let installFont = false;
  if (next.caption_font) await verifyCaptionFont(root, next, templates);
  else if (!activeCaptions(base).length) installFont = await planCaptionFont(next, templates);
  else if (next.items.some(i => i.kind === 'graphic')) {
    // Graphics reuse the bound caption font; binding it now would silently restyle
    // this legacy project's system-font captions, so refuse instead.
    fail('Graphic items need the bound caption font; this legacy project renders captions with system fonts. Create a new project to add graphics');
  }
  const result = { status: dryRun ? 'dry_run' : 'published', base_revision: latest.revision, migration_revision: migration?.revision ?? null,
    revision: next.revision, operations_sha256, diff: diffDocuments(base, next), notes, ...(declick.skipped_lanes.length ? { declick } : {}) };
  if (dryRun) return result;
  await copyImports(root, imports);
  if (installFont) await installCaptionFont(root);
  await installTemplates(root, templateWrites);
  if (migration) await publish(root, migration);
  await publish(root, next);
  return result;
}

// Digest check of asset files (in parallel): Map asset id → real path of each
// file whose bytes match asset.sha256. Assets in `verified` (a check of the
// same root earlier in this operation, e.g. loadProject's) are not hashed again.
async function checkAssetFiles(root, assets, verified = new Map()) {
  return new Map(await Promise.all(assets.map(async asset => {
    if (verified.has(asset.id)) return [asset.id, verified.get(asset.id)];
    const file = await fs.realpath(await safePath(path.join(root, asset.file)));
    if (await digest(file) !== asset.sha256) fail(`Asset changed: ${asset.id}`);
    return [asset.id, file];
  })));
}

// Caption font and every asset file of a revision; `verified`: loadProject's
// result for the same revision, so each file is hashed once per render.
export async function verifyAssets(root, project, templates, { verified } = {}) {
  await verifyCaptionFont(root, project, templates);
  return checkAssetFiles(root, project.assets, verified);
}
