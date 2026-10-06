// QA: clicks at audio cut points of a rendered file (0.8.0). A click is a
// waveform discontinuity: its second difference x[n] − 2x[n−1] + x[n−2] is as
// large as the step itself, while for smooth content it shrinks with
// (2πf/rate)² (440 Hz at 48 kHz: 0.003 of the amplitude). Per cut point the
// largest |second difference| within ±10 ms is compared with the largest one
// in the 50 ms on either side of that window (the same programme without the
// cut). Thresholds were measured (README 剪辑点音频).
import { spawn } from 'node:child_process';
import { mediaTool } from './media-analysis.mjs';

export const CLICK_RATE = 48000;
export const CLICK_WINDOW_SECONDS = 0.010; // ± around the cut
export const CLICK_CONTEXT_SECONDS = 0.050; // reference ring on each side of the window
// Warn when the window peak is at least CLICK_RATIO × the context peak and at
// least CLICK_FLOOR (linear full scale, −34 dBFS) in absolute terms: twice the
// largest second difference two 4 ms declick ramps meeting at a cut can make at
// full scale (2/192 at 48 kHz).
export const CLICK_RATIO = 6;
export const CLICK_FLOOR = 0.02;

// Audible cut points: every start and end of an audible item strictly inside
// (0, duration), one entry per distinct output time with every item there.
export function audioCutPoints(doc, audible, duration) {
  const fps = doc.canvas.fps, points = new Map();
  for (const item of audible) {
    for (const [frame, edge] of [[item.start_frame, 'in'], [item.start_frame + item.frames, 'out']]) {
      const time = frame / fps;
      if (time <= 0 || time >= duration) continue;
      if (!points.has(frame)) points.set(frame, { time, frame, items: [] });
      points.get(frame).items.push({ item_id: item.id, edge });
    }
  }
  return [...points.values()].sort((a, b) => a.frame - b.frame);
}

const secondDifference = (x, n) => Math.abs(x[n] - 2 * x[n - 1] + x[n - 2]);
const peakOf = (x, from, to) => {
  let peak = 0;
  for (let n = Math.max(2, from); n < Math.min(x.length, to); n++) peak = Math.max(peak, secondDifference(x, n));
  return peak;
};
// Score of one cut in mono samples x whose first sample is at `start` seconds.
export function clickScore(x, rate, start, cut) {
  const at = s => Math.round((s - start) * rate);
  const window = [at(cut - CLICK_WINDOW_SECONDS), at(cut + CLICK_WINDOW_SECONDS)];
  const peak = peakOf(x, ...window);
  const context = Math.max(peakOf(x, at(cut - CLICK_WINDOW_SECONDS - CLICK_CONTEXT_SECONDS), window[0]),
    peakOf(x, window[1], at(cut + CLICK_WINDOW_SECONDS + CLICK_CONTEXT_SECONDS)));
  const ratio = peak / Math.max(context, 1e-9);
  return { peak, context, ratio, click: peak >= CLICK_FLOOR && ratio >= CLICK_RATIO };
}

// Scores of every audible cut point of a rendered file. One sequential decode
// of the whole audio track (mono, 48 kHz), not one seek per cut: input -ss on
// an AAC track lands up to one 1024-sample frame early (measured, ffmpeg 9.0.1),
// which would move a click out of its ±10 ms window. Each cut is scored as soon
// as its samples have arrived and only the samples still needed are kept.
// audioOffset: output time of the first decoded sample (audio stream start
// minus video stream start).
export function cutPointClicks(file, points, { audioOffset = 0, timeout = 600000 } = {}) {
  const span = CLICK_WINDOW_SECONDS + CLICK_CONTEXT_SECONDS, pending = [...points].sort((a, b) => a.time - b.time), results = [];
  if (!pending.length) return Promise.resolve(results);
  const sampleOf = t => Math.round((t - audioOffset) * CLICK_RATE);
  return new Promise((resolve, reject) => {
    const child = spawn(mediaTool('ffmpeg'), ['-v', 'error', '-nostdin', '-i', file, '-vn', '-sn', '-dn', '-ac', '1', '-ar', String(CLICK_RATE), '-f', 'f32le', '-']);
    let buffer = new Float32Array(0), base = 0, carry = Buffer.alloc(0), stderr = '', settled = false;
    const finish = error => {
      if (settled) return;
      settled = true; clearTimeout(timer);
      if (child.exitCode === null) child.kill();
      error ? reject(error) : resolve(results);
    };
    const timer = setTimeout(() => finish(new Error(`Audio decode for click analysis timed out: ${file}`)), timeout);
    const score = final => {
      while (pending.length) {
        const point = pending[0], from = Math.max(0, sampleOf(point.time - span)), to = sampleOf(point.time + span);
        if (!final && base + buffer.length < to) break;
        pending.shift();
        // The ±10 ms window must lie inside the decoded audio: a cut past the
        // end of the audio (or before its start) cannot be judged.
        const end = base + buffer.length;
        if (sampleOf(point.time - CLICK_WINDOW_SECONDS) < 0 || sampleOf(point.time + CLICK_WINDOW_SECONDS) > end) {
          results.push({ ...point, unknown: `outside the decoded audio (${round(audioOffset, 3)}–${round(audioOffset + end / CLICK_RATE, 3)} s)` });
          continue;
        }
        const first = Math.max(from, base);
        results.push({ ...point, ...clickScore(buffer.subarray(first - base, Math.max(first - base, to - base)), CLICK_RATE, audioOffset + first / CLICK_RATE, point.time) });
      }
      const keep = pending.length ? Math.max(0, sampleOf(pending[0].time - span)) : Infinity;
      const drop = Math.min(buffer.length, Math.max(0, keep - base));
      if (drop) { buffer = buffer.slice(drop); base += drop; }
      if (!pending.length) finish();
    };
    child.stdout.on('data', chunk => {
      const bytes = carry.length ? Buffer.concat([carry, chunk]) : chunk, usable = bytes.length - bytes.length % 4;
      carry = Buffer.from(bytes.subarray(usable));
      const incoming = new Float32Array(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + usable));
      const merged = new Float32Array(buffer.length + incoming.length);
      merged.set(buffer); merged.set(incoming, buffer.length);
      buffer = merged;
      score(false);
    });
    child.stderr.on('data', chunk => { stderr += chunk; });
    child.on('error', finish);
    child.on('close', code => {
      if (settled) return;
      if (code !== 0) return finish(new Error(`Audio decode for click analysis failed (${code}): ${stderr.trim()}`));
      score(true); // Cuts closer to the end than the context ring: scored on what exists.
    });
  });
}

