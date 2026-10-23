# browser67 architecture

```text
Codex / MCP client
  -> src/mcp/browser/server.mjs
  -> src/tmwd-runtime/index.mjs
  -> src/tmwd-hub.mjs
     -> src/tmwd-hub/{config,sessions,relay,ws-server,link-server,shutdown}.mjs
  -> extension/background.js
     -> extension/browser67/window-focus-runtime.js
        -> dedicated Agent window / bounded focus lease
  -> Chrome/Edge tab

Codex / MCP client
  -> src/mcp/js-reverse/server.mjs
  -> src/tmwd-runtime/index.mjs
  -> src/tmwd-hub.mjs
     -> src/tmwd-hub/{config,sessions,relay,ws-server,link-server,shutdown}.mjs
  -> extension/background.js
  -> Chrome/Edge tab
  -> window.__TMWD_JS_REVERSE__ runtime hooks
```

Fallback paths:

```text
remote_cdp mode -> src/cdp-runtime/index.mjs -> http://127.0.0.1:9222
native fallback -> src/native/input.mjs -> macOS/Windows/Linux OS input backend
```

## Key design decisions

1. Keep browser67's real user-browser path as the default for profile-sensitive
   work; the current transport/protocol is TMWD.
2. Keep remote CDP explicit and visible.
3. Keep extension source vendored and reproducible.
4. Keep runtime artifacts under the active browser67 home, canonically
   `~/.browser67` with legacy `~/.tmwd-browser-mcp` compatibility.
5. Keep deterministic contracts separate from live browser gates.
6. Keep GenericAgent provenance explicit in `UPSTREAM.lock.json`.
7. Keep JS reverse MCP capabilities browser67-backed and hook-first;
   debugger/callframe workflows must stay explicit instead of silently
   pretending support.
8. Keep JS reverse docs and mounted skill content synchronized by script.
9. Keep the hub optionally managed by user-level launchd, not a hidden global service.
10. Keep routine managed work background-first in a dedicated, non-focused
    window within the selected Browser Profile. This isolates tab presentation,
    not profile data: approved cookies and sessions remain those of the same
    Profile.
11. Treat foreground focus as a bounded capability. Ordinary bridge work does
    not acquire it; native/CAPTCHA work may acquire one managed-tab focus lease.
    Restore is conditional on unchanged user focus, a still-live original
    target, an unchanged foreground target, and no service-worker recovery.
12. Bind extension WebSocket callbacks and replies to their accepting connection.
    After asynchronous work, send only while that socket is still current and
    open. Late callbacks cannot clear a replacement connection, and a pending
    tab-list query from an old connection cannot block the replacement's updates.
    A failed ACK send prevents script execution; an interrupted result is not replayed.
13. Controller WebSocket ownership starts while connecting. Endpoint changes and
    disposal cancel the previous attempt and its pending requests; late socket
    events cannot replace the current connection, update its cache or settle its
    requests. A request never follows a different endpoint after awaiting connect.
    Once a WS request has been sent, loss of its result is an uncertain execution
    failure and cannot trigger automatic replay through Link. Failed Link
    execution POSTs also cannot replay through WS: legacy hubs do not attest
    whether dispatch occurred. Context resolution and WS connection failures
    before send may still use the configured transport recovery policy.
14. `browser_execute_js` reports operational failure as a failed tool outcome
    (`ok:false`, MCP `isError:true`), with execution diagnostics in `error.details`.
    Structured bridge errors retain their message and code. User return values
    containing `status`, `ok` or `error` remain ordinary data inside `js_return`.
    Execution session diagnostics and pointers are scoped to the confirmed
    `(browser_instance_id, tab_id)` in both output modes; unresolved execution
    includes no registry sessions. Explicit session-list tools retain their scope.

## Maintenance boundaries

- Setup repairs the generated `mcp/servers.toml` pair when both default entries
  point into the same removed checkout, or still use compatibility entrypoints
  in the current checkout. It preserves unrelated bytes, custom commands/env,
  existing checkout directories and symlinks. Unsupported or conflicting entries
  report `manual_review_required` with a nonzero exit instead of claiming a
  complete setup. Registry writes use a private temporary file and compare the
  observed snapshot immediately before replacement; this detects observed edits,
  not a filesystem transaction against arbitrary external writers.
- The exact WS bridge command `{cmd:"management",method:"reload"}` is instance
  maintenance and needs no page session. The reload helper first resolves a
  connected Browser Instance, then uses that same identity without selecting,
  opening or changing a tab. Other bridge commands retain their session checks.
  Multiple-instance ambiguity and an unavailable requested/default instance fail
  closed. The current Hub must be running for zero-tab reload; an already running
  older Hub does not acquire this route from source edits. A scheduling response
  still requires reconnect and live identity verification before acceptance.
- `extension/` is source-controlled and mirrors GenericAgent's extension except
  install-local `config.js`.
- `src/extension/websocket-overlay.mjs` applies connection ownership in the
  extension build rather than modifying the vendored reference or installed
  files. The generated-code lifecycle regressions run in
  `contracts/extension-build-contract.mjs`; installation and live extension
  identity still require their separate gates.
- `~/.browser67/browser/tmwd_cdp_bridge/` is the canonical Chrome/Edge
  unpacked extension install target. Legacy installs under
  `~/.tmwd-browser-mcp/browser/tmwd_cdp_bridge/` remain supported during
  migration.
- `~/.browser67/runtime/` is runtime state and logs. Run directories live
  under `runtime/runs` and are governed by `npm run runtime:cleanup:dry-run`
  / `npm run runtime:cleanup -- --write` so screenshot evidence stays outside
  the repo without growing indefinitely.
- `runtime/js-reverse/` is ignored local evidence, reports, and rebuild bundles
  produced by `src/mcp/js-reverse/server.mjs`.
- `~/Library/LaunchAgents/com.browser67.tmwd-hub.plist` is optional user-level
  autostart state created by `npm run launchd:install`.
- `src/tmwd-hub.mjs` and `src/tmwd-hub-control.mjs` are thin executable
  entrypoints. Hub state, session TTL, WS relay, link HTTP commands, shutdown,
  endpoint parsing, probing, and state-file IO live in sibling module folders.
