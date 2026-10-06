// Footage analysis for cut-point suggestions (suggest-cuts.mjs). One source
// file is read once per signal and summarised into a JSON the suggester (and a
// person) can work from without opening the media again:
//   - media: duration, frame rate, media-time origin, SHA-256;
//   - shots: frame-exact shot boundaries over the whole file (the hard-cut /
//     flash rule of cut-fragments.mjs);
//   - captions: burned-in caption band changes over the whole file (the step
//     detector of burned-captions.mjs, not OCR);
//   - dips: short fades / dips to black and back (cut-fragments.mjs lumaDips on
//     the mean levels of the same decode), too gradual for the shot rule;
//   - phrases: ASR phrases (asr.mjs phrasesFromTokens) from a given transcript
//     or a local whisper.cpp run;
//   - energy: a 20 ms RMS envelope of the mono mix (valleys are where a cut
//     hides when music under the voice makes silence detection useless);
//   - loudness: the EBU R128 momentary series and true peak per 100 ms, so the
//     integrated loudness of any range can be computed later, plus the whole
//     file and every phrase.
// Everything stays local: decoded audio and frames live in memory or in a
// private temp dir that is removed. Customer text and media are never copied
// anywhere but the output file the caller names.
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { digest, ffprobeJson, run } from './project.mjs';
import { ebur128Summary, mediaTool } from './media-analysis.mjs';
import { CAPTION_CUT, captionBand, decodeWindow, round6, sourceTiming, stepEvents } from './burned-captions.mjs';
import { CUT_FRAGMENT, DIP, DIP_METHOD, frameStats, lumaDips, shotChanges } from './cut-fragments.mjs';
import { earliestStart, pictureStream, probedFrameRate, streamStart } from './source-frames.mjs';
import { TRANSCRIPT_SCHEMA, transcribe } from './asr.mjs';

export const ANALYSIS_SCHEMA = 'creative-craft.footage-analysis.v1';
export const ENERGY = Object.freeze({ window_seconds: 0.02, sample_rate: 16000, floor_db: -100 });
// Whole-file video scan: decoded in chunks (memory stays bounded), each padded
// so that a transition at a chunk edge still has the frames the detectors need.
export const SCAN = Object.freeze({ chunk_seconds: 15, pad_seconds: 0.3, scene_threshold: 0.3 });
export const TARGET_LUFS = -14;
const round = (value, digits = 3) => Math.round(value * 10 ** digits) / 10 ** digits;
const ffmpeg = () => mediaTool('ffmpeg');

// ---------------------------------------------------------------- energy
// RMS per window of `window` samples, in dBFS (floored), of mono float samples.
export function rmsEnvelope(samples, window, floor = ENERGY.floor_db) {
  const n = Math.floor(samples.length / window), out = new Array(n);
  for (let w = 0; w < n; w++) {
    let sum = 0;
    for (let i = w * window; i < (w + 1) * window; i++) sum += samples[i] * samples[i];
    const rms = Math.sqrt(sum / window);
    out[w] = rms > 0 ? Math.max(floor, round(20 * Math.log10(rms), 1)) : floor;
  }
  return out;
}

async function energyEnvelope(file, audioIndex, offset, signal) {
  const { stdout } = await run(ffmpeg(), ['-nostdin', '-v', 'error', '-i', file, '-map', `0:a:${audioIndex}`, '-vn', '-ac', '1', '-ar', String(ENERGY.sample_rate),
    '-f', 'f32le', 'pipe:1'], { encoding: 'buffer', timeout: 600000, maxBuffer: 1024 * 1024 * 1024, signal });
  const samples = new Float32Array(stdout.buffer, stdout.byteOffset, Math.floor(stdout.length / 4));
  const window = Math.round(ENERGY.window_seconds * ENERGY.sample_rate);
  return { window_seconds: ENERGY.window_seconds, sample_rate: ENERGY.sample_rate, start_seconds: round6(offset), unit: 'dBFS', floor_db: ENERGY.floor_db,
    format: 'values_db[i] = RMS of the mono mix over [start_seconds + i × window_seconds, start_seconds + (i + 1) × window_seconds), dBFS rounded to 0.1, floored at floor_db',
    values_db: rmsEnvelope(samples, window) };
}

