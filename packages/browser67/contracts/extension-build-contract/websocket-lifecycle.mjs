import assert from "node:assert/strict";

import { bounded, deferred, websocketHarness } from "./websocket-harness.mjs";

async function assertHandshake(background) {
  for (const phase of ["query", "storage"]) {
    const h = websocketHarness(background);
    const pending = deferred();
    const started = deferred();
    h.hooks[phase] = () => { started.resolve(); return pending.promise; };
    const old = h.open();
    const opening = old.onopen();
    await bounded(started.promise);
    h.close(old);
    const current = h.reconnect();
    pending.resolve(phase === "query" ? [] : { "browser67.browser_instance_id.v1": "contract-instance" });
    await bounded(opening);
    assert.equal(current.sent.length, 0, `old handshake cannot enter the new connection after ${phase}`);
    assert.equal(old.discarded.length, 0, "do not send through a closed socket");
    await bounded(current.onopen());
    assert.equal(current.sent[0].type, "ext_ready");
    assert.equal(current.sent[0].browser_instance_id, "contract-instance");
    assert.deepEqual(current.sent[0].extension_identity, { schema: "contract-build-identity" });
    assert.deepEqual(h.errors, []);
  }
  const h = websocketHarness(background);
  const current = h.open();
  h.hooks.query = async () => { throw new Error("tabs query failed"); };
  await bounded(current.onopen());
  assert.match(h.errors[0], /ext_ready.*tabs query failed/);
  h.close(current);
  h.hooks.query = async () => [];
  await bounded(h.reconnect().onopen());
  assert.equal(h.sockets[1].sent[0].type, "ext_ready", "fresh handshake recovers after a query failure");
}

async function assertTabsUpdate(background) {
  const h = websocketHarness(background);
  const old = h.open();
  const pending = deferred();
  const started = deferred();
  let queries = 0;
  h.hooks.query = () => { queries += 1; started.resolve(); return pending.promise; };
  const first = h.run("sendTabsUpdate()");
  await bounded(started.promise);
  const queued = h.run("sendTabsUpdate()");
  await Promise.resolve();
  assert.equal(queries, 1, "same-connection queries remain serialized");
  h.close(old);
  const current = h.reconnect();
  h.hooks.query = async () => [{ id: 9, title: "fresh", url: "https://example.test/" }];
  await bounded(h.run("sendTabsUpdate()"));
  assert.equal(current.sent.length, 1, "a stale pending query cannot block the new connection");
  pending.resolve([{ id: 8, title: "stale", url: "https://example.test/old" }]);
  await bounded(Promise.all([first, queued]));
  assert.deepEqual(current.sent.map((message) => message.tabs[0].id), [9]);
  assert.equal(old.sent.length + old.discarded.length, 0);
  assert.deepEqual(h.errors, []);

  h.hooks.query = async () => { throw new Error("update query failed"); };
  await bounded(h.run("sendTabsUpdate()"));
  assert.match(h.errors[0], /tabs_update.*update query failed/);
  h.hooks.query = async () => [];
  await bounded(h.run("sendTabsUpdate()"));
  assert.equal(current.sent.length, 2, "the queue recovers after an observable failure");
}

async function assertUpdateOrdering(background) {
  const h = websocketHarness(background);
  const current = h.open();
  const queries = [deferred(), deferred()];
  const started = [deferred(), deferred()];
  let count = 0;
  h.hooks.query = () => { const index = count++; started[index].resolve(); return queries[index].promise; };
  const first = h.run("sendTabsUpdate()");
  const second = h.run("sendTabsUpdate()");
  await bounded(started[0].promise);
  assert.equal(count, 1);
  queries[0].resolve([{ id: 1 }]);
  await bounded(first);
  await bounded(started[1].promise);
  queries[1].resolve([{ id: 2 }]);
  await bounded(second);
  assert.deepEqual(current.sent.map((message) => message.tabs[0].id), [1, 2]);
  assert(current.sent.every((message) => message.type === "tabs_update" && message.browser_instance_id === "contract-instance"));
}

