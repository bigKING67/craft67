// Source frame alignment (EditDocument v2 asset.frame_rate). Pure (only the
// pure timeline math), so compilation, font binding and QA can all share it.
//
// A media item's source_in_seconds is a decimal the author (or an agent) wrote,
// sometimes truncated: 24.4333 or 24.433 for frame 733 of a 30 fps source
// (733/30 = 24.43333…). The renderer shows the frame whose time is ≤ the seek
// time, so a truncated in-point shows the PREVIOUS frame. Compilation corrects
// exactly this case and nothing else: for a video-track media item of an asset
// with frame_rate, an in-point below a frame's start by at most
// TRUNCATION_SECONDS (2 ms: a decimal truncated to milliseconds or finer) AND by
// strictly less than TRUNCATION_FRAMES (0.1 frame) plays from that frame's
// start + CORRECTION_SECONDS (0.1 ms). Every other in-point (on a frame start,
// or further inside a frame) is kept, so a split stays continuous, an exact
// audio in-point stays exact and the shift is at most min(2 ms, 0.1 frame) +
// 0.1 ms. Audio-track items are never changed.
// Arithmetic is exact: the in-point is taken as the decimal the document holds
// (the shortest round-trip form of the JSON number) and the frame rate as an
// integer ratio, both as BigInt fractions. The document is never rewritten.
import { SOURCE_END_TOLERANCE, round9, sourceSeconds } from './timeline.mjs';

export const TRUNCATION_SECONDS = Object.freeze({ num: 2n, den: 1000n }); // 2 ms, inclusive
export const TRUNCATION_FRAMES = Object.freeze({ num: 1n, den: 10n }); // 0.1 frame, exclusive
export const CORRECTION_SECONDS = 0.0001;
const FRAME_RATE = /^([1-9][0-9]{0,5})\/([1-9][0-9]{0,5})$/;

export const validFrameRate = value => typeof value === 'string' && FRAME_RATE.test(value);
// "<num>/<den>" → { num, den } (BigInt). An already parsed rate is accepted
// too: it is checked by the same rule (its "<num>/<den>" form) and returned as
// is, so a caller parses once and both forms behave the same.
export function parseFrameRate(value) {
  const parsed = typeof value?.num === 'bigint' && typeof value?.den === 'bigint';
  const m = FRAME_RATE.exec(parsed ? `${value.num}/${value.den}` : typeof value === 'string' ? value : '');
  if (!m) throw new Error(`Invalid frame_rate ${parsed ? `${value.num}/${value.den}` : JSON.stringify(value)} (expected "<num>/<den>", e.g. "30/1" or "30000/1001")`);
  return parsed ? value : { num: BigInt(m[1]), den: BigInt(m[2]) };
}

// Exact {p, q} with value = p / q for a finite non-negative JS number, from its
// shortest round-trip decimal form ("24.4333", "1e-7", "1.5e+21").
function decimalFraction(value) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) throw new Error(`Source time must be a finite non-negative number: ${value}`);
  const m = /^(\d+)(?:\.(\d+))?(?:e([+-]\d+))?$/.exec(String(value));
  if (!m) throw new Error(`Unsupported number form: ${value}`);
  const digits = BigInt(`${m[1]}${m[2] ?? ''}`), exponent = Number(m[3] ?? 0) - (m[2]?.length ?? 0);
  return exponent >= 0 ? { p: digits * 10n ** BigInt(exponent), q: 1n } : { p: digits, q: 10n ** BigInt(-exponent) };
}

// An ffprobe ratio ("30/1", "1/15360") with both terms positive → { num, den }
// (Numbers); null otherwise ("0/0", missing). Shared by import (frame rates)
// and the QA source timing (time bases).
export function rational(value) {
  const m = /^(\d+)\/(\d+)$/.exec(String(value ?? ''));
  return m && Number(m[1]) > 0 && Number(m[2]) > 0 ? { num: Number(m[1]), den: Number(m[2]) } : null;
}

const gcd = (a, b) => { while (b) [a, b] = [b, a % b]; return a; };
// "30/1", "30000/1001" from ffprobe ratios, reduced; null when not a usable rate.
export function reduceFrameRate(value) {
  const r = rational(value);
  if (!r) return null;
  let num = BigInt(r.num), den = BigInt(r.den);
  const g = gcd(num, den); num /= g; den /= g;
  const text = `${num}/${den}`;
  return validFrameRate(text) ? text : null;
}

