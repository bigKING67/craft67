# Native runtime evidence

Static source scans and platform fixtures do not count as native runtime
evidence. The maturity gate accepts only schema-valid observed artifacts from
an iOS Simulator/device and an Android Emulator/device.

Probe the current host:

```bash
python3 scripts/design_craft_native_runtime_validate.py --probe --json
```

Validate recorded evidence:

```bash
python3 scripts/design_craft_native_runtime_validate.py \
  --validate \
  --require ios \
  --require android \
  --require-real-device \
  --require-current-source \
  --json
```

Required files for full maturity are `ios-observed.json` from an iOS Simulator,
`android-observed.json` from an Android Emulator, and
`real-device-observed.json` from at least one iOS or Android physical device.
Each must record the exact runtime identity, commands, at least three passing
runtime assertions, source commit/dirty state, skill version/tree hash, current
platform fixture-tree hash, local or CI capture context, and
at least one non-empty artifact stored beside the evidence JSON, with matching
relative path, byte count, and SHA-256. Missing, absolute, or directory-escaping
artifact paths are rejected. Do not create these files from static fixtures or
source inspection. Certified evidence must record a clean source commit that is
an ancestor of the current checkout while the current skill and fixture trees
still match the recorded hashes. This allows evidence files to be admitted in a
later commit without allowing old behavior or fixtures to unlock 100/100.

The active directory intentionally contains no pre-contract observed JSON.
Earlier v2 Simulator/Emulator files are preserved under `history/2026-07-11-v2/`
for provenance and are excluded from current validation. Never copy them back
or backfill v3 fields; regenerate all required artifacts from the real runtime.

Runtime identity is recorded only as `sha256:<digest>`; never commit raw device
serials or UDIDs. Assertions and artifacts are runtime-kind-specific rather
than arbitrary. Android evidence must hash the before/after accessibility XML,
the post-interaction screenshot, and the launch log. iOS evidence must hash the
before/after screenshots, interaction marker, and launch log.

For an authorized physical Android device:

```bash
bash scripts/native_runtime_device_android.sh \
  --serial <adb-serial> \
  --evidence-dir /tmp/design-craft-android-device
```

The runner rejects emulators, performs the build/install/launch/tap flow, writes
`real-device-observed.json`, and immediately validates the device-only evidence.

## Release bundle

After a clean source passes certification, create the annotated release tag and
wait for the tag-triggered `Native runtime evidence` workflow to complete. Then
build the native Release asset triplet from that exact latest successful run:

```bash
NATIVE_RUN_ID=<tag-run-id> make native-release-bundle-build
make native-release-bundle-verify
```

The bundle contains only `ios-observed.json`, `android-observed.json`,
`real-device-observed.json`, and the artifacts each JSON declares. The manifest
binds the current commit, tag, workflow path, run id/attempt/url, and evidence
hashes. Validation rejects stale source or fixture hashes, an older/manual run,
missing physical-device proof, undeclared or duplicate archive members,
symlink/hardlink/device members, path traversal, and non-normalized tar
metadata. The self-check builds twice and requires byte-identical outputs.
