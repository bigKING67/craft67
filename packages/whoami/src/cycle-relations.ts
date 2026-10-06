import { Lunar, Solar } from "lunar-typescript";
import { Temporal } from "@js-temporal/polyfill";
import type { Chart } from "./chart.js";

type Bazi = Chart["candidates"][number]["bazi"];
type Located = { position: string; stem: string; branch: string };
export type BranchRelation = { kind: string; positions: string[]; branches: string };

const BRANCH_PAIRS = [
  ["冲", "子午 丑未 寅申 卯酉 辰戌 巳亥"],
  ["六合", "子丑 寅亥 卯戌 辰酉 巳申 午未"],
  ["害", "子未 丑午 寅巳 卯辰 申亥 酉戌"],
] as const;
export const BRANCH_GROUPS = [
  ["三合", "申子辰 亥卯未 寅午戌 巳酉丑"],
  ["三刑", "寅巳申 丑戌未"],
] as const;
// 三会与下列扩展成对关系属 v2 口径：v2 的本命、流年、流月一致使用；v1 本命 relations 冻结，不含这些项。
export const SEASONAL_GROUPS = [["三会", "寅卯辰 巳午未 申酉戌 亥子丑"]] as const;
const STEM_PAIRS = [
  ["五合", "甲己 乙庚 丙辛 丁壬 戊癸"],
  ["冲", "甲庚 乙辛 丙壬 丁癸"],
] as const;

const STEM_CLASH = STEM_PAIRS[1][1];
const BRANCH_CLASH = BRANCH_PAIRS[0][1];
const inPair = (table: string, a: string, b: string) =>
  a !== b && table.split(" ").some((pair) => pair.includes(a) && pair.includes(b));

// 三合局按生、旺、墓：含旺支的两支为半合，生墓两支为拱合。
const TRINE_FRAMES = ["申子辰", "亥卯未", "寅午戌", "巳酉丑"];
const EXTENDED_PAIRS = [
  ["破", "子酉 卯午 辰丑 未戌 寅亥 巳申"],
  // 三刑组内的两两相刑；子卯刑已在基础表中。
  ["刑", "寅巳 巳申 寅申 丑戌 戌未 丑未"],
] as const;

/**
 * 两个地支之间的成对关系；本命与岁运共用同一张表，保证口径一致。
 * extended=false 为冻结的 v1 口径；true 另列半合、拱合、破与三刑组内两两相刑。
 */
export function pairBranchRelations(
  a: { position: string; branch: string },
  b: { position: string; branch: string },
  extended = false,
): BranchRelation[] {
  const out: BranchRelation[] = [];
  const at = { positions: [a.position, b.position], branches: a.branch + b.branch };
  for (const [kind, table] of BRANCH_PAIRS)
    if (inPair(table, a.branch, b.branch)) out.push({ kind, ...at });
  if (a.branch === b.branch && "辰午酉亥".includes(a.branch))
    out.push({ kind: "自刑", ...at });
  if (inPair("子卯", a.branch, b.branch)) out.push({ kind: "刑", ...at });
  if (!extended) return out;
  const frame = TRINE_FRAMES.find((f) => a.branch !== b.branch && f.includes(a.branch) && f.includes(b.branch));
  if (frame)
    out.push({ kind: [a.branch, b.branch].includes(frame[1]!) ? "半合" : "拱合", ...at });
  for (const [kind, table] of EXTENDED_PAIRS)
    if (inPair(table, a.branch, b.branch)) out.push({ kind, ...at });
  return out;
}

/** 全部成员都已出现的三合、三刑等组；required 中的每个位置都必须是补齐该组所必需的（去掉它就不完整）。 */
export function completeBranchGroups(
  members: { position: string; branch: string }[],
  required: string[] = [],
  tables: readonly (readonly [string, string])[] = BRANCH_GROUPS,
): BranchRelation[] {
  const out: BranchRelation[] = [];
  for (const [kind, groups] of tables)
    for (const group of groups.split(" ")) {
      const complete = (ms: typeof members) =>
        [...group].every((b) => ms.some((m) => m.branch === b));
      if (!complete(members)) continue;
      if (required.some((r) => complete(members.filter((m) => m.position !== r)))) continue;
      const used = members.filter((m) => group.includes(m.branch));
      out.push({ kind, positions: used.map((m) => m.position), branches: group });
    }
  return out;
}

type CycleRelation = {
  layer:
    | "流年-本命" | "大运-本命" | "流年-大运" | "大运-本命组合" | "流年参与组合"
    | "流月-本命" | "流月-流年" | "流月-大运" | "流月参与组合";
  scope: "stem" | "branch" | "pillar";
  kind: string;
  positions: string[];
  value: string;
};

