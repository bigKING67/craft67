import * as fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import { importRaster, regularPath } from './raster.mjs';
import { record, string, digest, number } from './document.mjs';
import { sha256 } from '../local-production/content-store.mjs';

export async function cropPhoto(output, input, { dryRun = false } = {}) {
  record(input, ['source', 'source_sha256', 'crop', 'authorization'], 'crop input');
  string(input.source, 'source', 4096);
  if (!path.isAbsolute(input.source)) throw new Error('Crop source must be an absolute local path');
  digest(input.source_sha256);
  record(input.authorization, ['user_approved', 'context'], 'crop authorization');
  if (input.authorization.user_approved !== true) throw new Error('Explicit user crop authorization required');
  string(input.authorization.context, 'authorization context', 500);
  record(input.crop, ['left', 'top', 'width', 'height'], 'crop rectangle');
  for (const key of ['left', 'top', 'width', 'height']) number(input.crop[key], `crop.${key}`, ['left', 'top'].includes(key) ? 0 : 1, 8192, true);
  output = path.resolve(output);
  await regularPath(path.dirname(output), { directory: true });
  try { await fs.lstat(output); throw new Error('Crop output already exists'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  const imported = await importRaster({ id: 'source', source: input.source });
  if (sha256(imported.original) !== input.source_sha256) throw new Error('Crop source digest mismatch');
  const { width, height } = imported.asset;
  const { left, top, width: cropWidth, height: cropHeight } = input.crop;
  if (left + cropWidth > width || top + cropHeight > height) throw new Error('Crop rectangle outside normalized source');
  const cropped = await sharp(imported.rendered).extract(input.crop).png({ compressionLevel: 9 }).toBuffer();
  // Independent check: slice rows from the full normalized raster rather than
  // comparing against a second run of the same extract operation.
  const full = await sharp(imported.rendered).ensureAlpha().raw().toBuffer();
  const row = cropWidth * 4, expected = Buffer.alloc(row * cropHeight);
  for (let y = 0; y < cropHeight; y++) full.copy(expected, y * row, ((top + y) * width + left) * 4, ((top + y) * width + left) * 4 + row);
  const actual = await sharp(cropped).ensureAlpha().raw().toBuffer();
  if (!expected.equals(actual)) throw new Error('Crop retained pixels differ');
  const originalFile = `original.${imported.asset.format}`;
  const receipt = {
    schema: 'creative-craft.photo-crop.v1',
    authorization: structuredClone(input.authorization),
    coordinate_space: 'EXIF-oriented sRGB source; top-left origin; integer pixels',
    source: { file: originalFile, sha256: imported.asset.sha256, width, height },
    normalized: { file: 'normalized.png', sha256: imported.asset.render_sha256 },
    crop: structuredClone(input.crop),
    result: { file: 'cropped.png', sha256: sha256(cropped), width: cropWidth, height: cropHeight },
    qa: { retained_rgba_sha256: sha256(actual), retained_pixels: cropWidth * cropHeight, changed_pixels: 0, scale: 1, product_completeness: 'UNVERIFIED' },
  };
  if (dryRun) return { output, dry_run: true, receipt };
  await fs.mkdir(output);
  try {
    for (const [name, bytes] of [[originalFile, imported.original], ['normalized.png', imported.rendered], ['cropped.png', cropped], ['receipt.json', Buffer.from(JSON.stringify(receipt, null, 2) + '\n')]]) {
      await fs.writeFile(path.join(output, name), bytes, { flag: 'wx' });
    }
  } catch (error) { await fs.rm(output, { recursive: true, force: true }); throw error; }
  return { output, dry_run: false, receipt };
}
