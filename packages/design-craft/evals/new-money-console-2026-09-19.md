# New Money console: bounded real-project application

Date: 2026-09-19. Decision: **PASS for the observed product UI scope**.
This is a real-project application case, not a controlled estimate of Skill
improvement, independent implementation, release certification, or live-service
browser acceptance.

## Inputs and authority

- Skill source: `a06965e843ce8a2aca5cba59cf97fee24ea4be41`; interface-detail
  and mobile-Web guidance entered at `f1938fc`. Installed parity was verified.
- Target: sibling `new-money-server`, final commit
  `186e9636ae8f2cb3fb4c287e5269e0607682c06b`. Changes are confined to
  `apps/web/src/{App.tsx,TeamPages.tsx,KnowledgePage.tsx,styles.css,Presentation.test.tsx}`.
- `PRODUCT.md` SHA-256:
  `26980fe3f5bc36d53afcb63cdebf55a38b69c17bc23eb205f9dd2fe102611195`.
- `DESIGN.md` SHA-256:
  `20bde4363ee9e0d7234624d4f869d2b2c690dbd0b9774973db4dd22500ebe19a`.
- Authority: existing warm-gray/deep-green tokens, native controls, React/Lucide,
  240px desktop rail. No new dependency or API contract.
- Recorded routes: overview `dashboard / visual-refine / page / web`;
  knowledge `admin / visual-refine / page / web`; L2/high, main_serial.
  Actual skills: design-craft and browser67. Route selection is separate from
  browser evidence; these values summarize the retained task reports.

## Observations and decisions

| Surface | Evidence-backed change | Acceptance boundary |
| --- | --- | --- |
| Overview | Replace dominant status banner/static checklist with metrics, working destinations, role-aware Desktop guidance and compact entitlement detail. | Destination clicks and one Enter activation reached the expected page and main focus; no invented connection/review completion. |
| Navigation | Keep desktop rail; expose current team and five destinations on mobile; add skip link and 44px icon targets. | Retained captures cover desktop, tablet structure and 320/390px layouts; no physical-device claim. |
| Knowledge | Group content in one responsive table cell; clarify project scope, full body, dangerous confirmation and local errors. | Review/cancel focus checked; synthetic 409 used one exact-revision request without retry; synthetic 503 retained review and recovery controls. |
| Members | Group name/email in one value cell and allow long-email wrapping. | 320/390px evidence shows email no longer falls into the label column. |
| Projects | Bound the flexible grid column with minmax(0,1fr) and wrap unbroken names. | A 390px viewport previously produced a 531px document; final captures remain 390px and 320px wide. |
| Audit | Add explicit success/denied/failed text alongside color. | Supplied denied fixture visibly reads 已拒绝. Other outcome labels are source evidence. |

This case exercises existing authority, product-truthfulness, responsive,
focus/state and sibling-consistency guidance plus the updated canvas/mobile-Web
guidance. It does **not** independently validate every Gustavo Craft concept:
nested corners, image outlines and optical glyph correction remain bounded by
the [controlled fixture](craft-details-2026-09-19.md).

## Browser and artifacts

Real Chrome was operated through browser67 against local Vite plus a synthetic
API proxy. The actual production project rendered, but displayed accounts,
content and mutations were fixtures. Dark mode used the browser preference;
light mode disabled the page's dark CSS media rule and set color-scheme:light.
This proves light-style rendering, not an OS-theme transition.

Evidence root alias `PRODUCT_EVIDENCE` denotes the operator-held, repo-external
New Money evidence directory. Groups below resolve to
`PRODUCT_EVIDENCE/2026-09-19-<group>/`. Reports and screenshot manifests remain
there; all 21 PNG hashes (8 overview, 4 knowledge, 9 regression) were rechecked
when writing this case. No screenshot or synthetic preview server enters the
installable Skill package.

