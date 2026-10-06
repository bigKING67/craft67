import { createHash } from "node:crypto";
import { readFileSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { isDeepStrictEqual } from "node:util";
import { InputError, object } from "./input.js";
import { buildChart } from "./chart.js";
import { buildEvidence, isEvidenceSchema } from "./evidence.js";
import { contextErrorOutcome } from "./outcome.js";
import { validateReport } from "./report.js";
import type { Evidence } from "./evidence.js";
import type { Report } from "./report.js";
import {
  assertSafeReportText,
  findUnresolvedPremiseUpgrade,
  requiredReasoningTopics,
} from "./report-safety.js";
import {
  decodeCanonicalBase64,
  readTrustedEd25519PublicKey,
  runtimeAttestationPayload,
  verifyEd25519Attestation,
} from "./attestation.js";
import { Temporal } from "@js-temporal/polyfill";

type Artifact = {
  path: string;
  sha256: string;
  bytes: number;
};

const digest = (data: Buffer) =>
  createHash("sha256").update(data).digest("hex");

const nonEmpty = (value: unknown, label: string) => {
  if (typeof value !== "string" || !value.trim())
    throw new InputError("INVALID_ACCEPTANCE", `${label} 必须是非空文字`);
  return value.trim();
};

const integer = (value: unknown, label: string) => {
  if (!Number.isInteger(value) || Number(value) < 0)
    throw new InputError("INVALID_ACCEPTANCE", `${label} 必须是非负整数`);
  return Number(value);
};

const nullableParameter = (value: unknown, label: string) => {
  if (value === null) return null;
  if (typeof value === "string" && value.trim()) return value.trim();
  if (typeof value === "number" && Number.isFinite(value)) return value;
  throw new InputError(
    "INVALID_ACCEPTANCE",
    `${label} 必须显式为 null、有限数字或非空文字`,
  );
};

const absoluteInstant = (value: unknown, label: string) => {
  const text = nonEmpty(value, label);
  try {
    Temporal.Instant.from(text);
  } catch {
    throw new InputError(
      "INVALID_ACCEPTANCE_RECEIPT",
      `${label} 必须是带时区或 Z 的绝对时刻`,
    );
  }
  return text;
};

function verifyArtifact(
  raw: unknown,
  baseDir: string,
  label: string,
): Artifact & { resolvedPath: string } {
  const artifact = object(raw, label);
  const path = nonEmpty(artifact.path, `${label}.path`);
  if (isAbsolute(path))
    throw new InputError(
      "INVALID_ACCEPTANCE",
      `${label}.path 必须相对验收清单目录`,
    );
  const resolvedPath = resolve(baseDir, path);
  const relativePath = relative(baseDir, resolvedPath);
  if (
    relativePath === ".." ||
    relativePath.startsWith(`..${sep}`) ||
    isAbsolute(relativePath)
  )
    throw new InputError(
      "INVALID_ACCEPTANCE",
      `${label}.path 不能越出验收清单目录`,
    );
  let actualPath: string;
  try {
    actualPath = realpathSync(resolvedPath);
    const realBase = realpathSync(baseDir);
    const actualRelative = relative(realBase, actualPath);
    if (
      actualRelative === ".." ||
      actualRelative.startsWith(`..${sep}`) ||
      isAbsolute(actualRelative)
    )
      throw new InputError(
        "INVALID_ACCEPTANCE",
        `${label}.path 不能通过符号链接越出验收清单目录`,
      );
  } catch (error) {
    if (error instanceof InputError) throw error;
    throw new InputError("MISSING_ACCEPTANCE_ARTIFACT", `${label} 文件不可读`);
  }
  let data: Buffer;
  try {
    data = readFileSync(actualPath);
  } catch {
    throw new InputError("MISSING_ACCEPTANCE_ARTIFACT", `${label} 文件不可读`);
  }
  const sha256 = nonEmpty(artifact.sha256, `${label}.sha256`);
  const bytes = integer(artifact.bytes, `${label}.bytes`);
  if (digest(data) !== sha256 || data.byteLength !== bytes)
    throw new InputError(
      "ACCEPTANCE_ARTIFACT_MISMATCH",
      `${label} 的哈希或大小与清单不一致`,
    );
  return { path, sha256, bytes, resolvedPath: actualPath };
}

function readJsonArtifact(
  artifact: Artifact & { resolvedPath: string },
  label: string,
  code = "INVALID_ACCEPTANCE_CONTEXT",
) {
  try {
    return JSON.parse(readFileSync(artifact.resolvedPath, "utf8")) as unknown;
  } catch {
    throw new InputError(
      code,
      `${label} 必须是合法 JSON`,
    );
  }
}

function readResponseArtifact(
  artifact: Artifact & { resolvedPath: string },
  label: string,
) {
  let text: string;
  try {
    text = readFileSync(artifact.resolvedPath, "utf8");
  } catch {
    throw new InputError("MISSING_ACCEPTANCE_ARTIFACT", `${label} 文件不可读`);
  }
  if (!text.trim())
    throw new InputError("INVALID_ACCEPTANCE", `${label} 不能为空`);
  assertSafeReportText(text, label);
  return text;
}

function verifyReportBinding(
  context: Artifact & { resolvedPath: string },
  report: Artifact & { resolvedPath: string },
  label: string,
): Report {
  const rawContext = readJsonArtifact(context, `${label}.context`);
  const parsedContext = object(rawContext, `${label}.context`);
  if (!isEvidenceSchema(parsedContext.schema))
    throw new InputError(
      "INVALID_ACCEPTANCE_REPORT",
      `${label}.report 只能绑定可重算的 evidence context`,
    );
  const rawReport = readJsonArtifact(
    report,
    `${label}.report`,
    "INVALID_ACCEPTANCE_REPORT",
  );
  return validateReport(rawReport, rawContext as Evidence);
}

function verifyResponseReportConsistency(
  response: string,
  report: Report,
  label: string,
) {
  if (!report.baziReasoning.length && !report.ziweiReasoning.length)
    return "not-applicable" as const;
  const upgrade = findUnresolvedPremiseUpgrade(response);
  if (upgrade)
    throw new InputError(
      "RESPONSE_REPORT_CONTRADICTION",
      `${label}.response 以“${upgrade.match}”把报告保留的条件性或未决前提写成已裁定结论`,
    );
  return "pass" as const;
}

type ResponseClaimRef = {
  candidate: string;
  topic: string;
};

const responseParagraphs = (response: string) =>
  response
    .trim()
    .split(/\r?\n[ \t]*\r?\n/u)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);

