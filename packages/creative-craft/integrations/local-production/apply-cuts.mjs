// Apply the decisions of a cut-suggestions file (suggest-cuts.mjs): every
// open decision (beats[].conflicts[] of a needs_decision beat) is resolved by
// an explicit --choose BEAT.EDGE=OPTION, the edge takes that option's frame
// (options already carry frame and frame-midpoint seconds), and the items are
// laid back to back again. Nothing is chosen silently: an unresolved decision,
// an unknown beat / edge / option, a choice for an edge without a decision or
// for a beat without a usable range, and an in choice other than the draft's
// when the out-point depends on it are refused. The output holds
//   - items: EditDocument v2 media items (no needs_decision / decisions keys);
//   - plan_beats: production-plan beats (source_kind footage, selection with the
//     ASR phrases inside the final range as evidence, status candidate), with
//     role / purpose / requirement / hard_constraints only when BEATS.json gave
//     them; missing ones are listed, never invented. Every beat is checked
//     against production-plan.schema.json ($defs.beat) and its selection rules;
//     problems are reported (plan_status, plan_errors), the items are written anyway.
import { randomUUID } from 'node:crypto';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { PLAN_FIELDS, SUGGEST_SCHEMA, RULES, backToBack } from './suggest-cuts.mjs';
import { sha256 } from './content-store.mjs';
import { round6 } from './burned-captions.mjs';
import { DIP } from './cut-fragments.mjs';
import { schemaErrors } from './json-schema.mjs';
import { prepareProject, readJson } from './project.mjs';

export const APPLIED_SCHEMA = 'creative-craft.applied-cuts.v1';
export const PLAN_SCHEMA_FILE = fileURLToPath(new URL('../../skills/creative-craft/schemas/production-plan.schema.json', import.meta.url));
// Copied from the Python source of truth: SELECTION_EVIDENCE_TOLERANCE_SECONDS
// in skills/creative-craft/scripts/creative_craft_contracts.py (keep in step).
const EVIDENCE_TOLERANCE = 2.0;

// "hook.out=keep_speech" → {beat, edge, option}; repeated choices for one edge are refused.
export function parseChoices(values) {
  const choices = new Map();
  for (const value of values) {
    const m = /^([^=]+)\.(in|out)=([a-z_]+)$/.exec(value);
    if (!m) throw new Error(`--choose needs BEAT.EDGE=OPTION with EDGE in or out (${value})`);
    const key = `${m[1]}.${m[2]}`;
    if (choices.has(key)) throw new Error(`--choose ${key} given twice`);
    choices.set(key, { beat: m[1], edge: m[2], option: m[3] });
  }
  return choices;
}

// Phrases of the final range: those with ≥ phrase_cover of their duration
// inside [from, to] (the range-beat rule of suggest-cuts). option_phrases holds
// every phrase any option reaches; files from before it fall back to the
// draft's phrases plus the phrases the drop options name.
function phrasesIn(beat, from, to, cover) {
  const listed = beat.evidence?.option_phrases ?? [...(beat.evidence?.phrases ?? []),
    ...(beat.conflicts ?? []).flatMap(c => (c.options ?? []).flatMap(o => o.dropped_phrase ? [o.dropped_phrase] : []))];
  const unique = [...new Map(listed.map(ph => [ph.index ?? `${ph.start}-${ph.end}`, ph])).values()].sort((a, b) => a.start - b.start);
  return unique.filter(ph => ph.end > ph.start && Math.min(ph.end, to) - Math.max(ph.start, from) >= cover * (ph.end - ph.start) - 1e-9);
}

const evidenceMethod = source => source === 'asr' ? 'local whisper.cpp ASR phrase (footage-analysis speech.phrases; token-timestamp times, approximate)'
  : source === 'transcript' ? 'transcript phrase (footage-analysis speech.phrases from a transcribe output)' : `phrase (speech source ${source})`;

