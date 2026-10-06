import { createHash } from 'node:crypto';
import { fail, id, integer, keys, number, text, validateNewAssetOrigin } from './edit-document.mjs';
import { outputFrames, round9, speedOf } from './timeline.mjs';

// Canonical JSON: object keys sorted recursively, no whitespace. The batch's
// operations_sha256 is SHA-256 over this UTF-8 string.
export function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonicalJson(value[k])}`).join(',')}}`;
  return JSON.stringify(value);
}
export const operationsSha256 = operations => createHash('sha256').update(canonicalJson(operations)).digest('hex');

const findTrack = (doc, key) => doc.tracks.find(t => t.id === key) ?? fail(`Unknown track: ${key}`);
const findItem = (doc, key) => doc.items.find(i => i.id === key) ?? fail(`Unknown item: ${key}`);
const unlocked = (doc, key) => { if (findTrack(doc, key).locked) fail(`Track is locked: ${key}`); };
const linkedTo = (doc, key) => doc.items.filter(i => i.kind === 'caption' && i.link?.item_id === key);
const freshItemId = (doc, key) => { if (!id(key) || doc.items.some(i => i.id === key)) fail(`Invalid or duplicate item id: ${key}`); };
const plainObject = value => value && typeof value === 'object' && !Array.isArray(value);
function removeItems(doc, doomed) {
  for (const item of doomed) unlocked(doc, item.track_id);
  doc.items = doc.items.filter(i => !doomed.includes(i));
}

