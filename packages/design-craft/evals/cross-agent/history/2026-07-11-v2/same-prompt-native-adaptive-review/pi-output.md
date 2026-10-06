## Design Craft Critique — Same Prompt: Native Adaptive Review

**Mode:** `critique` (read-only). No files edited; no simulator, emulator, or real-device validation claimed.

---

### 1. Evidence Level, Resolved Platform, and Design Read

**Evidence level:** `L0 static` — prompt prose and a list of static implementation descriptions only. No source tree, no build artifact, no screenshot, no accessibility tree, no runtime of any kind.

**Resolved platform:** `adaptive` (source: explicit prompt `PRODUCT.md` platform value; confidence: `0.85` because the implementation evidence strongly suggests a React Native codebase that is *not* behaving adaptively, creating a contradiction between the declared platform and the engineering behavior).

**Design read:** *Reading this as: a mobile field-operations task app for operators completing tasks one-handed on a phone and managers reviewing on tablet split-screen, with trustworthy/calm/operationally-native positioning, optimized for task completion without progress loss under interruption.*

---

### 2. Platform-Conformance Verdicts

#### iOS — **FAIL (blocking issues)**

The implementation actively destroys iOS platform trust:

- **Custom top bar + JS back button replacing UINavigationController** (ref: `ios-quality.md` *"Use a navigation stack for hierarchy"*, *"Preserve the left-edge back gesture"*). The left-edge back gesture is gone. The navigation stack is gone. Large/inline title behavior is gone. A fluent iPhone user will immediately recognize a foreign navigation model.
- **Fixed `width: 390` centered on tablets** (ref: `ios-quality.md` *"iPad and Split View use size classes and structural adaptation, not a stretched phone canvas"*). This is worse than a stretched canvas — it's a phone-sized island floating in the center of an iPad. It fails Split View, Slide Over, and any reasonable iPad posture.
- **Cupertino-shaped switch on both platforms** is correct for iOS but signals no platform-awareness when it also ships on Android.
- **`40x40` pressables** fail the `44x44pt` minimum touch target (ref: `ios-quality.md` *"Minimum touch target: 44x44pt"*).
- **Fixed `fontSize: 14` with font scaling disabled** blocks Dynamic Type, a release requirement.
- **500ms spring with overshoot and no Reduced Motion alternative** (ref: `motion-quality.md` *"Honor prefers-reduced-motion"*, `interaction-physics.md` *"Reduced Motion removes large travel, parallax, elastic overshoot"*). With the Remove animations setting on, this spring will still fire at full overshoot — a direct accessibility violation.
- **One web icon set** instead of SF Symbols (ref: `ios-quality.md` *"Prefer SF Symbols"*).

#### Android — **FAIL (blocking issues)**

The implementation destroys Android platform trust even more severely:

- **Empty `BackHandler` consuming Android Back** (ref: `android-quality.md` *"Preserve system and predictive Back; do not trap or hijack the gesture"*). The system Back gesture is fully trapped. Predictive Back is blocked. This is the single most aggressive platform violation possible on Android.
- **Custom JS back button** replaces both the system Back gesture and any top-app-bar back affordance (ref: `android-quality.md` *"Use top app bars for screen context"*). A fluent Android user will swipe from the edge, feel nothing happen, and assume the app is broken.
- **Cupertino-shaped switch on Android** (ref: `android-quality.md` *"Prefer Material switches"*). This is an iOS control on Android — the most visible possible cross-platform pollution.
- **One web icon set** instead of Material Symbols (ref: `android-quality.md` *"Prefer Material Symbols"*).
- **Fixed `width: 390` centered on tablets** fails Android multi-window and tablet posture (ref: `android-quality.md` *"Use window size classes and fold posture, not device-model checks"*).
- **`40x40` pressables** fail the `48x48dp` minimum touch target with `8dp` separation (ref: `android-quality.md` *"Minimum touch target: 48x48dp, normally with at least 8dp separation"*).
- **Fixed `fontSize: 14` with font scaling disabled** blocks Android font scaling, a release requirement.
- **Bottom tab bar unchanged on all form factors** (ref: `android-quality.md` *"Compact widths use a navigation bar with 3-5 destinations; medium/expanded widths use a rail or drawer"*). On an Android tablet, a phone tab bar is the wrong navigation structure.

