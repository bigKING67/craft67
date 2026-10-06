import { speedOf } from './timeline.mjs';
import { CAPTION_CUT, TIME_EPS, compiledNote, documentSeconds, frameMidAt, frameStep, round6 } from './burned-captions.mjs';

const round = (value, digits = 3) => Math.round(value * 10 ** digits) / 10 ** digits;

// Fragments of adjacent source shots at cut points. An in-point chosen a little
// before the source's own shot change opens the item with the tail of the
// previous shot (e.g. in 22.68 s while the source cuts at 23.23 s: 0.55 s of the
// old shot); an in-point inside a flash transition opens with a few white
// frames; an out-point a little after a source change ends with the head of
// the next shot. This checks the SOURCE around every video item's in/out point.
//
// Shot change at decoded transition k (frame k − 1 → k), on full grey frames
// scaled like the burned-caption check: the mean absolute difference MAD(k) is
// ≥ shot_mad (the burned-caption check's full-frame shot threshold, 30 grey
// levels) AND either
//   - MAD(k) − MAD(k − 1) ≥ scene_jump (= render scene threshold × 100, i.e. 30
//     for the default 0.3; ffmpeg's scene score is min(MAD, ΔMAD)/100 on the
//     same 0–255 scale), a hard cut that stands out of the motion around it, or
//   - the mean grey level steps by ≥ shot_mad, a flash/fade frame.
// Fast camera motion has a high but steady MAD and a steady mean, so it is not a
// change; a white flash steps the mean on its way in and out.
//
// A change inside the item within window_seconds of an edge is a FRAGMENT when
// the shot piece shown at that edge belongs mostly to the neighbouring shot
// (more of that shot lies outside the item than inside it) or the piece is a
// flash: a shot shorter than flash_seconds. A short shot shown whole from its
// first frame (in) or to its last frame (out) is a deliberate edit, not a
// fragment, and a change exactly on the in-point frame / on the first frame
// after the out-point is aligned.
export const CUT_FRAGMENT = Object.freeze({
  window_seconds: 1.0, // look this far inside the item from each edge (source seconds)
  flash_seconds: 0.5, // a shot shorter than this next to a cut is a flash
  shot_mad: CAPTION_CUT.shot_mad, // 0–255 grey levels
  analysis_short_edge: CAPTION_CUT.analysis_short_edge,
});
export const FRAGMENT_METHOD = 'full-frame grey difference on the source around each cut point (hard cut: MAD ≥ shot_mad and MAD jump ≥ scene_jump; flash/fade: mean step ≥ shot_mad)';

// Per decoded frame: mean grey level and the mean absolute difference to the
// previous frame (mad[0] = NaN). Shared by shotChanges and lumaDips.
export function frameStats(frames) {
  const mad = [NaN], mean = [];
  for (let k = 0; k < frames.length; k++) {
    const cur = frames[k], prev = frames[k - 1];
    let sum = 0, diff = 0;
    for (let i = 0; i < cur.length; i++) { sum += cur[i]; if (prev) diff += Math.abs(cur[i] - prev[i]); }
    mean.push(sum / cur.length);
    if (k) mad.push(diff / cur.length);
  }
  return { mad, mean };
}

// Indices k ≥ 2 of decoded frames that start a new shot (see above).
export function shotChanges(frames, { sceneJump, shotMad = CUT_FRAGMENT.shot_mad }, { mad, mean } = frameStats(frames)) {
  const changes = [];
  for (let k = 2; k < frames.length; k++) {
    if (mad[k] >= shotMad && (mad[k] - mad[k - 1] >= sceneJump || Math.abs(mean[k] - mean[k - 1]) >= shotMad)) changes.push(k);
  }
  return changes;
}

