import { ffprobeJson, run } from './project.mjs';
import { sourceSeconds, speedOf } from './timeline.mjs';
import { mediaTool } from './media-analysis.mjs';
import { compiledView, correctionOf, earliestStart, pictureStream, rational } from './source-frames.mjs';

// Burned-in caption cut points. Source footage often carries captions that are
// part of the picture and switch slightly after the speech they belong to; an
// in-point chosen from speech gaps can still show the previous line, an
// out-point can flash the next one. This is a frame-difference heuristic on a
// horizontal caption band of the SOURCE frames around each cut, not OCR: it
// cannot read, match or judge caption text, only report where the band
// changes as a step.
//
// Step detector (measured on real talking-head / product footage, see README):
// a pixel "steps" at transition k when it is steady (max − min ≤ steadyRange)
// over the steadyFrames frames before k and the steadyFrames frames from k on,
// and its mean level moves by ≥ stepDelta. Burned-in captions are static
// between changes and switch in one frame, so their glyph pixels step together
// inside one text line; hands, faces and camera motion are not steady and do
// not step. The score is the largest share of stepping pixels in any window of
// lineHeight rows inside the band (one caption line). A caption change is a
// transition whose score is ≥ lineShare. When the rest of the frame changes as
// well (mean absolute difference outside the band ≥ shotMad) the step is a
// full-frame shot change, not a caption change: it is reported as a shot and
// treated as aligned.
export const CAPTION_BAND = Object.freeze({ top: 0.62, bottom: 0.86 });
export const CAPTION_CUT = Object.freeze({
  window_seconds: 0.5, // look this far inside the item from each edge (source seconds)
  analysis_short_edge: 360, // frames are scaled so the shorter edge is this many pixels (grey)
  steady_frames: 3, steady_range: 12, step_delta: 40, // 0–255 grey levels
  line_height: 0.05, // caption line window, fraction of frame height
  line_share: 0.10, // ≥ 10% of the line window's pixels step …
  glyph_level: 200, glyph_share: 0.05, // … and ≥ 5% step to or from a light level (light caption glyphs)
  shot_mad: 30, // mean |Δ| outside the band ≥ 30 → full-frame shot change
  concurrency: 4, // cut-point windows decoded in parallel
});
export const CAPTION_METHOD = 'frame-difference step heuristic on the source caption band (not OCR)';
const round = (value, digits = 3) => Math.round(value * 10 ** digits) / 10 ** digits;
// Source times in reports and suggestions: microseconds (far inside any frame, no float noise).
export const round6 = value => round(value, 6);
// Midpoint of decoded frame k: halfway to the next decoded frame (the last one: half a frame).
// A cut time written there shows frame k whatever the rounding, unlike its start.
export const frameMidAt = (times, k, frame) => k + 1 < times.length ? (times[k] + times[k + 1]) / 2 : times[k] + frame / 2;

export function captionBand(option) {
  if (option === undefined) return CAPTION_BAND;
  const { top, bottom } = option ?? {};
  if (![top, bottom].every(v => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 1) || bottom - top < 0.05) {
    throw new Error('Caption band needs 0 ≤ top < bottom ≤ 1 with bottom − top ≥ 0.05');
  }
  return { top, bottom };
}

