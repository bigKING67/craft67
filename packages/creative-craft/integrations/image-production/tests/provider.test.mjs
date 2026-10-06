import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import sharp from 'sharp';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createProject, readProject, editBatch } from '../project.mjs';
import { demoInput } from '../fixtures.mjs';
import { executeProvider, checkProvider, recoverProvider } from '../provider.mjs';
import { codexCredentials } from '../provider-config.mjs';
import { inspectCandidate, acceptCandidate } from '../candidates.mjs';
import { inspectAlpha, requireAlpha } from '../provider-alpha.mjs';
import { readExecution } from '../provider-store.mjs';
import { sha256 } from '../../local-production/content-store.mjs';
import { runAcceptance } from '../provider-acceptance.mjs';

const template = JSON.parse(await fs.readFile(fileURLToPath(new URL('../../../skills/creative-craft/templates/image-job.json', import.meta.url))));
const fakeKey = 'test-only-private-credential';
async function fixture(t, handler) {
  const directory = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'craft-provider-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const input = await demoInput(path.join(directory, 'inputs'));
  const background = input.assets.find(asset => asset.id === 'background');
  const resized = await sharp(background.source).resize(1024, 1024).png().toBuffer();
  background.source = path.join(directory, 'background.png'); await fs.writeFile(background.source, resized);
  input.canvas.width = 1024; input.canvas.height = 1024;
  Object.assign(input.objects.find(object => object.id === 'background'), { width: 1024, height: 1024 });
  const root = path.join(directory, 'project'); const created = await createProject(root, input);
  const proposed = await sharp({ create: { width: 1024, height: 1024, channels: 4, background: '#cce4e0' } }).png().toBuffer();
  const calls = [];
  const server = http.createServer(async (req, res) => {
    try {
      const chunks = []; for await (const chunk of req) chunks.push(chunk);
      const call = { url: req.url, headers: req.headers, body: Buffer.concat(chunks) }; calls.push(call);
      if (req.url === '/v1/models') { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify({ data: [{ id: 'gpt-image-2.5-sunburst' }, { id: 'gpt-image-2.5-flare' }] })); }
      else if (handler) await handler(call, res, proposed, root);
      else { res.setHeader('Content-Type', 'application/json'); res.setHeader('x-request-id', 'request-test-123'); res.end(JSON.stringify({ data: [{ b64_json: proposed.toString('base64') }], usage: { input_tokens: 12, output_tokens: 24, extra: fakeKey } })); }
    } catch { res.destroy(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); return new Promise(resolve => server.close(resolve)); });
  const configDirectory = path.join(directory, 'config'); await fs.mkdir(configDirectory);
  await fs.writeFile(path.join(configDirectory, 'config.toml'), `model_provider = "selected"\n[model_providers.selected]\nbase_url = "http://127.0.0.1:${server.address().port}/v1"\nwire_api = "responses"\n[model_providers.ignored]\nbase_url = "https://invalid.example/v1"\n`);
  await fs.writeFile(path.join(configDirectory, 'auth.json'), JSON.stringify({ OPENAI_API_KEY: fakeKey }));
  const job = structuredClone(template); Object.assign(job, { job_id: 'background-job', declared_status: 'ready', provider_profile: 'openai.gpt-image-2.5-sunburst.2026-09-08' });
  job.prompt.scene = 'Warm studio background'; job.intended_use = 'Synthetic test background'; job.rights.status = 'CLEARED';
  const jobPath = path.join(directory, 'job.json'); await fs.writeFile(jobPath, JSON.stringify(job, null, 2));
  const spec = { job: jobPath, candidate_id: 'generated-background', base_revision: 1, target_id: 'background', references: [] };
  return { directory, root, created, proposed, calls, configDirectory, job, jobPath, spec,
    saveJob: () => fs.writeFile(jobPath, JSON.stringify(job, null, 2)) };
}

test('config uses active provider and auth.json; dry-run has no network or project writes', async t => {
  const f = await fixture(t);
  const credentials = await codexCredentials(f.configDirectory); assert.equal(credentials.provider, 'selected'); assert.equal(credentials.key, fakeKey);
  const before = await fs.readdir(f.root);
  const dry = await executeProvider(f.root, f.spec, { dryRun: true, configDirectory: '/missing-config' });
  assert.equal(dry.network_requests, 0); assert.deepEqual(await fs.readdir(f.root), before); assert.equal(f.calls.length, 0);
  const check = await checkProvider({ configDirectory: f.configDirectory });
  assert.ok(check.models.every(model => model.advertised)); assert.equal(check.configured_wire_api, 'responses');
  assert.ok(!JSON.stringify(check).includes(fakeKey)); assert.equal(check.generation_verified, false);
});

