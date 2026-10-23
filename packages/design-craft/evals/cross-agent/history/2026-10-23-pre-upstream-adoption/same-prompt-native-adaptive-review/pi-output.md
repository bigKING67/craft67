## 1. Evidence, platform, and design read

- **Mode:** design-craft `critique`, read-only.
- **Evidence level: L0 static — prose only.** Product context informs the critique, but there is no screenshot, inspected application source, or runtime evidence.
- **Resolved platform: `adaptive`**, with high confidence from the supplied `PRODUCT.md` declaration and React Native iOS/Android shipping context. The actual file and native targets were not inspected.
- **Style authority:** the supplied `DESIGN.md` description requires shared semantic roles and hierarchy, not identical controls or layouts.
- **Reading this as:** a field-task workflow for one-handed operators and tablet-based reviewers, with a calm, trustworthy character, optimized for rapid completion and interruption-safe verification.

**Diagnosis:** the concept shares platform appearance where it should share product meaning. Fixed phone geometry and overridden OS behavior undermine operational trust more than visual polish could repair.

## 2. Separate platform verdicts

| Platform | Static conformance verdict |
|---|---|
| **iOS / iPadOS** | **Not conformant as described.** Targets and disabled scaling conflict with accessibility requirements; custom navigation does not establish native stack/edge-back behavior; fixed width does not support iPad window adaptation. A Cupertino-shaped switch alone proves neither native semantics nor behavior. |
| **Android** | **Not conformant as described.** Consumed system Back is a direct platform-contract conflict. Undersized targets, disabled scaling, Cupertino controls, and unchanged tablet navigation reinforce an iOS/web-port experience rather than Material-native operation. |

These are design/conformance judgments against the supplied facts, **not observed runtime failures or store-review predictions**.

## 3. Prioritized finding ledger

**P1 means a release blocker against the stated requirements; P2 means a conformance correction.** Five blockers follow. Repairs reference the eight moves below.

| ID / priority | Supplied evidence and consequence | Runtime unknown | Repair / acceptance evidence |
|---|---|---|---|
| **F1 · P1 — Touch accessibility** | All primary pressables are **40×40**, below iOS **44×44 pt** and Android **48×48 dp** minimum targets. This is particularly poorly matched to one-handed field use. | Effective hit regions, overlap, spacing, reachability, and assistive activation were not inspected. | **M1.** Measure effective targets and demonstrate distinct, reachable activation on both platforms. |
| **F2 · P1 — Text and accessible operation** | Fixed **fontSize: 14**, with scaling disabled, explicitly defeats Dynamic Type/font-scaling requirements. A base size of 14 alone is not the decisive defect. | Clipping, VoiceOver/TalkBack semantics, reading order, announcements, and external-keyboard traversal remain unknown—not proven absent. | **M2.** Complete the flow at accessibility text sizes, with screen readers and keyboard, without hidden actions or trapped focus. |
| **F3 · P1 — Navigation and continuity** | Custom top bar/JS Back replaces native navigation; an empty `BackHandler` reportedly consumes Android Back. This removes expected escape behavior and puts interruption-safe work at risk. | Exact handler return value and call path, iOS edge-back support, predictive-Back cancellation, and draft persistence are unknown. Data loss is **not** established. | **M3–M4.** Demonstrate push/pop, system Back, canceled gestures, and resume/recovery with the same task context intact. |
| **F4 · P1 — Window adaptation** | Screen is forced to **width: 390** and centered on tablets; bottom tabs remain unchanged across phone/iPad/Android tablet. This is phone presentation, not demonstrated adaptive review. | Actual overflow in narrow windows, pane behavior, focus retention, keyboard occlusion, and fold/hinge handling are untested. Tabs themselves are not automatically wrong. | **M5.** Show compact and expanded layouts plus live split-screen/multi-window resizing without losing selection, progress, or actions. |
| **F5 · P1 — Motion accessibility** | Completion uses a **500 ms spring with overshoot**, with no Reduce Motion/Remove animations alternative. The missing alternative violates an explicit requirement; bounce also conflicts with the calm positioning. | Perceived delay, frame rate, interruption behavior, and whether completion waits for animation are unknown. | **M6.** Show immediate or reduced-motion feedback under OS settings, with identical completion semantics and no animation-gated persistence. |
| **F6 · P2 — Controls and appearance** | Raw **`#777777` / `#FFFFFF`** in both appearances bypass semantic theme roles; one Cupertino-shaped switch and web icon set erase platform distinctions. | Actual color pairings, contrast, switch semantics, icon legibility, and dark-theme rendering are unverified. | **M7–M8.** Inspect native control states and semantic light/dark/high-contrast mappings. If these colors form normal text/background, their ≈**4.48:1** contrast misses 4.5:1; that pairing is conditional, not observed. |

## 4. Concrete moves — eight, intentionally bounded

