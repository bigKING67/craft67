import { InputError, object } from "./input.js";

type Confidence = "high" | "medium" | "low";
type ImageSufficiency = "yes" | "partial" | "no";
type CaseRole = "target" | "control";
type Calibration = "pass" | "conditional" | "fail";

type KeyCase = {
  caseId: string;
  role: CaseRole;
  referenceFocusSpanLiteral: string;
};

type ReviewCase = {
  caseId: string;
  imageSufficiency: ImageSufficiency;
  focusColumnLiteral: string;
  focusColumnNormalized: string;
  focusSpanLiteral: string;
  focusSpanNormalized: string;
  focusSpanHasUncertainty: boolean;
  glyphConfidence: Confidence;
  punctuationConfidence: Confidence;
};

type Review = {
  reviewerId: string;
  reviewedAt: string;
  cases: Map<string, ReviewCase>;
};

export type BlindReviewInputBindings = {
  keySha256: string;
  responseSha256: string[];
};

const punctuation = /^\p{P}$/u;
const sha256 = /^[0-9a-f]{64}$/;

function invalid(message: string): never {
  throw new InputError("INVALID_BLIND_REVIEW", message);
}

function exactKeys(
  value: Record<string, unknown>,
  allowed: readonly string[],
  label: string,
) {
  for (const key of Object.keys(value))
    if (!allowed.includes(key)) invalid(`${label} 含未知字段 ${key}`);
}

function requiredString(
  value: Record<string, unknown>,
  key: string,
  label: string,
): string {
  const raw = value[key];
  if (typeof raw !== "string" || !raw.trim())
    invalid(`${label}.${key} 必须是非空文字`);
  return raw;
}

function choose<T extends string>(
  value: unknown,
  choices: readonly T[],
  label: string,
): T {
  if (!choices.includes(value as T))
    invalid(`${label} 必须为 ${choices.join(" / ")}`);
  return value as T;
}

function compactLiteral(value: string): string {
  return value.normalize("NFC").replace(/\s+/gu, "");
}

export function splitBlindReviewLiteral(value: string): {
  compact: string;
  characters: string;
  punctuationPattern: string;
} {
  const compact = compactLiteral(value);
  const glyphs = Array.from(compact);
  return {
    compact,
    characters: glyphs.filter((glyph) => !punctuation.test(glyph)).join(""),
    punctuationPattern: glyphs
      .map((glyph) => (punctuation.test(glyph) ? glyph : "_"))
      .join(""),
  };
}

function parseKey(raw: unknown): { packetId: string; cases: KeyCase[] } {
  const value = object(raw, "盲审答案键");
  if (value.schemaVersion !== 1)
    invalid("盲审答案键 schemaVersion 必须为 1");
  const packetId = requiredString(value, "packetId", "盲审答案键").trim();
  if (!Array.isArray(value.cases) || !value.cases.length)
    invalid("盲审答案键 cases 必须是非空数组");
  const seen = new Set<string>();
  const cases = value.cases.map((rawCase, index): KeyCase => {
    const item = object(rawCase, `盲审答案键.cases[${index}]`);
    const caseId = requiredString(item, "caseId", `答案键案例 ${index}`).trim();
    if (seen.has(caseId)) invalid(`答案键案例 ID 重复：${caseId}`);
    seen.add(caseId);
    return {
      caseId,
      role: choose(item.role, ["target", "control"], `${caseId}.role`),
      referenceFocusSpanLiteral: requiredString(
        item,
        "referenceFocusSpanLiteral",
        caseId,
      ),
    };
  });
  if (!cases.some((item) => item.role === "target"))
    invalid("答案键至少需要一个 target 案例");
  if (!cases.some((item) => item.role === "control"))
    invalid("答案键至少需要一个 control 案例");
  const summary = value.caseSummary;
  if (summary !== undefined) {
    const counts = object(summary, "caseSummary");
    const expected = {
      total: cases.length,
      target: cases.filter((item) => item.role === "target").length,
      control: cases.filter((item) => item.role === "control").length,
    };
    for (const [key, count] of Object.entries(expected))
      if (counts[key] !== count)
        invalid(`caseSummary.${key} 与答案键实际案例不一致`);
  }
  return { packetId, cases };
}