// Pure detector over decoded grey frames (Uint8Array/Buffer of width × height
// each) with their source times. Returns every transition that is a caption
// change or a full-frame shot change.
export function stepEvents({ frames, times, width, height }, band = CAPTION_BAND, p = CAPTION_CUT) {
  const N = width * height, m = p.steady_frames;
  const y0 = Math.round(height * band.top), y1 = Math.min(height, Math.round(height * band.bottom));
  const lineRows = Math.max(1, Math.round(height * p.line_height));
  const rows = new Float64Array(height), bright = new Float64Array(height), events = [];
  for (let k = m; k + m <= frames.length; k++) {
    rows.fill(0); bright.fill(0);
    let rest = 0, restCount = 0;
    const prev = frames[k - 1], cur = frames[k];
    for (let i = 0; i < N; i++) {
      const y = (i / width) | 0, inBand = y >= y0 && y < y1;
      if (!inBand) { rest += Math.abs(cur[i] - prev[i]); restCount++; continue; }
      let lo = 255, hi = 0, before = 0;
      for (let j = k - m; j < k; j++) { const v = frames[j][i]; if (v < lo) lo = v; if (v > hi) hi = v; before += v; }
      if (hi - lo > p.steady_range) continue;
      lo = 255; hi = 0; let after = 0;
      for (let j = k; j < k + m; j++) { const v = frames[j][i]; if (v < lo) lo = v; if (v > hi) hi = v; after += v; }
      if (hi - lo > p.steady_range || Math.abs(after - before) / m < p.step_delta) continue;
      rows[y]++;
      if (Math.max(after, before) / m >= p.glyph_level) bright[y]++;
    }
    const best = values => {
      let top = 0, acc = 0;
      for (let y = y0; y < y1; y++) { acc += values[y]; if (y - lineRows >= y0) acc -= values[y - lineRows]; if (acc > top) top = acc; }
      return top / (Math.min(lineRows, y1 - y0) * width);
    };
    const lineShare = best(rows), glyphShare = best(bright), restMad = restCount ? rest / restCount : 0;
    if (lineShare < p.line_share || glyphShare < p.glyph_share) continue;
    // frame_mid_seconds: midpoint of the first changed source frame (between its
    // time and the next frame's), the stable in/out time for that frame. Both
    // times stay exact here (judging compares them with the cut point); the
    // check rounds them for the report.
    events.push({ source_seconds: times[k], frame_mid_seconds: frameMidAt(times, k), line_share: round(lineShare), glyph_share: round(glyphShare),
      rest_mad: round(restMad, 1), kind: restMad >= p.shot_mad ? 'shot' : 'caption' });
  }
  return events;
}

// Exact timing of a source file from ffprobe integers rather than printed
// seconds: the analysed picture stream (pictureStream, the same selection and
// ratio parsing import uses for frame_rate) with its time_base, and the
// media-time origin start = earliest stream start (earliestStart over
// streamStart: start_pts × time_base, the same exact reading import uses;
// format.start_time only if no stream reports start_pts). A decoded
// frame's media time is pts × time_base − start, like data-media-start.
export async function sourceTiming(file) {
  const info = await ffprobeJson(file), picture = pictureStream(info);
  if (!picture) throw new Error('source has no video stream');
  const timeBase = rational(picture.stream.time_base);
  if (!timeBase) throw new Error(`ffprobe reported no usable video time_base (${picture.stream.time_base})`);
  const origin = earliestStart(info);
  return { start: origin ? origin.seconds : Number(info.format?.start_time) || 0, time_base: timeBase, video_index: picture.index };
}

// Memoised sourceTiming per file, so each source is probed once per check run.
export function sourceTimings() {
  const timings = new Map();
  return file => {
    if (!timings.has(file)) timings.set(file, sourceTiming(file));
    return timings.get(file);
  };
}

// Decode about [from, to) of a source file as grey frames (shorter edge
// analysis_short_edge) with their source times: -copyts keeps the decoded
// timestamps (showinfo's integer pts in the stream time base), converted with
// the ffprobe time_base and start (sourceTiming) to media-time seconds.
// -fps_mode passthrough writes every decoded frame exactly once (the rawvideo
// muxer would otherwise default to constant frame rate and duplicate/drop
// frames of variable-frame-rate sources), so frame k is the frame showinfo
// reported k-th.
export async function decodeWindow(file, from, to, p = CAPTION_CUT, timing, { signal } = {}) {
  timing ??= await sourceTiming(file);
  const e = p.analysis_short_edge, start = Math.max(0, from);
  const { stdout, stderr } = await run(mediaTool('ffmpeg'), ['-hide_banner', '-nostats', '-v', 'info', '-copyts', '-ss', String(start), '-t', String(Math.max(0.05, to - start)), '-i', file,
    '-map', `0:v:${timing.video_index ?? 0}`, '-an', '-sn', '-vf', `scale='if(lt(iw,ih),${e},-2)':'if(lt(iw,ih),-2,${e})',format=gray,showinfo`, '-fps_mode', 'passthrough', '-f', 'rawvideo', 'pipe:1'],
  { encoding: 'buffer', timeout: 120000, maxBuffer: 512 * 1024 * 1024, signal });
  return splitFrames(stdout, stderr.toString(), timing);
}

