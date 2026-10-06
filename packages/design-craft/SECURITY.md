# Security policy

## Supported versions

Security fixes are provided for the latest tagged release. The `main` branch is
development source and may contain unreleased changes.

| Version | Supported |
|---|---|
| latest release | yes |
| older releases | no |

## Reporting a vulnerability

Use GitHub Private Vulnerability Reporting for this repository. Do not include
tokens, cookies, credentials, private project source, or user-home archives in
an issue. Include the affected version or commit, operating system, minimal
reproduction, impact, and whether the issue crosses the documented trust
boundary.

## Trust boundaries

The published package contains only `skills/design-craft`, licenses, root
metadata, and public documentation. Repository tooling, eval history, upstream
checkouts, and local Codex route configuration are not package payload.

The installer writes only under `DESIGN_CRAFT_SKILL_ROOT` and
`DESIGN_CRAFT_BACKUP_ROOT`, uses a lock plus same-filesystem staging, verifies
the staged and installed trees, and rolls back failed switches. The retired
`frontend-craft` name is outside the v0.5 installer boundary: the installer
does not inspect, mutate, or delete existing copies. It does not read credential
stores or browser state.

Route manifests, evidence JSON, scorecards, upstream metadata, package
contents, and repository files are untrusted inputs. Validators must reject
path escape, symlink traversal, malformed types, stale source bindings, and
unsupported schemas rather than silently normalizing them.

Release certification and publication are separate. Certification uses a
repository-scoped, read-only Actions token and receives no long-lived personal
access token, Release-write permission, or attestation permission. Publication
accepts only an exact completed certification run, artifact ID, and SHA-256
digest. Its read-only job revalidates the self-contained bundle before a
dependent write-authority job rechecks the same immutable ZIP digest and
publishes without executing repository validation code. Live GitHub ruleset
and Actions-policy inspection remains an explicit maintainer audit rather than
part of the release credential boundary.

See `docs/security/threat-model.md` for the full model and recovery paths.
