#!/usr/bin/env node

import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { resolveBrowser67Home } from "../src/runtime/paths/home.mjs";
import { buildExtension } from "./build-extension.mjs";
import { ensureMcpRegistry } from "./setup-extension/registry.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "..");
const sourceDir = resolve(repoRoot, "extension");
const homeResolution = resolveBrowser67Home();
const defaultHome = homeResolution.path;
const defaultTargetDir = resolve(defaultHome, "browser/tmwd_cdp_bridge");
const defaultMcpRegistryPath = resolve(defaultHome, "mcp/servers.toml");

function parseArgs(argv) {
  const parsed = {
    targetDir: defaultTargetDir,
    registryPath: defaultMcpRegistryPath,
    json: false,
    forceConfig: false,
    skipRegistry: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index] ?? "";
    if (token === "--json") {
      parsed.json = true;
      continue;
    }
    if (token === "--force-config") {
      parsed.forceConfig = true;
      continue;
    }
    if (token === "--skip-registry") {
      parsed.skipRegistry = true;
      continue;
    }
    if (token === "--target") {
      parsed.targetDir = resolve(requiredValue(argv, index, token));
      index += 1;
      continue;
    }
    if (token === "--registry") {
      parsed.registryPath = resolve(requiredValue(argv, index, token));
      index += 1;
      continue;
    }
    if (token === "--help" || token === "-h") {
      parsed.help = true;
      continue;
    }
    throw new Error(`unknown argument: ${token}`);
  }
  return parsed;
}

function requiredValue(argv, index, token) {
  const value = String(argv[index + 1] ?? "").trim();
  if (!value || value.startsWith("--")) {
    throw new Error(`missing ${token} value`);
  }
  return value;
}

function usage() {
  return [
    "Usage: node scripts/setup-extension.mjs [--target <dir>] [--registry <path>] [--force-config] [--skip-registry] [--json]",
    "",
    "Copies extension/ into the active browser67 unpacked-extension directory and writes config.js.",
  ].join("\n");
}

function makeTid() {
  return `__browser67_${randomBytes(6).toString("hex")}`;
}

function run() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    process.stdout.write(`${usage()}\n`);
    return 0;
  }
  if (!existsSync(sourceDir)) {
    throw new Error(`missing extension source: ${sourceDir}`);
  }
  mkdirSync(args.targetDir, { recursive: true });
  const extensionBuild = buildExtension({ source_dir: sourceDir, target_dir: args.targetDir });
  const configPath = resolve(args.targetDir, "config.js");
  const configExists = existsSync(configPath);
  let configMigrated = false;
  if (!configExists || args.forceConfig) {
    writeFileSync(configPath, `globalThis.__browser67TID = '${makeTid()}';\n`, "utf8");
  } else {
    const currentConfig = readFileSync(configPath, "utf8");
    const legacyTid = currentConfig.match(/\b(?:const|let|var)\s+TID\s*=\s*['"]([^'"]+)['"]/);
    if (legacyTid && !currentConfig.includes("__browser67TID")) {
      writeFileSync(configPath, `globalThis.__browser67TID = ${JSON.stringify(legacyTid[1])};\n`, "utf8");
      configMigrated = true;
    }
  }
  const registry = args.skipRegistry
    ? { path: args.registryPath, changed: false, skipped: true }
    : ensureMcpRegistry(args.registryPath, repoRoot);
  const payload = {
    ok: (registry.warnings?.length ?? 0) === 0,
    status: (registry.warnings?.length ?? 0) === 0 ? "prepared" : "manual_review_required",
    product: "browser67",
    active_home: defaultHome,
    active_home_source: homeResolution.source,
    canonical_home: homeResolution.canonical_default,
    legacy_home: homeResolution.legacy_default,
    extension_dir: args.targetDir,
    extension_build: extensionBuild,
    config_path: configPath,
    config_created: !configExists || args.forceConfig,
    config_migrated: configMigrated,
    mcp_registry_path: registry.path,
    mcp_registry_changed: registry.changed,
    mcp_registry_skipped: registry.skipped === true,
    mcp_registry_migrated: registry.migrated === true,
    mcp_registry_warnings: registry.warnings ?? [],
    next_steps: [
      "Open chrome://extensions or edge://extensions",
      "Enable Developer mode",
      `Load unpacked extension from: ${args.targetDir}`,
      "Run: npm run hub:start",
      "For an already loaded extension, run: npm run extension:reload-live",
      "Otherwise reload browser67 TMWD Bridge from the browser extension page",
      "Run: npm run doctor",
    ],
  };
  if (args.json) {
    process.stdout.write(`${JSON.stringify(payload)}\n`);
    return payload.ok ? 0 : 1;
  }
  process.stdout.write(`Extension prepared: ${payload.extension_dir}\n`);
  const identity = payload.extension_build.extension_identity;
  process.stdout.write(`Extension version: ${identity.extension_version}\n`);
  process.stdout.write(`Build revision: ${identity.build_revision} (${identity.build_revision_source}${identity.build_inputs_dirty ? ", dirty development build" : ""})\n`);
  process.stdout.write("Live extension: UNVERIFIED until reload and doctor; remote latest version: NOT CHECKED\n");
  process.stdout.write(`Active home: ${payload.active_home} (${payload.active_home_source})\n`);
  process.stdout.write(`Config: ${payload.config_path}${payload.config_created ? " (created)" : " (kept)"}\n`);
  process.stdout.write(`MCP registry: ${payload.mcp_registry_path}${payload.mcp_registry_changed ? " (updated)" : " (unchanged)"}\n`);
  for (const warning of payload.mcp_registry_warnings) {
    process.stdout.write(`MCP registry requires manual review: ${warning}\n`);
  }
  process.stdout.write("Next:\n");
  for (const item of payload.next_steps) {
    process.stdout.write(`  - ${item}\n`);
  }
  return payload.ok ? 0 : 1;
}

try {
  process.exitCode = run();
} catch (error) {
  process.stderr.write(`setup-extension failed: ${String(error?.message ?? error)}\n`);
  process.exitCode = 1;
}
