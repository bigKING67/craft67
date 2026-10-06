# Binary and reverse-engineering foundations

Start every binary route with file hash, container/format, architecture, endianness, loader/runtime,
mitigations, sections, imports/exports, strings, entrypoints, and observable anti-analysis. Preserve the
original and record every unpacked/decrypted layer as new evidence.

## R0 - General reverse engineering

- **Use for:** unfamiliar compiled/packed/obfuscated targets, WASM/bytecode, anti-debug, Unity/IL2CPP.
- **First proof:** map input -> parser/dispatcher -> decisive branch/output; identify the runtime before tools.
- **Useful techniques:** strings/xrefs, call graph slices, controlled-input diffing, debugger trace, lightweight
  emulation, symbolic execution only after constraints are bounded.
- **Evidence:** exact hash/build, offsets or symbols, branch condition, input/output pair, clean replay.
- **When progress stalls:** keep R0 primary rather than inventing another route. After three bounded actions or two
  stage switches produce no new Evidence, record the current hypothesis, attempts, evidence gap, and decision delta;
  then replan through a feasibility gate and change the entry point, tool, or static/dynamic stage.
- **Avoid:** decompiling everything, trusting pseudocode types, or patching before the controlling invariant is known.

## R4 - DSL/custom VM

- Identify bytecode boundaries, opcode fetch/decode, VM state, operand encoding, control-flow opcodes, and host calls.
- Build an opcode table from dispatcher cases plus dynamic traces; mark inferred semantics separately.
- Write a bounded disassembler/interpreter and validate each opcode with a minimal bytecode sample.
- For flattened/virtualized code, recover state transitions before attempting high-level decompilation.

## R5 - .NET

- Confirm CLR metadata versus NativeAOT; inventory assemblies, resources, entrypoint, strong name, and target runtime.
- Recover metadata/tokens and deobfuscate in copies. Correlate IL with runtime reflection, dynamic loads, and P/Invoke.
- For loaders/malware, trace configuration decode -> assembly load -> invoked method; preserve decoded assemblies.
- Evidence includes module MVID/hash, metadata token/method, IL/native offset, and runtime observation.

## R6 - IDA/native static analysis

- Configure processor, ABI, loader, bases, and function boundaries before trusting decompilation.
- Rename from evidence, apply types from callers/callees, use xrefs and structure offsets, and annotate uncertainty.
- Validate pseudocode claims with disassembly and, for decisive branches, debugger/register/memory state.
- Export a compact map of functions, offsets, signatures, and referenced evidence rather than a database dump.

## R7 - radare2

- Run bounded analysis first (`aa`/targeted functions), confirm maps and base address, then use xrefs/graphs/types.
- Use `rabin2`, `rahash2`, `rasm2`, or `radiff2` when each is the narrowest evidence tool.
- Save commands or r2 scripts needed to reproduce names/comments; do not depend on transient interactive state.

## R15 - Binary diff and symbol migration

- Pin both binaries and normalize architecture, compiler/runtime, load base, and analysis settings.
- Match by exact symbols/hashes first, then call graph/data references/control-flow features; score confidence.
- Separate unchanged, moved, modified, added, and removed functions. Manually verify high-impact matches.
- A migrated symbol is an inference until cross-references and behavior align in the target build.

## R16 - Patch diff / N-day

- Acquire exact pre/post artifacts and patch metadata. Confirm the changed code is shipped and reachable.
- Reduce diff noise from toolchain/layout changes; trace changed validation, bounds, lifetime, or privilege logic.
- Form a vulnerability hypothesis, then verify safely with a local harness or non-destructive fixture.
- Report affected version evidence and uncertainty; a changed function alone is not exploitability proof.

## R17 - Pwn chain

- Record binary, loader/libc, remote protocol, mitigations, architecture, and clean-start behavior.
- Prove primitives in order: controllable bytes -> corruption -> instruction/data control -> leak -> stable target.
- Keep crash offsets, bad bytes, stack/heap state, allocation history, and framing exact.
- Build staged exploit scripts with timeouts and explicit local/remote profiles; replay from a reset baseline.

## R18 - EDR/AV reverse engineering

- Map user/kernel components, signed modules, callbacks/hooks, telemetry pipeline, policy/config, and trust boundaries.
- Prefer isolated observation and defensive compatibility research; record OS/build and product version exactly.
- Distinguish observed detection surface from a proposed evasion mechanism and from a validated sandbox result.
- Avoid persistent endpoint changes; use snapshots and restore state between experiments.

## R22 - Ghidra

- Import with the correct language/compiler spec and base, run bounded analyzers, then verify function starts/xrefs.
- Use headless scripts for reproducible batch analysis; record Ghidra version, loader options, and script hash.
- Treat decompiler output as a model; inspect instructions and calling convention at decisive sites.

## R33 - Go/Rust binaries

- Identify build info/runtime signatures, Go `pclntab`/module data or Rust panic/vtable/type artifacts.
- Recover function names/types when possible, then separate runtime/library noise from application logic.
- Pay attention to goroutine/channel or async/state-machine lowering and interface/trait dispatch.
- Validate recovered high-level flow against concrete callsites, strings, and runtime inputs.