function pillarRelations(op: Located, other: Located, layer: CycleRelation["layer"]) {
  const out: CycleRelation[] = [];
  const positions = [op.position, other.position];
  for (const [kind, table] of STEM_PAIRS)
    if (inPair(table, op.stem, other.stem))
      out.push({ layer, scope: "stem", kind, positions, value: op.stem + other.stem });
  for (const r of pairBranchRelations(op, other, true))
    out.push({ layer, scope: "branch", kind: r.kind, positions, value: r.branches });
  const pillar = op.stem + op.branch + other.stem + other.branch;
  if (op.stem === other.stem && op.branch === other.branch)
    out.push({ layer, scope: "pillar", kind: "伏吟", positions, value: pillar });
  if (inPair(STEM_CLASH, op.stem, other.stem) && inPair(BRANCH_CLASH, op.branch, other.branch))
    out.push({ layer, scope: "pillar", kind: "反吟", positions, value: pillar });
  return out;
}

/** lunar-typescript 节气时刻按北京时间给出，统一转为绝对毫秒。 */
const beijingMs = (solar: { toYmdHms(): string }) =>
  Temporal.Instant.from(`${solar.toYmdHms().replace(" ", "T")}+08:00`).epochMilliseconds;

const lichunCache = new Map<number, number>();
const lichun = (lunarYear: number) => {
  let ms = lichunCache.get(lunarYear);
  if (ms === undefined) {
    ms = beijingMs(Lunar.fromYmd(lunarYear, 1, 1).getJieQiTable()["立春"]!);
    lichunCache.set(lunarYear, ms);
  }
  return ms;
};

/** 收集须由指定位置补齐的三合、三刑、三会，按组与位置去重；流年与流月共用。 */
function groupCollector(relations: CycleRelation[]) {
  const seen = new Set<string>();
  const tables = [...BRANCH_GROUPS, ...SEASONAL_GROUPS];
  return (members: Located[], required: string[], layer: CycleRelation["layer"]) => {
    for (const g of completeBranchGroups(members, required, tables)) {
      const key = `${g.kind}:${g.positions.join(",")}`;
      if (seen.has(key)) continue;
      seen.add(key);
      relations.push({ layer, scope: "branch", kind: g.kind, positions: g.positions, value: g.branches });
    }
  };
}

const civil = (ms: number) =>
  Temporal.Instant.fromEpochMilliseconds(ms)
    .toZonedDateTimeISO("+08:00")
    .toString({ timeZoneName: "never" });

/** 本命柱与大运时间窗；流年与流月共用同一套大运覆盖判断。 */
function decadeTimeline(bazi: Bazi) {
  const natal: Located[] = bazi.pillars.map((p) => ({
    position: p.position,
    stem: p.stem,
    branch: p.branch,
  }));
  const { cycles } = bazi;
  const representative = Temporal.Instant.from(cycles.startInstant);
  const shift = (edge: "earliest" | "latest") =>
    Temporal.Instant.from(cycles.uncertainty.startInstant[edge]).epochMilliseconds -
    representative.epochMilliseconds;
  const [minShift, maxShift] = [shift("earliest"), shift("latest")];
  const bounds = cycles.decades.map((d) => ({
    d,
    from: Temporal.ZonedDateTime.from(d.startCivil).epochMilliseconds,
    to: Temporal.ZonedDateTime.from(d.endExclusiveCivil).epochMilliseconds,
  }));
  const lastIndex = cycles.decades.at(-1)!.index;
  const firstStart = bounds[0]!.from;
  /** 窗口 [start, end) 内可能生效的大运；unit 只决定 coverage 的措辞（whole-year / whole-month）。 */
  const active = (start: number, end: number, unit: "year" | "month") =>
    bounds.flatMap(({ d, from, to }) => {
      // 起运范围内任一时刻都覆盖整个窗口才算 whole-*；只在部分起运时刻下覆盖记为 possible。
      const always = from + maxShift <= start && to + minShift >= end;
      const sometimes = from + minShift < end && to + maxShift > start;
      const certainOverlap = from + maxShift < end && to + minShift > start;
      if (!sometimes) return [];
      return [{
        index: d.index,
        pillar: d.pillar,
        coverage: always ? `whole-${unit}` : certainOverlap ? `part-${unit}` : "possible-if-start-shifts",
      }];
    });
  // 起运范围不确定且窗口内有非完整覆盖的大运时，换运是否落在窗口内取决于实际起运时刻，统一标 start-uncertain。
  const status = (
    decades: { index: number; coverage: string }[],
    start: number,
    end: number,
    unit: "year" | "month",
  ) => {
    if (!decades.length) return start >= firstStart ? "after-last-decade" : "before-first-decade";
    if (decades.length === 1 && decades[0]!.coverage.startsWith("whole-")) return "single";
    if (cycles.uncertainty.status === "range") return "start-uncertain";
    if (decades.length === 1 && decades[0]!.index === 1 && firstStart > start) return `first-decade-starts-within-${unit}`;
    if (decades.length === 1 && decades[0]!.index === lastIndex && end > bounds.at(-1)!.to) return `last-decade-ends-within-${unit}`;
    return `switches-within-${unit}`;
  };
  const operators = (decades: { index: number; pillar: string }[]): Located[] =>
    decades.map((d) => ({ position: `decade-${d.index}`, stem: d.pillar[0]!, branch: d.pillar[1]! }));
  return { natal, active, status, operators };
}

