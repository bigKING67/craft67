## 1. Evidence level, platform, design read

- **Evidence level:** L0 static/contextual only — prompt + static implementation description. No source tree, build, screenshot, accessibility tree, rotation, split-screen, foldable, simulator/emulator, or hardware evidence.
- **Resolved platform:** `adaptive` with high confidence, from supplied `PRODUCT.md` context and iOS/Android store shipping target.
- **Style authority:** `DESIGN.md` allows shared semantic roles and content hierarchy, but explicitly permits platform-native navigation, controls, icons, materials, and motion.
- **Design read:** Reading this as a field task completion/review surface for one-handed operators and tablet managers, with a calm operational-native feel, optimized for fast completion, verification, and interruption recovery.

## 2. Platform-conformance verdict

- **iOS/iPadOS verdict:** **Not release-conformant.** The forced phone canvas, custom top bar/back behavior, fixed type, undersized targets, nonsemantic colors, shared Cupertino/web controls, unchanged phone tab bar on iPad, and unadapted spring motion conflict with iOS navigation, Dynamic Type, accessibility, safe-area/adaptive layout, and iPad expectations.
- **Android verdict:** **Not release-conformant, with a critical Back failure.** Consuming Android Back and bypassing predictive/system Back breaks a core Android contract. Fixed px-like layout/type, 40x40 actions, Cupertino switch, web icons, unchanged tablet bottom tabs, hard-coded colors, and missing Remove animations support also fail Material/adaptive expectations.

## 3. Prioritized findings

### P0 — System navigation is broken or replaced
- **Evidence:** Custom top bar and JS back button replace native navigation; empty `BackHandler` consumes Android Back.
- **Impact:** Users lose platform trust and may be unable to leave, recover, or rely on learned Back behavior. Android predictive Back is explicitly defeated.
- **Platforms:** iOS, Android; worse on Android.

### P0 — Accessibility release requirements are directly contradicted
- **Evidence:** `40x40` pressables; fixed `fontSize: 14`; font scaling disabled.
- **Impact:** Fails minimum target expectations, Dynamic Type/font scaling, one-handed use, VoiceOver/TalkBack readability, and likely external keyboard traversal discoverability.
- **Platforms:** iOS minimum target should be 44pt; Android should be 48dp.

### P0 — Adaptive layout is a phone mock centered on larger devices
- **Evidence:** Screen forced to `width: 390` and centered on tablets; bottom tab bar unchanged on phone, iPad, and Android tablet.
- **Impact:** Manager tablet split-screen/multi-window review is underserved; available space is wasted; navigation does not adapt to iPad/tablet/foldable patterns.
- **Platforms:** iPadOS Split View, Android tablet/multi-window/foldables.

### P1 — Visual system bypasses semantic theme authority
- **Evidence:** Raw `#777777` and `#FFFFFF` used in both appearances.
- **Impact:** Risks insufficient contrast, broken dark mode, broken high-contrast behavior, and drift from `DESIGN.md` semantic color roles.
- **Platforms:** iOS, Android.

### P1 — Platform controls, icons, and motion are accidental parity
- **Evidence:** Same Cupertino switch and one web icon set on both platforms; 500ms overshooting spring with no Reduced Motion/Remove animations alternative.
- **Impact:** Android feels like an iOS/web port; iOS loses system integration; motion may be vestibularly unsafe and too playful for operational task completion.
- **Platforms:** iOS, Android.

## 4. Concrete design moves

1. **Replace fixed `width: 390` with window/size-class adaptation.**  
   Compact phone: single task flow. Medium/expanded: task list + detail/review panes, respecting safe areas, IME, split-screen, and multi-window.

2. **Restore platform navigation contracts.**  
   iOS: native navigation stack, system back affordance, left-edge gesture. Android: remove empty Back consumption, integrate system/predictive Back, preserve task progress on interruption.

3. **Raise all action hit areas.**  
   iOS target floor: 44x44pt. Android target floor: 48x48dp with sensible spacing. Use visual compactness only if the accessible hit area remains compliant.

