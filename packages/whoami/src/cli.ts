import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { buildChart } from "./chart.js";
import { buildEvidence, evidenceForReport } from "./evidence.js";
import { parseInput, InputError } from "./input.js";
import {
  renderReport,
  reportTemplate,
  validateReport,
  type Report,
} from "./report.js";
import { prepareBenchmark, scoreBenchmark } from "./benchmark.js";
import { renderRuleReview } from "./rule-review.js";
import { compareBirths } from "./compare.js";
import { checkAcceptanceManifest } from "./acceptance.js";
import { contextErrorOutcome } from "./outcome.js";
import { checkAnswer } from "./answer-check.js";
import {
  finalizeRuntimeAttestation,
  prepareRuntimeAttestation,
} from "./attestation-workflow.js";

const HELP = `whoami（本地核心，不调用模型 API）
  validate --input <birth.json>
  chart --input <birth.json> [--years 2024,2025,2026] [--granularity year|month]
  context --input <birth.json> [--years ...] [--granularity year|month]
  rule-review --input <birth.json> [--years ...]  （财格规则复核 Markdown）
  compare --before <birth.json> --after <birth.json> [--years ...] [--before-candidate <ID>] [--after-candidate <ID>]
  report-template --input <birth.json> [--mode combined|bazi|ziwei] [--years ...] [--granularity year|month]
  report-check --input <birth.json> --report <report.json> [--years ...] [--granularity year|month]
  answer-check --input <birth.json> (--text <answer.md> | --audit <含 answer 的清单>) [--years ...] [--as-of YYYY-MM-DD] [--granularity year|month] [--audit <audit.json>]  （快速档纯文本答复门禁）
  render --input <birth.json> --report <report.json> [--years ...] [--granularity year|month]
  benchmark-prepare --dataset <data.json> --output-dir <private-dir> [--seed whoami-v1] [--astro <fortune_api_results.json>]
  benchmark-score --key <answers.json> --predictions <predictions.json>
  attestation-prepare --manifest <draft-manifest.json> --run <runtime-run.json>
  attestation-finalize --manifest <draft-manifest.json> --request <request.json> --signature <signature.txt> --trusted-runtime-key <ed25519-public.pem>
  acceptance-check --manifest <manifest.json> [--trusted-runtime-key <ed25519-public.pem>]
--granularity month 额外输出八字节气流月与紫微农历流月；同一报告的 context、report-template、report-check、render 与 answer-check 须使用相同的 years 与 granularity。
JSON 输入使用文件或 --input - 从 stdin 读取。正常结果到 stdout，错误到 stderr。
chart 返回 needs-input 时退出 2；ambiguous 返回 0 但不能按唯一盘解读。
benchmark-prepare 是唯一显式写文件命令，不覆盖已有文件；attestation-finalize 只向 stdout 返回已验签回执及其精确序列化字节。
`;
let activeCommand: string | undefined;
let activeContextYears: number[] | undefined;

