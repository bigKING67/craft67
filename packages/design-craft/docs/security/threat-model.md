# Threat model

## Assets

- Integrity of the canonical `skills/design-craft` runtime.
- User-controlled install and backup roots.
- Source/evidence provenance and release-level claims.
- Package, checksum, manifest, SBOM, and native evidence assets.
- Pristine upstream commits and reviewed absorption decisions.

## Untrusted inputs

Repository files, route manifests, JSON/TOML/YAML, Markdown, tar entries,
upstream content, evidence artifacts, CLI arguments, environment variables,
and existing install paths are data, not instructions.

## Primary threats and controls

### Path traversal and symlinks

Manifest paths must be relative POSIX paths without `..`, backslashes, or empty
segments. Source and export traversal checks reject every symlink component and
verify the resolved path remains below its root. Tar/SBOM processing rejects
links, special files, absolute paths, and parent traversal.

### Installer replacement and TOCTOU

The installer acquires a bounded lock, stages on the target filesystem, removes
runtime artifacts, writes provenance, verifies the staged tree, performs an
atomic rename, verifies again, and restores the previous target on failure.
The retired `frontend-craft` name is outside the v0.5 installer boundary: the
installer does not inspect, mutate, or delete existing copies. Operators must
verify ownership and preserve local changes before retiring one separately, as
documented in `docs/operations/v0.5-migration.md`.

Residual risk: local processes with permission to mutate the install root can
race filesystem checks. The post-switch digest check detects mutation before
success, but the installer is not a defense against an already-compromised OS
account.

Residual risk: old automation can continue invoking an unmanaged retired alias
until its callers are migrated and the copy is reviewed separately.

### Evidence inflation and stale provenance

Current cross-agent evidence requires the current score schema, machine JSON
scorecard, run manifest, skill tree, contract digest, and clean source binding.
Historical schemas cannot satisfy current release gates. Native evidence is
bound to the exact skill and fixture trees. Operational and Certified release
levels are explicit; missing evidence never promotes a release automatically.

### Supply chain and release assets

Upstreams are pinned and reviewed separately from the canonical skill. Actions
use full commit SHAs. Release assets use exact per-level allowlists. The package
checksum, release manifest, and SPDX file inventory bind the package bytes;
GitHub attestations and Release writes exist only in the publication workflow;
the certification workflow is read-only and emits a digest-bound, relocatable
artifact. Publication requires an explicit successful certification run ID,
artifact ID, and SHA-256 digest. A read-only job revalidates the complete bundle;
only a dependent job receives write authority, and it executes no repository
validation code before rechecking the same immutable REST ZIP digest. Release
certification uses only the repository-scoped Actions token and receives no
long-lived personal access token. Administration-level ruleset and
Actions-policy reads are isolated in an explicit maintainer audit instead of
the release critical path. Workflow artifacts are downloaded only after exact
Native and, for Certified, physical-device run observations validate workflow
identity, repository, run ID/attempt, ref, source commit, status, conclusion,
and URL.
Release assets are assembled and validated in same-filesystem staging before a
locked transactional replacement; published-set validation runs before the
backup is discarded, and failure restores the previous exact asset set.

### Resource exhaustion

Validation subprocesses have timeouts and bounded output summaries. Benchmark
fixtures use explicit 1k/10k/100k scales. Route pack and package validators use
declared inventories rather than unbounded external traversal.

## Recovery

On failed install, use the retained canonical backup and verify it with
`design_craft_install_verify.py`. On evidence or asset mismatch, discard the
derived artifact and regenerate from a clean, exact commit; never repair hashes
in place. A published Operational release cannot be relabeled Certified by
replacing assets: certification requires a new version and release record.
