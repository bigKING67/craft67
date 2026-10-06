// Cut-point suggestions from a footage analysis (analyze.mjs) and a list of
// beats. A beat is either a rough source time range {id, from, to} or a line of
// speech {id, text}. For every beat the suggester:
//   1. takes the complete ASR phrases the beat covers as its semantic bounds;
//   2. puts the in-point into the low-energy valley nearest before the first
//      phrase and the out-point into the one nearest after the last phrase, at
//      the valley's deepest point but at most lead_in / lead_out seconds from
//      the speech;
//   3. moves the in-point past a burned-in caption change within 0.5 s after it
//      (the previous line would still show) and past any shot change within
//      1 s after it (the opening would be a fragment or a too-short shot); moves
//      the out-point before a caption change within 0.5 s before it and before
//      a shot piece at the end that belongs to the next shot; repeats until no
//      rule moves it (a point on a caption change frame is aligned and is not
//      moved by a further change: it is reported); an edge inside a dip to
//      black (analysis dips) moves out of it when that cuts no more than
//      speech_tolerance of speech, else it stays and is reported;
//   4. writes every point as a frame midpoint (n + 0.5) / fps;
//   5. reports a CONFLICT instead of choosing silently when a move would cut
//      more than speech_tolerance seconds of speech (e.g. speech starts before
//      the source's own shot change) and lists the options: keep the speech and
//      accept the fragment / old caption, cut at the change (into the next
//      valley when there is one), or drop the edge phrase.
// The output is advice for a person who listens before approving: ASR times
// are approximate and the caption detector is a heuristic, not OCR.
import * as fs from 'node:fs/promises';
import { ANALYSIS_SCHEMA, TARGET_LUFS, integratedLoudness, truePeak, volumeFor } from './analyze.mjs';
import { judgeCutPoint, round6 } from './burned-captions.mjs';
import { judgeFragment } from './cut-fragments.mjs';

export const SUGGEST_SCHEMA = 'creative-craft.cut-suggestions.v1';
export const RULES = Object.freeze({
  phrase_cover: 0.5, // a range beat covers a phrase when ≥ 50 % of the phrase lies inside it
  in_before: 0.4, in_after: 0.15, // in-point valley search around the phrase start
  out_before: 0.15, out_after: 0.4, // out-point valley search around the phrase end
  neighbour_overlap: 0.15, // a search reaches at most this far into the neighbouring phrase
  valley_db: 6, // quiet: a 20 ms window ≤ search floor + 6 dB
  deep_db: 3, // a valley qualifies when its lowest window is ≤ floor + 3 dB
  merge_gap: 0.08, // quiet runs closer than this (a click, a breath) are one valley
  lead_in: 0.2, lead_out: 0.2, // a cut sits at the valley's deepest point, but at most this far from the speech
  clean_db: 8, refine_seconds: 0.3, // cut_at_change lands in a valley ≥ 8 dB below its surroundings within 0.3 s
  caption_window: 0.5, // = CAPTION_CUT.window_seconds of the QA check
  shot_window: 1.0, // no shot change within 1 s after an in-point
  flash_seconds: 0.5, // shot changes closer than this chain into one flash
  speech_tolerance: 0.25, // a move may cut at most this much speech before it is a conflict
  min_lead_in: 0.05, // a moved in-point closer than this before the speech onset is reported (attack may clip)
  text_min_score: 0.6, // text beats: minimum character LCS similarity
  text_ambiguous: 0.02, // another place within this score of the best is an ambiguity
  max_moves: 8,
});
const round = (value, digits = 3) => Math.round(value * 10 ** digits) / 10 ** digits;

// ---------------------------------------------------------------- frame grid
export function grid(analysis) {
  const m = /^(\d+)\/(\d+)$/.exec(analysis.media?.frame_rate ?? '');
  if (!m) throw new Error('suggest-cuts needs a constant frame rate (analysis media.frame_rate); this source has none');
  const fps = Number(m[1]) / Number(m[2]);
  return { fps, count: analysis.media.frame_count ?? Infinity, start: n => n / fps, mid: n => round6((n + 0.5) / fps),
    // last frame whose midpoint is ≤ t / first frame whose midpoint is ≥ t
    midAtOrBefore: t => Math.floor(t * fps - 0.5 + 1e-6), midAtOrAfter: t => Math.ceil(t * fps - 0.5 - 1e-6) };
}

// ---------------------------------------------------------------- energy
// Quiet runs inside [from, to] of the 20 ms envelope: windows ≤ floor +
// valley_db (floor = lowest window of the range), merged across gaps shorter
// than merge_gap. Each run has its lowest level (min_db) and deep_seconds. depth_db = level of the range's loud part (90th
// percentile window, the speech around the valley) − floor.
export function lowRuns(energy, from, to, p = RULES) {
  const w = energy.window_seconds, base = energy.start_seconds;
  const i0 = Math.max(0, Math.ceil((from - base) / w - 1e-6)), i1 = Math.min(energy.values_db.length - 1, Math.floor((to - base) / w - 1e-6));
  if (i1 < i0) return { runs: [], floor_db: null, depth_db: null };
  const values = energy.values_db.slice(i0, i1 + 1), floor = Math.min(...values), limit = floor + p.valley_db;
  const sorted = [...values].sort((a, b) => a - b), loud = sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * 0.9))];
  const runs = [];
  values.forEach((v, j) => {
    if (v > limit) return;
    const t = round6(base + (i0 + j) * w), last = runs.at(-1);
    if (last && t - last.to <= p.merge_gap + 1e-6) {
      last.to = round6(t + w);
      last.min_db = Math.min(last.min_db, v);
      last.windows.push([t, v]);
    } else runs.push({ from: t, to: round6(t + w), min_db: v, windows: [[t, v]] });
  });
  // deep_seconds: centre of the run's lowest part (windows within 1 dB of its
  // minimum, first to last), so a flat valley is cut in its middle, not at an edge.
  for (const run of runs) {
    const low = run.windows.filter(([, v]) => v <= run.min_db + 1);
    run.deep_seconds = round6((low[0][0] + low.at(-1)[0] + w) / 2);
    delete run.windows;
  }
  return { runs, floor_db: floor, depth_db: round(loud - floor, 1) };
}
const distance = (run, t) => t < run.from ? run.from - t : t > run.to ? t - run.to : 0;
// The qualifying (deep) run nearest to `anchor`, with the search facts; null when the range is empty.
export function valleyNear(energy, from, to, anchor, p = RULES) {
  const { runs, floor_db, depth_db } = lowRuns(energy, from, to, p);
  const deep = runs.filter(r => r.min_db <= floor_db + p.deep_db);
  const run = deep.reduce((best, r) => !best || distance(r, anchor) < distance(best, anchor) - 1e-9 ? r : best, null);
  return run ? { ...run, floor_db, depth_db, search: [round6(from), round6(to)] } : null;
}

