import { test } from "node:test";
import assert from "node:assert/strict";
import {
  createHash,
  generateKeyPairSync,
  sign,
} from "node:crypto";
import { mkdtempSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";
import { Temporal } from "@js-temporal/polyfill";
import { checkAcceptanceManifest } from "../src/acceptance.js";
import { contextFor } from "../src/evidence.js";
import { buildChart } from "../src/chart.js";
import { InputError } from "../src/input.js";
import { contextErrorOutcome } from "../src/outcome.js";
import { reportTemplate, SECTION_IDS } from "../src/report.js";
import {
  ed25519PublicKeyId,
  runtimeAttestationPayload,
  type AttestedReview,
  type RuntimeBindings,
  type RuntimeIdentity,
} from "../src/attestation.js";

const hash = (value: string | Buffer) =>
  createHash("sha256").update(value).digest("hex");
const birthInput = {
  calendar: "solar",
  date: "2000-08-16",
  time: "04:00",
  place: "合成",
  longitude: 120,
  timeZone: "Asia/Shanghai",
  gender: "female",
};

test("固定的 v5 紫微前向样例保持报告、答复与逐段绑定一致", () => {
  const manifestPath = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-007/manifest.json",
  );
  const result = checkAcceptanceManifest(
    JSON.parse(readFileSync(manifestPath, "utf8")),
    manifestPath,
  );
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "ziwei-transform-list-must-not-become-event-schedule",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  const response = readFileSync(
    join(
      process.cwd(),
      "examples/acceptance/semantic-forward-007/response.md",
    ),
    "utf8",
  );
  const nonWhitespaceLength = [...response].filter(
    (character) => !/\s/u.test(character),
  ).length;
  assert.equal(nonWhitespaceLength, 358);
});
test("固定的 v6 相对年份样例解析年份、改写模糊大限并保留未决前提", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-008",
  );
  const manifestPath = join(base, "manifest.json");
  const result = checkAcceptanceManifest(
    JSON.parse(readFileSync(manifestPath, "utf8")),
    manifestPath,
  );
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "relative-years-and-decadal-range-must-not-become-events",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.equal(report.schema, "whoami.report.v6");
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  const reportText = JSON.stringify(report.sections);
  assert.match(reportText, /明年.*2027/u);
  assert.match(reportText, /后年.*2028/u);
  assert.doesNotMatch(reportText, /下个大限|下一大限|下一个大限/u);
  const response = readFileSync(join(base, "response.md"), "utf8");
  const nonWhitespaceLength = [...response].filter(
    (character) => !/\s/u.test(character),
  ).length;
  assert.equal(nonWhitespaceLength, 405);
});
test("固定的 v6 缺年样例先停下，补算后仍不把明年写成升职结论", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-009",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "missing-2027-evidence-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "expanded-2027-evidence-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);
  const baseline = JSON.parse(
    readFileSync(join(base, "context-2026.json"), "utf8"),
  );
  const expanded = JSON.parse(
    readFileSync(join(base, "context-2026-2027.json"), "utf8"),
  );
  assert.deepEqual(baseline.years, [2026]);
  assert.deepEqual(expanded.years, [2026, 2027]);
  assert.equal(baseline.chartId, expanded.chartId);
  assert.notEqual(baseline.evidenceId, expanded.evidenceId);
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.equal(report.evidenceId, expanded.evidenceId);
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  assert.match(JSON.stringify(report.sections), /明年.*2027/u);
  for (const [name, length] of [
    ["response-stop.md", 178],
    ["response-expanded.md", 434],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 跨年时区样例先换算本地日期，再分别解析明年", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-010",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(
    result.caseChecks,
    ["asia-shanghai-next-year-2028", "america-los-angeles-next-year-2027"].map(
      (id) => ({
        id,
        responseSafety: "pass",
        reportValidation: "pass",
        responseReportPremise: "pass",
        responseClaimsValidation: "pass",
      }),
    ),
  );

  const instant = Temporal.Instant.from("2026-12-31T16:30:00Z");
  assert.equal(
    instant.toZonedDateTimeISO("Asia/Shanghai").toString(),
    "2027-01-01T00:30:00+08:00[Asia/Shanghai]",
  );
  assert.equal(
    instant.toZonedDateTimeISO("America/Los_Angeles").toString(),
    "2026-12-31T08:30:00-08:00[America/Los_Angeles]",
  );

  const input = JSON.parse(readFileSync(join(base, "input.json"), "utf8"));
  const shanghaiContext = JSON.parse(
    readFileSync(join(base, "context-shanghai-2027-2028.json"), "utf8"),
  );
  const losAngelesContext = JSON.parse(
    readFileSync(join(base, "context-los-angeles-2026-2027.json"), "utf8"),
  );
  assert.equal(input.timeZone, "Asia/Shanghai");
  assert.deepEqual(shanghaiContext.years, [2027, 2028]);
  assert.deepEqual(losAngelesContext.years, [2026, 2027]);
  assert.equal(shanghaiContext.chartId, losAngelesContext.chartId);
  assert.notEqual(shanghaiContext.evidenceId, losAngelesContext.evidenceId);

  for (const expected of [
    {
      name: "shanghai",
      report: "report-shanghai.json",
      response: "response-shanghai.md",
      context: shanghaiContext,
      timeReference: {
        asOfDate: "2027-01-01",
        timeZone: "Asia/Shanghai",
      },
      years: [2027, 2028],
      relativeYear: 2028,
      responseLength: 452,
    },
    {
      name: "los-angeles",
      report: "report-los-angeles.json",
      response: "response-los-angeles.md",
      context: losAngelesContext,
      timeReference: {
        asOfDate: "2026-12-31",
        timeZone: "America/Los_Angeles",
      },
      years: [2026, 2027],
      relativeYear: 2027,
      responseLength: 450,
    },
  ] as const) {
    const report = JSON.parse(
      readFileSync(join(base, expected.report), "utf8"),
    );
    assert.equal(report.schema, "whoami.report.v6");
    assert.equal(report.evidenceId, expected.context.evidenceId);
    assert.deepEqual(report.timeReference, expected.timeReference);
    assert.deepEqual(
      report.ziweiReasoning.find(
        (item: { topic: string }) => item.topic === "ziwei-timing",
      ).timingChain.years,
      expected.years,
    );
    assert.match(
      JSON.stringify(report.sections),
      new RegExp(`明年.*${expected.relativeYear}`, "u"),
      expected.name,
    );
    const response = readFileSync(join(base, expected.response), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      expected.responseLength,
    );
  }
});
test("固定的 v6 历法限定样例先停下，明确紫微年界后仍保留未决前提", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-011",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "calendar-qualified-time-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-ziwei-2027-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027.*紫微.*农历年标签/u);
  assert.doesNotMatch(
    reportText,
    /农历明年|明年按农历|过完春节|过了春节|春节后|立春后/u,
  );
  const stop = readFileSync(join(base, "response-stop.md"), "utf8");
  assert.match(stop, /农历明年.*过完春节.*立春后/us);
  for (const [name, length] of [
    ["response-stop.md", 245],
    ["response-explicit.md", 411],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 细分时间样例先停下，退回年度层后仍保留未决前提", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-012",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "subannual-time-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.doesNotMatch(
    reportText,
    /上半年|下半年|年初|年中|年底|年末|这个月|下个月|下周|第[一二三四]季度|三个月内/u,
  );
  const stop = readFileSync(join(base, "response-stop.md"), "utf8");
  assert.match(stop, /明年上半年.*三个月内.*年底前.*春节前几天/us);
  for (const [name, length] of [
    ["response-stop.md", 265],
    ["response-annual.md", 395],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 模糊时间样例先要求明确范围，再保留年度未决前提", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-013",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "vague-time-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.doesNotMatch(
    reportText,
    /近期|不久|很快|过阵子|过一段时间|什么时候|何时|几时|短期内|未来一段时间/u,
  );
  const stop = readFileSync(join(base, "response-stop.md"), "utf8");
  assert.match(stop, /近期.*不久.*很快.*过阵子.*什么时候/us);
  for (const [name, length] of [
    ["response-stop.md", 230],
    ["response-annual.md", 365],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 多年范围样例先明确闭区间，缺年补算后仍保持未决", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-014",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "relative-multiyear-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-range-missing-years-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "expanded-range-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);
  assert.equal(manifest.cases[1].report, undefined);

  const baseline = JSON.parse(
    readFileSync(join(base, "context-2026-2027.json"), "utf8"),
  );
  const expanded = JSON.parse(
    readFileSync(join(base, "context-2026-2029.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(baseline.years, [2026, 2027]);
  assert.deepEqual(expanded.years, [2026, 2027, 2028, 2029]);
  assert.equal(expanded.chartId, baseline.chartId);
  assert.notEqual(expanded.evidenceId, baseline.evidenceId);
  assert.equal(report.evidenceId, expanded.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027, 2028, 2029],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027—2029年度/u);
  assert.doesNotMatch(
    reportText,
    /未来三年|三年内|接下来五年|这几年|近几年|长期会|中长期|长远来看/u,
  );
  const rangeStop = readFileSync(
    join(base, "response-range-stop.md"),
    "utf8",
  );
  assert.match(
    rangeStop,
    /未来三年.*三年内.*接下来五年.*这几年.*长期会怎样/us,
  );
  const missingYears = readFileSync(
    join(base, "response-missing-years.md"),
    "utf8",
  );
  assert.match(missingYears, /2027—2029.*缺少 2028 与 2029.*继续停下/us);
  for (const [name, length] of [
    ["response-range-stop.md", 244],
    ["response-missing-years.md", 254],
    ["response-expanded.md", 387],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 绝对时点样例先区分类别，再退回年度主题", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-015",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 11);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "absolute-subannual-time-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.doesNotMatch(
    reportText,
    /2027\s*年\s*3\s*月|3\s*月\s*15\s*日|周一|星期五|明年春节|2027\s*年\s*立春|立春当天|清明那天/u,
  );
  const stop = readFileSync(join(base, "response-stop.md"), "utf8");
  assert.match(
    stop,
    /2027\s*年\s*3\s*月.*3\s*月\s*15\s*日.*周一.*明年春节.*立春当天/us,
  );
  for (const [name, length] of [
    ["response-stop.md", 244],
    ["response-annual.md", 370],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 数字日期与日内时点样例先停下，再退回年度主题", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-016",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 11);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "numeric-date-and-time-of-day-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.match(reportText, /2026-09-25/u);
  assert.doesNotMatch(
    reportText,
    /2027[-/.]0?3[-/.]15|3\.15|今晚|明早|上午九点|09:30/u,
  );
  const stop = readFileSync(join(base, "response-stop.md"), "utf8");
  assert.match(
    stop,
    /2027-03-15.*3\.15.*今晚.*明早.*上午九点/us,
  );
  for (const [name, length] of [
    ["response-stop.md", 258],
    ["response-annual.md", 376],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 歧义或非法日期时刻样例先拒绝，再退回年度主题", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-017",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 11);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "ambiguous-or-invalid-local-time-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.match(reportText, /2026-09-25/u);
  assert.doesNotMatch(reportText, /03\/04|2027-02-29|24:30|CST/u);
  const stop = readFileSync(join(base, "response-stop.md"), "utf8");
  assert.match(stop, /03\/04.*2027-02-29.*24:30.*CST/us);
  for (const [name, length] of [
    ["response-stop.md", 288],
    ["response-annual.md", 381],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 DST 当地时刻样例先分类缺失与重复，再退回年度主题", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-018",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 14);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "nonexistent-dst-local-time-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "ambiguous-dst-local-time-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);
  assert.equal(manifest.cases[1].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.match(reportText, /2026-09-25/u);
  assert.doesNotMatch(
    reportText,
    /2027-03-14|2026-11-01|02:30|01:30|America\/New_York/u,
  );
  const gap = readFileSync(join(base, "response-gap.md"), "utf8");
  assert.match(
    gap,
    /America\/New_York.*2027\s*年\s*3\s*月\s*14\s*日.*02:30.*不存在.*earlier.*later.*03:30/us,
  );
  const fold = readFileSync(join(base, "response-fold.md"), "utf8");
  assert.match(
    fold,
    /America\/New_York.*2026\s*年\s*11\s*月\s*1\s*日.*01:30.*earlier.*UTC−04:00.*later.*UTC−05:00/us,
  );
  for (const [name, length] of [
    ["response-gap.md", 358],
    ["response-fold.md", 336],
    ["response-annual.md", 390],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 offset 与 IANA 时区样例先核对一致性，再退回年度主题", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-019",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 17);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "valid-fold-offsets-still-need-granular-evidence",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "offset-zone-mismatch-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "offset-cannot-repair-dst-gap",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  for (const index of [0, 1, 2])
    assert.equal(manifest.cases[index].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.match(reportText, /2026-09-25/u);
  assert.doesNotMatch(
    reportText,
    /2026-11-01T01:30|2027-03-14T02:30|-04:00\[America\/New_York\]|-05:00\[America\/New_York\]|-06:00\[America\/New_York\]/u,
  );
  const validOffsets = readFileSync(
    join(base, "response-valid-offsets.md"),
    "utf8",
  );
  assert.match(
    validOffsets,
    /-04:00\[America\/New_York\].*earlier.*05:30Z.*-05:00\[America\/New_York\].*later.*06:30Z.*相隔一小时/us,
  );
  const mismatch = readFileSync(join(base, "response-mismatch.md"), "utf8");
  assert.match(
    mismatch,
    /2026-11-01\s*01:30.*America\/New_York.*UTC−04:00.*earlier.*UTC−05:00.*later.*-06:00.*矛盾/us,
  );
  const gap = readFileSync(join(base, "response-gap.md"), "utf8");
  assert.match(
    gap,
    /America\/New_York.*2027\s*年\s*3\s*月\s*14\s*日.*02:30.*不存在.*-05:00.*不能.*03:30/us,
  );
  for (const [name, length] of [
    ["response-valid-offsets.md", 425],
    ["response-mismatch.md", 383],
    ["response-gap.md", 341],
    ["response-annual.md", 423],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 绝对时刻等价样例先归并候选，再退回年度主题", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-020",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 14);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "equivalent-instant-options-must-merge",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "distinct-instants-still-need-granular-evidence",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  assert.equal(manifest.cases[0].report, undefined);
  assert.equal(manifest.cases[1].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.match(reportText, /2026-09-25/u);
  assert.doesNotMatch(
    reportText,
    /2026-11-01T01:30|2026-11-01T05:30|2026-11-01T06:30|2026-11-01T13:30|America\/New_York/u,
  );
  const equivalent = readFileSync(
    join(base, "response-equivalent.md"),
    "utf8",
  );
  assert.match(
    equivalent,
    /01:30-04:00\[America\/New_York\].*05:30Z.*13:30\+08:00\[Asia\/Shanghai\].*05:30Z.*一个候选/us,
  );
  const distinct = readFileSync(join(base, "response-distinct.md"), "utf8");
  assert.match(
    distinct,
    /-04:00\[America\/New_York\].*earlier.*05:30Z.*-05:00\[America\/New_York\].*later.*06:30Z.*相隔一小时.*两个候选/us,
  );
  for (const [name, length] of [
    ["response-equivalent.md", 420],
    ["response-distinct.md", 423],
    ["response-annual.md", 394],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 绝对时间区间样例先核对顺序与交集，再退回年度主题", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-021",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 17);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "invalid-interval-ordering-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "equivalent-overlapping-intervals-not-independent",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "disjoint-intervals-still-need-granular-evidence",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  for (const index of [0, 1, 2])
    assert.equal(manifest.cases[index].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.match(reportText, /2026-09-25/u);
  assert.doesNotMatch(
    reportText,
    /2026-11-01T01:30|2026-11-01T05:30|2026-11-01T06:00|2026-11-01T06:30|2026-11-01T07:00|2026-11-01T08:00|America\/New_York/u,
  );
  const invalid = readFileSync(join(base, "response-invalid.md"), "utf8");
  assert.match(
    invalid,
    /起点和终点.*05:30Z.*时长为零.*06:30Z.*05:30Z.*起点晚于终点.*不静默交换/us,
  );
  const overlap = readFileSync(join(base, "response-overlap.md"), "utf8");
  assert.match(
    overlap,
    /A.*05:30Z—06:30Z.*B.*05:30Z—06:30Z.*同一区间.*C.*06:00Z—07:00Z.*06:00Z—06:30Z.*正时长交集/us,
  );
  const disjoint = readFileSync(join(base, "response-disjoint.md"), "utf8");
  assert.match(
    disjoint,
    /05:30Z.*06:30Z.*07:00Z.*08:00Z.*相隔半小时.*没有正时长交集.*年度 evidence/us,
  );
  for (const [name, length] of [
    ["response-invalid.md", 335],
    ["response-overlap.md", 383],
    ["response-disjoint.md", 378],
    ["response-annual.md", 393],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 开放区间与时长样例先核对 elapsed time，再退回年度主题", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-022",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 17);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "open-ended-intervals-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "declared-duration-mismatch-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "consistent-elapsed-durations-still-need-evidence",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  for (const index of [0, 1, 2])
    assert.equal(manifest.cases[index].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.match(reportText, /2026-09-25/u);
  assert.doesNotMatch(
    reportText,
    /2026-11-01T05:30|2026-11-01T06:30|2027-03-14T01:30|2027-03-14T03:30|America\/New_York/u,
  );
  const openEnded = readFileSync(
    join(base, "response-open-ended.md"),
    "utf8",
  );
  assert.match(
    openEnded,
    /05:30Z.*下界.*没有结束时刻.*截至.*06:30Z.*上界.*没有开始时刻.*不自行补上另一端/us,
  );
  const mismatch = readFileSync(
    join(base, "response-duration-mismatch.md"),
    "utf8",
  );
  assert.match(
    mismatch,
    /05:30Z.*06:30Z.*60 分钟.*不是 90 分钟.*-05:00.*06:30Z.*-04:00.*07:30Z.*60 分钟.*两小时.*不存在.*elapsed time/us,
  );
  const valid = readFileSync(
    join(base, "response-duration-valid.md"),
    "utf8",
  );
  assert.match(
    valid,
    /05:30Z.*06:30Z.*60 分钟.*06:30Z.*07:30Z.*60 分钟.*墙上时间跨度.*elapsed time.*年度 evidence/us,
  );
  for (const [name, length] of [
    ["response-open-ended.md", 328],
    ["response-duration-mismatch.md", 402],
    ["response-duration-valid.md", 355],
    ["response-annual.md", 408],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 重复日程样例先补范围与 IANA 时区，再退回年度主题", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-023",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 17);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "unbounded-recurrence-must-stop",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "bounded-offset-recurrence-needs-iana",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "bounded-iana-recurrence-still-needs-occurrence-evidence",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
    {
      id: "explicit-2027-year-keeps-career-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);
  for (const index of [0, 1, 2])
    assert.equal(manifest.cases[index].report, undefined);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const report = JSON.parse(readFileSync(join(base, "report.json"), "utf8"));
  assert.deepEqual(context.years, [2026, 2027]);
  assert.equal(report.evidenceId, context.evidenceId);
  assert.deepEqual(report.timeReference, {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  });
  assert.deepEqual(
    report.ziweiReasoning.find(
      (item: { topic: string }) => item.topic === "ziwei-timing",
    ).timingChain.years,
    [2026, 2027],
  );
  const reportText = JSON.stringify(report);
  assert.match(reportText, /2027年度/u);
  assert.match(reportText, /2026-09-25/u);
  assert.doesNotMatch(
    reportText,
    /2026-11-01T00:00|2026-11-08T00:00|America\/New_York|每天 09:00|每周一 09:00/u,
  );
  const unbounded = readFileSync(
    join(base, "response-unbounded.md"),
    "utf8",
  );
  assert.match(
    unbounded,
    /每天 09:00.*每周一 09:00.*双侧绝对起止范围.*occurrence.*不生成命理报告.*不会自行假定/us,
  );
  const offset = readFileSync(
    join(base, "response-offset.md"),
    "utf8",
  );
  assert.match(
    offset,
    /00:00Z.*00:00Z.*双侧有界.*每天 09:00.*固定 offset.*IANA 地区时区.*出生资料中的时区.*不会生成报告/us,
  );
  const iana = readFileSync(join(base, "response-iana.md"), "utf8");
  assert.match(
    iana,
    /America\/New_York.*秋季 DST 回拨.*-04:00.*-05:00.*逐日展开 occurrence.*年度 evidence.*不生成报告.*日级、小时级/us,
  );
  for (const [name, length] of [
    ["response-unbounded.md", 265],
    ["response-offset.md", 304],
    ["response-iana.md", 391],
    ["response-annual.md", 407],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
test("固定的 v6 八字运年样例拒绝升职排名与事后回填", () => {
  const base = join(
    process.cwd(),
    "examples/acceptance/semantic-forward-024",
  );
  const manifestPath = join(base, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const result = checkAcceptanceManifest(manifest, manifestPath);
  assert.equal(result.status, "partial");
  assert.equal(result.reviewStatus, "PASS");
  assert.equal(result.artifactCount, 13);
  assert.deepEqual(result.counts, {
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  });
  assert.deepEqual(result.caseChecks, [
    {
      id: "career-ranking-without-reality-must-remain-unresolved",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
    {
      id: "reported-2026-promotion-must-not-retrofit-or-rank-future",
      responseSafety: "pass",
      reportValidation: "pass",
      responseReportPremise: "pass",
      responseClaimsValidation: "pass",
    },
  ]);

  const context = JSON.parse(
    readFileSync(join(base, "context.json"), "utf8"),
  );
  const baseline = JSON.parse(
    readFileSync(join(base, "report-baseline.json"), "utf8"),
  );
  const reality = JSON.parse(
    readFileSync(join(base, "report-reality.json"), "utf8"),
  );
  assert.deepEqual(context.years, [2026, 2027, 2028]);
  for (const report of [baseline, reality]) {
    assert.equal(report.schema, "whoami.report.v6");
    assert.equal(report.mode, "bazi");
    assert.equal(report.evidenceId, context.evidenceId);
    assert.deepEqual(report.timeReference, {
      asOfDate: "2026-09-25",
      timeZone: "Asia/Shanghai",
    });
    const timing = report.baziReasoning.find(
      (item: { topic: string }) => item.topic === "bazi-timing",
    );
    assert.equal(timing.status, "unresolved");
    assert.deepEqual(timing.years, [2026, 2027, 2028]);
    assert.equal(timing.timingChain.target, "career");
    assert.deepEqual(
      timing.timingChain.annualReviews.map(
        (item: { year: number; pillar: string; boundary: string }) => [
          item.year,
          item.pillar,
          item.boundary,
        ],
      ),
      [
        [2026, "丙午", "lichun"],
        [2027, "丁未", "lichun"],
        [2028, "戊申", "lichun"],
      ],
    );
    assert.ok(timing.timingChain.missingLinks.length >= 3);
  }
  const baselineReality = baseline.baziReasoning.find(
    (item: { topic: string }) => item.topic === "bazi-timing",
  ).timingChain.realityBasis;
  assert.deepEqual(baselineReality, {
    status: "not-provided",
    summary: "用户尚未提供可核验的岗位、考核、权限、组织机会、竞争条件或升职结果资料。",
    source: null,
  });
  const providedReality = reality.baziReasoning.find(
    (item: { topic: string }) => item.topic === "bazi-timing",
  ).timingChain.realityBasis;
  assert.equal(providedReality.status, "provided");
  assert.match(providedReality.source, /用户本轮.*2026 年升职.*未经独立核验/u);

  const baselineResponse = readFileSync(
    join(base, "response-baseline.md"),
    "utf8",
  );
  assert.match(
    baselineResponse,
    /不能.*排成升职第一、第二、第三.*丙午.*丁未.*戊申.*辛丑大运.*同支、同干.*不自动等于.*岗位空缺.*考核.*权限.*组织机会.*竞争条件/us,
  );
  const realityResponse = readFileSync(
    join(base, "response-reality.md"),
    "utf8",
  );
  assert.match(
    realityResponse,
    /2026 年确实升职.*事后复盘.*不能据此认定.*算准.*独立核验.*不能反向改写成事前命中.*2027.*2028.*不给排名/us,
  );
  for (const [name, length] of [
    ["response-baseline.md", 408],
    ["response-reality.md", 414],
  ] as const) {
    const response = readFileSync(join(base, name), "utf8");
    assert.equal(
      [...response].filter((character) => !/\s/u.test(character)).length,
      length,
    );
  }
});
const json = (value: unknown) => JSON.stringify(value) + "\n";

function validAcceptanceReport(evidence: ReturnType<typeof contextFor>) {
  const report = reportTemplate(evidence) as any;
  report.timeReference = {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  };
  const baziFact = evidence.facts.find((fact) => fact.system === "bazi")!;
  const ziweiFact = evidence.facts.find((fact) => fact.system === "ziwei")!;
  const rule = evidence.rules.find((item) =>
    item.factRefs.includes(baziFact.id),
  )!;
  report.baziReasoning.forEach((item: any) => {
    const factSuffixes = {
      strength: [".bazi.month", ".bazi.rootDetails"],
      pattern: [".bazi.monthExposure"],
      climate: [".bazi.month", ".bazi.dayMaster"],
      balance: [".bazi.rootDetails"],
      selection: [".bazi.monthExposure"],
      "bazi-timing": [".bazi.cycles", ".bazi.relations"],
    }[item.topic] as string[];
    const ruleSuffix = {
      strength: ".R-bazi-structure",
      pattern: ".R-bazi-month-exposure",
      climate: ".R-bazi-structure",
      balance: ".R-bazi-structure",
      selection: ".R-bazi-structure",
      "bazi-timing": ".R-bazi-timing",
    }[item.topic] as string;
    Object.assign(item, {
      conclusion: `${item.topic} 结构前提保持未决`,
      supportRefs: factSuffixes.map((suffix) =>
        evidence.facts.find((fact) =>
          fact.candidate === item.candidate && fact.id.endsWith(suffix)
        )!.id
      ),
      counterRefs: [],
      counterReview: `${item.topic} 尚未完成全部反证核对`,
      conditions: `${item.topic} 仅验证前向验收绑定`,
      alternatives: `${item.topic} 仍需传统依据复核`,
      ruleRefs: [evidence.rules.find((candidateRule) =>
        candidateRule.candidate === item.candidate &&
        candidateRule.id.endsWith(ruleSuffix)
      )!.id],
    });
    if (item.topic === "bazi-timing") {
      const cycleRef = item.supportRefs.find((id: string) =>
        id.endsWith(".bazi.cycles")
      );
      const natalRef = item.supportRefs.find((id: string) =>
        id.endsWith(".bazi.relations")
      );
      const cycles = evidence.facts.find((fact) => fact.id === cycleRef)!.value as {
        yearly: { year: number; pillar: string; boundary: "lichun" }[];
      };
      item.timingChain = {
        target: "general",
        cycleRefs: [cycleRef],
        annualReviews: item.years.map((year: number) => {
          const annual = cycles.yearly.find((entry) => entry.year === year)!;
          return {
            ...annual,
            natalRefs: [natalRef],
            review: `${year} ${annual.pillar} 只验证本命与运年作用链结构，现实结果未裁定。`,
          };
        }),
        crossLayerReview: "已分开本命结构、大运阶段与立春流年，未把干支关系直接换成事件。",
        missingLinks: ["缺少现实触发资料"],
        realityBasis: {
          status: "not-provided",
          summary: "验收输入没有现实经历或目标。",
          source: null,
        },
        withdrawalConditions: "出生资料、起运边界或现实条件变化时撤回并重算。",
      };
    }
  });
  const reasoningRefs = report.baziReasoning
    .filter((item: any) => item.topic !== "bazi-timing")
    .map((item: any) => ({
      candidate: item.candidate,
      topic: item.topic,
    }));
  report.ziweiReasoning.forEach((item: any) => {
    const base = evidence.facts.find((fact) =>
      fact.candidate === item.candidate && fact.id.endsWith(".ziwei.base")
    )!;
    const palaceName = {
      "ziwei-structure": "命宫",
      "ziwei-career": "官禄",
      "ziwei-wealth": "财帛",
      "ziwei-relationships": "夫妻",
    }[item.topic] as string | undefined;
    const topicPalace = palaceName
      ? evidence.facts.find((fact) =>
          fact.candidate === item.candidate &&
          fact.id.includes(".ziwei.palace-") &&
          (fact.value as { name?: string }).name === palaceName
        )!
      : null;
    const ruleSuffix = {
      "ziwei-structure": ".R-ziwei-事业",
      "ziwei-career": ".R-ziwei-事业",
      "ziwei-wealth": ".R-ziwei-财运",
      "ziwei-relationships": ".R-ziwei-关系",
      "ziwei-timing": ".R-ziwei-transformations",
    }[item.topic] as string;
    const ziweiRule = evidence.rules.find((rule) =>
      rule.candidate === item.candidate && rule.id.endsWith(ruleSuffix)
    )!;
    const timingRefs = item.topic === "ziwei-timing"
      ? {
          transformation: evidence.facts.find((fact) =>
            fact.candidate === item.candidate &&
            fact.id.endsWith(".ziwei.transformations")
          )!.id,
          cycle: evidence.facts.find((fact) =>
            fact.candidate === item.candidate && fact.id.endsWith(".ziwei.cycles")
          )!.id,
          palace: evidence.facts.find((fact) =>
            fact.candidate === item.candidate && fact.id.endsWith(".ziwei.palace-0")
          )!.id,
        }
      : null;
    Object.assign(item, {
      conclusion: `${item.topic} 紫微结构前提保持未决`,
      supportRefs: timingRefs
        ? [timingRefs.transformation, timingRefs.cycle, timingRefs.palace]
        : [base.id, topicPalace!.id],
      counterRefs: [],
      counterReview: `${item.topic} 尚未完成联宫与跨层反证核对`,
      conditions: `${item.topic} 仅验证前向验收绑定`,
      alternatives: `${item.topic} 仍需主题宫与现实资料复核`,
      ruleRefs: [ziweiRule.id],
      ...(timingRefs ? {
        timingChain: {
          target: "general",
          years: [...evidence.years],
          transformationRefs: [timingRefs.transformation],
          cycleRefs: [timingRefs.cycle],
          palaceRefs: [timingRefs.palace],
          crossLayerReview: "已分开本命、大限和流年层，未把标签直接换成事件。",
          missingLinks: ["缺少现实触发资料"],
          realityBasis: {
            status: "not-provided",
            summary: "验收输入没有现实经历或目标。",
            source: null,
          },
          withdrawalConditions: "出生资料或层级定位变化时撤回并重算。",
        },
      } : {}),
    });
  });
  report.uncertainty = "本报告只用于合成验收，不作现实预测保证";
  report.sections = SECTION_IDS.map((id) => ({
    id,
    claims: [
      {
        text: "当前依据只支持条件性解释，不能把未决前提写成确定结论。",
        kind: "interpretation",
        factRefs: [baziFact.id],
        ruleRefs: [rule.id],
        reasoningRefs,
        premiseStatus: "unresolved",
        conditions: "结论随前提复核结果调整",
        confidence: "low",
      },
    ],
  }));
  report.crossSystem = [
    {
      target: "general",
      years: [],
      relationship: "insufficient",
      text: "两套体系的事实不足以把未决八字前提升级为确定结论。",
      factRefs: [baziFact.id, ziweiFact.id],
      reasoningRefs: [
        ...reasoningRefs,
        {
          candidate: report.ziweiReasoning[0].candidate,
          topic: "ziwei-structure",
        },
      ],
      premiseStatus: "unresolved",
    },
  ];
  report.assertions = [{ factRef: baziFact.id, value: baziFact.value }];
  return report;
}

function validResponseClaims(
  response: string,
  reportSha256: string,
  report: ReturnType<typeof validAcceptanceReport>,
) {
  const claim = report.sections.find((section: any) => section.id === "summary")!
    .claims[0];
  return {
    schema: "whoami.response-claims.v1",
    reportSha256,
    paragraphs: response
      .trim()
      .split(/\r?\n[ \t]*\r?\n/u)
      .map((text, index) => ({
        id: `paragraph-${index + 1}`,
        text: text.trim(),
        reportClaims: [{ section: "summary", claimIndex: 0 }],
        reasoningRefs: claim.reasoningRefs,
        premiseStatus: claim.premiseStatus,
      })),
  };
}

test("自然语言验收绑定产物，缺运行回执只能是 partial", () => {
  const dir = mkdtempSync(join(tmpdir(), "whoami-acceptance-"));
  const artifact = (path: string, content: string) => {
    writeFileSync(join(dir, path), content);
    return { path, sha256: hash(content), bytes: Buffer.byteLength(content) };
  };
  const manifest = {
    schema: "whoami.acceptance-run.v1",
    suiteId: "synthetic-forward-001",
    skill: artifact("SKILL.md", "skill snapshot\n"),
    task: artifact("task.md", "task snapshot\n"),
    rubric: artifact("rubric.md", "rubric snapshot\n"),
    cases: [
      {
        id: "case-01",
        input: artifact("input.json", json(birthInput)),
        context: artifact("context.json", json(contextFor(birthInput, [2026]))),
        response: artifact("response.md", "response\n"),
      },
    ],
    runtime: {
      provider: "codex",
      model: "UNVERIFIED",
      modelVersion: "UNVERIFIED",
      reasoningEffort: "UNVERIFIED",
      temperature: null,
      seed: null,
      receipt: null,
    },
    review: {
      status: "PASS",
      factErrors: 0,
      premiseOmissions: 0,
      candidateMixing: 0,
      unsupportedTimingClaims: 0,
      unsafeClaims: 0,
    },
  };
  const result = checkAcceptanceManifest(manifest, join(dir, "manifest.json"));
  assert.equal(result.status, "partial");
  assert.equal(result.runtimeBound, false);
  assert.equal(result.runtimeAttested, false);
  assert.equal(result.runtimeVerified, false);
  assert.equal(result.runtimeKeyId, null);
  assert.equal(result.artifactCount, 6);
  assert.deepEqual(result.caseChecks, [
    {
      id: "case-01",
      responseSafety: "pass",
      reportValidation: "not-applicable",
      responseReportPremise: "not-applicable",
      responseClaimsValidation: "not-applicable",
    },
  ]);

  const unsafeResponse = artifact("unsafe-response.md", "这项投资稳赚不赔。\n");
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...manifest,
          cases: [{ ...manifest.cases[0], response: unsafeResponse }],
        },
        join(dir, "manifest-unsafe-response.json"),
      ),
    (error: unknown) =>
      error instanceof InputError && error.code === "UNSAFE_REPORT_CLAIM",
  );

  const emptyResponse = artifact("empty-response.md", " \n");
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...manifest,
          cases: [{ ...manifest.cases[0], response: emptyResponse }],
        },
        join(dir, "manifest-empty-response.json"),
      ),
    /response 不能为空/,
  );

  const orphanResponseClaims = artifact(
    "orphan-response-claims.json",
    json({
      schema: "whoami.response-claims.v1",
      reportSha256: "0".repeat(64),
      paragraphs: [],
    }),
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...manifest,
          cases: [
            { ...manifest.cases[0], responseClaims: orphanResponseClaims },
          ],
        },
        join(dir, "manifest-orphan-response-claims.json"),
      ),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
  );
});

test("前向验收可绑定并复算 v5 报告，运行回执也必须绑定报告", () => {
  const dir = mkdtempSync(join(tmpdir(), "whoami-acceptance-report-"));
  const artifact = (path: string, content: string) => {
    writeFileSync(join(dir, path), content);
    return { path, sha256: hash(content), bytes: Buffer.byteLength(content) };
  };
  const evidence = contextFor(birthInput, [2026]);
  const input = artifact("input.json", json(birthInput));
  const context = artifact("context.json", json(evidence));
  const response = artifact(
    "response.md",
    "当前尚不足以把木定成唯一用神，完整依据见绑定报告。\n",
  );
  const reportValue = validAcceptanceReport(evidence);
  const report = artifact("report.json", json(reportValue));
  const responseClaims = artifact(
    "response-claims.json",
    json(validResponseClaims("当前尚不足以把木定成唯一用神，完整依据见绑定报告。\n", report.sha256, reportValue)),
  );
  const runtimeFields = {
    provider: "synthetic-host",
    model: "synthetic-model",
    modelVersion: "v1",
    reasoningEffort: "high",
    temperature: null,
    seed: null,
  };
  const base = {
    schema: "whoami.acceptance-run.v1",
    suiteId: "synthetic-report-forward",
    skill: artifact("SKILL.md", "skill snapshot\n"),
    task: artifact("task.md", "task snapshot\n"),
    rubric: artifact("rubric.md", "rubric snapshot\n"),
    cases: [
      { id: "case", input, context, response, report, responseClaims },
    ],
    runtime: { ...runtimeFields, receipt: null },
    review: {
      status: "PASS",
      factErrors: 0,
      premiseOmissions: 0,
      candidateMixing: 0,
      unsupportedTimingClaims: 0,
      unsafeClaims: 0,
    },
  };
  const checked = checkAcceptanceManifest(base, join(dir, "manifest.json"));
  assert.equal(checked.status, "partial");
  assert.equal(checked.artifactCount, 8);
  assert.equal(checked.bindings.cases[0].report, report.sha256);
  assert.equal(
    checked.bindings.cases[0].responseClaims,
    responseClaims.sha256,
  );
  assert.deepEqual(checked.caseChecks[0], {
    id: "case",
    responseSafety: "pass",
    reportValidation: "pass",
    responseReportPremise: "pass",
    responseClaimsValidation: "pass",
  });

  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...base,
          cases: [{ id: "case", input, context, response, report }],
        },
        join(dir, "manifest-missing-response-claims.json"),
      ),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "INVALID_ACCEPTANCE_RESPONSE_CLAIMS",
  );

  const mismatchedResponseClaimsValue = validResponseClaims(
    "当前尚不足以把木定成唯一用神，完整依据见绑定报告。\n",
    report.sha256,
    reportValue,
  );
  mismatchedResponseClaimsValue.paragraphs[0].text = "另一段回答";
  const mismatchedResponseClaims = artifact(
    "mismatched-response-claims.json",
    json(mismatchedResponseClaimsValue),
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...base,
          cases: [
            {
              ...base.cases[0],
              responseClaims: mismatchedResponseClaims,
            },
          ],
        },
        join(dir, "manifest-mismatched-response-claims.json"),
      ),
    (error: unknown) =>
      error instanceof InputError && error.code === "RESPONSE_CLAIMS_MISMATCH",
  );

  const wrongReportHashValue = validResponseClaims(
    "当前尚不足以把木定成唯一用神，完整依据见绑定报告。\n",
    "0".repeat(64),
    reportValue,
  );
  const wrongReportHash = artifact(
    "wrong-report-hash-response-claims.json",
    json(wrongReportHashValue),
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...base,
          cases: [
            { ...base.cases[0], responseClaims: wrongReportHash },
          ],
        },
        join(dir, "manifest-wrong-report-hash.json"),
      ),
    (error: unknown) =>
      error instanceof InputError && error.code === "RESPONSE_CLAIMS_MISMATCH",
  );

  const incompleteReasoningValue = validResponseClaims(
    "当前尚不足以把木定成唯一用神，完整依据见绑定报告。\n",
    report.sha256,
    reportValue,
  );
  incompleteReasoningValue.paragraphs[0].reasoningRefs.pop();
  const incompleteReasoning = artifact(
    "incomplete-reasoning-response-claims.json",
    json(incompleteReasoningValue),
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...base,
          cases: [
            { ...base.cases[0], responseClaims: incompleteReasoning },
          ],
        },
        join(dir, "manifest-incomplete-reasoning.json"),
      ),
    (error: unknown) =>
      error instanceof InputError && error.code === "RESPONSE_CLAIMS_MISMATCH",
  );

  const contradictoryResponse = artifact(
    "contradictory-response.md",
    "木是唯一用神，结论已经确定，无需再核对其他条件。\n",
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...base,
          cases: [{ ...base.cases[0], response: contradictoryResponse }],
        },
        join(dir, "manifest-contradictory-response.json"),
      ),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "RESPONSE_REPORT_CONTRADICTION",
  );

  const invalidReport = validAcceptanceReport(evidence);
  invalidReport.sections[0].claims[0].text =
    "用神已经确定，无需再核对其他条件。";
  const invalid = artifact("invalid-report.json", json(invalidReport));
  assert.throws(
    () =>
      checkAcceptanceManifest(
        { ...base, cases: [{ ...base.cases[0], report: invalid }] },
        join(dir, "manifest-invalid.json"),
      ),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "UNRESOLVED_PREMISE_CLAIM",
  );

  const receiptContent =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v1",
      runId: "report-run-1",
      startedAt: "2026-09-24T00:00:00Z",
      runtime: runtimeFields,
      bindings: {
        skill: base.skill.sha256,
        task: base.task.sha256,
        cases: [
          {
            id: "case",
            input: input.sha256,
            context: context.sha256,
            response: response.sha256,
            report: report.sha256,
            responseClaims: responseClaims.sha256,
          },
        ],
      },
    }) + "\n";
  const receipt = artifact("receipt.json", receiptContent);
  const bound = checkAcceptanceManifest(
    { ...base, runtime: { ...runtimeFields, receipt } },
    join(dir, "manifest-bound.json"),
  );
  assert.equal(bound.runtimeBound, true);
  assert.equal(bound.artifactCount, 9);

  const receiptWithoutReportContent =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v1",
      runId: "report-run-2",
      startedAt: "2026-09-24T00:00:00Z",
      runtime: runtimeFields,
      bindings: {
        skill: base.skill.sha256,
        task: base.task.sha256,
        cases: [
          {
            id: "case",
            input: input.sha256,
            context: context.sha256,
            response: response.sha256,
            report: report.sha256,
          },
        ],
      },
    }) + "\n";
  const receiptWithoutReport = artifact(
    "receipt-without-report.json",
    receiptWithoutReportContent,
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...base,
          runtime: { ...runtimeFields, receipt: receiptWithoutReport },
        },
        join(dir, "manifest-unbound-report.json"),
      ),
    /未绑定本次 Skill、任务、输入、context、回答、可选报告及结构化答复绑定/,
  );
});

