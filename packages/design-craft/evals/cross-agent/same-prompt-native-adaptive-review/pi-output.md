## 1. Evidence, platform, and design read

- **Mode:** design-craft critique; read-only. No files edited.
- **Evidence level: L0 static, prose-only.** Product context is supplied, but there is no screenshot, inspected implementation, or runtime evidence.
- **Resolved platform: `adaptive`**, with high confidence from the supplied `PRODUCT.md` declaration, React Native description, and intended iOS/Android distribution. Neither project document was independently inspected.
- **Authority:** the supplied `DESIGN.md` shares semantic roles and hierarchy—not identical platform presentation.
- **Reading this as:** a field-task workspace for one-handed operators and tablet reviewers, with a calm, trustworthy character, optimized for fast completion, verification, and interruption-safe progress.

**Diagnosis:** this is described as a fixed phone interface with shared styling, not an adaptive native experience. Its largest problems concern task access and OS behavior, not visual polish.

Applied design-craft’s product, iOS, Android, adaptive, and validation references. The referenced React Native motion file was unavailable; motion recommendations below follow the available platform guidance.

## 2. Platform-conformance verdicts

| Platform | Verdict from supplied description |
|---|---|
| **iOS / iPadOS** | **Not conformant as described.** Navigation-stack replacement, undersized controls, disabled Dynamic Type, missing Reduce Motion behavior, and fixed tablet geometry contradict the platform and product requirements. A Cupertino-shaped switch alone does not establish native behavior. |
| **Android** | **Not conformant as described.** Consumed system Back is especially serious. Targets, font scaling, Cupertino controls, unadapted navigation, and missing Remove animations support further undermine native operation. |
| **Adaptive product** | **Release sign-off blocked on the described defects; runtime conformance unverified on both platforms.** Pixel equality is neither required nor desirable here. |

## 3. Prioritized finding ledger

“Evidence” below means **user-supplied implementation description**, not inspected source. Five blockers are prioritized; two additional findings remain important.

| ID / priority | Evidence and consequence | Runtime unknown | Repair and acceptance |
|---|---|---|---|
| **F1 — P1 blocker: navigation** | Custom top bar/JS Back replace native navigation; the described empty `BackHandler` consumes Android Back. This removes expected escape and hierarchy behavior. | Actual handler return value, iOS edge-swipe behavior, predictive Back commit/cancel, and progress retention. | **M1.** Pass native push/pop, modal dismissal, Back cancellation and completion, with task context retained. |
| **F2 — P1 blocker: text accessibility** | Fixed `fontSize: 14` with scaling disabled directly conflicts with Dynamic Type/font-scaling release requirements. | Screen-reader roles, labels, values, focus order, announcements, and keyboard access were not supplied—not proven absent. | **M2.** Pass supported accessibility text sizes without clipping or lost actions; complete the task with VoiceOver, TalkBack, and keyboard alone. |
| **F3 — P1 blocker: action access** | All primary pressables are `40×40`: below iOS’s `44×44pt` and Android’s `48×48dp` target guidance. This is particularly unsuitable for one-handed field work. | Effective hit regions, spacing, occlusion, and actual thumb reach. | **M3.** Measure effective targets and demonstrate reliable activation without overlapping adjacent targets. |
| **F4 — P1 blocker: adaptivity** | Forced `width: 390`, tablet centering, and unchanged bottom navigation impose a phone canvas on review workflows. Narrow windows may also overflow. | Actual clipping, window resizing, safe areas, IME obstruction, hinge handling, and pane state continuity. | **M4.** Keep the selected task and actions usable across compact/expanded windows, rotation, Split View, multi-window, and fold postures. |
| **F5 — P1 blocker: motion accessibility** | Completion uses a **500ms overshooting spring**, with no Reduced Motion/Remove animations alternative. The missing alternative violates an explicit release requirement. | Perceived delay, dropped frames, interruption handling, and whether completion waits for animation. | **M5.** Both OS settings remove spatial overshoot; completion and accessible feedback remain correct when animation is skipped or interrupted. |
| **F6 — P2: theme semantics** | Raw `#777777` and `#FFFFFF` in both appearances bypass the declared semantic theme system. If paired as normal text/background, contrast is about **4.48:1**, below 4.5:1. | Actual foreground/background pairings, opacity, rendered contrast, dark-mode appearance, and state differentiation. | **M6.** Audit actual pairs across appearances and states; meet applicable text/non-text contrast and avoid color-only status. |
| **F7 — P2: native controls and symbols** | One Cupertino-shaped switch and web icon family ship everywhere. This particularly conflicts with Android’s native-control expectations. | Whether the switch exposes native roles/state, keyboard behavior, and accessible labels; web icons are not inherently inaccessible. | **M7.** Verify platform-appropriate behavior and understandable symbols, including announced on/off state and nonvisual operation. |

**Additional release-critical evidence gap:** interruption-safe persistence is the product’s central promise, but no persistence or recovery behavior is described. Do not infer data loss—or claim safety. Address through **M8**.

## 4. Eight concrete design moves

