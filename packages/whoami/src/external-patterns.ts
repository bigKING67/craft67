import { element, hiddenStemsOf, stemCombineElement, tenGod, TEN_GOD_GROUPS } from "./chart.js";

type Pillar = { position: string; stem: string; branch: string };
type Bazi = { dayMaster: string; pillars: Pillar[] };

const SRC = {
  outer: "https://donglishuzhai.net/chapter/3735.html",
  misc: "https://donglishuzhai.net/chapter/3760.html",
  combine: "https://donglishuzhai.net/chapter/3718.html",
} as const;

// 五行的三合局与三会方。
const FRAMES: Record<string, string[]> = {
  木: ["亥卯未", "寅卯辰"],
  火: ["寅午戌", "巳午未"],
  金: ["巳酉丑", "申酉戌"],
  水: ["申子辰", "亥子丑"],
  土: [],
};
const WEALTH: string[] = [...TEN_GOD_GROUPS.wealth];
const SEAL: string[] = [...TEN_GOD_GROUPS.seal];
const OFFICER_KILLER: string[] = [...TEN_GOD_GROUPS.officerKiller];
const FOOD_HURT: string[] = [...TEN_GOD_GROUPS.foodHurt];
const PEER: string[] = [...TEN_GOD_GROUPS.peer];

type Check = { condition: string; observed: boolean; quote?: string; source?: string; interpretation?: string };

/**
 * 外格候选：只核对《子平真诠》论外格用舍、论杂格中写明、且可由干支复算的入口与排除条件。
 * 原书对外格明确存疑（“若月令自有用神，豈可別尋外格”），因此最多给出 entry-observed，不判成格；
 * “身無氣”“支中字多”等原文未给阈值的说法，按下方 interpretation 注明的 whoami 解释复算。
 */
