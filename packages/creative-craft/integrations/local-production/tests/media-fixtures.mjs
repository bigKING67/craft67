// Short synthetic media and shared helpers for the media tests (render size,
// media time zero, frame alignment, the support matrix). Self-authored lavfi
// signals only; every file is a few hundred kilobytes.
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { run } from '../project.mjs';
import { mediaTool } from '../media-analysis.mjs';

// ffmpeg with -v error (the media tool the execution layer uses).
export const ffmpeg = (...args) => run(mediaTool('ffmpeg'), ['-v', 'error', ...args], { timeout: 120000 });

// A new directory under the real temporary directory (os.tmpdir() resolved,
// e.g. /private/var/… on macOS, so safePath comparisons hold).
export const tempDir = async prefix => fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), prefix));

// 'red' | 'blue' | 'green' for a clearly saturated mean RGB, else 'rgb(r, g, b)'.
export function colourOf([r, g, b]) {
  if (r > 150 && g < 80 && b < 80) return 'red';
  if (b > 150 && r < 80 && g < 80) return 'blue';
  if (g > 100 && r < 80 && b < 80) return 'green';
  return `rgb(${[r, g, b].map(Math.round).join(', ')})`;
}

const VIDEO = {
  h264: ['-c:v', 'libx264', '-preset', 'ultrafast'],
  hevc: ['-c:v', 'libx265', '-preset', 'ultrafast', '-x265-params', 'log-level=error', '-tag:v', 'hvc1'],
  vp9: ['-c:v', 'libvpx-vp9', '-deadline', 'realtime', '-cpu-used', '8'],
};
const AUDIO = {
  aac: ['-c:a', 'aac'], mp3: ['-c:a', 'libmp3lame'], opus: ['-c:a', 'libopus'], pcm: ['-c:a', 'pcm_s16le'],
  flac: ['-c:a', 'flac'], alac: ['-c:a', 'alac'],
};
const encoder = (table, name) => table[name] ?? (() => { throw new Error(`Unknown codec ${name}`); })();

// Video `seconds` long at `rate`, solid `color`, with an optional sine track.
// options: { vcodec: 'h264'|'hevc'|'vp9', pix: 'yuv420p'…, acodec, size, rate,
//   seconds, color, vfr (drop 2 of every 5 frames: variable frame rate),
//   rotate (display-matrix degrees), right (colour of the right half, e.g.
//   'blue': left half `color`, right half `right`), extra: [...output args] }
export async function synthVideo(file, { vcodec = 'h264', pix = 'yuv420p', acodec = null, size = '320x240', rate = 30, seconds = 2,
  color = 'red', right = null, vfr = false, rotate = null, extra = [] } = {}) {
  const halves = right ? `,drawbox=x=iw/2:y=0:w=iw/2:h=ih:color=${right}:t=fill` : '';
  const inputs = ['-f', 'lavfi', '-i', `color=c=${color}:s=${size}:r=${rate}:d=${seconds}${halves}`];
  if (acodec) inputs.push('-f', 'lavfi', '-i', `sine=frequency=440:sample_rate=48000:duration=${seconds}`);
  const audio = acodec ? ['-map', '1:a', ...encoder(AUDIO, acodec)] : [];
  const target = rotate === null ? file : `${file}.unrotated${file.slice(file.lastIndexOf('.'))}`;
  const variable = vfr ? ['-vf', 'select=lt(mod(n\\,5)\\,3)', '-fps_mode', 'vfr'] : [];
  await ffmpeg('-y', ...inputs, '-map', '0:v', ...variable, ...encoder(VIDEO, vcodec), '-pix_fmt', pix, ...audio, ...extra, '-t', String(seconds), target);
  if (rotate !== null) {
    await ffmpeg('-y', '-display_rotation', String(rotate), '-i', target, '-map', '0', '-c', 'copy', file);
    await fs.rm(target);
  }
  return file;
}

