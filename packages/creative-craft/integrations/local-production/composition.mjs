import { validate } from './project.mjs';
import { validateV2 } from './edit-document.mjs';
import { envelopeIndex, isV2, itemEnvelope, resolveCaptions, volumeLane } from './timeline.mjs';
import { getTemplate, renderGraphic, templateSet, escapeHtml as escape } from './templates.mjs';
import { captionFontCss, captionFontReady } from './caption-font.mjs';
import { compiledView } from './source-frames.mjs';

const seconds = value => String(Math.round(value * 1e9) / 1e9);
// Half-open intervals must include the frame at their start, exclude the frame
// at their end. Bias serialized edges by 1 ns to absorb floating-point error;
// never round an edge above the renderer's exact frame / fps sample time.
// This is far below one frame and does not change source-media seek positions.
const timelineTiming = (start, end) => {
  const from = Math.max(0, start - 1e-9);
  const to = Math.max(0, end - 1e-9);
  return `data-start="${from}" data-duration="${to - from}"`;
};
const captionStyle = (style, height) => style ? `top:${seconds(style.centerY * 100)}%;bottom:auto;transform:translateY(-50%);font-size:${seconds(height * style.fontHeight)}px;font-weight:${style.weight};line-height:1.1;color:${style.color};-webkit-text-stroke:${seconds(height * style.strokeWidth)}px #222222;paint-order:stroke fill;text-shadow:0 1px 1px #222222;background:transparent;padding:0;border-radius:0` : '';

// options.templates: the revision's template set (loadProject); required when
// the revision pins its templates, else the execution-layer templates.
// options.declickSeconds: test injection only (envelopeIndex); renders use the default.
export function compose(project, canvas = project.canvas, { templates, declickSeconds } = {}) {
  if (isV2(project)) return composeV2(project, canvas, templateSet(project, templates), { declickSeconds });
  const { duration, frames } = validate(project);
  const { width, height } = canvas;
  const { fps } = project.canvas;
  const assets = new Map(project.assets.map(a => [a.id, a]));
  const elements = [], cues = [];
  const timing = (start, length, source = 0) => `${timelineTiming(start, start + length)} data-media-start="${source}"`;
  let cursor = 0;
  project.clips.forEach((clip, index) => {
    const start = cursor / fps, length = clip.frames / fps;
    const asset = assets.get(clip.asset_id);
    elements.push(`<video id="picture-${index}" src="${asset.file}" ${timing(start, length, clip.in_seconds)} data-track-index="0" muted playsinline style="object-fit:${clip.fit}"></video>`);
    if (asset.audio && clip.volume > 0) elements.push(`<audio id="sound-${index}" src="${asset.file}" ${timing(start, length, clip.in_seconds)} data-track-index="10" data-volume="${clip.volume}"></audio>`);
    clip.captions.forEach(caption => {
      const from = Math.max(clip.in_seconds, caption.from);
      const to = Math.min(clip.in_seconds + length, caption.to);
      if (to <= from) return;
      const cue = { start: start + from - clip.in_seconds, end: start + to - clip.in_seconds, text: caption.text };
      const cueId = `caption-${cues.length}`;
      const matched = caption.style ? ` style="${captionStyle(caption.style, height)}"` : '';
      elements.push(`<div id="${cueId}" class="caption"${matched} ${timelineTiming(cue.start, cue.end)} data-track-index="20">${escape(cue.text)}</div>`);
      cues.push(cue);
    });
    cursor += clip.frames;
  });
  project.audio.forEach((track, index) => {
    const length = Math.min(track.frames, frames - track.start_frame) / fps;
    if (length <= 0 || track.volume === 0) return;
    elements.push(`<audio id="bed-${index}" src="${assets.get(track.asset_id).file}" ${timing(track.start_frame / fps, length, track.in_seconds)} data-track-index="${30 + index}" data-volume="${track.volume}"></audio>`);
  });
  return { html: page(project, width, height, duration, elements), cues, duration, frames };
}

