import * as fs from 'node:fs/promises';
import path from 'node:path';
import { run } from './project.mjs';
import { mediaTool } from './media-analysis.mjs';

// Signal-level checks complement (and do not replace) human playback/listening.
const ffmpeg = () => mediaTool('ffmpeg');
export const frameAt = async (file, time, filter) => (await run(ffmpeg(), ['-v', 'error', '-ss', String(time), '-i', file,
  '-vf', filter, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], { encoding: 'buffer', maxBuffer: 1024 * 1024 })).stdout;
export const pcmAt = async (file, time) => (await run(ffmpeg(), ['-v', 'error', '-ss', String(time), '-i', file,
  '-t', '0.125', '-vn', '-ac', '1', '-ar', '8000', '-f', 'f32le', 'pipe:1'], { encoding: 'buffer' })).stdout;
export function mae(actual, expected) {
  if (!actual.length || expected.length !== actual.length) throw new Error('Invalid decoded frame size');
  return actual.reduce((sum, value, i) => sum + Math.abs(value - expected[i]), 0) / actual.length;
}
export function tonePower(pcm, hz) {
  let re = 0, im = 0;
  for (let i = 0; i < pcm.length / 4; i++) {
    const value = pcm.readFloatLE(i * 4), phase = 2 * Math.PI * hz * i / 8000;
    re += value * Math.cos(phase); im += value * Math.sin(phase);
  }
  return re * re + im * im;
}

export async function verifySmoke(base) {
  const samples = [
    ['talking-head-preview', 0.25, 0.25, 440], ['talking-head-preview', 1.25, 3.25, 880],
    ['brand-export', 0.25, 3.25, 880], ['brand-export', 1.25, 0.25, 440],
    ['commerce-export', 0.25, 4.25, 880], ['commerce-export', 0.75, 0.25, 440],
  ];
  const top = 'crop=iw:ih/2:0:0,scale=64:18';
  const results = [];
  for (const [name, time, sourceTime, frequency] of samples) {
    const file = path.join(base, name, 'video.mp4');
    const actual = await frameAt(file, time, top), expected = await frameAt(path.join(base, 'source.mp4'), sourceTime, top);
    if (actual.length !== 3456) throw new Error('Invalid decoded frame size');
    const picture = mae(actual, expected);
    if (picture > 18) throw new Error(`${name}@${time}: picture does not match source ${sourceTime} (MAE ${picture})`);
    const pcm = await pcmAt(file, time);
    const wanted = tonePower(pcm, frequency), other = tonePower(pcm, frequency === 440 ? 880 : 440);
    if (wanted < 1 || wanted < other * 10) throw new Error(`${name}@${time}: wrong/silent audio source`);
    results.push({ name, time, source_time: sourceTime, picture_mae: picture, tone_hz: frequency, signal: 'passed' });
  }
  await fs.writeFile(path.join(base, 'signal-checks.json'), JSON.stringify({ checks: results, human_listening: 'unverified' }, null, 2));
  return results;
}

const meanLuma = rgb => { let sum = 0; for (let i = 0; i < rgb.length; i += 3) sum += 0.299 * rgb[i] + 0.587 * rgb[i + 1] + 0.114 * rgb[i + 2]; return sum / (rgb.length / 3); };
const share = (rgb, test) => { let n = 0; for (let i = 0; i < rgb.length; i += 3) if (test(rgb[i], rgb[i + 1], rgb[i + 2])) n++; return n / (rgb.length / 3); };
const db = (a, b) => 10 * Math.log10(a / b);