// The selection rules of the plan's semantic validation that the schema cannot
// express, copied from validate_production_plan in
// skills/creative-craft/scripts/creative_craft_contracts.py (the source of truth).
function selectionErrors(selection) {
  if (!selection) return [];
  const { source_start_seconds: start, source_end_seconds: end } = selection, errors = [];
  if (!(end > start)) errors.push('selection end must be after start');
  selection.evidence.forEach((e, i) => {
    if (e.end_seconds < e.start_seconds) errors.push(`evidence[${i}] end precedes start`);
    if (!(e.start_seconds <= end + EVIDENCE_TOLERANCE && e.end_seconds >= start - EVIDENCE_TOLERANCE)) errors.push(`evidence[${i}] lies outside the selected range (±${EVIDENCE_TOLERANCE} s)`);
  });
  return errors;
}

export function applyCuts(cuts, choices = new Map(), planSchema) {
  if (cuts?.schema !== SUGGEST_SCHEMA) throw new Error(`Cuts must be ${SUGGEST_SCHEMA}`);
  const beats = new Map(cuts.beats.map(b => [b.id, b])), cover = cuts.rules?.phrase_cover ?? RULES.phrase_cover;
  for (const { beat, edge, option } of choices.values()) {
    const b = beats.get(beat);
    if (!b) throw new Error(`--choose ${beat}.${edge}: no beat ${beat} (beats: ${[...beats.keys()].join(', ')})`);
    const conflict = (b.conflicts ?? []).find(c => c.edge === edge);
    if (!conflict) throw new Error(`--choose ${beat}.${edge}: beat ${beat} has no open decision on its ${edge}-point`);
    if (!conflict.options.some(o => o.id === option)) throw new Error(`--choose ${beat}.${edge}=${option}: unknown option (options: ${conflict.options.map(o => o.id).join(', ')})`);
    if (!b.in) throw new Error(`--choose ${beat}.${edge}: beat ${beat} has no usable range (${b.status}${b.error ? `: ${b.error}` : ''}), so no choice can apply; re-run suggest-cuts with an adjusted range`);
  }
  // The out-point and its options were computed after the draft's in-point
  // (the out rules only look at changes after it, the drop option at the
  // draft's phrases). With another in option they may no longer hold: refuse
  // when the beat has an out decision or its out lies within reach of either
  // in-point: the shot rule looks shot_window back and the dip rule up to a
  // dip's length (DIP.max_seconds), both bounded by the in-point; recomputing
  // needs the analysis (re-run suggest-cuts).
  const reach = (cuts.rules?.shot_window ?? RULES.shot_window) + DIP.max_seconds;
  for (const { beat, edge, option } of choices.values()) {
    const b = beats.get(beat), conflict = b.conflicts.find(c => c.edge === edge);
    if (edge !== 'in' || option === conflict.draft_uses) continue;
    const chosen = conflict.options.find(o => o.id === option), near = [b.in.source_seconds, chosen.seconds].some(t => b.out.source_seconds - t <= reach + 1e-9);
    if (b.conflicts.some(c => c.edge === 'out') || near) {
      throw new Error(`--choose ${beat}.in=${option}: the out-point${b.conflicts.some(c => c.edge === 'out') ? ' and its options were' : ' was'} computed after the draft's in option ${conflict.draft_uses} and may not hold for ${option}; re-run suggest-cuts with the beat range adjusted to that in-point (e.g. from: ${chosen.seconds})`);
    }
  }
  const open = cuts.beats.flatMap(b => b.status !== 'needs_decision' ? [] : (b.conflicts ?? []).filter(c => c.edge !== 'text' && !choices.has(`${b.id}.${c.edge}`))
    .map(c => `${b.id}.${c.edge} (options: ${c.options.map(o => o.id).join(', ')}; draft uses ${c.draft_uses})`));
  if (open.length) throw new Error(`Unresolved decision(s): ${open.join('; ')}. Choose each with --choose BEAT.EDGE=OPTION`);

  const fps = cuts.draft.canvas_fps, draft = new Map(cuts.draft.items.map(i => [i.id, i])), notes = [], applied = [], decisions = [];
  // Every decided conflict (BEATS.json prefer or --choose) with the cut-rule
  // findings its option accepts; render QA (--decisions) marks those accepted.
  const decided = (b, e, o, by) => decisions.push({ beat: b.id, edge: e, asset_id: draft.get(b.id)?.asset_id ?? null, option: o.id, by, frame: o.frame, seconds: o.seconds, accepts: o.accepts ?? (o.id === 'keep_speech' ? null : []) });
  const ranges = cuts.beats.filter(b => b.in && draft.has(b.id)).map(b => {
    const edge = e => {
      const choice = choices.get(`${b.id}.${e}`), conflict = (b.conflicts ?? []).find(c => c.edge === e);
      if (!choice) {
        if (conflict?.decided_by) decided(b, e, conflict.options.find(x => x.id === conflict.draft_uses), conflict.decided_by);
        return { frame: b[e].frame, seconds: b[e].source_seconds };
      }
      const o = conflict.options.find(x => x.id === choice.option);
      decided(b, e, o, 'choice');
      applied.push({ beat: b.id, edge: e, option: o.id, frame: o.frame, seconds: o.seconds, draft_used: b.conflicts.find(c => c.edge === e).draft_uses });
      return { frame: o.frame, seconds: o.seconds };
    };
    const inPoint = edge('in'), outPoint = edge('out');
    if (outPoint.frame <= inPoint.frame) throw new Error(`Beat ${b.id}: the chosen out frame ${outPoint.frame} is not after the in frame ${inPoint.frame}`);
    const { needs_decision: _n, decisions: _d, ...item } = draft.get(b.id);
    // Only a measured volume can be stale (no audio or < 400 ms gives none).
    if ((inPoint.frame !== b.in.frame || outPoint.frame !== b.out.frame) && Number.isFinite(item.volume) && b.volume?.measured_lufs != null) notes.push(`${b.id}: volume ${item.volume} was measured on the draft range ${b.in.source_seconds}–${b.out.source_seconds} s; the chosen range differs, listen to the level`);
    return { draftItem: item, beat: b, inPoint, outPoint };
  });
  const slots = backToBack(ranges.map(r => [r.inPoint.seconds, r.outPoint.seconds]), fps);
  const items = ranges.map((r, i) => ({ ...r, item: { ...r.draftItem, ...slots[i], source_in_seconds: r.inPoint.seconds } }));
  const skipped = cuts.beats.filter(b => !b.in).map(b => ({ id: b.id, status: b.status, error: b.error ?? null }));
  if (!items.length) throw new Error('No beat has a usable range');
  if (items.some(({ item }) => item.asset_id === 'ASSET_ID')) notes.push('asset_id is the placeholder ASSET_ID (BEATS.json gave none): replace it in items and plan_beats');

  const method = evidenceMethod(cuts.analysis?.speech_source);
  const planBeats = [], incomplete = [], invalid = [];
  for (const { item, beat: b, inPoint, outPoint } of items) {
    const phrases = phrasesIn(b, inPoint.seconds, outPoint.seconds, cover);
    const choiceText = applied.filter(a => a.beat === b.id).map(a => `${a.edge}=${a.option}`).join(', ');
    const selection = { asset_ref: item.asset_id, source_start_seconds: inPoint.seconds, source_end_seconds: outPoint.seconds,
      evidence: phrases.map(ph => ({ modality: 'asr', start_seconds: ph.start, end_seconds: ph.end, excerpt: ph.text, raw_score: null, method })),
      reason: `suggest-cuts ${[b.prefer ? `conflicts decided up front by BEATS.json prefer ${b.prefer}` : '', choiceText ? `decided by choice (${choiceText})` : ''].filter(Boolean).join('; ') || 'suggested'}; cut points from energy valleys and caption / shot / dip rules`,
      status: 'candidate' };
    const given = keys => Object.fromEntries(keys.filter(k => k in b).map(k => [k, b[k]]));
    const beat = { id: b.id, ...given(['role', 'purpose']), duration_seconds: round6(item.frames / fps), source_kind: 'footage',
      ...given(['requirement', 'hard_constraints']), selection, generation_ref: null, locked: false };
    const missing = PLAN_FIELDS.filter(k => !(k in b));
    if (!phrases.length) missing.push('selection.evidence (no ASR phrase inside the range)');
    if (missing.length) incomplete.push({ id: b.id, missing });
    // Plan problems (a beat id the plan pattern refuses, > 600 s, an empty
    // excerpt, …) are reported, never fatal: the items stay usable.
    if (planSchema) {
      let errors;
      try {
        errors = [...schemaErrors(beat, planSchema.$defs.beat, planSchema), ...selectionErrors(selection)]
          .filter(e => !/: missing (role|purpose|requirement|hard_constraints)$/.test(e) && !(/selection\.evidence: needs at least 1/.test(e) && !phrases.length));
      } catch (error) { errors = [`schema check failed: ${error.message}`]; }
      if (errors.length) invalid.push({ id: b.id, errors });
    }
    planBeats.push(beat);
  }
  const planStatus = !planSchema ? 'unchecked' : invalid.length ? 'invalid' : incomplete.length ? 'incomplete' : 'valid';
  return {
    schema: APPLIED_SCHEMA, analysis: cuts.analysis, canvas_fps: fps, choices: applied, decisions, items: items.map(i => i.item), plan_beats: planBeats, plan_status: planStatus,
    ...(invalid.length ? { plan_errors: invalid } : {}), ...(incomplete.length ? { plan_beats_incomplete: incomplete } : {}), ...(skipped.length ? { skipped } : {}), notes,
    note: 'items: EditDocument v2 media items, back to back from frame 0 at canvas_fps, frames = max(1, round((out − in) × canvas_fps)). plan_beats: production-plan.v1 beats (selection status candidate); plan_status valid | incomplete (fields listed in plan_beats_incomplete were not given in BEATS.json) | invalid (plan_errors: the beat does not match production-plan.schema.json); the items are usable either way.',
  };
}

