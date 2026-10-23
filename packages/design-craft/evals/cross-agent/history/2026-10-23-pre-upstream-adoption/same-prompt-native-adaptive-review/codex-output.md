**Evidence: L0 static, prose only. Resolved platform: `adaptive`.** This follows the supplied `PRODUCT.md` declaration, React Native implementation description, and iOS/Android store targets; repository targets were not inspected.

Reading this as: a field-task app for one-handed operators and tablet reviewers, with a calm, trustworthy character, optimized for fast completion and interruption-safe verification.

The concept’s shared content hierarchy fits that purpose. Its forced geometry and identical platform treatments conflict with the native adaptation explicitly allowed by `DESIGN.md`.

**Platform verdicts**

- **iOS/iPadOS:** Does not meet the described release requirements. Disabled text scaling and missing Reduce Motion behavior are explicit conflicts; navigation replacement, undersized controls, and fixed tablet layout require correction.
- **Android:** Does not meet the described release requirements. Consuming system Back is a direct navigation conflict, alongside disabled scaling and missing Remove animations support. Cupertino controls further weaken platform familiarity.
- These are design-conformance judgments from supplied facts, **not observed runtime failures or store-review predictions**.

**Prioritized finding ledger**

Five blocking findings follow. “Blocking” means unresolved against this product’s release requirements.

| ID / priority | Supplied evidence and consequence | Runtime unknown | Concrete move and acceptance evidence |
|---|---|---|---|
| F1 / P1 — Accessibility and targets | All primary pressables are `40×40`; text is fixed at `14` with scaling disabled. This undermines one-handed acquisition and explicitly prevents required text adaptation. | Effective hit areas, clipping, screen-reader semantics, and keyboard order are unknown. | **M1:** Provide effective targets ≥`44×44pt` on iOS and ≥`48×48dp` on Android, with adequate separation; place the completion action within comfortable phone reach. **M2:** Restore system text scaling and platform type roles; specify labels, roles, values, announcements, and visible keyboard focus. Accept after largest supported accessibility text sizes, VoiceOver/TalkBack, and keyboard traversal retain every action without clipping or focus traps. |
| F2 / P1 — Navigation and continuity | A custom top bar/JavaScript back button replaces platform navigation; the described Android `BackHandler` consumes Back. Navigation cannot be trusted to preserve expected escape paths. | iOS edge-swipe behavior, predictive Back cancellation, and draft persistence have not been exercised. An actually empty handler’s return behavior requires source inspection. | **M3:** Restore a native-backed iOS stack and Android system/predictive Back integration. Persist drafts independently of navigation and animation; preserve task identity and review context. Accept when button/gesture Back, cancellation, backgrounding, and process restoration preserve intended history and progress. |
| F3 / P1 — Adaptivity | The screen is forced to `width: 390` and centered on tablets; the bottom tabs never change. This prevents meaningful use of expanded review space and risks overflow in narrower windows. | Actual clipping, tab suitability, keyboard occlusion, and fold/hinge handling are unknown. | **M4:** Use available window size and input mode to switch between compact task flow and expanded list/detail review. Adapt navigation when space warrants it; handle safe areas, IME, and hinges. Accept continuous resizing, rotation, split-screen, and multi-window without lost selection, progress, or unreachable actions. |
| F4 / P1 — Motion accessibility | Completion uses a `500ms` overshooting spring with no Reduced Motion/Remove animations alternative. The absent alternative directly conflicts with release requirements; bounce also works against the calm positioning. | Perceived delay, dropped frames, input blocking, and announcement timing are unmeasured. | **M5:** Remove decorative overshoot; use restrained platform motion and an immediate state change when animations are removed, or a minimal fade where appropriate. Keep completion persistence independent of animation callbacks. Accept equivalent status, focus, and recovery with either OS motion setting enabled, including interruption mid-transition. |
| F5 / P1 — Theme and contrast contract | Raw `#777777` and `#FFFFFF` ship in both appearances instead of semantic roles. If used as normal-size text/background, this pair is approximately `4.48:1`, below `4.5:1`. | Actual foreground/background pairings, opacity, state contrast, and dark appearance are unknown; a rendered contrast failure is not established. | **M6:** Map shared semantic roles to platform light/dark and increased-contrast values, including focus, disabled, error, and success states. Accept measured contrast for actual rendered pairs and readable state distinctions without relying on color alone. |

