// Explicit, bounded live acceptance for the existing Adapter; never part of CI.
import * as fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import assert from 'node:assert/strict';
import sharp from 'sharp';
import { demoInput } from './fixtures.mjs';
import { createProject, readProject, encode } from './project.mjs';
import { executeProvider, checkProvider } from './provider.mjs';
import { compareCandidate } from './candidates.mjs';
import { renderProject } from './render.mjs';

const [command, first, second, ...extra] = process.argv.slice(2);
const repository = fileURLToPath(new URL('../../', import.meta.url));
const save = (directory, name, value) => fs.writeFile(path.join(directory, name), encode(value), { flag: 'wx' });
const invoked = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked && command === 'prepare' && first && second && !extra.length) {
  const output = path.join(repository, 'dist', `image-p1c-eval-${new Date().toISOString().slice(0,10)}-${randomUUID().slice(0,8)}`);
  await fs.mkdir(output);
  const background = await fs.readFile(first), meta = await sharp(background).metadata();
  assert.equal(meta.format, 'png'); assert.equal(meta.width, 1024); assert.equal(meta.height, 1024);
  const template = JSON.parse(await fs.readFile(second));
  const jobs = [];
  for (const kind of ['edit', 'comparison']) {
    const input = await demoInput(path.join(output, `${kind}-sources`));
    input.project_id = `provider-${kind}`; input.canvas.width = input.canvas.height = 1024;
    input.objects.find(o => o.id === 'price').text = '¥149';
    Object.assign(input.objects.find(o => o.id === 'background'), { width: 1024, height: 1024 });
    const source = path.join(output, `${kind}-background.png`);
    if (kind === 'edit') {
      const leaf = Buffer.from('<svg width="1024" height="1024"><ellipse cx="940" cy="860" rx="23" ry="12" fill="#6e8161" transform="rotate(-25 940 860)"/><ellipse cx="929" cy="844" rx="17" ry="8" fill="#94a889" transform="rotate(30 929 844)"/></svg>');
      await sharp(background).composite([{ input: leaf }]).png().toFile(source);
    } else await fs.writeFile(source, background);
    input.assets.find(a => a.id === 'background').source = source;
    const root = path.join(output, `${kind}-project`); await createProject(root, input);
    await renderProject(root, path.join(output, `${kind}-before`));
    const edit = { context: { x: 0, y: 0, width: 1024, height: 1024 } };
    if (kind === 'edit') {
      const generation = Buffer.alloc(1024**2), protection = Buffer.alloc(1024**2), blend = Buffer.alloc(1024**2);
      for (let y = 0; y < 1024; y++) for (let x = 0; x < 1024; x++) {
        const at = y*1024+x, distance = Math.hypot(x-940, y-858);
        if (distance < 65) generation[at] = 255;
        if (distance < 55) blend[at] = Math.round(255*Math.min(1,(55-distance)/10));
        if (input.objects.some(o => o.id !== 'background' && x >= o.x && x < o.x+o.width && y >= o.y && y < o.y+o.height)) protection[at] = 255;
      }
      for (const [name, data] of Object.entries({ generation_mask: generation, protection_mask: protection, blend_mask: blend })) {
        edit[name] = path.join(output, `${name}.png`);
        await sharp(data, { raw: { width: 1024, height: 1024, channels: 1 } }).toColourspace('b-w').png().toFile(edit[name]);
      }
    }
    for (const model of kind === 'edit' ? ['sunburst'] : ['sunburst','flare']) {
      const name = `${kind}-${model}`, job = structuredClone(template);
      Object.assign(job, { job_id: name, provider_profile: `openai.gpt-image-2.5-${model}.2026-09-08` });
      job.canvas.quality = 'medium';
      if (kind === 'edit') {
        job.task_type = 'edit'; job.asset_refs = ['background'];
        job.intended_use = 'Remove a deliberate small green leaf from the lower-right background for bounded API-edit acceptance';
        job.prompt.subject = 'The existing photographic studio background';
        job.prompt.references = [{ asset_id: 'background', role: 'Current background to edit', preserve: ['Lighting','Composition','Texture outside the leaf'] }];
        job.prompt.change = ['Remove only the small green leaf around x=940, y=858; reconstruct the tabletop seamlessly.'];
        job.prompt.preserve = ['Keep all other background content unchanged.','Keep lighting, arch and tabletop texture.'];
      }
      const jobFile = path.join(output, `${name}-job.json`); await save(output, `${name}-job.json`, job);
      const spec = { job: jobFile, candidate_id: name, base_revision: 1, target_id: 'background',
        references: kind === 'edit' ? [{ asset_id: 'background', source }] : [], output_policy: 'resize_to_target' };
      if (kind === 'edit') spec.edit = edit;
      await save(output, `${name}-input.json`, spec);
      const dry = await executeProvider(root, spec, { dryRun: true }); await save(output, `${name}-dry-run.json`, dry);
      jobs.push({ name, root, input: `${name}-input.json` });
    }
  }
  const a = JSON.parse(await fs.readFile(path.join(output,'comparison-sunburst-dry-run.json')));
  const b = JSON.parse(await fs.readFile(path.join(output,'comparison-flare-dry-run.json')));
  assert.equal(a.request.prompt_sha256, b.request.prompt_sha256);
  await save(output, 'plan.json', { client_post_limit: 3, quality: 'medium', size: '1024x1024', single_sample_per_model: true, jobs });
  console.log(JSON.stringify({ status: 'prepared', output, network_requests: 0, client_post_limit: 3 }));
} else if (invoked && command === 'run' && first && second === '--live' && !extra.length) {
  await runAcceptance(first);
} else if (invoked) throw new Error('Usage: provider-acceptance.mjs prepare <cached-background.png> <generation-job.json> | run <prepared-directory> --live (at most three client POSTs; no retries)');