// Applies one non-revert batch to a clone of `base`. add_asset only probes via
// `importAsset`; copying is the caller's job after the whole batch validates.
export async function applyOperations(base, operations, { importAsset, imports }) {
  const doc = structuredClone(base), fps = doc.canvas.fps;
  for (const op of operations) {
    if (!plainObject(op)) fail('Invalid operation');
    if (op.type === 'add_asset') {
      keys(op, ['type', 'id', 'path', 'origin']);
      if (!id(op.id) || doc.assets.some(a => a.id === op.id) || typeof op.path !== 'string') fail(`Invalid or duplicate asset: ${op.id}`);
      const origin = op.origin ?? { kind: 'import' };
      validateNewAssetOrigin(origin);
      const imported = await importAsset(op.path);
      imports.push(imported);
      doc.assets.push({ id: op.id, ...imported.asset, origin: { ...origin } });
    } else if (op.type === 'add_track') {
      keys(op, ['type', 'track', 'index']);
      if (!plainObject(op.track) || doc.tracks.some(t => t.id === op.track.id)) fail(`Invalid or duplicate track: ${op.track?.id}`);
      const index = op.index ?? doc.tracks.length;
      if (!integer(index, 0, doc.tracks.length)) fail('Invalid track index');
      doc.tracks.splice(index, 0, { locked: false, ...structuredClone(op.track) });
    } else if (op.type === 'edit_track') {
      keys(op, ['type', 'track_id', 'locked', 'name', 'duck']);
      const track = findTrack(doc, op.track_id);
      if (!['locked', 'name', 'duck'].some(k => k in op)) fail('edit_track requires locked, name or duck');
      if ('locked' in op) { if (typeof op.locked !== 'boolean') fail('Invalid locked flag'); track.locked = op.locked; }
      if ('name' in op) { if (!text(op.name)) fail('Invalid track name'); track.name = op.name; }
      if ('duck' in op) {
        // Ducking changes how a track's items sound, so a locked track keeps its duck.
        unlocked(doc, track.id);
        if (op.duck === null) delete track.duck;
        else if (plainObject(op.duck)) track.duck = structuredClone(op.duck); // Shape and references: validateV2.
        else fail('Invalid duck');
      }
    } else if (op.type === 'add_item') {
      keys(op, ['type', 'item']);
      if (!plainObject(op.item)) fail('Invalid item');
      freshItemId(doc, op.item.id);
      unlocked(doc, op.item.track_id);
      doc.items.push(structuredClone(op.item));
    } else if (op.type === 'remove_item') {
      keys(op, ['type', 'item_id', 'ripple']);
      const item = findItem(doc, op.item_id);
      if ('ripple' in op && typeof op.ripple !== 'boolean') fail('Invalid ripple flag');
      if (op.ripple) {
        if (item.link) fail('Linked captions have no output time to ripple');
        const end = item.start_frame + item.frames;
        for (const other of doc.items) {
          if (other.track_id === item.track_id && other !== item && !other.link && other.start_frame >= end) other.start_frame -= item.frames;
        }
      }
      // Linked captions cannot outlive their media item.
      removeItems(doc, [item, ...linkedTo(doc, item.id)]);
    } else if (op.type === 'move_item') {
      keys(op, ['type', 'item_id', 'track_id', 'start_frame']);
      const item = findItem(doc, op.item_id);
      if (!('track_id' in op) && !('start_frame' in op)) fail('move_item requires track_id or start_frame');
      unlocked(doc, item.track_id);
      if ('track_id' in op) {
        const from = findTrack(doc, item.track_id), to = findTrack(doc, op.track_id);
        if (to.kind !== from.kind) fail(`Cannot move ${from.kind} item to ${to.kind} track`);
        unlocked(doc, to.id);
        item.track_id = to.id;
      }
      if ('start_frame' in op) {
        if (item.link) fail('Linked captions follow their media item; move the media item');
        if (!integer(op.start_frame, 0, 600 * fps)) fail('Invalid start_frame');
        item.start_frame = op.start_frame;
      }
    } else if (op.type === 'trim_item') {
      keys(op, ['type', 'item_id', 'head_frames', 'tail_frames', 'slip_seconds']);
      const item = findItem(doc, op.item_id);
      if (item.link) fail('Linked captions follow their media item; trim the media item');
      unlocked(doc, item.track_id);
      if (!['head_frames', 'tail_frames', 'slip_seconds'].some(k => k in op)) fail('trim_item requires head_frames, tail_frames or slip_seconds');
      for (const k of ['head_frames', 'tail_frames']) if (k in op && !integer(op[k], -600 * fps, 600 * fps)) fail(`Invalid ${k}`);
      // Fades and transition_in are kept as authored; the batch result must still
      // validate (fades fit, crossfade overlap exact), else adjust them in the batch.
      if ('head_frames' in op) {
        item.start_frame += op.head_frames;
        item.frames -= op.head_frames;
        if (item.kind === 'media') item.source_in_seconds = round9(item.source_in_seconds + op.head_frames / fps * speedOf(item));
      }
      if ('tail_frames' in op) item.frames -= op.tail_frames;
      if ('slip_seconds' in op) {
        if (item.kind !== 'media' || !number(op.slip_seconds, -1800, 1800)) fail('slip_seconds applies to media items only');
        item.source_in_seconds = round9(item.source_in_seconds + op.slip_seconds);
      }
    } else if (op.type === 'split_item') {
      keys(op, ['type', 'item_id', 'at_frame', 'new_item_id']);
      const item = findItem(doc, op.item_id);
      if (item.link) fail('Linked captions follow their media item; split the media item');
      unlocked(doc, item.track_id);
      freshItemId(doc, op.new_item_id);
      const head = op.at_frame - item.start_frame;
      if (!Number.isInteger(op.at_frame) || head < 1 || head >= item.frames) fail('Split frame must be strictly inside the item');
      const tail = { ...structuredClone(item), id: op.new_item_id, start_frame: op.at_frame, frames: item.frames - head };
      // Rule: the head keeps what happens at the item's start (fade_in,
      // transition_in), the tail keeps what happens at its end (fade_out); the
      // new cut between them is a hard cut. Speed, volume and visuals copy to both.
      delete item.fade_out_frames;
      delete tail.fade_in_frames;
      delete tail.transition_in;
      if (item.kind === 'media') {
        tail.source_in_seconds = round9(item.source_in_seconds + head / fps * speedOf(item));
        // Rule: a linked caption belongs to the half whose source window holds
        // its source_from; the other half never shows it (no duplication).
        for (const caption of linkedTo(doc, item.id)) {
          if (caption.link.source_from >= tail.source_in_seconds - 1e-9) { unlocked(doc, caption.track_id); caption.link.item_id = tail.id; }
        }
      }
      item.frames = head;
      doc.items.splice(doc.items.indexOf(item) + 1, 0, tail);
    } else if (op.type === 'replace_media') {
      keys(op, ['type', 'item_id', 'asset_id', 'source_in_seconds', 'captions']);
      const item = findItem(doc, op.item_id);
      if (item.kind !== 'media') fail('replace_media applies to media items');
      unlocked(doc, item.track_id);
      if (!doc.assets.some(a => a.id === op.asset_id)) fail(`Unknown asset: ${op.asset_id}`);
      item.asset_id = op.asset_id;
      if ('source_in_seconds' in op) item.source_in_seconds = op.source_in_seconds;
      // Old dialogue never sticks to new media; new captions must be explicit.
      removeItems(doc, linkedTo(doc, item.id));
      if ('captions' in op && (!Array.isArray(op.captions) || op.captions.length > 500)) fail('Invalid captions');
      for (const caption of op.captions ?? []) {
        keys(caption, ['id', 'track_id', 'text', 'style', 'source_from', 'source_to']);
        freshItemId(doc, caption.id);
        unlocked(doc, caption.track_id);
        doc.items.push({ id: caption.id, track_id: caption.track_id, kind: 'caption', text: caption.text,
          ...('style' in caption ? { style: caption.style } : {}),
          link: { item_id: item.id, source_from: caption.source_from, source_to: caption.source_to } });
      }
    } else if (op.type === 'set_item_props') {
      keys(op, ['type', 'item_id', 'props']);
      keys(op.props, ['volume', 'fit', 'opacity', 'transform', 'text', 'style', 'speed', 'fade_in_frames', 'fade_out_frames', 'transition_in', 'vars']);
      const item = findItem(doc, op.item_id);
      unlocked(doc, item.track_id);
      if (!Object.keys(op.props).length) fail('set_item_props requires props');
      for (const [k, value] of Object.entries(op.props)) {
        if (value === null) {
          if (['volume', 'text', 'vars'].includes(k)) fail(`${k} cannot be removed`);
          delete item[k];
        } else item[k] = structuredClone(value);
      }
    } else if (op.type === 'revert_to' || op.type === 'rebind_template') fail(`${op.type} must be the only operation in its batch`);
    else fail(`Unknown edit operation: ${op.type}`);
  }
  return doc;
}

