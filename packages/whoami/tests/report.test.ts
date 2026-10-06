import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { contextFor } from "../src/evidence.js";
import {
  reportTemplate,
  validateReport,
  renderReport,
  SECTION_IDS,
} from "../src/report.js";
import { findUnsafeReportClaim } from "../src/report-safety.js";
import { InputError } from "../src/input.js";
const input = {
  calendar: "solar",
  date: "2000-08-16",
  time: "04:00",
  place: "合成",
  longitude: 120,
  timeZone: "Asia/Shanghai",
  gender: "female",
};
const e = contextFor(input, [2026]);
function valid(context = e) {
  const e = context;
  const r = reportTemplate(e) as any;
  r.timeReference = {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  };
  const b = e.facts.find((f) => f.system === "bazi")!,
    z = e.facts.find((f) => f.system === "ziwei")!;
  const rule = e.rules.find((r) => r.factRefs.includes(b.id))!;
  r.baziReasoning.forEach((a: any) => {
    const factSuffixes = {
      strength: [".bazi.month", ".bazi.rootDetails"],
      pattern: [".bazi.monthExposure"],
      climate: [".bazi.month", ".bazi.dayMaster"],
      balance: [".bazi.rootDetails"],
      selection: [".bazi.monthExposure"],
      "bazi-timing": [".bazi.cycles", ".bazi.relations"],
    }[a.topic] as string[];
    const ruleSuffix = {
      strength: ".R-bazi-structure",
      pattern: ".R-bazi-month-exposure",
      climate: ".R-bazi-structure",
      balance: ".R-bazi-structure",
      selection: ".R-bazi-structure",
      "bazi-timing": ".R-bazi-timing",
    }[a.topic] as string;
    Object.assign(a, {
      conclusion: `${a.topic} 结构测试未裁定`,
      supportRefs: factSuffixes.map((suffix) =>
        e.facts.find((fact) =>
          fact.candidate === a.candidate && fact.id.endsWith(suffix)
        )!.id
      ),
      counterRefs: [],
      counterReview: `${a.topic} 未检验语义反证，不代表不存在`,
      conditions: `${a.topic} 仅结构测试`,
      alternatives: `${a.topic} 需另做传统依据核验`,
      ruleRefs: [e.rules.find((item) =>
        item.candidate === a.candidate && item.id.endsWith(ruleSuffix)
      )!.id],
    });
    if (a.topic === "bazi-timing") {
      const cycleRef = a.supportRefs.find((id: string) =>
        id.endsWith(".bazi.cycles")
      );
      const natalRef = a.supportRefs.find((id: string) =>
        id.endsWith(".bazi.relations")
      );
      const cycles = e.facts.find((fact) => fact.id === cycleRef)!.value as {
        yearly: { year: number; pillar: string; boundary: "lichun" }[];
      };
      a.timingChain = {
        target: "general",
        cycleRefs: [cycleRef],
        annualReviews: a.years.map((year: number) => {
          const annual = cycles.yearly.find((item) => item.year === year)!;
          return {
            ...annual,
            natalRefs: [natalRef],
            review: `${year} ${annual.pillar} 只验证本命与运年作用链结构，现实结果未裁定。`,
          };
        }),
        crossLayerReview: "已区分本命结构、大运阶段与立春流年，未把干支关系直接换成现实事件。",
        missingLinks: ["缺少现实触发资料"],
        realityBasis: {
          status: "not-provided",
          summary: "合成测试未提供现实经历或目标。",
          source: null,
        },
        withdrawalConditions: "出生资料、起运边界或现实条件变化时撤回并重算。",
      };
    }
  });
  const reasoningRefs = r.baziReasoning
    .filter((a: any) => a.topic !== "bazi-timing")
    .map((a: any) => ({
      candidate: a.candidate,
      topic: a.topic,
    }));
  r.ziweiReasoning.forEach((a: any) => {
    const base = e.facts.find((fact) =>
      fact.candidate === a.candidate && fact.id.endsWith(".ziwei.base")
    )!;
    const palaceName = {
      "ziwei-structure": "命宫",
      "ziwei-career": "官禄",
      "ziwei-wealth": "财帛",
      "ziwei-relationships": "夫妻",
    }[a.topic] as string | undefined;
    const topicPalace = palaceName
      ? e.facts.find((fact) =>
          fact.candidate === a.candidate &&
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
    }[a.topic] as string;
    const ziweiRule = e.rules.find((item) =>
      item.candidate === a.candidate && item.id.endsWith(ruleSuffix)
    )!;
    const timingRefs = a.topic === "ziwei-timing"
      ? {
          transformation: e.facts.find((fact) =>
            fact.candidate === a.candidate &&
            fact.id.endsWith(".ziwei.transformations")
          )!.id,
          cycle: e.facts.find((fact) =>
            fact.candidate === a.candidate && fact.id.endsWith(".ziwei.cycles")
          )!.id,
          palace: e.facts.find((fact) =>
            fact.candidate === a.candidate && fact.id.endsWith(".ziwei.palace-0")
          )!.id,
        }
      : null;
    Object.assign(a, {
      conclusion: `${a.topic} 紫微结构测试未裁定`,
      supportRefs: timingRefs
        ? [timingRefs.transformation, timingRefs.cycle, timingRefs.palace]
        : [base.id, topicPalace!.id],
      counterRefs: [],
      counterReview: `${a.topic} 未检验完整联宫与跨层反证`,
      conditions: `${a.topic} 仅结构测试`,
      alternatives: `${a.topic} 需结合主题宫与现实资料复核`,
      ruleRefs: [ziweiRule.id],
      ...(timingRefs ? {
        timingChain: {
          target: "general",
          years: [...e.years],
          transformationRefs: [timingRefs.transformation],
          cycleRefs: [timingRefs.cycle],
          palaceRefs: [timingRefs.palace],
          crossLayerReview: "已区分本命、大限与流年层，未把层级标签直接换成事件。",
          missingLinks: ["缺少现实触发资料"],
          realityBasis: {
            status: "not-provided",
            summary: "合成测试未提供现实经历或目标。",
            source: null,
          },
          withdrawalConditions: "出生资料或时间层定位变化时撤回并重算。",
        },
      } : {}),
    });
  });
  const ziweiStructureRef = {
    candidate: r.ziweiReasoning[0].candidate,
    topic: "ziwei-structure",
  };
  r.uncertainty = "仅用于结构验证的合成解释";
  r.sections = SECTION_IDS.map((id) => ({
    id,
    claims: [
      {
        text: "结构测试解释",
        kind: "interpretation",
        factRefs: [b.id],
        ruleRefs: [rule.id],
        reasoningRefs,
        premiseStatus: "unresolved",
        conditions: "非真实命理报告",
        confidence: "low",
      },
    ],
  }));
  r.crossSystem = [
    {
      target: "general",
      years: [],
      relationship: "insufficient",
      text: "证据不足以共同判断",
      factRefs: [b.id, z.id],
      reasoningRefs: [...reasoningRefs, ziweiStructureRef],
      premiseStatus: "unresolved",
    },
  ];
  r.assertions = [{ factRef: b.id, value: b.value }];
  return r;
}

const ZIWEI_SECTION_TOPICS: Record<string, string> = {
  summary: "ziwei-structure",
  character: "ziwei-structure",
  career: "ziwei-career",
  wealth: "ziwei-wealth",
  relationships: "ziwei-relationships",
  timing: "ziwei-timing",
  advice: "ziwei-structure",
};

