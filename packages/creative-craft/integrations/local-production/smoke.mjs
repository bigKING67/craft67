import { retentionRoot, withRetentionLock, planRetention, applyRetention } from './retention.mjs';
import * as fs from 'node:fs/promises';
import { existsSync, readdirSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { createProject, editProject, editBatch, readProject, digest, run } from './project.mjs';
import { renderProject } from './render.mjs';
import { verifySmoke, verifyMultitrack, verifyBrand, captionSource, frameAt, pcmAt, mae } from './verify-smoke.mjs';
import { mediaTool } from './media-analysis.mjs';
import { footageTranscript, synthFootage } from './tests/footage-fixture.mjs';

// Self-authored synthetic signals; no customer assets, ASR, TTS or paid APIs.
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../..');
const base = path.resolve(process.argv[2] || path.join(repo, 'dist/local-production', new Date().toISOString().replace(/[:.]/g, '-')));
if (process.argv[2] && (base === retentionRoot || base.startsWith(retentionRoot + path.sep))) {
  throw new Error('Custom output must be outside managed dist/local-production');
}
async function smoke() {
// QA output must validate against the shared JSON Schema. A Python with
// jsonschema is mandatory: missing it fails the smoke instead of skipping.
const python = process.env.CREATIVE_PYTHON || path.join(repo, '.venv/bin/python');
if (!existsSync(python)) throw new Error(`Schema validation needs Python with jsonschema: set CREATIVE_PYTHON or create ${python}`);
const validateSchema = async (schema, files) => run(python, ['-c', `import json,sys
from jsonschema import Draft202012Validator
schema=json.load(open(sys.argv[1]))
Draft202012Validator.check_schema(schema)
for f in sys.argv[2:]:
    Draft202012Validator(schema).validate(json.load(open(f)))
print(len(sys.argv)-2)`, path.join(repo, 'skills/creative-craft/schemas', schema), ...files]);
await validateSchema('render-qa.schema.json', [path.join(repo, 'tests/fixtures/render-qa/sample.json')]);

await fs.mkdir(base, { recursive: true });
const ffmpeg = mediaTool('ffmpeg');
const source = path.join(base, 'source.mp4'), broll = path.join(base, 'broll.mp4'), music = path.join(base, 'music.m4a');
await run(ffmpeg, ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=24:duration=6',
  '-f', 'lavfi', '-i', 'aevalsrc=0.1*sin(2*PI*if(lt(t\\,3)\\,440\\,880)*t):s=48000:d=6', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', source]);
await run(ffmpeg, ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'smptehdbars=size=640x360:rate=24:duration=4', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', broll]);
await run(ffmpeg, ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'sine=frequency=660:sample_rate=48000:duration=8', '-c:a', 'aac', music]);
const before = await digest(source);
const summary = { status: 'running', fixture: 'synthetic technical scenarios; not real creative evaluation', listening: 'unverified' };

// 1. Legacy local-edit.v1 project: unchanged v1 operations and CLI form.
const clip = (id, start, caption) => ({ id, asset_id: 'source', in_seconds: start, frames: 24, volume: 0.7,
  fit: 'contain', captions: [{ from: start, to: start + 1, text: caption }] });
const root = path.join(base, 'project');
await createProject(root, { project_id: 'production-smoke', title: 'Creative Craft 技术样例', canvas: { width: 1280, height: 720, fps: 24 },
  assets: [{ id: 'source', path: source }], clips: [clip('opening', 0, '口播：保留这一句'), clip('detail', 3, '产品：细节画面')], audio: [] });
const outcomes = [];
outcomes.push(await renderProject(root, path.join(base, 'talking-head-preview'), { preview: true, revision: 1 }));
await editProject(root, 1, [{ type: 'reorder', clip_ids: ['detail', 'opening'] },
  { type: 'update_clip', clip_id: 'detail', changes: { captions: [{ from: 3, to: 4, text: '品牌：让细节先说话' }] } }]);
outcomes.push(await renderProject(root, path.join(base, 'brand-export'), { revision: 2 }));
await editProject(root, 2, [{ type: 'update_clip', clip_id: 'detail', changes: { in_seconds: 4, frames: 12,
  captions: [{ from: 4, to: 4.5, text: '电商：换一个开场' }] } }]);
outcomes.push(await renderProject(root, path.join(base, 'commerce-export'), { revision: 3 }));
if ((await readProject(root)).revision !== 3 || before !== await digest(source)) throw new Error('Reopen or input preservation failed');
await verifySmoke(base);
await fs.writeFile(path.join(base, 'mute.json'), JSON.stringify([{ type: 'update_clip', clip_id: 'opening', changes: { volume: 0 } },
  { type: 'update_clip', clip_id: 'detail', changes: { volume: 0 } }]));
const cli = async (...args) => JSON.parse((await run(process.execPath, [path.join(here, 'cli.mjs'), ...args], { timeout: 300000, maxBuffer: 8 * 1024 * 1024 })).stdout);
assert.equal((await cli('edit', root, '3', path.join(base, 'mute.json'))).revision, 4, 'legacy CLI edit form');
const silent = await cli('render', root, path.join(base, 'silent-export'), '4'); // Also protects stdout from upstream diagnostics.
if (silent.status !== 'completed' || silent.output.audio) throw new Error('Silent CLI export failed');
await editProject(root, 4, [{ type: 'set_audio', audio: [{ id: 'music', asset_id: 'source', in_seconds: 3,
  start_frame: 12, frames: 24, volume: 0.2 }] }]);
const bed = await renderProject(root, path.join(base, 'independent-audio-export'), { revision: 5 });
const rms = pcm => {
  if (pcm.length < 1000) throw new Error('Missing audio samples');
  let power = 0; for (let i = 0; i < pcm.length; i += 4) power += pcm.readFloatLE(i) ** 2;
  return Math.sqrt(power / (pcm.length / 4));
};
const bedFile = path.join(base, 'independent-audio-export/video.mp4');
const beforeBed = rms(await pcmAt(bedFile, 0.125)), duringBed = rms(await pcmAt(bedFile, 0.75));
if (beforeBed > 0.001 || duringBed < 0.005) throw new Error('Independent audio placement failed');
summary.legacy_v1 = { outputs: [...outcomes, silent, bed].map(r => r.status), independent_audio: { before_rms: beforeBed, during_rms: duringBed } };

// 2. First v2 batch on the v1 project: pure migration revision, then the edit.
const migrated = await editBatch(root, { base_revision: 5, author: 'agent', summary: 'Rename main track', operations: [
  { type: 'edit_track', track_id: 'v_main', name: '主轨' }] });
assert.equal(migrated.migration_revision, 6);
assert.equal((await readProject(root, 6)).change.author, 'migration');
assert.equal((await readProject(root, 5)).schema_version, 'creative-craft.local-edit.v1', 'old v1 revision stays readable');
const migratedRender = await renderProject(root, path.join(base, 'migrated-export'), { revision: 6 });
const migration = [];
for (const time of [0.25, 0.75, 1.25]) {
  const a = await frameAt(bedFile, time, 'scale=64:36'), b = await frameAt(path.join(base, 'migrated-export/video.mp4'), time, 'scale=64:36');
  const pa = rms(await pcmAt(bedFile, time)), pb = rms(await pcmAt(path.join(base, 'migrated-export/video.mp4'), time));
  migration.push({ time, picture_mae: mae(a, b), rms_v1: pa, rms_v2: pb });
  if (mae(a, b) > 6 || Math.abs(pa - pb) > 0.01) throw new Error(`Migration changed the render at ${time}s`);
}
summary.migration = { revisions: [6, 7], render: migratedRender.status, comparison: migration };

// 3. Native v2 project: multi-track B-roll, music bed, linked and free captions.
const v2 = path.join(base, 'multitrack');
const created = await createProject(v2, { project_id: 'multitrack-smoke', title: '多轨技术样例', canvas: { width: 1280, height: 720, fps: 24 },
  assets: [{ id: 'talk', path: source }, { id: 'music', path: music }],
  tracks: [{ id: 'v_main', kind: 'video', locked: false, name: '主轨' }, { id: 'a_music', kind: 'audio', locked: false },
    { id: 'c_sub', kind: 'caption', locked: false }],
  items: [
    { id: 'talk1', track_id: 'v_main', kind: 'media', asset_id: 'talk', start_frame: 0, frames: 48, source_in_seconds: 0, volume: 0.8, fit: 'cover' },
    { id: 'talk2', track_id: 'v_main', kind: 'media', asset_id: 'talk', start_frame: 48, frames: 48, source_in_seconds: 3, volume: 0.8, fit: 'cover' },
    { id: 'bed', track_id: 'a_music', kind: 'media', asset_id: 'music', start_frame: 0, frames: 96, source_in_seconds: 0, volume: 0.6 },
    { id: 'cap1', track_id: 'c_sub', kind: 'caption', text: '口播：第一句', link: { item_id: 'talk1', source_from: 0.2, source_to: 1.5 } },
    { id: 'cap2', track_id: 'c_sub', kind: 'caption', text: '口播：第二句', link: { item_id: 'talk2', source_from: 3.2, source_to: 4.2 } },
    { id: 'title', track_id: 'c_sub', kind: 'caption', text: '标题：多轨合成', start_frame: 72, frames: 24 }] });
assert.equal(created.schema_version, 'creative-craft.edit-document.v2');
const assetCount = async () => (await fs.readdir(path.join(v2, 'assets'))).length;
const revisionCount = async () => (await fs.readdir(path.join(v2, 'revisions'))).filter(n => n.endsWith('.json')).length;
const addBroll = { base_revision: 1, author: 'agent', summary: 'Add generated-style B-roll above the main track', operations: [
  { type: 'add_asset', id: 'broll', path: broll, origin: { kind: 'import', label: 'synthetic bars' } },
  { type: 'add_track', track: { id: 'v_broll', kind: 'video', locked: false, name: 'B-roll' }, index: 1 },
  { type: 'add_item', item: { id: 'over', track_id: 'v_broll', kind: 'media', asset_id: 'broll', start_frame: 12, frames: 24,
    source_in_seconds: 0, volume: 0, fit: 'contain', transform: { x: 0.75, y: 0.25, scale: 0.4 } } }] };
await fs.writeFile(path.join(base, 'add-broll.json'), JSON.stringify(addBroll));
const assetsBefore = await assetCount();
const dry = await cli('edit', v2, path.join(base, 'add-broll.json'), '--dry-run');
assert.equal(dry.status, 'dry_run');
assert.deepEqual(dry.diff.items.added, ['over']);
assert.equal(await revisionCount(), 1, 'dry-run must not publish');
assert.equal(await assetCount(), assetsBefore, 'dry-run must not copy assets');
assert.equal((await cli('edit', v2, path.join(base, 'add-broll.json'))).revision, 2);
assert.equal(await assetCount(), assetsBefore + 1, 'add_asset imports after create');
await assert.rejects(editBatch(v2, { ...addBroll, summary: 'stale' }), /Revision conflict/);
await editBatch(v2, { base_revision: 2, author: 'human', summary: 'Lock picture', operations: [{ type: 'edit_track', track_id: 'v_main', locked: true }] });
await assert.rejects(editBatch(v2, { base_revision: 3, author: 'agent', summary: 'Trim locked', operations: [{ type: 'trim_item', item_id: 'talk1', tail_frames: 6 }] }), /locked/);
assert.equal(await revisionCount(), 3, 'locked edit must not publish');
await assert.rejects(editBatch(v2, { base_revision: 3, author: 'agent', summary: 'Unlock and split', operations: [{ type: 'edit_track', track_id: 'v_main', locked: false },
  { type: 'split_item', item_id: 'talk2', at_frame: 72, new_item_id: 'talk2b' }] }), /only operation/, 'unlock-then-edit must not share a batch');
await editBatch(v2, { base_revision: 3, author: 'human', summary: 'Unlock picture', operations: [{ type: 'edit_track', track_id: 'v_main', locked: false }] });
await editBatch(v2, { base_revision: 4, author: 'agent', summary: 'Split', operations: [{ type: 'split_item', item_id: 'talk2', at_frame: 72, new_item_id: 'talk2b' }] });
await editBatch(v2, { base_revision: 5, author: 'agent', summary: 'Back to the B-roll cut', operations: [{ type: 'revert_to', revision: 2 }] });
const reverted = await readProject(v2), target = await readProject(v2, 2);
assert.deepEqual([reverted.items, reverted.tracks], [target.items, target.tracks]);
const multi = await renderProject(v2, path.join(base, 'multitrack-export'), { revision: 6 });
const multitrackSignals = await verifyMultitrack(base, 'multitrack-export');
summary.multitrack = { revisions: await revisionCount(), render: multi.status, lint: multi.lint, signals: multitrackSignals };

// 4. QA on the actual export, schema-validated; then a deliberately failing export.
const qa = await cli('qa', v2, path.join(base, 'multitrack-export'), path.join(base, 'multitrack-qa'));
assert.notEqual(qa.verdict, 'fail', JSON.stringify(qa.checks.filter(c => c.status === 'fail')));
// cut-point-clicks: the talk1→talk2 hard cut at 2 s carries the 4 ms declick (0.8.0).
for (const [id, status] of [['duration-matches-revision', 'pass'], ['resolution', 'pass'], ['audio-stream', 'pass'], ['caption-sampled', 'pass'], ['cut-point-clicks', 'pass']]) {
  assert.equal(qa.checks.find(c => c.id === id).status, status, id);
}
assert.deepEqual(qa.checks.find(c => c.id === 'cut-point-clicks').measured.cut_points.map(p => p.time_seconds), [2]);
assert.ok(qa.samples.length >= 8 && qa.boundary_clips.length >= 2 && qa.contact_sheet, 'QA evidence');
// Review page (0.9.0): written with qa.json, plays the export by a relative path,
// loads nothing from the network; review-page rewrites only review.html.
const reviewHtml = await fs.readFile(path.join(base, 'multitrack-qa', 'review.html'), 'utf8');
assert.ok(reviewHtml.includes('src="../multitrack-export/video.mp4"') && !/https?:\/\//.test(reviewHtml), 'review.html');
assert.ok(reviewHtml.includes(await digest(path.join(base, 'multitrack-qa', 'qa.json'))), 'review.html is traceable to qa.json');
const regenerated = await cli('review-page', path.join(base, 'multitrack-qa'));
assert.equal(regenerated.status, 'written');
const tampered = path.join(base, 'tampered-export');
await fs.cp(path.join(base, 'multitrack-export'), tampered, { recursive: true });
// Fault injection: an exporter that drops audio yet claims completion.
await fs.rename(path.join(tampered, 'video.mp4'), path.join(tampered, 'with-audio.mp4'));
await run(ffmpeg, ['-v', 'error', '-i', path.join(tampered, 'with-audio.mp4'), '-c', 'copy', '-an', path.join(tampered, 'video.mp4')]);
await fs.unlink(path.join(tampered, 'with-audio.mp4'));
const receipt = JSON.parse(await fs.readFile(path.join(tampered, 'receipt.json'), 'utf8'));
receipt.output = { ...receipt.output, sha256: await digest(path.join(tampered, 'video.mp4')), audio: false };
await fs.writeFile(path.join(tampered, 'receipt.json'), JSON.stringify(receipt, null, 2));
const bad = await cli('qa', v2, tampered, path.join(base, 'tampered-qa'));
assert.equal(bad.verdict, 'fail');
assert.equal(bad.checks.find(c => c.id === 'audio-stream').status, 'fail');
assert.equal(bad.checks.find(c => c.id === 'cut-point-clicks').status, 'unknown', 'no audio stream to analyse');
summary.qa = { verdict: qa.verdict, checks: Object.fromEntries(qa.checks.map(c => [c.id, c.status])), samples: qa.samples.length,
  boundary_clips: qa.boundary_clips.length, fault_injection: { verdict: bad.verdict, audio_stream: 'fail' } };

// 5. P2 brand packaging: title card + lower third, two main shots joined by a
// crossfade, a 1.5× segment, music ducked under the main track, fades.
const brand = path.join(base, 'packaging');
const depthDb = -12;
await createProject(brand, { project_id: 'brand-smoke', title: '品牌包装技术样例', canvas: { width: 1280, height: 720, fps: 24 },
  assets: [{ id: 'talk', path: source }, { id: 'bars', path: broll, origin: { kind: 'generated', provenance_ref: 'jobs/synthetic-bars.json' } }, { id: 'music', path: music }],
  tracks: [{ id: 'v_main', kind: 'video', locked: false, name: '主画面' }, { id: 'v_gfx', kind: 'video', locked: false, name: '包装' },
    { id: 'a_music', kind: 'audio', locked: false, duck: { under_track_id: 'v_main', depth_db: depthDb, attack_frames: 6, release_frames: 12 } },
    { id: 'c_sub', kind: 'caption', locked: false }],
  items: [
    { id: 'main1', track_id: 'v_main', kind: 'media', asset_id: 'talk', start_frame: 0, frames: 72, source_in_seconds: 0, volume: 0.8, fit: 'cover', fade_in_frames: 12 },
    { id: 'main2', track_id: 'v_main', kind: 'media', asset_id: 'bars', start_frame: 60, frames: 60, source_in_seconds: 0, volume: 0, fit: 'cover',
      transition_in: { kind: 'crossfade', frames: 12 } },
    { id: 'main3', track_id: 'v_main', kind: 'media', asset_id: 'talk', start_frame: 120, frames: 48, source_in_seconds: 2.5, volume: 0.8, fit: 'cover',
      speed: 1.5, fade_out_frames: 12 },
    { id: 'card', track_id: 'v_gfx', kind: 'graphic', template: 'title-card', vars: { title: '品牌焕新', subtitle: 'Creative Craft 技术样例' },
      start_frame: 0, frames: 36, fade_in_frames: 6, fade_out_frames: 6 },
    { id: 'strap', track_id: 'v_gfx', kind: 'graphic', template: 'lower-third', vars: { title: '主讲人', subtitle: '品牌顾问', accent: '#2f9e8f' },
      start_frame: 76, frames: 40, fade_in_frames: 6, fade_out_frames: 6 },
    { id: 'bed', track_id: 'a_music', kind: 'media', asset_id: 'music', start_frame: 0, frames: 168, source_in_seconds: 0, volume: 0.5,
      fade_in_frames: 12, fade_out_frames: 24 },
    { id: 'line', track_id: 'c_sub', kind: 'caption', text: '变速：细节一闪而过', link: { item_id: 'main3', source_from: 3.5, source_to: 4.5 } }] });
const brandRender = await renderProject(brand, path.join(base, 'packaging-export'), { revision: 1 });
assert.equal(brandRender.lint.warning_count + brandRender.lint.error_count, 0, JSON.stringify(brandRender.lint.findings));
assert.ok(!brandRender.lint.findings.some(f => f.code === 'audio_volume_double_automation'));
assert.equal(brandRender.caption_font.runtime_load, 'passed');
// Graphic templates are pinned to the revision and travel with the render.
const brandBindings = (await readProject(brand, 1)).graphic_templates;
assert.deepEqual(brandBindings.map(b => b.id), ['lower-third', 'title-card']);
assert.deepEqual(brandRender.templates.map(t => [t.id, t.pinned, t.source, t.sha256]), brandBindings.map(b => [b.id, true, 'project', b.sha256]));
for (const binding of brandBindings) assert.equal(await digest(path.join(base, 'packaging-export', binding.file)), binding.sha256, 'bound template copied into the render');
const brandHtml = await fs.readFile(path.join(base, 'packaging-export/index.html'), 'utf8');
assert.match(brandHtml, /id="v-main3"[^>]*data-playback-rate="1.5"/);
assert.ok(!/<audio[^>]*data-volume/.test(brandHtml) && (brandHtml.match(/<audio[^>]*data-automation=/g) ?? []).length === 3, 'every sound level is a volume lane');
// Linked caption on the 1.5× item: source 3.5–4.5 s → output 5 + 1/1.5 … 5 + 2/1.5 s.
// The 24 fps source records frame_rate, but its in-point 2.5 s (frame 60's
// start) is not a truncated decimal, so compilation keeps it.
assert.equal((await readProject(brand, 1)).assets.find(a => a.id === 'talk').frame_rate, '24/1');
assert.match(await fs.readFile(path.join(base, 'packaging-export/captions.vtt'), 'utf8'), /00:00:05\.667 --> 00:00:06\.333\n变速：细节一闪而过/);
const brandSignals = await verifyBrand(base, 'packaging-export', { depthDb });
const brandQa = await cli('qa', brand, path.join(base, 'packaging-export'), path.join(base, 'packaging-qa'));
assert.notEqual(brandQa.verdict, 'fail', JSON.stringify(brandQa.checks.filter(c => c.status === 'fail')));
const brandCheck = id => brandQa.checks.find(c => c.id === id);
for (const id of ['graphic-safe-area', 'caption-safe-area', 'hyperframes-lint', 'duration-matches-revision', 'audio-stream', 'cut-point-clicks']) assert.equal(brandCheck(id).status, 'pass', id);
assert.ok('audio_lowered_db' in brandCheck('true-peak').measured, 'true-peak cites the limiter record');
assert.ok(brandQa.samples.some(s => s.item_id === 'card') && brandQa.samples.some(s => s.item_id === 'strap'), 'graphics are sampled');
// Fault injection for a P2 check: a large two-line caption centred at 90% height
// leaves the 5% safe area; the QA of that revision must fail on it.
await editBatch(brand, { base_revision: 1, author: 'agent', summary: 'Oversized low caption', operations: [{ type: 'add_item', item: { id: 'low', track_id: 'c_sub',
  kind: 'caption', text: '字幕太大\n贴近底边', start_frame: 24, frames: 24, style: { fontHeight: 0.08, centerY: 0.9, color: '#ffffff', strokeWidth: 0.002, weight: 700 } } }] });
await renderProject(brand, path.join(base, 'packaging-unsafe-preview'), { revision: 2, preview: true });
const unsafe = await cli('qa', brand, path.join(base, 'packaging-unsafe-preview'), path.join(base, 'packaging-unsafe-qa'));
assert.equal(unsafe.verdict, 'fail');
const unsafeCheck = unsafe.checks.find(c => c.id === 'caption-safe-area');
assert.equal(unsafeCheck.status, 'fail');
assert.ok(unsafeCheck.measured.boxes.find(b => b.item_id === 'low').bottom > 0.95);
summary.brand_packaging = { render: brandRender.status, templates: brandRender.templates, lint: { errors: brandRender.lint.error_count, warnings: brandRender.lint.warning_count },
  audio_limiter: brandRender.audio_limiter, signals: brandSignals, qa: { verdict: brandQa.verdict, checks: Object.fromEntries(brandQa.checks.map(c => [c.id, c.status])),
    true_peak: brandCheck('true-peak').measured }, fault_injection: { verdict: unsafe.verdict, caption_safe_area: unsafeCheck.status,
    low_caption_box: unsafeCheck.measured.boxes.find(b => b.item_id === 'low') } };

// 6. P2.1 portrait QA: burned-in caption cut points, per-shot sampling and
// template placements. Synthetic sources: a test pattern whose burned-in
// "caption" (white glyph boxes at ~70% height) switches at 1.5 s, and a file
// with a 0.6 s colour-bar shot inside it.
const captioned = path.join(base, 'captioned.mp4'), shortShot = path.join(base, 'short-shot.mp4');
await captionSource(captioned, { changeAt: 1.5 });
await captionSource(shortShot, { duration: 4, shortShot: [0.6, 1.2] });
const portrait = path.join(base, 'portrait');
await createProject(portrait, { project_id: 'portrait-smoke', title: '竖屏检查样例', canvas: { width: 360, height: 640, fps: 30 },
  assets: [{ id: 'cap', path: captioned }, { id: 'shots', path: shortShot }],
  tracks: [{ id: 'v_main', kind: 'video', locked: false }, { id: 'v_gfx', kind: 'video', locked: false }],
  items: [
    // In-point 1.3 s: the burned-in caption switches 0.2 s later (late, warn).
    { id: 'late', track_id: 'v_main', kind: 'media', asset_id: 'cap', start_frame: 0, frames: 30, source_in_seconds: 1.3, volume: 0 },
    // Source 0.6–1.2 s is a short shot: output 1.6–2.2 s, away from this item's midpoint (3.0 s) and cuts.
    { id: 'shots', track_id: 'v_main', kind: 'media', asset_id: 'shots', start_frame: 30, frames: 120, source_in_seconds: 0, volume: 0 },
    // In-point exactly at the caption change (aligned, no warning).
    { id: 'aligned', track_id: 'v_main', kind: 'media', asset_id: 'cap', start_frame: 150, frames: 30, source_in_seconds: 1.5, volume: 0 },
    { id: 'card', track_id: 'v_gfx', kind: 'graphic', template: 'title-card', vars: { title: '竖屏标题', placement: 'top' }, start_frame: 0, frames: 30 },
    { id: 'strap', track_id: 'v_gfx', kind: 'graphic', template: 'lower-third', vars: { title: '主讲人', subtitle: '副标题字号不小于三成', placement: 'upper' },
      start_frame: 150, frames: 30 }] });
const portraitRender = await renderProject(portrait, path.join(base, 'portrait-preview'), { revision: 1, preview: true });
assert.ok(portraitRender.templates.length === 2 && portraitRender.templates.every(t => t.pinned === true && t.source === 'project'), JSON.stringify(portraitRender.templates));
assert.equal(portraitRender.lint.warning_count + portraitRender.lint.error_count, 0, JSON.stringify(portraitRender.lint.findings));
const portraitHtml = await fs.readFile(path.join(base, 'portrait-preview/index.html'), 'utf8');
assert.match(portraitHtml, /id="g-card"[^>]*data-placement="top"[^>]*top:8%;width:80%;height:20%/);
assert.match(portraitHtml, /id="g-strap"[^>]*data-placement="upper"[^>]*top:14%;width:78%;height:20%;font-size:3\.6px;--fs-title:3\.6em;--fs-subtitle:3em/);
const portraitQa = await cli('qa', portrait, path.join(base, 'portrait-preview'), path.join(base, 'portrait-qa'), '--scene-threshold', '0.3');
const portraitCheck = id => portraitQa.checks.find(c => c.id === id);
const burned = portraitCheck('burned-caption-cut-points');
assert.equal(burned.status, 'warn', burned.observation);
const lateIn = burned.measured.points.find(p => p.item_id === 'late' && p.edge === 'in');
assert.ok(lateIn.result === 'warn' && Math.abs(lateIn.suggested_source_seconds - 45.5 / 30) < 1e-3, JSON.stringify(lateIn));
assert.equal(burned.measured.points.find(p => p.item_id === 'aligned' && p.edge === 'in').result, 'aligned');
assert.deepEqual(burned.measured.points.filter(p => p.result === 'warn').map(p => `${p.item_id}:${p.edge}`), ['late:in'], 'caption-free source and aligned cut stay quiet');
assert.equal(portraitCheck('shot-sampled').status, 'pass');
// The 'shots' item opens on the file's first frame and shows its 0.6 s bars shot whole: no fragment anywhere.
assert.equal(portraitCheck('cut-boundary-fragments').status, 'pass', portraitCheck('cut-boundary-fragments').observation);
const shotSample = portraitQa.samples.find(s => s.reason === 'shot' && s.time_seconds >= 1.6 && s.time_seconds < 2.2);
assert.ok(shotSample, `the 0.6 s shot is sampled: ${JSON.stringify(portraitCheck('shot-sampled').measured.shots)}`);
assert.equal(portraitCheck('graphic-safe-area').status, 'pass');
// The short shot's sample is bars, not the test pattern around it.
const barsShare = rgb => { let n = 0; for (let i = 0; i < rgb.length; i += 3) if (Math.max(rgb[i], rgb[i + 1], rgb[i + 2]) - Math.min(rgb[i], rgb[i + 1], rgb[i + 2]) > 100) n++; return n / (rgb.length / 3); };
summary.portrait_qa = { verdict: portraitQa.verdict, checks: Object.fromEntries(portraitQa.checks.map(c => [c.id, c.status])),
  burned_caption_points: burned.measured.points.map(p => ({ item: p.item_id, edge: p.edge, source: p.source_seconds, result: p.result, suggested: p.suggested_source_seconds ?? null })),
  shots: portraitCheck('shot-sampled').measured.shots, short_shot_sample: { id: shotSample.id, time: shotSample.time_seconds,
    saturated_share: barsShare(await frameAt(path.join(base, 'portrait-preview/video.mp4'), shotSample.time_seconds, 'scale=36:64')) } };
assert.ok(summary.portrait_qa.short_shot_sample.saturated_share > 0.3, JSON.stringify(summary.portrait_qa.short_shot_sample));

// 7. Source frame alignment: a 30 fps source turns from red to blue at frame 22
// (22/30 = 0.7333… s); the in-point is written truncated as 0.7333 (0.001 frame
// below frame 22). A v2 import records frame_rate and compilation plays from
// frame 22's start + 0.1 ms, so output frame 0 is blue and the cut-fragment
// check passes. A local-edit.v1 project (no frame_rate, historical behaviour)
// shows frame 21 (red) and QA warns.
const switching = path.join(base, 'switch-at-22.mp4');
await run(ffmpeg, ['-v', 'error', '-n', '-f', 'lavfi', '-i', 'color=c=red:s=320x180:r=30:d=0.7333333', '-f', 'lavfi', '-i', 'color=c=blue:s=320x180:r=30:d=1.2666667',
  '-filter_complex', '[0:v]trim=end_frame=22[a];[1:v]trim=end_frame=38,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30', switching]);
const snapped = path.join(base, 'frame-snap'), unsnapped = path.join(base, 'frame-snap-v1');
const snapDoc = await createProject(snapped, { project_id: 'frame-snap', title: '帧对齐', canvas: { width: 320, height: 180, fps: 30 },
  assets: [{ id: 'switch', path: switching }], tracks: [{ id: 'v_main', kind: 'video', locked: false }],
  items: [{ id: 'cut', track_id: 'v_main', kind: 'media', asset_id: 'switch', start_frame: 0, frames: 15, source_in_seconds: 0.7333, volume: 0 }] });
assert.equal(snapDoc.assets[0].frame_rate, '30/1', 'import records the source frame rate');
assert.equal((await readProject(snapped)).items[0].source_in_seconds, 0.7333, 'the document keeps the written in-point');
await createProject(unsnapped, { project_id: 'frame-snap-v1', title: '无帧率', canvas: { width: 320, height: 180, fps: 30 },
  assets: [{ id: 'switch', path: switching }], clips: [{ id: 'cut', asset_id: 'switch', in_seconds: 0.7333, frames: 15, volume: 0, fit: 'contain', captions: [] }], audio: [] });
await renderProject(snapped, path.join(base, 'frame-snap-preview'), { preview: true, revision: 1 });
await renderProject(unsnapped, path.join(base, 'frame-snap-v1-preview'), { preview: true, revision: 1 });
assert.match(await fs.readFile(path.join(base, 'frame-snap-preview/index.html'), 'utf8'), /id="v-cut"[^>]*data-media-start="0\.733433333"/);
const firstFrame = async dir => (await run(ffmpeg, ['-v', 'error', '-i', path.join(base, dir, 'video.mp4'), '-vf', 'select=eq(n\\,0),scale=8:8', '-frames:v', '1',
  '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], { encoding: 'buffer' })).stdout;
const tint = rgb => { let r = 0, b = 0; for (let i = 0; i < rgb.length; i += 3) { r += rgb[i]; b += rgb[i + 2]; } return r > b ? 'red' : 'blue'; };
const firstColours = { snapped: tint(await firstFrame('frame-snap-preview')), v1_without_frame_rate: tint(await firstFrame('frame-snap-v1-preview')) };
assert.deepEqual(firstColours, { snapped: 'blue', v1_without_frame_rate: 'red' });
const snapQa = await cli('qa', snapped, path.join(base, 'frame-snap-preview'), path.join(base, 'frame-snap-qa'));
const snapFragments = snapQa.checks.find(c => c.id === 'cut-boundary-fragments');
assert.equal(snapFragments.status, 'pass', snapFragments.observation);
const snapIn = snapFragments.measured.points.find(p => p.edge === 'in');
assert.deepEqual([snapIn.source_frame, snapIn.source_seconds, snapIn.compiled_source_seconds, snapIn.result], [22, 0.7333, 0.733433, 'aligned']);
const v1Qa = await cli('qa', unsnapped, path.join(base, 'frame-snap-v1-preview'), path.join(base, 'frame-snap-v1-qa'));
const v1Fragments = v1Qa.checks.find(c => c.id === 'cut-boundary-fragments');
assert.equal(v1Fragments.status, 'warn', v1Fragments.observation);
summary.frame_snap = { first_frame: firstColours, qa_fragments: { snapped: snapFragments.status, without_frame_rate: v1Fragments.status },
  snapped_in: { source_frame: snapIn.source_frame, compiled_source_seconds: snapIn.compiled_source_seconds } };

// analyze → suggest-cuts → apply-cuts on synthetic footage; the emitted plan
// beats are validated by Python jsonschema against production-plan.schema.json
// (apply-cuts checks them with its own small validator; this is the reference).
const footage = await synthFootage(path.join(base, 'footage.mov'));
const footageText = await footageTranscript(footage, path.join(base, 'footage-transcript.json'));
await cli('analyze', footage, path.join(base, 'footage-analysis.json'), '--transcript', footageText);
await fs.writeFile(path.join(base, 'footage-beats.json'), JSON.stringify({ asset_id: 'footage', beats: [{ id: 'third', from: 2.5, to: 3.8,
  role: 'proof', purpose: 'Synthetic third line.', requirement: 'Complete phrase.', hard_constraints: ['keep the caption box'] }] }));
const footageCuts = await cli('suggest-cuts', path.join(base, 'footage-analysis.json'), path.join(base, 'footage-beats.json'), path.join(base, 'footage-cuts.json'));
const applied = await cli('apply-cuts', path.join(base, 'footage-cuts.json'), path.join(base, 'footage-applied.json'),
  ...footageCuts.needs_decision.flatMap(b => b.decisions.flatMap(d => ['--choose', `${b.id}.${d.edge}=keep_speech`])));
assert.deepEqual([applied.status, applied.plan_status], ['applied', 'valid'], JSON.stringify(applied));
const appliedDoc = JSON.parse(await fs.readFile(path.join(base, 'footage-applied.json'), 'utf8'));
const planFile = path.join(base, 'footage-plan.json');
await fs.writeFile(planFile, JSON.stringify({ schema_version: 'creative-craft.production-plan.v1', plan_id: 'smoke-footage', title: 'Smoke footage plan', brief_ref: null,
  intended_use: 'smoke test', output: { duration_seconds_target: 1, ratio: '16:9', language: 'zh-CN' }, delivery_promises: [], beats: appliedDoc.plan_beats }));
await validateSchema('production-plan.schema.json', [planFile]);
summary.apply_cuts = { items: appliedDoc.items.length, plan_beats: appliedDoc.plan_beats.length, evidence: appliedDoc.plan_beats[0].selection.evidence.length };

const revisionFiles = [v2, brand, portrait, snapped].flatMap(dir => readdirSync(path.join(dir, 'revisions')).filter(n => n.endsWith('.json')).map(n => path.join(dir, 'revisions', n)));
revisionFiles.push(...[6, 7].map(n => path.join(root, 'revisions', `00000${n}.json`)));
await validateSchema('edit-document-v2.schema.json', revisionFiles);
const qaDirs = ['multitrack-qa', 'tampered-qa', 'packaging-qa', 'packaging-unsafe-qa', 'portrait-qa', 'frame-snap-qa', 'frame-snap-v1-qa'];
await validateSchema('render-qa.schema.json', qaDirs.map(d => path.join(base, d, 'qa.json')));
summary.schema = { revisions: revisionFiles.length, qa_files: qaDirs.length, status: 'passed' };
summary.input_preserved = before === await digest(source);
summary.status = 'passed';
await fs.writeFile(path.join(base, 'summary.json'), JSON.stringify(summary, null, 2));
console.log(`SMOKE_ARTIFACTS=${base}`);

}
if (!process.argv[2]) {
  await withRetentionLock(retentionRoot, async () => {
    await smoke();
    console.log('SMOKE_RETENTION=' + JSON.stringify(await applyRetention(await planRetention())));
  });
} else {
  await smoke(); // Custom output is never automatically retired.
}
