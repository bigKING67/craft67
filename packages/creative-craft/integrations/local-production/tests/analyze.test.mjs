import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { ANALYSIS_SCHEMA, PHRASE_SPLIT, analyzeFootage, buildShots, scanVideo, splitPhrases, integratedLoudness, parseAnalyzeArgs, parseEbur128Frames, rmsEnvelope, truePeak, volumeFor } from '../analyze.mjs';
import { suggestCuts } from '../suggest-cuts.mjs';
import { tempDir } from './media-fixtures.mjs';
import { FOOTAGE, footageTranscript, synthFootage, synthOffsetFootage } from './footage-fixture.mjs';

// Energy (dB) of an analysis envelope at media time t (the window containing t), read from the documented format.
const energyAt = (energy, t) => energy.values_db[Math.min(energy.values_db.length - 1, Math.max(0, Math.floor((t - energy.start_seconds) / energy.window_seconds)))];

test('rmsEnvelope gives dBFS per window and floors silence', () => {
  const samples = new Float32Array(640);
  for (let i = 320; i < 640; i++) samples[i] = i % 2 ? 0.5 : -0.5; // RMS 0.5 → −6.0 dBFS
  assert.deepEqual(rmsEnvelope(samples, 320), [-100, -6]);
});

test('parseEbur128Frames reads momentary loudness and the frame true peak (max over channels)', () => {
  const log = [
    '[Parsed_ebur128_0 @ 0x1] t: 0.0999773  TARGET:-23 LUFS    M:-120.7 S:-120.7     I: -70.0 LUFS       LRA:   0.0 LU  FTPK:  -0.5  -0.3 dBFS  TPK:  -0.5  -0.3 dBFS',
    '[Parsed_ebur128_0 @ 0x1] t: 0.199977   TARGET:-23 LUFS    M: -12.5 S:-120.7     I: -12.5 LUFS       LRA:   0.0 LU  FTPK:  -3.0  -inf dBFS  TPK:  -0.5  -0.3 dBFS',
  ].join('\n');
  assert.deepEqual(parseEbur128Frames(log), [{ t: 0.0999773, m: -120.7, tp: -0.3 }, { t: 0.199977, m: -12.5, tp: -3 }]);
});

test('integratedLoudness gates like BS.1770 and needs a full 400 ms block', () => {
  const series = { hop_seconds: 0.1, start_seconds: 0, momentary_lufs: [-80, -80, -80, -80, -10, -10, -10, -10, -25, -10], true_peak_dbtp: [-40, -40, -40, -40, -3, -2, -3, -3, -20, -1] };
  // Blocks ending at 0.5–1.0 s: −80 is below the absolute gate, −25 below the relative gate (mean − 10 LU).
  assert.equal(integratedLoudness(series, 0, 1), -10);
  assert.equal(integratedLoudness(series, 0, 0.35), null); // shorter than one block
  assert.equal(truePeak(series, 0.4, 0.7), -2);
  assert.equal(volumeFor(-10), 0.631);
  assert.equal(volumeFor(-20), 1); // never above 1
  assert.equal(volumeFor(null), null);
});

// 20 ms envelope: speech −6 dBFS, `quiet` spans at `level` dBFS.
const envelope = (seconds, quiet, level = -30) => ({ window_seconds: 0.02, start_seconds: 0,
  values_db: Array.from({ length: Math.round(seconds / 0.02) }, (_, i) => quiet.some(([a, b]) => (i + 0.5) * 0.02 >= a && (i + 0.5) * 0.02 < b) ? level : -6) });

test('splitPhrases: whitespace between CJK characters is a boundary placed at the energy gap', () => {
  const phrase = { start: 5.22, end: 7.56, text: '对不起了 周年庆重粉活动' };
  const [a, b] = splitPhrases([phrase], envelope(10, [[5.94, 6.06]]));
  assert.deepEqual([a.start, a.end, a.text, b.start, b.end, b.text], [5.22, 5.94, '对不起了', 6.06, 7.56, '周年庆重粉活动']);
  assert.deepEqual([a.split_by, a.split_from, b.index], ['whitespace', 0, 1]);
  // Full-width space too; two boundaries.
  assert.deepEqual(splitPhrases([{ start: 0, end: 2.4, text: '叫啦\u3000叫啦 真的叫啦' }], envelope(3, [[0.6, 0.7], [1.3, 1.4]])).map(q => q.text), ['叫啦', '叫啦', '真的叫啦']);
});