// Pair raw grey frames with showinfo frame lines. Times come from each line's
// integer pts × the ffprobe time_base − start, not from the printed pts_time
// (its decimals depend on the ffmpeg version). A frame line without an integer
// pts, a showinfo input time base that differs from the stream's, or a
// frame/time count mismatch means the times cannot be trusted, so it throws (the
// cut point becomes unknown) instead of guessing or truncating.
export function splitFrames(raw, log, { start = 0, time_base: timeBase } = {}) {
  if (!timeBase?.num || !timeBase?.den) throw new Error('splitFrames needs the stream time_base');
  const config = log.match(/config in time_base:\s*(\d+)\/(\d+)/);
  if (config && Number(config[1]) * timeBase.den !== Number(config[2]) * timeBase.num) {
    throw new Error(`showinfo time base ${config[1]}/${config[2]} differs from the stream time base ${timeBase.num}/${timeBase.den}; frame times are not trustworthy`);
  }
  const all = log.split('\n'), tagged = all.filter(line => line.includes('Parsed_showinfo'));
  const lines = (tagged.length ? tagged : all).filter(line => /\bn:\s*\d+\b/.test(line));
  if (!lines.length) {
    if (raw.length) throw new Error(`decoded ${raw.length} byte(s) but showinfo reported no frames; frame times are not trustworthy`);
    return { frames: [], times: [], width: 0, height: 0 };
  }
  const size = lines[0].match(/\bs:(\d+)x(\d+)/) ?? log.match(/\bs:(\d+)x(\d+)/);
  if (!size) throw new Error('showinfo reported no frame size (s:WxH); ffmpeg output format not understood');
  const width = Number(size[1]), height = Number(size[2]), N = width * height;
  const times = lines.map(line => {
    const pts = line.match(/\bpts:\s*(-?\d+)\b/);
    if (!pts) throw new Error(`showinfo frame line has no integer pts (${line.trim().slice(0, 80)}); ffmpeg output format not understood`);
    return Number(pts[1]) * timeBase.num / timeBase.den - start;
  });
  if (raw.length % N !== 0 || raw.length / N !== times.length) {
    throw new Error(`decoded ${raw.length / N} frame(s) but showinfo reported ${times.length} timestamp(s); frame times are not trustworthy`);
  }
  const frames = Array.from({ length: times.length }, (_, k) => raw.subarray(k * N, (k + 1) * N));
  return { frames, times, width, height };
}

export const frameStep = times => {
  const gaps = times.slice(1).map((t, i) => t - times[i]).filter(g => g > 1e-4).sort((a, b) => a - b);
  return gaps.length ? gaps[gaps.length >> 1] : 1 / 30;
};

// Which source frames a cut point shows. The renderer seeks the source to
// source_in + j × step for output frame j (step = speed / fps source seconds)
// and shows the frame whose time is ≤ that time. In-point: the first shown
// frame is the one with time ≤ at < time + frame. Out-point (exclusive): the
// last shown frame is the one at or before at − step. So a time a hair before a
// frame's start (e.g. 24.4333 for frame 733/30, or even 1e-7 s before it) still
// shows the previous frame. TIME_EPS only absorbs floating-point noise between
// equal times (exact frame times are pts × time_base; errors are ~1e-13 s), far
// below any time a document can express that the renderer would tell apart.
export const TIME_EPS = 1e-9;
export const shownAtIn = (t, at, frame) => t <= at + TIME_EPS && t > at - frame + TIME_EPS;
export const shownBeforeOut = (t, at, step) => t <= at - step + TIME_EPS;