test("验收拒绝产物漂移、越界路径和带问题的 PASS", () => {
  const dir = mkdtempSync(join(tmpdir(), "whoami-acceptance-invalid-"));
  const artifact = (path: string, content: string) => {
    writeFileSync(join(dir, path), content);
    return { path, sha256: hash(content), bytes: Buffer.byteLength(content) };
  };
  const skill = artifact("SKILL.md", "skill snapshot\n");
  const task = artifact("task.md", "task snapshot\n");
  const rubric = artifact("rubric.md", "rubric snapshot\n");
  const input = artifact("input.json", json(birthInput));
  const context = artifact(
    "context.json",
    json(contextFor(birthInput, [2026])),
  );
  const response = artifact("response.md", "response\n");
  const runtimeFields = {
    provider: "codex",
    model: "model",
    modelVersion: "version",
    reasoningEffort: "medium",
    temperature: "default",
    seed: "default",
  };
  const receiptContent =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v1",
      runId: "run-1",
      startedAt: "2026-09-23T00:00:00Z",
      runtime: runtimeFields,
      bindings: {
        skill: skill.sha256,
        task: task.sha256,
        cases: [
          {
            id: "case",
            input: input.sha256,
            context: context.sha256,
            response: response.sha256,
          },
        ],
      },
    }) + "\n";
  writeFileSync(join(dir, "receipt.json"), receiptContent);
  const receipt = {
    path: "receipt.json",
    sha256: hash(receiptContent),
    bytes: Buffer.byteLength(receiptContent),
  };
  const base = {
    schema: "whoami.acceptance-run.v1",
    suiteId: "invalid",
    skill,
    task,
    rubric,
    cases: [{ id: "case", input, context, response }],
    runtime: {
      ...runtimeFields,
      receipt,
    },
    review: {
      status: "PASS",
      factErrors: 1,
      premiseOmissions: 0,
      candidateMixing: 0,
      unsupportedTimingClaims: 0,
      unsafeClaims: 0,
    },
  };
  assert.throws(
    () => checkAcceptanceManifest(base, join(dir, "manifest.json")),
    /不能把 review.status 标为 PASS/,
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        { ...base, skill: { ...skill, path: "../SKILL.md" } },
        join(dir, "manifest.json"),
      ),
    /不能越出/,
  );
  if (process.platform !== "win32") {
    const outside = mkdtempSync(join(tmpdir(), "whoami-acceptance-outside-"));
    writeFileSync(join(outside, "secret.txt"), "secret");
    symlinkSync(join(outside, "secret.txt"), join(dir, "escape-link"));
    assert.throws(
      () =>
        checkAcceptanceManifest(
          {
            ...base,
        skill: {
          path: "escape-link",
              sha256: hash("secret"),
              bytes: Buffer.byteLength("secret"),
            },
          },
          join(dir, "manifest.json"),
        ),
      /符号链接越出/,
    );
  }
  assert.throws(
    () =>
      checkAcceptanceManifest(
        { ...base, skill: { ...skill, sha256: "0".repeat(64) } },
        join(dir, "manifest.json"),
      ),
    /哈希或大小/,
  );
  const boundOnly = checkAcceptanceManifest(
    { ...base, review: { ...base.review, factErrors: 0 } },
    join(dir, "manifest.json"),
  );
  assert.equal(boundOnly.status, "partial");
  assert.equal(boundOnly.runtimeBound, true);
  assert.equal(boundOnly.runtimeAttested, false);
  assert.equal(boundOnly.runtimeVerified, false);
  assert.equal(boundOnly.runtimeKeyId, null);
  assert.match(boundOnly.limitations.join("\n"), /没有受信宿主证明/);
  const failed = checkAcceptanceManifest(
    { ...base, review: { ...base.review, status: "FAIL" } },
    join(dir, "manifest.json"),
  );
  assert.equal(failed.status, "failed");
  assert.equal(failed.reviewStatus, "FAIL");
  assert.equal(failed.runtimeBound, true);
  assert.equal(failed.runtimeAttested, false);
  assert.equal(failed.runtimeVerified, false);
  for (const status of [["FAIL"], ["PASS"]])
    assert.throws(
      () =>
        checkAcceptanceManifest(
          { ...base, review: { ...base.review, status } },
          join(dir, "manifest.json"),
        ),
      /review.status 无效/,
    );

  const trustDir = mkdtempSync(join(tmpdir(), "whoami-runtime-trust-"));
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  const publicKeyPath = join(trustDir, "runtime-public.pem");
  const publicKeyPem = publicKey.export({ format: "pem", type: "spki" });
  writeFileSync(publicKeyPath, publicKeyPem);
  const keyId = ed25519PublicKeyId(publicKey);
  const runId = "run-attested-1";
  const startedAt = "2026-09-23T12:00:00Z";
  const v2Bindings = {
    skill: skill.sha256,
    task: task.sha256,
    rubric: rubric.sha256,
    cases: [
      {
        id: "case",
        input: input.sha256,
        context: context.sha256,
        response: response.sha256,
      },
    ],
  } satisfies RuntimeBindings;
  const passReview = {
    status: "PASS",
    factErrors: 0,
    premiseOmissions: 0,
    candidateMixing: 0,
    unsupportedTimingClaims: 0,
    unsafeClaims: 0,
  } satisfies AttestedReview;
  const signedV2Receipt = (
    path: string,
    signedRunId: string,
    signedRuntime: RuntimeIdentity,
    signedReview: AttestedReview,
    signedBindings: RuntimeBindings = v2Bindings,
  ) => {
    const signedSignature = sign(
      null,
      runtimeAttestationPayload({
        suiteId: base.suiteId,
        runId: signedRunId,
        startedAt,
        runtime: signedRuntime,
        bindings: signedBindings,
        review: signedReview,
      }),
      privateKey,
    ).toString("base64");
    const content =
      JSON.stringify({
        schema: "whoami.runtime-receipt.v2",
        runId: signedRunId,
        startedAt,
        runtime: signedRuntime,
        bindings: signedBindings,
        attestation: {
          algorithm: "Ed25519",
          keyId,
          signature: signedSignature,
        },
      }) + "\n";
    return {
      artifact: artifact(path, content),
      signature: signedSignature,
    };
  };
  const signedPassReceipt = signedV2Receipt(
    "receipt-v2.json",
    runId,
    runtimeFields,
    passReview,
  );
  const signature = signedPassReceipt.signature;
  const v2Receipt = signedPassReceipt.artifact;
  const normalPayload = runtimeAttestationPayload({
    suiteId: base.suiteId,
    runId,
    startedAt,
    runtime: runtimeFields,
    bindings: v2Bindings,
    review: passReview,
  });
  const reorderedRuntime = {
    seed: runtimeFields.seed,
    temperature: runtimeFields.temperature,
    reasoningEffort: runtimeFields.reasoningEffort,
    modelVersion: runtimeFields.modelVersion,
    model: runtimeFields.model,
    provider: runtimeFields.provider,
  };
  const reorderedBindings = {
    cases: v2Bindings.cases.map((item) => ({
      response: item.response,
      context: item.context,
      input: item.input,
      id: item.id,
    })),
    rubric: v2Bindings.rubric,
    task: v2Bindings.task,
    skill: v2Bindings.skill,
  };
  const reorderedReview = {
    unsafeClaims: passReview.unsafeClaims,
    unsupportedTimingClaims: passReview.unsupportedTimingClaims,
    candidateMixing: passReview.candidateMixing,
    premiseOmissions: passReview.premiseOmissions,
    factErrors: passReview.factErrors,
    status: passReview.status,
  };
  const reorderedPayload = runtimeAttestationPayload({
    suiteId: base.suiteId,
    runId,
    startedAt,
    runtime: reorderedRuntime,
    bindings: reorderedBindings,
    review: reorderedReview,
  });
  assert.equal(reorderedPayload.compare(normalPayload), 0);
  const reorderedReceiptContent =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v2",
      runId,
      startedAt,
      runtime: reorderedRuntime,
      bindings: reorderedBindings,
      attestation: {
        algorithm: "Ed25519",
        keyId,
        signature: sign(null, reorderedPayload, privateKey).toString("base64"),
      },
    }) + "\n";
  const reorderedReceipt = artifact(
    "receipt-v2-reordered.json",
    reorderedReceiptContent,
  );
  const v2Manifest = {
    ...base,
    runtime: { ...base.runtime, receipt: v2Receipt },
    review: passReview,
  };
  const attested = checkAcceptanceManifest(
    v2Manifest,
    join(dir, "manifest-v2.json"),
    { trustedRuntimeKeyPath: publicKeyPath },
  );
  assert.equal(attested.status, "verified");
  assert.equal(attested.runtimeBound, true);
  assert.equal(attested.runtimeAttested, true);
  assert.equal(attested.runtimeVerified, true);
  assert.equal(attested.runtimeKeyId, keyId);
  const reorderedAttested = checkAcceptanceManifest(
    {
      ...v2Manifest,
      runtime: { ...v2Manifest.runtime, receipt: reorderedReceipt },
    },
    join(dir, "manifest-v2.json"),
    { trustedRuntimeKeyPath: publicKeyPath },
  );
  assert.equal(reorderedAttested.status, "verified");
  const partialReview = {
    ...passReview,
    status: "PARTIAL",
  } satisfies AttestedReview;
  const failedReview = {
    ...passReview,
    status: "FAIL",
    factErrors: 1,
  } satisfies AttestedReview;
  for (const tamperedReview of [partialReview, failedReview])
    assert.throws(
      () =>
        checkAcceptanceManifest(
          { ...v2Manifest, review: tamperedReview },
          join(dir, "manifest-v2.json"),
          { trustedRuntimeKeyPath: publicKeyPath },
        ),
      /签名无效/,
    );
  const replacedRubric = artifact(
    "rubric-replaced.md",
    "replaced rubric snapshot\n",
  );
  const tamperedRubricBindings = {
    ...v2Bindings,
    rubric: replacedRubric.sha256,
  };
  const tamperedRubricReceiptContent =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v2",
      runId,
      startedAt,
      runtime: runtimeFields,
      bindings: tamperedRubricBindings,
      attestation: { algorithm: "Ed25519", keyId, signature },
    }) + "\n";
  const tamperedRubricReceipt = artifact(
    "receipt-v2-tampered-rubric.json",
    tamperedRubricReceiptContent,
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...v2Manifest,
          rubric: replacedRubric,
          runtime: {
            ...v2Manifest.runtime,
            receipt: tamperedRubricReceipt,
          },
        },
        join(dir, "manifest-v2-tampered-rubric.json"),
        { trustedRuntimeKeyPath: publicKeyPath },
      ),
    /签名无效/,
  );
  const partialReceipt = signedV2Receipt(
    "receipt-v2-partial.json",
    "run-attested-partial",
    runtimeFields,
    partialReview,
  ).artifact;
  const attestedPartial = checkAcceptanceManifest(
    {
      ...v2Manifest,
      runtime: { ...v2Manifest.runtime, receipt: partialReceipt },
      review: partialReview,
    },
    join(dir, "manifest-v2-partial.json"),
    { trustedRuntimeKeyPath: publicKeyPath },
  );
  assert.equal(attestedPartial.runtimeVerified, true);
  assert.equal(attestedPartial.status, "partial");
  const failedReceipt = signedV2Receipt(
    "receipt-v2-failed.json",
    "run-attested-failed",
    runtimeFields,
    failedReview,
  ).artifact;
  const attestedFailed = checkAcceptanceManifest(
    {
      ...v2Manifest,
      runtime: { ...v2Manifest.runtime, receipt: failedReceipt },
      review: failedReview,
    },
    join(dir, "manifest-v2-failed.json"),
    { trustedRuntimeKeyPath: publicKeyPath },
  );
  assert.equal(attestedFailed.runtimeVerified, true);
  assert.equal(attestedFailed.status, "failed");
  assert.throws(
    () =>
      checkAcceptanceManifest(v2Manifest, join(dir, "manifest-v2.json")),
    /需要 --trusted-runtime-key/,
  );
  writeFileSync(join(dir, "runtime-public.pem"), publicKeyPem);
  assert.throws(
    () =>
      checkAcceptanceManifest(v2Manifest, join(dir, "manifest-v2.json"), {
        trustedRuntimeKeyPath: join(dir, "runtime-public.pem"),
      }),
    /清单目录树之外/,
  );
  const otherTrustDir = mkdtempSync(join(tmpdir(), "whoami-runtime-wrong-"));
  const otherKey = generateKeyPairSync("ed25519").publicKey;
  const otherKeyPath = join(otherTrustDir, "runtime-public.pem");
  writeFileSync(
    otherKeyPath,
    otherKey.export({ format: "pem", type: "spki" }),
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(v2Manifest, join(dir, "manifest-v2.json"), {
        trustedRuntimeKeyPath: otherKeyPath,
      }),
    /keyId 与受信公钥不一致/,
  );
  const rsaTrustDir = mkdtempSync(join(tmpdir(), "whoami-runtime-rsa-"));
  const rsaKey = generateKeyPairSync("rsa", { modulusLength: 2048 }).publicKey;
  const rsaKeyPath = join(rsaTrustDir, "runtime-public.pem");
  writeFileSync(rsaKeyPath, rsaKey.export({ format: "pem", type: "spki" }));
  assert.throws(
    () =>
      checkAcceptanceManifest(v2Manifest, join(dir, "manifest-v2.json"), {
        trustedRuntimeKeyPath: rsaKeyPath,
      }),
    /必须是 Ed25519 公钥/,
  );
  const invalidSignatureContent =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v2",
      runId,
      startedAt,
      runtime: runtimeFields,
      bindings: v2Bindings,
      attestation: {
        algorithm: "Ed25519",
        keyId,
        signature: sign(null, Buffer.from("wrong payload"), privateKey).toString(
          "base64",
        ),
      },
    }) + "\n";
  const invalidSignatureReceipt = artifact(
    "receipt-v2-invalid-signature.json",
    invalidSignatureContent,
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...v2Manifest,
          runtime: {
            ...v2Manifest.runtime,
            receipt: invalidSignatureReceipt,
          },
        },
        join(dir, "manifest-v2.json"),
        { trustedRuntimeKeyPath: publicKeyPath },
      ),
    /签名无效/,
  );
  const invalidBase64Content =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v2",
      runId,
      startedAt,
      runtime: runtimeFields,
      bindings: v2Bindings,
      attestation: {
        algorithm: "Ed25519",
        keyId,
        signature: "not base64!",
      },
    }) + "\n";
  const invalidBase64Receipt = artifact(
    "receipt-v2-invalid-base64.json",
    invalidBase64Content,
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...v2Manifest,
          runtime: { ...v2Manifest.runtime, receipt: invalidBase64Receipt },
        },
        join(dir, "manifest-v2.json"),
        { trustedRuntimeKeyPath: publicKeyPath },
      ),
    /必须是规范 base64/,
  );
  const incompleteRuntime = { ...runtimeFields, model: "UNVERIFIED" };
  const incompleteRunId = "run-attested-incomplete";
  const incompleteSignature = sign(
    null,
    runtimeAttestationPayload({
      suiteId: base.suiteId,
      runId: incompleteRunId,
      startedAt,
      runtime: incompleteRuntime,
      bindings: v2Bindings,
      review: passReview,
    }),
    privateKey,
  ).toString("base64");
  const incompleteReceiptContent =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v2",
      runId: incompleteRunId,
      startedAt,
      runtime: incompleteRuntime,
      bindings: v2Bindings,
      attestation: {
        algorithm: "Ed25519",
        keyId,
        signature: incompleteSignature,
      },
    }) + "\n";
  const incompleteReceipt = artifact(
    "receipt-v2-incomplete-runtime.json",
    incompleteReceiptContent,
  );
  const incompleteAttested = checkAcceptanceManifest(
    {
      ...base,
      runtime: { ...incompleteRuntime, receipt: incompleteReceipt },
      review: { ...base.review, factErrors: 0 },
    },
    join(dir, "manifest-v2-incomplete.json"),
    { trustedRuntimeKeyPath: publicKeyPath },
  );
  assert.equal(incompleteAttested.runtimeBound, false);
  assert.equal(incompleteAttested.runtimeAttested, true);
  assert.equal(incompleteAttested.runtimeVerified, false);
  assert.equal(incompleteAttested.status, "partial");
  const invalidStartedAtContent =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v1",
      runId: "invalid-time",
      startedAt: "yesterday evening",
      runtime: runtimeFields,
      bindings: v2Bindings,
    }) + "\n";
  const invalidStartedAtReceipt = artifact(
    "receipt-invalid-started-at.json",
    invalidStartedAtContent,
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...base,
          runtime: {
            ...base.runtime,
            receipt: invalidStartedAtReceipt,
          },
          review: { ...base.review, factErrors: 0 },
        },
        join(dir, "manifest.json"),
      ),
    /必须是带时区或 Z 的绝对时刻/,
  );
  writeFileSync(join(dir, "manifest-v2.json"), JSON.stringify(v2Manifest));
  const cliAttested = spawnSync(
    process.execPath,
    [
      "--import",
      "tsx",
      "src/cli.ts",
      "acceptance-check",
      "--manifest",
      join(dir, "manifest-v2.json"),
      "--trusted-runtime-key",
      publicKeyPath,
    ],
    { encoding: "utf8" },
  );
  assert.equal(cliAttested.status, 0, cliAttested.stderr);
  assert.equal(JSON.parse(cliAttested.stdout).status, "verified");
  for (const temperature of [undefined, {}, true, Number.POSITIVE_INFINITY])
    assert.throws(
      () =>
        checkAcceptanceManifest(
          {
            ...base,
            runtime: { ...base.runtime, temperature, receipt: null },
            review: { ...base.review, factErrors: 0 },
          },
          join(dir, "manifest.json"),
        ),
      /必须显式为 null、有限数字或非空文字/,
    );
  const receiptWithoutTemperature =
    JSON.stringify({
      schema: "whoami.runtime-receipt.v1",
      runId: "run-missing-temperature",
      startedAt: "2026-09-23T00:00:00Z",
      runtime: {
        provider: "codex",
        model: "model",
        modelVersion: "version",
        reasoningEffort: "medium",
        seed: "default",
      },
      bindings: {
        skill: skill.sha256,
        task: task.sha256,
        cases: [
          {
            id: "case",
            input: input.sha256,
            context: context.sha256,
            response: response.sha256,
          },
        ],
      },
    }) + "\n";
  writeFileSync(join(dir, "receipt-no-temperature.json"), receiptWithoutTemperature);
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...base,
          runtime: {
            ...base.runtime,
            receipt: {
              path: "receipt-no-temperature.json",
              sha256: hash(receiptWithoutTemperature),
              bytes: Buffer.byteLength(receiptWithoutTemperature),
            },
          },
          review: { ...base.review, factErrors: 0 },
        },
        join(dir, "manifest.json"),
      ),
    /runtime receipt.temperature 必须显式/,
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...base,
          runtime: { ...base.runtime, model: "different-model" },
          review: { ...base.review, factErrors: 0 },
        },
        join(dir, "manifest.json"),
      ),
    /模型或采样参数不一致/,
  );
  writeFileSync(join(dir, "..inside.txt"), "inside");
  const inside = {
    path: "..inside.txt",
    sha256: hash("inside"),
    bytes: Buffer.byteLength("inside"),
  };
  const valid = {
    ...base,
    skill: inside,
    runtime: { ...base.runtime, receipt: null },
    review: { ...base.review, factErrors: 0 },
  };
  assert.equal(
    checkAcceptanceManifest(valid, join(dir, "manifest.json")).status,
    "partial",
  );
});