1. **M1 — Enlarge effective action regions.** Use at least 44×44 pt on iOS and 48×48 dp on Android, normally with 8 dp Android separation. Prefer a clearly labeled, thumb-reachable completion button; respect bottom/IME insets and avoid overlapping hit slop.
2. **M2 — Restore scalable, semantic UI.** Map typography to platform text roles with scaling enabled and flexible wrapping/layout. Supply labels, roles, values, state announcements, and visible keyboard focus with logical traversal.
3. **M3 — Restore OS-owned navigation.** Use native-stack integration on iOS with edge-back; integrate Android system/predictive Back rather than swallowing it. Top-bar Up and system Back must retain their distinct responsibilities.
4. **M4 — Make interruption recovery explicit.** Persist task identity, draft fields, and completion/sync status independently of animation. Distinguish “Saved on device,” “Sync pending,” and “Verified”; support retry without duplicate completion and resume the prior task.
5. **M5 — Restructure by available window space.** Replace fixed 390 width with window-driven composition: compact task detail; expanded task list plus selected detail/review pane. Adapt navigation and collapse panes gracefully as split windows narrow, preserving selection and focus.
6. **M6 — Use restrained completion feedback.** Remove decorative overshoot; give immediate semantic status feedback. Use iOS Reduce Motion and Android Remove animations branches, including immediate change where appropriate; animation must not own business-state commitment.
7. **M7 — Map shared color roles to each platform.** Define surface, text, secondary text, action, error, and verified roles across light/dark/high contrast. Use iOS semantic colors/materials and Android Material roles/tonal elevation; Dynamic Color is optional, with a deliberate fallback.
8. **M8 — Adapt native controls and symbols.** Use native iOS switches and SF Symbols, Android Material switches and Material Symbols, with consistent domain meaning and accessible labels—not look-alike controls hiding incompatible behavior.

### Intentional parity matrix

| Area | Stays shared | iOS / iPadOS adaptation | Android adaptation |
|---|---|---|---|
| Content and task states | Task hierarchy, validation, completion/verification meaning | Native presentation | Native presentation |
| Navigation and gestures | Destinations and task identity | Stack, edge-back, appropriate tabs/sidebar | System/predictive Back; compact bar, rail/drawer where appropriate |
| Window structure | Selection and review context | Safe areas; iPad size/window-aware panes | Window classes; system/IME/hinge insets and fold posture |
| Controls and icons | Action meanings and state model | System controls, SF Symbols, native sheets | Material controls, symbols, dialogs/sheets |
| Accessibility | Equivalent task access and outcomes | VoiceOver, Dynamic Type, keyboard traversal | TalkBack, font scaling, keyboard/D-pad traversal |
| Appearance and motion | Semantic roles and causal feedback | System materials; Reduce Motion | Tonal elevation; Remove animations |
| Offline/error recovery | Durable drafts, retry rules, duplicate protection | Platform lifecycle integration | Platform lifecycle integration |
| Analytics | Same domain events and completion definitions | OS interaction metadata where useful | OS interaction metadata where useful |

**Parity means equivalent outcomes and preserved work—not pixel equality.**

## 5. Verified versus unverified

- **Established for this review:** the prompt’s stated constraints and implementation facts; design-craft guidance was read and applied. No application files were edited.
- **Not independently verified:** `PRODUCT.md`, `DESIGN.md`, source behavior, target configuration, accessibility trees, actual contrast pairings, rendered layout, state persistence, or performance.
- **No validation performed:** build, screenshot review, rotation, split-screen, multi-window, foldable, simulator/emulator, or hardware testing.
- Automated routing/source checks were not run: this benchmark supplies no application source or execution target. They cannot substitute for missing native evidence.
- **Overall status:** static release blockers identified; runtime and visual acceptance remain **unverified**, not passed.

## 6. Minimal validation plan — proposed, not executed

1. **Source:** inspect project instructions, `PRODUCT.md`, `DESIGN.md`, package/native targets, navigation ownership and `BackHandler` returns, effective hit regions, scaling props, tokens, accessibility properties, motion-setting subscriptions, layout branches, and persistence paths. Trace F1–F6 to actual file locations.
2. **Build/tests:** run established project type-check/lint/test scripts, then iOS `xcodebuild` compile/tests and Android Gradle compile/tests using repository-defined schemes/tasks. Add focused tests for Back handling, draft restoration, duplicate-safe completion, and motion-setting branches.
3. **iOS Simulator: unverified locally.** Obtain iPhone compact and iPad expanded/Split View evidence; exercise rotation, keyboard, light/dark appearance, accessibility text sizes, Reduce Motion, navigation, and interruption recovery. Record screenshots and interaction results.
4. **Android Emulator: unverified locally.** Obtain phone, tablet/multi-window, and foldable-posture evidence; exercise font scaling, TalkBack, keyboard, appearance, IME/hinge insets, Remove animations, and system/predictive Back on supported API levels.
5. **Real devices: no iOS or Android evidence.** Validate VoiceOver/TalkBack, one-handed reach and activation, gesture completion/cancellation, background/process-loss recovery, and relevant Android OEM behavior on representative hardware. Measure release-build responsiveness before claiming smoothness.
6. **Acceptance:** revisit F1–F6 with linked source/build/runtime artifacts, covering compact and expanded states on **both** platforms. Screenshots support appearance; interaction recordings and task results must establish behavior and recovery.