// ---------------------------------------------------------------- loudness
// Per-100 ms frames of ffmpeg's ebur128 filter (framelog at verbose level):
// t (end of the 400 ms momentary block), M (momentary LUFS) and the frame's
// true peak (FTPK, max over channels, dBTP; null when this ffmpeg does not
// print it). Lines are matched one by one, so field order and spacing may vary.
const LEVEL = '(-?[\\d.]+|-inf|nan)';
export function parseEbur128Frames(log) {
  const frames = [];
  for (const line of log.split('\n')) {
    if (!line.includes('Parsed_ebur128')) continue;
    const t = line.match(/\bt:\s*([\d.]+)/), m = line.match(new RegExp(`\\bM:\\s*${LEVEL}`));
    if (!t || !m) continue;
    const ftpk = line.match(/FTPK:((?:\s*(?:-?[\d.]+|-inf|nan))+)\s*dBFS/);
    const peaks = ftpk ? ftpk[1].trim().split(/\s+/).map(Number).filter(Number.isFinite) : [];
    frames.push({ t: Number(t[1]), m: Number(m[1]), tp: ftpk ? (peaks.length ? Math.max(...peaks) : -Infinity) : null });
  }
  return frames;
}

// BS.1770 integrated loudness of [from, to] from momentary (400 ms, 100 ms hop)
// blocks fully inside the range: absolute gate −70 LUFS, relative gate −10 LU
// below the ungated mean. null when no block fits (range < 0.4 s) or all are gated.
const BLOCK = 0.4;
export function integratedLoudness(series, from, to) {
  const { hop_seconds: hop, start_seconds: start, momentary_lufs: values } = series;
  const blocks = [];
  values.forEach((m, k) => {
    const end = start + (k + 1) * hop;
    if (end - BLOCK >= from - 1e-6 && end <= to + 1e-6 && Number.isFinite(m) && m > -70) blocks.push(m);
  });
  if (!blocks.length) return null;
  const energy = l => 10 ** ((l + 0.691) / 10), loud = e => -0.691 + 10 * Math.log10(e);
  const mean = list => list.reduce((s, l) => s + energy(l), 0) / list.length;
  const gate = loud(mean(blocks)) - 10, kept = blocks.filter(l => l > gate);
  return kept.length ? round(loud(mean(kept)), 1) : null;
}
// Highest per-frame true peak of frames ending in (from, to + hop].
export function truePeak(series, from, to) {
  const { hop_seconds: hop, start_seconds: start, true_peak_dbtp: values } = series;
  let peak = -Infinity;
  values.forEach((p, k) => { const end = start + (k + 1) * hop; if (end > from + 1e-6 && end <= to + hop + 1e-6 && p !== null && p > peak) peak = p; });
  return Number.isFinite(peak) ? round(peak, 1) : null;
}
// Volume (linear gain 0–1) that brings `lufs` to the target; render volume cannot exceed 1.
export function volumeFor(lufs, target = TARGET_LUFS) {
  if (lufs === null || !Number.isFinite(lufs)) return null;
  return round(Math.min(1, 10 ** ((target - lufs) / 20)), 3);
}

