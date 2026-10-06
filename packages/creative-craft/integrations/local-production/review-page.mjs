import { createHash, randomUUID } from 'node:crypto';
import { existsSync } from 'node:fs';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { digest, sha256 } from './content-store.mjs';
import { TOOL, safePath } from './project.mjs';
import { insideSafeArea } from './safe-area.mjs';

// Human review page: one static review.html next to qa.json, derived from it.
// renderReviewPage is a pure function (qa data → HTML string); writeReviewPage
// is the small file wrapper (resolve the rendered video, digest qa.json and the
// video, write review.html). The page links the rendered video, frames, clips
// and contact sheet by relative paths, loads nothing from the network and runs
// no command: it is a view of the evidence, not evidence itself.
export const REVIEW_PAGE = 'review.html';
const APPROVE_SCRIPT = fileURLToPath(new URL('../../skills/creative-craft/scripts/creative_craft.py', import.meta.url));

// ---- Safe text ---------------------------------------------------------------
const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ESC[c]);
// JSON inside <script type="application/json">: no `<`, `>` or `&` survives, so
// neither `</script>` nor `<!--` can end or alter the element.
export const jsonForScript = value => (JSON.stringify(value ?? null) ?? 'null')
  .replace(/</g, '\\u003c').replace(/>/g, '\\u003e').replace(/&/g, '\\u0026').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');
const arr = v => Array.isArray(v) ? v : [];
const obj = v => v && typeof v === 'object' && !Array.isArray(v) ? v : {};
const num = v => typeof v === 'number' && Number.isFinite(v) ? v : null;
const str = v => typeof v === 'string' && v.length ? v : null;
const h = escapeHtml;
// Own keys only: a value such as 'constructor' must not resolve to Object.prototype.
const own = (map, key) => typeof key === 'string' && Object.hasOwn(map, key) ? map[key] : undefined;

// m:ss.ss of a time in seconds (rounded to centiseconds first: 59.999 → 1:00.00).
export function timecode(seconds) {
  const cs = Math.round(Math.max(0, num(seconds) ?? 0) * 100), minutes = Math.floor(cs / 6000);
  return `${minutes}:${((cs % 6000) / 100).toFixed(2).padStart(5, '0')}`;
}

// Readable local time "YYYY-MM-DD HH:mm" (the generating machine's time zone
// unless timeZone is given) in <time datetime title> keeping the ISO value.
export function localTime(iso, timeZone) {
  const date = typeof iso === 'string' ? new Date(iso) : null;
  if (!date || Number.isNaN(date.getTime())) return iso ? `<time>${escapeHtml(iso)}</time>` : '未记录';
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(date).map(p => [p.type, p.value]));
  return `<time datetime="${escapeHtml(iso)}" title="${escapeHtml(iso)}">${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}</time>`;
}

// Relative href from the directory holding review.html to a file: POSIX
// separators, every segment percent-encoded (a `:` or `#` in a name cannot turn
// into a scheme or fragment). Another root (Windows drive) falls back to file://.
export function relativeHref(fromDir, target) {
  const rel = path.relative(path.resolve(fromDir), path.resolve(fromDir, target));
  if (!rel || path.isAbsolute(rel)) return pathToFileURL(path.resolve(fromDir, target)).href;
  return rel.split(path.sep).map(part => part === '..' || part === '.' ? part : encodeURIComponent(part)).join('/');
}

// ---- Labels ------------------------------------------------------------------
const STATUS = { pass: '通过', warn: '警告', fail: '失败', unknown: '未知', not_applicable: '不适用' };
const statusKey = s => own(STATUS, s) ? s : 'unknown';
const VERDICT = { pass: ['pass', '通过'], pass_with_warnings: ['warn', '通过（有警告）'], fail: ['fail', '失败'] };
const REVIEW_STATUS = { pending: '待评审', done: '已评审' };
const DECISION = { pending: '待定', accept: '接受', revise: '需修改', reject: '拒绝' };
const SEVERITY = { critical: ['fail', '严重'], major: ['warn', '主要'], minor: ['info', '次要'] };
const REASON = { item_mid: 'item 中点', cut_before: '剪辑点前', cut_after: '剪辑点后', caption: '字幕', shot: '镜头', manual: '手动' };
const CATEGORY = { structure: '结构', video: '画面', audio: '声音', captions: '字幕', lint: 'lint', delivery: '交付' };
const CHECK_NAME = {
  'duration-matches-revision': '时长与修订一致', resolution: '分辨率', 'frame-rate': '帧率', 'audio-stream': '音轨',
  'black-segments': '黑场', 'freeze-segments': '静止画面', 'silence-in-audible-ranges': '有声区间内的静音',
  'integrated-loudness': '积分响度', 'true-peak': '真峰值', 'cut-point-clicks': '剪辑点咔哒声', 'caption-sampled': '字幕采样',
  'caption-safe-area': '字幕安全区', 'graphic-safe-area': '图形安全区', 'shot-sampled': '按镜头采样',
  'burned-caption-cut-points': '烧录字幕剪辑点', 'cut-boundary-fragments': '剪辑点相邻镜头碎片', 'caption-speech-sync': '字幕与口播同步', 'hyperframes-lint': 'HyperFrames lint',
};
const checkName = id => own(CHECK_NAME, id) ?? String(id ?? '未命名检查');
const EDGE = { in: '入点', out: '出点' };

// Status shapes (not colour alone): circle+tick, triangle+!, square+×, dashed circle+?, circle+bar, circle+i.
const ICON = {
  pass: '<circle cx="8" cy="8" r="6.5"/><path d="M5 8.3l2 2 4-4.5"/>',
  warn: '<path d="M8 1.9L14.9 14H1.1z"/><path d="M8 6.2v3.4M8 11.6v.3"/>',
  fail: '<rect x="1.8" y="1.8" width="12.4" height="12.4" rx="1.5"/><path d="M5.4 5.4l5.2 5.2M10.6 5.4l-5.2 5.2"/>',
  unknown: '<circle cx="8" cy="8" r="6.5" stroke-dasharray="2.6 1.9"/><path d="M6.2 6.4a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.1v.4M8 11.6v.3"/>',
  not_applicable: '<circle cx="8" cy="8" r="6.5"/><path d="M5 8h6"/>',
  info: '<circle cx="8" cy="8" r="6.5"/><path d="M8 7.3v4M8 4.8v.3"/>',
  pending: '<circle cx="8" cy="8" r="6.5"/><path d="M8 4.6V8l2.4 1.6"/>',
};
const icon = (tone, size = 18) => `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${ICON[tone] ?? ICON.unknown}</svg>`;
const badge = (tone, label) => `<span class="status s-${h(tone)}">${icon(tone)}<span>${h(label)}</span></span>`;
const statusBadge = status => badge(statusKey(status), own(STATUS, status) ?? `未知（${status ?? '缺失'}）`);
const empty = text => `<p class="empty">${h(text)}</p>`;

// ---- Derived data (exported for tests) ---------------------------------------
// Reviewer as written in qa.json: the name once plus one kind label ("Claude ·
// Agent 评审"). A name that already ends with a kind marker in () or （） keeps
// only the name. reviewer_kind is written by the reviewer; it is not a sign-off.
const KIND_MARKER = /[（(]\s*(?:agent|ai|human|人工|智能体)\s*[)）]\s*$/i;
const KIND_LABEL = { agent: 'Agent 评审', human: '人工评审' };
const kindLabel = kind => own(KIND_LABEL, kind) ?? `${kind} 评审`;
export function reviewerLabel(review) {
  review = obj(review);
  const name = str(review.reviewer)?.trim() || null, kind = str(review.reviewer_kind);
  const label = kind ? kindLabel(kind) : null;
  if (!name) return label ? `未填写 · ${label}` : '未填写';
  return label && !KIND_MARKER.test(name) ? `${name} · ${label}` : name;
}
// Who the decision line names: an agent also when reviewer_kind is missing; a
// human reviewer is not a sign-off either.
const reviewKind = review => kindLabel(str(review.reviewer_kind) ?? 'agent');

// Human sign-off of this qa.json from a parsed production.json: the inspect
// stage's approval (video-approve --stage inspect) covers this qa.json only when
// its SHA-256 is the latest render-qa recorded in inspect: the signer looked at
// that one. A render-qa recorded in export (state 'export') was checked after
// the sign-off and never reviewed by the signer, so it is not shown as signed.
// qaPath (qa.json relative to the production root) finds an artifact
// that recorded other bytes of the same file. state: signed | unsigned |
// changed (recorded at this path with another SHA-256: qa.json was edited after
// recording) | superseded (an earlier inspect round) | export | not-recorded.
export function signOffFrom(production, qaPath, qaSha256) {
  const stages = arr(obj(production).stages).map(obj), stage = id => stages.find(s => s.id === id) ?? {};
  const inspect = stage('inspect'), approval = obj(inspect.approval);
  const recorded = id => arr(stage(id).artifacts).map(obj).filter(a => a.kind === 'render-qa' && str(a.sha256));
  const inspectQa = recorded('inspect'), exportQa = recorded('export');
  const base = { status: str(inspect.status), by: str(approval.by), at: str(approval.at), note: str(approval.note), qaPath };
  if (!base.by || inspect.status !== 'completed') return { state: 'unsigned', ...base };
  if (qaSha256 && inspectQa.at(-1)?.sha256 === qaSha256) return { state: 'signed', stage: 'inspect', ...base };
  if (qaSha256 && exportQa.some(a => a.sha256 === qaSha256)) return { state: 'export', signedQa: str(inspectQa.at(-1)?.path), ...base };
  if (qaSha256 && inspectQa.some(a => a.sha256 === qaSha256)) return { state: 'superseded', latest: str(inspectQa.at(-1).path), ...base };
  const same = [...inspectQa, ...exportQa].filter(a => a.path === qaPath).at(-1);
  if (same) return { state: 'changed', recordedSha256: same.sha256, ...base };
  return { state: 'not-recorded', ...base };
}