function asZiweiOnly(report: any, evidence = e) {
  report.mode = "ziwei";
  report.baziReasoning = [];
  report.crossSystem = [];
  report.assertions = [];
  const rule = evidence.rules.find((item) =>
    item.id.endsWith(".R-ziwei-transformations")
  )!;
  report.sections.forEach((section: any) =>
    section.claims.forEach((claim: any) => {
      claim.factRefs = rule.factRefs;
      claim.ruleRefs = [rule.id];
      claim.reasoningRefs = evidence.candidateIds.map((candidate) => ({
        candidate,
        topic: ZIWEI_SECTION_TOPICS[section.id],
      }));
      claim.premiseStatus = "unresolved";
    }),
  );
  return report;
}
test("完整报告可校验和渲染，并明确不是语义认证", () => {
  const r = valid();
  assert.equal(validateReport(r, e).chartId, e.chartId);
  const rendered = renderReport(r, e);
  assert.match(rendered, /可核对的命盘依据/);
  assert.match(
    rendered,
    /资料来源：地点=未核验；经度=未核验；时区=未核验。/,
  );
  assert.match(rendered, /## 术语速查/);
  assert.match(rendered, /\| 调候 \|/);
  assert.match(rendered, /\| 四化 \|/);
  assert.match(
    rendered,
    /> \*\*解释边界\*\*：传统解释把握为较低（非发生概率）；八字论证前提仍未决。非真实命理报告/,
  );
  assert.match(
    rendered,
    /<summary>查看本段命盘依据与论证主题<\/summary>/,
  );
  assert.match(
    rendered,
    /<summary>查看对照依据与论证主题<\/summary>/,
  );
  assert(
    rendered.indexOf("## 核心结论") < rendered.indexOf("## 术语速查"),
  );
  assert(
    rendered.indexOf("## 建议") < rendered.indexOf("## 术语速查"),
  );
  assert(
    rendered.indexOf("## 八字与紫微对照") <
      rendered.indexOf("## 术语速查"),
  );
  assert(
    rendered.indexOf("## 术语速查") <
      rendered.indexOf("## 八字判断的依据与分歧"),
  );
  const beforeAppendix = rendered.slice(
    0,
    rendered.indexOf("## 可核对的命盘依据"),
  );
  assert.match(beforeAppendix, /八字论证前提：未决（当前命盘：八字·/);
  assert(!beforeAppendix.includes(e.candidateIds[0]));
  assert(rendered.includes(`（${e.candidateIds[0]}）`));
});
test("报告拒绝死亡、诊断、保证收益与必然婚变断言", () => {
  const cases = [
    ["命主必死。", "death-prediction"],
    ["命主已确诊为癌症。", "medical-diagnosis"],
    ["这次投资稳赚不赔。", "guaranteed-finance"],
    ["两人注定离婚。", "inevitable-relationship"],
  ] as const;
  for (const [text, category] of cases) {
    const report = valid();
    report.sections[0].claims[0].text = text;
    assert.throws(
      () => validateReport(report, e),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "UNSAFE_REPORT_CLAIM" &&
        error.message.includes(
          findUnsafeReportClaim(text)?.label ?? "不会出现的标签",
        ),
      `${category} 应被拒绝`,
    );
  }
});
test("高风险门禁覆盖所有渲染自由文本入口", () => {
  const mutations: Array<(report: any) => void> = [
    (report) => { report.title = "稳赚命理报告"; },
    (report) => { report.uncertainty = "命主活不过五十岁"; },
    (report) => { report.sections[0].claims[0].conditions = "命主一定会得癌症"; },
    (report) => { report.baziReasoning[0].conclusion = "婚姻必破"; },
    (report) => { report.baziReasoning[0].counterReview = "投资必赚"; },
    (report) => { report.baziReasoning[0].conditions = "命主必二婚"; },
    (report) => { report.baziReasoning[0].alternatives = "死亡时间是五十岁"; },
    (report) => { report.baziReasoning.at(-1).timingChain.annualReviews[0].review = "命主一定会得癌症"; },
    (report) => { report.baziReasoning.at(-1).timingChain.crossLayerReview = "投资稳赚"; },
    (report) => { report.baziReasoning.at(-1).timingChain.missingLinks[0] = "婚姻必破"; },
    (report) => { report.baziReasoning.at(-1).timingChain.withdrawalConditions = "命主活不过五十岁"; },
    (report) => {
      const timing = report.baziReasoning.at(-1);
      timing.status = "conditional";
      timing.timingChain.missingLinks = [];
      timing.timingChain.realityBasis = {
        status: "provided",
        summary: "合成来源",
        source: "稳赚资料",
      };
    },
    (report) => { report.crossSystem[0].text = "命主确诊糖尿病"; },
  ];
  for (const mutate of mutations) {
    const report = valid();
    mutate(report);
    assert.throws(
      () => validateReport(report, e),
      (error: unknown) =>
        error instanceof InputError && error.code === "UNSAFE_REPORT_CLAIM",
    );
  }
});
test("明确否定高风险断言时允许通过，并在转折后继续检查", () => {
  const safe = valid();
  safe.title = "不作死亡或疾病诊断的命理解读";
  safe.uncertainty = "不能预测死亡时间，也不能确诊疾病";
  safe.sections[0].claims[0].text =
    "不能据此断言财旺、稳赚或必亏，也不代表关系必然离婚。";
  safe.sections[0].claims[0].conditions =
    "不宜把传统解释写成保证收益；并非稳赚。";
  safe.baziReasoning[0].conclusion = "没有稳赚，只有条件性解释";
  assert.doesNotThrow(() => validateReport(safe, e));

  const unsafeAfterContrast = valid();
  unsafeAfterContrast.sections[0].claims[0].text =
    "不能保证收益，但是这项投资稳赚不赔。";
  assert.throws(
    () => validateReport(unsafeAfterContrast, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "UNSAFE_REPORT_CLAIM",
  );
});
test("含八字事实的正文和跨体系判断必须绑定同候选论证", () => {
  const missing = valid();
  missing.sections[0].claims[0].reasoningRefs = [];
  assert.throws(
    () => validateReport(missing, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_REASONING_LINK",
  );

  const foreign = valid();
  foreign.sections[0].claims[0].reasoningRefs[0].candidate = "C-other";
  assert.throws(
    () => validateReport(foreign, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "INVALID_REASONING_LINK",
  );

  const duplicate = valid();
  duplicate.crossSystem[0].reasoningRefs.push({
    ...duplicate.crossSystem[0].reasoningRefs[0],
  });
  assert.throws(
    () => validateReport(duplicate, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "INVALID_REASONING_LINK",
  );
});
test("正文 premiseStatus 由所引论证状态决定，不能自行升级", () => {
  const report = valid();
  report.sections[0].claims[0].premiseStatus = "conditional";
  assert.throws(
    () => validateReport(report, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "PREMISE_STATUS_MISMATCH",
  );
});
test("正文提到用神等主题时必须绑定对应论证", () => {
  const report = valid();
  report.sections[0].claims[0].text = "用神取舍仍需核对，当前不作唯一判断。";
  report.sections[0].claims[0].reasoningRefs = [
    { candidate: e.candidateIds[0], topic: "strength" },
  ];
  assert.throws(
    () => validateReport(report, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_REASONING_LINK",
  );
});
test("未决前提拒绝显式越级，明确否定越级结论可通过并可见渲染", () => {
  const unsafe = valid();
  unsafe.sections[0].claims[0].text = "用神已经确定，无需再核对其他条件。";
  assert.throws(
    () => validateReport(unsafe, e),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "UNRESOLVED_PREMISE_CLAIM",
  );

  const safe = valid();
  safe.sections[0].claims[0].text =
    "当前尚不足以把木定成唯一用神，也不支持结论已经确定，仍须保留其他取法。";
  const markdown = renderReport(safe, e);
  assert.match(markdown, /八字论证前提：未决/);
  assert.match(markdown, /当前命盘：八字·旺衰、八字·格局、八字·调候、八字·扶抑、八字·用神取舍/);
});
test("部分来源逐项保留未核验状态", () => {
  const partial = contextFor(
    { ...input, provenance: { placeSource: "出生记录" } },
    [2026],
  );
  assert.match(
    renderReport(valid(partial), partial),
    /资料来源：地点=出生记录；经度=未核验；时区=未核验。/,
  );
});
test("八字与综合报告自动展示同候选起运范围并进入附录", () => {
  const uncertain = contextFor(
    { ...input, time: "04:00", timeBasis: "civil", uncertaintyMinutes: 59 },
    [2026],
  );
  const cycles = uncertain.facts.find((fact) =>
    fact.id.endsWith(".bazi.cycles"),
  )!;
  const markdown = renderReport(valid(uncertain), uncertain);
  assert(
    markdown.indexOf("## 建议") <
      markdown.indexOf("## 出生时间与起运范围（自动生成）"),
  );
  assert.match(markdown, /119 个样本，119 个不同起运结果/);
  assert.match(markdown, /2003-06-26T01:01:00\+08:00/);
  assert.match(markdown, /2003-07-05T22:59:00\+08:00/);
  assert(markdown.includes(`引用标识：${cycles.id}`));

  const bazi = valid(uncertain);
  bazi.mode = "bazi";
  bazi.crossSystem = [];
  bazi.ziweiReasoning = [];
  assert(renderReport(bazi, uncertain).includes("出生时间与起运范围"));

  const ziwei = asZiweiOnly(valid(uncertain), uncertain);
  assert(!renderReport(ziwei, uncertain).includes("出生时间与起运范围"));
});
test("双候选自动范围逐段绑定各自起止值与附录锚点", () => {
  const boundaryInput = JSON.parse(readFileSync(
    new URL("../examples/acceptance/boundary/birth.json", import.meta.url),
    "utf8",
  ));
  const boundaryReport = JSON.parse(readFileSync(
    new URL("../examples/acceptance/boundary/report.json", import.meta.url),
    "utf8",
  ));
  // 样例报告绑定历史 evidence v1。
  const boundary = contextFor(boundaryInput, [2026, 2027, 2028], "whoami.evidence.v1");
  const markdown = renderReport(boundaryReport, boundary);
  const start = markdown.indexOf("## 出生时间与起运范围（自动生成）");
  const end = markdown.indexOf("## 核心规则复核（自动生成）");
  assert(start >= 0 && end > start);
  const automatic = markdown.slice(start, end);
  const [c1, c2] = boundary.candidateIds;
  const c1Start = automatic.indexOf("### 候选 1");
  const c2Start = automatic.indexOf("### 候选 2");
  assert(c1Start >= 0 && c2Start > c1Start);
  const c1Block = automatic.slice(c1Start, c2Start);
  const c2Block = automatic.slice(c2Start);
  const c1Cycles = boundary.facts.find((fact) =>
    fact.candidate === c1 && fact.id.endsWith(".bazi.cycles"),
  )!;
  const c2Cycles = boundary.facts.find((fact) =>
    fact.candidate === c2 && fact.id.endsWith(".bazi.cycles"),
  )!;
  const c1Anchor = boundary.facts.findIndex((fact) => fact.id === c1Cycles.id) + 1;
  const c2Anchor = boundary.facts.findIndex((fact) => fact.id === c2Cycles.id) + 1;

  assert.match(c1Block, /3 个样本，3 个不同起运结果/);
  assert.match(c1Block, /1991-10-17T11:00:00\+08:00/);
  assert.match(c1Block, /1991-10-17T15:02:00\+08:00/);
  assert(c1Block.includes(`(#fact-${c1Anchor})`));
  assert(!c1Block.includes("1991-10-17T06:58:00+08:00"));
  assert(!c1Block.includes("1991-10-17T08:59:00+08:00"));

  assert.match(c2Block, /2 个样本，2 个不同起运结果/);
  assert.match(c2Block, /1991-10-17T06:58:00\+08:00/);
  assert.match(c2Block, /1991-10-17T08:59:00\+08:00/);
  assert(c2Block.includes(`(#fact-${c2Anchor})`));
  assert(!c2Block.includes("1991-10-17T11:00:00+08:00"));
  assert(!c2Block.includes("1991-10-17T15:02:00+08:00"));
  const beforeAppendix = markdown.slice(
    0,
    markdown.indexOf("## 可核对的命盘依据"),
  );
  assert(!beforeAppendix.includes(c1));
  assert(!beforeAppendix.includes(c2));
  assert(markdown.includes(`（${c1}）`));
  assert(markdown.includes(`（${c2}）`));
});
test("旧报告拒绝用于修改后的资料或年份", () => {
  assert.throws(
    () =>
      validateReport(valid(), contextFor({ ...input, time: "06:00" }, [2026])),
    /已变/,
  );
  assert.throws(
    () => validateReport(valid(), contextFor(input, [2027])),
    /已变/,
  );
});
test("不存在引用与错误事实不能通过", () => {
  const r = valid();
  r.sections[0].claims[0].factRefs = ["invented"];
  assert.throws(() => validateReport(r, e), /不存在/);
  const s = valid();
  s.assertions[0].value = "编造值";
  assert.throws(() => validateReport(s, e), /不一致/);
});
test("纯目录、空模板、缺章节、单边综合不能通过", () => {
  assert.throws(() => validateReport(reportTemplate(e), e));
  const r = valid();
  r.sections.pop();
  assert.throws(() => validateReport(r, e));
  const s = valid();
  s.crossSystem[0].factRefs = [e.facts.find((f) => f.system === "bazi")!.id];
  assert.throws(() => validateReport(s, e));
});
test("单体系不混入另一体系", () => {
  const r = valid();
  r.mode = "bazi";
  r.crossSystem = [];
  r.ziweiReasoning = [];
  assert.doesNotThrow(() => validateReport(r, e));
  r.sections[0].claims[0].factRefs.push(
    e.facts.find((f) => f.system === "ziwei")!.id,
  );
  assert.throws(() => validateReport(r, e));
});

test("多候选证据包不能只交付一张候选的报告", () => {
  const other = { ...e, candidateIds: [...e.candidateIds, "C2-unrepresented"] };
  assert.throws(() => validateReport(valid(), other), /每张候选/);
});

test("结构化事实对象键顺序变化不构成事实改变", () => {
  const r = valid();
  r.assertions[0].value = Object.fromEntries(
    Object.entries(r.assertions[0].value).reverse(),
  );
  assert.doesNotThrow(() => validateReport(r, e));
});

test("紫微单体系报告可独立校验", () => {
  const r = asZiweiOnly(valid());
  assert.doesNotThrow(() => validateReport(r, e));
});

test("旧紫微或综合报告不得仅替换版本号；八字单体系 v3/v4 可兼容读取", () => {
  const r = valid();
  r.schema = "whoami.report.v2";
  assert.throws(() => validateReport(r, e), /v5/);
  const oldCombined = valid();
  oldCombined.schema = "whoami.report.v4";
  oldCombined.ziweiReasoning.forEach((item: any) => delete item.timingChain);
  assert.throws(() => validateReport(oldCombined, e), /v5/);
  const oldBazi = valid();
  oldBazi.schema = "whoami.report.v3";
  delete oldBazi.timeReference;
  oldBazi.mode = "bazi";
  oldBazi.crossSystem = [];
  oldBazi.baziReasoning = oldBazi.baziReasoning.filter(
    (item: any) => item.topic !== "bazi-timing",
  );
  oldBazi.sections.forEach((section: any) =>
    section.claims.forEach((claim: any) => {
      claim.reasoningRefs = claim.reasoningRefs.filter(
        (item: any) => item.topic !== "bazi-timing",
      );
    }),
  );
  oldBazi.ziweiReasoning = [];
  delete oldBazi.ziweiReasoning;
  assert.equal(validateReport(oldBazi, e).ziweiReasoning.length, 0);
  const oldBaziV4 = valid();
  oldBaziV4.schema = "whoami.report.v4";
  delete oldBaziV4.timeReference;
  oldBaziV4.mode = "bazi";
  oldBaziV4.crossSystem = [];
  oldBaziV4.baziReasoning = oldBaziV4.baziReasoning.filter(
    (item: any) => item.topic !== "bazi-timing",
  );
  oldBaziV4.sections.forEach((section: any) =>
    section.claims.forEach((claim: any) => {
      claim.reasoningRefs = claim.reasoningRefs.filter(
        (item: any) => item.topic !== "bazi-timing",
      );
    }),
  );
  oldBaziV4.ziweiReasoning = [];
  assert.equal(validateReport(oldBaziV4, e).schema, "whoami.report.v4");

  const oldV5 = valid();
  oldV5.schema = "whoami.report.v5";
  delete oldV5.timeReference;
  oldV5.baziReasoning = oldV5.baziReasoning.filter(
    (item: any) => item.topic !== "bazi-timing",
  );
  oldV5.sections.forEach((section: any) =>
    section.claims.forEach((claim: any) => {
      claim.reasoningRefs = claim.reasoningRefs.filter(
        (item: any) => item.topic !== "bazi-timing",
      );
    }),
  );
  oldV5.crossSystem.forEach((item: any) => {
    item.reasoningRefs = item.reasoningRefs.filter(
      (ref: any) => ref.topic !== "bazi-timing",
    );
  });
  delete oldV5.crossSystem[0].target;
  delete oldV5.crossSystem[0].years;
  assert.equal(validateReport(oldV5, e).schema, "whoami.report.v5");
  oldV5.sections[0].claims[0].text = "未来年份与今后年份仍只保留条件性复核。";
  assert.doesNotThrow(() => validateReport(oldV5, e));
  oldV5.sections[0].claims[0].text = "明年仍只保留条件性复核。";
  assert.throws(
    () => validateReport(oldV5, e),
    /须迁移到 v6.*timeReference/,
  );
});
test("紫微五类论证缺失、重复或跨体系依据均拒绝", () => {
  const missing = valid();
  missing.ziweiReasoning.pop();
  assert.throws(() => validateReport(missing, e), /每张候选必须分别说明紫微/);

  const duplicate = valid();
  duplicate.ziweiReasoning.push(duplicate.ziweiReasoning[0]);
  assert.throws(() => validateReport(duplicate, e), /紫微论证候选\/主题未知或重复/);

  const crossSystem = valid();
  crossSystem.ziweiReasoning[0].counterRefs = [
    e.facts.find((fact) => fact.system === "bazi")!.id,
  ];
  assert.throws(
    () => validateReport(crossSystem, e),
    /紫微论证不能混入另一候选或体系/,
  );
});
test("紫微事业、财运与关系论证必须绑定对应主题规则和主题宫", () => {
  const wrongRule = valid();
  const career = wrongRule.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-career",
  );
  career.ruleRefs = [e.rules.find((rule) =>
    rule.id.endsWith(".R-ziwei-财运")
  )!.id];
  career.supportRefs.push(e.facts.find((fact) =>
    fact.id.endsWith(".ziwei.transformations")
  )!.id);
  assert.throws(
    () => validateReport(wrongRule, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TOPIC_RULE",
  );

  const missingPalace = valid();
  const missingCareer = missingPalace.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-career",
  );
  missingCareer.supportRefs = missingCareer.supportRefs.filter((id: string) => {
    const fact = e.facts.find((item) => item.id === id)!;
    return (fact.value as { name?: string }).name !== "官禄";
  });
  assert.throws(
    () => validateReport(missingPalace, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TOPIC_EVIDENCE",
  );
});
test("紫微本命结构必须绑定本命基础、命宫和主题联宫规则", () => {
  const missingBase = valid();
  const structure = missingBase.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-structure",
  );
  structure.supportRefs = structure.supportRefs.filter(
    (id: string) => !id.endsWith(".ziwei.base"),
  );
  assert.throws(
    () => validateReport(missingBase, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TOPIC_EVIDENCE",
  );

  const transformationsOnly = valid();
  const anotherStructure = transformationsOnly.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-structure",
  );
  const transformationRule = e.rules.find((rule) =>
    rule.id.endsWith(".R-ziwei-transformations")
  )!;
  anotherStructure.ruleRefs = [transformationRule.id];
  anotherStructure.supportRefs.push(e.facts.find((fact) =>
    fact.id.endsWith(".ziwei.transformations")
  )!.id);
  assert.throws(
    () => validateReport(transformationsOnly, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TOPIC_RULE",
  );
});
test("v5 限运作用链绑定年份、四化、大限、主题宫与现实触发", () => {
  const missing = valid();
  const missingTiming = missing.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-timing",
  );
  delete missingTiming.timingChain;
  assert.throws(
    () => validateReport(missing, e),
    /timingChain/,
  );

  const wrongYear = valid();
  wrongYear.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-timing",
  ).timingChain.years = [2025];
  assert.throws(
    () => validateReport(wrongYear, e),
    /当前证据包内的流年/,
  );

  const wrongPalace = valid();
  const timing = wrongPalace.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-timing",
  );
  timing.timingChain.palaceRefs = [
    e.facts.find((fact) => fact.id.endsWith(".ziwei.base"))!.id,
  ];
  assert.throws(
    () => validateReport(wrongPalace, e),
    /timingChain\.palaceRefs/,
  );

  const wrongTarget = valid();
  wrongTarget.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-timing",
  ).timingChain.target = "career";
  assert.throws(
    () => validateReport(wrongTarget, e),
    /career.*官禄宫/,
  );

  const careerTarget = valid();
  const careerTiming = careerTarget.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-timing",
  );
  const wealthPalace = careerTiming.timingChain.palaceRefs[0];
  const careerPalace = e.facts.find((fact) =>
    fact.id.includes(".ziwei.palace-") &&
    (fact.value as { name?: string }).name === "官禄"
  )!.id;
  careerTiming.timingChain.target = "career";
  careerTiming.timingChain.palaceRefs = [careerPalace];
  careerTiming.supportRefs = careerTiming.supportRefs.map((id: string) =>
    id === wealthPalace ? careerPalace : id
  );
  assert.doesNotThrow(() => validateReport(careerTarget, e));

  const misplaced = valid();
  misplaced.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-career",
  ).timingChain = structuredClone(timing.timingChain);
  assert.throws(
    () => validateReport(misplaced, e),
    /只有 ziwei-timing/,
  );
});
test("现实触发未绑定时限运失败封闭，显式来源也不等于现实验证", () => {
  const report = valid();
  const timing = report.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-timing",
  );
  timing.status = "conditional";
  assert.throws(
    () => validateReport(report, e),
    /现实触发资料未绑定.*unresolved/,
  );

  timing.timingChain.realityBasis = {
    status: "provided",
    summary: "由报告编写者声明已获得目标和现实经历。",
    source: "用户在本次会话提供的自述",
  };
  assert.throws(
    () => validateReport(report, e),
    /清空未闭合环节/,
  );
  timing.timingChain.missingLinks = [];
  assert.doesNotThrow(() => validateReport(report, e));
});
test("紫微年度正文必须绑定限运论证，并由 timingChain 覆盖完整年份范围", () => {
  const evidence = contextFor(input, [2026, 2027, 2028]);
  const missingTiming = asZiweiOnly(valid(evidence), evidence);
  const careerClaim = missingTiming.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  careerClaim.text = "事业主题讨论 2026—2028，但不把年份直接写成事件。";
  assert.throws(
    () => validateReport(missingTiming, evidence),
    /具体年份.*ziwei-timing/,
  );

  careerClaim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  const timing = missingTiming.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-timing",
  );
  timing.timingChain.years = [2026, 2028];
  assert.throws(
    () => validateReport(missingTiming, evidence),
    /未全部纳入.*timingChain\.years/,
  );

  timing.timingChain.years = [2026, 2027, 2028];
  assert.doesNotThrow(() => validateReport(missingTiming, evidence));
});
test("v6 以冻结日期解析相对年份，并拒绝越界年份与模糊大限", () => {
  const evidence = contextFor(input, [2026, 2027, 2028]);
  const report = asZiweiOnly(valid(evidence), evidence);
  const careerClaim = report.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  careerClaim.text = "明年只讨论事业主题，不把它写成必然事件。";
  assert.throws(
    () => validateReport(report, evidence),
    /相对时间基准|具体年份.*ziwei-timing/,
  );
  careerClaim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  assert.doesNotThrow(() => validateReport(report, evidence));

  const outOfScope = structuredClone(report);
  outOfScope.sections.find(
    (section: any) => section.id === "career",
  ).claims[0].text = "后年只讨论事业主题，不把它写成必然事件。";
  outOfScope.timeReference.asOfDate = "2028-09-25";
  assert.throws(
    () => validateReport(outOfScope, evidence),
    /相对年份不在当前 evidence\.years/,
  );

  const vagueCycle = structuredClone(report);
  vagueCycle.sections.find(
    (section: any) => section.id === "career",
  ).claims[0].text = "下个大限再决定事业行动。";
  assert.throws(
    () => validateReport(vagueCycle, evidence),
    /无法唯一解析的相对大限/,
  );

  const badDate = structuredClone(report);
  badDate.timeReference.asOfDate = "2026-02-30";
  assert.throws(() => validateReport(badDate, evidence), /有效的 YYYY-MM-DD/);
  const badZone = structuredClone(report);
  badZone.timeReference.timeZone = "Mars/Olympus";
  assert.throws(() => validateReport(badZone, evidence), /有效的 IANA 时区/);
});
test("历法限定相对时间失败封闭，明确年份与体系年界继续允许", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  const careerClaim = base.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  for (const text of [
    "农历明年再判断事业。",
    "明年按农历再判断事业。",
    "过完春节再判断事业。",
    "立春后再判断事业。",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /未建模的历法限定时间.*明确公历年份及对应体系年界/,
      text,
    );
  }

  careerClaim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  careerClaim.text =
    "2027紫微流年按农历年标签复核事业，不把年度标签写成现实事件。";
  assert.doesNotThrow(() => validateReport(base, evidence));
  careerClaim.text =
    "八字2027年界按立春口径复核，未来年份与今后年份仍不是相对年份指令。";
  assert.doesNotThrow(() => validateReport(base, evidence));
});
test("年度 evidence 拒绝半年季度月周日粒度，明确年度主题继续允许", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  for (const text of [
    "明年上半年判断事业结果。",
    "三个月内判断事业结果。",
    "年底判断事业结果。",
    "下个月判断事业结果。",
    "月末判断事业结果。",
    "下个季度判断事业结果。",
    "第一季度判断事业结果。",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /当前 evidence 不支持的细分时间.*退回明确年度主题/,
      text,
    );
  }

  const careerClaim = base.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  careerClaim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  careerClaim.text =
    "2027年度只复核事业主题；月份资料尚未提供，流月与流日也未计算。";
  assert.doesNotThrow(() => validateReport(base, evidence));
});
test("模糊时间范围必须先明确年份或起止范围，不能自行换算", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  for (const text of [
    "近期判断事业结果。",
    "不久后判断事业结果。",
    "很快会有事业结果。",
    "过阵子判断事业结果。",
    "过一段时间判断事业结果。",
    "什么时候适合调整工作。",
    "短期内判断事业结果。",
    "未来一段时间判断事业结果。",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /无法绑定到确定年份或起止范围.*明确 YYYY 年度主题或明确日期范围/,
      text,
    );
  }

  const careerClaim = base.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  careerClaim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  careerClaim.text =
    "2027年度只复核事业主题；当前资料不支持具体时点判断。";
  assert.doesNotThrow(() => validateReport(base, evidence));
});
test("多年相对范围须改写为年度闭区间，并逐年覆盖 evidence", () => {
  const evidence = contextFor(input, [2026, 2027, 2028, 2029]);
  const base = asZiweiOnly(valid(evidence), evidence);
  for (const text of [
    "未来三年判断事业结果。",
    "三年内判断事业结果。",
    "接下来五年判断事业结果。",
    "这几年判断事业结果。",
    "近几年判断事业结果。",
    "长期判断事业结果。",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /无法唯一确定首尾年份.*YYYY—YYYY 年度闭区间/,
      text,
    );
  }

  const careerClaim = base.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  careerClaim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  careerClaim.text =
    "2027—2029年度只复核事业主题，不把年度范围写成事件结果。";
  assert.doesNotThrow(() => validateReport(base, evidence));

  const incompleteEvidence = contextFor(input, [2026, 2027]);
  const incomplete = asZiweiOnly(valid(incompleteEvidence), incompleteEvidence);
  const incompleteClaim = incomplete.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  incompleteClaim.reasoningRefs.push({
    candidate: incompleteEvidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  incompleteClaim.text =
    "2027—2029年度只复核事业主题，不把年度范围写成事件结果。";
  assert.throws(
    () => validateReport(incomplete, incompleteEvidence),
    /明确年度区间缺少 2028、2029 evidence.*补算完整年份/,
  );

  const reversed = structuredClone(base);
  reversed.sections.find(
    (section: any) => section.id === "career",
  ).claims[0].text = "2029—2027年度事业主题。";
  assert.throws(
    () => validateReport(reversed, evidence),
    /起年晚于止年.*YYYY—YYYY 顺序/,
  );
});
test("绝对月日星期与命名历法点不能绕过年度 evidence", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  for (const text of [
    "2027年3月判断事业结果。",
    "2025年12月复核过事业结果。",
    "3月15日判断事业结果。",
    "3月份判断事业结果。",
    "三月十五日判断事业结果。",
    "周一判断事业结果。",
    "星期五判断事业结果。",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /当前 evidence 不支持的绝对细分时间.*退回明确年度主题/,
      text,
    );
  }

  for (const text of [
    "明年春节判断事业结果。",
    "2027年立春判断事业结果。",
    "立春当天判断事业结果。",
    "清明那天判断事业结果。",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /未进入 evidence 的历法时点.*公历日期、历法与时区口径/,
      text,
    );
  }

  base.title = "1993 年冬月癸水命的年度事业主题";
  base.uncertainty =
    "八字年度边界按立春口径，紫微年度边界按农历新年标签；不提供具体时点判断。";
  const careerClaim = base.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  careerClaim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  careerClaim.text =
    "2027年度只复核事业主题；月份、日期和星期资料均未提供。";
  assert.doesNotThrow(() => validateReport(base, evidence));
  base.title = "1996年7月19日合成资料的年度事业主题";
  assert.doesNotThrow(() => validateReport(base, evidence));
});
test("数字日期与日内时刻不能伪装成年度判断", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  for (const text of [
    "2027-03-15能升职吗？",
    "2027/03/15适合谈加薪吗？",
    "2027.3.15会有结果吗？",
    "3.15适合面试吗？",
    "03/15能签约吗？",
    "3-15跳槽如何？",
    "2027-03-15必然成功。",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /把数字日期.*用于当前年度 evidence 不支持的具体时点判断.*日级证据/,
      text,
    );
  }

  for (const text of [
    "今晚行动好吗？",
    "明早会有结果吗？",
    "明天上午是否适合面试？",
    "上午九点联系主管合适吗？",
    "下午3:30适合谈加薪吗？",
    "09:30能签约吗？",
    "上午九点是最佳时刻。",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /UNSUPPORTED_TIME_OF_DAY|当地日期与 IANA 时区.*日级和小时级证据/,
      text,
    );
  }

  base.title = "合成资料的 2027 年度事业主题";
  base.uncertainty =
    "资料按公历 1993-11-08 14:20 计算；报告以 2026-09-25、Asia/Shanghai 冻结年度口径，不提供具体日期或日内时刻判断。";
  const careerClaim = base.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  careerClaim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  careerClaim.text =
    "2027年度只复核事业主题；具体日期与日内时刻资料均未提供。";
  assert.doesNotThrow(() => validateReport(base, evidence));
});
test("歧义与非法日期时刻先于 evidence 粒度失败", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  for (const text of [
    "2027-02-29适合行动吗？",
    "2027-13-01会有结果吗？",
    "2027-04-31能签约吗？",
    "2027-03/15适合面试吗？",
    "02/30适合谈加薪吗？",
    "31-31会成功吗？",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /无效或分隔符不一致的数字日期|不存在的无年份数字日期/,
      text,
    );
  }

  for (const text of [
    "03/04适合面试吗？",
    "11-12会有结果吗？",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /月日顺序不唯一.*YYYY-MM-DD/,
      text,
    );
  }

  for (const text of [
    "24:30适合行动吗？",
    "09:60会有结果吗？",
    "23:59:60能签约吗？",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /无效钟点.*00—23.*00—59/,
      text,
    );
  }

  for (const text of [
    "09:30 CST适合面试吗？",
    "北京时间上午九点行动好吗？",
  ]) {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    assert.throws(
      () => validateReport(report, evidence),
      /时区缩写或口语标签.*IANA 时区/,
      text,
    );
  }
});
test("显式 IANA 当地时刻先验证 DST 存在性与唯一性", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  const validateCareerText = (text: string) => {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    return () => validateReport(report, evidence);
  };

  for (const text of [
    "2027-03-14 02:30 America/New_York适合行动吗？",
    "2027-03-14 02:30 America/New_York later能签约吗？",
  ])
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "NONEXISTENT_LOCAL_TIME",
      text,
    );

  assert.throws(
    validateCareerText(
      "2026-11-01 01:30 America/New_York适合谈加薪吗？",
    ),
    (error: unknown) =>
      error instanceof InputError && error.code === "AMBIGUOUS_LOCAL_TIME",
  );

  for (const text of [
    "适合在2026-11-01 01:30 America/New_York earlier谈加薪吗？",
    "适合在2026-11-01 01:30 America/New_York later谈加薪吗？",
    "适合在2026-11-01 03:30 America/New_York谈加薪吗？",
  ])
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "UNSUPPORTED_TIME_GRANULARITY",
      text,
    );

  assert.throws(
    validateCareerText("2027-03-14 02:30 America/Nowhere适合行动吗？"),
    (error: unknown) =>
      error instanceof InputError && error.code === "INVALID_TIMEZONE",
  );
});
test("显式 UTC offset 必须与 IANA 当地时刻规则一致", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  const validateCareerText = (text: string) => {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    return () => validateReport(report, evidence);
  };

  for (const text of [
    "适合在2026-11-01T01:30-04:00[America/New_York]谈加薪吗？",
    "适合在2026-11-01T01:30-05:00[America/New_York]谈加薪吗？",
    "适合在2027-03-14T03:30-04:00[America/New_York]行动吗？",
  ])
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "UNSUPPORTED_TIME_GRANULARITY",
      text,
    );

  for (const text of [
    "2026-11-01T01:30-06:00[America/New_York]适合签约吗？",
    "2027-03-14T03:30-05:00[America/New_York]适合行动吗？",
  ])
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "OFFSET_TIME_ZONE_MISMATCH",
      text,
    );

  assert.throws(
    validateCareerText(
      "2027-03-14T02:30-05:00[America/New_York]适合行动吗？",
    ),
    (error: unknown) =>
      error instanceof InputError && error.code === "NONEXISTENT_LOCAL_TIME",
  );
  assert.throws(
    validateCareerText(
      "2027-03-14T03:30-04:00[America/Nowhere]适合行动吗？",
    ),
    (error: unknown) =>
      error instanceof InputError && error.code === "INVALID_TIMEZONE",
  );
});
test("等价时间表达归并为同一绝对时刻，不能伪装成两个候选", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  const validateCareerText = (text: string) => {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    return () => validateReport(report, evidence);
  };

  for (const text of [
    "2026-11-01T01:30-04:00[America/New_York]和2026-11-01T05:30Z哪个更适合签约？",
    "2026-11-01T01:30-05:00[America/New_York]与2026-11-01T06:30Z哪个更好？",
    "2026-11-01T01:30-04:00[America/New_York]和2026-11-01T13:30+08:00[Asia/Shanghai]二选一。",
  ])
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "DUPLICATE_ABSOLUTE_TIME",
      text,
    );

  assert.throws(
    validateCareerText(
      "2026-11-01T01:30-05:00[America/New_York]和2026-11-01T05:30Z哪个更适合签约？",
    ),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "UNSUPPORTED_TIME_GRANULARITY",
  );

  for (const text of [
    "2026-02-30T05:30Z适合行动吗？",
    "2026-11-01T25:30Z适合行动吗？",
    "2026-11-01T01:31-04:00[America/New_York]适合行动吗？",
  ]) {
    const expected = text.includes("02-30")
      ? "INVALID_NUMERIC_DATE"
      : text.includes("T25:")
        ? "INVALID_CLOCK_TIME"
        : "UNSUPPORTED_TIME_GRANULARITY";
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError && error.code === expected,
      text,
    );
  }

  const acknowledged = structuredClone(base);
  const claim = acknowledged.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  claim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  claim.text =
    "2026-11-01T01:30-04:00[America/New_York]与2026-11-01T05:30Z两者表示同一绝对时刻，仅说明写法等价。";
  assert.doesNotThrow(() => validateReport(acknowledged, evidence));
});
test("绝对时间区间先校验顺序，再归并等价或重叠候选", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  const validateCareerText = (text: string) => {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    return () => validateReport(report, evidence);
  };

  for (const [text, code] of [
    [
      "2026-11-01T05:30Z至2026-11-01T05:30Z适合签约吗？",
      "ZERO_LENGTH_TIME_INTERVAL",
    ],
    [
      "2026-11-01T06:30Z至2026-11-01T05:30Z适合签约吗？",
      "REVERSED_TIME_INTERVAL",
    ],
    [
      "2026-11-01T05:30Z至2026-11-01T06:30Z至2026-11-01T07:30Z适合签约吗？",
      "AMBIGUOUS_TIME_INTERVAL",
    ],
    [
      "区间一是2026-11-01T01:30-04:00[America/New_York]至2026-11-01T01:30-05:00[America/New_York]；区间二是2026-11-01T05:30Z至2026-11-01T06:30Z，哪个更适合签约？",
      "DUPLICATE_TIME_INTERVAL",
    ],
    [
      "区间一是2026-11-01T05:30Z至2026-11-01T06:30Z；区间二是2026-11-01T06:00Z至2026-11-01T07:00Z，两个窗口哪个更适合签约？",
      "OVERLAPPING_TIME_INTERVAL",
    ],
  ] as const)
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError && error.code === code,
      text,
    );

  for (const text of [
    "区间一是2026-11-01T05:30Z至2026-11-01T06:30Z；区间二是2026-11-01T06:30Z至2026-11-01T07:30Z，两个窗口哪个更适合签约？",
    "区间一是2026-11-01T05:30Z至2026-11-01T06:30Z；区间二是2026-11-01T07:00Z至2026-11-01T08:00Z，哪个更好？",
  ])
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "UNSUPPORTED_TIME_GRANULARITY",
      text,
    );

  const acknowledged = structuredClone(base);
  const claim = acknowledged.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  claim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  claim.text =
    "2026-11-01T05:30Z至2026-11-01T06:30Z与2026-11-01T06:00Z至2026-11-01T07:00Z两者存在重叠，仅作时间换算说明。";
  assert.doesNotThrow(() => validateReport(acknowledged, evidence));
});
test("开放区间须补齐端点，声明时长按绝对经过时间核对", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  const validateCareerText = (text: string) => {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    return () => validateReport(report, evidence);
  };

  for (const text of [
    "2026-11-01T05:30Z以后哪个时间更适合签约？",
    "截至2026-11-01T06:30Z适合行动吗？",
  ])
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "OPEN_ENDED_TIME_INTERVAL",
      text,
    );

  for (const text of [
    "2026-11-01T05:30Z至2026-11-01T06:30Z，持续90分钟，适合签约吗？",
    "2027-03-14T01:30-05:00[America/New_York]至2027-03-14T03:30-04:00[America/New_York]，持续2小时，适合行动吗？",
    "2026-11-01T01:30-04:00[America/New_York]至2026-11-01T01:30-05:00[America/New_York]，实际经过0分钟，适合签约吗？",
  ])
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "TIME_INTERVAL_DURATION_MISMATCH",
      text,
    );

  assert.throws(
    validateCareerText(
      "2026-11-01T05:30Z至2026-11-01T06:30Z，持续1小时75分钟，适合签约吗？",
    ),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "INVALID_TIME_INTERVAL_DURATION",
  );
  assert.throws(
    validateCareerText(
      "持续60分钟的窗口是2026-11-01T05:30Z至2026-11-01T06:30Z，适合签约吗？",
    ),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "AMBIGUOUS_TIME_INTERVAL_DURATION",
  );

  for (const text of [
    "2026-11-01T05:30Z至2026-11-01T06:30Z，持续60分钟，适合签约吗？",
    "2027-03-14T01:30-05:00[America/New_York]至2027-03-14T03:30-04:00[America/New_York]，实际经过60分钟，适合行动吗？",
  ])
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "UNSUPPORTED_TIME_GRANULARITY",
      text,
    );

  const informational = structuredClone(base);
  const claim = informational.sections.find(
    (section: any) => section.id === "career",
  ).claims[0];
  claim.reasoningRefs.push({
    candidate: evidence.candidateIds[0],
    topic: "ziwei-timing",
  });
  claim.text = "资料截至2026-11-01T06:30Z，仅作来源时间记录。";
  assert.doesNotThrow(() => validateReport(informational, evidence));
});
test("重复日程须先限定绝对范围与地区时区，再提供逐次 evidence", () => {
  const evidence = contextFor(input, [2026, 2027]);
  const base = asZiweiOnly(valid(evidence), evidence);
  const validateCareerText = (text: string) => {
    const report = structuredClone(base);
    report.sections.find(
      (section: any) => section.id === "career",
    ).claims[0].text = text;
    return () => validateReport(report, evidence);
  };

  for (const [text, code] of [
    ["每天09:00适合联系客户吗？", "RECURRENCE_RANGE_REQUIRED"],
    [
      "2026-11-01T00:00Z至2026-11-08T00:00Z，每天09:00适合联系客户吗？",
      "RECURRENCE_TIME_ZONE_REQUIRED",
    ],
    [
      "2026-11-01T00:00-04:00[America/New_York]至2026-11-08T00:00-05:00[America/New_York]，每天09:00适合联系客户吗？",
      "UNSUPPORTED_RECURRENCE_GRANULARITY",
    ],
  ] as const)
    assert.throws(
      validateCareerText(text),
      (error: unknown) =>
        error instanceof InputError && error.code === code,
      text,
    );

  const informational = structuredClone(base);
  informational.sections.find(
    (section: any) => section.id === "career",
  ).claims[0].text = "系统每天09:00运行，仅作计划说明。";
  assert.doesNotThrow(() => validateReport(informational, evidence));
});
test("紫微正文必须绑定章节主题，不能继续使用 not-applicable", () => {
  const missing = valid();
  const ziweiFact = e.facts.find((fact) => fact.system === "ziwei")!;
  const ziweiRule = e.rules.find((rule) =>
    rule.id.endsWith(".R-ziwei-transformations")
  )!;
  missing.sections[0].claims[0].factRefs.push(ziweiFact.id);
  missing.sections[0].claims[0].ruleRefs.push(ziweiRule.id);
  assert.throws(
    () => validateReport(missing, e),
    /每个紫微候选事实都必须绑定具体论证前提/,
  );

  const wrongTopic = valid();
  wrongTopic.sections[0].claims[0].factRefs.push(ziweiFact.id);
  wrongTopic.sections[0].claims[0].ruleRefs.push(ziweiRule.id);
  wrongTopic.sections[0].claims[0].reasoningRefs.push({
    candidate: e.candidateIds[0],
    topic: "ziwei-career",
  });
  assert.throws(
    () => validateReport(wrongTopic, e),
    /本命结构主题.*对应紫微论证/,
  );

  const pureZiwei = asZiweiOnly(valid());
  pureZiwei.sections[0].claims[0].premiseStatus = "not-applicable";
  assert.throws(
    () => validateReport(pureZiwei, e),
    /premiseStatus 必须与所引八字与紫微论证状态一致|premiseStatus 必须与所引八字论证状态一致/,
  );
});
test("正文状态取八字与紫微所引前提中的最保守值", () => {
  const report = valid();
  report.baziReasoning.forEach((item: any) => {
    if (item.topic !== "bazi-timing") item.status = "conditional";
  });
  report.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-structure",
  ).status = "conditional";
  report.sections.forEach((section: any) =>
    section.claims.forEach((claim: any) => {
      claim.premiseStatus = "conditional";
    }),
  );
  report.crossSystem[0].premiseStatus = "conditional";
  const claim = report.sections[0].claims[0];
  const ziweiFact = e.facts.find((fact) => fact.system === "ziwei")!;
  const ziweiRule = e.rules.find((rule) =>
    rule.id.endsWith(".R-ziwei-transformations")
  )!;
  claim.factRefs.push(ziweiFact.id);
  claim.ruleRefs.push(ziweiRule.id);
  claim.reasoningRefs = [
    ...claim.reasoningRefs,
    {
      candidate: e.candidateIds[0],
      topic: "ziwei-structure",
    },
  ];
  assert.doesNotThrow(() => validateReport(report, e));

  report.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-structure",
  ).status = "unresolved";
  assert.throws(
    () => validateReport(report, e),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "PREMISE_STATUS_MISMATCH",
  );
  claim.premiseStatus = "unresolved";
  report.crossSystem[0].premiseStatus = "unresolved";
  assert.doesNotThrow(() => validateReport(report, e));
});
test("缺主题、重复主题和漏写反证复核均拒绝", () => {
  const missing = valid(); missing.baziReasoning.pop();
  assert.throws(() => validateReport(missing, e), /每张候选/);
  const duplicate = valid(); duplicate.baziReasoning.push(duplicate.baziReasoning[0]);
  assert.throws(() => validateReport(duplicate, e), /重复/);
  const blank = valid(); blank.baziReasoning[0].counterReview = " ";
  assert.throws(() => validateReport(blank, e), /counterReview/);
});
test("v6 八字运年论证必须绑定专属规则、周期事实和合法年份", () => {
  const missing = valid();
  missing.baziReasoning = missing.baziReasoning.filter(
    (item: any) => item.topic !== "bazi-timing",
  );
  assert.throws(
    () => validateReport(missing, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_REASONING",
  );

  const wrongRule = valid();
  const wrongRuleTiming = wrongRule.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  );
  const structureRule = e.rules.find((item) =>
    item.id.endsWith(".R-bazi-structure")
  )!;
  wrongRuleTiming.ruleRefs = [structureRule.id];
  wrongRuleTiming.counterRefs.push(
    structureRule.factRefs.find((id) =>
      e.facts.some((fact) => fact.id === id && fact.system === "bazi")
    )!,
  );
  assert.throws(
    () => validateReport(wrongRule, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TOPIC_RULE",
  );

  const wrongFact = valid();
  const wrongFactTiming = wrongFact.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  );
  wrongFactTiming.supportRefs = [e.facts.find((fact) =>
    fact.id.endsWith(".bazi.relations")
  )!.id];
  assert.throws(
    () => validateReport(wrongFact, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TOPIC_EVIDENCE",
  );

  const wrongYear = valid();
  wrongYear.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  ).years = [2027];
  assert.throws(() => validateReport(wrongYear, e), /当前证据包内的流年/);

  const missingNarrativeYear = valid();
  const narrativeTiming = missingNarrativeYear.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  );
  narrativeTiming.years = [];
  narrativeTiming.conclusion = "2026 年的运年作用仍未裁定。";
  assert.throws(
    () => validateReport(missingNarrativeYear, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TIMING_YEAR",
  );

  const missingChain = valid();
  delete missingChain.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  ).timingChain;
  assert.throws(
    () => validateReport(missingChain, e),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "INVALID_REPORT" &&
      /timingChain/.test(error.message),
  );

  const misplacedChain = valid();
  misplacedChain.baziReasoning[0].timingChain = structuredClone(
    misplacedChain.baziReasoning.at(-1).timingChain,
  );
  assert.throws(
    () => validateReport(misplacedChain, e),
    /只有 bazi-timing 可以填写 timingChain/,
  );

  const incompleteAnnuals = valid();
  incompleteAnnuals.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  ).timingChain.annualReviews = [];
  assert.throws(
    () => validateReport(incompleteAnnuals, e),
    /annualReviews 必须逐项覆盖 years/,
  );

  const wrongPillar = valid();
  wrongPillar.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  ).timingChain.annualReviews[0].pillar = "甲子";
  assert.throws(
    () => validateReport(wrongPillar, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "FACT_MISMATCH",
  );

  const missingNatalLink = valid();
  const missingNatalTiming = missingNatalLink.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  );
  missingNatalTiming.timingChain.annualReviews[0].natalRefs = [
    missingNatalTiming.timingChain.cycleRefs[0],
  ];
  assert.throws(
    () => validateReport(missingNatalLink, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "INVALID_REFERENCE",
  );

  const prematureConditional = valid();
  prematureConditional.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  ).status = "conditional";
  assert.throws(
    () => validateReport(prematureConditional, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "PREMISE_STATUS_MISMATCH",
  );

  const legacy = valid();
  legacy.schema = "whoami.report.v5";
  delete legacy.timeReference;
  assert.throws(() => validateReport(legacy, e), /bazi-timing 只属于/);
});
test("v6 引用八字运年或具体年份时必须绑定覆盖该年的运年论证", () => {
  const report = valid();
  const candidate = e.candidateIds[0]!;
  const cycle = e.facts.find((fact) => fact.id.endsWith(".bazi.cycles"))!;
  const timingRule = e.rules.find((item) =>
    item.id.endsWith(".R-bazi-timing")
  )!;
  const claim = report.sections[0].claims[0];
  claim.text = "2026 年只保留未决的八字运年解释。";
  claim.factRefs = [cycle.id];
  claim.ruleRefs = [timingRule.id];
  claim.reasoningRefs = [{ candidate, topic: "selection" }];
  assert.throws(
    () => validateReport(report, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_REASONING_LINK",
  );

  claim.reasoningRefs = [{ candidate, topic: "bazi-timing" }];
  assert.doesNotThrow(() => validateReport(report, e));
  const reportTiming = report.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  );
  reportTiming.years = [];
  reportTiming.timingChain.annualReviews = [];
  assert.throws(
    () => validateReport(report, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TIMING_YEAR",
  );
});
test("同候选八字主题不能整段复制论证，但可复用单个字段", () => {
  const duplicated = valid();
  const [source, target] = duplicated.baziReasoning;
  for (const field of ["conclusion", "counterReview", "conditions", "alternatives"])
    target[field] = ` \n ${source[field]} \t `;
  assert.throws(
    () => validateReport(duplicated, e),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "DUPLICATE_REASONING_NARRATIVE" &&
      /八字论证/.test(error.message),
  );

  const sharedConclusion = valid();
  sharedConclusion.baziReasoning[1].conclusion =
    sharedConclusion.baziReasoning[0].conclusion;
  assert.doesNotThrow(() => validateReport(sharedConclusion, e));
});
test("同候选紫微主题不能整段复制论证，但可复用单个字段", () => {
  const duplicated = valid();
  const [source, target] = duplicated.ziweiReasoning;
  for (const field of ["conclusion", "counterReview", "conditions", "alternatives"])
    target[field] = ` \n ${source[field]} \t `;
  assert.throws(
    () => validateReport(duplicated, e),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "DUPLICATE_REASONING_NARRATIVE" &&
      /紫微论证/.test(error.message),
  );

  const sharedCondition = valid();
  sharedCondition.ziweiReasoning[1].conditions =
    sharedCondition.ziweiReasoning[0].conditions;
  assert.doesNotThrow(() => validateReport(sharedCondition, e));
});
test("未决允许没有已定位反证，但必须说明缺口并提供盘面依据", () => {
  const r = valid();
  assert.doesNotThrow(() => validateReport(r, e));
  r.baziReasoning[0].supportRefs = [];
  assert.throws(() => validateReport(r, e), /盘面依据/);
});
test("论证拒绝跨体系、另一候选、悬空规则和重复计数", () => {
  const z = valid();
  z.baziReasoning[0].counterRefs = [e.facts.find(f => f.system === "ziwei")!.id];
  assert.throws(() => validateReport(z, e), /另一候选或体系/);
  const foreign = { ...e, facts: [...e.facts, { ...e.facts.find(f => f.system === "bazi")!, id: "foreign", candidate: "C-other" }] };
  const r = valid(); r.baziReasoning[0].counterRefs = ["foreign"];
  assert.throws(() => validateReport(r, foreign), /另一候选或体系/);
  const badRule = valid(); badRule.baziReasoning[0].ruleRefs.push(e.rules.find(r => r.id.includes("R-ziwei"))!.id);
  assert.throws(() => validateReport(badRule, e), /每条规则/);
  const duplicate = valid(); duplicate.baziReasoning[0].supportRefs.push(duplicate.baziReasoning[0].supportRefs[0]);
  assert.throws(() => validateReport(duplicate, e), /重复计数/);
});
test("八字主题必须绑定对应结构规则与事实锚点", () => {
  const wrongRule = valid();
  const pattern = wrongRule.baziReasoning.find(
    (item: any) => item.topic === "pattern",
  );
  const cycles = e.facts.find((fact) => fact.id.endsWith(".bazi.cycles"))!;
  pattern.supportRefs.push(cycles.id);
  pattern.ruleRefs = [e.rules.find((rule) =>
    rule.id.endsWith(".R-bazi-timing")
  )!.id];
  assert.throws(
    () => validateReport(wrongRule, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TOPIC_RULE",
  );

  const missingFact = valid();
  const climate = missingFact.baziReasoning.find(
    (item: any) => item.topic === "climate",
  );
  climate.supportRefs = climate.supportRefs.filter(
    (id: string) => !id.endsWith(".bazi.month"),
  );
  assert.throws(
    () => validateReport(missingFact, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_TOPIC_EVIDENCE",
  );
});
test("论证独有的反证和规则进入渲染附录", () => {
  const r = valid();
  const root = e.facts.find(f => f.id.endsWith(".rootDetails"))!;
  const rule = e.rules.find(f => f.id.endsWith(".R-bazi-root-review"))!;
  r.baziReasoning[0].counterRefs = [root.id];
  r.baziReasoning[0].ruleRefs.push(rule.id);
  const rendered = renderReport(r, e);
  assert(rendered.includes(`引用标识：${root.id}`));
  assert(rendered.includes(rule.guidance));
});

test("紫微模式仍检查正文候选覆盖，不依赖八字论证门禁", () => {
  const r = asZiweiOnly(valid());
  assert.throws(
    () =>
      validateReport(r, {
        ...e,
        candidateIds: [...e.candidateIds, "C2-unrepresented"],
      }),
    /每张候选|遗漏候选/,
  );
});

test("输入时间不能冒充多候选的当前体系分析覆盖", () => {
  const evidence = contextFor(
    {
      ...input,
      date: "1988-02-15",
      time: "23:00",
      timeBasis: "civil",
      uncertaintyMinutes: 2,
    },
    [2026],
  );
  assert.equal(evidence.candidateIds.length, 2);
  const [first, second] = evidence.candidateIds;
  const makeClaim = (candidate: string, topic: string) => {
    const rule = evidence.rules.find(
      (item) => item.candidate === candidate && item.id.includes("R-ziwei-"),
    )!;
    return {
      text: `候选 ${candidate} 的结构测试`,
      kind: "interpretation",
      factRefs: [...rule.factRefs],
      ruleRefs: [rule.id],
      reasoningRefs: [{
        candidate,
        topic,
      }],
      premiseStatus: "unresolved",
      conditions: "仅结构测试",
      confidence: "low",
    };
  };
  const report = reportTemplate(evidence, "ziwei") as any;
  report.timeReference = {
    asOfDate: "2026-09-25",
    timeZone: "Asia/Shanghai",
  };
  report.ziweiReasoning.forEach((item: any) => {
    const base = evidence.facts.find(
      (candidateFact) =>
        candidateFact.candidate === item.candidate &&
        candidateFact.id.endsWith(".ziwei.base"),
    )!;
    const palaceName = {
      "ziwei-structure": "命宫",
      "ziwei-career": "官禄",
      "ziwei-wealth": "财帛",
      "ziwei-relationships": "夫妻",
    }[item.topic] as string | undefined;
    const topicPalace = palaceName
      ? evidence.facts.find((candidateFact) =>
          candidateFact.candidate === item.candidate &&
          candidateFact.id.includes(".ziwei.palace-") &&
          (candidateFact.value as { name?: string }).name === palaceName
        )!
      : null;
    const ruleSuffix = {
      "ziwei-structure": ".R-ziwei-事业",
      "ziwei-career": ".R-ziwei-事业",
      "ziwei-wealth": ".R-ziwei-财运",
      "ziwei-relationships": ".R-ziwei-关系",
      "ziwei-timing": ".R-ziwei-transformations",
    }[item.topic] as string;
    const rule = evidence.rules.find(
      (candidateRule) =>
        candidateRule.candidate === item.candidate &&
        candidateRule.id.endsWith(ruleSuffix),
    )!;
    const timingRefs = item.topic === "ziwei-timing"
      ? {
          transformation: evidence.facts.find((candidateFact) =>
            candidateFact.candidate === item.candidate &&
            candidateFact.id.endsWith(".ziwei.transformations")
          )!.id,
          cycle: evidence.facts.find((candidateFact) =>
            candidateFact.candidate === item.candidate &&
            candidateFact.id.endsWith(".ziwei.cycles")
          )!.id,
          palace: evidence.facts.find((candidateFact) =>
            candidateFact.candidate === item.candidate &&
            candidateFact.id.endsWith(".ziwei.palace-0")
          )!.id,
        }
      : null;
    Object.assign(item, {
      conclusion: `${item.topic} 候选紫微结构仍需复核`,
      supportRefs: timingRefs
        ? [timingRefs.transformation, timingRefs.cycle, timingRefs.palace]
        : [base.id, topicPalace!.id],
      counterRefs: [],
      counterReview: `${item.topic} 未完成全部反证核对`,
      conditions: `${item.topic} 仅用于候选覆盖测试`,
      alternatives: `${item.topic} 保留其他解释`,
      ruleRefs: [rule.id],
      ...(timingRefs ? {
        timingChain: {
          target: "general",
          years: [...evidence.years],
          transformationRefs: [timingRefs.transformation],
          cycleRefs: [timingRefs.cycle],
          palaceRefs: [timingRefs.palace],
          crossLayerReview: "已分开本命、大限和流年层。",
          missingLinks: ["缺少现实触发资料"],
          realityBasis: {
            status: "not-provided",
            summary: "没有现实经历或目标。",
            source: null,
          },
          withdrawalConditions: "出生资料或层级定位变化时撤回。",
        },
      } : {}),
    });
  });
  report.uncertainty = "两个候选分别核对";
  report.sections = SECTION_IDS.map((id) => ({
    id,
    claims: [makeClaim(first!, ZIWEI_SECTION_TOPICS[id])],
  }));
  report.sections[0].claims[0].factRefs.push(
    evidence.facts.find(
      (fact) => fact.candidate === second && fact.id.endsWith(".input.time"),
    )!.id,
  );
  assert.throws(
    () => validateReport(report, evidence),
    /输入元数据不能代替实际分析/,
  );
  report.sections[0].claims.push(
    makeClaim(second!, ZIWEI_SECTION_TOPICS.summary),
  );
  assert.doesNotThrow(() => validateReport(report, evidence));
});

test("正文不能靠一条相关规则掩盖另一条无关规则", () => {
  const r=valid();
  r.sections[0].claims[0].ruleRefs.push(e.rules.find(x=>x.id.endsWith("R-ziwei-transformations"))!.id);
  assert.throws(()=>validateReport(r,e), /每条引用规则/);
});
test("单体系事实断言也必须遵守模式限制", () => {
  const r=valid();r.mode="bazi";r.crossSystem=[];r.ziweiReasoning=[];
  const z=e.facts.find(f=>f.system==="ziwei")!;
  r.assertions=[{factRef:z.id,value:z.value}];
  assert.throws(()=>validateReport(r,e), /事实断言引用了另一体系/);
});
test("跨体系印证不能拼接不同候选的两套命盘", () => {
  const r=valid();const z=e.facts.find(f=>f.system==="ziwei")!;
  const other={...z,id:"C-other.ziwei.base",candidate:"C-other"};
  r.crossSystem[0].factRefs=[r.crossSystem[0].factRefs[0],other.id];
  assert.throws(()=>validateReport(r,{...e,facts:[...e.facts,other]}), /不可拼盘|另一候选/);
});

test("v6 跨体系判断必须显式绑定主题和正文年份范围", () => {
  const missingTarget = valid();
  delete missingTarget.crossSystem[0].target;
  assert.throws(
    () => validateReport(missingTarget, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "CROSS_SYSTEM_SCOPE_MISMATCH",
  );

  const mismatchedYears = valid();
  mismatchedYears.crossSystem[0].years = [2026];
  assert.throws(
    () => validateReport(mismatchedYears, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "CROSS_SYSTEM_SCOPE_MISMATCH",
  );
});

test("未决前提不能升级为跨体系强关系", () => {
  const report = valid();
  report.crossSystem[0].relationship = "supports";
  assert.throws(
    () => validateReport(report, e),
    (error: unknown) =>
      error instanceof InputError &&
      error.code === "UNRESOLVED_CROSS_SYSTEM_RELATIONSHIP",
  );
});

test("跨体系强关系必须绑定声明主题的直接事实与论证", () => {
  const report = valid();
  const candidate = e.candidateIds[0]!;
  const selection = report.baziReasoning.find(
    (item: any) => item.topic === "selection",
  );
  const structure = report.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-structure",
  );
  selection.status = "conditional";
  structure.status = "conditional";
  const base = e.facts.find((fact) => fact.id.endsWith(".ziwei.base"))!;
  const lifePalace = e.facts.find(
    (fact) =>
      fact.id.includes(".ziwei.palace-") &&
      (fact.value as { name?: string }).name === "命宫",
  )!;
  report.crossSystem = [
    {
      target: "general",
      years: [],
      relationship: "supports",
      text: "两套条件性传统分析在同一综合结构问题上给出相容方向。",
      factRefs: [selection.supportRefs[0], base.id, lifePalace.id],
      reasoningRefs: [
        { candidate, topic: "selection" },
        { candidate, topic: "ziwei-structure" },
      ],
      premiseStatus: "conditional",
    },
  ];
  assert.doesNotThrow(() => validateReport(report, e));

  const unrelatedBaziFact = e.facts.find(
    (fact) =>
      fact.system === "bazi" && !selection.supportRefs.includes(fact.id),
  )!;
  report.crossSystem[0].factRefs[0] = unrelatedBaziFact.id;
  assert.throws(
    () => validateReport(report, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "CROSS_SYSTEM_SCOPE_MISMATCH",
  );
  report.crossSystem[0].factRefs[0] = selection.supportRefs[0];
  report.crossSystem[0].target = "career";
  assert.throws(
    () => validateReport(report, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "CROSS_SYSTEM_SCOPE_MISMATCH",
  );
});

test("带年份的跨体系强关系必须同时绑定两体系时间链", () => {
  const report = valid();
  const candidate = e.candidateIds[0]!;
  const baziTiming = report.baziReasoning.find(
    (item: any) => item.topic === "bazi-timing",
  );
  const timing = report.ziweiReasoning.find(
    (item: any) => item.topic === "ziwei-timing",
  );
  baziTiming.status = "conditional";
  baziTiming.timingChain.missingLinks = [];
  baziTiming.timingChain.realityBasis = {
    status: "provided",
    summary: "合成回归资料已绑定，仅用于结构校验。",
    source: "合成回归夹具",
  };
  timing.status = "conditional";
  timing.timingChain.missingLinks = [];
  timing.timingChain.realityBasis = {
    status: "provided",
    summary: "合成回归资料已绑定，仅用于结构校验。",
    source: "合成回归夹具",
  };
  const ziweiCycles = e.facts.find((fact) =>
    fact.id.endsWith(".ziwei.cycles")
  )!;
  const transformations = e.facts.find((fact) =>
    fact.id.endsWith(".ziwei.transformations")
  )!;
  report.crossSystem = [
    {
      target: "timing",
      years: [2026],
      relationship: "complements",
      text: "2026 年的两套条件性时间分析分别说明结构与作用层。",
      factRefs: [baziTiming.supportRefs[0], ziweiCycles.id, transformations.id],
      reasoningRefs: [
        { candidate, topic: "ziwei-timing" },
      ],
      premiseStatus: "conditional",
    },
  ];
  assert.throws(
    () => validateReport(report, e),
    (error: unknown) =>
      error instanceof InputError && error.code === "MISSING_REASONING_LINK",
  );

  report.crossSystem[0].reasoningRefs.unshift({
    candidate,
    topic: "bazi-timing",
  });
  assert.doesNotThrow(() => validateReport(report, e));
});

test("自动复核在用户正文后保留未由模型引用的反例及事实来源",()=>{
  const r=valid();
  assert(!r.sections.flatMap((s:any)=>s.claims.flatMap((c:any)=>c.factRefs)).some((id:string)=>id.endsWith('.wealthReview')));
  const md=renderReport(r,e);
  assert(md.indexOf('## 建议')<md.indexOf('## 核心规则复核（自动生成）'));
  assert(md.indexOf('## 核心规则复核（自动生成）')<md.indexOf('## 八字判断的依据与分歧'));
  assert(md.includes('相邻依据：年干庚（偏财）与月干甲（偏印）'));
  const f=e.facts.find(f=>f.id.endsWith('.wealthReview'))!;
  const number=e.facts.indexOf(f)+1;
  assert(md.includes(`](#fact-${number})`));assert(md.includes(`<a id="fact-${number}">`));
  assert(md.includes(`${e.candidateIds[0]}.R-bazi-wealth-review`));
});
test("纯紫微渲染不插入八字复核或其自动附录",()=>{
  const r=asZiweiOnly(valid());
  const md=renderReport(r,e);
  assert(!md.includes('核心规则复核'));assert(!md.includes('.wealthReview'));
  assert(md.includes('| 四化 |'));assert(!md.includes('| 旺衰 |'));
  assert(md.includes('<summary>查看本段命盘依据与论证主题</summary>'));
  assert(!md.includes('八字论证前提'));
  assert(md.includes('紫微论证前提'));
});

test("未决论证拒绝正文越级声称已经成立",()=>{
  const evidence=contextFor({...input,date:'2003-08-11',time:'02:00',timeBasis:'civil'},[2026]);
  const r=valid(evidence);r.sections[0].claims[0].text='故障注入：财旺生官已经成立，不必理会其他条件。';
  assert.throws(
    ()=>validateReport(r,evidence),
    (error: unknown)=>error instanceof InputError && error.code==='UNRESOLVED_PREMISE_CLAIM',
  );
});

test("完整报告自动显示同星跨层四化，并加入未主动引用的附录",()=>{
 const evidence=contextFor({...input,date:'1996-07-19',time:'09:40'},[2026,2027,2028]);
 const r=valid(evidence);const md=renderReport(r,evidence);
 assert(md.indexOf('## 建议')<md.indexOf('## 四化分层核对（自动生成）'));
 assert(md.indexOf('## 四化分层核对（自动生成）')<md.indexOf('## 八字判断的依据与分歧'));
 assert(md.includes('天同：生年化禄（本命夫妻）；大限2018—2027化忌（本命夫妻）；流年2026化禄（本命夫妻；流年宫职迁移）'));
 const f=evidence.facts.find(f=>f.id.endsWith('.ziwei.transformations'))!;
 const n=evidence.facts.indexOf(f)+1;
 assert(md.includes(`](#fact-${n})`));assert(md.includes(`<a id="fact-${n}">`));
 assert(md.includes(`${evidence.candidateIds[0]}.R-ziwei-transformations`));
});
test("纯八字报告不引入紫微自动复核，纯紫微仍保留四化复核",()=>{
 const b=valid();b.mode='bazi';b.crossSystem=[];b.ziweiReasoning=[];
 const baziMd=renderReport(b,e);
 assert(!baziMd.includes('四化分层核对'));
 assert(baziMd.includes('| 旺衰 |'));assert(!baziMd.includes('| 四化 |'));
 const z=asZiweiOnly(valid());
 const md=renderReport(z,e);assert(md.includes('四化分层核对'));assert(!md.includes('核心规则复核'));
});

test("完整报告保留真实资料与限制性说明，不能借此夹带月份预测", () => {
  const texts = [
    "目前不能判断近期是否会升职。",
    "出生日期是2000年8月16日。",
    "不能据此承诺事件或安排月份。出生日期为2000-08-16，历法为公历。",
    "出生日期为2000-08-16，无法预测下个月是否升职。",
    "你在2025年3月换过工作，这是用户提供的经历，尚未独立核验。",
  ];
  for (const text of texts) {
    const r = valid();
    r.sections[0].claims[0].text += `\n${text}`;
    const checked = validateReport(r, e);
    assert.ok(renderReport(checked, e).includes(text));
  }
  for (const text of [
    "出生日期是2000年8月17日。",
    "出生日期为2000-08-16，历法为农历。",
    "出生日期为2000-08-16，历法为公历，下个月会升职。",
    "出生日期为2000-08-16，无法预测下个月是否升职，下个月会升职。",
    "目前不能判断近期是否会升职，但是下个月会升职。",
    "不能判断近期是否升职且下个月适合跳槽。",
    "不能判断近期是否升职：下个月适合跳槽。",
    "用户称2025年3月已换工作，下个月升职，未经独立核验。",
    "用户称2025年3月已换工作、短期内升职，未经独立核验。",
    "用户称2025年3月已换工作/过段时间升职，未经独立核验。",
    "你在2025年3月换过工作，这是用户提供的经历，尚未独立核验。近期会再次升职。",
  ]) {
    const r = valid();
    r.sections[0].claims[0].text += `\n${text}`;
    assert.throws(() => validateReport(r, e), InputError);
  }
});


test("农历出生完整报告保留两种日期格式并拒绝无关非法日期", () => {
  const evidence = contextFor({ ...input, calendar: "lunar", date: "2024-02-30", leapMonth: false }, [2026]);
  for (const text of ["出生日期为农历2024-02-30。", "出生日期为农历2024年02月30日。"]) {
    const r = valid(evidence);
    r.sections[0].claims[0].text += `\n${text}`;
    assert.ok(renderReport(validateReport(r, evidence), evidence).includes(text));
  }
  const r = valid(evidence);
  r.sections[0].claims[0].text += "无法预测出生日期2027年2月30日是否升职。";
  assert.throws(() => validateReport(r, evidence), (e: unknown) => e instanceof InputError && e.code === "INVALID_NUMERIC_DATE");
});

test("报告与渲染接受完整 ISO 资料钟点，拒绝其中非法秒数", () => {
  const report = valid();
  report.uncertainty += "来源记录时刻：1991-10-17T06:58:00+08:00[Asia/Shanghai]。";
  assert.doesNotThrow(() => validateReport(report, e));
  assert.match(renderReport(report, e), /1991-10-17T06:58:00\+08:00/);
  const original = report.uncertainty;
  for (const clock of ["06:58:60", "06:60:0", "25:58:0", "06:60:000"]) {
    report.uncertainty = original.replace("06:58:00", clock);
    assert.throws(() => validateReport(report, e), (error: unknown) =>
      error instanceof InputError && error.code === "INVALID_CLOCK_TIME");
  }
});
test("v6 正文引用岁运关系事实时必须绑定同候选 bazi-timing", () => {
  const r = valid();
  validateReport(r, e);
  const candidate = e.candidateIds[0]!;
  const claim = r.sections
    .flatMap((s: { claims: { factRefs: string[]; reasoningRefs: { topic: string }[] }[] }) => s.claims)
    .find((c: { factRefs: string[]; reasoningRefs: { topic: string }[] }) =>
      c.factRefs.some((id) => id.includes(".bazi.")) &&
      !c.reasoningRefs.some((l) => l.topic === "bazi-timing"))!;
  assert(claim);
  claim.factRefs.push(`${candidate}.bazi.cycleRelations`);
  assert.throws(() => validateReport(r, e), (err: unknown) =>
    err instanceof InputError && err.code === "MISSING_REASONING_LINK" && err.message.includes("岁运关系"));
});
test("v6 正文写流月须引用对应流月事实，引用流月事实须绑定运限论证", () => {
  const m = contextFor(input, [2026], undefined, "month");
  const c = m.candidateIds[0]!;
  const base = valid(m);
  validateReport(base, m);
  const pick = (r: ReturnType<typeof valid>) =>
    r.sections
      .flatMap((s: { claims: { text: string; factRefs: string[]; reasoningRefs: { topic: string }[] }[] }) => s.claims)
      .find((cl: { factRefs: string[]; reasoningRefs: { topic: string }[] }) =>
        cl.factRefs.some((id) => id.includes(".bazi.")) &&
        !cl.reasoningRefs.some((l) => l.topic === "bazi-timing"))!;
  const labelOnly = valid(m);
  pick(labelOnly).text += "八字流月甲午另见条件。";
  assert.throws(() => validateReport(labelOnly, m), (e: unknown) =>
    e instanceof InputError && e.code === "MISSING_TOPIC_EVIDENCE" && e.message.includes("八字流月"));
  const unlinked = valid(m);
  pick(unlinked).factRefs.push(`${c}.bazi.monthlyCycles`);
  assert.throws(() => validateReport(unlinked, m), (e: unknown) =>
    e instanceof InputError && e.code === "MISSING_REASONING_LINK");
});
