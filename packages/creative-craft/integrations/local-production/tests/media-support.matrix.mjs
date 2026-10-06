// Render-support matrix runner (explicit opt-in, real producer + Chrome):
//   PRODUCER_HEADLESS_SHELL_PATH=… node tests/media-support.matrix.mjs [--json]
// Each case (tests/media-support-cases.mjs) is a 1 s synthetic source imported
// into a v2 project (createProject), rendered as a preview, then judged:
// completed, the centre of the first frame shows the source colour, and (cases
// with audio) the output carries the tone (mean volume above -40 dB). The
// first frame is judged in three regions (top eighth, centre quarter, bottom
// eighth), so a picture that covers only part of the frame fails. Every
// step of a case (synthesis, probe, project, render, judgement) runs inside the
// case: a failing case is one failed row and never stops the others. The
// temporary directory is removed after all cases. When run directly, the
// producer's capture stall watchdog is shortened (HF_DE_STALL_MS, default 60 s)
// so a stalling case fails in ~15 s instead of 60 s and upstream console
// diagnostics are silenced. Cases run one at a time: renders running
// concurrently in one process were measured to corrupt each other's picture
// (the video covering only the top part of the frame); MATRIX_CONCURRENCY
// overrides it for reproducing that. Importing this module has no side
// effects. Results: README「素材兼容」.
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createProject, ffprobeJson } from '../project.mjs';
import { renderProject } from '../render.mjs';
import { mapLimit } from '../media-analysis.mjs';
import { REGION, frameColour, meanVolume, synthAudio, synthVideo, tempDir } from './media-fixtures.mjs';
import { CASES, caseSpec } from './media-support-cases.mjs';

// options: seconds (source length), sourceIn (in-point), size ('WxH', source
// and canvas), full (export instead of preview).
export async function runCase(testCase, dir, { seconds = 1, sourceIn = 0, size = '320x240', full = false } = {}) {
  const [label, kind, name, options] = testCase, [width, height] = size.split('x').map(Number);
  const row = { label, kind, container: path.extname(name).slice(1), video: null, audio: null, ok: false };
  const started = Date.now();
  let step = 'synthesis';
  try {
    const work = path.join(dir, name.replace(/\W/g, '_')), source = path.join(work, name), out = path.join(work, 'render');
    await fs.mkdir(work);
    if (kind === 'video') await synthVideo(source, { seconds, size, ...options });
    else await synthAudio(source, { seconds, ...options });
    const background = kind === 'audio' ? await synthVideo(path.join(work, 'bg.mp4'), { seconds, size }) : undefined;
    step = 'probe';
    const info = await ffprobeJson(source), v = info.streams.find(s => s.codec_type === 'video'), a = info.streams.find(s => s.codec_type === 'audio');
    Object.assign(row, { format: info.format.format_name, video: v ? `${v.codec_name}/${v.profile ?? '-'}/${v.pix_fmt}` : null, audio: a?.codec_name ?? null });
    step = 'project';
    await createProject(path.join(work, 'project'), caseSpec(testCase, { source, background, width, height, sourceIn }));
    step = 'render';
    await renderProject(path.join(work, 'project'), out, { preview: !full, signal: AbortSignal.timeout(120000) });
    step = 'judgement';
    const regions = [];
    for (const region of ['top', 'centre', 'bottom']) regions.push(await frameColour(path.join(out, 'video.mp4'), 0, REGION[region]));
    row.first_frame = new Set(regions).size === 1 ? regions[0] : `top/centre/bottom ${regions.join(' / ')}`;
    if (a) row.mean_volume_db = Math.round(await meanVolume(path.join(out, 'video.mp4')));
    row.ok = row.first_frame === 'red' && (!a || row.mean_volume_db > -40);
  } catch (error) {
    row.error = `${step} failed: ${error.message.split('\n')[0].slice(0, 160)}`;
  }
  row.seconds = Math.round((Date.now() - started) / 1000);
  return row;
}

// All cases matching `only` (regex on the file name), `limit` at a time (see
// above: keep 1 for trustworthy results), in one
// temporary directory removed afterwards. Never rejects because of a case.
export async function runMatrix({ only = /./, limit = 1, ...options } = {}) {
  const dir = await tempDir('media-matrix-');
  try {
    return await mapLimit(CASES.filter(c => only.test(c[2])), limit, c => runCase(c, dir, options));
  } finally { await fs.rm(dir, { recursive: true, force: true }); }
}

export const markdownTable = rows => '| 用例 | 用途 | 容器 | 视频 | 音频 | 结果 | 用时 |\n|---|---|---|---|---|---|---|\n' +
  rows.map(r => `| ${r.label} | ${r.kind === 'video' ? '视频' : '独立音频'} | ${r.container} | ${r.video ?? '—'} | ${r.audio ?? '—'} | ${r.ok ? '可渲染'
    : `失败：${r.error ?? `首帧 ${r.first_frame}，音量 ${r.mean_volume_db} dB`}`} | ${r.seconds} s |\n`).join('');

// Direct execution only. Knobs for reproducing heavier sources: MATRIX_ONLY
// (regex on the file name), MATRIX_SECONDS (source length, default 1),
// MATRIX_IN (in-point, default 0), MATRIX_SIZE (source and canvas WxH, default
// 320x240), MATRIX_FULL=1 (export instead of preview), MATRIX_CONCURRENCY
// (cases at a time, default 1).
const direct = process.argv[1] && await fs.realpath(process.argv[1]).then(file => file === fileURLToPath(import.meta.url), () => false);
if (direct) {
  if (!process.env.PRODUCER_HEADLESS_SHELL_PATH) throw new Error('Set PRODUCER_HEADLESS_SHELL_PATH for the support matrix');
  process.env.HF_DE_STALL_MS ??= '15000';
  console.log = console.info = console.warn = () => {}; // upstream capture diagnostics
  const env = process.env;
  const rows = await runMatrix({ only: new RegExp(env.MATRIX_ONLY ?? '.'), seconds: Number(env.MATRIX_SECONDS ?? 1), sourceIn: Number(env.MATRIX_IN ?? 0),
    size: env.MATRIX_SIZE ?? '320x240', full: env.MATRIX_FULL === '1', limit: Number(env.MATRIX_CONCURRENCY ?? 1) });
  process.stdout.write(process.argv.includes('--json') ? JSON.stringify(rows, null, 2) + '\n' : markdownTable(rows));
  if (rows.some(r => !r.ok)) process.exitCode = 1;
}
