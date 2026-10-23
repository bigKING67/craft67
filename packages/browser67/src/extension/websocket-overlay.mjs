const socketHelpers = `function browser67SocketIsCurrent(socket) {
  return Boolean(socket && ws === socket && socket.readyState === WebSocket.OPEN);
}

function browser67SendSocketMessage(socket, message) {
  if (!browser67SocketIsCurrent(socket)) return false;
  try {
    socket.send(JSON.stringify(message));
    return true;
  } catch (error) {
    console.error('[TMWD-WS] send ' + message.type + ' failed', error);
    return false;
  }
}

`;

const openHandlerAnchor = `  ws.onopen = async () => {
    console.log('[TMWD-WS] Connected!');
    scheduleKeepalive(); // Keep SW alive while connected
    const tabs = await queryScriptableTabs();
    ws.send(JSON.stringify({
      type: 'ext_ready',
      browser_instance_id: await browser67GetInstanceId(),
      extension_identity: globalThis.__browser67BuildIdentity ?? null,
      tabs: tabs.map(t => ({ id: t.id, url: t.url, title: t.title }))
    }));
    console.log('[TMWD-WS] Sent ext_ready with', tabs.length, 'tabs');
  };
`;

const openHandler = `  const socket = ws;
  socket.onopen = async () => {
    if (!browser67SocketIsCurrent(socket)) return;
    try {
      console.log('[TMWD-WS] Connected!');
      scheduleKeepalive();
      const tabs = await queryScriptableTabs();
      if (!browser67SendSocketMessage(socket, {
        type: 'ext_ready',
        browser_instance_id: await browser67GetInstanceId(),
        extension_identity: globalThis.__browser67BuildIdentity ?? null,
        tabs: tabs.map(t => ({ id: t.id, url: t.url, title: t.title }))
      })) return;
      console.log('[TMWD-WS] Sent ext_ready with', tabs.length, 'tabs');
    } catch (error) {
      console.error('[TMWD-WS] ext_ready failed', error);
    }
  };
`;

const tabsUpdateAnchor = `async function sendTabsUpdate() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const tabs = (await queryScriptableTabs()).filter(t => !/streamlit/i.test(t.title));
  ws.send(JSON.stringify({
    type: 'tabs_update',
    browser_instance_id: await browser67GetInstanceId(),
    extension_identity: globalThis.__browser67BuildIdentity ?? null,
    tabs: tabs.map(t => ({ id: t.id, url: t.url, title: t.title }))
  }));
}
`;

const tabsUpdate = `let browser67TabsUpdateSocket = null;
let browser67TabsUpdateFlight = Promise.resolve();
function sendTabsUpdate() {
  const socket = ws;
  if (!browser67SocketIsCurrent(socket)) return Promise.resolve();
  if (browser67TabsUpdateSocket !== socket) {
    browser67TabsUpdateSocket = socket;
    browser67TabsUpdateFlight = Promise.resolve();
  }
  browser67TabsUpdateFlight = browser67TabsUpdateFlight.then(async () => {
    if (!browser67SocketIsCurrent(socket)) return;
    const tabs = (await queryScriptableTabs()).filter(t => !/streamlit/i.test(t.title));
    browser67SendSocketMessage(socket, {
      type: 'tabs_update',
      browser_instance_id: await browser67GetInstanceId(),
      extension_identity: globalThis.__browser67BuildIdentity ?? null,
      tabs: tabs.map(t => ({ id: t.id, url: t.url, title: t.title }))
    });
  }).catch(error => {
    console.error('[TMWD-WS] tabs_update failed', error);
  });
  return browser67TabsUpdateFlight;
}
`;

function replaceRequired(source, anchor, replacement) {
  const index = source.indexOf(anchor);
  if (index < 0 || source.indexOf(anchor, index + anchor.length) >= 0) {
    throw new Error("upstream WebSocket anchors changed; review browser67 connection ownership");
  }
  return source.replace(anchor, replacement);
}

function patchWebSocketLifecycle(source) {
  // Keep the upstream reference unchanged; every generated async reply must use
  // the accepting connection, including the legacy plain-JS execution path.
  let replyCount = 0;
  let next = source.replace(/^( +)ws\.send\(JSON\.stringify\((\{[^\n]+\})\)\);$/gm, (_, indent, payload) => {
    replyCount += 1;
    const send = `browser67SendSocketMessage(socket, ${payload})`;
    return payload.startsWith("{ type: 'ack',") ? `${indent}if (!${send}) return;` : `${indent}${send};`;
  });
  if (replyCount !== 7) {
    throw new Error("upstream WebSocket replies changed; review browser67 connection ownership");
  }
  next = replaceRequired(next, "async function handleWsExec(data) {", `${socketHelpers}async function handleWsExec(data, socket) {`);
  next = replaceRequired(next, "await handleWsExec(data);", "await handleWsExec(data, socket);");
  next = replaceRequired(next, openHandlerAnchor, openHandler);
  next = replaceRequired(next, "  ws.onmessage = async (event) => {", [
    "  socket.onmessage = async (event) => {",
    "    if (!browser67SocketIsCurrent(socket)) return;",
  ].join("\n"));
  next = replaceRequired(next, "  ws.onclose = () => {", [
    "  socket.onclose = () => {",
    "    if (ws !== socket) return;",
  ].join("\n"));
  next = replaceRequired(next, "  ws.onerror = (e) => {", [
    "  socket.onerror = (e) => {",
    "    if (ws !== socket) return;",
  ].join("\n"));
  next = replaceRequired(next, "console.error('[TMWD-WS] message parse error', e);", "console.error('[TMWD-WS] Message failed', e);");
  next = replaceRequired(next, tabsUpdateAnchor, tabsUpdate);
  const executionStart = next.indexOf("async function handleWsExec(data, socket) {");
  if (/\bws\.send\b/.test(next.slice(executionStart))) {
    throw new Error("unscoped WebSocket send remains in the generated async handlers");
  }
  return next;
}

export { patchWebSocketLifecycle };
