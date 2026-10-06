import * as fs from 'node:fs/promises';
import path from 'node:path';
import { TOOL, digest, ffprobeJson, loadProject, run, safePath, validateDocument, migrateV1, SCHEMA_V2 } from './project.mjs';
import { audibleItems, resolveCaptions } from './timeline.mjs';
import { legacyAlignment } from './frame-alignment.mjs';
import { bindAlignment, compiledView } from './source-frames.mjs';
import { outputSize, revisionFile } from './render.mjs';
import { captionBox, graphicBox, insideSafeArea } from './safe-area.mjs';
import { templateSet } from './templates.mjs';
import { captionBand } from './burned-captions.mjs';
import { cutPointChecks } from './cut-checks.mjs';
import { ANALYSIS_SCHEMA } from './analyze.mjs';
import { APPLIED_SCHEMA } from './apply-cuts.mjs';
import { audioCutPoints, clickCheck } from './audio-clicks.mjs';
import { reviewPageFor, writeReviewPage } from './review-page.mjs';
import { ebur128Summary, logSegments, mediaTool, overlap, silenceFilter, silences, union } from './media-analysis.mjs';

// Technical checks on one actual rendered file of one revision. Automated
// results never stand in for the composited-frame review, which starts pending.
const ffmpeg = () => mediaTool('ffmpeg');
const fail = message => { throw new Error(message); };
const round = (value, digits = 3) => Math.round(value * 10 ** digits) / 10 ** digits;

async function filterLog(args) {
  // Filter reports are info-level stderr lines; the process must still succeed.
  const { stderr } = await run(ffmpeg(), ['-hide_banner', '-nostats', ...args, '-f', 'null', '-'], { timeout: 600000, maxBuffer: 64 * 1024 * 1024 });
  return stderr;
}

async function probeRender(file) {
  const result = await ffprobeJson(file);
  const video = result.streams.find(s => s.codec_type === 'video') ?? fail('Rendered file has no video stream');
  const [num, den] = String(video.avg_frame_rate || video.r_frame_rate).split('/').map(Number);
  const duration = Number(video.duration) || Number(result.format.duration);
  return { width: video.width, height: video.height, fps: den ? num / den : num, duration,
    start_time: Number(video.start_time) || 0, has_audio: result.streams.some(s => s.codec_type === 'audio'),
    audio_start_time: Number(result.streams.find(s => s.codec_type === 'audio')?.start_time) || 0 };
}

// Shot boundaries of the rendered file: frames whose ffmpeg scene score (0–1,
// change against the previous frame) exceeds the threshold start a new shot.
export const SCENE_THRESHOLD = 0.3;
export async function detectShots(file, duration, threshold = SCENE_THRESHOLD) {
  const log = await filterLog(['-i', file, '-an', '-vf', `select='gt(scene,${threshold})',showinfo`]);
  const starts = [...log.matchAll(/pts_time:\s*([\d.]+)/g)].map(m => Number(m[1])).filter(t => t > 0 && t < duration);
  const edges = [0, ...new Set(starts.sort((a, b) => a - b)), duration];
  return edges.slice(0, -1).map((start, i) => ({ start, end: edges[i + 1] }));
}
// production: the production root (production.json directory) for the review
// page's sign-off command; null leaves a placeholder there.
// analyses: footage-analysis files (analyze --asr) of the project's assets; their
// ASR phrases add caption-speech-sync.
export function qaOptions({ captionBand: band, sceneThreshold = SCENE_THRESHOLD, production = null, analyses = [], decisions = null } = {}) {
  if (decisions !== null && (typeof decisions !== 'string' || !decisions)) fail('Decisions must be a file path');
  if (typeof sceneThreshold !== 'number' || !(sceneThreshold > 0 && sceneThreshold < 1)) fail('Scene threshold must be a number between 0 and 1 (exclusive)');
  if (production !== null && (typeof production !== 'string' || !production)) fail('Production must be a directory path');
  if (!Array.isArray(analyses) || !analyses.every(a => typeof a === 'string' && a)) fail('Analyses must be file paths');
  return { band: captionBand(band), sceneThreshold, production, analyses, decisions };
}

