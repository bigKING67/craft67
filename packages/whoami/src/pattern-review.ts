import { element, STEMS, stemCombineElement, TEN_GOD_GROUPS, type Chart } from "./chart.js";

type Bazi = Chart["candidates"][number]["bazi"];

const SRC = {
  rescue: "https://donglishuzhai.net/chapter/3722.html",
  change: "https://donglishuzhai.net/chapter/3723.html",
  officer: "https://donglishuzhai.net/chapter/3744.html",
  seal: "https://donglishuzhai.net/chapter/3748.html",
  food: "https://donglishuzhai.net/chapter/3750.html",
  killer: "https://donglishuzhai.net/chapter/3752.html",
  hurt: "https://donglishuzhai.net/chapter/3754.html",
} as const;
// v3 新增章节单独列出：输出的 sources 在 v2 中不得变化（evidence v2 已冻结）。
const SRC_V3 = {
  useGod: "https://donglishuzhai.net/chapter/3721.html",
  blade: "https://donglishuzhai.net/chapter/3756.html",
  lu: "https://donglishuzhai.net/chapter/3758.html",
} as const;

const WEALTH: string[] = [...TEN_GOD_GROUPS.wealth];
const SEAL: string[] = [...TEN_GOD_GROUPS.seal];
const FOOD_HURT: string[] = [...TEN_GOD_GROUPS.foodHurt];

type Check = {
  id: string;
  category: "support" | "risk" | "rescue";
  label: string;
  /** 每组至少一干在年/月/时透出。 */
  groups: string[][];
  /** 这些十神都不得透出（如“食帶煞而無財”）。 */
  absent?: string[];
  /** 这些十神的显干须被另一显干五合（不计日干，《论十干合而不合》“合日干不爲合去”）。 */
  combinedWith?: string[];
  quote: string;
  source: string;
  pending: string;
};

