// Fetch the pinned caption font named in fonts/manifest.json and verify its digest.
// The binary is not committed; caption-font.mjs refuses to render without it.
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fonts');
const manifest = JSON.parse(await fs.readFile(path.join(dir, 'manifest.json'), 'utf8'));
const target = path.join(dir, manifest.file);
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

try {
  if (sha256(await fs.readFile(target)) === manifest.sha256) {
    console.log(`${manifest.file} already present and verified`);
    process.exit(0);
  }
  throw new Error(`${manifest.file} exists but its SHA-256 does not match; remove it and retry`);
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}

const response = await fetch(manifest.source);
if (!response.ok) throw new Error(`Font download failed: HTTP ${response.status}`);
const bytes = Buffer.from(await response.arrayBuffer());
if (bytes.length !== manifest.bytes || sha256(bytes) !== manifest.sha256) {
  throw new Error('Downloaded font does not match fonts/manifest.json; refusing to save it');
}
const partial = `${target}.partial`;
await fs.writeFile(partial, bytes, { flag: 'wx' });
await fs.rename(partial, target);
console.log(`Fetched and verified ${manifest.file}`);
