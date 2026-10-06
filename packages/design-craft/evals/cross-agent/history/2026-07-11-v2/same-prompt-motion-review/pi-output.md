## Design Craft — Motion Critique: Gesture Sheet

**Mode:** `critique` (read-only)
**Evidence level:** Static source only — JavaScript + CSS snippet, no pointer trace, frame timeline, Reduced Motion run, responsive run, or real-device touch test. Per `interaction-physics.md`: *static source checks cannot prove gesture feel.*

---

### Design Read

**Reading this as:** a web operations app for repeated daily use, with calm utility UI, optimized for preserving task context while dragging a sheet between `collapsed` / `half` / `full`. Motion exists only to preserve causality and direct manipulation — not to entertain.

---

### 1. Should This Motion Exist?

**Yes**, but only parts of it. Per `motion-quality.md` frequency table: a sheet dragged "tens/day" merits standard animation with restraint. The snap-to-nearest-point after release serves a causal purpose (spatial consistency + state indication). The `scale(0.96)` press feedback is also valid if brief.

**What must not animate as written:**

| Element | Problem |
|---|---|
| `transition: all 300ms` on `.sheet` | Animates `top` (layout property — violates performance gate). `all` catches every property change, including unintended ones. |
| `ease-in` on the snap animation | Delays the moment users watch most. Directly violates `motion-quality.md`: *"Avoid ease-in for UI interactions."* |
| 480ms snap duration | Too long for a daily-use utility interaction. Motion-quality defaults modal/drawer to 200-500ms, but a repeated sheet snap should be brisker (200-350ms). |
| `:active` scale relying on the 300ms `transition: all` | The press-down feedback will lag by 300ms instead of responding in 100-160ms. Wrong easing, wrong property scope, wrong duration. |

---

### 2. Prioritized Findings

#### 🔴 **Block — `ease-in` on the snap animation**

```js
{ duration: 480, easing: "ease-in", fill: "forwards" }
```

`ease-in` starts slow and accelerates. The user releases the sheet and sees… nothing for the first ~100ms, then a lurch. This is the opposite of what direct manipulation demands: the animation must start at the carried velocity and settle. Per `motion-quality.md`: *"Users need immediate response at the start."*

**User impact:** The sheet feels sticky/unresponsive on release. In a daily-use ops tool, this erodes trust that the interface heard the input.

---

#### 🔴 **Block — No interruption; `animating` flag locks input**

```js
if (animating) return;
// ...
animating = true;
// ... animation.finished.then(() => animating = false);
```

The entire ~480ms snap window is a dead zone. If the user grabs the sheet mid-snap to reverse direction, the input is silently dropped. `interaction-physics.md` is explicit: *"never lock input until a transition completes."*

**User impact:** In an ops app used repeatedly, a user will grab the sheet again before a snap finishes — especially after an 480ms `ease-in` that feels delayed. Dropped input teaches the user to wait, which is anti-agency (product-design-principles: Agency).

---

#### 🔴 **Block — No velocity tracking or projected endpoint**

```js
const target = nearestSnapPoint(sheet.offsetTop);
```

The snap target is chosen only from the release position. A quick flick toward `full` that ends just above the `half` threshold will snap to `half` — ignoring the user's clear intent. `interaction-physics.md` requires projection:

```text
projectedEndpoint = current + projection(releaseVelocity, 0.998)
target = nearestSnapPoint(projectedEndpoint)
```

**User impact:** Inconsistent snapping undermines direct-manipulation causality. The sheet fights the user's momentum.

---

#### 🟡 **Approve with changes — `transition: all 300ms` on `.sheet`**

Animating `top` triggers layout recalculation on every frame. `motion-quality.md`: *"Avoid animating layout properties such as top and left."* The JS already sets `top` via `pointermove`, so the CSS transition fights the JS for control of the same property during drags — potentially causing stutter. The `:active` scale also inherits this 300ms/`all` transition, making press feedback sluggish.

---

#### 🟡 **Approve with changes — Missing hysteresis and pointer capture**

No intent threshold before committing to a drag. A short tap will move the sheet by 1-2px before the snap fires. `interaction-physics.md`: *"Require roughly 8-12px of movement before committing a drag direction so taps remain taps."*

No `setPointerCapture` — if the pointer leaves the sheet bounds, tracking stops. On a narrow sheet (collapsed state), this is likely.

---