One additional, nonblocking finding:

| ID / priority | Supplied evidence and consequence | Runtime unknown | Concrete move and acceptance evidence |
|---|---|---|---|
| F6 / P2 — Control familiarity | Both platforms use a Cupertino-shaped switch and one web icon set. This is accidental visual parity, especially on Android. Shape alone does not establish native behavior on iOS either. | Switch semantics, state feedback, symbol legibility, and interaction behavior are unverified. | **M7:** Use native iOS and Material Android controls, with platform-appropriate symbols mapped to shared action meanings. Accept correct accessible role/value, familiar interaction, and consistent meaning across platforms. |

**Intentional parity matrix**

| Area | Shared contract | iOS/iPadOS adaptation | Android adaptation |
|---|---|---|---|
| Content and task flow | Task identity, hierarchy, rules, completion criteria, review evidence | Native presentation of the same flow | Native presentation of the same flow |
| Navigation and layout | Destinations, selected task, recoverable context | Stack and edge-back; tabs/sidebar and split panes as space permits | System/predictive Back; navigation bar/rail/drawer and panes by window size |
| Controls and icons | Action meaning and state | Native controls and appropriate SF Symbols | Material controls and appropriate Material Symbols |
| Accessibility | Equivalent operability, meaningful order, status feedback | Dynamic Type, VoiceOver, keyboard focus | Font scaling, TalkBack, keyboard/D-pad focus |
| Appearance | Semantic color roles and content emphasis | System colors/materials and accessible alternatives | Material color roles/tonal elevation; deliberate static palette |
| Motion and gestures | Causal feedback, interruption, accessible alternatives | Native transitions and Reduce Motion | Native transitions and Remove animations |
| States and recovery | Draft, saving, saved, offline, error, retry, conflict; retained input | Platform-appropriate presentation | Platform-appropriate presentation |
| Analytics | Same semantic task events and outcomes | Platform metadata; no duplicate completion event | Platform metadata; no duplicate completion event |

**Verified versus unverified**

- **Established from the prompt:** declared platform, product/style authority, and the eight supplied implementation characteristics. These were accepted as evidence, not independently source-verified.
- **Derived:** the requirement conflicts above and the conditional color-pair calculation.
- **Unverified:** visual hierarchy in a rendered screen, actual hit areas, assistive-technology behavior, persistence, gestures, performance, themes, resizing, and all runtime acceptance criteria.
- No files were edited. No source scan, build, screenshot, simulator, emulator, or hardware validation was performed. The loaded skill lacked its referenced React Native motion and taste-review files; available platform, adaptive, interaction, and validation references informed this critique.

**Minimal validation plan — proposed, not executed**

1. **Source:** Inspect actual project authority, native targets, navigation configuration and Back-handler return values, target expansion, scaling props, accessibility semantics, theme mapping, motion-setting subscriptions, window adaptation, and draft/state ownership. Add focused tests for restoration and duplicate completion prevention.
2. **Build:** Run established type/lint/test scripts, then the project’s iOS Xcode build/tests and Android Gradle build/tests. Build success does not establish native usability.
3. **iOS Simulator: unverified locally.** Exercise an iPhone and iPad, including compact Split View and expanded review, rotation, accessibility text sizes, appearances, Reduce Motion, keyboard focus, and interruption recovery.
4. **Android Emulator: unverified locally.** Exercise phone, tablet/multi-window, and a foldable profile; cover font scaling, TalkBack, Remove animations, system/predictive Back commit and cancellation, IME/insets, and restoration.
5. **Real devices: unverified on both platforms.** Validate one-handed reach, VoiceOver/TalkBack task completion, physical keyboard traversal, gesture behavior, and interruption recovery on representative phones and tablets. Capture runtime evidence tied to build and settings; only hardware measurements can support final claims about gesture feel or sustained performance.