async function assertReplies(background) {
  for (const code of ["1 + 1", { cmd: "contract" }, { legacy: true }]) {
    for (const reconnect of [false, true]) {
      const h = websocketHarness(background);
      const old = h.open();
      const pending = deferred();
      const started = deferred();
      const script = typeof code === "string";
      h.hooks[script ? "execute" : "command"] = () => { started.resolve(); return pending.promise; };
      const listenersBefore = h.created.listeners.size;
      const response = h.message(old, code, { monitorNewTabs: true });
      await bounded(started.promise);
      h.close(old);
      const current = reconnect ? h.reconnect() : null;
      pending.resolve(script ? [{ result: { ok: true, data: "stale" } }] : { ok: true, data: "stale" });
      await bounded(response);
      assert.deepEqual(old.sent.map((message) => message.type), script ? ["ack"] : []);
      assert.equal(old.discarded.length, 0);
      assert.equal(current?.sent.length ?? 0, 0, "a response belongs only to the accepting connection");
      assert.equal(h.created.listeners.size, listenersBefore, "script tab listeners are released after disconnect");
      assert.deepEqual(h.errors, []);
    }
  }

  const h = websocketHarness(background);
  const current = h.open();
  await bounded(h.message(current, "1 + 1"));
  assert.deepEqual(current.sent.map((message) => message.type), ["ack", "result"]);
  assert.equal(current.sent[1].result, "script-result");
  h.hooks.execute = async () => [{ result: { ok: false, error: "script failed" } }];
  await bounded(h.message(current, "throw new Error()"));
  assert.equal(current.sent.at(-1).error, "script failed");
  await bounded(h.message(current, "1", { tabId: null }));
  assert.match(current.sent.at(-1).error, /invalid or missing numeric tabId/);
  await bounded(h.message(current, { cmd: "contract" }));
  assert.equal(current.sent.at(-1).result, "command-result");
  await bounded(h.message(current, { legacy: true }));
  assert.equal(current.sent.at(-1).result, "command-result");
  assert(current.sent.every((message) => message.browser_instance_id === "contract-instance"));
  assert.deepEqual(h.errors, []);
}

async function assertAckOwnership(background) {
  const h = websocketHarness(background);
  const old = h.open();
  const pending = deferred();
  const started = deferred();
  let executions = 0;
  h.hooks.storage = () => { started.resolve(); return pending.promise; };
  h.hooks.execute = async () => { executions += 1; return [{ result: { ok: true } }]; };
  const response = h.message(old, "1 + 1");
  await bounded(started.promise);
  h.close(old);
  const current = h.reconnect();
  pending.resolve({ "browser67.browser_instance_id.v1": "contract-instance" });
  await bounded(response);
  assert.equal(executions, 0, "a stale command cannot start after its ACK identity lookup");
  assert.equal(old.discarded.length + current.sent.length, 0);
  assert.deepEqual(h.errors, []);
}

async function assertReplyIdentityOwnership(background) {
  for (const operation of ["tabs_update", "command", "legacy"]) {
    const h = websocketHarness(background);
    const old = h.open();
    const pending = deferred();
    const started = deferred();
    h.hooks.storage = () => { started.resolve(); return pending.promise; };
    const response = operation === "tabs_update"
      ? h.run("sendTabsUpdate()")
      : h.message(old, operation === "command" ? { cmd: "contract" } : { legacy: true });
    await bounded(started.promise);
    h.close(old);
    const current = h.reconnect();
    pending.resolve({ "browser67.browser_instance_id.v1": "contract-instance" });
    await bounded(response);
    assert.equal(old.discarded.length + current.sent.length, 0, `${operation} rechecks ownership after identity lookup`);
    assert.deepEqual(h.errors, []);
  }
}

async function assertSendFailure(background) {
  const h = websocketHarness(background);
  const current = h.open();
  let executions = 0;
  h.hooks.execute = async () => { executions += 1; return [{ result: { ok: true } }]; };
  current.sendError = new Error("socket send failed");
  await bounded(h.message(current, "1 + 1"));
  assert.equal(executions, 0, "failed ACK cannot start a script");
  assert.match(h.errors[0], /send ack failed.*socket send failed/);
  await bounded(h.run("sendTabsUpdate()"));
  assert.match(h.errors[1], /send tabs_update failed.*socket send failed/);
  delete current.sendError;
  await bounded(h.message(current, "1 + 1"));
  await bounded(h.run("sendTabsUpdate()"));
  assert.equal(executions, 1);
  assert.deepEqual(current.sent.map((message) => message.type), ["ack", "result", "tabs_update"]);
}

async function assertConnectionCallbacks(background) {
  const h = websocketHarness(background);
  const old = h.open();
  old.readyState = 2;
  const current = h.reconnect();
  const alarmCount = h.alarms.length;
  h.close(old);
  assert.equal(h.run("ws === null"), false, "late close cannot clear the current connection");
  assert.equal(h.alarms.length, alarmCount, "late close cannot reschedule the current connection");
  await bounded(old.onopen());
  await bounded(h.message(old, { cmd: "contract" }));
  assert.equal(old.discarded.length + current.sent.length, 0, "late callbacks remain fenced");
  await bounded(current.onopen());
  assert.equal(current.sent[0].type, "ext_ready");
  h.close(current);
  assert.equal(h.run("ws === null"), true);
  assert.equal(h.alarms.at(-1), "tmwd-ws-probe");
}

async function assertWebSocketLifecycle(background) {
  await assertHandshake(background);
  await assertTabsUpdate(background);
  await assertUpdateOrdering(background);
  await assertReplies(background);
  await assertAckOwnership(background);
  await assertReplyIdentityOwnership(background);
  await assertSendFailure(background);
  await assertConnectionCallbacks(background);
}

export { assertWebSocketLifecycle };
