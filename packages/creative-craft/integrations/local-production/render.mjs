import * as fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { digest, ffprobeJson, probe, loadProject, safePath, verifyAssets, run } from './project.mjs';
import { compose, webVtt } from './composition.mjs';
import { copyCaptionFont } from './caption-font.mjs';
import { copyBoundTemplates } from './template-binding.mjs';
import { audibleItems, isV2 } from './timeline.mjs';
import { templateProvenance } from './templates.mjs';
import { mediaTool } from './media-analysis.mjs';
import { compiledView } from './source-frames.mjs';

const require = createRequire(import.meta.url);
const packageVersion = async name => JSON.parse(await fs.readFile(new URL(`./node_modules/${name}/package.json`, import.meta.url), 'utf8')).version;
export const revisionFile = (root, revision) => path.join(root, 'revisions', `${String(revision).padStart(6, '0')}.json`);

// Measured renderer limits (HyperFrames producer 0.8.108, headless Chrome 154,
// macOS): with a capture (composition) height of 86 px or less the sequential
// screenshot capture makes no progress and the producer fails after its stall
// timeout ("capture stalled", 60 s); 88 px and up render, whatever the
// container, codec or presence of video. Width is not limiting: 2, 4, 6, 8, 10,
// 16, 32 and 64 px wide captures (160 px high) and 8x88 all render, with the
// source colour checked down to 4 px; no output of a valid canvas is narrower
// than 10 px (a 64x3840 preview), so width needs no rule. Largest captures
// measured to render: 7680x128 and 128x7680 (MAX_CAPTURE). See README
// 「素材兼容与渲染尺寸」.
export const MIN_RENDER_HEIGHT = 88;
export const MAX_CAPTURE = Object.freeze({ width: 7680, height: 7680 });
// Encoder settings of the scale-back: one fixed high-quality setting whatever
// the render quality (the capture was already encoded once at that quality;
// this second generation should add as little loss as possible).
const DOWNSCALE_ENCODE = ['-preset', 'medium', '-crf', '18'];

// Output size. Preview: longest edge at most 640 (never above the canvas),
// even dimensions. Export: the project canvas.
export function outputSize(canvas, preview) {
  const scale = preview ? Math.min(1, 640 / Math.max(canvas.width, canvas.height)) : 1;
  const even = value => Math.max(2, Math.round(value / 2) * 2);
  return { width: even(canvas.width * scale), height: even(canvas.height * scale) };
}

// The output size times the smallest integer factor that reaches
// MIN_RENDER_HEIGHT (factor 1 when the output already does).
export function captureSize({ width, height }) {
  const factor = Math.max(1, Math.ceil(MIN_RENDER_HEIGHT / height));
  return { width: width * factor, height: height * factor, factor };
}

// { output, capture } of a render. The composition is laid out at the capture
// size (captions and graphics scale with it) and a capture other than the
// output is scaled back to it. Export: the canvas, captured at captureSize.
// Preview: captureSize of the preview output, unless that is larger than the
// export capture in either dimension (e.g. 648x88: preview 640x86 would need
// 1280x172, the export captures 648x88); then the preview is captured at the
// export capture and scaled back by a non-integer factor (factor null; the
// even-rounded preview aspect differs from the canvas by under one output
// pixel). A preview is never captured larger than its export. Every capture of
// a valid canvas is at most 7680x3840 (export 3840x64..86 → 7680 wide), inside
// MAX_CAPTURE; a capture beyond it is refused (unreachable for valid canvases,
// kept so a changed rule cannot silently render at an unmeasured size).
export function renderSizes(canvas, preview) {
  const output = outputSize(canvas, preview), full = captureSize(canvas);
  let capture = captureSize(output);
  if (capture.width > full.width || capture.height > full.height) capture = { ...full, factor: null };
  if (capture.width > MAX_CAPTURE.width || capture.height > MAX_CAPTURE.height) {
    throw new Error(`Capture ${capture.width}x${capture.height} exceeds the measured limit ${MAX_CAPTURE.width}x${MAX_CAPTURE.height}`);
  }
  return { output, capture };
}

// Scale a capture back to the output size: area averaging (exact for an
// integer factor), square pixels, the capture's pixel format and colour tags,
// fixed encoder settings (DOWNSCALE_ENCODE); audio copied. On failure or
// cancellation the partial output is removed; the capture is removed in every
// case.
export async function scaleBack(capture, output, { width, height }, signal) {
  try {
    const info = await ffprobeJson(capture), video = info.streams.find(s => s.codec_type === 'video');
    const colour = [['-color_range', video.color_range], ['-colorspace', video.color_space], ['-color_primaries', video.color_primaries],
      ['-color_trc', video.color_transfer]].filter(([, value]) => value && value !== 'unknown').flat();
    await run(mediaTool('ffmpeg'), ['-v', 'error', '-i', capture, '-map', '0:v:0', '-map', '0:a?', '-vf', `scale=${width}:${height}:flags=area,setsar=1`,
      '-fps_mode', 'passthrough', '-c:v', 'libx264', ...DOWNSCALE_ENCODE, '-pix_fmt', video.pix_fmt, ...colour, '-c:a', 'copy',
      '-movflags', '+faststart', '-n', output], { timeout: 600000, maxBuffer: 4 * 1024 * 1024, signal });
  } catch (error) {
    await fs.rm(output, { force: true });
    throw error;
  } finally {
    await fs.rm(capture, { force: true });
  }
}