// Machine-readable review of what a batch would change.
export function diffDocuments(before, after) {
  const map = list => new Map(list.map(x => [x.id, x]));
  const compare = (a, b) => {
    const left = map(a), right = map(b);
    return { added: [...right.keys()].filter(k => !left.has(k)), removed: [...left.keys()].filter(k => !right.has(k)),
      changed: [...right.keys()].filter(k => left.has(k) && canonicalJson(left.get(k)) !== canonicalJson(right.get(k))) };
  };
  // Template bindings: what this revision would pin, drop or rebind.
  const pins = compare(before.graphic_templates ?? [], after.graphic_templates ?? []), pin = list => new Map(list.map(b => [b.id, { version: b.version, sha256: b.sha256 }]));
  const [was, now] = [pin(before.graphic_templates ?? []), pin(after.graphic_templates ?? [])];
  return { items: compare(before.items, after.items), tracks: compare(before.tracks, after.tracks),
    assets_added: compare(before.assets, after.assets).added,
    graphic_templates: { added: pins.added.map(id => ({ id, ...now.get(id) })), removed: pins.removed,
      changed: pins.changed.map(id => ({ id, from: was.get(id), to: now.get(id) })) },
    duration_frames: { before: outputFrames(before), after: outputFrames(after) } };
}