// Judge one cut point from the caption events around it. In-point: a caption
// change on a later frame within the window means the previous line is still
// on screen at the cut → warn. Out-point: a change on a shown frame within the
// window before the cut means the next line flashes → warn. An edge ALIGNED on
// a caption change (on the in-point frame / on the first frame after the
// out-point: the line starts or ends with the cut) is not
// warned by a further change inside the window: it is the next line (in) or
// the switch to the line being spoken (out), and moving onto it would cut
// speech (suggest-cuts holds such points too; it also holds an edge on a 'shot'
// step, which this check still warns on, and its qa_precheck says so). It is recorded as short_line
// (the change nearest the edge and how long the edge line shows) for a look.
// The suggested time is the MIDPOINT of the first changed source frame (not
// its start, and not rounded): a time written at a frame boundary, or rounded
// to a few decimals, can fall just before that frame, so the renderer would
// still show the previous one. As an in-point it shows the changed frame first;
// as an out-point the last shown frame is the one before the change.
// `at` is the time the render plays (judged); `written` (default `at`) is the
// document's value, the base of suggested_shift_seconds, so written + shift is
// the suggested time.
export const frameMidOf = (event, frame) => event.frame_mid_seconds ?? event.source_seconds + frame / 2;
export function judgeCutPoint(edge, at, events, { frame, step = frame, window = CAPTION_CUT.window_seconds, written = at }) {
  const captions = events.filter(e => e.kind === 'caption'), t = e => e.source_seconds;
  const inside = edge === 'in' ? captions.filter(e => t(e) > at + TIME_EPS && t(e) <= at + window + TIME_EPS)
    : captions.filter(e => t(e) >= at - window - TIME_EPS && shownBeforeOut(t(e), at, step));
  // The caption step on the edge frame. A 'shot' step there (the band changed
  // with the whole frame) is not caption alignment: a new shot can carry the
  // old line on. It still warns, marked edge_on_shot_change so a person can
  // check whether the new line simply starts with the shot cut.
  const onEdge = e => edge === 'in' ? shownAtIn(t(e), at, frame) : !shownBeforeOut(t(e), at, step) && t(e) <= at - step + frame + TIME_EPS;
  const aligned = captions.find(onEdge);
  if (!inside.length) return { result: aligned ? 'aligned' : 'clear' };
  if (aligned) {
    const near = edge === 'in' ? inside[0] : inside.at(-1);
    return { result: 'aligned', short_line: { source_seconds: round6(t(near)), frame_mid_seconds: round6(frameMidOf(near, frame)),
      shown_seconds: round6(Math.abs(t(near) - t(aligned))) } };
  }
  const shot = events.some(e => e.kind === 'shot' && onEdge(e)) ? { edge_on_shot_change: true } : {};
  const pick = inside[0]; // in: earliest change; out: earliest change before the cut
  const suggested = round6(frameMidOf(pick, frame));
  return { result: 'warn', suggested_source_seconds: suggested, suggested_shift_seconds: round6(suggested - written), ...shot };
}

// Cut points of every video-track media item whose asset has picture, as the
// render plays them: the items of the compiled view (compiledView, the same view
// compilation uses; a view passed in is used as is), so point.item carries the
// compiled in-point and source_seconds the time the render plays (judged with
// the renderer's rule, shownAtIn / shownBeforeOut). When an in-point was
// corrected (truncated decimal; correctionOf(point.item) gives the written
// item), the point also records the document's values: document_source_seconds
// is the written in-point (in) or the written in-point + duration (out), and
// the in point names the source_frame it was corrected to.
export function cutPoints(doc) {
  const view = compiledView(doc), fps = view.canvas.fps, assets = new Map(view.assets.map(a => [a.id, a]));
  const video = new Set(view.tracks.filter(t => t.kind === 'video').map(t => t.id));
  return view.items.filter(i => i.kind === 'media' && video.has(i.track_id) && assets.get(i.asset_id)?.video !== false).flatMap(item => {
    const correction = correctionOf(item), written = correction?.written;
    const sourceOut = item.source_in_seconds + sourceSeconds(item, fps);
    return [{ item, edge: 'in', source_seconds: item.source_in_seconds, output_frame: item.start_frame,
      ...(written ? { document_source_seconds: written.source_in_seconds, source_frame: correction.frame } : {}) },
    { item, edge: 'out', source_seconds: sourceOut, output_frame: item.start_frame + item.frames,
      ...(written ? { document_source_seconds: written.source_in_seconds + sourceSeconds(written, fps) } : {}) }];
  });
}
// The document's value of a cut point (the written time an edit changes):
// document_source_seconds when the in-point was corrected, else source_seconds.
export const documentSeconds = point => point.document_source_seconds ?? point.source_seconds;
// Observation text after a reported entry's (document) source time: the time
// the render plays, when compilation corrected the in-point.
export const compiledNote = e => 'compiled_source_seconds' in e ? ` (compiled ${e.compiled_source_seconds.toFixed(6)} s)` : '';

