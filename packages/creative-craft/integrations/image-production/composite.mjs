import sharp from 'sharp';
import { sha256 } from '../local-production/content-store.mjs';
import { LIMITS, record, number } from './document.mjs';
import { readBytes } from './raster.mjs';

export function validateContext(context, width, height) {
  record(context, ['x', 'y', 'width', 'height'], 'context');
  number(context.x, 'context.x', 0, width - 1, true); number(context.y, 'context.y', 0, height - 1, true);
  number(context.width, 'context.width', 1, width, true); number(context.height, 'context.height', 1, height, true);
  if (context.x + context.width > width || context.y + context.height > height) throw new Error('Context outside target raster');
}

export async function maskBytes(bytes, width, height, { protection = false } = {}) {
  const image = sharp(bytes, { limitInputPixels: LIMITS.pixels, failOn: 'warning' });
  const meta = await image.metadata();
  if (meta.format !== 'png' || (meta.pages ?? 1) !== 1 || meta.width !== width || meta.height !== height ||
      meta.channels !== 1 || meta.hasAlpha || meta.depth !== 'uchar') throw new Error('Mask must be an aligned, single-channel 8-bit grayscale PNG without alpha');
  const data = await image.toColourspace('b-w').raw().toBuffer();
  if (data.length !== width * height) throw new Error('Mask pixel count mismatch');
  if (protection && data.some(value => value !== 0 && value !== 255)) throw new Error('Protection mask must be binary (0 or 255)');
  return { bytes, data, sha256: sha256(bytes), width, height };
}

export async function importMask(source, width, height, options) {
  return maskBytes(await readBytes(source, LIMITS.sourceBytes), width, height, options);
}

async function rgba(bytes, width, height) {
  const { data, info } = await sharp(bytes, { limitInputPixels: LIMITS.pixels }).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  if (info.width !== width || info.height !== height || info.channels !== 4) throw new Error('Composite source dimensions mismatch');
  return data;
}

export async function compositeRaster(original, proposed, { width, height, context, generation, protection, blend }, { signal } = {}) {
  validateContext(context, width, height);
  signal?.throwIfAborted();
  const before = await rgba(original, width, height), after = await rgba(proposed, width, height);
  const output = Buffer.from(before);
  const pixels = width * height;
  if ([generation, protection, blend].some(data => data.length !== pixels)) throw new Error('Composite mask pixel count mismatch');
  let protectedPixels = 0, outsidePixels = 0, changedPixels = 0, allowedPixels = 0;
  for (let pixel = 0; pixel < pixels; pixel++) {
    if ((pixel & 65535) === 0) signal?.throwIfAborted();
    const x = pixel % width, y = Math.floor(pixel / width);
    const inside = x >= context.x && y >= context.y && x < context.x + context.width && y < context.y + context.height;
    if (generation[pixel] && !inside) throw new Error('Generation mask extends outside context');
    if (blend[pixel] && !generation[pixel]) throw new Error('Blend mask extends outside generation mask');
    if (protection[pixel] !== 0 && protection[pixel] !== 255) throw new Error('Protection mask must be binary');
    const weight = protection[pixel] ? 0 : blend[pixel];
    if (protection[pixel]) protectedPixels++;
    if (!weight) { outsidePixels++; continue; }
    allowedPixels++;
    const at = pixel * 4;
    if (weight === 255) after.copy(output, at, at, at + 4);
    else {
      // Blend premultiplied color, then return to straight RGBA. This avoids
      // treating transparent candidate colors as opaque edge colors.
      const oldAlpha = before[at + 3] * (255 - weight) / 255;
      const newAlpha = after[at + 3] * weight / 255;
      const alpha = oldAlpha + newAlpha;
      output[at + 3] = Math.round(alpha);
      for (let channel = 0; channel < 3; channel++) output[at + channel] = alpha ? Math.round((before[at + channel] * oldAlpha + after[at + channel] * newAlpha) / alpha) : 0;
    }
    if (!output.subarray(at, at + 4).equals(before.subarray(at, at + 4))) changedPixels++;
  }
  if (!allowedPixels) throw new Error('No editable pixels after applying protection');
  if (!changedPixels) throw new Error('Candidate composite makes no pixel change');
  const png = await sharp(output, { raw: { width, height, channels: 4 } }).png({ compressionLevel: 9 }).toBuffer();
  const decoded = await rgba(png, width, height);
  let protectedChanged = 0, outsideChanged = 0;
  for (let pixel = 0; pixel < pixels; pixel++) {
    const at = pixel * 4;
    if (!decoded.subarray(at, at + 4).equals(before.subarray(at, at + 4))) {
      if (protection[pixel]) protectedChanged++;
      if (!blend[pixel] || protection[pixel]) outsideChanged++;
    }
  }
  if (protectedChanged || outsideChanged) throw new Error('Composite protection pixel check failed');
  return { png, qa: { color_space: 'srgb', alpha_blend: 'premultiplied', protected_pixels: protectedPixels, outside_blend_pixels: outsidePixels,
    changed_pixels: changedPixels, protected_changed_pixels: protectedChanged, outside_blend_changed_pixels: outsideChanged } };
}