// ---------------------------------------------------------------- beats → phrases
const normalise = text => String(text).toLowerCase().replace(/[\s\p{P}\p{S}]/gu, '');
export function lcs(a, b) {
  let prev = new Array(b.length + 1).fill(0);
  for (let i = 1; i <= a.length; i++) {
    const cur = [0];
    for (let j = 1; j <= b.length; j++) cur[j] = a[i - 1] === b[j - 1] ? prev[j - 1] + 1 : Math.max(prev[j], cur[j - 1]);
    prev = cur;
  }
  return prev[b.length];
}
export const similarity = (a, b) => (a.length + b.length) ? 2 * lcs(a, b) / (a.length + b.length) : 0;

// Phrases of a beat: {first, last} phrase indices (null, null: none), and for
// text beats how they were matched.
export function beatPhrases(beat, phrases, p = RULES) {
  if (typeof beat.text === 'string') {
    const target = normalise(beat.text);
    if (!target) throw new Error(`Beat ${beat.id}: empty text`);
    const runs = [];
    for (let i = 0; i < phrases.length; i++) {
      let text = '';
      for (let j = i; j < phrases.length && text.length <= target.length * 1.5; j++) {
        text += normalise(phrases[j].text);
        runs.push({ first: i, last: j, score: round(similarity(target, text), 3) });
      }
    }
    runs.sort((x, y) => y.score - x.score || x.first - y.first || x.last - y.last);
    const best = runs[0];
    if (!best || best.score < p.text_min_score) return { error: `no phrase run matches the text (best similarity ${best?.score ?? 0} < ${p.text_min_score})` };
    const rivals = runs.filter(r => best.score - r.score <= p.text_ambiguous && (r.last < best.first || r.first > best.last));
    return { first: best.first, last: best.last, match: {
      method: `character LCS similarity 2·LCS/(|a|+|b|) of the beat text and each run of consecutive phrases, both without whitespace, punctuation and symbols, lower-cased; the best run wins (earliest and shortest on ties), minimum ${p.text_min_score}`,
      score: best.score, matched_text: phrases.slice(best.first, best.last + 1).map(ph => ph.text).join(''),
      ...(rivals.length ? { ambiguous_with: rivals.slice(0, 3).map(r => ({ first_phrase: r.first, last_phrase: r.last, score: r.score, start: phrases[r.first].start, end: phrases[r.last].end })) } : {}) } };
  }
  const { from, to } = beat;
  if (!(Number.isFinite(from) && Number.isFinite(to) && to > from && from >= 0)) throw new Error(`Beat ${beat.id} needs 0 ≤ from < to or a text`);
  const covered = phrases.flatMap((ph, i) => ph.end > ph.start && Math.min(ph.end, to) - Math.max(ph.start, from) >= p.phrase_cover * (ph.end - ph.start) - 1e-9 ? [i] : []);
  return covered.length ? { first: covered[0], last: covered.at(-1) } : { first: null, last: null };
}

// ---------------------------------------------------------------- edges
export function context(analysis, p = RULES) {
  const g = grid(analysis);
  const shotStarts = analysis.shots.list.map(s => s.start_frame).filter(k => k > 0).sort((a, b) => a - b);
  const captionFrames = [...new Set(analysis.captions.changes.map(c => c.frame))].sort((a, b) => a - b);
  // Kind per frame ('caption' wins when both): the QA judges a 'shot' step on
  // the edge frame differently, so the precheck must pass it through.
  const captionKind = new Map();
  for (const c of analysis.captions.changes) if (captionKind.get(c.frame) !== 'caption') captionKind.set(c.frame, c.kind === 'shot' ? 'shot' : 'caption');
  // Analyses made before dip detection have no dips: no dip rule.
  const dips = (analysis.dips?.list ?? []).filter(d => Number.isInteger(d.start_frame) && Number.isInteger(d.end_frame));
  return { analysis, p, g, shotStarts, shotStartSet: new Set(shotStarts), captionFrames, captionSet: new Set(captionFrames), captionKind, dips,
    phrases: analysis.speech.phrases, energy: analysis.energy };
}

