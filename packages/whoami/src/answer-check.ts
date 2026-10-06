import { InputError } from "./input.js";
import { monthlyLabels, type Evidence } from "./evidence.js";
import {
  assertNoUnresolvedPremiseUpgrade,
  assertSafeReportText,
} from "./report-safety.js";
import {
  referencedRelativeYears,
  validIsoDate,
  validateReportTemporalText,
} from "./report-time.js";
import { assertZiweiPalaceScope, scopeForText, ziweiScopes } from "./ziwei-palace-scope.js";
import { checkAnswerAudit } from "./answer-audit.js";

/**
 * 快速档纯文本答复的门禁：复用报告的高风险措辞、未决前提升级、时间表达与紫微宫位集合核对。
 * 没有结构化论证，因此不能证明解释语义正确，也不能替代完整报告的 report-check。
 */
export function checkAnswer(text: string, evidence: Evidence, asOfDate?: string, audit?: unknown) {
  if (!text.trim())
    throw new InputError("INVALID_ANSWER", "answer 文本为空");
  if (asOfDate !== undefined && !validIsoDate(asOfDate))
    throw new InputError("INVALID_ARGUMENT", "as-of 必须是有效的 YYYY-MM-DD，并按用户报告时区冻结");
  assertSafeReportText(text, "answer");
  assertNoUnresolvedPremiseUpgrade(text, "answer");
  // 相对年份缺少冻结日期时，报告层提示“迁移 v6/填写 timeReference”；快速档改为指向 --as-of。
  if (asOfDate === undefined && referencedRelativeYears(text, 2000).length)
    throw new InputError(
      "AMBIGUOUS_RELATIVE_TIME",
      "answer 使用了今年、明年等相对年份；请用 --as-of 提供按用户报告时区冻结的当天日期，或改写为明确年份",
    );
  validateReportTemporalText(
    text,
    "answer",
    evidence.years,
    asOfDate ? Number(asOfDate.slice(0, 4)) : null,
    { role: "prose", asOfDate, birth: evidence.input, monthlyLabels: monthlyLabels(evidence) },
  );
  // 多候选答复无法确定段落属于哪张盘，宫位集合不做自动核对，并在结果中明示。
  const scope = scopeForText(ziweiScopes(evidence));
  if (scope) assertZiweiPalaceScope(text, scope, "answer");
  // 断言清单在措辞与时间门禁之后核对：门禁是粗筛，清单要求逐句声明类型、把握与依据。
  const auditResult = audit === undefined ? ("not-provided" as const) : checkAnswerAudit(text, audit, evidence);
  const auditNote =
    audit === undefined
      ? "；未提供断言清单"
      : "，以及断言清单的整句覆盖、类型、依据与限定语（登记为条件性但仍写得绝对的句子只能靠限定语粗筛）";
  return {
    status: "valid" as const,
    chartId: evidence.chartId,
    evidenceId: evidence.evidenceId,
    audit: auditResult,
    palaceScope: scope ? ("checked" as const) : ("skipped-multi-candidate" as const),
    limitations: scope
      ? `仅检查高风险措辞、未决前提升级、时间表达与固定写法下的流年流月宫位集合${auditNote}；不证明解释语义正确或预测能力，也不替代完整报告的 report-check。`
      : `仅检查高风险措辞、未决前提升级与时间表达${auditNote}；多候选答复未做宫位集合核对，须人工逐候选核对。不证明解释语义正确或预测能力，也不替代完整报告的 report-check。`,
  };
}