4. **Re-enable text scaling and adopt semantic type roles.**  
   Use iOS Dynamic Type text styles and Android `sp`/Material type roles; verify wrapping, truncation, and action reachability at large accessibility sizes.

5. **Move raw colors into semantic tokens.**  
   Replace `#777777`/`#FFFFFF` with roles such as foreground-muted, surface, surface-elevated, border, success, warning, and disabled across light/dark/high-contrast appearances.

6. **Branch controls and iconography intentionally.**  
   iOS: native switch, SF Symbols, iOS materials/tint. Android: Material switch, Material Symbols, Material color/elevation behavior. Keep labels and task semantics shared.

7. **Adapt navigation by width and platform.**  
   Phones may keep bottom tabs if there are stable top-level destinations. iPad should consider sidebar/split navigation. Android tablets should consider navigation rail/drawer rather than unchanged bottom tabs.

8. **Replace the completion animation policy.**  
   Use a calmer, shorter platform-native transition; remove overshoot for operational confirmation. Provide Reduce Motion / Remove animations path: cross-fade or immediate state change plus persistent completion feedback.

## 5. Intentional parity matrix

| Area | Stays shared | Must adapt per platform |
|---|---|---|
| Product flow | Task completion, verification, interruption recovery | Navigation presentation and Back behavior |
| Content hierarchy | Task title, status, required fields, completion proof | Large titles/sidebar/rail/top app bar treatment |
| State model | Draft, saved, complete, error, offline/interrupted | Native restoration hooks and system lifecycle behavior |
| Design tokens | Semantic roles and intent names | System colors, materials, elevation, tint/dynamic color |
| Accessibility outcomes | Screen reader support, scaling, keyboard traversal | VoiceOver vs TalkBack labels/traits/state descriptions |
| Controls | Meaning and enabled/disabled states | iOS controls vs Material controls |
| Icons | Conceptual meaning | SF Symbols on iOS, Material Symbols on Android |
| Motion | Calm confirmation and no-progress-loss feedback | iOS Reduce Motion, Android Remove animations, platform transitions |
| Tablet behavior | Manager can review efficiently | iPad split/sidebar; Android rail/drawer/fold posture |

## 6. Verified versus unverified claims

**Verified from supplied static evidence only**
- Fixed 390-wide centered screen exists in described implementation.
- Custom top bar/JS back replaces native navigation.
- Android Back is consumed by an empty handler.
- Primary actions are 40x40.
- Font size is fixed at 14 and scaling is disabled.
- Raw colors are used across appearances.
- Same Cupertino switch/web icon set ships on both platforms.
- Bottom tab bar does not adapt for tablets.
- Completion transition uses 500ms overshooting spring with no reduced/remove-motion alternative.

**Unverified**
- Actual contrast ratios.
- Actual VoiceOver/TalkBack traversal, labels, roles, and announcements.
- External keyboard order/focus visibility.
- Real clipping at large text sizes.
- Safe-area, rotation, split-screen, multi-window, foldable, and IME behavior.
- Gesture feel, frame rate, haptics, latency, or interruption recovery.
- Whether other files compensate for any described issue.

## 7. Minimal validation plan

**Source/build**
- Inspect React Native navigation setup, `BackHandler` usage, accessibility props, font scaling, token usage, platform branches, and tablet layout conditions.
- Run TypeScript/lint/unit checks if available.
- Run iOS build check via `xcodebuild` and Android build check via Gradle if the repo/toolchain exists.

**Runtime required before release claims**
- **iOS Simulator: unverified locally.** Validate iPhone + iPad, portrait/landscape, Split View, Dynamic Type accessibility sizes, VoiceOver, Reduce Motion, light/dark/high contrast.
- **Android Emulator: unverified locally.** Validate phone + tablet/foldable profiles, multi-window, font scale, TalkBack, predictive Back, Remove animations, light/dark/dynamic color.
- **Real-device evidence: missing.** Required before claiming final one-handed ergonomics, Back/gesture feel, haptics, performance, OEM behavior, and sustained field reliability.