test('real HTTP generation creates a receipt-bound candidate without accepting; credentials never persist', async t => {
  const f = await fixture(t);
  const result = await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory });
  assert.equal(result.receipt.outcome, 'succeeded'); assert.equal(result.receipt.snapshot, null);
  assert.equal(result.receipt.parameters.client_post_attempts, 1); assert.deepEqual(result.receipt.parameters.usage, { input_tokens: 12, output_tokens: 24 });
  assert.equal(result.receipt.parameters.billing.state, 'UNVERIFIED'); assert.equal(result.receipt.provider_execution_id, 'request-test-123');
  assert.equal((await readProject(f.root)).sha256, f.created.sha256); assert.equal(result.candidate.status, 'ready');
  assert.equal(f.calls.length, 1); assert.equal(f.calls[0].headers.authorization, `Bearer ${fakeKey}`);
  const body = JSON.parse(f.calls[0].body); assert.equal(body.model, 'gpt-image-2.5-sunburst'); assert.equal(body.n, 1); assert.ok(body.prompt.includes('BACKGROUND / SCENE'));
  for (const entry of await fs.readdir(result.job)) if (entry.endsWith('.json') || entry.endsWith('.md')) assert.ok(!(await fs.readFile(path.join(result.job, entry), 'utf8')).includes(fakeKey));
  await acceptCandidate(f.root, { candidate_id: f.spec.candidate_id, base_revision: 1, author: 'agent', summary: 'Accept test output' });
  assert.equal((await readProject(f.root)).document.revision, 2);
  const receiptFile = path.join(result.job, 'receipt.json'); await fs.appendFile(receiptFile, '\n');
  await assert.rejects(inspectCandidate(f.root, f.spec.candidate_id), /Execution binding digest/);
});

test('Flare uses its explicit model ID; invalid formal jobs/references/stale revisions fail before POST', async t => {
  const f = await fixture(t);
  f.job.canvas.variants = 2; await f.saveJob(); await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /one PNG/);
  f.job.canvas.variants = 1; f.job.canvas.size = '1000x1000'; await f.saveJob(); await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /canonical contract/);
  f.job.canvas.size = '1024x1024'; f.job.provider_profile = 'openai.gpt-image-2.5-flare.2026-09-08'; await f.saveJob();
  await assert.rejects(executeProvider(f.root, { ...f.spec, references: [{ asset_id: 'unbound', source: f.jobPath }] }, { configDirectory: f.configDirectory }), /Reference inputs/);
  await assert.rejects(executeProvider(f.root, { ...f.spec, base_revision: 2 }, { configDirectory: f.configDirectory }), /base revision/);
  assert.equal(f.calls.length, 0);
  const result = await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }); assert.equal(result.receipt.model, 'gpt-image-2.5-flare');
});

test('HTTP error is redacted, does not retry, and the job claim prevents rerunning a failed request', async t => {
  const f = await fixture(t, async (call, res) => { res.statusCode = 503; res.end(JSON.stringify({ error: { message: `${fakeKey} secret provider body` } })); });
  let failure; try { await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }); } catch (e) { failure = e; }
  assert.equal(failure.receipt.outcome, 'failed'); assert.equal(failure.receipt.parameters.http_status, 503); assert.ok(!JSON.stringify(failure.receipt).includes(fakeKey));
  assert.equal(f.calls.length, 1); assert.equal((await readProject(f.root)).sha256, f.created.sha256);
  await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /EEXIST/); assert.equal(f.calls.length, 1);
});

test('timeout/cancel have no accepted revision or success output and do not retry', async t => {
  for (const mode of ['timeout', 'cancel']) await t.test(mode, async t => {
    const controller = new AbortController();
    const f = await fixture(t, async () => { if (mode === 'cancel') controller.abort(); });
    let failure; try { await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory, timeoutMs: 1000, signal: controller.signal }); } catch (e) { failure = e; }
    assert.equal(failure.receipt.outcome, mode === 'cancel' ? 'cancelled' : 'failed');
    assert.equal(failure.receipt.provider_errors[0].code, mode === 'cancel' ? 'cancelled' : 'timeout'); assert.equal(failure.receipt.provider_errors[0].upstream_execution_unknown, true);
    assert.deepEqual(failure.receipt.outputs, []); assert.equal(f.calls.length, 1); assert.equal((await readProject(f.root)).sha256, f.created.sha256);
  });
});

