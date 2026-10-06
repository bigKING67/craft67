import * as fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import { ALPHA_ERRORS, inspectAlpha, requireAlpha, verifyAlpha } from './provider-alpha.mjs';
import { sha256, writeOnce } from '../local-production/content-store.mjs';
import { id, record, number, LIMITS } from './document.mjs';
import { readProject } from './project.mjs';
import { readBytes, readAsset, importRaster } from './raster.mjs';
import { ensureDirectory, assertCandidateSlot, candidateBytes } from './candidate-store.mjs';
import { maskBytes, validateContext } from './composite.mjs';
import { stageCandidate } from './candidates.mjs';
import { codexCredentials, contract } from './provider-config.mjs';
import { IMAGE_MODELS, PROFILE_MODELS } from './provider-store.mjs';
import { normalizeImage } from './provider-normalize.mjs';

const RESPONSE_LIMIT = 30_000_000;
const MASK_KEYS = ['generation_mask', 'protection_mask', 'blend_mask'];
async function responseJSON(response) {
  if (Number(response.headers.get('content-length')) > RESPONSE_LIMIT) throw new Error('response_size_limit');
  const chunks = []; let length = 0;
  for await (const chunk of response.body) {
    length += chunk.length;
    if (length > RESPONSE_LIMIT) { await response.body.cancel().catch(() => {}); throw new Error('response_size_limit'); }
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

function numericUsage(value, depth = 0) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || depth > 2) return null;
  const result = {};
  for (const [key, item] of Object.entries(value)) {
    if (!['input_tokens', 'output_tokens', 'total_tokens', 'input_tokens_details', 'output_tokens_details', 'text_tokens', 'image_tokens', 'cached_tokens'].includes(key)) continue;
    if (Number.isSafeInteger(item) && item >= 0) result[key] = item;
    else if (item && typeof item === 'object') { const nested = numericUsage(item, depth + 1); if (nested) result[key] = nested; }
  }
  return Object.keys(result).length ? result : null;
}

export async function checkProvider({ configDirectory, signal } = {}) {
  const config = await codexCredentials(configDirectory);
  const timeout = AbortSignal.timeout(20_000);
  let response;
  try { response = await fetch(`${config.baseUrl}/models`, { headers: { Authorization: `Bearer ${config.key}` }, redirect: 'error', signal: signal ? AbortSignal.any([signal, timeout]) : timeout }); }
  catch { throw new Error('Provider model listing failed'); }
  if (!response.ok) throw new Error(`Provider model listing HTTP ${response.status}`);
  const data = await responseJSON(response);
  return { provider: config.provider, configured_wire_api: config.wireApi, adapter_endpoint: 'Image API',
    models: IMAGE_MODELS.map(model => ({ model, advertised: data.data?.some(row => row.id === model) === true })),
    credential_source: 'Codex config.toml + auth.json', generation_verified: false };
}