// Headline of the verdict box. Only a human sign-off recorded in production.json
// (signOff.state 'signed') leads with "人工已签字", the review decision below
// it. Without one, an accepted review leads with "等待人工签字" in the pending
// tone (never the pass colour) and names who reviewed ("Agent 评审：接受");
// revise/reject lead with the decision (warn/fail shape), an unfinished review
// with "待评审". The automatic verdict always follows, and an automatic fail is
// flagged separately so no decision can hide it.
const DECISION_TONE = { accept: 'pass', revise: 'warn', reject: 'fail' };
export function headline(qa, signOff = null) {
  qa = obj(qa);
  const review = obj(qa.review), checks = arr(qa.checks).map(obj);
  const [autoTone, autoLabel] = own(VERDICT, qa.verdict) ?? ['unknown', `未知（${qa.verdict ?? '缺失'}）`];
  const failed = checks.filter(c => c.status === 'fail').length;
  const autoFailed = qa.verdict === 'fail' || failed > 0;
  const done = review.status === 'done', signed = obj(signOff).state === 'signed' && Boolean(str(signOff.by));
  const decision = own(DECISION, review.decision) ?? `未知（${review.decision ?? '缺失'}）`;
  const reviewTone = done ? own(DECISION_TONE, review.decision) ?? 'unknown' : 'pending';
  const reviewText = done ? `${reviewKind(review)}：${decision}` : '待评审';
  const [tone, title, sub] = signed ? [reviewTone, `人工已签字：${signOff.by}`, done ? `评审决定：${decision}` : reviewText]
    : !done ? ['pending', '待评审', null]
      : obj(signOff).state === 'export' ? [review.decision === 'accept' ? 'pending' : reviewTone, '导出检查：签字人未审看本文件', reviewText]
      : review.decision === 'accept' ? ['pending', '等待人工签字', reviewText]
        : [reviewTone, reviewText, null];
  return { tone, title, sub, signed, done, autoTone, autoLabel, autoFailed, failed };
}

