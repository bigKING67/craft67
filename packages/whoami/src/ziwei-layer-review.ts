import type { ziweiTransforms } from "./ziwei-transforms.js";
import type { Evidence } from "./evidence.js";

type Transformations = ReturnType<typeof ziweiTransforms>;
type Entry = {
  layer: string;
  mutagen: string;
  natalPalace: string;
  yearlyPalace?: string | null;
};

// 只比较现有四化标签，不对权重、相消、吉凶或事件作判断。
export function ziweiLayerReview(t: Transformations) {
  return t.yearly.map(year => {
    const stars = new Map<string, Entry[]>();
    const gaps: { layer: string; star: string | null; mutagen: string; status: string }[] = [];
    const add = (star: string, entry: Entry) => stars.set(star, [...(stars.get(star) ?? []), entry]);
    for (const o of t.origin) {
      if (o.status !== "located") {
        gaps.push({ layer: "生年", star: o.stars.join("、") || null, mutagen: o.mutagen, status: o.status });
      } else {
        add(o.stars[0]!, { layer: "生年", mutagen: o.mutagen, natalPalace: o.targets[0]!.natalPalace });
      }
    }
    const layers = [
      ...t.decadals.filter(d => year.year >= d.yearRangeInclusive[0]! && year.year <= d.yearRangeInclusive[1]!)
        .map(d => ({ label: `大限${d.yearRangeInclusive.join("—")}`, transforms: d.transformations, yearly: false })),
      { label: `流年${year.year}`, transforms: year.transformations, yearly: true },
    ];
    for (const layer of layers) for (const item of layer.transforms) {
      if (item.status !== "located") {
        gaps.push({ layer: layer.label, star: item.star, mutagen: item.mutagen, status: item.status });
      } else {
        const target = item.targets[0]!;
        if (layer.yearly && target.scopePalace == null)
          gaps.push({ layer: layer.label, star: item.star, mutagen: item.mutagen, status: "missing-yearly-palace" });
        add(item.star!, {
          layer: layer.label, mutagen: item.mutagen, natalPalace: target.natalPalace,
          ...(layer.yearly ? { yearlyPalace: target.scopePalace ?? null } : {}),
        });
      }
    }
    return {
      year: year.year,
      contrasts: [...stars].filter(([, entries]) => new Set(entries.map(e => e.mutagen)).size > 1)
        .map(([star, entries]) => ({ star, entries })),
      gaps,
    };
  });
}

export function ziweiLayerFacts(e: Evidence) {
  return e.candidateIds.map(candidate => {
    const factId = `${candidate}.ziwei.transformations`;
    const value = e.facts.find(f => f.id === factId)!.value as Transformations;
    return { candidate, factId, ruleId: `${candidate}.R-ziwei-transformations`, years: ziweiLayerReview(value) };
  });
}

export function describeLayerEntry(entry: Entry): string {
  return `${entry.layer}化${entry.mutagen}（本命${entry.natalPalace}${"yearlyPalace" in entry
    ? `；流年宫职${entry.yearlyPalace ?? "未定位"}` : ""}）`;
}