async function prepare(root, spec) {
  record(spec, ['job', 'candidate_id', 'base_revision', 'target_id', 'references', 'edit', 'output_policy'], 'Provider input');
  if (spec.output_policy !== undefined && !['strict', 'resize_to_target'].includes(spec.output_policy)) throw new Error('Unsupported output policy');
  id(spec.candidate_id, 'candidate id'); id(spec.target_id, 'target id');
  const jobBytes = await readBytes(spec.job, 1_000_000), job = JSON.parse(jobBytes);
  id(job.job_id, 'job id');
  const compiled = await contract('compile', job);
  const model = PROFILE_MODELS.get(job.provider_profile);
  if (!model || job.schema_version !== 'creative-craft.image-job.v2' || job.execution_surface !== 'openai.image_api' ||
      job.execution_mode !== 'single_turn' || job.declared_status !== 'ready' || job.canvas.format !== 'png' || job.canvas.variants !== 1) throw new Error('Adapter requires a ready single-turn GPT Image 2.5 job with one PNG output');
  if (job.rights.status === 'REJECTED') throw new Error('Rejected asset rights');
  const project = await readProject(root);
  if (project.document.revision !== spec.base_revision) throw new Error('Provider base revision conflict');
  await assertCandidateSlot(root, spec.candidate_id);
  const object = project.document.objects.find(object => object.id === spec.target_id);
  if (!object || object.kind !== 'image' || object.locked) throw new Error('Provider target must be an unlocked image object');
  const asset = project.document.assets.find(asset => asset.id === object.asset_id);
  const size = `${asset.width}x${asset.height}`;
  if (job.canvas.size !== size) throw new Error('Job output size must explicitly match target raster');
  if (!Array.isArray(spec.references) || spec.references.length > 3 || spec.references.length !== job.asset_refs.length) throw new Error('Reference inputs must match job asset refs (maximum 3)');
  if (new Set(spec.references.map(ref => ref.asset_id)).size !== spec.references.length) throw new Error('Duplicate reference IDs');
  const refs = [];
  for (let index = 0; index < spec.references.length; index++) {
    const ref = spec.references[index]; record(ref, ['asset_id', 'source'], 'Provider reference'); id(ref.asset_id, 'reference id');
    if (ref.asset_id !== job.asset_refs[index]) throw new Error('Reference order differs from job');
    const image = await importRaster({ id: ref.asset_id, source: ref.source });
    refs.push({ id: ref.asset_id, bytes: image.rendered, sha256: image.asset.render_sha256 });
  }
  if (job.task_type === 'generate' && (refs.length || spec.edit !== undefined)) throw new Error('Generation requires no image refs or masks; use edit for referenced creation');
  if (job.task_type === 'edit') {
    if (!refs.length || refs[0].id !== asset.id || refs[0].sha256 !== asset.render_sha256) throw new Error('First edit reference must be the current target raster');
  }
  let masks, providerMask;
  if (spec.edit !== undefined) {
    if (job.task_type !== 'edit') throw new Error('Masks require edit mode');
    record(spec.edit, ['context', 'generation_mask', 'protection_mask', 'blend_mask'], 'Provider edit');
    validateContext(spec.edit.context, asset.width, asset.height);
    const c = spec.edit.context;
    if (c.x !== 0 || c.y !== 0 || c.width !== asset.width || c.height !== asset.height) throw new Error('This Adapter sends full-raster context; cropped context is unsupported');
    masks = {};
    for (const key of MASK_KEYS) masks[key] = await maskBytes(await readBytes(spec.edit[key], LIMITS.sourceBytes), asset.width, asset.height, { protection: key === 'protection_mask' });
    const alpha = Buffer.alloc(asset.width * asset.height * 4, 255); let allowed = 0;
    for (let pixel = 0; pixel < masks.generation_mask.data.length; pixel++) {
      const generation = masks.generation_mask.data[pixel], protection = masks.protection_mask.data[pixel], blend = masks.blend_mask.data[pixel];
      if (blend && !generation) throw new Error('Blend mask extends outside generation mask');
      if (blend && !protection) allowed++;
      // Local white means change; Provider alpha=0 means change.
      alpha[pixel * 4 + 3] = protection ? 255 : 255 - generation;
    }
    if (!allowed) throw new Error('No editable pixels after protection');
    providerMask = await sharp(alpha, { raw: { width: asset.width, height: asset.height, channels: 4 } }).png().toBuffer();
  }
  const parameters = { model, size, quality: job.canvas.quality, background: job.canvas.background, output_format: 'png', n: 1 };
  const request = { endpoint: job.task_type === 'edit' ? 'images/edits' : 'images/generations', parameters,
    output_policy: spec.output_policy ?? 'strict',
    prompt_sha256: sha256(compiled.prompt), references: refs.map(ref => ({ asset_id: ref.id, sha256: ref.sha256 })),
    provider_mask_sha256: providerMask ? sha256(providerMask) : null, project_id: project.document.project_id,
    base_revision: spec.base_revision, base_sha256: project.sha256, target_id: spec.target_id, candidate_id: spec.candidate_id };
  return { job, jobBytes, compiled, refs, masks, providerMask, parameters, request, project, asset };
}