// The dip an edge frame lands in: in-point n is a darkened frame (opens
// fading up), out-point n − 1 (the last shown frame) is one (ends fading out).
const dipAt = (ctx, edge, n) => ctx.dips.find(d => edge === 'in' ? d.start_frame <= n && n < d.end_frame : d.start_frame < n && n <= d.end_frame);
const dipText = d => `dip to black ${d.start_seconds}–${d.end_seconds} s (frames ${d.start_frame}–${d.end_frame - 1}, mean level ${d.ref_luma} → ${d.min_luma})`;
// Evidence of an edge left inside a dip, with the reason it stays: the draft
// uses a conflict option (`uses`), the dip starts at or before the in-point
// (out edge), moving out cuts more than speech_tolerance (`onset` / `end` as
// in settleIn / settleOut), or the rules ran out of moves (max_moves).
function dipNote(ctx, edge, n, notes, { uses, onset, end, inFrame }) {
  const { g, p } = ctx, d = dipAt(ctx, edge, n);
  if (!d) return null;
  const target = edge === 'in' ? d.end_frame : d.start_frame;
  const cut = edge === 'in' ? Math.max(0, g.mid(target) - Math.max(onset, g.mid(n))) : Math.max(0, Math.min(end, g.mid(n)) - g.mid(target));
  const [reason, text] = uses ? ['conflict_option', `the draft uses the conflict option ${uses}, which lands here`]
    : edge === 'in' && target >= g.count ? ['no_recovered_frame', 'the dip runs to the end of the file: there is no recovered frame to start from']
    : edge === 'out' && target <= inFrame ? ['dip_starts_before_in', `the dip starts at or before the in-point (frame ${inFrame}), so ending before it leaves nothing`]
      : cut > p.speech_tolerance + 1e-9 ? ['speech_tolerance', `${edge === 'in' ? 'starting' : 'ending'} at frame ${target} would cut ${round(cut, 3)} s of speech (more than ${p.speech_tolerance} s)`]
        : ['max_moves', `the cut rules stopped after ${p.max_moves} moves`];
  notes.push(`${edge}-point frame ${n} is inside a ${dipText(d)}: the cut ${edge === 'in' ? 'opens fading up from black' : 'ends fading out'}; it is kept because ${text}; check it`);
  return { start_frame: d.start_frame, min_frame: d.min_frame, end_frame: d.end_frame, start_seconds: d.start_seconds, end_seconds: d.end_seconds, ref_luma: d.ref_luma, min_luma: d.min_luma, kept_because: reason };
}

// An in-point on a caption change frame with another change within
// caption_window after it: the opening line shows only briefly (it may be the
// rest of the previous line). Reported, not moved; null otherwise.
function openingCaption(ctx, n) {
  const { g, p } = ctx;
  if (!ctx.captionSet.has(n)) return null;
  const next = ctx.captionFrames.find(k => k > n && g.start(k) <= g.mid(n) + p.caption_window + 1e-9);
  return next === undefined ? null : { in_frame: n, next_change_frame: next, next_change_seconds: round6(g.start(next)), shown_seconds: round((next - n) / g.fps, 3) };
}

// The mirror for an out-point on a caption change frame (the first frame not
// shown starts the next line: aligned) with another change within
// caption_window before it: the closing line shows only briefly. Reported, not
// moved; null otherwise.
function closingCaption(ctx, n, minFrame) {
  const { g, p } = ctx;
  if (!ctx.captionSet.has(n)) return null;
  const previous = ctx.captionFrames.findLast(k => k < n && k > minFrame && g.start(k) >= g.mid(n) - p.caption_window - 1e-9);
  return previous === undefined ? null : { out_frame: n, previous_change_frame: previous, previous_change_seconds: round6(g.start(previous)), shown_seconds: round((n - previous) / g.fps, 3) };
}

// Caption and shot rules on an in-point frame, repeated until nothing moves
// it. speech_cut_seconds of a move: speech between the valley end (`onset`)
// and the new in-point that the move removes.
function settleIn(ctx, n, onset) {
  const { g, p } = ctx, moves = [];
  const move = (rule, to, reason) => { moves.push({ rule, from_frame: n, to_frame: to, to_seconds: g.mid(to), reason, speech_cut_seconds: round(Math.max(0, g.mid(to) - Math.max(onset, g.mid(n))), 3) }); n = to; };
  for (let step = 0; step < p.max_moves; step++) {
    const at = g.mid(n);
    // A change on the in-point frame itself starts the new line with the cut
    // (aligned, as the QA check judges it). A further change within
    // caption_window after it does not move the in-point (a frame-difference
    // event cannot tell a new line from a partial or animated change); it is
    // reported by openingCaption instead and the render QA judges it again.
    const caption = ctx.captionSet.has(n) ? undefined : ctx.captionFrames.find(k => k > n && g.start(k) <= at + p.caption_window + 1e-9);
    if (caption !== undefined) { move('caption', caption, `burned caption changes at frame ${caption} (${round6(g.start(caption))} s), ${round(g.start(caption) - at, 3)} s after the in-point: the previous line would show`); continue; }
    // Inside a dip to black: start at its first recovered frame, unless that
    // cuts more than speech_tolerance (then kept and reported, never a conflict:
    // a short fade-up is a look, not a lost word).
    const dip = dipAt(ctx, 'in', n);
    // A dip open at the file end has no recovered frame (end_frame = frame count).
    if (dip && dip.end_frame < g.count && Math.max(0, g.mid(dip.end_frame) - Math.max(onset, at)) <= p.speech_tolerance + 1e-9) { move('dip', dip.end_frame, `in-point is inside a ${dipText(dip)}: the opening would fade up from black`); continue; }
    let shot = ctx.shotStarts.find(k => k > n && g.start(k) <= at + p.shot_window + 1e-9);
    if (shot === undefined) break;
    const first = shot;
    for (let next = ctx.shotStarts.find(k => k > shot); next !== undefined && (next - shot) / g.fps < p.flash_seconds; next = ctx.shotStarts.find(k => k > shot)) shot = next;
    move('shot', shot, `source shot changes at frame ${first} (${round6(g.start(first))} s)${shot !== first ? `, flash/short shots until frame ${shot}` : ''}, ${round(g.start(first) - at, 3)} s after the in-point: the opening would ${ctx.shotStartSet.has(n) ? 'be a shot shorter than' : 'show a fragment of the previous shot for less than'} ${p.shot_window} s`);
  }
  return { frame: n, moves };
}

