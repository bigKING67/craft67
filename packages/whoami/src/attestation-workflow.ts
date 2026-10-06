import { createHash } from "node:crypto";
import { realpathSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { isDeepStrictEqual } from "node:util";
import { Temporal } from "@js-temporal/polyfill";
import { checkAcceptanceManifest } from "./acceptance.js";
import {
  decodeCanonicalBase64,
  readTrustedEd25519PublicKey,
  runtimeAttestationPayload,
  verifyEd25519Attestation,
  type AttestedReview,
  type RuntimeBindings,
  type RuntimeIdentity,
} from "./attestation.js";
import { InputError, object } from "./input.js";

const digest = (data: Buffer) =>
  createHash("sha256").update(data).digest("hex");

const nonEmpty = (value: unknown, label: string) => {
  if (typeof value !== "string" || !value.trim())
    throw new InputError(
      "INVALID_ATTESTATION_REQUEST",
      `${label} 必须是非空文字`,
    );
  return value.trim();
};

const nullableParameter = (value: unknown, label: string) => {
  if (value === null) return null;
  if (typeof value === "string" && value.trim()) return value.trim();
  if (typeof value === "number" && Number.isFinite(value)) return value;
  throw new InputError(
    "INVALID_ATTESTATION_REQUEST",
    `${label} 必须显式为 null、有限数字或非空文字`,
  );
};

function runtimeIdentity(raw: unknown, label: string): RuntimeIdentity {
  const runtime = object(raw, label);
  return {
    provider: nonEmpty(runtime.provider, `${label}.provider`),
    model: nonEmpty(runtime.model, `${label}.model`),
    modelVersion: nonEmpty(runtime.modelVersion, `${label}.modelVersion`),
    reasoningEffort: nonEmpty(
      runtime.reasoningEffort,
      `${label}.reasoningEffort`,
    ),
    temperature: nullableParameter(runtime.temperature, `${label}.temperature`),
    seed: nullableParameter(runtime.seed, `${label}.seed`),
  };
}

function absoluteInstant(value: unknown, label: string) {
  const text = nonEmpty(value, label);
  try {
    Temporal.Instant.from(text);
  } catch {
    throw new InputError(
      "INVALID_ATTESTATION_REQUEST",
      `${label} 必须是带时区或 Z 的绝对时刻`,
    );
  }
  return text;
}

function runtimeRun(raw: unknown) {
  const run = object(raw, "runtime run");
  if (run.schema !== "whoami.runtime-run.v1")
    throw new InputError(
      "INVALID_ATTESTATION_REQUEST",
      "runtime run schema 无效",
    );
  return {
    schema: "whoami.runtime-run.v1" as const,
    runId: nonEmpty(run.runId, "runtime run.runId"),
    startedAt: absoluteInstant(run.startedAt, "runtime run.startedAt"),
    runtime: runtimeIdentity(run.runtime, "runtime run.runtime"),
  };
}

export function prepareRuntimeAttestation(
  rawManifest: unknown,
  manifestPath: string,
  rawRun: unknown,
) {
  const manifest = object(rawManifest, "acceptance manifest");
  const manifestRuntime = object(manifest.runtime, "runtime");
  if (manifestRuntime.receipt !== null)
    throw new InputError(
      "INVALID_ATTESTATION_REQUEST",
      "签发前 manifest.runtime.receipt 必须显式为 null",
    );
  const checked = checkAcceptanceManifest(rawManifest, manifestPath);
  const normalizedManifestRuntime = runtimeIdentity(
    manifestRuntime,
    "manifest.runtime",
  );
  const run = runtimeRun(rawRun);
  if (!isDeepStrictEqual(run.runtime, normalizedManifestRuntime))
    throw new InputError(
      "ATTESTATION_REQUEST_MISMATCH",
      "runtime run 与 manifest 的模型或采样参数不一致",
    );
  const bindings: RuntimeBindings = {
    skill: checked.bindings.skill,
    task: checked.bindings.task,
    rubric: checked.bindings.rubric,
    cases: checked.bindings.cases,
  };
  const review: AttestedReview = {
    status: checked.reviewStatus,
    ...checked.counts,
  };
  const payload = runtimeAttestationPayload({
    suiteId: checked.suiteId,
    runId: run.runId,
    startedAt: run.startedAt,
    runtime: run.runtime,
    bindings,
    review,
  });
  return {
    schema: "whoami.runtime-attestation-request.v1" as const,
    suiteId: checked.suiteId,
    run,
    bindings,
    review,
    payload: {
      encoding: "base64" as const,
      sha256: digest(payload),
      bytes: payload.byteLength,
      data: payload.toString("base64"),
    },
  };
}

function outsideTrustedKey(path: string, manifestPath: string) {
  const trusted = readTrustedEd25519PublicKey(path);
  const realBase = realpathSync(dirname(resolve(manifestPath)));
  const keyRelative = relative(realBase, trusted.resolvedPath);
  if (
    keyRelative === "" ||
    (!keyRelative.startsWith(`..${sep}`) && !isAbsolute(keyRelative))
  )
    throw new InputError(
      "INVALID_ATTESTATION_REQUEST",
      "trusted runtime key 必须位于验收清单目录树之外",
    );
  return trusted;
}

export function finalizeRuntimeAttestation(
  rawManifest: unknown,
  manifestPath: string,
  rawRequest: unknown,
  signatureText: string,
  trustedRuntimeKeyPath: string,
) {
  const request = object(rawRequest, "attestation request");
  const expected = prepareRuntimeAttestation(
    rawManifest,
    manifestPath,
    request.run,
  );
  if (!isDeepStrictEqual(rawRequest, expected))
    throw new InputError(
      "ATTESTATION_REQUEST_MISMATCH",
      "attestation request 与当前 manifest、runtime run 或 canonical payload 不一致",
    );
  const payload = decodeCanonicalBase64(expected.payload.data);
  if (
    payload.byteLength !== expected.payload.bytes ||
    digest(payload) !== expected.payload.sha256
  )
    throw new InputError(
      "ATTESTATION_REQUEST_MISMATCH",
      "attestation request payload 摘要不一致",
    );
  const signature = decodeCanonicalBase64(
    nonEmpty(signatureText, "signature"),
  );
  const trusted = outsideTrustedKey(trustedRuntimeKeyPath, manifestPath);
  if (!verifyEd25519Attestation(payload, signature, trusted.key))
    throw new InputError(
      "ATTESTATION_REQUEST_MISMATCH",
      "runtime attestation 签名无效",
    );
  const receipt = {
    schema: "whoami.runtime-receipt.v2" as const,
    runId: expected.run.runId,
    startedAt: expected.run.startedAt,
    runtime: expected.run.runtime,
    bindings: expected.bindings,
    attestation: {
      algorithm: "Ed25519" as const,
      keyId: trusted.keyId,
      signature: signature.toString("base64"),
    },
  };
  const content = Buffer.from(JSON.stringify(receipt, null, 2) + "\n");
  return {
    schema: "whoami.runtime-attestation-finalization.v1" as const,
    receipt,
    serializedReceipt: {
      encoding: "base64" as const,
      sha256: digest(content),
      bytes: content.byteLength,
      data: content.toString("base64"),
    },
    keyId: trusted.keyId,
    payloadSha256: expected.payload.sha256,
  };
}