// Dips (fade/dip to black and back): a short run of frames whose mean grey
// level falls well below the level on both sides and recovers. Each step of a
// gradual dip is too small for shotChanges (real footage: 119 → 97 → 73 → 49
// → 25 → 3 → 23 → … → 110 over 0.33 s, about 23 levels per frame), so a cut
// inside one opens with a fade up from black or ends fading out.
// From a frame m that is the darkest of its run, the run is walked outwards
// while the level keeps rising (by more than step_levels within one or two
// frames; frames near the bottom, ≤ flat_levels above it, pass even when flat,
// so a held black is one run) until it settles. It is a dip when the darkest
// level is ≤ ratio × ref and ≥ depth_levels below ref (ref = the lower of the
// two settled levels) and the darkened frames span ≤ max_seconds. A run that
// reaches the window edge before settling is not judged (its level is unknown),
// unless that edge is the file's own first / last frame (fileStart / fileEnd):
// an opening fade-up from black or a closing fade-out is a dip open on that
// side, judged against the one settled side. With one side only, a darker
// last (or first) shot is not told apart from a fade by recovery, so the
// darkest level must be near black: ≤ open_ratio × ref (a hard cut from red to
// blue is ~50 %; a fade to black is a few %).
// Calibrated on a 157.6 s talking-head/product film (see README): the one real
// dip is ≥ 100 levels deep; nothing else comes within 20 levels / 70 %.
export const DIP = Object.freeze({ max_seconds: 1.5, ratio: 0.5, open_ratio: 0.25, depth_levels: 40, step_levels: 2, flat_levels: 20 });
export const DIP_METHOD = 'per-frame mean grey level (frames scaled to short edge 360): a run darker than the settled level on both sides by ≥ depth_levels and to ≤ ratio × that level, recovering within max_seconds; at the first / last frame of the file a run open on that side, to ≤ open_ratio × the other side';

// Dips of a mean-level series: [{start, min, end, end_seconds, ref, min_luma}]
// as indices, start = first darkened frame, end = first recovered frame
// (exclusive; mean.length for a dip open at the file end, whose end_seconds is
// the end of the last frame).
export function lumaDips(mean, times, p = DIP, { fileStart = false, fileEnd = false } = {}) {
  const dips = [], n = mean.length, last = n - 1;
  const rises = (k, dir, bottom) => {
    const a = mean[k + dir], b = mean[k + 2 * dir];
    return a !== undefined && a >= mean[k] - p.step_levels && (a > mean[k] + p.step_levels || (b !== undefined && b > mean[k] + p.step_levels) || mean[k] <= bottom + p.flat_levels);
  };
  for (let m = fileStart ? 0 : 1; m < (fileEnd ? n : n - 1); m++) {
    if (!(!(m > 0) || mean[m] <= mean[m - 1]) || !(m === last || mean[m] < mean[m + 1]) || (dips.length && m < dips.at(-1).end)) continue;
    let s = m, e = m;
    while (rises(s, -1, mean[m]) && times[m] - times[s] <= p.max_seconds) s--;
    while (rises(e, 1, mean[m]) && times[e] - times[m] <= p.max_seconds) e++;
    if (rises(s, -1, mean[m]) || rises(e, 1, mean[m])) continue; // still moving after max_seconds
    // A walk that ends on the window's first / last frame: settled there unless
    // that frame is still dark (nearer the bottom than the other side); then the
    // run is open, allowed only at the file's own edge.
    const dark = (k, other) => mean[k] - mean[m] < (mean[other] - mean[m]) / 2;
    if ((s === 0 && !fileStart) || (e === last && !fileEnd)) continue;
    const openStart = s === 0 && dark(0, e), openEnd = e === last && dark(last, s);
    if (openStart && openEnd) continue; // dark from the first to the last frame: no settled level
    const start = openStart ? 0 : s + 1, end = openEnd ? n : e;
    let darkest = m;
    for (let k = start; k < end; k++) if (mean[k] < mean[darkest]) darkest = k;
    const ref = openStart ? mean[e] : openEnd ? mean[s] : Math.min(mean[s], mean[e]), low = mean[darkest];
    const endSeconds = end < n ? times[end] : times[last] + frameStep(times);
    if (darkest !== m || low > (openStart || openEnd ? p.open_ratio : p.ratio) * ref || ref - low < p.depth_levels || endSeconds - times[start] > p.max_seconds + 1e-9) continue;
    dips.push({ start, min: m, end, end_seconds: endSeconds, ref: round(ref, 1), min_luma: round(low, 1) });
  }
  return dips;
}

