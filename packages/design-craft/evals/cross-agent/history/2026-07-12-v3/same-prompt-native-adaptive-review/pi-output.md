## 1. Evidence level, platform, design read

- **Evidence level:** **L0 static/prose only** — based on the prompt and static implementation description. No source tree, build, screenshot, accessibility tree, rotation, split-screen, foldable, simulator/emulator, or hardware evidence was provided.
- **Resolved platform:** **adaptive** from supplied `PRODUCT.md` context: one product shipping through iOS and Android stores. Confidence: high for review purposes, but not source-verified.
- **Design read:** Reading this as a native adaptive field-operations task flow for one-handed phone completion and tablet manager review, with a calm trustworthy operational tone, optimized for fast completion, verification, and interruption resilience.

## 2. Platform-conformance verdict

- **iOS verdict:** **Not conformant; release-blocking.** The concept violates core iOS expectations around native navigation stack behavior, iPad adaptation, Dynamic Type, 44pt targets, native controls/icons, semantic color behavior, and Reduce Motion support.
- **Android verdict:** **Not conformant; release-blocking.** The concept violates Android system/predictive Back, Material/adaptive navigation, 48dp touch targets, font scaling, Material controls/icons, semantic theming, tablet/foldable adaptation, and Remove animations support.

## 3. Prioritized findings — blocking only

1. **Accessibility gate failure — blocking**
   - Evidence: `40x40` pressables, fixed `fontSize: 14`, font scaling disabled, no Reduced Motion/Remove animations alternative.
   - Impact: fails stated release requirements for Dynamic Type/font scaling, touch accessibility, motion sensitivity, and likely external keyboard/AT traversal.
   - iOS risk: below 44pt target; no Dynamic Type.
   - Android risk: below 48dp target; ignores system font scale and Remove animations.

2. **Navigation contract broken — blocking**
   - Evidence: custom top bar and JavaScript back button replace platform navigation; empty `BackHandler` consumes Android Back.
   - Impact: undermines platform trust and increases risk of lost progress or trapped users during interruptions.
   - iOS: likely breaks native stack affordances and left-edge back expectation.
   - Android: directly breaks system Back and predictive Back.

3. **Adaptive layout is not adaptive — blocking**
   - Evidence: screen forced to `width: 390` and centered on tablets; same bottom tab bar on phone, iPad, and Android tablet.
   - Impact: manager tablet split-screen/multi-window review is reduced to a phone canvas, wasting space and likely harming scan/review speed.
   - Missing: size classes, panes, rails/sidebars, split view, fold/multi-window behavior.

4. **Controls, icons, and theming are platform-incorrect — blocking**
   - Evidence: same Cupertino-shaped switch and one web icon set on both platforms; raw `#777777` and `#FFFFFF` in both appearances.
   - Impact: looks like a port rather than native software; risks dark-mode, high-contrast, contrast, and state inconsistency.
   - DESIGN allows shared semantic roles, not forced identical controls/materials.

5. **Motion violates accessibility and product tone — blocking**
   - Evidence: task-complete transition is a 500ms overshooting spring with no Reduced Motion/Remove animations alternative.
   - Impact: too expressive for “calm operational” completion, can be vestibular-hostile, and may delay or obscure task state feedback.

## 4. Concrete design moves

1. Replace custom navigation with platform-native navigation:
   - iOS: native stack/tab/sidebar patterns with preserved back gesture.
   - Android: top app bar/navigation components with system and predictive Back preserved; remove empty `BackHandler`.

2. Make the screen responsive to window/size class, not fixed width:
   - Compact phone: focused one-handed task flow.
   - Tablet/split-screen: task detail + verification/review pane, sidebar/rail where appropriate.

3. Raise interactive target sizes:
   - iOS minimum **44x44pt**.
   - Android minimum **48x48dp** with adequate spacing.
   - Use full-width or bottom-reachable primary actions for one-handed operation.

4. Restore text scaling:
   - Use semantic text roles and allow Dynamic Type / Android font scaling.
   - Reflow content instead of clipping or hiding actions at larger sizes.

5. Replace raw colors with semantic roles from `DESIGN.md`:
   - Validate light, dark, high-contrast, disabled, pressed, error, success, and focus states.
   - Avoid raw `#777777` / `#FFFFFF` except as token definitions.

