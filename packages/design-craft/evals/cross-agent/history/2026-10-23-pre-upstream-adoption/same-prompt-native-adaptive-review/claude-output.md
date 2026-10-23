## design-craft critique: adaptive field-ops task screen

**Mode:** `critique` (read-only). **References applied:** `adaptive-quality.md`, `ios-quality.md`, `android-quality.md`. I did not run the route planner or the static-review helpers because there is no source tree to point them at.

### 1. Evidence level, platform, design read

- **Evidence level:** static description only (the prompt plus your implementation notes). There was no source, build, screenshot, accessibility tree, or runtime of any kind.
- **Resolved platform:** `adaptive`. `PRODUCT.md` says so, it's a React Native screen, and it ships to both stores. Confidence in the platform is high. Confidence in how it actually behaves is low until it runs on a device.
- **Authority:** `DESIGN.md` shares color roles and content hierarchy, and explicitly allows native navigation, controls, icons, materials and motion. So the shared look-alikes described below aren't required by the design system. They are accidental drift.
- **Design read:** Reading this as a native field-task flow for a one-handed phone operator and a split-screen tablet manager, with a calm, trustworthy, platform-native feel, optimized for finishing and verifying a task without losing progress when interrupted.

### 2. Platform-conformance verdicts

- **iOS: Fails (static).** The custom top bar and JS back button replace the navigation stack, so there's no left-edge swipe back and no native title behavior. Targets are 40pt (below 44pt). Dynamic Type is blocked. The iPad layout is a centered 390pt phone canvas. There's no Reduce Motion path. The Cupertino switch looks right on iOS, but it's custom, so its VoiceOver role and value are unverified.
- **Android: Fails (static), and worse than iOS.** An empty `BackHandler` swallows system and predictive Back, which traps the user. Targets are 40dp (below 48dp). Font scale (`sp`) is disabled. An iOS-shaped switch and web icons stand in for Material. The bottom bar never becomes a rail on medium or expanded windows. There's no Remove-animations path.

### 3. Prioritized findings (blocking: F1–F5)

| ID | Pri | Area | Source proof (from your description) | Runtime unknown | Fix | Acceptance evidence |
|---|---|---|---|---|---|---|
| F1 | P0 | Navigation | JS back replaces the iOS stack; empty `BackHandler` swallows Android Back | Whether in-progress task state survives back, kill or restore | Use the native stack on both platforms (e.g. react-navigation native-stack). Delete the empty handler. Only intercept Back when there's unsaved work, and then show a "Keep editing / Discard" choice instead of swallowing it. Persist the task draft on every step. | Edge swipe works on iOS. Predictive-Back preview works on Android 14+. The draft survives background, kill and relaunch on both. |
| F2 | P0 | A11y / type | Fixed `fontSize: 14` with font scaling disabled | Clipping and reflow at large sizes | Turn scaling back on. Map shared semantic text roles to Dynamic Type styles on iOS and Material `sp` roles on Android. Cap scaling only on decorative or display text. Let rows reflow vertically. | At AX5 (iOS) and 200% font scale (Android), no text clips and every primary action can still be reached. |
| F3 | P0 | Controls / a11y | All primary actions are `40x40` | Real hit area if there's already padding or `hitSlop` | Make the effective target at least 44pt on iOS and at least 48dp on Android, with 8dp spacing. Put the main "Complete" action within thumb reach as a full-width button. | Accessibility Inspector and Android Accessibility Scanner report no target-size issues. |
| F4 | P0 | Adaptivity | `width: 390` centered; bottom tabs unchanged on phone, iPad and Android tablet | Narrow split widths (about 320pt in Slide Over or a ⅓ split), rotation, fold posture | Lay out by window or size class, never by device. Compact: stack plus tab or nav bar. Regular/expanded: list and detail side by side for the manager, with a sidebar on iPad and a navigation rail on Android. Remove the fixed width. | Screens at compact width, iPad ½ and ⅓ Split View, Android multi-window, and an unfolded foldable show no horizontal clipping and both panes. |
| F5 | P1→blocking | Motion / a11y | 500ms overshoot spring with no reduced-motion branch | Frame pacing on low-end Android | Use a short, critically damped confirmation (about 200–250ms, no overshoot). With Reduce Motion or Remove animations on, cross-fade or change state instantly. Fire the haptic at the moment of completion, not when the animation ends. Announce "Task completed" through `AccessibilityInfo`. | The reduced-motion path is visible with each OS setting on. VoiceOver and TalkBack announce completion. |
| F6 | P1 | Theming | Raw `#777777` / `#FFFFFF` in both light and dark | Whether dark mode shows a white surface or white-on-light text | Map onto `DESIGN.md` semantic roles: iOS semantic colors and Material color roles, with real dark and high-contrast values. `#777` on `#FFF` is about **4.48:1, just under AA 4.5:1** for 14pt body text. | A contrast check passes in light, dark and increased contrast on both platforms. |
| F7 | P1 | Controls / icons | Cupertino switch and one web icon set on both platforms | Switch role and state for TalkBack and VoiceOver | Use the native switch on each platform (RN `Switch` follows the platform), SF Symbols on iOS, Material Symbols on Android. Keep icon meaning shared. | Each switch reports role, state and label in the accessibility tree. |
| F8 | P1 | Keyboard | Custom pressables and top bar | Focus order, visible focus, Esc/Back, Tab traversal | Use the native header and stack. Give each pressable a focus style plus `accessibilityRole` and label. Order focus to match reading order. | With an external keyboard on iPad and Android, Tab reaches every action in order with visible focus. |

