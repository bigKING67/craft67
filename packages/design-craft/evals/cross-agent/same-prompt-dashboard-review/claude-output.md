# Revenue ops dashboard critique (design-craft `critique` mode)

Reading this as: an internal revenue operations console for ecommerce operators. It should be dense but calm, and it should help them decide **which account or campaign needs action in the next hour**.

## 1. Evidence level and score band

- **Evidence level: L0 (static prose).** All I have is a written description and product context. There is no screenshot, DOM, token dump or runtime evidence.
- **Product UI taste score: about 72–80 out of 100 (provisional). Band: "Functional but ordinary" to the low end of "Clean but generic".**
- **Score ceiling: 84.** The calibration rules don't allow a score above 84 when the main problem is a flat hierarchy or card soup. This layout matches design-craft's "Bad dashboard" pattern exactly.
- **Why not lower:** the structure (KPIs, a table and a rail) is a recognisable console layout, and the style authority (restrained, token-only color) is sound.
- **Why not higher:** nothing in the layout gives priority to anything. The chart is decorative, and the rail is filler.
- The score can't move up or down until a screenshot and the states (loading, empty, error, focus) are seen. Treat it as a hypothesis, not a measurement.

## 2. Design read: the job to optimize for

**Primary job:** triage. That means: spot the top exception, understand why it matters (impact in revenue terms), and act or assign it within one hour.

- **Surface mode:** `Operate`, not `Persuade`. Information architecture matters more than visual drama.
- **Treatment variant:** *Enterprise dense*, borrowing from *Ops command center*. That means compact type, subtle dividers, a table-first rhythm and minimal elevation. Exceptions are the only high-contrast elements, and semantic status color appears only where it carries meaning.
- **Success test:** the operator can name the top account or campaign at risk, and what to do about it, **within 3 seconds** of the page loading.

## 3. Blocking findings (5)

| ID | Pri | Finding | Basis | Runtime unknown |
|---|---|---|---|---|
| F1 | P0 | **No lead object.** 12 equal KPI cards give routine totals the same visual weight as anomalies, so the eye has nowhere to land and the triage job fails. | The prompt says "12 equal KPI cards" | Real values; whether any card already carries a state |
| F2 | P0 | **Nothing above the fold answers "what needs attention".** There is no exception queue or ranked list of at-risk accounts and campaigns. The operator has to infer priority from the totals. | The listed structure has no queue | Whether the table is sorted by risk by default |
| F3 | P1 | **The decorative area chart takes prime space without answering an operational question.** An area chart with no threshold, comparison or marked onset is ornament. | The prompt says "decorative area chart" | Axes, scale, legend, tooltips |
| F4 | P1 | **The dense table is a data dump.** It is dense but not task-ordered: identity, status, risk, revenue impact and next action are probably not the first columns, and there are no row actions. | The prompt says "dense account table" | Column order, sort, filters, truncation |
| F5 | P1 | **The right rail of generic tips is decoration disguised as guidance.** It doesn't name an entity, a change, an impact or an owner, and it takes width from the table. | The prompt says "generic tips" | Whether the content is static or computed |

**Score impact:** F1 and F2 alone hold the score at 84 or below. F3–F5 are what push it toward the mid-70s.

## 4. Concrete design moves (8)

Each move covers one decision layer; the blockers each move resolves are in brackets.

1. **Command and context band** [F1]. Add a thin header strip with:
   - the time window (for example "Last 60 min vs same hour last week");
   - when the data was last refreshed, and how fresh it is;
   - a segment/channel filter.

   No hero, no global CTA. This answers "compared to what?" once for the whole page.
2. **Lead risk object plus a supporting metric strip** [F1]. *Dashboard card soup → decision surface* and *Flat KPI grid → priority hierarchy*.
   - Promote one lead state, for example "Revenue at risk now: $X across N accounts", with a delta and the threshold it crossed.
   - Collapse the other KPIs into a single compact strip with tabular numerals.
   - Cut that strip to about 5–6 metrics. Move the rest into a diagnostic tier further down, or into a drill-down.
3. **An exception queue at the top** [F2]. Add a ranked list of accounts and campaigns that crossed a threshold. Each row shows:
   - the entity name;
   - the signal (for example "conversion −38% vs baseline");
   - the impact, as revenue per hour;
   - the time since onset;
   - an owner, plus Assign and Open actions as verb-object buttons.

   This is the primary work object.
