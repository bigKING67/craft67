import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { runCutChecks } from '../cut-checks.mjs';
import { decisionAcceptor } from '../qa.mjs';
import { checkSummary } from '../review-page.mjs';
import { run } from '../project.mjs';

const doc = { canvas: { fps: 30 }, assets: [{ id: 'film', file: 'f.mp4' }], tracks: [{ id: 'v', kind: 'video' }],
  items: [{ id: 'close', track_id: 'v', kind: 'media', asset_id: 'film', start_frame: 0, frames: 60, source_in_seconds: 5.016667 }] };
// A stand-in check: every point warns with a shot fragment (rules: shot).
const fakeCheck = {
  measured: {}, none: 'none', range: p => [p.source_seconds - 0.1, p.source_seconds + 0.1],
  analyse: () => ({ result: 'warn', kind: 'fragment' }), rulesOf: () => ['shot'],
  summary: n => ({ scope: `${n} point(s)`, finding: 'fragment', describe: e => `${e.item_id} ${e.edge}`, warned: (c, d) => `${c} warned: ${d}.`, pass: 'pass.' }),
};
const decode = async () => ({ frames: [new Uint8Array(4)], times: [0], width: 2, height: 2 });

test('decisions: an accepted finding at the decided edge is not a warning; another edge still warns', async t => {
  const dir = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'creative-decisions-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const write = async (name, value) => { const f = path.join(dir, name); await fs.writeFile(f, JSON.stringify(value)); return f; };
  await run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=64x64:rate=30:duration=8', '-pix_fmt', 'yuv420p', path.join(dir, 'f.mp4')]);
  const applied = { schema: 'creative-craft.applied-cuts.v1', decisions: [{ beat: 'close', edge: 'in', asset_id: 'film', option: 'keep_speech', by: 'prefer', frame: 150, seconds: 5.016667, accepts: ['shot'] }] };
  const accept = await decisionAcceptor(doc, await write('applied.json', applied));
  const [result] = await runCutChecks(doc, dir, [fakeCheck], { decode, accept });
  assert.deepEqual(result.measured.points.map(e => [e.edge, e.result, e.accepted?.option ?? null]), [['in', 'accepted', 'keep_speech'], ['out', 'warn', null]]);
  assert.equal(result.status, 'warn');
  assert.match(result.observation, /1 finding\(s\) accepted by a recorded edit decision \(close in-point: keep_speech by prefer\)/);
  // A moved edge, an option that does not accept the rule, or an item the revision lacks.
  const moved = await decisionAcceptor(doc, await write('moved.json', { ...applied, decisions: [{ ...applied.decisions[0], seconds: 5.2 }] }));
  assert.equal(moved({ item_id: 'close', edge: 'in', source_seconds: 5.016667 }, ['shot']), null, 'moved by more than a frame');
  // Rounding: a 60 fps source on a 30 fps canvas moves an out-point by up to half an output frame; still the same edge.
  const sixty = { ...doc, assets: [{ id: 'film', file: 'f.mp4', frame_rate: '60/1' }] };
  const out = await decisionAcceptor(sixty, await write('out.json', { ...applied, decisions: [{ ...applied.decisions[0], edge: 'out', seconds: 7.008333 }] }));
  assert.ok(out({ item_id: 'close', edge: 'out', source_seconds: 7.025 }, ['shot']), 'half an output frame later (1/60 s) is the decided edge');
  assert.equal(out({ item_id: 'close', edge: 'out', source_seconds: 7.05 }, ['shot']), null, 'a whole output frame later is a moved edge');
  await assert.rejects(decisionAcceptor(doc, await write('nul.json', { ...applied, decisions: [{ ...applied.decisions[0], accepts: null }] })), /before 0\.13 .*rerun suggest-cuts and apply-cuts/);
  await assert.rejects(decisionAcceptor(doc, await write('bad.json', { ...applied, decisions: [{ ...applied.decisions[0], seconds: '5.0' }] })), /decisions\[0\] needs beat, edge in\/out/);
  await assert.rejects(decisionAcceptor(doc, await write('asset.json', { ...applied, decisions: [{ ...applied.decisions[0], asset_id: 'reshoot' }] })), /close on asset reshoot, but this revision uses film/);
  const caption = await decisionAcceptor(doc, await write('cap.json', applied));
  assert.equal(caption({ item_id: 'close', edge: 'in', source_seconds: 5.016667 }, ['caption']), null);
  await assert.rejects(decisionAcceptor(doc, await write('gone.json', { ...applied, decisions: [{ ...applied.decisions[0], beat: 'gone' }] })), /item\(s\) gone that this revision does not have/);
  await assert.rejects(decisionAcceptor(doc, await write('old.json', { schema: 'creative-craft.applied-cuts.v1' })), /no decisions/);
  await assert.rejects(decisionAcceptor(doc, await write('x.json', { schema: 'x' })), /not a creative-craft\.applied-cuts\.v1 file/);
  // Only accepted findings: pass, with the decision named.
  const both = await decisionAcceptor(doc, await write('both.json', { ...applied, decisions: [...applied.decisions, { ...applied.decisions[0], edge: 'out', seconds: 7.016667 }] }));
  const [clean] = await runCutChecks(doc, dir, [fakeCheck], { decode, accept: both });
  assert.equal(clean.status, 'pass');
  assert.match(clean.observation, /^No open fragment at 2 point\(s\): each one found is accepted by a recorded edit decision\./);
});

test('review page names accepted findings in Chinese', () => {
  const text = checkSummary({ id: 'cut-boundary-fragments', status: 'pass', observation: 'x', measured: { window_seconds: 1, points: [
    { item_id: 'close', edge: 'in', output_seconds: 11.333, result: 'accepted', kind: 'fragment', accepted: { by: 'prefer', option: 'keep_speech', rules: ['shot'] } },
    { item_id: 'hook', edge: 'in', output_seconds: 0, result: 'clear' }] } });
  assert.match(text, /都没有相邻镜头碎片、闪场或黑场过渡（已接受的除外）。1 处已按剪辑决定接受：成片 0:11\.33 close 入点（保留整句，BEATS\.json 事先决定）。/);
});
