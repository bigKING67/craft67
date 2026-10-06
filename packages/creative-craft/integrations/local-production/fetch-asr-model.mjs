// Fetch the pinned whisper.cpp model named in ASR_MODEL (asr.mjs) into
// $CREATIVE_WHISPER_MODEL_DIR (default ~/.cache/whisper-cpp) and verify its digest.
// The model is never committed; asr.mjs refuses to transcribe with an unverified model.
import { createHash } from 'node:crypto';
import { createWriteStream } from 'node:fs';
import * as fs from 'node:fs/promises';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { ASR_MODEL, defaultModelPath, modelDir, verifyModel } from './asr.mjs';

const target = defaultModelPath();
try {
  await verifyModel(target);
  console.log(`${ASR_MODEL.file} already present and verified in ${modelDir()}`);
  process.exit(0);
} catch (error) {
  if (error.code !== 'ENOENT') throw new Error(`${error.message}; remove ${target} and retry`);
}

await fs.mkdir(modelDir(), { recursive: true });
const partial = `${target}.partial`;
await fs.rm(partial, { force: true }); // leftover from an interrupted download
const response = await fetch(ASR_MODEL.source);
if (!response.ok) throw new Error(`Model download failed: HTTP ${response.status}`);
const hash = createHash('sha256');
let bytes = 0;
const body = Readable.fromWeb(response.body);
body.on('data', chunk => { hash.update(chunk); bytes += chunk.length; });
await pipeline(body, createWriteStream(partial, { flags: 'wx' }));
const actual = hash.digest('hex');
if (bytes !== ASR_MODEL.bytes || actual !== ASR_MODEL.sha256) {
  await fs.rm(partial, { force: true });
  throw new Error(`Downloaded model does not match ASR_MODEL (${bytes} bytes, ${actual}); refusing to save it`);
}
await fs.rename(partial, target);
console.log(`Fetched and verified ${ASR_MODEL.file} into ${modelDir()}`);
