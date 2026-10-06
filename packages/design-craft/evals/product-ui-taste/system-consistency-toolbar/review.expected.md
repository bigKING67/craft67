# Expected system review

## Baseline

- Review scope is the toolbar plus the shared compact-utility-action family.
- Authority is explicit enough to compare the three utility actions.
- The selection checkbox remains a different semantic family; its different
  indicator is not, by itself, a visual-language finding.
- Evidence is a textual golden fixture. It does not prove a real browser or
  host-agent review.

## Inventories

- Surface inventory: one workbench toolbar, reviewed from the supplied Light
  observations; Dark is unverified.
- Component families: selection control; compact utility action.
- Interaction patterns: selection, immediate utility action, focus feedback.

## State and theme matrix

| Family / variant | Default | Hover | Pressed | Focus-visible | Light | Dark |
| --- | --- | --- | --- | --- | --- | --- |
| Selection control | verified | not_applicable | verified | verified | verified | unverified |
| Utility / Filter | verified | verified | verified | verified | verified | unverified |
| Utility / Add item | F-01 | F-01 | F-01 | F-01 | F-01 | unverified |
| Utility / Refresh | F-02 | F-02 | unverified | verified | F-02 | unverified |

## Reference fidelity

No approved comp, screenshot, or design-file reference is supplied, so the
reference fidelity matrix is `not_applicable`. The explicit component authority
and exemplar observations remain the comparison baseline.

## Finding ledger

| ID | Severity | Scope | Family / state | Finding | Required resolution | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| F-01 | P1 | Toolbar | Utility / default, pressed, focus | The icon-only Add item action uses a contained circle, scale-only feedback, and no visible focus despite the shared ghost utility authority. Passing target-size and default-style assertions do not resolve the family mismatch. | Reuse the shared utility primitive and its focus/state tokens, or explicitly evolve the authority and every equivalent instance. | Same-state rendered comparison in both supported themes. |
| F-02 | P1 | Toolbar | Utility / default, hover | Refresh drifts from the family radius, icon size, and hover timing without an intentional variant. | Restore the shared family geometry and state timing. | Same-state rendered comparison against the Filter exemplar. |

## Post-fix verdict

No fix batch or final rendered evidence is supplied. F-01 and F-02 therefore
remain `unresolved`; this golden fixture must not infer resolution from target
size or default-style assertions.

## Sign-off

`blocked`

Confirmed P1 family inconsistencies block delivery. Missing Dark-theme evidence
is also recorded, but it does not downgrade a known blocker to `incomplete`.
The screenshot/check assertions described in the input are supporting evidence,
not visual acceptance.
