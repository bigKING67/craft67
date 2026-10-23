import assert from "node:assert/strict";
import { createServer } from "node:http";
import { WebSocketServer } from "ws";
import { executeTmwdJsWithFallback } from "../../src/tmwd-runtime/execute.mjs";
import { createTmwdWsRuntime } from "../../src/tmwd-runtime/ws.mjs";
import { createTmwdTransportHealthStore } from "../../src/tmwd-runtime/health.mjs";
import { createSessionRegistry } from "../../src/runtime/sessions/registry.mjs";

export async function assertUnknownExecutionIsNotReplayed() {
  const target = { id: "replay-instance:42", tab_id: "42", browser_instance_id: "replay-instance", title: "fixture", url: "https://fixture.test/" };
  const counts = { ws: 0, link: 0 };
  let failureMode = "close";
  let linkFailure = "";
  const ws = new WebSocketServer({ host: "127.0.0.1", port: 0 });
  ws.on("connection", (socket) => socket.on("message", (text) => {
    const message = JSON.parse(String(text));
    if (message.code?.cmd === "tabs") {
      socket.send(JSON.stringify({ id: message.id, result: [target] }));
      return;
    }
    counts.ws += 1; // The fixture received the script; its effects may already exist.
    if (failureMode === "close") socket.close();
    // timeout mode deliberately loses the execution result without closing.
  }));
  await new Promise((resolve) => ws.once("listening", () => resolve(undefined)));
  const http = createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    const message = JSON.parse(Buffer.concat(chunks).toString());
    let result;
    if (message.cmd === "get_all_sessions") result = [target];
    else {
      counts.link += 1;
      if (linkFailure === "http_disconnect") {
        response.destroy();
        return;
      }
      result = linkFailure ? { error: "tmwd extension websocket closed" } : { data: { recovered_before_send: true } };
    }
    response.setHeader("Connection", "close");
    response.setHeader("Content-Type", "application/json");
    response.end(JSON.stringify({ r: result }));
  });
  await new Promise((resolve) => http.listen(0, "127.0.0.1", () => resolve(undefined)));
  const wsAddress = ws.address();
  const httpAddress = http.address();
  if (!wsAddress || typeof wsAddress === "string" || !httpAddress || typeof httpAddress === "string") throw new Error("missing fixture address");
  const args = {
    tmwd_transport: "auto", timeout_ms: 300, browser_instance_id: target.browser_instance_id,
    session_id: target.tab_id, tmwd_ws_endpoint: `ws://127.0.0.1:${wsAddress.port}`,
    tmwd_link_endpoint: `http://127.0.0.1:${httpAddress.port}/link`,
  };
  const context = { tmwd_transport: "ws", endpoint: args.tmwd_ws_endpoint, target };
  try {
    for (const mode of ["close", "timeout"]) {
      failureMode = mode;
      const runtime = {
        sessionStore: createSessionRegistry(), transportHealth: createTmwdTransportHealthStore(),
        tmwdWsRuntime: createTmwdWsRuntime({ sessionStore: createSessionRegistry() }),
      };
      try {
        await assert.rejects(
          executeTmwdJsWithFallback(args, context, "return 'possibly executed';", { runtime }),
          (error) => {
            assert.equal(error.executionMayHaveStarted, true);
            assert.equal(error.transportAttempts.length, 1, "an uncertain execution cannot resolve or execute through another transport");
            return true;
          },
        );
        assert.equal(counts.link, 0);
      } finally {
        await runtime.tmwdWsRuntime.dispose();
      }
    }
    assert.equal(counts.ws, 2);
    for (const failure of ["reported_disconnect", "http_disconnect"]) {
      linkFailure = failure;
      const runtime = {
        sessionStore: createSessionRegistry(), transportHealth: createTmwdTransportHealthStore(),
        tmwdWsRuntime: createTmwdWsRuntime({ sessionStore: createSessionRegistry() }),
      };
      try {
        await assert.rejects(
          executeTmwdJsWithFallback(args, { ...context, tmwd_transport: "link", endpoint: args.tmwd_link_endpoint }, "return 'possibly executed over link';", { runtime }),
          (error) => {
            assert.equal(error.executionMayHaveStarted, true);
            assert.equal(error.transportAttempts.length, 1, "uncertain Link execution cannot replay through WS");
            return true;
          },
        );
        assert.equal(counts.ws, 2);
      } finally {
        await runtime.tmwdWsRuntime.dispose();
      }
    }
    linkFailure = "";
    // A refused connection is known to have failed before send and may recover.
    const runtime = { tmwdWsRuntime: createTmwdWsRuntime(), transportHealth: createTmwdTransportHealthStore(), sessionStore: createSessionRegistry() };
    try {
      const closedEndpoint = "ws://127.0.0.1:9";
      const recovered = await executeTmwdJsWithFallback(
        { ...args, timeout_ms: 1_000, tmwd_ws_endpoint: closedEndpoint },
        { ...context, endpoint: closedEndpoint }, "return 'not sent over ws';", { runtime },
      );
      assert.equal(recovered.executed.value.recovered_before_send, true);
      assert.equal(counts.link, 3);
      assert.equal(counts.ws, 2);
    } finally {
      await runtime.tmwdWsRuntime.dispose();
    }
  } finally {
    for (const client of ws.clients) client.terminate();
    await new Promise((resolve) => ws.close(() => resolve(undefined)));
    http.closeAllConnections();
    await new Promise((resolve) => http.close(() => resolve(undefined)));
  }
}
