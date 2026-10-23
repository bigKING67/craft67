import { randomUUID } from "node:crypto";
import { linkSync, lstatSync, mkdirSync, readFileSync, renameSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, join, resolve, sep } from "node:path";

const STRING = `(?:"(?:[^"\\\\\\r\\n]|\\\\.)*"|'[^'\\r\\n]*')`;
const DEFAULT_ENV = new Map([
  ["BROWSER_STRUCTURED_TMWD_MODE", "tmwd"],
  ["BROWSER_STRUCTURED_TMWD_TRANSPORT", "auto"],
  ["BROWSER_STRUCTURED_TMWD_WS_ENDPOINT", "ws://127.0.0.1:18765"],
  ["BROWSER_STRUCTURED_TMWD_LINK_ENDPOINT", "http://127.0.0.1:18766/link"],
]);
const ROLES = new Map([
  ["tmwd_browser", "browser"], ["tmwd-browser-mcp", "browser"], ["js-reverse", "js-reverse"],
]);

function parseString(raw) {
  if (typeof raw !== "string" || !new RegExp(`^${STRING}$`).test(raw)) return null;
  try { return raw.startsWith("'") ? raw.slice(1, -1) : JSON.parse(raw); } catch { return null; }
}

// Only the installer's single-line generated TOML subset is eligible for repair.
// Unknown keys, custom commands/env, duplicate fields and richer TOML stay intact.
function readEntry(text) {
  const entry = { text, fields: new Map(), env: new Map(), safe: true };
  if (!/^\s*\[\[servers\]\]/.test(text)) return entry;
  let inEnv = false;
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || /^\[\[servers\]\]\s*(?:#.*)?$/.test(trimmed)) continue;
    if (trimmed === "[servers.env]" && !inEnv) { inEnv = true; continue; }
    const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (!match) { entry.safe = false; continue; }
    const [, key, raw] = match;
    let value = null;
    if (key === "args" && !inEnv) {
      value = raw.match(new RegExp(`^\\[\\s*(${STRING})\\s*\\]\\s*(?:#.*)?$`))?.[1] ?? null;
    } else {
      value = raw.match(new RegExp(`^(${STRING}|true|false)\\s*(?:#.*)?$`))?.[1] ?? null;
    }
    const fields = inEnv ? entry.env : entry.fields;
    if (fields.has(key) || value === null) entry.safe = false;
    fields.set(key, { raw: value, value: parseString(value) ?? value });
  }
  for (const key of entry.fields.keys()) {
    if (!["name", "command", "args", "enabled"].includes(key)) entry.safe = false;
  }
  for (const [key, field] of entry.env) {
    if (DEFAULT_ENV.get(key) !== field.value) entry.safe = false;
  }
  if (entry.fields.get("command")?.value !== "node") entry.safe = false;
  return entry;
}

function entryRoot(entry, role) {
  const path = entry.fields.get("args")?.value;
  if (typeof path !== "string" || !isAbsolute(path)) return null;
  for (const suffix of [
    join("src", "mcp", role, "server.mjs"),
    role === "browser" ? join("src", "server.mjs") : join("src", "js-reverse-server.mjs"),
  ]) {
    if (path.endsWith(`${sep}${suffix}`)) return path.slice(0, -suffix.length - 1);
  }
  return null;
}

function isMissing(path) {
  try { lstatSync(path); return false; } catch (error) {
    if (error.code === "ENOENT") return true;
    throw error;
  }
}

function defaultBlock(name, serverPath) {
  return [
    "", "# browser67 MCP server.", "[[servers]]", `name = ${JSON.stringify(name)}`,
    'command = "node"', `args = [${JSON.stringify(serverPath)}]`, "enabled = true", "",
    "[servers.env]",
    ...[...DEFAULT_ENV].map(([key, value]) => `${key} = ${JSON.stringify(value)}`), "",
  ].join("\n");
}

