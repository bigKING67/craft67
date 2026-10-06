import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { CORRECTION_SECONDS, compiledView, correctedSourceIn, correctionOf, parseFrameRate, pictureStream, probedFrameRate, rational, reduceFrameRate, streamStart, earliestStart, mediaZeroProblem,
  truncatedFrame } from '../source-frames.mjs';
import { validateV2 } from '../edit-document.mjs';
import { applyOperations } from '../operations.mjs';
import { compose } from '../composition.mjs';
import { activeCaptions, fontRuns } from '../caption-font.mjs';
import { cutPoints } from '../burned-captions.mjs';
import { SOURCE_END_TOLERANCE, resolveCaptions, sourceSeconds } from '../timeline.mjs';
import { createProject, editBatch, ffprobeJson, readProject } from '../project.mjs';
import { ffmpeg, tempDir } from './media-fixtures.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const fixture = async name => JSON.parse(await fs.readFile(path.resolve(here, '../../../tests/fixtures/edit-document-v2', name), 'utf8'));
const corrected = (k, num, den) => Math.round((k * den / num + CORRECTION_SECONDS) * 1e9) / 1e9;
const itemOf = (doc, id) => doc.items.find(i => i.id === id);

test('truncatedFrame at 30/1: in-points at most 2 ms (and less than 0.1 frame) below a frame start', () => {
  // 733/30 = 24.4333…: 24.433, 24.4327, 24.4333 and 24.433333 are 0.33, 0.63,
  // 0.033 and 0.0003 ms below frame 733.
  for (const written of [24.433, 24.4327, 24.4333, 24.433333]) {
    assert.equal(truncatedFrame(written, '30/1'), 733, String(written));
    assert.deepEqual(correctedSourceIn(written, '30/1'), { seconds: corrected(733, 30, 1), frame: 733 }, String(written));
  }
  assert.equal(correctedSourceIn(24.4333, '30/1').seconds, 24.433433333);
  assert.equal(truncatedFrame(733 / 30 - 3.3e-5, '30/1'), 733);
  // Exactly 2 ms below is still a truncation; more than 2 ms below is not.
  assert.equal(truncatedFrame(0.098, '30/1'), 3); // exactly 2 ms below 3/30 = 0.1
  assert.equal(truncatedFrame(24.4314, '30/1'), 733); // 1.933 ms below
  assert.equal(truncatedFrame(24.4313, '30/1'), null); // 2.033 ms below
  assert.equal(truncatedFrame(0.731334, '30/1'), 22); // 1.9993 ms below 22/30
  assert.equal(truncatedFrame(0.731333, '30/1'), null); // 2.0003 ms below
  assert.equal(truncatedFrame(24.43, '30/1'), null); // 3.33 ms below (0.1 frame)
  assert.equal(truncatedFrame(24.431, '30/1'), null); // 2.33 ms below
  // Inside a frame, on a frame start, on a midpoint: kept as written.
  for (const kept of [24.42, 24.46, 24.45, 1, 0, 1e-7, 0.5]) assert.equal(correctedSourceIn(kept, '30/1'), null, String(kept));
  assert.equal(truncatedFrame(2 / 30 - 1e-7, '30/1'), 2);
});

test('truncation limit: 2 ms, or 0.1 frame when that is shorter (60/1)', () => {
  // At 60 fps 0.1 frame = 1.667 ms < 2 ms.
  assert.equal(truncatedFrame(1.4986, '60/1'), 90); // 1.4 ms below 1.5 s = 0.084 frame
  assert.equal(truncatedFrame(1.4983, '60/1'), null); // 1.7 ms = 0.102 frame
});

