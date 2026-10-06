import { createHash } from "node:crypto";
import { Temporal } from "@js-temporal/polyfill";
import { Lunar, Solar } from "lunar-typescript";
import iztro from "iztro";
import { parseInput, type BirthInput, InputError } from "./input.js";
import { starLocator } from "./ziwei-transforms.js";
import { resolveBirth, timeAt, SOLAR_SCREENING_MINUTES } from "./time.js";

export const ENGINE = {
  whoami: "0.2.0",
  calendar: "lunar-typescript@1.8.6",
  ziwei: "iztro@2.6.1",
  time: "@js-temporal/polyfill@0.5.1",
  tzdata: process.versions.tz ?? "unknown",
  node: process.versions.node,
};
export const STEMS = [..."甲乙丙丁戊己庚辛壬癸"];
export const BRANCHES = [..."子丑寅卯辰巳午未申酉戌亥"];
const ELEMENTS = [..."木火土金水"];
const HIDDEN = [
  "癸",
  "己癸辛",
  "甲丙戊",
  "乙",
  "戊乙癸",
  "丙戊庚",
  "丁己",
  "己丁乙",
  "庚壬戊",
  "辛",
  "戊辛丁",
  "壬甲",
];
/** 天干五合及合化五行；格局与外格共用。 */
export const STEM_COMBINE: Record<string, string> = { 甲己: "土", 乙庚: "金", 丙辛: "水", 丁壬: "木", 戊癸: "火" };
export const stemCombineElement = (a: string, b: string): string | undefined =>
  STEM_COMBINE[a + b] ?? STEM_COMBINE[b + a];
/** 十神分组；格局与外格共用。 */
export const TEN_GOD_GROUPS = {
  wealth: ["正财", "偏财"],
  seal: ["正印", "偏印"],
  foodHurt: ["食神", "伤官"],
  officerKiller: ["正官", "七杀"],
  peer: ["比肩", "劫财"],
} as const;
/** 地支藏干（首字为本气），与 chart 生成藏干用同一张表。 */
export const hiddenStemsOf = (branch: string) => [...HIDDEN[BRANCHES.indexOf(branch)]!];
export function digest(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}
export function element(stem: string): string {
  return ELEMENTS[Math.floor(STEMS.indexOf(stem) / 2)]!;
}
export function tenGod(dayMaster: string, other: string): string {
  const a = STEMS.indexOf(dayMaster),
    b = STEMS.indexOf(other);
  const relation = (Math.floor(b / 2) - Math.floor(a / 2) + 5) % 5;
  const same = a % 2 === b % 2;
  return [
    ["比肩", "劫财"],
    ["食神", "伤官"],
    ["偏财", "正财"],
    ["七杀", "正官"],
    ["偏印", "正印"],
  ][relation]![same ? 0 : 1]!;
}
function solar(p: Temporal.PlainDateTime) {
  return Solar.fromYmdHms(p.year, p.month, p.day, p.hour, p.minute, p.second);
}
function baziAt(input: BirthInput, instant: Temporal.Instant, solarShift = 0) {
  const t = timeAt(input, instant, solarShift);
  const beijing = instant
    .toZonedDateTimeISO("Asia/Shanghai")
    .withTimeZone("+08:00")
    .toPlainDateTime();
  const absoluteLunar = solar(beijing).getLunar();
  const local = solar(t.clock).getLunar().getEightChar();
  local.setSect(input.dayBoundary === "zi" ? 1 : 2);
  const day = local.getDay();
  const hourIndex = Math.floor((t.clock.hour + 1) / 2) % 12;
  const hourStem = STEMS[((STEMS.indexOf(day[0]!) % 5) * 2 + hourIndex) % 10]!;
  const values = [
    absoluteLunar.getYearInGanZhiExact(),
    absoluteLunar.getMonthInGanZhiExact(),
    day,
    hourStem + BRANCHES[hourIndex],
  ];
  const positions = ["year", "month", "day", "hour"] as const;
  const pillars = positions.map((position, i) => {
    const value = values[i]!;
    return {
      position,
      value,
      stem: value[0]!,
      branch: value[1]!,
      element: element(value[0]!),
      tenGod: position === "day" ? "日主" : tenGod(day[0]!, value[0]!),
      hiddenStems: [...HIDDEN[BRANCHES.indexOf(value[1]!)]!].map((stem) => ({
        stem,
        element: element(stem),
        tenGod: tenGod(day[0]!, stem),
      })),
    };
  });
  return {
    time: t.audit,
    clock: t.clock,
    pillars,
    dayMaster: day[0]!,
    absoluteLunar,
    beijing,
  };
}
export type Granularity = "year" | "month";
const LUNAR_MONTH_NAMES = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"];

