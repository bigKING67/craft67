import { InputError } from "./input.js";
import type { ziweiAt } from "./chart.js";
import type { Evidence } from "./evidence.js";

type Ziwei = ReturnType<typeof ziweiAt>;
type Palace = Ziwei["palaces"][number];
type Yearly = Ziwei["yearly"];
type Monthly = NonNullable<Ziwei["monthly"]>;
export type ZiweiScope = { palaces: Palace[]; yearly: Yearly; monthly?: Monthly };

export const isZiweiPalaceFactId = (id: string) => /\.ziwei\.palace-\d+$/u.test(id);

/**
 * 为一段文本选定宫位核对所用的候选：单候选命盘直接使用该候选；多候选时仅当文本线索指向唯一候选。
 * 返回 undefined 表示无法确定归属，调用方须把本项标为未核对，而不是当作通过。
 */
export function scopeForText(
  scopes: Map<string, ZiweiScope>,
  candidateHints: Iterable<string> = [],
) {
  if (scopes.size === 1) return [...scopes.values()][0];
  const hinted = new Set(candidateHints);
  return hinted.size === 1 ? scopes.get([...hinted][0]!) : undefined;
}

/** 按候选汇总本命十二宫、流年宫职与（月度 evidence 的）流月宫职，供宫位集合核对复用。 */
export function ziweiScopes(evidence: Evidence) {
  const scopes = new Map<string, ZiweiScope>();
  for (const candidate of evidence.candidateIds) {
    const cycles = evidence.facts.find((f) => f.id === `${candidate}.ziwei.cycles`)
      ?.value as { yearly: Yearly } | undefined;
    const monthly = evidence.facts.find((f) => f.id === `${candidate}.ziwei.monthly`)?.value as
      | Monthly
      | undefined;
    scopes.set(candidate, {
      palaces: evidence.facts
        .filter((f) => f.candidate === candidate && isZiweiPalaceFactId(f.id))
        .map((f) => f.value as Palace),
      yearly: cycles?.yearly ?? [],
      ...(monthly ? { monthly } : {}),
    });
  }
  return scopes;
}

const PALACE_NAMES = [
  "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
  "迁移", "仆役", "官禄", "田宅", "福德", "父母",
];
// 容许“2026 年的流年官禄宫落在本命命宫（午）”等常见变体。
const HEADER = new RegExp(
  `(\\d{4})\\s*年?(?:的)?流年(官禄|财帛|夫妻)宫?落(?:在|于)?本命(${PALACE_NAMES.join("|")})宫?[（(]?([子丑寅卯辰巳午未申酉戌亥])?`,
  "gu",
);
// 流月段首：“2026年紫微流月丁酉（农历八月）的官禄落本命仆役（亥）”。
const MONTH_HEADER = new RegExp(
  `(\\d{4})\\s*年?(?:的)?\\s*紫微\\s*流月([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])(?:\\s*[（(][^）)]*[）)])?(?:的)?(官禄|财帛|夫妻)宫?落(?:在|于)?本命(${PALACE_NAMES.join("|")})宫?[（(]?([子丑寅卯辰巳午未申酉戌亥])?`,
  "gu",
);
// 同一分句内显式声明另引集合外背景时放行，见 references/report.md 前提一致性一节。
const OUTSIDE_MARKER = /(三方四正|联宫)之外|不属(于)?(本题|该主题|本主题|该年)/u;
const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");

/** 本命宫引用：宫名后接地支（其后须为标点、括号或文本结尾，避免“财帛未见”“夫妻子女”），或接本宫星曜（允许中间有“宫”或括号）。 */
function palaceReference(p: Palace) {
  const stars = [...p.majorStars, ...p.minorStars].map((s) => escape(s.name));
  const alternatives = [
    `${p.branch}(?=[（(，、。；：:\\s]|$)`,
    `宫?[（(]${p.branch}(?:宫)?[）)]`,
    `宫(?:位)?(?:位于|在)${p.branch}`,
  ];
  if (stars.length) alternatives.push(`宫?[（(]?(?:${stars.join("|")})`);
  return new RegExp(`${escape(p.name)}(?:${alternatives.join("|")})`, "u");
}

/**
 * 逐段核对“YYYY(年)流年<主题宫>落本命<宫>”或“YYYY年紫微流月<干支>的<主题宫>落本命<宫>”之后的解释：
 * 段首落宫须与命盘一致，段内写出的本命宫须属于该期该主题的物理宫集合。只覆盖这两种固定写法。
 */
export function assertZiweiPalaceScope(raw: string, scope: ZiweiScope, label: string) {
  const text = raw.replace(/\r\n?/gu, "\n"); // CRLF 文本同样以空行分段
  const { palaces, yearly, monthly } = scope;
  type Header = { index: number; whole: string; period: string; role: string; name: string; branch?: string; roles?: string[] };
  const headers: Header[] = [
    ...[...text.matchAll(HEADER)].map((m) => ({
      index: m.index!, whole: m[0], period: `${m[1]} 年流年`, role: m[2]!, name: m[3]!, branch: m[4],
      roles: yearly.find((y) => y.year === Number(m[1]))?.palaceNames,
    })),
    ...[...text.matchAll(MONTH_HEADER)].map((m) => {
      // 同一年同干支的流月（如闰月两段）宫职不一致时无法唯一定位，不核对。
      const entries = (monthly ?? []).filter((x) => x.year === Number(m[1]) && x.stem + x.branch === m[2]);
      const unique = new Set(entries.map((x) => x.palaceNames.join(","))).size === 1;
      return {
        index: m.index!, whole: m[0], period: `${m[1]} 年紫微流月${m[2]}`, role: m[3]!, name: m[4]!, branch: m[5],
        roles: unique ? entries[0]!.palaceNames : undefined,
      };
    }),
  ].sort((a, b) => a.index - b.index);
  headers.forEach((header, i) => {
    if (!header.roles) return; // 年份或流月是否在 evidence 内由时间门禁负责
    const anchor = palaces.find((p) => header.roles![p.index] === header.role);
    if (!anchor) return;
    if (anchor.name !== header.name || (header.branch !== undefined && anchor.branch !== header.branch))
      throw new InputError(
        "PALACE_SCOPE_MISMATCH",
        `${label} 写“${header.whole}”，但当前命盘 ${header.period}${header.role}落本命${anchor.name}${anchor.branch}`,
      );
    const start = header.index + header.whole.length;
    const nextHeader = headers[i + 1]?.index ?? text.length;
    const paragraphEnd = text.indexOf("\n\n", start);
    const segment = text.slice(start, paragraphEnd === -1 ? nextHeader : Math.min(nextHeader, paragraphEnd));
    const outside = palaces
      .filter((p) => !anchor.surroundedIndices.includes(p.index))
      .map((p) => ({ p, pattern: palaceReference(p) }));
    for (const clause of segment.split(/[。；！？，\n]/u)) {
      if (OUTSIDE_MARKER.test(clause)) continue;
      for (const { p, pattern } of outside) {
        const hit = clause.match(pattern);
        if (hit)
          throw new InputError(
            "PALACE_SCOPE_MISMATCH",
            `${label} 的 ${header.period}${header.role}段落引用了本命${p.name}${p.branch}（“${hit[0]}”），不属于该期${header.role}的三方四正；如需引用集合外背景，须在同一分句写明“三方四正之外”或“不属本题”`,
          );
      }
    }
  });
}
