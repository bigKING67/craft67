import { createHash, randomUUID } from 'node:crypto';
import { createReadStream } from 'node:fs';
import * as fs from 'node:fs/promises';
import path from 'node:path';

// Project files are written once and never replaced. Shared by revision
// publication, asset imports, bound graphic templates and the caption font.
const fail = message => { throw new Error(message); };
export const sha256 = value => createHash('sha256').update(value).digest('hex');

export async function digest(file) {
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(file)) hash.update(chunk);
  return hash.digest('hex');
}

// Places `bytes` (or a copy of `source`) at `target` without ever replacing a
// file: the content goes to a temporary file in the target directory, its
// digest is checked against `expected` (if given) before it is published, then
// it is hard-linked into place, so readers see no file or the complete file.
// When the target already exists: `conflict` set fails with that message;
// otherwise the existing file is reused (content addressing: same name, same
// bytes). Either way the published file's digest is checked again. Returns
// true when this call created the file. Callers re-run their own checks
// (regular file, content rules) on top.
export async function writeOnce(target, { bytes, source }, { expected, mismatch = 'Content changed while writing', conflict } = {}) {
  const directory = path.dirname(target);
  const temp = path.join(directory, `.pending-${randomUUID()}`);
  if (source !== undefined) await fs.copyFile(source, temp, fs.constants.COPYFILE_EXCL);
  else await fs.writeFile(temp, bytes, { flag: 'wx' });
  let created = false;
  try {
    // Durable before visible: a crash must not publish a linked but empty file.
    await syncPath(temp, 'r+');
    if (expected && await digest(temp) !== expected) fail(mismatch);
    await fs.link(temp, target);
    created = true;
  } catch (error) {
    if (error.code !== 'EEXIST') throw error;
    if (conflict) fail(conflict);
  } finally { await fs.unlink(temp); }
  if (created) await syncPath(directory, 'r').catch(error => {
    // Some platforms (Windows) cannot open or fsync a directory handle.
    if (!['EISDIR', 'EPERM', 'EINVAL', 'EACCES'].includes(error.code)) throw error;
  });
  if (expected && await digest(target) !== expected) fail(mismatch);
  return created;
}

async function syncPath(file, flags) {
  const handle = await fs.open(file, flags);
  try { await handle.sync(); } finally { await handle.close(); }
}