function parseUncertainPositions(value: unknown, label: string) {
  if (!Array.isArray(value)) invalid(`${label} 必须是数组`);
  value.forEach((raw, index) => {
    const item = object(raw, `${label}[${index}]`);
    exactKeys(
      item,
      [
        "sequenceIndex",
        "observedShape",
        "candidateReadings",
        "confidence",
        "reason",
      ],
      `${label}[${index}]`,
    );
    if (!Number.isInteger(item.sequenceIndex) || (item.sequenceIndex as number) < 1)
      invalid(`${label}[${index}].sequenceIndex 必须是从 1 开始的整数`);
    if (typeof item.observedShape !== "string")
      invalid(`${label}[${index}].observedShape 必须是文字`);
    if (
      !Array.isArray(item.candidateReadings) ||
      !item.candidateReadings.every((candidate) => typeof candidate === "string")
    )
      invalid(`${label}[${index}].candidateReadings 必须是文字数组`);
    choose(
      item.confidence,
      ["high", "medium", "low"],
      `${label}[${index}].confidence`,
    );
    if (typeof item.reason !== "string")
      invalid(`${label}[${index}].reason 必须是文字`);
  });
}

function parseReviewCase(raw: unknown, reviewerId: string, index: number): ReviewCase {
  const label = `${reviewerId}.cases[${index}]`;
  const value = object(raw, label);
  exactKeys(
    value,
    [
      "caseId",
      "imageSufficiency",
      "focusColumnLiteral",
      "focusColumnNormalized",
      "focusSpanLiteral",
      "focusSpanNormalized",
      "focusSpanHasUncertainty",
      "glyphConfidence",
      "punctuationConfidence",
      "uncertainPositions",
      "neighboringColumnNotes",
    ],
    label,
  );
  const caseId = requiredString(value, "caseId", label).trim();
  const focusColumnLiteral = requiredString(value, "focusColumnLiteral", label);
  const focusColumnNormalized = requiredString(
    value,
    "focusColumnNormalized",
    label,
  );
  const focusSpanLiteral = requiredString(value, "focusSpanLiteral", label);
  const focusSpanNormalized = requiredString(
    value,
    "focusSpanNormalized",
    label,
  );
  if (
    splitBlindReviewLiteral(focusColumnLiteral).characters !==
    splitBlindReviewLiteral(focusColumnNormalized).characters
  )
    invalid(`${label} 的整栏规范化改变了汉字序列`);
  if (
    splitBlindReviewLiteral(focusSpanLiteral).characters !==
    splitBlindReviewLiteral(focusSpanNormalized).characters
  )
    invalid(`${label} 的红框规范化改变了汉字序列`);
  if (typeof value.focusSpanHasUncertainty !== "boolean")
    invalid(`${label}.focusSpanHasUncertainty 必须是布尔值`);
  if (
    focusSpanLiteral.includes("□") &&
    value.focusSpanHasUncertainty === false
  )
    invalid(`${label} 含 □ 时必须标记 focusSpanHasUncertainty=true`);
  parseUncertainPositions(value.uncertainPositions, `${label}.uncertainPositions`);
  if (typeof value.neighboringColumnNotes !== "string")
    invalid(`${label}.neighboringColumnNotes 必须是文字`);
  return {
    caseId,
    imageSufficiency: choose(
      value.imageSufficiency,
      ["yes", "partial", "no"],
      `${label}.imageSufficiency`,
    ),
    focusColumnLiteral,
    focusColumnNormalized,
    focusSpanLiteral,
    focusSpanNormalized,
    focusSpanHasUncertainty: value.focusSpanHasUncertainty,
    glyphConfidence: choose(
      value.glyphConfidence,
      ["high", "medium", "low"],
      `${label}.glyphConfidence`,
    ),
    punctuationConfidence: choose(
      value.punctuationConfidence,
      ["high", "medium", "low"],
      `${label}.punctuationConfidence`,
    ),
  };
}