---

### 3. Prioritized Findings

#### Accessibility (BLOCKING — 6 violations)

| # | Finding | Reference | Severity |
|---|---------|-----------|----------|
| A1 | Font scaling disabled on both platforms; fixed `fontSize: 14` with `allowFontScaling: false` | `ios-quality.md` Dynamic Type, `android-quality.md` font scaling, `product-context.md` accessibility requirements | **Block** — release requirement violated |
| A2 | No Reduced Motion/Remove animations alternative for the 500ms spring transition | `motion-quality.md` *"Honor prefers-reduced-motion"*, `interaction-physics.md` Reduced Motion | **Block** — release requirement violated |
| A3 | `40x40` pressables fail both iOS `44x44pt` and Android `48x48dp` minimums | `ios-quality.md`, `android-quality.md` touch targets | **Block** — especially for one-handed field use |
| A4 | VoiceOver/TalkBack labels, traits, traversal order, and custom actions are unverified but required | `product-context.md` *"VoiceOver and TalkBack labels and traversal are release requirements"* | **Unverified critical** |
| A5 | External keyboard traversal is unverified but required | `product-context.md` *"external keyboard traversal are release requirements"* | **Unverified critical** |
| A6 | Custom touch handling (empty BackHandler, custom nav bar) likely bypasses accessibility services | `ios-quality.md`, `android-quality.md` accessibility sections | **High risk** |

#### Navigation (BLOCKING — 3 violations)

| # | Finding | Reference |
|---|---------|-----------|
| N1 | Empty `BackHandler` consumes Android system/predictive Back — the most severe platform violation | `android-quality.md` *"Preserve system and predictive Back; do not trap or hijack the gesture"* |
| N2 | Custom JS back button replaces native navigation stacks on both platforms; left-edge swipe back is lost on iOS | `ios-quality.md` *"Use a navigation stack for hierarchy"*, *"Preserve the left-edge back gesture"* |
| N3 | Bottom tab bar is identical on phone, iPad, and Android tablet — no navigation rail, sidebar, or drawer for expanded widths | `adaptive-quality.md` *"Phone-to-tablet adaptation restructures navigation"*, `android-quality.md` *"medium/expanded widths use a rail or drawer"* |

#### Controls (BLOCKING — 2 violations)

| # | Finding | Reference |
|---|---------|-----------|
| C1 | Cupertino-shaped switch ships on Android — cross-platform control pollution | `adaptive-quality.md` *"Do not hide platform branching behind visual look-alikes"*, `android-quality.md` *"Prefer Material switches"* |
| C2 | Single web icon set on both platforms instead of SF Symbols on iOS and Material Symbols on Android | `ios-quality.md`, `android-quality.md` icon guidance |

#### Theming (BLOCKING — 2 violations)

| # | Finding | Reference |
|---|---------|-----------|
| T1 | Raw `#777777` and `#FFFFFF` hard-coded in both appearances — bypasses semantic design tokens, fails dark mode parity, breaks high-contrast support | `design-system-contract.md` token role enforcement, `ios-quality.md` *"Use semantic system colors"* |
| T2 | No evidence of Dynamic Color support on Android or semantic material theming; raw hex values suggest no Material 3 theme | `android-quality.md` *"Use semantic Material color roles"*, *"first-class dark/high-contrast themes"* |

#### Motion (BLOCKING — 1 violation)

| # | Finding | Reference |
|---|---------|-----------|
| M1 | 500ms spring with overshoot exceeds the standard UI animation range (200-500ms for modals/drawers) and has no Reduced Motion alternative | `motion-quality.md` timing bounds, accessibility, `interaction-physics.md` |

#### Adaptivity (BLOCKING — 2 violations)