// P2 brand packaging export (24 fps, 1280x720). Expectations are computed from
// the edit document the smoke builds: main1 talk 0–72 (fade in 12), main2 bars
// 60–120 crossfading in over 12, main3 talk 120–168 at 1.5× from source 2.5 s
// (fade out 12); title card 0–36, lower third 76–116 (over the bars); music ducked −12 dB under
// v_main speech (0–3 s, 5–7 s), fade in 12 / out 24.
export async function verifyBrand(base, name, { depthDb }) {
  const file = path.join(base, name, 'video.mp4'), talk = path.join(base, 'source.mp4'), bars = path.join(base, 'broll.mp4');
  // Input seeking keeps the first frame with pts >= t: seek a quarter frame early to land on frame k.
  const at = frame => Math.max(0, (frame - 0.25) / 24), top = 'crop=iw:ih/2:0:0,scale=64:18';
  const checks = {};
  // Speed: output frame 132 shows source 2.5 + 12/24 × 1.5 = 3.25 s, not the 1× position 3.0 s.
  const sped = await frameAt(file, at(132), top);
  const speed = { expected_source: 3.25, mae_expected: mae(sped, await frameAt(talk, at(78), top)), mae_if_1x: mae(sped, await frameAt(talk, at(72), top)) };
  if (speed.mae_expected > 18 || speed.mae_expected * 2 > speed.mae_if_1x) throw new Error(`${name}: speed-changed picture is not at source 3.25 s ${JSON.stringify(speed)}`);
  checks.speed = speed;
  // Crossfade mid-point (frame 66 of overlap 60–72): a 50/50 mix of talk @2.75 s and bars.
  const mixed = await frameAt(file, at(66), top), a = await frameAt(talk, at(66), top), b = await frameAt(bars, at(6), top);
  const blend = Buffer.from(a.map((v, i) => Math.round((v + b[i]) / 2)));
  const crossfade = { mae_blend: mae(mixed, blend), mae_outgoing: mae(mixed, a), mae_incoming: mae(mixed, b) };
  if (crossfade.mae_blend > 12 || crossfade.mae_blend * 2 > Math.min(crossfade.mae_outgoing, crossfade.mae_incoming)) throw new Error(`${name}: crossfade mid-point is not a two-source mix ${JSON.stringify(crossfade)}`);
  checks.crossfade = crossfade;
  // Picture fades: the top band (outside both graphics) starts black and ends near black.
  const band = 'crop=iw:ih/4:0:0,scale=64:9';
  const fades = { luma_frame0: meanLuma(await frameAt(file, at(0), band)), luma_frame30: meanLuma(await frameAt(file, at(30), band)),
    luma_frame150: meanLuma(await frameAt(file, at(150), band)), luma_frame167: meanLuma(await frameAt(file, at(167), band)) };
  if (fades.luma_frame0 > 8 || fades.luma_frame30 < 40 || fades.luma_frame167 > fades.luma_frame150 * 0.2) throw new Error(`${name}: picture fades not observed ${JSON.stringify(fades)}`);
  checks.fades = fades;
  // Ducking: 660 Hz music energy inside speech vs the open window between speech (3.5–4.75 s).
  const music = async time => tonePower(await pcmAt(file, time), 660);
  const open = await music(4.0), duckedEarly = await music(1.5), duckedLate = await music(5.75);
  const ducking = { depth_db: depthDb, open_power: open, ducked_db_at_1_5s: db(duckedEarly, open), ducked_db_at_5_75s: db(duckedLate, open),
    fade_in_db_at_0s: db(await music(0), duckedEarly) };
  for (const value of [ducking.ducked_db_at_1_5s, ducking.ducked_db_at_5_75s]) {
    if (open < 1 || Math.abs(value - depthDb) > 2) throw new Error(`${name}: music not ducked by ~${depthDb} dB ${JSON.stringify(ducking)}`);
  }
  if (ducking.fade_in_db_at_0s > -10) throw new Error(`${name}: music fade-in not observed ${JSON.stringify(ducking)}`);
  checks.ducking = ducking;
  // Template text visible: title-card box (frame 18, over talk) and the lower-third plate's
  // text area (frame 96, over bars; the plate is bottom-left aligned inside its template box)
  // differ from the picture underneath and contain white text on a dark plate.
  const graphic = async (frame, crop, reference, sourceTime) => {
    const shot = await frameAt(file, at(frame), crop), under = await frameAt(reference, sourceTime, `scale=1280:720,${crop}`);
    return { mae_vs_picture_underneath: mae(shot, under), white_share: share(shot, (r, g, bl) => r > 200 && g > 200 && bl > 200),
      dark_share: share(shot, (r, g, bl) => 0.299 * r + 0.587 * g + 0.114 * bl < 45) };
  };
  const titleCard = await graphic(18, 'crop=1024:288:128:216', talk, at(18)), lowerThird = await graphic(96, 'crop=120:60:77:586', bars, at(36));
  for (const [label, g] of [['title card', titleCard], ['lower third', lowerThird]]) {
    if (g.mae_vs_picture_underneath < 25 || g.white_share < 0.003 || g.dark_share < 0.2) throw new Error(`${name}: ${label} text not visible ${JSON.stringify(g)}`);
  }
  checks.graphics = { title_card: titleCard, lower_third: lowerThird };
  return checks;
}

