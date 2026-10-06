# Android quality

Use this for Jetpack Compose, Android Views, React Native/Expo, Flutter, or
another product shipping to Android. Material Design 3 and Android system
behavior govern structure, navigation, input, and accessibility; brand is
expressed through the Material theme rather than by porting iOS or web controls.

## Native trust test

Would a fluent Android user trust every control and the system Back behavior,
or recognize an iOS/web port? Use Material components and platform idioms,
including adaptive navigation, predictive Back, insets, and Dynamic Color when
appropriate.

## Layout and navigation

- Compact widths use a navigation bar with 3-5 destinations; medium/expanded
  widths use a rail or drawer when appropriate.
- Preserve system and predictive Back; do not trap or hijack the gesture.
- Apply status, navigation, cutout, hinge, and IME insets in edge-to-edge UI.
- Use top app bars for screen context and at most one FAB for the primary action.
- Use window size classes and fold posture, not device-model checks.

## Controls, type, and color

- Minimum touch target: `48x48dp`, normally with at least `8dp` separation.
- Use Material type roles and `sp`, not fixed pixel type.
- Use semantic Material color roles, a deliberate static fallback, first-class
  dark/high-contrast themes, and tonal elevation.
- Prefer Material buttons, switches, chips, snackbars, bottom sheets, dialogs,
  pickers, navigation, and Material Symbols over Cupertino/web replacements.

## Motion and feedback

- Use Material container transform, shared-axis, fade-through, or another
  platform-consistent pattern where it clarifies hierarchy.
- Honor the Remove animations setting with a cross-fade or immediate state
  change.
- Snackbars communicate transient actionable feedback; dialogs interrupt only
  for decisions that truly require it.
- Gesture-driven motion follows `interaction-physics.md` and Android nested
  scrolling/gesture coordination.

## Accessibility and resilience

- Verify TalkBack labels, roles, state descriptions, traversal order, custom
  actions, and announcements.
- Verify system font scaling without clipped text or unreachable actions.
- Test hardware keyboard/D-pad where relevant, localization expansion,
  appearance, orientation, multi-window, fold postures, offline/error states,
  and interrupted tasks.

## Runtime validation

Preferred breadth: Emulator across API levels, phone/tablet/foldable profiles,
orientations, font scales, appearance, and accessibility settings. Preferred
truth: representative real hardware for gesture navigation, OEM differences,
performance, camera/sensor, and thermal/battery behavior.

If `adb`/`emulator` is unavailable, source scan and fixture tests are useful but
the Android runtime result remains explicitly unverified.