test("验收拒绝与输入或当前引擎不一致的 context", () => {
  const dir = mkdtempSync(join(tmpdir(), "whoami-acceptance-binding-"));
  const artifact = (path: string, content: string) => {
    writeFileSync(join(dir, path), content);
    return { path, sha256: hash(content), bytes: Buffer.byteLength(content) };
  };
  const input = artifact("input.json", json(birthInput));
  const otherContext = artifact(
    "other-context.json",
    json(contextFor({ ...birthInput, time: "06:00" }, [2026])),
  );
  const manifest = {
    schema: "whoami.acceptance-run.v1",
    suiteId: "binding",
    skill: artifact("SKILL.md", "skill\n"),
    task: artifact("task.md", "task\n"),
    rubric: artifact("rubric.md", "rubric\n"),
    cases: [{
      id: "case",
      input,
      context: otherContext,
      response: artifact("response.md", "response\n"),
    }],
    runtime: {
      provider: "UNVERIFIED",
      model: "UNVERIFIED",
      modelVersion: "UNVERIFIED",
      reasoningEffort: "UNVERIFIED",
      temperature: null,
      seed: null,
      receipt: null,
    },
    review: {
      status: "PASS",
      factErrors: 0,
      premiseOmissions: 0,
      candidateMixing: 0,
      unsupportedTimingClaims: 0,
      unsafeClaims: 0,
    },
  };
  assert.throws(
    () => checkAcceptanceManifest(manifest, join(dir, "manifest.json")),
    /不是由对应 input、years 与当前引擎生成的同类结果/,
  );

  const tampered = contextFor(birthInput, [2026]) as any;
  tampered.facts[0].value = { invented: true };
  const tamperedArtifact = artifact("tampered-context.json", json(tampered));
  assert.throws(
    () => checkAcceptanceManifest(
      {
        ...manifest,
        cases: [{ ...manifest.cases[0], context: tamperedArtifact }],
      },
      join(dir, "manifest.json"),
    ),
    /不是由对应 input、years 与当前引擎生成的同类结果/,
  );
});