test('malformed/URL/wrong-dimension output fails closed with a durable receipt', async t => {
  for (const mode of ['url', 'invalid-base64', 'wrong-size']) await t.test(mode, async t => {
    const f = await fixture(t, async (call, res) => {
      const image = await sharp({ create: { width: 64, height: 64, channels: 4, background: '#ffffff' } }).png().toBuffer();
      res.end(JSON.stringify({ data: [mode === 'url' ? { url: 'https://invalid.example/image.png' } : { b64_json: mode === 'wrong-size' ? image.toString('base64') : '!!not-base64' }] }));
    });
    await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /see bound receipt/);
    const receipt = JSON.parse(await fs.readFile(path.join(f.root, 'jobs/background-job/receipt.json')));
    assert.equal(receipt.outcome, mode === 'wrong-size' ? 'partial' : 'failed');
    if (mode === 'wrong-size') { assert.equal(receipt.outputs.length, 1); assert.equal(receipt.parameters.returned_image.width, 64); assert.ok((await fs.stat(path.join(f.root,receipt.outputs[0].path))).size>0); }
    else assert.deepEqual(receipt.outputs, []);
    assert.equal((await readProject(f.root)).sha256, f.created.sha256); assert.equal(f.calls.length, 1);
  });
});

test('human edit during generation leaves successful Provider output in a stale candidate', async t => {
  const f = await fixture(t, async (call, res, image, root) => {
    await editBatch(root, { base_revision: 1, author: 'human', summary: 'Human price edit', operations: [{ type: 'update_object', id: 'price', patch: { text: '¥149' } }] });
    res.end(JSON.stringify({ data: [{ b64_json: image.toString('base64') }] }));
  });
  const result = await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory });
  assert.equal(result.receipt.outcome, 'succeeded'); assert.equal(result.candidate.status, 'stale');
  await assert.rejects(acceptCandidate(f.root, { candidate_id: f.spec.candidate_id, base_revision: 2, author: 'agent', summary: 'Must fail' }), /Candidate base revision/);
  assert.equal((await readProject(f.root)).document.objects.find(o => o.id === 'price').text, '¥149');
});

test('masked HTTP edit converts local polarity to Provider alpha and preserves protected/outside pixels', async t => {
  const f = await fixture(t);
  const asset = f.created.document.assets.find(a => a.id === 'background');
  f.job.task_type = 'edit'; f.job.asset_refs = [asset.id]; f.job.prompt.references = [{ asset_id: asset.id, role: 'edit source', preserve: ['outside selection'] }];
  f.job.prompt.change = ['Replace local background patch']; f.job.prompt.preserve = ['Product and logo']; await f.saveJob();
  f.spec.references = [{ asset_id: asset.id, source: path.join(f.root, asset.render_file) }];
  const pixels = 1024 * 1024; const generation = Buffer.alloc(pixels), protection = Buffer.alloc(pixels), blend = Buffer.alloc(pixels);
  for (let y = 810; y < 850; y++) for (let x = 920; x < 960; x++) generation[y * 1024 + x] = blend[y * 1024 + x] = 255;
  protection[820 * 1024 + 930] = 255;
  f.spec.edit = { context: { x: 0, y: 0, width: 1024, height: 1024 } };
  for (const [name, data] of Object.entries({ generation_mask: generation, protection_mask: protection, blend_mask: blend })) {
    const file = path.join(f.directory, name+'.png'); await sharp(data, { raw: { width: 1024, height: 1024, channels: 1 } }).toColourspace('b-w').png().toFile(file); f.spec.edit[name] = file;
  }
  const result = await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory });
  assert.equal(f.calls[0].url, '/v1/images/edits'); assert.ok(f.calls[0].headers['content-type'].startsWith('multipart/form-data'));
  const alpha = await sharp(path.join(result.job, 'provider-mask.png')).ensureAlpha().raw().toBuffer();
  assert.equal(alpha[(820*1024+930)*4+3],255); assert.equal(alpha[(820*1024+940)*4+3],0); assert.equal(alpha[3],255);
  assert.equal(result.candidate.candidate.qa.protected_changed_pixels,0); assert.equal(result.candidate.candidate.qa.outside_blend_changed_pixels,0);
  const head = await readProject(f.root); assert.equal(head.sha256,f.created.sha256);
});

test('concurrent runs of the same job publish one claim and send exactly one client POST', async t => {
  const f = await fixture(t);
  const results = await Promise.allSettled([executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), executeProvider(f.root, f.spec, { configDirectory: f.configDirectory })]);
  assert.equal(results.filter(r => r.status === 'fulfilled').length, 1); assert.equal(f.calls.length, 1);
});

