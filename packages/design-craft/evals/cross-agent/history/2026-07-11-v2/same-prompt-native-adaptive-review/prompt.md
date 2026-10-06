# Same prompt: native adaptive review

Use design-craft to critique the following cross-platform mobile concept. This
is a read-only benchmark: do not edit files and do not claim simulator,
emulator, or real-device validation.

Product context:

- `PRODUCT.md` platform: `adaptive`.
- Product: field operations task app shipping through iOS and Android stores.
- Primary user: operator completing a task one-handed on a phone, then a
  manager reviewing the same task in tablet split-screen or multi-window.
- Purpose: complete and verify the task quickly without losing progress when
  interrupted.
- Positioning: trustworthy, calm, and operationally native on each platform.
- Accessibility: VoiceOver, TalkBack, Dynamic Type/font scaling, Reduced
  Motion/Remove animations, and external keyboard traversal are release
  requirements.
- `DESIGN.md`: shared semantic color roles and content hierarchy; it explicitly
  allows platform-native navigation, controls, icons, materials, and motion.

Static implementation evidence:

- One React Native screen is forced to `width: 390` and centered on tablets.
- A custom top bar and JavaScript back button replace iOS navigation stack and
  Android system/predictive Back; an empty `BackHandler` consumes Android Back.
- All primary actions use `40x40` pressables.
- Text uses fixed `fontSize: 14` with font scaling disabled.
- Raw `#777777` and `#FFFFFF` values are used in both appearances.
- The same Cupertino-shaped switch and one web icon set ship on both platforms.
- A bottom tab bar remains unchanged on phone, iPad, and Android tablet.
- The task-complete transition is a 500ms spring with overshoot and has no
  Reduced Motion/Remove animations alternative.

Available evidence: prompt and static implementation description only. No
source tree, build, screenshot, accessibility tree, rotation, split-screen,
foldable, simulator/emulator, or hardware run was performed.

Return:

1. Evidence level, resolved platform, and design read.
2. Platform-conformance verdict for iOS and Android separately.
3. Prioritized accessibility, navigation, control, theming, motion, and
   adaptivity findings.
4. Concrete design moves and an intentional parity matrix: what stays shared
   versus what must adapt per platform.
5. Verified versus unverified claims.
6. Minimal source/build/runtime validation plan, explicitly naming any missing
   iOS Simulator, Android Emulator, and real-device evidence.
