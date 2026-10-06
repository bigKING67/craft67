# iOS quality

Use this for SwiftUI, UIKit, React Native/Expo, Flutter, or another product
shipping to iPhone/iPad. Project `DESIGN.md` may express brand, but iOS Human
Interface Guidelines and OS behavior govern structure, navigation, input, and
accessibility.

## Native trust test

Would a fluent iPhone user trust every control and gesture, or recognize a web
page wearing an iOS skin? Default to system components and behavior. Depart
only when the user benefit is specific and the replacement preserves OS
guarantees.

## Layout and navigation

- Keep interactive content inside safe areas around the notch, Dynamic Island,
  rounded corners, home indicator, and keyboard.
- Use a navigation stack for hierarchy, a tab bar for 2-5 top-level sections,
  and sheets for focused dismissible tasks.
- Preserve the left-edge back gesture.
- Use large titles at appropriate top-level destinations and inline titles on
  detail screens.
- iPad and Split View use size classes and structural adaptation, not a
  stretched phone canvas.

## Controls, type, and color

- Minimum touch target: `44x44pt`.
- Use Dynamic Type text styles; avoid fixed point sizes that block user scaling.
- Prefer San Francisco/system text for UI; limit brand faces to deliberate
  display roles.
- Use semantic system colors, system materials, one coherent tint, SF Symbols,
  and first-class light/dark/high-contrast behavior.
- Prefer native switches, segmented controls, pickers, context menus, alerts,
  swipe actions, and grouped lists over HTML-shaped replacements.

## Motion and feedback

- Push, sheet, and dismissal paths should remain spatially symmetric and
  interruptible.
- Honor Reduce Motion with cross-fades or reduced travel.
- Haptics and sound fire at the causal state change, not at an unrelated end
  callback, and remain restrained.
- Gesture-driven motion follows `interaction-physics.md` and native gesture
  coordination.

## Accessibility and resilience

- Verify VoiceOver labels, traits, values, focus order, custom actions, and
  announcements.
- Verify Dynamic Type through accessibility sizes without clipping or losing
  actions.
- Test keyboard/switch control where the product supports iPad or external
  input.
- Cover appearance, orientation, localization expansion, offline/error states,
  and interrupted tasks.

## Runtime validation

Preferred breadth: Simulator across phone/tablet, orientations, Dynamic Type,
appearance, and accessibility settings. Preferred truth: representative real
hardware for gestures, haptics, performance, camera/sensor, and thermal/battery
behavior.

If `xcodebuild`/`simctl` or a simulator is unavailable, source scan and fixture
tests are useful but the iOS runtime result remains explicitly unverified.
