# Performance quality

Use this for UI performance, dashboards, charts, tables, animations, and heavy
frontend interactions.

## Default stance

Do not optimize blindly. Identify the hot path or risk first, then verify with
the smallest useful measurement: browser smoke, Web Vitals/Lighthouse signal,
DevTools/CDP metric, build output, bundle report, profiler, or targeted test.
In a read-only plan, establish the baseline before selecting or claiming
performance fixes. Do not prescribe virtualization, debouncing, memoization,
workers, or asset changes as measured improvements before the baseline exists.
You may still require an explicit bound for work that is demonstrably
unbounded, while leaving the implementation choice contingent on measurement
and project constraints.

Calibrate severity separately from architecture risk. A direct map of 10,000
rows or synchronous filtering is decisive evidence of unbounded work, but not
by itself proof of user-visible latency or a P0 release blocker. Keep it at P1
until target-device measurement establishes severe task failure, unless the
source already proves guaranteed exhaustion, data loss, or inability to
complete the stated job.

Do not assign P0 solely from an unmeasured static hot-path shape. Use P1 risk
unless source proves certain task failure at the stated scale or runtime
measurement proves a release blocker.

When acceptance conditions are requested but the project has no performance
budget, propose provisional numeric thresholds and label them for ratification
instead of saying only "responsive" or "fast". Match them to the actual device,
browser, data scale, and interaction. Useful examples include input/filter p95,
maximum long-task duration, mounted row bound, peak memory, CLS, and a maximum
base-to-head regression with both relative and absolute limits.

## Frontend hot paths

Watch for:

- Large arrays mapped directly inside render without paging, virtualization, or
  memoized preparation.
- Expensive sort/filter/group computations on every render.
- Deep clones and repeated JSON parse/stringify.
- High-frequency input/scroll/resize handlers using React state.
- Layout reads and writes interleaved in loops.
- SVG/canvas/chart resize loops.
- Animating width/height/top/left/filter on many nodes.
- Images without dimensions, modern formats, lazy loading, or correct sizes.

## Dashboards and data viz

- Bound data size before rendering.
- Use server aggregation when possible.
- For tables, require pagination, virtualization, or an explicit row bound.
- For charts, verify container resize, canvas/SVG size, tooltip overflow, and
  mobile behavior.
- Avoid recomputing derived chart series inside render.
- Keep color ramps accessible and semantically consistent.

## Motion performance

- Prefer transform and opacity.
- Avoid animating layout properties on repeated elements.
- Use `will-change` sparingly and remove if it does not help.
- Respect `prefers-reduced-motion`.
- Do not make content invisible until JS animation starts.

## Bundle and dependency cost

- Check current dependencies before adding packages.
- Prefer framework-native image/font features.
- Split rarely used heavy views.
- Avoid importing whole utility/icon/chart libraries for a small subset when
  the project has alternatives.

## Delivery evidence

For performance-sensitive work, report:

- Target hot path.
- Data scale assumption.
- What was changed.
- How it was measured or why it could not be measured.
- Residual risk.