test('splitPhrases keeps word spaces, gapless spaces and short dips inside continuous speech', () => {
  const latin = { start: 0, end: 3, text: '这个3.0的Bossin 素颜霜在我脸上' };
  assert.equal(splitPhrases([latin], envelope(4, [[1.2, 1.3]])).length, 1);
  const noGap = { start: 0, end: 2, text: '送她来了 直播间' }; // no energy gap near the space
  assert.deepEqual(splitPhrases([noGap], envelope(3, [])).map(q => q.text), ['送她来了 直播间']);
  // A 0.22 s dip 20 dB down inside a phrase without separator: below pause_seconds, not split.
  assert.equal(splitPhrases([{ start: 0, end: 3, text: '想要快速出门讨厌蜡黄' }], envelope(4, [[1.0, 1.22]], -26)).length, 1);
  assert.ok(PHRASE_SPLIT.pause_seconds > 0.22 && PHRASE_SPLIT.pause_db >= 15);
});

test('splitPhrases splits at a long pause and marks the time-divided text', () => {
  const parts = splitPhrases([{ start: 0, end: 4, text: '一二三四五六七八' }], envelope(5, [[1.9, 2.3]], -40));
  assert.deepEqual(parts.map(q => [q.start, q.end, q.text, q.split_by, q.text_split_estimated]), [[0, 1.9, '一二三四', 'energy', true], [2.3, 4, '五六七八', 'energy', true]]);
});

test('buildShots lists frame-exact shots with frame midpoints', () => {
  const shots = buildShots([1.5, 2.5], { rate: { num: 30, den: 1 }, duration: 4, frameCount: 120 });
  assert.deepEqual(shots.map(s => [s.start_frame, s.end_frame, s.frames, s.start_mid_seconds]), [[0, 45, 45, 0.016667], [45, 75, 30, 1.516667], [75, 120, 45, 2.516667]]);
});

test('parseAnalyzeArgs accepts the documented options and refuses mixtures', () => {
  assert.deepEqual(parseAnalyzeArgs(['a.mp4', 'o.json', '--asr', '--caption-band', '0.6:0.9']).options, { asr: true, lang: 'zh', clean: 'auto', captionBand: { top: 0.6, bottom: 0.9 } });
  assert.throws(() => parseAnalyzeArgs(['a.mp4', 'o.json', '--asr', '--transcript', 't.json']), /either/);
  assert.throws(() => parseAnalyzeArgs(['a.mp4', 'o.json', '--bogus', 'x']), /Bad analyze option/);
  assert.throws(() => parseAnalyzeArgs(['a.mp4']), /MEDIA and NEW_OUT/);
});