// v2 multi-track export: main picture outside the B-roll box, B-roll inside it
// (z order + transform), and the music bed mixed with the main track's tone.
export async function verifyMultitrack(base, name) {
  const file = path.join(base, name, 'video.mp4'), source = path.join(base, 'source.mp4'), broll = path.join(base, 'broll.mp4');
  const box = 'crop=512:288:704:36,scale=64:36', left = 'crop=600:260:0:300,scale=60:26', sourceLeft = 'crop=300:130:0:150,scale=60:26';
  const checks = [];
  const compare = async (label, time, filter, reference, referenceTime, referenceFilter, limit = 18) => {
    const value = mae(await frameAt(file, time, filter), await frameAt(reference, referenceTime, referenceFilter));
    checks.push({ label, time, mae: value });
    if (value > limit) throw new Error(`${name}@${time}: ${label} (MAE ${value})`);
  };
  await compare('main picture before B-roll', 0.25, left, source, 0.25, sourceLeft);
  await compare('B-roll inside its transform box', 1.0, box, broll, 0.5, 'scale=64:36');
  await compare('main picture beside B-roll', 1.0, left, source, 1.0, sourceLeft);
  const outside = mae(await frameAt(file, 0.25, box), await frameAt(broll, 0.5, 'scale=64:36'));
  if (outside < 30) throw new Error(`${name}: B-roll box visible before its start (MAE ${outside})`);
  checks.push({ label: 'B-roll absent before start', time: 0.25, mae: outside });
  for (const [time, main] of [[0.25, 440], [2.25, 880]]) {
    const pcm = await pcmAt(file, time);
    const music = tonePower(pcm, 660), dialogue = tonePower(pcm, main), wrong = tonePower(pcm, main === 440 ? 880 : 440);
    if (music < 1 || dialogue < 1 || dialogue < wrong * 10) throw new Error(`${name}@${time}: expected ${main} Hz main tone and 660 Hz music bed`);
    checks.push({ label: 'main tone + music bed', time, main_hz: main, music_power: music, dialogue_power: dialogue });
  }
  return checks;
}

// Self-authored portrait source with a burned-in "caption": a row of white
// glyph boxes with dark strokes at ~70% height over a moving test pattern. The
// caption switches from line A to line B at changeAt seconds; without changeAt
// the source has no caption. shortShot = [from, to] cuts to colour bars inside
// the file (a short shot within one asset).
// slowFrom: frames after that many seconds are retimed to 15 fps (1/15 s apart; the lowest rate the caption check pads for)
// while earlier ones stay at 30 fps, giving a variable-frame-rate file.
export async function captionSource(file, { duration = 3, changeAt, shortShot, size = '360x640', slowFrom } = {}) {
  const [w, h] = size.split('x').map(Number), y = Math.round(h * 0.7), gh = Math.round(h * 0.03);
  const glyphs = (xs, width, when) => xs.flatMap(x => [`drawbox=x=${x - 3}:y=${y - 3}:w=${width + 6}:h=${gh + 6}:color=black:t=fill:enable='${when}'`,
    `drawbox=x=${x}:y=${y}:w=${width}:h=${gh}:color=white:t=fill:enable='${when}'`]);
  const caption = changeAt === undefined ? [] : [...glyphs([0.15, 0.27, 0.39, 0.51, 0.63].map(f => Math.round(f * w)), Math.round(w * 0.07), `lt(t,${changeAt})`),
    ...glyphs([0.2, 0.36, 0.52, 0.68].map(f => Math.round(f * w)), Math.round(w * 0.1), `gte(t,${changeAt})`)];
  const source = `testsrc2=size=${size}:rate=30:duration=${duration}`;
  const inputs = ['-f', 'lavfi', '-i', source, ...(shortShot ? ['-f', 'lavfi', '-i', `smptehdbars=size=${size}:rate=30:duration=${duration}`] : [])];
  const retime = slowFrom === undefined ? [] : [`setpts='if(lt(N,${slowFrom * 30}),N/30,${slowFrom}+(N-${slowFrom * 30})/15)/TB'`];
  const chain = [...(shortShot || retime.length ? [] : ['null']), ...retime, ...caption].join(',');
  const graph = shortShot ? `[0:v][1:v]overlay=enable='between(t,${shortShot[0]},${shortShot[1] - 0.001})'${caption.length ? ',' + caption.join(',') : ''}[v]` : `[0:v]${chain}[v]`;
  await run(ffmpeg(), ['-v', 'error', '-n', ...inputs, '-filter_complex', graph, '-map', '[v]', ...(retime.length ? ['-fps_mode', 'vfr'] : []), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', file]);
}
