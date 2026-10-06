import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { CAPTION_FONT, bindCaptionFont, verifyCaptionFont, copyCaptionFont,
  captionFontCss, captionFontReady, validateCaptionFont } from '../caption-font.mjs';

function fixture(text = '很温和的就把我们\n头皮上的脏东西和油脂给清理走') {
  return { canvas: { fps: 30 }, clips: [{ in_seconds: 0, frames: 60,
    captions: [{ from: 0, to: 2, text, style: { weight: 900 } }] }] };
}
async function directory(t) {
  const root = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'caption-font-test-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  return root;
}

test('font bytes are frozen with the project and copied unchanged into render', async t => {
  const root = await directory(t), output = await directory(t), project = fixture();
  await bindCaptionFont(root, project);
  assert.deepEqual(project.caption_font, CAPTION_FONT);
  await verifyCaptionFont(root, project);
  await copyCaptionFont(root, output, project);
  await verifyCaptionFont(output, project);
  assert.match(captionFontCss(project), /font-synthesis:none/);
  assert.ok(!captionFontCss(project).includes('local('));
});
test('missing, replaced, and symlinked font files never fall back to host fonts', async t => {
  const root = await directory(t), project = fixture();
  await bindCaptionFont(root, project);
  const file = path.join(root, project.caption_font.file);
  await fs.rename(file, file + '.original');
  await assert.rejects(verifyCaptionFont(root, project), { code: 'ENOENT' });
  await fs.writeFile(file, 'corrupt font');
  await assert.rejects(verifyCaptionFont(root, project), /hash mismatch/);
  await fs.unlink(file);
  await fs.symlink(file + '.original', file);
  await assert.rejects(verifyCaptionFont(root, project), /regular file/);
});
test('uncovered glyph is rejected before publishing a font binding', async t => {
  const project = fixture('文字😀');
  await assert.rejects(bindCaptionFont(await directory(t), project), /missing glyph U\+1F600/);
  assert.equal(project.caption_font, undefined);
});
test('empty and old projects keep legacy semantics; inactive unsupported cues do not block', async t => {
  const root = await directory(t), project = fixture('😀');
  project.clips[0].captions[0].from = 3;
  project.clips[0].captions[0].to = 4;
  await bindCaptionFont(root, project);
  assert.equal(project.caption_font, undefined);
  assert.equal(captionFontCss(project), '');
  assert.equal(captionFontReady(project), '');
  await verifyCaptionFont(root, project);
});
test('caller cannot replace the versioned font with a URL, another hash or extra CSS', () => {
  for (const changes of [{ file: 'https://bad/font.ttf' }, { sha256: 'a'.repeat(64) }, { css: 'injected' }, { profile: 'unknown' }]) {
    assert.throws(() => validateCaptionFont({ ...CAPTION_FONT, ...changes }), /Unsupported/);
  }
});
test('render readiness waits for every requested weight; failure keeps the gate closed', async () => {
  const project = fixture(); project.caption_font = { ...CAPTION_FONT };
  project.clips[0].captions.push({ from: 0, to: 1, text: '普通字幕' });
  const requested = [];
  let release;
  const pending = new Promise(resolve => { release = resolve; });
  const context = vm.createContext({ window: {}, document: { fonts: { load: async font => {
    requested.push(font); await pending; return [{ status: 'loaded' }];
  } } }, console: { error() {} } });
  vm.runInContext(captionFontReady(project), context);
  assert.equal(context.window.__captionFontLoaded, false);
  release(); await context.window.__captionFontReady;
  assert.equal(context.window.__captionFontLoaded, true);
  await context.window.__hf.buildReady.captionFont;
  assert.equal(requested.length, 2);
  assert.ok(requested[0].startsWith('900 '));
  for (const load of [async () => [], async () => [{ status: 'error' }], async () => { throw new Error('font decode failed'); }]) {
    const broken = vm.createContext({ window: {}, document: { fonts: { load } }, console: { error() {} } });
    vm.runInContext(captionFontReady(project), broken);
    await assert.rejects(broken.window.__captionFontReady);
    assert.equal(broken.window.__captionFontLoaded, false);
    let settled = false;
    broken.window.__hf.buildReady.captionFont.then(() => { settled = true; }, () => { settled = true; });
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(settled, false);
  }
});
