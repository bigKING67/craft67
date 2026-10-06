# Public history policy

The public repository keeps its existing additive Git history. Historical
commits before the current privacy gate may contain workstation paths and the
names of deliberately published benchmark products such as DataHub or Groland.
Those identifiers are not treated as credentials, but this policy does not
claim that history rewriting could recall content already cloned or cached.

## Baseline

- Privacy-gate baseline commit:
  `d4380a0b8b848c03402f263a09d59bb36cfabdc4`.
- New commits after that baseline must not add absolute macOS, Linux, or Windows
  user-home paths.
- Current-tree evidence must not store raw Simulator UDIDs, physical-device
  identifiers, or Android serials. Runtime identifiers use `sha256:<hex>`.
- Home-relative browser artifact paths are accepted only as non-secret local
  provenance; packaged Skill files must remain machine-neutral.
- Real project names in `evals/` are intentional public calibration fixtures.
  Secrets, authentication material, private payloads, and user data are never
  accepted by this policy.

## Future changes

Use additive redaction and a regression gate by default. Do not rewrite public
history unless a separate audit identifies material sensitive data and the
owner explicitly approves the SHA/tag/clone disruption.

## craft67 snapshot migration

The original baseline above applies to the original standalone repository.
In craft67, the package is imported as a source snapshot with its original
commit recorded in `../../../docs/migration-sources.json`. The privacy gate scans
all commits affecting this package, including the initial import, rather than
requiring an unreachable standalone ancestor. A missing HEAD remains a failure.