// Paired output flags: [template flag, output flag, option keys].
const WRITE_PAIRS = [['--plan-template', '--plan-out', 'planTemplate', 'planOut'], ['--spec-template', '--spec-out', 'specTemplate', 'specOut']];
export const APPLY_USAGE = 'apply-cuts needs CUTS.json NEW_OUT.json [--choose BEAT.EDGE=OPTION]... [--plan-template PLAN.json --plan-out NEW_PLAN.json] [--spec-template SPEC.json --spec-out NEW_SPEC.json]';
export function parseApplyArgs(argv) {
  const [cuts, output, ...rest] = argv, choose = [], write = {};
  if (!cuts || !output || cuts.startsWith('--') || output.startsWith('--') || rest.length % 2) throw new Error(APPLY_USAGE);
  const keyOf = new Map(WRITE_PAIRS.flatMap(([t, o, tk, ok]) => [[t, tk], [o, ok]]));
  for (let i = 0; i < rest.length; i += 2) {
    const [flag, value] = [rest[i], rest[i + 1]];
    if (value.startsWith('--')) throw new Error(`Missing value for ${flag}. ${APPLY_USAGE}`);
    if (flag === '--choose') choose.push(value);
    else if (keyOf.has(flag) && !(keyOf.get(flag) in write)) write[keyOf.get(flag)] = value;
    else throw new Error(`Unknown or repeated apply-cuts option ${flag}. ${APPLY_USAGE}`);
  }
  for (const [t, o, tk, ok] of WRITE_PAIRS) if ((tk in write) !== (ok in write)) throw new Error(`${t} and ${o} go together`);
  return { cuts, output, choices: parseChoices(choose), write };
}