test('Provider success with unstageable output is retained and cannot trigger a second generation', async t => {
  const f = await fixture(t, async (call,res,image,root) => {
    const project = await readProject(root); const asset = project.document.assets.find(a => a.id === 'background');
    const bytes = await fs.readFile(path.join(root,asset.render_file)); res.end(JSON.stringify({data:[{b64_json:bytes.toString('base64')}]}));
  });
  let failure; try { await executeProvider(f.root,f.spec,{configDirectory:f.configDirectory}); } catch(e) { failure=e; }
  assert.equal(failure.receipt.outcome,'succeeded'); assert.match(failure.message,/Output retained/);
  const state=JSON.parse(await fs.readFile(path.join(failure.output,'result.json'))); assert.equal(state.status,'candidate_failed');
  assert.ok((await fs.stat(path.join(failure.output,'output.png'))).size>0); assert.equal((await readProject(f.root)).sha256,f.created.sha256);
  await assert.rejects(executeProvider(f.root,f.spec,{configDirectory:f.configDirectory}),/EEXIST/); assert.equal(f.calls.length,1);
});

test('acceptance report separates provider success from candidate and comparison failures', async t => {
  for (const mode of ['ready', 'candidate-failed', 'comparison-failed']) await t.test(mode, async t => {
    let posts = 0;
    const f = await fixture(t, async (call, res, image, root) => {
      posts++;
      if (mode === 'candidate-failed' && posts === 3) {
        const project = await readProject(root), asset = project.document.assets.find(value => value.id === 'background');
        image = await fs.readFile(path.join(root, asset.render_file));
      }
      res.end(JSON.stringify({ data: [{ b64_json: image.toString('base64') }] }));
    });
    const output = path.join(f.directory, 'acceptance'); await fs.mkdir(output);
    const jobs = [];
    for (let index = 1; index <= 3; index++) {
      const name = `acceptance-${index}`, job = { ...f.job, job_id: name };
      const jobFile = path.join(output, `${name}-job.json`);
      await fs.writeFile(jobFile, JSON.stringify(job));
      await fs.writeFile(path.join(output, `${name}-input.json`), JSON.stringify({ ...f.spec, job: jobFile, candidate_id: name }));
      jobs.push({ name, root: f.root, input: `${name}-input.json` });
    }
    await fs.writeFile(path.join(output, 'plan.json'), JSON.stringify({ client_post_limit: 3, jobs }));
    if (mode === 'comparison-failed') await fs.mkdir(path.join(output, 'acceptance-3-compare'));
    const report = await runAcceptance(output, { configDirectory: f.configDirectory });
    const persisted = JSON.parse(await fs.readFile(path.join(output, 'live-report.json')));
    assert.deepEqual(persisted, report);
    assert.equal(report.status, mode === 'ready' ? 'CANDIDATES_READY_FOR_INSPECTION' : 'PARTIAL');
    assert.equal(report.events.length, 3);
    assert.ok(report.events.every(event => event.provider_outcome === 'succeeded'));
    assert.deepEqual(report.events.map(event => event.outcome), ['succeeded', 'succeeded', mode === 'ready' ? 'succeeded' : 'failed']);
    assert.equal(report.real_product_quality, 'UNVERIFIED'); assert.equal(report.owner_approval, 'UNVERIFIED');
    assert.equal(report.global_config_unchanged, true); assert.equal(report.auth_unchanged, true);
    assert.equal(posts, 3); assert.equal((await readProject(f.root)).sha256, f.created.sha256);
    const state = JSON.parse(await fs.readFile(path.join(f.root, 'jobs/acceptance-3/result.json')));
    assert.equal(state.status, mode === 'candidate-failed' ? 'candidate_failed' : 'candidate');
    if (mode === 'candidate-failed') await assert.rejects(inspectCandidate(f.root, 'acceptance-3'), { code: 'ENOENT' });
    else assert.equal((await inspectCandidate(f.root, 'acceptance-3')).status, 'ready');
    assert.ok(!JSON.stringify(report).includes(fakeKey));
  });
});

test('explicit same-aspect normalization retains native output and binds the resized PNG', async t => {
  const f = await fixture(t,async(call,res,image)=>{
    const native=await sharp(image).resize(1254,1254).png().toBuffer();res.end(JSON.stringify({data:[{b64_json:native.toString('base64')}]}));
  });
  const result=await executeProvider(f.root,{...f.spec,output_policy:'resize_to_target'},{configDirectory:f.configDirectory});
  assert.deepEqual(result.receipt.parameters.output_normalization.source_size,[1254,1254]);
  assert.deepEqual(result.receipt.parameters.output_normalization.target_size,[1024,1024]);
  assert.equal(result.receipt.outputs.length,2);assert.equal(result.candidate.candidate.source.width,1024);
  assert.equal(result.receipt.parameters.output_normalization.crop,false);assert.equal(f.calls.length,1);
  await inspectCandidate(f.root,f.spec.candidate_id);
});

