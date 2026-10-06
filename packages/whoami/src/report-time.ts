import { Temporal } from "@js-temporal/polyfill";
import { InputError } from "./input.js";
import { inspectLocalDateTime } from "./time.js";

const RELATIVE_YEAR_OFFSETS = new Map([
  ["今年", 0],
  ["本年", 0],
  ["明年", 1],
  ["后年", 2],
  ["去年", -1],
  ["前年", -2],
]);
const RELATIVE_YEAR_PATTERN = /(今年|本年|明年|后年|去年|前年)(?!份|度)/gu;
const RELATIVE_CYCLE_PATTERN = /(下个大限|下一大限|下一个大限)/gu;
const CALENDAR_QUALIFIED_RELATIVE_PATTERN =
  /(?:农历|阴历|夏历)(?:的)?(?:今年|本年|明年|后年|去年|前年)|(?:今年|本年|明年|后年|去年|前年)(?:按|以|的)?(?:农历|阴历|夏历)|(?:过完|过了|过)(?:春节|农历新年|立春)|(?:春节|农历新年|立春)(?:前|后|以前|以后|之前|之后)/u;
const NAMED_CALENDAR_POINT_PATTERN =
  /(?:(?:今年|本年|明年|后年|去年|前年|(?:19|20)\d{2}\s*年?)(?:春节|农历新年|立春|雨水|惊蛰|春分|清明|谷雨|立夏|小满|芒种|夏至|小暑|大暑|立秋|处暑|白露|秋分|寒露|霜降|立冬|小雪|大雪|冬至|小寒|大寒))|(?:(?:春节|农历新年|立春|雨水|惊蛰|春分|清明|谷雨|立夏|小满|芒种|夏至|小暑|大暑|立秋|处暑|白露|秋分|寒露|霜降|立冬|小雪|大雪|冬至|小寒|大寒)(?:当天|当日|那天|之日|适合|会|能|是否|如何|怎么样|怎么))/u;
const MONTHLY_LABEL_PATTERN =
  /(?:((?:19|20)\d{2})\s*年?\s*(?:的)?\s*)?(八字|紫微)?\s*流月\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])(?:\s*[（(]([^）)]*)[）)])?/gu;
/**
 * 文本中的流月标签：可选年份前缀、体系、干支与括号起止说明。报告绑定与时间门禁共用；
 * 传入 context 时与时间门禁一致，先屏蔽出生资料等非预测性说明。
 */
export function monthlyLabelMentions(text: string, context?: TemporalTextContext, label = "text") {
  const scanned = context ? nonPredictiveText(text, context, label) : text;
  return [...scanned.matchAll(MONTHLY_LABEL_PATTERN)].map((m) => ({
    source: m[0],
    year: m[1] ? Number(m[1]) : null,
    system: (m[2] ?? null) as "八字" | "紫微" | null,
    pillar: m[3]!,
    note: m[4],
  }));
}
const JIE_NAMES = "立春|惊蛰|清明|立夏|芒种|小暑|立秋|白露|寒露|立冬|大雪|小寒";
const JIE_RANGE_PATTERN = new RegExp(`(${JIE_NAMES})\\s*(?:至|到|—|–|-|~|～)\\s*(${JIE_NAMES})`, "u");
const LUNAR_MONTH_PATTERN = /(闰)?(正|一|二|三|四|五|六|七|八|九|十一|十二|十|冬|腊)月(上半|下半)?/u;
const LUNAR_MONTH_ALIASES: Record<string, string> = { 一: "正", 十一: "冬", 十二: "腊" };
const SUBANNUAL_RELATIVE_TIME_PATTERN =
  /(?:(?:今年|本年|明年|后年|去年|前年)?(?:上半年|下半年|年初|年中|年底|年末))|(?:这个月|本月|当月|下个月|下月|上个月|上月|月初|月中|月底|月末)|(?:本周|这周|下周|上周|本星期|这星期|下星期|上星期)|(?:(?:这个|这|本|当|下个?|下一|上个?|上一)季度|第?[一二三四1-4]季度|Q[1-4])|(?:(?:未来|今后|接下来)?(?:\d+|[一二三四五六七八九十两]+)(?:个)?(?:天|周|星期|个月)(?:内|以内|之内|后|以后|前|以前))/iu;
const ABSOLUTE_SUBANNUAL_TIME_PATTERN =
  /(?:(?:((?:19|20)\d{2})\s*年\s*(?:0?[1-9]|1[0-2]|正|十一|十二|一|二|三|四|五|六|七|八|九|十|冬|腊)\s*月(?:份)?(?:\s*(?:0?[1-9]|[12]\d|3[01]|初?[一二三四五六七八九十廿卅]+)\s*(?:日|号))?)|(?:(?:0?[1-9]|1[0-2])\s*月(?:份)?(?:\s*(?:0?[1-9]|[12]\d|3[01]|初?[一二三四五六七八九十廿卅]+)\s*(?:日|号))?)|(?:(?:正|十一|十二|一|二|三|四|五|六|七|八|九|十|冬|腊)\s*月\s*(?:初?[一二三四五六七八九十廿卅]+)\s*(?:日|号))|(?:(?:周|星期|礼拜)[一二三四五六日天1-7]))/gu;
const FULL_NUMERIC_DATE_PATTERN =
  /(?<![\dA-Za-z])((?:19|20)\d{2})([-/.])(\d{1,2})([-/.])(\d{1,2})(?![\dA-Za-z])/gu;
const YEARLESS_NUMERIC_DATE_PATTERN =
  /(?<![\dA-Za-z])(\d{1,2})([-/.])(\d{1,2})(?![\dA-Za-z])/gu;
const NUMERIC_CLOCK_CANDIDATE_PATTERN =
  /(?:(?<![\dA-Za-z])(?<!\d[:：])|(?<=(?:19|20)\d{2}-\d{2}-\d{2}[Tt]))(\d{1,2})[:：](\d{2})(?:[:：](\d+)(?:\.\d+)?)?(?=$|[^\dA-Za-z]|[Zz](?![\dA-Za-z]))(?![:：]\d)/gu;
