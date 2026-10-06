# Web 3D runtime QA

## Browser authority

Use browser67 for real-browser work. Select or create a managed dedicated tab
with `active:false`; preserve user tabs and profiles. Do not fall back to the
in-app browser. A bounded foreground interval is allowed only for final visual
acceptance when the user has authorized it.

## Readiness

For a production build in a background-managed tab, establish the target
viewport before waiting for 3D readiness and verify the actual page metrics.
If the runtime chunks have loaded, Console has no blocking error, and the page
still remains at `loading`, run one bounded browser67 viewport capture
transaction, verify the requested inner dimensions and PNG dimensions, then
recheck semantic readiness. This transaction may wake a deferred R3F canvas
measurement; it is a readiness stimulus, not visual acceptance. If
`document.visibilityState` remains `hidden`, label the screenshot
`INVALID SAMPLE` even when the DOM, GLB request, and WebGL context become ready.

In development or test mode, wait for the viewer observability snapshot to
report `status: ready`. In a production build, the browser-exposed snapshot is
intentionally absent; wait for the semantic status UI to report `ready`, then
verify the GLB request, populated asset metrics, and a live WebGL context. Do
not weaken production privacy by exposing the development snapshot.

When the snapshot is available, verify that `document.visibilityState` is
appropriate for the claim, RAF counters advance, the canvas has nonzero
dimensions, the camera and renderer exist, and object/mesh/triangle counts
agree with the loaded asset. Compare the frozen `scene.nodeNames` and
`scene.materialNames` lists with the GLB semantic report; do not infer node
coverage from counts alone. A stale screenshot or DOM/3D disagreement is
`INVALID SAMPLE`.

## Checks

- console has no blocking errors;
- GLB request succeeds without unexpected redirects or decoder errors;
- model is visible and framed;
- orbit, zoom, and reset-camera work;
- resize does not create a canvas loop or overflow;
- remount/unmount increments lifecycle counters and disposes owned resources;
- context loss changes the visible state away from `ready`, pauses camera
  controls, restores the renderer, shows fresh RAF progress afterward, and
  preserves scene identity;
- reduced motion removes nonessential automatic drift;
- desktop 1440x900 and mobile 390x844 layout are usable;
- desktop performance comes from an explicit warmup/sample window and meets
  the approved fixture budget;
- at least three sequential asset reloads in the same renderer stay within the
  approved geometry and texture deltas.

Mobile viewport testing proves layout only. It is not mobile GPU evidence.

## Existing-app pointer interaction repairs

For a bounded repair in an existing Three.js/R3F application, inspect its
actual input, camera, transform, and lifecycle code. The bundled Viewer probe
is not assumed to exist in another application. Preserve the application's
asset authority and established visual intent. Applying these runtime checks
does not establish support for character creation, rigging, or animation
production outside the V0.1 boundary.

- Separate input gain from a final rotation limit. Clamp the composed target
  after additive effects such as convergence, not only the raw pointer input.
  Choose limits from the actual asset and approved expression; do not copy
  another project's angles or treat parameter names as proof of a limit.
- Use elapsed-time damping for follow/return transitions, for example
  `alpha = 1 - exp(-dt / timeConstant)`, rather than a fixed per-frame blend.
  Source inspection can prove this mechanism, but equal perceived response on
  different refresh-rate hardware still requires corresponding observations.
- Define the no-input pose and exit behavior explicitly. Check pointer leave,
  window blur, document hiding, and quick re-entry. If return is delayed,
  cancel the pending return on fresh input and clear timers/listeners on
  unmount. Keep intentional playful behavior within the approved limits.
- Verify initial pose, both input extremes, near-target behavior, settled
  return, interrupted return, and the first relevant camera/scroll transition.
  Record whether input is synthetic or native and reject timing samples
  contaminated by concurrent input. Quaternion angular distance measures total
  rotation; it is not the same as a yaw or pitch component limit.
- Test touch/coarse-pointer initialization separately from responsive layout.
  A viewport changed after mount does not validate a capability decision read
  only at mount. Do not call renderer draw/pass counters display FPS; use a
  dedicated frame-time observation for timing claims.

Keep ad hoc interaction receipts distinct from the canonical asset/browsing
gate receipts. A successful application patch and screenshots do not imply a
passing `3d_craft.py validate` run, Blender export, or source/GLB parity.
Do not fabricate missing asset fields to fit the bundled Viewer contract.

## Explicit performance profile

Do not treat the rolling values in `snapshot.raf` as a performance test. They
are a diagnostic tail and may mix loading, hidden-tab, resize, context-restore,
and steady-state frames. A strict profile uses the development/test-only
observability control path. After the approved viewport is established and the
Viewer is visibly `ready`, prefer the single bounded control call:

```js
await window.__THREE_D_CRAFT_TEST__.runPerformanceAndResourceProfile({
  resource_cycles: 3,
  timeout_ms: 60000,
})
```

