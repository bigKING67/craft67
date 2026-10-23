import assert from "node:assert/strict";
import { createServer } from "node:http";
import { WebSocketServer } from "ws";
import { createTmwdWsRuntime } from "../../src/tmwd-runtime/ws.mjs";
import { createSessionRegistry } from "../../src/runtime/sessions/registry.mjs";

class ControlledSocket {
  static OPEN = 1;
  static CLOSED = 3;
  static sockets = [];
  readyState = 0;
  listeners = new Map();
  sent = [];
  closeCount = 0;
  failSend = false;

  constructor(endpoint) {
    this.endpoint = endpoint;
    ControlledSocket.sockets.push(this);
  }
  addEventListener(type, callback) {
    const callbacks = this.listeners.get(type) ?? [];
    callbacks.push(callback);
    this.listeners.set(type, callbacks);
  }
  emit(type, data = {}) {
    if (type === "open") this.readyState = 1;
    if (type === "close") this.readyState = 3;
    for (const callback of this.listeners.get(type) ?? []) callback(data);
  }
  close() {
    this.closeCount += 1;
    this.readyState = 2;
    queueMicrotask(() => this.emit("close"));
  }
  send(text) {
    if (this.failSend) throw new Error("fixture send failed");
    const request = JSON.parse(text);
    this.sent.push(request);
    if (request.code?.cmd !== "silent") {
      queueMicrotask(() => this.emit("message", { data: JSON.stringify({ id: request.id, result: this.endpoint }) }));
    }
  }
}

export async function assertSocketOwnership() {
  ControlledSocket.sockets = [];
  const sessionStore = createSessionRegistry();
  const runtime = createTmwdWsRuntime({ WebSocketImpl: ControlledSocket, sessionStore });
  const args = (port) => ({ tmwd_ws_endpoint: `ws://127.0.0.1:${port}`, timeout_ms: 500 });
  try {
    const first = runtime.connect(args(17001));
    const rejectedFirst = assert.rejects(first, /endpoint changed/);
    const oldSocket = ControlledSocket.sockets[0];
    const next = runtime.connect(args(17002));
    const current = ControlledSocket.sockets[1];
    await rejectedFirst;
    assert.equal(runtime.stats().state, "connecting", "the cancelled attempt's finally cannot reset its replacement");
    current.emit("open");
    await next;
    assert.equal(oldSocket.closeCount > 0, true, "a superseded CONNECTING socket must close promptly");
    oldSocket.emit("open");
    oldSocket.emit("message", { data: JSON.stringify({ type: "tabs_update", tabs: [{ id: 999, browser_instance_id: "stale" }] }) });
    oldSocket.emit("error", { message: "late error" });
    oldSocket.emit("close");
    assert.equal(runtime.stats().state, "open");
    assert.equal(runtime.stats().cached_tab_count, 0);
    assert.equal(runtime.stats().connection_generation, 1);
    const response = await runtime.send(args(17002), { code: { cmd: "tabs" } }, 500);
    assert.equal(response.result, args(17002).tmwd_ws_endpoint);
    assert.equal(oldSocket.sent.length, 0);
    assert.equal(current.sent.length, 1);

    const silent = runtime.send(args(17002), { code: { cmd: "silent" } }, 500);
    await Promise.resolve();
    const silentId = current.sent.at(-1).id;
    oldSocket.emit("message", { data: JSON.stringify({ id: silentId, result: "wrong socket" }) });
    assert.equal(runtime.stats().pending_count, 1, "old replies cannot settle a request owned by the current socket");
    current.emit("message", { data: JSON.stringify({ id: silentId, result: "current socket" }) });
    assert.equal((await silent).result, "current socket");

    current.failSend = true;
    await assert.rejects(runtime.send(args(17002), { code: { cmd: "tabs" } }, 500), /fixture send failed/);
    assert.equal(runtime.stats().pending_count, 0, "a synchronous send failure must release its request and timer");
    current.failSend = false;
    const pending = runtime.send(args(17002), { code: { cmd: "silent" } }, 500);
    const rejectedPending = assert.rejects(pending, /endpoint changed/);
    await Promise.resolve();
    const replacement = runtime.connect(args(17003));
    const shared = runtime.connect(args(17003));
    assert.equal(ControlledSocket.sockets.length, 3, "same-endpoint callers share the connecting socket");
    ControlledSocket.sockets[2].emit("open");
    await Promise.all([replacement, shared, rejectedPending]);
    assert.equal(runtime.stats().pending_count, 0);
    assert.equal((await runtime.send(args(17003), { code: { cmd: "tabs" } }, 500)).success, true);

    const unsent = runtime.send(args(17003), { code: { cmd: "tabs" } }, 500);
    const rejectedUnsent = assert.rejects(unsent, /not connected/);
    const switched = runtime.connect(args(17005));
    ControlledSocket.sockets.at(-1).emit("open");
    await Promise.all([switched, rejectedUnsent]);
    assert.equal(ControlledSocket.sockets.at(-1).sent.length, 0, "a request cannot follow a different endpoint across await");
  } finally {
    await runtime.dispose({ timeout_ms: 100 });
  }
  const disposing = createTmwdWsRuntime({ WebSocketImpl: ControlledSocket, sessionStore });
  const connecting = disposing.connect(args(17004));
  const rejectedConnecting = assert.rejects(connecting, /disposed/);
  const abandoned = ControlledSocket.sockets.at(-1);
  await disposing.dispose({ timeout_ms: 100 });
  await rejectedConnecting;
  abandoned.emit("open");
  abandoned.emit("message", { data: JSON.stringify({ type: "ext_ready", tabs: [{ id: 999 }] }) });
  assert.equal(disposing.stats().state, "idle");
  assert.equal(disposing.stats().pending_count, 0);
  assert.equal(disposing.stats().cached_tab_count, 0);
  assert.equal(disposing.stats().connection_generation, 0);

  const timingOut = createTmwdWsRuntime({ WebSocketImpl: ControlledSocket, sessionStore });
  await assert.rejects(timingOut.connect({ ...args(17006), timeout_ms: 100 }), /connect timeout/);
  const timedOutSocket = ControlledSocket.sockets.at(-1);
  timedOutSocket.emit("open");
  assert.equal(timingOut.stats().state, "idle");
  assert.equal(timingOut.stats().connection_generation, 0);
  assert.equal(timedOutSocket.closeCount, 1);
  await timingOut.dispose();
}

