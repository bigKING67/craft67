import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { ANALYSIS_SCHEMA, analyzeFootage } from '../analyze.mjs';
import { RULES, SUGGEST_SCHEMA, beatPhrases, lowRuns, parseBeats, suggestCuts, suggestCutsFile, valleyNear } from '../suggest-cuts.mjs';
import { tempDir } from './media-fixtures.mjs';
import { run } from '../project.mjs';
import { PLAN_SCHEMA_FILE, applyCuts, applyCutsFile, parseApplyArgs, parseChoices, planFrom, specFrom } from '../apply-cuts.mjs';
import { schemaErrors } from '../json-schema.mjs';
import { FOOTAGE, footageTranscript, synthFootage } from './footage-fixture.mjs';

// An analysis document built directly: 30 fps, speech at −6 dBFS over the
// phrase spans, −40 dBFS elsewhere (or `energy` overrides per window), shots
// starting at `shots` frames, caption changes at `captions` frames, constant
// −10 LUFS momentary loudness.
function analysis({ seconds = 10, shots = [], captions = [], phrases = [], energy, frameRate = '30/1' } = {}) {
  const w = 0.02, n = Math.round(seconds / w);
  const values = Array.from({ length: n }, (_, i) => {
    const t = (i + 0.5) * w;
    return energy?.(t) ?? (phrases.some(p => t >= p.start && t < p.end) ? -6 : -40);
  });
  const fps = 30, starts = [0, ...shots];
  return {
    schema: ANALYSIS_SCHEMA,
    media: { path_basename: 'x.mp4', sha256: 'f'.repeat(64), duration: seconds, frame_rate: frameRate, fps, frame_count: seconds * fps },
    shots: { list: starts.map((f, i) => ({ index: i, start_frame: f, end_frame: starts[i + 1] ?? seconds * fps })) },
    captions: { changes: captions.map(c => [c].flat()).map(([f, kind = 'caption']) => ({ frame: f, source_seconds: f / fps, frame_mid_seconds: (f + 0.5) / fps, kind })) },
    speech: { source: 'transcript', phrases: phrases.map((p, i) => ({ index: i, ...p })) },
    energy: { window_seconds: w, start_seconds: 0, values_db: values },
    loudness: { series: { hop_seconds: 0.1, start_seconds: 0, momentary_lufs: Array(seconds * 10).fill(-10), true_peak_dbtp: Array(seconds * 10).fill(-3) } },
  };
}
const beat = (doc, b) => suggestCuts(doc, [b]).beats[0];

test('lowRuns merges quiet runs across a click and valleyNear picks the deep run nearest the anchor', () => {
  const values = Array(50).fill(-6);
  for (let i = 10; i < 20; i++) values[i] = -30; // 0.20–0.40 s
  values[14] = -12; values[15] = -12; // a 40 ms click inside
  for (let i = 30; i < 33; i++) values[i] = -28; // 0.60–0.66 s
  const energy = { window_seconds: 0.02, start_seconds: 0, values_db: values };
  const { runs } = lowRuns(energy, 0, 1);
  assert.deepEqual(runs.map(r => [r.from, r.to]), [[0.2, 0.4], [0.6, 0.66]]);
  assert.deepEqual([valleyNear(energy, 0, 1, 0.45).from, valleyNear(energy, 0, 1, 0.7).from], [0.2, 0.6]);
  // Only runs within deep_db of the floor qualify.
  values[30] = values[31] = values[32] = -25;
  assert.equal(valleyNear(energy, 0, 1, 0.7).from, 0.2);
});

test('beatPhrases: a range covers phrases mostly inside it; text beats match by character LCS', () => {
  const phrases = [{ start: 0, end: 2, text: '都2026年了，' }, { start: 2.1, end: 4, text: '谁夏天还在用粉底液上妆，' }, { start: 4, end: 5, text: '还一蹭就掉。' }];
  assert.deepEqual(beatPhrases({ id: 'a', from: 1.5, to: 5.2 }, phrases), { first: 1, last: 2 });
  assert.deepEqual(beatPhrases({ id: 'a', from: 0.9, to: 3.2 }, phrases), { first: 0, last: 1 });
  assert.deepEqual(beatPhrases({ id: 'a', from: 0.9, to: 3 }, phrases), { first: 0, last: 0 }); // 47 % of phrase 1 inside: not covered
  const match = beatPhrases({ id: 't', text: '谁夏天还用粉底液上妆 还一蹭就掉' }, phrases);
  assert.deepEqual([match.first, match.last], [1, 2]);
  assert.ok(match.match.score >= 0.9);
  assert.match(beatPhrases({ id: 't', text: '完全无关的一句话' }, phrases).error, /no phrase run matches/);
  const twice = beatPhrases({ id: 't', text: '还一蹭就掉' }, [...phrases, { start: 6, end: 7, text: '还一蹭就掉！' }]);
  assert.equal(twice.first, 2);
  assert.equal(twice.match.ambiguous_with[0].first_phrase, 3);
});

test('in-point: valley, then the shot rule moves it onto a shot change within 1 s (frame midpoint)', () => {
  const doc = analysis({ shots: [96], phrases: [{ start: 3.3, end: 5.0, text: '一句话。' }] });
  const b = beat(doc, { id: 'b', from: 3.0, to: 5.2 });
  assert.equal(b.status, 'suggested');
  assert.equal(b.in.frame, 96); // valley ends 3.3 s (frame 98); shot change at frame 96 is within 1 s after the valley frame
  assert.equal(b.in.source_seconds, 3.216667);
  assert.deepEqual(b.evidence.in.moves.map(m => m.rule), ['shot']);
  assert.equal(b.evidence.in.qa_precheck.cut_fragment, 'aligned');
});