// The burned-caption analysis for the shared cut-point pass (cut-checks.mjs):
// the source range it needs around a cut point, the per-point judgement on the
// decoded frames of that range, and the texts of its summary.
export function captionCutCheck(bandOption, p = CAPTION_CUT) {
  const band = captionBand(bandOption);
  // Pad the range so transitions at its ends still have steady_frames on both
  // sides (sized for sources down to 15 fps).
  const pad = (p.steady_frames + 1) / 15;
  const scope = n => `${n} source cut point(s), caption band ${round(band.top * 100, 1)}–${round(band.bottom * 100, 1)}% of the source frame height`;
  return {
    measured: { method: CAPTION_METHOD, band, window_seconds: p.window_seconds,
      thresholds: { analysis_short_edge: p.analysis_short_edge, steady_frames: p.steady_frames, steady_range: p.steady_range, step_delta: p.step_delta,
        line_height: p.line_height, line_share: p.line_share, glyph_level: p.glyph_level, glyph_share: p.glyph_share, shot_mad: p.shot_mad } },
    none: 'No video media items, so no source cut points to check for burned-in captions.',
    range: point => point.edge === 'in' ? [point.source_seconds - pad, point.source_seconds + p.window_seconds + pad]
      : [point.source_seconds - p.window_seconds - pad, point.source_seconds + pad],
    analyse(point, window, fps) {
      if (window.frames.length < 2 * p.steady_frames + 1) throw new Error('too few decoded frames');
      const events = stepEvents(window, band, p), frame = frameStep(window.times);
      const near = events.filter(e => Math.abs(e.source_seconds - point.source_seconds) <= p.window_seconds + frame);
      return { ...judgeCutPoint(point.edge, point.source_seconds, near, { frame, step: speedOf(point.item) / fps, window: p.window_seconds, written: documentSeconds(point) }),
        caption_changes: near.filter(e => e.kind === 'caption').map(e => ({ ...e, source_seconds: round6(e.source_seconds), frame_mid_seconds: round6(e.frame_mid_seconds) })),
        shot_changes: near.filter(e => e.kind === 'shot').map(e => round6(e.source_seconds)) };
    },
    summary: n => ({
      scope: scope(n), finding: 'burned-in caption change',
      describe: e => `${e.item_id} ${e.edge}-point at source ${e.source_seconds.toFixed(6)} s${compiledNote(e)} → ${e.suggested_source_seconds.toFixed(6)} s`,
      warned: (count, details, unchecked) => `${count} of ${scope(n)} show a burned-in caption change within ${p.window_seconds} s inside the cut (in-point: previous line still shown; out-point: next line flashes). Suggested source times (midpoint of the first changed source frame, so the cut cannot fall back onto the previous frame): ${details}.${unchecked} Frame-difference heuristic, not OCR.`,
      pass: `At none of ${scope(n)} does a burned-in caption change within ${p.window_seconds} s inside the cut show the previous line (in-point) or flash the next one (out-point). Frame-difference heuristic, not OCR; it cannot read caption text.`,
      note: entries => {
        const short = entries.filter(e => e.short_line);
        const onShot = entries.filter(e => e.result === 'warn' && e.edge_on_shot_change);
        return [short.length ? `${short.length} aligned cut point(s) have another caption change within ${p.window_seconds} s inside (not warned; the edge line shows only briefly, look at it): ${short.map(e => `${e.item_id} ${e.edge}-point at source ${e.source_seconds.toFixed(6)} s, change at ${e.short_line.source_seconds.toFixed(6)} s, edge line ${e.short_line.shown_seconds} s`).join('; ')}.` : '',
          onShot.length ? `${onShot.length} warned cut point(s) sit on a source shot change (${onShot.map(e => `${e.item_id} ${e.edge}`).join(', ')}): the new line may simply start with the shot cut; check by eye.` : ''].filter(Boolean).join(' ');
      },
    }),
  };
}