| # | Finding | Reference |
|---|---------|-----------|
| AD1 | `width: 390` forced and centered on all tablets — the defining anti-pattern of fake adaptive engineering | `adaptive-quality.md` *"Adaptive means one product family with platform-correct experiences. It does not mean identical pixels or one stretched phone layout."* |
| AD2 | No structural adaptation for iPad Split View, Android multi-window, fold postures, or orientation changes | `adaptive-quality.md` *"Support orientation, iPad Split View, Android multi-window, keyboard/IME, fold posture, and text scaling"* |

---

### 4. Concrete Design Moves and Intentional Parity Matrix

#### Design Moves (in priority order)

**Move 1 — Restore native navigation (highest priority).**
Delete the custom top bar and JS back button. Use `react-navigation` native stack on iOS (UINavigationController semantics, large/inline titles, left-edge back gesture) and a native-feeling stack on Android with proper `BackHandler` integration that does not consume the event. On Android, let system Back and predictive Back work without interference.

**Move 2 — Adaptive layout by window size class, not fixed pixels.**
Replace `width: 390` with layout driven by `useWindowDimensions` plus size-class heuristics or a library like `react-native-size-matters` used responsibly. Phone: single-column, full-width. Tablet: split-pane (task list + detail), navigation rail, or a responsive column layout. Support iPad Split View and Android multi-window resize.

**Move 3 — Platform-adaptive controls.**
On iOS: use a native `Switch` (Cupertino), SF Symbols via `react-native-sfsymbols`, and system pickers/sheets. On Android: use Material `Switch`, Material Symbols, and platform-appropriate dialogs/snackbars. Do not ship the same control on both platforms.

**Move 4 — Touch targets to platform minimums.**
Resize all primary action pressables: `44x44pt` on iOS, `48x48dp` on Android. For one-handed field use, consider even larger targets for critical actions (complete task, emergency, next step).

**Move 5 — Font scaling and Dynamic Type.**
Remove `allowFontScaling: false`. Use Dynamic Type text styles on iOS (`body`, `callout`, `title3`, etc.) and `sp`-based scaling on Android. Test at 200% scaling without clipping or losing actions.

**Move 6 — Design tokens over raw hex.**
Replace `#777777` and `#FFFFFF` with semantic token references from `DESIGN.md` (e.g., `color.text.secondary`, `color.surface.primary`). Ensure light/dark/high-contrast parity for all tokens.

**Move 7 — Motion accessibility.**
Keep the spring transition for the happy path but gate it: when `AccessibilityInfo.isReduceMotionEnabled()` returns true on either platform, replace the 500ms spring with a 200ms cross-fade or immediate state change. Keep the spring damping at or above `0.8` even in the animated path.

**Move 8 — Navigation adaptation for tablets.**
Replace the bottom tab bar on tablets: use a navigation rail or sidebar on iPad (per size class `regular` width) and a navigation rail on Android tablets. Keep the tab bar only on compact-width phones.

#### Intentional Parity Matrix

| Concern | Shared | iOS-specific | Android-specific |
|---------|--------|-------------|-----------------|
| **Domain model, task state machine, business rules** | ✓ Shared | — | — |
| **Semantic design-token roles** (color, spacing, type roles) | ✓ Shared | — | — |
| **Content hierarchy and core task flow** | ✓ Shared | — | — |
| **Accessibility outcomes** (labels, roles, traversal quality) | ✓ Shared goal | — | — |
| **Navigation model** | — | UINavigationController stack, left-edge swipe back, large/inline titles, tab bar (compact) / sidebar (regular) | Top app bar, system Back + predictive Back, bottom nav (compact) / rail (expanded) |
| **Back behavior** | — | Native stack pop, left-edge gesture | System Back gesture, predictive Back animation |
| **Controls** | — | Cupertino switch, SF Symbols, native pickers/sheets | Material switch, Material Symbols, MD3 dialogs/snackbars |
| **Typography primitives** | — | Dynamic Type text styles (`body`, `title3`, etc.) | `sp` units with Material type scale |
| **Touch targets** | — | `44x44pt` minimum | `48x48dp` minimum, `8dp` separation |
| **Icons** | — | SF Symbols | Material Symbols |
| **Motion language** | Semantic intent (task completion feedback) | iOS spring parameters, Reduce Motion cross-fade | MD3 container transform or fade-through, Remove animations cross-fade |
| **Haptics** | — | `UIImpactFeedbackGenerator` styles | `HapticFeedbackConstants` |
| **Layout adaptation** | Size-class and window-width logic | iPad Split View, Slide Over, size classes | Multi-window resize, fold postures |
| **Appearance** | Semantic token roles, light/dark parity | System appearance + manual toggle | System appearance + manual toggle + Dynamic Color (optional) |