// 各行只把原文点名、可由显干机械核对的组合做成前提；引文为东篱书斋转录本原文（繁体），不含校注与按语。
const PATTERNS: { id: string; label: string; monthTenGods: string[]; checks: Check[] }[] = [
  {
    id: "officer", label: "正官格", monthTenGods: ["正官"],
    checks: [
      { id: "wealth-seal", category: "support", label: "官逢财印", groups: [WEALTH, SEAL], quote: "官逢財印，又無刑沖破害，官格成也", source: SRC.rescue, pending: "刑冲破害属地支条件；财印是否相碍、相合（《论正官》“兩不相礙，其貴也大”）未裁定" },
      { id: "hurt", category: "risk", label: "官逢伤官", groups: [["伤官"]], quote: "官逢傷尅刑沖，官格敗也", source: SRC.rescue, pending: "伤官能否克官、有无印解未裁定" },
      { id: "wealth-hurt", category: "risk", label: "官逢财又逢伤（带忌）", groups: [WEALTH, ["伤官"]], quote: "正官逢財而又逢傷", source: SRC.rescue, pending: "带忌程度与救应未裁定" },
      { id: "hurt-seal", category: "rescue", label: "伤官透印以解", groups: [["伤官"], SEAL], quote: "官逢傷，而透印以解之", source: SRC.rescue, pending: "印能否制伤护官未裁定，出现不等于救应完成" },
      { id: "hurt-seal-wealth", category: "risk", label: "透伤用印又见财", groups: [["伤官"], SEAL, WEALTH], quote: "官格透傷用印者，又忌見財", source: SRC.officer, pending: "原文另举财合、制伤反成贵格之例，须看合与位置" },
      { id: "mixed-killer", category: "risk", label: "官杀混杂", groups: [["七杀"]], quote: "混煞貴乎取清", source: SRC.officer, pending: "是否合煞、制煞而取清未裁定；地支混杂原书口径不一，仅核显干" },
    ],
  },
  {
    id: "killer", label: "七杀格", monthTenGods: ["七杀"],
    checks: [
      { id: "food-control", category: "support", label: "煞逢食制", groups: [["食神"]], quote: "煞用食制者，上也", source: SRC.killer, pending: "身强与否（《论用神成败救应》“身强七煞逢制”）及制煞是否得宜未裁定" },
      { id: "seal", category: "support", label: "煞用印", groups: [SEAL], quote: "七煞用印者…煞印有情，便爲貴格", source: SRC.killer, pending: "煞印是否有情（原例依月令同根）未裁定" },
      { id: "wealth-no-control", category: "risk", label: "煞逢财无制", groups: [WEALTH], absent: ["食神"], quote: "七煞逢財無制，七煞格敗也", source: SRC.rescue, pending: "伤官、印等其他制化是否存在及有效未裁定" },
      { id: "food-wealth", category: "risk", label: "食制而露财", groups: [["食神"], WEALTH], quote: "不宜露財透印，以財能轉食生煞", source: SRC.killer, pending: "原文有“財先食後”反成大贵的次序例外，须看干序与位置" },
      { id: "food-seal", category: "risk", label: "食制而透印（带忌）", groups: [["食神"], SEAL], quote: "七煞逢食制，而又逢印", source: SRC.rescue, pending: "原文有“印先食後”的次序例外；印是否去食未裁定" },
      { id: "food-seal-wealth", category: "rescue", label: "逢财去印存食", groups: [["食神"], SEAL, WEALTH], quote: "印來護煞，而逢財以去印存食", source: SRC.rescue, pending: "财能否去印存食未裁定，出现不等于救应完成" },
      { id: "mixed-officer", category: "risk", label: "官煞混杂", groups: [["正官"]], quote: "或去官，或去煞，取清則貴", source: SRC.killer, pending: "去留取清未裁定；仅核显干" },
    ],
  },
  {
    id: "seal", label: "印格（正偏同论）", monthTenGods: SEAL,
    checks: [
      { id: "officer", category: "support", label: "官印双全", groups: [["正官"]], quote: "官印雙全", source: SRC.rescue, pending: "官星是否清纯（《论印》“只要官星清純”）未裁定" },
      { id: "killer", category: "support", label: "印轻逢煞", groups: [["七杀"]], quote: "印輕逢煞", source: SRC.rescue, pending: "印轻与否未裁定；同一组合在身强印重时为败（见 killer-heavy）" },
      { id: "killer-heavy", category: "risk", label: "身强印重而透煞", groups: [["七杀"]], quote: "身强印重而透煞", source: SRC.rescue, pending: "身强、印重与否未裁定；与 killer 同一显干组合，方向取决于强弱" },
      { id: "food-hurt", category: "support", label: "身印两旺用食伤泄气", groups: [FOOD_HURT], quote: "身印兩旺而用食傷洩氣", source: SRC.rescue, pending: "身印是否两旺未裁定；印浅身轻为寒贫之局" },
      { id: "wealth", category: "support", label: "印多逢财", groups: [WEALTH], quote: "印多逢財而財透根輕", source: SRC.rescue, pending: "印多、财根轻与否未裁定；同一组合在印轻时为败（见 wealth-light）" },
      { id: "wealth-light", category: "risk", label: "印轻逢财", groups: [WEALTH], quote: "印輕逢財", source: SRC.rescue, pending: "印轻与否未裁定；《论印》另允印多用财，两说须按条件取" },
      { id: "killer-food", category: "support", label: "用煞兼带伤食", groups: [["七杀"], FOOD_HURT], quote: "用煞而兼帶傷食者…皆爲貴格", source: SRC.seal, pending: "作用关系未裁定" },
      { id: "food-wealth", category: "risk", label: "印透食神又遇财（带忌）", groups: [FOOD_HURT, WEALTH], quote: "印透食神…而又遇財露", source: SRC.rescue, pending: "带忌程度与救应未裁定" },
      { id: "killer-wealth", category: "risk", label: "透煞生印又透财（带忌）", groups: [["七杀"], WEALTH], quote: "透煞以生印，而又透財", source: SRC.rescue, pending: "带忌程度与救应未裁定" },
      { id: "wealth-robber", category: "rescue", label: "印逢财而劫财以解", groups: [WEALTH, ["劫财"]], quote: "印逢財，而劫財以解之", source: SRC.rescue, pending: "劫财能否解财存印、是否合财未裁定，出现不等于救应完成" },
    ],
  },
  {
    id: "food", label: "食神格", monthTenGods: ["食神"],
    checks: [
      { id: "wealth", category: "support", label: "食神生财", groups: [WEALTH], quote: "食神生財，美格也。財要有根", source: SRC.food, pending: "财是否有根、身是否强未裁定" },
      { id: "killer-no-wealth", category: "support", label: "食带煞而无财", groups: [["七杀"]], absent: WEALTH, quote: "食帶煞而無財", source: SRC.rescue, pending: "食能否制煞未裁定" },
      { id: "killer-seal", category: "support", label: "弃食就煞而透印", groups: [["七杀"], SEAL], quote: "棄食就煞而透印", source: SRC.rescue, pending: "是否弃食就煞未裁定" },
      { id: "owl", category: "risk", label: "食神逢枭", groups: [["偏印"]], quote: "食神逢梟", source: SRC.rescue, pending: "正印是否同论夺食原文未分（《论食神》“印來奪食”）；另查 seal-any" },
      { id: "seal-any", category: "risk", label: "印来夺食（未分偏正）", groups: [SEAL], quote: "印來奪食，透財以解", source: SRC.food, pending: "须就全局之势；正印是否同样夺食未裁定" },
      { id: "officer", category: "risk", label: "食神忌官", groups: [["正官"]], quote: "食神忌官，金水不忌", source: SRC.food, pending: "日主金水与季节条件须宿主核对（见 dayMasterElement）" },
      { id: "wealth-killer", category: "risk", label: "生财露煞", groups: [WEALTH, ["七杀"]], quote: "生財露煞，食神格敗也", source: SRC.rescue, pending: "原文另有“財先煞後”次序例外" },
      { id: "killer-seal-wealth", category: "risk", label: "带煞印又逢财（带忌）", groups: [["七杀"], SEAL, WEALTH], quote: "食神帶煞印而又逢財", source: SRC.rescue, pending: "带忌程度与救应未裁定" },
      { id: "owl-killer", category: "rescue", label: "逢枭而就煞成格", groups: [["偏印"], ["七杀"]], quote: "食逢梟，而就煞以成格", source: SRC.rescue, pending: "出现不等于救应完成" },
      { id: "owl-wealth", category: "rescue", label: "逢枭而生财护食", groups: [["偏印"], WEALTH], quote: "或生財以護食", source: SRC.rescue, pending: "出现不等于救应完成" },
    ],
  },
  {
    id: "hurt", label: "伤官格", monthTenGods: ["伤官"],
    checks: [
      { id: "wealth", category: "support", label: "伤官生财", groups: [WEALTH], quote: "只要身强而財有根，便爲貴格", source: SRC.hurt, pending: "身强、财根未裁定" },
      { id: "seal", category: "support", label: "伤官佩印", groups: [SEAL], quote: "傷官佩印而傷官旺、印有根", source: SRC.rescue, pending: "伤官旺、印有根未裁定；伤轻身旺为败（见 seal-light）" },
      { id: "seal-light", category: "risk", label: "佩印而伤轻身旺", groups: [SEAL], quote: "佩印而傷輕身旺", source: SRC.rescue, pending: "伤轻身旺与否未裁定；与 seal 同一显干组合" },
      { id: "killer-seal", category: "support", label: "伤旺身弱透煞印", groups: [["七杀"], SEAL], quote: "傷官旺、身主弱而透煞印", source: SRC.rescue, pending: "伤旺身弱未裁定" },
      { id: "killer-no-wealth", category: "support", label: "伤官带煞而无财", groups: [["七杀"]], absent: WEALTH, quote: "傷官帶煞而無財", source: SRC.rescue, pending: "作用关系未裁定" },
      { id: "wealth-seal", category: "support", label: "财印两清", groups: [WEALTH, SEAL], quote: "只要干頭兩清而不相礙", source: SRC.hurt, pending: "财印是否相碍（原例以他干间隔）未裁定" },
      { id: "officer", category: "risk", label: "伤官见官", groups: [["正官"]], quote: "傷官非金水而見官", source: SRC.rescue, pending: "日主金水与季节条件须宿主核对（见 dayMasterElement）" },
      { id: "wealth-killer", category: "risk", label: "生财而带煞", groups: [WEALTH, ["七杀"]], quote: "生財而帶煞身輕", source: SRC.rescue, pending: "身轻与否未裁定；煞逢合则为救（见 wealth-killer-combined）" },
      { id: "wealth-killer-combined", category: "rescue", label: "生财透煞而煞逢合", groups: [WEALTH, ["七杀"]], quote: "傷官生財，透煞而煞逢合", source: SRC.rescue, pending: "煞是否被合须看干合关系，出现不等于救应完成" },
    ],
  },
];

