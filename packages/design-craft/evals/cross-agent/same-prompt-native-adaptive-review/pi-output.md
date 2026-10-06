## 1. Evidence level, resolved platform, design read

- **Evidence level:** static prompt-only critique. No source tree, build, screenshot, accessibility tree, simulator/emulator, or device evidence.
- **Resolved platform:** `adaptive` from supplied `PRODUCT.md` context: native iOS/iPadOS + Android phone/tablet shipping.
- **Style authority:** supplied `DESIGN.md` allows shared semantic color/content hierarchy while explicitly permitting platform-native navigation, controls, icons, materials, and motion.
- **Design read:** Reading this as a native field-operations task surface for one-handed operators and tablet-review managers, with a calm trustworthy operational tone, optimized for fast completion, review, interruption recovery, and platform confidence.

## 2. Platform-conformance verdict

- **iOS/iPadOS:** **Not conformant; release-blocking.** The fixed phone canvas, custom navigation/back model, disabled Dynamic Type, undersized targets, non-semantic colors, non-native parity choices, unchanged tablet tabs, and non-reduced spring motion conflict with iOS/iPadOS expectations.
- **Android:** **Not conformant; release-blocking.** The consumed Android Back/predictive Back path, Cupertino control styling, web icon set, fixed type, undersized targets, raw colors, unchanged tablet tab bar, and missing Remove animations alternative conflict with Android/Material expectations.

## 3. Prioritized findings

| ID | Priority | Finding | Static proof | Why it blocks |
|---|---:|---|---|---|
| F1 | P0 | Non-adaptive layout | Screen forced to `width: 390` and centered on tablets; bottom tabs unchanged on phone/iPad/Android tablet | Fails tablet split-screen/multi-window manager review; adaptive means restructuring, not centering a phone UI. |
| F2 | P0 | Platform navigation/back is replaced or trapped | Custom top bar + JS back replaces iOS stack and Android system/predictive Back; empty `BackHandler` consumes Android Back | Breaks native trust, interruption recovery, left-edge iOS back, Android predictive Back, keyboard/system traversal expectations. |
| F3 | P0 | Accessibility release requirements are violated | Primary actions are `40x40`; text is fixed `fontSize: 14` with scaling disabled | Below iOS 44pt and Android 48dp target floors; fails Dynamic Type/font scaling and likely external-keyboard usability. |
| F4 | P0 | Design-system/theming and native controls are accidental parity | Raw `#777777`/`#FFFFFF`; same Cupertino switch and one web icon set on both platforms | Ignores semantic roles, dark/high-contrast appearance, Material/SF idioms, and platform-native control affordances. |
| F5 | P1 | Motion conflicts with accessibility and operational calm | Task-complete transition is 500ms spring with overshoot and no Reduced Motion/Remove animations path | Overshoot is inappropriate for a calm verification moment unless justified; missing reduced/remove path is release-blocking for accessibility. |

## 4. Concrete design moves

1. **Replace the 390px/pt fixed canvas** with window-size-class layout: compact phone single-column; expanded tablet two-pane task/review; resilient to rotation, Split View, multi-window, and fold posture.
2. **Restore native navigation ownership:** iOS navigation stack with system back/edge gesture; Android system Back/predictive Back with explicit save/confirm behavior only when needed.
3. **Resize and label all primary actions:** minimum 44pt iOS, 48dp Android, with adequate spacing, hit slop where needed, accessible names, disabled/loading states, and visible keyboard focus.
4. **Enable scalable typography:** iOS Dynamic Type text styles; Android Material type roles/`sp`; layouts tested through large accessibility sizes without clipping or lost actions.
5. **Move colors to semantic roles:** use `DESIGN.md` roles plus iOS semantic colors/materials and Android Material color roles/Dynamic Color fallback; remove raw `#777777`/`#FFFFFF`.
6. **Use platform-native controls and symbols:** iOS switches, SF Symbols, sheets/context actions; Android Material switches, Material Symbols, snackbars/bottom sheets/dialogs where appropriate.
7. **Adapt navigation chrome by width:** compact phones may keep platform tabs/bottom navigation; iPad should consider sidebar/split view; Android medium/expanded should consider rail/drawer.
8. **Redesign task-complete motion:** short, interruptible, low-amplitude confirmation; no overshoot by default; Reduced Motion/Remove animations uses cross-fade or immediate state change while preserving feedback.

## 5. Intentional parity matrix

| Area | Shared across platforms | iOS/iPadOS adaptation | Android adaptation |
|---|---|---|---|
| Product flow | Same task states, completion semantics, save/resume contract | Native stack/sheets where hierarchical or modal | Predictive Back-aware navigation and Material destinations |
| Content hierarchy | Same priority: task status, required actions, verification evidence | Large/inline titles, grouped lists where fitting | Top app bars, Material list/card grammar where fitting |
| Accessibility outcome | VoiceOver/TalkBack parity, scalable text, reduced motion, keyboard traversal | Dynamic Type, VoiceOver traits/actions, 44pt targets | Font scaling, TalkBack roles/state descriptions, 48dp targets |
| Theming | Shared semantic color roles | iOS semantic colors/materials/SF Symbols | Material color roles, tonal elevation, Material Symbols |
| Controls | Same meaning and state model | Native iOS controls | Native Material controls |
| Tablet behavior | Same manager review capability | iPad split view/sidebar patterns | Tablet/foldable rail/drawer/two-pane patterns |
| Motion | Same causal feedback and calm tone | iOS-native, reduced-travel alternatives | Material motion, Remove animations alternative |

## 6. Verified vs. unverified claims

**Verified from supplied static evidence only**
- Platform context is stated as adaptive.
- The described implementation uses fixed width, custom back/top bar, consumed Android Back, 40x40 pressables, disabled font scaling, raw colors, shared Cupertino switch/web icons, unchanged bottom tabs, and non-reduced overshooting completion motion.
- Those facts are sufficient to mark conformance and accessibility risks as release-blocking at design-review level.

**Unverified**
- Actual rendered layout, safe-area handling, rotation, Split View, multi-window, foldable behavior.
- VoiceOver/TalkBack labels, traits, order, announcements, and external keyboard traversal.
- Real contrast ratios, dark/high-contrast appearance, clipping under large text.
- Gesture feel, animation smoothness, haptics, interruption behavior, or persistence after app/background interruption.
- Any source paths, package scripts, build status, screenshot fidelity, simulator/emulator behavior, or hardware behavior.

## 7. Minimal validation plan

1. **Source audit:** inspect `PRODUCT.md`, `DESIGN.md`, RN screen code, navigation setup, `BackHandler`, dimensions/window-size logic, tokens, typography, pressables, icons, switches, and animation settings.
2. **Build/static checks:** run project type-check/lint/tests; iOS compile via Xcode tooling; Android compile via Gradle. Commands must come from the actual repo scripts.
3. **iOS Simulator evidence — currently missing:** verify iPhone and iPad layouts, rotation, Dynamic Type, Reduce Motion, light/dark/high contrast, keyboard traversal, navigation stack/back gesture, interruption recovery.
4. **Android Emulator evidence — currently missing:** verify phone/tablet/foldable or resizable profiles, multi-window, font scaling, Remove animations, TalkBack, predictive Back, dark theme, keyboard/D-pad traversal.
5. **Real-device evidence — currently missing:** representative iPhone/iPad and Android phone/tablet/foldable checks for gesture feel, haptics, system Back, performance, and interruption recovery before release claims.