// EditDocument v2: tracks are layered in array order (later = above). Each
// track gets its own data-track-index lane (video n, sound 100+n, captions
// 200+n) and video/caption elements an explicit z-index; captions sit above
// every picture (captions carry class "clip" for HyperFrames lint/Studio; the
// render runtime does not select on it). transform x/y is the item centre as a fraction of the canvas,
// scale the fraction of the canvas box the item occupies.
//
// P2 mapping (HyperFrames 0.8.108): speed → data-playback-rate on <video> and
// <audio>; every time-varying sound level (fades, equal-power crossfade,
// cut-edge declick, duck) → one
// data-automation volume lane per <audio> (clip-local seconds, absolute linear
// gain; data-volume omitted so the lane is the only gain), never a GSAP volume
// tween; picture fades and crossfades → contiguous GSAP opacity fromTo tweens on
// an element authored at opacity 0. Items joined by a crossfade alternate
// between two data-track-index rolls (+40) so overlapping clips never share one.
// Graphic items render fixed template markup inside the box of their placement
// (vars.placement or the template default); 1 em = 1% of the shorter canvas edge.
// Templates come from the revision's set: its bound bytes when pinned, else the
// execution-layer templates.
function composeV2(doc, canvas, templates, { declickSeconds } = {}) {
  const { duration, frames } = validateV2(doc, { templates });
  // Source frame alignment: the compiled view (truncated in-points of video-track
  // items corrected). renderProject passes the view it computed once (used as is
  // here); a document passed in is compiled here, once. Everything below
  // (data-media-start, linked caption windows, the font runs of page()) uses it.
  doc = compiledView(doc);
  const { width, height } = canvas;
  const { fps } = doc.canvas;
  const assets = new Map(doc.assets.map(a => [a.id, a]));
  const lanes = new Map(doc.tracks.map((t, i) => [t.id, i]));
  const kinds = new Map(doc.tracks.map(t => [t.id, t.kind]));
  // Lane order, then time: a crossfading item follows (and paints over) its predecessor.
  const byLane = (a, b) => lanes.get(a.track_id) - lanes.get(b.track_id) || (a.start_frame ?? 0) - (b.start_frame ?? 0);
  // Crossfade neighbours and duck curves, built once for this compile.
  const index = envelopeIndex(doc, { declickSeconds });
  const rolls = new Map();
  for (const item of doc.items.filter(i => i.kind !== 'caption').sort(byLane)) {
    const previous = item.transition_in ? index.predecessor.get(item) : null;
    rolls.set(item.id, previous ? 1 - rolls.get(previous.id) : 0);
  }
  const span = item => timelineTiming(item.start_frame / fps, (item.start_frame + item.frames) / fps);
  const timing = item => `${span(item)} data-media-start="${item.source_in_seconds}"${(item.speed ?? 1) !== 1 ? ` data-playback-rate="${item.speed}"` : ''}`;
  const percent = v => `${seconds(v * 100)}%`;
  const elements = [], tweens = [], skippedLanes = [];
  // Opacity animation: authored hidden, then one tween per envelope segment.
  const visual = (elementId, item, style) => {
    const envelope = itemEnvelope(doc, item, 'visual', index);
    if (!envelope) { if ('opacity' in item && item.opacity !== 1) style.push(`opacity:${item.opacity}`); return; }
    style.push('opacity:0');
    // A finished tween holds its end value, so constant segments after the first
    // need no tween. Like clip edges, tween starts are biased 1 ns early so the
    // frame at a segment start is inside it; durations end a further 2 ns early
    // so adjacent serialized tweens never overlap.
    for (let i = 1; i < envelope.length; i++) {
      const [t0, v0] = envelope[i - 1], [t1, v1] = envelope[i];
      if (i > 1 && v0 === v1) continue;
      tweens.push(`tl.fromTo("#${elementId}",{opacity:${v0}},{opacity:${v1},duration:${seconds(Math.max(0, t1 - t0 - 3e-9))},ease:"none",immediateRender:false},${seconds(Math.max(0, t0 - 1e-9))});`);
    }
  };
  for (const item of doc.items.filter(i => i.kind === 'media' || i.kind === 'graphic').sort(byLane)) {
    const lane = lanes.get(item.track_id), roll = 40 * rolls.get(item.id);
    if (item.kind === 'graphic') {
      const { template, placement: { box }, inner, properties, attributes } = renderGraphic(item, templates);
      const style = [`z-index:${lane + 1}`, `left:${percent(box.left)}`, `top:${percent(box.top)}`, `width:${percent(box.width)}`, `height:${percent(box.height)}`,
        `font-size:${seconds(Math.min(width, height) / 100)}px`, ...properties];
      visual(`g-${item.id}`, item, style);
      elements.push(`<div id="g-${item.id}" class="clip gfx gfx-${template.id}" data-template="${template.id}" data-template-version="${template.version}" ${attributes.join(' ')} style="${style.join(';')}" ${span(item)} data-track-index="${lane}">${inner}</div>`);
      continue;
    }
    const asset = assets.get(item.asset_id);
    if (kinds.get(item.track_id) === 'video') {
      const style = [`z-index:${lane + 1}`, `object-fit:${item.fit ?? 'contain'}`];
      if (item.transform) {
        const { x, y, scale } = item.transform;
        style.push(`left:${percent(x - scale / 2)}`, `top:${percent(y - scale / 2)}`, 'right:auto', 'bottom:auto', `width:${percent(scale)}`, `height:${percent(scale)}`);
      }
      visual(`v-${item.id}`, item, style);
      elements.push(`<video id="v-${item.id}" src="${asset.file}" ${timing(item)} data-track-index="${lane + roll}" muted playsinline style="${style.join(';')}"></video>`);
    }
    if (asset.audio && item.volume > 0) {
      const { envelope, skipped } = volumeLane(doc, item, index), start = item.start_frame / fps;
      if (skipped) skippedLanes.push(skipped);
      let level = `data-volume="${item.volume}"`;
      if (envelope) {
        const automation = { version: 1, lanes: [{ target: 'volume', points: envelope.map(([t, v]) => ({ t: Math.max(0, Math.round((t - start) * 1e6) / 1e6), v })) }] };
        level = `data-automation="${escape(JSON.stringify(automation))}"`;
      }
      elements.push(`<audio id="a-${item.id}" src="${asset.file}" ${timing(item)} data-track-index="${100 + lane + roll}" ${level}></audio>`);
    }
  }
  const cues = [];
  for (const { item, start, end } of resolveCaptions(doc).sort((a, b) => lanes.get(a.item.track_id) - lanes.get(b.item.track_id))) {
    const lane = lanes.get(item.track_id);
    elements.push(`<div id="c-${item.id}" class="clip caption" style="z-index:${200 + lane};${captionStyle(item.style, height)}" ${timelineTiming(start, end)} data-track-index="${200 + lane}">${escape(item.text)}</div>`);
    cues.push({ start, end, text: item.text });
  }
  cues.sort((a, b) => a.start - b.start);
  const graphics = doc.items.filter(i => i.kind === 'graphic').length;
  const css = [...new Set(doc.items.filter(i => i.kind === 'graphic').map(i => i.template))].map(name => getTemplate(name, templates).css).join('');
  return { html: page(doc, width, height, duration, elements, { css, tweens, templates }), cues, graphics, duration, frames,
    declick: { skipped_lanes: skippedLanes } };
}