const responseClaimRefKey = (ref: ResponseClaimRef) =>
  `${ref.candidate}:${ref.topic}`;

function verifyResponseClaimsBinding(
  response: string,
  responseClaims: Artifact & { resolvedPath: string },
  reportArtifact: Artifact,
  report: Report,
  label: string,
) {
  const raw = readJsonArtifact(
    responseClaims,
    `${label}.responseClaims`,
    "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
  );
  const parsed = object(raw, `${label}.responseClaims`);
  if (parsed.schema !== "whoami.response-claims.v1")
    throw new InputError(
      "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
      `${label}.responseClaims schema 无效`,
    );
  if (
    nonEmpty(parsed.reportSha256, `${label}.responseClaims.reportSha256`) !==
    reportArtifact.sha256
  )
    throw new InputError(
      "RESPONSE_CLAIMS_MISMATCH",
      `${label}.responseClaims 没有绑定当前 report 哈希`,
    );
  if (!Array.isArray(parsed.paragraphs) || !parsed.paragraphs.length)
    throw new InputError(
      "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
      `${label}.responseClaims.paragraphs 至少包含一项`,
    );
  const actualParagraphs = responseParagraphs(response);
  if (parsed.paragraphs.length !== actualParagraphs.length)
    throw new InputError(
      "RESPONSE_CLAIMS_MISMATCH",
      `${label}.responseClaims 必须逐段覆盖完整 response`,
    );
  const sections = new Map(
    report.sections.map((section) => [section.id, section]),
  );
  const ids = new Set<string>();
  parsed.paragraphs.forEach((rawParagraph, paragraphIndex) => {
    const paragraph = object(
      rawParagraph,
      `${label}.responseClaims.paragraphs[${paragraphIndex}]`,
    );
    const id = nonEmpty(
      paragraph.id,
      `${label}.responseClaims.paragraphs[${paragraphIndex}].id`,
    );
    if (ids.has(id))
      throw new InputError(
        "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
        `${label}.responseClaims 段落 id 不能重复`,
      );
    ids.add(id);
    const text = nonEmpty(
      paragraph.text,
      `${label}.responseClaims.paragraphs[${paragraphIndex}].text`,
    );
    if (text !== actualParagraphs[paragraphIndex])
      throw new InputError(
        "RESPONSE_CLAIMS_MISMATCH",
        `${label}.responseClaims 第 ${paragraphIndex + 1} 段与 response 不一致`,
      );
    if (!Array.isArray(paragraph.reportClaims) || !paragraph.reportClaims.length)
      throw new InputError(
        "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
        `${label}.responseClaims 第 ${paragraphIndex + 1} 段必须绑定至少一个 report claim`,
      );
    const reportClaimKeys = new Set<string>();
    const expectedReasoning = new Map<string, ResponseClaimRef>();
    let expectedStatus: "conditional" | "unresolved" | "not-applicable" =
      "not-applicable";
    paragraph.reportClaims.forEach((rawClaim, claimRefIndex) => {
      const claimRef = object(
        rawClaim,
        `${label}.responseClaims.paragraphs[${paragraphIndex}].reportClaims[${claimRefIndex}]`,
      );
      const sectionId = nonEmpty(
        claimRef.section,
        `${label}.responseClaims.reportClaims.section`,
      );
      const claimIndex = integer(
        claimRef.claimIndex,
        `${label}.responseClaims.reportClaims.claimIndex`,
      );
      const key = `${sectionId}:${claimIndex}`;
      if (reportClaimKeys.has(key))
        throw new InputError(
          "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
          `${label}.responseClaims 的 report claim 引用不能重复`,
        );
      reportClaimKeys.add(key);
      const section = sections.get(sectionId);
      const claim = section?.claims[claimIndex];
      if (!claim)
        throw new InputError(
          "RESPONSE_CLAIMS_MISMATCH",
          `${label}.responseClaims 引用了不存在的 report claim`,
        );
      for (const ref of claim.reasoningRefs)
        expectedReasoning.set(responseClaimRefKey(ref), ref);
      if (claim.premiseStatus === "unresolved") expectedStatus = "unresolved";
      else if (
        claim.premiseStatus === "conditional" &&
        expectedStatus === "not-applicable"
      )
        expectedStatus = "conditional";
    });
    if (!Array.isArray(paragraph.reasoningRefs))
      throw new InputError(
        "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
        `${label}.responseClaims.reasoningRefs 必须是数组`,
      );
    const providedReasoning = new Map<string, ResponseClaimRef>();
    paragraph.reasoningRefs.forEach((rawRef, reasoningIndex) => {
      const ref = object(
        rawRef,
        `${label}.responseClaims.paragraphs[${paragraphIndex}].reasoningRefs[${reasoningIndex}]`,
      );
      const value = {
        candidate: nonEmpty(
          ref.candidate,
          `${label}.responseClaims.reasoningRef.candidate`,
        ),
        topic: nonEmpty(
          ref.topic,
          `${label}.responseClaims.reasoningRef.topic`,
        ),
      };
      const key = responseClaimRefKey(value);
      if (providedReasoning.has(key))
        throw new InputError(
          "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
          `${label}.responseClaims 的论证引用不能重复`,
        );
      providedReasoning.set(key, value);
    });
    if (
      providedReasoning.size !== expectedReasoning.size ||
      [...expectedReasoning.keys()].some((key) => !providedReasoning.has(key))
    )
      throw new InputError(
        "RESPONSE_CLAIMS_MISMATCH",
        `${label}.responseClaims 的 reasoningRefs 必须与所引 report claims 完全一致`,
      );
    for (const topic of requiredReasoningTopics(text))
      if (![...providedReasoning.values()].some((ref) => ref.topic === topic))
        throw new InputError(
          "MISSING_RESPONSE_REASONING_LINK",
          `${label}.responseClaims 第 ${paragraphIndex + 1} 段提到 ${topic}，但所引 report claims 没有对应论证`,
        );
    if (paragraph.premiseStatus !== expectedStatus)
      throw new InputError(
        "RESPONSE_CLAIMS_MISMATCH",
        `${label}.responseClaims 第 ${paragraphIndex + 1} 段的 premiseStatus 与所引 report claims 不一致`,
      );
  });
  return "pass" as const;
}

