import type { Chart } from "./chart.js";

type Ziwei = Chart["candidates"][number]["ziwei"];
const MUTAGENS = ["禄", "权", "科", "忌"] as const;

/** 按星名定位本命物理宫；缺星、重名保持 missing-star / ambiguous-star，不取第一个。生年、运限、流月与飞化共用。 */
type LocatorStar = { name: string; mutagen?: string };
type LocatorPalace = {
  index: number;
  name: string;
  branch: string;
  majorStars: LocatorStar[];
  minorStars: LocatorStar[];
  adjectiveStars: LocatorStar[];
};
// 参数只取结构字段，不依赖 Chart 类型，chart.ts 构建流月时也能调用。
export function starLocator(palaces: LocatorPalace[]) {
  const stars = palaces.flatMap(p =>
    [...p.majorStars, ...p.minorStars, ...p.adjectiveStars].map(s => ({
      name: s.name, birthMutagen: s.mutagen,
      palaceIndex: p.index, natalPalace: p.name, branch: p.branch,
    })),
  );
  const locate = (starName: string | undefined, names?: string[]) => {
    const targets = starName ? stars.filter(s => s.name === starName).map(s => ({
      palaceIndex: s.palaceIndex, natalPalace: s.natalPalace, branch: s.branch,
      ...(names ? { scopePalace: names[s.palaceIndex] ?? null } : {}),
    })) : [];
    return {
      star: starName ?? null,
      status: !starName ? "missing-transform" : targets.length === 0 ? "missing-star" : targets.length > 1 ? "ambiguous-star" : "located",
      targets,
    };
  };
  return { stars, locate };
}

export function ziweiTransforms(z: Ziwei) {
  const { stars, locate } = starLocator(z.palaces);
  return {
    origin: MUTAGENS.map(mutagen => ({
      scope: "origin", mutagen,
      stars: stars.filter(s => s.birthMutagen === mutagen).map(s => s.name),
      targets: stars.filter(s => s.birthMutagen === mutagen).map(s => ({
        star: s.name, palaceIndex: s.palaceIndex, natalPalace: s.natalPalace, branch: s.branch,
      })),
      status: stars.filter(s => s.birthMutagen === mutagen).length === 1 ? "located" : "unresolved",
    })),
    decadals: z.decadals
      .filter(d => z.yearly.some(y => y.year >= d.yearRange[0]! && y.year <= d.yearRange[1]!))
      .map(d => ({
        scope: "decadal", stem: d.stem, branch: d.branch,
        decadalLifePalace: d.palace,
        ageRange: d.ageRange,
        yearRangeInclusive: d.yearRange,
        boundary: "lunar-new-year",
        transformations: MUTAGENS.map((mutagen, i) => ({mutagen, ...locate(d.mutagen[i])})),
      })),
    yearly: z.yearly.map(y => ({
      scope: "yearly", year: y.year, boundary: y.boundary, stem: y.stem, branch: y.branch,
      transformations: MUTAGENS.map((mutagen, i) => ({mutagen, ...locate(y.mutagen[i], y.palaceNames)})),
    })),
    limits: [
      "大限只列与请求流年相交者；yearRangeInclusive 两端均为农历年份标签，不是公历元旦或生日边界。",
      "本命落宫是星曜在原盘的固定位置；流年 scopePalace 是同一位置在该流年承担的宫职，二者不可混称。",
      "未提供大限宫职映射，不由本命宫名猜测；本模块不计算宫干飞化、自化或事件吉凶。",
      "缺失或重名保留 unresolved/missing/ambiguous 状态，不猜测星曜落宫；重复四化层不计为独立概率证据。",
    ],
  };
}
