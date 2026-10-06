import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import sharp from 'sharp';
import { sha256, writeOnce } from '../local-production/content-store.mjs';
import { readProject, regularPath, encode, candidateDocument } from './project.mjs';
import { assertOutsideProject } from './raster.mjs';
import { readCandidateEntry } from './candidate-store.mjs';
import { inspectCandidate } from './candidates.mjs';
import { number } from './document.mjs';

const packageInfo = JSON.parse(await fs.readFile(new URL('./package.json', import.meta.url), 'utf8'));
const engineVersions = {};
for (const [name, pinned] of Object.entries(packageInfo.dependencies)) {
  const installed = JSON.parse(await fs.readFile(new URL(`./node_modules/${name}/package.json`, import.meta.url), 'utf8')).version;
  if (installed !== pinned) throw new Error(`Installed dependency differs from pinned version: ${name}`);
  engineVersions[name] = installed;
}

function worker(args, { signal, timeoutMs }) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [fileURLToPath(new URL('./render-worker.mjs', import.meta.url)), ...args], { stdio: ['ignore', 'pipe', 'pipe'] });
    let output = '', errors = '', failure;
    const stop = reason => { failure ??= reason; child.kill('SIGKILL'); };
    const abort = () => stop('Render cancelled');
    const timer = setTimeout(() => stop('Render timed out'), timeoutMs);
    signal?.addEventListener('abort', abort, { once: true });
    if (signal?.aborted) abort();
    child.stdout.on('data', bytes => { output += bytes; if (output.length > 100_000) stop('Worker output limit exceeded'); });
    child.stderr.on('data', bytes => { errors = (errors + bytes).slice(-8000); });
    child.on('error', error => { failure ??= error.message; });
    // Wait for actual process close before cleaning this invocation's files.
    child.on('close', code => {
      clearTimeout(timer); signal?.removeEventListener('abort', abort);
      if (failure || code !== 0) reject(new Error(failure ?? (errors.trim() || `Worker exited ${code}`)));
      else { try { resolve(JSON.parse(output)); } catch { reject(new Error('Invalid render worker response')); } }
    });
  });
}

export async function renderProject(root, output, { revision, candidateId, previewMax = 0, signal, timeoutMs = 60000 } = {}) {
  number(previewMax, 'previewMax', 0, 8192, true); number(timeoutMs, 'timeoutMs', 1, 60000, true);
  if (previewMax !== 0 && previewMax < 64) throw new Error('Preview must be at least 64 pixels');
  if (candidateId !== undefined) {
    const entry = await readCandidateEntry(root, candidateId);
    if (revision !== undefined && revision !== entry.candidate.base_revision) throw new Error('Candidate preview revision mismatch');
    revision = entry.candidate.base_revision;
  }
  const project = await readProject(root, { revision });
  let renderDocument = project.document, candidate;
  if (candidateId !== undefined) {
    const prepared = await candidateDocument(root, project, candidateId);
    renderDocument = prepared.document; candidate = { id: candidateId, sha256: prepared.entry.sha256 };
  }
  const documentSha = sha256(encode(renderDocument));
  output = path.resolve(output);
  await regularPath(path.dirname(output), { directory: true });
  await assertOutsideProject(project.root, output);
  // Render artifacts never replace another run, including a failed run.
  await fs.mkdir(output);
  const receipt = { schema: 'creative-craft.local-image-render.v1', status: 'running', mode: previewMax ? 'preview' : 'export',
    project_id: project.document.project_id, revision: project.document.revision, project_sha256: project.sha256, document_sha256: documentSha,
    engines: { node: process.version, ...engineVersions }, font: project.document.font,
    assets: renderDocument.assets.map(asset => ({ id: asset.id, sha256: asset.sha256, render_sha256: asset.render_sha256 })),
    canvas: project.document.canvas, visual_quality: 'UNVERIFIED', started_at: new Date().toISOString() };
  if (candidate) receipt.candidate_preview = candidate;
  try {
    const result = await worker([project.root, String(project.document.revision), project.sha256, output, String(previewMax), candidate?.id ?? '', candidate?.sha256 ?? ''], { signal, timeoutMs });
    if (signal?.aborted) throw new Error('Render cancelled');
    // Recheck source bindings and history before claiming a successful output.
    const final = await readProject(root, { revision: project.document.revision });
    if (final.sha256 !== project.sha256) throw new Error('Revision changed during rendering');
    if (candidate) {
      const checked = await candidateDocument(root, final, candidate.id);
      if (checked.entry.sha256 !== candidate.sha256 || sha256(encode(checked.document)) !== documentSha) throw new Error('Candidate changed during rendering');
      // A standalone preview must retain its decision context. This is an
      // observation, not permission to accept or a claim of visual approval.
      const observed = await inspectCandidate(root, candidate.id);
      if (observed.sha256 !== candidate.sha256) throw new Error('Candidate changed during rendering');
      Object.assign(receipt.candidate_preview, { checked_at: new Date().toISOString(),
        status_at_check: observed.status, current_revision_at_check: observed.current_revision,
        accepted_revision: observed.accepted_revision, applied_in_current: observed.applied_in_current,
        stale: observed.stale, decision_pending: observed.decision_pending });
    }
    const png = await fs.readFile(await regularPath(path.join(output, 'image.png')));
    const svg = await fs.readFile(await regularPath(path.join(output, 'image.svg')));
    const metadata = await sharp(png).metadata();
    await sharp(png).raw().toBuffer(); // Full decode, not only a header check.
    const scale = previewMax ? Math.min(1, previewMax / Math.max(project.document.canvas.width, project.document.canvas.height)) : 1;
    const expectedWidth = Math.round(project.document.canvas.width * scale), expectedHeight = Math.round(project.document.canvas.height * scale);
    if (metadata.format !== 'png' || metadata.width !== expectedWidth || metadata.height !== expectedHeight || result.width !== expectedWidth || result.height !== expectedHeight) throw new Error('Rendered dimensions mismatch');
    if (signal?.aborted) throw new Error('Render cancelled');
    await writeOnce(path.join(output, 'document.json'), { bytes: encode(renderDocument) }, { expected: documentSha });
    receipt.status = 'completed';
    receipt.outputs = { png: { file: 'image.png', sha256: sha256(png), width: metadata.width, height: metadata.height }, svg: { file: 'image.svg', sha256: sha256(svg) } };
    receipt.qa = { source_bindings: 'PASS', png_decode: 'PASS', dimensions: 'PASS', object_bounds: 'PASS', font_glyphs: 'PASS', text_fit: 'PASS',
      // Width is the declared box: wrapping keeps lines inside it, and a per-glyph advance check rejects glyphs wider than it.
      text_fit_basis: { height: 'measured layout height', width: 'wrapped to declared box; per-glyph advance checked' }, text_measurements: result.text_measurements };
  } catch (error) {
    receipt.status = error.message === 'Render cancelled' ? 'cancelled' : 'failed'; receipt.error = error.message;
    for (const name of ['image.png', 'image.svg', 'document.json']) await fs.rm(path.join(output, name), { force: true });
    receipt.finished_at = new Date().toISOString();
    await writeOnce(path.join(output, 'receipt.json'), { bytes: encode(receipt) });
    const failure = new Error(error.message); failure.receipt = receipt; failure.output = output; throw failure;
  }
  receipt.finished_at = new Date().toISOString();
  await writeOnce(path.join(output, 'receipt.json'), { bytes: encode(receipt) });
  return { output, receipt };
}
