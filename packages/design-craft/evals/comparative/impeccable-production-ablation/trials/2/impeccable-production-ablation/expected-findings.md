# Expected findings

The judge should reward outputs that:

- sequence audit, harden, polish, then measured optimize rather than mixing a
  redesign into production repair;
- identify swallowed save errors and ambiguous pending/close behavior as
  correctness risks, not cosmetic issues;
- cover empty/loading/error/permission/conflict/rate-limit/offline/retry/partial
  batch states and hostile content;
- replace fixed page/drawer/table geometry with bounded adaptive behavior and
  explicit tablet/long-translation checks;
- require focus management, background inertness, labels, focus-visible,
  keyboard behavior, adequate targets, and reduced-motion handling;
- measure 10,000-row rendering, filter latency, image layout shift, and handler
  cost before selecting virtualization, debouncing, memoization, or asset work;
- treat `transition: all`, `ease-in`, removed outlines, fixed widths, and
  missing image dimensions as source signals whose user impact still requires
  contextual validation;
- include observable acceptance and rollback conditions.