test('truncatedFrame at 30000/1001 uses exact rational frame times', () => {
  const start = k => k * 1001 / 30000;
  for (const k of [1, 100, 733, 1798, 29970]) {
    assert.equal(truncatedFrame(start(k) - 3.3e-5, '30000/1001'), k, `start of ${k} − 3.3e-5 s`);
    assert.equal(truncatedFrame((2 * k + 1) * 1001 / 60000, '30000/1001'), null, `midpoint of ${k}`);
    assert.equal(truncatedFrame(start(k) - 0.0025, '30000/1001'), null, `2.5 ms before ${k}`);
  }
  // Millisecond truncation: 733 × 1001 / 30000 = 24.457766…, written 24.457 (0.77 ms below).
  assert.deepEqual(correctedSourceIn(24.457, '30000/1001'), { seconds: corrected(733, 30000, 1001), frame: 733 });
  assert.deepEqual(correctedSourceIn(4.504, '30000/1001'), { seconds: corrected(135, 30000, 1001), frame: 135 }); // 4.5045 − 0.5 ms
  assert.equal(truncatedFrame(24.4333, '30000/1001'), null); // 732.266 frames
  assert.deepEqual(correctedSourceIn(4.5044, '30000/1001'), { seconds: corrected(135, 30000, 1001), frame: 135 });
});

test('truncatedFrame at 24/1: millisecond truncation', () => {
  // 733 / 24 = 30.541666…: 30.541 is 0.67 ms below frame 733; 11/24 = 0.458333…
  assert.deepEqual(correctedSourceIn(30.541, '24/1'), { seconds: corrected(733, 24, 1), frame: 733 });
  assert.equal(truncatedFrame(0.458, '24/1'), 11);
  assert.equal(truncatedFrame(30.539, '24/1'), null); // 2.67 ms below
});

test('correctedSourceIn and truncatedFrame accept a rate string or its parsed form alike', () => {
  for (const [seconds, rate] of [[24.433, '30/1'], [24.457, '30000/1001'], [24.43, '30/1'], [30.541, '24/1']]) {
    const parsed = parseFrameRate(rate);
    assert.equal(parseFrameRate(parsed), parsed, 'a parsed rate is returned as is');
    assert.deepEqual(correctedSourceIn(seconds, parsed), correctedSourceIn(seconds, rate));
    assert.equal(truncatedFrame(seconds, parsed), truncatedFrame(seconds, rate));
  }
  assert.throws(() => correctedSourceIn(1, { num: 0n, den: 1n }), /Invalid frame_rate 0\/1/);
  assert.throws(() => correctedSourceIn(1, { num: 30, den: 1 }), /Invalid frame_rate/);
});