function page(project, width, height, duration, elements, { css = '', tweens = [], templates } = {}) {
  return `<!doctype html>
<html><head><meta charset="utf-8"><title>${escape(project.title)}</title>
<script src="gsap.min.js"></script>
<style>html,body{margin:0;background:#000;overflow:hidden}#main{position:relative;width:${width}px;height:${height}px;background:#000}video{position:absolute;inset:0;width:100%;height:100%}.caption{position:absolute;left:7%;right:7%;bottom:8%;text-align:center;color:#fff;white-space:pre-wrap;font:600 ${Math.round(height * 0.052)}px/1.35 'PingFang SC','Noto Sans CJK SC',sans-serif;text-shadow:0 2px 4px #000;background:rgba(0,0,0,.65);padding:8px;border-radius:6px}.gfx{position:absolute;box-sizing:border-box;overflow:hidden;color:#fff}${css}</style></head>
<body><style>${captionFontCss(project)}</style><div id="main" data-composition-id="main" data-width="${width}" data-height="${height}" data-duration="${seconds(duration)}">${elements.join('\n')}</div>
<script>${captionFontReady(project, templates)}
window.__timelines=window.__timelines||{};const tl=gsap.timeline({paused:true});tl.to({}, {duration:${seconds(duration)}});${tweens.join('')}window.__timelines.main=tl;</script></body></html>`;
}

export function webVtt(cues) {
  const stamp = s => {
    const ms = Math.round(s * 1000);
    return `${String(Math.floor(ms / 3600000)).padStart(2, '0')}:${String(Math.floor(ms / 60000) % 60).padStart(2, '0')}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}.${String(ms % 1000).padStart(3, '0')}`;
  };
  return `WEBVTT\n\n${cues.map(c => `${stamp(c.start)} --> ${stamp(c.end)}\n${escape(c.text).replace(/\r?\n\r?\n/g, '\n')}\n`).join('\n')}`;
}