const CLOCK_TIME_PATTERN =
  /(?:(?:上午|下午|早上|晚上|中午|凌晨|清晨|傍晚)\s*(?:(?:[01]?\d|2[0-3]|[一二三四五六七八九十两]+)\s*(?:点|时)(?:半|整|[0-5]?\d分?)?|(?:[01]?\d|2[0-3])[:：][0-5]\d))|(?<![\dA-Za-z])(?:[01]?\d|2[0-3])[:：][0-5]\d(?![\dA-Za-z])/gu;
const RELATIVE_DAYPART_PATTERN =
  /(?:今晚|今夜|今早|明早|明晚|明夜|明晨|(?:今天|今日|明天|后天)(?:上午|下午|早上|晚上|中午|凌晨|清晨|傍晚))/gu;
const AMBIGUOUS_TIME_ZONE_PATTERN =
  /(?<![A-Za-z])(?:CST|EST|PST|MST|IST|BST)(?![A-Za-z])|(?:北京时间|中国标准时间|美东时间|美西时间|中部时间)/gu;
const TIME_ZONE_CONTEXT_PATTERN = /(?:时区|时间|当地|日期|钟点|几点)/u;
const LOCAL_DATE_TIME_WITH_ZONE_PATTERN =
  /(?<![\dA-Za-z])((?:19|20)\d{2})-(\d{2})-(\d{2})[ T](\d{2})[:：](\d{2})(?:[:：](\d{2}))?\s+([A-Za-z_+-]+(?:\/[A-Za-z0-9._+-]+)+)(?:\s+(earlier|later))?(?![A-Za-z])/giu;
const OFFSET_ZONED_DATE_TIME_PATTERN =
  /(?<![\dA-Za-z])((?:19|20)\d{2})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?([+-]\d{2}:\d{2})\[([A-Za-z_+-]+(?:\/[A-Za-z0-9._+-]+)+)\](?![A-Za-z])/giu;
