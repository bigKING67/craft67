# {{NUMBER}} - {{TITLE}}

- **Status**: proposed
- **Commit**: `{{COMMIT}}`
- **Severity**: `{{SEVERITY}}`
- **Category**: `{{CATEGORY}}`
- **Evidence level**: `<static | browser-observed | simulator | emulator | device>`
- **Estimated scope**: `<files and rough change size>`

## Problem

Describe the user-visible motion problem, its frequency, and why it matters.
Cite every location as `path/to/file:line` and include the relevant current
excerpt.

## Authority and local conventions

- Product/style authority: `<PRODUCT.md / DESIGN.md / scoped rule>`
- Existing motion tokens: `<token names and file:line>`
- Correct local exemplar: `<file:line and why it is the right precedent>`
- Deliberate exceptions to generic guidance: `<none or explicit exceptions>`

## Target behavior

State the exact observable result. Use project-owned values first. If runtime
tuning is required, provide a bounded initial range and the measurement or
feel-check that selects the final value.

## Steps

1. `<one concrete edit with file and resulting behavior>`
2. `<next concrete edit>`
3. `<validation or migration step>`

## Boundaries

- Do not change `<out-of-scope files or behavior>`.
- Do not add dependencies unless `<explicitly justified condition>`.
- Stop and report if `<source, authority, or API drift condition>` is observed.

## Verification

### Mechanical

```bash
<targeted type, lint, test, or build command>
```

### Runtime and feel check

- Trigger: `<exact interaction and repeated/interrupted variants>`
- Normal motion: `<observable acceptance criteria>`
- Reduced Motion/Remove animations: `<preserved feedback and removed travel>`
- Performance: `<trace, frame, or hot-path condition when relevant>`
- Device/browser scope: `<viewports, browser, simulator/emulator, or hardware>`

## Done when

- `<machine-checkable completion criterion>`
- `<runtime-observed completion criterion>`
- `<explicit remaining unverified item, or none>`
