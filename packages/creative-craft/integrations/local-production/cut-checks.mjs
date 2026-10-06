import path from 'node:path';
import { mapLimit } from './media-analysis.mjs';
import { CAPTION_CUT, TIME_EPS, captionCutCheck, cutPoints, decodeWindow, documentSeconds, round6, sourceTimings } from './burned-captions.mjs';
import { fragmentCutCheck } from './cut-fragments.mjs';
import { captionSpeechCheck } from './caption-speech.mjs';

// One pass over the SOURCE around every video item's in/out point for all
// cut-point checks (burned-in captions, adjacent-shot fragments). Each cut point
// is decoded once, over the union of the ranges the checks need, and each check
// judges the frames of its own range; each source file is probed once. A decode
// failure makes the point unknown for every check, a check's own failure only
// for that check.
//
// A check (captionCutCheck, fragmentCutCheck, captionSpeechCheck) provides
// measured (method and thresholds), none (observation without cut points),
// range(point) → [from, to] source seconds, analyse(point, window, fps, range)
// → result fields, and summary(n) → texts for summarizeCutChecks (n: the cut
// points it applies to). Optionally applies(point) → false with skip(point) →
// result fields: such points are not decoded for it, never unknown, and not
// counted (result not_applicable).
const within = (window, [from, to]) => {
  const keep = window.times.flatMap((t, k) => t >= from - TIME_EPS && t < to ? [k] : []);
  return { ...window, frames: keep.map(k => window.frames[k]), times: keep.map(k => window.times[k]) };
};

// accept(entry, rules) → { by, option } or null: a warned finding whose cut
// rules (check.rulesOf) a recorded edit decision accepted becomes 'accepted'.
export async function runCutChecks(doc, root, checks, { sampleAt = () => null, decode = decodeWindow, accept = null } = {}) {
  const fps = doc.canvas.fps, assets = new Map(doc.assets.map(a => [a.id, a]));
  const points = cutPoints(doc), timingOf = sourceTimings();
  if (!points.length) return checks.map(check => ({ status: 'not_applicable', observation: check.none, measured: { ...check.measured, points: [] } }));
  const applies = (check, point) => check.applies ? check.applies(point) : true;
  const results = await mapLimit(points, CAPTION_CUT.concurrency, async point => {
    const file = path.join(root, assets.get(point.item.asset_id).file), active = checks.map(check => applies(check, point));
    const ranges = checks.map((check, i) => active[i] ? check.range(point) : null), used = ranges.filter(Boolean);
    // Reported in the document's terms: source_seconds is the value the document
    // holds (what an edit changes; suggestions and shifts are based on it). A
    // corrected in-point (see cutPoints) also lists the time the render plays,
    // compiled_source_seconds, and the in-point the source_frame it was corrected to.
    const compiled = 'document_source_seconds' in point ? { compiled_source_seconds: round6(point.source_seconds) } : {};
    const frame = 'source_frame' in point ? { source_frame: point.source_frame } : {};
    const entry = { item_id: point.item.id, edge: point.edge, source_seconds: round6(documentSeconds(point)), ...compiled, ...frame, output_seconds: round6(point.output_frame / fps) };
    const unknown = error => ({ ...entry, result: 'unknown', error: error.message.slice(0, 200) });
    const skipped = (check, i) => active[i] ? null : { ...entry, result: 'not_applicable', ...check.skip(point) };
    if (!used.length) return checks.map(skipped);
    let window;
    try {
      window = await decode(file, Math.min(...used.map(r => r[0])), Math.max(...used.map(r => r[1])), CAPTION_CUT, await timingOf(file));
    } catch (error) {
      return checks.map((check, i) => skipped(check, i) ?? unknown(error));
    }
    return checks.map((check, i) => {
      if (!active[i]) return skipped(check, i);
      try {
        return { ...entry, ...check.analyse(point, within(window, ranges[i]), fps, ranges[i]) };
      } catch (error) {
        return unknown(error);
      }
    });
  });
  return checks.map((check, i) => {
    const entries = results.map(r => {
      const e = r[i], ok = e.result === 'warn' && accept && check.rulesOf ? accept(e, check.rulesOf(e)) : null;
      return ok ? { ...e, result: 'accepted', accepted: ok } : e;
    }), counted = entries.filter(e => e.result !== 'not_applicable');
    return { ...summarizeCutChecks(counted, { ...check.summary(counted.length), sampleAt }), applicable: counted.length, measured: { ...check.measured, points: entries } };
  });
}