test('frame rate parsing, reduction and import rules', () => {
  assert.deepEqual(parseFrameRate('30000/1001'), { num: 30000n, den: 1001n });
  for (const bad of ['30', '0/1', '30/0', '30.0/1', '1234567/1', '', null]) assert.throws(() => parseFrameRate(bad), /Invalid frame_rate/);
  assert.equal(reduceFrameRate('60/2'), '30/1');
  assert.equal(reduceFrameRate('0/0'), null);
  const video = (r, avg, extra = {}) => ({ codec_type: 'video', r_frame_rate: r, avg_frame_rate: avg, time_base: '1/15360', start_pts: 0, start_time: '0.000000', ...extra });
  const audio = { codec_type: 'audio', r_frame_rate: '0/0', avg_frame_rate: '0/0', time_base: '1/44100', start_pts: 0, start_time: '0.000000' };
  const at0 = streams => ({ streams, format: { start_time: '0.000000' } });
  assert.equal(probedFrameRate(at0([video('30/1', '30/1'), audio])), '30/1');
  assert.equal(probedFrameRate(at0([video('30000/1001', '60000/2002')])), '30000/1001');
  // Variable frame rate (r ≠ avg): none, the renderer behaviour is kept.
  assert.equal(probedFrameRate(at0([video('30/1', '1800000/60061'), audio])), null);
  // The picture stream's start (start_pts × time_base) must be the earliest
  // stream start, which the renderer and QA take as media time 0.
  assert.equal(probedFrameRate(at0([video('30/1', '30/1', { start_pts: 7680, start_time: '0.500000' }), audio])), null, 'video after audio');
  assert.equal(probedFrameRate({ streams: [video('30/1', '30/1', { start_pts: undefined })], format: { start_time: '0.000000' } }), null);
  assert.equal(probedFrameRate({ streams: [video('30/1', '30/1', { time_base: '0/0' })], format: { start_time: '0.000000' } }), null);
  // All streams at the same non-zero start: media time 0 is the video start.
  assert.equal(probedFrameRate({ streams: [video('30/1', '30/1', { start_pts: 7680, start_time: '0.500000' })], format: { start_time: '0.500000' } }), '30/1');
  const late = { ...audio, start_pts: 22050, start_time: '0.500000' }; // 0.5 s in another time base, compared exactly
  assert.equal(probedFrameRate({ streams: [video('30/1', '30/1', { start_pts: 7680 }), late], format: { start_time: '0.500000' } }), '30/1');
  assert.equal(probedFrameRate({ streams: [video('30/1', '30/1', { start_pts: 7680 }), { ...late, start_pts: 22049 }], format: {} }), null, 'audio one sample earlier');
  // Audio starting before the video (a negative start, as an MKV or WebM can
  // keep): media time 0 is the audio start, frame k is not at k / rate.
  const primed = { ...audio, start_pts: -941, start_time: '-0.021338' };
  assert.equal(probedFrameRate({ streams: [video('30/1', '30/1'), primed], format: { start_time: '-0.021338' } }), null);
  // Audio starting after the video does not move media time 0.
  assert.equal(probedFrameRate(at0([video('30/1', '30/1'), { ...audio, start_pts: 441 }])), '30/1');
  // Streams without a usable start are not compared (as in sourceTiming).
  assert.equal(probedFrameRate(at0([video('30/1', '30/1'), { ...audio, start_pts: undefined }])), '30/1');
  assert.equal(probedFrameRate({ streams: [video('30/1', '30/1')], format: {} }), '30/1');
  // One start reading: the exact fraction and its seconds.
  assert.deepEqual(streamStart(primed), { p: -941n, q: 44100n, seconds: -941 / 44100 });
  assert.deepEqual(streamStart(video('30/1', '30/1', { start_pts: 7680 })), { p: 7680n, q: 15360n, seconds: 0.5 });
  assert.equal(streamStart({ ...audio, start_pts: undefined }), null);
  assert.equal(streamStart({ ...audio, time_base: '0/0' }), null);
  assert.equal(earliestStart({ streams: [video('30/1', '30/1', { start_pts: 7680 }), primed] }).seconds, -941 / 44100);
  assert.equal(earliestStart({ streams: [{ ...audio, start_pts: undefined }] }), null);
  // The reason the frame grid does not start at media time 0 (null when it does).
  assert.equal(mediaZeroProblem(at0([video('30/1', '30/1'), audio])), null);
  assert.match(mediaZeroProblem({ streams: [video('30/1', '30/1'), primed] }), /video stream starts at 0 s, after the earliest stream start -0\.0213\d+ s/);
  // Audio only, or only cover art.
  assert.equal(probedFrameRate(at0([audio])), null);
  const cover = video('90000/1', '0/0', { width: 64, height: 64, disposition: { attached_pic: 1 } });
  assert.equal(probedFrameRate(at0([audio, cover])), null);
  assert.equal(pictureStream(at0([audio, cover])), null);
  // Cover art before the picture: the QA timing decodes the picture (0:v:1), but
  // no frame_rate is recorded, since width and height come from the first video
  // stream (the cover) and frame_rate must describe the same stream.
  const picture = video('25/1', '25/1', { width: 160, height: 90, disposition: { attached_pic: 0 } });
  assert.deepEqual(pictureStream(at0([cover, picture, audio])), { stream: picture, index: 1 });
  assert.equal(probedFrameRate(at0([cover, picture, audio])), null);
  assert.deepEqual(pictureStream(at0([picture, cover, audio])), { stream: picture, index: 0 });
  assert.equal(probedFrameRate(at0([picture, cover, audio])), '25/1');
  assert.deepEqual(rational('1/15360'), { num: 1, den: 15360 });
  for (const bad of ['0/0', '1/0', '30', undefined]) assert.equal(rational(bad), null, String(bad));
});

