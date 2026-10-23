import { sameBrowserTab } from "../../tab-workspace/identity.mjs";

// Execution may inspect the registry for routing, but its response belongs to one tab.
function executionSessionDiagnostics(sessionStore, target = null) {
  const sessions = target
    ? sessionStore.list().filter((session) => sameBrowserTab(session, target))
    : [];
  const pointers = sessionStore.sessionPointers();
  const selectedIds = new Set(sessions.map((session) => session.id));
  const pointer = (key) => selectedIds.has(pointers[key]) ? pointers[key] : null;
  return {
    browser_instance_id: target?.browser_instance_id || undefined,
    sessions,
    active_session_id: pointer("active_session_id"),
    default_session_id: pointer("default_session_id"),
    latest_session_id: pointer("latest_session_id"),
    active_browser_instance_id: pointer("active_session_id") ? pointers.active_browser_instance_id : null,
    default_browser_instance_id: pointer("default_session_id") ? pointers.default_browser_instance_id : null,
  };
}

export { executionSessionDiagnostics };