// A cut point inside a dip: in-point when its first shown frame k0 is a
// darkened frame (the item opens fading up), out-point when its last shown
// frame kL is (it ends fading out). output_frames: output frames of the item
// that show darkened frames (the renderer's rule, as for fragments).
// suggested_source_seconds: midpoint of the first recovered frame (in) / of
// the first darkened frame (out: the last shown frame is the one before it).
export function judgeDip(edge, { times, dips, at, step, frame, first, itemFrames }) {
  const outputBefore = t => Math.min(itemFrames, Math.max(0, Math.ceil((t - first) / step - TIME_EPS)));
  const k = lastAtOrBefore(times, edge === 'in' ? at : at - step);
  const dip = k < 0 ? undefined : dips.find(d => d.start <= k && k < d.end);
  if (!dip) return null;
  const output = edge === 'in' ? outputBefore(dip.end_seconds) : itemFrames - outputBefore(times[dip.start]);
  // No usable suggestion: an in-point in a dip open at the file end has no
  // recovered frame; an out-point in a dip that starts at or before the item's
  // first shown frame (an opening fade-up) would end before the item starts.
  const target = edge === 'in' ? dip.end : dip.start;
  const usable = edge === 'in' ? target < times.length : times[target] > first + TIME_EPS;
  return { start_seconds: round6(times[dip.start]), min_seconds: round6(times[dip.min]), end_seconds: round6(dip.end_seconds), ref_luma: dip.ref, min_luma: dip.min_luma, output_frames: output,
    suggested_source_seconds: usable ? round6(frameMidAt(times, target, frame)) : null };
}

const lastAtOrBefore = (times, t) => { let k = -1; while (k + 1 < times.length && times[k + 1] <= t + TIME_EPS) k++; return k; };