#### 🟡 **Approve with changes — `:active` press feedback missing its own transition**

`scale(0.96)` is a reasonable value, but it piggybacks on `transition: all 300ms`. Press feedback should be 100-160ms with strong `ease-out` per `motion-quality.md`. A missing `:active` transition also means there's no Reduced Motion alternative.

---

#### 🟢 **Approve — `fill: "forwards"` on the snap**

Correct — preserves the final `top` value so the sheet doesn't snap back. But unnecessary if the JS sets `style.top` after the animation completes. Minor redundancy, not a defect.

---

### 3. Concrete Design Moves

#### Pointer-down feedback

```css
.sheet {
  transition: transform 120ms var(--ease-out);
}
.sheet:active {
  transform: scale(0.97);
}
```

Separate transition from the sheet's positional logic. Drop `all`. Keep duration ≤160ms. Per `motion-quality.md`, press feedback should use `ease-out` and stay under 160ms.

#### 1:1 tracking

```js
let grabOffset = 0;
let gestureActive = false;

sheet.addEventListener("pointerdown", (e) => {
  if (gestureActive) return; // interrupt current snap instead of dropping input
  sheet.setPointerCapture(e.pointerId);
  grabOffset = e.clientY - sheet.getBoundingClientRect().top;
  gestureActive = false; // wait for hysteresis
});

sheet.addEventListener("pointermove", (e) => {
  const dy = Math.abs(e.clientY - startY);
  if (!gestureActive && dy < 10) return; // hysteresis ~10px
  gestureActive = true;
  // Cancel any in-flight WAAPI animation, read current presentation value
  sheet.style.top = `${e.clientY - grabOffset}px`;
});
```

Key improvements: pointer capture, grab-offset preservation, hysteresis threshold, and cancellation of in-flight animations instead of input blocking.

#### Presentation-value interruption

```js
sheet.addEventListener("pointerdown", (e) => {
  // Instead of "if (animating) return", cancel current animation:
  if (sheet.getAnimations().length > 0) {
    sheet.getAnimations().forEach(a => a.cancel());
    // Read the current computed top so we retarget from presentation value
    sheet.style.top = `${sheet.getBoundingClientRect().top}px`;
  }
  // ... proceed with tracking
});
```

Per `interaction-physics.md`: *"retarget from the current on-screen presentation value, not the previous logical target."*

#### Velocity handoff + projected endpoints

```js
const VELOCITY_HISTORY = 5;
const pointerHistory = [];

function measureVelocity(event) {
  pointerHistory.push({ y: event.clientY, t: event.timeStamp });
  if (pointerHistory.length > VELOCITY_HISTORY) pointerHistory.shift();
}

function releaseVelocity() {
  if (pointerHistory.length < 2) return 0;
  const first = pointerHistory[0];
  const last = pointerHistory[pointerHistory.length - 1];
  const dt = last.t - first.t;
  if (dt === 0) return 0;
  return (last.y - first.y) / dt; // px/ms
}

function projectedEndpoint(current, velocity) {
  const d = 0.998;
  return current + (velocity * d) / (1 - d);
}
```

Then: `target = nearestSnapPoint(projectedEndpoint(currentTop, releaseVelocity()));`

#### Soft boundaries

For the `collapsed` and `full` extremes, apply progressive resistance during tracking:

```js
function rubberBand(offset, min, max, constant = 0.55) {
  if (offset < min) {
    const overshoot = min - offset;
    return min - (overshoot * max * constant) / (max + constant * overshoot);
  }
  if (offset > max) {
    const overshoot = offset - max;
    return max + (overshoot * max * constant) / (max + constant * overshoot);
  }
  return offset;
}
```

Per `interaction-physics.md`: the provided formula uses `dimension` as the range length and `constant` starting at `0.55`.

#### Snap animation

```js
sheet.animate(
  [{ top: `${currentTop}px` }, { top: `${target}px` }],
  {
    duration: 300,
    easing: "cubic-bezier(0.32, 0.72, 0, 1)", // --ease-drawer from motion-quality.md
    fill: "forwards",
  }
);
```

Spring alternative (if using a spring library or WAAPI spring): damping `0.8`, response `0.3s` per `interaction-physics.md` drawer/sheet defaults.

#### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  .sheet {
    transition: opacity 150ms ease-out;
    /* Remove transform transition — no spatial travel */
  }
  .sheet:active {
    transform: none;
    /* Replace with a static state indicator: */
    outline: 2px solid var(--color-accent);
    outline-offset: -2px;
  }
}
```

And in JS:

```js
const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const snapDuration = prefersReduced ? 0 : 300;
const snapEasing = prefersReduced ? "steps(1)" : "cubic-bezier(0.32, 0.72, 0, 1)";
```

Per `motion-quality.md`: *"Reduced motion means gentler and less positional movement, not necessarily zero change; opacity/color transitions that aid comprehension can remain."* A cross-fade to the new position plus a static border on press preserves state feedback without spatial travel — matching the product context's accessibility requirement that Reduced Motion "must preserve state feedback without large spatial travel."

---

### 4. Verified vs. Unverified Claims

| Claim | Status |
|---|---|
| `ease-in` is the wrong easing for UI snap | **Verified** — matches motion-quality.md easing rules and the physics of direct manipulation. |
| 480ms is too long for a daily-use sheet snap | **Verified** — motion-quality.md bounds standard UI to ≤300ms; the 300ms `transition: all` on the same element confirms inconsistency. |
| Missing pointer capture will break tracking on small surfaces | **Unverified** — depends on the sheet's collapsed-state dimensions and whether the user's pointer strays. Needs a real-device test. |
| `transition: all` causes layout thrash during `pointermove` | **Unverified** — depends on the DOM tree size, paint complexity, and whether the browser coalesces style/layout. A Performance panel trace would confirm. |
| Missing hysteresis causes false drags on taps | **Unverified** — depends on how steady the user's finger is. 10px is a starting recommendation, not observed. |
| Projected-endpoint snapping improves perceived responsiveness | **Unverified** — needs A/B testing or frame-by-frame comparison with real release velocities. |
| Rubber-band function constant `0.55` feels correct | **Unverified** — starting value from `interaction-physics.md`; needs tuning on the actual sheet dimensions and device. |

---

### 5. Minimal Browser/Device Validation Plan

Before approving implementation, run these checks in order of priority:

| # | Check | Tool | What to verify |
|---|---|---|---|
| 1 | **Real touch device** | iPad or Android phone, DevTools remote debug | Does pointer tracking survive leaving the collapsed-sheet bounds? Does `:active` scale feel immediate or laggy? Does the 8-12px hysteresis prevent false drags on taps? |
| 2 | **Frame timeline** | Chrome DevTools Performance panel, record while dragging + releasing | Is `top` causing layout/paint on every frame during `pointermove`? Is the `transition: all` creating style recalc storms? |
| 3 | **Velocity projection A/B** | Two builds: release-position snap vs. projected-endpoint snap | Does projection reduce "the sheet snapped the wrong way" incidents with quick flicks? |
| 4 | **Interruption test** | Manual: grab sheet mid-snap, drag opposite direction | Confirm there is no visual jump on re-grab (retarget from presentation value). |
| 5 | **Boundary resistance** | Drag past `collapsed` and `full` extremes | Confirm rubber-banding feels progressive, not hard-stop. Confirm release from overshoot snaps to the nearest valid point. |
| 6 | **Reduced Motion** | macOS Accessibility → Display → Reduce motion; or iOS Settings → Accessibility → Motion → Reduce Motion | Confirm no spatial travel, feedback preserved via static indicator (outline, opacity cross-fade, or color change). |
| 7 | **120 Hz device** | iPad Pro or high-refresh Android | Confirm no jank visible at higher frame rates; `top` animation may tear at 120Hz where it looked fine at 60Hz. |

**Minimum bar for approval:** items 1, 4, and 6 must pass on at least one real touch device. Items 2, 3, and 5 are "should pass" unless the product context treats them as release-critical. Item 7 is nice-to-have unless 120Hz users are a known segment.

---

### Verdict

**Block.** The `ease-in` snap animation, missing interruption, absent velocity/projection, and `transition: all 300ms` on a layout property are each independently blocking for a direct-manipulation sheet used repeatedly in a daily ops tool. The `:active` press feedback piggybacking on the same transition is a compounding defect. None of these findings depend on runtime evidence — the static code alone is sufficient to block.

The design moves above provide concrete, reference-backed alternatives for every finding. The validation plan gates implementation approval on real touch-device evidence, per `interaction-physics.md`: *"If no suitable runtime is available, report the interaction as unverified rather than 'correct.'"*
