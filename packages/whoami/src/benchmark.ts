import { digest } from "./chart.js";
import { object, InputError } from "./input.js";

type Question = {
  id: string;
  case_id: string;
  birth_info: Record<string, unknown>;
  question: string;
  options: { letter: string; text: string }[];
  answer: string;
  category: string;
};
export function prepareBenchmark(
  raw: unknown,
  seed = "whoami-v1",
  astroRaw?: unknown,
) {
  const body = object(raw, "benchmark");
  if (!Array.isArray(body.questions))
    throw new InputError(
      "INVALID_BENCHMARK",
      "需要 MingLi-Bench {questions: [...]}",
    );
  const ids = new Set<string>();
  const questions = body.questions.map((q0) => {
    const q = object(q0, "question");
    for (const k of ["id", "case_id", "question", "answer", "category"])
      if (typeof q[k] !== "string" || !String(q[k]).trim())
        throw new InputError("INVALID_BENCHMARK", `缺少 ${k}`);
    if (ids.has(q.id as string))
      throw new InputError("INVALID_BENCHMARK", "题目 ID 重复");
    ids.add(q.id as string);
    object(q.birth_info, "birth_info");
    if (!Array.isArray(q.options) || q.options.length < 2)
      throw new InputError("INVALID_BENCHMARK", "选项不足");
    const letters = new Set<string>();
    for (const o0 of q.options) {
      const o = object(o0, "option");
      if (
        typeof o.letter !== "string" ||
        typeof o.text !== "string" ||
        letters.has(o.letter)
      )
        throw new InputError("INVALID_BENCHMARK", "选项格式无效或字母重复");
      letters.add(o.letter);
    }
    if (!letters.has(q.answer as string))
      throw new InputError("INVALID_BENCHMARK", "答案不在选项内");
    return q as unknown as Question;
  });
  const externalCharts = new Map<string, unknown>();
  if (astroRaw !== undefined) {
    if (!Array.isArray(astroRaw))
      throw new InputError("INVALID_BENCHMARK", "--astro 必须为上游预排盘数组");
    for (const row0 of astroRaw) {
      const row = object(row0, "astro row");
      if (typeof row.case_id !== "string" || externalCharts.has(row.case_id))
        throw new InputError("INVALID_BENCHMARK", "预排盘 case_id 无效或重复");
      const response = object(row.api_response, "api_response");
      if (response.success !== true) continue;
      const data = object(
        object(response.data, "api_response.data").data,
        "chart data",
      );
      if (
        typeof data.chineseDate !== "string" ||
        !Array.isArray(data.palaces) ||
        data.palaces.length !== 12
      )
        throw new InputError("INVALID_BENCHMARK", "预排盘字段不完整");
      const palaces = data.palaces.map((p0) => {
        const p = object(p0, "palace");
        return {
          name: p.name,
          heavenlyStem: p.heavenlyStem,
          earthlyBranch: p.earthlyBranch,
          decadal: p.decadal,
          stars: ["majorStars", "minorStars"].flatMap((key) => {
            if (!Array.isArray(p[key]))
              throw new InputError("INVALID_BENCHMARK", "星曜数组缺失");
            return (p[key] as unknown[]).map((s0) => {
              const s = object(s0, "star");
              return {
                kind: key,
                name: s.name,
                brightness: s.brightness,
                mutagen: s.mutagen,
              };
            });
          }),
        };
      });
      externalCharts.set(row.case_id, {
        provenance:
          "external-chart / MingLi-Bench precomputed iztro; not whoami calculation verification",
        chineseDate: data.chineseDate,
        time: data.time,
        fiveElementsClass: data.fiveElementsClass,
        palaces,
      });
    }
  }
  const datasetHash = digest({
    questions: raw,
    externalCharts: astroRaw ?? null,
    seed,
  });
  const split = (caseId: string) =>
    parseInt(digest({ seed, caseId }).slice(0, 8), 16) % 5 === 0
      ? "holdout"
      : "development";
  const prompts = questions.map((q) => ({
    id: q.id,
    caseId: q.case_id,
    split: split(q.case_id),
    category: q.category,
    // Deliberate allowlist. Never forward arbitrary dataset fields into model inputs.
    input: {
      birthInfo: Object.fromEntries(
        [
          "raw",
          "gender",
          "year",
          "month",
          "day",
          "hour",
          "minute",
          "country",
          "location",
          "calendar_type",
        ]
          .filter((k) => k in q.birth_info)
          .map((k) => [k, q.birth_info[k]]),
      ),
      question: q.question,
      options: q.options.map((o) => ({ letter: o.letter, text: o.text })),
      ...(externalCharts.has(q.case_id)
        ? { externalChart: externalCharts.get(q.case_id) }
        : {}),
    },
    instruction:
      '按提供的信息回答选择题，只输出 {"id":"本题ID","answer":"选项字母或null","limitations":"限制"}。资料不足可弃答；不能补造经纬度、时区或真实经历。外部命盘仅用于推理评测。此题不是现实预测验证。',
  }));
  return {
    prompts: {
      schema: "whoami.benchmark-prompts.v1",
      seed,
      datasetHash,
      items: prompts,
    },
    answerKey: {
      schema: "whoami.benchmark-key.v1",
      seed,
      datasetHash,
      items: questions.map((q) => ({
        id: q.id,
        caseId: q.case_id,
        split: split(q.case_id),
        category: q.category,
        answer: q.answer,
        allowedAnswers: q.options.map((o) => o.letter),
      })),
    },
  };
}
export function scoreBenchmark(keyRaw: unknown, predRaw: unknown) {
  const key = object(keyRaw, "answer key"),
    pred = object(predRaw, "predictions");
  if (
    key.schema !== "whoami.benchmark-key.v1" ||
    !Array.isArray(key.items) ||
    !Array.isArray(pred.items)
  )
    throw new InputError("INVALID_BENCHMARK", "评分文件格式无效");
  if (pred.datasetHash !== key.datasetHash)
    throw new InputError("DATASET_MISMATCH", "预测必须绑定相同 datasetHash");
  const predictions = new Map<string, string | null>();
  const keys = key.items.map((v) => object(v, "key item"));
  const known = new Set(keys.map((k) => k.id));
  for (const p0 of pred.items) {
    const p = object(p0, "prediction");
    const k = keys.find((k) => k.id === p.id);
    if (
      typeof p.id !== "string" ||
      !known.has(p.id) ||
      predictions.has(p.id) ||
      (p.answer !== null &&
        (typeof p.answer !== "string" ||
          !Array.isArray(k?.allowedAnswers) ||
          !k.allowedAnswers.includes(p.answer)))
    )
      throw new InputError("INVALID_PREDICTION", "预测 ID/答案无效或重复");
    predictions.set(p.id, p.answer as string | null);
  }
  const summaries = ["development", "holdout"].map((split) => {
    const items = keys.filter((x) => x.split === split);
    const correct = items.filter(
      (x) => predictions.get(String(x.id)) === x.answer,
    ).length;
    const answered = items.filter(
      (x) => typeof predictions.get(String(x.id)) === "string",
    ).length;
    return {
      split,
      total: items.length,
      answered,
      correct,
      accuracy: items.length ? correct / items.length : null,
      coverage: items.length ? answered / items.length : null,
    };
  });
  return {
    schema: "whoami.benchmark-score.v1",
    datasetHash: key.datasetHash,
    summaries,
    limitation:
      "未答题计入分母；分数仅衡量本题集选择题表现，不能视为现实预测准确率。",
  };
}