// A production plan from a hand-written template (plan_id, brief_ref, output,
// delivery_promises, …) with its beats replaced by the applied ones; refused
// unless every beat is complete, names a real asset and the whole plan matches
// the schema (semantic checks run at video-record / validate).
export function planFrom(template, applied, planSchema) {
  if (applied.plan_status !== 'valid') {
    const why = [...(applied.plan_errors ?? []).map(b => `${b.id}: ${b.errors.join('; ')}`), ...(applied.plan_beats_incomplete ?? []).map(b => `${b.id}: missing ${b.missing.join(', ')}`)];
    throw new Error(`Plan beats are ${applied.plan_status}, so no plan is written: ${why.join(' | ')}`);
  }
  if (applied.plan_beats.some(b => b.selection?.asset_ref === 'ASSET_ID')) throw new Error('Plan beats name the placeholder asset ASSET_ID: set asset_id in BEATS.json and rerun suggest-cuts');
  const plan = { ...template, beats: applied.plan_beats };
  const errors = schemaErrors(plan, planSchema, planSchema);
  if (errors.length) throw new Error(`Plan template with the applied beats does not match production-plan.schema.json: ${errors.slice(0, 5).join('; ')}`);
  return plan;
}

// A v2 spec from a template (project_id, canvas, assets, tracks, other items):
// the MEDIA items of the applied track are replaced by the applied items; other
// items (graphics on that track, other tracks) are kept, and the ones that now
// run past the new main-track end are named in notes. Refused when the track is
// missing or locked, an asset is unknown or the template's fps differs from the
// fps the items were laid out at. Then validated exactly as createProject does
// (prepareProject: imports probed, nothing written).
export async function specFrom(template, applied, prepare = prepareProject) {
  const track = applied.items[0]?.track_id;
  if (!track) throw new Error('No applied items to write into a spec');
  const target = (template.tracks ?? []).find(t => t.id === track);
  if (!target) throw new Error(`Spec template has no track ${track} (tracks: ${(template.tracks ?? []).map(t => t.id).join(', ')})`);
  if (target.locked) throw new Error(`Spec template track ${track} is locked; unlock it to replace its items`);
  if (template.canvas?.fps !== applied.canvas_fps) throw new Error(`Spec template canvas.fps ${template.canvas?.fps} differs from the ${applied.canvas_fps} fps the items were laid out at (set canvas_fps in BEATS.json or the template fps)`);
  const assets = new Set((template.assets ?? []).map(a => a.id));
  const missing = [...new Set(applied.items.map(i => i.asset_id))].filter(id => !assets.has(id));
  if (missing.length) throw new Error(`Spec template has no asset ${missing.join(', ')}${missing.includes('ASSET_ID') ? ' (set asset_id in BEATS.json and rerun suggest-cuts)' : ''}`);
  // The applied items fill the track back to back, so anything else on it would
  // overlap them; and a kept item linked to that track's media was timed against
  // the old source ranges. Both are refused rather than written stale.
  const onTrack = (template.items ?? []).filter(i => i.track_id === track && i.kind !== 'media');
  if (onTrack.length) throw new Error(`Spec template has non-media item(s) on ${track} (${onTrack.map(i => i.id).join(', ')}): the applied media fill it from frame 0; move them to another track`);
  const kept = (template.items ?? []).filter(i => i.track_id !== track);
  const replaced = new Set([...(template.items ?? []).filter(i => i.track_id === track).map(i => i.id), ...applied.items.map(i => i.id)]);
  const linked = kept.filter(i => replaced.has(i.link?.item_id));
  if (linked.length) throw new Error(`Spec template item(s) ${linked.map(i => i.id).join(', ')} link to ${track} media that apply-cuts replaces; remove them and re-time captions for the new cut`);
  const spec = { ...template, items: [...kept, ...applied.items] };
  await prepare(spec);
  const end = Math.max(...applied.items.map(i => i.start_frame + i.frames));
  const late = kept.filter(i => Number.isInteger(i.start_frame) && Number.isInteger(i.frames) && i.start_frame + i.frames > end);
  return { spec, notes: late.length ? [`kept item(s) ${late.map(i => i.id).join(', ')} run past the new main-track end (frame ${end}); retime them`] : [] };
}

