// Caption/speech sync at in-points (render-qa caption-speech-sync): does the
// burned caption line on screen when the cut opens belong to speech spoken
// BEFORE the cut? The frame-difference detector cannot read the line, and its
// change times miss lines that switch during motion or a fade, so this check
// compares the band itself: the outlined light strokes (burned captions are
// light glyphs with a dark outline or shadow) of the first shown frame against
// a frame inside the last earlier speech (ASR phrases from the source analysis)
// within 1 s before the cut. When both frames hold text and the cut frame's
// strokes are almost all already there, the opening line was on screen while
// earlier speech was spoken: it likely shows words the cut does not play.
//
// Calibration (5 real 30 fps films, every ASR phrase start as an in-point 0.1 s
// before it; 427 points with text in both frames; coverage read by eye on 6
// random frames per band): ≥ 0.9 → 6/6 the earlier line, 0.8–0.9 → 4/6 (one
// changed line, one set of graphic labels), 0.7–0.8 → 2/6, 0.6–0.7 → 1/6.
// Different lines in the same place share about half their strokes. Text
// presence: frames with caption text 0.4–4.0 % outlined strokes, without
// 0.00–0.07 %. A hint to look at (about 5 in 6 right at ≥ 0.8), not a verdict.
import { CAPTION_BAND, TIME_EPS, frameStep, round6 } from './burned-captions.mjs';

export const CAPTION_SPEECH = Object.freeze({
  lookback_seconds: 1.0, // earlier speech considered before the cut
  lookahead_seconds: 1.0, // the speech the cut opens on starts within this after it (else: none)
  min_speech_seconds: 0.15, // shortest earlier speech piece sampled
  outline_px: 2, glyph_level: 200, outline_level: 70, // a stroke pixel: ≥ glyph_level with a pixel ≤ outline_level outline_px away (360 px short edge)
  text_min_share: 0.3, // % of band pixels that are strokes for "the band holds text"
  coverage: 0.8, // share of the cut frame's strokes found (±1 px) in the earlier frame
});
export const CAPTION_SPEECH_METHOD = 'outlined light-stroke mask of the source caption band: first shown frame vs a frame inside the last earlier ASR speech within lookback_seconds (not OCR; cannot read the line)';

const round = (v, d = 3) => Math.round(v * 10 ** d) / 10 ** d;

// Stroke mask of the band rows only (Uint8Array of width × band rows, 1 =
// stroke) and its share in % of the band.
export function strokeMask(frame, width, height, band = CAPTION_BAND, p = CAPTION_SPEECH) {
  const d = p.outline_px, y0 = Math.max(d, Math.round(height * band.top)), y1 = Math.min(height - d, Math.round(height * band.bottom));
  const rows = Math.max(0, y1 - y0), mask = new Uint8Array(width * rows);
  let strokes = 0, count = 0;
  for (let y = y0; y < y1; y++) {
    const row = y * width, out = (y - y0) * width;
    for (let x = d; x < width - d; x++, count++) {
      const i = row + x;
      if (frame[i] < p.glyph_level) continue;
      if (Math.min(frame[i - d], frame[i + d], frame[i - d * width], frame[i + d * width]) <= p.outline_level) { mask[out + x] = 1; strokes++; }
    }
  }
  return { mask, rows, strokes, share: count ? round(100 * strokes / count, 2) : 0 };
}

// Share of a's strokes with a stroke of b within ±1 px (masks of one band).
export function strokeCoverage(a, b, width) {
  if (!a.strokes) return 0;
  let hit = 0;
  for (let y = 0; y < a.rows; y++) {
    for (let x = 0; x < width; x++) {
      if (!a.mask[y * width + x]) continue;
      let found = false;
      for (let yy = Math.max(0, y - 1); yy <= Math.min(a.rows - 1, y + 1) && !found; yy++)
        for (let xx = Math.max(0, x - 1); xx <= Math.min(width - 1, x + 1) && !found; xx++) found = b.mask[yy * width + xx] === 1;
      if (found) hit++;
    }
  }
  return round(hit / a.strokes, 2);
}

