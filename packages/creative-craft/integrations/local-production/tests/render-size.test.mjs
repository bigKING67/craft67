import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { createProject, loadProject, probe } from '../project.mjs';
import { MAX_CAPTURE, MIN_RENDER_HEIGHT, captureSize, outputSize, renderSizes, scaleBack } from '../render.mjs';
import { compose } from '../composition.mjs';
import { synthVideo, tempDir } from './media-fixtures.mjs';

test('preview keeps the longest edge at 640 (never above the canvas); export is the canvas', () => {
  assert.deepEqual(outputSize({ width: 1280, height: 720 }, true), { width: 640, height: 360 });
  assert.deepEqual(outputSize({ width: 720, height: 1280 }, true), { width: 360, height: 640 });
  assert.deepEqual(outputSize({ width: 320, height: 180 }, true), { width: 320, height: 180 });
  assert.deepEqual(outputSize({ width: 128, height: 72 }, true), { width: 128, height: 72 });
  // Extreme aspect ratios are no longer raised to the capture limit: the capture is.
  assert.deepEqual(outputSize({ width: 1280, height: 160 }, true), { width: 640, height: 80 });
  assert.deepEqual(outputSize({ width: 3840, height: 64 }, true), { width: 640, height: 10 });
  assert.deepEqual(outputSize({ width: 64, height: 3840 }, true), { width: 10, height: 640 });
  assert.deepEqual(outputSize({ width: 3840, height: 480 }, false), { width: 3840, height: 480 });
});

test('outputs below the measured capture height are captured at the smallest integer multiple that reaches it', () => {
  assert.equal(MIN_RENDER_HEIGHT, 88);
  assert.deepEqual(captureSize({ width: 320, height: 180 }), { width: 320, height: 180, factor: 1 });
  assert.deepEqual(captureSize({ width: 160, height: 88 }), { width: 160, height: 88, factor: 1 });
  assert.deepEqual(captureSize({ width: 160, height: 86 }), { width: 320, height: 172, factor: 2 });
  assert.deepEqual(captureSize({ width: 128, height: 72 }), { width: 256, height: 144, factor: 2 });
  assert.deepEqual(captureSize({ width: 64, height: 64 }), { width: 128, height: 128, factor: 2 });
  assert.deepEqual(captureSize({ width: 10, height: 640 }), { width: 10, height: 640, factor: 1 });
  const sizes = (w, h, preview) => renderSizes({ width: w, height: h }, preview);
  assert.deepEqual(sizes(128, 72, false), { output: { width: 128, height: 72 }, capture: { width: 256, height: 144, factor: 2 } });
  assert.deepEqual(sizes(128, 72, true), { output: { width: 128, height: 72 }, capture: { width: 256, height: 144, factor: 2 } });
  assert.deepEqual(sizes(1280, 160, true), { output: { width: 640, height: 80 }, capture: { width: 1280, height: 160, factor: 2 } });
  assert.deepEqual(sizes(3840, 64, false), { output: { width: 3840, height: 64 }, capture: { width: 7680, height: 128, factor: 2 } });
  assert.deepEqual(sizes(3840, 64, true), { output: { width: 640, height: 10 }, capture: { width: 5760, height: 90, factor: 9 } });
  // A preview whose integer multiple would exceed the export capture is captured at the export capture.
  assert.deepEqual(sizes(648, 88, true), { output: { width: 640, height: 86 }, capture: { width: 648, height: 88, factor: null } });
  assert.deepEqual(sizes(3840, 88, true), { output: { width: 640, height: 14 }, capture: { width: 3840, height: 88, factor: null } });
});

test('every valid canvas: capture reaches the height limit, stays within the measured maximum, preview never above export', () => {
  assert.deepEqual(MAX_CAPTURE, { width: 7680, height: 7680 });
  let widest = 0, tallest = 0, narrowest = Infinity, fallbacks = 0;
  for (let w = 64; w <= 3840; w += 2) {
    for (let h = 64; h <= 3840; h += 2) {
      const full = renderSizes({ width: w, height: h }, false), small = renderSizes({ width: w, height: h }, true);
      for (const { output, capture } of [full, small]) {
        if (capture.height < MIN_RENDER_HEIGHT || capture.width % 2 || capture.height % 2) assert.fail(`${w}x${h}: ${JSON.stringify(capture)}`);
        // An integer factor keeps the output aspect exactly.
        if (capture.factor !== null && (capture.width !== output.width * capture.factor || capture.height !== output.height * capture.factor)) assert.fail(`${w}x${h}`);
        widest = Math.max(widest, capture.width); tallest = Math.max(tallest, capture.height); narrowest = Math.min(narrowest, output.width);
      }
      if (small.capture.width > full.capture.width || small.capture.height > full.capture.height) assert.fail(`${w}x${h}: preview capture above export`);
      if (small.capture.factor === null) fallbacks++;
    }
  }
  assert.deepEqual([widest, tallest], [7680, 3840], 'largest captures of valid canvases (7680 measured to render)');
  // Width needs no capture rule: the narrowest output of a valid canvas (64x3840 preview) is 10 px, above the 2–8 px measured to render.
  assert.equal(narrowest, 10);
  assert.ok(fallbacks > 0);
});

