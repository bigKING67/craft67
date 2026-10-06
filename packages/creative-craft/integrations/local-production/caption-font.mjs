import { sha256, writeOnce } from './content-store.mjs';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { isV2, resolveCaptions } from './timeline.mjs';
import { compiledView } from './source-frames.mjs';
import { graphicTexts, templateSet } from './templates.mjs';

// Versioned renderer resource, not an assertion about the original video's font.
const bundle = new URL('./fonts/', import.meta.url);
const manifest = JSON.parse(await fs.readFile(new URL('manifest.json', bundle), 'utf8'));
export const CAPTION_FONT = Object.freeze({ profile: manifest.profile, sha256: manifest.sha256,
  file: `fonts/${manifest.sha256}.ttf` });
export const FONT_FAMILY = 'CreativeCaptionNotoSCV1';

export function validateCaptionFont(binding) {
  if (!binding || Array.isArray(binding) || Object.keys(binding).length !== 3 ||
      Object.entries(CAPTION_FONT).some(([key, value]) => binding[key] !== value)) {
    throw new Error('Unsupported caption font binding');
  }
}

export function activeCaptions(project) {
  // The captions compilation shows (windows of the compiled view; a view passed
  // in by renderProject or compose is used as is, not compiled again).
  if (isV2(project)) return resolveCaptions(compiledView(project)).map(caption => caption.item);
  return project.clips.flatMap(clip => clip.captions.filter(caption =>
    caption.to > clip.in_seconds && caption.from < clip.in_seconds + clip.frames / project.canvas.fps));
}

// Every text run the bound font renders: visible captions and graphic template
// text (graphics reuse the caption font and are bound the same way).
// `templates`: the revision's template set (required when it is pinned).
export function fontRuns(project, templates) {
  const captions = activeCaptions(project).map(caption => ({ text: caption.text, weight: caption.style?.weight ?? 600 }));
  const graphics = isV2(project) ? project.items.filter(i => i.kind === 'graphic') : [];
  if (!graphics.length) return captions;
  const set = templateSet(project, templates);
  return [...captions, ...graphics.flatMap(item => graphicTexts(item, set)).map(({ text, weight }) => ({ text, weight }))];
}

async function fontBytes(file) {
  // Callers resolve the project root through safePath. The font directory/file
  // must also be ordinary files, never a link into mutable host font locations.
  if ((await fs.lstat(path.dirname(file))).isSymbolicLink() || !(await fs.lstat(file)).isFile()) {
    throw new Error('Caption font must be a regular file');
  }
  const bytes = await fs.readFile(file);
  if (sha256(bytes) !== CAPTION_FONT.sha256) {
    throw new Error('Caption font hash mismatch');
  }
  return bytes;
}

// This parser only consumes the hash-verified bundled SFNT. Its Unicode format
// 12 cmap covers both BMP and supplementary characters. A fallback glyph or a
// host emoji font must not silently change a caption's appearance.
function glyphRanges(bytes) {
  let cmap;
  for (let index = 0; index < bytes.readUInt16BE(4); index++) {
    const table = 12 + index * 16;
    if (bytes.toString('ascii', table, table + 4) === 'cmap') cmap = bytes.readUInt32BE(table + 8);
  }
  if (cmap === undefined) throw new Error('Caption font cmap missing');
  for (let index = 0; index < bytes.readUInt16BE(cmap + 2); index++) {
    const record = cmap + 4 + index * 8;
    const platform = bytes.readUInt16BE(record), encoding = bytes.readUInt16BE(record + 2);
    const offset = cmap + bytes.readUInt32BE(record + 4);
    if ((platform === 0 || (platform === 3 && encoding === 10)) && bytes.readUInt16BE(offset) === 12) {
      return Array.from({ length: bytes.readUInt32BE(offset + 12) }, (_, i) => {
        const group = offset + 16 + i * 12;
        return [bytes.readUInt32BE(group), bytes.readUInt32BE(group + 4), bytes.readUInt32BE(group + 8)];
      });
    }
  }
  throw new Error('Caption font Unicode cmap missing');
}