// The source frame k whose start (k / rate) a truncated in-point fell short of:
// `seconds` is below k / rate by at most 2 ms and by strictly less than 0.1
// frame. Null for any other in-point (exactly on a frame start, or further
// inside a frame). frameRate: "<num>/<den>" or parseFrameRate's result.
export function truncatedFrame(seconds, frameRate) {
  const { num, den } = parseFrameRate(frameRate);
  const { p, q } = decimalFraction(seconds);
  // Position in frames: seconds × num / den = P / Q.
  const P = p * num, Q = q * den, rest = P % Q; // 0 ≤ rest < Q
  if (!rest) return null;
  // Below the next frame start by gap / Q frames = gap × den / (Q × num) seconds.
  const gap = Q - rest;
  if (gap * TRUNCATION_FRAMES.den >= Q * TRUNCATION_FRAMES.num) return null;
  if (gap * den * TRUNCATION_SECONDS.den > Q * num * TRUNCATION_SECONDS.num) return null;
  return Number(P / Q + 1n);
}

// Compiled in-point for an in-point on a source of `frameRate` (string or
// parsed; parsed once here): { seconds: frame start + 0.1 ms, frame } when
// truncated, else null (keep it).
export function correctedSourceIn(seconds, frameRate) {
  const rate = parseFrameRate(frameRate), frame = truncatedFrame(seconds, rate);
  if (frame === null) return null;
  return { seconds: round9(frame * Number(rate.den) / Number(rate.num) + CORRECTION_SECONDS), frame };
}

// The document as compiled, computed once per render or QA pass and shared by
// everything that depends on source time (data-media-start, linked caption
// windows, font runs, QA caption samples, cut-point checks). Video-track media
// items of assets with frame_rate get their corrected in-point; an item whose
// corrected range would pass the asset end (beyond SOURCE_END_TOLERANCE, as
// validateV2) keeps its in-point. Audio-track items are unchanged.
// validateV2 is the single source of the asset rules (frame_rate only on assets
// with a picture); this reads frame_rate only and does not validate.
// The input is never mutated; a view passed in again is returned as is.
//
// Which assets' frame_rate applies is decided once, outside: a document read
// from a project (loadProject) is bound to its frame alignment (bindAlignment;
// frame-alignment.mjs re-checks every asset with frame_rate against its file),
// an edit batch carries that decision to the document it builds, and QA binds
// the alignment the render receipt recorded. A bound document applies exactly
// the assets its alignment marks applied; a stale one keeps its written
// in-points. A document that is not bound (built in memory: tests, compose of a
// literal document, a project being created from files the import rule has
// just probed) gets the structural view only: every recorded frame_rate is
// applied as written and no file is looked at.
const VIEWS = new WeakSet(), CORRECTIONS = new WeakMap(), ALIGNMENTS = new WeakMap();

// Bind `doc` to `alignment`: exactly one { asset_id, frame_rate, applied,
// reason? } entry per asset with frame_rate (checked, so an alignment from a
// receipt or an earlier revision that does not describe this document is
// refused). Returns doc. A compiled view cannot be rebound.
export function bindAlignment(doc, alignment) {
  if (VIEWS.has(doc)) throw new Error('A compiled view cannot be bound to another frame alignment');
  const rated = doc.assets.filter(a => a.frame_rate);
  if (!Array.isArray(alignment) || alignment.length !== rated.length ||
      rated.some(a => !alignment.some(e => e?.asset_id === a.id && e.frame_rate === a.frame_rate && typeof e.applied === 'boolean'))) {
    throw new Error('Frame alignment does not describe this document (one entry per asset with frame_rate expected)');
  }
  ALIGNMENTS.set(doc, alignment);
  return doc;
}
// The alignment bound to a document (or to the document a view was compiled from), or null.
export const alignmentOf = doc => ALIGNMENTS.get(doc) ?? null;

export function compiledView(doc) {
  if (VIEWS.has(doc)) return doc;
  const alignment = ALIGNMENTS.get(doc), applied = asset => !alignment || alignment.find(e => e.asset_id === asset.id).applied;
  const fps = doc.canvas.fps, assets = new Map(doc.assets.filter(a => a.frame_rate && applied(a)).map(a => [a.id, a]));
  const video = new Set(doc.tracks.filter(t => t.kind === 'video').map(t => t.id));
  const items = doc.items.map(item => {
    const asset = item.kind === 'media' && video.has(item.track_id) ? assets.get(item.asset_id) : undefined;
    const fix = asset ? correctedSourceIn(item.source_in_seconds, asset.frame_rate) : null;
    if (!fix || fix.seconds + sourceSeconds(item, fps) > asset.duration + SOURCE_END_TOLERANCE) return item;
    const compiled = { ...item, source_in_seconds: fix.seconds };
    CORRECTIONS.set(compiled, { written: item, frame: fix.frame });
    return compiled;
  });
  const view = { ...doc, items };
  VIEWS.add(view);
  if (alignment) ALIGNMENTS.set(view, alignment);
  return view;
}