export function ziweiAt(
  clock: Temporal.PlainDateTime,
  input: BirthInput,
  years: number[],
  granularity: Granularity = "year",
) {
  const settings = {
    yearDivide: "normal",
    ageDivide: "normal",
    horoscopeDivide: "normal",
    dayDivide: input.dayBoundary === "zi" ? "forward" : "current",
    algorithm: "default",
  } as const;
  iztro.astro.config(settings);
  const timeIndex = Math.floor((clock.hour + 1) / 2); // 12 is late Zi; do not discard it.
  const c = iztro.astro.bySolar(
    clock.toPlainDate().toString(),
    timeIndex,
    input.gender === "male" ? "男" : "女",
    true,
    "zh-CN",
  );
  const birthLunarYear = solar(clock).getLunar().getYear();
  const star = (s: {
    name: string;
    brightness?: string;
    mutagen?: string;
  }) => ({
    name: s.name,
    brightness: s.brightness ?? "",
    mutagen: s.mutagen ?? "",
  });
  const palaces = c.palaces.map((p) => ({
    index: p.index,
    name: p.name,
    stem: p.heavenlyStem,
    branch: p.earthlyBranch,
    isBodyPalace: p.isBodyPalace,
    majorStars: p.majorStars.map(star),
    minorStars: p.minorStars.map(star),
    adjectiveStars: p.adjectiveStars.map(star),
    decadal: p.decadal,
    surroundedIndices: [
      p.index,
      (p.index + 4) % 12,
      (p.index + 8) % 12,
      (p.index + 6) % 12,
    ],
  }));
  return {
    settings: {
      ...settings,
      fixLeap: true,
      language: "zh-CN",
      calendarBasis: "chart-clock-date",
      birthLunarYear,
    },
    lunarDate: c.lunarDate,
    time: c.time,
    soulPalace: c.earthlyBranchOfSoulPalace,
    bodyPalace: c.earthlyBranchOfBodyPalace,
    soul: c.soul,
    body: c.body,
    fiveElementsClass: c.fiveElementsClass,
    palaces,
    decadals: c
      .decadalList()
      .map((d) => ({
        palace: d.palaceName,
        ageRange: d.ageRange,
        yearRange: d.yearRange,
        stem: d.heavenlyStem,
        branch: d.earthlyBranch,
        mutagen: d.mutagen,
      })),
    yearly: years
      .filter((y) => y >= birthLunarYear)
      .map((year) => {
        // Only annual fields; June 15 is an interior representative date, not a prediction date.
        const h = c.horoscope(`${year}-06-15`, 0);
        return {
          year,
          boundary: "lunar-new-year",
          stem: h.yearly.heavenlyStem,
          branch: h.yearly.earthlyBranch,
          palaceNames: h.yearly.palaceNames,
          mutagen: h.yearly.mutagen,
          decadalPalaceIndex: h.decadal.index,
        };
      }),
    ...(granularity === "month" ? { monthly: ziweiMonthly(c, palaces, years.filter((y) => y >= birthLunarYear)) } : {}),
  };
}

/**
 * 紫微流月直接取 iztro monthlyList（fixLeap=true：闰月 1–15 日归上月、16 日起归下月），
 * 只补公历起止与四化落宫。另一派把整个闰月归上月，因此闰月两段均标 leapConvention。
 */