### 4. Design moves and parity matrix

**Moves** (each covers the findings listed):
1. Use the native stack and system Back on both platforms, with a guard that only appears when there's unsaved work (F1, F8).
2. Save the task draft per step, so interruptions, Back and process death are all safe (F1, product purpose).
3. Map semantic type roles to Dynamic Type and `sp`, and let layouts reflow (F2).
4. Size targets per platform (44pt on iOS, 48dp on Android) with a thumb-zone primary action (F3).
5. Base layout on window class: one stack in compact, list and detail in regular/expanded; sidebar on iPad, rail on Android (F4).
6. Define one completion motion with a reduced-motion variant, the haptic at the state change, and a spoken announcement (F5).
7. Turn semantic color roles into per-platform tokens with dark and high-contrast values (F6).
8. Use the native switch and native icon set on each platform, with icon meaning shared (F7).

**Parity matrix** (identical behavior is the goal for the shared rows; matching pixels is not):

| Dimension | Shared | iOS adapts | Android adapts |
|---|---|---|---|
| Task flow, states, domain rules | ✔ same steps, validation, offline/error/recovery | — | — |
| Content hierarchy, copy, analytics events | ✔ | — | — |
| Color | Semantic roles from `DESIGN.md` | System semantic colors, materials | M3 color roles, tonal elevation, optional Dynamic Color |
| Navigation | Same information architecture and destinations | Stack plus edge swipe; tab bar → sidebar on iPad | Predictive Back; nav bar → rail/drawer when expanded |
| Type | Semantic role names | Dynamic Type styles, SF | Material type roles in `sp` |
| Controls | Control intent (toggle, confirm) | `UISwitch`-style, action sheets | Material switch, bottom sheet, snackbar |
| Icons | Icon meaning | SF Symbols | Material Symbols |
| Motion | Completion meaning and duration budget; reduced-motion outcome | Spring/fade honoring Reduce Motion | Material fade-through honoring Remove animations |
| Accessibility outcome | Labels, order, announcements, keyboard reach | VoiceOver traits, rotor | TalkBack roles, state descriptions |
| Layout | Pane content model | Size classes, Split View | Window size classes, multi-window, fold posture |

### 5. Verified vs. unverified

- **Verified from your description:** the 40×40 targets fall short of 44pt and 48dp; fixed type with scaling disabled conflicts with the release requirement; an empty `BackHandler` swallows Back; the fixed 390 width and the unchanged tab bar on tablets aren't adaptive; there's no reduced-motion branch; #777 on #FFF is about 4.48:1 (arithmetic only).
- **Unverified:** actual rendering, clipping and split-view behavior; dark-mode appearance; VoiceOver and TalkBack output; keyboard focus; whether task progress survives interruption; animation frame pacing; haptics. I did not run an iOS Simulator, an Android Emulator, or a real device.

### 6. Minimal validation plan (nothing below has been run)

1. **Source:** confirm the navigation library, every `BackHandler` call, `allowFontScaling` and `maxFontSizeMultiplier` usage, hard-coded colors and sizes, and `AccessibilityInfo.isReduceMotionEnabled` usage. Then run `design_craft_static_review.py` and `design_craft_token_audit.py` against the tree.
2. **Build:** a debug and a release build for each platform, plus lint and typecheck.
3. **iOS Simulator (missing):** iPhone compact; iPad ½ and ⅓ Split View in both orientations; Dynamic Type at AX5; dark mode with Increase Contrast; Reduce Motion; VoiceOver pass; external keyboard Tab pass; background, kill and relaunch mid-task.
4. **Android Emulator (missing):** phone; tablet and foldable profiles; multi-window; font scale 200%; dark mode; Remove animations; TalkBack pass; predictive Back on API 34+; hardware keyboard; "Don't keep activities" to test process death.
5. **Real devices (missing):** at least one iPhone and one mid-range Android, to judge the edge-swipe and gesture-Back feel, haptic timing, one-handed reach, and frame pacing of the completion animation.

All eight findings stay open until steps 3–5 produce artifacts. The adaptive verdict is unverified on both platforms.
