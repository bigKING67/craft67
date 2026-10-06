import { test } from "node:test";
import assert from "node:assert/strict";
import { prepareBenchmark, scoreBenchmark } from "../src/benchmark.js";
const dataset = {
  questions: Array.from({ length: 30 }, (_, i) => ({
    id: `q${i}`,
    case_id: `c${Math.floor(i / 3)}`,
    birth_info: { raw: "synthetic", answer: "SECRET" },
    question: "合成问题",
    options: [
      { letter: "A", text: "甲" },
      { letter: "B", text: "乙" },
    ],
    answer: "A",
    category: "合成",
    explanation: "SECRET",
  })),
};
test("同命主不跨分区，答案与非白名单字段不进入输入", () => {
  const { prompts, answerKey } = prepareBenchmark(dataset);
  for (const x of prompts.items)
    assert.equal(
      new Set(
        prompts.items.filter((y) => y.caseId === x.caseId).map((y) => y.split),
      ).size,
      1,
    );
  assert.ok(!JSON.stringify(prompts).includes("SECRET"));
  assert.ok(!prompts.items.some((x) => "answer" in x.input));
  assert.equal(answerKey.items.length, 30);
  assert.equal(new Set(prompts.items.map((x) => x.split)).size, 2);
});
test("未答题纳入分母，datasetHash、未知与重复 ID 拒绝", () => {
  const { answerKey } = prepareBenchmark(dataset);
  const p = {
    datasetHash: answerKey.datasetHash,
    items: [{ id: "q0", answer: "A" }],
  };
  const score = scoreBenchmark(answerKey, p);
  assert.equal(
    score.summaries.reduce((n, s) => n + s.correct, 0),
    1,
  );
  assert.equal(
    score.summaries.reduce((n, s) => n + s.total, 0),
    30,
  );
  assert.throws(() => scoreBenchmark(answerKey, { ...p, datasetHash: "bad" }));
  assert.throws(() =>
    scoreBenchmark(answerKey, { ...p, items: [...p.items, ...p.items] }),
  );
  assert.throws(() =>
    scoreBenchmark(answerKey, {
      ...p,
      items: [{ id: "unknown", answer: "A" }],
    }),
  );
});

test("外部命盘标记来源且不混淆主辅星，不同评测配置指纹不同", () => {
  const astro = [
    {
      case_id: "c0",
      api_response: {
        success: true,
        data: {
          data: {
            chineseDate: "甲子 丙寅 戊辰 庚申",
            time: "申时",
            fiveElementsClass: "金四局",
            palaces: Array.from({ length: 12 }, (_, i) => ({
              name: `宫${i}`,
              heavenlyStem: "甲",
              earthlyBranch: "子",
              majorStars: [{ name: "紫微", brightness: "庙" }],
              minorStars: [{ name: "文昌" }],
            })),
          },
        },
      },
    },
  ];
  const a = prepareBenchmark(dataset),
    b = prepareBenchmark(dataset, "whoami-v1", astro);
  assert.notEqual(a.prompts.datasetHash, b.prompts.datasetHash);
  const external = b.prompts.items[0]!.input.externalChart as any;
  assert.match(external.provenance, /external-chart/);
  assert.deepEqual(
    external.palaces[0].stars.map((s: any) => s.kind),
    ["majorStars", "minorStars"],
  );
  assert.throws(() =>
    scoreBenchmark(b.answerKey, {
      datasetHash: b.answerKey.datasetHash,
      items: [{ id: "q0", answer: "Z" }],
    }),
  );
  const score = scoreBenchmark(b.answerKey, {
    datasetHash: b.answerKey.datasetHash,
    items: [{ id: "q0", answer: null }],
  });
  assert.equal(
    score.summaries.reduce((n, s) => n + s.answered, 0),
    0,
  );
});
