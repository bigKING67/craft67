# Reporting and confidence

Lead with the outcome, then the shortest evidence chain that lets another analyst reproduce it.

## Required sections

1. Objective and scope
2. Outcome
3. Decisive evidence (IDs, hashes, offsets/functions/events)
4. Reproduction or verification
5. Findings and connected paths
6. Limitations, contradicted hypotheses, and unverified areas
7. Artifacts and environment

## Evidence language

- `OBSERVED`: directly present in a preserved artifact or live capture.
- `INFERRED`: follows from observed facts through a stated reasoning step.
- `HYPOTHESIZED`: plausible and useful to test, but not yet supported.
- `UNVERIFIED`: claimed by a source/tool or expected by design without current proof.

Do not label a result confirmed because a parser ran or a string exists. A static transform gate does not
prove live request acceptance; a mock exploit does not prove the target build. A valid case seal proves that
the current local files match the seal receipt and graph, not factual correctness, signer identity, or an
external immutable history.

## Reproducibility details

Record target hash/version, tool versions, exact entry command, inputs, expected decisive output, environment
differences, and reset/cleanup steps. Prefer small command snippets and evidence references over raw log dumps.

The deterministic Evidence projection includes source, acquisition method, observation time, optional note,
hash, size, and stored or external location. Free-text metadata is rendered as a single-line Markdown code span
so source content cannot inject headings, lists, HTML, or additional report fields.