export async function executeProvider(root, spec, { configDirectory, signal, timeoutMs = 180_000, dryRun = false } = {}) {
  number(timeoutMs, 'Provider timeout', 1, 300_000, true);
  const prepared = await prepare(root, spec);
  if (dryRun) return { status: 'dry_run', request: prepared.request, network_requests: 0 };
  signal?.throwIfAborted();
  const config = await codexCredentials(configDirectory);
  const jobs = path.join(root, 'jobs'); await ensureDirectory(jobs);
  const directory = path.join(jobs, prepared.job.job_id);
  await fs.mkdir(directory); // Exclusive durable claim: same job is never retried automatically.
  const save = (name, bytes) => writeOnce(path.join(directory, name), { bytes });
  const started = new Date().toISOString();
  await save('job.json', prepared.jobBytes);
  await save('prompt-pack.md', Buffer.from(prepared.compiled.pack));
  await save('request.json', candidateBytes(prepared.request));
  for (const ref of prepared.refs) await save(`reference-${ref.id}.png`, ref.bytes);
  if (prepared.providerMask) {
    await save('provider-mask.png', prepared.providerMask);
    for (const [key, mask] of Object.entries(prepared.masks)) await save(`${key}.png`, mask.bytes);
  }
  await save('started.json', candidateBytes({ started_at: started, status: 'prepared', client_post_limit: 1 }));
  let body;
  if (prepared.job.task_type === 'generate') body = JSON.stringify({ ...prepared.parameters, prompt: prepared.compiled.prompt });
  else {
    body = new FormData();
    for (const [key, value] of Object.entries({ ...prepared.parameters, prompt: prepared.compiled.prompt })) body.set(key, String(value));
    for (const ref of prepared.refs) body.append('image[]', new Blob([ref.bytes], { type: 'image/png' }), `${ref.id}.png`);
    if (prepared.providerMask) body.set('mask', new Blob([prepared.providerMask], { type: 'image/png' }), 'mask.png');
  }
  const timeout = AbortSignal.timeout(timeoutMs), combined = signal ? AbortSignal.any([signal, timeout]) : timeout;
  const parameters = { ...prepared.parameters, endpoint: prepared.request.endpoint, context: spec.edit?.context ?? null,
    client_post_attempts: 0, usage: null, billing: { state: 'UNVERIFIED', actual_cost: null, currency: null } };
  const receipt = { schema_version: 'creative-craft.execution-receipt.v1', receipt_id: `receipt-${prepared.job.job_id}`,
    job_id: prepared.job.job_id, job_sha256: sha256(prepared.jobBytes), provider_profile: prepared.job.provider_profile,
    execution_surface: prepared.job.execution_surface, model: prepared.parameters.model, snapshot: null,
    host: 'creative-craft.image-production', operator: 'agent', started_at: started, completed_at: started, outcome: 'failed',
    request_or_prompt_sha256: sha256(candidateBytes(prepared.request)), parameters, provider_execution_id: null, outputs: [], provider_errors: [], moderation_result: null,
    limitations: ['Requested alias does not verify the actual upstream snapshot.', 'Gateway billing and internal retries are unverified.', 'Provider masks guide generation; deterministic composition protects pixels.', 'This receipt is execution evidence, not visual approval.'] };
  let output;
  try {
    combined.throwIfAborted();
    // A price/human edit during preparation must not be charged against an old basis.
    if ((await readProject(root)).sha256 !== prepared.project.sha256) throw new Error('preflight_revision_conflict');
    parameters.client_post_attempts = 1;
    const response = await fetch(`${config.baseUrl}/${prepared.request.endpoint}`, {
      method: 'POST', headers: { Authorization: `Bearer ${config.key}`, ...(typeof body === 'string' ? { 'Content-Type': 'application/json' } : {}) },
      body, redirect: 'error', signal: combined,
    });
    parameters.http_status = response.status;
    if (!response.ok) { await response.body?.cancel(); throw new Error('http_error'); }
    const data = await responseJSON(response);
    parameters.usage = numericUsage(data.usage);
    const requestId = response.headers.get('x-request-id');
    if (requestId && /^[a-zA-Z0-9_-]{1,200}$/.test(requestId) && !requestId.includes(config.key)) receipt.provider_execution_id = requestId;
    const encoded = data.data?.length === 1 ? data.data[0].b64_json : undefined;
    if (typeof encoded !== 'string' || encoded.length % 4 || !/^[A-Za-z0-9+/]*={0,2}$/.test(encoded)) throw new Error('invalid_image_response');
    output = Buffer.from(encoded, 'base64');
    if (!output.length || output.length > LIMITS.sourceBytes || output.toString('base64') !== encoded) throw new Error('invalid_image_size');
    const { info } = await sharp(output, { limitInputPixels: LIMITS.pixels, failOn: 'warning' }).raw().toBuffer({ resolveWithObject: true });
    const meta = await sharp(output).metadata();
    parameters.returned_image = { format: meta.format, width: info.width, height: info.height, depth: meta.depth, pages: meta.pages ?? 1 };
    // Preserve a decodable rejected result for offline diagnosis; do not charge
    // for regenerating a result that has already reached this client.
    if (['png', 'jpeg', 'webp'].includes(meta.format) && (meta.pages ?? 1) === 1) {
      const received = `received-output.${meta.format}`;
      await save(received, output);
      receipt.outputs = [{ asset_id: `received-${prepared.job.job_id}`, path: `jobs/${prepared.job.job_id}/${received}`, sha256: sha256(output), mime_type: `image/${meta.format}`, bytes: output.length }];
    }
    if (prepared.job.canvas.background === 'transparent') {
      parameters.transparency = { received: await inspectAlpha(output) };
      requireAlpha(parameters.transparency.received);
    }
    const normalized = await normalizeImage(output, prepared.asset.width, prepared.asset.height, spec.output_policy);
    output = normalized.bytes; parameters.output_normalization = normalized.normalization;
    if (parameters.transparency) {
      parameters.transparency.output = normalized.normalization ? await inspectAlpha(output) : parameters.transparency.received;
      requireAlpha(parameters.transparency.output);
    }
    // The paid body is already local; a late timeout/cancel must not discard it.
    await save('output.png', output);
    const finalOutput = { asset_id: `generated-${prepared.job.job_id}`, path: `jobs/${prepared.job.job_id}/output.png`, sha256: sha256(output), mime_type: 'image/png', bytes: output.length };
    receipt.outputs = normalized.normalization ? [...receipt.outputs, finalOutput] : [finalOutput];
    receipt.outcome = 'succeeded';
  } catch (error) {
    receipt.outcome = receipt.outputs.length ? 'partial' : signal?.aborted ? 'cancelled' : 'failed';
    const codes = ['preflight_revision_conflict', 'http_error', 'response_size_limit', 'invalid_image_response', 'invalid_image_size', 'output_dimensions_or_format_mismatch', ...ALPHA_ERRORS];
    // A specific local verdict outranks an abort that fired while it was being computed.
    receipt.provider_errors = [{ code: codes.includes(error.message) ? error.message : timeout.aborted ? 'timeout' : signal?.aborted ? 'cancelled' : 'transport_or_response_error',
      upstream_execution_unknown: parameters.client_post_attempts === 1 && !receipt.outputs.length }];
  }
  if (parameters.client_post_attempts === 0) {
    // Nothing left this client: release the claim so the job can run after re-reading the project.
    await fs.rm(directory, { recursive: true, force: true });
    throw new Error(`No Provider request sent (${receipt.provider_errors[0].code}); job claim released`);
  }
  receipt.completed_at = new Date().toISOString();
  const receiptBytes = candidateBytes(receipt);
  try { await contract('validate', receipt); }
  catch {
    // Never lose evidence of a POST to the out-of-process validator; provider-recover promotes it later.
    await save('receipt.unvalidated.json', receiptBytes);
    const error = new Error('Provider receipt validation failed; unvalidated receipt and any received output retained. Use provider-recover; do not repeat generation.');
    error.receipt = receipt; error.output = directory; throw error;
  }
  await save('receipt.json', receiptBytes);
  if (receipt.outcome !== 'succeeded') {
    const error = new Error('Provider execution failed or cancelled; see bound receipt. No automatic retry.'); error.receipt = receipt; error.output = directory; throw error;
  }
  const candidate = await publishCandidate(root, directory, { candidateId: spec.candidate_id, request: prepared.request, receipt, receiptBytes,
    receiptFile: 'receipt.json', job: prepared.job, jobBytes: prepared.jobBytes });
  return { status: 'candidate', job: directory, receipt, candidate };
}