test("验收可绑定未知时辰的 needs-input chart，但不能冒充 evidence", () => {
  const dir = mkdtempSync(join(tmpdir(), "whoami-acceptance-needs-input-"));
  const artifact = (path: string, content: string) => {
    writeFileSync(join(dir, path), content);
    return { path, sha256: hash(content), bytes: Buffer.byteLength(content) };
  };
  const unknownInput = { ...birthInput, time: null };
  const needsInput = buildChart(unknownInput, [2026]);
  assert.equal(needsInput.status, "needs-input");
  const manifest = {
    schema: "whoami.acceptance-run.v1",
    suiteId: "needs-input",
    skill: artifact("SKILL.md", "skill\n"),
    task: artifact("task.md", "task\n"),
    rubric: artifact("rubric.md", "rubric\n"),
    cases: [{
      id: "unknown-time",
      input: artifact("input.json", json(unknownInput)),
      context: artifact("context.json", json(needsInput)),
      response: artifact("response.md", "response\n"),
    }],
    runtime: {
      provider: "UNVERIFIED",
      model: "UNVERIFIED",
      modelVersion: "UNVERIFIED",
      reasoningEffort: "UNVERIFIED",
      temperature: null,
      seed: null,
      receipt: null,
    },
    review: {
      status: "PASS",
      factErrors: 0,
      premiseOmissions: 0,
      candidateMixing: 0,
      unsupportedTimingClaims: 0,
      unsafeClaims: 0,
    },
  };
  assert.equal(
    checkAcceptanceManifest(manifest, join(dir, "manifest.json")).status,
    "partial",
  );
  const impossibleReport = artifact("report.json", json({}));
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...manifest,
          cases: [{ ...manifest.cases[0], report: impossibleReport }],
        },
        join(dir, "manifest-with-report.json"),
      ),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "INVALID_ACCEPTANCE_REPORT",
  );

  const fakeEvidence = { ...needsInput, schema: "whoami.evidence.v1" };
  const fake = artifact("fake-evidence.json", json(fakeEvidence));
  assert.throws(
    () => checkAcceptanceManifest(
      { ...manifest, cases: [{ ...manifest.cases[0], context: fake }] },
      join(dir, "manifest.json"),
    ),
    /输入不足，无法生成 evidence/,
  );
});

