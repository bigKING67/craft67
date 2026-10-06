#!/usr/bin/env node
import * as fs from 'node:fs/promises';

// Modules load inside main() so dependency/font load failures still produce JSON errors.
let createProject, createPhotoProject, readProject, editBatch, regularPath, renderProject, copyVariants, cropPhoto, record,
  stageCandidate, listCandidates, inspectCandidate, acceptCandidate, discardCandidate, compareCandidate, unlockCandidate,
  checkProvider, executeProvider, recoverProvider;
async function load() {
  ({ createProject, createPhotoProject, readProject, editBatch, regularPath } = await import('./project.mjs'));
  ({ renderProject } = await import('./render.mjs'));
  ({ copyVariants } = await import('./copy-variants.mjs'));
  ({ cropPhoto } = await import('./photo-crop.mjs'));
  ({ record } = await import('./document.mjs'));
  ({ stageCandidate, listCandidates, inspectCandidate, acceptCandidate, discardCandidate, compareCandidate, unlockCandidate } = await import('./candidates.mjs'));
  ({ checkProvider, executeProvider, recoverProvider } = await import('./provider.mjs'));
}

async function input(file) {
  await regularPath(file);
  if ((await fs.stat(file)).size > 1_000_000) throw new Error('Input JSON byte limit exceeded');
  return JSON.parse(await fs.readFile(file, 'utf8'));
}

async function main() {
  await load();
  const [command, root, argument, flag, ...rest] = process.argv.slice(2);
  const historicalRender = ['render', 'preview'].includes(command) && flag === '--revision' && rest.length === 1;
  if (!root || (rest.length && !historicalRender)) throw new Error('Usage: cli.mjs create|create-photo|crop-photo|copy-variants|read|edit|preview|render|candidate-stage|candidate-list|candidate-read|candidate-accept|candidate-discard|candidate-unlock|candidate-compare|provider-check|provider-run|provider-recover <project> [input.json|output|id] [--dry-run]; render|preview also accept --revision <positive-integer>');
  let result;
  switch (command) {
    case 'crop-photo':
      if (!argument || (flag && flag !== '--dry-run')) throw new Error('crop-photo requires a new output directory, input JSON and optionally --dry-run');
      result = await cropPhoto(root, await input(argument), { dryRun: flag === '--dry-run' }); break;
    case 'copy-variants': {
      if (!argument || flag) throw new Error('copy-variants requires one input JSON');
      const controller = new AbortController();
      const cancel = () => controller.abort();
      process.once('SIGINT', cancel); process.once('SIGTERM', cancel);
      try { result = await copyVariants(root, await input(argument), { signal: controller.signal }); }
      finally { process.removeListener('SIGINT', cancel); process.removeListener('SIGTERM', cancel); }
      break;
    }
    case 'provider-recover':
      if (!argument || flag) throw new Error('provider-recover requires one input JSON');
      result = await recoverProvider(root, await input(argument)); break;
    case 'provider-check':
      if (argument || flag) throw new Error('provider-check accepts no extra arguments');
      result = await checkProvider(); break;
    case 'provider-run': {
      if (!argument || (flag && flag !== '--dry-run')) throw new Error('provider-run requires input JSON and optionally --dry-run');
      const controller = new AbortController();
      const cancel = () => controller.abort();
      process.once('SIGINT', cancel); process.once('SIGTERM', cancel);
      try { result = await executeProvider(root, await input(argument), { signal: controller.signal, dryRun: flag === '--dry-run' }); }
      finally { process.removeListener('SIGINT', cancel); process.removeListener('SIGTERM', cancel); }
      break;
    }
    case 'create-photo':
      if (!argument || (flag && flag !== '--dry-run')) throw new Error('create-photo requires a brief JSON file and optionally --dry-run');
      result = await createPhotoProject(root, await input(argument), { dryRun: flag === '--dry-run' }); break;
    case 'create':
      if (!argument || flag) throw new Error('create requires one input JSON file');
      result = await createProject(root, await input(argument)); break;
    case 'read': {
      if (flag) throw new Error('read accepts an optional numeric revision');
      if (argument !== undefined && !/^[1-9]\d*$/.test(argument)) throw new Error('Revision must be a positive decimal integer');
      const project = await readProject(root, { revision: argument === undefined ? undefined : Number(argument) });
      result = { root: project.root, document: project.document, sha256: project.sha256, latest_revision: project.latest_revision, candidate_decisions: project.candidate_decisions }; break;
    }
    case 'edit':
      if (!argument || (flag && flag !== '--dry-run')) throw new Error('edit requires input JSON and optionally --dry-run');
      result = await editBatch(root, await input(argument), { dryRun: flag === '--dry-run' }); break;
    case 'candidate-stage': case 'candidate-discard': case 'candidate-unlock': case 'candidate-accept': case 'candidate-compare': {
      if (!argument || (flag && (command !== 'candidate-accept' || flag !== '--dry-run'))) throw new Error(`${command} requires input JSON`);
      const spec = await input(argument);
      if (command === 'candidate-stage') result = await stageCandidate(root, spec);
      else if (command === 'candidate-discard') result = await discardCandidate(root, spec);
      else if (command === 'candidate-unlock') result = await unlockCandidate(root, spec);
      else if (command === 'candidate-accept') result = await acceptCandidate(root, spec, { dryRun: flag === '--dry-run' });
      else {
        record(spec, ['candidate_id', 'output'], 'compare input');
        result = await compareCandidate(root, spec.candidate_id, spec.output);
      }
      break;
    }
    case 'candidate-list':
      if (argument || flag) throw new Error('candidate-list accepts no extra arguments');
      result = await listCandidates(root); break;
    case 'candidate-read':
      if (!argument || flag) throw new Error('candidate-read requires one candidate id');
      result = await inspectCandidate(root, argument); break;
    case 'preview': case 'render': {
      if (!argument || (flag !== undefined && !historicalRender)) throw new Error(`${command} requires a new output directory and optionally --revision <positive-integer>`);
      const revision = historicalRender ? Number(rest[0]) : undefined;
      if (historicalRender && (!/^[1-9]\d*$/.test(rest[0]) || !Number.isSafeInteger(revision))) throw new Error('Revision must be a positive decimal integer');
      const controller = new AbortController();
      const cancel = () => controller.abort();
      process.once('SIGINT', cancel); process.once('SIGTERM', cancel);
      try { result = await renderProject(root, argument, { revision, previewMax: command === 'preview' ? 640 : 0, signal: controller.signal }); }
      finally { process.removeListener('SIGINT', cancel); process.removeListener('SIGTERM', cancel); }
      break;
    }
    default: throw new Error('Unknown image command');
  }
  console.log(JSON.stringify(result, null, 2));
}

main().catch(error => { console.error(JSON.stringify({ status: error.receipt?.status ?? 'failed', error: error.message, output: error.output })); process.exitCode = 1; });
