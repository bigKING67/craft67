import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { PAGE_SCRIPT, approveCommand, buildCuts, buildIssues, checkSummary, escapeHtml, headline, jsonForScript, localTime, parseReviewPageArgs, relativeHref, renderReviewPage,
  reviewPage, reviewerLabel, signOffFrom, timecode, writeReviewPage } from '../review-page.mjs';

// Self-authored qa.json shapes only (no customer data).
const sha = 'a'.repeat(64);
const qaFixture = () => ({
  schema_version: 'creative-craft.render-qa.v1', qa_id: 'qa-demo-r2-preview-1', project_id: 'demo', revision: 2, revision_sha256: sha,
  render: { kind: 'preview', file: '/abs/render/video.mp4', sha256: sha, width: 360, height: 640, fps: 30, duration_seconds: 12.5, has_audio: true },
  tool: { name: 'creative-craft-local-production', version: '0.9.0', ffmpeg: '8.0' }, created_at: '2026-10-04T00:00:00.000Z',
  checks: [
    { id: 'resolution', category: 'structure', status: 'pass', observation: 'Rendered 360x640.', measured: { width: 360 } },
    { id: 'integrated-loudness', category: 'audio', status: 'warn', observation: 'Loudness outside target.', measured: { lufs: -19.7 } },
    { id: 'true-peak', category: 'audio', status: 'pass', observation: 'Peak ok.', measured: { true_peak_dbtp: -3.2 } },
    { id: 'shot-sampled', category: 'video', status: 'fail', observation: 'No frame for 1 shot.', refs: [{ time_seconds: 7.25 }] },
    { id: 'cut-point-clicks', category: 'audio', status: 'unknown', observation: 'Decode failed.',
      measured: { cut_points: [{ time_seconds: 4, items: [{ item_id: 'a', edge: 'out' }, { item_id: 'b', edge: 'in' }], click: null, unknown: 'outside' }] } },
    { id: 'burned-caption-cut-points', category: 'captions', status: 'warn', observation: 'b in-point warns.', refs: [{ time_seconds: 4, item_id: 'b', sample_id: 's-cut120-after' }],
      measured: { points: [
        { item_id: 'a', edge: 'in', source_seconds: 1, output_seconds: 0, result: 'clear' },
        { item_id: 'a', edge: 'out', source_seconds: 5, output_seconds: 4, result: 'clear' },
        { item_id: 'b', edge: 'in', source_seconds: 9, output_seconds: 4, result: 'warn', suggested_source_seconds: 9.216667, suggested_shift_seconds: 0.216667 },
        { item_id: 'b', edge: 'out', source_seconds: 17.5, output_seconds: 12.5, result: 'aligned' }] } },
  ],
  samples: [
    { id: 's-a-mid', time_seconds: 2.016667, reason: 'item_mid', item_id: 'a', file: 'frames/s-a-mid.png', sha256: sha },
    { id: 's-cut120-before', time_seconds: 3.983333, reason: 'cut_before', file: 'frames/s-cut120-before.png', sha256: sha },
    { id: 's-cut120-after', time_seconds: 4.016667, reason: 'cut_after', file: 'frames/s-cut120-after.png', sha256: sha },
  ],
  boundary_clips: [{ cut_seconds: 4, file: 'clips/cut-000120.mp4', sha256: sha }],
  contact_sheet: { file: 'contact-sheet.png', sha256: sha }, verdict: 'fail',
  review: { status: 'done', reviewer: 'editor', reviewer_kind: 'human', decision: 'revise', findings: [
    { id: 'f-minor', severity: 'minor', observation: 'Slight colour shift.', refs: [{ time_seconds: 1 }] },
    { id: 'f-crit', severity: 'critical', observation: 'Wrong product.', refs: [{ time_seconds: 9, item_id: 'b' }], fix: 'Replace shot.' }] },
  unverified: ['human listening'],
});
const page = (qa, options = {}) => renderReviewPage(qa, { videoHref: '../render/video.mp4', video: { state: 'match' }, generatedAt: 'T', ...options });

test('timecode formats m:ss.ss and rounds through the minute', () => {
  assert.equal(timecode(0), '0:00.00');
  assert.equal(timecode(5.533333), '0:05.53');
  assert.equal(timecode(59.999), '1:00.00');
  assert.equal(timecode(125.4), '2:05.40');
  assert.equal(timecode(undefined), '0:00.00');
});

test('local time: readable text, ISO kept in datetime/title, raw text for invalid values', () => {
  assert.equal(localTime('2026-10-03T05:32:10.167Z', 'Asia/Shanghai'),
    '<time datetime="2026-10-03T05:32:10.167Z" title="2026-10-03T05:32:10.167Z">2026-10-03 13:32</time>');
  assert.equal(localTime('2026-12-31T23:59:00Z', 'UTC'), '<time datetime="2026-12-31T23:59:00Z" title="2026-12-31T23:59:00Z">2026-12-31 23:59</time>');
  assert.equal(localTime('not a date <x>'), '<time>not a date &lt;x&gt;</time>');
  assert.equal(localTime(null), '未记录');
  const html = page(qaFixture(), { timeZone: 'Asia/Shanghai', generatedAt: '2026-10-04T14:13:57.211Z' });
  assert.match(html, /检查时间 <time datetime="2026-10-04T00:00:00.000Z" title="2026-10-04T00:00:00.000Z">2026-10-04 08:00<\/time><\/span> · <span class="nw">本页生成 <time[^>]*>2026-10-04 22:13<\/time>/);
  assert.match(html, /<a href="#player-section">跳到成片<\/a>/);
});

const signed = { state: 'signed', stage: 'inspect', by: '王<审片>', at: '2026-10-04T15:50:30Z', note: null, status: 'completed', qaPath: 'qa/qa.json' };