/**
 * 逐个请求年份列出流年、该流年（立春至次年立春）内的大运，以及三层干支关系。
 * 只列传统关系表中的组合，不判断化合成败、吉凶或现实事件。
 */
export function cycleRelations(bazi: Bazi) {
  const { natal, active, status, operators: toOperators } = decadeTimeline(bazi);
  return bazi.cycles.yearly.map((y) => {
    const start = lichun(y.year);
    const end = lichun(y.year + 1);
    const decades = active(start, end, "year");
    const yearly: Located = { position: "yearly", stem: y.pillar[0]!, branch: y.pillar[1]! };
    const operators = toOperators(decades);
    const relations: CycleRelation[] = [
      ...natal.flatMap((n) => pillarRelations(yearly, n, "流年-本命")),
      ...operators.flatMap((op) => natal.flatMap((n) => pillarRelations(op, n, "大运-本命"))),
      ...operators.flatMap((op) => pillarRelations(yearly, op, "流年-大运")),
    ];
    // 三合、三刑、三会按“本命 + 每步可能生效的大运 (+ 流年)”分别检查，只保留须岁运补齐的完整组；
    // 不需要流年即成立的组记为“大运-本命组合”，避免把整步大运的组合误读为当年新触发。
    const pushGroups = groupCollector(relations);
    for (const op of operators) pushGroups([...natal, op], [op.position], "大运-本命组合");
    pushGroups([...natal, yearly], ["yearly"], "流年参与组合");
    for (const op of operators)
      pushGroups([...natal, yearly, op], ["yearly", op.position], "流年参与组合");
    return {
      year: y.year,
      pillar: y.pillar,
      // 与大运 startCivil 一致使用 +08:00 民用时间表示立春时刻。
      lichunStart: civil(start),
      lichunEndExclusive: civil(end),
      decadeStatus: status(decades, start, end, "year"),
      decades,
      relations,
    };
  });
}

/**
 * 按节（立春、惊蛰……小寒）切分每个请求流年的 12 个流月，列出流月干支、窗口内大运，
 * 以及流月与本命、流年、大运的成对关系。流月只是叠加在年、运之上的一层，不单独断事。
 */
export function monthlyCycles(bazi: Bazi) {
  const { natal, active, status, operators: toOperators } = decadeTimeline(bazi);
  return bazi.cycles.yearly.map((y) => {
    const yearly: Located = { position: "yearly", stem: y.pillar[0]!, branch: y.pillar[1]! };
    const months = [];
    let start = lichun(y.year);
    let startJie = "立春";
    for (let i = 0; i < 12; i += 1) {
      // 在节后 1 分钟取月柱与下一个节，避开节点本身的边界歧义。
      const probe = Solar.fromJulianDay(
        Solar.fromYmdHms(...civilParts(start)).getJulianDay() + 1 / 1440,
      );
      const lunar = probe.getLunar();
      const next = lunar.getNextJie(false);
      const nextJie = next.getSolar();
      const end = beijingMs(nextJie);
      const pillar = lunar.getMonthInGanZhiExact();
      const decades = active(start, end, "month");
      const monthly: Located = { position: "monthly", stem: pillar[0]!, branch: pillar[1]! };
      const operators = toOperators(decades);
      const relations: CycleRelation[] = [
        ...natal.flatMap((n) => pillarRelations(monthly, n, "流月-本命")),
        ...pillarRelations(monthly, yearly, "流月-流年"),
        ...operators.flatMap((op) => pillarRelations(monthly, op, "流月-大运")),
      ];
      // 须由流月补齐的三合、三刑、三会（本命、流年、大运已完整的组不重复列出）。
      const pushGroups = groupCollector(relations);
      for (const combo of operators.length ? operators.map((op) => [yearly, op]) : [[yearly]])
        pushGroups([...natal, ...combo, monthly], ["monthly"], "流月参与组合");
      months.push({
        pillar,
        startJie,
        endJie: next.getName(),
        start: civil(start),
        endExclusive: civil(end),
        decadeStatus: status(decades, start, end, "month"),
        decades,
        relations,
      });
      start = end;
      startJie = next.getName();
    }
    return { year: y.year, yearPillar: y.pillar, months };
  });
}

function civilParts(ms: number): [number, number, number, number, number, number] {
  const z = Temporal.Instant.fromEpochMilliseconds(ms).toZonedDateTimeISO("+08:00");
  return [z.year, z.month, z.day, z.hour, z.minute, z.second];
}
