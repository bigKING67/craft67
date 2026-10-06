import { InputError } from "./input.js";

type JsonObject = Record<string, unknown>;

export type CodexRuntimeEvidenceInput = {
  codexVersion: string;
  initializeSchema: unknown | null;
  attestationParamsSchema: unknown | null;
  attestationResponseSchema: unknown | null;
  rawResponseSchema: unknown | null;
  threadStartSchema: unknown | null;
};

function optionalSchema(value: unknown | null, label: string): JsonObject | null {
  if (value === null) return null;
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new InputError(
      "INVALID_CODEX_EVIDENCE_SCHEMA",
      `${label} 必须是 JSON object 或 null`,
    );
  return value as JsonObject;
}

function child(value: unknown, key: string): JsonObject | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const nested = (value as JsonObject)[key];
  return nested && typeof nested === "object" && !Array.isArray(nested)
    ? (nested as JsonObject)
    : null;
}

function stringList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((entry): entry is string => typeof entry === "string")
    : [];
}

function descriptionContains(value: unknown, phrase: string) {
  return (
    typeof value === "string" &&
    value.toLocaleLowerCase("en-US").includes(phrase.toLocaleLowerCase("en-US"))
  );
}

function stringProperty(schema: JsonObject | null, property: string) {
  const properties = child(schema, "properties");
  const declaration = properties ? child(properties, property) : null;
  return declaration?.type === "string";
}

function requiredStringProperty(schema: JsonObject | null, property: string) {
  return (
    stringProperty(schema, property) &&
    stringList(schema?.required).includes(property)
  );
}

function attestationCapability(initialize: JsonObject | null) {
  const definitions = child(initialize, "definitions");
  const capabilities = definitions
    ? child(definitions, "InitializeCapabilities")
    : null;
  const properties = child(capabilities, "properties");
  return properties ? child(properties, "requestAttestation") : null;
}

function threadRawEvents(threadStart: JsonObject | null) {
  const properties = child(threadStart, "properties");
  return properties ? child(properties, "experimentalRawEvents") : null;
}

function declaresWhoamiBinding(params: JsonObject | null) {
  const properties = child(params, "properties");
  if (!properties) return false;
  const names = new Set(Object.keys(properties));
  const payloadDeclared = names.has("payload");
  const bindingDeclared = [
    "manifest",
    "bindings",
    "suiteId",
    "artifacts",
  ].some((name) => names.has(name));
  return payloadDeclared && bindingDeclared;
}

export function auditCodexRuntimeEvidence(input: CodexRuntimeEvidenceInput) {
  if (typeof input.codexVersion !== "string" || !input.codexVersion.trim())
    throw new InputError(
      "INVALID_CODEX_EVIDENCE_SCHEMA",
      "codexVersion 必须是非空文字",
    );

  const initialize = optionalSchema(input.initializeSchema, "initializeSchema");
  const attestationParams = optionalSchema(
    input.attestationParamsSchema,
    "attestationParamsSchema",
  );
  const attestationResponse = optionalSchema(
    input.attestationResponseSchema,
    "attestationResponseSchema",
  );
  const rawResponse = optionalSchema(input.rawResponseSchema, "rawResponseSchema");
  const threadStart = optionalSchema(input.threadStartSchema, "threadStartSchema");

  const capability = attestationCapability(initialize);
  const rawEvents = threadRawEvents(threadStart);
  const token = child(child(attestationResponse, "properties"), "token");
  const capabilityDeclared = capability?.type === "boolean";
  const upstreamHeaderDeclared = descriptionContains(
    capability?.description,
    "x-oai-attestation",
  );
  const opaqueClientTokenDeclared =
    requiredStringProperty(attestationResponse, "token") &&
    descriptionContains(token?.description, "opaque client attestation token");
  const manifestPayloadBindingDeclared =
    declaresWhoamiBinding(attestationParams);
  const experimentalOptInDeclared = rawEvents?.type === "boolean";
  const internalOnlyDeclared =
    descriptionContains(rawEvents?.description, "internal use only") ||
    descriptionContains(rawResponse?.description, "internal-only");
  const responseIdDeclared = requiredStringProperty(rawResponse, "responseId");
  const threadIdDeclared = requiredStringProperty(rawResponse, "threadId");
  const turnIdDeclared = requiredStringProperty(rawResponse, "turnId");

  const reasons: string[] = [];
  if (
    capabilityDeclared &&
    upstreamHeaderDeclared &&
    opaqueClientTokenDeclared &&
    !manifestPayloadBindingDeclared
  )
    reasons.push("TRANSPORT_ATTESTATION_NOT_WHOAMI_BOUND");
  else if (!manifestPayloadBindingDeclared)
    reasons.push("WHOAMI_ATTESTATION_BINDING_UNDECLARED");
  if (experimentalOptInDeclared || internalOnlyDeclared)
    reasons.push("RAW_RESPONSE_EVENT_INTERNAL_OR_EXPERIMENTAL");
  if (responseIdDeclared)
    reasons.push("RESPONSE_ID_WITHOUT_PROVIDER_READBACK");
  reasons.push("LIVE_PROVIDER_READBACK_NOT_PERFORMED");

  return {
    schema: "whoami.codex-runtime-evidence-audit.v1" as const,
    codexVersion: input.codexVersion.trim(),
    transportAttestation: {
      capabilityDeclared,
      upstreamHeaderDeclared,
      opaqueClientTokenDeclared,
      manifestPayloadBindingDeclared,
      acceptanceEligible: false,
    },
    rawResponseCapture: {
      experimentalOptInDeclared,
      internalOnlyDeclared,
      responseIdDeclared,
      threadIdDeclared,
      turnIdDeclared,
      liveProviderReadbackPerformed: false,
      acceptanceEligible: false,
    },
    decision: {
      status: "insufficient" as const,
      canUpgradeAcceptance: false,
      reasons,
    },
  };
}