test('in-point: a caption change within 0.5 s moves it; a change on the in frame is aligned', () => {
  const phrases = [{ start: 3.3, end: 5.0, text: '一句话。' }];
  const moved = beat(analysis({ captions: [102], phrases }), { id: 'b', from: 3.0, to: 5.2 });
  assert.equal(moved.in.frame, 102);
  assert.match(moved.evidence.in.moves[0].reason, /previous line would show/);
  assert.match(moved.notes.join(' '), /cuts 0.117 s after the energy valley/);
  assert.equal(moved.evidence.in.qa_precheck.burned_caption, 'aligned');
  // Old line disappears at 96, new line appears at 101: starting on the change (96) is aligned and not pushed on to 101; the second change is reported.
  // A 'shot' step on the in frame is held like a caption change, but the QA warns
  // on it (edge_on_shot_change): the precheck says so instead of 'aligned'.
  const onShot = beat(analysis({ captions: [[96, 'shot'], 101], phrases }), { id: 'b', from: 3.0, to: 5.2 });
  assert.equal(onShot.in.frame, 96);
  assert.equal(onShot.evidence.in.qa_precheck.burned_caption, 'warn');
  const blank = beat(analysis({ captions: [96, 101], phrases }), { id: 'b', from: 3.0, to: 5.2 });
  assert.equal(blank.in.frame, 96);
  assert.deepEqual(blank.evidence.in.opening_caption, { in_frame: 96, next_change_frame: 101, next_change_seconds: 3.366667, shown_seconds: 0.167 });
});

test('in-point exactly on a caption change with another change n + 6 frames later: reported in notes and evidence, not moved', () => {
  const phrases = [{ start: 3.3, end: 5.0, text: '一句话。' }];
  // The valley puts the in-point on frame 92, itself a caption change; the next change at 98 is 0.2 s later.
  const b = beat(analysis({ captions: [92, 98], phrases }), { id: 'b', from: 3.0, to: 5.2 });
  assert.equal(b.evidence.in.valley_frame, 92);
  assert.equal(b.in.frame, 92);
  assert.deepEqual(b.evidence.in.moves, []);
  assert.equal(b.status, 'suggested');
  assert.deepEqual(b.evidence.in.opening_caption, { in_frame: 92, next_change_frame: 98, next_change_seconds: 3.266667, shown_seconds: 0.2 });
  assert.match(b.notes.join(' '), /in-point frame 92 is a burned caption change and the caption changes again at frame 98 \(3\.266667 s\): the opening caption shows only 0\.2 s and may be the rest of the previous line/);
  // A change after the caption window (frame 108, 0.533 s after the in-point midpoint) is not reported.
  const later = beat(analysis({ captions: [92, 108], phrases }), { id: 'b', from: 3.0, to: 5.2 });
  assert.equal(later.in.frame, 92);
  assert.equal(later.evidence.in.opening_caption, undefined);
  assert.ok(!later.notes.some(n => /opening caption/.test(n)));
});

test('out-point on a caption change frame is not moved again by an earlier change within 0.5 s (no cascade): reported in notes and evidence', () => {
  // Speech ends 4.0 s; the valley puts the out at frame 126, the caption rule moves it onto the change at 121 (4.033 s, the next line).
  // The change at 108 (3.6 s) is the switch to the line being spoken: moving there would cut 0.4 s of it.
  const phrases = [{ start: 2.0, end: 4.0, text: '一句话。' }];
  const b = beat(analysis({ captions: [108, 121], phrases }), { id: 'b', from: 1.8, to: 4.2 });
  assert.equal(b.status, 'suggested');
  assert.equal(b.out.frame, 121);
  assert.deepEqual(b.evidence.out.moves.map(m => [m.rule, m.to_frame]), [['caption', 121]]);
  assert.deepEqual(b.evidence.out.closing_caption, { out_frame: 121, previous_change_frame: 108, previous_change_seconds: 3.6, shown_seconds: 0.433 });
  assert.match(b.notes.join(' '), /out-point frame 121 is a burned caption change and the caption also changed at frame 108 \(3\.6 s\): the closing caption shows only 0\.433 s/);
  assert.equal(b.evidence.out.qa_precheck.burned_caption, 'aligned');
  // Without a change on the out frame a change within 0.5 s before it still moves it.
  const single = beat(analysis({ captions: [114], phrases }), { id: 'b', from: 1.8, to: 4.2 });
  assert.equal(single.out.frame, 114);
  assert.equal(single.evidence.out.closing_caption, undefined);
});