export function expectsAudio(project, frames) {
  if (isV2(project)) return audibleItems(project).length > 0;
  return project.clips.some(c => c.volume > 0 && project.assets.find(a => a.id === c.asset_id)?.audio) ||
    project.audio.some(a => a.volume > 0 && a.start_frame < frames);
}

// HyperFrames lint gate: any error-severity finding blocks the render.
export async function lintComposition(html) {
  const { lintHyperframeHtml, shouldBlockRender } = await import('@hyperframes/lint');
  const result = await lintHyperframeHtml(html, { filePath: 'index.html' });
  return { engine: '@hyperframes/lint', version: await packageVersion('@hyperframes/lint'), ok: result.ok,
    error_count: result.errorCount, warning_count: result.warningCount, info_count: result.infoCount,
    blocked: shouldBlockRender(true, false, result.errorCount, result.warningCount),
    findings: result.findings.map(({ code, severity, message, elementId }) => ({ code, severity, message, ...(elementId ? { element_id: elementId } : {}) })) };
}

// Concurrent captures in one process corrupt each other (measured: frames
// filled only at the top, black below), so the browser capture
// (executeRenderJob) runs one at a time per process; preparation, lint, the
// scale-back and the decode check run outside the lock. A task whose signal is
// aborted while it waits for its turn rejects at once with the abort reason
// (the caller's cancellation path runs immediately) and never starts; once
// started, a task is never abandoned: it settles on its own (the producer
// observes the signal), so the lock is held until the capture has stopped.
let captureQueue = Promise.resolve();
export function withRenderLock(task, signal) {
  let started = false;
  const turn = captureQueue.then(() => { signal?.throwIfAborted(); started = true; return task(); });
  captureQueue = turn.then(() => {}, () => {});
  if (!signal) return turn;
  return new Promise((resolve, reject) => {
    const abandon = () => { if (!started) reject(signal.reason); };
    signal.addEventListener('abort', abandon, { once: true });
    if (signal.aborted) abandon();
    turn.then(resolve, reject).finally(() => signal.removeEventListener('abort', abandon));
  });
}

