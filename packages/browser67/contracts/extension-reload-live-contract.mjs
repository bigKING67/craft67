#!/usr/bin/env node

import assert from "node:assert/strict";
import { createServer } from "node:http";
import { WebSocketServer } from "ws";

import { reloadBrowser67Extension } from "../scripts/reload-extension-live.mjs";
import { readHubConfig } from "../src/tmwd-hub/config.mjs";
import { createHubState } from "../src/tmwd-hub/state.mjs";
import { createWsHubServer } from "../src/tmwd-hub/ws-server.mjs";
import { openWs } from "./browser67-hub-relay-contract/ws-client.mjs";

async function until(predicate) {
  const deadline = Date.now() + 2_000;
  while (!predicate()) {
    assert.ok(Date.now() < deadline, "fixture state must settle within its deadline");
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 10));
  }
}

async function runHubZeroTabCases() {
  const hub = createHubState();
  const { wsHttpServer, wsServer } = createWsHubServer(hub, readHubConfig({}));
  wsHttpServer.listen(0, "127.0.0.1");
  await new Promise((resolvePromise) => wsHttpServer.once("listening", resolvePromise));
  const endpoint = `ws://127.0.0.1:${wsHttpServer.address().port}`;
  const extensions = [];
  const counts = new Map([["instance-a", 0], ["instance-b", 0]]);
  let rejectNext = true;
  let withholdNext = false;
  try {
    for (const id of counts.keys()) {
      const extension = await openWs(endpoint);
      extensions.push(extension);
      extension.send(JSON.stringify({
        type: "ext_ready", browser_instance_id: id, tabs: [],
        extension_identity: {
          schema: "browser67.extension-identity.v1", product: "browser67",
          extension_version: "0.11.4", manifest_version: "0.11.4",
          build_revision: "fixture", build_revision_source: "fixture", build_inputs_dirty: false,
          source_digest: "a".repeat(64), protocol_revision: 2,
        },
      }));
      extension.on("message", (raw) => {
        const request = JSON.parse(String(raw));
        assert.deepEqual(request.code, { cmd: "management", method: "reload" });
        assert.equal(request.browser_instance_id, id);
        assert.equal(Object.hasOwn(request, "tabId"), false);
        assert.equal(request.monitorNewTabs, false);
        counts.set(id, counts.get(id) + 1);
        if (withholdNext) { withholdNext = false; return; }
        extension.send(JSON.stringify({ type: "ack", id: request.id, browser_instance_id: id }));
        extension.send(JSON.stringify({
          type: rejectNext ? "error" : "result", id: request.id, browser_instance_id: id,
          ...(rejectNext ? { error: "fixture reload rejected" } : { result: { ok: true } }),
        }));
        rejectNext = false;
      });
    }
    await until(() => hub.browserInstances.size === 2);
    assert.equal(hub.sessions.size, 0);
    await assert.rejects(reloadBrowser67Extension({ endpoint, timeoutMs: 1_000 }), /multiple browser instances/);
    assert.deepEqual([...counts.values()], [0, 0]);
    await assert.rejects(reloadBrowser67Extension({ endpoint, browserInstanceId: "instance-a", timeoutMs: 1_000 }), /fixture reload rejected/);
    const recovered = await reloadBrowser67Extension({ endpoint, browserInstanceId: "instance-a", timeoutMs: 1_000 });
    assert.equal(recovered.browser_instance_id, "instance-a");
    assert.deepEqual([...counts.values()], [2, 0]);
    await assert.rejects(reloadBrowser67Extension({ endpoint, browserInstanceId: "missing-instance", timeoutMs: 1_000 }), /unavailable/);

    // The exception is exactly management.reload. Other commands still need a page.
    const controller = await openWs(endpoint);
    try {
      hub.defaultBrowserInstanceId = "instance-a";
      for (const target of [
        { browser_instance_id: "invalid/instance" },
        { browser_instance_id: "" },
        { browser_instance_id: null },
        { browserInstanceId: "invalid/alias" },
        { browser_instance_id: "instance-a", browserInstanceId: "instance-b" },
      ]) {
        const response = new Promise((resolvePromise) => controller.once("message", (raw) => resolvePromise(JSON.parse(String(raw)))));
        controller.send(JSON.stringify({ id: "invalid-instance", ...target, code: { cmd: "management", method: "reload" } }));
        assert.equal((await response).errorCode, "BROWSER_INSTANCE_INVALID");
      }
      hub.defaultBrowserInstanceId = "";
      for (const code of [
        { cmd: "management", method: "disable" },
        { cmd: "management", method: "reload", tabId: 42 },
        { cmd: "cdp", method: "Runtime.evaluate", params: { expression: "1" } },
      ]) {
        const response = new Promise((resolvePromise) => controller.once("message", (raw) => resolvePromise(JSON.parse(String(raw)))));
        controller.send(JSON.stringify({ id: "page-required", browser_instance_id: "instance-a", code }));
        assert.equal((await response).type, "error");
      }
    } finally { controller.close(); }
    assert.deepEqual([...counts.values()], [2, 0]);

    withholdNext = true;
    await assert.rejects(reloadBrowser67Extension({ endpoint, browserInstanceId: "instance-a", timeoutMs: 500 }), /timed out/);
    await until(() => hub.pendingExec.size === 0);
    assert.equal((await reloadBrowser67Extension({ endpoint, browserInstanceId: "instance-a", timeoutMs: 1_000 })).ok, true);
    hub.defaultBrowserInstanceId = "instance-b";
    assert.equal((await reloadBrowser67Extension({ endpoint, timeoutMs: 1_000 })).browser_instance_id, "instance-b");
    extensions[1].close();
    await until(() => hub.browserInstances.get("instance-b").socket === null);
    const before = counts.get("instance-a");
    await assert.rejects(reloadBrowser67Extension({ endpoint, timeoutMs: 1_000 }), /unavailable/);
    assert.equal(counts.get("instance-a"), before, "an unavailable default never reloads a surviving instance");
  } finally {
    for (const socket of wsServer.clients) socket.terminate();
    await new Promise((resolvePromise) => wsServer.close(resolvePromise));
    await new Promise((resolvePromise) => wsHttpServer.close(resolvePromise));
  }
}