// 30 fps 320x180 video: red frames 0..switchFrame-1, blue from switchFrame on,
// every frame a keyframe, with an optional sine track. `args` go before the
// output (e.g. -output_ts_offset, -avoid_negative_ts); `audioArgs` before the
// sine input (e.g. -itsoffset -0.067).
export async function synthRedThenBlue(file, { switchFrame, seconds, acodec = null, args = [], audioArgs = [] }) {
  const audio = acodec ? [...audioArgs, '-f', 'lavfi', '-i', `sine=d=${seconds}`] : [];
  await ffmpeg('-y', '-f', 'lavfi', '-i', `color=red:s=320x180:r=30:d=${switchFrame / 30}`, '-f', 'lavfi', '-i', `color=blue:s=320x180:r=30:d=${seconds - switchFrame / 30}`,
    ...audio, '-filter_complex', '[0:v][1:v]concat=n=2:v=1,format=yuv420p[v]', '-map', '[v]', ...(acodec ? ['-map', '2:a', ...encoder(AUDIO, acodec)] : []),
    '-c:v', 'libx264', '-g', '1', ...args, file);
  return file;
}

// Audio-only sine `seconds` long.
export async function synthAudio(file, { acodec = 'aac', seconds = 2, extra = [] } = {}) {
  await ffmpeg('-y', '-f', 'lavfi', '-i', `sine=frequency=440:sample_rate=48000:duration=${seconds}`, ...encoder(AUDIO, acodec), ...extra, file);
  return file;
}

// Colour name (colourOf) of decoded frame `n` (region as frameColor).
export const frameColour = async (file, n = 0, region) => colourOf(await frameColor(file, n, region));

// Frame regions (ffmpeg crop arguments): the centre quarter, the middle
// half-height band of the left and right quarters, the top and bottom eighths
// of the centre half width (inside the picture of a pillarboxed rotated source).
export const REGION = Object.freeze({ centre: 'iw/2:ih/2', left: 'iw/4:ih/2:0:ih/4', right: 'iw/4:ih/2:iw*3/4:ih/4',
  top: 'iw/2:ih/8:iw/4:0', bottom: 'iw/2:ih/8:iw/4:ih*7/8' });

// Mean RGB of a region (default the centre quarter) of decoded frame `n` of `file` (select=eq(n,N)).
export async function frameColor(file, n = 0, region = REGION.centre) {
  const { stdout } = await run(mediaTool('ffmpeg'), ['-v', 'error', '-i', file, '-vf', `select=eq(n\\,${n}),crop=${region},scale=16:16`, '-frames:v', '1',
    '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], { encoding: 'buffer', maxBuffer: 1024 * 1024 });
  const sum = [0, 0, 0];
  for (let i = 0; i < stdout.length; i++) sum[i % 3] += stdout[i];
  return sum.map(v => v / (stdout.length / 3));
}

// Mean volume (dB) of the first audio stream; -Infinity when silent or absent.
export async function meanVolume(file) {
  const { stderr } = await run(mediaTool('ffmpeg'), ['-v', 'info', '-nostats', '-i', file, '-map', '0:a:0?', '-af', 'volumedetect', '-f', 'null', '-'],
    { maxBuffer: 4 * 1024 * 1024 });
  const m = /mean_volume:\s*(-?[\d.]+|-inf) dB/.exec(stderr);
  return m && m[1] !== '-inf' ? Number(m[1]) : -Infinity;
}

// A 0.6.0 project: frame_rate written on an asset the 0.7.0 import rule would
// not give one (audio starting before the video). The revision file is edited
// by hand to simulate it; the code under test never writes it.
export async function agedProject(root, asset = 'src', frameRate = '30/1') {
  const file = path.join(root, 'revisions', '000001.json'), doc = JSON.parse(await fs.readFile(file, 'utf8'));
  doc.assets.find(a => a.id === asset).frame_rate = frameRate;
  await fs.chmod(file, 0o644);
  await fs.writeFile(file, JSON.stringify(doc, null, 2) + '\n');
  return file;
}