| Selected artifact | PNG dimensions | SHA-256 |
| --- | --- | --- |
| knowledge/before-mobile.png | 390 × 1427 | `54bd529789e340fdadde19f8d77b6a3a847bbf98d03f5985929215b32858a94e` |
| knowledge/after-mobile.png | 390 × 1365 | `476951e2dd03285619574e30525068df10d1b3a535c142a661dda604019d44ed` |
| regression/before-projects.png | 531 × 1166 | `dde5da601e710680d29062d247fb80529773dbe3993cc9a32b7906bc4fcc58d0` |
| regression/after-projects-dark.png | 390 × 1207 | `27365a4e745d10f4854e27813f4b71d2f7acf7a8ddc9e22bd0498a1710bd263d` |
| regression/after-projects-light-320.png | 320 × 1228 | `89be31de9c6398e03bbc3f85daa30bf0be1d0bf7383e991cc2c1238605823b1a` |

The overview tablet capture precedes final small token/label refinements and
supports structure only. Earlier reports describing uncommitted work are
historical checkpoints; the final five-file change is now bound to the target
commit above. The before/after cases are sequential work on one project, not
randomized or blind comparisons. No causal uplift score is assigned.

## Verification and exclusions

- Target `corepack pnpm check`: TypeScript, 20 tests and Vite build passed;
  final diff whitespace check passed. No measured performance uplift claim.
- Main-agent visual/system review accepted the bounded modified surfaces.
  Managed browser tabs were explicitly finalized and task preview servers stopped.
- Separate backend acceptance at the same target commit passed the guarded
  PostgreSQL flow (2 tests, 740.76 seconds); independent readback found all 22
  application tables empty, nine successful migrations and zero test connections.
  This is target engineering evidence, **not design-quality evidence**.
- Unverified: browser connected to real test API for successful persisted flows,
  real email delivery, screen reader, physical touch/keyboard/safe-area behavior,
  all-page/all-state coverage and independent Skill-effectiveness comparison.
- No new source-bound host/native certification is implied. The fixed-reference
  decision for Gustavo Craft and the original fixture verdict remain unchanged.

## Fresh-session read-only use check

A separate `codex exec --ephemeral --sandbox read-only` invocation started in
the target repository without a resume/fork and without naming the Skill in
the task prompt. It received the existing 320px project screenshot above and
this bounded task (translated): inspect project-list long-name wrapping and
visual consistency against current source/design authority; keep the existing
implementation unless a necessary repair has evidence; do not edit files,
start services, use the browser/database or delegate; distinguish source,
supplied image and unverified runtime within 600 Chinese characters.

Observed execution: exit 0, one completed turn, three completed shell calls,
all exit 0. The completed command records establish actual reads of installed
`design-craft/SKILL.md`, `references/system-review.md`, host `frontend.md`, target
`AGENTS.md`, `DESIGN.md`, `DESIGN.dark.md`, and scoped TeamPages/CSS sections.
No extra Skill reference, route planner, browser/database command, service
startup or mutation appeared in those records. The target worktree remained
clean. The L0 read-only task did not require an L1+ planner invocation.

The final answer recommended **keep**: it cited bounded flexible columns,
long-word wrapping and consistent project-row structure, described the supplied
image, and explicitly withheld claims about fresh runtime, other widths and
dark-mode rendering. It did not prescribe new tokens, a component library or
an unnecessary visual change. It did not claim to have captured the image.
The response measured 741 raw Markdown characters, or 550 after replacing link
targets with their labels. The prompt's 600-character budget did not define
link-target counting; no strict raw-output-budget pass is claimed.

Verdict: **PASS for one fresh CLI session's natural Skill selection, narrow
reference loading, project-authority reasoning and evidence boundaries**.
This is not a fresh browser run, full autonomous implementation, independent
replication of the earlier fixes, multi-host certification, or evidence that
every newly added reference activates correctly. Model/runtime identity was
not separately certified. Existing product browser evidence remains separate.