test('verdict headline: only a recorded human sign-off leads with 已签字; agent accept waits; an automatic fail is never hidden', () => {
  const box = html => html.slice(html.indexOf('<div class="verdict'), html.indexOf('<nav class="quick"'));
  const variant = (verdict, review, failing = false) => {
    const qa = qaFixture();
    qa.verdict = verdict;
    qa.review = review;
    if (!failing) qa.checks = qa.checks.filter(c => c.status !== 'fail');
    return qa;
  };
  // 1. Done + revise with automatic pass_with_warnings: the decision leads (warn shape and colour), auto verdict below.
  let qa = variant('pass_with_warnings', { status: 'done', reviewer: 'r', reviewer_kind: 'agent', decision: 'revise', findings: [] });
  assert.deepEqual(headline(qa), { tone: 'warn', title: 'Agent 评审：需修改', sub: null, signed: false, done: true, autoTone: 'warn', autoLabel: '通过（有警告）', autoFailed: false, failed: 0 });
  let html = box(page(qa));
  assert.match(html, /^<div class="verdict s-warn"[^>]*><svg[^>]*><path d="M8 1\.9L14\.9 14H1\.1z"/);
  assert.match(html, /<p class="big s-warn">Agent 评审：需修改<\/p>/);
  assert.match(html, /自动检查：<span class="status s-warn">.*<span>通过（有警告）<\/span>/);
  assert.ok(!html.includes('<p class="big s-warn">自动') && !html.includes('alert-fail'));
  // Reject → fail shape.
  assert.match(box(page(variant('pass', { status: 'done', reviewer: 'r', decision: 'reject', findings: [] }))), /^<div class="verdict s-fail"[^>]*><svg[^>]*><rect/);
  // 2. Accept without a sign-off (agent, missing kind, or a self-declared human): "等待人工签字", pending tone, never the pass colour.
  for (const kind of ['agent', undefined, 'human']) {
    qa = variant('pass', { status: 'done', reviewer: 'r', reviewer_kind: kind, decision: 'accept', findings: [] });
    const head = headline(qa);
    assert.deepEqual([head.tone, head.title, head.sub, head.signed], ['pending', '等待人工签字', `${kind === 'human' ? '人工评审' : 'Agent 评审'}：接受`, false]);
    html = box(page(qa));
    assert.match(html, /^<div class="verdict s-pending"[^>]*><svg[^>]*><circle cx="8" cy="8" r="6.5"\/><path d="M8 4\.6V8/);
    assert.match(html, /<p class="big s-pending">等待人工签字<\/p>\n<p class="sub">(Agent |人工)评审：接受<\/p>/);
    assert.match(html, /未提供 production\.json（review-page --production），无法核对人工签字/);
    assert.ok(!/class="big s-pass"|verdict s-pass/.test(html));
  }
  // Not-signed states from production.json keep "等待人工签字" and say why.
  const waiting = { status: 'done', reviewer: 'r', reviewer_kind: 'agent', decision: 'accept', findings: [] };
  for (const [signOff, why] of [
    [{ state: 'unsigned', status: 'awaiting_approval' }, /inspect 阶段尚未签字（状态：awaiting_approval）/],
    [{ ...signed, state: 'changed', recordedSha256: 'b'.repeat(64) }, /签字针对的是另一版本的 qa\.json：记录的 SHA-256 为 <span class="mono">bbbbbbbbbbbb…<\/span>，本文件为 <span class="mono">cccccccccccc…<\/span>（qa\.json 在记录后被修改）/],
    [{ ...signed, state: 'superseded', latest: 'qa-r2/qa.json' }, /签字针对的是 inspect 阶段之后记录的 qa\.json（qa-r2\/qa\.json）/],
    [{ ...signed, state: 'not-recorded' }, /inspect 与 export 阶段都没有记录本 qa\.json（qa\/qa\.json）/],
    [{ state: 'unreadable', error: '文件不存在' }, /无法读取 production\.json：文件不存在/],
  ]) {
    html = box(page(variant('pass', waiting), { signOff, qaSha256: 'c'.repeat(64) }));
    assert.match(html, /<p class="big s-pending">等待人工签字<\/p>/, signOff.state);
    assert.match(html, why, signOff.state);
  }
  // 3. Signed in production.json: "人工已签字：<by> · <time>" leads (escaped), the decision follows, pass shape for accept.
  qa = variant('pass', waiting);
  assert.deepEqual(headline(qa, signed), { tone: 'pass', title: '人工已签字：王<审片>', sub: '评审决定：接受', signed: true, done: true, autoTone: 'pass', autoLabel: '通过', autoFailed: false, failed: 0 });
  html = box(page(qa, { signOff: signed, timeZone: 'Asia/Shanghai' }));
  assert.match(html, /^<div class="verdict s-pass"/);
  assert.match(html, /<p class="big s-pass">人工已签字：王&lt;审片&gt; · <time datetime="2026-10-04T15:50:30Z"[^>]*>2026-10-04 23:50<\/time><\/p>\n<p class="sub">评审决定：接受<\/p>/);
  assert.match(html, /签字记录：production\.json 中 inspect 阶段由 王&lt;审片&gt;（<time[^>]*>2026-10-04 23:50<\/time>）签字；本 qa\.json 的 SHA-256 记录在 inspect 阶段。/);
  // 4. Review not finished: "待评审" title (clock shape), automatic verdict and counts below.
  qa = variant('pass', { status: 'pending', reviewer: null, decision: 'pending', findings: [] });
  html = box(page(qa));
  assert.equal(headline(qa).tone, 'pending');
  assert.match(html, /<p class="big s-pending">待评审<\/p>/);
  assert.match(html, /自动检查：<span class="status s-pass">.*<span>通过<\/span>/);
  assert.match(html, /<ul class="counts"/);
  // 5. Automatic fail + accepted review: the fail stays visible and is called out, signed or not.
  qa = variant('fail', { status: 'done', reviewer: 'r', decision: 'accept', findings: [] }, true);
  for (const signOff of [null, signed]) {
    html = box(page(qa, { signOff }));
    assert.match(html, /<p class="alert-fail"><svg[^>]*><rect[^]*自动检查有失败项（1 项），评审虽为「接受」，失败项仍需处理或说明。/);
    assert.match(html, /自动检查：<span class="status s-fail">.*<span>失败<\/span>/);
  }
  // 6. Automatic fail + pending review: still flagged.
  html = box(page(variant('fail', { status: 'pending', reviewer: null, decision: 'pending', findings: [] }, true)));
  assert.match(html, /待评审/);
  assert.match(html, /自动检查有失败项（1 项）。/);
});

test('sign-off from production.json: latest inspect or any export render-qa SHA-256, else why not', () => {
  const art = (kind, p, sha256) => ({ kind, path: p, sha256 });
  const production = (approval, inspect, exported = [], status = 'completed') => ({ stages: [
    { id: 'inspect', status, approval, artifacts: inspect }, { id: 'export', status: 'completed', approval: null, artifacts: exported }] });
  const by = { by: 'bigKING67', at: '2026-10-04T15:50:30Z', note: '看片签字' };
  const [a, b, c] = ['a', 'b', 'c'].map(x => x.repeat(64));
  const inspect = [art('render-qa', 'qa-r1/qa.json', a), art('note', 'rights.md', c), art('render-qa', 'qa-r2/qa.json', b)];
  assert.deepEqual(signOffFrom(production(by, inspect), 'qa-r2/qa.json', b),
    { state: 'signed', stage: 'inspect', status: 'completed', by: 'bigKING67', at: '2026-10-04T15:50:30Z', note: '看片签字', qaPath: 'qa-r2/qa.json' });
  // An export render-qa was checked after the sign-off: not shown as signed.
  const exported = signOffFrom(production(by, inspect, [art('render-qa', 'qa-x/qa.json', c)]), 'qa-x/qa.json', c);
  assert.deepEqual([exported.state, exported.signedQa], ['export', 'qa-r2/qa.json']);
  const exportHead = headline({ verdict: 'pass', checks: [], review: { status: 'done', decision: 'accept', reviewer_kind: 'agent' } }, exported);
  assert.deepEqual([exportHead.signed, exportHead.tone, exportHead.title], [false, 'pending', '导出检查：签字人未审看本文件']);
  // A note artifact with the same digest is not a render-qa.
  assert.equal(signOffFrom(production(by, inspect), 'rights.md', c).state, 'not-recorded');
  assert.equal(signOffFrom(production(by, inspect), 'qa-r1/qa.json', a).state, 'superseded');
  assert.equal(signOffFrom(production(by, inspect), 'qa-r1/qa.json', a).latest, 'qa-r2/qa.json');
  const changed = signOffFrom(production(by, inspect), 'qa-r2/qa.json', 'd'.repeat(64));
  assert.deepEqual([changed.state, changed.recordedSha256], ['changed', b]);
  assert.equal(signOffFrom(production(null, inspect, [], 'awaiting_approval'), 'qa-r2/qa.json', b).state, 'unsigned');
  assert.equal(signOffFrom(production(by, inspect, [], 'in_progress'), 'qa-r2/qa.json', b).state, 'unsigned');
  for (const junk of [null, {}, { stages: 'x' }, { stages: [{ id: 'inspect', approval: 'x', artifacts: [null] }] }]) assert.equal(signOffFrom(junk, 'qa.json', a).state, 'unsigned');
});

test('reviewer: the name once plus one kind label', () => {
  assert.equal(reviewerLabel({ reviewer: 'Claude', reviewer_kind: 'agent' }), 'Claude · Agent 评审');
  assert.equal(reviewerLabel({ reviewer: 'Claude（agent）', reviewer_kind: 'agent' }), 'Claude（agent）');
  assert.equal(reviewerLabel({ reviewer: 'Claude (Agent) ', reviewer_kind: 'agent' }), 'Claude (Agent)');
  assert.equal(reviewerLabel({ reviewer: '王五（人工）', reviewer_kind: 'human' }), '王五（人工）');
  assert.equal(reviewerLabel({ reviewer: '王五', reviewer_kind: 'human' }), '王五 · 人工评审');
  assert.equal(reviewerLabel({ reviewer: 'Claude（剪辑组）', reviewer_kind: 'agent' }), 'Claude（剪辑组） · Agent 评审');
  assert.equal(reviewerLabel({ reviewer: 'x', reviewer_kind: 'robot' }), 'x · robot 评审');
  assert.equal(reviewerLabel({ reviewer: 'x' }), 'x');
  assert.equal(reviewerLabel({ reviewer: null, reviewer_kind: 'agent' }), '未填写 · Agent 评审');
  assert.equal(reviewerLabel(null), '未填写');
  const qa = qaFixture();
  qa.review.reviewer = 'Claude（agent）';
  qa.review.reviewer_kind = 'agent';
  const html = page(qa);
  assert.ok(!html.includes('（agent）（Agent）') && !html.includes('（Agent）'));
  assert.match(html, /<dt>评审人<\/dt><dd>Claude（agent）<\/dd>/);
  assert.match(html, /评审人：Claude（agent）<\/p>/);
  // A self-declared human reviewer is labelled as such, and still not a sign-off.
  const human = page(qaFixture());
  assert.match(human, /<dt>评审人（人工）<\/dt><dd>editor · 人工评审<\/dd>/);
  assert.match(human, /reviewer_kind 不是人工签字的证据/);
  assert.match(human, /<strong>未签字<\/strong>/);
});

test('check summaries: Chinese text from status and measured for every known check, English fallback otherwise', () => {
  const sum = (id, status, measured, extra = {}) => checkSummary({ id, status, observation: 'English.', ...(measured === undefined ? {} : { measured }), ...extra });
  // Aligned edges with a further change inside (qa short_line) and dips to black are named in Chinese.
  assert.match(sum('burned-caption-cut-points', 'pass', { window_seconds: 0.5, points: [
    { item_id: 'hook', edge: 'out', source_seconds: 60.116667, output_seconds: 3.233333, result: 'aligned', short_line: { source_seconds: 59.633333, shown_seconds: 0.467 } },
    { item_id: 'texture', edge: 'in', source_seconds: 71.35, output_seconds: 3.233333, result: 'clear' }] }),
  /1 个剪辑点正好落在字幕变化帧上.*成片 0:03\.23 hook 出点，那一句只显示 0\.47 秒/);
  assert.match(sum('cut-boundary-fragments', 'warn', { window_seconds: 1, points: [
    { item_id: 'wear', edge: 'in', source_seconds: 124.95, output_seconds: 10.333333, result: 'warn', kind: 'dip',
      dip: { output_frames: 6, output_duration_seconds: 0.2, suggested_source_seconds: 125.15 } }] }),
  /成片 0:10\.33 wear 入点开头从黑场淡入 6 帧（0\.20 秒），建议把源入点改到源时间 125\.150 秒.*黑场过渡可以检出/);
  // A warned edge on a source shot change says the new line may start with the cut.
  assert.match(sum('burned-caption-cut-points', 'warn', { window_seconds: 0.5, points: [
    { item_id: 'test', edge: 'in', source_seconds: 111.683333, output_seconds: 6.3, result: 'warn', suggested_source_seconds: 112.083333, edge_on_shot_change: true }] }),
  /成片 0:06\.30 test 入点，源时间 111\.683 秒 → 建议源时间 112\.083 秒（剪辑点在源镜头切换上，可能只是新的一句随镜头开始，请目测）/);
  // No suggestion: an in-point in a dip that runs to the end of the file.
  assert.match(sum('cut-boundary-fragments', 'warn', { window_seconds: 1, points: [
    { item_id: 'end', edge: 'in', source_seconds: 150, output_seconds: 12, result: 'warn', kind: 'dip', dip: { output_frames: 9, output_duration_seconds: 0.3, suggested_source_seconds: null } }] }),
  /成片 0:12\.00 end 入点开头从黑场淡入 9 帧（0\.30 秒），黑场一直到素材结尾，没有可改的入点/);
  // Caption/speech sync: a warned in-point names the earlier speech and what the cut opens on.
  assert.match(sum('caption-speech-sync', 'warn', { points: [
    { item_id: 'texture', edge: 'in', output_seconds: 3.233333, result: 'warn', coverage: 0.91, earlier_speech: '你们看,', opening_speech: '哇哦,' },
    { item_id: 'texture', edge: 'out', output_seconds: 6.3, result: 'not_applicable', reason: 'out_point' },
    { item_id: 'hook', edge: 'in', output_seconds: 0, result: 'clear', coverage: 0.48 }] }),
  /^2 个入点中有 1 个.*成片 0:03\.23 texture 入点，这行字幕在入点前说「你们看,」时已经在屏幕上（笔画重合 91%），而这里开口说的是「哇哦,」。.*请目测。$/);
  assert.equal(sum('caption-speech-sync', 'not_applicable', { points: [] }), '没有带口播分析（qa --analysis）的入点可以判断。');
  // Unchecked in-points are named; an opening without speech says so; the cut block gets a row.
  assert.match(sum('caption-speech-sync', 'warn', { points: [
    { item_id: 'a', edge: 'in', output_seconds: 0, result: 'warn', coverage: 0.95, earlier_speech: '上一句', opening_speech: null },
    { item_id: 'b', edge: 'in', output_seconds: 2, result: 'unknown', error: 'decode failed' }] }),
  /而入点后 1 秒内没有口播。1 个入点未能检查：成片 0:02\.00 b 入点。/);
  const speechQa = qaFixture();
  speechQa.checks.push({ id: 'caption-speech-sync', category: 'captions', status: 'warn', observation: 'x', measured: { points: [
    { item_id: 'b', edge: 'in', output_seconds: 4, result: 'warn', coverage: 0.9, earlier_speech: '你们看', opening_speech: '哇哦' },
    { item_id: 'a', edge: 'out', output_seconds: 4, result: 'not_applicable', reason: 'out_point' }] } });
  const speechCut = buildCuts(speechQa).find(c => c.time === 4);
  assert.deepEqual(speechCut.speech.map(p => p.edge), ['in'], 'not_applicable entries are not listed on the cut');
  assert.match(page(speechQa), /<dt>字幕与口播<\/dt><dd><ul><li>b 入点：.*这行字幕在入点前说「你们看」时已在屏幕上（笔画重合 90%），这里开口是「哇哦」，请目测/);
  assert.ok(!page(qaFixture()).includes('<dt>字幕与口播</dt>'), 'no row without the check');
  // An accepted fragment still shows what was accepted, then the decision.
  const acceptedQa = qaFixture();
  acceptedQa.checks.push({ id: 'cut-boundary-fragments', category: 'video', status: 'pass', observation: 'x', measured: { window_seconds: 1, points: [
    { item_id: 'b', edge: 'in', output_seconds: 4, result: 'accepted', kind: 'fragment', fragment_frames: 18, suggested_source_in_seconds: 9.6, accepted: { by: 'prefer', option: 'keep_speech', rules: ['shot'] } }] } });
  assert.match(page(acceptedQa), /b 入点：.*已接受.*相邻镜头碎片 18 帧，建议源入点 9\.600 s.*（保留整句，BEATS\.json 事先决定）/);
  // A fragment warning that also sits in a dip names both.
  assert.match(sum('cut-boundary-fragments', 'warn', { window_seconds: 1, points: [
    { item_id: 'b', edge: 'in', source_seconds: 9, output_seconds: 4, result: 'warn', kind: 'fragment', fragment_frames: 3, suggested_source_in_seconds: 9.117,
      dip: { output_frames: 4, output_duration_seconds: 0.133, suggested_source_seconds: 9.25 } }] }),
  /开头有 3 帧上一个源镜头，建议把源入点从源时间 9\.000 秒改到源时间 9\.117 秒；同时开头从黑场淡入 4 帧（0\.13 秒），建议把源入点改到源时间 9\.250 秒/);
  assert.equal(sum('duration-matches-revision', 'pass', { expected_seconds: 17.2, actual_seconds: 17.2, expected_frames: 516 }),
    '成片时长 0:17.20（17.200 秒），修订应为 516 帧（17.200 秒，允许 ±1 帧）：一致。');
  assert.match(sum('duration-matches-revision', 'fail', { expected_seconds: 17.2, actual_seconds: 18, expected_frames: 516 }), /0:18\.00（18\.000 秒）.*：不一致。$/);
  assert.equal(sum('resolution', 'pass', { width: 360, height: 640, expected_width: 360, expected_height: 640, expected_source: 'receipt' }),
    '成片 360×640，应为 360×640（渲染回执记录的输出尺寸）：一致。');
  assert.equal(sum('resolution', 'fail', { width: 360, height: 640, expected_width: 704, expected_height: 1252, expected_source: 'output-size-rule' }),
    '成片 360×640，应为 704×1252（回执没有记录输出尺寸，按当前输出尺寸规则）：不一致。');
  assert.equal(sum('frame-rate', 'pass', { fps: 30 }), '成片 30 fps，与工程帧率一致。');
  assert.equal(sum('frame-rate', 'fail', { fps: 25 }), '成片 25 fps，与工程帧率不一致。');
  assert.equal(sum('audio-stream', 'pass', { has_audio: true, audible_items: ['a', 'b'] }), '工程有 2 个有声 item，成片有音轨。');
  assert.equal(sum('audio-stream', 'fail', { has_audio: false, audible_items: ['a'] }), '工程有 1 个有声 item，但成片没有音轨。');
  assert.equal(sum('audio-stream', 'warn', { has_audio: true, audible_items: [] }), '工程没有有声 item，成片却有音轨。');
  assert.equal(sum('black-segments', 'pass', { segments: [] }), '时间轴有画面处没有超过 0.5 秒的黑场。');
  assert.equal(sum('black-segments', 'warn', { segments: [{ start: 1, end: 2.5 }, { start: 61, end: 62 }] }), '时间轴有画面处有 2 段超过 0.5 秒的黑场：0:01.00–0:02.50、1:01.00–1:02.00。');
  assert.equal(sum('freeze-segments', 'warn', { segments: [{ start: 3, end: 6 }] }), '时间轴有画面处有 1 段超过 2 秒的静止画面：0:03.00–0:06.00。');
  assert.equal(sum('silence-in-audible-ranges', 'pass', { segments: [] }), '有声区间内没有超过 2 秒的静音。');
  assert.equal(sum('integrated-loudness', 'pass', { lufs: -14.2 }), '积分响度 -14.2 LUFS，在目标 -14 ±3 LUFS 范围内。');
  assert.equal(sum('integrated-loudness', 'warn', { lufs: -19.7 }), '积分响度 -19.7 LUFS，不在目标 -14 ±3 LUFS 范围内。');
  assert.equal(sum('integrated-loudness', 'warn', { lufs: null }), '积分响度 负无穷（无声），不在目标 -14 ±3 LUFS 范围内。');
  assert.equal(sum('integrated-loudness', 'unknown', { lufs: null }), 'ebur128 没有给出响度摘要，无法判断积分响度。');
  assert.equal(sum('true-peak', 'pass', { true_peak_dbtp: -3.1, audio_lowered_db: 0, limiter_engaged: false, limiter_ceiling_dbtp: -1 }),
    '真峰值 -3.1 dBTP（上限 -1 dBTP），未超过上限。渲染限幅器没有介入。');
  assert.equal(sum('true-peak', 'warn', { true_peak_dbtp: -0.4, audio_lowered_db: 2.35, limiter_engaged: true }), '真峰值 -0.4 dBTP（上限 -1 dBTP），超过上限。渲染限幅器把整体混音降低了 2.4 dB。');
  assert.equal(sum('true-peak', 'pass', { true_peak_dbtp: -2, audio_lowered_db: null, limiter_engaged: null }), '真峰值 -2.0 dBTP（上限 -1 dBTP），未超过上限。渲染回执没有限幅器记录。');
  // Audio checks of a render without audio carry no measured.
  assert.equal(sum('true-peak', 'not_applicable'), '工程没有有声 item，不测量。');
  assert.equal(sum('cut-point-clicks', 'unknown'), '成片没有音轨，无法测量。');
  const items = [{ item_id: 'hook', edge: 'out' }, { item_id: 'texture', edge: 'in' }];
  const clicks = { ratio_threshold: 6, floor: 0.02, cut_points: [{ time_seconds: 3.233333, items, click: false }, { time_seconds: 6.3, items: [{ item_id: 'test', edge: 'in' }], click: true },
    { time_seconds: 70, items: [{ item_id: 'z', edge: 'in' }], click: null, unknown: 'outside' }] };
  assert.equal(sum('cut-point-clicks', 'pass', { ...clicks, cut_points: clicks.cut_points.slice(0, 1) }),
    '1 个有声剪辑点都没有咔哒声（判定：剪辑点 ±10 毫秒内二阶差分峰值达到周围的 6 倍且不低于 0.02）。');
  assert.equal(sum('cut-point-clicks', 'warn', clicks),
    '3 个有声剪辑点中有 1 个有咔哒声（判定：剪辑点 ±10 毫秒内二阶差分峰值达到周围的 6 倍且不低于 0.02）：0:06.30（test 入点）。1 个剪辑点未能检查：1:10.00（z 入点）。');
  assert.equal(sum('cut-point-clicks', 'unknown', { cut_points: [clicks.cut_points[0], clicks.cut_points[2]] }), '已分析的 1 个有声剪辑点没有咔哒声，但检查不完整。1 个剪辑点未能检查：1:10.00（z 入点）。');
  assert.equal(sum('cut-point-clicks', 'unknown', { error: 'ffmpeg timed out' }), '剪辑点咔哒声分析未能运行（原因见原文）。');
  assert.equal(sum('cut-point-clicks', 'not_applicable', { cut_points: [] }), '成片内没有有声剪辑点。');
  assert.equal(sum('caption-sampled', 'not_applicable'), '本修订没有可见字幕。');
  assert.equal(sum('caption-sampled', 'pass', undefined, { refs: [{ time_seconds: 1, sample_id: 's1' }, { time_seconds: 2, sample_id: 's2' }] }), '已在 2 条字幕各自的中点采样合成帧，供人工查看。');
  assert.equal(sum('caption-sampled', 'fail', undefined, { refs: [{ time_seconds: 1, sample_id: 's1' }, { time_seconds: 2 }] }), '2 条字幕中有 1 条无法采样画面。');
  const inside = { left: 0.1, top: 0.7, right: 0.9, bottom: 0.8 }, outside = { left: 0.01, top: 0.7, right: 0.9, bottom: 0.8 };
  assert.equal(sum('caption-safe-area', 'pass', { method: 'compiled-layout-estimate', margin: 0.05, boxes: [{ item_id: 'c1', ...inside }] }), '1 个字幕框都在 5% 安全边距内（按编译布局估算，不是像素检测）。');
  assert.equal(sum('caption-safe-area', 'fail', { margin: 0.05, boxes: [{ item_id: 'c1', ...inside }, { item_id: 'c2', ...outside }] }), '1 个字幕框越过 5% 安全边距：c2（布局估算，不是像素检测）。');
  assert.equal(sum('caption-safe-area', 'not_applicable'), '本修订没有字幕。');
  assert.equal(sum('graphic-safe-area', 'pass', { margin: 0.05, boxes: [{ item_id: 'g', ...inside }] }), '1 个图形按模板框渲染；模板加载校验保证模板框都在 5% 安全边距内。不是像素检测，也不测量文字是否放得下。');
  assert.equal(sum('graphic-safe-area', 'not_applicable'), '本修订没有图形。');
  const shots = { scene_threshold: 0.3, shots: [{ start: 0, end: 3.233, sample_id: 's-a' }, { start: 3.233, end: 3.9, sample_id: 's-b' }] };
  assert.equal(sum('shot-sampled', 'pass', shots), '检测到 2 个镜头（其中 1 个短于 1 秒），每个都有采样帧。镜头按成片的 ffmpeg 场景分数检测（阈值 0.3）。');
  assert.equal(sum('shot-sampled', 'fail', shots, { refs: [{ time_seconds: 0, sample_id: 's-a' }, { time_seconds: 3.233 }] }), '检测到 2 个镜头，其中 1 个无法采样画面。镜头按成片的 ffmpeg 场景分数检测（阈值 0.3）。');
  // Cut-point checks: output time m:ss.ss, source times labelled 源时间.
  const burned = { window_seconds: 0.5, band: { top: 0.62, bottom: 0.86 }, points: [
    { item_id: 'hook', edge: 'out', source_seconds: 60.116666, output_seconds: 3.233333, result: 'warn', suggested_source_seconds: 59.65 },
    { item_id: 'test', edge: 'in', source_seconds: 111.683333, output_seconds: 6.3, result: 'warn', suggested_source_seconds: 112.083333 },
    { item_id: 'wear', edge: 'out', source_seconds: 131.816667, output_seconds: 17.2, result: 'aligned' }] };
  assert.equal(sum('burned-caption-cut-points', 'warn', burned),
    '3 个源剪辑点中有 2 个在剪辑点内侧 0.5 秒有烧录字幕变化：成片 0:03.23 hook 出点，源时间 60.117 秒 → 建议源时间 59.650 秒；成片 0:06.30 test 入点，源时间 111.683 秒 → 建议源时间 112.083 秒。'
    + '入点有变化表示上一句字幕还在，出点有变化表示下一句字幕闪现；建议时间取第一处变化源帧的中点。字幕带为源画面高度的 62%–86%；帧差启发式，不是 OCR，读不出字幕文字。');
  assert.match(sum('burned-caption-cut-points', 'pass', { ...burned, points: burned.points.slice(2) }), /^1 个源剪辑点内侧 0\.5 秒都没有烧录字幕变化。/);
  assert.match(sum('burned-caption-cut-points', 'unknown', { ...burned, points: [burned.points[2], { item_id: 'q', edge: 'in', output_seconds: 1, result: 'unknown', error: 'x' }] }),
    /^已分析的 1 个源剪辑点没有烧录字幕变化，但检查不完整。1 个剪辑点未能检查：成片 0:01\.00 q 入点。/);
  assert.match(sum('burned-caption-cut-points', 'not_applicable', { points: [] }), /^没有视频素材 item，没有要检查烧录字幕变化的源剪辑点。/);
  const fragments = { window_seconds: 1, points: [
    { item_id: 'b', edge: 'in', source_seconds: 9, output_seconds: 4, result: 'warn', kind: 'fragment', fragment_frames: 3, suggested_source_in_seconds: 9.116667 },
    { item_id: 'a', edge: 'out', source_seconds: 5, output_seconds: 4, result: 'warn', kind: 'flash', fragment_frames: 2, suggested_frames: 118, drop_output_frames: 2, suggested_source_out_seconds: 4.95 },
    { item_id: 'c', edge: 'in', source_seconds: 1, output_seconds: 8, result: 'clear' }] };
  assert.equal(sum('cut-boundary-fragments', 'warn', fragments),
    '3 个源剪辑点中有 2 个在剪辑点内侧 1 秒有相邻镜头碎片、闪场或黑场过渡：成片 0:04.00 b 入点开头有 3 帧上一个源镜头，建议把源入点从源时间 9.000 秒改到源时间 9.117 秒；'
    + '成片 0:04.00 a 出点结尾有 2 帧闪场或极短镜头（< 0.5 秒），建议只保留 118 帧（去掉 2 帧，源出点为源时间 4.950 秒）。整帧差异启发式：压暗再亮起的黑场过渡可以检出，叠化与同机位跳切低于阈值时检测不到。');
  assert.match(sum('cut-boundary-fragments', 'pass', { ...fragments, points: fragments.points.slice(2) }), /^1 个源剪辑点内侧 1 秒都没有相邻镜头碎片、闪场或黑场过渡。/);
  assert.equal(sum('hyperframes-lint', 'pass', { error_count: 0, warning_count: 0, codes: [] }), 'HyperFrames lint：0 个错误，0 个警告。');
  assert.equal(sum('hyperframes-lint', 'warn', { error_count: 0, warning_count: 2, codes: ['W1', 'W2'] }), 'HyperFrames lint：0 个错误，2 个警告（W1、W2）。');
  assert.equal(sum('hyperframes-lint', 'unknown'), '渲染回执没有 lint 结果。');
  // Fallback to the English observation: unknown id, missing or incomplete measured, inherited keys.
  for (const check of [{ id: 'new-check', status: 'pass', measured: {} }, { id: 'resolution', status: 'pass' }, { id: 'integrated-loudness', status: 'warn', measured: {} },
    { id: 'black-segments', status: 'pass', measured: { segments: 'x' } }, { id: 'constructor', status: 'pass', measured: {} }, { id: 'frame-rate', status: 'warn', measured: { fps: 30 } }, null]) {
    assert.equal(checkSummary(check), null, JSON.stringify(check));
  }
  // The page: Chinese summary first, English observation folded under 原文 (escaped); a fallback shows the English text only.
  const qa = qaFixture();
  qa.checks.push({ id: 'new-check', category: 'video', status: 'warn', observation: 'Only <English>.' });
  qa.checks[1].observation = 'Loudness <b>outside</b> target.';
  const html = page(qa);
  const table = html.slice(html.indexOf('id="checks"'), html.indexOf('id="signoff"'));
  assert.match(table, /<p class="obs">积分响度 -19\.7 LUFS，不在目标 -14 ±3 LUFS 范围内。<\/p><details class="orig"><summary>原文<\/summary><p class="obs" lang="en">Loudness &lt;b&gt;outside&lt;\/b&gt; target\.<\/p><\/details>/);
  assert.match(table, /<p class="obs">Only &lt;English&gt;\.<\/p>(?!<details class="orig")/);
  const issues = html.slice(html.indexOf('id="issues"'), html.indexOf('id="cuts"'));
  assert.match(issues, /<p class="obs">积分响度 -19\.7 LUFS[^<]*<\/p><details class="orig"><summary>原文<\/summary>/);
});

test('escaping: text, attributes and embedded JSON cannot break out', () => {
  assert.equal(escapeHtml(`<a href="x">'&`), '&lt;a href=&quot;x&quot;&gt;&#39;&amp;');
  const json = jsonForScript({ s: '</script><script>alert(1)</script>', amp: 'a&b', ls: ' ' });
  assert.ok(!json.includes('<') && !json.includes('>') && !json.includes('&') && !json.includes(' '));
  assert.deepEqual(JSON.parse(json), { s: '</script><script>alert(1)</script>', amp: 'a&b', ls: ' ' });

  const qa = qaFixture(), evil = '</script><script>alert(1)</script><img src=x onerror=alert(2)>';
  qa.project_id = evil;
  qa.qa_id = evil;
  qa.checks[1].observation = evil;
  qa.checks[1].id = `x" onclick="alert(3)`;
  qa.checks[1].measured = { note: evil };
  qa.review.findings[0].observation = evil;
  qa.review.findings[0].fix = evil;
  qa.samples[0].item_id = evil;
  qa.unverified = [evil];
  const html = page(qa);
  // Exactly the page's own two script elements (summary JSON + behaviour).
  assert.equal(html.match(/<script/g).length, 2);
  assert.equal(html.match(/<\/script>/g).length, 2);
  assert.ok(!html.includes('<img src=x'));
  assert.ok(!html.includes('onclick="alert'));
  assert.ok(html.includes('&lt;/script&gt;&lt;script&gt;alert(1)&lt;/script&gt;'));
  const summary = html.match(/<script type="application\/json" id="qa-summary">([^<]*)<\/script>/)[1];
  assert.equal(JSON.parse(summary).qa_id, evil);
});

test('no external URL: every src/href is relative, an anchor or file:, and CSP forbids the network', () => {
  const html = page(qaFixture(), { qaDir: '/abs/qa' });
  assert.ok(!/https?:\/\//.test(html), 'no http(s) URL anywhere in a page built from clean data');
  for (const [, url] of html.matchAll(/\s(?:src|href)="([^"]*)"/g)) assert.ok(!/^[a-z][a-z0-9+.-]*:/i.test(url) || url.startsWith('file:'), url);
  assert.match(html, /default-src 'none'/);
  assert.ok(!/<link\b/.test(html) && !/@import|url\(/.test(html), 'no stylesheet or font loads');
  // The CSP hashes match the inline style and script exactly (so the page itself runs).
  const hash = text => `'sha256-${createHash('sha256').update(text, 'utf8').digest('base64')}'`;
  const style = html.match(/<style>([\s\S]*?)<\/style>/)[1], script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  assert.ok(html.includes(`style-src ${hash(style)}`) && html.includes(`script-src ${hash(script)}`));
});

test('relative paths from the QA directory', () => {
  assert.equal(relativeHref('/w/qa-r1', '/w/render-r1/video.mp4'), '../render-r1/video.mp4');
  assert.equal(relativeHref('/w/qa', '/w/qa/clips/cut 1#a.mp4'), 'clips/cut%201%23a.mp4');
  assert.equal(relativeHref('/w/qa', '/w/x:y/v.mp4'), '../x%3Ay/v.mp4');
  assert.equal(relativeHref('/w/qa', 'frames/a.png'), 'frames/a.png');
  const html = page(qaFixture());
  assert.match(html, /<video id="player"[^>]* src="\.\.\/render\/video\.mp4"/);
  assert.match(html, /src="clips\/cut-000120\.mp4"/);
  assert.match(html, /src="frames\/s-cut120-before\.png"/);
});

test('issues: warn/fail/unknown checks and findings, most severe first, with jump data', () => {
  const issues = buildIssues(qaFixture());
  assert.deepEqual(issues.map(i => i.id), ['f-crit', 'shot-sampled', 'burned-caption-cut-points', 'integrated-loudness', 'f-minor', 'cut-point-clicks']);
  const html = page(qaFixture());
  const panel = html.slice(html.indexOf('id="issues"'), html.indexOf('id="cuts"'));
  assert.match(panel, /<button type="button" class="btn" data-seek="9" data-label="0:09.00">跳到 0:09.00<\/button><span><span class="nw">item b<\/span><\/span>/);
  assert.match(panel, /data-seek="7.25" data-label="0:07.25">跳到 0:07.25/);
  assert.match(panel, /data-seek="4" data-label="0:04.00">跳到 0:04.00/);
  assert.match(panel, /未给出时间/); // loudness: whole-film metric
  assert.ok(panel.indexOf('严重') < panel.indexOf('失败') && panel.indexOf('失败') < panel.indexOf('警告'));
  // Every status carries text and a shape, never colour alone.
  for (const label of ['通过', '警告', '失败', '未知', '不适用']) assert.ok(html.includes(`<span>${label}</span>`), label);
  // Nothing autoplays; seeking does not call play() (only a clip's own button does).
  assert.ok(!/autoplay/.test(html));
  // The only play() call is the clip button's own toggle.
  assert.equal((html.match(/\.play\(/g) ?? []).length, 1);
  assert.match(PAGE_SCRIPT, /const toggleClip=[^\n]*\.play\(/);
});

test('cut points: sides, clip, before/after frames and per-check results', () => {
  const cuts = buildCuts(qaFixture());
  assert.deepEqual(cuts.map(c => c.time), [0, 4, 12.5]);
  const cut = cuts[1];
  assert.deepEqual([cut.before, cut.after], [['a'], ['b']]);
  assert.equal(cut.clip.file, 'clips/cut-000120.mp4');
  assert.equal(cut.beforeFrame.id, 's-cut120-before');
  assert.equal(cut.afterFrame.id, 's-cut120-after');
  assert.equal(cut.burned.length, 2);
  assert.equal(cut.clicks.length, 1);
  const html = page(qaFixture());
  const cuts4 = html.slice(html.indexOf('剪辑点 0:04.00'), html.indexOf('结尾 0:12.50'));
  assert.match(cuts4, /建议源时间 9\.217 s/);
  assert.match(cuts4, /无数据（此 qa\.json 没有该检查）/); // cut-boundary-fragments absent
  assert.match(html, /开头 0:00\.00/);
});

test('empty and legacy qa.json render explicit empty states without throwing', () => {
  for (const qa of [{}, null, 'nonsense', { checks: 'x', samples: [{}], review: null, render: { width: 'x' } }]) {
    const html = renderReviewPage(qa);
    assert.match(html, /没有需要查看的问题/);
    assert.match(html, /找不到成片文件/);
    assert.match(html, /无剪辑点数据/);
    assert.match(html, /没有缩略图墙/);
    assert.match(html, /没有采样帧/);
    assert.match(html, /qa\.json 没有检查记录/);
    assert.match(html, /qa\.json 没有列出未验证项/);
  }
  // A pre-0.8 qa.json: no fragment/click checks, review pending, no reviewer_kind.
  const legacy = qaFixture();
  legacy.checks = legacy.checks.filter(c => !['cut-point-clicks'].includes(c.id));
  legacy.review = { status: 'pending', reviewer: null, decision: 'pending', findings: [] };
  delete legacy.contact_sheet;
  const html = page(legacy);
  assert.match(html, /待评审 · 决定：待定/);
  assert.match(html, /评审尚未填写意见/);
  assert.equal((html.match(/无数据（此 qa\.json 没有该检查）/g) ?? []).length, 6); // 3 cuts × (fragments, clicks)
  // Missing video: jump buttons are disabled, not broken.
  const noVideo = renderReviewPage(qaFixture(), { videoHref: null, video: { state: 'missing', file: '/gone.mp4' } });
  assert.match(noVideo, /找不到成片文件：\/gone\.mp4/);
  assert.ok(!/data-seek="[^"]*" data-label="[^"]*">/.test(noVideo));
  assert.match(page(qaFixture(), { video: { state: 'mismatch' } }), /SHA-256 不一致/);
});

test('sign-off: copyable approve command, placeholder root, revise warning', () => {
  assert.equal(approveCommand(), 'python3 scripts/creative_craft.py video-approve --root <production> --stage inspect --by <name>');
  assert.equal(approveCommand({ production: '/a b/prod', script: '/s/creative_craft.py' }),
    "python3 /s/creative_craft.py video-approve --root '/a b/prod' --stage inspect --by <name>");
  const html = page(qaFixture());
  assert.match(html, /data-copy="python3 scripts\/creative_craft\.py video-approve --root &lt;production&gt; --stage inspect --by &lt;name&gt;"/);
  assert.match(html, /不应签字通过/);
  assert.match(html, /<li>human listening<\/li>/);
});

test('review-page writes only review.html, traceable to the qa.json bytes', async t => {
  const dir = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'creative-review-page-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const qaDir = path.join(dir, 'qa'), renderDir = path.join(dir, 'render');
  await fs.mkdir(path.join(qaDir, 'frames'), { recursive: true });
  await fs.mkdir(renderDir);
  await fs.writeFile(path.join(renderDir, 'video.mp4'), 'not really a video');
  const qa = qaFixture();
  qa.render.file = path.join(renderDir, 'video.mp4');
  qa.render.sha256 = createHash('sha256').update('not really a video').digest('hex');
  await fs.writeFile(path.join(qaDir, 'frames', 's-a-mid.png'), 'png');
  const text = JSON.stringify(qa, null, 2) + '\n';
  await fs.writeFile(path.join(qaDir, 'qa.json'), text);
  const before = await fs.readdir(qaDir);
  const result = await reviewPage(qaDir);
  assert.equal(result.qa_sha256, createHash('sha256').update(text).digest('hex'));
  assert.deepEqual((await fs.readdir(qaDir)).sort(), [...before, 'review.html'].sort());
  const html = await fs.readFile(path.join(qaDir, 'review.html'), 'utf8');
  assert.ok(html.includes(result.qa_sha256));
  assert.match(html, /src="\.\.\/render\/video\.mp4"/);
  assert.match(html, /SHA-256 与 qa\.json 记录一致/);
  assert.match(html, /src="frames\/s-a-mid\.png"/);
  assert.ok(!html.includes('src="frames/s-cut120-before.png"'), 'missing files are not linked');
  // Regeneration replaces review.html; qa.json is untouched; a symlinked review.html is refused.
  await reviewPage(qaDir, { video: path.join(renderDir, 'video.mp4'), production: dir });
  assert.equal(await fs.readFile(path.join(qaDir, 'qa.json'), 'utf8'), text);
  assert.match(await fs.readFile(path.join(qaDir, 'review.html'), 'utf8'), new RegExp(`--root ${dir.replace(/[/.]/g, '\\$&')} `));
  await fs.rm(path.join(qaDir, 'review.html'));
  await fs.symlink(path.join(dir, 'elsewhere.html'), path.join(qaDir, 'review.html'));
  await assert.rejects(writeReviewPage(qaDir, 'x'), /not a regular file/);
  await assert.rejects(fs.stat(path.join(dir, 'elsewhere.html')));
});

test('review-page --production: sign-off read from production.json against the qa.json bytes', async t => {
  const dir = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'creative-review-signoff-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const qaDir = path.join(dir, 'qa-r1');
  await fs.mkdir(qaDir);
  const qa = qaFixture();
  qa.verdict = 'pass';
  qa.checks = qa.checks.filter(c => c.status !== 'fail');
  qa.review = { status: 'done', reviewer: 'Claude（agent）', reviewer_kind: 'agent', decision: 'accept', findings: [] };
  const text = JSON.stringify(qa, null, 2) + '\n', digest = createHash('sha256').update(text).digest('hex');
  await fs.writeFile(path.join(qaDir, 'qa.json'), text);
  const write = (approval, artifacts) => fs.writeFile(path.join(dir, 'production.json'), JSON.stringify({ stages: [
    { id: 'inspect', status: approval ? 'completed' : 'awaiting_approval', approval, artifacts }] }));
  const heading = async () => (await fs.readFile(path.join(qaDir, 'review.html'), 'utf8')).match(/<p class="big [^"]+">([^\n]*)<\/p>/)[1];
  // No production.json at the root: reported, not thrown.
  await reviewPage(qaDir, { production: dir });
  assert.equal(await heading(), '等待人工签字');
  assert.match(await fs.readFile(path.join(qaDir, 'review.html'), 'utf8'), /无法读取 production\.json：文件不存在/);
  // Approved and this qa.json's digest recorded: signed.
  const approval = { by: 'bigKING67', at: '2026-10-04T15:50:30Z', note: '' };
  await write(approval, [{ kind: 'render-qa', path: 'qa-r1/qa.json', sha256: digest }]);
  await reviewPage(qaDir, { production: dir });
  assert.match(await heading(), /^人工已签字：bigKING67 · <time datetime="2026-10-04T15:50:30Z"/);
  assert.match(await fs.readFile(path.join(qaDir, 'review.html'), 'utf8'), /"sign_off":"signed"/);
  // qa.json edited after recording: the signature covers another version.
  await fs.writeFile(path.join(qaDir, 'qa.json'), text.replace('"accept"', '"accept" '));
  await reviewPage(qaDir, { production: dir });
  assert.equal(await heading(), '等待人工签字');
  assert.match(await fs.readFile(path.join(qaDir, 'review.html'), 'utf8'), new RegExp(`另一版本的 qa\\.json：记录的 SHA-256 为 <span class="mono">${digest.slice(0, 12)}…`));
  // Not yet approved.
  await write(null, [{ kind: 'render-qa', path: 'qa-r1/qa.json', sha256: digest }]);
  await reviewPage(qaDir, { production: dir });
  assert.match(await fs.readFile(path.join(qaDir, 'review.html'), 'utf8'), /inspect 阶段尚未签字（状态：awaiting_approval）/);
});

test('cut samples of an old qa.json (frame-start times) attach to their cut by id', () => {
  const qa = qaFixture();
  qa.samples = [{ id: 's-cut120-before', time_seconds: 119 / 30, reason: 'cut_before', file: 'frames/b.png', sha256: sha },
    { id: 's-cut120-after', time_seconds: 4, reason: 'cut_after', file: 'frames/a.png', sha256: sha }];
  const cuts = buildCuts(qa);
  assert.deepEqual(cuts.map(c => c.time), [0, 4, 12.5]);
  assert.deepEqual([cuts[1].beforeFrame.file, cuts[1].afterFrame.file], ['frames/b.png', 'frames/a.png']);
});

test('without render.fps the before/after samples of one cut still pair by id', () => {
  const qa = qaFixture();
  delete qa.render.fps;
  const cuts = buildCuts(qa).filter(c => c.beforeFrame || c.afterFrame);
  assert.equal(cuts.length, 1);
  assert.deepEqual([cuts[0].time, cuts[0].beforeFrame.id, cuts[0].afterFrame.id], [4, 's-cut120-before', 's-cut120-after']);
});

test('inherited keys are not labels; a backslash stays inside one file name', () => {
  const qa = qaFixture();
  qa.checks[0].status = 'constructor';
  qa.checks[0].category = 'toString';
  qa.review.decision = 'toString';
  qa.samples[0].file = 'frames/a\\b.png';
  const html = renderReviewPage(qa, { qaDir: '/abs/qa', videoHref: 'video.mp4' });
  assert.ok(!html.includes('[native code]'));
  assert.match(html, /未知（toString）/);
  if (path.sep === '/') assert.match(html, /src="frames\/a%5Cb\.png"/);
});

test('review-page: digest of the qa.json bytes, any JSON shape, symlinked QA directory refused', async t => {
  const dir = await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()), 'creative-review-page-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const qaDir = path.join(dir, 'qa');
  await fs.mkdir(qaDir);
  // An invalid UTF-8 byte inside a string: the digest is of the bytes on disk.
  const bytes = Buffer.concat([Buffer.from('{"qa_id":"x'), Buffer.from([0xe4, 0xb8]), Buffer.from('"}\n')]);
  await fs.writeFile(path.join(qaDir, 'qa.json'), bytes);
  assert.equal((await reviewPage(qaDir)).qa_sha256, createHash('sha256').update(bytes).digest('hex'));
  await fs.writeFile(path.join(qaDir, 'qa.json'), 'null\n');
  assert.deepEqual((await reviewPage(qaDir)).qa_id, null);
  await fs.symlink(qaDir, path.join(dir, 'link'));
  await assert.rejects(reviewPage(path.join(dir, 'link')), /Symlink not allowed/);
});

test('cut clips: one play/pause button each instead of native controls', () => {
  const html = page(qaFixture());
  const cuts = html.slice(html.indexOf('id="cuts"'));
  assert.match(cuts, /<video data-clip preload="metadata" playsinline [^>]*src="clips\/cut-000120\.mp4"[^>]*><\/video>/);
  assert.ok(!/<video[^>]*data-clip[^>]*controls/.test(html), 'clips have no native controls');
  assert.match(cuts, /<button type="button" class="btn" data-clip-toggle><span data-state>播放片段<\/span><span class="offscreen">（剪辑点 0:04\.00）<\/span><\/button>/);
  assert.match(html, /<video id="player" controls /, 'the main player keeps native controls');
});

// Minimal fakes for running PAGE_SCRIPT: listeners keyed by event name, with
// capture listeners on the document receiving events dispatched to media.
function fakePage() {
  const docListeners = {};
  const media = (attrs = {}) => {
    const el = { listeners: {}, paused: true, ended: false, readyState: 0, networkState: 1, error: null, loads: 0, pauses: 0, _t: 0, throwOnSeek: false, ...attrs,
      addEventListener(n, f) { (this.listeners[n] ??= []).push(f); },
      get currentTime() { return this._t; }, set currentTime(v) { if (this.throwOnSeek) throw new Error('not seekable'); this._t = v; },
      load() { this.loads++; this.networkState = 2; }, pause() { this.paused = true; this.pauses++; fire(this, 'pause'); },
      play() { this.paused = false; fire(this, 'play'); return this.playResult ?? Promise.resolve(); },
      scrollIntoView() {}, focus() {}, matches: sel => sel === 'video[data-clip]' && Boolean(attrs.clip),
      closest: () => (attrs.clip ? figure : null) };
    return el;
  };
  const fire = (el, n) => { for (const f of el.listeners[n] ?? []) f({ target: el }); for (const f of docListeners[n] ?? []) f({ target: el }); };
  const label = { textContent: '播放片段' };
  const figure = { querySelector: sel => (sel.includes('[data-state]') ? label : clip) };
  const player = media(), clip = media({ clip: true }), live = { textContent: '' };
  const document = { getElementById: id => ({ player, live })[id] ?? null, querySelectorAll: () => [player, clip],
    addEventListener(n, f) { (docListeners[n] ??= []).push(f); } };
  new Function('document', 'navigator', PAGE_SCRIPT)(document, {});
  const button = (attrs) => ({ closest: sel => (sel === '[data-seek]' && attrs.seek ? { disabled: false, dataset: attrs.seek } : sel === '[data-clip-toggle]' && attrs.clip ? { closest: () => figure } : null) });
  const click = target => { for (const f of docListeners.click) f({ target }); };
  const settle = () => new Promise(r => setTimeout(r, 60));
  return { player, clip, live, label, fire, click, settle, jump: (t, l) => click(button({ seek: { seek: String(t), label: l } })), toggle: () => click(button({ clip: true })) };
}

test('page script: a jump before metadata starts the load, the last jump wins, errors and failed seeks are announced', async () => {
  const p = fakePage();
  p.jump(3, '0:03.00');
  p.jump(5.5, '0:05.50');
  assert.equal(p.player.loads, 1, 'load() started once (a second call would restart it)');
  await p.settle();
  assert.equal(p.live.textContent, '成片加载中，加载完成后定位到 0:05.50');
  p.player.readyState = 1;
  p.fire(p.player, 'loadedmetadata');
  await p.settle();
  assert.equal(p.player.currentTime, 5.5);
  assert.equal(p.live.textContent, '播放器已定位到 0:05.50');
  p.fire(p.player, 'loadedmetadata'); // a reload does not re-apply an old jump
  assert.equal(p.player.currentTime, 5.5);

  const q = fakePage();
  q.jump(2, '0:02.00');
  q.player.error = { code: 4 };
  q.fire(q.player, 'error');
  await q.settle();
  assert.equal(q.live.textContent, '成片无法加载，无法定位');
  q.player.readyState = 1;
  q.fire(q.player, 'loadedmetadata');
  assert.equal(q.player.currentTime, 0, 'a dropped jump is not applied later');
  // A decode error after metadata does not block seeking.
  q.jump(1, '0:01.00');
  await q.settle();
  assert.deepEqual([q.player.currentTime, q.live.textContent], [1, '播放器已定位到 0:01.00']);
  q.player.throwOnSeek = true;
  q.jump(7, '0:07.00');
  await q.settle();
  assert.equal(q.live.textContent, '无法定位到 0:07.00');
});

test('page script: clip button label follows playback; others pause only once a clip really plays', async () => {
  const p = fakePage();
  p.player.paused = false;
  p.toggle();
  assert.equal(p.label.textContent, '暂停片段');
  assert.equal(p.player.pauses, 0, 'the film keeps playing until the clip is really playing');
  p.fire(p.clip, 'playing');
  assert.deepEqual([p.player.paused, p.clip.paused], [true, false]);
  p.toggle();
  assert.equal(p.label.textContent, '播放片段');
  p.clip.ended = true;
  p.fire(p.clip, 'ended');
  assert.equal(p.label.textContent, '重播片段');

  const q = fakePage();
  q.player.paused = false;
  q.clip.playResult = Promise.reject(new Error('404'));
  q.toggle();
  await q.settle();
  assert.equal(q.label.textContent, '播放片段', 'a failed play() restores the label');
  assert.equal(q.live.textContent, '片段无法播放');
  assert.equal(q.player.paused, false, 'a clip that never played does not pause the film');
});

test('review-page arguments', () => {
  assert.deepEqual(parseReviewPageArgs(['q', '--video', 'v.mp4', '--production', 'p']), { qaDir: 'q', options: { video: 'v.mp4', production: 'p' } });
  assert.throws(() => parseReviewPageArgs([]), /Usage/);
  assert.throws(() => parseReviewPageArgs(['q', '--bogus', '1']), /Unknown/);
});
