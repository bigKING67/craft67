// Explicit opt-in: uses the installed headless Chromium and real FFmpeg/producer.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createProject, run } from '../project.mjs';
import { renderProject } from '../render.mjs';

test('real producer loads the bound font, applies weights, and rejects a missing font', { timeout: 90000 }, async t => {
  assert.ok(process.env.PRODUCER_HEADLESS_SHELL_PATH, 'Set PRODUCER_HEADLESS_SHELL_PATH for this integration check');
  const root = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'caption-font-render-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  process.env.PRODUCER_PLAYER_READY_TIMEOUT_MS = '2000';
  process.env.PRODUCER_RENDER_READY_TIMEOUT_MS = '2000';
  const source = path.join(root, 'black.mp4'), project = path.join(root, 'project'), output = path.join(root, 'output');
  await run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=720x1280:r=30:d=1',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', source]);
  const style = { fontHeight: .035, centerY: .6875, color: '#ffffff', strokeWidth: .0015, weight: 900 };
  await createProject(project, { project_id: 'font-test', title: 'font-test', canvas: { width: 720, height: 1280, fps: 30 },
    assets: [{ id: 'black', path: source }], clips: [{ id: 'clip', asset_id: 'black', in_seconds: 0,
      frames: 30, volume: 0, fit: 'contain', captions: [
        { from: 0, to: .5, text: '很温和的就把我们', style: { ...style, weight: 400 } },
        { from: .5, to: 1, text: '很温和的就把我们', style }
      ] }], audio: [] });
  const receipt = await renderProject(project, output);
  assert.equal(receipt.status, 'completed');
  assert.equal(receipt.caption_font.runtime_load, 'passed');
  assert.equal(receipt.caption_font.source_match, 'unverified');
  const whitePixels = async time => {
    const { stdout } = await run('ffmpeg', ['-v', 'error', '-ss', String(time), '-i', path.join(output, 'video.mp4'),
      '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], { encoding: 'buffer', maxBuffer: 2 * 1024 * 1024 });
    return stdout.reduce((sum, value) => sum + (value > 220 ? 1 : 0), 0);
  };
  assert.ok(await whitePixels(.7) > (await whitePixels(.2)) * 1.5, '900 weight must be visibly heavier than 400');

  // Fault injection is after byte verification: simulate a browser resource
  // failure. The ordinary fonts.ready wait/producer tween flag let this pass.
  const broken = path.join(root, 'broken');
  await fs.mkdir(broken);
  await fs.cp(path.join(output, 'assets'), path.join(broken, 'assets'), { recursive: true });
  await fs.copyFile(path.join(output, 'gsap.min.js'), path.join(broken, 'gsap.min.js'));
  const html = await fs.readFile(path.join(output, 'index.html'), 'utf8');
  await fs.writeFile(path.join(broken, 'index.html'), html.replace(/fonts\/[a-f0-9]{64}\.ttf/g, 'fonts/missing.ttf'));
  const { createRenderJob, executeRenderJob } = await import('@hyperframes/producer');
  const job = createRenderJob({ fps: 30, quality: 'draft', format: 'mp4', workers: 1,
    useGpu: false, hdrMode: 'force-sdr', strictness: 'strict' });
  await assert.rejects(executeRenderJob(job, broken, path.join(broken, 'video.mp4'), () => {}, AbortSignal.timeout(20000)),
    /captionFont/);
  assert.equal(job.status, 'failed');
});
