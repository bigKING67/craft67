# Evaluation layout

`evals/` separates executable specifications, current machine evidence,
fixtures, and immutable history.

- `specs/`: reusable human-readable evaluation prompts and expected behavior.
- `fixtures/`: deterministic scanner, route, platform, and L4 test inputs.
- `golden-tasks/`: stable replayable task cards.
- `comparative/`: current comparative contracts and derived scorecards;
  archived observed runs live under `comparative/history/`.
- `cross-agent/`: current host status and score contracts; archived observed
  runs live under `cross-agent/history/`.
- `native-runtime/`: native fixtures and evidence contracts, with its own
  history boundary.
- `product-ui-taste/`: calibrated product UI evaluation cases.
- `visual-reference/`: bounded source pilots and deterministic Reference Card,
  catalog, Pack, target-fit, and false-transfer cases; screenshot binaries stay
  repo-external. `target-validation/` may contain controlled same-content
  browser fixtures, but those results remain prototype evidence and cannot be
  presented as production evidence. `comparative-validation/` contains
  pre-registered same-input comparisons on separate repository-local targets;
  these may promote only hypotheses that already satisfy their target-evidence
  prerequisite, and do not establish production value or human preference.
- `history/`: retired repository-level narrative logs that cannot satisfy a
  current gate.

Current machine truth must be JSON validated by the owning schema or contract.
Markdown may define a spec, render a deterministic view from that JSON, or
preserve immutable history; it must not become a second writable status store.
