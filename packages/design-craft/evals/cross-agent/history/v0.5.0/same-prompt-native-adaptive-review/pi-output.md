## 1. Evidence level, platform, design read

- **Evidence level:** L0 static/prose evidence with explicit product context. No source tree, build, screenshot, accessibility tree, simulator/emulator, or device run.
- **Resolved platform:** `adaptive`, from supplied `PRODUCT.md` context.
- **Design read:** Reading this as a native field-operations task flow for one-handed operators and tablet-review managers, with a calm trustworthy operational tone, optimized for fast completion, review, and interruption-safe progress.

## 2. Platform-conformance verdict

- **iOS / iPadOS:** **Release-blocking non-conformance.** The concept fights iOS navigation, Dynamic Type, minimum target sizing, system controls/icons/materials, Reduce Motion, and iPad adaptive layout expectations.
- **Android:** **Release-blocking non-conformance.** Consuming Android Back, ignoring predictive Back, shipping Cupertino/web controls, fixed type, undersized targets, unchanged tablet tabs, and no Remove animations path are not operationally native.

## 3. Prioritized findings — max five blockers

1. **Adaptive layout is effectively a phone mock on larger devices.**  
   Evidence: screen forced to `width: 390` and centered on tablets; bottom tabs unchanged on phone, iPad, and Android tablet.  
   Impact: manager split-screen/multi-window review is compromised; tablet space does not improve verification speed.

2. **Navigation breaks platform trust and recovery.**  
   Evidence: custom top bar and JS back button replace native stacks; empty `BackHandler` consumes Android Back.  
   Impact: iOS loses expected stack/edge-back behavior; Android loses system/predictive Back and may trap interrupted users.

3. **Accessibility release requirements are directly contradicted.**  
   Evidence: `40x40` pressables, fixed `fontSize: 14`, font scaling disabled.  
   Impact: below iOS `44x44pt` and Android `48x48dp` targets; Dynamic Type/font scaling cannot meet release requirements.

4. **Theming and controls are accidental parity, not native parity.**  
   Evidence: raw `#777777`/`#FFFFFF` in both appearances; same Cupertino switch and web icon set on both platforms.  
   Impact: weak dark/high-contrast resilience, possible contrast failures, and platform users see an obvious port.

5. **Completion motion is too expressive and not accessibility-aware.**  
   Evidence: 500ms spring with overshoot and no Reduced Motion/Remove animations alternative.  
   Impact: violates calm operational positioning and motion-accessibility requirements; completion feedback may feel decorative or vestibular.

## 4. Concrete design moves

1. Replace fixed `390` layout with size/window-class driven layouts: compact phone, medium tablet/split, expanded tablet.
2. Keep compact phone optimized for one-handed task completion; move frequent actions near thumb reach without shrinking targets.
3. Create tablet review structure: iPad sidebar/split view; Android navigation rail or list-detail pane for medium/expanded widths.
4. Restore platform navigation: iOS native stack/sheet behavior with edge-back; Android system/predictive Back with dirty-state confirmation only when needed.
5. Raise touch targets: iOS minimum `44x44pt`; Android minimum `48x48dp`, with adequate spacing and hit slop.
6. Enable text scaling: Dynamic Type/text styles on iOS, `sp`/Material type roles on Android; verify up to accessibility/200% sizes.
7. Replace raw colors/icons/controls with semantic tokens plus native mappings: SF Symbols/system controls on iOS, Material Symbols/Material controls on Android.
8. Redesign completion feedback as short, causal, interruptible platform motion; Reduced Motion/Remove animations should use immediate state change or subtle cross-fade, not overshoot.

## 5. Intentional parity matrix

| Area | Shared | iOS / iPadOS adapts | Android adapts |
|---|---|---|---|
| Product flow | Task state, completion, verification, progress recovery | Native stack/sheets, iPad split structure | Predictive Back, Material hierarchy, multi-window/fold posture |
| Layout | Content hierarchy and semantic regions | Size classes, safe areas, sidebar/split view | Window size classes, navigation rail/drawer, hinge/IME insets |
| Controls | Meaning and state model | Native switches, pickers, alerts, SF Symbols | Material switches, dialogs, snackbars, Material Symbols |
| Type | Hierarchy roles | Dynamic Type text styles | Material type roles using scalable `sp` |
| Color | Semantic roles from `DESIGN.md` | System colors/materials/tint mapping | Material color roles, tonal elevation, optional Dynamic Color |
| Motion | Causal feedback and reduced-motion outcome | iOS push/sheet/cross-fade conventions | Material fade-through/shared-axis/container patterns |
| Accessibility | Equivalent completion with AT and keyboard | VoiceOver, Switch Control, hardware keyboard on iPad | TalkBack, D-pad/keyboard, Remove animations |
| Analytics/state | Same task semantics and recovery events | Platform-specific navigation events if needed | Back/multi-window/fold events if needed |

## 6. Verified versus unverified claims

**Verified only from supplied static description:**
- Forced `width: 390`.
- Custom top bar / JS back button.
- Empty Android `BackHandler` consuming Back.
- `40x40` pressables.
- Fixed `fontSize: 14` with font scaling disabled.
- Raw color values.
- Shared Cupertino switch and web icons.
- Unchanged bottom tabs across form factors.
- 500ms overshooting completion spring without reduced-motion alternative.

**Unverified:**
- Actual rendered appearance, contrast ratios, clipping, focus order, labels, roles, announcements.
- iOS edge-back, Android predictive Back behavior at runtime.
- Rotation, iPad Split View, Android multi-window, foldables, IME/insets.
- VoiceOver, TalkBack, external keyboard traversal.
- Animation smoothness, performance, interruption behavior, haptics.
- Any simulator, emulator, or real-device result.

## 7. Minimal validation plan

1. **Source audit:** inspect `PRODUCT.md`, `DESIGN.md`, React Native navigation, `BackHandler`, `allowFontScaling`, Pressable sizes/hit slop, token usage, platform branches, safe-area/inset handling, window-size adaptation, and reduced-motion hooks.
2. **Build/static checks:** run project type-check, lint, unit tests; then platform builds such as iOS `xcodebuild` and Android Gradle if available.
3. **iOS Simulator:** **unverified locally**. Required: iPhone + iPad, portrait/landscape, Split View, Dynamic Type accessibility sizes, VoiceOver, Reduce Motion, external keyboard.
4. **Android Emulator:** **unverified locally**. Required: phone + tablet/foldable profiles, multi-window, font scale 200%, TalkBack, Remove animations, predictive Back, keyboard/D-pad.
5. **Real-device evidence:** missing. Required before release claims for one-handed ergonomics, gesture feel, haptics, sustained performance, OEM Android variance, and interruption recovery.
