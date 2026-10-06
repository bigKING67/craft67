import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { readBytes, regularPath } from './raster.mjs';

const bridge = fileURLToPath(new URL('./provider-contracts.py', import.meta.url));

export async function contract(command, data, extra = []) {
  return new Promise((resolve, reject) => {
    // CREATIVE_CRAFT_PYTHON pins an explicit interpreter instead of PATH lookup.
    const child = spawn(process.env.CREATIVE_CRAFT_PYTHON || 'python3', [bridge, command, ...extra], { stdio: ['pipe', 'pipe', 'pipe'] });
    const chunks = []; let length = 0;
    const timer = setTimeout(() => child.kill('SIGKILL'), 10_000);
    child.stdout.on('data', chunk => { length += chunk.length; if (length > 2_000_000) child.kill('SIGKILL'); else chunks.push(chunk); });
    child.stderr.resume(); // Never expose subprocess diagnostics from auth parsing.
    child.on('error', () => { clearTimeout(timer); reject(new Error('Python 3.11+ contract bridge unavailable')); });
    child.on('close', code => {
      clearTimeout(timer);
      let result;
      try { result = JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch {}
      if (result?.error === 'python_version') return reject(new Error('Python 3.11+ contract bridge unavailable'));
      if (code === 0 && result && result.valid !== false) return resolve(result);
      // Job/receipt validation errors describe declared content; config errors may not be echoed.
      const details = command !== 'config' && Array.isArray(result?.errors) ? `: ${result.errors.slice(0, 5).join('; ')}` : '';
      reject(new Error(`Config or canonical contract validation failed${details}`));
    });
    child.stdin.on('error', () => {});
    child.stdin.end(data === undefined ? '' : JSON.stringify(data));
  });
}

export async function codexCredentials(directory = path.join(os.homedir(), '.codex')) {
  await regularPath(directory, { directory: true });
  for (const name of ['config.toml', 'auth.json']) await readBytes(path.join(directory, name), 1_000_000);
  const result = await contract('config', undefined, [directory]);
  let url;
  try { url = new URL(result.base_url); } catch { throw new Error('Invalid configured provider URL'); }
  if (url.username || url.password || url.search || url.hash ||
      !['http:', 'https:'].includes(url.protocol) ||
      (url.protocol === 'http:' && !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname))) throw new Error('Provider URL requires HTTPS or loopback HTTP, without embedded credentials');
  if (typeof result.api_key !== 'string' || !result.api_key.trim() || /[\r\n]/.test(result.api_key)) throw new Error('Missing or invalid auth.json OPENAI_API_KEY');
  return { baseUrl: url.href.replace(/\/$/, ''), key: result.api_key, provider: result.provider, wireApi: result.wire_api };
}
