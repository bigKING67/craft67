import { test } from "node:test";
import assert from "node:assert/strict";
import {
  createHash,
  generateKeyPairSync,
  sign,
} from "node:crypto";
import {
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import {
  finalizeRuntimeAttestation,
  prepareRuntimeAttestation,
} from "../src/attestation-workflow.js";
import { checkAcceptanceManifest } from "../src/acceptance.js";
import { contextFor } from "../src/evidence.js";

const hash = (value: string | Buffer) =>
  createHash("sha256").update(value).digest("hex");

function fixture() {
  const dir = mkdtempSync(join(tmpdir(), "whoami-attestation-flow-"));
  const artifact = (path: string, content: string) => {
    writeFileSync(join(dir, path), content);
    return { path, sha256: hash(content), bytes: Buffer.byteLength(content) };
  };
  const inputValue = {
    calendar: "solar",
    date: "2000-08-16",
    time: "04:00",
    place: "合成",
    longitude: 120,
    timeZone: "Asia/Shanghai",
    gender: "female",
  };
  const input = artifact("input.json", JSON.stringify(inputValue) + "\n");
  const context = artifact(
    "context.json",
    JSON.stringify(contextFor(inputValue, [2026])) + "\n",
  );
  const runtime = {
    provider: "synthetic-host",
    model: "synthetic-model",
    modelVersion: "2026-09-24",
    reasoningEffort: "high",
    temperature: null,
    seed: "fixed",
  };
  const manifest = {
    schema: "whoami.acceptance-run.v1",
    suiteId: "attestation-workflow-synthetic",
    skill: artifact("SKILL.snapshot.md", "synthetic skill\n"),
    task: artifact("task.md", "synthetic task\n"),
    rubric: artifact("rubric.md", "synthetic rubric\n"),
    cases: [
      {
        id: "case-01",
        input,
        context,
        response: artifact("response.md", "synthetic response\n"),
      },
    ],
    runtime: { ...runtime, receipt: null },
    review: {
      status: "PASS",
      factErrors: 0,
      premiseOmissions: 0,
      candidateMixing: 0,
      unsupportedTimingClaims: 0,
      unsafeClaims: 0,
    },
  };
  const run = {
    schema: "whoami.runtime-run.v1",
    runId: "synthetic-run-001",
    startedAt: "2026-09-24T00:00:00Z",
    runtime,
  };
  const manifestPath = join(dir, "manifest-draft.json");
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\n");
  return { dir, manifestPath, manifest, run, runtime };
}

test("签发请求从已复算 manifest 生成 canonical payload，拒绝错绑运行", () => {
  const setup = fixture();
  try {
    const request = prepareRuntimeAttestation(
      setup.manifest,
      setup.manifestPath,
      setup.run,
    );
    const payload = Buffer.from(request.payload.data, "base64");
    assert.equal(request.schema, "whoami.runtime-attestation-request.v1");
    assert.equal(request.payload.encoding, "base64");
    assert.equal(request.payload.bytes, payload.byteLength);
    assert.equal(request.payload.sha256, hash(payload));
    const claims = JSON.parse(payload.toString("utf8"));
    assert.equal(claims.schema, "whoami.runtime-attestation.v2");
    assert.equal(claims.bindings.rubric, setup.manifest.rubric.sha256);
    assert.deepEqual(claims.review, setup.manifest.review);
    assert.throws(
      () =>
        prepareRuntimeAttestation(
          setup.manifest,
          setup.manifestPath,
          {
            ...setup.run,
            runtime: { ...setup.runtime, model: "different-model" },
          },
        ),
      /runtime run 与 manifest 的模型或采样参数不一致/,
    );
    assert.throws(
      () =>
        prepareRuntimeAttestation(
          {
            ...setup.manifest,
            runtime: {
              ...setup.manifest.runtime,
              receipt: { path: "stale.json", sha256: "0", bytes: 0 },
            },
          },
          setup.manifestPath,
          setup.run,
        ),
      /receipt 必须显式为 null/,
    );
  } finally {
    rmSync(setup.dir, { recursive: true, force: true });
  }
});

test("签发请求把前向样例的 report 与 responseClaims 哈希纳入逐 case bindings", () => {
  const manifestPath = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-006/manifest.json",
  );
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const run = {
    schema: "whoami.runtime-run.v1",
    runId: "semantic-forward-006-binding-probe",
    startedAt: "2026-09-24T00:00:00Z",
    runtime: {
      provider: manifest.runtime.provider,
      model: manifest.runtime.model,
      modelVersion: manifest.runtime.modelVersion,
      reasoningEffort: manifest.runtime.reasoningEffort,
      temperature: manifest.runtime.temperature,
      seed: manifest.runtime.seed,
    },
  };
  const request = prepareRuntimeAttestation(manifest, manifestPath, run);
  assert.equal(
    request.bindings.cases[0].report,
    manifest.cases[0].report.sha256,
  );
  assert.equal(
    request.bindings.cases[0].responseClaims,
    manifest.cases[0].responseClaims.sha256,
  );
  const claims = JSON.parse(
    Buffer.from(request.payload.data, "base64").toString("utf8"),
  );
  assert.equal(
    claims.bindings.cases[0].report,
    manifest.cases[0].report.sha256,
  );
  assert.equal(
    claims.bindings.cases[0].responseClaims,
    manifest.cases[0].responseClaims.sha256,
  );
});