---

### 5. Verified Versus Unverified Claims

**Verified (from prompt static evidence only):**

| Claim | Evidence |
|-------|----------|
| Screen forced to `width: 390` on tablets | Directly stated in implementation description |
| Custom top bar + JS back button replaces native navigation | Directly stated |
| Empty `BackHandler` consumes Android Back | Directly stated |
| `40x40` pressables for primary actions | Directly stated |
| Fixed `fontSize: 14` with font scaling disabled | Directly stated |
| Raw `#777777` and `#FFFFFF` hard-coded | Directly stated |
| Cupertino switch on both platforms | Directly stated |
| Single web icon set on both platforms | Directly stated |
| Bottom tab bar unchanged across form factors | Directly stated |
| 500ms spring with overshoot, no Reduced Motion alternative | Directly stated |

**Unverified (claimed as release requirements or implied, but no evidence provided):**

| Claim | Status |
|-------|--------|
| VoiceOver labels, traits, and traversal exist and are correct | Unverified — no accessibility tree, no audit, no VoiceOver run |
| TalkBack labels, roles, and traversal exist and are correct | Unverified — no TalkBack run |
| Dynamic Type / font scaling reaches 200% without clipping | **Falsified by static evidence** — font scaling is explicitly disabled |
| Reduced Motion replaces transitions with cross-fades | **Falsified by static evidence** — no Reduced Motion alternative exists for the 500ms spring |
| External keyboard traversal works | Unverified — no keyboard test |
| The app actually runs on both iOS and Android | Unverified — no build or runtime evidence |
| Safe-area insets are handled correctly | Unverified — no notch/Dynamic Island/home-indicator evidence |
| Offline/error states and interrupted-task recovery work | Unverified — no state coverage |
| Switch access or alternative input works | Unverified |
| `DESIGN.md` semantic color roles are actually defined | Unverified — `DESIGN.md` path not provided, no token file evidence |
| `PRODUCT.md` exists with the described content | Unverified — prompt describes it but no file was provided |

**Confidence:** Platform-conformance violations are `0.95` confidence because they follow from the stated implementation choices and platform requirements. Accessibility violations for font scaling and Reduced Motion are `1.0` confidence because the prompt explicitly describes behavior that contradicts stated release requirements. All unverified claims are marked as such.

---

### 6. Minimal Source/Build/Runtime Validation Plan

#### Source validation (can run now, no toolchain needed)

1. **`PRODUCT.md` audit**: Locate and read `PRODUCT.md`. Verify that `Platform: adaptive`, accessibility requirements, and user definitions match what the prompt describes. Confirm no visual tokens have leaked into `PRODUCT.md` (ref: `product-context.md` separation of authority).
2. **`DESIGN.md` audit**: Locate and read `DESIGN.md`. Verify that semantic color roles, type scales, spacing tokens, motion primitives, and light/dark parity are defined. Confirm no hard-coded `#777777` or `#FFFFFF` bypasses the token system.
3. **Static platform scan**: `scripts/design_craft_platform_scan.py --target <repo> --platform adaptive --json` to detect native source patterns vs. web-shaped code.
4. **Token audit**: `scripts/design_craft_token_audit.py --target <repo>` to find hard-coded colors, fixed font sizes, and arbitrary spacing that bypass the design system.
5. **CSS/focus smell scan**: `scripts/design_craft_css_smell_scan.py` and `scripts/design_craft_focus_audit.py` for the React Native style layer.
6. **Source grep for known anti-patterns**:
   - `width: 390` (or any fixed width on root containers)
   - `allowFontScaling: false`
   - `BackHandler.addEventListener` with empty or consuming handlers
   - `fontSize: 14` (or any fixed numeric fontSize without scaling)
   - `#777777`, `#FFFFFF`, or any raw hex in component styles
   - Import paths for icon sets (verify web icon library vs. SF Symbols / Material Symbols)

