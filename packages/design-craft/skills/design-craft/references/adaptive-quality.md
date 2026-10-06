# Adaptive cross-platform quality

Use this when `platform=adaptive`: React Native/Expo, Flutter, Kotlin
Multiplatform/Compose Multiplatform, or a repository with real iOS and Android
targets. Read both `ios-quality.md` and `android-quality.md` first.

Adaptive means one product family with platform-correct experiences. It does
not mean identical pixels or one stretched phone layout.

## Shared versus platform-specific

Share:

- product intent and domain model
- semantic design-token roles
- content hierarchy and core task flow
- accessibility outcomes and analytics semantics
- business rules and non-visual state machines when architecture supports it

Adapt:

- navigation model and system Back behavior
- safe-area/window/IME/hinge handling
- controls, pickers, dialogs, sheets, context actions, and icon sets
- typography scaling primitives and system materials/elevation
- motion patterns, gesture coordination, haptics, and platform feedback

Do not hide platform branching behind visual look-alikes that lose native
behavior. A shared component is valuable only when it preserves both platform
contracts.

## Structural adaptation

- Drive layout from size/window classes, available space, posture, and input
  mode rather than device names.
- Phone-to-tablet adaptation restructures navigation and content into
  appropriate columns, panes, rails, drawers, sidebars, or popovers.
- Support orientation, iPad Split View, Android multi-window, keyboard/IME,
  fold posture, and text scaling without removing core functionality.
- WebView/Capacitor/Cordova shells remain `web` unless the shipped product UI is
  actually native on both platforms.

## Cross-platform audit

Review each platform independently before comparing them:

1. iOS conformance and accessibility.
2. Android conformance and accessibility.
3. Shared design-system semantics and product parity.
4. Intentional differences versus accidental drift.
5. Performance and startup/render/gesture hot paths on each runtime.

Record a parity matrix for navigation, states, accessibility, content,
analytics, offline/error recovery, appearance, and release-critical gestures.
Pixel equality is not a parity requirement.

## Runtime validation

Minimum credible runtime evidence includes one iOS and one Android runtime,
with at least compact width plus one expanded/tablet or multi-window state when
the product supports them. Real hardware is required before claiming final
gesture, haptic, camera/sensor, OEM, or sustained-performance quality.

If either platform runtime is unavailable, report the adaptive result as
partially unverified and identify the missing platform explicitly.
