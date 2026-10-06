# Intent map

Use this when the user's request is phrased as a subjective frontend complaint
instead of a precise mode. It maps common wording to the smallest useful
design-craft pass.

Project evidence still wins: live runtime, scoped `AGENTS.md`, project
`DESIGN.md`, route output, and existing components outrank this map.

## Visual and taste complaints

- "给我几个真正不同的版本", "先做原型让我选", "prototype": use
  `prototype`; narrow to one UI piece, preserve project authority, diverge on
  named layout/density/interaction/disclosure/motion axes, keep exploration
  isolated from production code, and stop for explicit selection before
  promotion. Color, copy, icon, or decoration-only swaps are not separate
  directions; do not copy a fixed picker/runtime contract blindly.

- "太 AI", "模板味", "廉价", "不高级": start with `critique`; read
  `visual-judgment.md`; add `product-ui-taste-review.md` when the user wants a
  score, concrete top issues, or acceptance criteria; then use `polish` or
  `redesign` only if the user asks for changes.
- "打几分", "为什么没给满", "哪里扣分", "100 分": use `critique`; read
  `product-ui-taste-review.md` and `taste-score-calibration.md`; report the
  evidence level, UI score, maturity band, top deductions, and acceptance
  criteria.
- "颜色平", "灰", "没层次", "对比不够": use `critique` or `polish`; read
  `design-system-contract.md`; check token roles, surface/text contrast,
  accent intent, and light/dark parity.
- "排版不对", "不聚焦", "信息层级乱": use `critique`; read
  `visual-judgment.md`, `product-ui-taste-review.md`, and
  `surface-playbooks.md`; judge primary job, hierarchy, scan path, type roles,
  and spacing rhythm.
- "太挤", "太散", "卡片太多": use `critique` then `polish`; check density,
  grouping, section rhythm, and whether nested-card structure is hiding the
  actual task.
- "视觉不统一", "同一工具栏风格不一致", "交互语言不一致": read
  `system-review.md`; use its lightweight completion gate for one local
  component or section, and use full `system-review` when the mismatch is an
  observed regression or crosses component families or surfaces. Do not infer
  a Radix UI, Base UI, or other primitive-library migration from visual drift
  without a confirmed library-level blocker.
- "整体视觉语言 Review", "设计体系 Review", "全站统一一下", "多页面一致性":
  use full `system-review`; inventory surfaces, semantic component families,
  interaction patterns, applicable states, and themes before signing off.
- "动效怪", "花", "晕", "不顺": use `motion`; read
  `motion-quality.md`; add `interaction-physics.md` for gestures; check motion
  purpose, frequency, interruption, performance, and Reduced Motion.
- "把全站动效优化一下", "系统审计动画", "给我动效改进计划": use
  `motion-plan`; read `motion-audit-planning.md`; map the motion surface, vet
  prioritized findings, and create implementation-ready plans without editing
  product source unless implementation is explicitly requested.

## Product and content complaints

- "不知道点哪里", "主按钮不明显", "决策不清楚": use `critique`; identify the
  primary action, competing actions, and whether visual hierarchy supports the
  job.
- "文案弱", "空状态弱", "错误提示泛": use `polish` or `harden`; read
  `design-system-contract.md`; fix action/object labels, recovery copy, empty
  state first action, loading copy, and toast specificity.
- "看一下哪里有问题": use `critique` first when the request is subjective;
  add `product-ui-taste-review.md` for product UI/screenshots; use `audit` when
  the request asks for measurable release quality.
- "整体审一下": use `critique` for one bounded surface, but use
  `system-review` when "整体" means the product, multiple routes, or its visual
  and interaction systems.
- "上线前检查", "生产质量": use `audit` plus `harden`; include browser
  validation for visible UI and route-specific risk.

## Resilience, performance, and structure complaints

- "移动端差", "小屏溢出", "响应式不行": use `harden` or `adapt`; read
  `surface-playbooks.md`; test narrow viewport, overflow, wrapping, touch
  target size, and source-order stacking.
- "长文案会炸", "数据多会乱", "空数据不好看": use `harden`; test hostile
  content lengths, missing fields, empty/loading/error states, and large lists.
- "卡顿", "慢", "动画掉帧", "表格/图表撑不住": use `optimize`; read
  `performance-quality.md`; establish a baseline before changing code.
- "目录乱", "组件拆得怪", "复用混乱": use `structure` or `architecture`;
  read `project-structure.md` and `architecture-quality.md`.
- "Base UI 还是 Radix", "选哪个 headless UI", "要不要迁组件库": use
  `architecture`; read `component-primitive-selection.md`; resolve current
  project authority and record `keep | adopt | migrate | defer` before changing
  dependencies or wrappers.

## Design-system seed complaints

- "新项目没有设计规范", "先给个默认设计系统", "这个项目样式很弱": if no stronger
  style authority exists, use the bundled original developer-product seed via:

  ```bash
  scripts/design_craft_seed_design.sh --target <project-dir>
  ```

- If a project already has credible `DESIGN.md`, tokens, brand guide, or strong
  runtime style, compare against the developer-product seed instead of overwriting it.
