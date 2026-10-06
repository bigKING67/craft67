import { Temporal } from "@js-temporal/polyfill";
import { InputError, solarDate, type BirthInput } from "./input.js";

// NOAA fractional-year approximation. 2 min is a screening margin, not a certified error bound.
export const SOLAR_SCREENING_MINUTES = 2;
export type LocalDateTimeResolution =
  | { status: "unique"; value: Temporal.ZonedDateTime }
  | {
      status: "ambiguous";
      earlier: Temporal.ZonedDateTime;
      later: Temporal.ZonedDateTime;
    }
  | { status: "nonexistent" };

export function inspectLocalDateTime(
  plain: Temporal.PlainDateTime,
  timeZone: string,
): LocalDateTimeResolution {
  const earlier = plain.toZonedDateTime(timeZone, {
    disambiguation: "earlier",
  });
  const later = plain.toZonedDateTime(timeZone, {
    disambiguation: "later",
  });
  const earlierMatches = earlier.toPlainDateTime().equals(plain);
  const laterMatches = later.toPlainDateTime().equals(plain);
  if (!earlierMatches || !laterMatches) return { status: "nonexistent" };
  if (Temporal.ZonedDateTime.compare(earlier, later) !== 0)
    return { status: "ambiguous", earlier, later };
  return { status: "unique", value: earlier };
}

export function equationOfTime(utc: Temporal.PlainDateTime): number {
  const hour = utc.hour + utc.minute / 60 + utc.second / 3600;
  const gamma =
    ((2 * Math.PI) / utc.daysInYear) * (utc.dayOfYear - 1 + (hour - 12) / 24);
  return (
    229.18 *
    (0.000075 +
      0.001868 * Math.cos(gamma) -
      0.032077 * Math.sin(gamma) -
      0.014615 * Math.cos(2 * gamma) -
      0.040849 * Math.sin(2 * gamma))
  );
}
export function resolveBirth(input: BirthInput): Temporal.ZonedDateTime {
  if (input.time === null)
    throw new InputError("MISSING_TIME", "出生时辰未知，无法生成唯一完整命盘");
  const plain = Temporal.PlainDateTime.from(
    `${solarDate(input)}T${input.time}`,
  );
  let resolution: LocalDateTimeResolution;
  try {
    resolution = inspectLocalDateTime(plain, input.timeZone);
  } catch {
    throw new InputError(
      "INVALID_TIMEZONE",
      "无法用给定 IANA 时区解析出生时间",
    );
  }
  if (resolution.status === "nonexistent")
    throw new InputError(
      "NONEXISTENT_LOCAL_TIME",
      "夏令时跳变导致该钟表时间不存在，请更正出生资料",
    );
  if (resolution.status === "ambiguous") {
    if (input.dstDisambiguation === "reject")
      throw new InputError(
        "AMBIGUOUS_LOCAL_TIME",
        "出生时间处于夏令时重复区间，请核对历史时区并明确 dstDisambiguation=earlier 或 later",
      );
    return resolution[input.dstDisambiguation];
  }
  return resolution.value;
}
export function timeAt(
  input: BirthInput,
  instant: Temporal.Instant,
  solarShiftMinutes = 0,
) {
  const civil = instant.toZonedDateTimeISO(input.timeZone);
  const utc = instant.toZonedDateTimeISO("UTC").toPlainDateTime();
  const eq = equationOfTime(utc);
  const offsetMinutes = civil.offsetNanoseconds / 60e9;
  const longitudeCorrectionMinutes = 4 * input.longitude - offsetMinutes;
  const trueSolar = utc.add({
    milliseconds: Math.round(
      (4 * input.longitude + eq + solarShiftMinutes) * 60_000,
    ),
  });
  const clock =
    input.timeBasis === "true-solar" ? trueSolar : civil.toPlainDateTime();
  return {
    clock,
    audit: {
      instant: instant.toString(),
      civil: civil.toString(),
      trueSolar: trueSolar.toString(),
      chartClock: clock.toString(),
      offsetMinutes,
      longitudeCorrectionMinutes,
      equationOfTimeMinutes: eq,
      totalCorrectionMinutes: longitudeCorrectionMinutes + eq,
      model: "NOAA fractional-year equation of time",
      solarShiftMinutes,
      screeningMarginMinutes:
        input.timeBasis === "true-solar" ? SOLAR_SCREENING_MINUTES : 0,
    },
  };
}