// ---- Chinese summaries of the automated checks --------------------------------
// qa.mjs writes each observation in English. For a known check id the page
// leads with a Chinese summary built from status and measured (the English
// observation stays available as 原文). An unknown id, or a check without the
// measured fields its summary needs, gives null: the page shows the English
// observation. Output times are m:ss.ss; source times say "源时间 x.xxx 秒".
const fixed = (v, digits) => num(v) === null ? null : num(v).toFixed(digits);
const sourceTime = v => `源时间 ${fixed(v, 3) ?? '?'} 秒`;
const pct = v => `${Math.round(v * 1000) / 10}%`;
const edgeOf = p => `${p.item_id ?? '?'} ${own(EDGE, p.edge) ?? p.edge ?? ''}`.trim();
// A cut-boundary-fragments point inside a source dip to black (plain text; the
// summary and the cut list share it). No suggestion: the dip runs to the end of
// the file (in) or starts before the item (out).
const dipFade = p => {
  const d = obj(p.dip), isIn = p.edge === 'in', seconds = fixed(d.output_duration_seconds, 2);
  const fix = num(d.suggested_source_seconds) !== null ? `，建议把源${isIn ? '入点' : '出点'}改到${sourceTime(d.suggested_source_seconds)}`
    : isIn ? '，黑场一直到素材结尾，没有可改的入点' : '，黑场在这一段开头之前就开始，提前出点也避不开';
  return `${isIn ? '从黑场淡入' : '淡出到黑场'} ${d.output_frames ?? '?'} 帧${seconds ? `（${seconds} 秒）` : ''}${fix}`;
};
const segments = (what, minimum, where) => (status, m) => {
  if (!Array.isArray(m.segments)) return null;
  const list = m.segments.map(obj).map(s => `${timecode(s.start)}–${timecode(s.end)}`).join('、');
  return status === 'pass' ? `${where}没有超过 ${minimum} 秒的${what}。`
    : status === 'warn' ? `${where}有 ${m.segments.length} 段超过 ${minimum} 秒的${what}：${list}。` : null;
};
// Cut-point checks (cut-checks.mjs): per-point results; a warned point is
// described by `describe(point, where)`, `note(measured)` closes the summary.
const OPTION_TEXT = { keep_speech: '保留整句', cut_at_change: '从变化处切', drop_first_phrase: '去掉第一句', drop_last_phrase: '去掉最后一句' };
const decisionText = a => `${own(OPTION_TEXT, obj(a).option) ?? obj(a).option ?? '?'}，${obj(a).by === 'prefer' ? 'BEATS.json 事先决定' : obj(a).by === 'choice' ? 'apply-cuts --choose 选定' : String(obj(a).by ?? '?')}`;
const cutPoints = (what, describe, note) => (status, m) => {
  if (!Array.isArray(m.points)) return null;
  const points = m.points.map(obj), within = num(m.window_seconds) === null ? '' : ` ${m.window_seconds} 秒`;
  if (!points.length) return `没有视频素材 item，没有要检查${what}的源剪辑点。`;
  const warned = points.filter(p => p.result === 'warn'), unknown = points.filter(p => p.result === 'unknown');
  const at = p => `成片 ${timecode(p.output_seconds)} ${edgeOf(p)}`;
  const text = warned.length ? `${points.length} 个源剪辑点中有 ${warned.length} 个在剪辑点内侧${within}有${what}：${warned.map(p => describe(p, at(p))).join('；')}。`
    : unknown.length ? `已分析的 ${points.length - unknown.length} 个源剪辑点没有${what}，但检查不完整。`
      : `${points.length} 个源剪辑点内侧${within}都没有${what}${points.some(p => p.result === 'accepted') ? '（已接受的除外）' : ''}。`;
  // Findings a recorded edit decision accepted (qa --decisions): named, not warned.
  const accepted = points.filter(p => p.result === 'accepted');
  const decided = accepted.length ? `${accepted.length} 处已按剪辑决定接受：${accepted.map(p => `${at(p)}（${decisionText(p.accepted)}）`).join('；')}。` : '';
  return `${text}${unknown.length ? `${unknown.length} 个剪辑点未能检查：${unknown.map(at).join('、')}。` : ''}${decided}${note(m)}`;
};
const safeArea = (what, pass) => (status, m) => {
  if (status === 'not_applicable') return `本修订没有${what}。`;
  if (!Array.isArray(m.boxes)) return null;
  const boxes = m.boxes.map(obj), margin = pct(num(m.margin) ?? 0.05);
  if (status === 'pass') return pass(boxes.length, margin);
  const outside = boxes.filter(b => !insideSafeArea(b));
  return status === 'fail' && outside.length ? `${outside.length} 个${what}框越过 ${margin} 安全边距：${outside.map(b => b.item_id ?? '?').join('、')}（布局估算，不是像素检测）。` : null;
};
const judged = (status, a, b) => status === 'pass' ? a : status === 'fail' ? b : null;
const SUMMARY = {
  'duration-matches-revision': (status, m) => {
    const actual = num(m.actual_seconds), expected = num(m.expected_seconds), frames = num(m.expected_frames), verdict = judged(status, '一致', '不一致');
    if (actual === null || expected === null || frames === null || !verdict) return null;
    return `成片时长 ${timecode(actual)}（${actual.toFixed(3)} 秒），修订应为 ${frames} 帧（${expected.toFixed(3)} 秒，允许 ±1 帧）：${verdict}。`;
  },
  resolution: (status, m) => {
    const verdict = judged(status, '一致', '不一致');
    if (![m.width, m.height, m.expected_width, m.expected_height].every(v => num(v) !== null) || !verdict) return null;
    const basis = m.expected_source === 'receipt' ? '（渲染回执记录的输出尺寸）' : m.expected_source === 'output-size-rule' ? '（回执没有记录输出尺寸，按当前输出尺寸规则）' : '';
    return `成片 ${m.width}×${m.height}，应为 ${m.expected_width}×${m.expected_height}${basis}：${verdict}。`;
  },
  'frame-rate': (status, m) => {
    const verdict = judged(status, '与工程帧率一致', '与工程帧率不一致');
    return num(m.fps) === null || !verdict ? null : `成片 ${m.fps} fps，${verdict}。`;
  },
  'audio-stream': (status, m) => {
    if (typeof m.has_audio !== 'boolean' || !Array.isArray(m.audible_items)) return null;
    const n = m.audible_items.length;
    return n ? `工程有 ${n} 个有声 item，${m.has_audio ? '成片有音轨' : '但成片没有音轨'}。` : `工程没有有声 item，${m.has_audio ? '成片却有音轨' : '成片也没有音轨'}。`;
  },
  'black-segments': segments('黑场', 0.5, '时间轴有画面处'),
  'freeze-segments': segments('静止画面', 2, '时间轴有画面处'),
  'silence-in-audible-ranges': segments('静音', 2, '有声区间内'),
  'integrated-loudness': (status, m) => {
    if (!Object.hasOwn(m, 'lufs')) return null;
    if (status === 'unknown') return 'ebur128 没有给出响度摘要，无法判断积分响度。';
    if (!['pass', 'warn'].includes(status)) return null;
    return `积分响度 ${num(m.lufs) === null ? '负无穷（无声）' : `${fixed(m.lufs, 1)} LUFS`}，${status === 'pass' ? '在' : '不在'}目标 -14 ±3 LUFS 范围内。`;
  },
  'true-peak': (status, m) => {
    if (!Object.hasOwn(m, 'true_peak_dbtp')) return null;
    const limiter = m.limiter_engaged === true ? `渲染限幅器把整体混音降低了 ${fixed(m.audio_lowered_db, 1) ?? '?'} dB。`
      : m.limiter_engaged === false ? '渲染限幅器没有介入。' : '渲染回执没有限幅器记录。';
    if (status === 'unknown') return `ebur128 没有给出真峰值。${limiter}`;
    if (!['pass', 'warn'].includes(status)) return null;
    return `真峰值 ${fixed(m.true_peak_dbtp, 1) ?? '负无穷'} dBTP（上限 -1 dBTP），${status === 'warn' ? '超过上限' : '未超过上限'}。${limiter}`;
  },
  'cut-point-clicks': (status, m) => {
    if (str(m.error)) return '剪辑点咔哒声分析未能运行（原因见原文）。';
    if (!Array.isArray(m.cut_points)) return null;
    const points = m.cut_points.map(obj);
    if (!points.length) return '成片内没有有声剪辑点。';
    const where = p => `${timecode(p.time_seconds)}（${arr(p.items).map(obj).map(edgeOf).join('、')}）`;
    const clicks = points.filter(p => p.click === true), unknown = points.filter(p => p.click !== true && p.click !== false);
    const rule = num(m.ratio_threshold) !== null && num(m.floor) !== null
      ? `（判定：剪辑点 ±10 毫秒内二阶差分峰值达到周围的 ${m.ratio_threshold} 倍且不低于 ${m.floor}）` : '';
    const text = clicks.length ? `${points.length} 个有声剪辑点中有 ${clicks.length} 个有咔哒声${rule}：${clicks.map(where).join('；')}。`
      : unknown.length ? `已分析的 ${points.length - unknown.length} 个有声剪辑点没有咔哒声，但检查不完整。`
        : `${points.length} 个有声剪辑点都没有咔哒声${rule}。`;
    return `${text}${unknown.length ? `${unknown.length} 个剪辑点未能检查：${unknown.map(where).join('；')}。` : ''}`;
  },
  // caption-sampled records no measured: its refs list one entry per caption.
  'caption-sampled': (status, m, check) => {
    if (status === 'not_applicable') return '本修订没有可见字幕。';
    const refs = arr(check.refs).map(obj);
    if (!refs.length) return null;
    return judged(status, `已在 ${refs.length} 条字幕各自的中点采样合成帧，供人工查看。`,
      `${refs.length} 条字幕中有 ${refs.filter(r => !str(r.sample_id)).length} 条无法采样画面。`);
  },
  'caption-safe-area': safeArea('字幕', (n, margin) => `${n} 个字幕框都在 ${margin} 安全边距内（按编译布局估算，不是像素检测）。`),
  'graphic-safe-area': safeArea('图形', (n, margin) => `${n} 个图形按模板框渲染；模板加载校验保证模板框都在 ${margin} 安全边距内。不是像素检测，也不测量文字是否放得下。`),
  'shot-sampled': (status, m, check) => {
    if (!Array.isArray(m.shots)) return null;
    const shots = m.shots.map(obj), short = shots.filter(s => num(s.start) !== null && num(s.end) !== null && s.end - s.start < 1).length;
    const how = num(m.scene_threshold) === null ? '' : `镜头按成片的 ffmpeg 场景分数检测（阈值 ${m.scene_threshold}）。`;
    if (status === 'pass') return `检测到 ${shots.length} 个镜头${short ? `（其中 ${short} 个短于 1 秒）` : ''}，每个都有采样帧。${how}`;
    const refs = arr(check.refs).map(obj);
    return status === 'fail' && refs.length ? `检测到 ${shots.length} 个镜头，其中 ${refs.filter(r => !str(r.sample_id)).length} 个无法采样画面。${how}` : null;
  },
  'burned-caption-cut-points': cutPoints('烧录字幕变化', (p, at) => `${at}，${sourceTime(p.source_seconds)} → 建议${sourceTime(p.suggested_source_seconds)}${p.edge_on_shot_change === true ? '（剪辑点在源镜头切换上，可能只是新的一句随镜头开始，请目测）' : ''}`, m => {
    const band = obj(m.band), where = num(band.top) !== null && num(band.bottom) !== null ? `字幕带为源画面高度的 ${pct(band.top)}–${pct(band.bottom)}；` : '';
    // Aligned edges with a further change inside are not warned (qa short_line): list them to look at.
    const short = arr(m.points).map(obj).filter(p => obj(p.short_line).shown_seconds !== undefined);
    const look = short.length ? `${short.length} 个剪辑点正好落在字幕变化帧上，但内侧 0.5 秒内字幕又变了一次（不报警告，剪辑点那一句只显示很短，请看一下）：${short.map(p => `成片 ${timecode(p.output_seconds)} ${edgeOf(p)}，那一句只显示 ${fixed(p.short_line.shown_seconds, 2) ?? '?'} 秒`).join('；')}。` : '';
    return `${look}入点有变化表示上一句字幕还在，出点有变化表示下一句字幕闪现；建议时间取第一处变化源帧的中点。${where}帧差启发式，不是 OCR，读不出字幕文字。`;
  }),
  'cut-boundary-fragments': cutPoints('相邻镜头碎片、闪场或黑场过渡', (p, at) => {
    // A point can warn for a fragment or flash and also sit in a dip: name both.
    const side = p.edge === 'in' ? '开头' : '结尾';
    if (p.kind === 'dip') return `${at}${side}${dipFade(p)}`;
    const alsoDip = p.dip ? `；同时${side}${dipFade(p)}` : '';
    const what = p.kind === 'flash' ? '闪场或极短镜头（< 0.5 秒）' : p.edge === 'in' ? '上一个源镜头' : '下一个源镜头';
    return p.edge === 'in'
      ? `${at}开头有 ${p.fragment_frames ?? '?'} 帧${what}，建议把源入点从${sourceTime(p.source_seconds)}改到${sourceTime(p.suggested_source_in_seconds)}${alsoDip}`
      : `${at}结尾有 ${p.fragment_frames ?? '?'} 帧${what}，建议只保留 ${p.suggested_frames ?? '?'} 帧（去掉 ${p.drop_output_frames ?? '?'} 帧，源出点为${sourceTime(p.suggested_source_out_seconds)}）${alsoDip}`;
  }, () => '整帧差异启发式：压暗再亮起的黑场过渡可以检出，叠化与同机位跳切低于阈值时检测不到。'),
  'caption-speech-sync': (status, m) => {
    if (status === 'not_applicable') return '没有带口播分析（qa --analysis）的入点可以判断。';
    if (!Array.isArray(m.points)) return null;
    const judged = m.points.map(obj).filter(p => p.result !== 'not_applicable'), warned = judged.filter(p => p.result === 'warn');
    const unknown = judged.filter(p => p.result === 'unknown'), skipped = m.points.map(obj).filter(p => p.reason === 'no_analysis').length;
    const opens = p => p.opening_speech ? `而这里开口说的是「${p.opening_speech}」` : '而入点后 1 秒内没有口播';
    const text = warned.length
      ? `${judged.length} 个入点中有 ${warned.length} 个开头的字幕很可能属于入点之前的口播：${warned.map(p => `成片 ${timecode(p.output_seconds)} ${edgeOf(p)}，这行字幕在入点前说「${p.earlier_speech ?? '?'}」时已经在屏幕上（笔画重合 ${pct(num(p.coverage) ?? 0)}），${opens(p)}`).join('；')}。`
      : unknown.length ? `已判断的 ${judged.length - unknown.length} 个入点没有发现问题，但检查不完整。`
        : `${judged.length} 个入点开头的字幕都不是入点之前的口播留下的。`;
    const unchecked = unknown.length ? `${unknown.length} 个入点未能检查：${unknown.map(p => `成片 ${timecode(p.output_seconds)} ${edgeOf(p)}`).join('、')}。` : '';
    return `${text}${unchecked}${skipped ? `另有 ${skipped} 个入点的素材没有口播分析，未判断。` : ''}比较的是字幕区的描边笔画，不是 OCR，读不出字；标定时约六分之五判对，请目测。`;
  },
  'hyperframes-lint': (status, m) => {
    if (num(m.error_count) === null || num(m.warning_count) === null) return null;
    const codes = arr(m.codes).filter(str);
    return `HyperFrames lint：${m.error_count} 个错误，${m.warning_count} 个警告${codes.length ? `（${codes.join('、')}）` : ''}。`;
  },
};
// Checks qa.mjs writes without measured: audio checks of a render without audio,
// lint without a receipt record, and the caption/graphic checks that summarise
// from status and refs.
const AUDIO_CHECKS = new Set(['silence-in-audible-ranges', 'integrated-loudness', 'true-peak', 'cut-point-clicks']);
const WITHOUT_MEASURED = new Set(['caption-sampled', 'caption-safe-area', 'graphic-safe-area']);
export function checkSummary(check) {
  check = obj(check);
  const summarize = own(SUMMARY, check.id);
  if (!summarize) return null;
  const measured = check.measured && typeof check.measured === 'object' && !Array.isArray(check.measured) ? check.measured : null;
  if (!measured && AUDIO_CHECKS.has(check.id)) return check.status === 'not_applicable' ? '工程没有有声 item，不测量。' : check.status === 'unknown' ? '成片没有音轨，无法测量。' : null;
  if (!measured && check.id === 'hyperframes-lint') return check.status === 'unknown' ? '渲染回执没有 lint 结果。' : null;
  if (!measured && !WITHOUT_MEASURED.has(check.id)) return null;
  return summarize(check.status, measured ?? {}, check) ?? null;
}

const ISSUE_RANK = { finding: { critical: 0, major: 2, minor: 4 }, check: { fail: 1, warn: 3, unknown: 5 } };
const firstTime = refs => Math.min(...refs.map(r => num(r.time_seconds) ?? Infinity), Infinity);

// Everything the reviewer must look at: warn/fail/unknown checks and review
// findings, most severe first (critical finding, fail, major, warn, minor,
// unknown), then by earliest referenced time.
export function buildIssues(qa) {
  const issues = [];
  for (const check of arr(obj(qa).checks).map(obj)) {
    if (!['warn', 'fail', 'unknown'].includes(check.status)) continue;
    issues.push({ kind: 'check', id: String(check.id ?? ''), tone: check.status, label: STATUS[check.status], rank: ISSUE_RANK.check[check.status],
      title: checkName(check.id), summary: checkSummary(check), observation: String(check.observation ?? ''), refs: arr(check.refs).map(obj) });
  }
  for (const finding of arr(obj(obj(qa).review).findings).map(obj)) {
    const [tone, label] = own(SEVERITY, finding.severity) ?? SEVERITY.minor;
    issues.push({ kind: 'finding', id: String(finding.id ?? ''), tone, label, rank: own(ISSUE_RANK.finding, finding.severity) ?? 4,
      title: '评审意见', observation: String(finding.observation ?? ''), fix: str(finding.fix), refs: arr(finding.refs).map(obj) });
  }
  return issues.sort((a, b) => a.rank - b.rank || firstTime(a.refs) - firstTime(b.refs) || a.id.localeCompare(b.id));
}