test('retained native-size output recovers offline without mutating the old receipt or repeating POST', async t=>{
  const f=await fixture(t,async(call,res,image)=>{
    const native=await sharp(image).resize(1254,1254).png().toBuffer();res.end(JSON.stringify({data:[{b64_json:native.toString('base64')}]}));
  });
  await assert.rejects(executeProvider(f.root,f.spec,{configDirectory:f.configDirectory}),/see bound receipt/);
  const before=await fs.readFile(path.join(f.root,'jobs/background-job/receipt.json'));
  const recovered=await recoverProvider(f.root,{job_id:'background-job',candidate_id:'recovered-native',output_policy:'resize_to_target'});
  assert.equal(recovered.network_requests,0);assert.equal(f.calls.length,1);assert.equal(recovered.candidate.status,'ready');
  assert.deepEqual(await fs.readFile(path.join(f.root,'jobs/background-job/receipt.json')),before);
  await acceptCandidate(f.root,{candidate_id:'recovered-native',base_revision:1,author:'agent',summary:'Accept resampled fixture'});
  await fs.appendFile(path.join(f.root,'jobs/background-job/received-output.png'),'tamper');
  await assert.rejects(inspectCandidate(f.root,'recovered-native'),/Normalization source binding/);
});

test('normalization does not crop or stretch a different aspect ratio', async t=>{
  const f=await fixture(t,async(call,res,image)=>{
    const native=await sharp(image).resize(1024,1536).png().toBuffer();res.end(JSON.stringify({data:[{b64_json:native.toString('base64')}]}));
  });
  await assert.rejects(executeProvider(f.root,{...f.spec,output_policy:'resize_to_target'},{configDirectory:f.configDirectory}),/see bound receipt/);
  await assert.rejects(recoverProvider(f.root,{job_id:'background-job',candidate_id:'reject-distortion',output_policy:'resize_to_target'}),/output_dimensions/);
  assert.equal(f.calls.length,1);assert.equal((await readProject(f.root)).sha256,f.created.sha256);
});

async function transparentPNG(size = 1024) {
  const data = Buffer.alloc(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const at = (y * size + x) * 4;
    data[at] = 220; data[at + 1] = 100; data[at + 2] = 60;
    data[at + 3] = x < size / 2 ? 0 : x === size / 2 ? 128 : 255;
  }
  return sharp(data, { raw: { width: size, height: size, channels: 4 } }).png().toBuffer();
}

test('Sunburst and Flare transparent PNGs bind actual alpha and remain unaccepted', async t => {
  for (const model of ['sunburst', 'flare']) await t.test(model, async t => {
    const image = await transparentPNG();
    const f = await fixture(t, async (call, res) => res.end(JSON.stringify({ data: [{ b64_json: image.toString('base64') }] })));
    f.job.provider_profile = `openai.gpt-image-2.5-${model}.2026-09-08`; f.job.canvas.background = 'transparent'; await f.saveJob();
    const dry = await executeProvider(f.root, f.spec, { dryRun: true });
    assert.equal(dry.request.parameters.background, 'transparent'); assert.equal(f.calls.length, 0);
    const result = await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory });
    const checks = result.receipt.parameters.transparency;
    assert.equal(JSON.parse(f.calls[0].body).background, 'transparent');
    assert.equal(checks.received.zero_pixels, 512 * 1024); assert.equal(checks.received.partial_pixels, 1024);
    assert.deepEqual(checks.output, checks.received); assert.equal(checks.output.sha256, sha256(image));
    assert.equal((await inspectCandidate(f.root, f.spec.candidate_id)).status, 'ready');
    assert.equal((await readProject(f.root)).sha256, f.created.sha256); assert.equal(f.calls.length, 1);
  });
});