export function externalPatternCandidates(bazi: Bazi) {
  const day = bazi.dayMaster;
  const dayElement = element(day);
  const byPos = Object.fromEntries(bazi.pillars.map((p) => [p.position, p]));
  const visible = bazi.pillars.filter((p) => p.position !== "day");
  const branches = bazi.pillars.map((p) => p.branch);
  const gods = (stems: string[]) => stems.map((s) => tenGod(day, s));
  const visibleGods = gods(visible.map((p) => p.stem));
  const hasVisible = (targets: string[]) => visibleGods.some((g) => targets.includes(g));
  const monthMain = hiddenStemsOf(byPos.month!.branch)[0]!;
  // 月令本气是否比劫（“日與月同”）只作信息输出。
  const monthMainGod = tenGod(day, monthMain);
  const frameComplete = (el: string) => (FRAMES[el] ?? []).find((f) => [...f].every((b) => branches.includes(b)));
  const sameElementRoot = bazi.pillars.some((p) => hiddenStemsOf(p.branch).some((h) => element(h) === dayElement));
  // whoami 对“身無氣／日主無根”的解释：地支无同五行藏干、显干无比劫。原文无阈值；透印另作排除条件。
  const noStrength = !sameElementRoot && !hasVisible(PEER);
  const counts = new Map<string, number>();
  for (const b of branches) counts.set(b, (counts.get(b) ?? 0) + 1);
  const maxRepeat = Math.max(...counts.values());

  // 外格通则：干头无官煞（化格的合化之干除外，见下）。月令是否比劫只作信息，从格的月令本就不是比劫。
  const officerGate: Check = { condition: "年/月/时干透正官或七杀", observed: hasVisible(OFFICER_KILLER), quote: "大約要干頭無官無煞，方成外格", source: SRC.misc };
  const gate = [{ condition: "年/月/时干无正官、七杀", observed: !officerGate.observed, quote: officerGate.quote, source: SRC.misc }];

  // 入口齐全后才看排除条件：入口不全记 not-observed，避免日干相符即列出大量无关的 blocked。
  const candidate = (id: string, label: string, entry: Check[], ownBlockers: Check[], pending: string, gateBlocker: Check | null = officerGate) => {
    const blockers = gateBlocker && !ownBlockers.some((b) => b.condition === gateBlocker.condition) ? [...ownBlockers, gateBlocker] : ownBlockers;
    const complete = entry.every((c) => c.observed);
    return {
      id,
      label,
      status: !complete ? ("not-observed" as const) : blockers.some((b) => b.observed) ? ("blocked" as const) : ("entry-observed" as const),
      entry,
      blockers,
      pending,
    };
  };

  const dayCombine = ["month", "hour"]
    .map((pos) => ({ pos, stem: byPos[pos]!.stem, el: stemCombineElement(day, byPos[pos]!.stem) }))
    .find((x) => x.el);
  const transformEl = dayCombine?.el;

  const candidates = [
    candidate("one-element", "一方秀气", [
      { condition: `地支全${dayElement}之三合或三会`, observed: Boolean(frameComplete(dayElement)), quote: "取甲乙全亥卯未、寅卯辰，又生春月之類", source: SRC.misc },
      { condition: `月支在${dayElement}局内（得时）`, observed: Boolean(frameComplete(dayElement)?.includes(byPos.month!.branch)), source: SRC.misc },
    ], [
      { condition: "年/月/时干透正官或七杀", observed: hasVisible(OFFICER_KILLER), quote: "大約要干頭無官無煞，方成外格", source: SRC.misc },
    ], "“喜印露而體純”是喜忌而非入口；局是否纯、有无破局须宿主论证"),
    candidate("transform", "化格", [
      { condition: "日干与月干或时干五合", observed: Boolean(dayCombine), quote: "要化出之物，得時乘令，四支局全", source: SRC.misc },
      { condition: `月令本气属化神五行${transformEl ?? ""}`, observed: Boolean(transformEl && element(monthMain) === transformEl), source: SRC.misc },
      { condition: `地支全化神${transformEl ?? ""}之三合或三会`, observed: Boolean(transformEl && frameComplete(transformEl)), quote: "丁壬化木，地支全亥卯未、寅卯辰，而又生於春月", source: SRC.misc },
    ], [], "原书以日干合月干为例，未限定月干或时干；相合是否被间隔或争合破坏（《论十干合而不合》）须宿主论证；局不全者原书称次等",
    // 合化之干本身可能是官星（如丁壬之壬），不计入干头官煞。
    { ...officerGate, condition: "除合化之干外，年/月/时干透正官或七杀", observed: visible.some((p) => p.position !== dayCombine?.pos && OFFICER_KILLER.includes(tenGod(day, p.stem))) }),
    candidate("reverse-clash", "倒冲", [
      { condition: "年/月/时干无财、官", observed: !hasVisible([...WEALTH, "正官"]), quote: "四柱無財官而對面以沖之，要支中字多", source: SRC.misc },
      { condition: `同一地支至少三见（当前最多 ${maxRepeat} 见）`, observed: maxRepeat >= 3, source: SRC.misc, interpretation: "“支中字多”无阈值；whoami 按原书例（三午、四午）取至少三见" },
    ], [], "藏干中的财官、冲神是否被合住须宿主论证"),
    candidate("facing-sun", "朝阳", [
      { condition: "辛日", observed: day === "辛", source: SRC.misc },
      { condition: "年/月/时干见戊", observed: visible.some((p) => p.stem === "戊"), source: SRC.misc },
    ], [
      { condition: "年/月/时干见木或火", observed: visible.some((p) => ["木", "火"].includes(element(p.stem))), quote: "要干頭無木火，方成其格", source: SRC.misc },
    ], "原例为戊子时；时支与冲合关系须宿主论证"),
    candidate("combine-lu", "合禄", [
      { condition: "戊日或癸日", observed: day === "戊" || day === "癸", quote: "戊日庚申", source: SRC.misc },
      { condition: "时柱庚申", observed: byPos.hour!.stem + byPos.hour!.branch === "庚申", source: SRC.misc },
    ], [
      { condition: "年/月/时干透正官", observed: hasVisible(["正官"]), quote: "命無官星", source: SRC.misc },
    ], "藏干官星是否算“有官”原文未言，须宿主论证"),
    candidate("follow-wealth", "弃命从财", [
      { condition: "年/月/时干见财", observed: hasVisible(WEALTH), source: SRC.misc },
      { condition: "日主身无气", observed: noStrength, source: SRC.misc, interpretation: "地支无同五行藏干，且显干无比劫与印" },
    ], [
      { condition: "年/月/时干透印", observed: hasVisible(SEAL), quote: "若透印則身賴印生而不從", source: SRC.misc },
      { condition: "年/月/时干透正官或七杀", observed: hasVisible(OFFICER_KILLER), quote: "有官煞則…其格不成", source: SRC.misc },
    ], "“四柱皆財”无阈值，财势是否足以弃命须宿主论证"),
    candidate("follow-killer", "弃命从煞", [
      { condition: "年/月/时干见七杀", observed: hasVisible(["七杀"]), quote: "四柱皆煞，而日主無根", source: SRC.misc },
      { condition: "日主无根", observed: noStrength, source: SRC.misc, interpretation: "地支无同五行藏干，且显干无比劫与印" },
    ], [
      { condition: "年/月/时干透食神或伤官", observed: hasVisible(FOOD_HURT), quote: "若有傷食則煞受制而不從", source: SRC.misc },
      { condition: "年/月/时干透印", observed: hasVisible(SEAL), quote: "有印則…不從", source: SRC.misc },
    ], "“四柱皆煞”无阈值，煞势是否足以弃命须宿主论证"),
    candidate("well-rail", "井栏", [
      { condition: "庚日", observed: day === "庚", quote: "庚金生三、七月", source: SRC.misc },
      { condition: "月支辰或申（三、七月）", observed: ["辰", "申"].includes(byPos.month!.branch), source: SRC.misc, interpretation: "“三、七月”原页无注，whoami 按月建取辰、申" },
      { condition: "地支全申子辰", observed: [..."申子辰"].every((b) => branches.includes(b)), source: SRC.misc },
    ], [
      { condition: "干透丙丁或支有巳午", observed: visible.some((p) => ["丙", "丁"].includes(p.stem)) || branches.some((b) => ["巳", "午"].includes(b)), quote: "若透丙丁，有巳午…非井欄之格", source: SRC.misc },
    ], "月份口径有歧义，须宿主说明"),
    candidate("punish-combine", "刑合", [
      { condition: "癸日", observed: day === "癸", quote: "癸日甲寅時", source: SRC.misc },
      { condition: "时柱甲寅", observed: byPos.hour!.stem + byPos.hour!.branch === "甲寅", source: SRC.misc },
    ], [
      { condition: "干见庚或支见申", observed: visible.some((p) => p.stem === "庚") || branches.includes("申"), source: SRC.misc },
      { condition: "干见戊或己", observed: visible.some((p) => ["戊", "己"].includes(p.stem)), source: SRC.misc },
    ], "刑合取官之说是否成立须宿主论证"),
    candidate("distant-combine", "遥合（原书称此格可废）", [
      { condition: "辛日", observed: day === "辛", source: SRC.misc },
      { condition: "地支丑至少两见", observed: (counts.get("丑") ?? 0) >= 2, quote: "丑多則會巳而辛丑得官", source: SRC.misc, interpretation: "“丑多”无阈值，whoami 取至少两见" },
    ], [
      { condition: "支见子", observed: branches.includes("子"), source: SRC.misc },
      { condition: "干见丙丁戊己", observed: visible.some((p) => ["丙", "丁", "戊", "己"].includes(p.stem)), source: SRC.misc },
    ], "原书言“此格可廢”，只作候选记录"),
  ];

  return {
    scope: "外格候选：只核对《子平真诠》论外格用舍、论杂格写明且可由干支复算的入口与排除条件",
    gate,
    monthMainTenGod: monthMainGod,
    candidates,
    judgment: "unresolved" as const,
    sources: { ...SRC },
    limits: [
      "原书认为月令自有用神时不可别寻外格，“硬填入格，百無一是”；entry-observed 只表示可复算入口出现，须先论证正格不成立。",
      "入口齐全后才看排除条件：blocked 表示入口齐全但原文明言的排除条件（含干头官煞通则）出现；not-observed 表示入口不全；均不判正格成败。",
      "interpretation 标注的条件是 whoami 对原文无阈值说法的复算定义，不是原文；拱禄、魁罡等原书否定的杂格不列。",
      "从儿、从旺、从强等原书未载之格不在本模块内。",
    ],
  };
}
