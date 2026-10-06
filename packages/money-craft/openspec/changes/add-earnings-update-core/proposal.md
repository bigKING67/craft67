# Change: Add earnings update core (UP-02 first loop)

## Why

The existing core audits financial reconciliations and preserves thesis history, but cannot compute a reproducible bridge from new filing actuals to changed model inputs, valuation scenarios and a tracking proposal.

## What Changes

- Add a deterministic Python earnings update module and `earnings review` CLI, reusable independently of the host Skill.
- Bind two adjacent same-fiscal-window periods to source-file hashes, dated publication metadata, units and page/table locators. Require an explicit unchanged/restated/unverified comparison basis.
- Compute actual changes, optional dated expectation differences and three earnings-multiple scenarios. Reconcile the ordered earnings/factor/multiple/shares/FX bridge; preserve the frozen prior model when prior actuals are subsequently restated.
- Bind a proposed thesis update to the audited prior thesis without auto-writing or promoting it. Use existing track init/check/verify for the final reviewed update.
- Add schemas, behavior regressions and a historical issuer-report replay with public numbers and metadata; keep full source documents and runtime tracking artifacts outside the repository.

## Scope and Authorization

The user approved continuation after the proposed earnings-review → model-update → valuation-change → thesis-update loop and the two-filing acceptance criterion. This is its implementation. It does not add an application, live trading, automatic claim classification, DCF/comps engines, subscription data sources or formal investment publication.

The first calculator supports positive attributable earnings and a documented earnings-multiple method. Incompatible calendars, loss-making businesses, mixed units and unverified comparison bases fail visibly instead of receiving an improvised model. Human extraction accuracy and investment claim support remain unverified by software.

## Compatibility and Verification

The new command is additive. Existing thesis/tracking/research commands remain authoritative for their workflows. No historical or installed artifacts are migrated. Validate finite-number/period/source boundaries, restatement and expectation look-ahead controls, bridge conservation, no thesis mutation and reviewed tracking handoff, plus source/package checks. Rollback removes the additive entry point; existing historical archives remain unchanged.