test('the composition is laid out at the capture size: caption sizes scale with it', async t => {
  const dir = await tempDir('render-size-');
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const clip = await synthVideo(path.join(dir, 'clip.mp4'), { size: '128x72', seconds: 1 }), root = path.join(dir, 'project');
  await createProject(root, { project_id: 'tiny', title: 'tiny', canvas: { width: 128, height: 72, fps: 30 }, assets: [{ id: 'clip', path: clip }],
    tracks: [{ id: 'v', kind: 'video', locked: false }, { id: 'c', kind: 'caption', locked: false }],
    items: [{ id: 'one', track_id: 'v', kind: 'media', asset_id: 'clip', start_frame: 0, frames: 15, source_in_seconds: 0, volume: 0 },
      { id: 'cap', track_id: 'c', kind: 'caption', start_frame: 0, frames: 15, text: 'Hi',
        style: { fontHeight: 0.08, centerY: 0.8, color: '#ffffff', strokeWidth: 0.004, weight: 700 } }] });
  const { doc, templates } = await loadProject(root);
  const fontSize = html => Number(/id="c-cap"[^>]*font-size:([\d.]+)px/.exec(html)[1]);
  const direct = compose(doc, { width: 128, height: 72 }, { templates }).html, captured = compose(doc, captureSize({ width: 128, height: 72 }), { templates }).html;
  assert.match(captured, /data-width="256" data-height="144"/);
  assert.equal(fontSize(captured), 2 * fontSize(direct));
});

// A stand-in ffmpeg (CREATIVE_FFMPEG) that writes a partial output file (its
// last argument) and then fails, or keeps running until it is killed.
async function fakeFfmpeg(dir, behaviour) {
  const script = path.join(dir, `ffmpeg-${behaviour}.sh`);
  await fs.writeFile(script, `#!/bin/sh\nfor last; do :; done\nprintf partial > "$last"\n${behaviour === 'fail' ? 'exit 1' : 'exec sleep 30'}\n`, { mode: 0o755 });
  return script;
}

test('a failed or cancelled scale-back removes the capture and the partial output', async t => {
  const dir = await tempDir('scale-back-'), saved = process.env.CREATIVE_FFMPEG;
  const restore = () => { if (saved === undefined) delete process.env.CREATIVE_FFMPEG; else process.env.CREATIVE_FFMPEG = saved; };
  t.after(async () => { restore(); await fs.rm(dir, { recursive: true, force: true }); });
  const capture = path.join(dir, 'capture.mp4'), output = path.join(dir, 'video.mp4'), size = { width: 128, height: 72 };
  const source = await synthVideo(path.join(dir, 'source.mp4'), { size: '256x144', seconds: 1 });
  const gone = file => assert.rejects(fs.access(file), { code: 'ENOENT' }, `${path.basename(file)} removed`);

  process.env.CREATIVE_FFMPEG = await fakeFfmpeg(dir, 'fail');
  await fs.copyFile(source, capture);
  await assert.rejects(scaleBack(capture, output, size));
  await gone(capture); await gone(output);

  process.env.CREATIVE_FFMPEG = await fakeFfmpeg(dir, 'hang');
  await fs.copyFile(source, capture);
  const controller = new AbortController(), pending = scaleBack(capture, output, size, controller.signal);
  for (let i = 0; i < 250 && !(await fs.stat(output).catch(() => null)); i++) await new Promise(resolve => setTimeout(resolve, 20));
  await fs.access(output); // the partial output exists while the encoder runs
  controller.abort();
  await assert.rejects(pending, { name: 'AbortError' });
  await gone(capture); await gone(output);

  // The real ffmpeg: only the output remains, at the output size.
  restore();
  await fs.copyFile(source, capture);
  await scaleBack(capture, output, size);
  await gone(capture);
  const media = await probe(output);
  assert.deepEqual([media.width, media.height], [128, 72]);
});