// Provider success and candidate publication are separate outcomes. Staging is
// local and is not cancelled: a paid output should not end as candidate_failed.
async function publishCandidate(root, directory, { candidateId, request, receipt, receiptBytes, receiptFile, job, jobBytes, recovered = false }) {
  const execution = { job_id: job.job_id, job_sha256: sha256(jobBytes), receipt_file: `jobs/${job.job_id}/${receiptFile}`, receipt_sha256: sha256(receiptBytes) };
  const stage = { id: candidateId, base_revision: request.base_revision, target_id: request.target_id, source: path.join(directory, 'output.png'),
    mode: request.provider_mask_sha256 ? 'masked' : 'replace', summary: job.intended_use.slice(0, 500), execution };
  if (request.provider_mask_sha256) stage.edit = { context: receipt.parameters.context, ...Object.fromEntries(MASK_KEYS.map(key => [key, path.join(directory, `${key}.png`)])) };
  const flag = recovered ? { recovered: true } : {};
  const result = value => writeOnce(path.join(directory, 'result.json'), { bytes: candidateBytes(value) });
  try {
    const candidate = await stageCandidate(root, stage);
    await result({ status: 'candidate', ...flag, candidate_id: candidateId, candidate_sha256: candidate.sha256, candidate_status: candidate.status });
    return candidate;
  } catch (cause) {
    await result({ status: 'candidate_failed', ...flag, provider_outcome: 'succeeded',
      reason_code: ALPHA_ERRORS.includes(cause.message) ? cause.message : 'candidate_validation_failed' });
    const error = new Error(`Provider ${recovered ? 'output recovered' : 'succeeded'}; candidate staging failed. Output retained; do not repeat generation.`);
    error.receipt = receipt; error.output = directory; throw error;
  }
}