test("验收可绑定当前引擎的确定性 context error，并拒绝伪造错误", () => {
  const dir = mkdtempSync(join(tmpdir(), "whoami-acceptance-error-"));
  const artifact = (path: string, content: string) => {
    writeFileSync(join(dir, path), content);
    return { path, sha256: hash(content), bytes: Buffer.byteLength(content) };
  };
  const gapInput = {
    ...birthInput,
    date: "2024-03-10",
    time: "02:30",
    place: "纽约（合成）",
    longitude: -74.006,
    timeZone: "America/New_York",
    timeBasis: "civil",
    dstDisambiguation: "later",
  };
  let engineError: InputError | undefined;
  try {
    buildChart(gapInput, [2026]);
  } catch (error) {
    if (error instanceof InputError) engineError = error;
  }
  assert.equal(engineError?.code, "NONEXISTENT_LOCAL_TIME");
  const outcome = contextErrorOutcome(engineError!, [2026]);
  const context = artifact("context-error.json", json(outcome));
  const manifest = {
    schema: "whoami.acceptance-run.v1",
    suiteId: "context-error",
    skill: artifact("SKILL.md", "skill\n"),
    task: artifact("task.md", "task\n"),
    rubric: artifact("rubric.md", "rubric\n"),
    cases: [{
      id: "dst-gap",
      input: artifact("input.json", json(gapInput)),
      context,
      response: artifact("response.md", "response\n"),
    }],
    runtime: {
      provider: "UNVERIFIED",
      model: "UNVERIFIED",
      modelVersion: "UNVERIFIED",
      reasoningEffort: "UNVERIFIED",
      temperature: null,
      seed: null,
      receipt: null,
    },
    review: {
      status: "PASS",
      factErrors: 0,
      premiseOmissions: 0,
      candidateMixing: 0,
      unsupportedTimingClaims: 0,
      unsafeClaims: 0,
    },
  };
  assert.equal(
    checkAcceptanceManifest(manifest, join(dir, "manifest.json")).status,
    "partial",
  );
  const impossibleReport = artifact("report.json", json({}));
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...manifest,
          cases: [{ ...manifest.cases[0], report: impossibleReport }],
        },
        join(dir, "manifest-with-report.json"),
      ),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "INVALID_ACCEPTANCE_REPORT",
  );
  for (const forged of [
    { ...outcome, code: "AMBIGUOUS_LOCAL_TIME" },
    { ...outcome, message: "可以自动改成 03:30" },
    { ...outcome, years: [1800] },
  ]) {
    const forgedArtifact = artifact(
      `forged-${forged.code}-${forged.years[0]}.json`,
      json(forged),
    );
    assert.throws(
      () =>
        checkAcceptanceManifest(
          {
            ...manifest,
            cases: [{ ...manifest.cases[0], context: forgedArtifact }],
          },
          join(dir, "manifest.json"),
        ),
      /不是由对应 input、years 与当前引擎生成的同类结果/,
    );
  }
  const validContext = artifact(
    "false-error.json",
    json(contextErrorOutcome(engineError!, [2026])),
  );
  assert.throws(
    () =>
      checkAcceptanceManifest(
        {
          ...manifest,
          cases: [{
            ...manifest.cases[0],
            input: artifact("valid-input.json", json(birthInput)),
            context: validContext,
          }],
        },
        join(dir, "manifest.json"),
      ),
    /声称计算失败/,
  );
});

