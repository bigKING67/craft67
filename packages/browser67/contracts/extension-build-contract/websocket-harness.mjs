import assert from "node:assert/strict";
import vm from "node:vm";

function deferred() {
  let resolve;
  const promise = new Promise((settle) => { resolve = settle; });
  return { promise, resolve };
}

async function bounded(promise) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error("WebSocket contract stalled")), 1000);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

function event() {
  const listeners = new Set();
  return {
    listeners,
    addListener: (listener) => listeners.add(listener),
    removeListener: (listener) => listeners.delete(listener),
  };
}

function websocketHarness(background) {
  const start = background.indexOf("// --- WebSocket Client for TMWebDriver ---");
  assert(start >= 0, "exercise the WebSocket code from the generated extension");
  const sockets = [];
  const errors = [];
  const alarms = [];
  const created = event();
  const updated = event();
  const removed = event();
  const hooks = {
    query: async () => [],
    storage: async () => ({ "browser67.browser_instance_id.v1": "contract-instance" }),
    execute: async () => [{ result: { ok: true, data: "script-result" } }],
    command: async () => ({ ok: true, data: "command-result" }),
  };
  class Socket {
    static OPEN = 1;
    constructor() {
      this.readyState = 0;
      this.sent = [];
      this.discarded = [];
      sockets.push(this);
    }
    send(payload) {
      if (this.sendError) throw this.sendError;
      if (this.readyState === 0) throw new Error("InvalidStateError: CONNECTING");
      if (this.readyState !== 1) {
        this.discarded.push(payload);
        return;
      }
      this.sent.push(JSON.parse(payload));
    }
  }
  const context = vm.createContext({
    WebSocket: Socket,
    console: { log() {}, error: (...args) => errors.push(args.map((x) => x?.message ?? String(x)).join(" ")) },
    chrome: {
      alarms: { create: (name) => alarms.push(name), onAlarm: event() },
      runtime: { onStartup: event(), onInstalled: event() },
      tabs: { onCreated: created, onUpdated: updated, onRemoved: removed, get: async (id) => ({ id }) },
      storage: { local: { get: () => hooks.storage(), set: async () => {} } },
      scripting: { executeScript: () => hooks.execute() },
    },
    queryScriptableTabs: () => hooks.query(),
    handleExtMessage: (...args) => hooks.command(...args),
    normalizeNumericTabId: (value) => Number.isInteger(value) ? value : null,
    buildPageScript: (value) => value,
    buildCdpScript: (value) => value,
    setTimeout: (callback) => queueMicrotask(callback),
    crypto: { randomUUID: () => "contract-instance" },
    __browser67BuildIdentity: { schema: "contract-build-identity" },
  });
  vm.runInContext(background.slice(start), context, { filename: "generated/background.js" });
  const run = (source) => vm.runInContext(source, context);
  const open = () => { sockets.at(-1).readyState = Socket.OPEN; return sockets.at(-1); };
  return {
    sockets, errors, alarms, hooks, created, updated, removed, run, open,
    close(socket) { socket.readyState = 3; socket.onclose(); },
    reconnect() { run("connectWS()"); return open(); },
    message(socket, code, options = {}) {
      return socket.onmessage({ data: JSON.stringify({ id: "contract-request", tabId: 7, monitorNewTabs: false, code, ...options }) });
    },
  };
}

export { bounded, deferred, websocketHarness };
