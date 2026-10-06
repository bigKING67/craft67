import { InputError } from "./input.js";

export type UnsafeReportCategory =
  | "death-prediction"
  | "medical-diagnosis"
  | "guaranteed-finance"
  | "inevitable-relationship"
  | "guaranteed-event";

/** 确定性事件词表；answer-audit 的事件触发词在此基础上补充主题词。 */
export const EVENT_WORDS =
  "升职|加薪|晋升|升迁|升官|当官|当领导|当老板|掌权|发财|暴富|发达|成名|出名|中奖|结婚|复合|怀孕|跳槽成功|考上|录取|上岸|破产|失业|被裁";

type SafetyRule = {
  category: UnsafeReportCategory;
  label: string;
  pattern: RegExp;
};

const RULES: readonly SafetyRule[] = [
  {
    category: "death-prediction",
    label: "死亡或寿命确定性预测",
    pattern:
      /必死|死定了|活不过(?:\d{1,3}\s*岁|[^，。！？；\n]{1,10})|(?:死亡|去世)(?:时间|日期|年份)|(?:注定|必然|必定|一定(?:会)?|肯定(?:会)?)(?:死亡|去世|早逝)/gu,
  },
  {
    category: "medical-diagnosis",
    label: "疾病诊断",
    pattern:
      /确诊(?:为|是)?[^，。！？；\n]{0,16}|(?:你|命主|此人)(?:已经|已)?(?:患有|有)(?:癌|肿瘤|心脏病|糖尿病|抑郁症|精神病|疾病|病症)|(?:必然|必定|一定(?:会)?|肯定(?:会)?|注定|必得|会得|将得)(?:[^，。！？；\n]{0,10})(?:癌|肿瘤|心脏病|糖尿病|抑郁症|精神病|疾病|病症)/gu,
  },
  {
    category: "guaranteed-finance",
    label: "保证收益或确定性盈亏",
    pattern:
      /稳赚(?:不赔)?|必赚|必亏|包赚|保证收益|收益保证|保本保收益|无风险收益|(?:一定|肯定)(?:会)?赚钱|注定发财/gu,
  },
  {
    category: "inevitable-relationship",
    label: "必然婚变或关系事件",
    pattern:
      /(?:注定|必然|必定|一定(?:会)?|肯定(?:会)?)(?:离婚|婚变|分手|出轨)|婚姻必破|必二婚/gu,
  },
  {
    category: "guaranteed-event",
    label: "确定性事业或人生事件",
    pattern: new RegExp(
      // 断定词后接事件即拦截；断定词后紧跟提醒类动作（避免、应对、准备、需时间……）时是提醒，不算断言。
      // 只看紧跟处而非整段间隔，避免“顺应”“需求”这类词取消真断言。
      `(?:注定|必然|必定|(?:一定|肯定|保证)(?:会|能))(?!(?:要|需要|需|应该|应)?(?:防|避|留意|注意|小心|警惕|提防|应对|应付|面对|准备|预防|时间|时日))[^，。！？；\\n]{0,4}(?:${EVENT_WORDS})` +
        `|(?:一定|肯定|保证)(?:${EVENT_WORDS})|(?:升职|加薪|晋升|结婚|复合|发财)(?:已成定局|板上钉钉)`,
      "gu",
    ),
  },
];

const CLAUSE_BOUNDARY = /[，。！？；：:\n]/u;
const CONTRAST_BOUNDARY = /(?:但是|但|然而|不过|可是)/u;
const NEGATION_WORDS =
  "(?:尚)?不足以|不支持|不能|不得|不可|不应|不要|不宜|不依赖|不把|没有|未(?:自动)?(?:判定|确定|裁定)|切勿|拒绝|避免|禁止|并非|不是|不代表|不等于|不等同(?:于)?|不意味着|不给(?!力)|不构成|不证明|未证明|不确认|不说明|不表示|是不是|是否|能否|无法|不会";
const NEGATION_CONTEXT = new RegExp(`(?:${NEGATION_WORDS})(?:[^，。！？；\\n]{0,24})$|不$`, "u");
const NEGATION_ANYWHERE = new RegExp(`(?:${NEGATION_WORDS})`, "u");
const POST_NEGATION = /^(?:并不成立|不是事实|并不存在|不可能|不可成立)/u;
// 条件前项的引导词：显式条件标记，或“不给/不做……就”这类以否定动作作前项的写法。
const CONDITION_OPENER = /如果|若|假如|要是|一旦|只要|倘若|不给(?!力)|不做|不去|不肯|不愿/u;
// 后项起点；“就业”不是连接词。
const CONSEQUENT = /(?:就|则|便|那么)(?!业)/gu;

/** 与匹配处同一分句、且在最后一个转折词之后的前文。 */
function clausePrefix(text: string, index: number) {
  return text.slice(0, index).split(CLAUSE_BOUNDARY).at(-1)!.split(CONTRAST_BOUNDARY).at(-1)!;
}

