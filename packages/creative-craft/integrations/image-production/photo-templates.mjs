import { string } from './document.mjs';

const templates = {
  'brand-detail': { width: 1600, height: 2000, margin: 173, top: 615, bottom: 131,
    textX: 173, brandY: 95, brandSize: 52, brandHeight: 78, headlineY: 258, headlineSize: 96, headlineHeight: 280, leading: 1.3, ruleY: 188, footY: 1915, footWidth: 100 },
  'xiaohongshu-cover': { width: 1344, height: 1792, margin: 45, top: 493, bottom: 45,
    textX: 60, brandY: 48, brandSize: 48, brandHeight: 70, headlineY: 166, headlineSize: 110, headlineHeight: 290, leading: 1.25, ruleY: 138, footY: 1770, footWidth: 80 },
};
export function templateCanvas(name) {
  if (typeof name !== 'string' || !Object.hasOwn(templates, name)) throw new Error('Unknown photo template');
  const { width, height } = templates[name]; return { width, height };
}
export function prepareTemplate(brief, canvas, imported) {
  const t = templates[brief.template];
  string(brief.brand, 'template brand');
  if (Object.hasOwn(brief, 'caption')) throw new Error('Purpose templates do not support caption; use object edits');
  if (canvas.width * t.height !== canvas.height * t.width) throw new Error(`Template requires ${t.width}:${t.height} canvas ratio`);
  const scale = canvas.width / t.width, px = value => Math.round(value * scale);
  const margin = px(t.margin), top = px(t.top), bottom = px(t.bottom);
  const availableWidth = canvas.width - margin * 2, availableHeight = canvas.height - top - bottom;
  const { width, height } = imported.asset;
  if (width > availableWidth || height > availableHeight) throw new Error(`Photo ${width}x${height} exceeds template slot ${availableWidth}x${availableHeight}. Supply a larger same-ratio canvas; no automatic resize or crop.`);
  const photo = { id: 'photo', kind: 'image', locked: true, visible: true,
    x: Math.floor((canvas.width - width) / 2), y: top + Math.floor((availableHeight - height) / 2), width, height,
    opacity: 1, asset_id: 'photo', fit: 'contain' };
  const left = px(t.textX), textWidth = canvas.width - left * 2;
  const text = (id, value, y, size, h, leading, color) => ({ id, kind: 'text', locked: false, visible: true, x: left, y: px(y), width: textWidth, height: px(h), opacity: 1, text: value, font_size: px(size), line_height: leading, color, align: 'left' });
  const line = (id, y, width, height, color) => ({ id, kind: 'rect', locked: false, visible: true, x: left, y: px(y), width, height: Math.max(1, px(height)), opacity: 1, radius: 0, color });
  return {
    input: { project_id: brief.project_id, title: brief.title ?? brief.project_id, canvas: { ...canvas, background: brief.background ?? '#f5f2eb' }, objects: [photo,
      text('brand', brief.brand, t.brandY, t.brandSize, t.brandHeight, 1.25, '#39372f'),
      text('headline', brief.headline, t.headlineY, t.headlineSize, t.headlineHeight, t.leading, '#34362e'),
      line('top-rule', t.ruleY, textWidth, 2, '#c1a568'), line('foot-rule', t.footY, px(t.footWidth), 3, '#b49a60')] },
    imports: [imported],
    layout: { template: brief.template, template_version: 1, slot: { x: margin, y: top, width: availableWidth, height: availableHeight }, photo: { x: photo.x, y: photo.y, width, height, scale: 1, cropped: false } },
  };
}
