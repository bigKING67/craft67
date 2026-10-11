## 1. Evidence, platform, and design read

- **Method:** design-craft, read-only critique.
- **Evidence level: L0 static**—prompt and implementation description only. Product context is supplied, but no screenshot or source inspection supports a higher evidence level.
- **Resolved platform: `adaptive`**, based on the supplied `PRODUCT.md` declaration and React Native iOS/Android shipping context. These project facts were not independently inspected.
- **Authority:** the supplied `DESIGN.md` shares semantic roles and hierarchy, not identical controls or navigation.
- **Reading this as:** a field-task workflow for one-handed operators and tablet-based managers, with a calm, trustworthy native character, optimized for fast completion, verification, and interruption recovery.

**Diagnosis:** this is described as a fixed phone UI replicated across platforms, not an adaptive native experience. Shared product semantics are appropriate; forced behavioral and pixel parity are not.

## 2. Separate platform verdicts

| Platform | Conformance verdict from supplied evidence |
|---|---|
| **iOS / iPadOS** | **Does not meet the stated release requirements.** Disabled scaling, undersized controls, missing Reduce Motion alternative, and fixed tablet geometry conflict with accessibility and adaptation goals. A custom back control does not establish native stack or edge-swipe behavior. A Cupertino-shaped switch alone does not prove native semantics. |
| **Android** | **Does not meet the stated release requirements.** Consuming system Back is a direct navigation defect; predictive Back is not preserved as described. Fixed scaling, small controls, missing Remove animations support, and Cupertino/web controls undermine Android accessibility and native operation. |
  
These are design/conformance judgments, **not observed runtime failures or store-rejection predictions**.

## 3. Prioritized finding ledger

Five release blockers are identified below; two additional findings require correction or verification. “Evidence” means the supplied description, not inspected code.

| ID / priority | Evidence and consequence | Runtime unknown | Repair / acceptance |
|---|---|---|---|
| **F1 — P1 blocker: navigation** | Custom top bar/JS Back replaces native navigation; Android Back is reportedly consumed. Operators lose predictable exit and return paths. | Actual handler return value, stack ownership, edge-swipe cancellation, predictive Back, and retained progress. | **M1**; Back must dismiss/pop/exit appropriately without trapping users or losing drafts. |
| **F2 — P1 blocker: text accessibility** | Fixed `fontSize: 14` with scaling disabled directly contradicts Dynamic Type/font-scaling requirements. Uniform sizing also weakens hierarchy. | Wrapping, truncation, reading order, and accessibility-size layout. | **M2**; core content and actions remain available at supported accessibility sizes, including at least 200% scaling. |
| **F3 — P1 blocker: action targets** | All primary pressables are `40×40`, below iOS `44×44pt` and Android `48×48dp` target baselines. | Whether effective hit regions are expanded, overlap, or are clipped by parents. | **M3**; measure effective targets, spacing, one-handed reach, and keyboard activation on each platform. |
| **F4 — P1 blocker: adaptivity** | `width: 390`, tablet centering, and an unchanged bottom tab bar provide no described structural adaptation. This underserves manager review and risks narrow-window overflow. | Actual clipping, inset handling, focus behavior, and task continuity while resizing. | **M4**; compact and expanded windows retain all actions and selected-task state without a fixed phone canvas. |
| **F5 — P1 blocker: motion accessibility** | Task completion uses a **500ms overshooting spring** without an accessibility alternative. The missing alternative violates release requirements; bounce also conflicts with the calm positioning. | Perceived duration, interruption behavior, and whether completion waits for animation. | **M5**; OS motion settings produce equivalent feedback without overshoot/travel and never gate saving. |
| **F6 — P1 verification gate: appearance/contrast** | Raw `#777777` and `#FFFFFF` appear in both themes, bypassing semantic appearance roles. If paired as normal text/background, contrast is approximately **4.48:1**, below 4.5:1. | Actual color pairings, compositing, state contrast, and dark-mode readability. | **M6**; measure rendered pairings in both appearances and relevant contrast settings. The conditional ratio is not a measured screen result. |
| **F7 — P2: native controls/icons** | One Cupertino-shaped switch and one web icon set ship everywhere. Android is explicitly styled as a port; neither platform’s behavior is established by shape. | Native roles, checked values, labels, focus, and interaction semantics. | **M7**; platform-correct controls and meaningful symbols preserve equivalent actions and accessible state. |

**Additional release gates, not proven defects:** VoiceOver/TalkBack semantics, external-keyboard traversal, and interruption persistence have no evidence. Resolve through **M3/M7/M8** and runtime tests; do not assume either success or failure.

## 4. Concrete design moves

