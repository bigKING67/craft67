# Product context: Cairn

## Register

- Platform: web
- Surface mode: `Persuade`
- Surface: evidence-dense product evaluation page
- Evidence status: repository-local controlled fixture, not production evidence

## User

Product, security, and procurement leaders deciding whether a vendor has enough
current, attributable release evidence to justify a pilot.

## Primary job

Understand the product promise, inspect the scope, control, impact, and
exception evidence behind it, and decide whether to open the sample dossier or
request a pilot.

## Product promise

Cairn turns scattered release claims, controls, change impact, and open
exceptions into one decision-ready evidence dossier.

## Fixed content inventory

- Product name: Cairn
- Context label: Decision evidence / release 24.8
- Primary headline: One dossier. Every claim, control, and open exception.
- Supporting sentence: Cairn connects what changed, what was verified, who owns
  the remaining calls, and when every source was last observed.
- Primary action: Open sample dossier
- Secondary action: Review the method
- Commercial action: Request a pilot
- Decision posture: Ready with 3 open calls
- Evidence summary:
  - 14 / 14 services in scope
  - 37 / 40 controls verified
  - 3 open exceptions
  - 18 minute evidence freshness
- Evidence ledger:
  - Coverage map / Ready / 14 of 14 services
  - Change impact / Verified / 3 changes, 2 customer workflows
  - Exception ownership / Decide / 3 open, 2 owners confirmed
- Method: Map the claim, bind the evidence, name the decision
- Questions: source freshness, missing evidence, and pilot behavior
- Final action: Request a bounded pilot

Both experiment variants must use this exact inventory. A variant may change
composition, typographic emphasis, and responsive priority, but not the claims,
data, semantic sections, controls, state behavior, or product scope.

## State inventory

The same route supports these query states for both variants:

- `default`: complete demonstration evidence.
- `loading`: evidence refresh in progress with `aria-busy=true`.
- `empty`: no evidence package attached and no invented metrics.
- `error`: source refresh failed with a keyboard-reachable retry action.
- `success`: decision packet approved with the same underlying evidence.
- `long`: deliberately long source and exception labels to test wrapping.

State-specific copy is demonstration content. It must never imply a real
customer, production integration, certification, or measured business result.

## Accessibility and trust

- Use semantic landmarks and exactly one visible `h1`.
- All controls must be keyboard reachable with visible focus.
- The sample dossier must use a native dialog, focus its close control, and
  restore focus to the invoking control when dismissed.
- The error retry action must announce the resulting state change.
- Reduced-motion users receive no entrance animation or smooth scrolling.
- Status cannot rely on color alone.
- Sample metrics and states are visibly labeled as controlled demonstration
  data.

## Out of scope

- Authentication, uploads, integrations, persistence, analytics, or backend.
- Real customers, compliance, security, reliability, conversion, or ROI claims.
- Third-party copy, screenshots, brand identity, imagery, financial data,
  medical data, or distinctive source geometry.
