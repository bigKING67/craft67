# Design-craft critique: RevOps "next hour" dashboard

**Mode:** `critique`, read-only. **Surface mode:** `Operate`. **Treatment:** Enterprise dense, with Ops command center hierarchy.
**Sources read:** `SKILL.md`, `taste-score-calibration.md`, `design-move-library.md`, `surface-playbooks.md` (dashboard section). I ran no route planner and no helper scripts, and edited no files.

## 1. Evidence level and score band

- **Evidence level: L0 static.** All I have is a prose description. There is no screenshot, DOM, token dump or browser run. The product context is useful, but L1 needs a screenshot as well.
- **Provisional score: 72–78 / 100, between "Functional but ordinary" and "Clean but generic".**
- **Hard ceiling: 84.** Card soup and a flat hierarchy are the main problems, and the anti-inflation rule caps those at 84. The rule against scoring above 88 with unverified states also applies.
- **Why this score:**
  - `+` The parts are right for an Operate surface: KPIs, a trend view, a dense table, and a stated restrained enterprise style.
  - `−` 12 equal cards means nothing leads. It is the "Bad dashboard" pattern almost word for word.
  - `−` The chart and the right rail are decoration, not decision support.
  - `−` States, responsive behavior and focus are completely unknown.
- **Not scored:** rendered spacing, type, contrast, token use, and every interaction or data state.

## 2. Design read

> Reading this as: an internal RevOps console for ecommerce operators, with a restrained, dense-but-calm enterprise vibe, optimized for **triage: picking the one account or campaign that needs action in the next hour, and acting on it.**

So the page has one job: answer "what needs me now, why, and what do I do?" Overview metrics only support that answer. They should not be the first thing the operator reads.

## 3. Blocking findings (5)

| ID | Pri | Finding (from the prompt) | Runtime unknown |
|---|---|---|---|
| F1 | P0 | **Card soup with no lead object.** 12 KPI cards share the same size and weight, so the "next hour" risk looks the same as routine totals. The three-second rule (find the top risk or action within three seconds) almost certainly fails. | Which metrics actually change from hour to hour, and whether there are thresholds |
| F2 | P0 | **No exception queue.** The work object, "which account or campaign needs attention", doesn't exist as its own element. The operator has to work it out from the cards and the table. | Whether anomaly or threshold data is available to drive a queue |
| F3 | P1 | **The table is a data dump.** The prompt says "dense account table" but doesn't say it is ordered by task. Identity, status, risk, impact and next action are probably not the first columns, and row actions are unspecified. | Column order, sort and filter behavior, row actions, keyboard reach |
| F4 | P1 | **Decorative chart and generic tips rail.** The area chart answers no named question. The tips don't name an entity, a change, an impact or an action. Both take prime space from F2. | Whether the chart's metric matters for triage at all |
| F5 | P1 | **No owned states.** Nothing is defined for loading, empty, error, stale data, permissions or long labels. That is a trust risk for an hourly decision surface: stale numbers presented as current lead to wrong actions. | Everything; nothing was observed |

## 4. Concrete design moves (8, one per decision layer)

1. **M1 Command/context band (F1, F5).** Add a thin top band with the time scope ("Last 60 min vs. same hour last week"), a data-freshness timestamp with a stale warning, and a few global filters (channel, region). No hero treatment and no global CTA.
2. **M2 Lead + support hierarchy (F1).** Promote one **lead risk object**, for example "3 campaigns below ROAS floor · $X/hr at risk". Fold the other KPIs into a compact **supporting metric strip** of 4–6 values. Give each value a delta, a comparison period and a threshold, so every number answers "compared to what?" Move the rest to a secondary view. Use tabular numerals.
3. **M3 Exception queue near the top (F2).** Make the core of the page `lead + support + action queue`. The queue is a ranked list of accounts and campaigns that crossed a threshold. Each row shows the entity, what changed, impact in $/hr, how long since onset, and a verb-object action ("Pause campaign", "Open account").
4. **M4 Diagnostic chart, not decoration (F4).** Replace the area chart with one chart tied to the selected queue item, such as spend vs. revenue for that campaign with the anomaly onset marked. Put it below the decision area. Label axes and scale honestly, and show tooltips with exact values. If no named question justifies it, remove it.
5. **M5 Task-first table (F3).** Order columns as identity → status → risk/impact → next action, and group metadata after them. Right-align numbers, left-align text. Truncate identities with the full name available on hover or via a title. Put filters right next to the table and make row actions keyboard reachable.
6. **M6 Replace the right rail (F4).** Turn the rail into a contextual detail panel for the selected queue or table row: evidence, owner, recent actions. Delete the generic tips. Keep an insight only if it names an entity, a change, an impact and an action or owner.
7. **M7 Token-backed semantic color and surfaces (F1, F5).** Use status color only where a state carries meaning (critical, warning, healthy, stale), always paired with an icon or text so color is never the only signal. Use subtle dividers and minimal elevation. Use no raw hex outside tokens, and check theme parity if the project has dark mode.
8. **M8 States, responsive and accessibility (F5).** Give each module its own loading, empty ("No exceptions in the last hour" as a positive confirmation), error and retry, stale, and permission-denied states, placed next to the module. At narrow widths, stack the queue first. Keep focus order as band → lead → queue → table, with visible focus rings and no hover-only actions.

**Blocker → move coverage:** F1→M1, M2, M7 · F2→M3 · F3→M5 · F4→M4, M6 · F5→M1, M7, M8. Nothing is deferred.

## 5. Verified vs. unverified

**Verified, from the prompt text only:**
- The structure is described as 12 equal KPI cards, a decorative area chart, a dense account table and a generic tips rail.
- The stated user is an operator triaging for the next hour.
- The stated style is restrained enterprise, token-backed color, no hero treatment.

**Inferred, not verified:**
- That the three-second test fails (F1).
- The table column order (F3).
- That the chart has no diagnostic value (F4).
- That states are missing rather than just not mentioned (F5).

**Unverified, nothing observed:**
- Rendered spacing, type scale, contrast, actual token use, theme parity.
- Hover, focus, keyboard, loading, empty, error, stale, permission states.
- Responsive layout, long-label behavior, real data volume, table and chart performance.

I make no browser, screenshot or runtime claims.

## 6. Minimal validation plan before implementation

1. **Product inputs:** confirm with RevOps which signals define "needs attention" (thresholds, ranking for the queue) and whether the data is fresh enough for hourly use. Without this, M2 and M3 can't be built honestly.
2. **Authority:** read the project's `DESIGN.md` and tokens, and confirm status-color roles and the table and panel components already in use (`keep` by default).
3. **Baseline at L2:** take a browser screenshot of the current dashboard at desktop width, plus DOM and computed styles, to confirm F1, F3 and F4 and to give a before image.
4. **State matrix:** with fixtures, render empty, loading, error, stale, permission-denied, a 500-row table and 80-character entity names, and capture each state.
5. **Accessibility pass:** keyboard walk through band → queue → table row action, check visible focus and contrast on status tokens, and confirm status is readable without color.
6. **Responsive:** capture desktop, tablet (targets at least 44 CSS px) and a narrow layout with the queue first.
7. **Provisional performance gates, to be agreed, not measured:**
   - table filter input p95 ≤ 100 ms
   - no long task over 50 ms while scrolling
   - mounted rows ≤ 100 with virtualization
   - CLS ≤ 0.1 when modules load
   - Roll back if any of these regresses by more than 20% from the baseline.
8. **Acceptance test:** an operator names the top action within three seconds on the after screenshot, and every retained chart or insight maps to a named question and action.
