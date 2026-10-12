## Design-craft critique: revenue ops dashboard (`critique` mode, read-only)

### 1. Evidence level and score band

- **Evidence level: L0 static.** All I have is a written description plus product context. With no screenshot this can't reach L1, and nothing was rendered or inspected.
- **Provisional score: about 70/100, range 65–76, low confidence.** That puts it between "Functional but ordinary" (60–74) and "Clean but generic" (75–84).
- **Hard ceiling: 84.** The calibration rule says flat hierarchy or card soup caps the score at 84. Spacing, type and token use can't be judged from prose, so the score can't go above the band.
- **Why:**
  - **+** The pieces you'd expect are there: KPIs, a trend chart and a dense account table.
  - **−** Twelve KPI cards of equal weight give no priority.
  - **−** Nothing on the page answers "what needs me in the next hour?"
  - **−** The chart is decorative and the right rail is generic.

### 2. Design read

Reading this as: a revenue operations console for internal ecommerce operators, restrained, dense and calm, built so the operator can **pick the one account or campaign to act on in the next hour and act on it.**

So the page should be ranked by exceptions, not laid out as an overview. Totals and trends are there to support a decision. They aren't the decision.

### 3. Blocking findings (5)

| ID | Pri | Finding | Basis (prompt only) |
|---|---|---|---|
| F1 | P0 | **Flat KPI grid.** Twelve equal cards at the top have no lead metric. Risk and routine totals look the same, so the operator has to compare all twelve before acting. | "12 equal KPI cards" |
| F2 | P0 | **No exception queue or next-action object.** Nothing ranks accounts or campaigns by urgency or impact. The main job only gets done by scanning the dense table by hand. | The described structure has no queue, alert or ranked list |
| F3 | P1 | **Decorative chart.** An area chart with no named question takes up prime space above the table. It has no threshold, anomaly marker or link to an entity. | "one decorative area chart" |
| F4 | P1 | **Table is probably a data dump.** "Dense" with no stated column priority suggests schema order. Identity, status, risk, impact and next action may not be scannable without decoding the whole row. | "dense account table". Column order is **unverified** |
| F5 | P1 | **Generic right rail.** The tips name no entity, threshold, impact or owner, so they are decoration posing as analysis. They also take width from the table. | "right rail with generic tips" |

Loading, empty, stale-data, error and permission states aren't described anywhere. That's an unknown, not a confirmed defect, so move M7 covers it as a risk.

### 4. Concrete design moves (8)

This applies the library's "dashboard card soup → decision surface" move with the enterprise-dense treatment. Target anatomy: command band, lead risk object, metric strip, exception queue, diagnostic chart, task-first table.

- **M1 Command/context band.** Add one compact header row with scope (team, region, channel), time window, data freshness ("updated 4 min ago") and filters that sit next to the data they affect. No hero treatment.
- **M2 Lead vs. supporting hierarchy (F1).** Promote one lead risk object, such as "Revenue at risk, next 60 min" with its delta and threshold. Turn 4–6 of the KPIs into a compact supporting metric strip with tabular numerals, and give each one a period and a comparison ("compared to what?"). Move the remaining KPIs to drill-down.
- **M3 Exception queue near the top (F2).** Rank accounts and campaigns by urgency × impact. Each row shows identity, what changed, the size of the impact, the owner and one action written as verb + object ("Pause campaign", "Assign to rep"). This becomes the primary work object.
- **M4 Chart in a diagnostic role (F3).** Tie the chart to a named question, e.g. "Is checkout conversion breaking threshold today?" Show threshold and anomaly markers and link it to the selected queue or table row. If no question survives review, delete it. Either way it goes below the decision surface.
- **M5 Task-first table (F4).** Order the leading columns as identity, status, risk, impact, next action, and group metadata after them. Right-align numbers in tabular figures. Show status as text or an icon plus color, never color alone. Truncate long names on purpose with the full value available. Row actions must be reachable by keyboard.
- **M6 Replace the rail (F5).** Turn the rail into a contextual detail and action panel for the selected row: recent changes, owner, history, actions. If it can't earn that role, remove it and give the width back to the table. Any insight that stays must name the entity, the observed change, the impact and the action or owner.
- **M7 States as contract.** Give each module its own loading, empty ("No accounts need attention, last checked 10:42"), stale-data, partial-error-with-retry and permission state, local to that module. Use tokens and existing component variants only.
- **M8 System and access.** Color is token-backed and used only for meaning (risk, warning, ok, neutral). Prefer dividers to card surfaces and keep elevation minimal. Visible focus order should follow the visual order: band, lead object, queue, table. Plan reflow at narrower widths with the queue first. Use touch targets of at least 44 CSS px if tablets are in scope.

Every blocker maps to a move: F1→M2, F2→M3, F3→M4, F4→M5, F5→M6. None are deferred.

### 5. Verified vs. unverified

- **Taken from the prompt:** the four-part structure, the 12 equal KPIs, the chart described as decorative, the generic tips, the style authority and the user's job.
- **Inferred, not verified:** the table's column order and status treatment, the visual weight of each module, whether the chart has thresholds.
- **Unverified (no evidence at all):** rendered spacing, type and color, token compliance, contrast, hover and focus, keyboard order, responsive behavior, loading/empty/error/stale states, long-label handling, table performance, and the real data semantics (what counts as "needs attention").
- **No browser, DOM or screenshot validation was done**, and no files were edited.

### 6. Minimal validation plan before implementation

1. **Data semantics (blocks M2 and M3):** agree with ops leads on the ranking formula, the thresholds and the field that defines the owner.
2. **Grayscale wireframe, 3-second test:** with 3–5 operators on realistic data, check whether they can name the top account or campaign to act on within three seconds.
3. **Token audit:** map every status and surface to existing tokens and flag any one-off colors.
4. **L2 browser capture** at 1440, 1280 and 1024 px with real long names, plus DOM and computed-style checks for spacing, type and contrast.
5. **State fixtures:** loading, empty queue, stale data, partial API failure and a permission-restricted user, each rendered and captured.
6. **Focus walk:** confirm keyboard order through band, lead object, queue, table and row actions, with focus visible in each theme in use.
7. **Table performance gates.** These are provisional, need sign-off, and haven't been measured: filter/sort p95 ≤ 100 ms, no long task > 50 ms during scroll, mounted rows bounded (virtualize above about 200), CLS ≤ 0.05. Roll back if the head build regresses on any gate compared with the base build.

Score claims above L0 need steps 4–6. A claimed improvement needs before/after evidence at L4.
