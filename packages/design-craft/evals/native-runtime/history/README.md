# Historical native runtime evidence

Historical native snapshots are retained for provenance only. They are excluded
from active v3 certification and must not be upgraded by editing JSON fields or
hashes. Regenerate the runtime flow against the clean current source instead.

`2026-07-11-v2/` contains the former iOS Simulator and Android Emulator v2
records and their available screenshots/interaction marker. They predate the
current required artifact-role, launch-log, accessibility-tree, fixture-hash,
and native-contract bindings, so they cannot satisfy `native-runtime-check`.