test('missing alpha, opaque RGBA, partial-only and empty outputs retain specific failures without retry', async t => {
  for (const [mode, color, channels, code] of [
    ['no-alpha', '#eeeeee', 3, 'output_missing_alpha'],
    ['opaque-rgba', '#eeeeee', 4, 'output_no_clear_background'],
    ['partial-only', '#ffffff80', 4, 'output_no_clear_background'],
    ['empty', '#ff00ff00', 4, 'output_empty_foreground'],
  ]) await t.test(mode, async t => {
    const image = await sharp({ create: { width: 1024, height: 1024, channels, background: color } }).png().toBuffer();
    const f = await fixture(t, async (call, res) => res.end(JSON.stringify({ data: [{ b64_json: image.toString('base64') }] })));
    f.job.canvas.background = 'transparent'; await f.saveJob();
    let error; try { await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }); } catch (caught) { error = caught; }
    assert.equal(error.receipt.outcome, 'partial'); assert.equal(error.receipt.provider_errors[0].code, code);
    assert.equal(error.receipt.parameters.transparency.received.sha256, sha256(image));
    assert.deepEqual(await fs.readFile(path.join(error.output, 'received-output.png')), image);
    await assert.rejects(fs.stat(path.join(error.output, 'output.png')), { code: 'ENOENT' });
    await assert.rejects(inspectCandidate(f.root, f.spec.candidate_id), { code: 'ENOENT' });
    await assert.rejects(recoverProvider(f.root, { job_id: f.job.job_id, candidate_id: 'invalid-recovery', output_policy: 'resize_to_target' }), /partial size-mismatch/);
    await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /EEXIST/);
    assert.equal(f.calls.length, 1); assert.equal((await readProject(f.root)).sha256, f.created.sha256);
  });
});

test('ordinary opaque/auto receipts still reopen without alpha evidence', async t => {
  for (const background of ['opaque', 'auto']) await t.test(background, async t => {
    const f = await fixture(t); f.job.canvas.background = background; await f.saveJob();
    const result = await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory });
    assert.equal(result.receipt.parameters.transparency, undefined);
    await acceptCandidate(f.root, { candidate_id: f.spec.candidate_id, base_revision: 1, author: 'agent', summary: 'Ordinary compatibility' });
    assert.equal((await inspectCandidate(f.root, f.spec.candidate_id)).status, 'accepted');
  });
});

test('transparent edit protects original RGBA and rejects a composed result with no clear background', async t => {
  for (const hideAllClearPixels of [false, true, 'recovery']) await t.test(String(hideAllClearPixels), async t => {
    const image = await transparentPNG(hideAllClearPixels === 'recovery' ? 1254 : 1024);
    const f = await fixture(t, async (call, res) => res.end(JSON.stringify({ data: [{ b64_json: image.toString('base64') }] })));
    const asset = f.created.document.assets.find(a => a.id === 'background');
    f.job.canvas.background = 'transparent'; f.job.task_type = 'edit'; f.job.asset_refs = [asset.id];
    f.job.prompt.references = [{ asset_id: asset.id, role: 'edit source', preserve: ['protected pixels'] }]; await f.saveJob();
    f.spec.references = [{ asset_id: asset.id, source: path.join(f.root, asset.render_file) }];
    const full = Buffer.alloc(1024 * 1024, 255), protection = Buffer.alloc(full.length);
    for (let y = 0; y < 1024; y++) for (let x = 0; x < 512; x++) if (hideAllClearPixels || (x < 8 && y < 8)) protection[y * 1024 + x] = 255;
    f.spec.edit = { context: { x: 0, y: 0, width: 1024, height: 1024 } };
    for (const [name, data] of Object.entries({ generation_mask: full, protection_mask: protection, blend_mask: full })) {
      const file = path.join(f.directory, `${name}.png`);
      await sharp(data, { raw: { width: 1024, height: 1024, channels: 1 } }).toColourspace('b-w').png().toFile(file); f.spec.edit[name] = file;
    }
    if (hideAllClearPixels) {
      if (hideAllClearPixels === 'recovery') {
        await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /see bound receipt/);
        let failure;
        try { await recoverProvider(f.root, { job_id: f.job.job_id, candidate_id: f.spec.candidate_id, output_policy: 'resize_to_target' }); }
        catch (error) { failure = error; }
        assert.match(failure.message, /candidate staging failed/); assert.equal(failure.receipt.outcome, 'succeeded');
        assert.ok(await fs.stat(path.join(failure.output, 'output.png')));
      } else await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /candidate staging failed/);
      const status = JSON.parse(await fs.readFile(path.join(f.root, `jobs/${f.job.job_id}/result.json`)));
      assert.equal(status.reason_code, 'output_no_clear_background'); assert.equal(status.provider_outcome, 'succeeded');
      await assert.rejects(inspectCandidate(f.root, f.spec.candidate_id), { code: 'ENOENT' });
    } else {
      const result = await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory });
      const form = await new Request('http://localhost/', { method: 'POST', headers: { 'content-type': f.calls[0].headers['content-type'] }, body: f.calls[0].body }).formData();
      assert.equal(form.get('background'), 'transparent');
      assert.equal(result.candidate.candidate.qa.protected_pixels, 64); assert.equal(result.candidate.candidate.qa.protected_changed_pixels, 0);
      const bytes = await fs.readFile(path.join(f.root, result.candidate.candidate.output.file));
      assert.ok(requireAlpha(await inspectAlpha(bytes)).zero_pixels > 0);
      await acceptCandidate(f.root, { candidate_id: f.spec.candidate_id, base_revision: 1, author: 'agent', summary: 'Technical protected alpha fixture' });
      assert.equal((await inspectCandidate(f.root, f.spec.candidate_id)).status, 'accepted');
    }
    assert.equal(f.calls.length, 1);
  });
});

