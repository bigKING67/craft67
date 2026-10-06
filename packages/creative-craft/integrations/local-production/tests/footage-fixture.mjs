// Synthetic footage for the analyze / suggest-cuts tests: self-authored lavfi
// signals only, a few hundred kilobytes.
//
// 4 s, 30 fps, 320x240, every frame a keyframe:
//   - picture red for frames 0–44, blue from frame 45 (a hard shot change at 1.5 s);
//   - a white "caption" box in the caption band (rows 170–185 of 240, 71–77 %)
//     at x 40–159 for frames 0–74 and at x 160–279 from frame 75 (a burned
//     caption change at 2.5 s that leaves the rest of the frame unchanged);
//   - a 440 Hz tone ("speech") over 0.3–0.9 s, 1.1–2.2 s and 2.6–3.6 s, silence between.
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { digest } from '../project.mjs';
import { TRANSCRIPT_SCHEMA } from '../asr.mjs';
import { ffmpeg } from './media-fixtures.mjs';

export const FOOTAGE = Object.freeze({ fps: 30, seconds: 4, shot_frame: 45, caption_frame: 75, speech: [[0.3, 0.9], [1.1, 2.2], [2.6, 3.6]] });

export async function synthFootage(file) {
  const tone = FOOTAGE.speech.map(([a, b]) => `between(t,${a},${b})`).join('+');
  await ffmpeg('-y', '-f', 'lavfi', '-i', `color=red:s=320x240:r=30:d=${FOOTAGE.seconds}`,
    '-f', 'lavfi', '-i', `aevalsrc='0.5*sin(2*PI*440*t)*(${tone})':s=48000:d=${FOOTAGE.seconds}`,
    '-filter_complex', `[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=blue:t=fill:enable='gte(n,${FOOTAGE.shot_frame})',` +
      `drawbox=x=40:y=170:w=120:h=16:color=white:t=fill:enable='lt(n,${FOOTAGE.caption_frame})',` +
      `drawbox=x=160:y=170:w=120:h=16:color=white:t=fill:enable='gte(n,${FOOTAGE.caption_frame})',format=yuv420p[v]`,
    '-map', '[v]', '-map', '1:a', '-c:v', 'libx264', '-preset', 'ultrafast', '-g', '1', '-c:a', 'pcm_s16le', '-t', String(FOOTAGE.seconds), file);
  return file;
}

// Same tone bursts (audio-local FOOTAGE.speech) in an audio stream that starts
// `offset` seconds after the picture (-itsoffset: the mov edit list gives the
// audio stream start_time = offset); a static grey picture without shot or
// caption changes. Media time of a burst = its audio-local time + offset.
export async function synthOffsetFootage(file, offset) {
  const tone = FOOTAGE.speech.map(([a, b]) => `between(t,${a},${b})`).join('+');
  await ffmpeg('-y', '-f', 'lavfi', '-i', `color=gray:s=320x240:r=30:d=${FOOTAGE.seconds}`,
    '-itsoffset', String(offset), '-f', 'lavfi', '-i', `aevalsrc='0.5*sin(2*PI*440*t)*(${tone})':s=48000:d=${FOOTAGE.seconds - offset}`,
    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'ultrafast', '-g', '1', '-pix_fmt', 'yuv420p', '-c:a', 'pcm_s16le', file);
  return file;
}

// A transcript (asr.mjs format) whose phrases are the tone bursts.
export async function footageTranscript(media, file, texts = ['第一句话。', '第二句话，', '第三句话。']) {
  const phrases = FOOTAGE.speech.map(([start, end], i) => ({ start, end, text: texts[i] }));
  await fs.writeFile(file, JSON.stringify({ schema: TRANSCRIPT_SCHEMA, media: { path_basename: path.basename(media), sha256: await digest(media), duration: FOOTAGE.seconds },
    segments: phrases, phrases }));
  return file;
}