// Real delayed HTTP upgrades reproduce the race independently of the controlled socket.
export async function assertRealSocketOwnership() {
  const sockets = new Set();
  const gates = new Map();
  const received = [];
  const websocket = new WebSocketServer({ noServer: true });
  const server = createServer();
  server.on("connection", (socket) => {
    sockets.add(socket);
    socket.once("close", () => sockets.delete(socket));
  });
  server.on("upgrade", (request, socket, head) => {
    const upgrade = () => {
      if (!socket.destroyed) websocket.handleUpgrade(request, socket, head, (client) => {
        client.on("message", (text) => {
          const payload = JSON.parse(String(text));
          received.push(request.url);
          client.send(JSON.stringify({ id: payload.id, result: request.url }));
        });
      });
    };
    if (request.url === "/a") gates.set("a", upgrade);
    else upgrade();
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(undefined)));
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("missing fixture address");
  const endpoint = `ws://127.0.0.1:${address.port}`;
  const runtime = createTmwdWsRuntime({ sessionStore: createSessionRegistry() });
  try {
    const a = runtime.connect({ tmwd_ws_endpoint: `${endpoint}/a`, timeout_ms: 1_000 });
    const rejectedA = assert.rejects(a, /endpoint changed/);
    for (let i = 0; i < 100 && !gates.has("a"); i += 1) await new Promise((resolve) => setTimeout(resolve, 5));
    assert.equal(gates.has("a"), true, "first upgrade reached the fixture");
    await runtime.connect({ tmwd_ws_endpoint: `${endpoint}/b`, timeout_ms: 1_000 });
    gates.get("a")();
    await rejectedA;
    const response = await runtime.send({ tmwd_ws_endpoint: `${endpoint}/b` }, { code: { cmd: "tabs" } }, 1_000);
    assert.equal(response.result, "/b");
    assert.deepEqual(received, ["/b"]);
  } finally {
    await runtime.dispose();
    for (const socket of sockets) socket.destroy();
    await new Promise((resolve) => websocket.close(() => resolve(undefined)));
    await new Promise((resolve) => server.close(() => resolve(undefined)));
  }
}