// Caption and shot rules on an out-point (frame n = the first frame NOT
// shown). A shot piece [k, n) at the end is a fragment of the next shot when
// that shot starts after the speech has ended (`end`), when more of it lies
// after the out-point than before, or when it is a flash.
function settleOut(ctx, n, end, minFrame) {
  const { g, p } = ctx, moves = [];
  const move = (rule, to, reason) => { moves.push({ rule, from_frame: n, to_frame: to, to_seconds: g.mid(to), reason, speech_cut_seconds: round(Math.max(0, Math.min(end, g.mid(n)) - g.mid(to)), 3) }); n = to; };
  for (let step = 0; step < p.max_moves; step++) {
    const at = g.mid(n);
    // A change on the out frame itself (the first frame not shown) ends the
    // line with the cut (aligned, as the QA check judges it). An earlier change
    // within caption_window does not move it again: that is the switch to the
    // line being spoken, and moving onto it cuts the end of that line's speech
    // (the cascade 60.15 → 60.1 → 59.63 s on real footage). closingCaption
    // reports it instead, like openingCaption on the in-point.
    const caption = ctx.captionSet.has(n) ? undefined : ctx.captionFrames.find(k => k < n && k > minFrame && g.start(k) >= at - p.caption_window - 1e-9);
    if (caption !== undefined) { move('caption', caption, `burned caption changes at frame ${caption} (${round6(g.start(caption))} s), ${round(at - g.start(caption), 3)} s before the out-point: the next line would flash`); continue; }
    const dip = dipAt(ctx, 'out', n); // as for the in-point: end before the dip when that cuts ≤ speech_tolerance
    if (dip && dip.start_frame > minFrame && Math.max(0, Math.min(end, at) - g.mid(dip.start_frame)) <= p.speech_tolerance + 1e-9) { move('dip', dip.start_frame, `out-point is inside a ${dipText(dip)}: the ending would fade out`); continue; }
    if (ctx.shotStartSet.has(n)) break;
    let shot = ctx.shotStarts.findLast(k => k < n && k > minFrame && g.start(k) >= at - p.shot_window - 1e-9);
    if (shot === undefined) break;
    const next = ctx.shotStarts.find(k => k > n) ?? g.count, after = next - n, shown = n - shot;
    if (!(g.start(shot) >= end - 1e-9 || after > shown || (after + shown) / g.fps < p.flash_seconds)) break;
    const last = shot;
    for (let prev = ctx.shotStarts.findLast(k => k < shot && k > minFrame); prev !== undefined && (shot - prev) / g.fps < p.flash_seconds; prev = ctx.shotStarts.findLast(k => k < shot && k > minFrame)) shot = prev;
    move('shot', shot, `source shot changes at frame ${last} (${round6(g.start(last))} s)${shot !== last ? ` after flash/short shots from frame ${shot}` : ''}, ${round(at - g.start(last), 3)} s before the out-point: the ending would be a fragment of the next shot`);
  }
  return { frame: n, moves };
}

// Where in a valley a cut goes: its deepest part, but at most lead_in before
// the speech that follows (in) / lead_out after the speech that ends (out).
const inTime = (valley, onset, p) => Math.min(onset, Math.max(valley.deep_seconds, onset - p.lead_in));
const outTime = (valley, end, p) => Math.max(end, Math.min(valley.deep_seconds, end + p.lead_out));

// The in-point valley before phrase `first` (or the beat start) and the rules on it.
function suggestIn(ctx, beat, first) {
  const { g, p, phrases } = ctx;
  const anchor = first === null ? beat.from : phrases[first].start;
  const prev = first === null ? null : phrases[first - 1];
  const from = Math.max(anchor - p.in_before, prev ? prev.end - p.neighbour_overlap : -Infinity, 0), to = anchor + p.in_after;
  const valley = valleyNear(ctx.energy, from, to, anchor, p);
  const onset = valley ? Math.min(valley.to, to) : anchor;
  const t = valley ? inTime(valley, onset, p) : anchor;
  const valleyFrame = Math.max(0, g.midAtOrBefore(t));
  return { anchor: round6(anchor), valley, onset: round6(onset), valleyFrame, ...settleIn(ctx, valleyFrame, onset) };
}
function suggestOut(ctx, beat, last, minFrame) {
  const { g, p, phrases } = ctx;
  const anchor = last === null ? beat.to : phrases[last].end;
  const next = last === null ? null : phrases[last + 1];
  const from = anchor - p.out_before, to = Math.max(anchor, Math.min(anchor + p.out_after, next ? next.start + p.neighbour_overlap : Infinity));
  const valley = valleyNear(ctx.energy, from, to, anchor, p);
  const end = valley ? Math.max(valley.from, from) : anchor;
  const t = valley ? outTime(valley, end, p) : anchor;
  const valleyFrame = Math.min(g.count, g.midAtOrAfter(t));
  return { anchor: round6(anchor), valley, end: round6(end), valleyFrame, ...settleOut(ctx, valleyFrame, end, minFrame) };
}

const cutOf = moves => round(moves.reduce((s, m) => s + m.speech_cut_seconds, 0), 3);
const at = (ctx, n) => ({ frame: n, seconds: ctx.g.mid(n) });
const tolerated = (ctx, moves) => moves.every(m => m.speech_cut_seconds <= ctx.p.speech_tolerance);