export async function runAcceptance(directory, { configDirectory = path.join(os.homedir(), '.codex') } = {}) {
  const output = path.resolve(directory), plan = JSON.parse(await fs.readFile(path.join(output,'plan.json')));
  assert.equal(plan.jobs.length, 3); assert.equal(plan.client_post_limit, 3);
  await save(output, 'live-started.json', { client_post_limit: 3, started_at: new Date().toISOString() });
  const credentials = configDirectory;
  const configBefore = await fs.readFile(path.join(credentials,'config.toml')), authBefore = await fs.readFile(path.join(credentials,'auth.json'));
  const controller = new AbortController(), cancel = () => controller.abort();
  process.once('SIGINT',cancel); process.once('SIGTERM',cancel);
  const report = { status: 'PARTIAL', client_post_limit: 3, events: [], actual_cost: 'UNVERIFIED', real_product_quality: 'UNVERIFIED', owner_approval: 'UNVERIFIED' };
  try {
    await save(output,'provider-check.json',await checkProvider({ signal:controller.signal, configDirectory }));
    for (const item of plan.jobs) {
      controller.signal.throwIfAborted();
      const basis = (await readProject(item.root)).sha256;
      const spec = JSON.parse(await fs.readFile(path.join(output,item.input))), started = performance.now();
      console.log(JSON.stringify({ phase:'request', name:item.name, maximum_client_posts:3 }));
      let result;
      try {
        result = await executeProvider(item.root,spec,{ signal:controller.signal, configDirectory });
        await save(output,`${item.name}-result.json`,result);
        await compareCandidate(item.root,item.name,path.join(output,`${item.name}-compare`));
        report.events.push({ name:item.name, elapsed_ms:Math.round(performance.now()-started), outcome:'succeeded', provider_outcome:result.receipt.outcome,
          receipt:result.candidate.candidate.execution, parameters:result.receipt.parameters, qa:result.candidate.candidate.qa });
      } catch (error) {
        const receipt = error.receipt ?? result?.receipt;
        report.events.push({ name:item.name, elapsed_ms:Math.round(performance.now()-started), outcome:'failed', provider_outcome:receipt?.outcome??null,
          parameters:receipt?.parameters??null, provider_errors:receipt?.provider_errors??null,
          error:'Execution, candidate preparation or comparison failed; retained evidence must be inspected; no retry' });
      }
      assert.equal((await readProject(item.root)).sha256,basis);
      await save(output,`${item.name}-event.json`,report.events.at(-1));
      console.log(JSON.stringify({ phase:'result',...report.events.at(-1) }));
    }
    report.status = report.events.every(e => e.outcome === 'succeeded') ? 'CANDIDATES_READY_FOR_INSPECTION' : 'PARTIAL';
  } finally {
    process.removeListener('SIGINT',cancel); process.removeListener('SIGTERM',cancel);
    report.global_config_unchanged = (await fs.readFile(path.join(credentials,'config.toml'))).equals(configBefore);
    report.auth_unchanged = (await fs.readFile(path.join(credentials,'auth.json'))).equals(authBefore);
    await save(output,'live-report.json',report);
  }
  console.log(JSON.stringify({ status:report.status, output }));
  return report;
}
