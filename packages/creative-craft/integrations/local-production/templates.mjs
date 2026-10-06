import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

// Graphic templates are versioned execution-layer resources: fixed HTML/CSS in
// this repository plus typed variables. Documents only choose a template id and
// supply primitive values; nothing caller-supplied becomes markup, CSS, a URL or
// a script. Text is HTML-escaped, colours are #rrggbb, booleans become a fixed
// data attribute, numbers a CSS custom property.
// v2 definition format: named placements (each a box) instead of one box, and
// text sizes only through font_em (CSS reads them as var(--fs-<name>)).
export const TEMPLATE_SCHEMA = 'creative-craft.graphic-template.v2';
export const SAFE_MARGIN = 0.05;
// Reserved graphic var: selects one of the template's named placements.
export const PLACEMENT_VAR = 'placement';
// Minimum rendered text size: 3 em = 3% of the shorter canvas edge (portrait
// 1080 wide: 32.4 px). The rule is stated against the canvas width; on landscape
// canvases the shorter edge (height) is used so 1 em keeps one meaning for every
// aspect ratio (see README).
export let MIN_TEXT_EM = 3;
const fail = message => { throw new Error(message); };
// Shared with document validation (edit-document.mjs): template ids, var names and
// the structural rule for var values (template types are checked separately).
export const TEMPLATE_ID = /^[a-z][a-z0-9-]{0,47}$/;
export const VAR_NAME = /^[a-z][a-z0-9_]{0,31}$/;
// String length counts UTF-16 code units (JS length), as the contract requires.
export const isGraphicVarValue = v => (typeof v === 'string' && v.length >= 1 && v.length <= 200) || (typeof v === 'number' && Number.isFinite(v)) || typeof v === 'boolean';
const COLOR = /^#[0-9a-fA-F]{6}$/;
const FORBIDDEN = /<\s*(script|style|iframe|object|embed|img|link|meta|svg|math|base|form)|\son\w+\s*=|javascript:|url\s*\(|@import|expression\s*\(|\b(src|href|srcset|action)\s*=/i;
export const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const plain = value => value && typeof value === 'object' && !Array.isArray(value);
const exact = (value, allowed, label) => {
  if (!plain(value)) fail(`${label} must be an object`);
  for (const key of Object.keys(value)) if (!allowed.includes(key)) fail(`${label}: unknown field ${key}`);
};
const fraction = v => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 1;
const PLACEMENT_NAME = /^[a-z][a-z0-9_]{0,31}$/;
// CSS properties (vendor prefix stripped) that can change rendered text size
// other than font-size:var(--fs-<var>).
const TEXT_SIZE_PROPERTIES = ['font', 'zoom', 'transform', 'scale', 'font-size-adjust', 'text-size-adjust'];

function validateBox(name, label, box) {
  exact(box, ['left', 'top', 'width', 'height'], `Graphic template ${name} placement ${label}`);
  const { left, top, width, height } = box;
  if (![left, top, width, height].every(fraction) || width <= 0 || height <= 0 || left < SAFE_MARGIN || top < SAFE_MARGIN ||
      left + width > 1 - SAFE_MARGIN + 1e-9 || top + height > 1 - SAFE_MARGIN + 1e-9) fail(`Graphic template ${name} placement ${label} leaves the 5% safe area`);
}

function validateDefinition(name, def) {
  const label = `Graphic template ${name}`;
  exact(def, ['type', 'optional', 'default', 'max_length', 'font_em', 'weight', 'min', 'max'], `${label} var`);
  if (!['string', 'color', 'boolean', 'number'].includes(def.type)) fail(`${label}: unsupported var type ${def.type}`);
  if ('optional' in def && typeof def.optional !== 'boolean') fail(`${label}: optional must be boolean`);
  if (def.type === 'string') {
    if ('default' in def || !Number.isInteger(def.max_length) || def.max_length < 1 || def.max_length > 200 ||
        typeof def.font_em !== 'number' || !(def.font_em > 0) || ![400, 600, 700, 900].includes(def.weight)) fail(`${label}: string vars need max_length 1–200, font_em and weight`);
  } else if ('max_length' in def || 'font_em' in def || 'weight' in def) fail(`${label}: text metrics only apply to strings`);
  if (def.type === 'number' && !(Number.isFinite(def.min) && Number.isFinite(def.max) && def.min <= def.max)) fail(`${label}: number vars need min/max`);
  if (def.type !== 'number' && ('min' in def || 'max' in def)) fail(`${label}: min/max only apply to numbers`);
  if ('default' in def && !def.optional) fail(`${label}: only optional vars take a default`);
  if ('default' in def) checkValue(name, def, def.default, label);
}

function checkValue(name, def, value, label) {
  const ok = def.type === 'string' ? typeof value === 'string' && value.length >= 1 && value.length <= def.max_length
    : def.type === 'color' ? typeof value === 'string' && COLOR.test(value)
      : def.type === 'boolean' ? typeof value === 'boolean'
        : typeof value === 'number' && Number.isFinite(value) && value >= def.min && value <= def.max;
  if (!ok) fail(`${label}: var ${name} must be ${def.type === 'string' ? `a string of 1–${def.max_length} characters` : def.type === 'color' ? 'a #rrggbb colour' : def.type === 'number' ? `a number in ${def.min}–${def.max}` : 'a boolean'}`);
}

// Fails closed at load: a template that could escape its box, the safe area or
// the fixed-markup rule never becomes available.
export function validateTemplate(name, template) {
  exact(template, ['schema_version', 'id', 'version', 'description', 'placements', 'default_placement', 'vars', 'html', 'css'], `Graphic template ${name}`);
  if (template.schema_version !== TEMPLATE_SCHEMA || template.id !== name || !TEMPLATE_ID.test(name) ||
      !Number.isInteger(template.version) || template.version < 1 || typeof template.description !== 'string') fail(`Invalid graphic template identity: ${name}`);
  if (!plain(template.placements) || !Object.keys(template.placements).length) fail(`Graphic template ${name} has no placements`);
  for (const [key, box] of Object.entries(template.placements)) {
    if (!PLACEMENT_NAME.test(key)) fail(`Graphic template ${name}: invalid placement name ${key}`);
    validateBox(name, key, box);
  }
  if (!Object.hasOwn(template.placements, template.default_placement)) fail(`Graphic template ${name}: default_placement must name one of its placements`);
  if (!plain(template.vars) || !Object.keys(template.vars).length) fail(`Graphic template ${name} has no vars`);
  if (PLACEMENT_VAR in template.vars) fail(`Graphic template ${name}: var name ${PLACEMENT_VAR} is reserved`);
  const narrowest = Math.min(...Object.values(template.placements).map(b => b.width));
  for (const [key, def] of Object.entries(template.vars)) {
    if (!VAR_NAME.test(key)) fail(`Graphic template ${name}: invalid var name ${key}`);
    validateDefinition(key, def);
    if (def.type !== 'string') continue;
    // Worst case: every character is full-width (1 em). Every placement box is
    // at least 100 × width em wide because 1 em = 1% of the shorter canvas edge.
    if (def.max_length * def.font_em > 100 * narrowest * 0.95) fail(`Graphic template ${name}: ${key} cannot fit its box at max_length`);
    if (!template.css.includes(`font-size:var(--fs-${key})`)) fail(`Graphic template ${name}: ${key} must be sized by font-size:var(--fs-${key})`);
  }
  if (typeof template.html !== 'string' || typeof template.css !== 'string' || FORBIDDEN.test(template.html) || FORBIDDEN.test(template.css) ||
      template.css.includes('<')) fail(`Graphic template ${name} contains forbidden markup`);
  // Text sizes come only from font_em (emitted as --fs-<var>), so the minimum
  // size rule cannot be bypassed by a literal font-size in the CSS.
  if ([...template.css.matchAll(/font-size\s*:\s*([^;}]*)/g)].some(m => !/^var\(--fs-[a-z][a-z0-9_]*\)$/.test(m[1].trim()))) fail(`Graphic template ${name}: CSS font-size must be var(--fs-<var>)`);
  // Nor by anything else that changes rendered text size: the font shorthand,
  // zoom, transforms/scale (translate-only positioning is not offered either),
  // size-adjust properties, or redefining a --fs-* property below the root.
  // Comments and escapes are refused so none of these can be spelled around.
  if (/\/\*|\\/.test(template.css)) fail(`Graphic template ${name}: CSS comments and escapes are not allowed`);
  for (const [, property] of template.css.matchAll(/(?:^|[{;])\s*([-a-zA-Z0-9_]+)\s*:/g)) {
    const bare = property.toLowerCase().replace(/^-(webkit|moz|ms|o)-/, '');
    if (TEXT_SIZE_PROPERTIES.includes(bare) || bare.startsWith('--fs-')) fail(`Graphic template ${name}: CSS property ${property} could change text size`);
  }
  if (/\b(scale|scale3d|scalex|scaley|scalez|matrix|matrix3d)\s*\(/i.test(template.css)) fail(`Graphic template ${name}: CSS scale()/matrix() could change text size`);
  // Only inline <span> markup with class attributes: one timeline row per graphic
  // (HyperFrames lint flags nested block structure inside a timed element).
  const tags = [...template.html.matchAll(/<\/?([a-zA-Z0-9-]+)([^>]*)>/g)];
  if (tags.some(([, tag, attrs]) => tag !== 'span' || !/^(\s+class="[a-z0-9 -]+")?$/.test(attrs))) fail(`Graphic template ${name}: html may only contain <span class="…"> elements`);
  const holes = [...template.html.matchAll(/\{\{([^}]*)\}\}/g)].map(m => m[1]);
  const strings = Object.keys(template.vars).filter(k => template.vars[k].type === 'string');
  if (holes.length !== strings.length || holes.some(h => !strings.includes(h)) || new Set(holes).size !== holes.length) fail(`Graphic template ${name}: each string var must appear exactly once in html`);
  // Every CSS rule is scoped to this template's root class.
  for (const rule of template.css.split('}').map(r => r.trim()).filter(Boolean)) {
    const [selectors] = rule.split('{');
    if (!rule.includes('{') || selectors.split(',').some(s => !s.trim().startsWith(`.gfx-${name}`))) fail(`Graphic template ${name}: CSS must be scoped to .gfx-${name}`);
  }
  return template;
}

const directory = new URL('./templates/', import.meta.url);
// Minimum text size: a string var below MIN_TEXT_EM is raised to it before
// validation, so the box-fit check runs on the size that will actually render.
export function enforceMinimumText(template) {
  for (const def of Object.values(template.vars ?? {})) if (def?.type === 'string' && typeof def.font_em === 'number' && def.font_em < MIN_TEXT_EM) def.font_em = MIN_TEXT_EM;
  return template;
}
const freeze = value => { for (const v of Object.values(value)) if (v && typeof v === 'object') freeze(v); return Object.freeze(value); };
export const templateSha256 = bytes => createHash('sha256').update(bytes).digest('hex');
// Deterministic serialization of a normalized template: these are the bytes a
// revision binds, and their sha256 is the binding digest.
export const serializeTemplate = template => `${JSON.stringify(template, null, 2)}\n`;
const decode = bytes => Buffer.from(bytes).toString('utf8');

// Execution-layer source bytes -> the normalized template (minimum text size
// applied, every load rule checked) and its serialized bytes and digest.
export function normalizeTemplate(name, source) {
  const template = validateTemplate(name, enforceMinimumText(JSON.parse(decode(source))));
  const bytes = Buffer.from(serializeTemplate(template));
  return Object.freeze({ template: freeze(template), bytes, sha256: templateSha256(bytes) });
}

// Project-bound bytes are used exactly as bound: the safety and structure rules
// (validateTemplate) run again, but nothing is rewritten, so a later change to
// a normalization rule (such as MIN_TEXT_EM) never changes a pinned revision.
// Bindings written before normalization pinned raw source bytes (detected as
// bytes that are not the serialization of their own content); those were
// normalized on every load, so if the current normalization would change them
// they are refused as a rule difference instead of being silently rewritten.
export function parseBoundTemplate(name, bytes) {
  const text = decode(bytes), template = validateTemplate(name, JSON.parse(text));
  if (text !== serializeTemplate(template) && serializeTemplate(enforceMinimumText(structuredClone(template))) !== serializeTemplate(template)) {
    fail(`Graphic template ${name}: bound raw (pre-normalization) bytes differ from the current template rules (text below the ${MIN_TEXT_EM} em minimum); they are not rewritten`);
  }
  return freeze(template);
}

// Execution-layer templates: normalized templates plus the serialized bytes
// and digest a revision binds (graphic_templates); revisions without bindings
// render with whatever this registry holds.
function loadRuntime(dir) {
  return new Map(readdirSync(dir).filter(n => n.endsWith('.json')).sort().map(file => {
    const name = file.slice(0, -5);
    return [name, normalizeTemplate(name, readFileSync(new URL(file, dir)))];
  }));
}
let runtimeDir = directory;
let RUNTIME = loadRuntime(directory);
export let TEMPLATES = new Map([...RUNTIME].map(([name, entry]) => [name, entry.template]));
export const runtimeTemplate = name => RUNTIME.get(name) ?? fail(`Unknown graphic template: ${name}`);
// Test hook: simulates an execution-layer template upgrade. Returns a restore function.
const swap = (registry, dir) => { [RUNTIME, runtimeDir] = [registry, dir]; TEMPLATES = new Map([...RUNTIME].map(([name, entry]) => [name, entry.template])); };
export function useRuntimeTemplates(dir) {
  const saved = [RUNTIME, runtimeDir];
  dir = dir instanceof URL ? dir : pathToFileURL(dir.endsWith('/') ? dir : `${dir}/`);
  swap(loadRuntime(dir), dir);
  return () => swap(...saved);
}
// Test hook: simulates a stricter minimum text rule (execution layer reloaded).
export function useMinimumText(em) {
  const saved = [MIN_TEXT_EM, RUNTIME, runtimeDir];
  MIN_TEXT_EM = em;
  swap(loadRuntime(runtimeDir), runtimeDir);
  return () => { MIN_TEXT_EM = saved[0]; swap(saved[1], saved[2]); };
}

// Template set of a document, always passed explicitly: revisions with
// graphic_templates use only the bound bytes loaded from their project
// (loadProject returns them with the document); revisions without the field
// use the execution-layer registry. A pinned document without its set fails.
export function templateSet(doc, templates) {
  if (templates) return templates;
  if (doc?.graphic_templates !== undefined) fail('Graphic templates pinned to this revision are not loaded; read the revision with its template set (loadProject)');
  return TEMPLATES;
}

export const getTemplate = (name, templates = TEMPLATES) => templates.get(name) ?? fail(`Unknown graphic template: ${name}`);
// Receipt provenance: pinned bindings name the project file; unpinned
// (historical) revisions name the execution-layer bytes that rendered them.
export function templateProvenance(doc) {
  if (doc.graphic_templates) return doc.graphic_templates.map(({ id, version, sha256, file }) => ({ id, version, sha256, pinned: true, source: 'project', file }))
    .sort((a, b) => a.id.localeCompare(b.id));
  return [...new Set((doc.items ?? []).filter(i => i.kind === 'graphic').map(i => i.template))].sort()
    .map(id => { const { template, sha256 } = runtimeTemplate(id); return { id, version: template.version, sha256, pinned: false, source: 'runtime' }; });
}

// Node-side semantic check of a graphic item's vars against its template.
export function validateGraphicVars(item, templates = TEMPLATES) {
  const template = getTemplate(item.template, templates), label = `Graphic item ${item.id}`;
  for (const key of Object.keys(item.vars)) if (key !== PLACEMENT_VAR && !(key in template.vars)) fail(`${label}: template ${template.id} has no var ${key}`);
  if (PLACEMENT_VAR in item.vars && !(typeof item.vars[PLACEMENT_VAR] === 'string' && Object.hasOwn(template.placements, item.vars[PLACEMENT_VAR]))) {
    fail(`${label}: placement must be one of ${Object.keys(template.placements).join(', ')} (template ${template.id})`);
  }
  for (const [key, def] of Object.entries(template.vars)) {
    if (!(key in item.vars)) { if (!def.optional) fail(`${label}: missing required var ${key}`); continue; }
    checkValue(key, def, item.vars[key], label);
  }
  return template;
}

// Placement of a validated graphic item: its named box, or the template default.
export function graphicPlacement(item, templates = TEMPLATES) {
  const template = getTemplate(item.template, templates), name = item.vars?.[PLACEMENT_VAR] ?? template.default_placement;
  return { name, box: template.placements[name] ?? fail(`Graphic item ${item.id}: unknown placement ${name}`) };
}

// Resolved values (defaults applied) for a validated graphic item.
export function graphicValues(item, templates = TEMPLATES) {
  const template = getTemplate(item.template, templates);
  return Object.fromEntries(Object.entries(template.vars).map(([k, def]) => [k, k in item.vars ? item.vars[k] : def.default]));
}

// Text runs the bound font must cover, with their weights.
export function graphicTexts(item, templates = TEMPLATES) {
  const template = getTemplate(item.template, templates), values = graphicValues(item, templates);
  return Object.entries(template.vars).filter(([k, d]) => d.type === 'string' && typeof values[k] === 'string')
    .map(([k, d]) => ({ text: values[k], weight: d.weight, font_em: d.font_em, var: k }));
}

// Fixed markup with escaped text. Returns the inner HTML, placement, root
// attributes and inline custom properties; the caller adds timing, id and stacking.
export function renderGraphic(item, templates = TEMPLATES) {
  const template = getTemplate(item.template, templates), values = graphicValues(item, templates), placement = graphicPlacement(item, templates);
  const inner = template.html.replace(/\{\{([a-z][a-z0-9_]*)\}\}/g, (_, key) => values[key] === undefined ? '' : escapeHtml(values[key]));
  const properties = [], attributes = [];
  for (const [key, def] of Object.entries(template.vars)) {
    if (def.type === 'string') properties.push(`--fs-${key}:${def.font_em}em`);
    const value = values[key];
    if (value === undefined) continue;
    if (def.type === 'color' || def.type === 'number') properties.push(`--${key}:${def.type === 'color' ? value.toLowerCase() : String(value)}`);
    if (def.type === 'boolean') attributes.push(`data-${key.replace(/_/g, '-')}="${value ? 'true' : 'false'}"`);
  }
  attributes.push(`data-placement="${placement.name}"`);
  return { template, placement, inner, properties, attributes };
}