// Edit decisions from an apply-cuts result (--decisions): a warned cut-point
// finding is 'accepted' when a decision for the same item edge and asset, at
// the same source time, accepts every cut rule the finding comes from
// (keep_speech: the rule it kept the speech against). Same time: within half an
// output frame (the item length is rounded to whole output frames) plus half a
// source frame and the 6-decimal rounding of reports; an edge moved by a frame
// since the decision is judged as usual. A file that is not an apply-cuts
// result, a malformed decision, one made before rules were recorded (accepts
// null: rerun suggest-cuts and apply-cuts) or one for an item or asset this
// revision does not have is an error, never a silent "nothing accepted".
export async function decisionAcceptor(doc, file) {
  const applied = JSON.parse(await fs.readFile(await safePath(file), 'utf8'));
  if (applied?.schema !== APPLIED_SCHEMA) fail(`${file} is not a ${APPLIED_SCHEMA} file (apply-cuts output)`);
  const list = Array.isArray(applied.decisions) ? applied.decisions : fail(`${file} has no decisions (an apply-cuts result from before 0.13; rerun apply-cuts)`);
  list.forEach((d, i) => {
    const ok = typeof d?.beat === 'string' && ['in', 'out'].includes(d.edge) && typeof d.option === 'string' && typeof d.by === 'string'
      && Number.isFinite(d.seconds) && typeof d.asset_id === 'string' && (d.accepts === null || (Array.isArray(d.accepts) && d.accepts.every(r => typeof r === 'string')));
    if (!ok) fail(`${file}: decisions[${i}] needs beat, edge in/out, option, by, numeric seconds, asset_id and accepts`);
    if (d.accepts === null) fail(`${file}: decisions[${i}] (${d.beat} ${d.edge}) comes from a suggest-cuts result before 0.13 that did not record which rules ${d.option} accepts; rerun suggest-cuts and apply-cuts`);
  });
  const items = new Map(doc.items.map(i => [i.id, i]));
  const unknown = list.filter(d => !items.has(d.beat));
  if (unknown.length) fail(`${file} decides item(s) ${[...new Set(unknown.map(d => d.beat))].join(', ')} that this revision does not have`);
  const otherAsset = list.filter(d => items.get(d.beat).asset_id !== d.asset_id);
  if (otherAsset.length) fail(`${file} decides ${otherAsset.map(d => `${d.beat} on asset ${d.asset_id}`).join(', ')}, but this revision uses ${otherAsset.map(d => items.get(d.beat).asset_id).join(', ')}`);
  const sourceFps = id => { const [n, m = 1] = String(doc.assets.find(a => a.id === id)?.frame_rate ?? '').split('/').map(Number); return n > 0 && m > 0 ? n / m : doc.canvas.fps; };
  return (entry, rules) => {
    const d = list.find(x => x.beat === entry.item_id && x.edge === entry.edge);
    if (!d || !rules.every(r => d.accepts.includes(r))) return null;
    const tolerance = 0.5 / doc.canvas.fps + 0.5 / sourceFps(d.asset_id) + 1e-6;
    return Math.abs(d.seconds - entry.source_seconds) <= tolerance ? { by: d.by, option: d.option, rules } : null;
  };
}

// ASR phrases per asset id from footage-analysis files, matched by the media
// SHA-256 the analysis recorded. An analysis of no asset, of the same asset
// twice, or without phrases is an error (a silent skip would read as a pass).
export async function assetPhrases(doc, files) {
  const byId = new Map();
  for (const file of files) {
    const analysis = JSON.parse(await fs.readFile(await safePath(file), 'utf8'));
    if (analysis?.schema !== ANALYSIS_SCHEMA) fail(`${file} is not a ${ANALYSIS_SCHEMA} file`);
    const assets = doc.assets.filter(a => a.sha256 === analysis.media?.sha256);
    if (!assets.length) fail(`${file} analyses ${analysis.media?.path_basename ?? 'unknown media'} (SHA-256 ${String(analysis.media?.sha256).slice(0, 12)}…), which is not an asset of this revision`);
    const phrases = analysis.speech?.phrases ?? [];
    if (!phrases.length) fail(`${file} has no ASR phrases (run analyze with --asr or --transcript)`);
    // A malformed phrase would make every in-point quietly "clear".
    const bad = phrases.findIndex(ph => !(Number.isFinite(ph?.start) && Number.isFinite(ph?.end) && ph.end > ph.start && typeof ph.text === 'string'));
    if (bad >= 0) fail(`${file}: speech.phrases[${bad}] needs numeric start < end and a text`);
    for (const asset of assets) {
      if (byId.has(asset.id)) fail(`Asset ${asset.id} has more than one --analysis`);
      byId.set(asset.id, phrases);
    }
  }
  return byId;
}