function planMcpRegistry(current, repoRoot) {
  if (/"""|'''/.test(current)) {
    return { text: current, migrated: false, warnings: ["unsupported_registry_toml_preserved"] };
  }
  const chunks = current.split(/(?=^\s*\[\[servers\]\]\s*(?:#.*)?$)/m);
  if (chunks[0] && !/^\s*\[\[servers\]\]/.test(chunks[0])
    && chunks[0].split(/\r?\n/).some((line) => line.trim() && !line.trim().startsWith("#"))) {
    return { text: current, migrated: false, warnings: ["unsupported_registry_toml_preserved"] };
  }
  const entries = chunks.map(readEntry);
  if (entries.some((entry) => /^\s*\[\[servers\]\]/.test(entry.text)
    && typeof parseString(entry.fields.get("name")?.raw) !== "string")) {
    return { text: current, migrated: false, warnings: ["unrecognized_server_name_preserved"] };
  }
  const named = (role) => entries.filter((entry) => ROLES.get(entry.fields.get("name")?.value) === role);
  const browsers = named("browser");
  const reverses = named("js-reverse");
  const warnings = [];
  let migrated = false;
  if (browsers.length === 1 && reverses.length === 1) {
    const pair = [browsers[0], reverses[0]];
    const roots = [entryRoot(pair[0], "browser"), entryRoot(pair[1], "js-reverse")];
    if (roots.every(Boolean) && roots[0] === roots[1]) {
      let eligible = roots[0] === repoRoot;
      try { eligible ||= isMissing(roots[0]); } catch { warnings.push("legacy_checkout_state_unknown"); }
      const needsRepair = pair.some((entry, index) => (
        entry.fields.get("args")?.value !== resolve(repoRoot, "src/mcp", index === 0 ? "browser" : "js-reverse", "server.mjs")
        || entry.fields.get("name")?.value === "tmwd-browser-mcp"
      ));
      if (eligible && needsRepair && pair.every((entry) => entry.safe)) {
        for (const [index, role] of ["browser", "js-reverse"].entries()) {
          const entry = pair[index];
          const args = entry.fields.get("args");
          const name = entry.fields.get("name");
          // Match complete assignment lines, never comments or unrelated strings.
          const canonical = resolve(repoRoot, "src/mcp", role, "server.mjs");
          if (args.value !== canonical) {
            entry.text = entry.text.replace(/^(\s*args\s*=\s*\[\s*)("(?:[^"\\\r\n]|\\.)*"|'[^'\r\n]*')(?=\s*\])/m,
              (_match, prefix) => `${prefix}${JSON.stringify(canonical)}`);
          }
          if (name.value === "tmwd-browser-mcp") {
            entry.text = entry.text.replace(/^(\s*name\s*=\s*)("tmwd-browser-mcp"|'tmwd-browser-mcp')/m, '$1"tmwd_browser"');
          }
          migrated ||= args.value !== resolve(repoRoot, "src/mcp", role, "server.mjs") || name.value === "tmwd-browser-mcp";
        }
      } else if (eligible && needsRepair) {
        warnings.push("customized_legacy_pair_preserved");
      }
    } else {
      warnings.push("legacy_pair_roots_differ_or_incomplete");
    }
  } else if (browsers.length > 1 || reverses.length > 1) {
    warnings.push("duplicate_mcp_names_preserved");
  } else if (browsers.length + reverses.length > 0) {
    warnings.push("incomplete_mcp_pair_preserved");
  }
  let next = entries.map((entry) => entry.text).join("");
  for (const [role, name] of [["browser", "tmwd_browser"], ["js-reverse", "js-reverse"]]) {
    if (named(role).length === 0) next += defaultBlock(name, resolve(repoRoot, "src/mcp", role, "server.mjs"));
  }
  return { text: next, migrated, warnings };
}

function readRegistrySnapshot(path) {
  try {
    const stat = lstatSync(path);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error("MCP registry must be a regular file; refusing symlink or non-file target");
    return { text: readFileSync(path, "utf8"), dev: stat.dev, ino: stat.ino, mtimeMs: stat.mtimeMs };
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

function writeRegistrySnapshot(path, expected, next) {
  const temporary = `${path}.${process.pid}.${randomUUID()}.tmp`;
  try {
    writeFileSync(temporary, next, { encoding: "utf8", flag: "wx", mode: 0o600 });
    const current = readRegistrySnapshot(path);
    if (JSON.stringify(current) !== JSON.stringify(expected)) throw new Error("MCP registry changed during setup; rerun after reviewing concurrent edits");
    // A missing registry uses an exclusive link so a concurrent creator is never replaced.
    if (expected === null) linkSync(temporary, path);
    else renameSync(temporary, path);
  } finally {
    try { unlinkSync(temporary); } catch (error) { if (error.code !== "ENOENT") throw error; }
  }
}

function ensureMcpRegistry(path, repoRoot) {
  mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
  const snapshot = readRegistrySnapshot(path);
  const plan = planMcpRegistry(snapshot?.text ?? "", repoRoot);
  const changed = plan.text !== (snapshot?.text ?? "");
  if (changed) writeRegistrySnapshot(path, snapshot, plan.text);
  return { path, changed, migrated: plan.migrated, warnings: plan.warnings };
}

export { ensureMcpRegistry, planMcpRegistry, readRegistrySnapshot, writeRegistrySnapshot };
