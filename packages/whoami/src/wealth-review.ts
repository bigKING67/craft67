import type { Chart } from "./chart.js";

type Bazi = Chart["candidates"][number]["bazi"];
const SOURCE = "https://donglishuzhai.net/chapter/3722.html";
const PLACEMENT_SOURCE = "https://donglishuzhai.net/chapter/3746.html";
const PILLAR_ORDER = ["year", "month", "day", "hour"];

// 柱位相邻是可复算的窄条件，不等于克制已经发生或整格成败。
function sealPlacement(bazi: Bazi, inScope: boolean) {
  const visible = bazi.pillars.filter(p => p.position !== "day");
  const wealth = visible.filter(p => p.tenGod === "正财" || p.tenGod === "偏财");
  const seals = visible.filter(p => p.tenGod === "正印" || p.tenGod === "偏印");
  const point = (p: Bazi["pillars"][number]) => ({ position: p.position, stem: p.stem, tenGod: p.tenGod });
  const pairs = inScope ? wealth.flatMap(w => seals.map(s => {
    const wi = PILLAR_ORDER.indexOf(w.position), si = PILLAR_ORDER.indexOf(s.position);
    return {
      wealth: point(w), seal: point(s),
      adjacent: Math.abs(wi - si) === 1,
      between: PILLAR_ORDER.slice(Math.min(wi, si) + 1, Math.max(wi, si)),
    };
  })) : [];
  const status = !pairs.length ? "not-applicable" as const
    : pairs.some(p => p.adjacent) ? "adjacent-risk" as const : "no-adjacent-pair" as const;
  return {
    status, pairs,
    conclusion: status === "adjacent-risk"
      ? "显干财印存在相邻对；不能仅凭同透认定位置妥贴，须先解释此相邻风险。"
      : status === "no-adjacent-pair"
        ? "所列显干财印均不相邻；仅通过不相邻这一窄条件，不证明两不相克或成格。"
        : "财格候选入口或显干财印配对未满足；本项不作位置判断。",
    pending: "相邻风险是否被合化、通关等改变，以及身强弱、印能否帮身与整格成败，仍需另证；不相邻不等于无相克。",
    source: PLACEMENT_SOURCE,
  };
}

// 只检查“显财显官直接援引原文分支”的反例，不裁定救应或全局成败。
function officerBranch(bazi: Bazi, inScope: boolean) {
  const visible = bazi.pillars.filter(p => p.position !== "day");
  const positions = (god: string) => visible.filter(p => p.tenGod === god)
    .map(p => ({ position: p.position, stem: p.stem, tenGod: p.tenGod }));
  const officers = positions("正官");
  const checks = [
    { id: "no-visible-hurting", condition: "不透伤官", positions: positions("伤官") },
    { id: "no-visible-killer", condition: "未见七杀同透（不混七杀的局部检查）", positions: positions("七杀") },
  ].map(c => ({ ...c, result: c.positions.length ? "counterexample" as const : "not-observed" as const }));
  const applicable = inScope && officers.length > 0;
  const blockers = applicable ? checks.filter(c => c.result === "counterexample").map(c => c.id) : [];
  const status = !applicable ? "not-applicable" as const
    : blockers.length ? "blocked" as const : "pending" as const;
  return {
    status, officers, checks, blockers,
    scope: "既有月令透财入口且正官显透；仅检查直接采用财旺生官原文分支的显干反例，不覆盖暗官或救应后另论。",
    conclusion: status === "blocked"
      ? "存在伤官或七杀同透的反例，不能直接援引不透伤官、不混七杀的分支；若主张有救应，必须另行论证。"
      : status === "pending"
        ? "本轮显干反例未见；财旺、身强、官的作用及藏干和合化影响未核验，不能据此确认财旺生官成立。"
        : "月令透财入口或显官入口未满足，本项不作财旺生官分支判断；不否定暗官及其他取法。",
    source: PLACEMENT_SOURCE,
  };
}

// These are observable prerequisites, not completed traditional judgments.
const CHECKS = [
  { id: "food", label: "财与食神同透", groups: [["食神"]], pending: "身强、带比及食神生财的作用关系尚未裁定" },
  { id: "officer", label: "财与正官同透", groups: [["正官"]], pending: "官是否旺、财官作用及有无伤合尚未裁定" },
  { id: "seal", label: "财与印同透", groups: [["正印", "偏印"]], pending: "财印位置是否相宜、是否相克及印类差异尚未裁定" },
  { id: "peer", label: "财与比劫同透", groups: [["比肩", "劫财"]], pending: "财轻比重尚未裁定；比劫同透不自动破格" },
  { id: "killer", label: "财与七杀同透", groups: [["七杀"]], pending: "七杀作用及有无制化救应尚未裁定" },
  { id: "robber-food", label: "劫财与食神并见的救应候选", groups: [["劫财"], ["食神"]], pending: "食神能否化劫生财尚未裁定，出现不等于救应完成" },
  { id: "robber-officer", label: "劫财与正官并见的救应候选", groups: [["劫财"], ["正官"]], pending: "正官能否制劫护财尚未裁定，出现不等于救应完成" },
  { id: "killer-food", label: "七杀与食神并见的救应候选", groups: [["七杀"], ["食神"]], pending: "食神能否制杀生财尚未裁定，出现不等于救应完成" },
];

export function wealthReview(bazi: Bazi) {
  const month = bazi.pillars.find(p => p.position === "month")!;
  const visible = bazi.pillars.filter(p => p.position !== "day");
  const candidates = month.hiddenStems
    .filter(h => h.tenGod === "正财" || h.tenGod === "偏财")
    .map(h => ({ stem: h.stem, tenGod: h.tenGod,
      exposedAt: visible.filter(p => p.stem === h.stem).map(p => p.position) }))
    .filter(h => h.exposedAt.length > 0);
  return {
    scope: "月支财星同干透于年/月/时；仅核对显干前提",
    status: candidates.length ? "candidate-only" as const : "outside-scope" as const,
    monthBranch: month.branch,
    candidates,
    sealPlacement: sealPlacement(bazi, candidates.length > 0),
    officerBranch: officerBranch(bazi, candidates.length > 0),
    checks: candidates.length ? CHECKS.map(check => {
      const groups = check.groups.map(gods => ({
        tenGods: gods,
        positions: visible.filter(p => gods.includes(p.tenGod)).map(p => ({
          position: p.position, stem: p.stem, tenGod: p.tenGod,
        })),
      }));
      return {
        id: check.id, label: check.label,
        prerequisite: groups.every(g => g.positions.length > 0) ? "observed" as const : "not-observed" as const,
        groups,
        pending: check.pending,
      };
    }) : [],
    judgment: "unresolved" as const,
    source: SOURCE,
    limits: [
      "not-observed 仅指本轮显干条件未见，不表示藏干无作用、没有救应或现实无该事件。",
      "outside-scope 仅表示不满足本模块入口，不表示无财格；未覆盖未透取用、会支变化及其他格局。",
      "所有线索并列保留，不相互抵消、计分或多数表决；旺衰、位置、合化、制化有效性仍需单独论证。",
    ],
  };
}
