import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { contextFor } from "../src/evidence.js";
import { checkAnswer } from "../src/answer-check.js";
import { findUnsafeReportClaim } from "../src/report-safety.js";

const birth = JSON.parse(readFileSync("examples/birth.json", "utf8"));
const e = contextFor(birth, [2026, 2027]);
const code = (c: string) => ({ code: c });

test("快速档答复通过条件性年度表达，拒绝高风险断言、细分时点与未决升级", () => {
  assert.equal(
    checkAnswer("2026年事业主题责任加重，是否升职取决于授权与考核，这是条件性解释。", e).status,
    "valid",
  );
  assert.throws(() => checkAnswer("2026年一定会升职加薪。", e), code("UNSAFE_REPORT_CLAIM"));
  assert.throws(() => checkAnswer("2026年3月适合跳槽。", e), code("UNSUPPORTED_TIME_GRANULARITY"));
  assert.throws(() => checkAnswer("用神已经确定为水。", e), code("UNRESOLVED_PREMISE_CLAIM"));
  // 格局只能确认候选入口；“财格成立/已成格”属未决升级，否定与条件句放行。
  assert.throws(() => checkAnswer("你的八字是偏财格，财格成立。", e), code("UNRESOLVED_PREMISE_CLAIM"));
  assert.throws(() => checkAnswer("七杀格已成格。", e), code("UNRESOLVED_PREMISE_CLAIM"));
  for (const ok of ["只能确认财格候选入口，不确认成格。", "显干财印不相邻，也不证明财格成立。", "财格是否成立尚未裁定。"])
    assert.equal(checkAnswer(ok, e).status, "valid", ok);
  assert.throws(() => checkAnswer("  ", e), code("INVALID_ANSWER"));
});

test("相对年份必须提供冻结日期，且解析后仍须落在 evidence 内", () => {
  assert.throws(() => checkAnswer("明年事业需要核对条件。", e));
  assert.equal(checkAnswer("明年事业需要核对条件。", e, "2026-09-28").status, "valid");
  assert.throws(() => checkAnswer("明年事业需要核对条件。", e, "2027-09-28"));
  assert.throws(() => checkAnswer("今年如何？", e, "2026-02-30"), code("INVALID_ARGUMENT"));
});

test("确定性事业与人生事件断言被拦截，否定与条件表达放行", () => {
  for (const text of ["注定结婚", "明年必然晋升", "肯定会发财", "升职已成定局"])
    assert.equal(findUnsafeReportClaim(text)?.category, "guaranteed-event", text);
  for (const text of [
    "这一年有一定的加薪空间",
    "存在一定程度升职机会",
    "一定要留意被裁风险",
    "化权不代表一定会升职",
    "夫妻大限不等同于必然结婚",
    "也不意味着后者一定结婚早",
    "不给排名、概率、保证升职或行动窗口",
  ])
    assert.equal(findUnsafeReportClaim(text), null, text);
  assert.equal(findUnsafeReportClaim("不作他想地说注定离婚")?.category, "inevitable-relationship");
  assert.equal(findUnsafeReportClaim("你注定要发财")?.category, "guaranteed-event");
  assert.equal(findUnsafeReportClaim("你一定能当领导")?.category, "guaranteed-event");
  assert.equal(findUnsafeReportClaim("有当领导的可能，但取决于授权"), null);
  assert.equal(findUnsafeReportClaim("他必然要破产")?.category, "guaranteed-event");
  assert.equal(findUnsafeReportClaim("这很不给力，注定结婚")?.category, "guaranteed-event");
});

test("缺少冻结日期时相对年份提示 --as-of；单候选报告宫位核对，多候选明示未核对", () => {
  assert.throws(() => checkAnswer("明年事业需要核对条件。", e), (err: Error) =>
    (err as Error & { code: string }).code === "AMBIGUOUS_RELATIVE_TIME" && err.message.includes("--as-of"));
  assert.equal(checkAnswer("2026年事业需要核对条件。", e).palaceScope, "checked");
  const multi = contextFor({ ...birth, uncertaintyMinutes: 120 }, [2026]);
  if (multi.candidateIds.length > 1)
    assert.equal(checkAnswer("2026年事业需要核对条件。", multi).palaceScope, "skipped-multi-candidate");
});

test("answer-check CLI 从 stdin 读取文本并沿用错误退出码契约", () => {
  const run = (text: string) =>
    spawnSync(
      process.execPath,
      ["--import", "tsx", "src/cli.ts", "answer-check", "--input", "examples/birth.json", "--years", "2026", "--text", "-"],
      { input: text, encoding: "utf8" },
    );
  const ok = run("2026年事业主题需要核对授权与支持。");
  assert.equal(ok.status, 0);
  assert.equal(JSON.parse(ok.stdout).evidenceId, contextFor(birth, [2026]).evidenceId);
  const both = spawnSync(
    process.execPath,
    ["--import", "tsx", "src/cli.ts", "answer-check", "--input", "-", "--text", "-"],
    { input: "{}", encoding: "utf8" },
  );
  assert.equal(JSON.parse(both.stderr).code, "INVALID_ARGUMENT");
  const bad = run("2026年必然升职。");
  assert.equal(bad.status, 1);
  assert.equal(JSON.parse(bad.stderr).code, "UNSAFE_REPORT_CLAIM");
});
