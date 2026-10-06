// Load-time re-check of asset frame_rate (source frame alignment).
// frame_rate is recorded at import; a project imported by 0.6.0 can hold it on
// a source whose video does not start at media time 0 (the earliest stream
// start, e.g. an MKV/WebM with a negative audio start), where the truncation
// correction would aim at the wrong frame grid. loadProject decides, once per
// load, which assets' frame_rate applies: every asset with frame_rate is probed
// again (mediaZeroProblem, the import rule); a failing asset gets no
// correction (its items keep the written in-point, the renderer behaviour).
// The decision is bound to the loaded document (bindAlignment) and so reaches
// every compiledView of it (font planning and checks, compose, render); render
// receipts record it and QA compiles with the recorded one. The project files
// are never rewritten.
import { ffprobeJson } from './project.mjs';
import { mediaZeroProblem } from './source-frames.mjs';

// mediaZeroProblem per verified file: keyed by the file's real path and the
// sha256 its bytes were just checked against, so an entry is only reached by a
// caller whose own digest check of that same file passed (the caller hashes
// first; nothing here trusts an unchecked file). A probe in flight is shared
// only by callers holding the same verified key; a failed probe is not cached.
const PROBLEMS = new Map();
function problemOf(file, sha256) {
  const key = `${file}\0${sha256}`;
  if (!PROBLEMS.has(key)) {
    const pending = ffprobeJson(file).then(mediaZeroProblem);
    PROBLEMS.set(key, pending);
    pending.catch(() => PROBLEMS.delete(key));
  }
  return PROBLEMS.get(key);
}

// One entry per asset with frame_rate: { asset_id, frame_rate, applied: true }
// or { asset_id, frame_rate, applied: false, reason }. files: Map asset id →
// real path of the asset file whose digest matched asset.sha256 (verified by
// the caller). Probes run in parallel.
export async function frameAlignment(doc, files) {
  return Promise.all(doc.assets.filter(a => a.frame_rate).map(async asset => {
    if (!files.has(asset.id)) throw new Error(`Asset not verified: ${asset.id}`);
    const reason = await problemOf(files.get(asset.id), asset.sha256);
    return { asset_id: asset.id, frame_rate: asset.frame_rate, applied: !reason, ...(reason ? { reason } : {}) };
  }));
}

// The alignment of a document an edit batch builds from loaded ones. Every
// asset with frame_rate keeps the decision made for the same bytes (sha256)
// when its source document was loaded: sources is a list of [doc, alignment]
// (the base revision; the target of revert_to). An asset imported by this
// batch (sha256 in `imported`) was probed by the import rule a moment ago,
// which records frame_rate only when mediaZeroProblem finds nothing: applied.
export function carryAlignment(doc, sources, imported = new Set()) {
  const known = new Map();
  for (const [source, alignment] of sources) {
    for (const entry of alignment ?? []) known.set(source.assets.find(a => a.id === entry.asset_id).sha256, entry);
  }
  return doc.assets.filter(a => a.frame_rate).map(asset => {
    const entry = imported.has(asset.sha256) ? { applied: true } : known.get(asset.sha256);
    if (!entry) throw new Error(`Frame alignment of asset ${asset.id} was not determined`);
    return { asset_id: asset.id, frame_rate: asset.frame_rate, applied: entry.applied, ...(entry.reason ? { reason: entry.reason } : {}) };
  });
}

// Renders made before receipts recorded frame_alignment (0.6.0) applied every
// recorded frame_rate: the alignment QA assumes for them.
export const legacyAlignment = doc => doc.assets.filter(a => a.frame_rate).map(a => ({ asset_id: a.id, frame_rate: a.frame_rate, applied: true }));