test('validateV2: frame_rate only on assets with a picture and in rational form', async () => {
  const doc = await fixture('valid/source-frame-rates.json');
  validateV2(doc);
  const audioRate = await fixture('invalid/audio-asset-with-frame-rate.json');
  assert.throws(() => validateV2(audioRate), /Asset music frame_rate requires a video stream/);
  const bad = structuredClone(doc);
  bad.assets[0].frame_rate = '29.97';
  assert.throws(() => validateV2(bad), /Invalid frame_rate on asset talk/);
});

test('compilation corrects truncated in-points of video-track items only; the document is not rewritten', async () => {
  const doc = await fixture('valid/source-frame-rates.json');
  itemOf(doc, 'talk1').source_in_seconds = 4.5044; // 0.003 frame below frame 135 at 29.97
  itemOf(doc, 'talk2').source_in_seconds = 10; // 299.7 frames: inside frame 299, kept
  itemOf(doc, 'broll1').source_in_seconds = 1.9999; // 0.003 frame below frame 60 at 30
  // The talk asset (picture and sound) on the audio track, with a truncated in-point.
  doc.items.push({ id: 'talk-sound', track_id: 'a_music', kind: 'media', asset_id: 'talk', start_frame: 270, frames: 30, source_in_seconds: 4.5044, volume: 0.5 });
  validateV2(doc);
  const before = structuredClone(doc);
  const { html, cues } = compose(doc);
  assert.deepEqual(doc, before, 'compile does not mutate');
  const start = id => Number(new RegExp(`id="${id}"[^>]*data-media-start="([^"]+)"`).exec(html)[1]);
  assert.equal(start('v-talk1'), corrected(135, 30000, 1001));
  assert.equal(start('a-talk1'), corrected(135, 30000, 1001), 'the item\'s own sound plays from its picture\'s in-point');
  assert.equal(start('v-talk2'), 10, 'an in-point inside a frame is kept');
  assert.equal(start('v-broll1'), corrected(60, 30, 1));
  assert.equal(start('a-talk-sound'), 4.5044, 'audio-track items are never corrected');
  assert.equal(start('a-bed'), 0);
  // The linked caption (source 2.0–4.5 on talk1) is now outside talk1's window;
  // move it inside and it maps through the compiled in-point.
  const linked = structuredClone(doc);
  Object.assign(itemOf(linked, 'cap1').link, { source_from: 5, source_to: 6 });
  const cue = compose(linked).cues.find(c => c.text === '第一句');
  assert.ok(Math.abs(cue.start - (5 - corrected(135, 30000, 1001))) < 1e-9);
  assert.ok(!cues.some(c => c.text === '第一句'));
  // Without frame_rate the written times are compiled as before.
  const plain = structuredClone(doc);
  for (const asset of plain.assets) delete asset.frame_rate;
  const plainHtml = compose(plain).html;
  assert.match(plainHtml, /id="v-talk1"[^>]*data-media-start="4.5044"/);
  assert.match(plainHtml, /id="v-broll1"[^>]*data-media-start="1.9999"/);
});