function ziweiMonthly(
  c: ReturnType<typeof iztro.astro.bySolar>,
  palaces: Parameters<typeof starLocator>[0],
  years: number[],
) {
  // 复用 ziweiAt 已规范化的宫位，保证流月定位与生年、运限四化口径一致。
  const { locate } = starLocator(palaces);
  const solarOf = (year: number, month: number, leap: boolean, day: number) =>
    Lunar.fromYmd(year, leap ? -month : month, day).getSolar();
  return years.flatMap((year) =>
    c.monthlyList(year, true).map((m) => {
      const name = LUNAR_MONTH_NAMES[m.month - 1]!;
      const leap = m.isLeapMonth ? (m.part === "first" ? ("first-half" as const) : ("second-half" as const)) : (false as const);
      const [fromDay, toDay] = m.dayRange;
      return {
        year,
        lunarMonth: m.month,
        label: m.isLeapMonth ? `闰${name}月${m.part === "first" ? "上半" : "下半"}` : `${name}月`,
        leap,
        ...(leap
          ? { leapConvention: "iztro：闰月 1–15 日归上月、16 日起归下月；另一派整月归上月" }
          : {}),
        solarStart: solarOf(year, m.month, m.isLeapMonth, fromDay).toYmd(),
        solarEndExclusive: solarOf(year, m.month, m.isLeapMonth, toDay).next(1).toYmd(),
        stem: m.heavenlyStem,
        branch: m.earthlyBranch,
        lifePalaceIndex: m.index,
        palaceNames: m.palaceNames,
        // 与流年四化一致：给出本命物理宫及其在当月承担的宫职。
        transformations: m.mutagen.map((star, i) => ({
          mutagen: "禄权科忌"[i]!,
          ...locate(star, m.palaceNames),
        })),
        stars: (m.stars ?? []).flatMap((list, palaceIndex) =>
          list.map((st) => ({ name: st.name, palaceIndex })),
        ),
      };
    }),
  );
}
function cycles(
  input: BirthInput,
  data: ReturnType<typeof baziAt>,
  years: number[],
) {
  const ec = data.absoluteLunar.getEightChar();
  ec.setSect(input.dayBoundary === "zi" ? 1 : 2);
  const yun = ec.getYun(input.gender === "male" ? 1 : 0, 2);
  const start = Temporal.PlainDateTime.from(
    yun.getStartSolar().toYmdHms().replace(" ", "T"),
  ).toZonedDateTime("+08:00");
  const monthCycleIndex = Array.from(
    { length: 60 },
    (_, i) => STEMS[i % 10]! + BRANCHES[i % 12]!,
  ).indexOf(data.pillars[1]!.value);
  const direction = yun.isForward() ? 1 : -1;
  const startLocal = start.toInstant().toZonedDateTimeISO(input.timeZone);
  return {
    direction: direction === 1 ? "forward" : "backward",
    method:
      "lunar-typescript Yun sect=2; absolute birth vs Jie; original civil basis",
    startAge: {
      years: yun.getStartYear(),
      months: yun.getStartMonth(),
      days: yun.getStartDay(),
      hours: yun.getStartHour(),
    },
    startInstant: start.toInstant().toString(),
    startCivil: startLocal.toString(),
    decades: Array.from({ length: 10 }, (_, i) => {
      const index = (monthCycleIndex + direction * (i + 1) + 600) % 60;
      return {
        index: i + 1,
        pillar: STEMS[index % 10]! + BRANCHES[index % 12]!,
        startCivil: startLocal.add({ years: 10 * i }).toString(),
        endExclusiveCivil: startLocal.add({ years: 10 * (i + 1) }).toString(),
      };
    }),
    yearly: years.map((year) => ({
      year,
      pillar: STEMS[(year - 4) % 10]! + BRANCHES[(year - 4) % 12]!,
      boundary: "lichun",
    })),
  };
}
export function buildChart(raw: unknown, years?: number[], granularity: Granularity = "year") {
  const input = parseInput(raw);
  const centerYear = Temporal.Now.plainDateISO("Asia/Shanghai").year;
  const resolvedYears = [
    ...new Set(
      years ?? [
        centerYear - 2,
        centerYear - 1,
        centerYear,
        centerYear + 1,
        centerYear + 2,
      ],
    ),
  ].sort((a, b) => a - b);
  if (
    !resolvedYears.length ||
    resolvedYears.length > 20 ||
    resolvedYears.some((y) => !Number.isInteger(y) || y < 1901 || y > 2099)
  )
    throw new InputError(
      "INVALID_YEARS",
      "流年须为 1901–2099 整数，最多 20 年",
    );
  const policy = {
    baziYear: "lichun-absolute-instant",
    baziMonth: "jie-absolute-instant",
    dayBoundary: input.dayBoundary,
    solarModel: "NOAA fractional-year",
    ziweiYear: "lunar-new-year",
  };
  const chartId = digest({ input, policy, ENGINE });
  if (input.time === null)
    return {
      schema: "whoami.chart.v1" as const,
      chartId,
      status: "needs-input" as const,
      input,
      policy,
      engines: ENGINE,
      years: resolvedYears,
      questions: ["出生时间未知：请提供时辰或大致时间范围；不能使用中午替代。"],
      warnings: [],
      candidates: [],
    };
  const birth = resolveBirth(input).toInstant();
  const offsets = new Set([
    0,
    -input.uncertaintyMinutes,
    input.uncertaintyMinutes,
  ]);
  for (let n = -input.uncertaintyMinutes; n < input.uncertaintyMinutes; n += 1)
    offsets.add(n);
  const shifts =
    input.timeBasis === "true-solar"
      ? [0, -SOLAR_SCREENING_MINUTES, SOLAR_SCREENING_MINUTES]
      : [0];
  const groups = new Map<
    string,
    {
      data: ReturnType<typeof baziAt>;
      samples: { birthOffsetMinutes: number; solarShiftMinutes: number }[];
      cycleSamples: ReturnType<typeof cycles>[];
    }
  >();
  // Nominal first, preserving the actual stated instant when all sample charts agree.
  for (const offset of offsets)
    for (const shift of shifts) {
      const instant = birth.add({ milliseconds: Math.round(offset * 60_000) });
      const data = baziAt(input, instant, shift);
      const cycle = cycles(input, data, resolvedYears);
      const ziDate = data.clock.toPlainDate().toString();
      const key = JSON.stringify([
        data.pillars.map((p) => p.value),
        ziDate,
        Math.floor((data.clock.hour + 1) / 2),
      ]);
      const sample = { birthOffsetMinutes: offset, solarShiftMinutes: shift };
      const group = groups.get(key);
      if (group) {
        group.samples.push(sample);
        group.cycleSamples.push(cycle);
      } else groups.set(key, { data, samples: [sample], cycleSamples: [cycle] });
    }
  const cycleUncertainty = (
    samples: { birthOffsetMinutes: number; solarShiftMinutes: number }[],
    cycleSamples: ReturnType<typeof cycles>[],
  ) => {
    const starts = cycleSamples
      .map((cycle) => ({
        instant: cycle.startInstant,
        civil: cycle.startCivil,
      }))
      .sort((a, b) =>
        Temporal.Instant.compare(
          Temporal.Instant.from(a.instant),
          Temporal.Instant.from(b.instant),
        ),
      );
    const distinctStarts = new Set(starts.map((start) => start.instant)).size;
    return {
      status: distinctStarts > 1 ? ("range" as const) : ("exact" as const),
      sampleCount: samples.length,
      distinctStartCount: distinctStarts,
      birthOffsetMinutes: {
        min: Math.min(...samples.map((sample) => sample.birthOffsetMinutes)),
        max: Math.max(...samples.map((sample) => sample.birthOffsetMinutes)),
      },
      solarShiftMinutes: {
        min: Math.min(...samples.map((sample) => sample.solarShiftMinutes)),
        max: Math.max(...samples.map((sample) => sample.solarShiftMinutes)),
      },
      startInstant: {
        earliest: starts[0]!.instant,
        latest: starts.at(-1)!.instant,
      },
      startCivil: {
        earliest: starts[0]!.civil,
        latest: starts.at(-1)!.civil,
      },
    };
  };
  const candidates = [...groups.entries()].map(
    ([key, { data, samples, cycleSamples }], index) => ({
      id: `C${index + 1}-${digest(key).slice(0, 8)}`,
      representativeTime: data.time,
      samples,
      bazi: {
        pillars: data.pillars,
        dayMaster: data.dayMaster,
        cycles: {
          ...cycleSamples[0]!,
          uncertainty: cycleUncertainty(samples, cycleSamples),
        },
      },
      ziwei: ziweiAt(data.clock, input, resolvedYears, granularity),
    }),
  );
  const warnings: string[] = [];
  if (input.timeBasis === "true-solar")
    warnings.push(
      "真太阳时使用 NOAA 近似均时差；±2 分钟仅作边界筛查，不是经认证的误差上限，不能声称秒级精度。",
    );
  if (input.uncertaintyMinutes > 0)
    warnings.push(
      "出生区间按每分钟及端点采样；候选是代表性样本，不保证覆盖亚分钟交叠边界。未确认时间前不输出唯一确定判断。",
    );
  if (
    candidates.some(
      (candidate) => candidate.bazi.cycles.uncertainty.status === "range",
    )
  )
    warnings.push(
      "同一候选四柱内的起运时刻会随出生区间变化；cycles.uncertainty 保留完整范围，报告不得把代表值写成已确认单点。",
    );
  if (candidates.length > 1)
    warnings.push("时间边界产生多个候选盘，报告必须区分共同事实与条件性解读。");
  const nominal = timeAt(input, birth);
  const civil = baziAt({ ...input, timeBasis: "civil" }, birth);
  return {
    schema: "whoami.chart.v1" as const,
    chartId,
    status:
      candidates.length > 1 || input.uncertaintyMinutes > 0
        ? ("ambiguous" as const)
        : ("ready" as const),
    input,
    policy,
    engines: ENGINE,
    years: resolvedYears,
    // 月度粒度按需开启；年度输出不含此字段，保持既有 chart/context 字节不变。
    ...(granularity === "month" ? { granularity } : {}),
    questions: [],
    warnings,
    time: nominal.audit,
    civilComparison: {
      pillars: civil.pillars.map((p) => p.value),
      changed:
        JSON.stringify(civil.pillars.map((p) => p.value)) !==
        JSON.stringify(candidates[0]!.bazi.pillars.map((p) => p.value)),
    },
    candidates,
  };
}
export type Chart = ReturnType<typeof buildChart>;