6. Use platform controls and iconography:
   - iOS: native switch behavior, SF Symbols, iOS materials where appropriate.
   - Android: Material switch, Material Symbols, tonal elevation/Dynamic Color where appropriate.

7. Define a platform-aware motion policy:
   - Default completion feedback should be quick, restrained, interruptible, and state-first.
   - Reduced Motion / Remove animations path should use cross-fade, opacity change, or immediate state update with no overshoot.

8. Design interruption resilience explicitly:
   - Preserve draft/progress across app switch, Back, rotation, split-screen changes, offline/slow states.
   - Announce completion/errors to VoiceOver/TalkBack and keep keyboard focus predictable.

## 5. Intentional parity matrix

| Area | Shared across platforms | iOS adaptation | Android adaptation |
|---|---|---|---|
| Product flow | Same task states, verification model, save/progress semantics | iOS-native hierarchy and gestures | Android-native hierarchy and Back model |
| Navigation | Same destinations and information architecture | Navigation stack, tab/sidebar as size class fits | Top app bar, nav bar/rail/drawer, predictive Back |
| Layout | Same content priority and review hierarchy | iPhone compact; iPad Split View/sidebars | Phone compact; tablet/foldable/multi-window panes/rails |
| Controls | Same semantic actions and labels | Native iOS controls, sheets, context menus, SF Symbols | Material controls, dialogs/sheets/snackbars, Material Symbols |
| Type | Same content hierarchy | Dynamic Type text styles | Material type roles with `sp` and font scale |
| Color | Same semantic token roles | iOS system colors/materials where suitable | Material color roles, tonal elevation, Dynamic Color if adopted |
| Motion | Same state meaning: start, save, complete, error | iOS-consistent push/sheet/fade; Reduce Motion | Material transitions/fade-through; Remove animations |
| Accessibility | Same release outcomes | VoiceOver, Switch/keyboard, iPad keyboard traversal | TalkBack, keyboard/D-pad, predictive Back accessibility |

## 6. Verified vs unverified claims

**Verified only from supplied static description:**
- Forced `width: 390` and centered tablet layout.
- Custom top bar / JavaScript back button.
- Empty Android `BackHandler` consuming Back.
- `40x40` pressables.
- Fixed `fontSize: 14` with font scaling disabled.
- Raw `#777777` and `#FFFFFF`.
- Same Cupertino-shaped switch and web icon set on both platforms.
- Bottom tab bar unchanged across phone/tablet.
- 500ms overshooting completion spring without reduced/remove alternative.
- Product and design constraints as stated in the prompt.

**Unverified:**
- Actual source paths, component ownership, and code branches.
- Visual hierarchy, density, contrast ratios, screenshots, and dark-mode output.
- VoiceOver/TalkBack labels, traits, traversal, announcements, and custom actions.
- Dynamic Type/font-scale clipping behavior.
- External keyboard traversal.
- Safe-area, IME, hinge, orientation, split-screen, and foldable behavior.
- Whether progress is actually lost on interruption.
- Native builds, runtime behavior, haptics, perceived smoothness, or performance.
- iOS Simulator, Android Emulator, and real-device behavior.

## 7. Minimal validation plan

1. **Source review**
   - Inspect `PRODUCT.md`, `DESIGN.md`, navigation setup, `BackHandler` usage, style definitions, token usage, platform branches, accessibility props, motion settings, and layout/window-size logic.

2. **Build/static checks**
   - Run project typecheck/lint/test scripts if present.
   - iOS: run appropriate `xcodebuild` compile/test target if available.
   - Android: run Gradle assemble/lint/test target if available.

3. **iOS runtime — missing**
   - **iOS Simulator: unverified locally / not performed.**
   - Needed: iPhone compact + iPad/Split View, Dynamic Type, Reduce Motion, VoiceOver or Accessibility Inspector, keyboard traversal, safe areas, orientation, interruption recovery.

4. **Android runtime — missing**
   - **Android Emulator: unverified locally / not performed.**
   - Needed: phone + tablet/foldable or multi-window profile, font scale, Remove animations, TalkBack, keyboard/D-pad, predictive Back, IME/insets, interruption recovery.

5. **Physical hardware — missing**
   - **Real-device evidence: not performed for iOS or Android.**
   - Required before release claims for gesture feel, haptics, OEM Android behavior, one-handed reach, sustained performance, and real accessibility-device behavior.

Applied `design-craft` in native adaptive critique mode; this is a read-only benchmark review, not simulator/emulator/device validation.