function parseReview(
  raw: unknown,
  packetId: string,
  keyCases: KeyCase[],
  index: number,
): Review {
  const label = `答卷[${index}]`;
  const value = object(raw, label);
  exactKeys(
    value,
    [
      "schemaVersion",
      "packetId",
      "reviewerId",
      "reviewedAt",
      "independenceAttestation",
      "cases",
      "uncertainPositionExample",
    ],
    label,
  );
  if (value.schemaVersion !== 1) invalid(`${label}.schemaVersion 必须为 1`);
  if (value.packetId !== packetId) invalid(`${label}.packetId 与答案键不一致`);
  const reviewerId = requiredString(value, "reviewerId", label).trim();
  const reviewedAt = requiredString(value, "reviewedAt", label).trim();
  if (Number.isNaN(Date.parse(reviewedAt)))
    invalid(`${reviewerId}.reviewedAt 不是可解析日期`);
  const attestation = object(
    value.independenceAttestation,
    `${reviewerId}.independenceAttestation`,
  );
  exactKeys(
    attestation,
    [
      "reviewedWithoutAnswerKey",
      "reviewedWithoutOtherReviewerResponses",
      "usedOcrOrExternalLookup",
      "notes",
    ],
    `${reviewerId}.independenceAttestation`,
  );
  if (attestation.reviewedWithoutAnswerKey !== true)
    invalid(`${reviewerId} 未声明避开答案键`);
  if (attestation.reviewedWithoutOtherReviewerResponses !== true)
    invalid(`${reviewerId} 未声明独立于其他答卷`);
  if (attestation.usedOcrOrExternalLookup !== false)
    invalid(`${reviewerId} 使用了 OCR 或外部检索，不能进入盲审裁决`);
  if (typeof attestation.notes !== "string")
    invalid(`${reviewerId}.independenceAttestation.notes 必须是文字`);
  if (!Array.isArray(value.cases)) invalid(`${reviewerId}.cases 必须是数组`);
  const cases = new Map<string, ReviewCase>();
  value.cases.forEach((rawCase, caseIndex) => {
    const parsed = parseReviewCase(rawCase, reviewerId, caseIndex);
    if (cases.has(parsed.caseId))
      invalid(`${reviewerId} 重复回答案例 ${parsed.caseId}`);
    cases.set(parsed.caseId, parsed);
  });
  const expected = new Set(keyCases.map((item) => item.caseId));
  for (const caseId of cases.keys())
    if (!expected.has(caseId)) invalid(`${reviewerId} 含未知案例 ${caseId}`);
  for (const caseId of expected)
    if (!cases.has(caseId)) invalid(`${reviewerId} 缺少案例 ${caseId}`);
  return { reviewerId, reviewedAt, cases };
}