// Cut points of the render, grouped by output time (within half a frame): the
// items on either side, the ±1 s boundary clip, the last frame before and the
// first frame after, and every cut-point check entry at that time. Times come
// from the checks' measured points, boundary clips and cut samples, so an old
// qa.json without some of them still lists the cuts it knows.
export function buildCuts(qa) {
  qa = obj(qa);
  const fps = num(obj(qa.render).fps), half = fps ? 0.5 / fps : 0, tol = fps ? 0.5 / fps : 0.001;
  const checks = arr(qa.checks).map(obj), find = id => checks.find(c => c.id === id);
  const cuts = [];
  const at = time => {
    let cut = cuts.find(c => Math.abs(c.time - time) <= tol);
    if (!cut) cuts.push(cut = { time, before: [], after: [], clip: null, beforeFrame: null, afterFrame: null, burned: [], fragments: [], clicks: [], speech: [] });
    return cut;
  };
  const side = (cut, item, edge) => {
    const list = edge === 'out' ? cut.before : edge === 'in' ? cut.after : null;
    if (list && str(item) && !list.includes(item)) list.push(item);
  };
  for (const [key, id] of [['burned', 'burned-caption-cut-points'], ['fragments', 'cut-boundary-fragments'], ['speech', 'caption-speech-sync']]) {
    for (const point of arr(obj(find(id)?.measured).points).map(obj)) {
      const time = num(point.output_seconds);
      if (time === null || point.result === 'not_applicable') continue; // caption-speech-sync: out-points / no analysis
      const cut = at(time);
      cut[key].push(point);
      side(cut, point.item_id, point.edge);
    }
  }
  for (const point of arr(obj(find('cut-point-clicks')?.measured).cut_points).map(obj)) {
    const time = num(point.time_seconds);
    if (time === null) continue;
    const cut = at(time);
    cut.clicks.push(point);
    for (const item of arr(point.items).map(obj)) side(cut, item.item_id, item.edge);
  }
  for (const clip of arr(qa.boundary_clips).map(obj)) if (num(clip.cut_seconds) !== null && str(clip.file)) at(clip.cut_seconds).clip = clip;
  const cutSamples = arr(qa.samples).map(obj).filter(s => num(s.time_seconds) !== null && str(s.file) && ['cut_before', 'cut_after'].includes(s.reason));
  const cutFrame = sample => /^s-cut(\d+)-(?:before|after)$/.exec(String(sample.id ?? ''))?.[1] ?? null;
  // Without render.fps the frame number cannot become a time: the samples of one
  // cut frame are placed at the mean of their times so they still pair up.
  const pairTime = new Map();
  for (const sample of cutSamples) {
    const n = cutFrame(sample);
    if (n !== null) pairTime.set(n, [...(pairTime.get(n) ?? []), sample.time_seconds]);
  }
  for (const sample of cutSamples) {
    const time = sample.time_seconds, n = cutFrame(sample);
    // The sample id names the cut frame (s-cut<N>-before/after); qa.json before
    // 0.6 recorded frame-start times, later ones frame midpoints, so the id wins.
    const cut = at(n !== null ? fps ? Number(n) / fps : pairTime.get(n).reduce((a, b) => a + b, 0) / pairTime.get(n).length
      : sample.reason === 'cut_before' ? time + half : time - half);
    cut[sample.reason === 'cut_before' ? 'beforeFrame' : 'afterFrame'] = sample;
  }
  return cuts.sort((a, b) => a.time - b.time);
}

function measuredValue(qa, id, key) {
  const check = arr(obj(qa).checks).map(obj).find(c => c.id === id);
  return num(obj(check?.measured)[key]);
}

// ---- Page --------------------------------------------------------------------
const CSS_BASE = `
:root{color-scheme:light dark;--bg:#f4f6f8;--surface:#ffffff;--text:#1a1f24;--muted:#525b66;--border:#cfd6de;--accent:#0a58a8;--pass:#17703a;--warn:#865200;--fail:#b42318;--unknown:#5b3fb0;--info:#525b66;--mark:#fff4d6;
--sans:system-ui,-apple-system,"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",sans-serif;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root{--bg:#101318;--surface:#181c22;--text:#e7eaee;--muted:#a6afba;--border:#3a424d;--accent:#7cb8ff;--pass:#5cc97e;--warn:#e0b04a;--fail:#ff8a80;--unknown:#c2a8ff;--info:#a6afba;--mark:#3a3420}}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 var(--sans);font-variant-numeric:tabular-nums}
.wrap{max-width:1360px;margin:0 auto;padding:24px 24px 48px}
h1{font-size:1.6rem;line-height:1.3;margin:0 0 4px;text-wrap:balance}
h2{font-size:1.25rem;line-height:1.35;margin:0 0 12px}
h3{font-size:1.05rem;line-height:1.4;margin:0}
p{margin:0 0 8px}
a{color:var(--accent)}
.muted{color:var(--muted)}
.small{font-size:.875rem}
.mono{font-family:var(--mono);font-size:.875rem;overflow-wrap:anywhere}
.icon{flex:none;vertical-align:-3px}
.status{display:inline-flex;align-items:center;gap:6px;font-weight:600}
.s-pass{color:var(--pass)}.s-warn{color:var(--warn)}.s-fail{color:var(--fail)}.s-unknown{color:var(--unknown)}.s-not_applicable,.s-info,.s-pending{color:var(--info)}
section{margin-top:40px}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:20px}
button{font:inherit;color:inherit}
.btn{white-space:nowrap;display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;min-width:44px;padding:8px 14px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--accent);font-weight:600;cursor:pointer;text-align:left}
.btn:hover{border-color:var(--accent)}
.btn[disabled]{color:var(--muted);cursor:not-allowed;border-style:dashed}
:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
#player:focus,#player:focus-within{outline:3px solid var(--accent);outline-offset:3px}
.offscreen{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.skip{position:absolute;left:8px;top:-60px;background:var(--surface);padding:10px 14px;border:1px solid var(--accent);border-radius:6px;z-index:2}
.skip:focus{top:8px}
header.top{display:grid;gap:20px}
.verdict{display:flex;gap:16px;align-items:flex-start;padding:16px 20px;border:1px solid var(--border);border-left-width:6px;border-radius:8px;background:var(--surface)}
.verdict.s-pass{border-left-color:var(--pass)}.verdict.s-warn{border-left-color:var(--warn)}.verdict.s-fail{border-left-color:var(--fail)}.verdict.s-unknown{border-left-color:var(--unknown)}.verdict.s-pending{border-left-color:var(--info)}
.verdict .auto{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:2px 0 6px}
.alert-fail{display:flex;gap:8px;align-items:center;padding:8px 12px;border:2px solid var(--fail);border-radius:6px;color:var(--fail);margin:6px 0 8px}
.verdict .big{font-size:1.35rem;font-weight:700;line-height:1.3}
.verdict .sub{font-weight:600;margin:2px 0 4px}
.verdict p{color:var(--text)}
.counts{display:flex;flex-wrap:wrap;gap:8px 20px;margin:8px 0 0;padding:0;list-style:none}
.counts .n{font-weight:700;color:var(--text);margin-left:2px}
dl.facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px 24px;margin:0}
dl.facts div{min-width:0}
dl.facts dt{font-size:.875rem;color:var(--muted)}
dl.facts dd{margin:0;font-weight:600;overflow-wrap:anywhere}
time,.nw{white-space:nowrap}
nav.quick{display:none}
details.hash summary{cursor:pointer;min-height:44px;display:inline-flex;flex-wrap:wrap;align-items:center;gap:0 6px}
details.hash summary .muted{flex:none;white-space:nowrap}
details.hash[open] .mono{display:block;margin:4px 0 8px}
nav.toc{display:flex;flex-wrap:wrap;gap:4px 8px;margin-top:4px;padding-top:12px;border-top:1px solid var(--border)}
nav.toc a{display:inline-flex;align-items:center;min-height:44px;padding:0 10px;border-radius:6px;text-decoration:none;font-weight:600}
nav.toc a:hover{text-decoration:underline}
.main{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:24px;align-items:start;margin-top:32px}
.main>section{margin-top:0}
.player{display:grid;justify-items:center;gap:10px}
#player{display:block;background:#000;border-radius:4px;aspect-ratio:var(--vw)/var(--vh);width:min(100%,calc(min(70vh,720px)*var(--vw)/var(--vh)));height:auto}
.player .note{justify-self:stretch}
.issues{list-style:none;margin:0;padding:0}
.issues>li{padding:14px 0;border-top:1px solid var(--border)}
.issues>li:first-child{border-top:0;padding-top:0}
.issue-head{display:flex;flex-wrap:wrap;align-items:center;gap:4px 12px;margin-bottom:6px}
.obs{overflow-wrap:anywhere}
.fix{padding-left:10px;border-left:3px solid var(--border)}
.refs{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin:8px 0 0;padding:0;list-style:none}
.refs li{display:inline-flex;align-items:center;gap:8px}
.cut{padding:20px 0;border-top:1px solid var(--border)}
.cut:first-of-type{border-top:0;padding-top:0}
.cut-head{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;margin-bottom:12px}
.cut-media{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start;margin-bottom:12px}
.cut-media figure{margin:0;display:grid;gap:4px;align-content:start;width:calc(220px*var(--vw)/var(--vh));max-width:100%;min-width:120px}
.cut-media video,.cut-media img{display:block;background:#000;border-radius:4px;aspect-ratio:var(--vw)/var(--vh);height:auto;width:100%}
.cut-media .missing{width:100%;aspect-ratio:var(--vw)/var(--vh);display:grid;place-items:center;padding:8px;text-align:center;border:1px dashed var(--border);border-radius:4px;color:var(--muted);font-size:.875rem}
figcaption{font-size:.875rem;color:var(--muted)}
.cut-media figcaption.clip-caption{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px}
.cut-media video[data-clip]{cursor:pointer}
dl.results{display:grid;grid-template-columns:minmax(120px,max-content) 1fr;gap:8px 16px;margin:0}
dl.results dt{color:var(--muted)}
dl.results dd{margin:0;min-width:0}
dl.results ul{margin:0;padding:0;list-style:none}
dl.results li{overflow-wrap:anywhere}
.sheet{margin:0 0 20px}
.sheet img{display:block;max-width:100%;height:auto;border-radius:4px;background:#000}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;list-style:none;margin:0;padding:0}
.tile{display:grid;gap:6px;width:100%;padding:6px;border:1px solid var(--border);border-radius:6px;background:var(--surface);cursor:pointer;text-align:left}
.tile:hover{border-color:var(--accent)}
.tile img{display:block;width:100%;height:auto;aspect-ratio:var(--vw)/var(--vh);object-fit:contain;background:#000;border-radius:3px}
.tile .t{font-weight:700;color:var(--accent)}
.tile .r{font-size:.875rem;color:var(--muted);overflow-wrap:anywhere}
.table-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:8px;background:var(--surface)}
table{border-collapse:collapse;width:100%;min-width:640px}
th,td{padding:10px 12px;border-top:1px solid var(--border);text-align:left;vertical-align:top}
thead th{border-top:0;font-size:.875rem;color:var(--muted);font-weight:600;background:var(--surface)}
td.obs-cell{min-width:280px}
td .id{display:block;font-size:.875rem;color:var(--muted);overflow-wrap:anywhere}
details.measured summary,details.orig summary{cursor:pointer;min-height:44px;display:inline-flex;align-items:center;color:var(--accent);font-weight:600}
details.orig .obs{color:var(--muted)}
pre{margin:4px 0 0;padding:12px;max-height:360px;overflow:auto;background:var(--bg);border:1px solid var(--border);border-radius:6px;font:.8125rem/1.5 var(--mono);white-space:pre}
.cmd{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start}
.cmd pre{flex:1 1 360px;max-height:none;white-space:pre-wrap;overflow-wrap:anywhere}
.signoff{display:grid;gap:24px}
.signoff ul{margin:0;padding-left:1.2em}
.empty{padding:14px 16px;border:1px dashed var(--border);border-radius:6px;color:var(--muted);margin:0}
.empty.ok{color:var(--pass);border-style:solid;display:flex;gap:8px;align-items:center}
.alert{padding:10px 14px;border:1px solid var(--warn);border-radius:6px;color:var(--text);background:var(--mark)}
footer{margin-top:48px;padding-top:16px;border-top:1px solid var(--border);font-size:.875rem;color:var(--muted)}
footer dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:8px 0 0}
footer dd{margin:0;min-width:0}
@media (max-width:900px){.wrap{padding:16px 16px 40px}.main{grid-template-columns:minmax(0,1fr)}h1{font-size:1.4rem}dl.results{grid-template-columns:minmax(0,1fr)}dl.results dt{margin-top:4px}}
@media (max-width:600px){header.top{gap:14px}.verdict{padding:12px 14px;gap:12px}.verdict>.icon{width:28px;height:28px}.verdict .big{font-size:1.15rem}
dl.facts{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 16px}dl.facts .wide{grid-column:1/-1}
nav.quick{display:flex;flex-wrap:wrap;gap:8px}nav.quick a{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--accent);font-weight:600;text-decoration:none}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
@media print{.btn,nav.toc,.skip{display:none}body{background:#fff}}
`;

