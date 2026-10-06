import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { Temporal } from "@js-temporal/polyfill";
import { Solar } from "lunar-typescript";
import { buildChart, tenGod } from "../src/chart.js";
import { InputError, parseInput, solarDate } from "../src/input.js";
import { equationOfTime, resolveBirth, timeAt } from "../src/time.js";

const base = {
  calendar: "solar",
  date: "2000-08-16",
  time: "04:00:00",
  place: "合成地点",
  longitude: 120,
  timeZone: "Asia/Shanghai",
  gender: "female",
  timeBasis: "civil",
};
const chart = (extra: Record<string, unknown> = {}) =>
  buildChart({ ...base, ...extra }, [2025, 2026]);
const values = (extra: Record<string, unknown> = {}) =>
  chart(extra).candidates[0]!.bazi.pillars.map((p) => p.value);
const golden = JSON.parse(
  readFileSync(
    new URL("./fixtures/chart-goldens.json", import.meta.url),
    "utf8",
  ),
);
for (const row of golden.bazi)
  test(`外部四柱样例 ${row.date} ${row.time}`, () =>
    assert.deepEqual(values({ date: row.date, time: row.time }), row.expected));
for (const row of golden.lunarBazi)
  test(`外部农历四柱样例 ${row.date} ${row.time}`, () =>
    assert.deepEqual(
      values({
        calendar: "lunar",
        date: row.date,
        time: row.time,
        leapMonth: row.leapMonth,
      }),
      row.expected,
    ));
test("外部紫微文档样例与十二宫结构", () => {
  const c = chart().candidates[0]!.ziwei;
  for (const key of [
    "soulPalace",
    "bodyPalace",
    "soul",
    "body",
    "fiveElementsClass",
  ])
    assert.equal(c[key as keyof typeof c], golden.ziwei[key]);
  assert.equal(c.palaces.length, 12);
  assert.equal(new Set(c.palaces.map((p) => p.branch)).size, 12);
  assert.equal(c.palaces.flatMap((p) => p.majorStars).length, 14);
  assert.deepEqual(
    c.palaces.map((palace) => ({
      name: palace.name,
      stem: palace.stem,
      branch: palace.branch,
      mainStars: palace.majorStars.map((star) => star.name),
      stars: [...palace.majorStars, ...palace.minorStars]
        .map((star) => star.name)
        .sort(),
    })),
    golden.ziwei.palaces.map((palace: { stars: string[] }) => ({
      ...palace,
      stars: [...palace.stars].sort(),
    })),
  );
});
test("起运 sect=2 与独立于适配器的上游样例相符", () => {
  const c = chart({ date: "2022-03-09", time: "20:51:00", gender: "male" })
    .candidates[0]!;
  assert.deepEqual(
    { ...c.bazi.cycles.startAge, hours: undefined },
    { years: 8, months: 9, days: 2, hours: undefined },
  );
  assert.match(c.bazi.cycles.startCivil, /^2030-12-12/);
});
test("午夜换日为明确的日干/时干一致口径", () => {
  const zi = values({ date: "1988-02-15", time: "23:30" });
  const midnight = values({
    date: "1988-02-15",
    time: "23:30",
    dayBoundary: "midnight",
  });
  assert.deepEqual(zi.slice(2), ["辛丑", "戊子"]);
  assert.deepEqual(midnight.slice(2), ["庚子", "丙子"]);
  assert.deepEqual(
    values({
      date: "1988-02-16",
      time: "00:00",
      dayBoundary: "midnight",
    }).slice(2),
    ["辛丑", "戊子"],
  );
});
test("午夜紫微晚子时设置不会污染后续子初盘", () => {
  const a = chart({ time: "23:30" }).candidates[0]!.ziwei;
  chart({ time: "23:30", dayBoundary: "midnight" });
  assert.deepEqual(chart({ time: "23:30" }).candidates[0]!.ziwei, a);
});
test("节气按绝对时刻，不随真太阳时经度改变年月柱", () => {
  const term = Solar.fromYmd(2024, 2, 4).getLunar().getJieQiTable()["立春"]!;
  const instant = Temporal.PlainDateTime.from(
    term.toYmdHms().replace(" ", "T"),
  ).toZonedDateTime("+08:00");
  const at = (seconds: number, longitude: number) => {
    const d = instant.add({ seconds }).toPlainDateTime();
    return values({
      date: d.toPlainDate().toString(),
      time: d.toPlainTime().toString(),
      longitude,
      timeBasis: "true-solar",
    }).slice(0, 2);
  };
  assert.deepEqual(at(-1, 75), ["癸卯", "乙丑"]);
  assert.deepEqual(at(1, 75), ["甲辰", "丙寅"]);
  assert.deepEqual(at(1, 135), at(1, 75));
});
test("同一瞬间跨时区的年月柱和起运绝对时刻一致", () => {
  const a = chart({ date: "2005-12-23", time: "08:37" }).candidates[0]!;
  const b = chart({
    date: "2005-12-22",
    time: "19:37",
    timeZone: "America/New_York",
    longitude: -74,
  }).candidates[0]!;
  assert.deepEqual(
    a.bazi.pillars.slice(0, 2).map((p) => p.value),
    b.bazi.pillars.slice(0, 2).map((p) => p.value),
  );
  assert.notEqual(a.bazi.dayMaster, b.bazi.dayMaster);
  assert.equal(a.bazi.cycles.startInstant, b.bazi.cycles.startInstant);
});
test("NOAA 公式 gamma=0 的解析校验", () =>
  assert.ok(
    Math.abs(
      equationOfTime(Temporal.PlainDateTime.from("2001-01-01T12:00")) -
        -2.90416896,
    ) < 1e-9,
  ));
