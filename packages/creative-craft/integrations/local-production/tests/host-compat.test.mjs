import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SCHEMA, SCHEMA_V2, run } from '../project.mjs';

// Hosts pinned to 0.1.0 drive the CLI with a v1 spec and v1 operations. That
// flow must keep working unchanged; v2 batches upgrade the project explicitly.
const cli = fileURLToPath(new URL('../cli.mjs', import.meta.url));
const node = async (...args) => JSON.parse((await run(process.execPath, [cli, ...args])).stdout);

test('v1 host flow: CLI create with a v1 spec, v1 edit, then a v2 batch migrates', async t => {
  const dir = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'creative-host-compat-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const source = path.join(dir, 'take.mp4'), project = path.join(dir, 'project');
  await run('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=128x72:rate=24:duration=3', '-pix_fmt', 'yuv420p', source]);
  const write = async (name, value) => { const file = path.join(dir, name); await fs.writeFile(file, JSON.stringify(value)); return file; };

  const spec = await write('spec.json', { project_id: 'host', title: 'host', canvas: { width: 128, height: 72, fps: 24 },
    assets: [{ id: 'take', path: source }], audio: [],
    clips: [{ id: 'a', asset_id: 'take', in_seconds: 0, frames: 24, volume: 0, fit: 'contain', captions: [{ from: 0, to: 0.5, text: '第一句' }] },
      { id: 'b', asset_id: 'take', in_seconds: 1, frames: 24, volume: 0, fit: 'contain', captions: [] }] });
  assert.equal((await node('create', project, spec)).schema_version, SCHEMA, 'a v1 spec creates a v1 project');

  const ops = await write('ops.json', [{ type: 'reorder', clip_ids: ['b', 'a'] }]);
  const edited = await node('edit', project, '1', ops);
  assert.deepEqual([edited.schema_version, edited.revision, edited.clips.map(c => c.id)], [SCHEMA, 2, ['b', 'a']]);

  const batch = await write('batch.json', { base_revision: 2, author: 'agent', summary: 'trim', operations: [{ type: 'trim_item', item_id: 'b', tail_frames: 4 }] });
  const result = await node('edit', project, batch);
  assert.deepEqual([result.migration_revision, result.revision], [3, 4]);
  const latest = await node('read', project);
  assert.equal(latest.schema_version, SCHEMA_V2);
  assert.equal(latest.items.find(i => i.id === 'b').frames, 20);
  await assert.rejects(node('edit', project, '4', ops), /v1 operations are not supported/);
});