// cut_at_change: a cut at the change drops the speech before it (in) or after
// it (out). When a clear valley (≥ clean_db below its surroundings) follows
// the change within refine_seconds (in; precedes it for out), the cut moves
// into it so it falls between words; the rules are applied again from there.
function cutAtChange(ctx, edge, result, minFrame) {
  const { g, p } = ctx, t = g.mid(result.frame);
  const [from, to] = edge === 'in' ? [t, t + p.refine_seconds] : [t - p.refine_seconds, t];
  const valley = valleyNear(ctx.energy, from, to, edge === 'in' ? from : to, p);
  // moves: the rule moves that led to the change, then those from the refined point.
  if (!valley || valley.depth_db < p.clean_db) return { frame: result.frame, clean: false, valley: null, valleyFrame: null, moves: result.moves };
  if (edge === 'in') {
    const onset = Math.min(valley.to, to), valleyFrame = Math.max(result.frame, g.midAtOrBefore(inTime(valley, onset, p)));
    const settled = settleIn(ctx, valleyFrame, onset);
    return { frame: settled.frame, clean: tolerated(ctx, settled.moves), valley, valleyFrame, moves: [...result.moves, ...settled.moves] };
  }
  const end = Math.max(valley.from, from), valleyFrame = Math.min(result.frame, g.midAtOrAfter(outTime(valley, end, p)));
  const settled = settleOut(ctx, valleyFrame, end, minFrame);
  return { frame: settled.frame, clean: tolerated(ctx, settled.moves), valley, valleyFrame, moves: [...result.moves, ...settled.moves] };
}

// Evidence of how an edge frame was reached: the semantic anchor, the energy
// valley and its frame, and the rule moves from there.
const edgeEvidence = (anchor, valley, valleyFrame, moves) => ({ semantic_anchor_seconds: anchor, energy_valley: valley, valley_frame: valleyFrame, moves });

// Options for an edge whose rules cut speech, and the one the draft uses:
// dropping the edge phrase when the new edge is clean (phrases stay the
// semantic unit), else cut_at_change when it lands in a clear valley (drops
// words, keeps the cut between words), else keeping the speech. evidence: how
// the chosen option's frame was reached (edgeEvidence).
function edgeOptions(ctx, edge, beat, first, last, result, minFrame) {
  const { p, phrases } = ctx, i = result.moves.findIndex(m => m.speech_cut_seconds > p.speech_tolerance);
  const keep = i === 0 ? result.valleyFrame : result.moves[i - 1].to_frame, accepted = result.moves.slice(i).map(m => m.reason).join('; ');
  const cut = cutAtChange(ctx, edge, result, minFrame), dropped = edge === 'in' ? Math.abs(ctx.g.mid(cut.frame) - result.onset) : Math.abs(result.end - ctx.g.mid(cut.frame));
  const evidence = {
    keep_speech: edgeEvidence(result.anchor, result.valley, result.valleyFrame, result.moves.slice(0, i)),
    cut_at_change: edgeEvidence(result.anchor, cut.valley, cut.valleyFrame, cut.moves),
  };
  const options = [
    // accepts: the cut rules whose finding keeping the speech accepts (render QA
    // marks such a finding accepted when this option was decided: apply-cuts decisions).
    { id: 'keep_speech', ...at(ctx, keep), clean: false, accepts: [result.moves[i].rule], // only the move off the kept frame; later moves start elsewhere
      consequence: `keeps the speech ${edge === 'in' ? `from ${result.onset}` : `to ${result.end}`} s and accepts: ${accepted}` },
    { id: 'cut_at_change', ...at(ctx, cut.frame), clean: cut.clean, dropped_speech_seconds: round(dropped, 3),
      consequence: `${edge === 'in' ? 'starts after' : 'ends before'} the change and drops about ${round(dropped, 3)} s of speech${cut.valley ? `; the cut falls in a valley (${cut.valley.from}–${cut.valley.to} s, ${cut.valley.depth_db} dB below its surroundings), between words` : '; no clear valley at the change, the cut falls inside speech'}` },
  ];
  const k = edge === 'in' ? first + 1 : last - 1;
  if (first !== null && first < last) {
    const other = edge === 'in' ? suggestIn(ctx, beat, k) : suggestOut(ctx, beat, k, minFrame);
    evidence[edge === 'in' ? 'drop_first_phrase' : 'drop_last_phrase'] = edgeEvidence(other.anchor, other.valley, other.valleyFrame, other.moves);
    options.push({ id: edge === 'in' ? 'drop_first_phrase' : 'drop_last_phrase', ...at(ctx, other.frame), clean: tolerated(ctx, other.moves),
      dropped_phrase: { index: edge === 'in' ? first : last, ...(({ start, end, text }) => ({ start, end, text }))(phrases[edge === 'in' ? first : last]) },
      consequence: `${edge === 'in' ? 'starts with' : 'ends with'} phrase ${k} ("${phrases[k].text}")${other.moves.length ? ` (${other.moves.map(m => m.reason).join('; ')})` : ''}${tolerated(ctx, other.moves) ? '' : `; still cuts ${cutOf(other.moves)} s of its speech`}` });
  }
  // BEATS.json prefer (keep_speech / cut_at_change) is the person's decision
  // made up front, e.g. montage where speech runs across shot cuts.
  const chosen = (beat.prefer && options.find(o => o.id === beat.prefer)) ?? options.find(o => o.id.startsWith('drop_') && o.clean) ?? options.find(o => o.id === 'cut_at_change' && o.clean) ?? options[0];
  return { options, chosen, evidence: evidence[chosen.id] };
}

const phraseEvidence = ph => ({ index: ph.index, start: ph.start, end: ph.end, text: ph.text, ...(ph.text_reliable === false ? { text_reliable: false } : {}) });

