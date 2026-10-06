import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { contextFor } from "../src/evidence.js";
import { checkAnswer } from "../src/answer-check.js";

const birth = JSON.parse(readFileSync("examples/birth.json", "utf8"));
const e = contextFor(birth, [2026]);
const c = e.candidateIds[0]!;
const code = (x: string) => ({ code: x });

const answer = [
  "日主丙火生于申月，申中本气庚金透于年干和时干。",
  "按月令取法，当前只能确认财格候选入口，是否成格仍须看身强弱。",
  "2026年流年丙午与日柱伏吟，事业上更像责任加重、需要核对授权的一年，是否升职取决于现实条件。",
  "本次地点与时区来源未核验。",
].join("");
const audit = () => ({
  schema: "whoami.answer-audit.v1",
  evidenceId: e.evidenceId,
  claims: [
    { text: "日主丙火生于申月，申中本气庚金透于年干和时干。", kinds: ["fact"], stance: "fact-restatement", factRefs: [`${c}.bazi.dayMaster`, `${c}.bazi.monthExposure`] },
    { text: "按月令取法，当前只能确认财格候选入口，是否成格仍须看身强弱。", kinds: ["pattern"], stance: "unresolved", factRefs: [`${c}.bazi.wealthReview`] },
    { text: "2026年流年丙午与日柱伏吟，事业上更像责任加重、需要核对授权的一年，是否升职取决于现实条件。", kinds: ["timing", "event"], stance: "conditional", factRefs: [`${c}.bazi.cycleRelations`] },
  ],
});

test("断言清单逐句覆盖、类型与依据一致时通过，未提供时明示 not-provided", () => {
  const r = checkAnswer(answer, e, undefined, audit());
  // 按逗号切分后，含触发词的分句为：两个格局分句、一个时间分句、一个事件分句。
  assert.deepEqual(r.audit, { claims: 3, unitsCovered: 4 });
  assert.equal(checkAnswer(answer, e).audit, "not-provided");
});

test("含判断的句子漏登记、或覆盖断言漏声明类型时拒绝", () => {
  const missing = audit();
  missing.claims.pop();
  assert.throws(() => checkAnswer(answer, e, undefined, missing), code("AUDIT_COVERAGE_GAP"));
  const wrongKind = audit();
  wrongKind.claims[2]!.kinds = ["event"];
  assert.throws(() => checkAnswer(answer, e, undefined, wrongKind), code("AUDIT_KIND_MISMATCH"));
});

test("判断不能登记为事实复述；类型须引用对应命盘事实", () => {
  const asFact = audit();
  asFact.claims[1]!.stance = "fact-restatement";
  assert.throws(() => checkAnswer(answer, e, undefined, asFact), code("AUDIT_KIND_MISMATCH"));
  const noPatternFact = audit();
  noPatternFact.claims[1]!.factRefs = [`${c}.bazi.cycles`];
  assert.throws(() => checkAnswer(answer, e, undefined, noPatternFact), code("AUDIT_KIND_MISMATCH"));
});

test("原句须逐字存在、事实 ID 须真实、evidenceId 须一致", () => {
  const rewritten = audit();
  rewritten.claims[1]!.text = "财格已经成立。";
  assert.throws(() => checkAnswer(answer, e, undefined, rewritten), code("INVALID_AUDIT"));
  const fakeRef = audit();
  fakeRef.claims[0]!.factRefs = [`${c}.bazi.notAFact`];
  assert.throws(() => checkAnswer(answer, e, undefined, fakeRef), code("INVALID_AUDIT"));
  const stale = { ...audit(), evidenceId: "stale" };
  assert.throws(() => checkAnswer(answer, e, undefined, stale), code("AUDIT_STALE"));
  assert.throws(() => checkAnswer(answer, e, undefined, { ...audit(), claims: [] }), code("INVALID_AUDIT"));
});

