import { spawnSync } from "node:child_process";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { auditCodexRuntimeEvidence } from "../src/codex-runtime-evidence.js";

const codex = process.env.CODEX_BIN?.trim() || "codex";

function run(args: string[], stage: string) {
  const result = spawnSync(codex, args, {
    encoding: "utf8",
    shell: false,
    maxBuffer: 16 * 1024 * 1024,
  });
  if (result.error)
    throw new Error(`${stage} 无法启动 Codex CLI: ${result.error.message}`);
  if (result.status !== 0)
    throw new Error(`${stage} 失败，Codex CLI 退出码 ${String(result.status)}`);
  return result.stdout;
}

function readSchema(root: string, relativePath: string): unknown | null {
  const path = join(root, relativePath);
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, "utf8")) as unknown;
  } catch {
    throw new Error(`生成的 schema 不是合法 JSON: ${relativePath}`);
  }
}

const schemaDir = mkdtempSync(join(tmpdir(), "whoami-codex-runtime-"));
try {
  const codexVersion = run(["--version"], "读取版本").trim();
  run(
    [
      "app-server",
      "generate-json-schema",
      "--experimental",
      "--out",
      schemaDir,
    ],
    "生成 app-server schema",
  );
  const result = auditCodexRuntimeEvidence({
    codexVersion,
    initializeSchema: readSchema(schemaDir, "v1/InitializeParams.json"),
    attestationParamsSchema: readSchema(
      schemaDir,
      "AttestationGenerateParams.json",
    ),
    attestationResponseSchema: readSchema(
      schemaDir,
      "AttestationGenerateResponse.json",
    ),
    rawResponseSchema: readSchema(
      schemaDir,
      "v2/RawResponseCompletedNotification.json",
    ),
    threadStartSchema: readSchema(schemaDir, "v2/ThreadStartParams.json"),
  });
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`Codex 运行时证据审计失败: ${message}\n`);
  process.exitCode = 1;
} finally {
  rmSync(schemaDir, { recursive: true, force: true });
}
