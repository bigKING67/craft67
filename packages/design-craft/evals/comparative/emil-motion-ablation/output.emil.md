## Verdict

**[Static evidence] This is not yet reliable direct manipulation.** Input ownership, coordinates, and animation lifecycle need fixing before tuning the feel. **[Expected effect—not observed]** The sheet may jump, trail the pointer, resist interruption, and snap against flick intent—poor fits for a calm, frequently used operations app.

Labels below distinguish **Evidence** in the supplied code, **Risk** inferred from it, and **Recommendation** requiring validation.

## Prioritized findings

| Priority | Finding |
|---|---|
| **P0 — Gesture ownership** | **Evidence:** Every `pointermove` writes position, including mouse hover; no active-drag flag or pointer-ID check exists. No capture, cancellation, or lost-capture handling is shown. **Risk:** Accidental movement, competing pointers, and missed releases outside the sheet. |
| **P0 — Coordinate integrity** | **Evidence:** `startY` is unused; viewport-relative `clientY` is assigned directly to CSS `top`, which uses the positioning context. **Risk:** The first move loses the grab offset and can jump; coordinate mismatch depends on surrounding layout. |
| **P0 — Conflicting motion owners** | **Evidence:** `transition: all 300ms` covers positional changes while JavaScript writes `top`; release separately animates `top`. **Risk:** Drag updates chase a transitioning position instead of tracking directly. Actual interactions depend on computed styles and layout. |
| **P0 — Interruption and cleanup** | **Evidence:** `animating` blocks only down events—not moves or releases. Animation handles are discarded; `fill: "forwards"` retains the final effect without synchronizing inline position. **Risk:** Overlapping settles, stale completion callbacks, and retained effects masking subsequent writes. Cancellation would also reject `.finished` without cleanup. |
| **P0 — Reduced Motion requirement** | **Evidence:** Neither code block contains a reduced-motion branch. **Risk:** Users receive the same large spatial settle and press scale. A CSS-only override would not disable the JavaScript animation. |
| **P1 — Release behavior** | **Evidence:** Target selection receives position only; settling uses fixed 480ms `ease-in`. **Risk:** No explicit velocity-aware targeting or handoff; the sheet restarts slowly and reaches its target without a gentle deceleration. Flicks and careful placement receive the same treatment. |
| **P1 — Unnecessary surface motion** | **Evidence:** Pressing scales the entire sheet to `0.96`. **Risk:** Content and controls shrink during interaction, disturbing the grab relationship without explaining state. |
| **P1 — Rendering cost** | **Evidence:** Motion writes/animates `top` and reads `offsetTop`. **Risk:** Layout work rather than compositor-friendly translation; actual frame cost is unmeasured. |

## Concrete direct-manipulation moves

1. **Give position one owner.** Maintain explicit `idle → dragging → settling` states, one active pointer ID, one current position, and one animation handle. Keep the semantic snap state separate from intermediate position.

2. **Preserve the grab.** On eligible primary-pointer down, sample the currently displayed position, stop the existing settle without changing that position, then record pointer origin and sheet origin. During drag:
   ```js
   y = originSheetY + (event.clientY - originPointerY);
   ```
   Use one consistent coordinate system and render with `translateY`; no positional CSS transition during tracking.

3. **Own the gesture deliberately.** Prefer a dedicated handle; capture the pointer and ignore unrelated pointers. Define `pointerup`, `pointercancel`, and `lostpointercapture` cleanup. Apply an appropriate `touch-action` policy to the handle, not indiscriminately to scrollable sheet content. Preserve taps and content scrolling; introduce only a small intent threshold if needed.

4. **Make interruption continuous.** Re-grabbing must work during every settle. Start from the live displayed position—not the previous snap target. Retarget autonomous motion with current velocity; when dragging resumes, pointer movement owns position immediately. Ignore stale completion callbacks and handle cancellation explicitly.

5. **Let release express intent.** Estimate velocity from a short timestamped sample history, accounting for a pause before release. Select among collapsed, half, and full using a bounded projected endpoint, direction, and modest snap hysteresis. Slow placement should favor nearby states; intentional flicks should advance predictably.

6. **Settle quietly.** Start with a critically damped, velocity-aware spring: no decorative bounce, no fixed input lockout. Treat a roughly 0.3–0.4s response as a tuning starting point, not a verified duration. Use gentle, bounded edge resistance; never allow momentum to carry the surface offscreen.

7. **Replace whole-sheet scaling.** Give the handle immediate, restrained color or contrast feedback. Keep content stable. Commit the final position to the canonical state and remove the finished animation effect.

8. **Provide equivalent reduced-motion feedback.** Detect the preference in JavaScript as well as CSS. Keep user-controlled tracking immediate, but eliminate automatic long-distance travel, overshoot, and scaling: commit the snap immediately, optionally using a brief local opacity/color cue. Provide explicit, keyboard-operable state controls so dragging is unnecessary; visibly and accessibly identify the selected state.

## Verified / unverified boundary

- **Verified by static inspection only:** The control flow, property writes, timing parameters, and missing mechanisms listed above in the supplied excerpt.
- **Unverified:** Surrounding CSS, positioning context, `nearestSnapPoint` internals, external accessibility handling, touch-scroll arbitration, actual visual jumps, latency, and frame performance.
- **No files were edited. No browser or device validation was performed.**

## Smallest runtime validation plan

1. **One desktop browser + one physical touch device:** Exercise slow drags and directional flicks between all three states. Pass: preserved grab offset, immediate tracking, predictable targets, no hover movement.
2. **Interrupt and cancel:** Re-grab/reverse early and late in a settle; leave bounds, cancel a gesture, and introduce a second pointer. Pass: no jump, stuck state, competing animation, or unhandled rejection.
3. **Check touch arbitration:** Scroll content, tap controls, then drag the handle. Pass: each action owns only its intended behavior.
4. **Enable Reduced Motion and use keyboard controls:** Reach all three states. Pass: no automatic large spatial travel or scale, clear state feedback, retained focus.
5. **Record one drag → flick → re-grab sequence:** Inspect frame timing and layout work on representative hardware. Pass: no recurring motion-induced layout or missed-frame pattern; assess responsiveness at normal speed as well as frame-by-frame.