const round = (value, digits = 4) => Math.round(value * 10 ** digits) / 10 ** digits;
const db = value => value > 0 ? round(20 * Math.log10(value), 1) : null;
// The QA check (category audio) from scored cut points.
// Any click → warn; else any point that could not be judged (outside the
// decoded audio) → unknown; pass only when every point was judged.
export function judgeClicks(scored) {
  const clicks = scored.filter(s => s.click), unknown = scored.filter(s => s.unknown);
  const where = list => list.map(c => `${c.time.toFixed(3)} s (${c.items.map(i => `${i.item_id} ${i.edge}`).join(', ')})${c.unknown ? ` ${c.unknown}` : ''}`).join('; ');
  const measured = { method: 'second-difference peak within ±10 ms of each audible cut vs the 50 ms on either side (mono 48 kHz decode of the rendered file)',
    window_seconds: CLICK_WINDOW_SECONDS, context_seconds: CLICK_CONTEXT_SECONDS, ratio_threshold: CLICK_RATIO, floor: CLICK_FLOOR,
    cut_points: scored.map(s => s.unknown ? { time_seconds: round(s.time, 6), items: s.items, click: null, unknown: s.unknown }
      : { time_seconds: round(s.time, 6), items: s.items, peak: round(s.peak, 5), context: round(s.context, 5), ratio: round(s.ratio, 2), peak_dbfs: db(s.peak), click: s.click }) };
  if (!scored.length) return { status: 'not_applicable', observation: 'No audible cut point inside the render.', measured };
  const unchecked = unknown.length ? ` ${unknown.length} of ${scored.length} cut point(s) were not checked: ${where(unknown)}.` : '';
  return { status: clicks.length ? 'warn' : unknown.length ? 'unknown' : 'pass', measured,
    observation: clicks.length
      ? `${clicks.length} of ${scored.length} audible cut point(s) show a waveform discontinuity (second-difference peak ≥ ${CLICK_RATIO}× its surroundings and ≥ ${CLICK_FLOOR}): ${where(clicks)}. Listen at these times; percussive or noisy content right at a cut can also trigger this.${unchecked}`
      : unknown.length ? `No click at the ${scored.length - unknown.length} analysed cut point(s), but the check is incomplete.${unchecked}`
        : `No click at ${scored.length} audible cut point(s) (second-difference peak below ${CLICK_RATIO}× its surroundings or below ${CLICK_FLOOR}).`,
    ...(clicks.length ? { refs: clicks.flatMap(c => c.items.map(i => ({ time_seconds: round(c.time, 6), item_id: i.item_id }))) } : {}) };
}

// The QA check of a rendered file: judgeClicks of cutPointClicks; a decode that
// fails or times out makes it unknown (the observation says why) instead of
// failing the whole QA run.
export function clickCheck(file, points, options) {
  return cutPointClicks(file, points, options).then(judgeClicks, error => {
    const reason = error.message.slice(0, 300);
    return { status: 'unknown', observation: `Click analysis could not run on ${points.length} audible cut point(s): ${reason}`, measured: { error: reason } };
  });
}