// Page script. Jump state has one owner: the latest pending jump, applied by
// one permanent loadedmetadata listener or dropped by the error listener; a
// jump before the film has metadata starts its load (the click is a user
// gesture). Clip labels follow play/pause/ended/error through delegated capture
// listeners (media events do not bubble); other videos pause only once one is
// really playing.
export const PAGE_SCRIPT = `(()=>{
const player=document.getElementById('player');const live=document.getElementById('live');
const say=t=>{live.textContent='';setTimeout(()=>{live.textContent=t;},30);};
let pending=null;
const go=(t,label)=>{let ok=true;try{player.currentTime=t;}catch(e){ok=false;}say(ok?'播放器已定位到 '+label:'无法定位到 '+label);};
const seek=(t,label)=>{if(!player)return;player.scrollIntoView({block:'nearest'});player.focus({preventScroll:true});
if(player.readyState>=1){go(t,label);return;}
if(player.error){say('成片无法加载，无法定位');return;}
pending={t,label};if(player.networkState!==2)player.load();say('成片加载中，加载完成后定位到 '+label);};
if(player){player.addEventListener('loadedmetadata',()=>{const p=pending;pending=null;if(p)go(p.t,p.label);});
player.addEventListener('error',()=>{if(pending){pending=null;say('成片无法加载，无法定位');}});}
const clipLabel=(v,text)=>{const b=v.closest('figure').querySelector('[data-clip-toggle] [data-state]');if(b)b.textContent=text;};
const clipState=v=>clipLabel(v,v.ended?'重播片段':v.paused?'播放片段':'暂停片段');
const toggleClip=v=>{if(v.paused||v.ended)v.play().catch(()=>{clipLabel(v,'播放片段');say('片段无法播放');});else v.pause();};
for(const n of ['play','pause','ended','error'])document.addEventListener(n,e=>{const v=e.target;if(v.matches?.('video[data-clip]'))n==='error'?clipLabel(v,'播放片段'):clipState(v);},true);
document.addEventListener('playing',e=>{document.querySelectorAll('video').forEach(o=>{if(o!==e.target&&!o.paused)o.pause();});},true);
const copy=async text=>{let ok=false;try{await navigator.clipboard.writeText(text);ok=true;}catch(e){
const ta=document.createElement('textarea');ta.value=text;ta.setAttribute('readonly','');ta.className='offscreen';document.body.append(ta);ta.select();
try{ok=document.execCommand('copy');}catch(e2){}ta.remove();}say(ok?'已复制':'复制失败，请手动选择文本复制');};
document.addEventListener('click',e=>{const s=e.target.closest('[data-seek]');
if(s&&!s.disabled){seek(Number(s.dataset.seek),s.dataset.label);return;}
const k=e.target.closest('[data-clip-toggle]')?.closest('figure').querySelector('video[data-clip]')??e.target.closest('video[data-clip]');
if(k){toggleClip(k);return;}
const c=e.target.closest('[data-copy]');if(c)copy(c.dataset.copy);});
})();`;

const cspHash = text => `'sha256-${createHash('sha256').update(text, 'utf8').digest('base64')}'`;
const shellQuote = value => /^[\w@%+=:,./-]+$/.test(value) ? value : `'${value.replace(/'/g, `'\\''`)}'`;

// The approve command shown for copying (never run by the page). <production>
// stays a placeholder when the production root is unknown.
export function approveCommand({ production = null, script = 'scripts/creative_craft.py' } = {}) {
  return ['python3', shellQuote(script), 'video-approve', '--root', production ? shellQuote(production) : '<production>', '--stage', 'inspect', '--by', '<name>'].join(' ');
}

/**
 * qa: parsed qa.json (any shape; missing fields render empty states).
 * options: qaDir (resolves absolute asset paths), videoHref (relative href of the
 * rendered video or null), video ({ state: 'match'|'mismatch'|'missing'|'unchecked', file }),
 * qaSha256, generatedAt, production, approveScript, missingFiles (Set of qa-relative files absent on disk),
 * signOff (null when no production root was given; else signOffFrom(...) or
 * { state: 'unreadable', error }).
 */
export function renderReviewPage(qa, options = {}) {
  qa = obj(qa);
  const { qaDir = null, videoHref = null, video = { state: 'unchecked' }, qaSha256 = null, generatedAt = null, production = null, timeZone = undefined,
    approveScript = 'scripts/creative_craft.py', missingFiles = new Set(), signOff = null } = options;
  const render = obj(qa.render), review = obj(qa.review), checks = arr(qa.checks).map(obj);
  const samples = arr(qa.samples).map(obj).filter(s => num(s.time_seconds) !== null && str(s.file));
  const width = num(render.width) > 0 ? render.width : 16, height = num(render.height) > 0 ? render.height : 9;
  const asset = file => {
    if (!str(file)) return null;
    if (missingFiles.has(file)) return null;
    if (path.isAbsolute(file)) return qaDir ? relativeHref(qaDir, file) : null;
    return relativeHref(qaDir ?? '.', file);
  };
  const hasVideo = Boolean(videoHref);
  const jump = (time, extra = '') => {
    const t = num(time);
    if (t === null) return '';
    const label = timecode(t);
    return `<button type="button" class="btn" data-seek="${h(t)}" data-label="${h(label)}"${hasVideo ? '' : ' disabled title="找不到成片，无法跳转"'}>跳到 ${h(label)}${extra}</button>`;
  };
  const refItem = ref => [str(ref.item_id) ? `<span class="nw">item ${h(ref.item_id)}</span>` : '', str(ref.sample_id) ? `<span class="muted small nw">采样 ${h(ref.sample_id)}</span>` : ''].filter(Boolean).join(' ');
  const refsList = refs => {
    const timed = refs.filter(r => num(r.time_seconds) !== null);
    if (!timed.length) return `<p class="muted small">未给出时间（全片或整体指标）${refs.map(refItem).filter(Boolean).length ? '：' + refs.map(refItem).filter(Boolean).join('，') : ''}</p>`;
    return `<ul class="refs">${timed.map(r => `<li>${jump(r.time_seconds)}${refItem(r) ? `<span>${refItem(r)}</span>` : ''}</li>`).join('')}</ul>`;
  };

  // Header summary.
  const head = headline(qa, signOff);
  // What production.json says about the human sign-off of this qa.json.
  const sign = obj(signOff), signer = () => `${h(sign.by)}（${localTime(sign.at, timeZone)}）`;
  const signNote = !signOff ? '生成本页时未提供 production.json（review-page --production），无法核对人工签字；qa.json 里的评审不是签字。'
    : {
      signed: () => `签字记录：production.json 中 inspect 阶段由 ${signer()}签字${sign.note ? `，备注：${h(sign.note)}` : ''}；本 qa.json 的 SHA-256 记录在 ${h(sign.stage)} 阶段。`,
      unreadable: () => `无法读取 production.json：${h(sign.error)}。无法核对人工签字。`,
      unsigned: () => `production.json 中 inspect 阶段尚未签字（状态：${h(sign.status ?? '未知')}）。`,
      changed: () => `production.json 中 ${signer()}的签字针对的是另一版本的 qa.json：记录的 SHA-256 为 <span class="mono">${h(String(sign.recordedSha256).slice(0, 12))}…</span>，本文件为 <span class="mono">${h(String(qaSha256 ?? '').slice(0, 12))}…</span>（qa.json 在记录后被修改），签字不涵盖当前内容。`,
      export: () => `production.json 中 inspect 阶段由 ${signer()}签字，签字针对的是检查版本 ${h(sign.signedQa ?? '未知')}。本 qa.json 是之后记录在 export 阶段的导出检查，签字人没有审看过它；请对照两份检查结果，导出检查出现新的警告或失败时需要重新审看。`,
      superseded: () => `production.json 中 ${signer()}的签字针对的是 inspect 阶段之后记录的 qa.json（${h(sign.latest ?? '未知')}），不是本文件。`,
      'not-recorded': () => `production.json 中有 ${signer()}的签字，但 inspect 与 export 阶段都没有记录本 qa.json（${h(sign.qaPath ?? '未知')}），签字不涵盖它。`,
    }[sign.state]?.() ?? `production.json 签字状态未知（${h(sign.state)}）。`;
  const titleHtml = head.signed ? `${h(head.title)} · ${localTime(sign.at, timeZone)}` : h(head.title);
  const counts = Object.keys(STATUS).map(s => [s, checks.filter(c => statusKey(c.status) === s).length]);
  const kind = render.kind === 'preview' ? '预览' : render.kind === 'export' ? '导出' : '未知';
  const duration = num(render.duration_seconds), fps = num(render.fps);
  const lufs = measuredValue(qa, 'integrated-loudness', 'lufs'), peak = measuredValue(qa, 'true-peak', 'true_peak_dbtp');
  const reviewStatus = own(REVIEW_STATUS, review.status) ?? (qa.review ? `未知（${review.status}）` : 'qa.json 无评审字段');
  const decision = own(DECISION, review.decision) ?? (review.decision ? String(review.decision) : '—');
  const fact = (term, value, wide = false) => `<div${wide ? ' class="wide"' : ''}><dt>${h(term)}</dt><dd>${value}</dd></div>`;
  const hashBlock = (value, label) => str(value)
    ? `<details class="hash"><summary><span class="mono">${h(value.slice(0, 12))}…${h(value.slice(-6))}</span><span class="muted small">展开</span></summary><span class="mono">${h(value)}</span><button type="button" class="btn" data-copy="${h(value)}">复制${h(label)}</button></details>`
    : '<span class="muted">未记录</span>';
  const issues = buildIssues(qa);
  const header = `<header class="top">