export async function renderProject(root, destination, { revision, preview = false, onProgress = () => {}, signal } = {}) {
  const { doc: project, templates, alignment, verified } = await loadProject(root, revision);
  // Source frame alignment: loadProject decided which assets' frame_rate
  // applies (stale ones are compiled without correction) and bound the document
  // to it; the compiled view is computed once here and shared by the font glyph
  // checks (verifyAssets, copyCaptionFont) and compose, which use a view passed
  // in as is. The receipt records the alignment; project.json keeps the
  // document as written. Asset files loadProject already hashed are not hashed
  // again.
  const view = isV2(project) ? compiledView(project) : project;
  await verifyAssets(root, view, templates, { verified });
  const { output: { width, height }, capture } = renderSizes(project.canvas, preview);
  const compiled = compose(view, { width: capture.width, height: capture.height }, { templates });
  const scaled = capture.width !== width || capture.height !== height;
  destination = await safePath(destination);
  root = await safePath(root);
  if (destination === root || destination.startsWith(root + path.sep)) throw new Error('Render outside the immutable project');
  await fs.mkdir(destination);
  const receipt = { schema_version: 'creative-craft.local-render.v1', status: 'running', project_id: project.project_id,
    revision: project.revision, document_schema: project.schema_version, revision_sha256: await digest(revisionFile(root, project.revision)),
    engine: '@hyperframes/producer', engine_version: await packageVersion('@hyperframes/producer'), preview,
    started_at: new Date().toISOString(), assets: project.assets.map(({ id, sha256 }) => ({ id, sha256 })), ...(alignment ? { frame_alignment: alignment } : {}),
    capture: { width: capture.width, height: capture.height, factor: capture.factor, ...(scaled ? { downscale: 'ffmpeg scale flags=area' } : {}),
      ...(capture.factor === null ? { basis: 'export capture (an integer multiple of the preview would be larger)' } : {}) },
    inspection: { structure: 'pending', decode: 'pending', visual: 'unverified', listening: 'unverified' } };
  if (compiled.declick) receipt.declick = compiled.declick; // v2: lanes compiled without the cut-edge declick (512-point limit)
  receipt.caption_font = project.caption_font ? { ...project.caption_font, integrity: 'passed',
    glyph_coverage: 'passed', runtime_load: compiled.cues.length || compiled.graphics ? 'pending' : 'not_required', source_match: 'unverified' } :
    { profile: 'legacy-system-fonts', runtime_load: 'unverified', source_match: 'unverified' };
  const writeReceipt = async () => {
    const temp = path.join(destination, '.receipt.json');
    await fs.writeFile(temp, JSON.stringify(receipt, null, 2) + '\n');
    await fs.rename(temp, path.join(destination, 'receipt.json'));
  };
  await writeReceipt();
  try {
    signal?.throwIfAborted();
    await fs.writeFile(path.join(destination, 'project.json'), JSON.stringify(project, null, 2) + '\n', { flag: 'wx' });
    receipt.project_sha256 = await digest(path.join(destination, 'project.json'));
    await copyCaptionFont(root, destination, view, templates);
    await copyBoundTemplates(root, destination, project); // Pinned template bytes travel with the render.
    await fs.mkdir(path.join(destination, 'assets'));
    for (const asset of project.assets) {
      const target = path.join(destination, asset.file);
      try { await fs.copyFile(await safePath(path.join(root, asset.file)), target, 1); }
      catch (error) { if (error.code !== 'EEXIST') throw error; }
      if (await digest(target) !== asset.sha256) throw new Error('Asset changed while preparing render');
    }
    await fs.copyFile(require.resolve('gsap/dist/gsap.min.js'), path.join(destination, 'gsap.min.js'), 1);
    await fs.writeFile(path.join(destination, 'index.html'), compiled.html, { flag: 'wx' });
    receipt.composition_sha256 = await digest(path.join(destination, 'index.html'));
    receipt.templates = isV2(project) ? templateProvenance(project) : [];
    await fs.writeFile(path.join(destination, 'captions.vtt'), webVtt(compiled.cues), { flag: 'wx' });
    receipt.lint = await lintComposition(compiled.html);
    if (receipt.lint.blocked) throw new Error(`HyperFrames lint blocked render: ${receipt.lint.findings.filter(f => f.severity === 'error').map(f => f.code).join(', ')}`);
    signal?.throwIfAborted();
    const { createRenderJob, executeRenderJob } = await import('@hyperframes/producer');
    const quality = preview ? 'draft' : 'standard';
    const job = createRenderJob({ fps: project.canvas.fps, quality, format: 'mp4', workers: 1, useGpu: false, hdrMode: 'force-sdr', strictness: 'strict' });
    // When the capture size differs from the output the producer renders the
    // composition to capture.mp4, scaled back to video.mp4 here (scaleBack
    // removes the capture, and a partial video.mp4 on failure).
    const output = path.join(destination, 'video.mp4'), captured = scaled ? path.join(destination, 'capture.mp4') : output;
    try {
      // Only the browser capture is serialized (withRenderLock).
      await withRenderLock(() => executeRenderJob(job, destination, captured,
        (state, message) => onProgress({ status: state.status, progress: state.progress, message }), signal), signal);
      if (job.status !== 'complete' || job.warnings.length) throw new Error(`Unqualified render outcome: ${job.status}`);
    } catch (error) {
      if (scaled) await fs.rm(captured, { force: true });
      throw error;
    }
    if (scaled) await scaleBack(captured, output, { width, height }, signal);
    if (project.caption_font && (compiled.cues.length || compiled.graphics)) receipt.caption_font.runtime_load = 'passed';
    // HyperFrames' AAC true-peak limiter lowers the whole mix when it would pass
    // -1 dBTP and reports the attenuation on the job (absent = not engaged).
    if (expectsAudio(project, compiled.frames)) {
      const lowered = Number.isFinite(job.audioLoweredDb) ? job.audioLoweredDb : 0;
      receipt.audio_limiter = { ceiling_dbtp: -1, engaged: lowered > 0, audio_lowered_db: lowered, source: 'RenderJob.audioLoweredDb' };
    }
    const media = await probe(output);
    if (!media.video || media.width !== width || media.height !== height || media.audio !== expectsAudio(project, compiled.frames) ||
        Math.abs(media.duration - compiled.duration) > Math.max(0.1, 2 / project.canvas.fps)) throw new Error('Output media does not match the project');
    receipt.inspection.structure = 'passed';
    await run(mediaTool('ffmpeg'), ['-v', 'error', '-xerror', '-i', output, '-f', 'null', '-'], { timeout: 180000, maxBuffer: 1024 * 1024 });
    receipt.inspection.decode = 'passed';
    receipt.output = { file: 'video.mp4', sha256: await digest(output), ...media };
    receipt.status = 'completed';
    return receipt;
  } catch (error) {
    receipt.status = signal?.aborted ? 'cancelled' : 'failed';
    receipt.error = error.message;
    throw error;
  } finally {
    receipt.finished_at = new Date().toISOString();
    await writeReceipt();
  }
}