test('analyzeFootage finds the synthetic shot change, caption change, gaps and loudness', async () => {
  const dir = await tempDir('creative-analyze-test-');
  try {
    const media = await synthFootage(path.join(dir, 'footage.mov'));
    const transcript = await footageTranscript(media, path.join(dir, 'transcript.json'));
    const out = path.join(dir, 'analysis.json');
    const result = await analyzeFootage(media, out, { transcript });
    assert.equal(result.status, 'analyzed');
    const a = JSON.parse(await fs.readFile(out, 'utf8'));
    assert.equal(a.schema, ANALYSIS_SCHEMA);
    assert.equal(a.media.frame_rate, '30/1');
    assert.equal(a.media.frame_count, 120);
    assert.match(a.media.sha256, /^[0-9a-f]{64}$/);
    assert.deepEqual(a.shots.list.map(s => s.start_frame), [0, FOOTAGE.shot_frame]);
    const captions = a.captions.changes.filter(c => c.kind === 'caption');
    assert.deepEqual(captions.map(c => c.frame), [FOOTAGE.caption_frame]);
    assert.equal(captions[0].frame_mid_seconds, 2.516667);
    assert.deepEqual(a.dips.list, [], 'a hard cut to a darker shot is not a dip');
    assert.equal(result.dips, 0);
    assert.equal(a.speech.source, 'transcript');
    assert.deepEqual(a.speech.phrases.map(p => [p.start, p.end]), FOOTAGE.speech);
    // Energy: tone around −9 dBFS, silence floored.
    assert.ok(energyAt(a.energy, 0.6) > -12 && energyAt(a.energy, 0.6) < -6);
    assert.equal(energyAt(a.energy, 1.0), -100);
    assert.equal(energyAt(a.energy, 2.4), -100);
    // The series reproduces ffmpeg's own integrated loudness of the file.
    assert.ok(Math.abs(integratedLoudness(a.loudness.series, 0, 10) - a.loudness.integrated_lufs) <= 0.5);
    assert.ok(a.speech.phrases.every(p => Number.isFinite(p.lufs)));
    await assert.rejects(analyzeFootage(media, out, { transcript }), /already exists/);
    // A transcript of another file is refused.
    const other = JSON.parse(await fs.readFile(transcript, 'utf8'));
    other.media.sha256 = '0'.repeat(64);
    await fs.writeFile(transcript, JSON.stringify(other));
    await assert.rejects(analyzeFootage(media, path.join(dir, 'b.json'), { transcript }), /different file/);
    // Without transcript or ASR the phrases are empty and the reason is recorded.
    await analyzeFootage(media, path.join(dir, 'c.json'));
    const bare = JSON.parse(await fs.readFile(path.join(dir, 'c.json'), 'utf8'));
    assert.equal(bare.speech.source, 'none');
    assert.deepEqual(bare.speech.phrases, []);
    assert.match(bare.speech.note, /--asr/);
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
});

test('analyzeFootage: an audio stream starting 0.3 s after the picture puts phrases, energy and suggested cuts on one media time', async t => {
  const dir = await tempDir('creative-analyze-offset-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const offset = 0.3, media = await synthOffsetFootage(path.join(dir, 'offset.mov'), offset);
  // The transcript counts from the first decoded audio sample (as asr.mjs does): the bursts at audio-local FOOTAGE.speech.
  const transcript = await footageTranscript(media, path.join(dir, 'transcript.json'));
  const out = path.join(dir, 'analysis.json');
  await analyzeFootage(media, out, { transcript });
  const a = JSON.parse(await fs.readFile(out, 'utf8'));
  assert.equal(a.audio_offset_seconds, offset);
  assert.match(a.time_base, /shifted by audio_offset_seconds/);
  assert.equal(a.energy.start_seconds, offset);
  assert.equal(a.loudness.series.start_seconds, offset);
  const expected = FOOTAGE.speech.map(([s, e]) => [s + offset, e + offset].map(v => Math.round(v * 1e6) / 1e6));
  assert.deepEqual(a.speech.phrases.map(p => [p.start, p.end]), expected);
  assert.deepEqual(a.speech.segments.map(p => [p.start, p.end]), expected);
  // Each phrase is loud just inside and silent just outside, on the energy's own time.
  for (const [s, e] of expected) {
    assert.ok(energyAt(a.energy, s + 0.05) > -12 && energyAt(a.energy, e - 0.05) > -12, `${s}–${e} loud inside`);
    assert.equal(energyAt(a.energy, s - 0.05), -100, `${s} silent before`);
    assert.equal(energyAt(a.energy, e + 0.05), -100, `${e} silent after`);
  }
  // Suggested in/out points of the middle phrase fall in the silences around it (media 1.4–2.5).
  const [beat] = suggestCuts(a, { beats: [{ id: 'mid', from: 1.3, to: 2.6 }] }).beats;
  assert.equal(beat.status, 'suggested', JSON.stringify(beat.conflicts));
  assert.ok(beat.in.source_seconds > expected[0][1] && beat.in.source_seconds < expected[1][0], `in ${beat.in.source_seconds}`);
  assert.ok(beat.out.source_seconds > expected[1][1] && beat.out.source_seconds < expected[2][0], `out ${beat.out.source_seconds}`);
  assert.equal(energyAt(a.energy, beat.in.source_seconds), -100);
  assert.equal(energyAt(a.energy, beat.out.source_seconds), -100);
});

test('analyzeFootage: when one reader fails, the other ffmpeg children are killed and the call returns promptly', async t => {
  const dir = await tempDir('creative-analyze-abort-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const media = await synthFootage(path.join(dir, 'footage.mov'));
  // A stand-in ffmpeg that records its pid and hangs (the energy and loudness readers).
  const pids = path.join(dir, 'pids'), slow = path.join(dir, 'slow-ffmpeg.sh');
  await fs.writeFile(slow, `#!/bin/sh\necho $$ >> '${pids}'\nexec sleep 60\n`, { mode: 0o755 });
  const saved = process.env.CREATIVE_FFMPEG;
  process.env.CREATIVE_FFMPEG = slow;
  t.after(() => { if (saved === undefined) delete process.env.CREATIVE_FFMPEG; else process.env.CREATIVE_FFMPEG = saved; });
  // The video scan fails once both audio readers are running.
  const decode = async () => {
    for (let k = 0; k < 100; k++) {
      const list = await fs.readFile(pids, 'utf8').then(text => text.trim().split('\n'), () => []);
      if (list.length >= 2) break;
      await new Promise(r => setTimeout(r, 50));
    }
    throw new Error('injected decode failure');
  };
  const t0 = Date.now();
  await assert.rejects(analyzeFootage(media, path.join(dir, 'a.json'), { decode }), /injected decode failure/);
  assert.ok(Date.now() - t0 < 10000, `returned after ${Date.now() - t0} ms`);
  const running = (await fs.readFile(pids, 'utf8')).trim().split('\n').map(Number);
  assert.equal(running.length, 2, 'energy and loudness readers were started');
  // SIGTERM was sent on abort (execFile rejects right away); the children are gone within moments, not after their 60 s.
  const alive = pid => { try { process.kill(pid, 0); return true; } catch { return false; } };
  for (let k = 0; k < 40 && running.some(alive); k++) await new Promise(r => setTimeout(r, 50));
  assert.deepEqual(running.filter(alive), [], 'children still running 2 s after the failure');
  await assert.rejects(fs.access(path.join(dir, 'a.json')), { code: 'ENOENT' });
});

test('scanVideo: a gradual dip to black across a chunk edge is found from the same decode (too gradual for the shot rule)', async () => {
  // 30 fps, 8×8 grey frames: level 120, from frame 148 a fade 120 → 3 (frame 152) → 110 (frame 157, about 22 levels per frame); chunks of 5 s.
  const level = k => k < 148 ? 120 : k < 153 ? 120 - (k - 147) * 23.4 : k < 158 ? 3 + (k - 152) * 21.4 : 110;
  const decode = async (file, from, to) => {
    const frames = [], times = [];
    for (let k = Math.max(0, Math.ceil(from * 30 - 1e-9)); k < Math.min(300, to * 30); k++) { frames.push(new Uint8Array(64).fill(Math.round(level(k)))); times.push(k / 30); }
    return { frames, times, width: 8, height: 8 };
  };
  const scan = await scanVideo('x', { timing: {}, duration: 10, band: { top: 0.62, bottom: 0.86 }, decode, chunk: 5 });
  assert.deepEqual(scan.shotTimes, [], 'no frame step reaches the shot rule');
  assert.equal(scan.dips.length, 1);
  const [dip] = scan.dips;
  assert.deepEqual([dip.start_seconds * 30, dip.min_seconds * 30, dip.end_seconds * 30].map(Math.round), [148, 152, 157]);
  assert.deepEqual([dip.ref_luma, dip.min_luma], [110, 3]);
});

test('scanVideo: an opening fade-up from black is a dip open at the file start (the whole-file series starts at the first frame)', async () => {
  const level = k => k < 2 ? 2 : k < 7 ? 2 + (k - 1) * 22 : 112;
  const decode = async (file, from, to) => {
    const frames = [], times = [];
    for (let k = Math.max(0, Math.ceil(from * 30 - 1e-9)); k < Math.min(90, to * 30); k++) { frames.push(new Uint8Array(64).fill(level(k))); times.push(k / 30); }
    return { frames, times, width: 8, height: 8 };
  };
  const scan = await scanVideo('x', { timing: {}, duration: 3, band: { top: 0.62, bottom: 0.86 }, decode, chunk: 5 });
  assert.deepEqual(scan.dips.map(d => [d.start_seconds, Math.round(d.end_seconds * 30), d.ref_luma, d.min_luma]), [[0, 6, 112, 2]]);
});
