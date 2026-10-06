import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { SCHEMA, validate, readProject, editProject, verifyAssets, digest } from '../project.mjs';
import { compose, webVtt } from '../composition.mjs';
import { renderProject } from '../render.mjs';

function fixture() {
  const sha = 'a'.repeat(64);
  return { schema_version: SCHEMA, project_id: 'test-project', title: '中文测试', revision: 1, parent_sha256: null,
    canvas: { width: 640, height: 360, fps: 24 },
    assets: [{ id: 'source', sha256: sha, file: `assets/${sha}.media`, duration: 6, video: true, audio: true, width: 640, height: 360 }],
    clips: [{ id: 'first', asset_id: 'source', in_seconds: 1, frames: 48, volume: 1, fit: 'contain', captions: [{ from: 0.5, to: 2, text: '第一句' }] },
      { id: 'second', asset_id: 'source', in_seconds: 4, frames: 24, volume: 0.5, fit: 'cover', captions: [{ from: 4, to: 5, text: '第二句' }] }], audio: [] };
}
async function projectOnDisk(t) {
  const dir = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'creative-production-test-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  await fs.mkdir(path.join(dir, 'revisions'));
  await fs.writeFile(path.join(dir, 'revisions/000001.json'), JSON.stringify(fixture()));
  return dir;
}

test('source captions clamp to trim and follow reordered clips', () => {
  const p = fixture();
  p.clips.reverse();
  const c = compose(p);
  assert.deepEqual(c.cues, [{ start: 0, end: 1, text: '第二句' }, { start: 1, end: 2, text: '第一句' }]);
  assert.equal(c.frames, 72);
  assert.match(c.html, /id="sound-1".*data-start="0.999999999".*data-media-start="1"/);
});
test('text is escaped and cannot inject scripts', () => {
  const p = fixture();
  p.clips[0].captions[0].text = '<script>alert("x")</script>';
  assert.ok(!compose(p).html.includes('<script>alert'));
  assert.match(webVtt(compose(p).cues), /&lt;script&gt;/);
});
test('preview compiles dimensions without changing saved project canvas', () => {
  const p = fixture();
  p.canvas = { width: 1280, height: 720, fps: 24 };
  assert.match(compose(p, { width: 640, height: 360 }).html, /data-width="640" data-height="360"/);
  assert.equal(p.canvas.width, 1280);
});
test('muted clips emit no audio elements', () => {
  const p = fixture(); p.clips.forEach(c => { c.volume = 0; });
  assert.ok(!compose(p).html.includes('<audio'));
});
test('reject invalid ranges, NaN and unsupported fields', () => {
  for (const changes of [{ frames: 1000 }, { frames: 0 }, { in_seconds: NaN }, { in_seconds: -1 }, { volume: 4 }, { speed: 2 }, { asset_id: 'missing' }]) {
    const p = fixture(); Object.assign(p.clips[0], changes);
    assert.throws(() => validate(p));
  }
});
test('reject path escapes and mismatched asset hash paths', () => {
  for (const file of ['../secret', '/etc/passwd', 'https://example.org/a.mp4', 'assets/fake.media']) {
    const p = fixture(); p.assets[0].file = file;
    assert.throws(() => validate(p), /Invalid asset/);
  }
});
test('audio clips at the end of the edited project', () => {
  const p = fixture();
  p.audio = [{ id: 'music', asset_id: 'source', in_seconds: 0, start_frame: 48, frames: 96, volume: 0.2 }];
  assert.match(compose(p).html, /id="bed-0".*data-start="1.999999999" data-duration="1"/);
});
test('read/edit/reopen preserves old revision and source-timed caption', async t => {
  const dir = await projectOnDisk(t);
  const original = await digest(path.join(dir, 'revisions/000001.json'));
  await editProject(dir, 1, [{ type: 'update_clip', clip_id: 'first', changes: { in_seconds: 2, frames: 24 } }]);
  assert.equal((await readProject(dir)).revision, 2);
  assert.equal((await readProject(dir, 1)).clips[0].frames, 48);
  assert.equal((await readProject(dir)).parent_sha256, original);
  assert.equal(await digest(path.join(dir, 'revisions/000001.json')), original);
  assert.deepEqual(compose(await readProject(dir)).cues, [{ start: 1, end: 2, text: '第二句' }]);
});
test('stale revision and duplicate reorder leave project unchanged', async t => {
  const dir = await projectOnDisk(t);
  await assert.rejects(editProject(dir, 2, [{ type: 'reorder', clip_ids: ['second', 'first'] }]), /conflict/);
  await assert.rejects(editProject(dir, 1, [{ type: 'reorder', clip_ids: ['first', 'first'] }]), /every clip/);
  assert.equal((await readProject(dir)).revision, 1);
});
test('concurrent edit publication has exactly one winner', async t => {
  const dir = await projectOnDisk(t);
  const results = await Promise.allSettled([1, 2].map(() => editProject(dir, 1, [{ type: 'reorder', clip_ids: ['second', 'first'] }])));
  assert.equal(results.filter(r => r.status === 'fulfilled').length, 1);
  assert.equal((await readProject(dir)).revision, 2);
});
test('symlink project/revision is refused', async t => {
  const dir = await projectOnDisk(t);
  const link = `${dir}-link`;
  await fs.symlink(dir, link);
  t.after(() => fs.unlink(link));
  await assert.rejects(readProject(link), /Symlink/);
});
test('invalid operation is atomic', async t => {
  const dir = await projectOnDisk(t);
  await assert.rejects(editProject(dir, 1, [{ type: 'reorder', clip_ids: ['second', 'first'] }, { type: 'delete_everything' }]), /Unknown edit/);
  assert.equal((await readProject(dir)).clips[0].id, 'first');
});
test('parent tampering is detected when reopening a revision', async t => {
  const dir = await projectOnDisk(t);
  await editProject(dir, 1, [{ type: 'reorder', clip_ids: ['second', 'first'] }]);
  await fs.appendFile(path.join(dir, 'revisions/000001.json'), ' ');
  await assert.rejects(readProject(dir), /Parent revision changed/);
});
test('cancelled render persists cancellation, not success', async t => {
  const dir = await projectOnDisk(t);
  const p = fixture();
  await fs.mkdir(path.join(dir, 'assets'));
  const stub = path.join(dir, 'stub');
  await fs.writeFile(stub, 'local test fixture');
  p.assets[0].sha256 = await digest(stub);
  p.assets[0].file = `assets/${p.assets[0].sha256}.media`;
  await fs.rename(stub, path.join(dir, p.assets[0].file));
  await fs.writeFile(path.join(dir, 'revisions/000001.json'), JSON.stringify(p));
  const target = `${dir}-cancelled`;
  t.after(() => fs.rm(target, { recursive: true, force: true }));
  await assert.rejects(renderProject(dir, target, { signal: AbortSignal.abort() }));
  const receipt = JSON.parse(await fs.readFile(path.join(target, 'receipt.json')));
  assert.equal(receipt.status, 'cancelled');
  assert.equal(receipt.output, undefined);
});
test('changed asset blocks render before producing a success receipt', async t => {
  const dir = await projectOnDisk(t);
  await fs.mkdir(path.join(dir, 'assets'));
  await fs.writeFile(path.join(dir, fixture().assets[0].file), 'tampered');
  await assert.rejects(verifyAssets(dir, fixture()), /Asset changed/);
  const target = path.join(dir, 'should-not-exist');
  await assert.rejects(renderProject(dir, target), /Asset changed/);
  await assert.rejects(fs.stat(target), { code: 'ENOENT' });
});