function verifyContextBinding(
  input: Artifact & { resolvedPath: string },
  context: Artifact & { resolvedPath: string },
  label: string,
) {
  const rawInput = readJsonArtifact(input, `${label}.input`);
  const rawContext = readJsonArtifact(context, `${label}.context`);
  const parsedContext = object(rawContext, `${label}.context`);
  const evidenceContext = isEvidenceSchema(parsedContext.schema);
  const needsInputContext =
    parsedContext.schema === "whoami.chart.v1" &&
    parsedContext.status === "needs-input";
  const errorContext =
    parsedContext.schema === "whoami.error.v1" &&
    parsedContext.status === "error" &&
    parsedContext.command === "context";
  if (!evidenceContext && !needsInputContext && !errorContext)
    throw new InputError(
      "INVALID_ACCEPTANCE_CONTEXT",
      `${label}.context 必须是 evidence、needs-input chart 或 context error`,
    );
  if (
    !Array.isArray(parsedContext.years) ||
    parsedContext.years.some((year) => !Number.isInteger(year))
  )
    throw new InputError(
      "INVALID_ACCEPTANCE_CONTEXT",
      `${label}.context years 必须是整数数组`,
    );
  let expected: unknown;
  try {
    const chart = buildChart(
      rawInput,
      parsedContext.years as number[],
      parsedContext.granularity === "month" ? "month" : "year",
    );
    if (errorContext)
      throw new InputError(
        "ACCEPTANCE_CONTEXT_MISMATCH",
        `${label}.context 声称计算失败，但对应 input 与 years 可以生成 context`,
      );
    if (needsInputContext) expected = chart;
    else {
      if (chart.status === "needs-input")
        throw new Error("输入不足，无法生成 evidence");
      // 按冻结 context 记录的 evidence 版本重算，历史样例不因新增事实失效。
      expected = buildEvidence(chart, parsedContext.schema as Parameters<typeof buildEvidence>[1]);
    }
  } catch (error) {
    if (errorContext && error instanceof InputError) {
      if (error.code === "ACCEPTANCE_CONTEXT_MISMATCH") throw error;
      expected = contextErrorOutcome(error, parsedContext.years as number[]);
    } else
    throw new InputError(
      "ACCEPTANCE_CONTEXT_MISMATCH",
      `${label}.context 无法由对应 input 与 years 重算：${error instanceof Error ? error.message : "unknown error"}`,
    );
  }
  if (!isDeepStrictEqual(rawContext, expected))
    throw new InputError(
      "ACCEPTANCE_CONTEXT_MISMATCH",
      `${label}.context 不是由对应 input、years 与当前引擎生成的同类结果`,
    );
}