test('the compiled view is computed once and shared: views, captions and cut points', async () => {
  const doc = await fixture('valid/source-frame-rates.json');
  itemOf(doc, 'talk1').source_in_seconds = 4.5044;
  const view = compiledView(doc);
  assert.equal(compiledView(view), view, 'a view is not corrected again');
  assert.notEqual(view, doc);
  const talk1 = itemOf(view, 'talk1');
  assert.deepEqual(correctionOf(talk1), { written: itemOf(doc, 'talk1'), frame: 135 });
  assert.equal(correctionOf(itemOf(view, 'talk2')), null);
  assert.equal(itemOf(view, 'talk2'), itemOf(doc, 'talk2'), 'unchanged items are shared');
  // Cut points of a view are its own items, matched to the document's items.
  const points = cutPoints(view);
  assert.ok(points.every(p => view.items.includes(p.item)));
  assert.ok(points.every(p => !('document' in p)));
  const written = p => correctionOf(p.item)?.written ?? p.item;
  assert.ok(points.every(p => doc.items.includes(written(p)) && written(p).id === p.item.id));
  // A caption visible only in the written window [4.5044, 4.50455] is not shown,
  // since the compiled in-point is 4.5046.
  Object.assign(itemOf(doc, 'cap1').link, { source_from: 4.5044, source_to: 4.50455 });
  assert.ok(resolveCaptions(doc).some(c => c.item.id === 'cap1'), 'visible in the written window');
  assert.ok(!activeCaptions(doc).some(c => c.id === 'cap1'), 'font runs follow the compiled view');
  // A view passed to compose / the font runs (as renderProject does) is used as
  // is: the same output as compiling the document there.
  const once = compiledView(doc);
  assert.equal(compose(once).html, compose(doc).html);
  assert.deepEqual(fontRuns(once), fontRuns(doc));
  assert.deepEqual(activeCaptions(once), activeCaptions(doc));
});

test('cut points: compiled in/out, the written in- and out-point, the frame', async () => {
  const doc = await fixture('valid/source-frame-rates.json');
  itemOf(doc, 'talk1').source_in_seconds = 4.5044;
  const [inPoint, outPoint] = cutPoints(doc).filter(p => p.item.id === 'talk1');
  const compiledIn = corrected(135, 30000, 1001);
  assert.deepEqual([inPoint.edge, inPoint.source_seconds, inPoint.document_source_seconds, inPoint.source_frame], ['in', compiledIn, 4.5044, 135]);
  assert.deepEqual([outPoint.edge, outPoint.source_seconds, outPoint.document_source_seconds], ['out', compiledIn + 150 / 30, 4.5044 + 150 / 30]);
  assert.ok(!('source_frame' in outPoint));
  assert.notEqual(outPoint.document_source_seconds, inPoint.document_source_seconds);
  // Uncorrected items and assets without frame_rate carry no document fields.
  const talk2 = cutPoints(doc).find(p => p.item.id === 'talk2' && p.edge === 'in');
  assert.ok(!('document_source_seconds' in talk2) && !('source_frame' in talk2));
  const plain = structuredClone(doc);
  for (const asset of plain.assets) delete asset.frame_rate;
  const plainIn = cutPoints(plain).find(p => p.item.id === 'talk1' && p.edge === 'in');
  assert.equal(plainIn.source_seconds, 4.5044);
  assert.ok(!('source_frame' in plainIn) && !('document_source_seconds' in plainIn));
});

test('split continuity: 24/1 source on a 60 fps canvas, split after 1 output frame', async () => {
  const doc = await fixture('valid/source-frame-rates.json');
  doc.canvas.fps = 60;
  doc.assets.find(a => a.id === 'broll').frame_rate = '24/1';
  doc.items = doc.items.filter(i => i.id === 'broll1');
  const broll = itemOf(doc, 'broll1');
  Object.assign(broll, { start_frame: 0, frames: 60 });
  for (const headIn of [0, 0.5, 1.2345]) {
    broll.source_in_seconds = headIn;
    const split = await applyOperations(doc, [{ type: 'split_item', item_id: 'broll1', at_frame: 1, new_item_id: 'tail' }], { imports: [] });
    validateV2(split);
    const view = compiledView(split), head = itemOf(view, 'broll1'), tail = itemOf(view, 'tail');
    assert.equal(head.source_in_seconds, headIn, `head ${headIn} kept`);
    assert.equal(tail.source_in_seconds, itemOf(split, 'tail').source_in_seconds, 'tail kept as written');
    assert.ok(Math.abs(tail.source_in_seconds - (head.source_in_seconds + sourceSeconds(head, 60))) < 1e-9, `tail starts where the head ends (${headIn})`);
  }
  // A truncated head (11/24 = 0.458333… written 0.4583) is corrected by 0.1 ms +
  // 0.0008 frame (0.03 ms); its tail (11.399 frames) is kept, and both sides of the seam
  // still show the same source frame.
  broll.source_in_seconds = 0.4583;
  const split = await applyOperations(doc, [{ type: 'split_item', item_id: 'broll1', at_frame: 1, new_item_id: 'tail' }], { imports: [] });
  const view = compiledView(split), head = itemOf(view, 'broll1'), tail = itemOf(view, 'tail');
  assert.equal(head.source_in_seconds, corrected(11, 24, 1));
  assert.equal(tail.source_in_seconds, itemOf(split, 'tail').source_in_seconds);
  const headEnd = head.source_in_seconds + sourceSeconds(head, 60);
  assert.ok(headEnd - tail.source_in_seconds <= 0.002 + CORRECTION_SECONDS);
  assert.equal(Math.floor(headEnd * 24), Math.floor(tail.source_in_seconds * 24));
});