test('dips to black: an edge inside one moves out of it when that cuts ≤ speech_tolerance; otherwise it is kept and reported', () => {
  const withDips = (doc, list) => ({ ...doc, dips: { list: list.map(([start_frame, min_frame, end_frame]) => ({ start_frame, min_frame, end_frame,
    start_seconds: start_frame / 30, min_seconds: min_frame / 30, end_seconds: end_frame / 30, ref_luma: 110, min_luma: 3 })) } });
  // In: the valley puts the in-point on frame 92; a dip [90, 95) moves it to 95 (speech starts 3.3 s, nothing cut).
  const inPhrases = [{ start: 3.3, end: 5.0, text: '一句话。' }];
  const moved = beat(withDips(analysis({ phrases: inPhrases }), [[90, 92, 95]]), { id: 'b', from: 3.0, to: 5.2 });
  assert.equal(moved.evidence.in.valley_frame, 92);
  assert.equal(moved.in.frame, 95);
  assert.deepEqual(moved.evidence.in.moves.map(m => [m.rule, m.to_frame, m.speech_cut_seconds]), [['dip', 95, 0]]);
  assert.match(moved.evidence.in.moves[0].reason, /fade up from black/);
  assert.equal(moved.evidence.in.dip, undefined);
  assert.ok(!moved.notes.some(n => /before the speech onset/.test(n)), 'a lead-in of 0.15 s is not reported');
  // A dip ending right at the speech onset: moved (no speech cut) but the lead-in is reported.
  const tight = beat(withDips(analysis({ phrases: inPhrases }), [[90, 92, 98]]), { id: 'b', from: 3.0, to: 5.2 });
  assert.equal(tight.in.frame, 98);
  assert.match(tight.notes.join(' '), /in-point dip rule leaves only 0\.0\d+ s before the speech onset .*listen to the first syllable/);
  // A dip to frame 108 (3.6 s) would cut 0.317 s of speech: kept, note and evidence, no conflict.
  const kept = beat(withDips(analysis({ phrases: inPhrases }), [[90, 98, 108]]), { id: 'b', from: 3.0, to: 5.2 });
  assert.equal(kept.status, 'suggested');
  assert.equal(kept.in.frame, 92);
  assert.deepEqual(kept.evidence.in.dip, { start_frame: 90, min_frame: 98, end_frame: 108, start_seconds: 3, end_seconds: 3.6, ref_luma: 110, min_luma: 3, kept_because: 'speech_tolerance' });
  assert.match(kept.notes.join(' '), /in-point frame 92 is inside a dip to black .*opens fading up from black; it is kept because starting at frame 108 would cut 0\.317 s of speech \(more than 0\.25 s\)/);
  // One long dark run over both edges: the in-point stays (speech), the out-point cannot end before a dip that starts before the in-point.
  const both = beat(withDips(analysis({ phrases: [{ start: 2.0, end: 4.0, text: '一句话。' }] }), [[50, 90, 130]]), { id: 'b', from: 1.8, to: 4.2 });
  assert.deepEqual([both.evidence.in.dip.kept_because, both.evidence.out.dip.kept_because], ['speech_tolerance', 'dip_starts_before_in']);
  assert.match(both.notes.join(' '), /out-point frame \d+ is inside a dip .*kept because the dip starts at or before the in-point/);
  // Out: speech ends 4.0 s, the valley puts the out-point on frame 126; a dip [123, 130) moves it to 123 (last shown frame 122).
  const outPhrases = [{ start: 2.0, end: 4.0, text: '一句话。' }];
  const out = beat(withDips(analysis({ phrases: outPhrases }), [[123, 126, 130]]), { id: 'b', from: 1.8, to: 4.2 });
  assert.equal(out.out.frame, 123);
  assert.deepEqual(out.evidence.out.moves.map(m => [m.rule, m.to_frame]), [['dip', 123]]);
  // A dip running to the end of the file has no recovered frame: the in-point stays and says why.
  const tail = beat(withDips(analysis({ seconds: 4, phrases: [{ start: 3.3, end: 3.9, text: '一句话。' }] }), [[90, 100, 120]]), { id: 'b', from: 3.0, to: 3.95 });
  assert.notEqual(tail.status, 'unmatched');
  assert.equal(tail.evidence.in.dip?.kept_because, 'no_recovered_frame');
  const outKept = beat(withDips(analysis({ phrases: outPhrases }), [[110, 120, 130]]), { id: 'b', from: 1.8, to: 4.2 });
  assert.equal(outKept.out.frame, 126);
  assert.equal(outKept.evidence.out.dip.start_frame, 110);
  assert.match(outKept.notes.join(' '), /out-point frame 126 is inside a dip to black .*ends fading out/);
});

test('in-point: flash shots after a change are skipped together', () => {
  const b = beat(analysis({ shots: [96, 98, 100], phrases: [{ start: 3.5, end: 5.0, text: '一句话。' }] }), { id: 'b', from: 3.2, to: 5.2 });
  assert.equal(b.in.frame, 100);
});

test('speech before the source shot change is a conflict with options, never a silent choice', () => {
  // Speech starts 0.4 s before the shot change at frame 90 (3.0 s); a second phrase follows a gap.
  const phrases = [{ start: 2.6, end: 3.8, text: '都2026年了，' }, { start: 4.3, end: 6.0, text: '谁夏天还在用粉底液上妆。' }];
  const doc = analysis({ shots: [90, 128], phrases });
  const b = beat(doc, { id: 'hook', from: 2.4, to: 6.2 });
  assert.equal(b.status, 'needs_decision');
  const [conflict] = b.conflicts;
  assert.equal(conflict.edge, 'in');
  assert.match(conflict.summary, /speech starts at about 2\.6 s/);
  assert.match(conflict.summary, /frame 90 \(3 s\)/);
  assert.deepEqual(conflict.options.map(o => o.id), ['keep_speech', 'cut_at_change', 'drop_first_phrase']);
  const options = Object.fromEntries(conflict.options.map(o => [o.id, o]));
  assert.ok(options.keep_speech.frame < 78); // keeps the speech, accepts the fragment
  assert.equal(options.cut_at_change.frame, 90);
  assert.equal(options.cut_at_change.clean, false); // the change falls inside speech
  assert.equal(options.drop_first_phrase.frame, 128); // next phrase, moved onto its shot change
  assert.equal(options.drop_first_phrase.clean, true);
  assert.equal(conflict.draft_uses, 'drop_first_phrase');
  assert.equal(b.in.frame, 128);
  assert.deepEqual(b.evidence.phrases.map(p => p.index), [1]);
  // The evidence is the edge the draft uses (the next phrase's anchor, valley and moves); the rules' own candidate is listed apart.
  const { in: inEvidence } = b.evidence;
  assert.equal(inEvidence.uses, 'drop_first_phrase');
  assert.equal(inEvidence.semantic_anchor_seconds, 4.3);
  assert.ok(inEvidence.energy_valley.from >= 3.8 && inEvidence.energy_valley.to <= 4.45, JSON.stringify(inEvidence.energy_valley));
  assert.deepEqual(inEvidence.moves.map(m => [m.rule, m.to_frame]), [['shot', 128]]);
  assert.ok(inEvidence.valley_frame < 128);
  assert.equal(inEvidence.rules_candidate.semantic_anchor_seconds, 2.6);
  assert.deepEqual(inEvidence.rules_candidate.moves.map(m => [m.rule, m.to_frame]), [['shot', 90]]);
  assert.equal(inEvidence.qa_precheck.cut_fragment, 'aligned');
  // The draft item of an open decision is marked explicitly (and so refused by v2 validation until resolved).
  const result = suggestCuts(doc, [{ id: 'hook', from: 2.4, to: 6.2 }, { id: 'calm', from: 4.2, to: 6.2 }]);
  const [marked, calm] = result.draft.items;
  assert.deepEqual([marked.needs_decision, marked.decisions], [true, [{ edge: 'in', draft_uses: 'drop_first_phrase', options: ['keep_speech', 'cut_at_change', 'drop_first_phrase'] }]]);
  assert.equal('needs_decision' in calm, false);
  assert.deepEqual(result.draft.needs_decision, ['hook']);
});