function usable(item: ReviewCase): boolean {
  return (
    item.imageSufficiency === "yes" &&
    item.glyphConfidence !== "low" &&
    !item.focusSpanHasUncertainty &&
    !item.focusSpanLiteral.includes("□") &&
    splitBlindReviewLiteral(item.focusSpanLiteral).characters.length > 0
  );
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

export function adjudicateBaziTimingBlindReview(
  rawKey: unknown,
  rawResponses: unknown[],
  bindings?: BlindReviewInputBindings,
) {
  const key = parseKey(rawKey);
  if (rawResponses.length < 2 || rawResponses.length > 3)
    invalid("盲审裁决只接受 2 或 3 份独立答卷");
  const reviews = rawResponses.map((response, index) =>
    parseReview(response, key.packetId, key.cases, index),
  );
  if (new Set(reviews.map((review) => review.reviewerId)).size !== reviews.length)
    invalid("reviewerId 必须互不相同");
  if (bindings) {
    if (!sha256.test(bindings.keySha256))
      invalid("keySha256 必须是小写 SHA-256");
    if (
      bindings.responseSha256.length !== reviews.length ||
      !bindings.responseSha256.every((digest) => sha256.test(digest))
    )
      invalid("responseSha256 必须与答卷一一对应");
  }

  const controls = key.cases.filter((item) => item.role === "control");
  const targets = key.cases.filter((item) => item.role === "target");
  const reviewerResults = reviews.map((review) => {
    const controlResults = controls.map((control) => {
      const response = review.cases.get(control.caseId)!;
      const observed = splitBlindReviewLiteral(response.focusSpanLiteral);
      const expected = splitBlindReviewLiteral(
        control.referenceFocusSpanLiteral,
      );
      const isUsable = usable(response);
      return {
        caseId: control.caseId,
        observedCharacters: observed.characters,
        expectedCharacters: expected.characters,
        usable: isUsable,
        matches: isUsable && observed.characters === expected.characters,
        observedPunctuationPattern: observed.punctuationPattern,
        expectedPunctuationPattern: expected.punctuationPattern,
      };
    });
    const matches = controlResults.filter((item) => item.matches).length;
    const calibration: Calibration =
      matches === controls.length
        ? "pass"
        : matches === 0
          ? "fail"
          : "conditional";
    return {
      reviewerId: review.reviewerId,
      reviewedAt: review.reviewedAt,
      calibration,
      controlMatches: matches,
      controlTotal: controls.length,
      controlResults,
    };
  });
  const calibration = new Map(
    reviewerResults.map((reviewer) => [
      reviewer.reviewerId,
      reviewer.calibration,
    ]),
  );

  const targetResults = targets.map((target) => {
    const reference = splitBlindReviewLiteral(target.referenceFocusSpanLiteral);
    const observations = reviews.map((review) => {
      const response = review.cases.get(target.caseId)!;
      const reading = splitBlindReviewLiteral(response.focusSpanLiteral);
      const isUsable = usable(response);
      return {
        reviewerId: review.reviewerId,
        calibration: calibration.get(review.reviewerId)!,
        focusSpanLiteral: reading.compact,
        characterReading: reading.characters,
        punctuationPattern: reading.punctuationPattern,
        imageSufficiency: response.imageSufficiency,
        glyphConfidence: response.glyphConfidence,
        punctuationConfidence: response.punctuationConfidence,
        focusSpanHasUncertainty: response.focusSpanHasUncertainty,
        usable: isUsable,
        highConfidence:
          isUsable && response.glyphConfidence === "high",
      };
    });
    const groups = new Map<string, typeof observations>();
    for (const observation of observations) {
      if (!observation.usable) continue;
      const group = groups.get(observation.characterReading) ?? [];
      group.push(observation);
      groups.set(observation.characterReading, group);
    }
    const candidate = [...groups.entries()]
      .filter(([, group]) => group.length >= 2)
      .map(([reading, group]) => {
        const hasPassingSupport = group.some(
          (item) => item.calibration === "pass",
        );
        const passingConflict = observations.some(
          (item) =>
            !group.includes(item) &&
            item.calibration === "pass" &&
            item.highConfidence &&
            item.characterReading !== reading,
        );
        return { reading, group, hasPassingSupport, passingConflict };
      })
      .find((item) => item.hasPassingSupport && !item.passingConflict);

    if (!candidate) {
      const reasons: string[] = [];
      if (![...groups.values()].some((group) => group.length >= 2))
        reasons.push("INSUFFICIENT_USABLE_AGREEMENT");
      if (
        [...groups.values()].some((group) => group.length >= 2) &&
        ![...groups.values()].some((group) =>
          group.some((item) => item.calibration === "pass"),
        )
      )
        reasons.push("NO_CONTROL_PASS_SUPPORT");
      if (
        observations.some(
          (left, index) =>
            left.calibration === "pass" &&
            left.highConfidence &&
            observations.some(
              (right, rightIndex) =>
                rightIndex > index &&
                right.calibration === "pass" &&
                right.highConfidence &&
                right.characterReading !== left.characterReading,
            ),
        )
      )
        reasons.push("CONTROL_PASS_HIGH_CONFIDENCE_CONFLICT");
      return {
        caseId: target.caseId,
        decision: "unresolved" as const,
        referenceCharacters: reference.characters,
        referencePunctuationPattern: reference.punctuationPattern,
        acceptedCharacterReading: null,
        differsFromReferenceCharacters: null,
        punctuationDecision: "unresolved" as const,
        acceptedPunctuationPattern: null,
        reasons: reasons.length ? reasons : ["NO_QUALIFYING_READING"],
        observations,
      };
    }

    const punctuationGroups = new Map<string, number>();
    for (const observation of candidate.group) {
      if (observation.punctuationConfidence === "low") continue;
      punctuationGroups.set(
        observation.punctuationPattern,
        (punctuationGroups.get(observation.punctuationPattern) ?? 0) + 1,
      );
    }
    const punctuationConsensus = [...punctuationGroups.entries()].find(
      ([, count]) => count >= 2,
    )?.[0];
    return {
      caseId: target.caseId,
      decision: "accepted" as const,
      referenceCharacters: reference.characters,
      referencePunctuationPattern: reference.punctuationPattern,
      acceptedCharacterReading: candidate.reading,
      differsFromReferenceCharacters: candidate.reading !== reference.characters,
      punctuationDecision: punctuationConsensus
        ? ("accepted" as const)
        : ("unresolved" as const),
      acceptedPunctuationPattern: punctuationConsensus ?? null,
      reasons: ["CHARACTER_READING_ACCEPTED"],
      observations,
    };
  });

  const triggerReasons: string[] = [];
  for (const reviewer of reviewerResults)
    if (reviewer.calibration === "fail")
      triggerReasons.push(`CONTROL_CALIBRATION_FAIL:${reviewer.reviewerId}`);
  for (const target of targetResults) {
    if (target.decision === "unresolved")
      triggerReasons.push(`TARGET_UNRESOLVED:${target.caseId}`);
    if (
      target.observations.some(
        (item) => item.imageSufficiency === "partial" || item.imageSufficiency === "no",
      )
    )
      triggerReasons.push(`IMAGE_INSUFFICIENT:${target.caseId}`);
    const highReadings = unique(
      target.observations
        .filter((item) => item.highConfidence)
        .map((item) => item.characterReading),
    );
    if (highReadings.length > 1)
      triggerReasons.push(`HIGH_CONFIDENCE_DISAGREEMENT:${target.caseId}`);
    if (
      reviews.length === 2 &&
      target.observations[0]!.characterReading !==
        target.observations[1]!.characterReading
    )
      triggerReasons.push(`FIRST_TWO_DISAGREE:${target.caseId}`);
  }
  const followUpReasons = unique(triggerReasons);
  const thirdReviewerRequired = reviews.length === 2 && followUpReasons.length > 0;
  const unresolvedTargets = targetResults.filter(
    (item) => item.decision === "unresolved",
  ).length;
  const manualAdjudicationRequired = reviews.length === 3 && unresolvedTargets > 0;
  const status = thirdReviewerRequired
    ? "needs-third-reviewer"
    : unresolvedTargets > 0
      ? "unresolved"
      : "accepted";

  return {
    schema: "whoami.bazi-timing-blind-review-adjudication.v1",
    packetId: key.packetId,
    status,
    reviewerCount: reviews.length,
    ...(bindings
      ? {
          inputBindings: {
            keySha256: bindings.keySha256,
            responses: reviews.map((review, index) => ({
              reviewerId: review.reviewerId,
              sha256: bindings.responseSha256[index]!,
            })),
          },
        }
      : {}),
    reviewers: reviewerResults,
    targets: targetResults,
    summary: {
      targetTotal: targets.length,
      acceptedTargets: targets.length - unresolvedTargets,
      unresolvedTargets,
      thirdReviewerRequired,
      manualAdjudicationRequired,
      followUpReasons,
    },
    notClaimed: [
      "external expertise beyond the submitted reviewer attestations",
      "validity of traditional theory or real-world prediction",
      "a unique canonical text beyond these local scan loci",
    ],
  };
}
