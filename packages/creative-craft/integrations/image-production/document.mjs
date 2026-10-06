import { fontManifest } from './font.mjs';

export const SCHEMA = 'creative-craft.local-image.v1';
export const LIMITS = Object.freeze({ pixels: 16_777_216, sourceBytes: 20_000_000, renderBytes: 16_777_216 * 5, objects: 100, assets: 64, operations: 100, revisions: 1000 });
const fail = message => { throw new Error(message); };
export function record(value, keys, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.getPrototypeOf(value) !== Object.prototype) fail(`${label} must be an object`);
  for (const key of Object.keys(value)) if (!keys.includes(key)) fail(`${label}: unsupported field ${key}`);
}
export function id(value, label = 'id') {
  if (typeof value !== 'string' || !/^[a-zA-Z][a-zA-Z0-9_-]{0,63}$/.test(value)) fail(`Invalid ${label}`);
}
export function string(value, label, max = 2000) {
  if (typeof value !== 'string' || !value.length || value.length > max) fail(`Invalid ${label}`);
}
export function number(value, label, min, max, integer = false) {
  if (!Number.isFinite(value) || value < min || value > max || (integer && !Number.isInteger(value))) fail(`Invalid ${label}`);
}
export function boolean(value, label) { if (typeof value !== 'boolean') fail(`Invalid ${label}`); }
export const color = value => { if (typeof value !== 'string' || !/^#[0-9a-fA-F]{6}$/.test(value)) fail('Color must be #RRGGBB'); };
export const digest = value => { if (typeof value !== 'string' || !/^[a-f0-9]{64}$/.test(value)) fail('Invalid SHA-256'); };

export function validateDocument(doc) {
  record(doc, ['schema', 'project_id', 'title', 'revision', 'parent_sha256', 'canvas', 'assets', 'font', 'objects', 'change'], 'document');
  if (doc.schema !== SCHEMA) fail('Unsupported image document schema');
  id(doc.project_id, 'project_id'); string(doc.title, 'title', 200);
  number(doc.revision, 'revision', 1, LIMITS.revisions, true);
  if (doc.revision === 1) { if (doc.parent_sha256 !== null) fail('Initial revision must have null parent'); }
  else digest(doc.parent_sha256);
  record(doc.canvas, ['width', 'height', 'background'], 'canvas');
  number(doc.canvas.width, 'canvas.width', 64, 8192, true);
  number(doc.canvas.height, 'canvas.height', 64, 8192, true);
  if (doc.canvas.width * doc.canvas.height > LIMITS.pixels) fail('Canvas pixel limit exceeded');
  color(doc.canvas.background);
  record(doc.font, ['profile', 'family', 'file', 'sha256', 'weight'], 'font');
  for (const key of ['profile', 'family', 'sha256', 'weight']) if (doc.font[key] !== fontManifest[key]) fail(`Unsupported font ${key}`);
  if (doc.font.file !== `fonts/${fontManifest.sha256}.otf`) fail('Invalid bound font path');
  if (!Array.isArray(doc.assets) || doc.assets.length > LIMITS.assets) fail('Invalid assets list');
  const assets = new Set();
  for (const asset of doc.assets) {
    validateAsset(asset);
    if (assets.has(asset.id)) fail('Duplicate asset id'); assets.add(asset.id);
  }
  if (!Array.isArray(doc.objects) || !doc.objects.length || doc.objects.length > LIMITS.objects) fail('Invalid objects list');
  const ids = new Set();
  for (const object of doc.objects) {
    const common = ['id', 'kind', 'locked', 'visible', 'x', 'y', 'width', 'height', 'opacity'];
    const extra = { image: ['asset_id', 'fit'], text: ['text', 'font_size', 'color', 'align', 'line_height'], rect: ['color', 'radius'] }[object.kind];
    if (!Array.isArray(extra)) fail('Unsupported object kind');
    record(object, [...common, ...extra], 'object'); id(object.id, 'object.id');
    if (ids.has(object.id)) fail('Duplicate object id'); ids.add(object.id);
    boolean(object.locked, 'locked'); boolean(object.visible, 'visible');
    number(object.x, 'object.x', 0, doc.canvas.width); number(object.y, 'object.y', 0, doc.canvas.height);
    number(object.width, 'object.width', 1, doc.canvas.width); number(object.height, 'object.height', 1, doc.canvas.height);
    if (object.x + object.width > doc.canvas.width || object.y + object.height > doc.canvas.height) fail(`Object outside canvas: ${object.id}`);
    number(object.opacity, 'opacity', 0, 1);
    if (object.kind === 'image') {
      if (!assets.has(object.asset_id)) fail(`Missing asset for ${object.id}`);
      if (!['contain', 'cover', 'fill'].includes(object.fit)) fail('Invalid image fit');
    } else if (object.kind === 'text') {
      string(object.text, 'text');
      // No untrusted markup, external font loading, controls or shaping fallback.
      if (/[\u0000-\u0009\u000B-\u001F\u007F-\u009F\u200B-\u200F\u202A-\u202E\u2060-\u206F]/u.test(object.text)) fail('Unsupported text control character');
      number(object.font_size, 'font_size', 8, 500); number(object.line_height, 'line_height', 1, 2);
      color(object.color); if (!['left', 'center', 'right'].includes(object.align)) fail('Invalid text alignment');
    } else { color(object.color); number(object.radius, 'radius', 0, Math.min(object.width, object.height) / 2); }
  }
  record(doc.change, ['author', 'summary', 'operations', 'candidate'], 'change');
  if (!['human', 'agent', 'system'].includes(doc.change.author)) fail('Invalid change author');
  string(doc.change.summary, 'change.summary', 500);
  if (!Array.isArray(doc.change.operations) || !doc.change.operations.length || doc.change.operations.length > LIMITS.operations || doc.change.operations.some(op => typeof op !== 'string')) fail('Invalid change operations');
  if (doc.change.candidate !== undefined) {
    record(doc.change.candidate, ['id', 'sha256'], 'accepted candidate'); id(doc.change.candidate.id, 'candidate id'); digest(doc.change.candidate.sha256);
    if (doc.change.operations.length !== 1 || doc.change.operations[0] !== 'accept_candidate') fail('Candidate acceptance must be isolated');
  } else if (doc.change.operations.includes('accept_candidate')) fail('Candidate acceptance needs a bound candidate');
  return doc;
}

export function validateAsset(asset) {
  record(asset, ['id', 'file', 'sha256', 'format', 'width', 'height', 'render_file', 'render_sha256'], 'asset');
  id(asset.id, 'asset.id');
  digest(asset.sha256); digest(asset.render_sha256);
  if (!['png', 'jpeg', 'webp'].includes(asset.format)) fail('Unsupported raster format');
  if (asset.file !== `assets/${asset.sha256}.${asset.format}` || asset.render_file !== `assets/${asset.render_sha256}.png`) fail('Invalid content-addressed asset path');
  number(asset.width, 'asset.width', 1, 8192, true); number(asset.height, 'asset.height', 1, 8192, true);
  if (asset.width * asset.height > LIMITS.pixels) fail('Asset pixel limit exceeded');
  return asset;
}