// QA pre-check: the render-qa judgements (burned captions, shot fragments) on
// the frame grid around a suggested point, so a suggestion is known to pass them.
function precheck(ctx, edge, inFrame, outFrame) {
  const { g } = ctx, n = edge === 'in' ? inFrame : outFrame, span = Math.ceil(3 * g.fps);
  const lo = Math.max(0, n - span), hi = Math.min(g.count, n + span), times = [], frames = [];
  for (let k = lo; k < hi; k++) { times.push(g.start(k)); frames.push(k); }
  const changes = frames.flatMap((k, i) => ctx.shotStartSet.has(k) && i >= 2 ? [i] : []);
  const point = g.mid(n), frame = 1 / g.fps;
  // The settle rules hold an edge on any change frame (pre-0.10 behaviour, kept);
  // the QA does not count a 'shot' step there as caption alignment, and this
  // precheck reports what the QA will say.
  const events = ctx.captionFrames.filter(k => Math.abs(g.start(k) - point) <= 1).map(k => ({ source_seconds: g.start(k), frame_mid_seconds: g.mid(k), kind: ctx.captionKind.get(k) ?? 'caption' }));
  return {
    burned_caption: judgeCutPoint(edge, point, events, { frame }).result,
    cut_fragment: judgeFragment(edge, { times, changes, at: point, step: frame, frame, first: g.mid(inFrame), last: g.mid(outFrame - 1), itemFrames: outFrame - inFrame,
      fileStart: lo === 0, fileEnd: hi === g.count }).result,
    dip: dipAt(ctx, edge, n) ? 'warn' : 'clear', // the dip part of cut-boundary-fragments
  };
}

export function suggestBeat(ctx, beat) {
  const { g, p, phrases } = ctx;
  const picked = phrases.length ? beatPhrases(beat, phrases, p)
    : typeof beat.text === 'string' ? { error: 'text beats need phrases (the analysis has no speech)' } : { first: null, last: null };
  if (picked.error) return { id: beat.id, ...planFields(beat), status: 'unmatched', error: picked.error };
  let { first, last } = picked;
  const conflicts = [], notes = [];
  if (first === null) notes.push(phrases.length ? 'No ASR phrase lies mostly inside the range: the beat edges are the semantic bounds.' : 'The analysis has no phrases: the beat edges are the semantic bounds.');
  const inResult = suggestIn(ctx, beat, first);
  let inFrame = inResult.frame, inEvidence = edgeEvidence(inResult.anchor, inResult.valley, inResult.valleyFrame, inResult.moves);
  if (!tolerated(ctx, inResult.moves)) {
    const { options, chosen, evidence } = edgeOptions(ctx, 'in', beat, first, last, inResult);
    conflicts.push({ edge: 'in', summary: `speech starts at about ${round6(Math.min(inResult.anchor, inResult.onset))} s (ASR phrase start ${inResult.anchor} s, energy valley ends ${inResult.onset} s), before what the rules require: ${inResult.moves.filter(m => m.speech_cut_seconds > 0).map(m => m.reason).join('; ')}`,
      options, draft_uses: chosen.id, ...(chosen.id === beat.prefer ? { decided_by: 'prefer' } : {}) });
    inFrame = chosen.frame;
    inEvidence = { uses: chosen.id, ...evidence, rules_candidate: inEvidence };
    if (chosen.id === 'drop_first_phrase') first += 1;
  } else {
    inResult.moves.filter(m => m.speech_cut_seconds > 0).forEach(m => notes.push(`in-point ${m.rule} rule cuts ${m.speech_cut_seconds} s after the energy valley (within the ${p.speech_tolerance} s tolerance): listen to the first syllable`));
    // A move that cuts no speech can still land just before the onset (a dip
    // ending at the first word): too little lead-in can clip its attack.
    const lead = round(inResult.onset - ctx.g.mid(inResult.frame), 3);
    if (inResult.moves.length && lead >= 0 && lead < p.min_lead_in) notes.push(`in-point ${inResult.moves.at(-1).rule} rule leaves only ${lead} s before the speech onset (energy valley end ${inResult.onset} s): listen to the first syllable`);
  }
  if (inResult.valley && inResult.valley.depth_db < p.valley_db) notes.push(`in-point valley is shallow (${inResult.valley.depth_db} dB below its surroundings): speech may run through it`);
  if (!inResult.valley) notes.push('no low-energy valley found near the in-point');
  const inDip = dipNote(ctx, 'in', inFrame, notes, { uses: inEvidence.uses, onset: inResult.onset });
  if (inDip) inEvidence = { ...inEvidence, dip: inDip };
  const opening = openingCaption(ctx, inFrame);
  if (opening) {
    inEvidence = { ...inEvidence, opening_caption: opening };
    notes.push(`in-point frame ${inFrame} is a burned caption change and the caption changes again at frame ${opening.next_change_frame} (${opening.next_change_seconds} s): the opening caption shows only ${opening.shown_seconds} s and may be the rest of the previous line; check it (render QA burned-caption-cut-points judges it again)`);
  }

  const outResult = suggestOut(ctx, beat, last, inFrame);
  let outFrame = outResult.frame, outEvidence = edgeEvidence(outResult.anchor, outResult.valley, outResult.valleyFrame, outResult.moves);
  if (!tolerated(ctx, outResult.moves)) {
    const { options, chosen, evidence } = edgeOptions(ctx, 'out', beat, first, last, outResult, inFrame);
    conflicts.push({ edge: 'out', summary: `speech runs to about ${outResult.end} s (ASR phrase end ${outResult.anchor} s), past what the rules require: ${outResult.moves.filter(m => m.speech_cut_seconds > 0).map(m => m.reason).join('; ')}`,
      options, draft_uses: chosen.id, ...(chosen.id === beat.prefer ? { decided_by: 'prefer' } : {}) });
    outFrame = chosen.frame;
    outEvidence = { uses: chosen.id, ...evidence, rules_candidate: outEvidence };
    if (chosen.id === 'drop_last_phrase') last -= 1;
  } else outResult.moves.filter(m => m.speech_cut_seconds > 0).forEach(m => notes.push(`out-point ${m.rule} rule cuts ${m.speech_cut_seconds} s before the energy valley (within the ${p.speech_tolerance} s tolerance): listen to the last syllable`));
  if (outResult.valley && outResult.valley.depth_db < p.valley_db) notes.push(`out-point valley is shallow (${outResult.valley.depth_db} dB below its surroundings): speech may run through it`);
  if (!outResult.valley) notes.push('no low-energy valley found near the out-point');
  const outDip = dipNote(ctx, 'out', outFrame, notes, { uses: outEvidence.uses, end: outResult.end, inFrame });
  if (outDip) outEvidence = { ...outEvidence, dip: outDip };
  const closing = closingCaption(ctx, outFrame, inFrame);
  if (closing) {
    outEvidence = { ...outEvidence, closing_caption: closing };
    notes.push(`out-point frame ${outFrame} is a burned caption change and the caption also changed at frame ${closing.previous_change_frame} (${closing.previous_change_seconds} s): the closing caption shows only ${closing.shown_seconds} s and may be cut short; check it (render QA burned-caption-cut-points judges it again)`);
  }
  if (picked.match?.ambiguous_with) conflicts.push({ edge: 'text', summary: 'the text matches another place about as well; the best (earliest on ties) is used', options: picked.match.ambiguous_with, draft_uses: 'best' });
  if (outFrame <= inFrame) return { id: beat.id, status: 'unmatched', error: `no usable range: out frame ${outFrame} ≤ in frame ${inFrame}`, conflicts };

  // Every phrase any option reaches (apply-cuts picks the ones inside the
  // range finally chosen, which may differ from the draft's).
  const reach = [inFrame, outFrame, ...conflicts.filter(c => c.edge !== 'text').flatMap(c => c.options.map(o => o.frame))];
  const [lo, hi] = [g.mid(Math.min(...reach)), g.mid(Math.max(...reach))];
  const optionPhrases = phrases.filter(ph => ph.end > lo && ph.start < hi).map(phraseEvidence);
  const inSeconds = g.mid(inFrame), outSeconds = g.mid(outFrame), series = ctx.analysis.loudness?.series;
  const lufs = series ? integratedLoudness(series, inSeconds, outSeconds) : null, peak = series ? truePeak(series, inSeconds, outSeconds) : null;
  const volume = volumeFor(lufs);
  if (volume === null) notes.push('Loudness unknown (no audio, or the range is shorter than one 400 ms block): volume 1 in the draft.');
  else if (volume === 1 && lufs < TARGET_LUFS) notes.push(`The range measures ${lufs} LUFS, quieter than ${TARGET_LUFS} LUFS; volume is capped at 1.`);
  return {
    // Conflicts settled by BEATS.json prefer stay listed (decided_by) but are not open.
    id: beat.id, status: conflicts.some(c => c.edge !== 'text' && !c.decided_by) ? 'needs_decision' : 'suggested',
    ...(beat.prefer ? { prefer: beat.prefer } : {}),
    ...(typeof beat.text === 'string' ? { text: beat.text, match: picked.match } : { range: [beat.from, beat.to] }),
    ...planFields(beat),
    in: { frame: inFrame, source_seconds: inSeconds },
    out: { frame: outFrame, source_seconds: outSeconds },
    frames: outFrame - inFrame, duration_seconds: round6((outFrame - inFrame) / g.fps),
    volume: { suggested: volume ?? 1, measured_lufs: lufs, true_peak_dbtp: peak, target_lufs: TARGET_LUFS,
      peak_after_gain_dbtp: peak !== null && volume ? round(peak + 20 * Math.log10(volume), 1) : null },
    conflicts, notes,
    evidence: {
      phrases: first === null ? [] : phrases.slice(first, last + 1).map(phraseEvidence),
      option_phrases: optionPhrases,
      in: { ...inEvidence, qa_precheck: precheck(ctx, 'in', inFrame, outFrame) },
      out: { ...outEvidence, qa_precheck: precheck(ctx, 'out', inFrame, outFrame) },
      shot_changes_inside: ctx.shotStarts.filter(k => k > inFrame && k < outFrame).map(k => ({ frame: k, seconds: round6(g.start(k)) })),
      caption_changes_inside: ctx.captionFrames.filter(k => k > inFrame && k < outFrame).map(k => ({ frame: k, seconds: round6(g.start(k)) })),
    },
  };
}