test("只登记片段不能覆盖整句；可按整段登记；小标题与纯时间事实不强制作判断", () => {
  const fragment = { ...audit(), claims: [...audit().claims.slice(0, 2), { text: "2026", kinds: ["timing", "event"], stance: "conditional", factRefs: [`${c}.bazi.cycleRelations`] }] };
  assert.throws(() => checkAnswer(answer, e, undefined, fragment), code("AUDIT_COVERAGE_GAP"));
  const paragraph = { ...audit(), claims: [{ text: answer.slice(answer.indexOf("按月令"), answer.indexOf("本次地点")), kinds: ["pattern", "timing", "event"], stance: "conditional", factRefs: [`${c}.bazi.wealthReview`, `${c}.bazi.cycleRelations`] }] };
  assert.equal((checkAnswer(answer, e, undefined, paragraph).audit as { claims: number }).claims, 1);
  const withHeading = "一、2026年财运\n" + "2026年流年丙午，全年处在辛巳大运。";
  const factAudit = { schema: "whoami.answer-audit.v1", evidenceId: e.evidenceId, claims: [
    { text: "2026年流年丙午，全年处在辛巳大运。", kinds: ["fact", "timing"], stance: "fact-restatement", factRefs: [`${c}.bazi.cycles`] },
  ] };
  assert.equal(checkAnswer(withHeading, e, undefined, factAudit).status, "valid");
  assert.equal(checkAnswer("你的性格偏外向，做事有主见，这是条件性的描述。", e, undefined, { ...factAudit, claims: [{ text: "你的性格偏外向", kinds: ["fact"], stance: "fact-restatement", factRefs: [`${c}.bazi.dayMaster`] }] }).status, "valid");
});

test("登记为条件性但句中没有任何限定语时拒绝；一次列出全部问题", () => {
  const blunt = "2026年财运会明显变好。你会有一笔意外的进账。";
  const bluntAudit = { schema: "whoami.answer-audit.v1", evidenceId: e.evidenceId, claims: [
    { text: "2026年财运会明显变好。", kinds: ["timing", "event"], stance: "conditional", factRefs: [`${c}.bazi.cycleRelations`] },
  ] };
  assert.throws(() => checkAnswer(blunt, e, undefined, bluntAudit), (err: Error & { code?: string }) =>
    err.code === "AUDIT_STANCE_MISMATCH" && err.message.includes("2 处问题") && err.message.includes("AUDIT_COVERAGE_GAP"));
});

test("清单格式错误报 INVALID_AUDIT；CRLF 原文可匹配；内嵌 answer 须与受检答复一致", () => {
  assert.throws(() => checkAnswer(answer, e, undefined, "abc"), code("INVALID_AUDIT"));
  assert.throws(() => checkAnswer(answer, e, undefined, { ...audit(), claims: [1] }), code("INVALID_AUDIT"));
  const crlf = answer.replace("。2026", "。\r\n2026");
  const crlfAudit = audit();
  crlfAudit.claims[2]!.text = "\r\n" + crlfAudit.claims[2]!.text;
  assert.equal(checkAnswer(crlf, e, undefined, crlfAudit).status, "valid");
  assert.throws(() => checkAnswer(answer, e, undefined, { ...audit(), answer: "别的答复" }), code("INVALID_AUDIT"));
});

test("CLI：清单内嵌 answer 时用 --audit - 从 stdin 一次传入；stdin 只能给一项", () => {
  const run = (args: string[], input: string) =>
    spawnSync(process.execPath, ["--import", "tsx", "src/cli.ts", "answer-check", "--input", "examples/birth.json", "--years", "2026", ...args], { input, encoding: "utf8" });
  const ok = run(["--audit", "-"], JSON.stringify({ ...audit(), answer }));
  assert.equal(ok.status, 0, ok.stderr);
  assert.deepEqual(JSON.parse(ok.stdout).audit, { claims: 3, unitsCovered: 4 });
  const both = run(["--audit", "-", "--text", "-"], "{}");
  assert.equal(JSON.parse(both.stderr).code, "INVALID_ARGUMENT");
  const none = run([], "");
  assert.equal(JSON.parse(none.stderr).code, "MISSING_ARGUMENT");
});

test("列出会改变判断的现实条件（含“是否”）不被当作绝对断言", () => {
  const list = "- 你现在的收入结构、是否在做投资或合伙、明年是否有工作变动。";
  const listAudit = { schema: "whoami.answer-audit.v1", evidenceId: e.evidenceId, claims: [
    { text: list, kinds: ["event", "timing"], stance: "unresolved", factRefs: [`${c}.bazi.cycleRelations`] },
  ] };
  // “明年”按 2025-09-28 冻结解析为 2026，落在 evidence 内。
  assert.equal(checkAnswer(list, e, "2025-09-28", listAudit).status, "valid");
});