test('the corrected range stays inside the asset, up to the last source frame', async () => {
  const doc = await fixture('valid/source-frame-rates.json');
  const broll = itemOf(doc, 'broll1'); // asset broll: 8 s at 30/1 (frames 0–239)
  Object.assign(broll, { source_in_seconds: 7.4666, frames: 16 }); // frame 224 truncated; through frame 239
  validateV2(doc);
  const item = itemOf(compiledView(doc), 'broll1');
  assert.equal(item.source_in_seconds, corrected(224, 30, 1));
  const end = item.source_in_seconds + sourceSeconds(item, 30);
  assert.ok(end <= 8 + SOURCE_END_TOLERANCE, `compiled end ${end}`);
  assert.ok(end - (7.4666 + sourceSeconds(broll, 30)) <= 0.002 + CORRECTION_SECONDS + 1e-12, 'shift ≤ 2 ms + 0.1 ms');
  validateV2(compiledView(doc));
  // An asset ending so that the written range fits the tolerance but the
  // corrected one would not: the in-point is kept.
  doc.assets.find(a => a.id === 'broll').duration = 7.99905;
  validateV2(doc);
  assert.equal(itemOf(compiledView(doc), 'broll1').source_in_seconds, 7.4666);
  assert.ok(!('source_frame' in cutPoints(doc).find(p => p.item.id === 'broll1')));
});