#### Build validation (requires toolchain)

1. **iOS**: `xcodebuild` or `npx react-native run-ios` — verify it compiles without error. This is a minimum bar.
2. **Android**: `./gradlew assembleDebug` or `npx react-native run-android` — verify it compiles.
3. **Type-check**: `npx tsc --noEmit` (TypeScript) or `npx flow check` (Flow).

#### Runtime validation (requires simulators/emulators — **none performed**)

| Platform | Tool | What to Validate | Status |
|----------|------|-----------------|--------|
| **iOS Simulator** | `simctl` / Xcode | iPhone SE (compact), iPhone 15 Pro Max, iPad Pro 12.9" (Split View, Slide Over), Dynamic Type at accessibility sizes, Reduce Motion ON, VoiceOver traversal, light/dark toggle, orientation rotation | **Unverified locally** |
| **Android Emulator** | `adb` / Android Studio | Pixel 8 (compact), Pixel Tablet (multi-window, split-screen), font scaling at 200%, Remove animations ON, TalkBack traversal, dark theme, foldable emulator profile, orientation, gesture navigation (3-button + gesture) | **Unverified locally** |
| **Real iOS device** | Physical iPhone + iPad | Haptics, actual one-handed feel, camera/sensor, thermal/battery, real notch/Dynamic Island/home indicator behavior, real VoiceOver gestures | **Unverified — no hardware evidence** |
| **Real Android device** | Physical phone + tablet | OEM gesture differences, haptics, camera/sensor, actual one-handed feel, real TalkBack behavior, real performance under thermal load | **Unverified — no hardware evidence** |

#### Specific interaction tests to run (when runtime is available)

1. On Android: swipe from the left edge with gesture navigation enabled. Does Back fire? Does the app navigate back? Does predictive Back show a preview? **The prompt evidence says it will fail.**
2. On iOS: swipe from the left edge of the screen. Does the navigation stack pop? **The prompt evidence says it will not.**
3. On iPad: open in Split View at 1/3 width, 1/2 width, and 2/3 width. Does the layout reflow or remain a centered 390px island?
4. On Android tablet: enable multi-window and resize. Does the layout adapt?
5. Set Dynamic Type to the largest accessibility size on iOS. Are all actions still reachable? **The prompt evidence says no.**
6. Set font scaling to 200% on Android. Is all text visible without clipping?
7. Enable Reduce Motion / Remove animations. Trigger task completion. Does a cross-fade play instead of the spring? **The prompt evidence says no.**
8. Run VoiceOver and TalkBack through the complete task flow: open task → read fields → complete task → verify. Are all controls labeled? Is traversal order logical?

---

### Summary

This implementation is **not adaptive** — it is a single-platform (and arguably neither-iOS-nor-Android) React Native screen with the wrong controls, wrong navigation, wrong touch targets, no font scaling, no motion accessibility, and no structural adaptation for tablets. It violates the four most fundamental platform contracts on Android (system Back, Material controls, Material icons, `48dp` touch targets) and three on iOS (navigation stack, SF Symbols, `44pt` touch targets). It also violates two stated release-critical accessibility requirements (font scaling and Reduced Motion). The design intent in `PRODUCT.md` — trustworthy, calm, operationally native — is contradicted by the implementation at every platform touchpoint.

**The fastest corrective path:** restore native navigation stacks on both platforms, let the system handle Back, swap to platform-native controls and icons, drive layout from size classes, enable font scaling, add Reduced Motion gating, and resize all touch targets to platform minimums. Only then does the question of "adaptive parity" become meaningful.