4. **Turn the chart into a diagnostic chart** [F3]. Either:
   - replace the area chart with a line showing the selected entity (or the lead metric) against its baseline, with the threshold band and the onset marked; or
   - delete the chart.

   Put it below the queue, and title it with the question it answers.
5. **Task-first table** [F4]. Column order: identity → status → risk → revenue impact → change → owner → next action. Then:
   - group other metadata after those columns, or behind column options;
   - right-align numbers and use tabular figures;
   - put filters directly next to the table;
   - make the default sort "risk, descending";
   - truncate identities with an accessible full name rather than clipping them silently.
6. **Remove or repurpose the rail** [F5]. Two options:
   - delete it and give the width back to the queue and table; or
   - turn it into a **selected-entity detail rail** with recent history, recent changes, owner and actions.

   Keep an "insight" only if it names an entity, a change, an impact and an action.
7. **Token-backed type, color and surface** [F1, F3]. Calm surfaces with dividers rather than card shadows.
   - Semantic status tokens (critical/warning/ok/neutral) appear only on the queue, table status cells and the lead object.
   - Status never relies on color alone: pair it with an icon or text label.
   - Use one type ramp, with no display sizes except the lead value.
8. **State and accessibility contract** [F2, F4]. Each module needs its own loading, empty, error and stale-data states. A good empty state for the queue is "No exceptions in the last 60 min", which is itself a valid answer.
   - Keyboard: a focus order of band → queue → table, with visible focus.
   - Row actions must be keyboard-reachable.
   - Targets must be at least 24×24 CSS px; use 44 px on any tablet or touch target.
   - At narrow widths: the queue comes first and the rail collapses.

All five blockers are covered: F1 → moves 1, 2, 7; F2 → moves 3, 8; F3 → moves 4, 7; F4 → moves 5, 8; F5 → move 6. None are deferred.

## 5. Verified versus unverified

**Verified (from the prompt text only):**
- The layout structure: 12 equal KPI cards, a decorative chart, a dense table and a generic tips rail.
- The product context, the primary user and the style authority.

**Inferred (reasonable, not observed):**
- The flat visual weight of the KPIs.
- The table's column order.
- The chart having no threshold or baseline.

**Unverified, so no claim is made:**
- Rendered spacing, type scale, contrast and whether tokens are actually used.
- Hover, focus, keyboard order and target sizes.
- Loading, empty, error, stale, permission and long-label states.
- Responsive and narrow-viewport behaviour.
- Chart scales, legends and tooltips.
- Table performance when there are many rows.
- Whether the data can support a "revenue at risk" or "exception" signal at all. **This is a product dependency for moves 2–3.**

I didn't open a browser, take screenshots or run any helper scripts. This is a static critique.

## 6. Minimal validation plan before implementation

1. **Confirm the data contract** with RevOps:
   - Do thresholds and baselines exist per account and per campaign?
   - Can revenue impact per hour be computed?
   - Is there an owner field?

   If not, moves 2–4 need to be redesigned before anyone builds them.
2. **Gather style authority:** read the project's `DESIGN.md` or token files and confirm that semantic status tokens and a tabular-numeral font exist.
3. **Capture an L2 baseline:** a desktop screenshot of the current dashboard plus the DOM and computed styles, so the score can be re-anchored on real evidence.
4. **Run a 3-second triage test:** show 3–5 operators a wireframe of moves 1–3 and ask them to name the top issue and its next action. The bar is that most of them get it right within about 3 seconds.
5. **Plan state coverage:** list loading, empty, error, stale and long-label fixtures for the queue, table and lead object before writing any code.
6. **Agree a provisional performance budget**, to be confirmed with the team (none of these were measured):
   - table filter/sort input p95 ≤ 100 ms;
   - no long task over 50 ms during a refresh;
   - mounted rows ≤ about 100 (virtualise above that);
   - CLS ≤ 0.1 when data refreshes.

   Roll back if the redesign regresses any of these against the current build.
7. **Gate the release on L3 evidence:** desktop and narrow-viewport screenshots, a recorded keyboard focus walk, and screenshots of each module's states. Only then can the score go above about 84.