test('import records frame_rate for v2 video (create and add_asset), not for audio, cover art, video starting after media time 0 or v1 projects', async t => {
  const dir = await tempDir('frame-rate-import-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const file = name => path.join(dir, name);
  await ffmpeg('-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=30000/1001:duration=1', '-f', 'lavfi', '-i', 'sine=d=1',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', file('ntsc.mp4'));
  await ffmpeg('-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=25:duration=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', file('pal.mp4'));
  await ffmpeg('-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=30:duration=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-output_ts_offset', '0.5', file('late.mp4'));
  // Video 0.5 s after the audio: media time 0 is the audio start.
  await ffmpeg('-itsoffset', '0.5', '-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=30:duration=1', '-f', 'lavfi', '-i', 'sine=d=1.5',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', file('behind.mkv'));
  const behind = (await ffprobeJson(file('behind.mkv'))).streams;
  assert.ok(streamStart(behind.find(s => s.codec_type === 'video')).seconds > streamStart(behind.find(s => s.codec_type === 'audio')).seconds, 'fixture: video after audio');
  await ffmpeg('-f', 'lavfi', '-i', 'sine=d=1', '-c:a', 'aac', file('tone.m4a'));
  await ffmpeg('-f', 'lavfi', '-i', 'color=c=red:s=64x64', '-frames:v', '1', file('cover.png'));
  await ffmpeg('-f', 'lavfi', '-i', 'sine=d=1', '-i', file('cover.png'), '-map', '1', '-map', '0', '-c:v', 'png', '-c:a', 'aac', '-disposition:v:0', 'attached_pic', file('cover.m4a'));
  // Audio starting 44 ms before media time 0 (as AAC priming does), video at 0.
  await ffmpeg('-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=30:duration=1', '-itsoffset', '-0.044', '-f', 'lavfi', '-i', 'sine=d=1.1',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-avoid_negative_ts', 'disabled', '-t', '1', file('primed.mkv'));
  const primed = (await ffprobeJson(file('primed.mkv'))).streams;
  assert.ok(primed.find(s => s.codec_type === 'audio').start_pts < 0 && primed.find(s => s.codec_type === 'video').start_pts === 0, 'fixture: audio before 0, video at 0');
  const root = path.join(dir, 'v2');
  const created = await createProject(root, { project_id: 'import-rate', title: 'import', canvas: { width: 320, height: 180, fps: 30 },
    assets: [{ id: 'ntsc', path: file('ntsc.mp4') }, { id: 'tone', path: file('tone.m4a') }, { id: 'late', path: file('late.mp4') }, { id: 'cover', path: file('cover.m4a') },
      { id: 'primed', path: file('primed.mkv') }, { id: 'behind', path: file('behind.mkv') }],
    tracks: [{ id: 'v', kind: 'video', locked: false }],
    items: [{ id: 'a', track_id: 'v', kind: 'media', asset_id: 'ntsc', start_frame: 0, frames: 15, source_in_seconds: 0, volume: 0 }] });
  const rates = doc => Object.fromEntries(doc.assets.map(a => [a.id, a.frame_rate ?? null]));
  // late.mp4 has one stream starting at 0.5 s, so media time 0 is its first
  // frame. primed.mkv (audio at -44 ms) and behind.mkv (video 0.5 s after the
  // audio) have media time 0 before the first video frame: the renderer shows
  // video time in-point - 0.044 (resp. + 0.5) there, so k / rate is not the
  // frame grid and no frame_rate is recorded (no truncation correction; QA
  // checks the decoded frame times and warns).
  assert.deepEqual(rates(created), { ntsc: '30000/1001', tone: null, late: '30/1', cover: null, primed: null, behind: null });
  assert.ok(!('frame_rate' in created.assets.find(a => a.id === 'tone')));
  // Cover art keeps the historical video flag and size (first video stream), but
  // has no frame rate (that stream is not a picture).
  const cover = created.assets.find(a => a.id === 'cover');
  assert.deepEqual([cover.video, cover.audio, cover.width, cover.height], [true, true, 64, 64]);
  assert.ok(!('frame_rate' in cover));
  // A local-edit.v1 project can use the audio file with cover art as a clip, as before.
  const coverV1 = await createProject(path.join(dir, 'cover-v1'), { project_id: 'cover-v1', title: 'cover', canvas: { width: 320, height: 180, fps: 30 },
    assets: [{ id: 'cover', path: file('cover.m4a') }], clips: [{ id: 'c', asset_id: 'cover', in_seconds: 0, frames: 15, volume: 1, fit: 'contain', captions: [] }], audio: [] });
  assert.deepEqual([coverV1.assets[0].video, coverV1.assets[0].width, coverV1.assets[0].height], [true, 64, 64]);
  assert.ok(!('frame_rate' in coverV1.assets[0]));
  // The video starting 0.5 s after the audio is still a picture.
  assert.deepEqual(['video', 'width', 'height'].map(k => created.assets.find(a => a.id === 'behind')[k]), [true, 160, 90]);
  await editBatch(root, { base_revision: 1, author: 'agent', summary: 'add', operations: [{ type: 'add_asset', id: 'pal', path: file('pal.mp4') }] });
  assert.equal(rates(await readProject(root)).pal, '25/1');
  // local-edit.v1 has no frame_rate field; its imports are not probed for one.
  const v1 = await createProject(path.join(dir, 'v1'), { project_id: 'import-v1', title: 'v1', canvas: { width: 320, height: 180, fps: 30 },
    assets: [{ id: 'ntsc', path: file('ntsc.mp4') }], clips: [{ id: 'c', asset_id: 'ntsc', in_seconds: 0, frames: 15, volume: 0, fit: 'contain', captions: [] }], audio: [] });
  assert.ok(!('frame_rate' in v1.assets[0]));
});
