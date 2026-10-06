# Protocol Lifecycle

This policy prevents compatibility code from becoming an indefinite second write path.
Existing artifacts are never silently rewritten or upgraded in place.

| Protocol | Current role | Last write line | Validation support | Earliest removal |
| --- | --- | --- | --- | --- |
| `review-craft.run.v5` | current review write format | current | current | not scheduled |
| `review-craft.run.v4` | sealed historical input only | v0.6.x | through v0.9.x | v1.0.0 and not before 2027-02-01 |
| `review-craft.run.v3` | sealed historical input only | v0.5.x | through v0.9.x | v1.0.0 and not before 2027-02-01 |
| `review-craft.fix-attempt.v1` | current fix-attempt lineage | current | current | not scheduled |
| `review-craft.fix.v1` | explicit legacy compatibility path | v0.7.x | through v0.9.x | v1.0.0 and not before 2027-02-01 |
| `review-craft.delivery.v2` | current attempt-delivery format | current | current | not scheduled |
| `review-craft.delivery.v1` | explicit legacy compatibility path | v0.7.x | through v0.9.x | v1.0.0 and not before 2027-02-01 |

Beginning with v0.8.0, the runtime must not create new `fix.v1` or `delivery.v1` artifacts.
It may validate already-created artifacts until the end of the v0.9 line. Any removal needs
at least 90 days of release-note notice and contract fixtures proving that current formats
cover the supported workflows.

There is no automatic migration:

- restart an unfinished run.v3 or run.v4 with current preflight;
- prepare a new fix-attempt lineage from the sealed review instead of converting fix.v1;
- regenerate delivery v2 from a verified current attempt instead of converting delivery.v1.

Compatibility validators are read boundaries. New fields, semantics, or evidence claims
must not be backported into frozen protocols.

## Source identity in current writes

Current inventory records carry `sourceIdentity` alongside the content-only `sha256`.
The source and worktree fingerprints include this identity, and fix baseline/current
records preserve it. A metadata-only change is a `MODIFIED` source change even when the
before/after content hashes are equal.

- Regular files bind the POSIX owner-executable bit, regardless of `core.filemode`.
  Windows binds the indexed Git executable flag (untracked files default to false);
  this is not a Windows ACL or effective execution-permission claim. Other permission
  bits, ACLs, mount options, and interpreter availability are outside this identity.
- Submodules remain atomic `other`/binary inventory entries, not recursive source
  coverage. Their identity binds both the indexed gitlink object ID and the actual
  checkout commit. An uninitialized checkout is represented explicitly as null,
  including when its directory is absent. Initialization therefore changes identity.
  Their `sha256` binds nested submodule identity records, not a directory's file bytes.
- A selected dirty, unmerged, or unverifiable submodule blocks source collection.
  Dirty recursive worktrees are not represented by a status string or treated as
  stable source. Hidden-status configuration cannot authorize reuse of verification.
  `assume-unchanged` and `skip-worktree` index flags are rejected, also in initialized
  nested submodules. Inventory scope/exclusion filtering precedes submodule inspection;
  an excluded dependency is outside the source-identity claim. Preflight and delivery
  still inspect whole-repository Git status separately and may reject a broken excluded
  checkout when that whole-repository cleanliness check cannot complete.
- Diff inventory binds the immutable base mode/gitlink for deleted paths. Submodule
  changes cannot be hidden from diff selection by `submodule.*.ignore` configuration.

Sealed run.v3/v4 validation uses the original file-record, Git status, and diff-selection
semantics through a private compatibility read path. That path cannot be selected by
current preflight, fix, delivery, or configuration. Frozen coverage rejects
`sourceIdentity` fields; it does not acquire current metadata guarantees.

Records without `sourceIdentity` keep their original fingerprint algorithm when read
as historical data. They do not acquire new guarantees. Current-protocol live source collection
uses the stronger identity, so an older current-format run/fix may fail live comparison even without a
content edit. Restart preflight and verification; do not strip metadata to force a match
or rewrite stored artifacts. Frozen run.v3/v4 and existing delivery attestations retain
their historical validation semantics; this is not an in-place protocol migration.

Git command semantics: [status](https://git-scm.com/docs/git-status) and
[index entries](https://git-scm.com/docs/git-ls-files).

## Independent assurance receipts

`review-craft.assurance-verification.v2` is required for new assured finalization and
binds the complete canonical findings document. Existing sealed v1-only runs retain
validation-only historical semantics; they are not silently migrated or newly finalized
under v1. Editing a historical receipt invalidates its registered content hash.
