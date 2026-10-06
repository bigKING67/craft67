import { test } from "node:test";
import assert from "node:assert/strict";
import { InputError } from "../src/input.js";
import * as reportTime from "../src/report-time.js";

const {
  referencedRelativeYears,
  validIsoDate,
  validateReportTemporalText,
} = reportTime;

function temporalErrorCode(
  text: string,
  evidenceYears = [2026, 2027],
  referenceYear = 2026,
) {
  try {
    validateReportTemporalText(
      text,
      "section career claim 0 text",
      evidenceYears,
      referenceYear,
    );
  } catch (error) {
    if (error instanceof InputError) return error.code;
    throw error;
  }
  return null;
}

test("报告时间模块只公开报告层实际使用的四个接口", () => {
  assert.deepEqual(Object.keys(reportTime).sort(), [
    "monthlyLabelMentions",
    "referencedRelativeYears",
    "validIsoDate",
    "validateReportTemporalText",
  ]);
});

test("ISO 钟点按完整时分秒识别，不把分钟秒钟重新当作时分", () => {
  for (const instant of [
    "1991-10-17T06:58:00+08:00[Asia/Shanghai]",
    "1991-10-17T06:58:00Z",
    "1991-10-17t06:58:00z",
    "1991-10-17T06:58:00.125Z",
    "1991-10-17T06:58:00",
    "1991-10-17 06:58:00 Asia/Shanghai",
    "06：58：00",
  ]) assert.equal(temporalErrorCode(`资料记录：${instant}。`), null, instant);
  for (const clock of ["25:58:00", "06:60:00", "06:58:60", "06:58:99.125", "25:58:0", "06:60:000", "06:58:0"])
    for (const text of [`资料记录：${clock}。`, `资料记录：1991-10-17T${clock}Z。`])
      assert.equal(temporalErrorCode(text), "INVALID_CLOCK_TIME", text);
  assert.notEqual(temporalErrorCode("2027-10-17T06:58:00Z适合签约。"), null);
});

test("时间文本验证器独立保持日期、时区、时刻与区间错误优先级", () => {
  for (const [text, code] of [
    ["2027-02-29适合行动吗？", "INVALID_NUMERIC_DATE"],
    [
      "2027-03-14 02:30 America/New_York适合行动吗？",
      "NONEXISTENT_LOCAL_TIME",
    ],
    [
      "2026-11-01T01:30-06:00[America/New_York]适合签约吗？",
      "OFFSET_TIME_ZONE_MISMATCH",
    ],
    [
      "2026-11-01T01:30-04:00[America/New_York]和2026-11-01T05:30Z哪个更适合签约？",
      "DUPLICATE_ABSOLUTE_TIME",
    ],
    [
      "2026-11-01T05:30Z至2026-11-01T05:30Z适合签约吗？",
      "ZERO_LENGTH_TIME_INTERVAL",
    ],
    [
      "2026-11-01T06:30Z至2026-11-01T05:30Z适合签约吗？",
      "REVERSED_TIME_INTERVAL",
    ],
    [
      "区间一是2026-11-01T05:30Z至2026-11-01T06:30Z；区间二是2026-11-01T06:00Z至2026-11-01T07:00Z，哪个更适合签约？",
      "OVERLAPPING_TIME_INTERVAL",
    ],
    [
      "2026-11-01T05:30Z以后哪个时间更适合签约？",
      "OPEN_ENDED_TIME_INTERVAL",
    ],
    [
      "2026-11-01T05:30Z至2026-11-01T06:30Z，持续90分钟，适合签约吗？",
      "TIME_INTERVAL_DURATION_MISMATCH",
    ],
    [
      "2027-03-14T01:30-05:00[America/New_York]至2027-03-14T03:30-04:00[America/New_York]，持续2小时，适合行动吗？",
      "TIME_INTERVAL_DURATION_MISMATCH",
    ],
  ] as const)
    assert.equal(temporalErrorCode(text), code, text);
});