test('a single-phrase conflict prefers a cut at the change when a clear valley follows it', () => {
  // Words 2.6–3.2 s and 3.45–5 s in one phrase; a shot at 3.1 s (frame 93) would leave 0.5 s of the old shot.
  const energy = t => (t >= 2.6 && t < 3.2) || (t >= 3.45 && t < 5) ? -6 : -40;
  const b = beat(analysis({ shots: [93], phrases: [{ start: 2.6, end: 5, text: '对不起了 周年庆' }], energy }), { id: 'b', from: 2.4, to: 5.2 });
  const [conflict] = b.conflicts;
  assert.deepEqual(conflict.options.map(o => o.id), ['keep_speech', 'cut_at_change']);
  assert.equal(conflict.draft_uses, 'cut_at_change');
  assert.ok(b.in.frame >= 96 && b.in.frame <= 103); // inside the 3.2–3.45 s gap, after the change
  assert.match(conflict.options[1].consequence, /between words/);
  // Evidence of the chosen cut: the valley after the change, the frame it gave and every move (to the change, then from the valley).
  const evidence = b.evidence.in;
  assert.equal(evidence.uses, 'cut_at_change');
  assert.ok(evidence.energy_valley.from >= 3.2 - 1e-9 && evidence.energy_valley.to <= 3.45 + 1e-9, JSON.stringify(evidence.energy_valley));
  assert.ok(evidence.valley_frame >= 96 && evidence.valley_frame <= 103 && evidence.valley_frame <= b.in.frame);
  assert.deepEqual(evidence.moves.map(m => [m.rule, m.to_frame]), [['shot', 93]]);
  assert.equal(evidence.rules_candidate.energy_valley.to <= 2.6 + 1e-9, true);
  assert.deepEqual(evidence.rules_candidate.moves, evidence.moves);
});

test('out-point: deepest point of the valley after the last phrase, before a caption change and before a piece of the next shot', () => {
  const phrases = [{ start: 1.0, end: 3.0, text: '一句话。' }, { start: 3.5, end: 5, text: '下一句。' }];
  const range = { id: 'b', from: 0.8, to: 3.1 };
  assert.equal(beat(analysis({ phrases }), range).out.frame, 96); // flat valley 3.0–3.4 s: its middle, capped at 0.2 s after the speech → first midpoint ≥ 3.2 s
  const deeper = t => t >= 3.14 && t < 3.18 ? -50 : undefined;
  assert.equal(beat(analysis({ phrases, energy: deeper }), range).out.frame, 95); // deepest part 3.14–3.18 s (within lead_out): first midpoint ≥ 3.16 s
  const shot = beat(analysis({ phrases, energy: deeper, shots: [93] }), range); // next shot starts after the speech
  assert.equal(shot.out.frame, 93);
  assert.equal(shot.evidence.out.qa_precheck.cut_fragment, 'aligned');
  const tail = beat(analysis({ phrases, shots: [88] }), range); // 2 frames of a long next shot at the end
  assert.equal(tail.out.frame, 88);
  const caption = beat(analysis({ phrases, captions: [89] }), range);
  assert.equal(caption.out.frame, 89);
  assert.match(caption.evidence.out.moves[0].reason, /next line would flash/);
});

test('speech past a shot change at the end is an out-point conflict', () => {
  const phrases = [{ start: 1.0, end: 2.0, text: '第一句，' }, { start: 2.2, end: 4.0, text: '第二句。' }];
  const b = beat(analysis({ phrases, shots: [105] }), { id: 'b', from: 0.8, to: 4.2 }); // 3.5 s: 0.5 s of speech on a shot that runs on
  assert.equal(b.status, 'needs_decision');
  assert.equal(b.conflicts[0].edge, 'out');
  assert.deepEqual(b.conflicts[0].options.map(o => o.id), ['keep_speech', 'cut_at_change', 'drop_last_phrase']);
  assert.equal(b.conflicts[0].draft_uses, 'drop_last_phrase');
  assert.ok(b.out.frame <= 66);
  // Evidence of the out edge the draft uses: the end of phrase 0 and its valley; the rules' candidate (end of phrase 1) apart.
  assert.equal(b.evidence.out.uses, 'drop_last_phrase');
  assert.equal(b.evidence.out.semantic_anchor_seconds, 2.0);
  assert.ok(b.evidence.out.energy_valley.from >= 2.0 - 1e-9 && b.evidence.out.energy_valley.to <= 2.35 + 1e-9, JSON.stringify(b.evidence.out.energy_valley));
  assert.equal(b.evidence.out.valley_frame, b.out.frame);
  assert.equal(b.evidence.out.rules_candidate.semantic_anchor_seconds, 4.0);
  assert.deepEqual(b.evidence.phrases.map(p => p.index), [0]);
});

