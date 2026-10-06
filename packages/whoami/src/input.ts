import { Temporal } from "@js-temporal/polyfill";
import { Lunar, LunarMonth } from "lunar-typescript";

export class InputError extends Error {
  constructor(
    public code: string,
    message: string,
  ) {
    super(message);
  }
}
export type BirthInput = {
  calendar: "solar" | "lunar";
  date: string;
  leapMonth: boolean;
  time: string | null;
  uncertaintyMinutes: number;
  place: string;
  longitude: number;
  timeZone: string;
  gender: "male" | "female";
  timeBasis: "true-solar" | "civil";
  dayBoundary: "zi" | "midnight";
  dstDisambiguation: "reject" | "earlier" | "later";
  provenance?: {
    placeSource?: string;
    longitudeSource?: string;
    timeZoneSource?: string;
    verifiedAt?: string;
  };
};
export function object(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new InputError("INVALID_INPUT", `${label} 必须是对象`);
  return value as Record<string, unknown>;
}
export function parseInput(raw: unknown): BirthInput {
  const x = object(raw, "出生资料");
  const allowed = [
    "calendar",
    "date",
    "leapMonth",
    "time",
    "uncertaintyMinutes",
    "place",
    "longitude",
    "timeZone",
    "gender",
    "timeBasis",
    "dayBoundary",
    "dstDisambiguation",
    "provenance",
  ];
  for (const key of Object.keys(x))
    if (!allowed.includes(key))
      throw new InputError(
        "UNKNOWN_FIELD",
        `未知字段 ${key}；避免拼写错误被静默忽略`,
      );
  const choose = <T extends string>(
    key: string,
    values: readonly T[],
    fallback?: T,
  ): T => {
    const v = x[key] ?? fallback;
    if (!values.includes(v as T))
      throw new InputError(
        "INVALID_INPUT",
        `${key} 必须为 ${values.join(" / ")}`,
      );
    return v as T;
  };
  const calendar = choose("calendar", ["solar", "lunar"]);
  if (typeof x.date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(x.date))
    throw new InputError("INVALID_DATE", "date 使用 YYYY-MM-DD");
  const year = Number(x.date.slice(0, 4));
  if (year < 1901 || year > 2098)
    throw new InputError("DATE_RANGE", "首版出生年份支持 1901–2098");
  if (calendar === "lunar" && typeof x.leapMonth !== "boolean")
    throw new InputError(
      "MISSING_LEAP_MONTH",
      "农历输入必须明确 leapMonth（是否闰月）",
    );
  if (x.leapMonth !== undefined && typeof x.leapMonth !== "boolean")
    throw new InputError("INVALID_INPUT", "leapMonth 必须是布尔值");
  if (calendar === "solar" && x.leapMonth === true)
    throw new InputError("INVALID_INPUT", "公历输入不能设置闰月");
  if (
    x.time !== null &&
    (typeof x.time !== "string" || !/^\d{2}:\d{2}(:\d{2})?$/.test(x.time))
  )
    throw new InputError(
      "INVALID_TIME",
      "time 使用 HH:mm[:ss]，未知请明确传 null",
    );
  if (x.time !== null) {
    try {
      Temporal.PlainTime.from(x.time as string);
    } catch {
      throw new InputError("INVALID_TIME", "出生时间无效");
    }
  }
  const uncertainty = x.uncertaintyMinutes ?? 0;
  if (
    typeof uncertainty !== "number" ||
    !Number.isFinite(uncertainty) ||
    uncertainty < 0 ||
    uncertainty > 120
  )
    throw new InputError(
      "INVALID_INPUT",
      "uncertaintyMinutes 必须在 0–120 之间；更宽范围请先确认时辰",
    );
  if (typeof x.place !== "string" || !x.place.trim())
    throw new InputError("MISSING_PLACE", "请填写出生地点 place");
  if (
    typeof x.longitude !== "number" ||
    !Number.isFinite(x.longitude) ||
    Math.abs(x.longitude) > 180
  )
    throw new InputError(
      "INVALID_LONGITUDE",
      "longitude 必须为 -180 至 180，经度东正西负",
    );
  if (typeof x.timeZone !== "string" || !x.timeZone || /^[+-]/.test(x.timeZone))
    throw new InputError(
      "INVALID_TIMEZONE",
      "timeZone 必须是 IANA 地区时区，如 Asia/Shanghai，不能仅给 UTC 偏移",
    );
  try {
    Temporal.Now.instant().toZonedDateTimeISO(x.timeZone);
  } catch {
    throw new InputError("INVALID_TIMEZONE", "无法识别 IANA 时区");
  }
  let provenance: BirthInput["provenance"];
  if (x.provenance !== undefined) {
    const rawProvenance = object(x.provenance, "provenance");
    const allowedProvenance = [
      "placeSource",
      "longitudeSource",
      "timeZoneSource",
      "verifiedAt",
    ];
    for (const key of Object.keys(rawProvenance))
      if (!allowedProvenance.includes(key))
        throw new InputError(
          "UNKNOWN_FIELD",
          `provenance 未知字段 ${key}`,
        );
    provenance = {};
    for (const key of allowedProvenance) {
      const value = rawProvenance[key];
      if (value === undefined) continue;
      if (typeof value !== "string" || !value.trim())
        throw new InputError(
          "INVALID_INPUT",
          `provenance.${key} 必须是非空文字`,
        );
      provenance[key as keyof NonNullable<BirthInput["provenance"]>] =
        value.trim();
    }
    if (!Object.keys(provenance).length)
      throw new InputError("INVALID_INPUT", "provenance 至少提供一项来源");
  }
  const input: BirthInput = {
    calendar,
    date: x.date,
    leapMonth: x.leapMonth === true,
    time: x.time as string | null,
    uncertaintyMinutes: uncertainty,
    place: x.place.trim(),
    longitude: x.longitude,
    timeZone: x.timeZone,
    gender: choose("gender", ["male", "female"]),
    timeBasis: choose("timeBasis", ["true-solar", "civil"], "true-solar"),
    dayBoundary: choose("dayBoundary", ["zi", "midnight"], "zi"),
    dstDisambiguation: choose(
      "dstDisambiguation",
      ["reject", "earlier", "later"],
      "reject",
    ),
    ...(provenance ? { provenance } : {}),
  };
  solarDate(input); // Check real month/day and leap-month existence, before any computation.
  return input;
}
export function solarDate(input: BirthInput): string {
  try {
    if (input.calendar === "solar")
      return Temporal.PlainDate.from(input.date).toString();
    const [year, month, day] = input.date.split("-").map(Number) as [
      number,
      number,
      number,
    ];
    const signedMonth = input.leapMonth ? -month : month;
    const lm = LunarMonth.fromYm(year, signedMonth);
    if (!lm || month < 1 || month > 12 || day < 1 || day > lm.getDayCount())
      throw new Error("invalid lunar date");
    return Lunar.fromYmd(year, signedMonth, day).getSolar().toYmd();
  } catch {
    throw new InputError("INVALID_DATE", "日期或农历闰月不存在");
  }
}