test("重复日程依次要求绝对范围、IANA 时区与逐次 evidence", () => {
  for (const [text, code] of [
    ["每天09:00适合联系客户吗？", "RECURRENCE_RANGE_REQUIRED"],
    ["每隔两周联系一次客户是否合适？", "RECURRENCE_RANGE_REQUIRED"],
    [
      "2026-11-01T00:00Z至2026-11-08T00:00Z，每天09:00适合联系客户吗？",
      "RECURRENCE_TIME_ZONE_REQUIRED",
    ],
    [
      "出生时区是Asia/Shanghai。2026-11-01T00:00Z至2026-11-08T00:00Z，每天09:00适合联系客户吗？",
      "RECURRENCE_TIME_ZONE_REQUIRED",
    ],
    [
      "2026-11-01T00:00-04:00[America/New_York]至2026-11-08T00:00-05:00[America/New_York]，每天09:00适合联系客户吗？",
      "UNSUPPORTED_RECURRENCE_GRANULARITY",
    ],
    [
      "2026-11-01T04:00Z至2026-11-08T05:00Z，按America/New_York当地每天09:00适合联系客户吗？",
      "UNSUPPORTED_RECURRENCE_GRANULARITY",
    ],
  ] as const)
    assert.equal(temporalErrorCode(text), code, text);

  assert.doesNotThrow(() =>
    validateReportTemporalText(
      "系统每天09:00运行，仅作计划说明。",
      "section career claim 0 text",
      [2026, 2027],
      2026,
    ),
  );
});

test("时间模块公开的日期与相对年份辅助函数保持确定性", () => {
  assert.equal(validIsoDate("2024-02-29"), true);
  assert.equal(validIsoDate("2027-02-29"), false);
  assert.equal(validIsoDate("2026/09/25"), false);
  assert.deepEqual(
    referencedRelativeYears("今年与明年，再看今年", 2026),
    [2026, 2027],
  );
  assert.deepEqual(referencedRelativeYears("明年", null), []);
});

const proseContext = {
  role: "prose" as const,
  asOfDate: "2026-09-25",
  birth: { calendar: "solar" as const, date: "2000-08-16", leapMonth: false },
};
function contextualCode(text: string, context = proseContext) {
  try {
    validateReportTemporalText(text, "claim.text", [2025, 2026, 2027], 2026, context);
    return null;
  } catch (error) {
    if (error instanceof InputError) return error.code;
    throw error;
  }
}

test("限制性说明只豁免本句，不放行逗号、句号或转折后的预测", () => {
  for (const text of [
    "目前不能判断近期是否会升职。",
    "无法预测下个月是否升职。",
    "不能确定什么时候会升职，不能预测近期的结果。",
  ]) assert.equal(contextualCode(text), null, text);
  for (const text of [
    "近期会升职。",
    "不能保证，但近期一定升职。",
    "不能判断近期是否会升职，但是下个月会升职。",
    "不能判断近期是否会升职。近期会有机会。",
    "不能判断近期是否会升职，近期会有机会。",
    "不能判断近期是否会升职却认为下个月会升职。",
  ]) assert.notEqual(contextualCode(text), null, text);
  assert.equal(temporalErrorCode("目前不能判断近期是否会升职。"), "AMBIGUOUS_TIME_HORIZON");
  assert.equal(contextualCode("无法预测2027-02-29是否升职。"), "INVALID_NUMERIC_DATE");
  assert.equal(contextualCode("无法预测2027年2月30日是否升职。"), "INVALID_NUMERIC_DATE");
});

test("出生日期按真实输入匹配，农历需显式历法与闰月", () => {
  for (const text of ["出生日期是2000年8月16日。", "出生日期为公历2000-08-16。"]) {
    assert.equal(contextualCode(text), null, text);
  }
  assert.equal(contextualCode("出生日期是2000年8月17日。"), "FACT_MISMATCH");
  assert.equal(contextualCode("出生日期是农历2000年8月16日。"), "FACT_MISMATCH");
  assert.notEqual(contextualCode("出生日期是2000年8月16日，下个月适合升职。"), null);
  const lunar = { ...proseContext, birth: { calendar: "lunar" as const, date: "2023-02-30", leapMonth: true } };
  assert.doesNotThrow(() => validateReportTemporalText("出生日期是农历2023年闰2月30日。", "claim.text", [2026], 2026, lunar));
  assert.throws(() => validateReportTemporalText("出生日期是农历2023年2月30日。", "claim.text", [2026], 2026, lunar), (e: unknown) => e instanceof InputError && e.code === "FACT_MISMATCH");
});

