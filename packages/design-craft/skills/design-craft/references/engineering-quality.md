# Engineering quality

Use this when changing frontend code, components, state, data flow,
interactions, or a reusable component library.

## Code elegance

- Express business intent in names and boundaries.
- Keep components small enough to understand, not artificially tiny.
- Separate domain decisions from visual primitives.
- Prefer explicit props over hidden global behavior.
- Avoid "temporary" boolean props that encode multiple concepts.
- Add comments only for non-obvious constraints, not for line-by-line narration.

## Component boundaries

Split when:

- A child has a distinct responsibility or lifecycle.
- A piece is reused with the same intent in at least two places.
- A heavy interactive leaf should be isolated from server/static layout.
- Testing or state ownership becomes clearer.

Do not split merely to reduce file length if cohesion is still high.

## State and data

- Keep state near the owner.
- Use URL/query state when it is navigation state.
- Use server/cache state for fetched data; avoid duplicating it into local
  state without a reason.
- Do not use React state for high-frequency scroll/pointer values.
- Validate external API data at the boundary when shape is uncertain.

## Lifecycle ownership

- Every route into the same state must run the same required finalization side
  effects. Prefer one transition or finalization boundary over duplicating
  cleanup, progress, interaction, and notification work across observers,
  recovery paths, callbacks, or normal user actions.
- Async resource setup that crosses an `await` must be invalidatable by
  teardown. Use an `AbortSignal`, a generation token, or epoch; re-check it
  after every meaningful `await` and immediately before publishing DOM,
  canvas, WebGL, object-URL, or other externally visible resources. Remove
  orphaned nodes and release handles when construction loses ownership.
- When one logical component may have multiple live instances, resolve its
  owner by stable identity and semantic validity instead of the first DOM
  match. Capture the instance set before a batch mutation, then restore or
  release the same captured instance set.

## Errors and observability

- Loading, empty, error, permission, and partial-data states are UI states, not
  afterthoughts.
- Do not swallow errors to make UI appear successful.
- If fallback behavior exists, make it visible and traceable.
- Surface enough context in logs or telemetry for diagnosis without leaking
  secrets.

## Dependencies

- Check `package.json` before importing.
- Prefer existing project libraries and primitives.
- Do not add a large dependency for a simple local behavior.
- One icon family per surface unless the project already mixes families.
- For design systems, use official packages when the brief clearly maps to one
  and the project can accept the dependency.

## Reusable component craft

- Make the common path low-friction, but keep state ownership and failure
  behavior explicit. A tiny API that hides global side effects is not a better
  API.
- Invest in excellent defaults before adding option count. Most consumers keep
  the default timing, spacing, copy, focus, and accessibility behavior.
- Name components and actions for their user-visible role. Memorability is
  useful only when discoverability, semantics, and package conventions remain
  clear.
- Handle invisible lifecycle edges: interruption, focus restoration, pointer
  capture, Reduced Motion, hidden-document timers, unmount during async work,
  and rapid repeated invocation.
- For transient UI, pause remaining-time timers on `visibilitychange` so a toast
  or undo action does not expire while the page is hidden. See
  `motion-patterns.md` for the interaction recipe and verification checks.
- Preserve reachable hover/pointer regions while stacked items move; do not
  create animated gaps that unexpectedly dismiss or de-hover the component.
- If the component is distributed to others, provide interactive examples with
  copyable usage, states, and accessibility behavior. Documentation is part of
  the component's adoption and quality surface.
- Prefer one cohesive component behavior over a large matrix of individually
  configurable timing values that can no longer be tested together.

## Review checklist

- Does this make the main task easier to understand?
- Did we change only the necessary surface?
- Are naming and module boundaries stable beyond this patch?
- Is there an observable failure path?
- Is there a simpler native/browser/framework feature?