// Frame-exact still of output frame `frame` (0-based) of a constant-frame-rate
// file. Input -ss seeking alone is ambiguous at frame boundaries (it can land
// one frame early or late next to a cut), so seek coarsely two frames early,
// keep the original timestamps (-copyts) and select the first frame whose pts
// reaches the half-frame before `frame`: the frame displayed at the frame
// midpoint (frame + 0.5) / fps. -fps_mode passthrough writes that decoded frame
// as is, never a duplicated neighbour.
export async function extractFrame(file, frame, fps, out, startTime = 0) {
  const seek = Math.max(0, (frame - 2) / fps), from = startTime + (frame - 0.5) / fps;
  await run(ffmpeg(), ['-v', 'error', '-copyts', '-ss', String(seek), '-i', file, '-an', '-sn',
    '-vf', `select='gte(t,${from.toFixed(6)})'`, '-fps_mode', 'passthrough', '-frames:v', '1', '-n', out], { timeout: 60000 });
}
export const frameMid = (frame, fps) => (frame + 0.5) / fps;

async function ffmpegVersion() {
  const { stdout } = await run(ffmpeg(), ['-version'], { timeout: 10000 });
  return stdout.split('\n')[0].split(' ')[2] || 'unknown';
}

// The frame alignment a render compiled with: { alignment, source }. source is
// 'receipt' when the receipt records frame_alignment, else 'legacy-default'
// (every recorded frame_rate applied, as renders before 0.7.0 compiled). The
// alignment must describe the document (bindAlignment refuses one that does not).
export function renderAlignment(receipt, doc) {
  return Array.isArray(receipt.frame_alignment) ? { alignment: receipt.frame_alignment, source: 'receipt' }
    : { alignment: legacyAlignment(doc), source: 'legacy-default' };
}