// Production-plan fields a beat may carry (passed through to cuts.json and on
// to apply-cuts' plan beats; never filled in when absent).
export const PLAN_FIELDS = ['role', 'purpose', 'requirement', 'hard_constraints'];
const planFields = beat => Object.fromEntries(PLAN_FIELDS.filter(k => beat[k] !== undefined).map(k => [k, beat[k]]));

// Options a beat may ask the draft to use for its conflicts (drop_* removes a
// whole phrase and stays the default; prefer it by leaving prefer out).
export const PREFER = ['keep_speech', 'cut_at_change'];
export function parseBeats(doc) {
  const beats = Array.isArray(doc) ? doc : doc?.beats;
  if (!Array.isArray(beats) || !beats.length) throw new Error('Beats must be a non-empty array (or {beats: [...]})');
  const ids = new Set();
  for (const b of beats) {
    if (typeof b?.id !== 'string' || !b.id || ids.has(b.id)) throw new Error(`Beat ids must be unique non-empty strings (${JSON.stringify(b?.id)})`);
    ids.add(b.id);
    if (typeof b.text !== 'string' && !(typeof b.from === 'number' && typeof b.to === 'number')) throw new Error(`Beat ${b.id} needs {from, to} or {text}`);
    for (const k of ['role', 'purpose', 'requirement']) if (b[k] !== undefined && !(typeof b[k] === 'string' && b[k].trim())) throw new Error(`Beat ${b.id}: ${k} must be a non-empty string`);
    if (b.hard_constraints !== undefined && !(Array.isArray(b.hard_constraints) && b.hard_constraints.every(c => typeof c === 'string' && c.trim()))) throw new Error(`Beat ${b.id}: hard_constraints must be an array of non-empty strings`);
    if (b.prefer !== undefined && !PREFER.includes(b.prefer)) throw new Error(`Beat ${b.id}: prefer must be one of ${PREFER.join(', ')}`);
  }
  const options = Array.isArray(doc) ? {} : doc;
  if (options.canvas_fps !== undefined && !(Number.isInteger(options.canvas_fps) && options.canvas_fps > 0)) throw new Error('canvas_fps must be a positive integer');
  return { beats, asset_id: options.asset_id ?? 'ASSET_ID', track_id: options.track_id ?? 'v_main', canvas_fps: options.canvas_fps ?? null };
}