async function loudnessSeries(file, audioIndex, offset, signal) {
  const { stderr } = await run(ffmpeg(), ['-nostdin', '-hide_banner', '-nostats', '-v', 'verbose', '-i', file, '-map', `0:a:${audioIndex}`, '-vn',
    '-af', 'ebur128=peak=true:framelog=verbose', '-f', 'null', '-'], { timeout: 600000, maxBuffer: 256 * 1024 * 1024, signal });
  const frames = parseEbur128Frames(stderr);
  if (!frames.length) throw new Error('ebur128 reported no frames');
  const summary = ebur128Summary(stderr), finite = value => Number.isFinite(value) ? value : null; // −inf as null, like the series
  return {
    series: { hop_seconds: 0.1, start_seconds: round6(offset), block_seconds: BLOCK,
      format: 'momentary_lufs[k] = EBU R128 momentary loudness of the 400 ms block ending at start_seconds + (k + 1) × hop_seconds; true_peak_dbtp[k] = true peak of the 100 ms frame ending there (max over channels); −inf as null',
      momentary_lufs: frames.map(f => Number.isFinite(f.m) ? round(f.m, 1) : null), true_peak_dbtp: frames.map(f => f.tp !== null && Number.isFinite(f.tp) ? round(f.tp, 1) : null) },
    integrated_lufs: finite(summary.integrated_lufs), true_peak_dbtp: finite(summary.true_peak_dbtp),
  };
}

// ---------------------------------------------------------------- video scan
// Frame number of a decoded time on a constant frame grid (null without one).
export const frameOf = (t, rate) => rate ? Math.round(t * rate.num / rate.den) : null;
export const frameMidSeconds = (n, rate) => round6((n + 0.5) * rate.den / rate.num);

// Shot list from sorted shot-change times: shot i runs from change i − 1 (or
// the first frame) to the frame before change i (or the last frame).
export function buildShots(changeTimes, { rate, duration, frameCount }) {
  const starts = [0, ...changeTimes];
  return starts.map((start, i) => {
    const end = i + 1 < starts.length ? starts[i + 1] : duration;
    const startFrame = frameOf(start, rate), endFrame = rate ? (i + 1 < starts.length ? frameOf(end, rate) : frameCount) : null;
    return { index: i, start_seconds: round6(start), end_seconds: round6(end),
      ...(rate ? { start_frame: startFrame, end_frame: endFrame, frames: endFrame - startFrame, start_mid_seconds: frameMidSeconds(startFrame, rate) } : {}),
      duration_seconds: round6(end - start) };
  });
}

// Decode [0, duration) in chunks and run both detectors on each; an event is
// kept by the chunk whose nominal range [a, b) holds its time. The per-frame
// mean levels of the same decode (frameStats, also used by shotChanges) are
// kept for the whole file, so dips spanning a chunk edge are found too.
export async function scanVideo(file, { timing, duration, band, sceneThreshold = SCAN.scene_threshold, decode = decodeWindow, chunk = SCAN.chunk_seconds, pad = SCAN.pad_seconds, signal }) {
  const shots = [], captions = [], levels = [];
  const sceneJump = round6(sceneThreshold * 100);
  for (let a = 0; a < duration; a += chunk) {
    const b = Math.min(duration, a + chunk);
    signal?.throwIfAborted();
    const window = await decode(file, a - pad, b + pad, CAPTION_CUT, timing, { signal });
    if (window.frames.length < 2) continue;
    const inside = t => t >= a - 1e-9 && t < b - 1e-9, stats = frameStats(window.frames);
    for (const k of shotChanges(window.frames, { sceneJump, shotMad: CUT_FRAGMENT.shot_mad }, stats)) if (inside(window.times[k])) shots.push(window.times[k]);
    for (const e of stepEvents(window, band, CAPTION_CUT)) if (inside(e.source_seconds)) captions.push(e);
    window.times.forEach((t, k) => { if (inside(t)) levels.push([t, stats.mean[k]]); });
  }
  levels.sort((x, y) => x[0] - y[0]);
  // The series runs from the file's first to its last frame: an opening fade-up
  // or a closing fade-out is a dip open on that side.
  const times = levels.map(l => l[0]), dips = lumaDips(levels.map(l => l[1]), times, DIP, { fileStart: true, fileEnd: true })
    .map(d => ({ start_seconds: times[d.start], min_seconds: times[d.min], end_seconds: d.end_seconds, ref_luma: d.ref, min_luma: d.min_luma }));
  return { shotTimes: [...new Set(shots)].sort((x, y) => x - y), captionEvents: captions.sort((x, y) => x.source_seconds - y.source_seconds), dips };
}