/**
 * 按分句结构判断断言是否被否定。断言位于“条件前项→就/则/便→后项”的后项时，只有出现在条件引导词之前
 * （否定整个条件句，如“并不意味着只要努力就一定会升职”）或后项内部的否定才算数；条件前项内部的否定
 * （“不给他机会就注定离婚”）不覆盖后项断言。没有条件结构时按原规则看断言前的否定。
 */
function isNegated(text: string, index: number, length: number) {
  const prefix = clausePrefix(text, index);
  const opener = CONDITION_OPENER.exec(prefix);
  const consequent = opener
    ? [...prefix.matchAll(CONSEQUENT)].filter((m) => m.index! > opener.index).at(-1)
    : undefined;
  if (opener && consequent) {
    if (NEGATION_ANYWHERE.test(prefix.slice(0, opener.index))) return true;
    if (NEGATION_CONTEXT.test(prefix.slice(consequent.index! + consequent[0].length))) return true;
  } else if (NEGATION_CONTEXT.test(prefix.slice(-36))) return true;
  return POST_NEGATION.test(text.slice(index + length, index + length + 12));
}

export function findUnsafeReportClaim(text: string) {
  for (const rule of RULES) {
    for (const match of text.matchAll(rule.pattern)) {
      const index = match.index ?? 0;
      if (!isNegated(text, index, match[0].length))
        return {
          category: rule.category,
          label: rule.label,
          match: match[0],
          index,
        };
    }
  }
  return null;
}

export function assertSafeReportText(text: string, field: string) {
  const issue = findUnsafeReportClaim(text);
  if (issue)
    throw new InputError(
      "UNSAFE_REPORT_CLAIM",
      `${field} 包含${issue.label}；命理解读产物不得把传统解释写成高风险现实断言`,
    );
}

const TOPIC_PATTERNS = {
  strength: /旺衰|身强|身弱|偏强|偏弱|可任(?:财|官|杀|食伤)/u,
  pattern: /格局|成格|破格|败格/u,
  climate: /调候|寒暖|燥湿/u,
  balance: /扶抑/u,
  selection: /用神|喜用|忌神|取用|五行方向/u,
} as const;

export function requiredReasoningTopics(text: string) {
  return (Object.entries(TOPIC_PATTERNS) as Array<
    [keyof typeof TOPIC_PATTERNS, RegExp]
  >)
    .filter(([, pattern]) => pattern.test(text))
    .map(([topic]) => topic);
}

// 格局成立类单独匹配，再按分句判断条件、让步与疑问框架；“尚未确定成格”不算。
const PATTERN_ESTABLISHED =
  /(?:正|偏)?(?:财|官|杀|煞|印|枭|食神|伤官|建禄|月刃|羊刃)格(?:已经|已|确实|确定|完全)?(?:成立|成格|确定|无疑)(?!的?(?:前提|条件|依据|话)|与否|与不|时(?:才|再|方|就)|之时|取决|需|须|要看|尚)|(?:已经|已|(?<![未不])确定|确实)成格/gu;
// 分句内的条件、让步、疑问框架；“只有”须与其后的“才”配对，“即使如此”是陈述。
const CONDITIONAL_FRAME = /如果|若|假如|倘若|要是|一旦|只要|要想|哪怕|是否|能否|(?:即使|即便)(?!如此)/u;

function inConditionalFrame(text: string, index: number, length: number) {
  const before = clausePrefix(text, index);
  const after = text.slice(index + length).split(CLAUSE_BOUNDARY)[0]!;
  return CONDITIONAL_FRAME.test(before) || (/只有/u.test(before) && /才/u.test(after));
}

const PREMISE_UPGRADE =
  /(?:已经|已)(?:成立|确定|裁定|定论)|(?:结论|方向)(?:已经|已)?(?:确定|唯一)|(?:唯一|确定)(?:的)?(?:用神|喜用|忌神|格局|扶抑方向)|(?:用神|喜用|忌神|格局|扶抑方向)(?:已经|已)?(?:确定|唯一)|(?:无需|不必)(?:再)?(?:核对|验证|复核|考虑|理会|保留)(?:其他)?(?:条件|反证|分支|前提)?|没有其他可能/gu;

export function findUnresolvedPremiseUpgrade(text: string) {
  const hits = [
    ...[...text.matchAll(PATTERN_ESTABLISHED)].filter(
      (m) => !inConditionalFrame(text, m.index!, m[0].length),
    ),
    ...text.matchAll(PREMISE_UPGRADE),
  ].sort((a, b) => a.index! - b.index!);
  for (const match of hits) {
    const index = match.index ?? 0;
    if (!isNegated(text, index, match[0].length))
      return { match: match[0], index };
  }
  return null;
}

export function assertNoUnresolvedPremiseUpgrade(text: string, field: string) {
  if (findUnresolvedPremiseUpgrade(text))
    throw new InputError(
      "UNRESOLVED_PREMISE_CLAIM",
      `${field} 把未决论证写成已裁定结论`,
    );
}
