# Jakub component-scenario guidance: bounded Shadow Lab observation

Date: 2026-09-05. Outcome: **PARTIAL — real component observations obtained**.
This is a main-agent application of current source instructions, not an
independent Host trial, before/after quality comparison or certification.

## Bound inputs

- Target: myblog, fixed commit `5b34f70f4befa70f7694cf6eac73c587ee537581`.
- Component: `src/components/pages/anime/AnimeCard.svelte`, unchanged.
- Lab ID: `myblog-5b34f70f4bef-20260905T053244Z-00fe85b2`.
- Snapshot: 446 files, 35,763,391 source bytes; archive SHA-256
  `0c0422a1d9812517afb01ac53474b5d8869871bce2fbd5b93f6941c951e499dc`.
- Skill: current working source, with exact input hashes in the lab's
  `skill-inputs.json` and the table below; includes the entrypoint, writing,
  hardening and validation references. Installed global Skill was not the test
  input.
- Route: L1-F / web / main_serial; final preflight allowed browser67.
- Authority: isolated Markdown record of the existing component, system body
  font, original main CSS/Stylus tokens, configured hue and `.dark` theme.
  The original project has no DESIGN.md; none was added there.

Test input paths are relative to `skills/design-craft/`:

| Input | SHA-256 |
| --- | --- |
| `SKILL.md` | `a5fed0e30f6ab012c8ee405c9be7d225f64126ac973eb06a12d7f663d78e540a` |
| `references/design-system-contract.md` | `85060067866d2c303d1b7a917038904aa5c0cb984b9339301c898aa80295e524` |
| `references/impeccable-workflow.md` | `c6dc4fe2c9701afcfe29ac61a0b15cd7352c3637cb71b51a5bbd5d9ccc44b48d` |
| `references/validation-contract.md` | `3d765cb612f88a975401fd11a7653e8b522a819284f45a7d1bdebbb471544cca` |

The lab imports the real component, original i18n/type dependencies and shared
styles. A separate Astro config limits compilation to the preview; the full
site layout, remote data, analytics and production navigation are excluded.
Poster fixtures are null and activation callbacks increment a local counter.
This validates component behavior, not full-page visual integration.

## Cases and observed results

| Case | Evidence | Result |
| --- | --- | --- |
| Typical title/status and missing poster | Real rendered card with placeholder and 20px title line. | Observed data rendering pass. |
| Long title and unbreakable status | Card client width 318px; status width 1626px; internal scroll width 1638px. Screenshot shows clipped status while document overflow is false. | Observed clipping failure for the fixture. Production frequency and upstream data length limits unverified. |
| Missing overview, date, episode status and zero rating | Card renders without optional rating/status; overview fallback exists in real component. | Observed rendering pass; no invented loading/error state. |
| Mixed-direction title and emoji | Supplied title renders within the card. | Observed rendering pass for this string, not full RTL/accessibility certification. |
| Keyboard activation | Focus real outer card, dispatch browser CDP Enter keyDown/keyUp: counter 0 -> 1. Space keyDown/keyUp: remains 1. | Observed Space activation failure; source handler only checks Enter. |
| Focus disclosure | Focused card's detail overlay computed opacity remains 0. | Disclosure issue observed in this focused state; full keyboard traversal and screen-reader behavior not claimed. |

Long titles are intentionally truncated with an existing title attribute; this
test does not label the mere presence of truncation a defect. The status row
has no equivalent visible recovery in the tested card. No product fixes were
made; the task evaluates the Skill, not authorization to repair myblog.

The scenario report annotates the real instances. Its initial dark-mode
explanatory text lacked a readable foreground; this was a harness defect,
corrected with existing neutral light/dark classes. Original component code
and shared style files remained unchanged.

## Browser evidence

Runtime: browser67, one agent-created managed tab in a dedicated background
Agent window. No user tab was adopted. Static captures were visually inspected
by the main agent; page visibility was hidden, so no animation smoothness or
foreground/device-feel claim is made.

| Artifact | Actual viewport | PNG | SHA-256 |
| --- | --- | --- | --- |
| Desktop light baseline | 1100 x 850 | 1100 x 2508 | `e304c088feaa5aeeffb641ae444d08061f2dbfc29c465e45b2f6981896e65d3d` |
| Mobile dark baseline | 390 x 844 | 390 x 2508 | `287a2255f13b47500c373e2a32b6a74c360f16aa1ed6efae75847e2ed9aa87fe` |
| Mobile dark annotated report | 390 x 844 | 390 x 2700 | `b3f3585a1db3c4c356ad1868ec52865c8b3c8053c4c5f5186aea456396f3265c` |

Each screenshot's atomic viewport transaction verified page dimensions and PNG
dimensions and cleared the override. These are full-page screenshots, so PNG
height differs from viewport height. Evidence lives in repo-external lab and
browser runtime artifacts; source-controlled prose contains no profile data.

## Execution and limitations

- Frozen offline install failed with `ERR_PNPM_NO_OFFLINE_META`. Frozen normal
  install subsequently passed, without changing the lock or supply-chain policy.
- `pnpm exec astro build` stalled before Astro started under denied egress and
  was terminated. Its failure receipt is retained; cause is not established.
- Direct invocation of the installed Astro CLI passed for both baseline and
  annotated preview under enforced macOS outbound-network denial.
- HTTP preview responded 200 on loopback. Browser observations are separate
  from build receipts; no browser-wide network-denial claim is made.
- Source audit after execution reports `source_unchanged=true` with no
  difference fields, including Git index metadata.
- Shadow Lab aggregate verification remains **failed** because it retains both
  failed attempts. Later successful phases do not rewrite that history.
- Toggle wording, plural templates, full translation flows, reduced motion,
  zoom, touch and screen readers remain untested by this component case.
- This confirms the new instructions can be applied to select relevant cases
  and report real observations. It does not establish that an independent Agent
  will discover the same issues or that they were caused by the new guidance.

No additional universal Skill rule was justified by this sample. The existing
new contract already distinguishes inner clipping, actual input behavior,
unsupported states, harness defects and unverified conditions.

## Cleanup

The task-created managed tab was closed and closure verified; remaining
unkept task tabs: zero. The loopback server exited with code 0 after interrupt.
Agent-window cleanup initially failed because its tab context had already
closed. A same-scope retry found no task-owned window identity. Therefore the
tab/server cleanup is verified, but empty Agent-window closure is unverified;
no broader window cleanup was attempted. The disposable lab and evidence are
retained for inspection and owned cleanup, not left as a running service.

Repository-only checks after this report: public-repository validation and
`git diff --check` passed. The previously successful 25-gate portable run covers
the unchanged Skill instruction content; this turn added evaluation evidence
and updated the candidate record only.
