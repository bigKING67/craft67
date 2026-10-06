import * as fs from 'node:fs/promises';
import path from 'node:path';
import { writeOnce } from './content-store.mjs';
import { parseBoundTemplate, runtimeTemplate, templateSha256 } from './templates.mjs';

// Graphic templates pinned to edit revisions (graphic_templates). Like the
// caption font, a binding is content-addressed: the normalized template's
// deterministic serialization (templates.mjs normalizeTemplate) lives at
// templates/<sha256>.json inside the project, and a pinned revision renders
// only from those bytes (hash and template rules re-checked on load, nothing
// rewritten).
// Callers pass project roots already resolved through safePath.
const fail = message => { throw new Error(message); };
export const bindingFile = sha256 => `templates/${sha256}.json`;
// Malformed template fields are left to validateV2 to report.
export const usedTemplates = doc => [...new Set((Array.isArray(doc.items) ? doc.items : []).filter(i => i?.kind === 'graphic' && typeof i.template === 'string').map(i => i.template))].sort();

async function boundBytes(root, binding) {
  const file = path.join(root, binding.file);
  try {
    // Never through a link into mutable host locations.
    if ((await fs.lstat(path.dirname(file))).isSymbolicLink() || !(await fs.lstat(file)).isFile()) fail(`Graphic template ${binding.id}: ${binding.file} must be a regular file`);
  } catch (error) {
    if (error.code === 'ENOENT') fail(`Graphic template ${binding.id}: bound file missing (${binding.file})`);
    throw error;
  }
  const bytes = await fs.readFile(file);
  if (templateSha256(bytes) !== binding.sha256) fail(`Graphic template ${binding.id}: bound file hash mismatch (${binding.file})`);
  return bytes;
}

export async function loadBoundTemplate(root, binding) {
  const bytes = await boundBytes(root, binding);
  let template;
  try { template = parseBoundTemplate(binding.id, bytes); }
  catch (error) { fail(`Graphic template ${binding.id} bound to this revision fails template validation: ${error.message}`); }
  if (template.version !== binding.version) fail(`Graphic template ${binding.id}: bound file is version ${template.version}, binding says ${binding.version}`);
  return template;
}

// Loads the bound template set of a pinned revision (bindings already
// shape-checked: id, sha256 and file = templates/<sha256>.json).
export async function loadPinnedTemplates(root, bindings) {
  const templates = new Map();
  for (const binding of bindings) templates.set(binding.id, await loadBoundTemplate(root, binding));
  return templates;
}

// sha256 of the bytes a revision renders template `id` with: its binding when
// pinned, else (historical revision) the current execution-layer bytes.
export const renderedTemplateSha = (doc, id) => (doc.graphic_templates ? doc.graphic_templates.find(b => b.id === id)?.sha256 : runtimeTemplate(id).sha256);

// Bindings of a new revision `next` built from `base` (null on create), whose
// loaded template set is `baseTemplates` (reused, not re-read). Every template a
// graphic uses keeps its existing binding, except:
// - `rebind`: that template moves to the current execution-layer bytes;
// - `revert` ({doc, templates} of the revert target): templates take the
//   target's bindings (its bound files are still in the project and were
//   checked when it was loaded); an unpinned target binds the current
//   execution-layer bytes, with a note.
// Templates first used here pin the execution-layer bytes. Bindings no graphic
// uses are dropped. Returns the files to write (nothing is written here),
// notes for the batch result and the template set of `next` for validation.
export function planTemplateBindings(base, next, { baseTemplates = null, rebind = null, revert = null } = {}) {
  const used = usedTemplates(next), writes = [], notes = [], templates = new Map();
  if (!used.length && !base?.graphic_templates) {
    delete next.graphic_templates;
    return { writes, notes, templates };
  }
  const [source, sourceTemplates] = revert ? [revert.doc, revert.templates] : [base, baseTemplates];
  const kept = new Map((source?.graphic_templates ?? []).map(b => [b.id, b]));
  const bindings = [];
  for (const id of used) {
    let binding = id === rebind ? null : kept.get(id), template = binding && sourceTemplates?.get(id);
    if (binding) template ?? fail(`Graphic template ${id}: the bound template set is not loaded`);
    else if (revert?.doc.graphic_templates) fail(`Graphic template ${id}: revert target revision ${revert.doc.revision} has no binding`);
    else {
      const runtime = runtimeTemplate(id);
      binding = { id, version: runtime.template.version, sha256: runtime.sha256, file: bindingFile(runtime.sha256) };
      template = runtime.template;
      writes.push({ binding, bytes: runtime.bytes }); // One per template id; ids are part of the bytes.
    }
    templates.set(id, template);
    bindings.push({ ...binding });
  }
  next.graphic_templates = bindings;
  if (revert && !revert.doc.graphic_templates && used.length) {
    notes.push(`Revision ${revert.doc.revision} predates graphic template pinning; reverting to it binds ${used.join(', ')} to the current execution-layer template bytes`);
  } else if (!revert && base && !base.graphic_templates && used.length) {
    notes.push(`Revision ${base.revision} predates graphic template pinning; this revision binds ${used.join(', ')} to the current execution-layer template bytes`);
  }
  return { writes, notes, templates };
}

// Locked tracks are frozen, including how their graphics render: no batch
// (rebind_template, revert_to, ...) may change the template bytes a graphic on a
// track locked in `base` renders with.
export function checkLockedTemplates(base, next) {
  const locked = new Set(base.tracks.filter(t => t.locked).map(t => t.id));
  for (const item of next.items) {
    if (item.kind !== 'graphic' || !locked.has(item.track_id) || renderedTemplateSha(next, item.template) === renderedTemplateSha(base, item.template)) continue;
    fail(`Track is locked: ${item.track_id} (graphic ${item.id} would render template ${item.template} from different bytes)`);
  }
}

// Content-addressed copies; an existing identical file is reused, never replaced.
export async function installTemplates(root, writes) {
  if (!writes.length) return;
  const dir = path.join(root, 'templates');
  await fs.mkdir(dir, { recursive: true });
  if (!(await fs.lstat(dir)).isDirectory()) fail('Project templates/ must be a directory');
  for (const { binding, bytes } of writes) {
    await writeOnce(path.join(root, binding.file), { bytes }, { expected: binding.sha256, mismatch: `Graphic template ${binding.id} changed while binding` });
    await boundBytes(root, binding); // Regular file, digest of what is now on disk.
  }
}

// Render directories carry the bound bytes so a render replays independently.
export async function copyBoundTemplates(root, destination, doc) {
  if (!doc.graphic_templates?.length) return;
  await fs.mkdir(path.join(destination, 'templates'));
  for (const binding of doc.graphic_templates) {
    await fs.copyFile(path.join(root, binding.file), path.join(destination, binding.file), fs.constants.COPYFILE_EXCL);
    await loadBoundTemplate(destination, binding);
  }
}