function checkGlyphs(bytes, runs) {
  const ranges = glyphRanges(bytes);
  for (const char of new Set(runs.flatMap(run => Array.from(run.text)))) {
    if ('\n\r\t'.includes(char)) continue;
    const code = char.codePointAt(0);
    if (!ranges.some(([start, end, glyph]) => code >= start && code <= end && glyph + code - start > 0)) {
      throw new Error(`Caption font missing glyph U+${code.toString(16).toUpperCase()}`);
    }
  }
}

// Check glyphs against the bundled font and record the binding (no writes).
// The font runs (and so the compiled view of a v2 document) are computed once.
export async function planCaptionFont(project, templates) {
  const runs = fontRuns(project, templates);
  if (!runs.length) return false;
  checkGlyphs(await fontBytes(fileURLToPath(new URL(manifest.file, bundle))), runs);
  project.caption_font = { ...CAPTION_FONT };
  return true;
}

// Copy the bundled bytes into a project; an existing identical copy is reused.
export async function installCaptionFont(root) {
  await fs.mkdir(path.join(root, 'fonts'), { recursive: true });
  const target = path.join(root, CAPTION_FONT.file);
  await writeOnce(target, { source: fileURLToPath(new URL(manifest.file, bundle)) }, { expected: CAPTION_FONT.sha256, mismatch: 'Caption font hash mismatch' });
  await fontBytes(target);
}

export async function bindCaptionFont(root, project, templates) {
  const binding = { ...project };
  if (!(await planCaptionFont(binding, templates))) return;
  await fs.mkdir(path.join(root, 'fonts'));
  await installCaptionFont(root);
  project.caption_font = binding.caption_font;
}

export async function verifyCaptionFont(root, project, templates) {
  if (!project.caption_font) return; // Legacy projects retain their old rendering contract.
  validateCaptionFont(project.caption_font);
  checkGlyphs(await fontBytes(path.join(root, project.caption_font.file)), fontRuns(project, templates));
}

export async function copyCaptionFont(root, destination, project, templates) {
  if (!project.caption_font) return;
  await fs.mkdir(path.join(destination, 'fonts'));
  await fs.copyFile(path.join(root, project.caption_font.file), path.join(destination, project.caption_font.file), 1);
  await verifyCaptionFont(destination, project, templates);
}

export function captionFontCss(project) {
  if (!project.caption_font) return '';
  return `@font-face{font-family:'${FONT_FAMILY}';src:url('${project.caption_font.file}') format('truetype');font-weight:100 900;font-style:normal;font-display:block}.caption,.gfx{font-family:'${FONT_FAMILY}';font-synthesis:none}`;
}

export function captionFontReady(project, templates) {
  if (!project.caption_font) return '';
  const weights = [...new Set(fontRuns(project, templates).map(run => run.weight))];
  // Producer's tween interceptor owns __hfTimelinesBuilding, and fonts.ready
  // resolves even on font failure. Use its explicit async build registry.
  // Producer 0.8.53 treated rejected build promises as settled (gate re-verified
  // on 0.8.108 by tests/font-render.integration.mjs): on error keep
  // this readiness entry pending so its bounded readiness timeout fails the
  // job. The rejection remains observable through __captionFontReady.
  return `window.__captionFontLoaded=false;
window.__captionFontReady=Promise.all(${JSON.stringify(weights)}.map(async weight=>{
  const faces=await document.fonts.load(weight+' 32px "${FONT_FAMILY}"','字幕');
  if(faces.length!==1||faces[0].status!=='loaded')throw new Error('Caption font load failed');
})).then(()=>{window.__captionFontLoaded=true;});
window.__hf=window.__hf||{};window.__hf.buildReady=window.__hf.buildReady||{};
window.__hf.buildReady.captionFont=window.__captionFontReady.catch(error=>{
  console.error('Caption font load failed',error);return new Promise(()=>{});
});`;
}
