import * as fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import { sha256, writeOnce } from '../local-production/content-store.mjs';
import { LIMITS, record, id, string } from './document.mjs';

const fail = message => { throw new Error(message); };

// Refuse symlinks at every existing component. This is a trusted local project
// store, not a sandbox against another process replacing paths concurrently.
// Entries directly under the filesystem root (macOS /tmp, /var) are OS-owned
// aliases and are resolved first; every component below them is still checked.
export async function regularPath(file, { directory = false } = {}) {
  let absolute = path.resolve(file);
  const top = path.join(path.parse(absolute).root, absolute.split(path.sep).filter(Boolean)[0] ?? '');
  if (top !== path.parse(absolute).root && (await fs.lstat(top)).isSymbolicLink()) absolute = path.join(await fs.realpath(top), path.relative(top, absolute));
  const parts = path.relative(path.parse(absolute).root, absolute).split(path.sep).filter(Boolean);
  let current = path.parse(absolute).root;
  for (let i = 0; i < parts.length; i++) {
    current = path.join(current, parts[i]);
    const stat = await fs.lstat(current);
    if (stat.isSymbolicLink()) fail('Symlink paths are unsupported');
    if (i < parts.length - 1 || directory) { if (!stat.isDirectory()) fail('Expected a directory'); }
    else if (!stat.isFile()) fail('Expected a regular file');
  }
  return absolute;
}

// Compare directory identity rather than path text, so case-insensitive or
// aliased spellings of the project cannot place outputs inside it.
export async function assertOutsideProject(root, output) {
  const project = await fs.stat(root);
  let current = await fs.realpath(path.dirname(path.resolve(output)));
  for (;;) {
    const stat = await fs.stat(current);
    if (stat.dev === project.dev && stat.ino === project.ino) fail('Output must be outside the project');
    const parent = path.dirname(current);
    if (parent === current) return;
    current = parent;
  }
}

export async function readBytes(file, limit) {
  await regularPath(file);
  if ((await fs.stat(file)).size > limit) fail('File byte limit exceeded');
  const bytes = await fs.readFile(file);
  if (bytes.length > limit) fail('File byte limit exceeded');
  return bytes;
}

export async function importRaster(input) {
  record(input, ['id', 'source'], 'asset input'); id(input.id, 'asset id'); string(input.source, 'asset source', 4096);
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(input.source)) fail('Asset source must be a local file');
  const original = await readBytes(input.source, LIMITS.sourceBytes);
  const source = sharp(original, { limitInputPixels: LIMITS.pixels, failOn: 'warning' });
  const metadata = await source.metadata();
  if (!['png', 'jpeg', 'webp'].includes(metadata.format) || (metadata.pages ?? 1) !== 1) fail('Only single-frame PNG, JPEG and WebP assets are supported');
  const rendered = await source.rotate().toColourspace('srgb').png({ compressionLevel: 9 }).toBuffer();
  const size = await sharp(rendered).metadata();
  if (size.width > 8192 || size.height > 8192) fail('Asset dimension limit exceeded');
  const originalSha = sha256(original), renderSha = sha256(rendered);
  return {
    asset: { id: input.id, file: `assets/${originalSha}.${metadata.format}`, sha256: originalSha, format: metadata.format,
      width: size.width, height: size.height, render_file: `assets/${renderSha}.png`, render_sha256: renderSha },
    original, rendered,
  };
}

export async function saveAsset(root, imported) {
  await writeOnce(path.join(root, imported.asset.file), { bytes: imported.original }, { expected: imported.asset.sha256 });
  await writeOnce(path.join(root, imported.asset.render_file), { bytes: imported.rendered }, { expected: imported.asset.render_sha256 });
}

export async function readAsset(root, asset) {
  // Candidate outputs are stored as their own normalized PNG, so they share the render bound.
  const original = await readBytes(path.join(root, asset.file), asset.file === asset.render_file ? LIMITS.renderBytes : LIMITS.sourceBytes);
  if (sha256(original) !== asset.sha256) fail(`Asset digest mismatch: ${asset.id}`);
  const sourceMeta = await sharp(original, { limitInputPixels: LIMITS.pixels }).metadata();
  const swapped = [5, 6, 7, 8].includes(sourceMeta.orientation);
  if (sourceMeta.format !== asset.format || (sourceMeta.pages ?? 1) !== 1 ||
      (swapped ? sourceMeta.height : sourceMeta.width) !== asset.width || (swapped ? sourceMeta.width : sourceMeta.height) !== asset.height) fail(`Source asset dimensions/format mismatch: ${asset.id}`);
  const rendered = await readBytes(path.join(root, asset.render_file), LIMITS.renderBytes);
  if (sha256(rendered) !== asset.render_sha256) fail(`Render asset digest mismatch: ${asset.id}`);
  const metadata = await sharp(rendered, { limitInputPixels: LIMITS.pixels }).metadata();
  if (metadata.format !== 'png' || metadata.depth !== 'uchar' || (metadata.pages ?? 1) !== 1 || metadata.width !== asset.width || metadata.height !== asset.height) fail(`Render asset dimensions mismatch: ${asset.id}`);
  return { original, rendered };
}
