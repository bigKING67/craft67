#!/usr/bin/env node

import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, stat, symlink, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import { ensureMcpRegistry, planMcpRegistry, readRegistrySnapshot, writeRegistrySnapshot } from "../scripts/setup-extension/registry.mjs";

const execFileAsync = promisify(execFile);
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const setupScript = path.resolve(repoRoot, "scripts/setup-extension.mjs");
const legacyBrowserServerPath = path.resolve(repoRoot, "src/server.mjs");
const legacyJsReverseServerPath = path.resolve(repoRoot, "src/js-reverse-server.mjs");
const browserServerPath = path.resolve(repoRoot, "src/mcp/browser/server.mjs");
const jsReverseServerPath = path.resolve(repoRoot, "src/mcp/js-reverse/server.mjs");
const packageVersion = JSON.parse(await readFile(path.resolve(repoRoot, "package.json"), "utf8")).version;

function tomlString(value) {
  return JSON.stringify(String(value));
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function assertContainsTomlString(text, value) {
  assert.match(text, new RegExp(escapeRegExp(tomlString(value))));
}

function assertMissingTomlString(text, value) {
  assert.doesNotMatch(text, new RegExp(escapeRegExp(tomlString(value))));
}

async function runSetup({ targetDir, registryPath }) {
  const { stdout, stderr } = await execFileAsync(process.execPath, [
    setupScript,
    "--target",
    targetDir,
    "--registry",
    registryPath,
    "--json",
  ], {
    cwd: repoRoot,
    maxBuffer: 1024 * 1024,
  });
  assert.equal(stderr, "");
  return JSON.parse(stdout);
}

async function main() {
    const tmpDir = await mkdtemp(path.join(os.tmpdir(), "browser67-setup-contract-"));
  try {
    const targetDir = path.join(tmpDir, "browser", "tmwd_cdp_bridge");
    const registryPath = path.join(tmpDir, "mcp", "servers.toml");
    await mkdir(path.dirname(registryPath), { recursive: true });
    await writeFile(registryPath, [
      "",
      "# Standalone browser67 real-browser MCP server.",
      "[[servers]]",
      'name = "tmwd-browser-mcp"',
      'command = "node"',
      `args = [${tomlString(legacyBrowserServerPath)}]`,
      "enabled = true",
      "",
      "[servers.env]",
      'BROWSER_STRUCTURED_TMWD_MODE = "tmwd"',
      "",
      "# browser67-backed JavaScript reverse-engineering MCP server.",
      "[[servers]]",
      'name = "js-reverse"',
      'command = "node"',
      `args = [${tomlString(legacyJsReverseServerPath)}]`,
      "enabled = true",
      "",
      "[servers.env]",
      'BROWSER_STRUCTURED_TMWD_MODE = "tmwd"',
      "",
    ].join("\n"), "utf8");

    const first = await runSetup({ targetDir, registryPath });
    assert.equal(first.ok, true);
    assert.equal(first.product, "browser67");
    assert.equal(first.mcp_registry_changed, true);
    assert.equal(first.extension_build?.schema, "browser67.extension-build.v1");
    const installedManifest = JSON.parse(await readFile(path.join(targetDir, "manifest.json"), "utf8"));
    assert.equal(installedManifest.name, "browser67 TMWD Bridge");
    assert.equal(installedManifest.version, packageVersion);
    assert.deepEqual(installedManifest.content_scripts, []);
    assert.equal(installedManifest.permissions.includes("webRequest"), true);
    assert.match(await readFile(path.join(targetDir, "background.js"), "utf8"), /browser67HandleCommand/);
    assert.match(await readFile(path.join(targetDir, "browser67", "runtime.js"), "utf8"), /tabIds: \[tabId\]/);
    const buildIdentity = JSON.parse(await readFile(path.join(targetDir, "browser67", "build-identity.json"), "utf8"));
    assert.equal(buildIdentity.schema, "browser67.extension-identity.v1");
    assert.equal(buildIdentity.extension_version, packageVersion);
    assert.equal(buildIdentity.manifest_version, installedManifest.version);
    assert.match(buildIdentity.source_digest, /^[a-f0-9]{64}$/);
    assert.match(
      await readFile(path.join(targetDir, "browser67", "build-identity.js"), "utf8"),
      /globalThis\.__browser67BuildIdentity/,
    );
    assert.match(await readFile(path.join(targetDir, "config.js"), "utf8"), /globalThis\.__browser67TID/);

    const normalized = await readFile(registryPath, "utf8");
    assert.match(normalized, /name = "tmwd_browser"/);
    assert.doesNotMatch(normalized, /name = "tmwd-browser-mcp"/);
    assertContainsTomlString(normalized, browserServerPath);
    assertContainsTomlString(normalized, jsReverseServerPath);
    assertMissingTomlString(normalized, legacyBrowserServerPath);
    assertMissingTomlString(normalized, legacyJsReverseServerPath);

    await writeFile(path.join(targetDir, "config.js"), "const TID = '__legacy_tid_kept';\n", "utf8");
    const second = await runSetup({ targetDir, registryPath });
    assert.equal(second.ok, true);
    assert.equal(second.mcp_registry_changed, false);
    assert.equal(second.config_migrated, true);
    assert.equal(
      await readFile(path.join(targetDir, "config.js"), "utf8"),
      'globalThis.__browser67TID = "__legacy_tid_kept";\n',
    );
    assert.equal(await readFile(registryPath, "utf8"), normalized);

    const movedRoot = path.join(tmpDir, "removed-checkout", "browser67");
    const moved = normalized
      .replace(tomlString(browserServerPath), tomlString(path.join(movedRoot, "src/mcp/browser/server.mjs")))
      .replace(tomlString(jsReverseServerPath), tomlString(path.join(movedRoot, "src/mcp/js-reverse/server.mjs")));
    await writeFile(registryPath, moved, "utf8");
    const migrated = await runSetup({ targetDir, registryPath });
    assert.equal(migrated.mcp_registry_changed, true, "setup must migrate the exact pair from a removed checkout");
    assert.equal(await readFile(registryPath, "utf8"), normalized, "migration changes only the two entrypoint paths");

    const withComment = moved + `\n# Keep this historical path: ${tomlString(path.join(movedRoot, "src/mcp/browser/server.mjs"))}\n`;
    assert.equal(planMcpRegistry(withComment, repoRoot).text, normalized + withComment.slice(moved.length));
    const singleQuoted = moved.replace(/args = \[("[^"\n]+")\]/g, (_match, value) => `args = ['${JSON.parse(value)}']`);
    assert.equal(planMcpRegistry(singleQuoted, repoRoot).text, normalized);
    for (const custom of [
      moved.replace('command = "node"', 'command = "/custom/node"'),
      moved.replace('BROWSER_STRUCTURED_TMWD_MODE = "tmwd"', 'BROWSER_STRUCTURED_TMWD_MODE = "auto"'),
      moved.replace('enabled = true', 'custom_field = "keep"\nenabled = true'),
      moved.replace('args = [', 'args = ["--trace-warnings", '),
      moved.replace('enabled = true', 'enabled = true\nenabled = false'),
      moved.replace('enabled = true', 'notes = """\n[[servers]]\nname = "fake"\n"""\nenabled = true'),
      moved.replaceAll('name = ', '"name" = '),
      moved.replaceAll('name = ', "'name' = "),
    ]) {
      assert.equal(planMcpRegistry(custom, repoRoot).text, custom, "customized or unsupported entries remain byte-identical");
    }
    await writeFile(registryPath, moved.replaceAll('name = ', '"name" = '), "utf8");
    await assert.rejects(runSetup({ targetDir, registryPath }), (error) => {
      const result = JSON.parse(error.stdout);
      assert.equal(error.code, 1);
      assert.equal(result.ok, false);
      assert.equal(result.status, "manual_review_required");
      assert.equal(result.mcp_registry_changed, false);
      assert.ok(result.mcp_registry_warnings.length > 0);
      return true;
    });
    await writeFile(registryPath, normalized, "utf8");
    const wrongRoot = moved.replace(tomlString(path.join(movedRoot, "src/mcp/js-reverse/server.mjs")),
      tomlString(path.join(tmpDir, "another-checkout", "src/mcp/js-reverse/server.mjs")));
    assert.equal(planMcpRegistry(wrongRoot, repoRoot).text, wrongRoot);
    await mkdir(movedRoot, { recursive: true });
    assert.equal(planMcpRegistry(moved, repoRoot).text, moved, "an existing checkout is never retargeted");
    await rm(movedRoot, { recursive: true });
    try {
      await symlink(path.join(tmpDir, "missing-symlink-target"), movedRoot, "dir");
      assert.equal(planMcpRegistry(moved, repoRoot).text, moved, "a dangling checkout symlink is not an absent checkout");
      await rm(movedRoot);
      const registryLink = path.join(tmpDir, "registry-link.toml");
      await symlink(registryPath, registryLink);
      assert.throws(() => ensureMcpRegistry(registryLink, repoRoot), /regular file/);
    } catch (error) {
      if (process.platform !== "win32" || !["EPERM", "EACCES"].includes(error.code)) throw error;
    }

    const beforeEdit = readRegistrySnapshot(registryPath);
    await writeFile(registryPath, normalized + "# concurrent edit\n", "utf8");
    assert.throws(() => writeRegistrySnapshot(registryPath, beforeEdit, normalized), /changed during setup/);
    assert.equal(await readFile(registryPath, "utf8"), normalized + "# concurrent edit\n");
    assert.throws(() => writeRegistrySnapshot(registryPath, null, normalized), /changed during setup/);
    await writeFile(registryPath, normalized, "utf8");
    if (process.platform !== "win32") assert.equal((await stat(registryPath)).mode & 0o777, 0o600);

    process.stdout.write(JSON.stringify({
      ok: true,
      check: "setup-extension-contract",
      normalized_legacy_registry: true,
      idempotent: true,
      managed_overlay_built: true,
      extension_identity_built: true,
      legacy_config_migrated: true,
      removed_checkout_pair_migrated: true,
      custom_and_existing_checkouts_preserved: true,
      observed_concurrent_edits_rejected: true,
      unknown_toml_names_require_manual_review: true,
    }) + "\n");
  } finally {
    await rm(tmpDir, { recursive: true, force: true });
  }
}

main().catch((error) => {
  process.stderr.write(`setup-extension-contract failed: ${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
});
