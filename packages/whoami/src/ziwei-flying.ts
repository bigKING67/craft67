import iztro from "iztro";
import type { ziweiAt } from "./chart.js";
import { starLocator } from "./ziwei-transforms.js";

type Ziwei = ReturnType<typeof ziweiAt>;
const MUTAGENS = ["禄", "权", "科", "忌"] as const;

/**
 * 宫干飞化：每个本命宫以宫干按 iztro 同一张十干四化表化出四星，定位到星曜所在的本命宫。
 * kind=self 为化出落回本宫（自化，亦称离心自化）；kind=opposite 为化入对宫（对宫视角即向心自化）。
 * 只列落点，不判吉凶；庚、戊、壬等干的四化星各派有异，本表只代表 iztro 口径。
 */
export function ziweiFlyingTransforms(ziwei: Ziwei) {
  const { locate } = starLocator(ziwei.palaces);
  const palaces = ziwei.palaces.map((p) => ({
    palaceIndex: p.index,
    palace: p.name,
    stem: p.stem,
    flights: iztro.util
      .getMutagensByHeavenlyStem(p.stem as Parameters<typeof iztro.util.getMutagensByHeavenlyStem>[0])
      .map((star, i) => {
        const located = locate(star);
        return {
          mutagen: MUTAGENS[i]!,
          star,
          // 星曜不在本命盘或重名时保留 missing-star / ambiguous-star，不补猜落点。
          status: located.status,
          targets: located.targets.map((t) => ({
            palaceIndex: t.palaceIndex,
            palace: t.natalPalace,
            kind: t.palaceIndex === p.index ? ("self" as const) : t.palaceIndex === (p.index + 6) % 12 ? ("opposite" as const) : ("other" as const),
          })),
        };
      }),
  }));
  return {
    convention: "iztro 十干四化表（庚干：太阳、武曲、太阴、天同）；其他流派的庚、戊、壬干四化星不同时须另行说明",
    palaces,
    selfTransforms: palaces.flatMap((p) =>
      p.flights
        .filter((f) => f.targets.some((t) => t.kind === "self"))
        .map((f) => ({ palaceIndex: p.palaceIndex, palace: p.palace, stem: p.stem, mutagen: f.mutagen, star: f.star })),
    ),
  };
}