// Every output is new; all are built and checked first, then written to
// temporary files and renamed into place (removed again if any step fails).
export async function applyCutsFile(cutsFile, output, choices, { planTemplate, planOut, specTemplate, specOut } = {}) {
  const outputs = [output, planOut, specOut].filter(Boolean);
  if (!outputs.every(o => o.endsWith('.json'))) throw new Error('Outputs must be .json files');
  // Same paths are refused here; two names of one file on a case-insensitive
  // file system meet EEXIST when placed (and everything is removed again).
  if (new Set(outputs.map(o => path.resolve(o))).size !== outputs.length) throw new Error('Outputs must be different files');
  for (const o of outputs) {
    if (await fs.lstat(o).then(() => true, () => false)) throw new Error(`Output already exists: ${o}`);
    if (!(await fs.stat(path.dirname(path.resolve(o))).catch(() => null))?.isDirectory()) throw new Error(`Output directory does not exist: ${path.dirname(o)}`);
  }
  const bytes = await fs.readFile(cutsFile), planSchema = await readJson(PLAN_SCHEMA_FILE);
  const result = applyCuts(JSON.parse(bytes.toString('utf8')), choices, planSchema);
  const plan = planOut ? planFrom(await readJson(planTemplate), result, planSchema) : null;
  const built = specOut ? await specFrom(await readJson(specTemplate), result) : null;
  result.notes.push(...(built?.notes ?? []));
  const doc = { ...result, cuts: { path_basename: path.basename(cutsFile), sha256: sha256(bytes) } };
  const files = [[output, doc], ...(plan ? [[planOut, plan]] : []), ...(built ? [[specOut, built.spec]] : [])];
  const temps = files.map(([file]) => path.join(path.dirname(file), `.${path.basename(file)}.${randomUUID()}`)), placed = [];
  try {
    for (const [i, [, value]] of files.entries()) await fs.writeFile(temps[i], JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
    // link() never replaces an existing file (EEXIST), unlike rename().
    for (const [i, [file]] of files.entries()) {
      await fs.link(temps[i], file).catch(error => { throw error.code === 'EEXIST' ? new Error(`Output already exists: ${file}`) : error; });
      placed.push(file);
    }
    await Promise.all(temps.map(f => fs.rm(f, { force: true })));
  } catch (error) {
    await Promise.all([...temps, ...placed].map(f => fs.rm(f, { force: true })));
    throw error;
  }
  return { status: 'applied', plan_status: result.plan_status, output, ...(plan ? { plan: planOut } : {}), ...(built ? { spec: specOut } : {}), choices: result.choices.map(c => `${c.beat}.${c.edge}=${c.option}`),
    items: result.items.map(i => ({ id: i.id, start_frame: i.start_frame, frames: i.frames, source_in_seconds: i.source_in_seconds })),
    ...(result.plan_errors ? { plan_errors: result.plan_errors.map(b => `${b.id}: ${b.errors.join('; ')}`) } : {}),
    ...(result.plan_beats_incomplete ? { plan_beats_incomplete: result.plan_beats_incomplete.map(b => `${b.id}: missing ${b.missing.join(', ')} (not invented; add them to BEATS.json and rerun suggest-cuts, or fill them in the plan)`) } : {}),
    ...(result.skipped ? { skipped: result.skipped } : {}), notes: result.notes };
}
