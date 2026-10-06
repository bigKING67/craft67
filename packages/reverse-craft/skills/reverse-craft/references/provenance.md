# Upstream provenance policy

Machine-readable details live in `provenance.json`; repository notices live in `THIRD_PARTY_NOTICES.md`.

Each derived path is classified as:

- `direct_copy`: substantially identical source; retain license/copyright and source hash.
- `adapted`: implementation or text preserves identifiable upstream structure.
- `reimplemented`: behavior/mechanism was independently implemented for Reverse Craft boundaries.
- `reference_only`: reviewed for decisions but not shipped.
- `runtime_dependency`: optional external runtime remains authoritative.

Upstream movement is never auto-merged. Audit current remote heads, compare affected mechanisms and licenses,
then update pins and tests only after review. GPL/AGPL subprojects are reference-only unless this repository's
license/distribution model is deliberately changed.

