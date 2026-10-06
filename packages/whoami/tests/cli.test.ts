import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const input = JSON.parse(readFileSync("examples/birth.json", "utf8"));
function cli(args: string[], value: unknown = input) {
  return spawnSync(
    process.execPath,
    ["--import", "tsx", "src/cli.ts", ...args],
    { input: JSON.stringify(value), encoding: "utf8" },
  );
}
test("CLI stdin 纯 JSON / stderr / 退出码契约", () => {
  const r = cli(["chart", "--input", "-", "--years", "2026"]);
  assert.equal(r.status, 0);
  assert.equal(r.stderr, "");
  assert.equal(JSON.parse(r.stdout).schema, "whoami.chart.v1");
  const missing = cli(["chart", "--input", "-"], { ...input, time: null });
  assert.equal(missing.status, 2);
  assert.equal(JSON.parse(missing.stdout).status, "needs-input");
  const invalid = cli(["chart", "--input", "-"], {
    ...input,
    gender: "invalid",
  });
  assert.equal(invalid.status, 1);
  assert.equal(invalid.stdout, "");
  assert.equal(JSON.parse(invalid.stderr).code, "INVALID_INPUT");
});
test("context 的确定性计算错误可作为验收产物重放", () => {
  const gap = cli(
    ["context", "--input", "-", "--years", "2026"],
    {
      ...input,
      date: "2024-03-10",
      time: "02:30",
      place: "纽约（合成）",
      longitude: -74.006,
      timeZone: "America/New_York",
      timeBasis: "civil",
      dstDisambiguation: "later",
    },
  );
  assert.equal(gap.status, 1);
  assert.equal(gap.stdout, "");
  assert.deepEqual(JSON.parse(gap.stderr), {
    schema: "whoami.error.v1",
    status: "error",
    command: "context",
    years: [2026],
    code: "NONEXISTENT_LOCAL_TIME",
    message: "夏令时跳变导致该钟表时间不存在，请更正出生资料",
  });
  for (const years of ["2026.5", "garbage", "Infinity"]) {
    const invalidYears = cli(
      ["context", "--input", "-", "--years", years],
      {
        ...input,
        date: "2024-03-10",
        time: "02:30",
        place: "纽约（合成）",
        longitude: -74.006,
        timeZone: "America/New_York",
        timeBasis: "civil",
        dstDisambiguation: "later",
      },
    );
    assert.equal(invalidYears.status, 1);
    assert.equal(invalidYears.stdout, "");
    assert.deepEqual(JSON.parse(invalidYears.stderr), {
      status: "error",
      code: "INVALID_YEARS",
      message: "流年须为 1901–2099 整数，最多 20 年",
    });
  }
});
test("CLI 三种报告模板与未知参数拒绝", () => {
  for (const mode of ["combined", "bazi", "ziwei"]) {
    const r = cli([
      "report-template",
      "--input",
      "-",
      "--mode",
      mode,
      "--years",
      "2026",
    ]);
    assert.equal(r.status, 0);
    const report = JSON.parse(r.stdout);
    assert.equal(report.schema, "whoami.report.v6");
    assert.deepEqual(report.timeReference, { asOfDate: "", timeZone: "" });
    assert.equal(report.mode, mode);
    assert.equal(report.baziReasoning.length > 0, mode !== "ziwei");
    assert.equal(report.ziweiReasoning.length > 0, mode !== "bazi");
    if (mode !== "ziwei") {
      const timing = report.baziReasoning.find(
        (item: any) => item.topic === "bazi-timing",
      );
      assert.deepEqual(timing.years, [2026]);
      assert.deepEqual(timing.timingChain.annualReviews, [
        {
          year: 2026,
          pillar: "丙午",
          boundary: "lichun",
          natalRefs: [],
          review: "",
        },
      ]);
    }
  }
  assert.equal(cli(["chart", "--input", "-", "--yaers", "2026"]).status, 1);
  assert.equal(cli(["chart", "--input", "-", "--input", "-"]).status, 1);
});
test("CLI 评测输出不覆盖已有文件", () => {
  const dir = mkdtempSync(join(tmpdir(), "whoami-cli-test-"));
  try {
    const d = join(dir, "dataset.json"),
      out = join(dir, "out");
    writeFileSync(
      d,
      JSON.stringify({
        questions: [
          {
            id: "q1",
            case_id: "c1",
            birth_info: { raw: "synthetic" },
            question: "Q",
            options: [
              { letter: "A", text: "x" },
              { letter: "B", text: "y" },
            ],
            answer: "A",
            category: "test",
          },
        ],
      }),
    );
    const args = ["benchmark-prepare", "--dataset", d, "--output-dir", out];
    assert.equal(cli(args).status, 0);
    const before = readFileSync(join(out, "answer-key.json"), "utf8");
    assert.equal(cli(args).status, 1);
    assert.equal(readFileSync(join(out, "answer-key.json"), "utf8"), before);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("规则复核从 stdin 输出有证据绑定的阻断理由，不需报告文件",()=>{
  const birth=JSON.parse(readFileSync("examples/acceptance/officer-branch/birth.json","utf8"));
  const r=cli(["rule-review","--input","-","--years","2026"],birth);
  const e=JSON.parse(cli(["context","--input","-","--years","2026"],birth).stdout);
  assert.equal(r.status,0);assert.equal(r.stderr,"");
  assert(r.stdout.includes(e.chartId));assert(r.stdout.includes(e.evidenceId));
  assert(r.stdout.includes("财旺生官分支：blocked"));
  assert(r.stdout.includes("反例为时干己（伤官）"));
  assert(r.stdout.includes(`${e.candidateIds[0]}.bazi.wealthReview`));
});
test("规则复核保留出生边界每个候选及不同分支状态",()=>{
  const birth=JSON.parse(readFileSync("examples/acceptance/boundary/birth.json","utf8"));
  const r=cli(["rule-review","--input","-","--years","2026"],birth);
  const e=JSON.parse(cli(["context","--input","-","--years","2026"],birth).stdout);
  assert.equal(r.status,0);assert.equal(e.candidateIds.length,2);
  for(const id of e.candidateIds) assert(r.stdout.includes(`## 候选 ${id}`));
  assert(r.stdout.includes("财旺生官分支：not-applicable"));
  assert(r.stdout.includes("财旺生官分支：pending"));
  assert(r.stdout.includes("ambiguous"));
});
test("规则复核入口外不伪造通过，财印风险保留全部配对",()=>{
  const outside=JSON.parse(readFileSync("examples/acceptance/ordinary/birth.json","utf8"));
  const r=cli(["rule-review","--input","-","--years","2026"],outside);
  assert.equal(r.status,0);assert(r.stdout.includes("财格入口：outside-scope"));
  assert(r.stdout.includes("财印位置：not-applicable"));
  const risk=cli(["rule-review","--input","-","--years","2026"]);
  assert.equal(risk.status,0);
  assert(risk.stdout.includes("年干庚（偏财）与月干甲（偏印）：相邻"));
  assert(risk.stdout.includes("时干庚（偏财）与月干甲（偏印）：隔日柱"));
});
test("规则复核缺时辰退出2且无解读，参数错误走stderr",()=>{
  const missing=cli(["rule-review","--input","-"],{...input,time:null});
  assert.equal(missing.status,2);assert.equal(missing.stderr,"");
  const body=JSON.parse(missing.stdout);assert.equal(body.status,"needs-input");
  assert.deepEqual(body.candidates,[]);
  const bad=cli(["rule-review","--input","-","--mode","combined"]);
  assert.equal(bad.status,1);assert.equal(bad.stdout,"");
  assert.equal(JSON.parse(bad.stderr).code,"INVALID_ARGUMENT");
});

test('compare支持单侧stdin并拒绝双侧stdin，不需要report文件',()=>{
 const r=cli(['compare','--before','examples/birth.json','--after','-','--years','2026']);
 assert.equal(r.status,0);assert.equal(r.stderr,'');
 const body=JSON.parse(r.stdout);assert.equal(body.status,'compared');assert.deepEqual(body.changedFacts,[]);
 const invalid=cli(['compare','--before','-','--after','-']);
 assert.equal(invalid.status,1);assert.equal(invalid.stdout,'');
 assert.equal(JSON.parse(invalid.stderr).code,'INVALID_ARGUMENT');
});
test('compare缺时辰或未选多候选退出2，不伪装比较完成',()=>{
 const unknown=cli(['compare','--before','examples/birth.json','--after','-','--years','2026'],{...input,time:null});
 assert.equal(unknown.status,2);assert.equal(JSON.parse(unknown.stdout).status,'needs-input');
 const boundary=cli(['compare','--before','examples/acceptance/boundary/birth.json','--after','-','--years','2026']);
 assert.equal(boundary.status,2);assert.equal(JSON.parse(boundary.stdout).status,'needs-selection');
});
