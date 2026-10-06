import test from 'node:test';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { runAlphaAcceptance } from '../alpha-smoke.mjs';

test('known RGBA product survives background candidates, scale, opacity, crop, undo and relocation', async t => {
  const directory = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'craft-image-alpha-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  await runAlphaAcceptance(path.join(directory, 'acceptance'));
});
