# Mobile and client platforms

Preserve the original package and signing metadata. Inventory platform version, architecture, entitlements/
permissions, components, update path, embedded runtimes, native libraries, local storage, IPC, and network trust.

## R1 - APK reverse

- Hash APK; inspect manifest, signing scheme/cert, SDK levels, components, resources, DEX count, ABI libs, and packers.
- Trace entry component -> Java/Kotlin -> JNI/native -> network/storage. Use JADX for navigation and smali for truth.
- Dynamic work: isolated emulator/device, explicit Frida hooks, logcat, filesystem/network observation, one variable at a time.
- Rebuild in a derived directory; record apktool versions, signing identity, zip alignment, install/launch result.
- Root/pinning/signature checks are branches to understand before bypassing; verify on the exact target build.

## R2 - Mobile reverse (Android+iOS)

- Select platform first. For IPA, inspect Mach-O slices, entitlements, provisioning, URL schemes, extensions, and ObjC/Swift.
- Map jailbreak/root detection, keychain/keystore use, IPC/deep links, WebViews, certificate validation, and backend binding.
- Separate simulator/emulator evidence from real-device evidence; state when platform protections are absent.
- Keep decrypted/extracted app material separate and hash every layer.

## R30 - Browser extension reverse

- Preserve CRX/XPI and unpacked tree; record extension ID/version, manifest version, permissions, CSP, host access.
- Trace content script <-> page bridge <-> service worker/background <-> native messaging/network.
- Inspect update URL and signed-package provenance before executing. Use an isolated browser profile for dynamic work.
- MV3 service workers suspend; use event/network evidence rather than assuming persistent state.

## R31 - macOS/Mach-O

- Record universal slices, Mach-O load commands, code signature/notarization, entitlements, hardened runtime, and dependencies.
- Recover Objective-C classes/selectors and Swift metadata; map XPC services, launch agents/daemons, helpers, and keychain use.
- Dynamic work should preserve quarantine/signature state and use a disposable user/profile when behavior mutates state.
- Distinguish ad-hoc re-sign behavior from the shipped artifact.

## R32 - Thick client

- Fingerprint Electron/.NET/Java/native runtime, packaging/update system, local databases/config/cache, IPC, and custom protocols.
- Trace renderer/UI input across IPC/RPC to privileged native/backend actions. Test trust at the receiving boundary.
- Inspect update signature/transport/rollback, local secret handling, certificate trust, and plugin/module loading.
- Separate client-only impact from server-authorized impact; validate against an in-scope test account/fixture.