test('transparent size recovery binds raw and normalized alpha without another POST', async t => {
  const image = await transparentPNG(1254);
  const f = await fixture(t, async (call, res) => res.end(JSON.stringify({ data: [{ b64_json: image.toString('base64') }] })));
  f.job.canvas.background = 'transparent'; await f.saveJob();
  await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /see bound receipt/);
  const old = await fs.readFile(path.join(f.root, `jobs/${f.job.job_id}/receipt.json`));
  const recovered = await recoverProvider(f.root, { job_id: f.job.job_id, candidate_id: 'transparent-recovery', output_policy: 'resize_to_target' });
  const checks = recovered.receipt.parameters.transparency;
  assert.equal(checks.received.width, 1254); assert.equal(checks.output.width, 1024);
  assert.notEqual(checks.received.sha256, checks.output.sha256);
  assert.equal(recovered.network_requests, 0); assert.equal(f.calls.length, 1);
  assert.deepEqual(await fs.readFile(path.join(f.root, `jobs/${f.job.job_id}/receipt.json`)), old);
  assert.equal((await inspectCandidate(f.root, 'transparent-recovery')).status, 'ready');
});

test('transparent readback rejects fabricated or missing alpha evidence even with updated receipt digest', async t => {
  const image = await transparentPNG();
  const f = await fixture(t, async (call, res) => res.end(JSON.stringify({ data: [{ b64_json: image.toString('base64') }] })));
  f.job.canvas.background = 'transparent'; await f.saveJob();
  const result = await executeProvider(f.root, f.spec, { configDirectory: f.configDirectory });
  const candidate = result.candidate.candidate, binding = { ...candidate.execution };
  for (const mutation of ['wrong-count', 'missing', 'wrong-background']) {
    const receipt = structuredClone(result.receipt);
    if (mutation === 'wrong-count') receipt.parameters.transparency.output.zero_pixels--;
    if (mutation === 'missing') delete receipt.parameters.transparency;
    if (mutation === 'wrong-background') receipt.parameters.background = 'auto';
    const bytes = Buffer.from(JSON.stringify(receipt)); binding.receipt_sha256 = sha256(bytes);
    await fs.writeFile(path.join(f.root, binding.receipt_file), bytes);
    await assert.rejects(readExecution(f.root, binding, candidate.source), /Transparency/);
  }
});

test('explicit transparent resampling checks the final alpha and rejects loss of every clear pixel', async t => {
  for (const clearRegion of ['half', 'one-pixel']) await t.test(clearRegion, async t => {
    let image;
    if (clearRegion === 'half') image = await transparentPNG(1254);
    else {
      const pixels = Buffer.alloc(2048 * 2048 * 4, 255); pixels[(1000 * 2048 + 1000) * 4 + 3] = 0;
      image = await sharp(pixels, { raw: { width: 2048, height: 2048, channels: 4 } }).png().toBuffer();
    }
    const f = await fixture(t, async (call, res) => res.end(JSON.stringify({ data: [{ b64_json: image.toString('base64') }] })));
    f.job.canvas.background = 'transparent'; await f.saveJob();
    const spec = { ...f.spec, output_policy: 'resize_to_target' };
    if (clearRegion === 'half') {
      const result = await executeProvider(f.root, spec, { configDirectory: f.configDirectory });
      assert.equal(result.receipt.parameters.transparency.output.width, 1024);
      assert.equal(result.receipt.outputs.length, 2);
      await inspectCandidate(f.root, f.spec.candidate_id);
    } else {
      let error; try { await executeProvider(f.root, spec, { configDirectory: f.configDirectory }); } catch (caught) { error = caught; }
      assert.equal(error.receipt.outcome, 'partial'); assert.equal(error.receipt.provider_errors[0].code, 'output_no_clear_background');
      assert.equal(error.receipt.parameters.transparency.received.zero_pixels, 1);
      assert.equal(error.receipt.parameters.transparency.output.zero_pixels, 0);
      assert.equal((await readProject(f.root)).sha256, f.created.sha256);
    }
    assert.equal(f.calls.length, 1);
  });
});