// 以下两格为 evidence v3 新增：入口按禄位、刃位而非十神（戊日午月为阳刃，但午本气丁为戊之正印）。
const LU: Record<string, string> = { 甲: "寅", 乙: "卯", 丙: "巳", 丁: "午", 戊: "巳", 己: "午", 庚: "申", 辛: "酉", 壬: "亥", 癸: "子" };
const BLADE: Record<string, string> = { 甲: "卯", 丙: "午", 戊: "午", 庚: "酉", 壬: "子" };
const OFFICER_KILLER: string[] = [...TEN_GOD_GROUPS.officerKiller];
const V3_PATTERNS: { id: string; label: string; checks: Check[] }[] = [
  {
    id: "lu", label: "建禄月劫格",
    checks: [
      { id: "officer-wealth-seal", category: "support", label: "透官而逢财印", groups: [["正官"], [...WEALTH, ...SEAL]], quote: "透官而逢財印", source: SRC.rescue, pending: "财印是否以官相隔而两不相伤（《论建禄月劫》）须看干位" },
      { id: "lone-officer", category: "risk", label: "孤官无辅", groups: [["正官"]], absent: [...WEALTH, ...SEAL], quote: "不可孤官無輔", source: SRC_V3.lu, pending: "原文言格局更小，属程度而非破格" },
      { id: "officer-hurt", category: "risk", label: "用官而透伤食", groups: [["正官"], FOOD_HURT], quote: "若透傷食，便爲破格", source: SRC_V3.lu, pending: "《论用神成败救应》只以透伤为带忌，两说宽严不同" },
      { id: "officer-hurt-combined", category: "rescue", label: "用官遇伤而伤被合", groups: [["正官"], ["伤官"]], combinedWith: ["伤官"], quote: "用官遇傷而傷被合", source: SRC.rescue, pending: "合是否被间隔或争合破坏须宿主论证" },
      { id: "wealth-food", category: "support", label: "透财而逢食伤", groups: [WEALTH, FOOD_HURT], quote: "透財而逢食傷", source: SRC.rescue, pending: "转劫生财是否成立须宿主论证" },
      { id: "wealth-no-food", category: "risk", label: "用财而不透伤食", groups: [WEALTH], absent: FOOD_HURT, quote: "用財而不透傷食，難於發福", source: SRC_V3.lu, pending: "原文另允一财多根者取富" },
      { id: "wealth-killer", category: "risk", label: "透财而逢煞", groups: [WEALTH, ["七杀"]], quote: "透財而逢煞", source: SRC.rescue, pending: "煞被合则为救（见 wealth-killer-combined）" },
      { id: "wealth-killer-combined", category: "rescue", label: "用财带煞而煞被合", groups: [WEALTH, ["七杀"]], combinedWith: ["七杀"], quote: "用財帶煞而煞被合", source: SRC.rescue, pending: "合是否成立须宿主论证" },
      { id: "killer-control", category: "support", label: "透煞而遇制伏", groups: [["七杀"], ["食神"]], quote: "透煞而遇制伏", source: SRC.rescue, pending: "制伏亦可由合与会局完成，只核食神显干" },
      { id: "food-hurt-only", category: "support", label: "无财官而用伤食泄秀", groups: [FOOD_HURT], absent: [...WEALTH, ...OFFICER_KILLER], quote: "無財官而用傷食，洩其太過", source: SRC_V3.lu, pending: "原文限春木秋金，须结合日主五行（dayMasterElement）与月令论证" },
      { id: "no-wealth-officer", category: "risk", label: "无财官而透煞印", groups: [["七杀", ...SEAL]], absent: ["正官", ...WEALTH], quote: "無財官，透煞印", source: SRC.rescue, pending: "败格判断仍须看全局" },
      { id: "officer-killer", category: "risk", label: "官煞竞出", groups: [["正官"], ["七杀"]], quote: "官煞競出，必須取清方爲貴格", source: SRC_V3.lu, pending: "合煞留官或制煞留官是否成立须宿主论证" },
    ],
  },
  {
    id: "blade", label: "阳刃格",
    checks: [
      { id: "officer-killer-wealth-seal", category: "support", label: "透官煞而露财印不见伤官", groups: [OFFICER_KILLER, [...WEALTH, ...SEAL]], absent: ["伤官"], quote: "陽刃透官煞而露財印，不見傷官", source: SRC.rescue, pending: "官煞根深与否（《论阳刃》“官煞露而根深，其貴也大”）未裁定" },
      { id: "no-officer-killer", category: "risk", label: "阳刃无官煞", groups: [], absent: OFFICER_KILLER, quote: "陽刃無官煞，陽刃格敗也", source: SRC.rescue, pending: "只核显干；藏干官煞须宿主论证" },
      { id: "officer", category: "support", label: "阳刃用官", groups: [["正官"]], quote: "陽刃用官，透刃不慮", source: SRC_V3.blade, pending: "官是否得力须宿主论证" },
      { id: "killer-blade", category: "risk", label: "露煞透刃（阳干之刃即劫财）", groups: [["七杀"], ["劫财"]], quote: "陽刃露煞，透刃無成", source: SRC_V3.blade, pending: "阳干之刃与七杀五合，实即合煞；须看位置" },
      { id: "officer-hurt", category: "risk", label: "透官而又被伤", groups: [["正官"], ["伤官"]], quote: "陽刃透官而又被傷", source: SRC.rescue, pending: "有无印护须宿主论证" },
      { id: "killer-combined", category: "risk", label: "透煞而又被合", groups: [["七杀"]], combinedWith: ["七杀"], quote: "透煞而又被合", source: SRC.rescue, pending: "合是否成立须宿主论证" },
      { id: "food-hurt-seal", category: "rescue", label: "带伤食而重印以护", groups: [OFFICER_KILLER, FOOD_HURT, SEAL], quote: "帶傷食而重印以護之", source: SRC.rescue, pending: "印是否“重”不能机械核对" },
      { id: "wealth", category: "risk", label: "阳刃用财", groups: [WEALTH], absent: OFFICER_KILLER, quote: "陽刃用財，格所不喜", source: SRC_V3.blade, pending: "原文另允财根深而用伤食转刃生财者就富" },
      { id: "mixed", category: "risk", label: "官煞杂而取清", groups: [["正官"], ["七杀"]], quote: "官煞雜而取清之", source: SRC_V3.blade, pending: "“雜”据中州本校改（原作“輕”）；原文又言“利於留煞”" },
    ],
  },
];