The returned object uses schema `3d-craft.web-profile-observation.v1`. A
passing result already contains receipt-shaped metrics, the explicit
performance profile, resource samples, asset identity, and page identity.
Serialize that exact result to an external JSON file; do not recalculate or
transcribe its fields. A failed result contains a reason and is not eligible
for binding. Preserve it as diagnostic evidence and fix the stated cause
before starting a deliberate new observation.

The browser adapter must establish and verify the approved viewport and DPR
before calling the control. The control observes the actual page dimensions;
it does not set browser emulation or select the scene's approved budget.

With browser67, a screenshot viewport override ends when that capture returns.
Do not set it in one call and assume a later profile call inherits it. Use one
bounded, exact-tab debugger batch for `Emulation.setDeviceMetricsOverride`,
`Page.getLayoutMetrics`, a `Runtime.evaluate` page-metrics/readiness check,
the profile invocation with `awaitPromise: true`, and
`Emulation.clearDeviceMetricsOverride`. The adapter must verify batch success,
JavaScript exception details, the returned observation's viewport/DPR, and
viewport cleanup/debugger release before accepting the result. A timeout or
partial batch is diagnostic evidence only. Preserve browser67's cleanup on
failure; never request persistent emulation. Capture subsequent PNG evidence
with its own atomic transaction at the same approved viewport/DPR and verify
its page identity and dimensions before binding.

The control performs this sequence after the adapter's viewport check:

1. record the actual page viewport and device pixel ratio;
2. require `document.visibilityState === "visible"` and viewer `status: ready`;
3. run the explicit warmup/sample profile;
4. capture a settled resource baseline;
5. perform at least three sequential GLB-subtree reloads in the same renderer;
6. return one immutable observation only after all steps complete.

The bundled profile freezes the actual page viewport from
`window.innerWidth/window.innerHeight`, warms up for 3,000 ms, then samples for
at least 10,000 ms. It becomes `invalid` if visibility, viewer readiness,
viewport, or DPR changes during that interval. Preserve the reason and use
`test_status: FAIL` or `UNVERIFIED`; do not silently restart until one run looks
good. Map viewer `renderer_peak.calls` to receipt
`renderer_peak.draw_calls`. The receipt's top-level `metrics` must exactly
match the passing profile so an unrelated rolling counter cannot be presented
as the approved result.

For resource stability, the control keeps the same Canvas and WebGLRenderer
alive:

1. when the initial asset is settled, dispatch
   `3d-craft:test-resource-samples-reset` and wait for the baseline sample;
2. dispatch `3d-craft:test-remount` once and wait for one additional mount,
   at least one additional disposal, `status: ready`, and the next settled
   sample;
3. repeat sequentially until at least three reload cycles and four samples
   exist;
4. report `geometry_delta` and `texture_delta` as the final settled sample
   minus the baseline.

The development viewer remount event reloads only the owned GLB subtree; it
does not replace the Canvas or renderer. React StrictMode may clean up more
than one development effect during a cycle, so disposal is a lower-bound
invariant rather than an exact count. A missing sample, skipped cleanup,
nonsequential mount count, recreated renderer, or unexplained positive delta is
not a passing resource-stability observation.

When an approved scene contract contains `budgets.performance_profile`, both a
passing explicit profile and passing resource-stability observation are
required for `web_runtime` and `browser.performance.profile`. Missing evidence
is `UNVERIFIED`; malformed, failed, mismatched, or over-budget evidence is
`FAIL`. Old V0.1 scenes without this nested budget remain readable, but their
legacy rolling metrics do not establish the strict profile described here.

### Pinned V0.1 timing warning

The pinned stable viewer stack (`@react-three/fiber` 9.7.0,
`@react-three/drei` 10.7.8, and Three.js r185) emits one warning because the
R3F root store still constructs `THREE.Clock`, which Three.js deprecated in
r183 in favor of `THREE.Timer`. Preserve the exact warning as a P2 issue when
the clean observation has zero errors and the runtime otherwise passes. Do not
silence `console.warn`, edit installed dependencies, downgrade Three.js, or
adopt an alpha R3F release merely to make the evidence appear clean. Recheck
the stable dependency line during the next planned viewer-stack update and
remove this exception when R3F migrates its clock implementation. This is not
a blanket warning allowlist: diagnose and record every other warning normally.

If a required browser67 prerequisite repeatedly fails while the page itself is
still healthy, write `status: BLOCKED`, `page_status: ready`, name the failed
capability in `blocker`, and preserve the successful partial observations. Do
not substitute a stale or unreviewed screenshot; validation propagates the
blocked state to browser gates while retaining evidence-backed capabilities.

The bundled development viewer exposes `window.__THREE_D_CRAFT_TEST__` as a
separate control surface; it never mutates the frozen
`window.__THREE_D_CRAFT__` snapshot. Low-level diagnosis may still dispatch
`3d-craft:test-performance-start`, `3d-craft:test-resource-samples-reset`, and
`3d-craft:test-remount`, but the linked observation path should use the bounded
control to avoid manual wait and calculation drift. The Viewer also accepts
`3d-craft:test-context-loss` and
`3d-craft:test-context-restore`; these call Three.js's real
`WEBGL_lose_context` path rather than simulating a CSS-only state. These events
and the browser-exposed observability snapshot are registered only in Vite
development or test mode; the snapshot remains frozen and read-only when
present. Its absence in production is expected.