const RULE_TEXT = 'in: deepest point of the deep low-energy valley nearest before the first phrase (at most lead_in before the speech), then caption rule (no change within caption_window after, unless on the in-point frame: a further change within caption_window after such a frame is reported in notes and evidence.in.opening_caption, not moved) and dip rule (inside a dip to black: move to its first recovered frame when that cuts ≤ speech_tolerance s of speech, else keep and report in notes and evidence.in.dip) and shot rule (no change within shot_window after; flash chains skipped), repeated; out: deepest point of the deep valley nearest after the last phrase (at most lead_out after the speech), first frame midpoint at or after it (exclusive), then caption rule (no change within caption_window before, unless on the out-point frame: a further change within caption_window before such a frame is reported in notes and evidence.out.closing_caption, not moved), dip rule (last shown frame inside a dip: move to the first darkened frame of the dip under the same speech rule, else evidence.out.dip) and shot rule (no piece of the next shot at the end), repeated; a move that cuts more than speech_tolerance s of speech is a conflict with options';

// The open decisions of a beat: which edge, the option the draft uses and the others.
const decisionsOf = r => r.conflicts.filter(c => c.edge !== 'text').map(c => ({ edge: c.edge, draft_uses: c.draft_uses, options: c.options.map(o => o.id) }));

// Items back to back from frame 0: [in, out] source seconds → {start_frame,
// frames} with frames = max(1, round((out − in) × fps)). Shared with apply-cuts.
export function backToBack(ranges, fps) {
  let cursor = 0;
  return ranges.map(([from, to]) => {
    const frames = Math.max(1, Math.round((to - from) * fps)), slot = { start_frame: cursor, frames };
    cursor += frames;
    return slot;
  });
}

export function suggestCuts(analysis, beatsDoc, p = RULES) {
  if (analysis?.schema !== ANALYSIS_SCHEMA) throw new Error(`Analysis must be ${ANALYSIS_SCHEMA}`);
  const { beats, asset_id, track_id, canvas_fps } = parseBeats(beatsDoc), ctx = context(analysis, p);
  const fps = canvas_fps ?? ctx.g.fps;
  const results = beats.map(beat => suggestBeat(ctx, beat));
  const placed = results.filter(r => r.in), slots = backToBack(placed.map(r => [r.in.source_seconds, r.out.source_seconds]), fps);
  const items = placed.map((r, i) => ({ id: r.id, track_id, kind: 'media', asset_id, ...slots[i], source_in_seconds: r.in.source_seconds, volume: r.volume.suggested,
    // Explicit marks on an open decision: EditDocument v2 refuses these keys, so the item cannot be used until a person decides and removes them.
    ...(r.status === 'needs_decision' ? { needs_decision: true, decisions: decisionsOf(r) } : {}) }));
  return {
    schema: SUGGEST_SCHEMA,
    analysis: { media_sha256: analysis.media.sha256, path_basename: analysis.media.path_basename, frame_rate: analysis.media.frame_rate, speech_source: analysis.speech.source },
    rules: { ...p, description: RULE_TEXT },
    beats: results,
    draft: { note: 'EditDocument v2 media items, back to back from frame 0 at canvas_fps (default: the source frame rate); frames = round((out − in) × canvas_fps). Replace asset_id. An item of a needs_decision beat carries needs_decision: true and decisions (the option the draft uses and the alternatives); v2 validation refuses those keys: decide with apply-cuts --choose BEAT.EDGE=OPTION, which re-lays the items without them.',
      canvas_fps: fps, needs_decision: results.filter(r => r.status === 'needs_decision').map(r => r.id), items },
    caveat: 'Advice, not approval: ASR times are approximate and the caption detector is a frame-difference heuristic. Listen to every cut and look at its first and last frame before rendering.',
  };
}

export function parseSuggestArgs(argv) {
  const [analysis, beats, output, ...rest] = argv;
  if (!analysis || !beats || !output || rest.length) throw new Error('suggest-cuts needs ANALYSIS.json BEATS.json NEW_OUT.json');
  return { analysis, beats, output };
}
export async function suggestCutsFile(analysisFile, beatsFile, output) {
  if (!output.endsWith('.json')) throw new Error('Suggestion output must be a .json file');
  if (await fs.lstat(output).then(() => true, () => false)) throw new Error(`Output already exists: ${output}`);
  const result = suggestCuts(JSON.parse(await fs.readFile(analysisFile, 'utf8')), JSON.parse(await fs.readFile(beatsFile, 'utf8')));
  await fs.writeFile(output, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
  const open = result.beats.filter(b => b.status === 'needs_decision');
  return { status: open.length ? 'needs_decision' : 'suggested', output,
    needs_decision: open.map(b => ({ id: b.id, decisions: decisionsOf(b) })),
    beats: result.beats.map(b => ({ id: b.id, status: b.status, in: b.in?.source_seconds ?? null, out: b.out?.source_seconds ?? null,
    frames: b.frames ?? null, volume: b.volume?.suggested ?? null, conflicts: b.conflicts?.length ?? 0, ...(b.error ? { error: b.error } : {}) })) };
}
