import assert from "node:assert/strict";
import vm from "node:vm";

// Execute the generated service worker, including its real list/handshake/update
// functions. A regex-only test would miss a stale builder transform.
export async function assertFileSchemeDiscovery(background) {
  let allowed = false;
  let permissionReads = 0;
  let created = 0;
  const messages = [];
  const event = () => ({ addListener() {}, removeListener() {} });
  const tabs = [
    { id: 1, url: "https://fixture.test/", title: "https" },
    { id: 2, url: "http://localhost/", title: "http" },
    { id: 3, url: "file:///tmp/%E6%9C%AC%E5%9C%B0%20page.html", title: "file" },
    { id: 4, url: "chrome://extensions/", title: "internal" },
    { id: 5, url: "about:blank", title: "blank" },
  ];
  const chrome = {
    extension: { async isAllowedFileSchemeAccess() { permissionReads++; return allowed; } },
    tabs: {
      async query() { return tabs; },
      async get(id) { return tabs.find(t => t.id === id); },
      async create(args) { created++; return { id: 6, ...args }; },
      onUpdated: event(), onRemoved: event(), onCreated: event(),
    },
    runtime: { onMessage: event(), onStartup: event(), onInstalled: event() },
    alarms: { create() {}, onAlarm: event() },
    storage: { local: { async get() { return {}; }, async set() {} } },
  };
  class Socket {
    static OPEN = 1;
    readyState = 1;
    send(raw) { messages.push(JSON.parse(raw)); }
  }
  const context = vm.createContext({
    chrome, WebSocket: Socket, importScripts() {},
    console: { log() {}, error() {} }, crypto: { randomUUID: () => "fixture-instance" },
  });
  vm.runInContext(background, context);
  const run = code => vm.runInContext(code, context);
  const ids = result => Array.from(result.data, t => t.id);
  assert.deepEqual(ids(await run("handleTabs({method:'list'})")), [1, 2]);
  await run("ws.onopen()");
  assert.deepEqual(messages.at(-1).tabs.map(t => t.id), [1, 2]);
  assert.equal((await run("handleTabs({method:'get',tabId:3})")).data.scriptable, false);
  const denied = await run("handleTabs({method:'create',url:'file:///tmp/test.html'})");
  assert.equal(denied.ok, false);
  assert.equal(denied.errorCode, "FILE_SCHEME_ACCESS_DENIED");
  assert.equal(created, 0, "permission denial must precede tab creation");
  assert.equal((await run("handleTabs({method:'check_url',url:'file:///tmp/test.html'})")).errorCode, "FILE_SCHEME_ACCESS_DENIED");
  assert.equal((await run("handleTabs({method:'create',url:'https://fixture.test/'})")).ok, true);
  allowed = true;
  assert.deepEqual(ids(await run("handleTabs({method:'list'})")), [1, 2, 3]);
  assert.equal((await run("handleTabs({method:'get',tabId:3})")).data.scriptable, true);
  assert.equal((await run("handleTabs({method:'create',url:'file:///tmp/test.html'})")).ok, true);
  assert.equal((await run("handleTabs({method:'check_url',url:'file:///tmp/test.html'})")).ok, true);
  await run("sendTabsUpdate()");
  assert.deepEqual(messages.at(-1).tabs.map(t => t.id), [1, 2, 3]);
  // Reconnection uses the same permission-aware discovery as incremental updates.
  await run("ws = null; connectWS(); ws.onopen()");
  assert.equal(messages.at(-1).type, "ext_ready");
  assert.deepEqual(messages.at(-1).tabs.map(t => t.id), [1, 2, 3]);
  allowed = false;
  await run("sendTabsUpdate()");
  assert.deepEqual(messages.at(-1).tabs.map(t => t.id), [1, 2]);
  assert.deepEqual(ids(await run("handleTabs({method:'list',includeUnscriptable:true})")), [1, 2, 3, 4, 5]);
  delete chrome.extension.isAllowedFileSchemeAccess;
  assert.deepEqual(ids(await run("handleTabs({method:'list'})")), [1, 2]);
  assert.equal((await run("handleTabs({method:'check_url',url:'file:///tmp/test.html'})")).errorCode, "FILE_SCHEME_ACCESS_DENIED");
  assert.ok(permissionReads > 5, "permission must not be cached across operations");
}
