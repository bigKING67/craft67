import * as fs from 'node:fs/promises';
import path from 'node:path';
import { sha256 } from '../local-production/content-store.mjs';
import { record, id, digest, LIMITS } from './document.mjs';
import { readBytes } from './raster.mjs';
import { normalizeImage } from './provider-normalize.mjs';
import { verifyAlpha } from './provider-alpha.mjs';

// Single source of truth: the module's provider profiles that enable this adapter.
const profiles = await Promise.all((await fs.readdir(new URL('./providers/', import.meta.url), { withFileTypes: true }))
  .filter(entry => entry.isFile() && entry.name.endsWith('.json'))
  .map(async entry => JSON.parse(await fs.readFile(new URL(`./providers/${entry.name}`, import.meta.url), 'utf8'))));
export const PROFILE_MODELS = new Map(profiles.filter(profile => profile.availability?.network_adapter_in_optional_module === true)
  .map(profile => [profile.profile_id, profile.model]).sort(([a], [b]) => a.localeCompare(b)));
export const IMAGE_MODELS = [...new Set(PROFILE_MODELS.values())];
export function validateExecution(binding) {
  record(binding, ['job_id', 'job_sha256', 'receipt_file', 'receipt_sha256'], 'execution binding');
  id(binding.job_id, 'job id'); digest(binding.job_sha256); digest(binding.receipt_sha256);
  if (![ `jobs/${binding.job_id}/receipt.json`, `jobs/${binding.job_id}/normalized-receipt.json` ].includes(binding.receipt_file)) throw new Error('Invalid execution receipt path');
}

export async function readExecution(root, binding, source) {
  validateExecution(binding);
  const jobBytes = await readBytes(path.join(root, 'jobs', binding.job_id, 'job.json'), 1_000_000);
  const receiptBytes = await readBytes(path.join(root, binding.receipt_file), 1_000_000);
  if (sha256(jobBytes) !== binding.job_sha256 || sha256(receiptBytes) !== binding.receipt_sha256) throw new Error('Execution binding digest mismatch');
  const job = JSON.parse(jobBytes), receipt = JSON.parse(receiptBytes);
  if (job.schema_version !== 'creative-craft.image-job.v2' || job.job_id !== binding.job_id || receipt.job_id !== job.job_id || receipt.job_sha256 !== binding.job_sha256 ||
      receipt.schema_version !== 'creative-craft.execution-receipt.v1' || receipt.outcome !== 'succeeded' ||
      receipt.provider_profile !== job.provider_profile || receipt.execution_surface !== job.execution_surface ||
      !IMAGE_MODELS.includes(receipt.model) || PROFILE_MODELS.get(job.provider_profile) !== receipt.model || ![1,2].includes(receipt.outputs?.length)) throw new Error('Execution receipt does not bind a successful image job');
  const output = receipt.outputs.find(output => output.path === `jobs/${job.job_id}/output.png`);
  if (!output) throw new Error('Missing final Provider output');
  if (output.path !== `jobs/${job.job_id}/output.png` || output.sha256 !== source.sha256 || output.mime_type !== 'image/png') throw new Error('Candidate source differs from Provider output');
  const bytes = await readBytes(path.join(root, output.path), LIMITS.renderBytes);
  if (bytes.length !== output.bytes || sha256(bytes) !== output.sha256) throw new Error('Provider output digest mismatch');
  const transparent = job.canvas.background === 'transparent';
  if (transparent) {
    if (receipt.parameters.background !== 'transparent') throw new Error('Transparency request binding mismatch');
    await verifyAlpha(bytes, receipt.parameters.transparency?.output);
    if (!receipt.parameters.output_normalization) await verifyAlpha(bytes, receipt.parameters.transparency?.received);
  }
  if (receipt.parameters.output_normalization) {
    const original = receipt.outputs.find(output => output.path === `jobs/${job.job_id}/received-output.png`);
    if (!original) throw new Error('Missing original normalization source');
    const raw = await readBytes(path.join(root, original.path), LIMITS.sourceBytes);
    const n = receipt.parameters.output_normalization;
    if (sha256(raw) !== original.sha256 || raw.length !== original.bytes || n.source_sha256 !== original.sha256 || n.output_sha256 !== output.sha256) throw new Error('Normalization source binding mismatch');
    if (transparent) await verifyAlpha(raw, receipt.parameters.transparency?.received);
    const recomputed = await normalizeImage(raw, source.width, source.height, 'resize_to_target');
    if (!recomputed.bytes.equals(bytes) || JSON.stringify(recomputed.normalization) !== JSON.stringify(n)) throw new Error('Normalization differs from recomputed result');
  }
  if (binding.receipt_file.endsWith('/normalized-receipt.json')) {
    const oldBytes = await readBytes(path.join(root, 'jobs', binding.job_id, 'receipt.json'), 1_000_000);
    if (sha256(oldBytes) !== receipt.parameters.source_receipt_sha256) throw new Error('Recovery source receipt digest mismatch');
  }
  return receipt;
}
