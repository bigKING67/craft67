import assert from "node:assert/strict";
import { createServer } from "node:http";

import { handleBrowserExecuteJs } from "../../src/server/browser-core/execute-js.mjs";
import { createBrowserToolRegistry, dispatchRegisteredTool } from "../../src/mcp/browser/tool-registry.mjs";
import { resolvePageContext } from "../../src/runtime/page-context.mjs";
import { createSessionRegistry } from "../../src/runtime/sessions/registry.mjs";
import { createTmwdTransportHealthStore } from "../../src/tmwd-runtime/health.mjs";
import { executionSessionDiagnostics } from "../../src/browser/execution/session-diagnostics.mjs";
import { firstOutcomeContent } from "./rpc-content.mjs";

const targets = [
  { id: "instance-a:1", tab_id: "1", browser_instance_id: "instance-a", title: "unrelated-active", url: "https://unrelated.test/" },
  { id: "instance-a:42", tab_id: "42", browser_instance_id: "instance-a", title: "execution-target", url: "https://fixture.test/" },
  { id: "instance-b:42", tab_id: "42", browser_instance_id: "instance-b", title: "unrelated-instance", url: "https://other.test/" },
];

export async function assertExecutionOutcomes() {
  let reply;
  const sessionStore = createSessionRegistry();
  sessionStore.sync(targets);
  for (const tabId of ["42", "instance-a:42", "instance-a:instance-a:42"]) {
    const scoped = executionSessionDiagnostics(sessionStore, { browser_instance_id: "instance-a", tab_id: tabId });
    assert.deepEqual(scoped.sessions.map((session) => session.id), ["instance-a:42"]);
    assert.equal(scoped.default_session_id, null);
    assert.equal(scoped.latest_session_id, null);
  }
  assert.deepEqual(executionSessionDiagnostics(sessionStore).sessions, [], "unresolved execution never falls back to another tab's diagnostics");
  const journal = [];
  const runtime = {
    runtime_id: "execution-outcome-contract",
    sessionStore,
    transportHealth: createTmwdTransportHealthStore(),
    tmwdWsRuntime: {
      listSessionsWithMeta: async () => ({ tabs: targets, cache: { connection_generation: 1 } }),
      send: async () => reply,
    },
    runForTab: async (_key, callback) => callback(),
    toolJournal: { record: async (entry) => journal.push(entry) },
  };
  const getManagedTab = async () => ({ ownership_origin: "agent_created", owner: "tmwd" });
  const registry = createBrowserToolRegistry({ handlers: {
    browser_execute_js: (args) => handleBrowserExecuteJs(args, { runtime, get_managed_tab: getManagedTab }),
  } });
  const tools = { ...registry, browser_execute_js: {
    ...registry.browser_execute_js,
    pagePolicy: (name, args, data) => resolvePageContext(name, args, data, {
      runtime, get_managed_tab: getManagedTab,
    }),
  } };
  const link = createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    const command = JSON.parse(Buffer.concat(chunks).toString());
    response.setHeader("Connection", "close");
    response.setHeader("Content-Type", "application/json");
    response.end(JSON.stringify({ r: command.cmd === "get_all_sessions" ? targets : reply }));
  });
  await new Promise((resolve) => link.listen(0, "127.0.0.1", () => resolve(undefined)));
  const address = link.address();
  if (!address || typeof address === "string") throw new Error("missing fixture address");
  const baseArgs = {
    script: "return 1;", tmwd_mode: "tmwd", browser_instance_id: "instance-a",
    tab_id: "42", no_monitor: true, timeout_ms: 1_000,
    tmwd_link_endpoint: `http://127.0.0.1:${address.port}/link`,
  };
  const call = async (args) => {
    const response = await dispatchRegisteredTool("browser_execute_js", { ...baseArgs, ...args }, { registry: tools, runtime });
    return { response, outcome: firstOutcomeContent(response) };
  };
  const assertScoped = (value) => {
    const text = JSON.stringify(value);
    assert.doesNotMatch(text, /unrelated|other\.test|instance-b/, "execution diagnostics must exclude other tabs and instances");
  };
  try {
    for (const script of [123, {}, [], null]) {
      const { outcome, response } = await call({ script });
      assert.equal(outcome.ok, false, "non-string scripts fail at the MCP input boundary");
      assert.equal(outcome.error.code, "INVALID_ARGUMENTS");
      assert.equal(response.isError, true);
    }
    for (const transport of ["ws", "link"]) {
      for (const mode of ["compact", "full"]) {
        for (const error of ["expected execution failure", { name: "Error", message: "expected execution failure", code: "FIXTURE_ERROR" }]) {
          reply = transport === "ws" ? { success: false, error } : { error };
          const { response, outcome } = await call({ tmwd_transport: transport, output_mode: mode });
          assert.equal(outcome.ok, false, `${transport}/${mode} must report an operational failure`);
          assert.equal(response.isError, true);
          assert.equal(outcome.status, "failed");
          assert.equal(outcome.error.message, "expected execution failure");
          assert.equal(outcome.error.code, typeof error === "string" ? "EXECUTION_ERROR" : "FIXTURE_ERROR");
          assert.equal(outcome.error.details.status, "failed");
          assertScoped(outcome);
          assert.equal(journal.at(-1).status, "error");
          assertScoped(journal.at(-1).error_details);
        }
        // A successful user value may itself contain status/error fields.
        const value = { status: "failed", error: "ordinary user data", ok: false };
        reply = transport === "ws"
          ? { success: true, result: value }
          : { ok: true, data: value };
        const { outcome } = await call({ tmwd_transport: transport, output_mode: mode });
        assert.equal(outcome.ok, true, "the request after a failure recovers without classifying user data");
        assert.equal(outcome.data.status, "success");
        assert.equal(outcome.page.browser_instance_id, "instance-a");
        assert.equal(outcome.page.tab_id, "42");
        assertScoped(outcome);
        assertScoped(journal.at(-1).result);
        const sessions = mode === "full" ? outcome.data.sessions : outcome.data.session_summary.selected;
        assert.equal(sessions.length, 1);
        assert.equal(sessions[0].id, "instance-a:42");
        if (mode === "full") assert.deepEqual(outcome.data.js_return, value);
        else assert.deepEqual(JSON.parse(outcome.data.js_return.preview), value);
      }
    }
    reply = { success: false, error: { message: "nested bridge error" } };
    runtime.tmwdWsRuntime.send = async () => ({ success: true, result: { ok: false, error: { message: "nested bridge error" } } });
    assert.equal((await call({ tmwd_transport: "ws", script: '{"cmd":"fixture"}' })).outcome.error.message, "nested bridge error");
    reply = { data: { ok: false, error: { message: "nested link bridge error" } } };
    assert.equal((await call({ tmwd_transport: "link", script: '{"cmd":"fixture"}' })).outcome.error.message, "nested link bridge error");
    const fallbackTools = { ...tools, browser_execute_js: {
      ...tools.browser_execute_js, handler: async () => ({ status: "fallback_executed", native_auto_fallback: { executed: true } }),
    } };
    const fallback = await dispatchRegisteredTool("browser_execute_js", baseArgs, { registry: fallbackTools, runtime });
    assert.equal(firstOutcomeContent(fallback).ok, true, "an actually executed native fallback keeps its successful outcome");
    runtime.tmwdWsRuntime.listSessionsWithMeta = async () => { throw new Error("tmwd ws is not connected"); };
    for (const mode of ["compact", "full"]) {
      const { outcome } = await call({
        tmwd_transport: "ws", output_mode: mode, native_auto_fallback: true,
        native_auto_fallback_policy: "strict", native_auto_execute: false,
      });
      assert.equal(outcome.ok, false);
      assert.equal(outcome.error.code, "NO_EXTENSION");
      const details = outcome.error.details;
      if (mode === "full") assert.deepEqual(details.sessions, []);
      else assert.equal(details.session_summary.count, 0);
      assert.equal(details.default_session_id, null);
      assert.equal(details.active_session_id, null);
      assert.equal(details.latest_session_id, null);
      assertScoped(outcome);
    }
  } finally {
    link.closeAllConnections();
    await new Promise((resolve) => link.close(() => resolve(undefined)));
  }
}