// The earlier speech to sample: the last piece (≥ min_speech_seconds) of the
// phrases FINISHED by the cut within lookback; null when none. A phrase the cut
// lands in is the speech it opens on: its line on screen is the right one.
export function earlierSpeech(phrases, at, p = CAPTION_SPEECH) {
  const pieces = phrases.filter(ph => ph.end <= at + p.min_speech_seconds / 3).map(ph => ({ ph, from: Math.max(ph.start, at - p.lookback_seconds), to: Math.min(ph.end, at) }))
    .filter(s => s.to - s.from >= p.min_speech_seconds - TIME_EPS).sort((a, b) => a.to - b.to);
  return pieces.at(-1) ?? null;
}

// Judge one in-point from decoded grey frames: { result: 'warn' | 'clear', ... }.
export function judgeCaptionSpeech({ frames, times, width, height }, { at, phrases }, band = CAPTION_BAND, p = CAPTION_SPEECH) {
  // The speech the cut opens on: the phrase it lands in or the next one starting
  // within lookahead (none: the cut opens in silence).
  const opening = phrases.find(ph => ph.end > at + TIME_EPS && ph.start <= at + p.lookahead_seconds) ?? null;
  const base = { opening_speech: opening?.text ?? null };
  const earlier = earlierSpeech(phrases, at, p);
  if (!earlier) return { result: 'clear', ...base, reason: 'no_earlier_speech' };
  const frame = frameStep(times);
  const cutIndex = times.findIndex(t => t > at - frame + TIME_EPS); // the frame shown at the in-point
  const sampleAt = Math.min((earlier.from + earlier.to) / 2, at - 2 * frame);
  const earlierIndex = times.findLastIndex(t => t <= sampleAt + TIME_EPS);
  if (cutIndex < 0 || earlierIndex < 0) throw new Error('decoded window misses the cut or the earlier speech frame');
  const cut = strokeMask(frames[cutIndex], width, height, band, p), before = strokeMask(frames[earlierIndex], width, height, band, p);
  const facts = { ...base, earlier_speech: earlier.ph.text, earlier_sample_seconds: round6(times[earlierIndex]), text_share_cut: cut.share, text_share_earlier: before.share };
  if (cut.share < p.text_min_share || before.share < p.text_min_share) return { result: 'clear', ...facts, reason: 'no_text' };
  const coverage = strokeCoverage(cut, before, width);
  return { result: coverage >= p.coverage ? 'warn' : 'clear', ...facts, coverage };
}

// The cut-check (cut-checks.mjs runCutChecks) for in-points; out-points and
// items without phrases (their asset has no --analysis) are not judged.
// phrasesFor(point) → ASR phrases of the point's asset, or null.
export function captionSpeechCheck(phrasesFor, band = CAPTION_BAND, p = CAPTION_SPEECH) {
  const scope = n => `${n} source in-point(s) with an ASR analysis`;
  return {
    applies: point => point.edge === 'in' && Boolean(phrasesFor(point)),
    skip: point => ({ reason: point.edge !== 'in' ? 'out_point' : 'no_analysis' }),
    measured: { method: CAPTION_SPEECH_METHOD, band, thresholds: { ...p } },
    none: 'No video media items, so no in-points to check against speech.',
    range: point => [point.source_seconds - p.lookback_seconds - 0.1, point.source_seconds + 0.1],
    analyse: (point, window) => judgeCaptionSpeech(window, { at: point.source_seconds, phrases: phrasesFor(point) }, band, p),
    summary: n => ({
      scope: scope(n), finding: 'caption line left from earlier speech',
      describe: e => `${e.item_id} in-point at output ${e.output_seconds.toFixed(3)} s opens on a caption line already shown during earlier speech ("${e.earlier_speech}", sampled at source ${e.earlier_sample_seconds.toFixed(3)} s; ${Math.round(e.coverage * 100)}% of its strokes)${e.opening_speech === null ? ' while it opens without speech' : ` while it plays "${e.opening_speech}"`}`,
      warned: (count, details, unchecked) => `${count} in-point(s) likely open on a caption line from speech before the cut: ${details}.${unchecked} Stroke comparison of the caption band, not OCR (about 5 in 6 right on calibration); check by eye.`,
      pass: 'No in-point opens on a caption line already shown during speech before the cut (stroke comparison of the caption band, not OCR).',

    }),
  };
}