const ROLES = ["main", "middle", "residual"] as const;
const isCombine = (a: string, b: string) => Boolean(stemCombineElement(a, b));

/**
 * 正官、七杀、印、食神、伤官五格的显干前提核对（财格见 wealthReview）。
 * 入口只看月支藏干十神；所有检查只报告显干组合是否出现，judgment 恒为 unresolved。
 */
export function patternReview(bazi: Bazi, options: { v3?: boolean } = {}) {
  const month = bazi.pillars.find((p) => p.position === "month")!;
  const visible = bazi.pillars.filter((p) => p.position !== "day");
  const exposure = (stem: string) => visible.filter((p) => p.stem === stem).map((p) => p.position);
  const hidden = month.hiddenStems.map((h, i) => ({
    stem: h.stem,
    tenGod: h.tenGod,
    role: ROLES[i] ?? "residual",
    exposedAt: exposure(h.stem),
  }));
  const at = (gods: string[]) =>
    visible.filter((p) => gods.includes(p.tenGod)).map((p) => ({ position: p.position, stem: p.stem, tenGod: p.tenGod }));
  // 某十神显干被另一显干五合（不计日干）。
  const combinedPairs = (gods: string[]) =>
    visible
      .filter((p) => gods.includes(p.tenGod))
      .flatMap((target) =>
        visible
          .filter((q) => q.position !== target.position && isCombine(target.stem, q.stem))
          .map((q) => ({ target: target.position, partner: q.position, stems: target.stem + q.stem })),
      );
  const runCheck = (check: Check) => {
    const groups = check.groups.map((gods) => ({ tenGods: gods, positions: at(gods) }));
    // presentAt 非空即表示“须不透”的十神实际透出，本项前提因此不成立。
    const absent = check.absent ? { tenGods: check.absent, presentAt: at(check.absent) } : null;
    const combined = check.combinedWith ? { tenGods: check.combinedWith, pairs: combinedPairs(check.combinedWith) } : null;
    const observed =
      groups.every((g) => g.positions.length) &&
      (!absent || !absent.presentAt.length) &&
      (!combined || combined.pairs.length > 0);
    return {
      id: check.id,
      category: check.category,
      label: check.label,
      prerequisite: observed ? ("observed" as const) : ("not-observed" as const),
      groups,
      ...(absent ? { mustBeAbsent: absent } : {}),
      ...(combined ? { combined } : {}),
      quote: check.quote,
      source: check.source,
      pending: check.pending,
    };
  };
  // 建禄月劫与阳刃：入口按月支禄位、刃位；月令其他透出藏干即可能的用神入口（《论用神》“別取財官煞食爲用”）。
  const dayStem = bazi.dayMaster;
  const yang = "甲丙戊庚壬".includes(dayStem);
  // 月劫与建禄、阳刃一样按位置：阴干月建为同五行阳干之禄（乙寅、丁巳、己巳、辛申、癸亥），不按月令本气十神。
  const yangPartner = STEMS[STEMS.indexOf(dayStem) - 1];
  const extendedEntry = (id: string) => {
    if (id === "blade")
      return yang && BLADE[dayStem] === month.branch
        ? [{ kind: "阳刃", branch: month.branch, rule: "禄前一位，惟五阳有之（《论阳刃》，“五”据中州本校改）" }]
        : [];
    if (LU[dayStem] === month.branch)
      return [{ kind: "建禄", branch: month.branch, rule: "月建逢禄堂（《论建禄月劫》）" }];
    return !yang && yangPartner && LU[yangPartner] === month.branch
      ? [{ kind: "月劫", branch: month.branch, rule: "阴干月建为同五行阳干之禄（阳干同位为阳刃）" }]
      : [];
  };
  const extendedPattern = (pattern: (typeof V3_PATTERNS)[number]) => {
    const entry = extendedEntry(pattern.id);
    const inScope = entry.length > 0;
    return {
      id: pattern.id,
      label: pattern.label,
      status: inScope ? ("candidate-only" as const) : ("outside-scope" as const),
      entry,
      useGodCandidates: inScope ? hidden.filter((h) => !["比肩", "劫财"].includes(h.tenGod) && h.exposedAt.length) : [],
      checks: inScope ? pattern.checks.map(runCheck) : [],
    };
  };
  return {
    scope: "月支藏干定正官/七杀/印/食神/伤官候选；仅核对年/月/时显干组合，不含日干",
    monthBranch: month.branch,
    dayMaster: bazi.dayMaster,
    dayMasterElement: element(bazi.dayMaster),
    patterns: PATTERNS.map((pattern) => {
      const entry = hidden.filter((h) => pattern.monthTenGods.includes(h.tenGod));
      const inScope = entry.length > 0;
      return {
        id: pattern.id,
        label: pattern.label,
        status: inScope ? ("candidate-only" as const) : ("outside-scope" as const),
        entry,
        // 月支多干并存时“透者作主”，其他透出的月令藏干是竞争入口，不能忽略。
        competingExposed: inScope
          ? hidden.filter((h) => !pattern.monthTenGods.includes(h.tenGod) && h.exposedAt.length)
          : [],
        checks: inScope ? pattern.checks.map(runCheck) : [],
      };
    }),
    ...(options.v3 ? { extendedPatterns: V3_PATTERNS.map((pattern) => extendedPattern(pattern)) } : {}),
    judgment: "unresolved" as const,
    sources: options.v3 ? { ...SRC, ...SRC_V3 } : { ...SRC },
    limits: [
      "候选只表示月支藏有该十神；本气、中气、余气与是否透出并列给出，透干优先与会支化格（《论用神变化》）须宿主另证。",
      "observed 只表示显干组合出现；支持、风险与救应可同时成立，不计分、不抵消、不多数表决。同一组合在不同强弱条件下方向相反时两行并列。",
      "not-observed 不表示藏干无作用或无救应；outside-scope 不表示无格。建禄、月刃、财格（见 wealthReview）及外格不在本模块内。",
      "引文取东篱书斋转录本原文，不含【校】与按语；中州本等异文、次序例外（財先食後等）与金水季节条件未自动处理。",
    ],
  };
}