test("真太阳时使用 UTC，夏令时不被重复加上", () => {
  const i = parseInput({
    ...base,
    date: "2000-07-01",
    time: "12:00",
    timeZone: "America/New_York",
    longitude: -75,
    timeBasis: "true-solar",
  });
  const t = timeAt(i, resolveBirth(i).toInstant());
  assert.equal(t.audit.offsetMinutes, -240);
  assert.equal(t.audit.longitudeCorrectionMinutes, -60);
  assert.equal(t.clock.hour, 10);
});
test("太阳时跨日期保留原时间且改变日时柱", () => {
  const c = chart({
    date: "2000-08-16",
    time: "00:30",
    longitude: 75,
    timeBasis: "true-solar",
  });
  assert.match(c.time!.trueSolar, /^2000-08-15T/);
  assert.match(c.time!.civil, /^2000-08-16T/);
  assert.equal(c.civilComparison!.changed, true);
});
test("时辰边界同时提供候选，不静默选盘", () => {
  const c = chart({ time: "05:00", uncertaintyMinutes: 3 });
  assert.equal(c.status, "ambiguous");
  assert.ok(c.candidates.length >= 2);
  assert.equal(
    new Set(c.candidates.map((x) => x.bazi.pillars[3]!.branch)).size,
    2,
  );
});
test("同一候选四柱内的出生区间保留起运范围", () => {
  const c = chart({ time: "04:00", uncertaintyMinutes: 120 });
  const candidate = c.candidates.find(
    (item) =>
      item.samples.some((sample) => sample.birthOffsetMinutes === -60) &&
      item.samples.some((sample) => sample.birthOffsetMinutes === 59),
  )!;
  assert.equal(candidate.bazi.cycles.uncertainty.status, "range");
  assert.equal(
    candidate.bazi.cycles.uncertainty.startInstant.earliest,
    "2003-06-25T15:00:00Z",
  );
  assert.equal(
    candidate.bazi.cycles.uncertainty.startInstant.latest,
    "2003-07-05T14:59:00Z",
  );
  assert(c.warnings.some((warning) => warning.includes("起运时刻")));
});
test("时辰未知返回 needs-input，而非伪造中午", () => {
  const c = chart({ time: null });
  assert.equal(c.status, "needs-input");
  assert.equal(c.candidates.length, 0);
});
test("农历闰月显式并与公历等价", () => {
  const p = parseInput({
    ...base,
    calendar: "lunar",
    date: "2023-02-01",
    leapMonth: true,
  });
  assert.equal(solarDate(p), "2023-03-22");
  assert.deepEqual(
    values({ calendar: "lunar", date: "2023-02-01", leapMonth: true }),
    values({ date: "2023-03-22" }),
  );
});
test("春节前出生保留实际所属的上一农历年", () => {
  const ziwei = buildChart(
    {
      ...base,
      date: "2000-01-15",
      time: "12:00",
      timeBasis: "civil",
    },
    [1999, 2000],
  ).candidates[0]!.ziwei;
  assert.match(ziwei.lunarDate, /一九九九年/);
  assert.equal(ziwei.settings.birthLunarYear, 1999);
  assert.deepEqual(
    ziwei.yearly.map((year) => year.year),
    [1999, 2000],
  );
});
test("不存在的闰月/日期、性别、经纬度、拼写和时间被拒绝", () => {
  for (const extra of [
    { calendar: "lunar", date: "2022-02-01", leapMonth: true },
    { date: "2001-02-29" },
    { gender: "other" },
    { longitude: 181 },
    { time: "25:30" },
    { timeZone: "Moon/Base" },
    { timeBasis: "solar-ish" },
    { timeBais: "civil" },
    { calendar: "lunar", date: "2023-02-01" },
    { provenance: {} },
    { provenance: { timeZoneSource: " " } },
    { provenance: { unknown: "x" } },
  ])
    assert.throws(() => chart(extra));
});
test("地点与时区来源元数据规范化并进入命盘绑定", () => {
  const provenance = {
    placeSource: " 用户提供的出生证明 ",
    longitudeSource: "公开地名库记录",
    timeZoneSource: "IANA Asia/Shanghai",
    verifiedAt: "2026-09-23",
  };
  const parsed = parseInput({ ...base, provenance });
  assert.deepEqual(parsed.provenance, {
    ...provenance,
    placeSource: provenance.placeSource.trim(),
  });
  assert.notEqual(chart().chartId, chart({ provenance }).chartId);
});
test("DST 缺失时间不得用 earlier/later 偷换", () => {
  for (const dstDisambiguation of ["reject", "earlier", "later"])
    assert.throws(
      () =>
        chart({
          date: "2024-03-10",
          time: "02:30",
          timeZone: "America/New_York",
          longitude: -74,
          dstDisambiguation,
        }),
      (error: unknown) =>
        error instanceof InputError &&
        error.code === "NONEXISTENT_LOCAL_TIME",
    );
});
test("DST 重复时间需要确认，earlier/later 保留实际差异", () => {
  const extra = {
    date: "2024-11-03",
    time: "01:30",
    timeZone: "America/New_York",
    longitude: -74,
  };
  assert.throws(() => chart(extra));
  const a = chart({ ...extra, dstDisambiguation: "earlier" }),
    b = chart({ ...extra, dstDisambiguation: "later" });
  assert.equal(
    Temporal.Instant.from(b.time!.instant).epochMilliseconds -
      Temporal.Instant.from(a.time!.instant).epochMilliseconds,
    3600000,
  );
});
test("历史中国夏令时被解析而非固定 +08", () =>
  assert.equal(
    resolveBirth(parseInput({ ...base, date: "1991-07-01", time: "12:00" }))
      .offset,
    "+09:00",
  ));
test("同输入与规则稳定，修改出生资料使 ID 失效", () => {
  assert.equal(chart().chartId, chart().chartId);
  assert.notEqual(chart().chartId, chart({ time: "06:00" }).chartId);
});
test("十神阴阳关系回归", () => {
  assert.equal(tenGod("辛", "乙"), "偏财");
  assert.equal(tenGod("辛", "戊"), "正印");
  assert.equal(tenGod("辛", "壬"), "伤官");
});