// For an item of a compiled view: { written, frame } (the document's item and
// the source frame its in-point was corrected to), or null when unchanged.
export const correctionOf = item => CORRECTIONS.get(item) ?? null;

// The analysed picture stream of an ffprobe JSON: the first video stream that
// is not cover art (attached_pic), as { stream, index } with index its position
// among the video streams (ffmpeg's 0:v:index); null when there is none. The QA
// source timing decodes this stream and import reads frame_rate from it.
export function pictureStream(info) {
  const videos = (info?.streams ?? []).filter(s => s.codec_type === 'video');
  const index = videos.findIndex(s => !s.disposition?.attached_pic);
  return index < 0 ? null : { stream: videos[index], index };
}

// A stream's start from ffprobe integers, exactly: start_pts × time_base as
// the fraction { p, q } (BigInt, q > 0) with its value in seconds; null when
// either is missing or unusable. The single start reading of import
// (probedFrameRate) and the QA source timing (sourceTiming).
export function streamStart(stream) {
  const tb = rational(stream?.time_base), pts = stream?.start_pts;
  if (!tb || pts === undefined || pts === null || pts === '' || !Number.isInteger(Number(pts))) return null;
  const p = BigInt(pts) * BigInt(tb.num), q = BigInt(tb.den);
  return { p, q, seconds: Number(pts) * tb.num / tb.den };
}

// a/b < c/d ⇔ a·d < c·b (denominators positive).
const earlier = (a, b) => a.p * b.q < b.p * a.q;
// The earliest streamStart of all streams of an ffprobe JSON (the media time 0
// of the renderer and the QA timing), or null when no stream reports one.
export function earliestStart(info) {
  let first = null;
  for (const start of (info?.streams ?? []).map(streamStart)) if (start && (!first || earlier(start, first))) first = start;
  return first;
}

// Why the frame grid k / rate of an ffprobe JSON's video does not start at
// media time 0, or null when it does:
//   - the first video stream is the picture (pictureStream index 0, not cover
//     art), so the asset's width, height (probe: first video stream, as before
//     frame_rate existed) and frame_rate describe the same stream;
//   - its own start (streamStart) equals the earliest start of all streams.
//     The renderer and the QA timing (sourceTiming) take that earliest start as
//     media time 0 (measured: in an MKV whose audio starts at -0.067 s, in-point
//     X shows video time X - 0.067), so only then does frame k start at media
//     time k / rate. Streams that all start at the same non-zero time qualify;
//     a file whose audio starts before its video (MKV/WebM can keep a negative
//     audio start, MP4 AAC priming under an offset) does not. Compared exactly.
// Import (probedFrameRate) and the load-time re-check (frameAlignment, loadProject) share it.
export function mediaZeroProblem(info) {
  const picture = pictureStream(info);
  if (!picture) return 'no picture stream (only cover art or no video)';
  if (picture.index !== 0) return 'the first video stream is cover art, the picture is a later stream';
  const start = streamStart(picture.stream);
  if (!start) return 'the video stream reports no usable start_pts/time_base';
  const first = earliestStart(info);
  return earlier(first, start) ? `the video stream starts at ${start.seconds} s, after the earliest stream start ${first.seconds} s (media time 0), ` +
    'so frame k does not start at media time k / rate' : null;
}

// frame_rate recorded at import from one ffprobe JSON (-show_streams
// -show_format), or null. Recorded only when the frame grid k / rate is
// trustworthy in media time: mediaZeroProblem finds nothing, and the picture
// stream reports the same rate as r_frame_rate and avg_frame_rate (compared
// reduced). They differ for variable-frame-rate sources (and for some damaged
// or edited constant-rate files); such sources get no frame_rate and keep the
// renderer behaviour. Audio-only files and cover art get none.
export function probedFrameRate(info) {
  if (mediaZeroProblem(info)) return null;
  const video = pictureStream(info).stream, rate = reduceFrameRate(video.r_frame_rate);
  return rate && rate === reduceFrameRate(video.avg_frame_rate) ? rate : null;
}