test("验收按 context 记录的 evidence 版本与粒度重算：月度与 v1 均可复核，篡改粒度被拒", () => {
  const dir = mkdtempSync(join(tmpdir(), "whoami-acceptance-granularity-"));
  const artifact = (path: string, content: string) => {
    writeFileSync(join(dir, path), content);
    return { path, sha256: hash(content), bytes: Buffer.byteLength(content) };
  };
  const manifestWith = (name: string, context: unknown) => ({
    schema: "whoami.acceptance-run.v1",
    suiteId: `synthetic-${name}`,
    skill: artifact("SKILL.md", "skill snapshot\n"),
    task: artifact("task.md", "task snapshot\n"),
    rubric: artifact("rubric.md", "rubric snapshot\n"),
    cases: [{
      id: "case-01",
      input: artifact("input.json", json(birthInput)),
      context: artifact(`${name}.json`, json(context)),
      response: artifact("response.md", "response\n"),
    }],
    runtime: { provider: "codex", model: "UNVERIFIED", modelVersion: "UNVERIFIED", reasoningEffort: "UNVERIFIED", temperature: null, seed: null, receipt: null },
    review: { status: "PASS", factErrors: 0, premiseOmissions: 0, candidateMixing: 0, unsupportedTimingClaims: 0, unsafeClaims: 0 },
  });
  const month = contextFor(birthInput, [2026], undefined, "month");
  assert.equal(checkAcceptanceManifest(manifestWith("month", month), join(dir, "m1.json")).status, "partial");
  const legacy = contextFor(birthInput, [2026], "whoami.evidence.v1");
  assert.equal(checkAcceptanceManifest(manifestWith("legacy", legacy), join(dir, "m2.json")).status, "partial");
  const { granularity: _dropped, ...claimsYear } = month;
  assert.throws(
    () => checkAcceptanceManifest(manifestWith("tampered", claimsYear), join(dir, "m3.json")),
    (error: unknown) => error instanceof InputError && error.code === "ACCEPTANCE_CONTEXT_MISMATCH",
  );
});