test('source-matched caption style is bounded, scales in preview and keeps legacy default', () => {
  const p = fixture();
  p.clips[0].captions[0].style = { fontHeight: .035, centerY: .6875, color: '#ffff88', strokeWidth: .0015, weight: 900 };
  const old = structuredClone(p);
  const html = compose(p, { width: 320, height: 180 }).html;
  assert.match(html, /top:68.75%;bottom:auto/);
  assert.match(html, /font-size:6.3px/);
  assert.match(html, /color:#ffff88/);
  assert.match(html, /background:transparent/);
  assert.match(html, /id="caption-1" class="caption" data-start/);
  assert.deepEqual(p, old);
  for (const bad of [{ color: 'red;display:none' }, { centerY: NaN }, { fontHeight: true }, { strokeWidth: .1 }, { weight: 100 }, { css: 'anything' }]) {
    const invalid = structuredClone(p);
    Object.assign(invalid.clips[0].captions[0].style, bad);
    assert.throws(() => compose(invalid));
  }
});


test('picture and caption half-open intervals switch on the exact boundary frame', () => {
  for (const fps of [24, 30, 60]) {
    for (const boundary of [1, 2, 41, 59, 61, 627, 668, 1496]) {
      const p = fixture();
      p.canvas.fps = fps;
      p.assets[0].duration = 120;
      p.clips[0] = { ...p.clips[0], in_seconds: 0, frames: boundary,
        captions: [{ from: 0, to: boundary / fps, text: 'before' }] };
      p.clips[1] = { ...p.clips[1], in_seconds: boundary / fps, frames: 2,
        captions: [{ from: boundary / fps, to: (boundary + 2) / fps, text: 'after' }] };
      const html = compose(p).html;
      const active = (id, frame) => {
        const tag = html.match(new RegExp(`<[^>]+id="${id}"[^>]*>`))[0];
        const start = Number(tag.match(/data-start="([^"]+)"/)[1]);
        const end = start + Number(tag.match(/data-duration="([^"]+)"/)[1]);
        return frame / fps >= start && frame / fps < end;
      };
      for (const prefix of ['picture', 'caption', 'sound']) {
        assert.equal(active(`${prefix}-0`, boundary - 1), true);
        assert.equal(active(`${prefix}-0`, boundary), false);
        assert.equal(active(`${prefix}-1`, boundary - 1), false);
        assert.equal(active(`${prefix}-1`, boundary), true);
      }
    }
  }
});