// ---------------------------------------------------------------- phrases
// Phrase refinement on the energy envelope. asr.mjs splits whisper tokens at
// punctuation only; under loud music the clean retry often separates clauses
// with a space instead ("对不起了 周年庆…"), and a transcript file keeps no token
// times, so the split is made here where the energy is known:
//   - whitespace (ASCII or U+3000) between two CJK characters is a phrase
//     boundary like punctuation; the boundary time is the energy gap nearest
//     the space's text position (± search_fraction of the phrase), at least
//     gap_db below the phrase median. Without such a gap the phrase is kept whole.
//     A space next to Latin letters or digits ("Bossin 素颜霜") is a word space, not a boundary.
//   - a pause inside a phrase splits it when it is at least pause_seconds long
//     and pause_db below the phrase median throughout. Measured on four real
//     talking-head sources (zh, music under voice): dips inside continuous
//     speech reached 0.22 s at −15 dB and 0.32 s at −12 dB, so the threshold
//     is above both. The text of such a split is divided by time
//     (text_split_estimated: true): there is no separator to say where.
export const PHRASE_SPLIT = Object.freeze({ edge_seconds: 0.1, search_fraction: 0.25, gap_db: 6, pause_db: 15, pause_seconds: 0.25 });
const CJK = /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u;
const visible = text => text.replace(/[\s　]/g, '').length;

export function splitPhrases(phrases, energy, p = PHRASE_SPLIT) {
  const out = [];
  phrases.forEach((ph, source) => {
    const local = energy ? splitOne(ph, energy, p) : [{ start: ph.start, end: ph.end, text: ph.text }];
    for (const q of local) {
      out.push({ ...q, ...(ph.text_reliable === false ? { text_reliable: false } : {}), ...(local.length > 1 ? { split_from: source } : {}) });
    }
  });
  return out.map((q, index) => ({ index, ...q }));
}

