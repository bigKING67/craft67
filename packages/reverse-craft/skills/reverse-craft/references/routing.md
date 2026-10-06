# Deterministic routing

The router uses the reviewed 43-route taxonomy in
`upstream/reverse-skill-routing.json` and the Reverse Craft family map in `modules.json`.

## Scoring

For each route rule:

1. `must` must match the normalized hint.
2. Every `mustAll` expression must match.
3. `exclude`, when present, vetoes that rule.
4. Each satisfied rule adds one point to the route.
5. A rule marked `fallbackOnly=true` contributes only when no non-fallback route matched. This keeps
   broad `R0` reverse/逆向 grammar from creating a false tie with a specific specialist route while
   preserving R0's OLLVM, anti-debug, emulator, debugger, and other specialist rules.
6. Highest score wins; ties use the declared `priority` order.
7. No match falls back to `R0`.

The output includes every positive candidate, matched rule notes, primary module reference, and
`ambiguous=true` when another route has the winning score. Treat ambiguity as a reason to inspect the
artifact, not to load all candidates.

## Artifact hints

`--artifact` adds bounded, read-only clues: filename, suffix, size, first 64 bytes, and common magic.
It never executes the artifact. For directories it records only the path/type; inspect structure with
normal shell tooling before deciding.

## Route versus workflow

The route selects the primary specialist lens, not a fixed command sequence. A `.so` in an APK task may
start at `R1` for packaging/signing and hand off one native subproblem to `R6`; it should not duplicate the
whole case. A report request (`R20`) should normally retain the analysis route as secondary.

## Source boundary

The routing JSON is an MIT-licensed adaptation pinned by SHA-256 and upstream commit in `provenance.json`.
Reverse Craft adds action-first bilingual IOC enrichment grammar and prioritizes explicit R44 CTI/OSINT intent before
R9 malware analysis so mixed enrichment requests retain the intelligence workflow; these local choices differ from the
reviewed upstream snapshot. Reverse Craft owns its scoring implementation, module map, tests, and output contract.