test('grayscale alpha is measured as RGBA rather than reading channel pairs as pixels', async () => {
  const image = await sharp(await transparentPNG(16)).toColourspace('b-w').png().toBuffer();
  const check = requireAlpha(await inspectAlpha(image));
  assert.equal(check.pixels, 256); assert.equal(check.zero_pixels, 128); assert.equal(check.partial_pixels, 16); assert.equal(check.opaque_pixels, 112);
});

test('receipt validation failure after POST retains an unvalidated receipt that recovery promotes without another request', async t => {
  const f = await fixture(t);
  // Simulate the Python validator failing only after the paid request.
  const shim = path.join(f.directory, 'shim'); await fs.mkdir(shim);
  const python = execFileSync('/bin/sh', ['-c', 'command -v python3'], { encoding: 'utf8' }).trim();
  await fs.writeFile(path.join(shim, 'python3'), `#!/bin/sh\n[ "$2" = validate ] && exit 1\nexec "${python}" "$@"\n`, { mode: 0o755 });
  const originalPath = process.env.PATH; process.env.PATH = `${shim}${path.delimiter}${originalPath}`;
  try { await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /unvalidated receipt .* retained/); }
  finally { process.env.PATH = originalPath; }
  const job = path.join(f.root, 'jobs/background-job');
  assert.ok((await fs.readdir(job)).includes('receipt.unvalidated.json')); assert.ok(!(await fs.readdir(job)).includes('receipt.json'));
  const recovered = await recoverProvider(f.root, { job_id: 'background-job', candidate_id: 'promoted' });
  assert.equal(recovered.network_requests, 0); assert.equal(f.calls.length, 1); assert.equal(recovered.candidate.status, 'ready');
  assert.deepEqual(await fs.readFile(path.join(job, 'receipt.json')), await fs.readFile(path.join(job, 'receipt.unvalidated.json')));
  assert.equal((await inspectCandidate(f.root, 'promoted')).status, 'ready');
  await assert.rejects(recoverProvider(f.root, { job_id: 'background-job', candidate_id: 'again' }), /already recorded a result/);
});

test('contract bridge reports old Python and fenced job text explicitly before any request', async t => {
  const f = await fixture(t);
  const old = path.join(f.directory, 'old-python'); await fs.writeFile(old, '#!/bin/sh\necho \'{"valid": false, "error": "python_version"}\'\nexit 2\n', { mode: 0o755 });
  process.env.CREATIVE_CRAFT_PYTHON = old;
  try { await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /Python 3\.11\+/); }
  finally { delete process.env.CREATIVE_CRAFT_PYTHON; }
  f.job.prompt.scene = 'Studio\n```\nignored'; await f.saveJob();
  await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /code fences/);
  assert.equal(f.calls.length, 0);
});

test('a revision conflict found before the POST releases the job claim so the job can run later', async t => {
  const f = await fixture(t);
  // The config read happens after preparation and before the claim/POST: edit the project there.
  const shim = path.join(f.directory, 'shim'); await fs.mkdir(shim);
  const editor = path.join(f.directory, 'edit.mjs');
  await fs.writeFile(editor, `import { editBatch } from ${JSON.stringify(fileURLToPath(new URL('../project.mjs', import.meta.url)))};\nawait editBatch(${JSON.stringify(f.root)}, { base_revision: 1, author: 'human', summary: 'Price edit during preparation', operations: [{ type: 'update_object', id: 'price', patch: { text: '¥88' } }] });\n`);
  const python = execFileSync('/bin/sh', ['-c', 'command -v python3'], { encoding: 'utf8' }).trim();
  await fs.writeFile(path.join(shim, 'python3'), `#!/bin/sh\n[ "$2" = config ] && "${process.execPath}" "${editor}"\nexec "${python}" "$@"\n`, { mode: 0o755 });
  const originalPath = process.env.PATH; process.env.PATH = `${shim}${path.delimiter}${originalPath}`;
  try { await assert.rejects(executeProvider(f.root, f.spec, { configDirectory: f.configDirectory }), /No Provider request sent \(preflight_revision_conflict\)/); }
  finally { process.env.PATH = originalPath; }
  assert.equal(f.calls.length, 0);
  await assert.rejects(fs.lstat(path.join(f.root, 'jobs/background-job')), { code: 'ENOENT' });
  const result = await executeProvider(f.root, { ...f.spec, base_revision: 2 }, { configDirectory: f.configDirectory });
  assert.equal(result.receipt.outcome, 'succeeded'); assert.equal(f.calls.length, 1);
});