// Judge one cut point. times: decoded source frame times; changes: sorted
// shot-change indices; at: source in/out seconds; step: source seconds per
// output frame; frame: source frame duration; first/last: the item's first and
// last shown source times; fileStart/fileEnd: the window reached the file's
// first/last frame (the shot really starts/ends there); itemFrames: the item's
// output frames.
//
// A shot piece at an edge warns only when part of that shot lies OUTSIDE the
// item (in: shown before the in-point; out: after the out-point) and either it
// is mostly outside or the shot is a flash. A shot shown from its own first
// frame (outside = 0) or to its own last frame (after = 0) is aligned with the
// cut even when it is short: it is shown whole on that side, an edit choice.
//
// fragment_frames counts OUTPUT frames of the render that show the fragment
// (through speed and source vs canvas frame rate: output frame j shows the
// source frame at or before first + j × step); source_frames counts the source
// frames of the fragment. change_mid_seconds is the midpoint of the changed frame.
// `at` is the time the render plays (judged); `written` (default `at`) is the
// document's in-point, the base of suggested_shift_seconds, so written + shift
// is suggested_source_in_seconds.
export function judgeFragment(edge, { times, changes, at, written = at, step, frame, first, last, fileStart = false, fileEnd = false, itemFrames }, p = CUT_FRAGMENT) {
  const W = p.window_seconds, F = p.flash_seconds;
  // Output frames whose source time is before t (they show frames before t).
  const outputBefore = t => Math.min(itemFrames, Math.max(0, Math.ceil((t - first) / step - TIME_EPS)));
  const change = k => ({ change_seconds: round6(times[k]), change_mid_seconds: round6(frameMidAt(times, k, frame)) });
  if (edge === 'in') {
    const k0 = lastAtOrBefore(times, at);
    if (k0 < 0) throw new Error('in-point frame not decoded');
    const before = changes.filter(k => k <= k0), s = before.length ? before.at(-1) : fileStart ? 0 : -1;
    const e = changes.find(k => k > k0 && times[k] <= Math.min(at + W, last) + TIME_EPS);
    if (e === undefined) return { result: s === k0 ? 'aligned' : 'clear' };
    const outside = s < 0 ? Infinity : times[k0] - times[s], shown = times[e] - times[k0];
    const flash = outside + shown < F - TIME_EPS;
    if (!(outside > TIME_EPS && (flash || outside > shown))) return { result: s === k0 ? 'aligned' : 'clear', ...change(e) };
    let c = e; // skip further short shots (a flash's way out) after the first change
    for (let n = changes.find(k => k > c); n !== undefined && times[n] - times[c] < F - TIME_EPS && times[n] <= last + TIME_EPS; n = changes.find(k => k > c)) c = n;
    const suggested = round6(frameMidAt(times, c, frame));
    return { result: 'warn', kind: flash || c !== e ? 'flash' : 'fragment', fragment_frames: outputBefore(times[c]), source_frames: c - k0, ...change(e),
      suggested_source_in_seconds: suggested, suggested_shift_seconds: round6(suggested - written) };
  }
  const kL = lastAtOrBefore(times, at - step);
  if (kL < 0) throw new Error('out-point frame not decoded');
  const e = changes.find(k => k > kL);
  const inside = changes.filter(k => k <= kL && times[k] >= at - W - TIME_EPS && times[k] > first + TIME_EPS);
  if (!inside.length) return { result: e === kL + 1 ? 'aligned' : 'clear' };
  const s = inside.at(-1), after0 = kL + 1 < times.length ? times[kL + 1] : times[kL] + frame;
  const after = (e !== undefined ? times[e] : fileEnd ? times.at(-1) + frame : Infinity) - after0, shown = after0 - times[s];
  const flash = shown + after < F - TIME_EPS;
  if (!(after > TIME_EPS && (flash || after > shown))) return { result: e === kL + 1 ? 'aligned' : 'clear', ...change(s) };
  let c = s; // skip further short shots before the last change (a flash's way in)
  for (let q = inside.findLast(k => k < c); q !== undefined && times[c] - times[q] < F - TIME_EPS; q = inside.findLast(k => k < c)) c = q;
  // Keep output frames whose source time is before frame c: the last shown frame is c − 1.
  const before = outputBefore(times[c]), keep = Math.max(1, before);
  const suggested = round6(frameMidAt(times, c, frame));
  return { result: 'warn', kind: flash || c !== s ? 'flash' : 'fragment', fragment_frames: itemFrames - before, source_frames: kL + 1 - c, ...change(s),
    suggested_source_out_seconds: suggested, suggested_frames: keep, drop_output_frames: itemFrames - keep };
}