export async function qaRender(root, renderDir, qaDir, options = {}) {
  const { band, sceneThreshold, production, analyses, decisions } = qaOptions(options);
  root = await safePath(root);
  renderDir = await safePath(renderDir);
  qaDir = await safePath(qaDir);
  if (qaDir === root || qaDir.startsWith(root + path.sep)) fail('QA output must be outside the immutable project');
  const receipt = JSON.parse(await fs.readFile(path.join(renderDir, 'receipt.json'), 'utf8'));
  if (receipt.status !== 'completed' || !receipt.output) fail(`Render is not completed: ${receipt.status}`);
  // Bind QA to one revision: snapshot digest, revision file digest and output digest.
  const { doc: project, templates } = await loadProject(root, receipt.revision);
  const revisionSha = await digest(revisionFile(root, receipt.revision));
  if (!receipt.revision_sha256 || receipt.revision_sha256 !== revisionSha) fail('Render receipt is not bound to this revision digest');
  const snapshotFile = path.join(renderDir, 'project.json');
  if (await digest(snapshotFile) !== receipt.project_sha256) fail('Render project snapshot changed');
  const snapshot = JSON.parse(await fs.readFile(snapshotFile, 'utf8'));
  if (JSON.stringify(snapshot) !== JSON.stringify(project) || snapshot.project_id !== receipt.project_id) fail('Render snapshot does not match the project revision');
  const video = path.join(renderDir, receipt.output.file);
  const videoSha = await digest(video);
  if (videoSha !== receipt.output.sha256) fail('Rendered video changed after the receipt');
  // --analysis files are checked before any evidence is written (a bad one
  // must not leave a half-written QA directory that cannot be reused).
  const phrases = analyses.length ? await assetPhrases(project, analyses) : null;
  // Decisions name v2 items (a v1 project's clips after migration).
  const migrated = project.schema_version === SCHEMA_V2 ? project : migrateV1(project);
  const accept = decisions ? await decisionAcceptor(migrated, decisions) : null;
  await fs.mkdir(qaDir); // Must be new; QA evidence is never overwritten.
  await fs.mkdir(path.join(qaDir, 'frames'));
  await fs.mkdir(path.join(qaDir, 'clips'));

  const { frames: expectedFrames } = validateDocument(project, { templates });
  const doc = migrated;
  const fps = doc.canvas.fps, expectedSeconds = expectedFrames / fps;
  const media = await probeRender(video);
  // Expected size: the output size the render recorded (it checked the file
  // against its own outputSize before writing the receipt), so a render made
  // under an earlier size rule (e.g. a 0.6.0 preview raised to 704x88) is judged
  // by its own rule. A receipt without it falls back to today's outputSize.
  const recorded = Number.isInteger(receipt.output.width) && Number.isInteger(receipt.output.height);
  const size = recorded ? { width: receipt.output.width, height: receipt.output.height } : outputSize(doc.canvas, receipt.preview);
  const audible = audibleItems(doc);
  const checks = [];
  const check = (id, category, status, observation, extra = {}) => checks.push({ id, category, status, observation, ...extra });

  // Structure.
  const drift = Math.abs(media.duration - expectedSeconds);
  check('duration-matches-revision', 'structure', drift <= 1 / fps + 1e-3 ? 'pass' : 'fail',
    `Rendered ${media.duration.toFixed(3)} s; revision expects ${expectedFrames} frames at ${fps} fps (${expectedSeconds.toFixed(3)} s, ±1 frame).`,
    { measured: { expected_seconds: round(expectedSeconds), actual_seconds: round(media.duration), expected_frames: expectedFrames } });
  check('resolution', 'structure', media.width === size.width && media.height === size.height ? 'pass' : 'fail',
    `Rendered ${media.width}x${media.height}; expected ${size.width}x${size.height} (${receipt.preview ? 'preview' : 'export'}, ` +
    `${recorded ? 'output size recorded by the render receipt' : 'the receipt records no output size: current output size rule'}).`,
    { measured: { width: media.width, height: media.height, expected_width: size.width, expected_height: size.height,
      expected_source: recorded ? 'receipt' : 'output-size-rule' } });
  check('frame-rate', 'structure', Math.abs(media.fps - fps) < 0.01 ? 'pass' : 'fail', `Rendered ${round(media.fps)} fps; project ${fps} fps.`, { measured: { fps: round(media.fps) } });
  const wantsAudio = audible.length > 0;
  check('audio-stream', 'structure', media.has_audio === wantsAudio ? 'pass' : wantsAudio ? 'fail' : 'warn',
    wantsAudio ? (media.has_audio ? 'Audible project and rendered audio stream present.' : 'Project has audible items but the render has no audio stream.')
      : (media.has_audio ? 'Render has an audio stream although no item is audible.' : 'No audible items and no audio stream.'),
    { measured: { has_audio: media.has_audio, audible_items: audible.map(i => i.id) } });

  // Video: black/freeze segments that are not explained by timeline gaps.
  const pictured = union(doc.items.filter(i => i.kind === 'media' && doc.tracks.find(t => t.id === i.track_id)?.kind === 'video' && i.opacity !== 0)
    .map(i => [i.start_frame / fps, (i.start_frame + i.frames) / fps]));
  const videoLog = await filterLog(['-i', video, '-an', '-vf', 'blackdetect=d=0.5:pix_th=0.10,freezedetect=n=-60dB:d=2']);
  const unexpected = (list, minimum) => list.map(s => ({ ...s, inside: overlap(s, pictured) })).filter(s => s.inside > minimum);
  const black = unexpected(logSegments(videoLog, 'black', media.duration), 0.5);
  check('black-segments', 'video', black.length ? 'warn' : 'pass',
    black.length ? `${black.length} black segment(s) longer than 0.5 s where the timeline has picture.` : 'No unexpected black segment longer than 0.5 s.',
    { measured: { segments: black.map(s => ({ start: round(s.start), end: round(s.end) })) }, ...(black.length ? { refs: black.map(s => ({ time_seconds: round(s.start) })) } : {}) });
  const frozen = unexpected(logSegments(videoLog, 'lavfi.freezedetect.freeze', media.duration), 2);
  check('freeze-segments', 'video', frozen.length ? 'warn' : 'pass',
    frozen.length ? `${frozen.length} frozen segment(s) longer than 2 s where the timeline has picture.` : 'No frozen segment longer than 2 s.',
    { measured: { segments: frozen.map(s => ({ start: round(s.start), end: round(s.end) })) }, ...(frozen.length ? { refs: frozen.map(s => ({ time_seconds: round(s.start) })) } : {}) });

  // Audio: silence inside audible ranges, integrated loudness and true peak.
  if (!media.has_audio) {
    for (const id of ['silence-in-audible-ranges', 'integrated-loudness', 'true-peak', 'cut-point-clicks']) {
      check(id, 'audio', wantsAudio ? 'unknown' : 'not_applicable', wantsAudio ? 'No audio stream to measure.' : 'Project has no audible items.');
    }
  } else {
    const audioLog = await filterLog(['-i', video, '-vn', '-af', `${silenceFilter(-50, 2)},ebur128=peak=true`]);
    const sounding = union(audible.map(i => [i.start_frame / fps, (i.start_frame + i.frames) / fps]));
    const silent = silences(audioLog, media.duration).map(s => ({ ...s, inside: overlap(s, sounding) })).filter(s => s.inside > 2);
    check('silence-in-audible-ranges', 'audio', silent.length ? 'warn' : 'pass',
      silent.length ? `${silent.length} silence(s) longer than 2 s inside ranges where the project has sound.` : 'No silence longer than 2 s inside audible ranges.',
      { measured: { segments: silent.map(s => ({ start: round(s.start), end: round(s.end) })) }, ...(silent.length ? { refs: silent.map(s => ({ time_seconds: round(s.start) })) } : {}) });
    const { integrated_lufs: lufs, true_peak_dbtp: peak } = ebur128Summary(audioLog);
    const loud = Number.isFinite(lufs) && Math.abs(lufs + 14) <= 3;
    check('integrated-loudness', 'audio', lufs === null ? 'unknown' : loud ? 'pass' : 'warn',
      lufs === null ? 'ebur128 summary missing.' : `Integrated loudness ${Number.isFinite(lufs) ? lufs.toFixed(1) : '-inf'} LUFS ${loud ? 'is within' : 'is outside'} the -14 ±3 LUFS target.`,
      { measured: { lufs: Number.isFinite(lufs) ? lufs : null } });
    // The renderer's AAC limiter evidence: how far HyperFrames lowered the whole
    // mix to stay under -1 dBTP (RenderJob.audioLoweredDb, copied into the receipt).
    const limiter = receipt.audio_limiter;
    const lowered = limiter ? (limiter.engaged ? ` The render limiter lowered the mix by ${limiter.audio_lowered_db.toFixed(1)} dB (audioLoweredDb).` : ' The render limiter was not engaged (no audioLoweredDb).')
      : ' Render receipt has no limiter record.';
    check('true-peak', 'audio', peak === null ? 'unknown' : peak > -1 ? 'warn' : 'pass',
      peak === null ?`ebur128 true peak missing.${lowered}` : `True peak ${Number.isFinite(peak) ? peak.toFixed(1) : '-inf'} dBTP (limit -1 dBTP).${lowered}`,
      { measured: { true_peak_dbtp: Number.isFinite(peak) ? peak : null, audio_lowered_db: limiter ? limiter.audio_lowered_db : null,
        limiter_engaged: limiter ? limiter.engaged : null, limiter_ceiling_dbtp: limiter ? limiter.ceiling_dbtp : null } });
    // Clicks (waveform discontinuities) within ±10 ms of every audible cut point.
    // A decode that fails or times out leaves this check unknown; the others stand.
    const clicks = await clickCheck(video, audioCutPoints(doc, audible, media.duration), { audioOffset: media.audio_start_time - media.start_time });
    check('cut-point-clicks', 'audio', clicks.status, clicks.observation, { measured: clicks.measured, ...(clicks.refs ? { refs: clicks.refs } : {}) });
  }

  // Composited-frame samples: item midpoints, both sides of each video cut, caption midpoints.
  const total = expectedFrames;
  const wanted = [], seen = new Set();
  const want = (id, frame, reason, itemId) => {
    frame = Math.min(Math.max(0, frame), total - 1);
    if (seen.has(`${reason}:${frame}:${itemId ?? ''}`)) return;
    seen.add(`${reason}:${frame}:${itemId ?? ''}`);
    wanted.push({ id, frame, reason, item_id: itemId });
  };
  for (const item of doc.items.filter(i => i.kind === 'media' || i.kind === 'graphic')) want(`s-${item.id}-mid`, item.start_frame + Math.floor(item.frames / 2), 'item_mid', item.id);
  const videoItems = doc.items.filter(i => i.kind === 'media' && doc.tracks.find(t => t.id === i.track_id).kind === 'video');
  const cuts = [...new Set(videoItems.flatMap(i => [i.start_frame, i.start_frame + i.frames]))].filter(f => f > 0 && f < total).sort((a, b) => a - b);
  for (const cut of cuts) { want(`s-cut${cut}-before`, cut - 1, 'cut_before'); want(`s-cut${cut}-after`, cut, 'cut_after'); }
  // The document as compiled (source frame alignment), computed once for the
  // caption samples and the cut-point checks, as the render compiled it: with
  // the frame_alignment its receipt recorded, not a new probe. A receipt without
  // it (rendered before 0.7.0) applied every recorded frame_rate.
  const { alignment, source: alignmentSource } = renderAlignment(receipt, doc);
  const view = compiledView(bindAlignment({ ...doc }, alignment));
  const alignmentMeasured = { frame_alignment: alignment, frame_alignment_source: alignmentSource };
  const captions = resolveCaptions(view);
  const captionSample = new Map();
  for (const { item, start, end } of captions) {
    const frame = Math.floor((start + end) / 2 * fps);
    want(`s-${item.id}-caption`, frame, 'caption', item.id);
    captionSample.set(item.id, { id: `s-${item.id}-caption`, time: frameMid(frame, fps) });
  }
  // Shots of the rendered file (scene detection): every shot, however short,
  // gets at least one sample; a shot already holding a planned sample adds none.
  const shots = (await detectShots(video, media.duration, sceneThreshold)).map((shot, index) => {
    const first = Math.max(0, Math.ceil(shot.start * fps - 1e-6)), last = Math.min(total - 1, Math.ceil(shot.end * fps - 1e-6) - 1);
    return { ...shot, index, first, last };
  }).filter(shot => shot.last >= shot.first);
  for (const shot of shots) {
    const inside = wanted.find(w => w.frame >= shot.first && w.frame <= shot.last);
    if (inside) { shot.sample = inside.id; continue; }
    shot.sample = `s-shot${shot.index}`;
    want(shot.sample, Math.floor((shot.first + shot.last) / 2), 'shot');
  }
  const samples = [];
  for (const sample of wanted) {
    // Frame-exact: the sample is output frame `sample.frame`, recorded at its
    // frame-midpoint time (cut_before = last frame before the cut, cut_after = first after it).
    const time = frameMid(sample.frame, fps), file = `frames/${sample.id}.png`;
    await extractFrame(video, sample.frame, fps, path.join(qaDir, file), media.start_time);
    const stat = await fs.stat(path.join(qaDir, file)).catch(() => null);
    if (!stat?.size) continue;
    samples.push({ id: sample.id, time_seconds: round(time, 6), reason: sample.reason, ...(sample.item_id ? { item_id: sample.item_id } : {}),
      file, sha256: await digest(path.join(qaDir, file)) });
  }
  const sampled = new Set(samples.map(s => s.id));
  const missing = captions.filter(c => !sampled.has(captionSample.get(c.item.id).id));
  check('caption-sampled', 'captions', !captions.length ? 'not_applicable' : missing.length ? 'fail' : 'pass',
    !captions.length ? 'No visible captions in this revision.' : missing.length ? `No frame could be sampled for ${missing.length} caption(s).`
      : `Sampled a composited frame at the midpoint of each of ${captions.length} caption(s) for review.`,
    captions.length ? { refs: captions.map(c => ({ time_seconds: round(captionSample.get(c.item.id).time, 6), item_id: c.item.id, ...(sampled.has(captionSample.get(c.item.id).id) ? { sample_id: captionSample.get(c.item.id).id } : {}) })) } : {});

  // Safe area (5% from every edge) at the sampled caption and graphic frames.
  // Neither is detected in pixels. Captions: boxes computed from the compiled
  // layout (caption block, wrap and line metrics from estimated text width).
  // Graphics: the template box, which template load validation already keeps
  // inside the margin; the check records that guarantee, it measures nothing new.
  const safeArea = (id, category, entries, sampleOf, label, method, inside) => {
    const outside = entries.filter(e => !insideSafeArea(e.box));
    check(id, category, !entries.length ? 'not_applicable' : outside.length ? 'fail' : 'pass',
      !entries.length ? `No ${label} in this revision.` : outside.length ? `${outside.length} ${label} box(es) cross the 5% safe margin: ${outside.map(e => e.id).join(', ')}.`
        : inside(entries.length),
      entries.length ? { measured: { method, margin: 0.05, boxes: entries.map(e => ({ item_id: e.id, ...e.box })) },
        refs: entries.map(e => ({ time_seconds: round(sampleOf(e).time, 6), item_id: e.id, ...(sampled.has(sampleOf(e).id) ? { sample_id: sampleOf(e).id } : {}) })) } : {});
  };
  safeArea('caption-safe-area', 'captions', captions.map(c => ({ id: c.item.id, box: captionBox(doc.canvas, c.item) })), e => captionSample.get(e.id), 'caption',
    'compiled-layout-estimate', n => `All ${n} caption box(es) are inside the 5% safe margin (layout estimate, not a pixel detection).`);
  const graphicItems = doc.items.filter(i => i.kind === 'graphic'), graphicTemplates = graphicItems.length ? templateSet(doc, templates) : null;
  safeArea('graphic-safe-area', 'video', graphicItems.map(i => ({ id: i.id, box: graphicBox(i, graphicTemplates), frame: i.start_frame + Math.floor(i.frames / 2) })),
    e => ({ id: `s-${e.id}-mid`, time: frameMid(e.frame, fps) }), 'graphic', 'template-load-guarantee',
    n => `${n} graphic(s) render in their template box; template load validation guarantees every template box lies inside the 5% safe margin. Not a pixel detection, and text fit inside the box is not measured.`);

  const unsampled = shots.filter(s => !sampled.has(s.sample));
  const short = shots.filter(s => s.end - s.start < 1);
  check('shot-sampled', 'video', unsampled.length ? 'fail' : 'pass',
    unsampled.length ? `No frame could be sampled for ${unsampled.length} of ${shots.length} detected shot(s).`
      : `Each of ${shots.length} detected shot(s) in the render has a sampled frame (${short.length} shorter than 1 s).`,
    { measured: { method: `ffmpeg scene score on the rendered file (select gt(scene,${sceneThreshold}))`, scene_threshold: sceneThreshold,
      shots: shots.map(s => ({ start: round(s.start), end: round(s.end), sample_id: s.sample })) },
    refs: shots.map(s => ({ time_seconds: round(s.start, 6), ...(sampled.has(s.sample) ? { sample_id: s.sample } : {}) })) });

  // Burned-in captions of the SOURCE at every video item's in/out point.
  const atCut = point => {
    const frame = Math.round(point.output_seconds * fps), id = point.edge === 'in' ? `s-cut${frame}-after` : `s-cut${frame}-before`;
    return sampled.has(id) ? id : sampled.has(`s-${point.item_id}-mid`) ? `s-${point.item_id}-mid` : null;
  };
  // Fragments of adjacent SOURCE shots (or a flash) just inside every video item's
  // in/out point. Both checks share one decode per cut point.
  const { burned, fragments, speech } = await cutPointChecks(view, root, { band, sceneThreshold, sampleAt: atCut,
    phrasesFor: phrases && (point => phrases.get(point.item.asset_id) ?? null), accept });
  check('burned-caption-cut-points', 'captions', burned.status, burned.observation, { measured: { ...burned.measured, ...alignmentMeasured }, ...(burned.refs ? { refs: burned.refs } : {}) });
  check('cut-boundary-fragments', 'video', fragments.status, fragments.observation, { measured: { ...fragments.measured, ...alignmentMeasured }, ...(fragments.refs ? { refs: fragments.refs } : {}) });
  // Caption/speech sync at in-points, only with --analysis (needs ASR phrases).
  if (speech) {
    const unjudged = speech.measured.points.filter(e => e.reason === 'no_analysis').length;
    const skippedNote = unjudged ? ` ${unjudged} in-point(s) of assets without an --analysis were not judged.` : '';
    check('caption-speech-sync', 'captions', speech.applicable ? speech.status : 'not_applicable',
      `${speech.applicable ? speech.observation : 'No in-point of an asset with an --analysis to judge.'}${skippedNote}`, { measured: speech.measured, ...(speech.refs ? { refs: speech.refs } : {}) });
  }

  // Lint result recorded by the render receipt (render is blocked on errors).
  const lint = receipt.lint;
  check('hyperframes-lint', 'lint', !lint ? 'unknown' : lint.error_count ? 'fail' : lint.warning_count ? 'warn' : 'pass',
    !lint ? 'Render receipt has no lint result.' : `HyperFrames lint ${lint.version}: ${lint.error_count} error(s), ${lint.warning_count} warning(s).`,
    lint ? { measured: { error_count: lint.error_count, warning_count: lint.warning_count, codes: [...new Set(lint.findings.map(f => f.code))] } } : {});

  // Contact sheet (ffmpeg tile over the samples) and ±1 s clips around each cut.
  let contactSheet = null;
  if (samples.length) {
    // Up to 40 tiles (more only when there are more shots): one sample of every
    // shot first, then evenly spread others; tiles in time order.
    const capacity = Math.max(40, shots.length);
    let pick = samples;
    if (samples.length > capacity) {
      const chosen = new Set(shots.map(s => samples.find(x => x.id === s.sample)).filter(Boolean));
      for (let i = 0; i < capacity && chosen.size < capacity; i++) chosen.add(samples[Math.floor(i * samples.length / capacity)]);
      for (const sample of samples) { if (chosen.size >= capacity) break; chosen.add(sample); }
      pick = [...chosen];
    }
    pick = [...pick].sort((a, b) => a.time_seconds - b.time_seconds);
    const list = path.join(qaDir, '.contact-sheet.txt');
    await fs.writeFile(list, pick.map(s => `file '${path.join(qaDir, s.file).replace(/'/g, "'\\''")}'`).join('\n') + '\n');
    const columns = Math.min(5, pick.length), rows = Math.ceil(pick.length / columns);
    await run(ffmpeg(), ['-v', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-vf', `scale=320:-2,tile=${columns}x${rows}:padding=4:margin=4`,
      '-frames:v', '1', '-n', path.join(qaDir, 'contact-sheet.png')], { timeout: 120000 });
    await fs.unlink(list);
    contactSheet = { file: 'contact-sheet.png', sha256: await digest(path.join(qaDir, 'contact-sheet.png')) };
  }
  const boundaryClips = [];
  for (const cut of cuts) {
    const at = cut / fps, start = Math.max(0, at - 1), length = Math.min(media.duration, at + 1) - start;
    const file = `clips/cut-${String(cut).padStart(6, '0')}.mp4`;
    await run(ffmpeg(), ['-v', 'error', '-ss', String(start), '-i', video, '-t', String(length), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
      '-c:a', 'aac', '-n', path.join(qaDir, file)], { timeout: 120000 });
    boundaryClips.push({ cut_seconds: round(at, 6), file, sha256: await digest(path.join(qaDir, file)) });
  }

  const statuses = checks.map(c => c.status);
  const qa = { schema_version: 'creative-craft.render-qa.v1',
    qa_id: `qa-${doc.project_id}-r${receipt.revision}-${receipt.preview ? 'preview' : 'export'}-${Date.now()}`,
    project_id: doc.project_id, revision: receipt.revision, revision_sha256: revisionSha,
    render: { kind: receipt.preview ? 'preview' : 'export', file: video, sha256: videoSha, width: media.width, height: media.height,
      fps: round(media.fps, 6), duration_seconds: round(media.duration, 6), has_audio: media.has_audio },
    tool: { name: TOOL.name, version: TOOL.version, ffmpeg: await ffmpegVersion() },
    created_at: new Date().toISOString(), checks, samples, boundary_clips: boundaryClips, contact_sheet: contactSheet,
    verdict: statuses.includes('fail') ? 'fail' : statuses.includes('warn') ? 'pass_with_warnings' : 'pass',
    review: { status: 'pending', reviewer: null, decision: 'pending', findings: [] },
    unverified: ['human listening (dialogue, music balance, sync)', 'creative quality and edit choices',
      'visual review of composited samples (pending agent/human review)', 'caption legibility and text accuracy',
      'safe-area boxes are layout estimates, not pixel measurements',
      'burned-in caption cut points are a frame-difference heuristic (not OCR): caption text, colour captions and captions outside the band are not checked',
      'cut-boundary fragments are a full-frame difference heuristic on the source: gradual dissolves and same-framing jump cuts below the thresholds are not detected',
      'cut-point clicks are a second-difference heuristic within ±10 ms of each audible cut: transients (plosives, percussion) at a cut can warn, and clicks masked by louder high-frequency content around the cut are not reported'] };
  // The review page (review.html, derived from these exact bytes) is built and
  // written before qa.json, which is published last: a page error leaves no
  // qa.json behind, and a qa.json present means the whole QA run completed.
  const qaText = JSON.stringify(qa, null, 2) + '\n';
  await writeReviewPage(qaDir, await reviewPageFor(qaDir, { qaText, qa, video, videoSha256: videoSha, production }));
  const temp = path.join(qaDir, '.qa.json');
  await fs.writeFile(temp, qaText, { flag: 'wx' });
  await fs.rename(temp, path.join(qaDir, 'qa.json'));
  return qa;
}
