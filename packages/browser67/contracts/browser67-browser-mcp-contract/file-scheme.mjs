import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { WebSocketServer } from "ws";
import { firstJsonContent } from "./rpc-content.mjs";

export async function assertFileSchemePreflight({ rpc, timeoutMs, registryPath }) {
  const commands = [];
  const server = new WebSocketServer({ port: 0, host: "127.0.0.1" });
  await new Promise(resolve => server.once("listening", resolve));
  const instance = "file-permission-contract";
  server.on("connection", socket => socket.on("message", raw => {
    const request = JSON.parse(String(raw));
    const command = request.code;
    if (command?.cmd === "tabs" && (!command.method || command.method === "list")) {
      socket.send(JSON.stringify({ id: request.id, success: true, result: [
        { id: 1, tab_id: "1", browser_instance_id: instance, url: "https://fixture.test/", title: "fixture" },
      ] }));
      return;
    }
    commands.push(command);
    socket.send(JSON.stringify({ id: request.id, type: "error", success: false,
      errorCode: "FILE_SCHEME_ACCESS_DENIED", error: 'Enable "Allow access to file URLs" for browser67' }));
  }));
  const readRegistry = () => readFile(registryPath, "utf8").catch(error => {
    if (error.code === "ENOENT") return null;
    throw error;
  });
  const before = await readRegistry();
  try {
    for (const action of ["create_managed", "select_or_create"]) {
      const response = await rpc.call("tools/call", {
        name: "browser_tab_lifecycle",
        arguments: {
          action, url: "file:///tmp/permission-contract.html",
          workspace_key: "file-permission-contract", browser_instance_id: instance,
          tmwd_mode: "tmwd", tmwd_transport: "ws",
          tmwd_ws_endpoint: `ws://127.0.0.1:${server.address().port}`,
        },
      }, timeoutMs);
      assert.equal(response.result.isError, true);
      assert.equal(firstJsonContent(response.result).error_code, "FILE_SCHEME_ACCESS_DENIED");
    }
    assert.deepEqual(commands, [
      { cmd: "tabs", method: "check_url", url: "file:///tmp/permission-contract.html", tabId: 1 },
      { cmd: "tabs", method: "check_url", url: "file:///tmp/permission-contract.html", tabId: 1 },
    ], "permission denial must precede window creation, tab creation, or navigation");
    assert.equal(await readRegistry(), before, "permission denial must not mutate managed registry");
  } finally {
    for (const socket of server.clients) socket.terminate();
    await new Promise(resolve => server.close(resolve));
  }
}