Context-loss evidence is a forward-compatible V0.2 extension of the v1 browser
receipt. It remains optional for V0.1 receipts. When present, a `PASS` requires
extension support, at least one observed loss and restore, a return to visible
`ready`, and new RAF progress after restoration. A reported `FAIL` blocks the
`web_runtime` gate; do not omit a failed observation to manufacture a pass.
R3F may continue scheduling JavaScript RAF callbacks while the WebGL context is
lost, so `lifecycle.context.status` is the interruption authority; do not claim
the browser RAF itself stopped unless a separate observation proves it.
Use the viewer's `?motion=reduce` query for deterministic screenshots and
verify the visible `Reduced motion` label before accepting the sample.

## Closeout

Capture artifact path, SHA-256, dimensions, target, browser identity, and task
scope. Perform a visual consistency review after capture. Put the observations
and browser67 cache paths in an external draft, then seal them with:

```bash
python3 scripts/3d_craft.py bind-browser-evidence \
  --run-dir /absolute/run \
  --observation /absolute/browser-runtime-draft.json \
  --json
```

The draft uses schema name `3d-craft.browser-runtime-draft.v1`. It contains
observed runtime facts, not a second candidate manifest. Do not include
`runtime`, `asset`, destination paths, screenshot hashes, byte counts, or PNG
dimensions: the command derives those facts. When strict profiling ran, set
`profile_observation_path` to the absolute path of the exact Viewer result and
omit `metrics`, `performance_profile`, and
`lifecycle.resource_stability`. The binder validates the linked observation,
checks its asset SHA-256 and desktop viewport/DPR, merges its fields, and seals
an exact run-owned copy at `evidence/browser-profile-observation.json`.

A minimal ready draft using the linked profile is:

```json
{
  "schema": "3d-craft.browser-runtime-draft.v1",
  "status": "ready",
  "asset_url": "/asset.glb",
  "console_errors": 0,
  "network": {
    "status": "PASS",
    "bytes": 123456,
    "sha256": "replace-with-the-observed-served-glb-sha256"
  },
  "raf": {"delta": 60},
  "profile_observation_path": "/absolute/web-profile-observation.json",
  "lifecycle": {
    "remount_test_status": "PASS",
    "ready_after_clean_reload": true,
    "context_loss": {
      "test_status": "PASS",
      "supported": true,
      "losses": 1,
      "restores": 1,
      "ready_after_restore": true,
      "raf_resumed_after_restore": true
    }
  },
  "cross_runtime": {
    "required_node_coverage_percent": 100,
    "bbox_drift_percent": 0.1
  },
  "desktop_screenshot": {
    "source_path": "/absolute/browser67-desktop.png",
    "css_viewport": [1440, 900],
    "device_pixel_ratio": 1,
    "capture_target": "viewport",
    "visibility_state": "visible",
    "horizontal_overflow": false,
    "visual_review": "PASS"
  },
  "responsive_layout": {
    "status": "PASS",
    "horizontal_overflow": false,
    "viewport": [390, 844],
    "scroll_extent": [390, 1269]
  },
  "mobile_screenshot": {
    "source_path": "/absolute/browser67-mobile.png",
    "css_viewport": [390, 844],
    "device_pixel_ratio": 1,
    "capture_target": "full_page",
    "visibility_state": "visible",
    "horizontal_overflow": false,
    "visual_review": "PASS",
    "note": "Responsive layout evidence only; physical mobile GPU is unverified."
  },
  "warnings": [],
  "unverified": ["Physical-mobile GPU frame timing was not measured."]
}
```

Replace the example bytes and SHA-256 with the values observed from the actual
network response. The command fails closed if those values differ from the
current run's `asset.glb`, if visibility is not `visible`, or if PNG dimensions
contradict the stated CSS viewport and DPR. It also rejects a failed or
malformed linked profile, conflicting inline profile fields, forged sampling
windows, top-level metrics that differ from the explicit profile, and resource
deltas that do not match the sequential samples. It refuses to overwrite any
sealed report, linked observation, or screenshot. On success, accepted
screenshots and the linked profile live in run-owned `evidence/`; browser67
cache paths remain provenance only. Legacy drafts may still provide the three
profile fields inline, but must not combine inline and linked authority.

Final `validate` reopens a linked profile after verifying its file binding,
validates its content and passing status, and compares its asset/page identity,
metrics, performance profile, and resource samples with the sealed browser
report. A report-only edit cannot retain a passing linked-evidence verdict by
leaving the observation file and its hash unchanged. Inline-only V0.1 receipts
remain supported under their existing validation rules.

For `status: BLOCKED`, set `page_status: ready` and a nonempty `blocker`.
Screenshots may be omitted when capture itself is the blocker; do not invent a
file to satisfy the contract. For `network.status: FAIL`, response bytes and
SHA-256 may likewise be omitted because no successful asset response exists.

Finalize the exact managed browser task after capture. Do not close or clean
unrelated tabs or instances.
