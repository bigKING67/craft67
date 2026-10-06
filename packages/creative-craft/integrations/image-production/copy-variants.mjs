import * as fs from 'node:fs/promises';
import path from 'node:path';
import { record, id, string, number, digest, validateDocument, LIMITS } from './document.mjs';
import { readProject, editBatch, encode, regularPath } from './project.mjs';
import { readBytes, assertOutsideProject } from './raster.mjs';
import { renderProject } from './render.mjs';
import { sha256 } from '../local-production/content-store.mjs';

// Derived projects intentionally start a fresh history; source provenance lives
// in the set manifest rather than pretending to carry source candidate decisions.
export async function copyVariants(root, input, { signal } = {}) {
  record(input, ['output', 'variants', 'updates'], 'copy variants');
  string(input.output, 'output', 4096);
  if (!Array.isArray(input.variants) || !input.variants.length || input.variants.length > 12) throw new Error('Expected 1–12 variants');
  if (!Array.isArray(input.updates) || !input.updates.length || input.updates.length > LIMITS.operations) throw new Error('Expected 1–100 text updates');
  const names = new Set(), ids = new Set();
  for (const variant of input.variants) {
    record(variant, ['name', 'revision', 'sha256'], 'variant');
    id(variant.name, 'variant name'); number(variant.revision, 'revision', 1, LIMITS.revisions, true); digest(variant.sha256);
    const key = variant.name.toLowerCase();
    if (names.has(key)) throw new Error('Duplicate variant name'); names.add(key);
  }
  for (const update of input.updates) {
    record(update, ['id', 'text'], 'text update'); id(update.id); string(update.text, 'text');
    if (ids.has(update.id)) throw new Error('Duplicate text update'); ids.add(update.id);
  }
  const cancelled = () => { if (signal?.aborted) throw new Error('Copy variants cancelled'); };
  cancelled();
  root = await regularPath(root, { directory: true });
  const output = path.resolve(input.output);
  await regularPath(path.dirname(output), { directory: true });
  await assertOutsideProject(root, output);
  const sources = [];
  for (const variant of input.variants) {
    const source = await readProject(root, { revision: variant.revision });
    if (source.sha256 !== variant.sha256) throw new Error(`Stale source binding: ${variant.name}`);
    for (const update of input.updates) {
      const object = source.document.objects.find(value => value.id === update.id);
      if (!object || object.kind !== 'text' || object.locked) throw new Error(`Expected unlocked text object: ${update.id} in ${variant.name}`);
    }
    sources.push(source);
  }
  cancelled();
  await fs.mkdir(output); // Exclusive ownership; never clean a preexisting target.
  try {
    const manifest = { schema: 'creative-craft.copy-variants.v1', status: 'completed', updates: input.updates, variants: [] };
    for (const [index, variant] of input.variants.entries()) {
      cancelled();
      const source = sources[index], directory = path.join(output, variant.name), projectRoot = path.join(directory, 'project');
      await fs.mkdir(directory); await fs.mkdir(projectRoot);
      for (const folder of ['assets', 'fonts', 'revisions']) await fs.mkdir(path.join(projectRoot, folder));
      const bindings = new Map([[source.document.font.file, source.document.font.sha256]]);
      for (const asset of source.document.assets) {
        bindings.set(asset.file, asset.sha256); bindings.set(asset.render_file, asset.render_sha256);
      }
      for (const [file, expected] of bindings) {
        const bytes = await readBytes(path.join(root, file), LIMITS.renderBytes);
        if (sha256(bytes) !== expected) throw new Error('Source asset changed during copy');
        await fs.writeFile(path.join(projectRoot, file), bytes, { flag: 'wx' });
      }
      const document = structuredClone(source.document);
      document.revision = 1; document.parent_sha256 = null;
      document.change = { author: 'system', summary: `Snapshot of source revision ${variant.revision}`, operations: ['create'] };
      validateDocument(document);
      await fs.writeFile(path.join(projectRoot, 'revisions/000001.json'), encode(document), { flag: 'wx' });
      const batch = { base_revision: 1, author: 'agent', summary: 'Apply shared variant copy',
        operations: input.updates.map(update => ({ type: 'update_object', id: update.id, patch: { text: update.text } })) };
      await editBatch(projectRoot, batch);
      const rendered = await renderProject(projectRoot, path.join(directory, 'export'), { signal });
      manifest.variants.push({ name: variant.name, source: { project_id: source.document.project_id, revision: variant.revision, sha256: source.sha256 },
        project: `${variant.name}/project`, export: `${variant.name}/export`, revision: 2,
        document_sha256: rendered.receipt.document_sha256, png_sha256: rendered.receipt.outputs.png.sha256 });
    }
    for (const variant of input.variants) {
      if ((await readProject(root, { revision: variant.revision })).sha256 !== variant.sha256) throw new Error('Source revision changed during export');
    }
    cancelled();
    await fs.writeFile(path.join(output, 'manifest.json'), encode(manifest), { flag: 'wx' });
    return { output, manifest };
  } catch (error) {
    await fs.rm(output, { recursive: true, force: true });
    throw error;
  }
}