// The fragment analysis for the shared cut-point pass (cut-checks.mjs): the
// source range it needs around a cut point, the per-point judgement on the
// decoded frames of that range, and the texts of its summary.
// Dips to black (lumaDips) are judged on the same frames: a cut point whose
// edge frame is a darkened frame of a source dip warns (kind 'dip' when there
// is no fragment), with the output frames and seconds that fade.
export function fragmentCutCheck(sceneThreshold = 0.3, p = CUT_FRAGMENT, d = DIP) {
  const sceneJump = round6(sceneThreshold * 100), pad = 0.2, W = p.window_seconds, F = p.flash_seconds, D = Math.max(W, d.max_seconds);
  const what = e => e.kind === 'flash' ? 'a flash / very short shot (< 0.5 s)' : e.edge === 'in' ? 'the previous source shot' : 'the next source shot';
  const dipText = e => `${e.item_id} ${e.edge}-point at output ${e.output_seconds.toFixed(3)} s ${e.edge === 'in' ? 'opens fading up from' : 'ends fading out into'} a source dip to black for ${e.dip.output_frames} output frame(s) (${e.dip.output_duration_seconds} s): source ${e.source_seconds.toFixed(6)} s${compiledNote(e)} lies in the dip ${e.dip.start_seconds.toFixed(6)}–${e.dip.end_seconds.toFixed(6)} s (mean level ${e.dip.ref_luma} → ${e.dip.min_luma}); ${e.dip.suggested_source_seconds === null ? (e.edge === 'in' ? 'the dip runs to the end of the file (no recovered frame to start at)' : 'the dip starts at or before the item\'s first shown frame (ending before it leaves nothing)') : `${e.edge === 'in' ? 'start at' : 'end at'} ${e.dip.suggested_source_seconds.toFixed(6)} s (midpoint of the ${e.edge === 'in' ? 'first recovered' : 'first darkened'} frame) to avoid it, if the speech allows`}`;
  return {
    measured: { method: `${FRAGMENT_METHOD}; dips: ${DIP_METHOD}`, window_seconds: W, flash_seconds: F,
      thresholds: { analysis_short_edge: p.analysis_short_edge, shot_mad: p.shot_mad, scene_jump: sceneJump, scene_threshold: sceneThreshold, dip: { ...d } } },
    none: 'No video media items, so no source cut points to check for shot fragments.',
    // The outer side reaches a whole dip (max_seconds) so its settled level is decoded.
    range: point => point.edge === 'in' ? [point.source_seconds - D - pad, point.source_seconds + W + F + pad]
      : [point.source_seconds - W - F - pad, point.source_seconds + D + pad],
    analyse(point, window, fps, [from, to]) {
      if (window.frames.length < 4) throw new Error('too few decoded frames');
      const { item } = point, step = speedOf(item) / fps, first = item.source_in_seconds, last = first + (item.frames - 1) * step;
      const frame = frameStep(window.times), stats = frameStats(window.frames), changes = shotChanges(window.frames, { sceneJump, shotMad: p.shot_mad }, stats);
      // The window reached the file's first / last frame (one rule for both judgements).
      const edges = { fileStart: from <= 0, fileEnd: window.times.at(-1) + 1.5 * frame < to };
      const judged = judgeFragment(point.edge, { times: window.times, changes, at: point.source_seconds, written: documentSeconds(point), step, frame, first, last, itemFrames: item.frames,
        ...edges }, p);
      const near = changes.map(k => window.times[k]).filter(t => Math.abs(t - point.source_seconds) <= W + F);
      const dip = judgeDip(point.edge, { times: window.times, dips: lumaDips(stats.mean, window.times, d, edges), at: point.source_seconds, step, frame, first, itemFrames: item.frames });
      const dipped = dip ? { dip: { ...dip, output_duration_seconds: round6(dip.output_frames / fps) }, ...(judged.result === 'warn' ? {} : { result: 'warn', kind: 'dip' }) } : {};
      return { ...judged, ...dipped, shot_changes: near.map(round6) };
    },
    summary: n => ({
      scope: `${n} source cut point(s)`, finding: 'adjacent-shot fragment or dip to black',
      describe: e => e.kind === 'dip' ? dipText(e) : (e.edge === 'in'
        ? `${e.item_id} in-point opens with ${e.fragment_frames} output frame(s) (${e.source_frames} source frame(s)) of ${what(e)}: source in ${e.source_seconds.toFixed(6)} s${compiledNote(e)} → ${e.suggested_source_in_seconds.toFixed(6)} s (midpoint of the first frame after the change)`
        : `${e.item_id} out-point ends with ${e.fragment_frames} output frame(s) (${e.source_frames} source frame(s)) of ${what(e)}: end before the source change (changed frame midpoint ${e.change_mid_seconds.toFixed(6)} s) → ${e.suggested_frames} output frame(s) (drop ${e.drop_output_frames}; source out ${e.suggested_source_out_seconds.toFixed(6)} s, midpoint of the changed frame)`)
        + (e.dip && e.kind !== 'dip' ? `; also ${dipText(e)}` : ''),
      warned: (count, details, unchecked) => `${count} of ${n} source cut point(s) show a fragment of an adjacent source shot within ${W} s inside the cut or land inside a source dip to black: ${details}.${unchecked}`,
      pass: `No adjacent-shot fragment or flash within ${W} s inside, and no edge inside a source dip to black, at any of ${n} source cut point(s).`,
    }),
  };
}