const ABSOLUTE_INSTANT_PATTERN =
  /(?<![\dA-Za-z])((?:19|20)\d{2})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.\d{1,9})?)?(?:Z|[+-]\d{2}:\d{2})(?![\dA-Za-z\[])/giu;
const TIME_COMPARISON_CONTEXT_PATTERN =
  /(?:哪个|哪一个|哪次|哪种|哪段|两者|二者|两个(?:区间|时段|时间段|窗口)|分别|对比|比较|还是|二选一|更适合|更好|优先选|选择哪)/u;
const TIME_EQUIVALENCE_ACK_PATTERN =
  /(?:(?:同一|相同)(?:个|一)?(?:绝对)?(?:时刻|瞬间))|(?:(?:时刻|瞬间)(?:相同|一致))|(?:等价(?:时刻|表达|关系)?)/u;
const TIME_INTERVAL_CONNECTOR_PATTERN =
  /^[\s`'"“”‘’（）()\[\]]*(?:到|至|—|–|~|～|-)[\s`'"“”‘’（）()\[\]]*$/u;
const TIME_INTERVAL_EQUIVALENCE_ACK_PATTERN =
  /(?:(?:同一|相同|等价)(?:个|一)?(?:时间)?(?:区间|时段|时间段|窗口))|(?:(?:区间|时段|时间段|窗口)(?:相同|一致|等价))/u;
const TIME_INTERVAL_OVERLAP_ACK_PATTERN =
  /(?:(?:存在|有|部分|彼此|两者|二者)?重叠)|(?:存在|有)?交集/u;
const OPEN_ENDED_TIME_SUFFIX_PATTERN =
  /^[\s`'"“”‘’（）()\[\]]*(?:之后|以后|之前|以前|起(?:算)?|开始)/u;
const OPEN_ENDED_TIME_PREFIX_PATTERN =
  /(?:截至|截止(?:到)?|不早于|不晚于|早于|晚于)[\s`'"“”‘’（）()\[\]]*$/u;
const TIME_INTERVAL_DURATION_PATTERN =
  /(?:实际(?:经过|历时|时长(?:为)?)|经过|历时|持续|时长(?:为)?|共计?|合计)\s*(?:(\d{1,6})\s*(?:小时|时)(?:\s*(\d{1,3})\s*(?:分钟|分))?|(\d{1,8})\s*(?:分钟|分))/gu;
const RECURRENCE_PATTERN =
  /(?:每天|每日|每个工作日|每周(?:[一二三四五六日天1-7])?|每星期(?:[一二三四五六日天1-7])?|每月(?:[0-3]?\d(?:日|号)?)?|每年|隔天|每隔(?:\d+|[一二三四五六七八九十百两]+)(?:天|周|个月|月))/gu;
const IANA_TIME_ZONE_TOKEN_PATTERN =
  /(?:\[[A-Za-z_+-]+(?:\/[A-Za-z0-9._+-]+)+\])|(?:[A-Za-z_+-]+(?:\/[A-Za-z0-9._+-]+)+)/u;
const RECURRENCE_TIME_ZONE_BINDING_PATTERN =
  /(?:(?:按|以|采用|使用)\s*(?:时区\s*)?[A-Za-z_+-]+(?:\/[A-Za-z0-9._+-]+)+)|(?:[A-Za-z_+-]+(?:\/[A-Za-z0-9._+-]+)+\s*(?:当地|时区))/u;
const TIME_DECISION_CONTEXT_PATTERN =
  /(?:适合|合适|会|能|是否|可否|可以|应该|要不要|如何|怎么样|怎么|哪个|哪段|选择哪|更好|结果|事业|财运|关系|运势|升职|加薪|跳槽|行动|联系|面试|签约|入职|离职|投资|结婚|复合|机会|窗口|吉凶|吉日|凶日|吉时|凶时|最佳|判断|预测|发生|出现|必然|一定|必成|成功|失败|有利|不利)/u;
const MULTIYEAR_RELATIVE_RANGE_PATTERN =
  /(?:(?:未来|今后|接下来|往后)(?:[1-9]\d?|[一二三四五六七八九十两]+|数|若干)(?:个)?年(?:内|以内|之内)?)|(?:(?:[1-9]\d?|[一二三四五六七八九十两]+|数|若干)(?:个)?年(?:内|以内|之内|后|以后|前|以前))|(?:这几年(?:来)?|近几年|最近几年|未来几年(?:内)?|今后几年(?:内)?|接下来几年(?:内)?|往后几年(?:内)?)|(?:(?:中长期|长期|长远)(?:内|来看|看|会|能|是否|如何|怎么样|怎么|判断|趋势|发展|规划|事业|财运|关系|运势))/u;
const VAGUE_TIME_HORIZON_PATTERN =
  /(?:近期|不久(?:前|后)?|很快|(?:再)?过(?:一)?(?:阵子|段时间)|什么时候|何时|几时|短期内|未来一段时间|接下来一段时间)/u;
const EXPLICIT_ANNUAL_RANGE_PATTERN =
  /((?:19|20)\d{2})\s*(?:-|–|—|~|～|至)\s*((?:19|20)\d{2})\s*(?:年|年度)/gu;
export function referencedRelativeYears(text: string, referenceYear: number | null) {
  if (referenceYear === null) return [];
  return [...new Set(
    [...text.matchAll(RELATIVE_YEAR_PATTERN)].map(
      (match) => referenceYear + RELATIVE_YEAR_OFFSETS.get(match[0])!,
    ),
  )].sort((a, b) => a - b);
}
function validGregorianDate(year: number, month: number, day: number) {
  const date = new Date(Date.UTC(year, month - 1, day));
  return (
    date.getUTCFullYear() === year &&
    date.getUTCMonth() === month - 1 &&
    date.getUTCDate() === day
  );
}
export function validIsoDate(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/u.exec(value);
  if (!match) return false;
  return validGregorianDate(
    Number(match[1]),
    Number(match[2]),
    Number(match[3]),
  );
}
function ianaTimeZoneToken(value: string) {
  const match = IANA_TIME_ZONE_TOKEN_PATTERN.exec(value);
  return match ? match[0].replace(/^\[|\]$/gu, "") : null;
}
function numericPlainDateTime(
  match: RegExpMatchArray,
  label: string,
): Temporal.PlainDateTime {
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const hour = Number(match[4]);
  const minute = Number(match[5]);
  const second = match[6] === undefined ? 0 : Number(match[6]);
  if (!validGregorianDate(year, month, day))
    throw new InputError(
      "INVALID_NUMERIC_DATE",
      `${label} 使用了无效公历日期“${match[0]}”`,
    );
  if (hour > 23 || minute > 59 || second > 59)
    throw new InputError(
      "INVALID_CLOCK_TIME",
      `${label} 使用了无效钟点“${match[0]}”；小时须为 00—23，分秒须为 00—59`,
    );
  return Temporal.PlainDateTime.from({ year, month, day, hour, minute, second });
}
type TemporalTextContext = {
  role?: "prose" | "title" | "reality-source";
  /** evidence 中实际存在的流月标签（如“八字流月壬午”“紫微流月癸未”）；年度 evidence 为 undefined。 */
  monthlyLabels?: Map<string, { year: number; range: string }[]>;
  asOfDate?: string;
  birth?: { calendar: "solar" | "lunar"; date: string; leapMonth: boolean };
};

const CHINESE_DATE = /((?:19|20)\d{2})年\s*(\d{1,2})月(?:\s*(\d{1,2})[日号])?/gu;
const CONTRAST_OR_INFERENCE = /但是|但|然而|不过|可是|却|反而|因此|所以|说明|意味着|证明|可见|从而|必然|一定|肯定|保证|注定|将会|将要|且|并|而|又|同时|随后|然后|接着|此外|另外|[:：]/u;
const BIRTH_STATEMENT = /^(?:你的|本次)?出生日期(?:是|为|[:：])\s*(公历|农历)?\s*((?:19|20)\d{2})(?:年|-)(闰)?(\d{1,2})(?:月|-)(\d{1,2})(?:日|号)?$/u;
const LIMITATION_STATEMENT = /^(?:目前|现阶段|现在)?(?:尚不能|不能|无法|尚无法|尚不足以)(?:判断|预测|确定|断言)(?:(?:近期|不久|很快|短期内|下个月|本月|这个月|下周|今年|明年|后年|(?:19|20)\d{2}年(?:\d{1,2}月(?:\d{1,2}[日号])?)?)(?:是否|能否)(?:会|能够)?(?:升职|加薪|跳槽|入职|离职|结婚|复合|成功|失败)|(?:什么时候|何时|几时)(?:会|能)?(?:升职|加薪|跳槽|入职|离职|结婚|复合|成功|失败)|(?:近期|不久|很快|短期内|下个月|本月|这个月|下周)的(?:结果|运势|情况))$/u;

function matchingBirthStatement(text: string, context: TemporalTextContext, label: string) {
  const birth = BIRTH_STATEMENT.exec(text.trim());
  if (!birth || !context.birth) return false;
  const calendar = birth[1] === "农历" ? "lunar" : "solar";
  if (calendar === "solar" && !validGregorianDate(Number(birth[2]), Number(birth[4]), Number(birth[5])))
    throw new InputError("INVALID_NUMERIC_DATE", `${label} 使用了无效公历出生日期`);
  const date = `${birth[2]}-${birth[4]!.padStart(2, "0")}-${birth[5]!.padStart(2, "0")}`;
  if (calendar !== context.birth.calendar || date !== context.birth.date ||
      Boolean(birth[3]) !== context.birth.leapMonth)
    throw new InputError("FACT_MISMATCH", `${label} 的出生日期或历法与当前输入不一致`);
  return true;
}

// Mask only narrowly recognized statements, retaining offsets for the checks below.
// A disclaimer never exempts adjacent clauses or the original date/time validation.
function nonPredictiveText(
  text: string,
  context: TemporalTextContext,
  label: string,
) {
  const mask = (value: string) => value.replace(/[^\r\n]/g, " ");
  return text.replace(/[^。！？；\n]+/gu, (sentence) => {
    const trimmed = sentence.trim();
    let hasBirthStatement = false;
    const birthText = sentence.replace(/[^，,]+/gu, (clause) => {
      if (!matchingBirthStatement(clause, context, label)) return clause;
      hasBirthStatement = true;
      return mask(clause);
    });
    if (hasBirthStatement) {
      for (const clause of sentence.split(/[，,]/u)) {
        const calendar = /^历法(?:是|为)(公历|农历)$/u.exec(clause.trim());
        if (calendar && (calendar[1] === "农历" ? "lunar" : "solar") !== context.birth?.calendar)
          throw new InputError("FACT_MISMATCH", `${label} 的历法说明与当前出生输入不一致`);
      }
    }
    // Attribution and uncertainty belong to the same sentence. No inference or
    // future assertion is admitted, even when it is attributed to the user.
    const historical = /^(?:(?:你|用户|命主|我)在([^，,]+)[，,](?:这是)?用户(?:提供的经历|本轮陈述|自述)[，,](?:尚未|未经|尚未经)独立核验|用户(?:自述|称|表示)[:：]?\s*([^，,]+)[，,](?:尚未|未经|尚未经)独立核验)$/u.exec(trimmed);
    if (historical && context.asOfDate && validIsoDate(context.asOfDate)) {
      const body = (historical[1] ?? historical[2])!;
      const date = /^((?:19|20)\d{2})(?:年|-)(\d{1,2})(?:月(?:([0-3]?\d)[日号])?|-(\d{1,2}))(.+)$/u.exec(body);
      if (date && !CONTRAST_OR_INFERENCE.test(body) &&
          !/会|将|可能|能够|可以|应当|应该|适合|有利|不利|预计|未来|运势|命盘/u.test(date[5]!) &&
          /过|曾|已/u.test(date[5]!)) {
        const year = Number(date[1]), month = Number(date[2]);
        const dayText = date[3] ?? date[4];
        const day = dayText ? Number(dayText) : 1;
        if (!validGregorianDate(year, month, day))
          throw new InputError("INVALID_NUMERIC_DATE", `${label} 的历史日期无效`);
        const historicalEnd = dayText
          ? `${date[1]}-${date[2]!.padStart(2, "0")}-${dayText.padStart(2, "0")}`
          : `${date[1]}-${date[2]!.padStart(2, "0")}-${new Date(Date.UTC(year, month, 0)).getUTCDate()}`;
        if (historicalEnd < context.asOfDate) {
          // Exempt only the bound historical date. Leave the event text and any
          // second time expression visible to every existing temporal guard.
          const token = body.slice(0, body.length - date[5]!.length);
          const start = sentence.indexOf(body);
          return sentence.slice(0, start) + mask(token) + sentence.slice(start + token.length);
        }
      }
    }
    return birthText.replace(/[^，,]+/gu, (clause) => {
      const value = clause.trim();
      if (!CONTRAST_OR_INFERENCE.test(value) &&
          LIMITATION_STATEMENT.test(value))
        return mask(clause);
      return clause;
    });
  });
}

export function validateReportTemporalText(
  text: string,
  label: string,
  evidenceYears: number[],
  referenceYear: number | null,
  context?: TemporalTextContext,
) {
  // Only a complete, input-matched lunar birth statement can change calendar
  // interpretation. A masked disclaimer or nearby word is not a calendar tag.
  const lunarBirthRanges = context?.birth?.calendar === "lunar"
    ? [...text.matchAll(/[^，,。！？；\n]+/gu)]
      .filter((sentence) => matchingBirthStatement(sentence[0], context, label))
      .map((sentence) => ({ start: sentence.index, end: sentence.index + sentence[0].length }))
    : [];
  const isExactLunarBirth = (index: number, length: number) =>
    lunarBirthRanges.some((range) => range.start <= index && range.end >= index + length);
  const resolvedTextInstants: Array<{
    source: string;
    instant: string;
    index: number;
    length: number;
  }> = [];
  const localContext = (index: number, length: number) =>
    text.slice(
      Math.max(0, index - 18),
      Math.min(text.length, index + length + 18),
    );
  const hasDecisionContext = (index: number, length: number) =>
    TIME_DECISION_CONTEXT_PATTERN.test(localContext(index, length));
  const calendarQualified = CALENDAR_QUALIFIED_RELATIVE_PATTERN.exec(text);
  if (calendarQualified)
    throw new InputError(
      "AMBIGUOUS_RELATIVE_TIME",
      `${label} 使用了未建模的历法限定时间“${calendarQualified[0]}”；请先改写为明确公历年份及对应体系年界`,
    );
  const namedCalendarPoint = NAMED_CALENDAR_POINT_PATTERN.exec(text);
  if (namedCalendarPoint)
    throw new InputError(
      "UNSUPPORTED_CALENDAR_POINT",
      `${label} 使用了未进入 evidence 的历法时点“${namedCalendarPoint[0]}”；请先明确对应公历日期、历法与时区口径，再接入相应日级证据`,
    );
  const fullNumericDates = [...text.matchAll(FULL_NUMERIC_DATE_PATTERN)];
  for (const numericDate of fullNumericDates) {
    if (isExactLunarBirth(numericDate.index, numericDate[0].length)) continue;
    const year = Number(numericDate[1]);
    const month = Number(numericDate[3]);
    const day = Number(numericDate[5]);
    if (
      numericDate[2] !== numericDate[4] ||
      !validGregorianDate(year, month, day)
    )
      throw new InputError(
        "INVALID_NUMERIC_DATE",
        `${label} 使用了无效或分隔符不一致的数字日期“${numericDate[0]}”；请先改为真实存在且格式一致的公历日期`,
      );
  }
  const yearlessNumericDates = [
    ...text.matchAll(YEARLESS_NUMERIC_DATE_PATTERN),
  ].filter((numericDate) => {
    const before = text.slice(
      Math.max(0, numericDate.index - 5),
      numericDate.index,
    );
    const after = text.slice(
      numericDate.index + numericDate[0].length,
      numericDate.index + numericDate[0].length + 1,
    );
    return (
      !/(?:19|20)\d{2}[-/.]$/u.test(before) &&
      !(before.endsWith(":") && after === ":")
    );
  });
  for (const numericDate of yearlessNumericDates) {
    if (!hasDecisionContext(numericDate.index, numericDate[0].length))
      continue;
    const left = Number(numericDate[1]);
    const right = Number(numericDate[3]);
    const monthDay = validGregorianDate(2000, left, right);
    const dayMonth = validGregorianDate(2000, right, left);
    if (!monthDay && !dayMonth)
      throw new InputError(
        "INVALID_NUMERIC_DATE",
        `${label} 使用了不存在的无年份数字日期“${numericDate[0]}”；请先提供真实存在的公历日期`,
      );
    if (monthDay && dayMonth && left !== right)
      throw new InputError(
        "AMBIGUOUS_NUMERIC_DATE",
        `${label} 使用了月日顺序不唯一的数字日期“${numericDate[0]}”；请改写为带四位年份的 YYYY-MM-DD`,
      );
  }
  for (const clockTime of text.matchAll(NUMERIC_CLOCK_CANDIDATE_PATTERN)) {
    const hour = Number(clockTime[1]);
    const minute = Number(clockTime[2]);
    const second = clockTime[3] === undefined ? 0 : Number(clockTime[3]);
    if (hour > 23 || minute > 59 || second > 59 ||
        (clockTime[3] !== undefined && clockTime[3].length !== 2))
      throw new InputError(
        "INVALID_CLOCK_TIME",
        `${label} 使用了无效钟点“${clockTime[0]}”；小时须为 00—23，分秒须为 00—59，秒整数部分须为两位`,
      );
  }
  for (const timeZone of text.matchAll(AMBIGUOUS_TIME_ZONE_PATTERN)) {
    const context = localContext(timeZone.index, timeZone[0].length);
    if (
      !TIME_DECISION_CONTEXT_PATTERN.test(context) &&
      !TIME_ZONE_CONTEXT_PATTERN.test(context)
    )
      continue;
    throw new InputError(
      "AMBIGUOUS_TIME_ZONE",
      `${label} 使用了不能唯一绑定规则的时区缩写或口语标签“${timeZone[0]}”；请改用明确的 IANA 时区`,
    );
  }
  for (const localDateTime of text.matchAll(
    LOCAL_DATE_TIME_WITH_ZONE_PATTERN,
  )) {
    const timeZone = localDateTime[7]!;
    const plain = numericPlainDateTime(localDateTime, label);
    let resolution;
    try {
      resolution = inspectLocalDateTime(plain, timeZone);
    } catch {
      throw new InputError(
        "INVALID_TIMEZONE",
        `${label} 使用了无法识别的 IANA 时区“${timeZone}”`,
      );
    }
    if (resolution.status === "nonexistent")
      throw new InputError(
        "NONEXISTENT_LOCAL_TIME",
        `${label} 使用了因时区跳变而不存在的当地时刻“${localDateTime[0]}”；earlier/later 不能把缺失时间变成真实时刻`,
      );
    if (
      resolution.status === "ambiguous" &&
      localDateTime[8] === undefined
    )
      throw new InputError(
        "AMBIGUOUS_LOCAL_TIME",
        `${label} 使用了时区回拨期间重复的当地时刻“${localDateTime[0]}”；请明确 earlier 或 later 分支`,
      );
    const selected =
      resolution.status === "ambiguous"
        ? resolution[localDateTime[8]!.toLowerCase() as "earlier" | "later"]
        : resolution.value;
    resolvedTextInstants.push({
      source: localDateTime[0],
      instant: selected.toInstant().toString(),
      index: localDateTime.index,
      length: localDateTime[0].length,
    });
  }
  for (const offsetDateTime of text.matchAll(
    OFFSET_ZONED_DATE_TIME_PATTERN,
  )) {
    const offset = offsetDateTime[7]!;
    const timeZone = offsetDateTime[8]!;
    const plain = numericPlainDateTime(offsetDateTime, label);
    let resolution;
    try {
      resolution = inspectLocalDateTime(plain, timeZone);
    } catch {
      throw new InputError(
        "INVALID_TIMEZONE",
        `${label} 使用了无法识别的 IANA 时区“${timeZone}”`,
      );
    }
    if (resolution.status === "nonexistent")
      throw new InputError(
        "NONEXISTENT_LOCAL_TIME",
        `${label} 使用了因时区跳变而不存在的当地时刻“${offsetDateTime[0]}”；显式 UTC offset 不能把缺失时间变成真实时刻`,
      );
    const allowedOffsets =
      resolution.status === "ambiguous"
        ? [resolution.earlier.offset, resolution.later.offset]
        : [resolution.value.offset];
    if (!allowedOffsets.includes(offset))
      throw new InputError(
        "OFFSET_TIME_ZONE_MISMATCH",
        `${label} 的 UTC offset“${offset}”与“${timeZone}”在该当地时刻的规则不一致；可复算 offset 为 ${allowedOffsets.join(" 或 ")}`,
      );
    const selected =
      resolution.status === "ambiguous"
        ? resolution.earlier.offset === offset
          ? resolution.earlier
          : resolution.later
        : resolution.value;
    resolvedTextInstants.push({
      source: offsetDateTime[0],
      instant: selected.toInstant().toString(),
      index: offsetDateTime.index,
      length: offsetDateTime[0].length,
    });
  }
  for (const absoluteTime of text.matchAll(ABSOLUTE_INSTANT_PATTERN)) {
    numericPlainDateTime(absoluteTime, label);
    let instant: Temporal.Instant;
    try {
      instant = Temporal.Instant.from(absoluteTime[0]);
    } catch {
      throw new InputError(
        "INVALID_ABSOLUTE_TIME",
        `${label} 使用了无法解析的绝对时刻“${absoluteTime[0]}”`,
      );
    }
    resolvedTextInstants.push({
      source: absoluteTime[0],
      instant: instant.toString(),
      index: absoluteTime.index,
      length: absoluteTime[0].length,
    });
  }
  const orderedResolvedInstants = [...resolvedTextInstants].sort(
    (left, right) => left.index - right.index,
  );
  const intervalLinks = orderedResolvedInstants
    .slice(0, -1)
    .map((left, index) => {
      const right = orderedResolvedInstants[index + 1]!;
      return TIME_INTERVAL_CONNECTOR_PATTERN.test(
        text.slice(left.index + left.length, right.index),
      );
    });
  if (intervalLinks.some((linked, index) => linked && intervalLinks[index + 1]))
    throw new InputError(
      "AMBIGUOUS_TIME_INTERVAL",
      `${label} 使用了连续多个端点的时间区间；请把每个候选明确写成独立的“开始时刻至结束时刻”`,
    );
  const resolvedIntervals: Array<{
    start: (typeof resolvedTextInstants)[number];
    end: (typeof resolvedTextInstants)[number];
  }> = [];
  const intervalMemberKeys = new Set<string>();
  for (let index = 0; index < intervalLinks.length; index += 1) {
    if (!intervalLinks[index]) continue;
    const start = orderedResolvedInstants[index]!;
    const end = orderedResolvedInstants[index + 1]!;
    const ordering = Temporal.Instant.compare(start.instant, end.instant);
    if (ordering === 0)
      throw new InputError(
        "ZERO_LENGTH_TIME_INTERVAL",
        `${label} 的时间区间“${start.source} 至 ${end.source}”起止为同一绝对时刻；请提供正时长区间`,
      );
    if (ordering > 0)
      throw new InputError(
        "REVERSED_TIME_INTERVAL",
        `${label} 的时间区间“${start.source} 至 ${end.source}”起点晚于终点；请按时间先后重写`,
      );
    resolvedIntervals.push({ start, end });
    intervalMemberKeys.add(`${start.index}:${start.length}`);
    intervalMemberKeys.add(`${end.index}:${end.length}`);
    index += 1;
  }
  for (const resolved of resolvedTextInstants) {
    if (intervalMemberKeys.has(`${resolved.index}:${resolved.length}`))
      continue;
    const prefix = text.slice(Math.max(0, resolved.index - 14), resolved.index);
    const suffix = text.slice(
      resolved.index + resolved.length,
      Math.min(text.length, resolved.index + resolved.length + 14),
    );
    if (
      (OPEN_ENDED_TIME_PREFIX_PATTERN.test(prefix) ||
        OPEN_ENDED_TIME_SUFFIX_PATTERN.test(suffix)) &&
      hasDecisionContext(resolved.index, resolved.length)
    )
      throw new InputError(
        "OPEN_ENDED_TIME_INTERVAL",
        `${label} 使用了只有单侧边界的时间范围“${resolved.source}”；请同时提供可复算的开始和结束时刻`,
      );
  }
  const durationBindings = new Set<number>();
  for (const duration of text.matchAll(TIME_INTERVAL_DURATION_PATTERN)) {
    if (resolvedIntervals.length === 0) continue;
    let intervalIndex = -1;
    for (let index = 0; index < resolvedIntervals.length; index += 1) {
      const interval = resolvedIntervals[index]!;
      if (interval.end.index + interval.end.length <= duration.index)
        intervalIndex = index;
    }
    if (intervalIndex < 0 || durationBindings.has(intervalIndex))
      throw new InputError(
        "AMBIGUOUS_TIME_INTERVAL_DURATION",
        `${label} 的时长“${duration[0]}”无法唯一绑定到前方一个时间区间；请把时长紧跟在对应区间之后并逐段标明`,
      );
    durationBindings.add(intervalIndex);
    const hours = duration[1] === undefined ? 0n : BigInt(duration[1]);
    const minutes = duration[2] === undefined ? 0n : BigInt(duration[2]);
    const minuteOnly = duration[3] === undefined ? 0n : BigInt(duration[3]);
    if (minutes >= 60n)
      throw new InputError(
        "INVALID_TIME_INTERVAL_DURATION",
        `${label} 的组合时长“${duration[0]}”中分钟须为 0—59；也可改写为总分钟数`,
      );
    const declaredMinutes =
      duration[3] === undefined ? hours * 60n + minutes : minuteOnly;
    const interval = resolvedIntervals[intervalIndex]!;
    const start = Temporal.Instant.from(interval.start.instant);
    const end = Temporal.Instant.from(interval.end.instant);
    const actualNanoseconds = end.epochNanoseconds - start.epochNanoseconds;
    const declaredNanoseconds = declaredMinutes * 60_000_000_000n;
    if (actualNanoseconds !== declaredNanoseconds) {
      const actualSeconds = actualNanoseconds / 1_000_000_000n;
      const actualDescription =
        actualSeconds % 3600n === 0n
          ? `${actualSeconds / 3600n} 小时`
          : actualSeconds % 60n === 0n
            ? `${actualSeconds / 60n} 分钟`
            : `${actualSeconds} 秒`;
      throw new InputError(
        "TIME_INTERVAL_DURATION_MISMATCH",
        `${label} 声明的时长“${duration[0]}”与绝对时刻之间实际经过的 ${actualDescription} 不一致；跨 DST 时须按 instant 差计算真实经过时长`,
      );
    }
  }
  for (const recurrence of text.matchAll(RECURRENCE_PATTERN)) {
    if (!hasDecisionContext(recurrence.index, recurrence[0].length)) continue;
    if (resolvedIntervals.length === 0)
      throw new InputError(
        "RECURRENCE_RANGE_REQUIRED",
        `${label} 的重复日程“${recurrence[0]}”没有可复算的绝对起止范围；请先提供完整时间区间`,
      );
    const intervalHasConsistentIanaTimeZone = resolvedIntervals.some(
      ({ start, end }) => {
        const startTimeZone = ianaTimeZoneToken(start.source);
        const endTimeZone = ianaTimeZoneToken(end.source);
        return startTimeZone !== null && startTimeZone === endTimeZone;
      },
    );
    const recurrenceContext = text.slice(
      Math.max(0, recurrence.index - 48),
      Math.min(text.length, recurrence.index + recurrence[0].length + 48),
    );
    if (
      !intervalHasConsistentIanaTimeZone &&
      !RECURRENCE_TIME_ZONE_BINDING_PATTERN.test(recurrenceContext)
    )
      throw new InputError(
        "RECURRENCE_TIME_ZONE_REQUIRED",
        `${label} 的重复日程“${recurrence[0]}”没有与绝对范围一致或在日程附近明确绑定的 IANA 时区；固定 UTC offset 与无关资料时区不能替代跨日期的地区时区规则`,
      );
    throw new InputError(
      "UNSUPPORTED_RECURRENCE_GRANULARITY",
      `${label} 的重复日程“${recurrence[0]}”尚未展开为逐次 occurrence evidence；当前年度 evidence 不能生成每天、每周或每月的具体事件判断`,
    );
  }
  const comparesTimeIntervals =
    resolvedIntervals.length > 1 &&
    TIME_COMPARISON_CONTEXT_PATTERN.test(text);
  const duplicateInterval = resolvedIntervals.find((interval, index) =>
    resolvedIntervals.slice(index + 1).some(
      (candidate) =>
        candidate.start.instant === interval.start.instant &&
        candidate.end.instant === interval.end.instant,
    ),
  );
  if (
    duplicateInterval &&
    comparesTimeIntervals &&
    !TIME_INTERVAL_EQUIVALENCE_ACK_PATTERN.test(text)
  )
    throw new InputError(
      "DUPLICATE_TIME_INTERVAL",
      `${label} 把不同写法归一化后相同的时间区间当成多个候选；该区间实际为 ${duplicateInterval.start.instant} 至 ${duplicateInterval.end.instant}，请合并为一个候选`,
    );
  let overlappingIntervals:
    | [
        (typeof resolvedIntervals)[number],
        (typeof resolvedIntervals)[number],
      ]
    | null = null;
  for (let leftIndex = 0; leftIndex < resolvedIntervals.length; leftIndex += 1) {
    const left = resolvedIntervals[leftIndex]!;
    for (
      let rightIndex = leftIndex + 1;
      rightIndex < resolvedIntervals.length;
      rightIndex += 1
    ) {
      const right = resolvedIntervals[rightIndex]!;
      if (
        left.start.instant === right.start.instant &&
        left.end.instant === right.end.instant
      )
        continue;
      if (
        Temporal.Instant.compare(left.start.instant, right.end.instant) < 0 &&
        Temporal.Instant.compare(right.start.instant, left.end.instant) < 0
      ) {
        overlappingIntervals = [left, right];
        break;
      }
    }
    if (overlappingIntervals) break;
  }
  if (
    overlappingIntervals &&
    comparesTimeIntervals &&
    !TIME_INTERVAL_OVERLAP_ACK_PATTERN.test(text)
  )
    throw new InputError(
      "OVERLAPPING_TIME_INTERVAL",
      `${label} 把含正时长交集的两个时间区间当成独立候选；请先明确重叠关系，或拆成互不重叠的窗口`,
    );
  const instantsByValue = new Map<string, typeof resolvedTextInstants>();
  for (const resolved of resolvedTextInstants.filter(
    (entry) => !intervalMemberKeys.has(`${entry.index}:${entry.length}`),
  )) {
    const entries = instantsByValue.get(resolved.instant) ?? [];
    entries.push(resolved);
    instantsByValue.set(resolved.instant, entries);
  }
  const duplicateInstant = [...instantsByValue.entries()].find(
    ([, entries]) => entries.length > 1,
  );
  if (
    duplicateInstant &&
    TIME_COMPARISON_CONTEXT_PATTERN.test(text) &&
    !TIME_EQUIVALENCE_ACK_PATTERN.test(text)
  )
    throw new InputError(
      "DUPLICATE_ABSOLUTE_TIME",
      `${label} 把 ${duplicateInstant[1].map((entry) => `“${entry.source}”`).join(" 与 ")} 当成不同候选比较，但它们都对应 ${duplicateInstant[0]}；请合并为同一绝对时刻`,
    );
  for (const resolved of resolvedTextInstants) {
    if (!hasDecisionContext(resolved.index, resolved.length)) continue;
    throw new InputError(
      "UNSUPPORTED_TIME_GRANULARITY",
      `${label} 把绝对时刻“${resolved.source}”用于当前年度 evidence 不支持的具体时点判断；请先接入对应日级和小时级证据`,
    );
  }
  const granularityText = context ? nonPredictiveText(text, context, label) : text;
  for (const match of text.matchAll(CHINESE_DATE)) {
    const exactLunarBirth = isExactLunarBirth(match.index, match[0].length);
    if (!exactLunarBirth && !validGregorianDate(Number(match[1]), Number(match[2]), Number(match[3] ?? 1)))
      throw new InputError("INVALID_NUMERIC_DATE", `${label} 使用了无效公历日期“${match[0]}”`);
  }
  // 月度只接受带体系与干支的流月标签，并须在 evidence 中真实存在；公历月、相对月仍按下方规则拒绝。
  // 与其他细分时间一致，只检查屏蔽了出生资料等非预测性说明后的文本。
  for (const month of monthlyLabelMentions(granularityText)) {
    if (!context?.monthlyLabels)
      throw new InputError(
        "UNSUPPORTED_TIME_GRANULARITY",
        `${label} 使用了流月“${month.source}”，但当前 evidence 只到年度；请用 --granularity month 重新计算后再引用流月`,
      );
    if (!month.system)
      throw new InputError(
        "AMBIGUOUS_MONTH_SYSTEM",
        `${label} 的“${month.source}”未写明体系；八字按节、紫微按农历月，边界不同，须写成“八字流月${month.pillar}”或“紫微流月${month.pillar}”`,
      );
    const tag = `${month.system}流月${month.pillar}`;
    const all = context.monthlyLabels.get(tag) ?? [];
    const entries = month.year === null ? all : all.filter((e) => e.year === month.year);
    if (!entries.length)
      throw new InputError(
        "MONTH_NOT_IN_EVIDENCE",
        `${label} 的“${month.year ?? ""}${month.year ? "年" : ""}${tag}”不在当前 evidence 的流月中；请核对体系、干支与请求年份`,
      );
    // 干支每五年重复；evidence 含多个同名流月时须写明年份。
    if (month.year === null && new Set(entries.map((e) => e.year)).size > 1)
      throw new InputError(
        "AMBIGUOUS_MONTH_YEAR",
        `${label} 的“${tag}”在 ${[...new Set(entries.map((e) => e.year))].join("、")} 年都有，请写明年份`,
      );
    // 标签后括号中的起止说明须与 evidence 一致：八字核对起止节，紫微核对农历月名。
    if (month.note === undefined) continue;
    let stated: string | null = null;
    if (month.system === "八字") {
      const jie = JIE_RANGE_PATTERN.exec(month.note);
      if (jie) stated = `${jie[1]}至${jie[2]}`;
    } else {
      const lunar = LUNAR_MONTH_PATTERN.exec(month.note);
      if (lunar)
        stated = `${lunar[1] ?? ""}${LUNAR_MONTH_ALIASES[lunar[2]!] ?? lunar[2]}月${lunar[3] ?? ""}`;
    }
    const ranges = entries.map((e) => e.range);
    if (
      stated !== null &&
      !ranges.some((range) => range === stated || (stated!.startsWith("闰") && range.startsWith(stated!)))
    )
      throw new InputError(
        "MONTH_RANGE_MISMATCH",
        `${label} 把“${tag}”写成“${stated}”，但当前 evidence 中为“${ranges.join("”或“")}”`,
      );
  }
  const monthHint = context?.monthlyLabels
    ? "；如需按月作答，改写为“八字流月<干支>”或“紫微流月<干支>”并写明其节气或农历起止"
    : "，或用 --granularity month 接入流月证据后改写为体系流月";
  const subannual = SUBANNUAL_RELATIVE_TIME_PATTERN.exec(granularityText);
  if (subannual)
    throw new InputError(
      "UNSUPPORTED_TIME_GRANULARITY",
      `${label} 使用了当前 evidence 不支持的细分时间“${subannual[0]}”；请退回明确年度主题${monthHint}`,
    );
  for (const absoluteSubannual of granularityText.matchAll(
    ABSOLUTE_SUBANNUAL_TIME_PATTERN,
  )) {
    const explicitYear = absoluteSubannual[1]
      ? Number(absoluteSubannual[1])
      : null;
    if (
      explicitYear !== null &&
      !evidenceYears.includes(explicitYear) &&
      (referenceYear === null || explicitYear < referenceYear) &&
      (context?.role === "title" || context?.role === "reality-source") &&
      !/(?:适合|会|能|应该|预测|吉凶|有利|不利|选择|机会|窗口)/u.test(localContext(absoluteSubannual.index, absoluteSubannual[0].length))
    )
      continue;
    throw new InputError(
      "UNSUPPORTED_TIME_GRANULARITY",
      `${label} 使用了当前 evidence 不支持的绝对细分时间“${absoluteSubannual[0]}”；公历月可能跨两个流月，请退回明确年度主题${monthHint}`,
    );
  }
  for (const numericDate of [
    ...fullNumericDates,
    ...yearlessNumericDates,
  ]) {
    if (!granularityText.slice(numericDate.index, numericDate.index + numericDate[0].length).trim() ||
        !hasDecisionContext(numericDate.index, numericDate[0].length))
      continue;
    throw new InputError(
      "UNSUPPORTED_TIME_GRANULARITY",
      `${label} 把数字日期“${numericDate[0]}”用于当前年度 evidence 不支持的具体时点判断；请退回明确年度主题，或先接入对应日级证据`,
    );
  }
  for (const clockTime of text.matchAll(CLOCK_TIME_PATTERN)) {
    if (!hasDecisionContext(clockTime.index, clockTime[0].length)) continue;
    throw new InputError(
      "UNSUPPORTED_TIME_OF_DAY",
      `${label} 把钟点“${clockTime[0]}”用于当前 evidence 不支持的日内判断；请先明确当地日期与 IANA 时区，并接入对应日级和小时级证据`,
    );
  }
  for (const daypart of text.matchAll(RELATIVE_DAYPART_PATTERN)) {
    if (!hasDecisionContext(daypart.index, daypart[0].length)) continue;
    throw new InputError(
      "UNSUPPORTED_TIME_OF_DAY",
      `${label} 把相对日内时点“${daypart[0]}”用于当前 evidence 不支持的事件判断；请先明确当地日期与 IANA 时区，并接入对应日级和小时级证据`,
    );
  }
  const multiyearRange = MULTIYEAR_RELATIVE_RANGE_PATTERN.exec(granularityText);
  if (multiyearRange)
    throw new InputError(
      "AMBIGUOUS_YEAR_RANGE",
      `${label} 使用了无法唯一确定首尾年份的多年范围“${multiyearRange[0]}”；请改写为明确 YYYY—YYYY 年度闭区间，并说明是否包含当前年`,
    );
  const vagueHorizon = VAGUE_TIME_HORIZON_PATTERN.exec(granularityText);
  if (vagueHorizon)
    throw new InputError(
      "AMBIGUOUS_TIME_HORIZON",
      `${label} 使用了无法绑定到确定年份或起止范围的模糊时间“${vagueHorizon[0]}”；请改写为明确 YYYY 年度主题或明确日期范围，并确保相应粒度 evidence 已计算`,
    );
  if (RELATIVE_CYCLE_PATTERN.test(text)) {
    RELATIVE_CYCLE_PATTERN.lastIndex = 0;
    throw new InputError(
      "AMBIGUOUS_RELATIVE_TIME",
      `${label} 使用了无法唯一解析的相对大限；请改写为 evidence 内的明确年份范围`,
    );
  }
  RELATIVE_CYCLE_PATTERN.lastIndex = 0;
  const relativeTerms = [...text.matchAll(RELATIVE_YEAR_PATTERN)];
  if (relativeTerms.length && referenceYear === null)
    throw new InputError(
      "AMBIGUOUS_RELATIVE_TIME",
      `${label} 使用了相对年份；须迁移到 v6 并填写 timeReference`,
    );
  const resolved = referencedRelativeYears(text, referenceYear);
  if (resolved.some((year) => !evidenceYears.includes(year)))
    throw new InputError(
      "RELATIVE_TIME_OUT_OF_SCOPE",
      `${label} 的相对年份不在当前 evidence.years，须重新计算对应年份`,
    );
  for (const match of text.matchAll(EXPLICIT_ANNUAL_RANGE_PATTERN)) {
    const start = Number(match[1]);
    const end = Number(match[2]);
    if (start > end)
      throw new InputError(
        "AMBIGUOUS_YEAR_RANGE",
        `${label} 的明确年度区间起年晚于止年；请按 YYYY—YYYY 顺序重写`,
      );
    const missing = [];
    for (let year = start; year <= end; year += 1)
      if (!evidenceYears.includes(year)) missing.push(year);
    if (missing.length)
      throw new InputError(
        "TIME_RANGE_OUT_OF_SCOPE",
        `${label} 的明确年度区间缺少 ${missing.join("、")} evidence；须按同一 input 补算完整年份后再生成报告。若这只是大限或大运的起止标签，写成不带“年/年度”的（YYYY—YYYY）`,
      );
  }
  return text;
}
