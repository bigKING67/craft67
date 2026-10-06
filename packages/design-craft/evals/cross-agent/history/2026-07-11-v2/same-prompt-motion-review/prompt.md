# Same prompt: motion review

Use design-craft to critique the following gesture-sheet interaction. This is a
read-only benchmark: do not edit files and do not claim browser/device
validation.

Product context:

- Surface: web operations app used repeatedly during the day.
- Primary job: drag a bottom sheet between `collapsed`, `half`, and `full`
  states without losing task context.
- Style authority: calm utility UI; motion exists only to preserve causality
  and direct manipulation, not to entertain.
- Accessibility: Reduced Motion must preserve state feedback without large
  spatial travel.

Static implementation evidence:

```js
let animating = false;

sheet.addEventListener("pointerdown", (event) => {
  if (animating) return;
  startY = event.clientY;
});

sheet.addEventListener("pointermove", (event) => {
  sheet.style.top = `${event.clientY}px`;
});

sheet.addEventListener("pointerup", () => {
  animating = true;
  const target = nearestSnapPoint(sheet.offsetTop);
  sheet.animate(
    [{ top: `${sheet.offsetTop}px` }, { top: `${target}px` }],
    { duration: 480, easing: "ease-in", fill: "forwards" },
  ).finished.then(() => {
    animating = false;
  });
});
```

```css
.sheet {
  transition: all 300ms;
}

.sheet:active {
  transform: scale(0.96);
}
```

Available evidence: prompt and static code only. No pointer trace, computed
style, frame timeline, Reduced Motion run, responsive run, or real-device touch
test was performed.

Return:

1. Evidence level and design read.
2. Whether this motion should exist and which parts should not animate.
3. Prioritized findings with direct-manipulation and interaction-physics
   reasoning.
4. Concrete design moves for pointer-down feedback, 1:1 tracking,
   presentation-value interruption, velocity handoff, projected endpoints,
   soft boundaries, and Reduced Motion.
5. Verified versus unverified claims.
6. Minimal browser/device validation plan before implementation approval.
