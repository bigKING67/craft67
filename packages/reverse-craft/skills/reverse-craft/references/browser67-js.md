# browser67-backed JavaScript reverse engineering

browser67 is the canonical implementation and session owner for live JavaScript/browser reversing.
Reverse Craft is an orchestrator and cross-domain evidence layer only.

## Readiness

1. Use `doctor --json` and inspect `integrations.browser67` plus `integrations.js_reverse_mcp`.
2. With multiple Browser Instances, select the opaque `browser_instance_id`; never guess from profile names.
3. Use a browser67-managed tab. Existing user tabs are read-only unless explicitly adopted.
4. Keep output bounded (`output_mode=compact`) and pin the target page before every decisive action.

## Narrow proof loop

1. `check_browser_health` and enumerate the correct frame/page.
2. Capture relevant requests and initiators before broad source search.
3. Search scripts from parameter name, endpoint, header, or callsite.
4. Install the smallest non-blocking hook before the operation, trigger once, then read hook data.
5. Trace plaintext -> transform -> key/material source -> serialization -> request placement.
6. Record normalized browser67 evidence and export a rebuild bundle when local reproduction matters.
7. Replay locally or against an in-scope fixture. Change one variable at a time.
8. Call scoped `finalize_task` unless the user asked to keep evidence tabs open.

## Trust boundary

- Do not synthesize cookies/tokens or copy auth state to source artifacts.
- A local reimplementation is verified only when it matches captured input/output and the intended request
  succeeds or a fixture proves the transform.
- Minified source similarity is not proof of the live call chain.
- Cross-origin/denied frames and closed shadow roots are explicit observation limits.
- Store browser67 run/artifact IDs and hashes in Reverse Craft; do not create a second tab/run registry.

## Missing integration

Do static asset work or provide a read-only setup plan. Never auto-edit global Codex MCP configuration from
skill activation. Installation/configuration is a distinct, explicitly authorized action.