<div><h1>审片报告：${h(qa.project_id ?? '未知工程')} 修订 ${h(qa.revision ?? '?')}</h1>
<p class="muted">${h(kind)}渲染 · <span class="nw">检查时间 ${localTime(qa.created_at, timeZone)}</span> · <span class="nw">本页生成 ${localTime(generatedAt, timeZone)}</span></p></div>
<div class="verdict s-${head.tone}" role="group" aria-label="审片结论">${icon(head.tone, 36)}<div>
<p class="big s-${head.tone}">${titleHtml}</p>
${head.sub ? `<p class="sub">${h(head.sub)}</p>` : ''}<p class="small">${signNote}</p>
<p class="auto">自动检查：${badge(head.autoTone, head.autoLabel)}</p>
${head.autoFailed ? `<p class="alert-fail">${icon('fail')}<strong>自动检查有失败项${head.failed ? `（${head.failed} 项）` : ''}${head.done && review.decision === 'accept' ? '，评审虽为「接受」，失败项仍需处理或说明' : ''}。</strong></p>` : ''}
<p>${issues.length ? `需要查看 ${issues.length} 项（自动检查的警告、失败、未知与评审意见）。` : '没有需要查看的自动检查问题或评审意见。'}自动检查只反映技术信号，不替代人工看片与听检。</p>
<ul class="counts" aria-label="检查状态计数">${counts.map(([s, n]) => `<li>${statusBadge(s)}<span class="n">${n}</span></li>`).join('')}</ul></div></div>
<nav class="quick" aria-label="快捷跳转"><a href="#player-section">跳到成片</a><a href="#issues">跳到问题（${issues.length}）</a></nav>
<dl class="facts">
${fact('工程', h(qa.project_id ?? '未知'))}${fact('修订', h(qa.revision ?? '未知'))}${fact('渲染类型', h(kind))}
${fact('时长', duration === null ? '未知' : `${h(timecode(duration))}（${h(duration.toFixed(3))} s）`)}
${fact('分辨率', num(render.width) && num(render.height) ? `${h(render.width)} × ${h(render.height)}` : '未知')}
${fact('帧率', fps === null ? '未知' : `${h(Math.round(fps * 1000) / 1000)} fps`)}
${fact('积分响度', lufs === null ? '无数据' : `${h(lufs.toFixed(1))} LUFS`)}${fact('真峰值', peak === null ? '无数据' : `${h(peak.toFixed(1))} dBTP`)}
${fact('评审状态', `${h(reviewStatus)} · 决定：${h(decision)}`)}
${fact(review.reviewer_kind === 'human' ? '评审人（人工）' : '评审人', h(reviewerLabel(review)))}
${fact('成片 SHA-256', hashBlock(render.sha256, '成片 SHA-256'), true)}
</dl>
<nav class="toc" aria-label="页面目录"><a href="#issues">需要查看的问题</a><a href="#cuts">剪辑点</a><a href="#samples">采样与缩略图墙</a><a href="#checks">全部检查</a><a href="#signoff">签字</a></nav>
</header>`;

  // Player + issues.
  const videoNote = {
    match: `<p class="muted small">成片文件 SHA-256 与 qa.json 记录一致。</p>`,
    mismatch: `<p class="alert">成片文件与 qa.json 记录的 SHA-256 不一致：文件在检查后被改动或替换，页面播放的不是被检查的成片。</p>`,
    unchecked: `<p class="muted small">成片文件未与 qa.json 记录的 SHA-256 核对。</p>`,
  }[video.state] ?? '';
  const player = hasVideo
    ? `<video id="player" controls preload="metadata" playsinline width="${h(width)}" height="${h(height)}" src="${h(videoHref)}" aria-label="渲染成片"></video>
<div class="note"><p class="muted small">成片：<span class="mono">${h(decodeURIComponent(videoHref.split('/').pop()))}</span>（相对本页 <span class="mono">${h(videoHref)}</span>）</p>${videoNote}</div>`
    : `<div class="note">${empty(`找不到成片文件${str(video.file) ? `：${video.file}` : str(render.file) ? `：${render.file}` : ''}。跳转按钮不可用；可用 review-page --video 指定成片位置后重新生成。`)}</div>`;
  // Chinese summary first, the English observation folded under 原文; no summary → the observation itself.
  const observationBlock = (summary, observation) => summary
    ? `<p class="obs">${h(summary)}</p>${observation ? `<details class="orig"><summary>原文</summary><p class="obs" lang="en">${h(observation)}</p></details>` : ''}`
    : `<p class="obs">${h(observation) || '<span class="muted">（无说明）</span>'}</p>`;
  const issueList = issues.length ? `<ol class="issues">${issues.map(issue => `<li>
<div class="issue-head">${badge(issue.tone, issue.label)}<h3>${h(issue.title)}</h3><span class="muted small">${issue.kind === 'check' ? '自动检查' : '评审意见'} ${h(issue.id)}</span></div>
${observationBlock(issue.summary, issue.observation)}
${issue.fix ? `<p class="fix"><span class="muted">建议修改：</span>${h(issue.fix)}</p>` : ''}${refsList(issue.refs)}</li>`).join('')}</ol>`
    : `<p class="empty ok">${icon('pass')}<span>没有需要查看的问题：所有自动检查为通过或不适用，评审没有意见。仍需人工看完整片并听检。</span></p>`;
  const main = `<div class="main">
