import { test } from "node:test";
import assert from "node:assert/strict";
import { adjudicateBaziTimingBlindReview } from "../src/blind-review-adjudication.js";
import { InputError } from "../src/input.js";

const key = {
  schemaVersion: 1,
  packetId: "synthetic-blind-review-v1",
  caseSummary: { total: 5, target: 3, control: 2 },
  cases: [
    {
      caseId: "case-01",
      role: "control",
      referenceFocusSpanLiteral: "壬生戌下闕",
    },
    {
      caseId: "case-02",
      role: "target",
      referenceFocusSpanLiteral: "是年進而中。",
    },
    {
      caseId: "case-03",
      role: "target",
      referenceFocusSpanLiteral: "主譬如吾身",
    },
    {
      caseId: "case-04",
      role: "control",
      referenceFocusSpanLiteral: "喜水則不吉。",
    },
    {
      caseId: "case-05",
      role: "target",
      referenceFocusSpanLiteral: "大。則運自降。吉。",
    },
  ],
};

const defaultReadings: Record<string, string> = {
  "case-01": "壬生戌下闕",
  "case-02": "是年進而中。",
  "case-03": "主譬如吾身",
  "case-04": "喜水則不吉。",
  "case-05": "大。則運自降。吉。",
};

function response(
  reviewerId: string,
  overrides: Record<string, string> = {},
  options: {
    confidence?: "high" | "medium" | "low";
    punctuationConfidence?: "high" | "medium" | "low";
    sufficiency?: "yes" | "partial" | "no";
  } = {},
) {
  return {
    schemaVersion: 1,
    packetId: key.packetId,
    reviewerId,
    reviewedAt: "2026-09-26",
    independenceAttestation: {
      reviewedWithoutAnswerKey: true,
      reviewedWithoutOtherReviewerResponses: true,
      usedOcrOrExternalLookup: false,
      notes: "",
    },
    cases: key.cases.map(({ caseId }) => {
      const literal = overrides[caseId] ?? defaultReadings[caseId]!;
      return {
        caseId,
        imageSufficiency: options.sufficiency ?? "yes",
        focusColumnLiteral: `前文${literal}後文`,
        focusColumnNormalized: `前文${literal}後文`,
        focusSpanLiteral: literal,
        focusSpanNormalized: literal,
        focusSpanHasUncertainty: false,
        glyphConfidence: options.confidence ?? "high",
        punctuationConfidence: options.punctuationConfidence ?? "high",
        uncertainPositions: [],
        neighboringColumnNotes: "",
      };
    }),
  };
}

test("两位通过校准的审读者可接受一致汉字，同时把标点分开裁决", () => {
  const first = response("reviewer-a", {
    "case-02": "是年進而申。",
  });
  const second = response("reviewer-b", {
    "case-02": "是年進而申。",
    "case-05": "大、則運自降。吉。",
  });
  const result = adjudicateBaziTimingBlindReview(key, [first, second]);
  assert.equal(result.status, "accepted");
  assert.deepEqual(
    result.reviewers.map((item) => item.calibration),
    ["pass", "pass"],
  );
  const changed = result.targets.find((item) => item.caseId === "case-02")!;
  assert.equal(changed.decision, "accepted");
  assert.equal(changed.acceptedCharacterReading, "是年進而申");
  assert.equal(changed.differsFromReferenceCharacters, true);
  const punctuationSplit = result.targets.find(
    (item) => item.caseId === "case-05",
  )!;
  assert.equal(punctuationSplit.decision, "accepted");
  assert.equal(punctuationSplit.punctuationDecision, "unresolved");
});

test("两位高置信读法冲突时要求第三位，不按答案键或多数猜测", () => {
  const result = adjudicateBaziTimingBlindReview(key, [
    response("reviewer-a"),
    response("reviewer-b", { "case-03": "日主譬如吾身" }),
  ]);
  assert.equal(result.status, "needs-third-reviewer");
  assert.equal(result.summary.thirdReviewerRequired, true);
  const target = result.targets.find((item) => item.caseId === "case-03")!;
  assert.equal(target.decision, "unresolved");
  assert.ok(
    result.summary.followUpReasons.includes(
      "HIGH_CONFIDENCE_DISAGREEMENT:case-03",
    ),
  );
});

test("低置信标点不会随已接受的汉字读法一起升级", () => {
  const result = adjudicateBaziTimingBlindReview(key, [
    response("reviewer-a", {}, { punctuationConfidence: "low" }),
    response("reviewer-b", {}, { punctuationConfidence: "low" }),
  ]);
  assert.equal(result.status, "accepted");
  assert.equal(
    result.targets.every((item) => item.decision === "accepted"),
    true,
  );
  assert.equal(
    result.targets.every((item) => item.punctuationDecision === "unresolved"),
    true,
  );
});

test("目标一致但一位审读者两个校准点均失败时仍要求第三位", () => {
  const result = adjudicateBaziTimingBlindReview(key, [
    response("reviewer-a"),
    response("reviewer-b", {
      "case-01": "壬生戌下關",
      "case-04": "喜水則大吉。",
    }),
  ]);
  assert.equal(result.reviewers[1]!.calibration, "fail");
  assert.equal(result.targets.every((item) => item.decision === "accepted"), true);
  assert.equal(result.status, "needs-third-reviewer");
  assert.ok(
    result.summary.followUpReasons.includes(
      "CONTROL_CALIBRATION_FAIL:reviewer-b",
    ),
  );
});

test("第三位不能压过通过校准的高置信冲突，结果保持未决", () => {
  const result = adjudicateBaziTimingBlindReview(key, [
    response("reviewer-a"),
    response("reviewer-b", { "case-03": "日主譬如吾身" }),
    response("reviewer-c", {
      "case-01": "壬生戌下關",
      "case-03": "主譬如吾身",
      "case-04": "喜水則大吉。",
    }),
  ]);
  assert.equal(result.reviewers[2]!.calibration, "fail");
  assert.equal(result.status, "unresolved");
  assert.equal(result.summary.thirdReviewerRequired, false);
  assert.equal(result.summary.manualAdjudicationRequired, true);
  const target = result.targets.find((item) => item.caseId === "case-03")!;
  assert.equal(target.decision, "unresolved");
  assert.ok(
    target.reasons.includes("CONTROL_PASS_HIGH_CONFIDENCE_CONFLICT"),
  );
});

test("拒绝非独立答卷以及会改变汉字序列的所谓规范化", () => {
  const contaminated = response("reviewer-a");
  contaminated.independenceAttestation.usedOcrOrExternalLookup = true;
  assert.throws(
    () =>
      adjudicateBaziTimingBlindReview(key, [
        contaminated,
        response("reviewer-b"),
      ]),
    (error: unknown) =>
      error instanceof InputError && error.code === "INVALID_BLIND_REVIEW",
  );

  const rewritten = response("reviewer-a");
  rewritten.cases[0]!.focusSpanNormalized = "壬生戌下关";
  assert.throws(
    () =>
      adjudicateBaziTimingBlindReview(key, [
        rewritten,
        response("reviewer-b"),
      ]),
    (error: unknown) =>
      error instanceof InputError && error.code === "INVALID_BLIND_REVIEW",
  );
});