1. **M1 — Restore platform-owned navigation.** Use a native-backed iOS stack with edge-swipe Back and appropriate sheets. On Android, integrate supported system/predictive Back; distinguish app-bar Up from system Back and remove blanket consumption.
2. **M2 — Make content scale and traverse.** Map shared text roles to platform typography, enable scaling, and allow wrapping/reflow. Define accessible names, roles, values, logical traversal, focus restoration, and completion announcements.
3. **M3 — Make primary actions comfortably reachable.** Provide at least `44×44pt` on iOS and `48×48dp` on Android, normally with `8dp` separation on Android. Prefer a clearly labeled, lower-screen “Complete task” action, inset above system UI/keyboard, over a small icon target.
4. **M4 — Adapt to the available window.** Use a compact task flow on phones/narrow windows; introduce task-list/detail or task/evidence panes when space supports them. Choose iPad tab/sidebar patterns and Android navigation bar/rail/drawer by available space, not device name.
5. **M5 — Make completion calm and independent of animation.** Replace celebratory overshoot with restrained platform-consistent feedback. Use reduced travel/cross-fade for iOS Reduce Motion and immediate state change for Android Remove animations; never gate saving on animation completion.
6. **M6 — Bind appearance to semantic roles.** Keep shared meanings such as surface, primary text, warning, and completed; resolve them through iOS semantic colors/materials and Android Material roles/elevation, with intentional light/dark and contrast variants.
7. **M7 — Share control intent, not skins.** Render native-backed iOS controls and Android/Material equivalents. Use SF Symbols and Material Symbols or deliberately platform-adapted equivalents while keeping labels and meaning consistent.
8. **M8 — Make progress durable and recovery explicit.** Persist drafts independently of screen lifetime, distinguish local save from server verification, make completion retry-safe, and expose pending sync, failure, retry, and conflict recovery without erasing task context.

### Intentional parity matrix

| Area | Stays shared | Must adapt |
|---|---|---|
| Task/content | Domain model, hierarchy, completion rules, task identity | Pane structure, density, action placement |
| Navigation/gestures | Destinations and task continuity | iOS stack/edge swipe/sheets; Android Up/system and predictive Back |
| Controls/icons | Action meaning, labels, state semantics | Native controls, symbol families, menus and pickers |
| Appearance | Semantic color roles and status meaning | Platform colors, materials/elevation, contrast/appearance resolution |
| Accessibility | Equivalent operability and information | VoiceOver/TalkBack semantics, text-scaling primitives, focus/input behavior |
| Motion/feedback | Completion meaning and causal timing | Native transitions, OS motion preferences, restrained platform feedback |
| Recovery/states | Draft, pending, verified, error/offline/conflict behavior | Native presentation and lifecycle integration |
| Analytics | Task/event definitions and outcomes | Platform/navigation context—not different success definitions |

## 5. Verified versus unverified

- **Established within this review:** the prompt describes the listed implementation choices; those choices conflict with the stated adaptive/accessibility contract. The color ratio is conditional arithmetic, not a rendered contrast measurement.
- **Not independently verified:** source details, actual hit areas, accessibility trees, screenshots, visual hierarchy, navigation behavior, responsiveness, recovery, animation smoothness, or performance.
- **No product source/build/runtime checks were run.** Route/static automation was skipped because this benchmark supplies no source tree and requires a prose-only, read-only review.
- **iOS Simulator: unverified locally.**
- **Android Emulator: unverified locally.**
- **Real-device evidence: absent for both iOS and Android.** Toolchain availability was not assessed.

## 6. Minimal source/build/runtime validation plan

1. **Source:** inspect actual `PRODUCT.md`, `DESIGN.md`, package scripts, native targets, navigator/Back handlers, pressable hit regions, typography/scaling, token mappings, motion-setting subscriptions, window logic, and draft persistence. Reconcile F1–F7 against code rather than treating this description as source proof.
2. **Build/tests:** run the repository’s established type-check/lint and targeted navigation, persistence/retry, theme, and reduced-motion tests. Compile/test iOS via the project’s `xcodebuild` workflow and Android via its Gradle workflow; exact commands require project configuration.
3. **iOS Simulator:** cover one iPhone and iPad, compact and expanded/Split View widths, rotation, keyboard, light/dark, accessibility text sizes, and Reduce Motion. Capture artifacts tied to build, OS, window size, and setting; screenshots alone do not verify interaction.
4. **Android Emulator:** cover phone/tablet and a foldable posture, resizing/multi-window, IME/insets, supported API Back modes including predictive Back, font scaling, themes, and Remove animations.
5. **Accessibility and recovery:** demonstrate task completion with VoiceOver, TalkBack, and external keyboard on supported test hosts. Background/terminate/relaunch, disconnect/reconnect, retry completion, and resize mid-task; record what survives and how recovery works.
6. **Real devices:** test representative iPhone/iPad and Android phone/tablet hardware for one-handed reach, native gestures, assistive technology, keyboard behavior, OEM differences, and perceived motion/performance. Include haptics/sensors if used.

**Exit criterion:** resolve F1–F5 with source plus observed native evidence, verify F6–F7 and M8, and retain separate platform sign-offs. No simulator, emulator, hardware, or release-readiness pass is claimed here.