test('draft items run back to back, frames from the cut points, volume toward −14 LUFS', () => {
  const phrases = [{ start: 1.0, end: 2.0, text: '一。' }, { start: 4.0, end: 5.5, text: '二。' }];
  const result = suggestCuts(analysis({ phrases }), { asset_id: 'clip', beats: [{ id: 'one', from: 0.9, to: 2.1 }, { id: 'two', text: '二' }] });
  assert.equal(result.schema, SUGGEST_SCHEMA);
  const [one, two] = result.draft.items;
  assert.deepEqual([one.start_frame, two.start_frame], [0, one.frames]);
  for (const [item, b] of [[one, result.beats[0]], [two, result.beats[1]]]) {
    assert.equal(item.frames, b.out.frame - b.in.frame);
    assert.equal(item.source_in_seconds, b.in.source_seconds);
    assert.equal(item.asset_id, 'clip');
    assert.equal(item.volume, 0.631); // −10 LUFS → −14 LUFS
    assert.equal(Math.round(item.source_in_seconds * 30 * 2) % 2, 1); // a frame midpoint (n + 0.5) / 30
  }
  assert.equal(result.beats[1].match.matched_text, '二。');
});

test('without phrases the beat edges are the semantic bounds; text beats cannot match', () => {
  const doc = analysis({ energy: t => (t > 1 && t < 2) ? -6 : -40 });
  const b = beat(doc, { id: 'r', from: 0.9, to: 2.2 });
  assert.equal(b.status, 'suggested');
  assert.match(b.notes[0], /no phrases/);
  assert.equal(beat(doc, { id: 't', text: '你好' }).status, 'unmatched');
});

test('inputs are validated: frame rate, beats, ids', () => {
  assert.throws(() => suggestCuts(analysis({ frameRate: null }), [{ id: 'a', from: 0, to: 1 }]), /constant frame rate/);
  assert.throws(() => suggestCuts({ schema: 'x' }, []), /Analysis must be/);
  assert.throws(() => parseBeats([]), /non-empty/);
  assert.throws(() => parseBeats([{ id: 'a', from: 0, to: 1 }, { id: 'a', text: 'x' }]), /unique/);
  assert.throws(() => parseBeats([{ id: 'a' }]), /from, to/);
  assert.equal(RULES.shot_window, 1);
});

