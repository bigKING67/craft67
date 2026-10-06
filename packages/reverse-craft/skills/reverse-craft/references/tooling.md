# Tool discovery and bootstrap

## Principle

Tool availability is evidence, not permission. Prefer installed tools and the smallest pipeline that proves
the current hypothesis. Do not install a suite just because a route mentions it.

## Profiles

- `core`: git, file, strings, jq, openssl
- `binary`: gdb/lldb, binutils, radare2, Ghidra/IDA presence, Python tooling
- `android`: adb, jadx, apktool, apksigner, Frida
- `ios`: codesign, otool, lldb, Frida/Objection (platform-dependent)
- `web`: node, browser67 checkout, Codex MCP inventory
- `forensics`: yara, tshark, Volatility, exiftool
- `firmware`: binwalk, unsquashfs, qemu-system
- `wireless`: aircrack-ng, tshark, rtl tools
- `all`: union of profiles; diagnostics only unless an apply plan is explicitly authorized

`doctor --deep` may invoke version commands with short timeouts. Without `--deep`, it performs only path,
platform, configuration, and filesystem checks.

MCP discovery never returns raw transport configuration. It exposes only a bounded safe projection: transport
type, command/cwd, argument count, environment/header names, and URL origin. Argument values, environment/header
values, URL credentials/query/path, unknown transport fields, and failing `codex mcp list` stderr are omitted.

## Setup transaction

`setup plan` detects one supported package manager and emits only missing packages. The saved plan contains:

- schema, creation/expiry timestamps, platform and machine
- profile, package manager, exact argv arrays, reason, expected binaries
- generated-by version and a canonical SHA-256 receipt

`setup apply` rejects shell strings. Each argv must start with the planned package manager and match a narrow
verb/flag allowlist. It writes a journal and command receipts under Reverse Craft home; stdout/stderr are
bounded and secrets are redacted. A failed command stops the plan. Re-run `doctor` before generating a new
plan; do not edit a failed plan.

The built-in catalog intentionally covers common CLI packages, not heavyweight GUI/licensed tools such as
IDA Pro or Xcode. For those, return official/manual guidance rather than pretending installation succeeded.