test("外部签名经清单外公钥验证后只返回精确 v2 回执字节", () => {
  const setup = fixture();
  const trustDir = mkdtempSync(join(tmpdir(), "whoami-attestation-trust-"));
  try {
    const { publicKey, privateKey } = generateKeyPairSync("ed25519");
    const publicKeyPath = join(trustDir, "runtime-public.pem");
    writeFileSync(
      publicKeyPath,
      publicKey.export({ format: "pem", type: "spki" }),
    );
    const request = prepareRuntimeAttestation(
      setup.manifest,
      setup.manifestPath,
      setup.run,
    );
    const signature = sign(
      null,
      Buffer.from(request.payload.data, "base64"),
      privateKey,
    ).toString("base64");
    const before = readdirSync(setup.dir).sort();
    const finalized = finalizeRuntimeAttestation(
      setup.manifest,
      setup.manifestPath,
      request,
      signature,
      publicKeyPath,
    );
    assert.equal(
      finalized.schema,
      "whoami.runtime-attestation-finalization.v1",
    );
    assert.deepEqual(readdirSync(setup.dir).sort(), before);
    const receiptContent = Buffer.from(
      finalized.serializedReceipt.data,
      "base64",
    );
    assert.equal(receiptContent.byteLength, finalized.serializedReceipt.bytes);
    assert.equal(hash(receiptContent), finalized.serializedReceipt.sha256);
    assert.deepEqual(JSON.parse(receiptContent.toString("utf8")), finalized.receipt);
    writeFileSync(join(setup.dir, "runtime-receipt.json"), receiptContent, {
      flag: "wx",
      mode: 0o600,
    });
    const receiptArtifact = {
      path: "runtime-receipt.json",
      sha256: finalized.serializedReceipt.sha256,
      bytes: finalized.serializedReceipt.bytes,
    };
    const result = checkAcceptanceManifest(
      {
        ...setup.manifest,
        runtime: {
          ...setup.manifest.runtime,
          receipt: receiptArtifact,
        },
      },
      join(setup.dir, "manifest-final.json"),
      { trustedRuntimeKeyPath: publicKeyPath },
    );
    assert.equal(result.status, "verified");
    assert.equal(result.runtimeVerified, true);
    assert.throws(
      () =>
        finalizeRuntimeAttestation(
          setup.manifest,
          setup.manifestPath,
          {
            ...request,
            review: { ...request.review, status: "PARTIAL" },
          },
          signature,
          publicKeyPath,
        ),
      /request 与当前 manifest/,
    );
    assert.throws(
      () =>
        finalizeRuntimeAttestation(
          setup.manifest,
          setup.manifestPath,
          request,
          sign(null, Buffer.from("wrong"), privateKey).toString("base64"),
          publicKeyPath,
        ),
      /签名无效/,
    );
    writeFileSync(
      join(setup.dir, "inside-public.pem"),
      publicKey.export({ format: "pem", type: "spki" }),
    );
    assert.throws(
      () =>
        finalizeRuntimeAttestation(
          setup.manifest,
          setup.manifestPath,
          request,
          signature,
          join(setup.dir, "inside-public.pem"),
        ),
      /清单目录树之外/,
    );
  } finally {
    rmSync(setup.dir, { recursive: true, force: true });
    rmSync(trustDir, { recursive: true, force: true });
  }
});