test('suggest-cuts on analysed synthetic footage: shot and caption changes from the media', async () => {
  const dir = await tempDir('creative-suggest-test-');
  try {
    const media = await synthFootage(path.join(dir, 'footage.mov'));
    const transcript = await footageTranscript(media, path.join(dir, 'transcript.json'));
    const analysisFile = path.join(dir, 'analysis.json'), beats = path.join(dir, 'beats.json'), out = path.join(dir, 'cuts.json');
    await analyzeFootage(media, analysisFile, { transcript });
    await fs.writeFile(beats, JSON.stringify([{ id: 'third', from: 2.5, to: 3.7 }, { id: 'second', from: 1.0, to: 3.7 }, { id: 'first', text: '第一句话' }]));
    const summary = await suggestCutsFile(analysisFile, beats, out);
    assert.deepEqual(summary.beats.map(b => b.status), ['suggested', 'needs_decision', 'suggested']);
    assert.equal(summary.status, 'needs_decision'); // the CLI summary names the open decisions
    assert.deepEqual(summary.needs_decision, [{ id: 'second', decisions: [{ edge: 'in', draft_uses: 'drop_first_phrase', options: ['keep_speech', 'cut_at_change', 'drop_first_phrase'] }] }]);
    const result = JSON.parse(await fs.readFile(out, 'utf8'));
    const [third, second, first] = result.beats;
    // Third phrase (2.6 s): valley 2.2–2.6 s, then the caption change at frame 75 (2.5 s) is within 0.5 s → in on frame 75.
    assert.equal(third.in.frame, FOOTAGE.caption_frame);
    assert.equal(third.in.source_seconds, 2.516667);
    assert.ok(third.out.source_seconds > 3.6 && third.out.source_seconds <= 3.6 + RULES.lead_out + 1 / 30); // in the silence after the tone
    // Second phrase starts 1.1 s, before the shot change at 1.5 s: a conflict, not a silent choice.
    assert.equal(second.conflicts[0].edge, 'in');
    assert.ok(second.conflicts[0].summary.includes(`frame ${FOOTAGE.shot_frame} (1.5 s)`));
    assert.equal(second.conflicts[0].draft_uses, 'drop_first_phrase');
    assert.equal(second.in.frame, FOOTAGE.caption_frame);
    // First phrase by text: in before 0.3 s, out in the 0.9–1.1 s gap, no shot change within it.
    assert.ok(first.in.source_seconds < 0.3 && first.out.source_seconds > 0.9 && first.out.source_seconds < 1.1);
    assert.equal(first.evidence.in.qa_precheck.cut_fragment, 'clear');
    await assert.rejects(suggestCutsFile(analysisFile, beats, out), /already exists/);
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
});

test('apply-cuts resolves open decisions by explicit choice only, re-lays the items and emits production-plan beats', async () => {
  const planSchema = JSON.parse(await fs.readFile(PLAN_SCHEMA_FILE, 'utf8'));
  // hook: speech starts before the shot change at frame 90 → needs_decision on the in edge (see the conflict test above).
  // The hook's out-point lies beyond the shot and dip reach of either in option (> 2.5 s), so another in choice is safe to apply.
  const phrases = [{ start: 2.6, end: 3.8, text: '都2026年了，' }, { start: 4.3, end: 7.5, text: '谁夏天还在用粉底液上妆。' }, { start: 8.8, end: 10.3, text: '还一蹭就掉。' }];
  const plan = { role: 'proof', purpose: 'Shows it stays on.', requirement: 'Complete phrases.', hard_constraints: ['keep burned subtitles'] };
  const cuts = suggestCuts(analysis({ seconds: 14, shots: [90, 128], phrases }), { asset_id: 'film', beats: [{ id: 'hook', from: 2.4, to: 7.7 }, { id: 'calm', from: 8.6, to: 10.5, ...plan }] });
  assert.deepEqual(cuts.draft.needs_decision, ['hook']);
  const calm = cuts.beats.find(b => b.id === 'calm');
  assert.deepEqual([calm.role, calm.hard_constraints], ['proof', ['keep burned subtitles']], 'plan fields pass through suggest-cuts');
  assert.deepEqual(cuts.beats[0].evidence.option_phrases.map(p => p.index), [0, 1], 'every phrase an option reaches');

  assert.throws(() => applyCuts(cuts, new Map(), planSchema), /Unresolved decision\(s\): hook\.in \(options: keep_speech, cut_at_change, drop_first_phrase; draft uses drop_first_phrase\)/);
  assert.throws(() => applyCuts(cuts, parseChoices(['hook.in=bogus']), planSchema), /unknown option \(options: keep_speech, cut_at_change, drop_first_phrase\)/);
  assert.throws(() => applyCuts(cuts, parseChoices(['hook.in=keep_speech', 'calm.out=keep_speech']), planSchema), /beat calm has no open decision on its out-point/);
  assert.throws(() => applyCuts(cuts, parseChoices(['nope.in=keep_speech']), planSchema), /no beat nope/);
  assert.throws(() => parseChoices(['hook.in=keep_speech', 'hook.in=cut_at_change']), /given twice/);
  assert.throws(() => parseChoices(['hook=keep_speech']), /BEAT\.EDGE=OPTION/);

  const keep = cuts.beats[0].conflicts[0].options.find(o => o.id === 'keep_speech');
  const applied = applyCuts(cuts, parseChoices(['hook.in=keep_speech']), planSchema);
  const [hook, calmItem] = applied.items;
  assert.equal(hook.source_in_seconds, keep.seconds);
  assert.equal(hook.frames, Math.round((cuts.beats[0].out.source_seconds - keep.seconds) * 30));
  assert.deepEqual([hook.start_frame, calmItem.start_frame], [0, hook.frames], 'back to back from frame 0');
  assert.ok(applied.items.every(i => !('needs_decision' in i) && !('decisions' in i)));
  assert.deepEqual(applied.choices.map(c => [c.beat, c.edge, c.option, c.frame, c.draft_used]), [['hook', 'in', 'keep_speech', keep.frame, 'drop_first_phrase']]);
  assert.match(applied.notes.join(' '), /hook: volume .* was measured on the draft range/);
  // Plan beats: the kept first phrase is evidence again; missing plan fields are listed, never invented.
  const [hookBeat, calmBeat] = applied.plan_beats;
  assert.deepEqual(hookBeat.selection.evidence.map(e => e.excerpt), ['都2026年了，', '谁夏天还在用粉底液上妆。']);
  assert.deepEqual([hookBeat.selection.source_start_seconds, hookBeat.source_kind, hookBeat.selection.status, hookBeat.selection.evidence[0].raw_score], [keep.seconds, 'footage', 'candidate', null]);
  assert.equal('role' in hookBeat, false);
  assert.deepEqual(applied.plan_beats_incomplete, [{ id: 'hook', missing: ['role', 'purpose', 'requirement', 'hard_constraints'] }]);
  assert.deepEqual(schemaErrors(calmBeat, planSchema.$defs.beat, planSchema), []);
  assert.deepEqual({ ...calmBeat, selection: undefined }, { id: 'calm', ...plan, duration_seconds: Math.round(calmItem.frames / 30 * 1e6) / 1e6, source_kind: 'footage', selection: undefined, generation_ref: null, locked: false });
  assert.deepEqual(calmBeat.selection.evidence.map(e => [e.modality, e.start_seconds, e.end_seconds, e.excerpt]), [['asr', 8.8, 10.3, '还一蹭就掉。']]);
  assert.match(schemaErrors({ ...calmBeat, source_kind: 'stock' }, planSchema.$defs.beat, planSchema).join(' '), /source_kind: must be one of/);
  assert.equal(applied.plan_status, 'incomplete');

  // A beat id the plan refuses (pattern ^[a-zA-Z]…) is a plan problem, not a failure: the items are still built.
  const renamed = structuredClone(cuts);
  renamed.beats[1].id = renamed.draft.items[1].id = '01_calm';
  const odd = applyCuts(renamed, parseChoices(['hook.in=keep_speech']), planSchema);
  assert.equal(odd.items.length, 2);
  assert.equal(odd.plan_status, 'invalid');
  assert.deepEqual(odd.plan_errors.map(e => e.id), ['01_calm']);
  assert.match(odd.plan_errors[0].errors.join(' '), /\$\.id: must match/);
  // A choice for a beat without a usable range is an error, not silently dropped.
  const unmatched = structuredClone(cuts);
  delete unmatched.beats[0].in; delete unmatched.beats[0].out;
  Object.assign(unmatched.beats[0], { status: 'unmatched', error: 'no usable range' });
  assert.throws(() => applyCuts(unmatched, parseChoices(['hook.in=keep_speech']), planSchema), /beat hook has no usable range \(unmatched: no usable range\)/);
  // An in choice other than the draft's when the out-point depends on the draft's in-point: refused.
  const both = structuredClone(cuts);
  both.beats[0].conflicts.push({ edge: 'out', options: [{ id: 'keep_speech', frame: both.beats[0].out.frame, seconds: both.beats[0].out.source_seconds }], draft_uses: 'keep_speech' });
  assert.throws(() => applyCuts(both, parseChoices(['hook.in=keep_speech', 'hook.out=keep_speech']), planSchema), /out-point and its options were computed after the draft's in option drop_first_phrase .*re-run suggest-cuts/);
  assert.equal(applyCuts(both, parseChoices(['hook.in=drop_first_phrase', 'hook.out=keep_speech']), planSchema).items.length, 2, 'the draft in option is fine');
  const short = structuredClone(cuts);
  short.beats[0].out.source_seconds = keep.seconds + 0.8;
  assert.throws(() => applyCuts(short, parseChoices(['hook.in=keep_speech']), planSchema), /the out-point was computed after the draft's in option/);

  // CLI file form: a new output only.
  const dir = await tempDir('creative-apply-cuts-');
  try {
    const cutsFile = path.join(dir, 'cuts.json'), out = path.join(dir, 'applied.json');
    await fs.writeFile(cutsFile, JSON.stringify(cuts));
    const { cuts: c, output, choices } = parseApplyArgs([cutsFile, out, '--choose', 'hook.in=drop_first_phrase']);
    const summary = await applyCutsFile(c, output, choices);
    assert.deepEqual([summary.status, summary.plan_status], ['applied', 'incomplete']);
    assert.match(summary.plan_beats_incomplete[0], /hook: missing role, purpose, requirement, hard_constraints \(not invented/);
    const written = JSON.parse(await fs.readFile(out, 'utf8'));
    assert.match(written.cuts.sha256, /^[0-9a-f]{64}$/);
    assert.deepEqual(written.plan_beats[0].selection.evidence.map(e => e.excerpt), ['谁夏天还在用粉底液上妆。']);
    await assert.rejects(applyCutsFile(c, output, choices), /already exists/);
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
});

test('apply-cuts writes a plan and a spec from templates, all or nothing', async () => {
  const planSchema = JSON.parse(await fs.readFile(PLAN_SCHEMA_FILE, 'utf8'));
  const fields = { role: 'proof', purpose: 'Shows it stays on.', requirement: 'Complete phrases.', hard_constraints: ['keep burned subtitles'] };
  const phrases = [{ start: 1.0, end: 2.5, text: '第一句。' }, { start: 4.0, end: 5.5, text: '第二句。' }];
  const cuts = suggestCuts(analysis({ phrases }), { asset_id: 'film', beats: [{ id: 'one', from: 0.8, to: 2.7, ...fields }, { id: 'two', from: 3.8, to: 5.7, ...fields }] });
  const applied = applyCuts(cuts, new Map(), planSchema);
  assert.equal(applied.plan_status, 'valid');
  const planHead = { schema_version: 'creative-craft.production-plan.v1', plan_id: 'demo', title: 'Demo', brief_ref: { path: 'brief.md', sha256: 'a'.repeat(64) },
    intended_use: 'test', output: { duration_seconds_target: 3, ratio: '9:16', language: 'zh-CN' }, delivery_promises: [], beats: [] };
  const plan = planFrom(planHead, applied, planSchema);
  assert.deepEqual(plan.beats.map(b => b.id), ['one', 'two']);
  assert.deepEqual(schemaErrors(plan, planSchema, planSchema), []);
  assert.throws(() => planFrom({ ...planHead, plan_id: undefined }, applied, planSchema), /does not match production-plan\.schema\.json/);
  assert.throws(() => planFrom(planHead, { ...applied, plan_status: 'invalid', plan_errors: [{ id: '1x', errors: ['$.id: must match'] }], plan_beats_incomplete: [{ id: 'two', missing: ['role'] }] }, planSchema),
    /Plan beats are invalid, so no plan is written: 1x: \$\.id: must match \| two: missing role/, 'both problems named');
  const placeholder = structuredClone(applied); placeholder.plan_beats[0].selection.asset_ref = 'ASSET_ID';
  assert.throws(() => planFrom(planHead, placeholder, planSchema), /placeholder asset ASSET_ID/);
  // Spec rules (validation injected): the applied track's media replaced, other tracks kept and noted when they run late.
  const pass = async () => {};
  const title = { id: 'title', track_id: 'v_gfx', kind: 'graphic', start_frame: 0, frames: 999 };
  const specHead = { project_id: 'demo', title: 'Demo', canvas: { width: 360, height: 640, fps: 30 }, assets: [{ id: 'film', path: '/x.mp4' }],
    tracks: [{ id: 'v_main', kind: 'video', locked: false }, { id: 'v_gfx', kind: 'video', locked: false }], items: [{ id: 'old', track_id: 'v_main', kind: 'media', asset_id: 'film' }, title] };
  const built = await specFrom(specHead, applied, pass);
  assert.deepEqual(built.spec.items.map(i => i.id), ['title', 'one', 'two']);
  assert.match(built.notes[0], /kept item\(s\) title run past the new main-track end/);
  await assert.rejects(specFrom({ ...specHead, items: [{ ...title, track_id: 'v_main' }] }, applied, pass), /non-media item\(s\) on v_main \(title\).*move them to another track/);
  await assert.rejects(specFrom({ ...specHead, items: [...specHead.items, { id: 'cap', track_id: 'c_main', kind: 'caption', text: 'x', link: { item_id: 'old', source_from: 1, source_to: 2 } }] }, applied, pass),
    /cap link to v_main media that apply-cuts replaces/);
  await assert.rejects(specFrom({ ...specHead, assets: [] }, applied, pass), /no asset film/);
  await assert.rejects(specFrom({ ...specHead, tracks: [] }, applied, pass), /no track v_main/);
  await assert.rejects(specFrom({ ...specHead, tracks: [{ id: 'v_main', kind: 'video', locked: true }] }, applied, pass), /track v_main is locked/);
  await assert.rejects(specFrom({ ...specHead, canvas: { ...specHead.canvas, fps: 25 } }, applied, pass), /canvas\.fps 25 differs from the 30 fps/);
  // Files with a real 6 s source: the spec passes createProject's own checks; a bad one writes nothing.
  const dir = await tempDir('creative-apply-write-');
  try {
    const file = name => path.join(dir, name), put = async (name, v) => { await fs.writeFile(file(name), JSON.stringify(v)); return file(name); };
    await run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=360x640:rate=30:duration=6', '-pix_fmt', 'yuv420p', file('take.mp4')]);
    const head = { ...specHead, assets: [{ id: 'film', path: file('take.mp4') }], items: [] };
    const cutsFile = await put('cuts.json', cuts), planT = await put('plan-head.json', planHead), specT = await put('spec-head.json', head);
    const parsed = parseApplyArgs([cutsFile, file('applied.json'), '--plan-template', planT, '--plan-out', file('plan.json'), '--spec-template', specT, '--spec-out', file('spec.json')]);
    const summary = await applyCutsFile(parsed.cuts, parsed.output, parsed.choices, parsed.write);
    assert.deepEqual([summary.plan, summary.spec], [file('plan.json'), file('spec.json')]);
    assert.deepEqual(JSON.parse(await fs.readFile(file('spec.json'), 'utf8')).items.map(i => i.id), ['one', 'two']);
    // A spec createProject refuses (here: an unknown item kind) is refused before anything is written.
    const invalid = await put('invalid-head.json', { ...head, items: [{ id: 'odd', track_id: 'v_gfx', kind: 'sticker', start_frame: 0, frames: 10 }] });
    await assert.rejects(applyCutsFile(cutsFile, file('applied2.json'), new Map(), { specTemplate: invalid, specOut: file('spec2.json') }), /kind|item/i);
    await assert.rejects(fs.stat(file('applied2.json')), 'nothing written when the spec is refused');
    // The notes a spec adds are in the written applied file too.
    const late = await put('late-head.json', head);
    await applyCutsFile(cutsFile, file('applied3.json'), new Map(), { specTemplate: late, specOut: file('spec3.json') });
    assert.ok(Array.isArray(JSON.parse(await fs.readFile(file('applied3.json'), 'utf8')).notes));
    await assert.rejects(applyCutsFile(cutsFile, file('a4.json'), new Map(), { planTemplate: planT, planOut: file('a4.json') }), /different files/);
    // A file that appears at an output path before placing is never replaced; everything placed is removed again.
    await fs.writeFile(file('taken.json'), 'mine');
    await assert.rejects(applyCutsFile(cutsFile, file('a5.json'), new Map(), { planTemplate: planT, planOut: file('taken.json') }), /already exists/);
    assert.equal(await fs.readFile(file('taken.json'), 'utf8'), 'mine');
    await assert.rejects(applyCutsFile(cutsFile, file('a6.json'), new Map(), { planTemplate: planT, planOut: file('missing/plan.json') }), /Output directory does not exist/);
    assert.throws(() => parseApplyArgs([cutsFile, 'o.json', '--plan-out', 'p.json']), /--plan-template and --plan-out go together/);
    assert.throws(() => parseApplyArgs([cutsFile, 'o.json', '--spec-out', 'a.json', '--spec-out', 'b.json']), /Unknown or repeated apply-cuts option --spec-out/);
    assert.throws(() => parseApplyArgs([cutsFile, 'o.json', '--plan-template', '--plan-out', 'p.json', 'x']), /Missing value for --plan-template/);
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
});

test('prefer: BEATS.json settles the conflicts up front (montage speech across shot cuts)', () => {
  // Speech starts 0.4 s before the shot change at frame 90 and ends 0.5 s after the one at frame 150.
  const phrases = [{ start: 2.6, end: 3.8, text: '如果你皮肤暗沉，' }, { start: 4.3, end: 5.5, text: '就试试它。' }];
  const doc = analysis({ shots: [90, 150], phrases });
  const plain = beat(doc, { id: 'close', from: 2.4, to: 5.7 });
  assert.equal(plain.status, 'needs_decision');
  const kept = beat(doc, { id: 'close', from: 2.4, to: 5.7, prefer: 'keep_speech' });
  assert.equal(kept.status, 'suggested');
  assert.equal(kept.prefer, 'keep_speech');
  assert.ok(kept.conflicts.length && kept.conflicts.every(c => c.draft_uses === 'keep_speech' && c.decided_by === 'prefer'));
  assert.ok(kept.in.source_seconds < 3 && kept.out.source_seconds > 5.4, 'whole speech kept');
  const cuts = suggestCuts(doc, { asset_id: 'film', beats: [{ id: 'close', from: 2.4, to: 5.7, prefer: 'keep_speech' }] });
  assert.deepEqual(cuts.draft.needs_decision, []);
  assert.equal(applyCuts(cuts, new Map(), null).items[0].frames, kept.frames, 'apply-cuts needs no --choose');
  assert.throws(() => parseBeats({ beats: [{ id: 'x', from: 0, to: 1, prefer: 'drop_first_phrase' }] }), /prefer must be one of keep_speech, cut_at_change/);
});

test('decisions: keep_speech records the rules it accepts; apply-cuts lists prefer and --choose decisions', () => {
  const phrases = [{ start: 2.6, end: 3.8, text: '如果你皮肤暗沉，' }, { start: 4.3, end: 5.5, text: '就试试它。' }];
  const doc = analysis({ shots: [90, 150], phrases });
  const plain = beat(doc, { id: 'close', from: 2.4, to: 5.7 });
  assert.deepEqual(plain.conflicts.map(c => c.options.find(o => o.id === 'keep_speech').accepts), [['shot'], ['shot']]);
  const preferred = suggestCuts(doc, { asset_id: 'film', beats: [{ id: 'close', from: 2.4, to: 5.7, prefer: 'keep_speech' }] });
  assert.ok(applyCuts(preferred, new Map(), null).decisions.every(d => d.asset_id === 'film'));
  assert.deepEqual(applyCuts(preferred, new Map(), null).decisions.map(d => [d.beat, d.edge, d.option, d.by, d.accepts]),
    [['close', 'in', 'keep_speech', 'prefer', ['shot']], ['close', 'out', 'keep_speech', 'prefer', ['shot']]]);
  const chosen = suggestCuts(doc, { asset_id: 'film', beats: [{ id: 'close', from: 2.4, to: 5.7 }] });
  const open = chosen.beats[0].conflicts.map(c => `close.${c.edge}=${c.draft_uses}`);
  const d = applyCuts(chosen, parseChoices(open), null).decisions;
  assert.ok(d.length === 2 && d.every(x => x.by === 'choice'));
  assert.ok(d.every(x => x.option === 'keep_speech' ? x.accepts.includes('shot') : Array.isArray(x.accepts) && !x.accepts.length), 'other options accept nothing');
});