function splitOne(ph, energy, p) {
  const w = energy.window_seconds, base = energy.start_seconds, values = energy.values_db, t = i => round6(base + i * w);
  const whole = [{ start: ph.start, end: ph.end, text: ph.text }];
  const i0 = Math.max(0, Math.ceil((ph.start - base) / w - 1e-6)), i1 = Math.min(values.length, Math.floor((ph.end - base) / w + 1e-6));
  if (i1 - i0 < 10) return whole;
  const level = [...values.slice(i0, i1)].sort((x, y) => x - y)[(i1 - i0) >> 1];
  const lo = Math.ceil((ph.start + p.edge_seconds - base) / w - 1e-6), hi = Math.floor((ph.end - p.edge_seconds - base) / w + 1e-6);
  // The lowest window in [from, to) (indices inside the phrase edges), widened while ≤ it + 6 dB; null unless gap_db below the median.
  const gapIn = (from, to) => {
    let m = -1;
    for (let i = Math.max(lo, from); i < Math.min(hi, to); i++) if (m < 0 || values[i] < values[m]) m = i;
    if (m < 0 || values[m] > level - p.gap_db) return null;
    let a = m, b = m;
    while (a - 1 >= lo && values[a - 1] <= values[m] + 6) a--;
    while (b + 1 < hi && values[b + 1] <= values[m] + 6) b++;
    return { from: t(a), to: t(b + 1), next: b + 1 };
  };
  // 1. whitespace between CJK characters
  const pieces = [], parts = ph.text.split(/([\s\u3000]+)/), total = visible(ph.text), duration = ph.end - ph.start;
  let current = { start: ph.start, text: '' }, consumed = 0, cursor = lo;
  for (let k = 0; k < parts.length; k++) {
    const part = parts[k];
    if (k % 2 === 0) { current.text += part; consumed += visible(part); continue; }
    const before = parts[k - 1].at(-1), after = parts[k + 1]?.[0];
    const at = ph.start + duration * consumed / total, reach = duration * p.search_fraction;
    const gap = before && after && CJK.test(before) && CJK.test(after)
      ? gapIn(Math.max(cursor, Math.floor((at - reach - base) / w)), Math.ceil((at + reach - base) / w)) : null;
    if (!gap) { current.text += part; continue; }
    pieces.push({ ...current, end: gap.from, split_by: 'whitespace' });
    current = { start: gap.to, text: '' };
    cursor = gap.next;
  }
  pieces.push({ ...current, end: ph.end, ...(pieces.length ? { split_by: 'whitespace' } : {}) });
  // 2. long pauses inside each piece; the text is divided by time
  const result = [];
  for (const piece of pieces) {
    const a = Math.max(lo, Math.ceil((piece.start + p.edge_seconds - base) / w - 1e-6)), b = Math.min(hi, Math.floor((piece.end - p.edge_seconds - base) / w + 1e-6));
    const runs = [];
    for (let i = a, start = -1; i <= b; i++) {
      const quiet = i < b && values[i] <= level - p.pause_db;
      if (quiet && start < 0) start = i;
      if (!quiet && start >= 0) { if ((i - start) * w >= p.pause_seconds - 1e-9) runs.push([start, i]); start = -1; }
    }
    const chars = [...piece.text.trim()], span = piece.end - piece.start;
    let from = piece.start, taken = 0;
    for (const [ra, rb] of runs) {
      const cut = Math.round(chars.length * (t(ra) - piece.start) / span);
      if (cut <= taken || cut >= chars.length) continue;
      result.push({ start: from, end: t(ra), text: chars.slice(taken, cut).join('').trim(), split_by: 'energy', text_split_estimated: true });
      from = t(rb); taken = cut;
    }
    const text = chars.slice(taken).join('').trim();
    result.push({ start: from, end: piece.end, text, ...(taken ? { split_by: 'energy', text_split_estimated: true } : piece.split_by ? { split_by: piece.split_by } : {}) });
  }
  return result.length > 1 ? result : whole;
}

async function phrasesFrom({ media, mediaSha, transcript, asr, lang, clean, signal }) {
  if (transcript) {
    const doc = JSON.parse(await fs.readFile(transcript, 'utf8'));
    if (doc.schema !== TRANSCRIPT_SCHEMA) throw new Error(`Transcript must be ${TRANSCRIPT_SCHEMA}`);
    if (doc.media?.sha256 && doc.media.sha256 !== mediaSha) throw new Error('Transcript was made from a different file (media.sha256 differs)');
    return { source: 'transcript', transcript: { path_basename: path.basename(transcript), engine: doc.engine ?? null, choice_reason: doc.choice_reason ?? null },
      phrases: doc.phrases ?? [], segments: doc.segments ?? [] };
  }
  if (!asr) return { source: 'none', note: 'No transcript given and --asr not set: phrases are empty, so suggest-cuts can only work from beat time ranges and has no semantic boundaries.', phrases: [], segments: [] };
  const tmp = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'creative-analyze-'));
  try {
    const out = path.join(tmp, 'transcript.json');
    await transcribe(media, out, { lang, clean, signal });
    const doc = JSON.parse(await fs.readFile(out, 'utf8'));
    return { source: 'asr', transcript: { engine: doc.engine, language: doc.language, chosen_attempt: doc.chosen_attempt, choice_reason: doc.choice_reason, attempts: doc.attempts },
      phrases: doc.phrases, segments: doc.segments };
  } finally {
    await fs.rm(tmp, { recursive: true, force: true });
  }
}