test("历史转述须明确归属和未核验，过去整月与当前月份分开", () => {
  for (const text of [
    "你在2025年3月换过工作，这是用户提供的经历，尚未独立核验。",
    "用户称2026年8月曾换工作，未经独立核验。",
    "用户自述2026-09-24已换工作，未经独立核验。",
  ]) assert.equal(contextualCode(text), null, text);
  for (const text of [
    "用户称2026年9月曾换工作，未经独立核验。",
    "用户称2027年3月将会升职，未经独立核验。",
    "用户称2025年3月换过工作，因此下个月会升职，未经独立核验。",
    "你在2025年3月换过工作。",
    "用户称2025年3月已换工作，未经独立核验。下个月会升职。",
  ]) assert.notEqual(contextualCode(text), null, text);
  assert.equal(contextualCode("用户称2025年2月30日已换工作，未经独立核验。"), "INVALID_NUMERIC_DATE");
});

test("资料来源角色不依赖标签且不允许来源字段夹带预测", () => {
  for (const label of ["bazi timingChain.realityBasis.source", "timingChain.realityBasis.source", "arbitrary diagnostic label"]) {
    assert.doesNotThrow(() => validateReportTemporalText("用户2023年3月记录", label, [2026], 2026, { ...proseContext, role: "reality-source" }));
    assert.throws(() => validateReportTemporalText("用户2023年3月记录", label, [2026], 2026));
    assert.throws(() => validateReportTemporalText("2023年3月适合升职", label, [2026], 2026, { ...proseContext, role: "reality-source" }));
  }
});


test("否定与用户归属不能吞掉连接词引出的肯定预测，农历不绕过非法公历日期", () => {
  for (const text of [
    "不能判断近期是否升职且下个月适合跳槽。",
    "不能判断近期是否升职而下个月适合跳槽。",
    "不能判断近期是否升职：下个月适合跳槽。",
    "不能判断近期是否升职 下个月会升职。",
    "用户称2025年3月已换工作，下个月升职，未经独立核验。",
    "用户称2025年3月已换工作且下个月升职，未经独立核验。",
    "用户称2025年3月已换工作、短期内升职，未经独立核验。",
    "用户称2025年3月已换工作/过段时间升职，未经独立核验。",
    "用户称2025年3月已换工作🙂2027-03-15升职，未经独立核验。",
  ]) assert.notEqual(contextualCode(text), null, text);
  assert.throws(() => validateReportTemporalText(
    "无法预测出生日期2027年2月30日是否升职。", "claim.text", [2026, 2027], 2026,
    { ...proseContext, birth: { calendar: "lunar", date: "2023-02-30", leapMonth: true } },
  ), (e: unknown) => e instanceof InputError && e.code === "INVALID_NUMERIC_DATE");
});


test("农历完整出生日期的中文与数字写法等价，其他数字日期仍按公历验证", () => {
  const context = { ...proseContext, birth: { calendar: "lunar" as const, date: "2024-02-30", leapMonth: false } };
  for (const text of ["出生日期为农历2024-02-30。", "出生日期为农历2024年02月30日。"]) {
    assert.doesNotThrow(() => validateReportTemporalText(text, "claim.text", [2026], 2026, context));
  }
  assert.throws(() => validateReportTemporalText("出生日期为农历2024-02-30。2027-02-30不适合行动。", "claim.text", [2026], 2026, context),
    (e: unknown) => e instanceof InputError && e.code === "INVALID_NUMERIC_DATE");
  assert.notEqual(contextualCode("用户称2025年3月已换工作下个月升职，未经独立核验。"), null);
});


test("真实宿主回归：出生资料允许逗号接历法，邻接预测与相反历法仍拒绝", () => {
  assert.equal(contextualCode("不能据此承诺事件或安排月份。出生日期为2000-08-16，历法为公历。"), null);
  assert.equal(contextualCode("出生日期为2000-08-16，无法预测下个月是否升职。"), null);
  assert.notEqual(contextualCode("出生日期为2000-08-16，无法预测下个月是否升职，下个月会升职。"), null);
  assert.equal(contextualCode("出生日期为2000-08-16，历法为农历。"), "FACT_MISMATCH");
  assert.notEqual(contextualCode("出生日期为2000-08-16，历法为公历，下个月会升职。"), null);
  assert.doesNotThrow(() => validateReportTemporalText(
    "出生日期为农历2024-02-30，历法为农历。", "claim.text", [2026], 2026,
    { ...proseContext, birth: { calendar: "lunar", date: "2024-02-30", leapMonth: false } },
  ));
});
