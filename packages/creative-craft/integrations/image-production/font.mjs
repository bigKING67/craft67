import * as fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { sha256, writeOnce } from '../local-production/content-store.mjs';

export const fontDirectory = fileURLToPath(new URL('./fonts/', import.meta.url));
export const fontManifest = JSON.parse(await fs.readFile(new URL('./fonts/manifest.json', import.meta.url), 'utf8'));

// Hash the 16 MB font once per buffer instead of on every glyph/width check.
const verifiedFonts = new WeakSet();
export function verifyFont(bytes) {
  if (verifiedFonts.has(bytes)) return;
  if (bytes.length !== fontManifest.bytes || sha256(bytes) !== fontManifest.sha256) throw new Error('Pinned font digest mismatch');
  verifiedFonts.add(bytes);
}

export async function installedFont() {
  const file = new URL(`./fonts/${fontManifest.file}`, import.meta.url);
  try {
    const stat = await fs.lstat(file);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error('Pinned font must be a regular file');
    const bytes = await fs.readFile(file);
    verifyFont(bytes);
    return bytes;
  } catch (error) {
    if (error.code === 'ENOENT') throw new Error('Pinned font missing: run npm run fetch-font in integrations/image-production');
    throw error;
  }
}

// This parser is used only after the exact, fixed OTF digest is verified.
// Its format-12 cmap covers the font's BMP and supplementary characters.
export function checkGlyphs(bytes, texts) {
  verifyFont(bytes);
  let cmap;
  for (let i = 0; i < bytes.readUInt16BE(4); i++) {
    const at = 12 + i * 16;
    if (bytes.toString('ascii', at, at + 4) === 'cmap') cmap = bytes.readUInt32BE(at + 8);
  }
  let table;
  for (let i = 0; i < bytes.readUInt16BE(cmap + 2); i++) {
    const at = cmap + 4 + i * 8;
    const offset = cmap + bytes.readUInt32BE(at + 4);
    if (bytes.readUInt16BE(offset) === 12) table = offset;
  }
  if (table === undefined) throw new Error('Pinned font cmap profile changed');
  const groups = bytes.readUInt32BE(table + 12);
  const missing = new Set();
  const glyphs = new Map();
  for (const char of texts.join('')) {
    if (char === '\n') continue;
    const cp = char.codePointAt(0);
    let low = 0, high = groups - 1, found = false;
    while (low <= high) {
      const mid = (low + high) >>> 1, at = table + 16 + mid * 12;
      const start = bytes.readUInt32BE(at), end = bytes.readUInt32BE(at + 4);
      if (cp < start) high = mid - 1;
      else if (cp > end) low = mid + 1;
      else { const glyph = bytes.readUInt32BE(at + 8) + cp - start; found = glyph !== 0; glyphs.set(cp, glyph); break; }
    }
    if (!found) missing.add(`U+${cp.toString(16).toUpperCase()}`);
  }
  if (missing.size) throw new Error(`Missing font glyphs: ${[...missing].join(', ')}`);
  return glyphs;
}

export function checkTextWidths(bytes, objects) {
  const glyphs = checkGlyphs(bytes, objects.map(object => object.text));
  const tables = new Map();
  for (let i = 0; i < bytes.readUInt16BE(4); i++) {
    const at = 12 + i * 16;
    tables.set(bytes.toString('ascii', at, at + 4), bytes.readUInt32BE(at + 8));
  }
  const units = bytes.readUInt16BE(tables.get('head') + 18);
  const count = bytes.readUInt16BE(tables.get('hhea') + 34);
  for (const object of objects) for (const char of object.text) {
    if (char === '\n') continue;
    const glyph = glyphs.get(char.codePointAt(0));
    const advance = bytes.readUInt16BE(tables.get('hmtx') + Math.min(glyph, count - 1) * 4);
    if (advance / units * object.font_size > object.width + 0.1) throw new Error(`Text box narrower than glyph: ${object.id}`);
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url) && process.argv[2] === '--fetch') {
  const target = new URL(`./fonts/${fontManifest.file}`, import.meta.url);
  try { await installedFont(); }
  catch (error) {
    if (!error.message.startsWith('Pinned font missing:')) throw error;
    const response = await fetch(fontManifest.source, { signal: AbortSignal.timeout(60000) });
    if (!response.ok) throw new Error(`Font download failed: HTTP ${response.status}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    verifyFont(bytes);
    await writeOnce(fileURLToPath(target), { bytes }, { expected: fontManifest.sha256 });
  }
  console.log(JSON.stringify({ status: 'verified', ...fontManifest }));
}