async function runConnectTimeoutCase() {
  const server = createServer();
  const connections = new Set();
  server.on("connection", (socket) => {
    connections.add(socket);
    socket.on("close", () => connections.delete(socket));
  });
  server.on("upgrade", (_request, socket) => {
    // Read the peer's FIN while deliberately withholding the upgrade response.
    socket.on("end", () => socket.destroy());
    socket.resume();
  });
  server.listen(0, "127.0.0.1");
  await new Promise((resolvePromise) => server.once("listening", resolvePromise));
  try {
    await assert.rejects(reloadBrowser67Extension({ endpoint: `ws://127.0.0.1:${server.address().port}`, timeoutMs: 500 }), /timed out/);
    await until(() => connections.size === 0);
  } finally {
    for (const socket of connections) socket.destroy();
    await new Promise((resolvePromise) => server.close(resolvePromise));
  }
}

async function listen(server) {
  if (server.address()) return;
  await new Promise((resolvePromise, rejectPromise) => {
    server.once("listening", resolvePromise);
    server.once("error", rejectPromise);
  });
}

async function close(server) {
  for (const client of server.clients) client.close();
  await new Promise((resolvePromise) => server.close(resolvePromise));
}

async function run() {
  const server = new WebSocketServer({ host: "127.0.0.1", port: 0 });
  let reloadRequestCount = 0;
  let noTabs = false;
  server.on("connection", (socket) => {
    socket.on("message", (raw) => {
      const request = JSON.parse(String(raw));
      if (request.code?.cmd === "tabs") {
        assert.deepEqual(request.code, { cmd: "tabs", method: "list" });
        socket.send(JSON.stringify({
          id: request.id,
          success: true,
          browser_instance_id: "browser-instance-a",
          result: noTabs ? [] : [{
            id: "42",
            tab_id: "42",
            browser_instance_id: "browser-instance-a",
          }],
        }));
        return;
      }
      reloadRequestCount += 1;
      assert.equal(request.browser_instance_id, "browser-instance-a");
      assert.equal(request.tabId, undefined, "extension maintenance must not require a page target");
      assert.deepEqual(request.code, { cmd: "management", method: "reload" });
      socket.send(JSON.stringify({ type: "ack", id: request.id }));
      if (reloadRequestCount !== 2) {
        socket.send(JSON.stringify({
          type: "result",
          id: request.id,
          browser_instance_id: "browser-instance-a",
          result: { ok: true },
        }));
      } else {
        socket.send(JSON.stringify({
          type: "error",
          id: request.id,
          error: "reload rejected",
        }));
      }
    });
  });
  await listen(server);
  const address = server.address();
  assert.equal(typeof address, "object");
  const endpoint = `ws://127.0.0.1:${String(address.port)}`;

  try {
    const reloaded = await reloadBrowser67Extension({ endpoint, timeoutMs: 2_000 });
    assert.equal(reloaded.ok, true);
    assert.equal(reloaded.status, "reload_scheduled");
    assert.equal(reloaded.endpoint, endpoint);
    await assert.rejects(
      reloadBrowser67Extension({ endpoint, timeoutMs: 2_000 }),
      /reload rejected/,
    );
    noTabs = true;
    const empty = await reloadBrowser67Extension({ endpoint, timeoutMs: 2_000, browserInstanceId: "browser-instance-a" });
    assert.equal(empty.status, "reload_scheduled");
    assert.equal(empty.browser_instance_id, "browser-instance-a");
    await runHubZeroTabCases();
    await runConnectTimeoutCase();
    process.stdout.write(`${JSON.stringify({
      ok: true,
      check: "extension-reload-live-contract",
      reload_request_shape: true,
      live_target_discovery: true,
      ack_ignored: true,
      extension_error_propagated: true,
      real_hub_zero_tabs: true,
      multi_instance_reload_scoped: true,
      page_commands_still_require_target: true,
      timeout_cleanup_and_recovery: true,
      invalid_explicit_instance_rejected: true,
      connecting_timeout_cleanup: true,
    })}\n`);
  } finally {
    await close(server);
  }
}

try {
  await run();
} catch (error) {
  process.stderr.write(`extension-reload-live-contract failed: ${String(error?.message ?? error)}\n`);
  process.exitCode = 1;
}