// Status, observation and refs of one cut-point check. Any warn → warn;
// otherwise any point that could not be checked → unknown (the observation
// names the unchecked points and why); pass only when every cut point was
// analysed and none warned. refs point at the warned cut points in the render.
// note(entries), when the check has one, is appended to the observation (facts
// that are not warnings but worth a look).
export function summarizeCutChecks(entries, { scope, finding, describe, warned: warnedText, pass, note = () => '', sampleAt = () => null }) {
  const warned = entries.filter(e => e.result === 'warn'), unknown = entries.filter(e => e.result === 'unknown');
  const status = warned.length ? 'warn' : unknown.length ? 'unknown' : 'pass';
  const unchecked = unknown.length ? ` ${unknown.length} of ${entries.length} cut point(s) were not checked (${unknown.map(e => `${e.item_id} ${e.edge}`).join(', ')}): ${[...new Set(unknown.map(e => e.error))].join('; ')}.` : '';
  const accepted = entries.filter(e => e.result === 'accepted');
  const observation = warned.length ? warnedText(warned.length, warned.map(describe).join('; '), unchecked)
    : unknown.length ? `No ${finding} found at the ${entries.length - unknown.length} analysed point(s) of ${scope}, but the check is incomplete.${unchecked}`
      : accepted.length ? `No open ${finding} at ${scope}: each one found is accepted by a recorded edit decision.` : pass;
  const decided = accepted.length ? `${accepted.length} finding(s) accepted by a recorded edit decision (${accepted.map(e => `${e.item_id} ${e.edge}-point: ${e.accepted.option} by ${e.accepted.by}`).join(', ')}).` : '';
  const extra = [note(entries), decided].filter(Boolean).join(' ');
  const refs = warned.map(e => {
    const sample = sampleAt(e);
    return { time_seconds: e.output_seconds, item_id: e.item_id, ...(sample ? { sample_id: sample } : {}) };
  });
  return { status, observation: extra ? `${observation} ${extra}` : observation, ...(refs.length ? { refs } : {}) };
}

// The render-qa cut-point checks from one decode per cut point. phrasesFor
// (point → ASR phrases of its asset, or null) adds caption-speech-sync; without
// it that check is not run (speech is null).
export async function cutPointChecks(doc, root, { band, sceneThreshold, sampleAt, decode, phrasesFor = null, accept = null } = {}) {
  const checks = [{ ...captionCutCheck(band), rulesOf: () => ['caption'] },
    { ...fragmentCutCheck(sceneThreshold), rulesOf: e => e.kind === 'dip' ? ['dip'] : ['shot', ...(e.dip ? ['dip'] : [])] },
    ...(phrasesFor ? [captionSpeechCheck(phrasesFor, band)] : [])];
  const [burned, fragments, speech = null] = await runCutChecks(doc, root, checks, { sampleAt, decode, accept });
  return { burned, fragments, speech };
}

// Each check on its own (same pass, one check).
export const burnedCaptionCheck = async (doc, root, { band, sampleAt } = {}) => (await runCutChecks(doc, root, [captionCutCheck(band)], { sampleAt }))[0];
export const cutFragmentCheck = async (doc, root, { sceneThreshold, sampleAt } = {}) => (await runCutChecks(doc, root, [fragmentCutCheck(sceneThreshold)], { sampleAt }))[0];