<section id="player-section" aria-labelledby="player-h"><h2 id="player-h">成片</h2><div class="panel player">${player}</div></section>
<section id="issues" aria-labelledby="issues-h"><h2 id="issues-h">需要查看的问题（${issues.length}）</h2><div class="panel">${issueList}</div></section>
</div>`;

  // Cut points.
  const cuts = buildCuts(qa);
  const end = duration ?? Infinity, tol = fps ? 0.5 / fps : 0.001;
  const has = id => checks.some(c => c.id === id);
  const frameFig = (sample, label) => {
    const href = sample ? asset(sample.file) : null;
    if (!href) return `<figure><div class="missing">${h(label)}：无采样图</div><figcaption>${h(label)}</figcaption></figure>`;
    return `<figure><img src="${h(href)}" alt="${h(label)}，${h(timecode(sample.time_seconds))}" loading="lazy" width="${h(width)}" height="${h(height)}"><figcaption>${h(label)} · ${h(timecode(sample.time_seconds))}</figcaption></figure>`;
  };
  const result = value => {
    const map = { clear: ['pass', '无问题'], aligned: ['pass', '对齐'], accepted: ['info', '已接受'], warn: ['warn', '警告'], unknown: ['unknown', '未知'] };
    const [tone, label] = own(map, value) ?? ['unknown', `未知（${value ?? '缺失'}）`];
    return badge(tone, label);
  };
  const edgeText = p => `${h(p.item_id ?? '?')} ${h(own(EDGE, p.edge) ?? p.edge ?? '')}`;
  const sec = v => num(v) === null ? null : `${num(v).toFixed(3)} s`;
  const cutRow = (label, id, entries, describe) => {
    const body = !has(id) ? '<span class="muted">无数据（此 qa.json 没有该检查）</span>'
      : !entries.length ? '<span class="muted">无数据（该检查未覆盖此剪辑点）</span>'
        : `<ul>${entries.map(describe).join('')}</ul>`;
    return `<dt>${h(label)}</dt><dd>${body}</dd>`;
  };
  const accepted = p => p.result === 'accepted' ? ` <span class="muted">（${h(decisionText(p.accepted))}）</span>` : '';
  const burnedText = p => `<li>${edgeText(p)}：${result(p.result)}${accepted(p)}${p.result === 'warn' && sec(p.suggested_source_seconds) ? ` 建议源时间 ${h(sec(p.suggested_source_seconds))}` : ''}${p.result === 'warn' && p.edge_on_shot_change === true ? ' <span class="muted">剪辑点在源镜头切换上，可能只是新的一句随镜头开始，请目测</span>' : ''}${num(obj(p.short_line).shown_seconds) !== null ? ` <span class="muted">这一句只显示 ${h(fixed(p.short_line.shown_seconds, 2))} 秒，请看一下</span>` : ''}${p.result === 'unknown' && p.error ? ` <span class="muted">${h(p.error)}</span>` : ''}</li>`;
  const speechText = p => `<li>${edgeText(p)}：${result(p.result)}${p.result === 'warn' ? ` <span class="muted">这行字幕在入点前说「${h(p.earlier_speech ?? '?')}」时已在屏幕上（笔画重合 ${h(pct(num(p.coverage) ?? 0))}），${p.opening_speech ? `这里开口是「${h(p.opening_speech)}」` : '入点后 1 秒内没有口播'}，请目测</span>` : ''}${p.result === 'unknown' && p.error ? ` <span class="muted">${h(p.error)}</span>` : ''}</li>`;
  const fragmentText = p => {
    const suggestion = sec(p.suggested_source_in_seconds ?? p.suggested_source_out_seconds);
    const dip = p.dip ? ` ${h(dipFade(p))}` : '';
    const fragment = ` ${p.kind === 'flash' ? '闪场' : '相邻镜头碎片'}${num(p.fragment_frames) !== null ? ` ${h(p.fragment_frames)} 帧` : ''}${suggestion ? `，建议源${p.edge === 'out' ? '出点' : '入点'} ${h(suggestion)}` : ''}`;
    const what = !['warn', 'accepted'].includes(p.result) ? '' : p.kind === 'dip' ? dip : `${fragment}${dip ? `；${dip.trim()}` : ''}`;
    return `<li>${edgeText(p)}：${result(p.result)}${what}${accepted(p)}${p.result === 'unknown' && p.error ? ` <span class="muted">${h(p.error)}</span>` : ''}</li>`;
  };
  const clickText = p => {
    const tone = p.click === true ? 'warn' : p.click === false ? 'pass' : 'unknown';
    const label = p.click === true ? '有咔哒' : p.click === false ? '无咔哒' : '未知';
    const items = arr(p.items).map(obj).map(edgeText).join('、');
    return `<li>${badge(tone, label)}${items ? ` <span class="muted">${items}</span>` : ''}${num(p.ratio) !== null ? ` 峰值比 ${h(p.ratio)}` : ''}${p.unknown ? ` <span class="muted">${h(p.unknown)}</span>` : ''}</li>`;
  };
  const cutBlock = cut => {
    const place = cut.time <= tol ? '开头' : Math.abs(cut.time - end) <= tol ? '结尾' : '剪辑点';
    const sides = `${cut.before.length ? `前：${cut.before.map(h).join('、')}` : '前：—'} → ${cut.after.length ? `后：${cut.after.map(h).join('、')}` : '后：—'}`;
    const clipHref = cut.clip ? asset(cut.clip.file) : null;
    // One play/pause button per clip instead of native controls: a 2 s clip needs
    // no scrubbing, and native controls cost ~4 tab stops per clip.
    const clip = clipHref ? `<figure><video data-clip preload="metadata" playsinline width="${h(width)}" height="${h(height)}" src="${h(clipHref)}" aria-label="剪辑点 ${h(timecode(cut.time))} 前后 1 秒片段"></video>
<figcaption class="clip-caption">前后 1 秒片段 <button type="button" class="btn" data-clip-toggle><span data-state>播放片段</span><span class="offscreen">（剪辑点 ${h(timecode(cut.time))}）</span></button></figcaption></figure>`
      : `<figure><div class="missing">${cut.clip ? '片段文件缺失' : '无边界片段'}</div><figcaption>前后 1 秒片段</figcaption></figure>`;
    return `<article class="cut" aria-label="${h(place)} ${h(timecode(cut.time))}">
<div class="cut-head"><h3>${h(place)} ${h(timecode(cut.time))} <span class="muted small">（${h(cut.time.toFixed(3))} s）</span></h3><span>${sides}</span>${jump(cut.time)}</div>
${cut.clip || cut.beforeFrame || cut.afterFrame ? `<div class="cut-media">${clip}${frameFig(cut.beforeFrame, '剪辑点前最后一帧')}${frameFig(cut.afterFrame, '剪辑点后第一帧')}</div>`
  : `<p class="muted small">没有边界片段与剪辑点采样${place === '剪辑点' ? '' : `（成片${place}，没有相邻画面）`}。</p>`}
<dl class="results">${cutRow('烧录字幕', 'burned-caption-cut-points', cut.burned, burnedText)}${cutRow('相邻镜头碎片', 'cut-boundary-fragments', cut.fragments, fragmentText)}${cutRow('剪辑点咔哒声', 'cut-point-clicks', cut.clicks, clickText)}${has('caption-speech-sync') && cut.speech.length ? cutRow('字幕与口播', 'caption-speech-sync', cut.speech, speechText) : ''}</dl>
</article>`;
  };
  const cutsSection = `<section id="cuts" aria-labelledby="cuts-h"><h2 id="cuts-h">剪辑点（${cuts.length}）</h2>
<p class="muted small">每个 item 的入点与出点按成片时间合并；“开头”“结尾”是首个 item 的入点与末个 item 的出点（源素材剪辑点，成片内无相邻画面）。</p>
<div class="panel">${cuts.length ? cuts.map(cutBlock).join('') : empty('无剪辑点数据：qa.json 没有剪辑点检查、边界片段或剪辑点采样。')}</div></section>`;

  // Samples and contact sheet.
  const sheetHref = asset(obj(qa.contact_sheet).file);
  const sheet = sheetHref ? `<figure class="sheet"><img src="${h(sheetHref)}" alt="缩略图墙：按时间顺序拼接的采样帧" loading="lazy"><figcaption>缩略图墙（contact sheet，按时间顺序）</figcaption></figure>`
    : empty(qa.contact_sheet ? '缩略图墙文件缺失。' : '没有缩略图墙。');
  const sorted = [...samples].sort((a, b) => a.time_seconds - b.time_seconds);
  const tiles = sorted.length ? `<ul class="grid">${sorted.map(s => {
    const href = asset(s.file), label = timecode(s.time_seconds), reason = own(REASON, s.reason) ?? String(s.reason ?? '未知原因');
    return `<li><button type="button" class="tile" data-seek="${h(s.time_seconds)}" data-label="${h(label)}"${hasVideo ? '' : ' disabled'} aria-label="跳到 ${h(label)}，${h(reason)}${s.item_id ? `，item ${h(s.item_id)}` : ''}">
${href ? `<img src="${h(href)}" alt="" loading="lazy" width="${h(width)}" height="${h(height)}">` : '<span class="missing">采样文件缺失</span>'}
<span class="t">${h(label)}</span><span class="r">${h(reason)}${s.item_id ? ` · ${h(s.item_id)}` : ''}</span></button></li>`;
  }).join('')}</ul>` : empty('没有采样帧。');
  const samplesSection = `<section id="samples" aria-labelledby="samples-h"><h2 id="samples-h">采样与缩略图墙（${sorted.length} 帧）</h2>
<p class="muted small">采样是合成后的成片帧。点击任一帧，播放器跳到该时间（不自动播放）。</p>${sheet}${tiles}</section>`;

  // All checks.
  const checkRows = checks.map(c => {
    const refs = arr(c.refs).map(obj).filter(r => num(r.time_seconds) !== null);
    const measured = c.measured && typeof c.measured === 'object' ? `<details class="measured"><summary>测量数据</summary><pre>${h(JSON.stringify(c.measured, null, 2))}</pre></details>` : '';
    return `<tr><td><strong>${h(checkName(c.id))}</strong><span class="id">${h(c.id ?? '')}</span></td><td>${h(own(CATEGORY, c.category) ?? c.category ?? '—')}</td><td>${statusBadge(c.status)}</td>
<td class="obs-cell">${observationBlock(checkSummary(c), String(c.observation ?? ''))}${refs.length ? `<ul class="refs">${refs.map(r => `<li>${jump(r.time_seconds)}${refItem(r) ? `<span>${refItem(r)}</span>` : ''}</li>`).join('')}</ul>` : ''}${measured}</td></tr>`;
  }).join('');
  const checksSection = `<section id="checks" aria-labelledby="checks-h"><h2 id="checks-h">全部检查（${checks.length}）</h2>
${checks.length ? `<div class="table-wrap"><table><thead><tr><th scope="col">检查</th><th scope="col">类别</th><th scope="col">状态</th><th scope="col">观察与测量</th></tr></thead><tbody>${checkRows}</tbody></table></div>` : empty('qa.json 没有检查记录。')}</section>`;

  // Sign-off.
  const findings = arr(review.findings).map(obj);
  const command = approveCommand({ production, script: approveScript });
  const unverified = arr(qa.unverified).filter(v => typeof v === 'string');
  const signoff = `<section id="signoff" aria-labelledby="signoff-h"><h2 id="signoff-h">签字</h2><div class="panel signoff">
