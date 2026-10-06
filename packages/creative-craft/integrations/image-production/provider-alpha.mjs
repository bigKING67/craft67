import sharp from 'sharp';
import { isDeepStrictEqual } from 'node:util';
import { sha256 } from '../local-production/content-store.mjs';
import { LIMITS } from './document.mjs';

export const ALPHA_ERRORS = ['output_missing_alpha', 'output_no_clear_background', 'output_empty_foreground'];

// Evidence of actual pixel transparency, not optical quality or product identity.
export async function inspectAlpha(bytes) {
  const meta = await sharp(bytes, { limitInputPixels: LIMITS.pixels, failOn: 'warning' }).metadata();
  const { data, info } = await sharp(bytes).toColourspace('srgb').ensureAlpha().raw({ depth: 'uchar' }).toBuffer({ resolveWithObject: true });
  let zero = 0, opaque = 0;
  for (let at = 3; at < data.length; at += 4) {
    if (data[at] === 0) zero++;
    else if (data[at] === 255) opaque++;
  }
  const pixels = info.width * info.height;
  return { sha256: sha256(bytes), width: info.width, height: info.height, has_alpha: meta.hasAlpha,
    pixels, zero_pixels: zero, partial_pixels: pixels - zero - opaque, opaque_pixels: opaque };
}

export function requireAlpha(check) {
  if (!check.has_alpha) throw new Error('output_missing_alpha');
  if (!check.zero_pixels) throw new Error('output_no_clear_background');
  if (check.zero_pixels === check.pixels) throw new Error('output_empty_foreground');
  return check;
}

export async function verifyAlpha(bytes, evidence) {
  const actual = requireAlpha(await inspectAlpha(bytes));
  if (!isDeepStrictEqual(actual, evidence)) throw new Error('Transparency evidence differs from output pixels');
  return actual;
}