export function parseAnalyzeArgs(argv) {
  const [media, output, ...rest] = argv;
  if (!media || !output || media.startsWith('--') || output.startsWith('--')) throw new Error('analyze needs MEDIA and NEW_OUT.json');
  const options = { asr: false, lang: 'zh', clean: 'auto' };
  for (let i = 0; i < rest.length; i++) {
    const flag = rest[i], value = rest[i + 1];
    if (flag === '--asr') { options.asr = true; continue; }
    if (value === undefined) throw new Error(`Option ${flag} needs a value`);
    if (flag === '--transcript') options.transcript = value;
    else if (flag === '--caption-band' && /^[\d.]+:[\d.]+$/.test(value)) { const [top, bottom] = value.split(':').map(Number); options.captionBand = { top, bottom }; }
    else if (flag === '--scene-threshold' && /^[\d.]+$/.test(value)) options.sceneThreshold = Number(value);
    else if (flag === '--lang') options.lang = value;
    else if (flag === '--clean') options.clean = value;
    else throw new Error(`Bad analyze option ${flag}`);
    i++;
  }
  if (options.asr && options.transcript) throw new Error('Use either --transcript or --asr, not both');
  return { media, output, options };
}

export async function analyzeFootage(media, output, { transcript, asr = false, lang = 'zh', clean = 'auto', captionBand: bandOption, sceneThreshold = SCAN.scene_threshold, decode } = {}) {
  if (!output.endsWith('.json')) throw new Error('Analysis output must be a .json file');
  if (await fs.lstat(output).then(() => true, () => false)) throw new Error(`Output already exists: ${output}`);
  if (!(sceneThreshold > 0 && sceneThreshold < 1)) throw new Error('Scene threshold must be between 0 and 1 (exclusive)');
  const band = captionBand(bandOption);
  const info = await ffprobeJson(media), picture = pictureStream(info);
  if (!picture) throw new Error('Media has no picture stream');
  const duration = Number(info.format?.duration);
  if (!(duration > 0)) throw new Error('Media duration unknown');
  const timing = await sourceTiming(media), frameRate = probedFrameRate(info);
  const rate = frameRate ? (([num, den]) => ({ num: Number(num), den: Number(den) }))(frameRate.split('/')) : null;
  const videoDuration = Number(picture.stream.duration) || duration;
  const frameCount = rate ? Math.round(videoDuration * rate.num / rate.den) : null;
  const mediaSha = await digest(media);

  const audios = info.streams.filter(s => s.codec_type === 'audio');
  const origin = earliestStart(info), audioStart = streamStart(audios[0]);
  // Media time of the first decoded audio sample. Energy and loudness are
  // decoded from it (their start_seconds); ASR and transcript times count from
  // it too (asr.mjs decodes the audio alone), so phrases are shifted by it.
  const audioOffset = audioStart && origin ? audioStart.seconds - origin.seconds : 0;
  const toMedia = list => audioOffset ? list.map(p => ({ ...p, start: round6(p.start + audioOffset), end: round6(p.end + audioOffset) })) : list;
  // The four readers run in parallel; the first failure aborts the others
  // (their ffmpeg / whisper children are killed) and is rethrown once all have
  // settled, so temp files are gone and the CLI exits promptly.
  const controller = new AbortController(), { signal } = controller;
  let failure = null;
  const task = promise => Promise.resolve(promise).catch(error => { if (!failure) { failure = error; controller.abort(error); } throw error; });
  const settled = await Promise.allSettled([
    task(scanVideo(media, { timing, duration, band, sceneThreshold, decode, signal })),
    task(audios.length ? energyEnvelope(media, 0, audioOffset, signal) : null),
    task(audios.length ? loudnessSeries(media, 0, audioOffset, signal) : null),
    task(audios.length ? phrasesFrom({ media, mediaSha, transcript, asr, lang, clean, signal }) : { source: 'none', note: 'Media has no audio stream.', phrases: [], segments: [] }),
  ]);
  if (failure) throw failure;
  const [scan, energy, loudness, words] = settled.map(s => s.value);
  const shots = buildShots(scan.shotTimes, { rate, duration: videoDuration, frameCount });
  const phrases = splitPhrases(toMedia(words.phrases), energy).map(p => ({ ...p,
    ...(loudness ? { lufs: integratedLoudness(loudness.series, p.start, p.end), true_peak_dbtp: truePeak(loudness.series, p.start, p.end) } : {}) }));
  const analysis = {
    schema: ANALYSIS_SCHEMA,
    media: { path_basename: path.basename(media), sha256: mediaSha, duration: round6(duration), video_duration: round6(videoDuration), start_seconds: round6(timing.start),
      frame_rate: frameRate, fps: rate ? round(rate.num / rate.den, 6) : null, frame_count: frameCount, width: picture.stream.width, height: picture.stream.height,
      has_audio: audios.length > 0,
      ...(rate ? {} : { frame_rate_note: 'No trustworthy constant frame rate (variable frame rate or a picture stream that does not start at media time 0): frame numbers are omitted, times are decoded frame times.' }) },
    time_base: 'All times (shots, captions, dips, phrases, segments, energy, loudness) are media seconds (stream time − earliest stream start), the time EditDocument source_in_seconds uses. ASR/transcript times count from the first decoded audio sample and are shifted by audio_offset_seconds (audio stream start − earliest stream start) into media time; energy and loudness start there (start_seconds). Frame n spans [n / fps, (n + 1) / fps); its midpoint (n + 0.5) / fps is the stable cut time.',
    audio_offset_seconds: round6(audioOffset),
    shots: {
      method: `full-frame grey difference (cut-fragments.mjs shotChanges): MAD ≥ ${CUT_FRAGMENT.shot_mad} and (MAD jump ≥ ${round6(sceneThreshold * 100)} or mean step ≥ ${CUT_FRAGMENT.shot_mad}); frames scaled to short edge ${CAPTION_CUT.analysis_short_edge}`,
      scene_threshold: sceneThreshold, list: shots },
    captions: {
      method: 'burned-captions.mjs stepEvents over the whole file (frame-difference step heuristic on the caption band, not OCR); kind "shot" = the band stepped together with the full frame',
      band, changes: scan.captionEvents.map(e => ({ source_seconds: round6(e.source_seconds), ...(rate ? { frame: frameOf(e.source_seconds, rate) } : {}),
        frame_mid_seconds: round6(e.frame_mid_seconds), kind: e.kind, line_share: e.line_share, glyph_share: e.glyph_share, rest_mad: e.rest_mad })) },
    // start = first darkened frame, end = first recovered frame (exclusive), min = darkest.
    dips: { method: DIP_METHOD, thresholds: { ...DIP }, list: scan.dips.map(d => ({
      ...(rate ? { start_frame: frameOf(d.start_seconds, rate), min_frame: frameOf(d.min_seconds, rate), end_frame: frameOf(d.end_seconds, rate) } : {}),
      start_seconds: round6(d.start_seconds), min_seconds: round6(d.min_seconds), end_seconds: round6(d.end_seconds), ref_luma: d.ref_luma, min_luma: d.min_luma })) },
    speech: { source: words.source, ...(words.note ? { note: words.note } : {}), ...(words.transcript ? { transcript: words.transcript } : {}),
      caveat: 'ASR phrase times come from whisper token timestamps (median error ~0.1 s, outliers up to seconds); they nominate boundaries, energy valleys and listening confirm them.',
      phrases, segments: toMedia(words.segments) },
    energy,
    loudness: loudness ? { target_lufs: TARGET_LUFS, integrated_lufs: loudness.integrated_lufs, true_peak_dbtp: loudness.true_peak_dbtp,
      volume_for_target: volumeFor(loudness.integrated_lufs), series: loudness.series } : null,
  };
  await fs.writeFile(output, JSON.stringify(analysis) + '\n', { flag: 'wx' });
  return { status: 'analyzed', output, duration: analysis.media.duration, frame_rate: frameRate, shots: shots.length, caption_changes: analysis.captions.changes.length, dips: analysis.dips.list.length,
    phrases: phrases.length, speech_source: words.source, integrated_lufs: analysis.loudness?.integrated_lufs ?? null };
}