<div><h3>签字状态</h3><p>${head.signed ? `<strong>人工已签字</strong>：${signer()}` : '<strong>未签字</strong>'}</p><p class="muted small">${signNote}</p></div>
<div><h3>评审决定</h3><p>${h(reviewStatus)} · 决定：<strong>${h(decision)}</strong> · 评审人：${h(reviewerLabel(review))}</p>
${review.reviewer_kind === 'human' ? '<p class="muted small">评审人自报为人工；qa.json 中的 reviewer_kind 不是人工签字的证据，签字以 production.json 的 video-approve 记录为准。</p>'
    : '<p class="muted small">评审由 Agent 填写（或未注明评审人类型）；qa.json 中的评审不是人工签字的证据。</p>'}
${findings.length ? `<ul>${findings.map(f => `<li>${badge(...(own(SEVERITY, f.severity) ?? SEVERITY.minor))} <span class="muted small">${h(f.id ?? '')}</span> ${h(f.observation ?? '')}${f.fix ? `<br><span class="muted">建议修改：</span>${h(f.fix)}` : ''}</li>`).join('')}</ul>` : empty(review.status === 'done' ? '评审没有意见。' : '评审尚未填写意见。')}</div>
<div><h3>签字命令</h3><p>审片人确认通过后，在终端自行执行下面的命令记录签字（适用于 <span class="mono">video-init --export-requires-human-review</span> 的 production，inspect 阶段等待批准时）。本页不执行任何操作。</p>
${review.decision === 'revise' || review.decision === 'reject' ? `<p class="alert">当前评审决定为「${h(decision)}」，不应签字通过；修改后重新渲染与检查。</p>` : ''}
<div class="cmd"><pre><code>${h(command)}</code></pre><button type="button" class="btn" data-copy="${h(command)}">复制命令</button></div>
<p class="muted small">${production ? '' : '<span class="mono">&lt;production&gt;</span> 是 production.json 所在目录，生成本页时未提供（可用 review-page --production 写入）；'}<span class="mono">&lt;name&gt;</span> 换成签字人姓名。</p></div>
<div><h3>未验证项</h3>${unverified.length ? `<ul>${unverified.map(u => `<li>${h(u)}</li>`).join('')}</ul>` : empty('qa.json 没有列出未验证项。')}</div>
</div></section>`;

  const summary = { qa_id: qa.qa_id ?? null, qa_sha256: qaSha256, schema_version: qa.schema_version ?? null, project_id: qa.project_id ?? null,
    revision: qa.revision ?? null, revision_sha256: qa.revision_sha256 ?? null, render_sha256: render.sha256 ?? null, verdict: qa.verdict ?? null,
    review_status: review.status ?? null, decision: review.decision ?? null, sign_off: signOff ? sign.state ?? null : null, generated_at: generatedAt, generator: `${TOOL.name} ${TOOL.version}` };
  const tool = obj(qa.tool);
  const footer = `<footer><p>本页由 qa.json 派生，只是证据的查看方式，不是证据本身；评审结果以 qa.json 与签字记录为准。</p><dl>
<dt>qa_id</dt><dd class="mono">${h(qa.qa_id ?? '未记录')}</dd><dt>qa.json SHA-256</dt><dd class="mono">${h(qaSha256 ?? '未计算')}</dd>
<dt>schema</dt><dd class="mono">${h(qa.schema_version ?? '未记录')}</dd><dt>修订 SHA-256</dt><dd class="mono">${h(qa.revision_sha256 ?? '未记录')}</dd>
<dt>检查工具</dt><dd>${h(tool.name ?? '未记录')} ${h(tool.version ?? '')}${tool.ffmpeg ? ` · ffmpeg ${h(tool.ffmpeg)}` : ''}</dd><dt>页面生成器</dt><dd>${h(TOOL.name)} ${h(TOOL.version)}</dd></dl></footer>`;

  const css = `:root{--vw:${width};--vh:${height}}${CSS_BASE}`;
  const csp = `default-src 'none'; img-src 'self' file: data:; media-src 'self' file:; style-src ${cspHash(css)}; script-src ${cspHash(PAGE_SCRIPT)}; base-uri 'none'; form-action 'none'`;
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="${csp}">
<meta name="referrer" content="no-referrer">
<title>审片报告 · ${h(qa.project_id ?? '未知工程')} 修订 ${h(qa.revision ?? '?')}</title>
<style>${css}</style>
</head>
<body>
<a class="skip" href="#issues">跳到需要查看的问题</a>
<div class="wrap">
${header}
<main>
${main}
${cutsSection}
${samplesSection}
${checksSection}
${signoff}
</main>
${footer}
</div>
<div id="live" class="offscreen" role="status" aria-live="polite"></div>
<script type="application/json" id="qa-summary">${jsonForScript(summary)}</script>
<script>${PAGE_SCRIPT}</script>
</body>
</html>
`;
}

// ---- File wrapper ------------------------------------------------------------
// The rendered video the page plays: `video` when given, else qa.render.file
// (absolute, or relative to the QA directory). Its digest is compared with the
// one qa.json recorded (skipped when the caller already verified it).
async function resolveVideo(qaDir, qa, video, knownSha256) {
  qa = obj(qa);
  const recorded = str(obj(qa.render).file);
  const file = video ? path.resolve(video) : recorded ? path.resolve(qaDir, recorded) : null;
  if (!file) return { href: null, video: { state: 'missing', file: null } };
  const stat = await fs.stat(file).catch(() => null);
  if (!stat?.isFile()) return { href: null, video: { state: 'missing', file } };
  const expected = str(obj(qa.render).sha256);
  const state = !expected ? 'unchecked' : (knownSha256 ?? await digest(file)) === expected ? 'match' : 'mismatch';
  return { href: relativeHref(qaDir, file), video: { state, file } };
}

async function missingFiles(qaDir, qa) {
  qa = obj(qa);
  const files = [...arr(qa.samples).map(s => obj(s).file), ...arr(qa.boundary_clips).map(c => obj(c).file), obj(qa.contact_sheet).file].filter(str);
  const present = await Promise.all(files.map(file => fs.stat(path.resolve(qaDir, file)).then(s => s.isFile(), () => false)));
  return new Set(files.filter((_, i) => !present[i]));
}

// Sign-off of this qa.json recorded in <production>/production.json (read only;
// a missing or invalid file is reported on the page, never thrown).
async function readSignOff(production, qaDir, qaSha256) {
  let data;
  try { data = JSON.parse(await fs.readFile(path.join(production, 'production.json'), 'utf8')); } catch (error) {
    return { state: 'unreadable', error: error.code === 'ENOENT' ? '文件不存在' : error.message };
  }
  // Real paths on both sides, so a symlinked prefix (macOS /var → /private/var) still relates them.
  const real = file => fs.realpath(file).catch(() => path.resolve(file));
  const qaPath = path.relative(await real(production), path.join(await real(qaDir), 'qa.json')).split(path.sep).join('/');
  return signOffFrom(data, qaPath, qaSha256);
}

// HTML for a QA directory. qaText: the exact qa.json bytes (a Buffer or the
// string written as UTF-8; digested into the page for traceability); qa
// defaults to their parse. qaSha256 skips re-hashing when the caller has it.
export async function reviewPageFor(qaDir, { qaText, qa = JSON.parse(qaText), qaSha256 = sha256(qaText), video = null, videoSha256 = null, production = null, generatedAt = new Date().toISOString() } = {}) {
  const { href, video: videoState } = await resolveVideo(qaDir, qa, video, videoSha256);
  production = production ? path.resolve(production) : null;
  return renderReviewPage(qa, { qaDir, videoHref: href, video: videoState, qaSha256, generatedAt,
    production, approveScript: existsSync(APPROVE_SCRIPT) ? APPROVE_SCRIPT : 'scripts/creative_craft.py',
    missingFiles: await missingFiles(qaDir, qa), signOff: production ? await readSignOff(production, qaDir, qaSha256) : null });
}

// Writes <qaDir>/review.html atomically (temporary file, then rename). Only this
// derived file is ever replaced: qa.json, frames, clips and the contact sheet
// are evidence and stay untouched. A symlinked or non-file review.html is refused.
export async function writeReviewPage(qaDir, html) {
  const target = path.join(qaDir, REVIEW_PAGE);
  const stat = await fs.lstat(target).catch(e => { if (e.code !== 'ENOENT') throw e; return null; });
  if (stat && !stat.isFile()) throw new Error(`${REVIEW_PAGE} exists and is not a regular file: ${target}`);
  const temp = path.join(qaDir, `.${REVIEW_PAGE}.${randomUUID()}`);
  await fs.writeFile(temp, html, { flag: 'wx' });
  try { await fs.rename(temp, target); } catch (error) { await fs.rm(temp, { force: true }); throw error; }
  return target;
}

// CLI review-page: regenerate review.html from the current qa.json (e.g. after
// the review was filled in).
export async function reviewPage(qaDir, { video = null, production = null } = {}) {
  // Same symlink policy as qa: the page is only written through regular paths.
  qaDir = await safePath(qaDir);
  const qaBytes = await fs.readFile(path.join(qaDir, 'qa.json')), qaSha256 = sha256(qaBytes);
  let qa;
  try { qa = JSON.parse(qaBytes.toString('utf8')); } catch (error) { throw new Error(`qa.json is not valid JSON: ${error.message}`); }
  const html = await reviewPageFor(qaDir, { qaText: qaBytes, qa, qaSha256, video, production });
  const file = await writeReviewPage(qaDir, html);
  return { status: 'written', file, qa_id: obj(qa).qa_id ?? null, qa_sha256: qaSha256 };
}

export function parseReviewPageArgs(argv) {
  const [qaDir, ...rest] = argv, options = {};
  if (!qaDir || qaDir.startsWith('--') || rest.length % 2) throw new Error('Usage: review-page QA_DIR [--video FILE] [--production DIR]');
  for (let i = 0; i < rest.length; i += 2) {
    if (rest[i] === '--video') options.video = rest[i + 1];
    else if (rest[i] === '--production') options.production = rest[i + 1];
    else throw new Error(`Unknown review-page option: ${rest[i]}`);
  }
  return { qaDir, options };
}