function verifyReview(raw: unknown) {
  const review = object(raw, "review");
  if (
    typeof review.status !== "string" ||
    !["PASS", "PARTIAL", "FAIL"].includes(review.status)
  )
    throw new InputError("INVALID_ACCEPTANCE", "review.status 无效");
  const status = review.status as "PASS" | "PARTIAL" | "FAIL";
  const counts = {
    factErrors: integer(review.factErrors, "review.factErrors"),
    premiseOmissions: integer(
      review.premiseOmissions,
      "review.premiseOmissions",
    ),
    candidateMixing: integer(
      review.candidateMixing,
      "review.candidateMixing",
    ),
    unsupportedTimingClaims: integer(
      review.unsupportedTimingClaims,
      "review.unsupportedTimingClaims",
    ),
    unsafeClaims: integer(review.unsafeClaims, "review.unsafeClaims"),
  };
  const issueCount = Object.values(counts).reduce(
    (sum, value) => sum + value,
    0,
  );
  if (status === "PASS" && issueCount > 0)
    throw new InputError(
      "INVALID_ACCEPTANCE",
      "存在已记录问题时不能把 review.status 标为 PASS",
    );
  return { status, counts };
}

export function checkAcceptanceManifest(
  raw: unknown,
  manifestPath: string,
  options: { trustedRuntimeKeyPath?: string } = {},
) {
  const manifest = object(raw, "acceptance manifest");
  if (manifest.schema !== "whoami.acceptance-run.v1")
    throw new InputError("INVALID_ACCEPTANCE", "验收清单 schema 无效");
  const baseDir = dirname(resolve(manifestPath));
  const suiteId = nonEmpty(manifest.suiteId, "suiteId");
  const skill = verifyArtifact(manifest.skill, baseDir, "skill");
  const task = verifyArtifact(manifest.task, baseDir, "task");
  const rubric = verifyArtifact(manifest.rubric, baseDir, "rubric");
  if (!Array.isArray(manifest.cases) || !manifest.cases.length)
    throw new InputError("INVALID_ACCEPTANCE", "cases 至少包含一个样例");
  const seen = new Set<string>();
  const cases = manifest.cases.map((rawCase, index) => {
    const item = object(rawCase, `cases[${index}]`);
    const id = nonEmpty(item.id, `cases[${index}].id`);
    if (seen.has(id))
      throw new InputError("INVALID_ACCEPTANCE", "case id 不能重复");
    seen.add(id);
    const input = verifyArtifact(item.input, baseDir, `${id}.input`);
    const context = verifyArtifact(item.context, baseDir, `${id}.context`);
    const response = verifyArtifact(item.response, baseDir, `${id}.response`);
    const report =
      item.report === undefined
        ? null
        : verifyArtifact(item.report, baseDir, `${id}.report`);
    const responseClaims =
      item.responseClaims === undefined
        ? null
        : verifyArtifact(
            item.responseClaims,
            baseDir,
            `${id}.responseClaims`,
          );
    verifyContextBinding(input, context, id);
    const responseText = readResponseArtifact(response, `${id}.response`);
    const validatedReport = report
      ? verifyReportBinding(context, report, id)
      : null;
    if (report && !responseClaims)
      throw new InputError(
        "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
        `${id}.responseClaims 在绑定 report 时为必填`,
      );
    if (!report && responseClaims)
      throw new InputError(
        "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
        `${id}.responseClaims 只能与 report 一起提供`,
      );
    const responseReportPremise = validatedReport
      ? verifyResponseReportConsistency(responseText, validatedReport, id)
      : "not-applicable";
    const responseClaimsValidation =
      validatedReport && report && responseClaims
        ? verifyResponseClaimsBinding(
            responseText,
            responseClaims,
            report,
            validatedReport,
            id,
          )
        : "not-applicable";
    return {
      id,
      input,
      context,
      response,
      report,
      responseClaims,
      responseReportPremise,
      responseClaimsValidation,
    };
  });
  const verifiedReview = verifyReview(manifest.review);
  const reviewStatus = verifiedReview.status;
  const counts = verifiedReview.counts;
  const runtime = object(manifest.runtime, "runtime");
  const runtimeFields = {
    provider: nonEmpty(runtime.provider, "runtime.provider"),
    model: nonEmpty(runtime.model, "runtime.model"),
    modelVersion: nonEmpty(runtime.modelVersion, "runtime.modelVersion"),
    reasoningEffort: nonEmpty(runtime.reasoningEffort, "runtime.reasoningEffort"),
    temperature: nullableParameter(runtime.temperature, "runtime.temperature"),
    seed: nullableParameter(runtime.seed, "runtime.seed"),
  };
  const receipt =
    runtime.receipt === null
      ? null
      : verifyArtifact(runtime.receipt, baseDir, "runtime.receipt");
  let runtimeAttested = false;
  let runtimeKeyId: string | null = null;
  if (receipt) {
    let rawReceipt: unknown;
    try {
      rawReceipt = JSON.parse(readFileSync(receipt.resolvedPath, "utf8"));
    } catch {
      throw new InputError(
        "INVALID_ACCEPTANCE_RECEIPT",
        "runtime.receipt 必须是合法 JSON",
      );
    }
    const parsed = object(rawReceipt, "runtime receipt");
    if (
      parsed.schema !== "whoami.runtime-receipt.v1" &&
      parsed.schema !== "whoami.runtime-receipt.v2"
    )
      throw new InputError(
        "INVALID_ACCEPTANCE_RECEIPT",
        "runtime receipt schema 无效",
      );
    const runId = nonEmpty(parsed.runId, "runtime receipt.runId");
    const startedAt = absoluteInstant(
      parsed.startedAt,
      "runtime receipt.startedAt",
    );
    const receiptRuntime = object(parsed.runtime, "runtime receipt.runtime");
    const boundRuntime = {
      provider: nonEmpty(receiptRuntime.provider, "runtime receipt.provider"),
      model: nonEmpty(receiptRuntime.model, "runtime receipt.model"),
      modelVersion: nonEmpty(
        receiptRuntime.modelVersion,
        "runtime receipt.modelVersion",
      ),
      reasoningEffort: nonEmpty(
        receiptRuntime.reasoningEffort,
        "runtime receipt.reasoningEffort",
      ),
      temperature: nullableParameter(
        receiptRuntime.temperature,
        "runtime receipt.temperature",
      ),
      seed: nullableParameter(receiptRuntime.seed, "runtime receipt.seed"),
    };
    if (!isDeepStrictEqual(boundRuntime, runtimeFields))
      throw new InputError(
        "ACCEPTANCE_RECEIPT_MISMATCH",
        "runtime receipt 与 manifest 的模型或采样参数不一致",
      );
    const bindings = object(parsed.bindings, "runtime receipt.bindings");
    const boundCases = arrayOfObjects(bindings.cases, "runtime receipt.cases").map(
      (item, index) => ({
        id: nonEmpty(item.id, `runtime receipt.cases[${index}].id`),
        input: nonEmpty(item.input, `runtime receipt.cases[${index}].input`),
        context: nonEmpty(
          item.context,
          `runtime receipt.cases[${index}].context`,
        ),
        response: nonEmpty(
          item.response,
          `runtime receipt.cases[${index}].response`,
        ),
        ...(item.report === undefined
          ? {}
          : {
              report: nonEmpty(
                item.report,
                `runtime receipt.cases[${index}].report`,
              ),
            }),
        ...(item.responseClaims === undefined
          ? {}
          : {
              responseClaims: nonEmpty(
                item.responseClaims,
                `runtime receipt.cases[${index}].responseClaims`,
              ),
            }),
      }),
    );
    const expectedBindings = {
      skill: skill.sha256,
      task: task.sha256,
      cases: cases.map((item) => ({
        id: item.id,
        input: item.input.sha256,
        context: item.context.sha256,
        response: item.response.sha256,
        ...(item.report ? { report: item.report.sha256 } : {}),
        ...(item.responseClaims
          ? { responseClaims: item.responseClaims.sha256 }
          : {}),
      })),
    };
    if (
      !isDeepStrictEqual(
        {
          skill: nonEmpty(bindings.skill, "runtime receipt.bindings.skill"),
          task: nonEmpty(bindings.task, "runtime receipt.bindings.task"),
          cases: boundCases,
        },
        expectedBindings,
      )
    )
      throw new InputError(
        "ACCEPTANCE_RECEIPT_MISMATCH",
        "runtime receipt 未绑定本次 Skill、任务、输入、context、回答、可选报告及结构化答复绑定",
      );
    if (parsed.schema === "whoami.runtime-receipt.v2") {
      if (
        nonEmpty(bindings.rubric, "runtime receipt.bindings.rubric") !==
        rubric.sha256
      )
        throw new InputError(
          "ACCEPTANCE_RECEIPT_MISMATCH",
          "runtime receipt 未绑定本次评审量表",
        );
      if (!options.trustedRuntimeKeyPath)
        throw new InputError(
          "INVALID_ACCEPTANCE_RECEIPT",
          "v2 runtime receipt 需要 --trusted-runtime-key 指定清单外受信公钥",
        );
      const trusted = readTrustedEd25519PublicKey(
        options.trustedRuntimeKeyPath,
      );
      const realBase = realpathSync(baseDir);
      const keyRelative = relative(realBase, trusted.resolvedPath);
      if (
        keyRelative === "" ||
        (!keyRelative.startsWith(`..${sep}`) && !isAbsolute(keyRelative))
      )
        throw new InputError(
          "INVALID_ACCEPTANCE_RECEIPT",
          "trusted runtime key 必须位于验收清单目录树之外",
        );
      if (parsed.attestation === undefined)
        throw new InputError(
          "INVALID_ACCEPTANCE_RECEIPT",
          "v2 runtime receipt 缺少 attestation",
        );
      const attestation = object(parsed.attestation, "runtime attestation");
      if (attestation.algorithm !== "Ed25519")
        throw new InputError(
          "INVALID_ACCEPTANCE_RECEIPT",
          "runtime attestation.algorithm 必须是 Ed25519",
        );
      const keyId = nonEmpty(attestation.keyId, "runtime attestation.keyId");
      if (keyId !== trusted.keyId)
        throw new InputError(
          "ACCEPTANCE_RECEIPT_MISMATCH",
          "runtime attestation.keyId 与受信公钥不一致",
        );
      const signature = decodeCanonicalBase64(
        nonEmpty(attestation.signature, "runtime attestation.signature"),
      );
      const payload = runtimeAttestationPayload({
        suiteId,
        runId,
        startedAt,
        runtime: boundRuntime,
        bindings: {
          skill: expectedBindings.skill,
          task: expectedBindings.task,
          rubric: rubric.sha256,
          cases: expectedBindings.cases,
        },
        review: { status: reviewStatus, ...counts },
      });
      if (!verifyEd25519Attestation(payload, signature, trusted.key))
        throw new InputError(
          "ACCEPTANCE_RECEIPT_MISMATCH",
          "runtime attestation 签名无效",
        );
      runtimeAttested = true;
      runtimeKeyId = trusted.keyId;
    }
  }
  const runtimeBound =
    receipt !== null &&
    !Object.values(runtimeFields).some((value) => value === "UNVERIFIED");
  // v1 proves artifact/metadata binding only. v2 additionally requires an
  // external trust root selected by the verifier.
  const runtimeVerified = runtimeBound && runtimeAttested;
  const status =
    reviewStatus === "FAIL"
      ? "failed"
      : reviewStatus === "PASS" && runtimeVerified
        ? "verified"
        : "partial";
  return {
    schema: "whoami.acceptance-result.v1" as const,
    suiteId,
    status,
    runtimeBound,
    runtimeAttested,
    runtimeVerified,
    runtimeKeyId,
    reviewStatus,
    counts,
    caseChecks: cases.map((item) => ({
      id: item.id,
      responseSafety: "pass" as const,
      reportValidation: item.report ? ("pass" as const) : ("not-applicable" as const),
      responseReportPremise: item.responseReportPremise,
      responseClaimsValidation: item.responseClaimsValidation,
    })),
    artifactCount:
      3 +
      cases.reduce(
        (count, item) =>
          count + 3 + (item.report ? 1 : 0) + (item.responseClaims ? 1 : 0),
        0,
      ) +
      (receipt ? 1 : 0),
    limitations: [
      ...(receipt ? [] : ["缺少可核对的实际模型运行回执。"]),
      ...(receipt && !runtimeAttested
        ? ["v1 回执只完成文件与声明参数绑定，没有受信宿主证明或 provider readback。"]
        : []),
      ...(runtimeBound
        ? []
        : ["模型、版本或采样参数未获完整文件绑定。"]),
      ...(runtimeAttested
        ? []
        : ["运行身份未获独立证明，结果不能升级为 verified。"]),
      "验收只评价给定样例的事实忠实与推理合同，不证明现实预测有效。",
    ],
    bindings: {
      skill: skill.sha256,
      task: task.sha256,
      rubric: rubric.sha256,
      cases: cases.map((item) => ({
        id: item.id,
        input: item.input.sha256,
        context: item.context.sha256,
        response: item.response.sha256,
        ...(item.report ? { report: item.report.sha256 } : {}),
        ...(item.responseClaims
          ? { responseClaims: item.responseClaims.sha256 }
          : {}),
      })),
      runtimeReceipt: receipt?.sha256 ?? null,
    },
  };
}

function arrayOfObjects(value: unknown, label: string) {
  if (!Array.isArray(value))
    throw new InputError("INVALID_ACCEPTANCE_RECEIPT", `${label} 必须是数组`);
  return value.map((item, index) => object(item, `${label}[${index}]`));
}
