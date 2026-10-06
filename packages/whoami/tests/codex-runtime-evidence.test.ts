import { test } from "node:test";
import assert from "node:assert/strict";
import { auditCodexRuntimeEvidence } from "../src/codex-runtime-evidence.js";
import { InputError } from "../src/input.js";

const observedSchemas = {
  codexVersion: "codex-cli 0.156.1",
  initializeSchema: {
    definitions: {
      InitializeCapabilities: {
        properties: {
          requestAttestation: {
            type: "boolean",
            description:
              "Opt into attestation/generate requests for upstream x-oai-attestation.",
          },
        },
      },
    },
  },
  attestationParamsSchema: { type: "object" },
  attestationResponseSchema: {
    properties: {
      token: {
        type: "string",
        description: "Opaque client attestation token.",
      },
    },
    required: ["token"],
    type: "object",
  },
  rawResponseSchema: {
    description:
      "Internal-only notification containing one upstream completion.",
    properties: {
      responseId: { type: "string" },
      threadId: { type: "string" },
      turnId: { type: "string" },
    },
    required: ["responseId", "threadId", "turnId"],
    type: "object",
  },
  threadStartSchema: {
    properties: {
      experimentalRawEvents: {
        type: "boolean",
        description: "This is for internal use only.",
      },
    },
    type: "object",
  },
};

test("识别 Codex 传输 attestation 与内部 response ID，但拒绝升级验收", () => {
  const result = auditCodexRuntimeEvidence(observedSchemas);
  assert.equal(result.schema, "whoami.codex-runtime-evidence-audit.v1");
  assert.deepEqual(result.transportAttestation, {
    capabilityDeclared: true,
    upstreamHeaderDeclared: true,
    opaqueClientTokenDeclared: true,
    manifestPayloadBindingDeclared: false,
    acceptanceEligible: false,
  });
  assert.deepEqual(result.rawResponseCapture, {
    experimentalOptInDeclared: true,
    internalOnlyDeclared: true,
    responseIdDeclared: true,
    threadIdDeclared: true,
    turnIdDeclared: true,
    liveProviderReadbackPerformed: false,
    acceptanceEligible: false,
  });
  assert.equal(result.decision.status, "insufficient");
  assert.equal(result.decision.canUpgradeAcceptance, false);
  assert.deepEqual(result.decision.reasons, [
    "TRANSPORT_ATTESTATION_NOT_WHOAMI_BOUND",
    "RAW_RESPONSE_EVENT_INTERNAL_OR_EXPERIMENTAL",
    "RESPONSE_ID_WITHOUT_PROVIDER_READBACK",
    "LIVE_PROVIDER_READBACK_NOT_PERFORMED",
  ]);
});

test("schema 缺失时失败封闭，不把未知能力判为运行实证", () => {
  const result = auditCodexRuntimeEvidence({
    codexVersion: "codex-cli synthetic",
    initializeSchema: null,
    attestationParamsSchema: null,
    attestationResponseSchema: null,
    rawResponseSchema: null,
    threadStartSchema: null,
  });
  assert.equal(result.transportAttestation.capabilityDeclared, false);
  assert.equal(result.transportAttestation.acceptanceEligible, false);
  assert.equal(result.rawResponseCapture.responseIdDeclared, false);
  assert.equal(result.rawResponseCapture.acceptanceEligible, false);
  assert.equal(result.decision.canUpgradeAcceptance, false);
  assert.deepEqual(result.decision.reasons, [
    "WHOAMI_ATTESTATION_BINDING_UNDECLARED",
    "LIVE_PROVIDER_READBACK_NOT_PERFORMED",
  ]);
});

test("拒绝空版本和非 object schema", () => {
  assert.throws(
    () => auditCodexRuntimeEvidence({ ...observedSchemas, codexVersion: " " }),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "INVALID_CODEX_EVIDENCE_SCHEMA",
  );
  assert.throws(
    () =>
      auditCodexRuntimeEvidence({
        ...observedSchemas,
        rawResponseSchema: [],
      }),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "INVALID_CODEX_EVIDENCE_SCHEMA",
  );
});
