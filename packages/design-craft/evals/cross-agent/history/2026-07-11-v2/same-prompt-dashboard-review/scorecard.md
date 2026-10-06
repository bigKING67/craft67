# Scorecard

This file defines the grading rubric for future Codex, Cursor, Claude, Pi, or
generic-agent runs. It is not itself an agent output.

| Criterion | Weight | Pass evidence | Deduction trigger |
|---|---:|---|---|
| Style authority and product context | 15 | Reads or asks for project style authority before judging dashboard polish. | Applies a stock dashboard style without checking product context. |
| Reference selection | 15 | Routes to product UI taste, design moves, surface playbooks, and validation references only as needed. | Loads unrelated references or ignores dashboard-specific guidance. |
| Anti-generic redesign | 15 | Avoids generic card reshuffling and diagnoses decision hierarchy. | Recommends decorative gradients, equal cards, or template chrome as the main fix. |
| Evidence level labeling | 15 | Labels whether the review is screenshot-only, browser-backed, responsive, or full before/after. | Gives a precise score while hiding missing browser/responsive/state evidence. |
| Verified/unverified boundary | 15 | Separates observed hierarchy issues from unverified interactions, focus, and responsive states. | Claims interaction or mobile quality without evidence. |
| Concrete design moves | 15 | Proposes lead metric, supporting strip, primary work area, and exception/action queue moves. | Gives vague advice such as "make it cleaner" without implementable structure. |
| Scope control and unrelated changes | 10 | Keeps recommendations scoped to dashboard UI quality and validation. | Suggests backend, data-model, or unrelated file changes without evidence. |