test("CLI 完成 prepare、外部签名、finalize 与 acceptance-check 闭环", () => {
  const setup = fixture();
  const trustDir = mkdtempSync(join(tmpdir(), "whoami-attestation-cli-trust-"));
  try {
    const runPath = join(setup.dir, "runtime-run.json");
    writeFileSync(runPath, JSON.stringify(setup.run, null, 2) + "\n");
    const prepared = spawnSync(
      process.execPath,
      [
        "--import",
        "tsx",
        "src/cli.ts",
        "attestation-prepare",
        "--manifest",
        setup.manifestPath,
        "--run",
        runPath,
      ],
      { encoding: "utf8" },
    );
    assert.equal(prepared.status, 0, prepared.stderr);
    const request = JSON.parse(prepared.stdout);
    const requestPath = join(setup.dir, "attestation-request.json");
    writeFileSync(requestPath, JSON.stringify(request, null, 2) + "\n");
    const { publicKey, privateKey } = generateKeyPairSync("ed25519");
    const publicKeyPath = join(trustDir, "runtime-public.pem");
    writeFileSync(
      publicKeyPath,
      publicKey.export({ format: "pem", type: "spki" }),
    );
    const signaturePath = join(setup.dir, "signature.txt");
    writeFileSync(
      signaturePath,
      sign(null, Buffer.from(request.payload.data, "base64"), privateKey).toString(
        "base64",
      ) + "\n",
    );
    const finalized = spawnSync(
      process.execPath,
      [
        "--import",
        "tsx",
        "src/cli.ts",
        "attestation-finalize",
        "--manifest",
        setup.manifestPath,
        "--request",
        requestPath,
        "--signature",
        signaturePath,
        "--trusted-runtime-key",
        publicKeyPath,
      ],
      { encoding: "utf8" },
    );
    assert.equal(finalized.status, 0, finalized.stderr);
    const finalization = JSON.parse(finalized.stdout);
    const rejectedOutput = spawnSync(
      process.execPath,
      [
        "--import",
        "tsx",
        "src/cli.ts",
        "attestation-finalize",
        "--manifest",
        setup.manifestPath,
        "--request",
        requestPath,
        "--signature",
        signaturePath,
        "--trusted-runtime-key",
        publicKeyPath,
        "--output",
        join(setup.dir, "must-not-exist.json"),
      ],
      { encoding: "utf8" },
    );
    assert.equal(rejectedOutput.status, 1);
    assert.match(rejectedOutput.stderr, /未知、重复或缺值参数/);
    assert.deepEqual(
      readdirSync(setup.dir).sort(),
      [
        "SKILL.snapshot.md",
        "attestation-request.json",
        "context.json",
        "input.json",
        "manifest-draft.json",
        "response.md",
        "rubric.md",
        "runtime-run.json",
        "signature.txt",
        "task.md",
      ].sort(),
    );
    const receiptContent = Buffer.from(
      finalization.serializedReceipt.data,
      "base64",
    );
    const receiptPath = join(setup.dir, "cli-runtime-receipt.json");
    writeFileSync(receiptPath, receiptContent, { flag: "wx", mode: 0o600 });
    const artifact = {
      path: "cli-runtime-receipt.json",
      sha256: finalization.serializedReceipt.sha256,
      bytes: finalization.serializedReceipt.bytes,
    };
    const finalManifestPath = join(setup.dir, "manifest-final.json");
    writeFileSync(
      finalManifestPath,
      JSON.stringify(
        {
          ...setup.manifest,
          runtime: { ...setup.manifest.runtime, receipt: artifact },
        },
        null,
        2,
      ) + "\n",
    );
    const checked = spawnSync(
      process.execPath,
      [
        "--import",
        "tsx",
        "src/cli.ts",
        "acceptance-check",
        "--manifest",
        finalManifestPath,
        "--trusted-runtime-key",
        publicKeyPath,
      ],
      { encoding: "utf8" },
    );
    assert.equal(checked.status, 0, checked.stderr);
    assert.equal(JSON.parse(checked.stdout).status, "verified");
    assert.equal(
      hash(readFileSync(receiptPath)),
      artifact.sha256,
    );
  } finally {
    rmSync(setup.dir, { recursive: true, force: true });
    rmSync(trustDir, { recursive: true, force: true });
  }
});