1. **M1 — Restore platform-owned navigation.** Use native-backed stack navigation with iOS interactive back and Android system/predictive Back integration. Remove blanket Back consumption; distinguish dismissing a modal, leaving a detail, and leaving the app.
2. **M2 — Introduce scalable type roles.** Map shared title/body/metadata hierarchy to system text styles and platform scaling. Allow wrapping and vertical growth rather than shrinking or clipping text.
3. **M3 — Make completion reachable and operable.** Use a clearly labeled primary action near the phone’s reachable lower region, respecting safe areas and keyboard insets. Meet `44pt`/`48dp` effective target floors; normally allow Android `8dp` separation. Provide visible keyboard focus and logical traversal.
4. **M4 — Replace fixed geometry with window-driven structure.** Compact windows use a focused task flow; expanded windows use task-list/detail or detail/evidence panes. Collapse panes without losing selection. Adapt navigation to iPad sidebar/tab conventions and Android rail/drawer conventions where appropriate—not merely by device name.
5. **M5 — Make completion calm and independent of animation.** Remove decorative overshoot; use restrained platform transitions. iOS Reduce Motion gets reduced travel or a short fade; Android Remove animations gets an immediate state change. Preserve textual confirmation and accessible announcements.
6. **M6 — Implement semantic appearance mappings.** Share roles such as surface, primary text, secondary text, status, and focus; map them to appropriate iOS/Material palettes and materials. Validate light/dark/contrast variants, including disabled/error states; never rely on color alone.
7. **M7 — Adapt native primitives behind shared APIs.** Use platform-correct switches, dialogs, sheets, and icon families, with shared domain meaning. Expose names, roles, values, state changes, and accessible actions; ensure focus restores after dismissal.
8. **M8 — Design recovery as a visible workflow.** Persist drafts and define pending/saved/failed completion states, retries, and duplicate-submit protection. On resume, restore task context; distinguish “saved on device” from “synced” when applicable. Specify manager review of pending or conflicting changes.

### Intentional parity matrix

| Area | Stays shared | Intentionally adapts |
|---|---|---|
| Content and task flow | Task identity, hierarchy, completion/verification rules | Pane arrangement, title placement, action presentation |
| Navigation and gestures | Destinations, selected task, safe exit semantics | iOS stack/edge swipe and iPad navigation; Android system/predictive Back and adaptive navigation |
| Controls and icons | Action meaning, validation, switch state | iOS native controls/SF Symbols where suitable; Material controls/appropriate Android symbols |
| Accessibility | Equivalent names, states, outcomes, keyboard access | VoiceOver vs TalkBack semantics/focus; Dynamic Type vs Android font scaling |
| Appearance | Semantic roles, status meaning, brand intent | Platform palettes, materials/elevation, contrast adaptations |
| Motion and feedback | Causal feedback and truthful completion state | Native transitions, OS motion preferences, restrained platform haptics |
| States and recovery | Drafts, loading, empty, error, offline/conflict semantics | Native presentation and lifecycle integration |
| Analytics | Domain events, task IDs, success/failure definitions | Platform interaction metadata—not divergent definitions of completion |

## 5. Verified versus unverified

- **Established from the prompt:** the declared platform, product requirements, style authority, and listed implementation choices.
- **Independently verified:** only the design-craft guidance consulted for this review; no implementation behavior.
- **Unverified:** source details, effective hit targets, visual hierarchy, actual contrast, accessibility trees, gestures, persistence, performance, rotation, split-screen, multi-window, and foldable behavior.
- No files were edited; no source scan, build, screenshot, simulator, emulator, or hardware test was performed.
- Review limitation: the routed React Native motion reference was absent; platform and interaction guidance supported the critique. No framework-specific animation implementation was validated.

## 6. Minimal source → build → runtime validation plan

1. **Source:** inspect actual `PRODUCT.md`, `DESIGN.md`, native targets, navigation/Back handlers, hit regions, scaling flags, tokens, accessibility props, motion-setting subscriptions, window/inset logic, and persistence ownership. Confirm or revise F1–F7 with file/line evidence.
2. **Tests/builds:** run repository-defined type/lint/tests, then iOS `xcodebuild` and Android Gradle compile/test workflows. Add focused tests for draft restoration, completion retries/idempotency, navigation state, and motion-setting branches. Passing builds do not establish native usability.
3. **iOS Simulator: unverified locally.** Test iPhone compact and iPad expanded/Split View; rotation, keyboard, light/dark, accessibility text sizes, Reduce Motion, navigation, and interruption recovery. Capture layouts and accessibility evidence where supported.
4. **Android Emulator: unverified locally.** Test compact phone and tablet/multi-window, plus a foldable posture/inset case; font scaling, TalkBack, keyboard/D-pad, themes, Remove animations, gesture/button Back, and predictive Back on a supported API.
5. **Real-device evidence: missing on both platforms.** Verify one-handed reach, VoiceOver/TalkBack task completion, physical-keyboard traversal, back-gesture cancellation, background/termination recovery, and offline retry. Use representative iPhone/iPad and Android phone/tablet hardware; check OEM behavior and haptics if used.
6. **Acceptance record:** retain build logs, device/OS/window configurations, screenshots, interaction recordings, and accessibility results mapped to finding IDs. Release sign-off remains blocked by the described requirement conflicts and incomplete until both platforms’ runtime gates pass.
