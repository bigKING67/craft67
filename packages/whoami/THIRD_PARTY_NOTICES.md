# Third-party material

`whoami` contains original code, tests, contracts, analysis notes and project-specific metadata licensed under the repository's MIT License. It also cites or reproduces limited material from external sources for calculation regression, textual comparison and auditability. The MIT License does not grant rights in the underlying third-party works.

## Research evidence and transcriptions

The following paths contain page crops, smaller review crops, transcriptions, collation data or source-specific quotations derived from external scans and web sources:

- `docs/research/evidence/`
- `docs/research/bazi-timing-blind-review/images/`
- `docs/research/bazi-timing-*.md`
- `docs/research/bazi-timing-*.json`
- other source-specific notes identified by `docs/research/source-manifest.json`

Their exact source URLs, editions, page locators, retrieval dates, hashes and use boundaries are recorded in [`docs/research/source-manifest.json`](docs/research/source-manifest.json) and the adjacent research files. The crops are evidence excerpts rather than project artwork. No claim is made that every scan, edition, transcription or website is free of rights in every jurisdiction. Rights in underlying source material remain governed by its own status and terms; project-original annotations, coordinates, schemas and comparison logic remain separate.

## Software dependencies and external fixtures

Runtime and development dependencies are listed in `package.json` and locked in `package-lock.json`; each dependency remains under its own license. Tests also use attributed public examples or independently encoded regression values described in `docs/research/source-manifest.json`. The repository does not vendor the referenced upstream implementations.

## Legacy Skill

The archived `bazi-ziwei` installation is not part of this repository and must not be added to it. Its audit boundary and non-reuse decision are recorded in [`docs/research/legacy-bazi.md`](docs/research/legacy-bazi.md).
