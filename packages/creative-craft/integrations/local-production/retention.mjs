import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

export const retentionRoot = fileURLToPath(new URL('../../dist/local-production', import.meta.url));
const fixture = 'synthetic technical scenarios; not real creative evaluation';
const runName = /^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z$/u;
const reports = new Set(['.json', '.html', '.md', '.txt', '.log', '.js', '.vtt']);
const payloads = new Set(['.ttf', '.otf', '.media', '.mp4', '.m4a', '.wav', '.png', '.jpg', '.jpeg', '.webp', '.svg']);
const exec = promisify(execFile);
const identity = s => `${s.dev}:${s.ino}:${s.size}:${s.mtimeNs}`;
async function directory(root) {
  const s = await fs.lstat(root);
  if (!s.isDirectory() || s.isSymbolicLink() || await fs.realpath(root) !== root) throw new Error('Unsafe retention directory');
}
export async function withRetentionLock(root, action) {
  await fs.mkdir(root, { recursive: true }); await directory(root);
  const lock = path.join(root, '.retention.lock');
  await fs.mkdir(lock); // Never steal a lock, including one left by an interrupted process.
  try { await fs.writeFile(path.join(lock, 'owner.json'), JSON.stringify({ pid: process.pid })); return await action(); }
  finally { await fs.unlink(path.join(lock, 'owner.json')); await fs.rmdir(lock); }
}
async function scan(root) {
  await directory(root);
  const files = [];
  async function visit(dir) {
    for (const name of await fs.readdir(dir)) {
      if (name === '.keep') throw new Error('Pinned run');
      const p = path.join(dir, name), s = await fs.lstat(p, { bigint: true });
      if (s.isSymbolicLink()) throw new Error('Symlink in run');
      if (s.isDirectory()) { await directory(p); await visit(p); }
      else if (s.isFile()) {
        const ext = path.extname(name).toLowerCase();
        const keep = reports.has(ext) && s.size <= 1048576n;
        if (!keep && !payloads.has(ext)) throw new Error('Unknown or oversized report');
        files.push({ path: path.relative(root, p), bytes: Number(s.size), identity: identity(s), keep });
      } else throw new Error('Unknown filesystem entry');
    }
  }
  await visit(root); return files.sort((a, b) => a.path.localeCompare(b.path));
}
async function successful(root) {
  await directory(root);
  const p = path.join(root, 'summary.json'), s = await fs.lstat(p);
  if (!s.isFile() || s.isSymbolicLink() || s.size > 1048576) return false;
  const summary = JSON.parse(await fs.readFile(p, 'utf8'));
  return summary.status === 'passed' && summary.fixture === fixture;
}
export async function planRetention(root = retentionRoot) {
  try { await directory(root); } catch (e) { if (e.code === 'ENOENT') return { root, retained: [], skipped: [], candidates: [], bytes: 0 }; throw e; }
  const passed = [], skipped = [];
  for (const name of (await fs.readdir(root)).sort()) {
    if (!runName.test(name)) continue;
    try { if (await successful(path.join(root, name))) passed.push(name); else skipped.push(name); }
    catch { skipped.push(name); }
  }
  const retained = passed.slice(-2), candidates = [];
  for (const name of passed.slice(0, -2)) {
    try {
      const files = await scan(path.join(root, name));
      if (files.some(f => !f.keep)) candidates.push({ name, files });
    } catch { skipped.push(name); }
  }
  return { root, retained, skipped, candidates, bytes: candidates.reduce((n, c) => n + c.files.filter(f => !f.keep).reduce((s, f) => s + f.bytes, 0), 0) };
}
export async function occupied(root) {
  if (!['darwin', 'linux'].includes(process.platform)) return true;
  try { await exec(process.platform === 'darwin' ? '/usr/sbin/lsof' : 'lsof', ['-nP', '+D', root], { timeout: 10000, maxBuffer: 1048576 }); return true; }
  catch (e) { return !(e.code === 1 && e.stdout === '' && e.stderr === ''); }
}
// Caller holds the same lock as the default smoke run. Non-cooperating writers
// remain outside this trusted local-owner workflow; identity drift fails closed.
export async function applyRetention(plan, inUse = occupied) {
  const current = await planRetention(plan.root);
  if (JSON.stringify(current) !== JSON.stringify(plan)) throw new Error('Retention plan changed');
  const result = { removedFiles: 0, removedBytes: 0, deferred: [] };
  for (const candidate of plan.candidates) {
    const root = path.join(plan.root, candidate.name);
    if (await inUse(root)) { result.deferred.push(candidate.name); continue; }
    if (!await successful(root) || JSON.stringify(await scan(root)) !== JSON.stringify(candidate.files)) throw new Error('Run changed');
    for (const f of candidate.files.filter(f => !f.keep)) {
      const p = path.join(root, f.path);
      await directory(path.dirname(p));
      if (identity(await fs.lstat(p, { bigint: true })) !== f.identity) throw new Error('Payload changed');
      await fs.unlink(p); result.removedFiles++; result.removedBytes += f.bytes;
    }
  }
  return result;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.length && !(args.length === 1 && args[0] === '--apply')) throw new Error('Usage: node retention.mjs [--apply]');
  const result = args.length ? await withRetentionLock(retentionRoot, async () => applyRetention(await planRetention())) : await planRetention();
  console.log(JSON.stringify(result, null, 2));
}