// Promote a receipt kept only because validation was unavailable after the POST.
async function boundReceipt(directory) {
  const file = path.join(directory, 'receipt.json');
  try { return await readBytes(file, 1_000_000); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const bytes = await readBytes(path.join(directory, 'receipt.unvalidated.json'), 1_000_000);
  await contract('validate', JSON.parse(bytes));
  await writeOnce(file, { bytes });
  return bytes;
}

export async function recoverProvider(root, input) {
  record(input, ['job_id', 'candidate_id', 'output_policy'], 'Provider recovery');
  id(input.job_id, 'job id'); id(input.candidate_id, 'candidate id');
  await assertCandidateSlot(root, input.candidate_id);
  const directory = path.join(root, 'jobs', input.job_id);
  const oldBytes = await boundReceipt(directory), old = JSON.parse(oldBytes);
  await contract('validate', old);
  const jobBytes = await readBytes(path.join(directory, 'job.json'), 1_000_000), job = JSON.parse(jobBytes);
  await contract('compile', job);
  const requestBytes = await readBytes(path.join(directory, 'request.json'), 1_000_000), request = JSON.parse(requestBytes);
  if (old.job_sha256 !== sha256(jobBytes) || old.job_id !== input.job_id || job.job_id !== input.job_id ||
      old.request_or_prompt_sha256 !== sha256(requestBytes) || !IMAGE_MODELS.includes(old.model) || old.model !== request.parameters.model ||
      old.provider_profile !== job.provider_profile || old.execution_surface !== job.execution_surface) throw new Error('Recovery receipt binding mismatch');
  if (old.outcome === 'succeeded') {
    // A complete output whose receipt was only just promoted (or whose publication was interrupted).
    try { await fs.lstat(path.join(directory, 'result.json')); throw new Error('Provider job already recorded a result'); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    const candidate = await publishCandidate(root, directory, { candidateId: input.candidate_id, request, receipt: old, receiptBytes: oldBytes,
      receiptFile: 'receipt.json', job, jobBytes, recovered: true });
    return { status: 'recovered_candidate', network_requests: 0, receipt: old, candidate };
  }
  if (input.output_policy !== 'resize_to_target') throw new Error('Recovery requires explicit resize_to_target policy');
  if (old.outcome !== 'partial' || old.outputs.length !== 1 || old.provider_errors[0]?.code !== 'output_dimensions_or_format_mismatch') throw new Error('Recovery requires a bound partial size-mismatch receipt');
  const received = old.outputs[0];
  if (received.path !== `jobs/${input.job_id}/received-output.png` || received.mime_type !== 'image/png') throw new Error('Recovery supports retained PNG only');
  const bytes = await readBytes(path.join(root, received.path), LIMITS.sourceBytes);
  if (sha256(bytes) !== received.sha256 || bytes.length !== received.bytes) throw new Error('Retained output digest mismatch');
  if (job.canvas.background === 'transparent') {
    if (old.parameters.background !== 'transparent' || request.parameters.background !== 'transparent') throw new Error('Transparency request binding mismatch');
    await verifyAlpha(bytes, old.parameters.transparency?.received);
  }
  const project = await readProject(root, { revision: request.base_revision });
  if (project.sha256 !== request.base_sha256 || project.document.project_id !== request.project_id) throw new Error('Recovery project basis mismatch');
  const object = project.document.objects.find(o => o.id === request.target_id), asset = project.document.assets.find(a => a.id === object?.asset_id);
  if (!asset || object.locked) throw new Error('Invalid recovery target');
  const normalized = await normalizeImage(bytes, asset.width, asset.height, input.output_policy);
  if (!normalized.normalization) throw new Error('Recovery requires actual dimension normalization');
  const alpha = job.canvas.background === 'transparent' ? requireAlpha(await inspectAlpha(normalized.bytes)) : null;
  await fs.writeFile(path.join(directory, 'normalization-started.json'), candidateBytes({ source_receipt_sha256: sha256(oldBytes), policy: input.output_policy }), { flag: 'wx' });
  await writeOnce(path.join(directory, 'output.png'), { bytes: normalized.bytes }, { expected: sha256(normalized.bytes) });
  const receipt = structuredClone(old); receipt.receipt_id += '-normalized'; receipt.completed_at = new Date().toISOString(); receipt.outcome = 'succeeded'; receipt.provider_errors = [];
  receipt.parameters.output_normalization = normalized.normalization; receipt.parameters.source_receipt_sha256 = sha256(oldBytes); receipt.parameters.recovery_client_post_attempts = 0;
  if (alpha) receipt.parameters.transparency.output = alpha;
  receipt.outputs.push({ asset_id: `normalized-${job.job_id}`, path: `jobs/${job.job_id}/output.png`, sha256: sha256(normalized.bytes), mime_type: 'image/png', bytes: normalized.bytes.length });
  receipt.limitations.push('Original Provider size mismatch remains recorded; output was explicitly resampled offline, without another request.');
  await contract('validate', receipt);
  const receiptBytes = candidateBytes(receipt); await writeOnce(path.join(directory, 'normalized-receipt.json'), { bytes: receiptBytes });
  const candidate = await publishCandidate(root, directory, { candidateId: input.candidate_id, request, receipt, receiptBytes,
    receiptFile: 'normalized-receipt.json', job, jobBytes, recovered: true });
  return { status: 'recovered_candidate', network_requests: 0, receipt, candidate };
}
