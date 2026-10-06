import { createHash } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { adjudicateBaziTimingBlindReview } from "../src/blind-review-adjudication.js";
import { InputError } from "../src/input.js";

const HELP = `八字岁运局部字样盲审裁决器
  npm run blind-review:adjudicate -- \\
    --response private/blind-review/reviewer-a.json \\
    --response private/blind-review/reviewer-b.json \\
    [--response private/blind-review/reviewer-c.json] \\
    [--key docs/quality/2026-09-26-bazi-timing-blind-review-key.json] \\
    [--out private/blind-review/adjudication.json]

只接受 2 或 3 份独立答卷。未提供 --out 时将结果写到 stdout；经 npm 管道读取纯 JSON 时请加 --silent。提供 --out 时创建父目录并拒绝覆盖已有文件。
`;

function digest(content: Buffer): string {
  return createHash("sha256").update(content).digest("hex");
}

function readJson(path: string, label: string) {
  let bytes: Buffer;
  try {
    bytes = readFileSync(path);
  } catch {
    throw new InputError("INVALID_BLIND_REVIEW", `${label} 不可读：${path}`);
  }
  try {
    return { data: JSON.parse(bytes.toString("utf8")) as unknown, sha256: digest(bytes) };
  } catch {
    throw new InputError(
      "INVALID_BLIND_REVIEW",
      `${label} 不是合法 JSON：${path}`,
    );
  }
}

function run() {
  const args = process.argv.slice(2);
  if (!args.length || args[0] === "--help" || args[0] === "help") {
    process.stdout.write(HELP);
    return;
  }
  const responses: string[] = [];
  const defaultKeyPath = fileURLToPath(
    new URL(
      "../docs/quality/2026-09-26-bazi-timing-blind-review-key.json",
      import.meta.url,
    ),
  );
  let keyPath = defaultKeyPath;
  let keyProvided = false;
  let outputPath: string | undefined;
  while (args.length) {
    const flag = args.shift();
    const value = args.shift();
    if (!flag?.startsWith("--") || !value || value.startsWith("--"))
      throw new InputError("INVALID_ARGUMENT", "未知参数或参数缺值");
    if (flag === "--response") responses.push(value);
    else if (flag === "--key") {
      if (keyProvided)
        throw new InputError("INVALID_ARGUMENT", "--key 不能重复");
      keyPath = value;
      keyProvided = true;
    } else if (flag === "--out") {
      if (outputPath)
        throw new InputError("INVALID_ARGUMENT", "--out 不能重复");
      outputPath = value;
    } else throw new InputError("INVALID_ARGUMENT", `未知参数 ${flag}`);
  }
  if (responses.length < 2 || responses.length > 3)
    throw new InputError("INVALID_ARGUMENT", "必须提供 2 或 3 个 --response");
  if (new Set(responses.map((path) => resolve(path))).size !== responses.length)
    throw new InputError("INVALID_ARGUMENT", "不能重复提供同一个答卷文件");
  const key = readJson(keyPath, "答案键");
  const responseFiles = responses.map((path, index) =>
    readJson(path, `答卷 ${index + 1}`),
  );
  const result = adjudicateBaziTimingBlindReview(
    key.data,
    responseFiles.map((item) => item.data),
    {
      keySha256: key.sha256,
      responseSha256: responseFiles.map((item) => item.sha256),
    },
  );
  const serialized = JSON.stringify(result, null, 2) + "\n";
  if (!outputPath) {
    process.stdout.write(serialized);
    return;
  }
  const resolved = resolve(outputPath);
  if (existsSync(resolved))
    throw new InputError("OUTPUT_EXISTS", `目标文件已存在，不覆盖：${resolved}`);
  mkdirSync(dirname(resolved), { recursive: true, mode: 0o700 });
  writeFileSync(resolved, serialized, { flag: "wx", mode: 0o600 });
  process.stdout.write(
    JSON.stringify(
      {
        status: "written",
        resultStatus: result.status,
        output: resolved,
        acceptedTargets: result.summary.acceptedTargets,
        unresolvedTargets: result.summary.unresolvedTargets,
      },
      null,
      2,
    ) + "\n",
  );
}

try {
  run();
} catch (error) {
  const input = error instanceof InputError;
  const code = input ? error.code : "INTERNAL_ERROR";
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`${JSON.stringify({ code, message })}\n`);
  process.exitCode = input ? 2 : 1;
}
