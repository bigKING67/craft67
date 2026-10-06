# Upstream audit workflow

1. Run `reverse_craft.py references audit --remote --json` to compare pinned commits with remote `main`.
2. If a head moved, inspect only commits since the pin and map changed mechanisms to Reverse Craft paths.
3. Reconfirm the license at the changed path; repository-level MIT does not override separately licensed subprojects.
4. Classify each accepted path as `direct_copy`, `adapted`, `reimplemented`, `reference_only`, or `runtime_dependency`.
5. Update the pin and direct-copy SHA only after reviewing the diff and running all related gates.
6. For browser67, never copy runtime/session code. Validate the external runtime separately and keep its commit evidence.

An upstream head change is `review_needed`, not an automatic sync request. A reference can improve while Reverse Craft
correctly retains its current implementation.

## Accepted R44 delta (2026-08-26)

- Reviewed reverse-skill through `914f74ad7d42d18d983d5842f8156440d9068399`; repository and changed R44 paths are MIT.
- Absorbed the R44 threat-intelligence/OSINT triggers from `98fcf243c95b734e2258d79e4be7da5f0660d01c`.
- Added action-first bilingual IOC enrichment grammar and adapted priority so explicit R44 intent wins a tie with R9
  malware terminology; the shipped routing file is therefore classified `adapted`, not `direct_copy`.
- Reimplemented the professional workflow as `modules/threat-intelligence-osint.md`; Xquik bootstrap/runtime code was
  not copied, and browser67 remains authoritative when existing logged-in browser state is required.

## Reviewed R0 decision-framework delta (2026-08-27)

- Reviewed reverse-skill from `914f74ad7d42d18d983d5842f8156440d9068399` through
  `37162cf9547c571c680c07005e9863d4610282dd`; the repository and changed R0/ADF paths remain MIT licensed.
- Adapted commit `c11e80e6a426c946c4ba7054147fa92639ba855c`: R0 remains primary when analysis is stuck; three bounded
  actions or two stage switches without new Evidence trigger hypothesis/evidence-gap/decision-delta capture and
  feasibility-gated replanning in `modules/binary-foundations.md`.
- Classified commit `37162cf9547c571c680c07005e9863d4610282dd` as `reference_only`: it only repairs CHANGELOG Markdown
  formatting and changes no reusable mechanism.
- Did not change the route taxonomy or routing JSON, copy the upstream ADF/stage framework, add dependencies, or import
  separately licensed GPL/AGPL subprojects.

## Reviewed codex-keysmith documentation delta (2026-08-26)

- Reviewed codex-keysmith from `6bae8cac5aa675d25ed11607669e7ef2ef97c6ac` through
  `2cb7f382ea8a08e9af5a6d9c16580b45f639891a`; the repository remains MIT licensed.
- The only changed paths are `README.md` and `README.en.md`, which add the project's official GitHub Discussions link.
- No dry-run, ownership, transaction, receipt, prompt-bank, or scenario-bank mechanism changed, so Reverse Craft
  retains its existing reimplementations and absorbs no code from this delta.