function run() {
  const args = process.argv.slice(2),
    command = args.shift();
  activeCommand = command;
  if (!command || command === "help" || command === "--help") {
    process.stdout.write(HELP);
    return;
  }
  const allowed: Record<string, string[]> = {
    validate: ["input"],
    chart: ["input", "years", "granularity"],
    context: ["input", "years", "granularity"],
    "rule-review": ["input", "years"],
    compare: ["before", "after", "years", "before-candidate", "after-candidate"],
    "report-template": ["input", "years", "mode", "granularity"],
    "report-check": ["input", "years", "report", "granularity"],
    "answer-check": ["input", "years", "text", "as-of", "granularity", "audit"],
    render: ["input", "years", "report", "granularity"],
    "benchmark-prepare": ["dataset", "output-dir", "seed", "astro"],
    "benchmark-score": ["key", "predictions"],
    "attestation-prepare": ["manifest", "run"],
    "attestation-finalize": [
      "manifest",
      "request",
      "signature",
      "trusted-runtime-key",
    ],
    "acceptance-check": ["manifest", "trusted-runtime-key"],
  };
  if (!allowed[command])
    throw new InputError("UNKNOWN_COMMAND", `未知命令 ${command}`);
  const opts: Record<string, string> = {};
  while (args.length) {
    const key = args.shift()!;
    const value = args.shift();
    if (
      !key.startsWith("--") ||
      !value ||
      value.startsWith("--") ||
      !allowed[command]!.includes(key.slice(2)) ||
      key.slice(2) in opts
    )
      throw new InputError("INVALID_ARGUMENT", "未知、重复或缺值参数");
    opts[key.slice(2)] = value;
  }
  const required = (key: string) => {
    if (!opts[key]) throw new InputError("MISSING_ARGUMENT", `需要 --${key}`);
    return opts[key]!;
  };
  const read = (key: string) => {
    const p = required(key);
    try {
      return JSON.parse(readFileSync(p === "-" ? 0 : p, "utf8")) as unknown;
    } catch {
      throw new InputError("INVALID_JSON", `${key} 文件不可读或不是合法 JSON`);
    }
  };
  // 参数错误先于输入计算返回，避免被包装成可重放的 context 计算错误。
  const granularity = opts.granularity ?? "year";
  if (granularity !== "year" && granularity !== "month")
    throw new InputError("INVALID_ARGUMENT", "granularity 只能是 year 或 month");
  if (command === "answer-check" && [opts.text, opts.input, opts.audit].filter((v) => v === "-").length > 1)
    throw new InputError("INVALID_ARGUMENT", "input、text、audit 最多一项从stdin读取");
  const emit = (x: unknown) =>
    process.stdout.write(JSON.stringify(x, null, 2) + "\n");
  if (command === "attestation-prepare") {
    const manifestPath = required("manifest");
    emit(
      prepareRuntimeAttestation(
        read("manifest"),
        manifestPath,
        read("run"),
      ),
    );
    return;
  }
  if (command === "attestation-finalize") {
    const manifestPath = required("manifest");
    let signature: string;
    try {
      signature = readFileSync(required("signature"), "utf8").trim();
    } catch {
      throw new InputError(
        "INVALID_ATTESTATION_REQUEST",
        "signature 文件不可读",
      );
    }
    emit(
      finalizeRuntimeAttestation(
        read("manifest"),
        manifestPath,
        read("request"),
        signature,
        required("trusted-runtime-key"),
      ),
    );
    return;
  }
  if (command === "acceptance-check") {
    const manifestPath = required("manifest");
    emit(
      checkAcceptanceManifest(read("manifest"), manifestPath, {
        trustedRuntimeKeyPath: opts["trusted-runtime-key"],
      }),
    );
    return;
  }
  if (command === "compare") {
    if (required("before") === "-" && required("after") === "-")
      throw new InputError("INVALID_ARGUMENT", "before和after不能同时从stdin读取；请至少为一侧提供文件");
    const result = compareBirths(read("before"), read("after"), opts.years?.split(",").map(Number), {
      beforeCandidate: opts["before-candidate"], afterCandidate: opts["after-candidate"],
    });
    emit(result);
    if (result.status !== "compared") process.exitCode = 2;
    return;
  }
  if (command === "benchmark-prepare") {
    const prepared = prepareBenchmark(
      read("dataset"),
      opts.seed,
      opts.astro ? read("astro") : undefined,
    );
    const dir = resolve(required("output-dir"));
    const targets = [
      resolve(dir, "prompts.json"),
      resolve(dir, "answer-key.json"),
    ];
    if (targets.some((p) => existsSync(p)))
      throw new InputError("OUTPUT_EXISTS", "目标评测文件已存在，不覆盖");
    mkdirSync(dir, { recursive: true, mode: 0o700 });
    writeFileSync(
      targets[0]!,
      JSON.stringify(prepared.prompts, null, 2) + "\n",
      { flag: "wx", mode: 0o600 },
    );
    writeFileSync(
      targets[1]!,
      JSON.stringify(prepared.answerKey, null, 2) + "\n",
      { flag: "wx", mode: 0o600 },
    );
    emit({
      paths: targets,
      count: prepared.prompts.items.length,
      datasetHash: prepared.prompts.datasetHash,
    });
    return;
  }
  if (command === "benchmark-score") {
    emit(scoreBenchmark(read("key"), read("predictions")));
    return;
  }
  const input = read("input");
  if (command === "validate") {
    emit({ status: "valid", input: parseInput(input) });
    return;
  }
  const years = opts.years?.split(",").map(Number);
  if (
    command === "context" &&
    years?.length &&
    years.every((year) => Number.isInteger(year))
  )
    activeContextYears = years;
  const chart = buildChart(input, years, granularity);
  if (chart.status === "needs-input") {
    emit(chart);
    process.exitCode = 2;
    return;
  }
  if (command === "chart") {
    emit(chart);
    return;
  }
  if (command === "rule-review") {
    process.stdout.write(renderRuleReview(chart));
    return;
  }
  const context = buildEvidence(chart);
  if (command === "context") {
    emit(context);
    return;
  }
  if (command === "report-template") {
    const mode = opts.mode ?? "combined";
    if (!["bazi", "ziwei", "combined"].includes(mode))
      throw new InputError("INVALID_ARGUMENT", "mode 无效");
    emit(reportTemplate(context, mode as Report["mode"]));
    return;
  }
  if (command === "answer-check") {
    // 清单可内嵌答复原文（audit.answer），此时用 --audit - 一次从 stdin 传入，答复不落盘。
    const audit = opts.audit ? read("audit") : undefined;
    const embedded =
      audit && typeof audit === "object" && typeof (audit as { answer?: unknown }).answer === "string"
        ? (audit as { answer: string }).answer
        : undefined;
    let text: string;
    if (opts.text) {
      try {
        text = readFileSync(opts.text === "-" ? 0 : opts.text, "utf8");
      } catch {
        throw new InputError("INVALID_ARGUMENT", "text 文件不可读");
      }
    } else if (embedded !== undefined) text = embedded;
    else throw new InputError("MISSING_ARGUMENT", "需要 --text，或在 --audit 中提供 answer");
    emit(checkAnswer(text, context, opts["as-of"], audit));
    return;
  }
  const report = read("report");
  // 既有报告按其绑定的 evidence 版本重算；新报告使用当前版本。
  const bound = evidenceForReport(chart, report, context);
  const reportEvidenceId =
    report && typeof report === "object" ? (report as { evidenceId?: unknown }).evidenceId : undefined;
  if (bound.evidenceId !== reportEvidenceId) {
    // 粒度参数不一致时给出直接原因，而不是笼统的 STALE_REPORT。
    const other = granularity === "month" ? "year" : "month";
    if (evidenceForReport(buildChart(input, years, other), report).evidenceId === reportEvidenceId)
      throw new InputError(
        "GRANULARITY_MISMATCH",
        other === "month"
          ? "该报告绑定月度 evidence，请加 --granularity month 重新校验"
          : "该报告绑定年度 evidence，请去掉 --granularity month 重新校验",
      );
  }
  if (command === "render") process.stdout.write(renderReport(report, bound));
  else {
    validateReport(report, bound);
    emit({
      status: "valid",
      chartId: bound.chartId,
      evidenceId: bound.evidenceId,
      evidenceSchema: bound.schema,
      limitations:
        "仅验证结构、引用与显式事实断言；不证明自然语言解释的语义正确性或预测能力。",
    });
  }
}
try {
  run();
} catch (e) {
  const body =
    activeCommand === "context" &&
    activeContextYears &&
    e instanceof InputError
      ? contextErrorOutcome(e, activeContextYears)
      : {
          status: "error" as const,
          code: e instanceof InputError ? e.code : "COMPUTATION_ERROR",
          message: e instanceof Error ? e.message : "unknown error",
        };
  process.stderr.write(
    JSON.stringify(body) + "\n",
  );
  process.exitCode = 1;
}
