import { test } from 'node:test';
import assert from 'node:assert/strict';
import { logSegments, mapLimit, mediaTool, overlap, silences, union, unionLength } from '../media-analysis.mjs';

test('media tool lookup honours CREATIVE_FFMPEG / CREATIVE_FFPROBE and refuses unknown tools', t => {
  const saved = { ffmpeg: process.env.CREATIVE_FFMPEG, ffprobe: process.env.CREATIVE_FFPROBE };
  const restore = (key, value) => { if (value === undefined) delete process.env[key]; else process.env[key] = value; };
  t.after(() => { restore('CREATIVE_FFMPEG', saved.ffmpeg); restore('CREATIVE_FFPROBE', saved.ffprobe); });
  delete process.env.CREATIVE_FFMPEG; delete process.env.CREATIVE_FFPROBE;
  assert.equal(mediaTool('ffmpeg'), 'ffmpeg');
  assert.equal(mediaTool('ffprobe'), 'ffprobe');
  process.env.CREATIVE_FFMPEG = '/opt/ff/ffmpeg'; process.env.CREATIVE_FFPROBE = '/opt/ff/ffprobe';
  assert.equal(mediaTool('ffmpeg'), '/opt/ff/ffmpeg');
  assert.equal(mediaTool('ffprobe'), '/opt/ff/ffprobe');
  assert.throws(() => mediaTool('sh'), /Unknown media tool/);
});

test('detector logs parse into segments; an open start runs to the duration', () => {
  const log = [
    '[silencedetect @ 0x1] silence_start: -0.002',
    '[silencedetect @ 0x1] silence_end: 1.5 | silence_duration: 1.5',
    '[silencedetect @ 0x1] silence_start: 4.25',
  ].join('\n');
  assert.deepEqual(silences(log, 6), [{ start: 0, end: 1.5 }, { start: 4.25, end: 6 }]);
  const video = '[blackdetect @ 0x2] black_start:0 black_end:2.04 black_duration:2.04\n[freezedetect @ 0x3] lavfi.freezedetect.freeze_start: 3\nlavfi.freezedetect.freeze_duration: 2\nlavfi.freezedetect.freeze_end: 5';
  assert.deepEqual(logSegments(video, 'black', 9), [{ start: 0, end: 2.04 }]);
  assert.deepEqual(logSegments(video, 'lavfi.freezedetect.freeze', 9), [{ start: 3, end: 5 }]);
  assert.deepEqual(silences('', 3), []);
});

test('interval union, clipped union length and overlap', () => {
  assert.deepEqual(union([[5, 9], [0, 2], [1, 3], [4, 4]]), [[0, 3], [5, 9]]);
  assert.equal(unionLength([[0, 2], [1, 3], [5, 9]], 8), 6);
  assert.equal(unionLength([[-1, 1]]), 1);
  assert.equal(overlap({ start: 2, end: 6 }, [[0, 3], [5, 9]]), 2);
});

test('mapLimit keeps order and never exceeds the limit', async () => {
  let active = 0, peak = 0;
  const result = await mapLimit([5, 1, 4, 2, 3, 0], 2, async value => {
    active++; peak = Math.max(peak, active);
    await new Promise(resolve => setTimeout(resolve, value * 3));
    active--;
    return value * 10;
  });
  assert.deepEqual(result, [50, 10, 40, 20, 30, 0]);
  assert.equal(peak, 2);
  assert.deepEqual(await mapLimit([], 4, async v => v), []);
});
